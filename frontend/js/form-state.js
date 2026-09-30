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
    return (!f.ate_participante || index <= f.ate_participante) &&
      (!f.visivel_quando?.length || f.visivel_quando.some(group =>
        Object.entries(group).every(([id, accepted]) => accepted.includes(String(values[canonical(id)] ?? "")))));
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
  function cnpjValid(value) {
    const s = String(value).toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (s.length !== 14) return false;
    if (/^([0-9A-Z])\1+$/.test(s)) return false;
    const peso = n => { let p = n % 8 === 0 ? 9 : (n % 8) + 1; const out = []; for (let i = 0; i < n; i++) { out.push(p); p = p === 2 ? 9 : p - 1; } return out.reverse(); };
    for (const n of [12, 13]) {
      let soma = 0;
      const pesos = peso(n);
      for (let i = 0; i < n; i++) soma += (s.charCodeAt(i) - 48 > 9 ? s.charCodeAt(i) - 48 : Number(s[i])) * pesos[i];
      const dv = soma % 11 < 2 ? 0 : 11 - (soma % 11);
      const esperado = s.charCodeAt(n) - 48 > 9 ? s.charCodeAt(n) - 48 : Number(s[n]);
      if (dv !== esperado && !(s[n] >= "A" && dv === Number(s[n]))) {
        // Para alfanumérico, compara pelo valor oficial (ASCII-48).
        const v = s.charCodeAt(n) - 48;
        if (dv !== v) return false;
      }
    }
    return true;
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
  function telefoneValid(value) { const d = onlyDigits(value); return d.length >= 10 && d.length <= 11; }
  function anoValid(value) { return /^\d{4}$/.test(String(value).trim()) && Number(value) >= 1900 && Number(value) <= 2100; }
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
      });
      return {nome_completo: person.nome_completo || "", cpf: person.cpf || "",
        data_assinatura: draft.globals.data_assinatura || "",
        local_assinatura: draft.globals.local_assinatura || "", campos_dinamicos: dynamic};
    });
  }
  window.ContractoForm = {canonical, visible, paginaDe, cpfValid, cnpjValid, docValid, pisValid, emailValid, telefoneValid, anoValid, dateValid, participants, formatCpfProgressive, formatDateProgressive};
})();
