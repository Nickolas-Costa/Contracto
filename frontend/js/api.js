/* Único ponto que conhece o shell nativo (pywebview hoje, Tauri v2 depois).
 *
 * Contrato nativo (docs/TAURI_CONTRATO.md): comandos com nome fixo e argumentos
 * nomeados — request, select_file, select_output, select_backup,
 * select_documents, import_profile, export_profile, open_result, open_file,
 * get_file. Sob pywebview viram métodos de `pywebview.api` (argumentos
 * posicionais, na ordem declarada); sob Tauri, `invoke(nome, argumentos)`.
 */
(function () {
  "use strict";

  const tauri = () => window.__TAURI__?.core?.invoke;

  function disponivel() {
    return !!(tauri() || (window.pywebview && window.pywebview.api));
  }

  async function nativo(nome, args = {}) {
    if (tauri()) return tauri()(nome, args);
    const api = window.pywebview?.api;
    if (!api) return { ok: false, code: "sem_ponte" };
    if (typeof api[nome] !== "function") return { ok: false, code: "unsupported" };
    return api[nome](...Object.values(args));
  }

  // Ponte pronta no shell nativo. pywebview dispara "pywebviewready"; um shell
  // sem evento (ex.: Tauri) chama no arranque. Mantém o resto do app ignorante
  // do shell: componentes não referenciam pywebview/Tauri diretamente.
  function aoPronto(callback) {
    if (window.__TAURI__) { callback(); return; }
    window.addEventListener("pywebviewready", callback);
  }

  // Shell Windows com WebView2 — único ponto que conhece o host para decidir o
  // diagnóstico do runtime WebView2. Sob Tauri (WebView2 embutido) retorna false.
  function ehShellWebView2() {
    return typeof navigator !== "undefined" && !!navigator.userAgent?.includes("Windows") && !!(window.chrome && window.chrome.webview);
  }

  async function request(method, path, payload) {
    if (!disponivel()) {
      return { status: 503, data: { code: "sem_ponte", message: "Abra pelo aplicativo." } };
    }
    try {
      return await nativo("request", { method, path, payload });
    } catch (erro) {
      return { status: 503, data: { code: "ponte_falhou" } };
    }
  }

  const selectOutput = () => nativo("select_output");
  const selectFile = () => nativo("select_file");
  const openResult = (jobId) => nativo("open_result", { job_id: jobId });
  const openFile = (fileId) => nativo("open_file", { file_id: fileId });

  async function getFile(fileId) {
    const r = await nativo("get_file", { file_id: fileId });
    if (!r || !r.ok || !r.base64) return { ok: false, code: (r && r.code) || "file_unavailable" };
    try {
      const bin = atob(r.base64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return { ok: true, blob: new Blob([bytes], { type: "application/pdf" }) };
    } catch (_) {
      return { ok: false, code: "file_unavailable" };
    }
  }

  async function getJob(jobId) {
    return request("GET", "/api/v1/jobs/" + encodeURIComponent(jobId));
  }

  async function listJobs() {
    return request("GET", "/api/v1/jobs");
  }

  async function getCapabilities() {
    const r = await request("GET", "/api/v1/capabilities");
    if (r.status === 200 && r.data) return r.data;
    return { pdf: true, word: false, ghostscript: false };
  }

  const selectAttachment = () => nativo("select_file");
  const selectBackup = () => nativo("select_backup");
  const importProfile = () => nativo("import_profile");
  const exportProfile = (nome) => nativo("export_profile", { nome });
  const selectDocuments = () => nativo("select_documents");

  async function activateProfile(nome) {
    return request("POST", "/api/v1/profiles/active", { nome });
  }

  async function backupSystem() {
    return request("POST", "/api/v1/system/backup", {});
  }

  async function restoreSystem(selectionId) {
    return request("POST", "/api/v1/system/restore", { selection_id: selectionId });
  }

  async function restoreSettings() {
    return request("POST", "/api/v1/settings/restore", {});
  }

  async function getSettings() {
    return request("GET", "/api/v1/settings");
  }

  async function updateSettings(dados) {
    return request("POST", "/api/v1/settings", dados);
  }

  async function getProfiles() {
    return request("GET", "/api/v1/profiles");
  }

  async function createProfile(dados) {
    return request("POST", "/api/v1/profiles", dados);
  }

  async function updateProfile(nome, dados) {
    return request("PUT", "/api/v1/profiles/" + encodeURIComponent(nome), dados);
  }

  async function deleteProfile(nome) {
    return request("DELETE", "/api/v1/profiles/" + encodeURIComponent(nome));
  }

  async function duplicateProfile(nome, novoNome) {
    return request("POST", "/api/v1/profiles/" + encodeURIComponent(nome) + "/duplicate", { novo_nome: novoNome });
  }

  window.ContractoAPI = {
    disponivel,
    aoPronto,
    ehShellWebView2,
    request,
    selectOutput,
    selectFile,
    selectAttachment,
    openResult,
    openFile,
    getFile,
    getJob,
    listJobs,
    getCapabilities,
    getSettings,
    updateSettings,
    getProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    duplicateProfile,
    selectBackup,
    importProfile,
    exportProfile,
    selectDocuments,
    activateProfile,
    backupSystem,
    restoreSystem,
    restoreSettings
  };
})();
