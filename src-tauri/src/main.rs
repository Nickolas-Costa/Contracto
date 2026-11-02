//! Shell Tauri do Contracto (ADR 0029, contrato em docs/TAURI_CONTRATO.md).
//!
//! Sobe o sidecar Python, guarda origem e token só em memória e expõe à página os
//! comandos nativos nomeados. A página nunca recebe caminho, token nem porta.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use base64::Engine;
use serde_json::{json, Value};
use tauri::{AppHandle, DragDropEvent, Manager, RunEvent, Webview, WebviewUrl, WebviewWindowBuilder, WindowEvent};
use tauri_plugin_dialog::{DialogExt, FileDialogBuilder, MessageDialogKind};

const CORPO_MAX: usize = 1024 * 1024;
const ARQUIVO_MAX: usize = 20 * 1024 * 1024;
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

struct Controle {
    filho: Child,
    entrada: ChildStdin,
    saida: BufReader<ChildStdout>,
    proximo: u64,
}

struct Backend {
    origem: String,
    token: String,
    http: reqwest::Client,
    controle: Mutex<Controle>,
}

fn sem_janela(cmd: &mut Command) -> &mut Command {
    #[cfg(windows)]
    std::os::windows::process::CommandExt::creation_flags(cmd, CREATE_NO_WINDOW);
    cmd
}

impl Backend {
    /// Envia um comando ao sidecar e espera a resposta de mesmo `id`.
    /// shortcut: leitura bloqueante sem timeout, trocar por thread/canal se o sidecar travar.
    fn controlar(&self, mut comando: Value) -> Option<Value> {
        let mut c = self.controle.lock().ok()?;
        c.proximo += 1;
        let id = c.proximo;
        comando["id"] = json!(id);
        writeln!(c.entrada, "{comando}").ok()?;
        c.entrada.flush().ok()?;
        let mut linha = String::new();
        loop {
            linha.clear();
            if c.saida.read_line(&mut linha).ok()? == 0 {
                return None;
            }
            if let Ok(v) = serde_json::from_str::<Value>(&linha) {
                if v["id"] == json!(id) {
                    return Some(v);
                }
            }
        }
    }

