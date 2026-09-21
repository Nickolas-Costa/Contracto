/* Ponte com o processo nativo (pywebview) ou aviso em navegador comum. */
(function () {
  "use strict";

  function disponivel() {
    return !!(window.pywebview && window.pywebview.api);
  }

  async function request(method, path, payload) {
    if (!disponivel()) {
      return { status: 503, data: { code: "sem_ponte", message: "Abra pelo aplicativo." } };
    }
    try {
      return await window.pywebview.api.request(method, path, payload);
    } catch (erro) {
      return { status: 503, data: { code: "ponte_falhou" } };
    }
  }

  async function selectOutput() {
    if (!disponivel()) return { code: "sem_ponte" };
    return window.pywebview.api.select_output();
  }

  async function selectFile() {
    if (!disponivel()) return { code: "sem_ponte" };
    return window.pywebview.api.select_file();
  }

  async function openResult(jobId) {
    if (!disponivel()) return { ok: false, code: "sem_ponte" };
    return window.pywebview.api.open_result(jobId);
  }

  async function getFile(fileId) {
    if (!disponivel()) return { ok: false, code: "sem_ponte" };
    const r = await window.pywebview.api.get_file(fileId);
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

  async function selectAttachment() {
    if (!disponivel()) return { code: "sem_ponte" };
    return window.pywebview.api.select_file();
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
    request,
    selectOutput,
    selectFile,
    selectAttachment,
    openResult,
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
    duplicateProfile
  };
})();
