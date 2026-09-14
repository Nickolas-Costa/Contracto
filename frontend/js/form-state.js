/* Valores fora do DOM; backend valida e calcula. */
(function () {
  "use strict";
  const canonical = id => id === "nome" ? "nome_completo" : id;
  function visible(field, values, index) {
    return (!field.ate_participante || index <= field.ate_participante) &&
      (!field.visivel_quando?.length || field.visivel_quando.some(group =>
        Object.entries(group).every(([id, accepted]) => accepted.includes(String(values[canonical(id)] ?? "")))));
  }
  function cpfValid(value) {
    const s = String(value).replace(/\D/g, "");
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
  window.ContractoForm = {canonical, visible, cpfValid, dateValid, participants};
})();
