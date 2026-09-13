/* Toasts, modal e navegação entre telas/etapas. */
(function () {
  "use strict";

  const ICONES = { success: "✓", info: "i", warning: "!", error: "✕" };

  function toast(message, type) {
    type = type || "success";
    const caixa = document.getElementById("toasts");
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.setAttribute("role", "status");
    const ins = document.createElement("span");
    ins.className = "insignia";
    ins.textContent = ICONES[type] || ICONES.info;
    const txt = document.createElement("span");
    txt.textContent = message;
    el.append(ins, txt);
    caixa.append(el);
    const timer = setTimeout(() => el.remove(), 4000);
    el.tabIndex = 0;
    el.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") { clearTimeout(timer); el.remove(); }
    });
    return el;
  }

  let ultimoFoco = null;

  function abrirModal(titulo, corpoHTML, botoes) {
    ultimoFoco = document.activeElement;
    const overlay = document.getElementById("overlay");
    document.getElementById("modal-titulo").textContent = titulo;
    const corpo = document.getElementById("modal-corpo");
    corpo.innerHTML = "";
    if (typeof corpoHTML === "string") {
      const p = document.createElement("p");
      p.textContent = corpoHTML;
      corpo.append(p);
    } else if (corpoHTML) {
      corpo.append(corpoHTML);
    }
    const acoes = document.getElementById("modal-acoes");
    acoes.innerHTML = "";
    (botoes || [{ texto: "Entendi", primario: true }]).forEach((b) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = b.texto;
      btn.className = "btn " + (b.primario ? "btn-primary" : "btn-secondary");
      btn.addEventListener("click", () => { fecharModal(); if (b.aoClicar) b.aoClicar(); });
      acoes.append(btn);
    });
    overlay.hidden = false;
    const primeiro = acoes.querySelector("button");
    if (primeiro) primeiro.focus();
  }

  function fecharModal() {
    document.getElementById("overlay").hidden = true;
    if (ultimoFoco && document.contains(ultimoFoco)) ultimoFoco.focus();
    ultimoFoco = null;
  }

  document.getElementById("overlay").addEventListener("click", (ev) => {
    if (ev.target.id === "overlay") fecharModal();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !document.getElementById("overlay").hidden) fecharModal();
  });

  function mostrarTela(nome) {
    ["inicio", "etapa2", "perfis", "config"].forEach((t) => {
      document.getElementById("tela-" + t).hidden = t !== nome;
    });
    document.querySelectorAll("[data-tela]").forEach((b) => {
      if (b.dataset.tela === nome) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
  }

  function irEtapa(n) {
    document.querySelectorAll("#stepper [data-etapa]").forEach((b) => {
      if (Number(b.dataset.etapa) === n) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    mostrarTela(n === 1 ? "inicio" : "etapa2");
  }

  document.querySelectorAll("[data-tela]").forEach((b) => {
    b.addEventListener("click", () => mostrarTela(b.dataset.tela));
  });
  document.querySelectorAll("#stepper [data-etapa]").forEach((b) => {
    b.addEventListener("click", () => irEtapa(Number(b.dataset.etapa)));
  });

  function aplicarTema(nome) {
    document.documentElement.dataset.theme = nome === "dark" ? "dark" : "light";
  }

  function aplicarTemaInicial() {
    let tema = "light";
    try {
      const salvo = localStorage.getItem("contracto-tema");
      if (salvo === "light" || salvo === "dark") {
        tema = salvo;
      } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        tema = "dark";
      }
    } catch (e) { /* sem armazenamento: segue o claro */ }
    aplicarTema(tema);
    const sel = document.getElementById("cfg-tema");
    if (sel) {
      sel.value = tema;
      if (!sel.dataset.ligado) {
        sel.dataset.ligado = "1";
        sel.addEventListener("change", () => {
          aplicarTema(sel.value);
          try { localStorage.setItem("contracto-tema", sel.value); } catch (e) { /* sem armazenamento */ }
        });
      }
    }
  }

  window.ContractoUI = { toast, abrirModal, fecharModal, mostrarTela, irEtapa, aplicarTema, aplicarTemaInicial };
})();
