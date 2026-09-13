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

  async function openResult(jobId) {
    if (!disponivel()) return { ok: false, code: "sem_ponte" };
    return window.pywebview.api.open_result(jobId);
  }

  async function getFile(fileId) {
    if (!disponivel()) return { ok: false, code: "sem_ponte" };
    return window.pywebview.api.get_file(fileId);
  }

  window.ContractoAPI = { disponivel, request, selectOutput, openResult, getFile };
})();
