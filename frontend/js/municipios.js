/* Municípios do ITBI (prefeitura, comarca, texto da isenção): lista editável nas Configurações e
 * pergunta inicial na primeira execução. Os dados vivem em contracto_config.json (municipios_itbi). */
(function () {
  "use strict";
  const ui = () => window.ContractoUI, api = () => window.ContractoAPI;

  function campo(rotulo, controle, classe) {
    const wrap = document.createElement("div");
    wrap.className = "field" + (classe ? " " + classe : "");
    const label = document.createElement("label");
    label.textContent = rotulo;
    controle.id = controle.id || "mun-" + Math.random().toString(36).slice(2, 9);
    label.htmlFor = controle.id;
    wrap.append(label, controle);
    return wrap;
  }
  function entrada(classe, valor, placeholder, longo) {
    const el = document.createElement(longo ? "textarea" : "input");
    el.className = classe + (longo ? " field-textarea" : "");
    if (longo) el.rows = 4; else el.type = "text";
    el.value = valor || ""; el.placeholder = placeholder || ""; el.autocomplete = "off";
    return el;
  }

  function linha(item, padrao, host) {
    const box = document.createElement("fieldset");
    box.className = "mun-item";
    const legenda = document.createElement("legend");
    legenda.textContent = item.prefeitura || "Novo município";
    const grade = document.createElement("div");
    grade.className = "field-grid";
    const pref = entrada("mun-prefeitura", item.prefeitura, "Ex: CAMOCIM-CE");
    pref.addEventListener("input", () => { legenda.textContent = pref.value.trim() || "Novo município"; });
    grade.append(
      campo("Prefeitura (município)", pref),
      campo("Comarca do cartório", entrada("mun-comarca", item.comarca, "Ex: CAMOCIM-CE")),
      campo("Texto da isenção (lei do município)", entrada("mun-isencao", item.texto_isencao, "Ex: Conforme Lei Municipal nº ...", true), "field-wide"));
    const rodape = document.createElement("div");
    rodape.className = "mun-rodape";
    const radio = document.createElement("input");
    radio.type = "radio"; radio.name = "cfg-mun-padrao"; radio.className = "mun-padrao";
    radio.checked = !!item.prefeitura && item.prefeitura === padrao;
    const rotuloRadio = document.createElement("label");
    rotuloRadio.className = "checkbox-inline";
    rotuloRadio.append(radio, " Município padrão");
    const remover = document.createElement("button");
    remover.type = "button"; remover.className = "btn btn-subtle";
    remover.textContent = "Remover"; remover.prepend(ui().icone("trash"));
    remover.addEventListener("click", () => box.remove());
    rodape.append(rotuloRadio, remover);
    box.append(legenda, grade, rodape);
    return box;
  }

  // Desenha a lista em `host`; `padrao` é a prefeitura marcada como padrão.
  function montar(host, lista, padrao) {
    if (!host) return;
    host.replaceChildren();
    (lista || []).forEach(item => host.append(linha(item, padrao, host)));
    if (!host.querySelector(".mun-padrao:checked")) host.querySelector(".mun-padrao")?.click();
  }
  function adicionar(host) {
    const nova = linha({}, "", host);
    host.append(nova);
    if (!host.querySelector(".mun-padrao:checked")) nova.querySelector(".mun-padrao").checked = true;
    nova.querySelector(".mun-prefeitura").focus();
  }
  // Lê a lista da tela; linhas sem prefeitura ficam de fora (o servidor também as descarta).
  function ler(host) {
    const municipios = [], vistos = new Set();
    let padrao = "";
    host.querySelectorAll(".mun-item").forEach(box => {
      const prefeitura = box.querySelector(".mun-prefeitura").value.trim();
      if (!prefeitura || vistos.has(prefeitura.toLowerCase())) return;
      vistos.add(prefeitura.toLowerCase());
      municipios.push({prefeitura, comarca: box.querySelector(".mun-comarca").value.trim(), texto_isencao: box.querySelector(".mun-isencao").value.trim()});
      if (box.querySelector(".mun-padrao").checked) padrao = prefeitura;
    });
    return {municipios, padrao: padrao || municipios[0]?.prefeitura || ""};
  }

  // Primeira execução: local e município do ITBI (cada cidade tem a sua lei de isenção). `depois` segue o fluxo.
  function configuracaoInicial(config, depois) {
    const itens = (config.municipios_itbi || []).length ? config.municipios_itbi : [{}];
    const padrao = itens.find(i => i.prefeitura === config.municipios_itbi_padrao) || itens[0];
    const corpo = document.createElement("div");
    const intro = document.createElement("p");
    intro.className = "hint";
    intro.textContent = "Estes dados vêm preenchidos nos formulários e podem ser alterados depois em Configurações.";
    const grade = document.createElement("div");
    grade.className = "field-grid";
    const local = entrada("ini-local", config.local_padrao, "Cidade - UF");
    const pref = entrada("ini-prefeitura", padrao.prefeitura, "Ex: CAMOCIM-CE");
    const comarca = entrada("ini-comarca", padrao.comarca, "Ex: CAMOCIM-CE");
    const texto = entrada("ini-isencao", padrao.texto_isencao, "Lei municipal de isenção do ITBI", true);
    grade.append(campo("Local de assinatura padrão", local, "field-wide"), campo("Prefeitura (município)", pref), campo("Comarca do cartório", comarca),
      campo("Texto da isenção do ITBI", texto, "field-wide"));
    corpo.append(intro, grade);
    const concluir = async (salvar) => {
      const payload = {primeira_execucao: false};
      if (salvar) {
        payload.local_padrao = local.value.trim();
        if (pref.value.trim()) {
          payload.municipios_itbi = [{prefeitura: pref.value.trim(), comarca: comarca.value.trim(), texto_isencao: texto.value.trim()}];
          payload.municipios_itbi_padrao = pref.value.trim();
        }
      }
      try { await api().updateSettings(payload); } catch (_) { /* tenta de novo na próxima abertura */ }
      depois?.();
    };
    ui().abrirModal("Configuração inicial", corpo, [
      {texto: "Salvar e continuar", primario: true, aoClicar: () => concluir(true)},
      {texto: "Usar o padrão", aoClicar: () => concluir(false)}]);
  }

  window.ContractoMunicipios = {montar, adicionar, ler, configuracaoInicial};
})();
