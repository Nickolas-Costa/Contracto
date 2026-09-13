/* Inicialização: tema, etapa 1 e aviso fora do app. */
(function () {
  "use strict";

  function iniciar() {
    let tema = "light";
    try {
      const salvo = localStorage.getItem("contracto-tema");
      if (salvo === "light" || salvo === "dark") {
        tema = salvo;
      } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        tema = "dark";
      }
    } catch (e) { /* sem armazenamento: segue o claro */ }
    window.ContractoUI.aplicarTema(tema);
    const sel = document.getElementById("cfg-tema");
    if (sel) {
      sel.value = tema;
      sel.addEventListener("change", () => {
        window.ContractoUI.aplicarTema(sel.value);
        try { localStorage.setItem("contracto-tema", sel.value); } catch (e) { /* sem armazenamento */ }
      });
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
