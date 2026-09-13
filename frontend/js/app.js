/* Inicialização: aguarda DOM e ponte, com estado persistente de conexão. */
(function () {
  "use strict";

  var iniciado = false;
  var timerFalha = null;

  function setConexao(estado, mensagem) {
    var el = document.getElementById("conexao");
    if (el) {
      el.textContent = mensagem;
      el.dataset.estado = estado;
    }
    ["btn-gerar", "btn-finalizar", "btn-pasta"].forEach(function (id) {
      var btn = document.getElementById(id);
      if (btn) btn.disabled = estado !== "pronto";
    });
  }

  function marcarFalha() {
    setConexao("falha", "Falha ao conectar. ");
    var el = document.getElementById("conexao");
    if (el && !document.getElementById("btn-tentar")) {
      var btn = document.createElement("button");
      btn.id = "btn-tentar";
      btn.type = "button";
      btn.textContent = "Tentar novamente";
      btn.addEventListener("click", function () {
        btn.remove();
        iniciar();
      });
      el.append(btn);
    }
  }

  async function verificar() {
    try {
      const r = await window.ContractoAPI.request("GET", "/api/v1/health");
      if (r.status === 200) {
        if (timerFalha) { clearTimeout(timerFalha); timerFalha = null; }
        setConexao("pronto", "Pronto.");
        return true;
      }
    } catch (e) { /* segue para falha abaixo */ }
    marcarFalha();
    return false;
  }

  function iniciar() {
    if (iniciado) return;
    setConexao("conectando", "Conectando…");
    if (window.ContractoAPI.disponivel()) {
      finalizarArranque();
      return;
    }
    const aoPronto = () => {
      window.removeEventListener("pywebviewready", aoPronto);
      finalizarArranque();
    };
    window.addEventListener("pywebviewready", aoPronto);
    if (timerFalha) clearTimeout(timerFalha);
    timerFalha = setTimeout(() => {
      window.removeEventListener("pywebviewready", aoPronto);
      marcarFalha();
    }, 15000);
    window.ContractoUI.aplicarTemaInicial();
  }

  async function finalizarArranque() {
    if (iniciado) return;
    iniciado = true;
    if (timerFalha) { clearTimeout(timerFalha); timerFalha = null; }
    window.ContractoUI.aplicarTemaInicial();
    const ok = await verificar();
    if (ok) window.ContractoEtapa1.ligar();
  }

  window.ContractoApp = { iniciar, verificar, reiniciado: () => { iniciado = false; } };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