    fn encerrar(&self) {
        let Ok(mut c) = self.controle.lock() else { return };
        let _ = writeln!(c.entrada, r#"{{"cmd":"shutdown"}}"#);
        let _ = c.entrada.flush();
        let limite = Instant::now() + Duration::from_secs(3);
        while c.filho.try_wait().ok().flatten().is_none() && Instant::now() < limite {
            std::thread::sleep(Duration::from_millis(50));
        }
        let _ = c.filho.kill();
    }

    /// Pede ao sidecar para autorizar um caminho escolhido no diálogo nativo.
    fn registrar(&self, tipo: &str, caminho: &Path) -> Option<Value> {
        let r = self.controlar(json!({"cmd": "register", "kind": tipo, "path": caminho.to_string_lossy()}))?;
        (r["ok"] == true).then(|| json!({"selection_id": r["selection_id"], "name": r["name"]}))
    }

    fn registrar_conversao(&self, caminhos: &[PathBuf]) -> Value {
        let itens: Vec<Value> = caminhos.iter().filter_map(|p| self.registrar("convert", p)).collect();
        if itens.is_empty() {
            return json!({"code": "selection_failed"});
        }
        let mut r = json!({
            "selection_ids": itens.iter().map(|i| i["selection_id"].clone()).collect::<Vec<_>>(),
            "names": itens.iter().map(|i| i["name"].clone()).collect::<Vec<_>>(),
        });
        if itens.len() < caminhos.len() {
            r["rejected"] = json!(caminhos.len() - itens.len());
        }
        r
    }

    /// Chamada autenticada à API loopback: o token só existe aqui.
    async fn chamar(&self, metodo: &str, caminho: &str, corpo: Option<Vec<u8>>) -> Option<reqwest::Response> {
        let mut r = self
            .http
            .request(reqwest::Method::from_bytes(metodo.as_bytes()).ok()?, format!("{}{}", self.origem, caminho))
            .bearer_auth(&self.token)
            .header("Origin", &self.origem);
        if let Some(c) = corpo {
            r = r.header("Content-Type", "application/json").body(c);
        }
        r.send().await.ok()
    }
}

fn ler_evento(saida: &mut BufReader<ChildStdout>) -> Result<Value, String> {
    let mut linha = String::new();
    saida.read_line(&mut linha).map_err(|e| e.to_string())?;
    serde_json::from_str(&linha).map_err(|_| "O servidor local não respondeu.".to_string())
}

/// Roda fora da thread da janela: a janela abre antes do sidecar ficar pronto e os comandos
/// esperam o backend (`backend()`). O sidecar avisa `already_running` antes de carregar o
/// servidor, então uma segunda instância sai sem nunca mostrar a janela.
fn iniciar(app: &AppHandle) -> Result<(), String> {
    // O sidecar é uma pasta (PyInstaller onedir) em `resources`: sem extrair 60 MB a cada abertura.
    let exe = std::env::current_exe()
        .map_err(|e| e.to_string())?
        .with_file_name("sidecar")
        .join("Contracto_sidecar.exe");
    let mut filho = sem_janela(&mut Command::new(exe))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("Não foi possível iniciar o servidor local: {e}"))?;
    let entrada = filho.stdin.take().ok_or("sidecar sem stdin")?;
    let mut saida = BufReader::new(filho.stdout.take().ok_or("sidecar sem stdout")?);
    let mut evento = ler_evento(&mut saida)?;
    if evento["event"] == "already_running" {
        std::process::exit(0);
    }
    if evento["event"] == "starting" {
        if let Some(janela) = app.get_webview_window("main") {
            let _ = janela.show();
        }
        evento = ler_evento(&mut saida)?;
    }
    let texto = |k: &str| evento[k].as_str().map(str::to_owned);
    let (Some(origem), Some(token)) = (texto("origin"), texto("token")) else {
        return Err("O servidor local não respondeu.".into());
    };
    let http = reqwest::Client::builder().no_proxy().timeout(Duration::from_secs(10)).build().map_err(|e| e.to_string())?;
    app.manage(Arc::new(Backend { origem, token, http, controle: Mutex::new(Controle { filho, entrada, saida, proximo: 0 }) }));
    Ok(())
}

/// Espera o backend ficar pronto (até 60 s).
async fn backend<M: Manager<tauri::Wry>>(m: &M) -> Option<Arc<Backend>> {
    for _ in 0..1200 {
        if let Some(b) = m.try_state::<Arc<Backend>>() {
            return Some(b.inner().clone());
        }
        tokio::time::sleep(Duration::from_millis(50)).await;
    }
    None
}

fn sem_servidor() -> Value {
    json!({"ok": false, "code": "local_server_unavailable"})
}

/// A página só chega aqui pelo protocolo do app (`tauri.localhost`) e sem capabilities
/// remotas; mesmo assim confere a origem, como o `ShellBridge._authorized`.
fn autorizada(webview: &Webview) -> bool {
    webview.label() == "main"
        && webview.url().ok().and_then(|u| u.host_str().map(|h| h == "tauri.localhost")).unwrap_or(false)
}

fn nao_autorizada() -> Value {
    json!({"ok": false, "code": "unauthorized_page"})
}

