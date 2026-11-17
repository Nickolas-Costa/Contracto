/* Etapa 2 (Conferência): resumo somente leitura dos dados preenchidos.
 * Recebe os dados da Etapa 1 por parâmetro; não guarda estado. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);

  // Cada valor leva ao campo na Etapa 1 (participante nulo = campo compartilhado).
  function mostrarValor(dd, texto, rotulo, participante, id, irParaCampo) {
    if (!irParaCampo) { dd.textContent = texto; return; }
    const b = document.createElement("button");
    b.type = "button"; b.className = "conf-valor"; b.textContent = texto;
    b.setAttribute("aria-label", "Editar " + rotulo + " (valor atual: " + texto + ")");
    b.addEventListener("click", () => irParaCampo(participante, id));
    dd.append(b);
  }

  function renderizar({ selected, catalog, fields, draft, maximum, agrupamento, nomeExibicao, form, values, irParaCampo, pendencias }) {
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
      [["Data da assinatura", draft.globals.data_assinatura || "—", "data_assinatura"],
       ["Local da assinatura", draft.globals.local_assinatura || "—", "local_assinatura"],
       ["Salvar em", $("pasta-saida")?.value || "—"],
       ["Participantes", draft.people.length + " de " + maximum]
      ].forEach(([rot, val, alvo]) => {
        const wrap = document.createElement("div"); wrap.className = "conf-item";
        const dt = document.createElement("dt"); dt.textContent = rot;
        const dd = document.createElement("dd");
        if (alvo) mostrarValor(dd, val, rot, null, alvo, irParaCampo); else dd.textContent = val;
        wrap.append(dt, dd); dl.append(wrap);
      });
      destBox.append(hDest, dl);
      resumoTopo.append(modelosBox, destBox);
      container.appendChild(resumoTopo);
      if (pendencias) {
        const aviso = document.createElement("p");
        aviso.className = "conf-aviso"; aviso.setAttribute("role", "status");
        aviso.textContent = pendencias + " campo(s) sem preencher ou fora do formato: os documentos serão gerados assim, com esses campos em branco ou como digitados.";
        container.appendChild(aviso);
      }

      // Agrupa campos por página/seção.
      const porPagina = {};
      fields.forEach(f => {
        if (["nome_completo","cpf","data_assinatura","local_assinatura"].includes(form().canonical(f.id))) return;
        const chave = form().paginaDe ? form().paginaDe(f, agrupamento) : (f.aba || "Geral");
        (porPagina[chave] = porPagina[chave] || []).push(f);
      });
      const HUMAN_CONF = (v, campo) => {
        if (v === true || String(v).toUpperCase() === "SIM") return "Sim";
        if (v === false || ["NÃO", "NAO"].includes(String(v).toUpperCase())) return "Não";
        if (v === undefined || v === null || String(v).trim() === "") return "—";
        return campo?.tipo === "SELECAO" ? form().rotuloOpcao(campo, v) : String(v);
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
          const dd=document.createElement("dd"); mostrarValor(dd, HUMAN_CONF(val, f), f.rotulo||id, null, id, irParaCampo);
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
        [["Nome", p.nome_completo || "—", "nome_completo"], ["CPF", p.cpf || "—", "cpf"]].forEach(([rot, val, alvo]) => {
          const wrap = document.createElement("div"); wrap.className = "conf-item";
          const dt = document.createElement("dt"); dt.textContent = rot;
          const dd = document.createElement("dd");
          mostrarValor(dd, val, rot, idx, alvo, irParaCampo);
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
            const dd = document.createElement("dd"); mostrarValor(dd, HUMAN_CONF(valorConf(p, draft.computed && draft.computed[idx], id), f), f.rotulo || id, idx, id, irParaCampo);
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
