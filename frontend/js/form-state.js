/* Valores fora do DOM; backend valida e calcula. */
(function () {
  "use strict";
  const canonical = id => id === "nome" ? "nome_completo" : id;
  function norm(field) {
    // Aliases legados: if_field -> visivel_quando, formula -> calculo, pagina via aba.
    const f = field || {};
    if (f.if_field && !f.visivel_quando) f.visivel_quando = f.if_field;
    if (f.formula && !f.calculo) f.calculo = f.formula;
    return f;
  }
  function visible(field, values, index) {
    const f = norm(field);
    // Insensível a caixa, espelhando mapping_engine/form_validation no backend.
    const same = (a, b) => String(a ?? "").toLowerCase() === String(b ?? "").toLowerCase();
    return (!f.ate_participante || index <= f.ate_participante) &&
      (!f.visivel_quando?.length || f.visivel_quando.some(group =>
        Object.entries(group).every(([id, accepted]) => (accepted || []).some(v => same(v, values[canonical(id)])))));
  }
  function paginaDe(campo, agrupamento) {
    const f = norm(campo);
    const aba = (f.aba || "Geral").trim() || "Geral";
    if (agrupamento && agrupamento[aba]) return agrupamento[aba];
    return aba;
  }
  function onlyDigits(s) { return String(s).replace(/\D/g, ""); }
  function formatCpfProgressive(valor) {
    const digitos = onlyDigits(valor).slice(0, 11);
    const tam = digitos.length;
    if (tam <= 3) return digitos;
    if (tam <= 6) return digitos.slice(0, 3) + "." + digitos.slice(3);
    if (tam <= 9) return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." + digitos.slice(6);
    return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." + digitos.slice(6, 9) + "-" + digitos.slice(9);
  }
  function formatDateProgressive(valor) {
    const digitos = onlyDigits(valor).slice(0, 8);
    const tam = digitos.length;
    if (tam <= 2) return digitos;
    if (tam <= 4) return digitos.slice(0, 2) + "/" + digitos.slice(2);
    return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
  }
  function formatCnpjProgressive(valor) {
    const c = String(valor).toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 14);
    let out = c.slice(0, 2);
    if (c.length > 2) out += "." + c.slice(2, 5);
    if (c.length > 5) out += "." + c.slice(5, 8);
    if (c.length > 8) out += "/" + c.slice(8, 12);
    if (c.length > 12) out += "-" + c.slice(12);
    return out;
  }
  // CPF até 11 dígitos; acima disso CNPJ (alfanumérico) com 00.000.000/0000-00.
  function formatDocProgressive(valor) {
    const s = String(valor).toUpperCase().replace(/[^A-Z0-9]/g, "");
    return s.length <= 11 && /^\d*$/.test(s) ? formatCpfProgressive(s) : formatCnpjProgressive(s);
  }
  function formatTelefoneProgressive(valor) {
    const d = onlyDigits(valor).slice(0, 11);
    if (d.length <= 2) return d ? "(" + d : "";
    const ini = d.length > 10 ? 5 : 4;
    return "(" + d.slice(0, 2) + ") " + d.slice(2, 2 + ini) + (d.length > 2 + ini ? "-" + d.slice(2 + ini) : "");
  }
  function formatCepProgressive(valor) {
    const d = onlyDigits(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }
  const PARTES_ENDERECO = ["tipo", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "cep"];
  // "Rua X, 12, compl, bairro, cidade-UF, cep": partes vazias ficam de fora.
  function comporEndereco(p) {
    const via = [p.tipo, p.logradouro].filter(Boolean).join(" ");
    const cidade = [p.cidade, p.uf].filter(Boolean).join("-");
    return [via, p.numero, p.complemento, p.bairro, cidade, p.cep].map(x => String(x ?? "").trim()).filter(Boolean).join(", ");
  }
  function formatPisProgressive(valor) {
    const d = onlyDigits(valor).slice(0, 11);
    return d.replace(/^(\d{3})(\d{1,5})?(\d{1,2})?(\d)?$/, (_, a, b, c, e) => a + (b ? "." + b : "") + (c ? "." + c : "") + (e ? "-" + e : ""));
  }
  function cpfValid(value) {
    const s = onlyDigits(value);
    if (s.length !== 11 || /^(\d)\1+$/.test(s)) return false;
    for (let n = 9; n < 11; n++) {
      let sum = 0;
      for (let i = 0; i < n; i++) sum += Number(s[i]) * (n + 1 - i);
      if ((sum * 10 % 11) % 10 !== Number(s[n])) return false;
    }
    return true;
  }
  function dateValid(s) {
    if (!/^\d{2}\/\d{2}\/\d{4}$/.test(s)) return false;
    const [d,m,y] = s.split("/").map(Number), date = new Date(y,m-1,d);
    return y >= 1900 && date.getFullYear() === y && date.getMonth() === m-1 && date.getDate() === d;
  }
  function dateFuture(s) {
    const [d, m, y] = s.split("/").map(Number), hoje = new Date();
    return new Date(y, m - 1, d) > new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  }
  // Pesos oficiais do CNPJ (iguais a utils/cnpj_validator.py); valor do caractere = ASCII - 48.
  const PESOS_CNPJ = [[5,4,3,2,9,8,7,6,5,4,3,2], [6,5,4,3,2,9,8,7,6,5,4,3,2]];
  function cnpjValid(value) {
    const s = String(value).toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (!/^[0-9A-Z]{12}\d{2}$/.test(s) || /^(\d)\1{13}$/.test(s)) return false;
    return PESOS_CNPJ.every((pesos, k) => {
      const soma = pesos.reduce((acc, peso, i) => acc + (s.charCodeAt(i) - 48) * peso, 0);
      return (soma % 11 < 2 ? 0 : 11 - (soma % 11)) === Number(s[12 + k]);
    });
  }
  function docValid(value) {
    const limpo = String(value).replace(/[^A-Za-z0-9]/g, "");
    if (limpo.length <= 11) return cpfValid(value);
    return cnpjValid(value);
  }
  function pisValid(value) {
    const s = onlyDigits(value);
    if (s.length !== 11) return false;
    let soma = 0;
    const pesos = [3,2,9,8,7,6,5,4,3,2];
    for (let i = 0; i < 10; i++) soma += Number(s[i]) * pesos[i];
    const dv = (11 - (soma % 11)) % 11;
    const dig = dv === 10 ? 0 : dv;
    return dig === Number(s[10]);
  }
  function emailValid(value) { return /^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/.test(String(value).trim()); }
  function anoValid(value) { return /^\d{4}$/.test(String(value).trim()) && Number(value) >= 1900 && Number(value) <= 2100; }
  function valorNumericoValid(value) {
    // Espelha form_validation MOEDA/AREA: milhar com ponto, decimal com vírgula, >= 0.
    const text = String(value).replace("R$", "").replace(/ /g, "");
    if (!text) return false;
    const norm = text.includes(",") ? text.replace(/\./g, "").replace(",", ".") : text;
    if (!/^\d+(\.\d+)?$/.test(norm)) return false;
    return Number(norm) >= 0;
  }
  function formatMoedaProgressive(valor, pontoDecimal = true) {
    // Milhar com ponto e decimal com vírgula; "1234.5" vira decimal só ao colar (digitando, o ponto é milhar).
    let s = String(valor);
    if (pontoDecimal && !s.includes(",") && /\.\d{1,2}$/.test(s)) s = s.replace(/\.(\d{1,2})$/, ",$1");
    s = s.replace(/[^\d,]/g, "");
    const i = s.indexOf(",");
    const inteiro = (i < 0 ? s : s.slice(0, i)).replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return i < 0 ? inteiro : inteiro + "," + s.slice(i + 1).replace(/,/g, "").slice(0, 2);
  }
  function formatMoedaFinal(valor) {
    const v = formatMoedaProgressive(valor);
    if (!v) return "";
    const [inteiro, decimais = ""] = v.split(",");
    return (inteiro || "0") + "," + decimais.padEnd(2, "0");
  }
  const sigDigito = c => /\d/.test(c ?? ""), sigDoc = c => /[0-9A-Za-z]/.test(c ?? ""), sigMoeda = c => /[\d,]/.test(c ?? "");
  const mascaraMoeda = {formatar: (v, colar) => formatMoedaProgressive(v, colar), sig: sigMoeda, decimal: true};
  const mascaras = {
    CPF: {formatar: formatCpfProgressive, sig: sigDigito},
    CNPJ: {formatar: formatCnpjProgressive, sig: sigDoc},
    CPF_CNPJ: {formatar: formatDocProgressive, sig: sigDoc},
    PIS_PASEP: {formatar: formatPisProgressive, sig: sigDigito},
    DATA: {formatar: formatDateProgressive, sig: sigDigito},
    TELEFONE: {formatar: formatTelefoneProgressive, sig: sigDigito},
    CEP: {formatar: formatCepProgressive, sig: sigDigito},
    INTEIRO: {formatar: onlyDigits, sig: sigDigito},
    ANO: {formatar: v => onlyDigits(v).slice(0, 4), sig: sigDigito},
    MOEDA: mascaraMoeda, AREA: mascaraMoeda,
  };
  // Reaplica a máscara mantendo o cursor depois do mesmo nº de caracteres significativos:
  // corrigir um dígito no meio não joga o cursor ao fim nem recria o valor.
  function mascarar(input, evento, mascara) {
    const tipo = evento?.inputType || "", anterior = input.dataset.anterior ?? "";
    let bruto = input.value, pos = input.selectionStart ?? bruto.length;
    const apagouUm = bruto.length === anterior.length - 1;
    // Apagar só um separador não mudaria nada depois da máscara: apaga o dígito vizinho.
    if (apagouUm && tipo === "deleteContentBackward" && !mascara.sig(anterior[pos])) {
      let i = pos - 1;
      while (i >= 0 && !mascara.sig(bruto[i])) i--;
      if (i >= 0) { bruto = bruto.slice(0, i) + bruto.slice(i + 1); pos = i; }
    } else if (apagouUm && tipo === "deleteContentForward" && !mascara.sig(anterior[pos])) {
      let i = pos;
      while (i < bruto.length && !mascara.sig(bruto[i])) i++;
      if (i < bruto.length) bruto = bruto.slice(0, i) + bruto.slice(i + 1);
    }
    // Valores com decimal: "." digitado vira vírgula; uma segunda vírgula é descartada.
    if (mascara.decimal && tipo === "insertText" && (evento.data === "." || evento.data === ",")) {
      const resto = bruto.slice(0, pos - 1) + bruto.slice(pos);
      if (resto.includes(",")) { bruto = resto; pos--; }
      else bruto = bruto.slice(0, pos - 1) + "," + bruto.slice(pos);
    }
    // Dígito no fim com os centavos cheios ("100,00" + 0): a vírgula sobe uma casa ("1.000,00"), como em caixa eletrônico.
    const v = bruto.indexOf(",");
    if (mascara.decimal && tipo === "insertText" && /\d/.test(evento.data) && v >= 0 && pos === bruto.length && bruto.length - v - 1 > 2) {
      const d = bruto.replace(/\D/g, "");
      bruto = d.slice(0, -2) + "," + d.slice(-2);
      pos = bruto.length;
    }
    let antes = 0;
    for (let i = 0; i < pos; i++) if (mascara.sig(bruto[i])) antes++;
    const novo = mascara.formatar(bruto, tipo === "insertFromPaste");
    let nova = 0;
    for (let n = 0; nova < novo.length && n < antes; nova++) if (mascara.sig(novo[nova])) n++;
    input.value = novo;
    input.setSelectionRange?.(nova, nova);
    input.dataset.anterior = novo;
    return novo;
  }
  const ROTULOS_OPCOES = {
    AUTORIZAR_OU_ALTERAR_DEBITO: "Autorizar ou alterar débito", CANCELAR_DEBITO: "Cancelar débito",
    DESCONHECO_POSSUIR: "Desconheço possuir", DECLARO_POSSUIR: "Declaro possuir", SELECIONE: "Selecione",
  };
  // O valor salvo é o código; o rótulo vem do perfil (rotulos_opcoes) ou de uma humanização do código.
  function rotuloOpcao(campo, valor) {
    if (!valor) return "Selecione";
    return campo?.rotulos_opcoes?.[valor] ?? ROTULOS_OPCOES[valor] ??
      String(valor).replace(/_/g, " ").toLowerCase().replace(/(^|\s)\S/g, c => c.toUpperCase()).trim();
  }
  const numeroBR = v => {
    const t = String(v ?? "").replace("R$", "").replace(/ /g, ""), n = Number(t.includes(",") ? t.replace(/\./g, "").replace(",", ".") : t);
    return Number.isFinite(n) ? n : 0;
  };
  // Espelha services/field_calculator.py: só nomes de campos com + ou -, nunca negativo, "1.234,56".
  function calcular(expressao, valores) {
    if (!/^\s*[A-Za-z_]\w*(\s*[+-]\s*[A-Za-z_]\w*)*\s*$/.test(expressao || "")) return null;
    let centavos = 0, primeiro = true;
    for (const m of expressao.matchAll(/([+-]?)\s*([A-Za-z_]\w*)/g)) {
      const c = Math.round(numeroBR(valores[m[2]]) * 100);
      centavos += !primeiro && m[1] === "-" ? -c : c;
      primeiro = false;
    }
    return formatMoedaFinal(String(Math.max(0, centavos) / 100).replace(".", ","));
  }
  function participants(draft, fields) {
    return draft.people.map((person,index) => {
      const values = {...person, ...draft.globals, ...(draft.computed?.[index] || {})};
      fields.forEach(f => {
        const id = canonical(f.id);
        if (values[id] === undefined) values[id] = f.valor_padrao ?? "";
        if (!visible(f,values,index+1) && f.limpar_quando_oculto) values[id] = "";
      });
      const dynamic = {};
      fields.forEach(f => {
        const id = canonical(f.id);
        if (!["nome_completo","cpf","data_assinatura","local_assinatura"].includes(id) && !f.calculo)
          dynamic[id] = values[id] ?? "";
      if (f.tipo === "ENDERECO") PARTES_ENDERECO.forEach(k => { dynamic[id + "_" + k] = values[id + "_" + k] ?? ""; });
      });
      return {nome_completo: person.nome_completo || "", cpf: person.cpf || "",
        data_assinatura: draft.globals.data_assinatura || "",
        local_assinatura: draft.globals.local_assinatura || "", campos_dinamicos: dynamic};
    });
  }
  window.ContractoForm = {canonical, visible, paginaDe, cpfValid, cnpjValid, docValid, pisValid, emailValid, anoValid, valorNumericoValid, dateValid, dateFuture, participants, formatCpfProgressive, formatDocProgressive, formatDateProgressive, formatMoedaProgressive, formatMoedaFinal, formatTelefoneProgressive, formatPisProgressive, formatCnpjProgressive, formatCepProgressive, comporEndereco, mascaras, mascarar, rotuloOpcao, calcular};
})();