fn id_valido(id: &str) -> bool {
    id.len() == 32 && id.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn caminho_valido(p: &str) -> bool {
    p.strip_prefix("/api/v1/")
        .is_some_and(|r| !r.is_empty() && r.bytes().all(|b| b.is_ascii_alphanumeric() || b"/%._-".contains(&b)))
}

fn dialogo(webview: &Webview) -> FileDialogBuilder<tauri::Wry> {
    webview.app_handle().dialog().file().set_parent(&webview.window())
}

fn downloads(webview: &Webview) -> Option<PathBuf> {
    webview.app_handle().path().download_dir().ok()
}

fn abrir_no_so(caminho: &str) -> bool {
    Path::new(caminho).is_absolute()
        && sem_janela(&mut Command::new("explorer.exe")).arg(caminho).spawn().is_ok()
}

#[tauri::command]
async fn request(webview: Webview, method: String, path: String, payload: Option<Value>) -> Value {
    if !autorizada(&webview) {
        return json!({"status": 403, "data": {"code": "unauthorized_page"}});
    }
    if !["GET", "POST", "PUT", "DELETE"].contains(&method.as_str()) || !caminho_valido(&path) {
        return json!({"status": 400, "data": {"code": "invalid_request"}});
    }
    let corpo = if method == "POST" || method == "PUT" {
        match serde_json::to_vec(&payload.unwrap_or(Value::Null)) {
            Ok(c) if c.len() <= CORPO_MAX => Some(c),
            Ok(_) => return json!({"status": 413, "data": {"code": "body_too_large"}}),
            Err(_) => return json!({"status": 400, "data": {"code": "invalid_request"}}),
        }
    } else {
        None
    };
    let Some(b) = backend(&webview).await else {
        return json!({"status": 503, "data": {"code": "local_server_unavailable"}});
    };
    let resposta = match b.chamar(&method, &path, corpo).await {
        Some(r) => r,
        None => return json!({"status": 503, "data": {"code": "local_server_unavailable"}}),
    };
    let status = resposta.status().as_u16();
    match resposta.bytes().await.ok().and_then(|c| serde_json::from_slice::<Value>(&c).ok()) {
        Some(data) => json!({"status": status, "data": data}),
        None => json!({"status": 503, "data": {"code": "local_server_unavailable"}}),
    }
}

async fn selecionar(webview: &Webview, tipo: &str, caminho: Option<tauri_plugin_dialog::FilePath>) -> Value {
    let Some(caminho) = caminho else { return json!({"cancelled": true}) };
    if !autorizada(webview) {
        return nao_autorizada();
    }
    let Some(b) = backend(webview).await else { return sem_servidor() };
    caminho
        .into_path()
        .ok()
        .and_then(|p| b.registrar(tipo, &p))
        .unwrap_or_else(|| json!({"code": "selection_failed"}))
}

#[tauri::command]
async fn select_file(webview: Webview) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let p = dialogo(&webview).add_filter("Documentos (*.pdf;*.rtf)", &["pdf", "rtf"]).blocking_pick_file();
    selecionar(&webview, "file", p).await
}

#[tauri::command]
async fn select_output(webview: Webview) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let mut d = dialogo(&webview);
    if let Some(dir) = downloads(&webview) {
        d = d.set_directory(dir);
    }
    selecionar(&webview, "directory", d.blocking_pick_folder()).await
}

#[tauri::command]
async fn select_backup(webview: Webview) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let p = dialogo(&webview).add_filter("Backup Contracto (*.zip)", &["zip"]).blocking_pick_file();
    selecionar(&webview, "backup", p).await
}

#[tauri::command]
async fn select_documents(webview: Webview) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let Some(escolhidos) = dialogo(&webview)
        .add_filter("Documentos (*.pdf;*.rtf;*.doc;*.docx)", &["pdf", "rtf", "doc", "docx"])
        .blocking_pick_files()
    else {
        return json!({"cancelled": true});
    };
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let caminhos: Vec<PathBuf> = escolhidos.into_iter().filter_map(|p| p.into_path().ok()).collect();
    let Some(b) = backend(&webview).await else { return sem_servidor() };
    b.registrar_conversao(&caminhos)
}

