/* Toasts, modal e navegação entre telas/etapas. */
(function () {
  "use strict";

  const ICONES = { success: "✓", info: "i", warning: "!", error: "✕" };
  // Foco local: um fragmento na URL alteraria a origem exata autorizada da ponte.
  document.getElementById("pular-conteudo").addEventListener("click",()=>{
    const main=document.getElementById("telas");main.focus();main.scrollIntoView({block:"start"});
  });

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
  let aoFechar = null;

  function abrirModal(titulo, corpoHTML, botoes, cleanup) {
    if (!document.getElementById("overlay").hidden) fecharModal();
    ultimoFoco = document.activeElement;
    aoFechar = cleanup || null;
    const overlay = document.getElementById("overlay");
    const tituloEl = document.getElementById("modal-titulo");
    tituloEl.textContent = titulo;
    if (!tituloEl.parentElement.classList.contains("modal-titulo-faixa")) {
      const faixa = document.createElement("div");
      faixa.className = "modal-titulo-faixa";
      tituloEl.replaceWith(faixa);
      faixa.append(tituloEl);
      const fechar = document.createElement("button");
      fechar.type = "button";
      fechar.className = "modal-fechar";
      fechar.textContent = "✕";
      fechar.setAttribute("aria-label", "Fechar diálogo");
      fechar.addEventListener("click", fecharModal);
      faixa.append(fechar);
    }
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
    document.getElementById("app").inert = true;
    const primeiro = acoes.querySelector("button");
    if (primeiro) primeiro.focus();
  }

  function fecharModal() {
    document.getElementById("overlay").hidden = true;
    document.getElementById("app").inert = false;
    document.getElementById("modal-corpo").replaceChildren();
    document.querySelector(".modal")?.classList.remove("modal-viewer");
    if (aoFechar) { aoFechar(); aoFechar = null; }
    if (ultimoFoco && document.contains(ultimoFoco)) ultimoFoco.focus();
    ultimoFoco = null;
  }

  document.getElementById("overlay").addEventListener("click", (ev) => {
    if (ev.target.id === "overlay") fecharModal();
  });
  document.addEventListener("keydown", (ev) => {
    const overlay = document.getElementById("overlay");
    if (overlay.hidden) return;
    if (ev.key === "Escape") { ev.preventDefault(); fecharModal(); }
    if (ev.key === "Tab") {
      const focusable = [...overlay.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), iframe, [tabindex="0"]')].filter(el => !el.hidden);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (ev.shiftKey && (document.activeElement === first || !overlay.contains(document.activeElement))) { ev.preventDefault(); last?.focus(); }
      else if (!ev.shiftKey && (document.activeElement === last || !overlay.contains(document.activeElement))) { ev.preventDefault(); first?.focus(); }
    }
  });

  function mostrarTela(nome) {
    if (!["inicio", "etapa2", "perfis", "config"].includes(nome)) return;
    document.getElementById("stepper").hidden = !["inicio", "etapa2"].includes(nome);
    ["inicio", "etapa2", "perfis", "config"].forEach((t) => {
      document.getElementById("tela-" + t).hidden = t !== nome;
    });
    document.querySelectorAll("[data-tela]").forEach((b) => {
      if (b.dataset.tela === nome || (nome === "etapa2" && b.dataset.tela === "inicio")) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
    const etapa = nome === "inicio" ? 1 : nome === "etapa2" ? 3 : 0;
    document.querySelectorAll("#stepper [data-etapa]").forEach(b => {
      if (etapa && Number(b.dataset.etapa) === etapa) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    window.scrollTo(0, 0);
  }

  function irEtapa(n) {
    if (n === 1) { mostrarTela("inicio"); return; }
    if (n === 2) {
      if (window.ContractoEtapa1 && window.ContractoEtapa1.revisar) window.ContractoEtapa1.revisar();
      return;
    }
    if (n === 3) { mostrarTela("etapa2"); return; }
    if (n === 4) {
      mostrarTela("etapa2");
      const btn = document.getElementById("btn-finalizar");
      if (btn) { btn.focus(); btn.scrollIntoView({ block: "center" }); }
    }
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
