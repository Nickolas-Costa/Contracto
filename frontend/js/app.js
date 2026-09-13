/* Inicialização: tema, etapa 1 e aviso fora do app. */
(function () {
  "use strict";

  function iniciar() {
    const tema = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    window.ContractoUI.aplicarTema(tema);
    const sel = document.getElementById("cfg-tema");
    if (sel) {
      sel.value = tema;
      sel.addEventListener("change", () => window.ContractoUI.aplicarTema(sel.value));
    }
    if (!window.ContractoAPI.disponivel()) {
      window.ContractoUI.toast("Abra pelo aplicativo: esta página precisa da ponte local.", "warning");
      return;
    }
    window.ContractoEtapa1.ligar();
    window.ContractoEtapa2.ligar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
