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
    return window.pywebview.api.get_file(fileId);
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
    openResult,
    getFile,
    getSettings,
    updateSettings,
    getProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    duplicateProfile
  };
})();
