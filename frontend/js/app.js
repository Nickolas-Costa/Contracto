/* Bootstrap recuperável; ligação dos eventos é independente da conexão. */
(function () {
  "use strict";
  let ligado = false, conectando = null, timer = null, pronto = false;
  function conexao(ok, mensagem) {
    pronto = ok;
    const el = document.getElementById("conexao");
    el.textContent = mensagem;
    el.dataset.estado = ok ? "pronto" : "falha";
    window.ContractoEtapa1?.atualizar();
    window.ContractoEtapa2?.atualizar();
  }
  function falha() {
    conexao(false, "Sem conexão. ");
    const btn = document.createElement("button");
    btn.id = "btn-tentar"; btn.type = "button"; btn.textContent = "Tentar novamente";
    btn.addEventListener("click", iniciar);
    document.getElementById("conexao").append(btn);
  }
  async function finalizarArranque() {
    if (conectando) return conectando;
    clearTimeout(timer);
    conectando = (async () => {
      try {
        const r = await window.ContractoAPI.request("GET", "/api/v1/health");
        if (r.status !== 200) { falha(); return false; }
        conexao(true, "Pronto.");
        if (!ligado) {
          ligado = true;
          window.ContractoEtapa2.ligar();
          window.ContractoEtapa1.ligar();
        } else {
          await window.ContractoEtapa1.reconectar();
          window.ContractoEtapa2.reconectar();
        }
        return true;
      } catch (_) { falha(); return false; }
    })();
    try { return await conectando; } finally { conectando = null; }
  }
  function iniciar() {
    window.ContractoUI.aplicarTemaInicial();
    if (conectando) return conectando;
    conexao(false, "Conectando…");
    clearTimeout(timer);
    if (window.ContractoAPI.disponivel()) return finalizarArranque();
    timer = setTimeout(falha, 15000);
  }
  window.ContractoApp = { iniciar, verificar: finalizarArranque, pronto: () => pronto, falha };
  window.addEventListener("pywebviewready", () => {
    if (document.readyState !== "loading") finalizarArranque();
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
