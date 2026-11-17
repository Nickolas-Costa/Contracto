/* Campo ENDERECO: um texto completo OU partes (logradouro, nº, bairro...). O texto completo é o valor
 * principal (owner[id]); no modo detalhado ele é montado das partes, que também seguem para o servidor
 * como <id>_tipo, <id>_logradouro, <id>_numero, <id>_complemento, <id>_bairro, <id>_cidade, <id>_uf e
 * <id>_cep, para PDFs que têm esses campos separados. */
(function () {
  "use strict";
  const TIPOS = ["Rua", "Avenida", "Travessa", "Alameda", "Praça", "Rodovia", "Estrada", "Largo", "Beco", "Via"];
  const UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(" ");
  // [chave, rótulo, colunas de 6, tipo]
  const PARTES = [["tipo", "Tipo", 2, "tipo"], ["logradouro", "Logradouro", 4], ["numero", "Número", 2], ["complemento", "Complemento", 4],
    ["bairro", "Bairro", 3], ["cidade", "Cidade", 3], ["uf", "UF", 2, "uf"], ["cep", "CEP", 2, "cep"]];

  function criar({field, index, global, owner, id, form, busy, touch, changed, atualizar}) {
    const base = "campo-" + (global ? "global" : index) + "-" + id;
    const wrap = document.createElement("div");
    wrap.className = "field field-wide endereco-campo";
    const topo = document.createElement("div");
    topo.className = "endereco-topo";
    const rotulo = document.createElement("label");
    rotulo.htmlFor = base; rotulo.textContent = (field.rotulo || id) + (field.obrigatorio ? " *" : "");
    const modos = document.createElement("div");
    modos.className = "modos-seletor endereco-modos"; modos.setAttribute("role", "group"); modos.setAttribute("aria-label", "Forma de preencher o endereço");
    const botoes = {};
    [["completo", "Completo"], ["detalhado", "Detalhado"]].forEach(([chave, texto]) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "seletor-item"; b.textContent = texto; b.dataset.editable = "true";
      b.addEventListener("click", () => { if (busy()) return; owner[id + "_modo"] = chave; mostrar(); });
      botoes[chave] = b; modos.append(b);
    });
    topo.append(rotulo, modos);

    const completo = document.createElement("input");
    completo.type = "text"; completo.id = base; completo.autocomplete = "off"; completo.maxLength = 4000;
    completo.value = owner[id] ?? "";
    completo.addEventListener("blur", () => { touch(); atualizar(); });
    completo.addEventListener("input", () => { if (busy()) return; owner[id] = completo.value.trim(); changed(); });

    const detalhado = document.createElement("div");
    detalhado.className = "endereco-partes";
    const entradas = {};
    PARTES.forEach(([chave, texto, colunas, tipo]) => {
      const div = document.createElement("div");
      div.className = "field"; div.style.gridColumn = "span " + colunas;
      const lab = document.createElement("label");
      const campo = document.createElement(tipo === "tipo" || tipo === "uf" ? "select" : "input");
      campo.id = base + "-" + chave; lab.htmlFor = campo.id; lab.textContent = texto; campo.dataset.editable = "true";
      if (campo.tagName === "SELECT") {
        (tipo === "uf" ? ["", ...UFS] : ["", ...TIPOS]).forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v || "—"; campo.append(o); });
      } else { campo.type = "text"; campo.autocomplete = "off"; if (tipo === "cep") { campo.inputMode = "numeric"; campo.placeholder = "00000-000"; } }
      campo.value = owner[id + "_" + chave] ?? "";
      campo.addEventListener("blur", () => { touch(); atualizar(); });
      campo.addEventListener(campo.tagName === "SELECT" ? "change" : "input", e => {
        if (busy()) return;
        owner[id + "_" + chave] = tipo === "cep" ? form.mascarar(campo, e, form.mascaras.CEP) : campo.value.trim();
        const partes = Object.fromEntries(PARTES.map(([k]) => [k, owner[id + "_" + k]]));
        owner[id] = form.comporEndereco(partes); completo.value = owner[id];
        changed();
      });
      entradas[chave] = campo; div.append(lab, campo); detalhado.append(div);
    });
    const erro = document.createElement("div");
    erro.id = base + "-erro"; erro.className = "erro"; erro.hidden = true;
    const dica = document.createElement("p");
    dica.className = "field-note"; dica.id = base + "-nota";
    dica.textContent = "No modo detalhado, o endereço completo é montado a partir das partes.";
    completo.setAttribute("aria-describedby", erro.id);

    function mostrar() {
      const modo = owner[id + "_modo"] === "detalhado" ? "detalhado" : "completo";
      completo.hidden = modo === "detalhado"; detalhado.hidden = modo !== "detalhado"; dica.hidden = modo !== "detalhado";
      Object.entries(botoes).forEach(([k, b]) => b.setAttribute("aria-pressed", String(k === modo)));
    }
    mostrar();
    wrap.append(topo, completo, detalhado, dica, erro);
    // O campo que recebe foco e erro é o que está à vista.
    return {wrap, error: erro, ativo: () => owner[id + "_modo"] === "detalhado" ? entradas.logradouro : completo};
  }

  window.ContractoEndereco = {criar};
})();