#[tauri::command]
async fn import_profile(webview: Webview) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let Some(p) = dialogo(&webview).add_filter("Perfil Contracto (*.json)", &["json"]).blocking_pick_file() else {
        return json!({"cancelled": true});
    };
    let Ok(caminho) = p.into_path() else { return json!({"ok": false, "code": "import_failed"}) };
    let Some(b) = backend(&webview).await else { return sem_servidor() };
    b
        .controlar(json!({"cmd": "import_profile", "path": caminho.to_string_lossy()}))
        .filter(|r| r["ok"] == true)
        .map(|r| r["result"].clone())
        .unwrap_or_else(|| json!({"ok": false, "code": "import_failed"}))
}

#[tauri::command]
async fn export_profile(webview: Webview, nome: String) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    if nome.trim().is_empty() {
        return json!({"ok": false, "code": "invalid_request"});
    }
    let seguro: String = nome.chars().filter(|c| !"<>:\"/\\|?*".contains(*c)).collect();
    let mut d = dialogo(&webview)
        .add_filter("Perfil Contracto (*.json)", &["json"])
        .set_file_name(if seguro.is_empty() { "perfil.json".into() } else { format!("{seguro}.json") });
    if let Some(dir) = downloads(&webview) {
        d = d.set_directory(dir);
    }
    let Some(p) = d.blocking_save_file() else { return json!({"cancelled": true}) };
    let Ok(mut caminho) = p.into_path() else { return json!({"ok": false, "code": "export_failed"}) };
    if caminho.extension().map_or(true, |e| !e.eq_ignore_ascii_case("json")) {
        caminho.set_extension("json");
    }
    let Some(b) = backend(&webview).await else { return sem_servidor() };
    b
        .controlar(json!({"cmd": "export_profile", "nome": nome, "path": caminho.to_string_lossy()}))
        .filter(|r| r["ok"] == true)
        .map(|r| r["result"].clone())
        .unwrap_or_else(|| json!({"ok": false, "code": "export_failed"}))
}

#[tauri::command(rename_all = "snake_case")]
async fn open_result(webview: Webview, job_id: String) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    let Some(b) = backend(&webview).await else { return sem_servidor() };
    let caminho = b
        .controlar(json!({"cmd": "result_dir", "job_id": job_id}))
        .filter(|r| r["ok"] == true)
        .and_then(|r| r["path"].as_str().map(str::to_owned));
    match caminho {
        None => json!({"ok": false, "code": "result_unavailable"}),
        Some(p) if abrir_no_so(&p) => json!({"ok": true, "code": "opened"}),
        Some(_) => json!({"ok": false, "code": "open_failed"}),
    }
}

#[tauri::command(rename_all = "snake_case")]
async fn open_file(webview: Webview, file_id: String) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    if !id_valido(&file_id) {
        return json!({"ok": false, "code": "invalid_request"});
    }
    let Some(b) = backend(&webview).await else { return sem_servidor() };
    let caminho = b
        .controlar(json!({"cmd": "file_path", "file_id": file_id}))
        .filter(|r| r["ok"] == true)
        .and_then(|r| r["path"].as_str().map(str::to_owned));
    match caminho {
        None => json!({"ok": false, "code": "result_unavailable"}),
        Some(p) if !p.to_lowercase().ends_with(".pdf") => json!({"ok": false, "code": "unsupported_preview"}),
        Some(p) if abrir_no_so(&p) => json!({"ok": true, "code": "opened"}),
        Some(_) => json!({"ok": false, "code": "open_failed"}),
    }
}

