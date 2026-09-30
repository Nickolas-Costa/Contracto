/* Toasts, modal e navegação entre telas/etapas. */
(function () {
  "use strict";

  const ICONES = { success: "✓", info: "i", warning: "!", error: "✕" };
  // Foco local: um fragmento na URL alteraria a origem exata autorizada da ponte.
  document.getElementById("pular-conteudo").addEventListener("click",()=>{
    const main=document.getElementById("telas");main.scrollIntoView({block:"start"});
    const primeiro=document.querySelector("#tela-inicio:not([hidden]) button:not(:disabled), #tela-inicio:not([hidden]) input, #tela-inicio:not([hidden]) select");
    if(primeiro)primeiro.focus({preventScroll:true});
  });

  // Fase 1 (DESIGN.md §7): temporário some em 6s com pausa sob hover/foco;
  // erro que exige correção permanece no contexto (duration 0 = persistente).
  // Máximo 3 visíveis: o mais antigo temporário é dispensado.
  function toast(message, type, duration) {
    type = type || "success";
    const caixa = document.getElementById("toasts");
    caixa.querySelectorAll(".toast").forEach(el => {
      if (caixa.children.length > 2 && !el.dataset.persistente) el.remove();
    });
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
    // duration 0 = persistente (dispensa com Escape); padrão 6s.
    const ms = duration === undefined ? 6000 : duration;
    let timer = null, restante = ms, inicio = 0;
    const remover = () => { if (timer) clearTimeout(timer); timer = null; el.remove(); };
    const pausar = () => { if (!timer) return; clearTimeout(timer); timer = null; restante -= Date.now() - inicio; };
    const retomar = () => {
      if (ms === 0 || timer || restante <= 0) return;
      inicio = Date.now();
      timer = setTimeout(remover, restante);
    };
    if (ms === 0) {
      el.dataset.persistente = "1";
    } else {
      retomar();
      el.addEventListener("mouseenter", pausar);
      el.addEventListener("mouseleave", retomar);
      el.addEventListener("focusin", pausar);
      el.addEventListener("focusout", retomar);
    }
    el.tabIndex = 0;
    el.addEventListener("keydown", (ev) => {
      // Se há modal aberto, o Escape pertence a ele (elemento mais interno);
      // não dispensa o toast atrás do overlay.
      if (ev.key === "Escape" && !document.getElementById("overlay").hidden) return;
      if (ev.key === "Escape") remover();
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
    // Convenção (DESIGN.md §7): o foco inicial vai ao primeiro botão, que
    // deve ser a opção segura — confirmações destrutivas listam "Cancelar" /
    // "Voltar" antes da ação irreversível. Modais nunca empilham: abrir um
    // novo fecha o anterior (linha acima).
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

  function etapaLiberada(n) {
    if (n <= 1) return true;
    if (n === 2) return !!(window.ContractoEtapa1 && window.ContractoEtapa1.composto());
    if (n >= 3) return !!(window.ContractoEtapa1 && window.ContractoEtapa1.composto()) && !!(window.ContractoEtapa2 && window.ContractoEtapa2.temBase());
    return true;
  }
  function etapaAtiva(nome) {
    return nome === "inicio" ? 1 : nome === "conferir" ? 2 : nome === "etapa2" ? 3 : 0;
  }
  function sincronizarStepper() {
    document.querySelectorAll("#stepper [data-etapa]").forEach(b => {
      const n = Number(b.dataset.etapa);
      const locked = !etapaLiberada(n);
      b.disabled = locked;
      b.title = locked ? "Conclua a etapa anterior para avançar" : "";
    });
  }
  function mostrarTela(nome) {
    if (!["inicio", "conferir", "etapa2", "perfis", "config", "conversao"].includes(nome)) return;
    document.getElementById("stepper").hidden = !["inicio", "conferir", "etapa2"].includes(nome);
    ["inicio", "conferir", "etapa2", "perfis", "config", "conversao"].forEach((t) => {
      const el = document.getElementById("tela-" + t);
      if (el) el.hidden = t !== nome;
    });
    document.querySelectorAll("[data-tela]").forEach((b) => {
      if (b.dataset.tela === nome || (["conferir", "etapa2"].includes(nome) && b.dataset.tela === "inicio")) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
    const etapa = etapaAtiva(nome);
    document.querySelectorAll("#stepper [data-etapa]").forEach(b => {
      if (etapa && Number(b.dataset.etapa) === etapa) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    if (nome === "perfis" && window.ContractoEtapa1?.carregarTelaPerfis) {
      window.ContractoEtapa1.carregarTelaPerfis();
    }
    if (nome === "inicio" || nome === "config" || nome === "conversao") {
      window.ContractoEtapa2?.atualizar();
    }
    if (nome === "config") {
      cfgCarregarRascunho();
    }
    window.scrollTo(0, 0);
  }

  function irEtapa(n) {
    if (n === 1) { mostrarTela("inicio"); return; }
    if (!etapaLiberada(n)) {
      if (n === 2) toast("Preencha o formulário e selecione modelos compatíveis antes de conferir.", "warning");
      else toast("Gere os documentos primeiro para poder concluir o trabalho.", "warning");
      mostrarTela("inicio");
      return;
    }
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
      const avancado = window.ContractoEtapa1 && window.ContractoEtapa1.modo() !== "simples";
      const alvo = avancado ? document.getElementById("btn-finalizar") : null;
      if (alvo && !alvo.hidden && !alvo.disabled) {
        alvo.focus({ preventScroll: true });
        alvo.scrollIntoView({ block: "nearest" });
      } else {
        document.getElementById("tela-etapa2")?.scrollIntoView({ block: "start" });
      }
      return;
    }
  }

  document.querySelectorAll("[data-tela]").forEach((b) => {
    b.addEventListener("click", () => mostrarTela(b.dataset.tela));
  });
  document.querySelectorAll("#stepper [data-etapa]").forEach((b) => {
    b.addEventListener("click", () => irEtapa(Number(b.dataset.etapa)));
  });

  document.addEventListener("DOMContentLoaded", sincronizarStepper);

  const TEXTO_AJUDA = [
    "1. Escolha o modo (Simples para vários formulários, Contrato para processo completo) e o modelo.",
    "2. Preencha os dados de cada participante e confira o resumo antes de gerar.",
    "3. Em Concluir, revise os PDFs, anexe comprovantes se preciso, escolha PDF ou PDF/A-2b e finalize."
  ];
  function ajudaModal() {
    const wrap = document.createElement("div");
    TEXTO_AJUDA.forEach(t => { const p = document.createElement("p"); p.textContent = t; wrap.append(p); });
    // Foto 6: a seção Sobre saiu da Config; a versão vive aqui.
    const versao = document.createElement("p");
    versao.className = "hint";
    versao.id = "versao-app";
    versao.textContent = "Consultando versão…";
    wrap.append(versao);
    abrirModal("Ajuda — Contracto em 3 passos", wrap, [{ texto: "Entendi, começar!", primario: true }]);
    if (window.ContractoAPI) {
      window.ContractoAPI.request("GET", "/api/v1/health").then(r => {
        const el = document.getElementById("versao-app");
        if (!el) return;
        if (r.status === 200 && r.data && r.data.version) {
          el.textContent = "Contracto v" + r.data.version + " — 100% local, sem telemetria. Termos de Uso, Privacidade e Avisos de Terceiros acompanham o aplicativo em docs/.";
        } else {
          el.textContent = "100% local, sem telemetria. Termos de Uso, Privacidade e Avisos de Terceiros acompanham o aplicativo em docs/.";
        }
      }).catch(() => {});
    }
  }
  async function boasVindasSePreciso() {
    try {
      const r = await window.ContractoAPI.getSettings();
      if (r.status === 200 && r.data && r.data.primeira_execucao) {
        ajudaModal();
        await window.ContractoAPI.updateSettings({ primeira_execucao: false });
      }
    } catch (_) { /* sem ponte: não bloqueia o arranque */ }
  }
  const btnAjuda = document.getElementById("btn-ajuda-topo");
  if (btnAjuda && !btnAjuda.dataset.ligado) {
    btnAjuda.dataset.ligado = "1";
    btnAjuda.addEventListener("click", ajudaModal);
  }
  document.addEventListener("DOMContentLoaded", () => { setTimeout(boasVindasSePreciso, 800); });

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

  // Fase 3 — paridade com o legado (settings_frame.py): "Padrão do Sistema"
  // resolve via matchMedia e acompanha trocas do SO enquanto ativo.
  function resolverTema(pref) {
    if (pref === "dark") return "dark";
    if (pref === "light") return "light";
    try {
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
    } catch (_) {}
    return "light";
  }

  function aplicarTemaInicial() {
    // Arranque: aplica SOMENTE os valores já salvos; edição na tela Config
    // usa rascunho e só persiste/aplica em "Salvar configurações".
    let pref = "sistema";
    let corSalva = null;
    try {
      const salvo = localStorage.getItem("contracto-tema");
      if (salvo === "light" || salvo === "dark" || salvo === "sistema") {
        pref = salvo;
      } else if (salvo === "system") {
        pref = "sistema"; // valor legado do backend
      }
      const cor = localStorage.getItem("contracto-cor");
      if (cor && /^#[0-9A-Fa-f]{6}$/.test(cor)) corSalva = cor;
    } catch (e) { /* sem armazenamento: segue o claro */ }
    aplicarTema(resolverTema(pref));
    if (window.matchMedia) {
      try {
        const mq = window.matchMedia("(prefers-color-scheme: dark)");
        const acompanhar = (e) => {
          let atual = "sistema";
          try { atual = localStorage.getItem("contracto-tema") || "sistema"; } catch (_) {}
          if (atual === "sistema" || atual === "system") aplicarTema(e.matches ? "dark" : "light");
        };
        if (mq.addEventListener) mq.addEventListener("change", acompanhar);
        else if (mq.addListener) mq.addListener(acompanhar);
      } catch (_) {}
    }
    const sel = document.getElementById("cfg-tema");
    if (sel) sel.value = (pref === "light" || pref === "dark") ? pref : "sistema";
    const input = document.getElementById("cfg-cor");
    const texto = document.getElementById("cfg-cor-texto");
    if (input && corSalva) input.value = corSalva;
    if (texto && corSalva) texto.value = corSalva;
  }

  function cfgLerSalvos() {
    let tema = "sistema", cor = "#005CA9";
    try {
      const t = localStorage.getItem("contracto-tema");
      if (t === "light" || t === "dark") tema = t;
      else if (t === "sistema" || t === "system" || t === null) tema = "sistema";
      const c = localStorage.getItem("contracto-cor");
      if (c && /^#[0-9A-Fa-f]{6}$/.test(c)) cor = c;
    } catch (e) { /* sem armazenamento */ }
    return { tema, cor };
  }

  // Paridade com o legado (settings_frame.py: CORES_PREDEFINIDAS).
  const CORES_PREDEFINIDAS = [
    ["#1E6FB3", "Azul Institucional"], ["#00234E", "Azul Royal"],
    ["#00838F", "Ciano"], ["#2E7D32", "Verde"],
    ["#6A1B9A", "Roxo"], ["#AD1457", "Rosa"],
    ["#E65100", "Laranja"], ["#455A64", "Cinza Azulado"]
  ];

  function marcarSwatch(cor) {
    document.querySelectorAll("#cfg-cores .color-swatch").forEach(b => {
      b.setAttribute("aria-pressed", b.dataset.cor === cor ? "true" : "false");
    });
  }

  function renderizarSwatches() {
    const host = document.getElementById("cfg-cores");
    if (!host || host.dataset.ligado) return;
    host.dataset.ligado = "1";
    CORES_PREDEFINIDAS.forEach(([hex, nome]) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "color-swatch";
      b.dataset.cor = hex;
      b.title = nome;
      b.setAttribute("aria-label", "Cor " + nome);
      b.setAttribute("aria-pressed", "false");
      b.style.background = hex;
      b.addEventListener("click", () => {
        // Rascunho: só preenche os campos; aplicar acontece em Salvar.
        const cor = document.getElementById("cfg-cor");
        const texto = document.getElementById("cfg-cor-texto");
        if (cor) cor.value = hex;
        if (texto) texto.value = hex;
        marcarSwatch(hex);
      });
      host.append(b);
    });
  }

  // Larguras proporcionais: 760 / 1080 / 1400 (deltas 320/320).
  const LARGURAS = { "Pequeno": 760, "Médio": 1080, "Medio": 1080, "Grande": 1400 };
  function aplicarLargura(tamanho) {
    const px = LARGURAS[tamanho];
    if (px) document.documentElement.style.setProperty("--largura-quadros", px + "px");
    else document.documentElement.style.removeProperty("--largura-quadros");
  }

  async function cfgCarregarRascunho() {
    const salvos = cfgLerSalvos();
    const sel = document.getElementById("cfg-tema");
    if (sel) sel.value = salvos.tema;
    const cor = document.getElementById("cfg-cor");
    if (cor) cor.value = salvos.cor;
    const texto = document.getElementById("cfg-cor-texto");
    if (texto) texto.value = salvos.cor;
    marcarSwatch(salvos.cor);
    if (window.ContractoAPI && window.ContractoAPI.getSettings) {
      try {
        const r = await window.ContractoAPI.getSettings();
        if (r.status === 200 && r.data) {
          const local = document.getElementById("cfg-local-padrao");
          if (local && typeof r.data.local_padrao === "string") local.value = r.data.local_padrao;
          const tam = document.getElementById("cfg-tamanho");
          if (tam && typeof r.data.tamanho_quadros === "string") tam.value = r.data.tamanho_quadros;
          const fmt = document.getElementById("cfg-formato");
          if (fmt && typeof r.data.formato_saida === "string") fmt.value = r.data.formato_saida;
          aplicarLargura(r.data.tamanho_quadros);
        }
      } catch (_) { /* mantém o que está digitado */ }
    }
  }

  async function cfgSalvar() {
    const sel = document.getElementById("cfg-tema");
    const cor = document.getElementById("cfg-cor");
    const texto = document.getElementById("cfg-cor-texto");
    const local = document.getElementById("cfg-local-padrao");
    const tam = document.getElementById("cfg-tamanho");
    const fmt = document.getElementById("cfg-formato");
    const corFinal = (/^#[0-9A-Fa-f]{6}$/.test((texto && texto.value) || "") ? texto.value : (cor && cor.value)) || "#005CA9";
    const prefFinal = (sel && (sel.value === "dark" || sel.value === "light")) ? sel.value : "sistema";
    try {
      localStorage.setItem("contracto-tema", prefFinal);
      localStorage.setItem("contracto-cor", corFinal);
    } catch (e) { /* sem armazenamento */ }
    aplicarTema(resolverTema(prefFinal));
    aplicarCor(corFinal);
    desenharFundoSenoidal();
    if (cor) cor.value = corFinal;
    if (texto) texto.value = corFinal;
    try {
      const payload = {
        local_padrao: ((local && local.value) || "").trim(),
        aparencia: prefFinal === "sistema" ? "system" : prefFinal, // canônico do backend
        cor_destaque: corFinal
      };
      if (tam && tam.value) payload.tamanho_quadros = tam.value;
      if (fmt && fmt.value) payload.formato_saida = fmt.value;
      aplicarLargura(tam && tam.value);
      const r = await window.ContractoAPI.updateSettings(payload);
      if (r.status !== 200) toast("Tema e cor salvos; preferências do computador não foram persistidas.", "warning");
      else toast("Configurações salvas.", "success");
    } catch (_) {
      toast("Tema e cor salvos; sem conexão para persistir as preferências.", "warning");
    }
  }

  function cfgDescartar() {
    cfgCarregarRascunho();
    toast("Alterações descartadas.", "info");
  }

  async function cfgReparo() {
    try {
      const r = await window.ContractoAPI.request("POST", "/api/v1/system/repair");
      if (r.status === 200) toast("Diagnóstico e reparo concluídos.", "success");
      else toast("Não foi possível concluir o reparo.", "error");
    } catch (_) {
      toast("Sem conexão para executar o reparo.", "error");
    }
  }

  async function cfgRestaurar() {
    const wrap = document.createElement("div");
    const p = document.createElement("p");
    p.textContent = "Restaurar tema, cor, local, largura dos quadros e formato para os padrões? Esta ação não apaga perfis nem documentos.";
    wrap.append(p);
    abrirModal("Restaurar padrões", wrap, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Restaurar padrões", primario: true, aoClicar: async () => {
          try {
            const r = await window.ContractoAPI.restoreSettings();
            if (r.status !== 200) { toast("Não foi possível restaurar os padrões.", "error"); return; }
            const pref = (r.data.aparencia === "dark" || r.data.aparencia === "light") ? r.data.aparencia : "sistema";
            try { localStorage.setItem("contracto-tema", pref); localStorage.setItem("contracto-cor", r.data.cor_destaque || "#005CA9"); } catch (_) {}
            aplicarTema(resolverTema(pref));
            aplicarCor(r.data.cor_destaque || "#005CA9");
            aplicarLargura(r.data.tamanho_quadros);
            await cfgCarregarRascunho();
            toast("Padrões restaurados.", "success");
          } catch (_) { toast("Sem conexão para restaurar os padrões.", "error"); }
        }
      }
    ]);
  }
  function ligarConfig() {
    renderizarSwatches();
    // Aplica a largura salva logo no arranque (sem exigir abrir Config).
    if (window.ContractoAPI && window.ContractoAPI.getSettings) {
      window.ContractoAPI.getSettings()
        .then(r => { if (r.status === 200 && r.data) aplicarLargura(r.data.tamanho_quadros); })
        .catch(() => {});
    }
    const salvar = document.getElementById("btn-cfg-salvar");
    if (salvar && !salvar.dataset.ligado) {
      salvar.dataset.ligado = "1";
      salvar.addEventListener("click", cfgSalvar);
    }
    const descartar = document.getElementById("btn-cfg-descartar");
    if (descartar && !descartar.dataset.ligado) {
      descartar.dataset.ligado = "1";
      descartar.addEventListener("click", cfgDescartar);
    }
    const restaurar = document.getElementById("btn-cfg-restaurar");
    if (restaurar && !restaurar.dataset.ligado) {
      restaurar.dataset.ligado = "1";
      restaurar.addEventListener("click", cfgRestaurar);
    }
    const reparo = document.getElementById("btn-cfg-reparo");
    if (reparo && !reparo.dataset.ligado) {
      reparo.dataset.ligado = "1";
      reparo.addEventListener("click", cfgReparo);
    }
  }
  document.addEventListener("DOMContentLoaded", ligarConfig);

  function desenharFundoSenoidal() {
    // Sonda WebView2 real: prefers-reduced-motion pode vir True mesmo sem
    // animação na página. As ondas são ESTÁTICAS (sem animação contínua),
    // então movimento reduzido não as remove — só alto contraste genuíno.
    try {
      if (window.matchMedia && window.matchMedia("(forced-colors: active)").matches) {
        document.querySelector(".bg-waves-container")?.remove();
        return;
      }
    } catch (_) {}
    let container = document.querySelector(".bg-waves-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "bg-waves-container";
      container.setAttribute("aria-hidden", "true");
      container.innerHTML = '<div class="bg-glow-orb bg-glow-top"></div><div class="bg-glow-orb bg-glow-bottom"></div><svg class="bg-waves-svg" id="bg-waves-svg" preserveAspectRatio="none" viewBox="0 0 1440 400"></svg>';
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
        path.setAttribute("stroke-opacity", isDark ? "0.55" : "0.45");
      } else {
        // Secundárias acompanham o acento com bem menos opacidade.
        path.setAttribute("stroke", corPrimaria);
        path.setAttribute("stroke-width", "1");
        path.setAttribute("stroke-opacity", isDark ? "0.14" : "0.22");
      }

      svg.appendChild(path);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    desenharFundoSenoidal();
    window.addEventListener("resize", desenharFundoSenoidal);
  });

  window.ContractoUI = { toast, abrirModal, fecharModal, mostrarTela, irEtapa, sincronizarStepper, aplicarTema, aplicarTemaInicial, desenharFundoSenoidal };
})();
