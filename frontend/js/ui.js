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
    if (!["inicio", "conferir", "etapa2", "perfis", "config"].includes(nome)) return;
    document.getElementById("stepper").hidden = !["inicio", "conferir", "etapa2"].includes(nome);
    ["inicio", "conferir", "etapa2", "perfis", "config"].forEach((t) => {
      const el = document.getElementById("tela-" + t);
      if (el) el.hidden = t !== nome;
    });
    document.querySelectorAll("[data-tela]").forEach((b) => {
      if (b.dataset.tela === nome || (["conferir", "etapa2"].includes(nome) && b.dataset.tela === "inicio")) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
    const etapa = nome === "inicio" ? 1 : nome === "conferir" ? 2 : nome === "etapa2" ? 3 : 0;
    document.querySelectorAll("#stepper [data-etapa]").forEach(b => {
      if (etapa && Number(b.dataset.etapa) === etapa) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    window.scrollTo(0, 0);
  }

  function irEtapa(n) {
    if (n === 1) { mostrarTela("inicio"); return; }
    if (n === 2) {
      if (window.ContractoEtapa1 && window.ContractoEtapa1.conferir) {
        window.ContractoEtapa1.conferir();
      } else {
        mostrarTela("conferir");
      }
      return;
    }
    if (n === 3) {
      if (window.ContractoEtapa1 && !window.ContractoEtapa1.composto()) {
        toast("Preencha o formulário e confira os dados antes de avançar.", "warning");
        mostrarTela("inicio");
        return;
      }
      mostrarTela("etapa2");
      return;
    }
    if (n === 4) {
      if (window.ContractoEtapa1 && !window.ContractoEtapa1.composto()) {
        toast("Gere os documentos primeiro para poder concluir o trabalho.", "warning");
        mostrarTela("inicio");
        return;
      }
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

  const indicadorGlobal = document.getElementById("indicador-fila-global");
  if (indicadorGlobal) {
    indicadorGlobal.addEventListener("click", () => {
      mostrarTela("etapa2");
    });
  }

  function aplicarTema(nome) {
    document.documentElement.dataset.theme = nome === "dark" ? "dark" : "light";
  }

  function aplicarCor(cor) {
    document.documentElement.style.setProperty("--c-primary", cor);
    const r = parseInt(cor.slice(1, 3), 16), g = parseInt(cor.slice(3, 5), 16), b = parseInt(cor.slice(5, 7), 16);
    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    const onPrimary = luminance > 0.5 ? "#172435" : "#FFFFFF";
    const light = `color-mix(in srgb, ${cor} 15%, ${luminance > 0.5 ? "#FFFFFF" : "#0F1419"})`;
    const hover = `color-mix(in srgb, ${cor} 85%, ${luminance > 0.5 ? "#FFFFFF" : "#0F1419"})`;
    document.documentElement.style.setProperty("--c-on-primary", onPrimary);
    document.documentElement.style.setProperty("--c-primary-light", light);
    document.documentElement.style.setProperty("--c-primary-hover", hover);
    document.body.style.backgroundImage = "none";
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
    // Cor de destaque salva
    try {
      const corSalva = localStorage.getItem("contracto-cor");
      if (corSalva && /^#[0-9A-Fa-f]{6}$/.test(corSalva)) {
        aplicarCor(corSalva);
        const input = document.getElementById("cfg-cor");
        const texto = document.getElementById("cfg-cor-texto");
        if (input) input.value = corSalva;
        if (texto) texto.value = corSalva;
      }
    } catch (e) { /* sem armazenamento */ }
    const corInput = document.getElementById("cfg-cor");
    const corTexto = document.getElementById("cfg-cor-texto");
    if (corInput && !corInput.dataset.ligado) {
      corInput.dataset.ligado = "1";
      corInput.addEventListener("input", () => {
        aplicarCor(corInput.value);
        if (corTexto) corTexto.value = corInput.value;
        try { localStorage.setItem("contracto-cor", corInput.value); } catch (e) { /* sem armazenamento */ }
      });
    }
    if (corTexto && !corTexto.dataset.ligado) {
      corTexto.dataset.ligado = "1";
      corTexto.addEventListener("input", () => {
        if (/^#[0-9A-Fa-f]{6}$/.test(corTexto.value)) {
          aplicarCor(corTexto.value);
          if (corInput) corInput.value = corTexto.value;
          try { localStorage.setItem("contracto-cor", corTexto.value); } catch (e) { /* sem armazenamento */ }
        }
      });
    }
  }

  function desenharFundoSenoidal() {
    let container = document.querySelector(".bg-waves-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "bg-waves-container";
      container.setAttribute("aria-hidden", "true");
      container.innerHTML = '<div class="bg-glow-orb bg-glow-top"></div><div class="bg-glow-orb bg-glow-bottom"></div><svg class="bg-waves-svg" id="bg-waves-svg" preserveAspectRatio="none" viewBox="0 0 1440 900"></svg>';
      document.body.prepend(container);
    }
    const svg = document.getElementById("bg-waves-svg");
    if (!svg) return;
    svg.innerHTML = "";
    const largura = 1440;
    const altura = 900;
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const corPrimaria = getComputedStyle(document.documentElement).getPropertyValue("--c-primary").trim() || "#1455A0";

    const destaqueIndices = new Set([6, 17, 26]);
    const numLinhas = 30;
    const steps = 60;

    for (let i = 0; i < numLinhas; i++) {
      const yOffset = (i - 5) * (altura / 18.0);
      let pathData = "";

      for (let s = 0; s <= steps; s++) {
        const x = (s / steps) * largura;
        const y = yOffset + (x * 0.28) + Math.sin(s * 0.14 + i * 0.22) * (altura * 0.05);
        pathData += (s === 0 ? "M " + x.toFixed(1) + " " + y.toFixed(1) : " L " + x.toFixed(1) + " " + y.toFixed(1));
      }

      const path = document.createElementNS("http" + "://www.w3.org/2000/svg", "path");
      path.setAttribute("d", pathData);
      path.setAttribute("fill", "none");

      if (destaqueIndices.has(i)) {
        path.setAttribute("stroke", corPrimaria);
        path.setAttribute("stroke-width", "2");
        path.setAttribute("stroke-opacity", isDark ? "0.6" : "0.45");
      } else {
        const strokeColor = isDark ? "#2B2E38" : "#DFE4EE";
        path.setAttribute("stroke", strokeColor);
        path.setAttribute("stroke-width", "1");
        path.setAttribute("stroke-opacity", isDark ? "0.35" : "0.5");
      }

      svg.appendChild(path);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    desenharFundoSenoidal();
    window.addEventListener("resize", desenharFundoSenoidal);
  });

  window.ContractoUI = { toast, abrirModal, fecharModal, mostrarTela, irEtapa, aplicarTema, aplicarTemaInicial, desenharFundoSenoidal };
})();