#[tauri::command(rename_all = "snake_case")]
async fn get_file(webview: Webview, file_id: String) -> Value {
    if !autorizada(&webview) {
        return nao_autorizada();
    }
    if !id_valido(&file_id) {
        return json!({"ok": false, "code": "invalid_request"});
    }
    let indisponivel = || json!({"ok": false, "code": "file_unavailable"});
    let Some(b) = backend(&webview).await else { return indisponivel() };
    let Some(mut r) = b.chamar("GET", &format!("/api/v1/files/{file_id}"), None).await else { return indisponivel() };
    match r.status().as_u16() {
        200 => {}
        413 => return json!({"ok": false, "code": "preview_too_large"}),
        _ => return indisponivel(),
    }
    let mut bruto = Vec::new();
    while let Ok(Some(pedaco)) = r.chunk().await {
        bruto.extend_from_slice(&pedaco);
        if bruto.len() > ARQUIVO_MAX {
            return json!({"ok": false, "code": "preview_too_large"});
        }
    }
    json!({"ok": true, "base64": base64::engine::general_purpose::STANDARD.encode(bruto)})
}

/// Arrasto nativo: o WebView2 não dispara eventos HTML5 de arrasto com o handler nativo ligado, então
/// o shell repassa a posição (destaque da zona) e, ao soltar, registra os caminhos como seleção
/// `convert` e entrega só IDs à página, que confere se foi solto na zona.
fn ao_arrastar(window: &tauri::Window, evento: &DragDropEvent) {
    let app = window.app_handle();
    let Some(web) = app.get_webview_window("main") else { return };
    let escala = window.scale_factor().unwrap_or(1.0);
    let ponto = |p: &tauri::PhysicalPosition<f64>| format!("{},{}", p.x / escala, p.y / escala);
    let chamada = match evento {
        DragDropEvent::Enter { position, .. } | DragDropEvent::Over { position } => format!("arrastar({})", ponto(position)),
        DragDropEvent::Leave => "arrastar()".to_string(),
        DragDropEvent::Drop { paths, position } => {
            let Some(b) = app.try_state::<Arc<Backend>>() else { return };
            let r = b.registrar_conversao(&paths[..paths.len().min(20)]);
            format!("receberArrasto({r},{})", ponto(position))
        }
        _ => return,
    };
    let _ = web.eval(format!("window.ContractoConversao&&window.ContractoConversao.{chamada}"));
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            request, select_file, select_output, select_backup, select_documents,
            import_profile, export_profile, open_result, open_file, get_file
        ])
        .on_window_event(|window, evento| {
            if let WindowEvent::DragDrop(arrasto) = evento {
                ao_arrastar(window, arrasto);
            }
        })
        .setup(|app| {
            let titulo = format!("Contracto {}", app.package_info().version);
            // Oculta até o sidecar confirmar que não é segunda instância (ver `iniciar`).
            WebviewWindowBuilder::new(app, "main", WebviewUrl::App("index.html".into()))
                .title(titulo)
                .inner_size(1200.0, 850.0)
                .maximized(true)
                .visible(false)
                .build()?;
            let app = app.handle().clone();
            std::thread::spawn(move || {
                if let Err(erro) = iniciar(&app) {
                    app.dialog().message(&erro).kind(MessageDialogKind::Error).title("Contracto").blocking_show();
                    std::process::exit(1);
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("falha ao iniciar o Tauri");
    app.run(|app, evento| {
        if let RunEvent::Exit = evento {
            if let Some(b) = app.try_state::<Arc<Backend>>() {
                b.encerrar();
            }
        }
    });
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn allowlist_do_request_igual_ao_shellbridge() {
        assert!(caminho_valido("/api/v1/jobs/abc-1.2_%20"));
        for ruim in ["/api/v1/", "/api/v2/x", "/etc/passwd", "/api/v1/a?b=1", "/api/v1/../x y", "api/v1/x"] {
            assert!(!caminho_valido(ruim), "{ruim}");
        }
    }

    #[test]
    fn id_de_selecao_tem_32_hex_minusculos() {
        assert!(id_valido(&"a1".repeat(16)));
        assert!(!id_valido(&"A1".repeat(16)) && !id_valido("abc") && !id_valido(&"g".repeat(32)));
    }
}
