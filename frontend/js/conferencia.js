/* Etapa 2 (Conferência): resumo somente leitura dos dados preenchidos.
 * Recebe os dados da Etapa 1 por parâmetro; não guarda estado. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);

  function renderizar({ selected, catalog, fields, draft, maximum, agrupamento, nomeExibicao, form, values }) {
    const container = $("corpo-conferencia");
    if (container) {
      container.replaceChildren();
      const nomes = selected.map(id => { const p = catalog.find(x => x.profile_id === id); const cru = p ? (p.name || p.nome || id) : id; return (typeof nomeExibicao === "function" && p) ? nomeExibicao(p) : cru; });
      const resumoTopo = document.createElement("div");
      resumoTopo.className = "conf-resumo";
      const modelosBox = document.createElement("div");
      modelosBox.className = "conf-bloco";
      const hMod = document.createElement("h3"); hMod.textContent = "Modelos selecionados (" + nomes.length + ")";
      const chips = document.createElement("div"); chips.className = "conf-chips";
      nomes.forEach(n=>{ const c=document.createElement("span"); c.className="section-tag"; c.textContent=n; chips.append(c); });
      modelosBox.append(hMod, chips);
      const destBox = document.createElement("div");
      destBox.className = "conf-bloco";
      const hDest = document.createElement("h3"); hDest.textContent = "Assinatura e destino";
      const dl = document.createElement("dl");
      dl.className = "conf-grid";
      [["Data da assinatura", draft.globals.data_assinatura || "—"],
       ["Local da assinatura", draft.globals.local_assinatura || "—"],
       ["Salvar em", $("pasta-saida")?.value || "—"],
       ["Participantes", draft.people.length + " de " + maximum]
      ].forEach(([rot, val]) => {
        const wrap = document.createElement("div"); wrap.className = "conf-item";
        const dt = document.createElement("dt"); dt.textContent = rot;
        const dd = document.createElement("dd"); dd.textContent = val;
        wrap.append(dt, dd); dl.append(wrap);
      });
      destBox.append(hDest, dl);
      resumoTopo.append(modelosBox, destBox);
      container.appendChild(resumoTopo);

      // Agrupa campos por página/seção.
      const porPagina = {};
      fields.forEach(f => {
        if (["nome_completo","cpf","data_assinatura","local_assinatura"].includes(form().canonical(f.id))) return;
        const chave = form().paginaDe ? form().paginaDe(f, agrupamento) : (f.aba || "Geral");
        (porPagina[chave] = porPagina[chave] || []).push(f);
      });
      const HUMAN_CONF = (v) => {
        if (v === true || v === "SIM") return "Sim";
        if (v === false || v === "NÃO" || v === "NAO") return "Não";
        if (v === undefined || v === null || String(v).trim() === "") return "—";
        const mapa = { "AUTORIZAR_OU_ALTERAR_DEBITO": "Autorizar ou alterar débito", "CANCELAR_DEBITO": "Cancelar débito", "DESCONHECO_POSSUIR": "Desconheço possuir", "DECLARO_POSSUIR": "Declaro possuir" };
        if (mapa[v]) return mapa[v];
        // SELECAO genérica: "APOSENTADO_OU_PENSIONISTA" → "Aposentado Ou Pensionista".
        return String(v).replace(/_/g, " ").toLowerCase().replace(/(^|\s)\S/g, s => s.toUpperCase()).trim() || "—";
      };
      // Valores calculados (preview do servidor) têm precedência sobre o rascunho.
      const valorConf = (owner, comp, id) => {
        const c = comp && comp[id];
        if (c !== undefined && c !== null && String(c).trim() !== "") return c;
        return owner[id];
      };
      // Globais compartilhados também aparecem na conferência.
      const globaisConf = fields.filter(f=>f.escopo === "global" && !["data_assinatura","local_assinatura"].includes(form().canonical(f.id)));
      if (globaisConf.length) {
        const gBox = document.createElement("div");
        gBox.className = "conferencia-secao conf-participante";
        const hG = document.createElement("h3"); hG.textContent = "Dados compartilhados";
        const gridG = document.createElement("dl"); gridG.className = "conf-grid";
        globaisConf.forEach(f=>{
          const id = form().canonical(f.id);
          const val = valorConf(draft.globals, draft.computed && draft.computed[0], id);
          if (val === undefined || String(val ?? "").trim() === "") return;
          const wrap=document.createElement("div"); wrap.className="conf-item";
          const dt=document.createElement("dt"); dt.textContent=(f.rotulo||id);
          const dd=document.createElement("dd"); dd.textContent=HUMAN_CONF(val);
          wrap.append(dt,dd); gridG.append(wrap);
        });
        if (gridG.children.length) { gBox.append(hG, gridG); container.appendChild(gBox); }
      }
      draft.people.forEach((p, idx) => {
        const pBox = document.createElement("div");
        pBox.className = "conferencia-secao conf-participante";
        const cab = document.createElement("div");
        cab.className = "conf-cab";
        const legend = document.createElement("h3");
        legend.textContent = idx ? "Participante " + (idx + 1) : "Participante principal";
        const contagem = document.createElement("span");
        contagem.className = "section-tag";
        cab.append(legend, contagem);
        pBox.appendChild(cab);
        let preenchidos = 2;
        const base = document.createElement("dl");
        base.className = "conf-grid";
        [["Nome", p.nome_completo || "—"], ["CPF", p.cpf || "—"]].forEach(([rot, val]) => {
          const wrap = document.createElement("div"); wrap.className = "conf-item";
          const dt = document.createElement("dt"); dt.textContent = rot;
          const dd = document.createElement("dd"); dd.textContent = val;
          wrap.append(dt, dd); base.append(wrap);
        });
        const idSecao = document.createElement("div");
        idSecao.className = "conf-subsecao";
        const hId = document.createElement("h4"); hId.textContent = "Identificação";
        idSecao.append(hId, base);
        pBox.appendChild(idSecao);
        Object.entries(porPagina).forEach(([pagina, listaCampos]) => {
          const visiveis = listaCampos.filter(f => {
            const id = form().canonical(f.id);
            if (f.escopo === "global") return false;
            if (!form().visible(f, values(idx), idx + 1)) return false;
            return p[id] !== undefined && String(p[id] ?? "").trim() !== "";
          });
          if (!visiveis.length) return;
          const secao = document.createElement("div");
          secao.className = "conf-subsecao";
          // "Geral" sozinho não diz nada: mesmo título da Etapa 1.
          const h = document.createElement("h4");
          h.textContent = pagina === "Geral" && Object.keys(porPagina).length === 1 ? "Dados do formulário" : pagina;
          const grid = document.createElement("dl"); grid.className = "conf-grid";
          preenchidos += visiveis.length;
          visiveis.forEach(f => {
            const id = form().canonical(f.id);
            const wrap = document.createElement("div"); wrap.className = "conf-item";
            const dt = document.createElement("dt"); dt.textContent = (f.rotulo || id);
            const dd = document.createElement("dd"); dd.textContent = HUMAN_CONF(valorConf(p, draft.computed && draft.computed[idx], id));
            wrap.append(dt, dd); grid.append(wrap);
          });
          secao.append(h, grid);
          pBox.appendChild(secao);
        });
        contagem.textContent = preenchidos + " campo(s) preenchido(s)";
        container.appendChild(pBox);
      });
      try { window.ContractoUI.sincronizarStepper?.(); } catch (_) {}
    }
  }

  window.ContractoConferencia = { renderizar };
})();
