# Contrato nativo UI ↔ shell (pywebview hoje, Tauri v2 depois)

Fonte única: `frontend/js/api.js`. O resto do front só chama `ContractoAPI.*`; trocar o
shell é implementar estes comandos no novo shell. A API HTTP (`/api/v1/*`) não muda.

## Comandos nativos

Nome fixo, argumentos **nomeados** (Tauri `invoke(nome, args)`); sob pywebview viram
métodos de `pywebview.api` com os mesmos argumentos na ordem abaixo.

| Comando | Argumentos | Retorno | Regra de segurança |
|---|---|---|---|
| `request` | `method`, `path`, `payload?` | `{status, data}` | Só `GET/POST/PUT/DELETE`; `path` casa `^/api/v1/[A-Za-z0-9/%._-]+$`; corpo ≤ 1 MiB; token e `Origin` anexados **pelo shell**, nunca pela página; página não autorizada → `403 unauthorized_page` |
| `select_file` | — | `{selection_id, name}` \| `{cancelled}` \| `{code}` | Diálogo nativo; PDF/RTF; registra seleção `file` |
| `select_output` | — | idem | Diálogo de pasta; seleção `directory` |
| `select_backup` | — | idem | `.zip`; seleção `backup` |
| `select_documents` | — | `{selection_ids, names, rejected?}` | Multi-seleção PDF/RTF/DOC/DOCX; seleção `convert` |
| `import_profile` | — | `{ok, nome}` \| `{ok:false, code}` | `.json` ≤ 1 MiB, validado como perfil |
| `export_profile` | `nome` | `{ok, nome}` | Diálogo de salvar `.json` |
| `open_result` | `job_id` | `{ok, code}` | Só resultado concluído, por ID; abre a pasta |
| `open_file` | `file_id` | `{ok, code}` | Só PDF de seleção válida; leitor padrão |
| `get_file` | `file_id` | `{ok, base64}` \| `{ok:false, code}` | ≤ 20 MiB; só seleção `file` |

A página **nunca** recebe caminho, token nem porta. `selection_id`/`file_id` são
capacidades opacas (`app/api/selections.py`, TTL 1 h).

## Eventos shell → página

| Evento | Como | Payload |
|---|---|---|
| Ponte pronta | pywebview: `pywebviewready`; Tauri: `window.__TAURI__` presente no carregamento | — |
| Arquivos soltos na dropzone da Conversão | o shell chama `ContractoConversao.receberArrasto(r)` (pywebview: `evaluate_js`; Tauri: `webview.eval` após `onDragDropEvent`) | `{selection_ids, names, rejected?}` ou `{code}` |

O shell registra cada caminho solto como seleção `convert` (mesma validação do
`select_documents`) e entrega só IDs.

## Sidecar Python (`app/sidecar.py`)

Para o Tauri, o backend roda sem janela:

```
python app/sidecar.py        # em produção: Contracto_sidecar.exe (externalBin)
```

- **stdout**, 1ª linha: `{"event":"ready","origin":"http://127.0.0.1:<porta>","token":"…","version":"…"}`.
  O token só trafega por este pipe e fica na memória do processo Rust.
- **stdin** (canal de controle, só o processo pai): um JSON por linha.

| Comando | Efeito | Resposta |
|---|---|---|
| `{"id","cmd":"register","kind":"file|directory|convert|backup","path"}` | autoriza o caminho escolhido no diálogo nativo | `{"id","ok":true,"selection_id","name"}` |
| `{"id","cmd":"result_dir","job_id"}` | caminho da pasta de um job concluído (para abrir) | `{"id","ok":true,"path"}` |
| `{"id","cmd":"file_path","file_id"}` | caminho de um PDF autorizado (leitor padrão) | `{"id","ok":true,"path"}` |
| `{"cmd":"shutdown"}` ou EOF | encerra servidor e jobs | — |

Erros: `{"id","ok":false,"code":"invalid_request|unknown_command|failed"}` (sem caminho
nem dado do usuário). Cobertura: `tests/test_sidecar.py` (inclui processo real).

## Mapeamento Tauri previsto

| Comando | Implementação no Rust |
|---|---|
| `request` | `reqwest`/`hyper` para `origin` com `Authorization: Bearer` + `Origin`; mesma allowlist e limite do `ShellBridge.request` |
| `select_*`, `export_profile` | `tauri-plugin-dialog` → caminho → `register` no sidecar |
| `import_profile` | diálogo + leitura em Rust (≤ 1 MiB) → `POST /api/v1/profiles` |
| `open_result`, `open_file` | `result_dir`/`file_path` no sidecar → `tauri-plugin-opener` |
| `get_file` | `GET /api/v1/files/{id}` com limite de 20 MiB → base64 |
| arrasto | `onDragDropEvent` → `register(convert)` → `eval` de `receberArrasto` |

`capabilities` mínimas: `dialog:allow-open`, `dialog:allow-save`, `opener:allow-open-path`
(escopo só pelos caminhos devolvidos pelo sidecar), sidecar `externalBin` com **allowlist
de um** executável. CSP idêntica à do `index.html` atual.

## Testes que travam o contrato

- `tests/api_adapter.cjs` (via `test_form_state_js.py`): cada função de `ContractoAPI`
  chama o comando certo com os argumentos certos sob pywebview, Tauri e sem shell.
- `tests/test_webview_bridge.py`: allowlist pública da ponte atual.
- `tests/test_frontend_base.py::test_shell_isolado_no_adaptador`: nada fora do `api.js`
  conhece `pywebview`/`__TAURI__`.
