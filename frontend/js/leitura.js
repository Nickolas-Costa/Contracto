/* Leitura de documentos do cliente (modos Simples e Contrato).
 * Fluxo: anexar PDF/RTF/DOC/DOCX (os três últimos viram PDF) → o servidor lê o PDF e propõe valores para os campos do
 * formulário → o usuário confere cada valor ao lado do documento → só então os valores entram no formulário.
 * Nada é aplicado sem confirmação. O shell nativo entrega só IDs (nunca caminhos); os originais não são tocados. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const api = () => window.ContractoAPI, ui = () => window.ContractoUI, e1 = () => window.ContractoEtapa1;
  const online = () => window.ContractoApp?.pronto() || false;
  const MAXIMO = 20, LOTE_LEITURA = 5, LIMIAR_MARCADO = 0.8;
  const COMPARTILHADO = "compartilhado";
  // estado do arquivo: fila → convertendo → lendo → lido | erro
  let arquivos = [], escolhas = new Map(), ativo = -1, trabalhando = false, aberto = false, ligado = false;
  let raiz = null, frame = null, zonaRef = null, docAtual = -1;


  function el(tag, classe, texto) {
    const n = document.createElement(tag);
    if (classe) n.className = classe;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  // ---------- servidor ----------
  async function esperar(jobId) {
    for (let falhas = 0; falhas < 5;) {
      await new Promise(r => setTimeout(r, 600));
      try {
        const r = await api().getJob(jobId);
        if (r.status !== 200) { falhas++; continue; }
        if (["completed", "failed", "cancelled"].includes(r.data.status)) return r.data;
      } catch (_) { falhas++; }
    }
    return null;
  }

  async function ler(lote) {
    const ids = e1().perfilIds();
    for (let i = 0; i < lote.length; i += LOTE_LEITURA) {
      const parte = lote.slice(i, i + LOTE_LEITURA);
      parte.forEach(a => { a.estado = "lendo"; });
      desenhar();
      let r = null;
      try { r = await api().request("POST", "/api/v1/extract", {file_ids: parte.map(a => a.file_id), profile_ids: ids}); } catch (_) { /* tratado abaixo */ }
      parte.forEach((a, k) => {
        const dados = r?.status === 200 ? r.data.arquivos?.[k] : null;
        if (!dados) { Object.assign(a, {estado: "erro", mensagem: r?.data?.message || "Não foi possível ler este arquivo."}); return; }
        Object.assign(a, {estado: dados.erro ? "erro" : "lido", mensagem: dados.erro || "", paginas: dados.paginas, propostas: {participante: dados.participante, [COMPARTILHADO]: dados.compartilhado}});
        // Contrato com mais de um comprador: por padrão preenche todos de uma vez.
        a.pessoas = Math.max(1, ...a.propostas.participante.map(p => p.por_pessoa?.length || 0));
        a.papel = a.pessoas > 1 ? TODOS : a.propostas.participante.length >= a.propostas[COMPARTILHADO].length ? 0 : COMPARTILHADO;
      });
      if (ativo < 0) ativo = arquivos.findIndex(a => a.estado === "lido");
      desenhar();
    }
  }

  // Envia à conversão o que está na fila e lê o resultado; arquivos que chegam durante o processo entram na rodada seguinte.
  async function processar() {
    if (trabalhando || !online()) return;
    trabalhando = true;
    try {
      for (let lote = arquivos.filter(a => a.estado === "fila"); lote.length; lote = arquivos.filter(a => a.estado === "fila")) {
        lote.forEach(a => { a.estado = "convertendo"; });
        desenhar();
        let job = null, mensagem = "";
        try {
          const r = await api().request("POST", "/api/v1/jobs/intake", {file_ids: lote.map(a => a.selection_id)});
          if (r.status === 202) job = await esperar(r.data.job_id); else mensagem = r.data?.message || "";
        } catch (_) { mensagem = "Conexão interrompida."; }
        if (job?.status === "completed") {
          lote.forEach((a, i) => { a.file_id = job.files?.[i]?.file_id; if (!a.file_id) Object.assign(a, {estado: "erro", mensagem: "Sem resultado."}); });
          await ler(lote.filter(a => a.estado === "convertendo"));
        } else {
          mensagem = mensagem || job?.error?.message || "A conversão não terminou.";
          lote.forEach(a => Object.assign(a, {estado: "erro", mensagem}));
          ui().toast(mensagem, "error", 8000);
          desenhar();
        }
      }
    } finally { trabalhando = false; desenhar(); }
  }

  // `r` vem do seletor nativo ou do arrasto: só IDs autorizados e nomes.
  function adicionar(r) {
    const ids = r?.selection_ids || (r?.selection_id ? [r.selection_id] : []);
    const nomes = r?.names || (r?.name ? [r.name] : []);
    if (!ids.length) { ui().toast("Não foi possível anexar os arquivos.", "error"); return Promise.resolve(); }
    if (!aberto) { abrir(); if (!aberto) return Promise.resolve(); }
    ids.forEach((id, i) => {
      if (arquivos.length >= MAXIMO || arquivos.some(x => x.selection_id === id)) return;
      const nome = nomes[i] || "Documento";
      const ext = (nome.match(/\.(\w+)$/) || [])[1]?.toUpperCase() || "";
      arquivos.push({selection_id: id, nome, estado: "fila", convertido: ext && ext !== "PDF" ? ext : ""});
    });
    if (r.rejected) ui().toast(r.rejected + " arquivo(s) ignorado(s): use PDF, RTF, DOC ou DOCX.", "warning");
    desenhar();
    return processar();
  }

  async function escolherArquivos() {
    if (!online()) return;
    try { const r = await api().selectDocuments(); if (!r.cancelled) await adicionar(r); }
    catch (_) { ui().toast("Falha ao abrir o seletor.", "error"); }
  }

  // ---------- visualização ----------
  async function mostrarDocumento(i, pagina) {
    ativo = docAtual = i;
    desenharAbas();
    const a = arquivos[i], painel = $("leitura-doc");
    if (!a?.file_id || !painel) return;
    if (!a.url) {
      painel.replaceChildren(el("p", "hint", "Carregando documento…"));
      try {
        const r = await api().getFile(a.file_id);
        if (!r.ok) throw new Error();
        a.url = URL.createObjectURL(r.blob);
      } catch (_) { painel.replaceChildren(el("p", "hint", "Não foi possível mostrar este documento.")); return; }
      if (ativo !== i) return;
    }
    frame = el("iframe", "pdf-preview");
    frame.title = "Documento " + a.nome;
    frame.src = a.url + (pagina > 0 ? "#page=" + pagina : "");
    painel.replaceChildren(frame);
  }

  function desenharAbas() {
    const abas = $("leitura-abas");
    if (!abas) return;
    abas.replaceChildren();
    arquivos.forEach((a, i) => {
      if (a.estado !== "lido" && a.estado !== "erro") return;
      const b = el("button", "pag-aba", a.nome);
      b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-selected", String(i === ativo));
      b.addEventListener("click", () => mostrarDocumento(i));
      abas.append(b);
    });
  }

  // ---------- revisão ----------
  const TODOS = "todos";
  const chave = (a, k, campo) => a.selection_id + "|" + k + "|" + campo;
  const alvoDe = (p, k) => (p.escopo === "global" || k === COMPARTILHADO ? null : k);

  // Valor que a proposta tem para o destino k (participante, ou compartilhado); null = o documento não traz.
  function efetivo(p, k) {
    const n = typeof k === "number" ? k : 0;
    if (p.escopo === "global") return {valor: p.valor, aviso: p.aviso || "", pagina: p.pagina};
    if (p.por_pessoa) { const e = p.por_pessoa[n]; return e ? {valor: e.valor, aviso: e.aviso || "", pagina: e.pagina || p.pagina} : null; }
    // Sem separação por pessoa: o participante 2 começa com o 2º valor lido (ordem do documento).
    const valor = typeof k === "number" && k > 0 && p.ordenadas?.[k] ? p.ordenadas[k] : p.valor;
    return {valor, aviso: p.aviso || "", pagina: p.pagina};
  }

  // Linhas de revisão do arquivo para o destino escolhido; "todos" cobre cada comprador do contrato.
  function linhasDe(a) {
    if (a.estado !== "lido") return [];
    const destinos = a.papel === COMPARTILHADO ? [COMPARTILHADO] : a.papel === TODOS ? [...Array(a.pessoas).keys()] : [a.papel];
    const saida = [];
    destinos.forEach(k => {
      (a.propostas[k === COMPARTILHADO ? COMPARTILHADO : "participante"] || []).forEach(p => {
        if (a.papel === TODOS && k > 0 && (!p.por_pessoa || p.escopo === "global")) return;
        const e = efetivo(p, k);
        if (e) saida.push({p, k, e});
      });
    });
    return saida;
  }

  function linhaProposta(i, a, {p, k, e}) {
    const chv = chave(a, k, p.campo_id), par = alvoDe(p, k) + "|" + p.campo_id;
    if (!escolhas.has(chv)) {
      // Mesmo campo do mesmo destino lido em outro arquivo: só o primeiro vem marcado.
      const tomado = [...escolhas.values()].some(x => x.marcado && x.par === par && x.uid !== a.selection_id);
      escolhas.set(chv, {marcado: p.confianca >= LIMIAR_MARCADO && !e.aviso && !tomado, valor: e.valor, uid: a.selection_id, par});
    }
    const esc = escolhas.get(chv);
    const rotuloTexto = a.papel === TODOS && typeof k === "number" && p.escopo !== "global" ? p.rotulo + " — participante " + (k + 1) : p.rotulo;
    const linha = el("div", "leitura-linha");
    const marca = el("input"); marca.type = "checkbox"; marca.checked = esc.marcado;
    marca.setAttribute("aria-label", "Aplicar " + rotuloTexto);
    marca.addEventListener("change", () => { esc.marcado = marca.checked; rodape(); });
    const corpo = el("div", "leitura-corpo");
    const rotulo = el("label", "leitura-rotulo", rotuloTexto);
    const valor = el("input"); valor.type = "text"; valor.className = "leitura-valor"; valor.value = esc.valor; valor.id = "leitura-v-" + chv.replace(/\W/g, "_");
    rotulo.htmlFor = valor.id;
    valor.addEventListener("input", () => { esc.valor = valor.value; });
    valor.addEventListener("focus", () => mostrarDocumento(i, e.pagina));
    const origem = el("span", "hint", p.metodo === "acroform" ? "campo do formulário do PDF" : "pág. " + e.pagina);
    corpo.append(rotulo, valor, origem);
    if (e.aviso) corpo.append(el("span", "leitura-atual", e.aviso + " Confira antes de aplicar."));
    const atual = e1().valorAtual(alvoDe(p, k), p.campo_id);
    if (atual && atual !== e.valor) corpo.append(el("span", "leitura-atual", "Hoje no formulário: " + atual + " (será substituído)"));
    if (p.alternativas?.length && !p.por_pessoa) {
      const alt = el("span", "hint", "Outras leituras: ");
      p.alternativas.forEach(v => {
        const b = el("button", "btn-link leitura-alt", v); b.type = "button";
        b.addEventListener("click", () => { esc.valor = v; valor.value = v; });
        alt.append(b, " ");
      });
      corpo.append(alt);
    }
    linha.append(marca, corpo);
    return linha;
  }

  function seletorPapel(i, a) {
    const info = e1().participantesInfo();
    const sel = el("select", "leitura-papel"); sel.setAttribute("aria-label", "De quem são os dados de " + a.nome);
    if (a.pessoas > 1) sel.append(new Option("Todos os compradores do documento (" + a.pessoas + ")", TODOS));
    info.nomes.forEach((n, k) => sel.append(new Option("Participante " + (k + 1) + (n ? " — " + n : ""), String(k))));
    if (info.nomes.length < info.maximo) sel.append(new Option("Novo participante " + (info.nomes.length + 1), String(info.nomes.length)));
    sel.append(new Option("Dados compartilhados (vendedor, imóvel…)", COMPARTILHADO));
    sel.value = String(a.papel);
    sel.addEventListener("change", () => { a.papel = [COMPARTILHADO, TODOS].includes(sel.value) ? sel.value : Number(sel.value); desenhar(); });
    return sel;
  }

  function blocoArquivo(i, a) {
    const bloco = el("section", "leitura-arquivo");
    bloco.dataset.estado = a.estado;
    const topo = el("div", "leitura-arquivo-topo");
    const nome = el("strong", "", a.nome);
    const estado = el("span", "leitura-estado");
    if (["fila", "convertendo", "lendo"].includes(a.estado)) estado.append(Object.assign(el("span", "spinner"), {ariaHidden: "true"}), " ");
    const linhas = linhasDe(a);
    estado.append({fila: "Na fila", convertendo: a.convertido ? "Convertendo " + a.convertido + " para PDF…" : "Preparando…", lendo: "Lendo…", erro: a.mensagem || "Não foi possível ler.",
      lido: linhas.length ? linhas.length + " campo(s) encontrado(s)" + (a.convertido ? " · convertido de " + a.convertido : "") : "Nada reconhecido para este destino"}[a.estado]);
    const remover = el("button", "btn btn-subtle", "Remover"); remover.type = "button"; remover.prepend(ui().icone("trash"));
    remover.disabled = ["convertendo", "lendo"].includes(a.estado);
    remover.addEventListener("click", () => {
      if (a.url) URL.revokeObjectURL(a.url);
      [...escolhas.keys()].filter(k => k.startsWith(a.selection_id + "|")).forEach(k => escolhas.delete(k));
      arquivos.splice(i, 1);
      ativo = docAtual = -1; // o visualizador e as abas voltam ao primeiro arquivo que sobrou
      desenhar();
    });
    topo.append(nome, estado, remover);
    bloco.append(topo);
    if (a.estado === "lido") {
      const destino = el("label", "leitura-destino", "Dados de: "); destino.append(seletorPapel(i, a));
      bloco.append(destino);
      if (!linhas.length) bloco.append(el("p", "hint", "Se o documento for uma imagem escaneada, o texto não pode ser lido: preencha manualmente."));
      linhas.forEach(l => bloco.append(linhaProposta(i, a, l)));
    }
    return bloco;
  }

  function marcados() {
    const saida = [];
    arquivos.forEach(a => {
      linhasDe(a).forEach(({p, k}) => {
        const esc = escolhas.get(chave(a, k, p.campo_id));
        if (esc?.marcado && esc.valor.trim()) saida.push({participante: alvoDe(p, k), campo_id: p.campo_id, valor: esc.valor.trim()});
      });
    });
    return saida;
  }

  function rodape() {
    const n = marcados().length, botao = $("leitura-aplicar");
    if (!botao) return;
    botao.disabled = !n || trabalhando;
    botao.textContent = n ? "Aplicar " + n + " campo(s) ao formulário" : "Aplicar ao formulário";
    $("leitura-resumo").textContent = n ? "Você ainda poderá editar tudo no formulário." : "Marque os valores que quer aplicar.";
  }

  function aplicar() {
    const lista = marcados();
    if (!lista.length) return;
    // Em campos já preenchidos com outro valor a substituição é explícita na linha ("será substituído") e vale só se marcada.
    const n = e1().aplicarLeitura(lista);
    ui().fecharModal();
    mostrarDesfazer(true);
    ui().toast(n + " campo(s) preenchido(s). Confira o formulário.", "success");
  }

  // ---------- modal ----------
  function desenharIntro(corpo) {
    const caixa = el("div", "leitura-intro");
    caixa.append(el("h3", "", "Preencha o formulário a partir dos documentos"),
      el("p", "", "Solte aqui o RG, a CNH, o cartão CNPJ, comprovantes, a matrícula do imóvel ou formulários anteriores. O Contracto lê CPF, nome, datas, endereço, telefone, e-mail e outros dados e mostra cada um ao lado do documento para você conferir."),
      el("p", "hint", "Aceita PDF, RTF, DOC e DOCX (os três últimos viram PDF na hora, com o Word instalado). Tudo acontece neste computador e nada é aplicado sem a sua confirmação."));
    corpo.append(caixa);
  }

  function desenhar() {
    if (!raiz || !aberto) return;
    const esq = $("leitura-esq");
    const rolagem = esq?.scrollTop || 0;
    raiz.dataset.vazio = String(!arquivos.length);
    esq.replaceChildren();
    if (!arquivos.length) desenharIntro(esq);
    esq.append(zonaRef);
    arquivos.forEach((a, i) => esq.append(blocoArquivo(i, a)));
    esq.scrollTop = rolagem;
    desenharAbas();
    zonaRef.classList.toggle("dropzone-grande", !arquivos.length);
    if (ativo < 0) ativo = arquivos.findIndex(a => a.estado === "lido");
    if (ativo >= 0 && docAtual !== ativo && arquivos[ativo]?.estado === "lido") mostrarDocumento(ativo);
    else if (ativo < 0 && $("leitura-doc")) $("leitura-doc").replaceChildren(el("p", "hint", "O documento aparece aqui para você comparar com os dados lidos."));
    rodape();
  }

  function abrir() {
    if (aberto) return;
    if (!e1() || !e1().composto() || !e1().perfilIds().length) {
      ui().toast("Escolha primeiro o modelo que será preenchido.", "warning");
      document.getElementById("seletor-modelos")?.scrollIntoView({block: "center"});
      return;
    }
    aberto = true; docAtual = -1;
    ativo = arquivos.findIndex(a => a.estado === "lido");
    raiz = el("div", "leitura");
    const esq = el("div", "leitura-esq"); esq.id = "leitura-esq";
    const dir = el("div", "leitura-dir");
    const abas = el("div", "pag-abas"); abas.id = "leitura-abas"; abas.setAttribute("role", "tablist");
    const doc = el("div", "leitura-doc"); doc.id = "leitura-doc";
    doc.append(el("p", "hint", "O documento aparece aqui para você comparar com os dados lidos."));
    dir.append(abas, doc);
    const zona = el("div", "dropzone dropzone-compacta"); zona.id = "drop-leitura"; zona.tabIndex = 0; zona.setAttribute("role", "button");
    zona.setAttribute("aria-label", "Arraste documentos ou clique para escolher");
    zona.append(el("strong", "", "Arraste os documentos para cá ou clique para escolher"), el("span", "hint", "PDF, RTF, DOC ou DOCX"));
    zona.addEventListener("click", escolherArquivos);
    zona.addEventListener("keydown", ev => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); escolherArquivos(); } });
    ["dragenter", "dragover"].forEach(t => zona.addEventListener(t, ev => { ev.preventDefault(); zona.classList.add("arrastando"); }));
    ["dragleave", "drop"].forEach(t => zona.addEventListener(t, ev => { ev.preventDefault(); zona.classList.remove("arrastando"); }));
    const pe = el("div", "leitura-rodape");
    const resumo = el("span", "hint"); resumo.id = "leitura-resumo";
    const cancelar = el("button", "btn btn-secondary", "Fechar"); cancelar.type = "button"; cancelar.addEventListener("click", () => ui().fecharModal());
    const aplicarBtn = el("button", "btn btn-primary", "Aplicar ao formulário"); aplicarBtn.type = "button"; aplicarBtn.id = "leitura-aplicar"; aplicarBtn.addEventListener("click", aplicar);
    pe.append(resumo, cancelar, aplicarBtn);
    raiz.append(esq, dir, pe);
    zonaRef = zona;
    ui().abrirModal("Leitura de documentos", raiz, [], () => { aberto = false; raiz = null; zonaRef = null; });
    document.querySelector(".modal")?.classList.add("modal-leitura");
    desenhar();
  }

  // ---------- faixa de entrada, arrasto e desfazer ----------
  function mostrarDesfazer(sim) { const b = $("leitura-desfazer"); if (b) b.hidden = !sim; }

  const emInicio = () => !$("tela-inicio").hidden;
  function arrastar(x) { $("leitura-banner")?.classList.toggle("arrastando", x !== undefined && emInicio()); }
  function receberArrasto(r) { arrastar(); if (r && emInicio()) adicionar(r); }
  function limpar() { arquivos.forEach(a => { if (a.url) URL.revokeObjectURL(a.url); }); arquivos = []; escolhas.clear(); ativo = docAtual = -1; mostrarDesfazer(false); }

  function ligar() {
    if (ligado) return;
    ligado = true;
    $("btn-ler-documentos")?.addEventListener("click", abrir);
    $("leitura-desfazer")?.addEventListener("click", () => { e1().desfazerLeitura(); mostrarDesfazer(false); ui().toast("Leitura desfeita.", "info"); });
  }

  // O shell nativo chama window.ContractoArrasto; aqui se decide quem recebe, pela tela aberta.
  const alvo = () => $("tela-conversao") && !$("tela-conversao").hidden ? window.ContractoConversao : (emInicio() ? window.ContractoLeitura : null);
  window.ContractoArrasto = {
    arrastar: (x, y) => { window.ContractoConversao?.arrastar(); window.ContractoLeitura?.arrastar(); alvo()?.arrastar(x, y); },
    receberArrasto: (r, x, y) => alvo()?.receberArrasto(r, x, y),
  };
  window.ContractoLeitura = {ligar, abrir, adicionar, arrastar, receberArrasto, limpar,
    prontos: () => arquivos.filter(a => a.estado === "lido").map(a => ({nome: a.nome, file_id: a.file_id}))};
})();
