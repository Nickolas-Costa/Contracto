/* Bootstrap recuperável; ligação dos eventos é independente da conexão. */
(function () {
  "use strict";
  let ligado = false, conectando = null, timer = null, retryTimer = null, pronto = false;
  let tentativas = 0, erroDeConexaoExibido = false;
  function conexao(ok, mensagem) {
    pronto = ok;
    const el = document.getElementById("conexao");
    if (el) {
      el.textContent = mensagem;
      el.dataset.estado = ok ? "pronto" : "falha";
    }
    window.ContractoEtapa1?.atualizar();
    window.ContractoEtapa2?.atualizar();
  }
  function mostrarCapacidades(caps) {
    // Tela Config ("Recursos deste computador"): resumo humano, sem caminhos locais.
    const el = document.getElementById("lista-capacidades");
    if (!el || !caps) return;
    const partes = ["PDF simples: " + (caps.pdf === false ? "indisponível" : "disponível"),
      "Conversão Word (RTF): " + (caps.word ? "disponível" : "indisponível"),
      "PDF/A (Ghostscript): " + (caps.ghostscript ? "disponível" : "indisponível")];
    el.textContent = partes.join(" · ");
  }
  function agendarReconexao() {
    clearTimeout(retryTimer);
    // O shell e a API são criados no mesmo processo. Uma espera progressiva
    // cobre a corrida de boot sem gerar loops síncronos ou dezenas de toasts.
    const espera = Math.min(1000 * (2 ** Math.min(tentativas, 4)), 10000);
    tentativas += 1;
    retryTimer = setTimeout(() => {
      retryTimer = null;
      iniciar();
    }, espera);
  }
  function falhaConexao() {
    conexao(false, "Indisponível");
    // O boot normal não é erro para o usuário. Só informe se a API continuar
    // indisponível após as tentativas iniciais, e uma única vez.
    if (tentativas >= 3 && !erroDeConexaoExibido) {
      erroDeConexaoExibido = true;
      window.ContractoUI?.toast("Não foi possível conectar ao serviço local. Feche e abra o Contracto novamente.", "error", 0);
    }
    agendarReconexao();
  }
  async function finalizarArranque() {
    if (conectando) return conectando;
    clearTimeout(timer);
    conectando = (async () => {
      try {
        const r = await window.ContractoAPI.request("GET", "/api/v1/health");
        if (r.status !== 200) { falhaConexao(); return false; }
        // Item 8: diagnóstico WebView2 amigável
        if (typeof navigator !== "undefined" && navigator.userAgent?.includes("Windows") && window.chrome?.webview) {
          try {
            const diag = await window.ContractoAPI.request("GET", "/api/v1/diagnostics/webview2");
            if (diag.status === 200 && diag.data && !diag.data.available) {
              const msg = diag.data.message + " <a href='" + diag.data.install_url + "' target='_blank'>Baixar WebView2</a>";
              window.ContractoUI.toast(msg, "warning", 0);
            }
          } catch (_) { /* silencioso */ }
        }
        try {
          const caps = await window.ContractoAPI.request("GET", "/api/v1/capabilities");
          if (caps.status === 200 && window.ContractoEtapa2) window.ContractoEtapa2.capacidades(caps.data);
          if (caps.status === 200) mostrarCapacidades(caps.data);
        } catch (_) { /* sem capacidades: PDF/A segue desativado por segurança */ }
        // A conexão foi confirmada. A partir daqui, falhas da interface não
        // podem reiniciar a ponte HTTP nem se passar por erro de backend.
        conexao(true, "Pronto.");
        tentativas = 0;
        erroDeConexaoExibido = false;
        clearTimeout(retryTimer);
        retryTimer = null;
        try {
          if (!ligado) {
            ligado = true;
            window.ContractoEtapa2.ligar();
            window.ContractoEtapa1.ligar();
          } else {
            await window.ContractoEtapa1.reconectar();
            window.ContractoEtapa2.reconectar();
          }
        } catch (_) {
          window.ContractoUI?.toast("A interface não pôde ser inicializada corretamente. Feche e abra o Contracto novamente.", "error", 0);
          return false;
        }
        return true;
      } catch (_) { falhaConexao(); return false; }
    })();
    try { return await conectando; } finally { conectando = null; }
  }
  function iniciar() {
    window.ContractoUI.aplicarTemaInicial();
    if (conectando) return conectando;
    clearTimeout(retryTimer);
    retryTimer = null;
    conexao(false, "Conectando…");
    clearTimeout(timer);
    if (window.ContractoAPI.disponivel()) return finalizarArranque();

    const interval = setInterval(() => {
      if (window.ContractoAPI.disponivel()) {
        clearInterval(interval);
        clearTimeout(timer);
        finalizarArranque();
      }
    }, 50);

    timer = setTimeout(() => {
      clearInterval(interval);
      falhaConexao();
    }, 15000);
  }
  window.ContractoApp = { iniciar, verificar: finalizarArranque, pronto: () => pronto, falha: falhaConexao };
  window.addEventListener("pywebviewready", () => {
    finalizarArranque();
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
