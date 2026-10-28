/* Rascunho preservado por campo e participante; DOM apenas apresenta valores. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id), form = () => window.ContractoForm;
  const draft = {people: [{nome_completo:"",cpf:""}], globals:{data_assinatura:"",local_assinatura:""}};
  let catalog = [], selected = [], fields = [], maximum = 1, revision = 0, compositionRevision = 0;
  let ultimaComposicao = null;
  let composing = false, composed = false, loaded = false, bound = false, issues = [], mode = "contrato";
  let paginas = [], paginaAtual = 0, usarPaginacao = false, agrupamento = {};
  const controls = [];
  const touched = new WeakMap(), touchedGlobals = new Set();
  let reviewing = false;
  function touch(owner, id) { if(!touched.has(owner))touched.set(owner,new Set());touched.get(owner).add(id); }
  let previewTimer=null, previewPending=false;
  const busy = () => window.ContractoEtapa2?.ocupado() || false;
  const online = () => window.ContractoApp?.pronto() || false;
  function changed() {
    issues = []; revision++;
    recalcularLocal();
    window.ContractoEtapa2?.invalidar();
    schedulePreview();
    atualizar();
  }
  function values(index) { return {...draft.people[index],...draft.globals,...(draft.computed?.[index] || {})}; }
  function schedulePreview() {
    clearTimeout(previewTimer);
    previewPending=composed && online() && draft.people.every(p=>p.nome_completo && form().cpfValid(p.cpf));
    if(!previewPending)return;
    previewTimer=setTimeout(async()=>{
      const expected=revision;
      const r=await window.ContractoAPI.request("POST","/api/v1/profiles/preview",{profile_ids:selected,participants:form().participants(draft,fields)});
      if(expected!==revision)return;
      previewPending=false;
      if(r.status===200){
        issues=r.data.issues || [];
        draft.computed=(r.data.values || []).map(row=>Object.fromEntries(fields.filter(f=>f.calculo).map(f=>[f.id,row[f.id]])));
        controls.filter(c=>c.field.calculo).forEach(c=>c.input.value=draft.computed[c.index]?.[c.id] ?? "");
      } else issues=r.data?.issues?.length ? r.data.issues : [{field:"Validação",message:"Não foi possível validar. Tente conectar novamente."}];
      atualizar();
    },350);
  }
  function avaliarFormulaLocal(expressao, valores) {
    // Avaliador restrito: apenas identificadores de campos + operadores aritméticos.
    if (!expressao || /[^A-Za-z0-9_+\-*/().\s,]/.test(expressao)) return null;
    const ids = Object.keys(valores);
    try {
      const fn = Function(...ids, '"use strict";return(' + expressao + ')');
      const args = ids.map(k => {
        const raw = String(valores[k] ?? "").replace(/\./g, "").replace(",", ".");
        const num = Number(raw);
        return Number.isFinite(num) ? num : 0;
      });
      const out = fn(...args);
      return (typeof out === "number" && Number.isFinite(out)) ? out : null;
    } catch (_) { return null; }
  }
  function sincronizarSelecao() {
    // A lista é montada antes da composição inicial; sem este sync o perfil
    // composto não aparece marcado (smoke: "one initial profile").
    // Fase 0: sincroniza também os botões do seletor de modelos (>2
    // contratos), que usam aria-pressed em vez de input:checked.
    document.querySelectorAll("#lista-formularios input").forEach(el=>{ el.checked=selected.includes(el.value); });
    document.querySelectorAll("#seletor-modelos .seletor-item").forEach(btn=>{
      btn.setAttribute("aria-pressed", selected.includes(btn.value) ? "true" : "false");
    });
  }
  function fieldControl(field,index,host) {
    const id = form().canonical(field.id), global = field.escopo === "global";
    const owner = global ? draft.globals : draft.people[index];
    if (owner[id] === undefined) owner[id] = field.valor_padrao ?? "";
    const wrap = document.createElement("div"); wrap.className = "field";
    if(id === "endereco" || field.tipo === "TEXTO_LONGO" || field.tipo === "MULTILINHA") wrap.classList.add("field-wide");
    const isTextarea = field.tipo === "TEXTO_LONGO" || field.tipo === "MULTILINHA";
    const label = document.createElement("label");
    const input = document.createElement(field.tipo === "SELECAO" ? "select" : (isTextarea ? "textarea" : "input"));
    if (isTextarea) {
      input.rows = 3;
      input.classList.add("field-textarea");
      const autoResize = () => { input.style.height = "auto"; input.style.height = Math.min(320, Math.max(80, input.scrollHeight)) + "px"; };
      input.addEventListener("input", autoResize);
      requestAnimationFrame(autoResize);
    }
    input.id = "campo-" + (global ? "global" : index) + "-" + id;
    label.htmlFor = input.id; label.textContent = (field.rotulo || id) + (field.obrigatorio && !field.calculo ? " *" : "");
    input.autocomplete = "off";
    if (field.tipo === "SELECAO") {
      const opcoes = field.opcoes || [];
      const ROTULOS_OPCOES = {
        "AUTORIZAR_OU_ALTERAR_DEBITO": "Autorizar ou alterar débito",
        "CANCELAR_DEBITO": "Cancelar débito",
        "DESCONHECO_POSSUIR": "Desconheço possuir",
        "DECLARO_POSSUIR": "Declaro possuir",
        "SELECIONE": "Selecione"
      };
      const humanizar = (nome) => {
        if (!nome) return "Selecione";
        if (ROTULOS_OPCOES[nome]) return ROTULOS_OPCOES[nome];
        return nome.replace(/_/g, " ").toLowerCase().replace(/(^|\s)\S/g, s => s.toUpperCase()).trim();
      };
      for (const value of ["", ...opcoes]) {
        const option = document.createElement("option"); option.value = value; option.textContent = humanizar(value); input.append(option);
      }
      if (owner[id] && opcoes.includes(owner[id])) input.value = owner[id];
      if (field.apresentacao === "checkbox" && opcoes.length && opcoes.length <= 4) {
        // Fase 0: o <select> original sai do DOM via replaceWith; os listeners
        // precisam ir nos checkboxes criados (antes eram anexados ao select
        // já destacado — noop — e a escolha nunca chegava ao rascunho).
        const caixas = opcoes.map(value => {
          const cb = document.createElement("label"); cb.className = "checkbox-inline";
          const chk = document.createElement("input"); chk.type = "checkbox"; chk.value = value; chk.checked = owner[id] === value; chk.id = input.id + "-" + value.replace(/[^A-Za-z0-9]/g, "_");
          chk.addEventListener("change", () => {
            if (busy()) { chk.checked = owner[id] === value; return; }
            owner[id] = chk.checked ? value : "";
            touch(owner, id);
            changed();
          });
          const lbl = document.createElement("span"); lbl.textContent = humanizar(value);
          cb.append(chk, lbl); return cb;
        });
        input.replaceWith(...caixas);
      }
    } else if (field.tipo === "CHECKBOX") {
      input.type="checkbox"; const options=field.opcoes?.length ? field.opcoes : ["SIM","NÃO"];
      if (owner[id] === "") owner[id]=options[options.length-1];
      input.checked = owner[id] === options[0] || owner[id] === true;
    } else {
      // <textarea> não expõe `type` gravável (HTMLTextAreaElement.type é somente leitura).
      if (!isTextarea) input.type = "text";
      if (["CPF","CNPJ","CPF_CNPJ","INTEIRO","ANO","DATA","MOEDA","AREA","PIS_PASEP"].includes(field.tipo)) input.inputMode = "decimal";
      if (field.tipo === "EMAIL") input.inputMode = "email";
      if (field.tipo === "TELEFONE") input.inputMode = "tel";
      if (field.tipo === "DATA") input.placeholder="DD/MM/AAAA";
      if (field.tipo === "MOEDA") input.placeholder="0,00";
      input.maxLength = 4000;
    }
    if (field.tipo !== "CHECKBOX" && field.tipo !== "SELECAO") input.value=owner[id];
    if (field.calculo) {input.readOnly=true; input.placeholder="Calculado automaticamente";}
    const error=document.createElement("div"); error.id=input.id+"-erro"; error.className="erro"; error.hidden=true;
    input.setAttribute("aria-describedby",error.id);
    input.addEventListener("blur",()=>{touch(owner,id);atualizar();});
    input.addEventListener("input",()=>{
      if (busy()) return;
      const options=field.opcoes?.length ? field.opcoes : ["SIM","NÃO"];
      let val = field.tipo === "CHECKBOX" ? (input.checked ? options[0] : options[options.length-1]) : input.value;
      if (field.tipo === "CPF") {
        val = form().formatCpfProgressive(val);
        input.value = val;
      } else if (field.tipo === "DATA") {
        val = form().formatDateProgressive(val);
        input.value = val;
      } else if (field.tipo === "MOEDA" && !field.calculo) {
        // Mantém o cursor após o mesmo nº de dígitos/vírgula (editar no meio não pula ao fim).
        const digitosAntes = (val.slice(0, input.selectionStart ?? val.length).match(/[\d,]/g) || []).length;
        val = form().formatMoedaProgressive(val);
        input.value = val;
        let pos = 0;
        for (let n = 0; pos < val.length && n < digitosAntes; pos++) if (/[\d,]/.test(val[pos])) n++;
        input.setSelectionRange?.(pos, pos);
      }
      owner[id] = val.trim();
      changed();
    });
    if (field.tipo === "MOEDA" && !field.calculo) {
      // Ao sair do campo completa os centavos: "180000" → "180.000,00".
      input.addEventListener("blur", () => {
        const final = form().formatMoedaFinal(input.value);
        if (final === input.value) return;
        input.value = final; owner[id] = final; changed();
      });
    }
    wrap.append(label,input,error); host.append(wrap);
    if(field.calculo){const note=document.createElement("p");note.className="field-note";note.id=input.id+"-nota";note.textContent="Calculado a partir dos dados informados.";wrap.append(note);input.setAttribute("aria-describedby",error.id+" "+note.id);}
    controls.push({field,index,id,owner,wrap,input,error});
  }
  function recalcularLocal() {
    controls.forEach(c => {
      const expr = c.field.calculo || c.field.formula;
      if (!expr) return;
      const vals = values(c.index);
      const out = avaliarFormulaLocal(expr, vals);
      if (out !== null) {
        const texto = String(Math.round(out * 100) / 100).replace(".", ",");
        c.input.value = texto;
        c.owner[c.id] = texto;
      }
    });
  }
  function resolverPaginas(lista, grupo) {
    const ordem = [];
    lista.forEach(f => {
      if (["nome_completo","cpf","data_assinatura","local_assinatura"].includes(form().canonical(f.id))) return;
      const p = form().paginaDe ? form().paginaDe(f, grupo) : (f.aba || "Geral");
      if (!ordem.includes(p)) ordem.push(p);
    });
    return ordem;
  }
  function renderPaginacao() {
    const host = $("paginacao-form");
    if (!host) return;
    host.replaceChildren();
    if (!composed || !usarPaginacao || paginas.length < 2) { host.hidden = true; return; }
    host.hidden = false;
    const prev = document.createElement("button");
    prev.type = "button"; prev.className = "btn btn-secondary btn-sm"; prev.textContent = "← Anterior";
    prev.disabled = paginaAtual === 0;
    prev.addEventListener("click", () => mudarPagina(-1));
    const info = document.createElement("span");
    info.className = "paginacao-indicador";
    info.textContent = "Página " + (paginaAtual + 1) + " de " + paginas.length;
    const nome = document.createElement("span");
    nome.className = "paginacao-nome";
    nome.textContent = paginas[paginaAtual] || "";
    const next = document.createElement("button");
    next.type = "button"; next.className = "btn btn-secondary btn-sm"; next.textContent = "Próxima →";
    next.disabled = paginaAtual >= paginas.length - 1;
    next.addEventListener("click", () => mudarPagina(1));
    host.append(prev, info, nome, next);
  }
  function mudarPagina(delta) {
    const novo = Math.max(0, Math.min(paginas.length - 1, paginaAtual + delta));
    if (novo === paginaAtual) return;
    if (delta > 0) {
      // Valida a página atual antes de avançar.
      reviewing = true;
      const erros = localIssues().filter(e => paginaDoControle(e) === paginas[paginaAtual]);
      atualizar();
      if (erros.length) {
        window.ContractoUI.toast("Revise os campos desta página antes de avançar.", "warning");
        return;
      }
      reviewing = false;
    }
    paginaAtual = novo;
    renderPaginacao();
    atualizar();
  }
  function paginaDoControle(e) {
    const c = controls.find(x => x.id === form().canonical(e.field) && (!e.participant || e.participant === x.index + 1));
    if (!c) return null;
    return form().paginaDe ? form().paginaDe(c.field, agrupamento) : (c.field.aba || "Geral");
  }
  function group(card, title) {
    const section=document.createElement("fieldset");section.className="field-section";
    const legend=document.createElement("legend");legend.textContent=title;
    const grid=document.createElement("div");grid.className="field-grid";
    section.append(legend,grid);card.append(section);return grid;
  }
  function render() {
    controls.length=0; $("participantes").replaceChildren(); $("campos-globais").replaceChildren();
    fields = (fields || []).filter(f => typeof f.id === "string" && f.id.length > 0);
    draft.people.forEach((person,index)=>{
      const card=document.createElement("div"); card.className="card";
      const header=document.createElement("div");header.className="card-header";
      const heading=document.createElement("div"),title=document.createElement("h2"); title.textContent=index ? "Participante "+(index+1) : "Participante principal";
      const hint=document.createElement("p");hint.className="hint";hint.textContent="Identificação e dados para os formulários selecionados.";heading.append(title,hint);header.append(heading);card.append(header);
      const identity=document.createElement("div");identity.className="field-grid identity-grid";card.append(identity);
      fieldControl({id:"nome_completo",rotulo:"Nome completo",tipo:"TEXTO",obrigatorio:true},index,identity);
      fieldControl({id:"cpf",rotulo:"CPF",tipo:"CPF",obrigatorio:true},index,identity);
      const personal=fields.filter(f=>f.escopo !== "global" && !["nome_completo","cpf","data_assinatura","local_assinatura"].includes(form().canonical(f.id)));
      const address=personal.filter(f=>f.id === "endereco"),details=personal.filter(f=>f.id !== "endereco");
      if(address.length){const grid=group(card,"Endereço");address.forEach(f=>fieldControl(f,index,grid));}
      if(details.length){
        const porAba = {};
        details.forEach(f=>{ const aba=(f.aba || "Geral").trim() || "Geral"; (porAba[aba]=porAba[aba]||[]).push(f); });
        const abas = Object.keys(porAba);
        if (abas.length <= 1) { const grid=group(card,"Dados do formulário"); details.forEach(f=>fieldControl(f,index,grid)); }
        else abas.forEach(aba=>{ const grid=group(card,aba); porAba[aba].forEach(f=>fieldControl(f,index,grid)); });
      }
      if (index) {
        // Fase 2 — paridade com o legado ("Copiar dados de [Participante X]"):
        // reaproveita os campos idênticos do participante principal, mantendo
        // nome e CPF próprios.
        const copiar = document.createElement("button"); copiar.type = "button"; copiar.className = "btn btn-subtle"; copiar.textContent = "Copiar dados do participante 1"; copiar.setAttribute("aria-label", "Copiar dados do participante 1 para o participante " + (index + 1)); copiar.dataset.editable = "true";
        copiar.addEventListener("click", () => {
          if (busy()) return;
          const origem = draft.people[0] || {}, destino = draft.people[index];
          Object.keys(origem).forEach(k => { if (k !== "nome_completo" && k !== "cpf") destino[k] = origem[k]; });
          window.ContractoUI.toast("Dados copiados do participante 1.", "success");
          changed(); render();
        });
        header.append(copiar);
        const remove=document.createElement("button"); remove.type="button"; remove.className="btn btn-subtle"; remove.textContent="Remover";remove.setAttribute("aria-label","Remover participante "+(index+1)); remove.dataset.editable="true";
        remove.addEventListener("click",()=>{if(busy())return; window.ContractoUI.toast("Participante removido.","warning");draft.people.splice(index,1);changed();render();$("btn-adicionar").focus();}); header.append(remove);
      }
      $("participantes").append(card);
    });
    const globals=fields.filter(f=>f.escopo === "global" && !["nome_completo","cpf","data_assinatura","local_assinatura"].includes(form().canonical(f.id)));
    if(globals.length){
      const card=document.createElement("div");card.className="card";
      const header=document.createElement("div");header.className="card-header";
      const heading=document.createElement("div"),title=document.createElement("h2");title.textContent="Dados compartilhados";
      const hint=document.createElement("p");hint.className="hint";hint.textContent="Valem para todos os participantes.";
      heading.append(title,hint);header.append(heading);card.append(header);
      const porAba={}; globals.forEach(f=>{const aba=(f.aba||"Geral").trim()||"Geral";(porAba[aba]=porAba[aba]||[]).push(f);});
      Object.keys(porAba).forEach(aba=>{
        const grid=group(card,aba); porAba[aba].forEach(f=>fieldControl(f,0,grid));
      });
      $("campos-globais").append(card);
    }
    recalcularLocal(); renderPaginacao(); sincronizarSelecao(); schedulePreview();atualizar();
  }
  function emPaginaAtual(c) {
    if (!usarPaginacao || paginas.length < 2) return true;
    if (["nome_completo","cpf"].includes(c.id)) return true;
    const p = form().paginaDe ? form().paginaDe(c.field, agrupamento) : (c.field.aba || "Geral");
    return p === paginas[paginaAtual];
  }
  function localIssues() {
    const result=[];
    controls.forEach(c=>{
      const visivelCondicional = form().visible(c.field,values(c.index),c.index+1);
      const naPagina = emPaginaAtual(c);
      c.wrap.hidden = !visivelCondicional || !naPagina;
      if(!visivelCondicional || c.field.calculo || c.field.formula)return;
      const value=String(c.owner[c.id] ?? "").trim();
      let message="";
      if(c.field.obrigatorio && !value && c.field.tipo !== "CHECKBOX")message="Preencha este campo.";
      if(value && c.field.tipo === "CPF" && !form().cpfValid(value))message="CPF inválido.";
      if(value && c.field.tipo === "CNPJ" && form().cnpjValid && !form().cnpjValid(value))message="CNPJ inválido.";
      if(value && c.field.tipo === "CPF_CNPJ" && form().docValid && !form().docValid(value))message="Documento inválido: use CPF ou CNPJ válido.";
      if(value && c.field.tipo === "PIS_PASEP" && form().pisValid && !form().pisValid(value))message="PIS/PASEP inválido.";
      if(value && c.field.tipo === "EMAIL" && form().emailValid && !form().emailValid(value))message="E-mail inválido.";
      if(value && c.field.tipo === "TELEFONE" && form().telefoneValid && !form().telefoneValid(value))message="Telefone inválido: use DDD + número.";
      if(value && c.field.tipo === "ANO" && form().anoValid && !form().anoValid(value))message="Ano inválido.";
      if(value && c.field.tipo === "DATA" && !form().dateValid(value))message="Use uma data válida em DD/MM/AAAA.";
      if(value && ["MOEDA","AREA"].includes(c.field.tipo) && !form().valorNumericoValid(value))message="Use um valor numérico válido (ex. 1.234,56).";
      if(value && c.field.tipo === "INTEIRO" && !/^\d+$/.test(value.trim()))message="Use um número inteiro.";
      if(c.field.tipo === "SELECAO" && value && !c.field.opcoes.includes(value))message="Selecione uma opção válida.";
      if(message)result.push({participant:c.index+1,field:c.id,message});
    });
    // Seção sem campo visível (outra página ou condição) some junto com o título.
    document.querySelectorAll("#participantes .field-section, #campos-globais .field-section").forEach(s=>{
      s.hidden=![...s.querySelectorAll(".field")].some(f=>!f.hidden);
    });
    if(!form().dateValid(draft.globals.data_assinatura)) result.push({field:"data_assinatura",message:"Informe uma data válida."});
    if(!draft.globals.local_assinatura)result.push({field:"local_assinatura",message:"Informe o local da assinatura."});
    return result;
  }
  function atualizar() {
    const errors=[...localIssues(),...issues].filter((e,index,all)=>all.findIndex(other=>other.field===e.field&&other.participant===e.participant)===index);
    controls.forEach(c=>{
      const error=(reviewing || touched.get(c.owner)?.has(c.id)) && !c.wrap.hidden && errors.find(e=>form().canonical(e.field)===c.id && (!e.participant || e.participant===c.index+1 || c.field.escopo === "global"));
      c.input.disabled=busy(); c.error.hidden=!error; c.error.textContent=error ? error.message || "Confira o valor e o formato deste campo." : "";
      if(error)c.input.setAttribute("aria-invalid","true");else c.input.removeAttribute("aria-invalid");
    });
    ["data_assinatura","local_assinatura"].forEach(id=>{
      const input=$(id.replaceAll("_","-")),error=$(input.id+"-erro");
      const issue=(reviewing||touchedGlobals.has(id))&&errors.find(e=>e.field===id);
      error.hidden=!issue;error.textContent=issue?.message || "";
      if(issue)input.setAttribute("aria-invalid","true");else input.removeAttribute("aria-invalid");
    });
    const pending=[];
    if(!online())pending.push("Aguardando conexão.");
    if(composing)pending.push("Carregando campos…");
    else if(!composed)pending.push("Selecione formulários compatíveis.");
    if(previewPending)pending.push("Validando campos…");
    if(draft.people.length>maximum)pending.push("Remova participantes: limite do perfil é "+maximum+".");
    if(!draft.output_id)pending.push("Selecione a pasta de saída.");
    const targetFor=e=>controls.find(c=>c.id===form().canonical(e.field)&&!c.wrap.hidden&&(!e.participant||e.participant===c.index+1||c.field.escopo==="global"))?.input || $(e.field.replaceAll("_","-"));
    errors.forEach(e=>{const target=targetFor(e),label=target?.labels?.[0]?.textContent?.replace(" *","") || e.field;pending.push((e.participant ? "Participante "+e.participant+": " : "")+label+" — "+(e.message || "Confira o valor."));});
    $("pendencias").textContent=busy() ? "Preparando seus documentos…" : composing ? "Carregando os campos…" : previewPending ? "Conferindo os dados…" : pending.length ? "Complete os dados para gerar." : "Tudo pronto para gerar.";
    $("pendencias").classList.toggle("pronto",!pending.length&&!busy());
    $("btn-gerar").disabled=!!pending.length||busy();
    $("btn-pasta").disabled=!online()||busy();
    $("btn-adicionar").disabled=busy()||!composed||draft.people.length>=maximum;
    $("limite-participantes").textContent=draft.people.length+" de "+maximum+" participante(s)";
    const badge=$("badge-participantes");
    if(badge) badge.textContent=draft.people.length+" participante(s)";
    document.querySelectorAll('[data-editable], #lista-formularios input, #data-assinatura, #local-assinatura, #modo-simples, #modo-contrato, #modo-conversao').forEach(el=>el.disabled=busy());
    const btn=$("btn-ver-pendencias");btn.hidden=!pending.length;
    const listaPendencias=pending.slice();
    btn.onclick=()=>{
      reviewing=true;atualizar();
      // Foto 9: modal estilo Ajuda com a lista; cada item navega até o campo.
      const wrap=document.createElement("div");
      const intro=document.createElement("p");
      intro.className="hint";
      intro.textContent="Toque em um item para ir até o campo e corrigir.";
      const lista=document.createElement("div");
      lista.className="pendencias-lista";
      listaPendencias.forEach(texto=>{
        const item=document.createElement("button");
        item.type="button";
        item.className="pendencia-item";
        item.textContent=texto;
        item.addEventListener("click",()=>{
          window.ContractoUI.fecharModal();
          const erro=errors.find(e=>texto.includes(e.field) || (e.message && texto.includes(e.message)));
          irParaPendencia(erro || errors[0]);
        });
        lista.append(item);
      });
      wrap.append(intro,lista);
      window.ContractoUI.abrirModal("Revise os campos pendentes",wrap,[{texto:"Fechar",primario:true}]);
      irParaPendencia(errors[0],true);
    };
    return pending;
  }
  function irParaPendencia(erro, semFoco) {
    // Fase 2 (DESIGN.md §7): a pendência navega até a página dela e foca o
    // campo; o foco nativo já torna o campo visível (sem scrollIntoView).
    if(!erro)return;
    reviewing=true;
    const alvo=targetForGlobal(erro);
    const ctrl=alvo && controls.find(c=>c.input===alvo);
    if(ctrl && usarPaginacao && paginas.length>1){
      const pag=form().paginaDe ? form().paginaDe(ctrl.field, agrupamento) : (ctrl.field.aba || "Geral");
      const idx=paginas.indexOf(pag);
      if(idx>=0 && idx!==paginaAtual){paginaAtual=idx;renderPaginacao();atualizar();}
    }
    const destino=controls.map(c=>c.input).find(el=>el===alvo) || alvo;
    if(destino && destino.focus && !semFoco){destino.focus();}
  }
  function targetForGlobal(e) {
    return controls.find(c=>c.id===form().canonical(e.field)&&!c.wrap.hidden&&(!e.participant||e.participant===c.index+1||c.field.escopo==="global"))?.input || $(e.field.replaceAll("_","-"));
  }
  async function selecionar(ids) {
    if(busy())return;
    const isSimple = mode === "simples";
    const finalIds = isSimple ? ids : (ids[0] ? [ids[0]] : []);
    // Foto 10: guarda a última composição válida; se a nova falhar (ex.
    // conflito 409), restaura em vez de zerar os campos.
    const anterior = {selected, fields, maximum, paginas, paginaAtual, usarPaginacao, agrupamento, composed};
    changed(); const request=++compositionRevision; selected=finalIds; composing=!!finalIds.length; composed=false;
    atualizar();
    if(!finalIds.length){fields=[];render();return;}
    const r=await window.ContractoAPI.request("POST","/api/v1/profiles/compose",{profile_ids:finalIds});
    if(request!==compositionRevision)return;
    composing=false;
    if(r.status!==200){
      selected=anterior.selected; fields=anterior.fields; maximum=anterior.maximum;
      paginas=anterior.paginas; paginaAtual=anterior.paginaAtual;
      usarPaginacao=anterior.usarPaginacao; agrupamento=anterior.agrupamento;
      composed=anterior.composed;
      issues=[{field:"Formulários",message:r.data?.message || "Falha ao carregar campos. Seleção anterior mantida."}];
      if (r.status === 409 && finalIds.length > 1) {
        // Bloco 4: conflito no modo simples — mesmo id com tipos/opções distintos.
        const nomes = finalIds.map(id => { const p = catalog.find(x => x.profile_id === id); return p ? (p.name || id) : id; });
        const detalhe = document.createElement("div");
        const intro = document.createElement("p");
        intro.textContent = "Os formulários selecionados definem o mesmo campo interno de formas diferentes: " + nomes.join(" × ") + ". " + (r.data?.message || "");
        const dica = document.createElement("p");
        dica.className = "hint";
        dica.textContent = "Ajuste um dos nomes internos nas configurações de perfis ou selecione formulários compatíveis.";
        detalhe.append(intro, dica);
        window.ContractoUI.abrirModal("Conflito entre formulários", detalhe, [{texto: "Entendi", primario: true}]);
      } else if (!anterior.composed) {
        window.ContractoUI.toast(r.data?.message || "Falha ao carregar campos.", "error");
      } else {
        window.ContractoUI.toast("Seleção incompatível — mantidos os formulários anteriores.", "warning");
      }
      render();
      return;
    }
    fields=r.data.fields || []; draft.computed=[]; maximum=r.data.max_participants || 1;
    usarPaginacao=!!r.data.usar_paginacao; agrupamento=r.data.agrupamento_paginas || {};
    paginas=r.data.paginas || resolverPaginas(fields, agrupamento); paginaAtual=0;
    ultimaComposicao=r.data || null;
    if(catalog.some(p=>finalIds.includes(p.profile_id)&&p.mode === "contrato") && !fields.some(f=>f.id === "endereco"))fields.push({id:"endereco",tipo:"TEXTO",rotulo:"Endereço",obrigatorio:true});
    composed=true;render();
  }
  function mostrarCarregamentoModelos(texto) {
    const lista = $("lista-formularios"), seletor = $("seletor-modelos");
    if (seletor) { seletor.replaceChildren(); seletor.setAttribute("aria-busy", "true"); }
    if (!lista) return;
    lista.replaceChildren();
    lista.setAttribute("aria-busy", "true");
    const status = document.createElement("div");
    status.className = "loading-status";
    status.setAttribute("role", "status");
    const giro = document.createElement("span");
    giro.className = "spinner";
    giro.setAttribute("aria-hidden", "true");
    const msg = document.createElement("span");
    msg.textContent = texto || "Buscando modelos…";
    status.append(giro, msg);
    const skel = document.createElement("div");
    skel.className = "skeleton";
    skel.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 3; i++) skel.append(document.createElement("span"));
    lista.append(status, skel);
  }
  function mostrarErroModelos() {
    const lista = $("lista-formularios");
    if (!lista) return;
    lista.replaceChildren();
    lista.removeAttribute("aria-busy");
    const box = document.createElement("div");
    box.className = "modelos-erro";
    const msg = document.createElement("span");
    msg.setAttribute("role", "alert");
    msg.textContent = "Não foi possível carregar os modelos. Verifique a conexão com o serviço local.";
    const retry = document.createElement("button");
    retry.type = "button";
    retry.id = "btn-recarregar-modelos";
    retry.className = "btn btn-secondary btn-sm";
    retry.textContent = "↻ Tentar novamente";
    retry.addEventListener("click", carregar);
    box.append(msg, retry);
    lista.append(box);
  }
  function finalizarCarregamentoModelos() {
    ["lista-formularios", "seletor-modelos"].forEach(id => {
      const el = $(id);
      if (el) el.removeAttribute("aria-busy");
    });
  }
  async function carregar() {
    mostrarCarregamentoModelos();
    const r=await window.ContractoAPI.request("GET","/api/v1/profiles");
    if(r.status!==200){issues=[{field:"Formulários",message:"Não foi possível carregar o catálogo."}];mostrarErroModelos();atualizar();return;}
    catalog=r.data;loaded=true;
    renderProfilesList();
    const defaultProfile = catalog.find(p=>p.mode === "contrato") || catalog[0];
    await selecionar(mode === "simples" ? [] : (defaultProfile?.profile_id ? [defaultProfile.profile_id] : []));
  }
  async function recarregarCatalogo() {
    // Re-GET sem resetar a seleção (refresh_profiles preserva os IDs por
    // identificador/nome): novo perfil aparece sem perder o trabalho atual.
    const r = await window.ContractoAPI.request("GET", "/api/v1/profiles");
    if (r.status !== 200) return;
    catalog = r.data;
    renderProfilesList();
    atualizar();
  }
  const NOMES_EXIBICAO = { "Seguro": "Form Seguro" };
  const nomeExibicao = (p) => NOMES_EXIBICAO[p.name] || NOMES_EXIBICAO[p.nome] || p.name || p.nome || p.profile_id;
  function renderProfilesList() {
    $("lista-formularios").replaceChildren();
    finalizarCarregamentoModelos();
    const isSimple = mode === "simples";
    const todosWrap = $("wrapper-selecionar-todos");
    const explicacao = $("modo-explicacao");
    const titulo = $("titulo-selecao-secao");
    if(todosWrap) { todosWrap.hidden = !isSimple; todosWrap.style.textAlign = "right"; }
    if(titulo) titulo.textContent = isSimple ? "Formulários simples" : "Modelo de contrato";
    if(explicacao) explicacao.innerHTML = isSimple ? "No modo <strong>Simples</strong> selecione um ou mais formulários em lote." : "No modo <strong>Contrato</strong> escolha apenas 1 contrato.";
    const filtrados = catalog.filter(p => isSimple ? (p.mode === "formulario_simples" || catalog.every(item => item.mode !== "formulario_simples")) : (p.mode === "contrato" || catalog.every(item => item.mode !== "contrato")));
    if(!filtrados.length){
      const msg = document.createElement("p"); msg.className="hint"; msg.textContent="Nenhum perfil disponível para este modo."; $("lista-formularios").append(msg); return;
    }
    // Foto 2: no modo Contrato os modelos são botões lado a lado (sem radio
    // nativo, sem linha inteira); o Simples mantém checkboxes p/ multisseleção.
    const seletor = $("seletor-modelos");
    if (!isSimple) {
      if (seletor) seletor.hidden = false;
      $("lista-formularios").replaceChildren();
      renderSeletorLista(filtrados, isSimple);
      return;
    }
    if (seletor) { seletor.replaceChildren(); seletor.hidden = true; }
    const grid = document.createElement("div");
    grid.className = "forms-grid";
    filtrados.forEach(p=>{
      const label=document.createElement("label");
      label.className = "form-card";
      const input=document.createElement("input");
      input.type = "checkbox";
      input.value=p.profile_id;
      input.checked=selected.includes(p.profile_id);
      input.addEventListener("change",()=>{
        if(busy()){input.checked=!input.checked;return;}
        selecionar([...grid.querySelectorAll("input:checked")].map(el=>el.value));
      });
      const corpo = document.createElement("span");
      corpo.className = "form-card-corpo";
      const nome = document.createElement("strong");
      nome.textContent = nomeExibicao(p);
      const meta = document.createElement("span");
      meta.className = "hint";
      const nCampos = (p.fields || []).length;
      meta.textContent = (p.max_participants > 1 ? "Até " + p.max_participants + " participantes" : "1 participante") + (nCampos ? " · " + nCampos + " campos" : "");
      corpo.append(nome, meta);
      label.append(input, corpo);
      grid.append(label);
    });
    $("lista-formularios").append(grid);
    // Fase 0: #buscar-perfis pertence à tela Perfis e já é gerenciado por
    // ligar()/carregarTelaPerfis() via renderProfilesManagement. Amarrá-lo
    // aqui a renderProfilesList() disparava dois renders conflitantes.
  }

  function renderSeletorLista(filtrados, isSimple) {
    const host = $("seletor-modelos");
    if (!host) return;
    host.replaceChildren();
    const count = document.createElement("span");
    count.className = "seletor-count";
    count.textContent = filtrados.length + " modelo" + (filtrados.length !== 1 ? "s" : "");
    host.append(count);
    filtrados.forEach(p => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "seletor-item";
      btn.value = p.profile_id;
      btn.setAttribute("aria-pressed", selected.includes(p.profile_id) ? "true" : "false");
      btn.textContent = (typeof nomeExibicao === "function" ? nomeExibicao(p) : (p.name || p.profile_id));
      btn.addEventListener("click", () => {
        if (busy()) return;
        if (isSimple) {
          const ja = selected.includes(p.profile_id);
          selecionar(ja ? selected.filter(id => id !== p.profile_id) : [...selected, p.profile_id]);
        } else {
          selecionar(btn.getAttribute("aria-pressed") === "true" ? [] : [p.profile_id]);
        }
      });
      host.append(btn);
    });
  }
  function pacoteProcesso() {
    // Pacote atual para o processamento (contrato ProcessInput da API local).
    if(!composed || !draft.output_id) return null;
    return {participants:form().participants(draft,fields),output_id:draft.output_id};
  }
  async function gerar() {
    if(atualizar().length||busy())return;
    const snapshot={profile_ids:[...selected],participants:form().participants(draft,fields),output_id:draft.output_id,revision};
    try {
      const forms = window.ContractoEtapa2?.formsSelecionados?.();
      if (Array.isArray(forms) && forms.length) snapshot.forms_selecionados = forms;
    } catch (_) {}
    const r=await window.ContractoEtapa2.gerar(snapshot);
    // Não prender na Conferência — com o trabalho aceito, avança
    // para Concluir onde o andamento é visível.
    if(r && r.status===202){window.ContractoUI.mostrarTela("etapa2");return;}
    if(r && r.status!==202){issues=r.data?.issues?.length ? r.data.issues : [{field:"Geração",message:r.data?.message || "Não foi possível gerar."}];atualizar();window.ContractoUI.toast(r.data?.message || "Confira os campos indicados.","error");controls.find(c=>c.input.hasAttribute("aria-invalid")&&!c.wrap.hidden)?.input.focus();}
  }
  async function conferir() {
    reviewing = true;
    const pendentes = atualizar();
    if (!selected.length) {
      window.ContractoUI.toast("Selecione ao menos um modelo para conferir.", "warning");
      window.ContractoUI.mostrarTela("inicio");
      return;
    }
    if (pendentes.length > 0) {
      window.ContractoUI.toast("Existem pendências no formulário. Revise os campos antes de avançar.", "warning");
      const btn = $("btn-ver-pendencias");
      if (btn && !btn.hidden) btn.click();
      else window.ContractoUI.mostrarTela("inicio");
      return;
    }
    // Revalidação servidor antes de confirmar a conferência.
    try {
      const r = await window.ContractoAPI.request("POST", "/api/v1/profiles/preview", {profile_ids: selected, participants: form().participants(draft, fields)});
      if (r.status === 200 && (r.data.issues || []).length) {
        issues = r.data.issues;
        atualizar();
        window.ContractoUI.toast("O servidor apontou pendências. Revise os campos.", "warning");
        return;
      }
      if (r.status !== 200) {
        window.ContractoUI.toast("Não foi possível revalidar. Confira a conexão e tente de novo.", "warning");
        return;
      }
    } catch (_) {
      window.ContractoUI.toast("Sem conexão para conferir. Tente novamente.", "error");
      return;
    }

    window.ContractoConferencia.renderizar({ selected, catalog, fields, draft, maximum, agrupamento, nomeExibicao, form, values });

    const btnVoltar = $("btn-conferir-voltar");
    const btnConfirmar = $("btn-conferir-confirmar");
    if (btnVoltar && !btnVoltar.dataset.ligado) {
      btnVoltar.dataset.ligado = "1";
      btnVoltar.addEventListener("click", () => window.ContractoUI.mostrarTela("inicio"));
    }
    if (btnConfirmar && !btnConfirmar.dataset.ligado) {
      btnConfirmar.dataset.ligado = "1";
      btnConfirmar.addEventListener("click", () => {
        gerar();
      });
    }

    // Reflete a composição atual nos formulários/extras da Etapa 2 antes de abrir.
    try { await window.ContractoEtapa2?.sincronizarContexto?.(); } catch (_) {}
    window.ContractoUI.mostrarTela("conferir");
  }

  function preservarAtivo() {
    // Fase 0: espelha o legado (chk_preservar_dados): quando marcado, o reset
    // mantém pessoas + assinatura/destino; caso contrário, limpa tudo.
    try { return localStorage.getItem("contracto-preservar") === "1"; }
    catch (_) { return !!$("chk-preservar-dados")?.checked; }
  }

  function novoTrabalho() {
    window.ContractoUI.abrirModal(
      "Iniciar novo trabalho",
      "<p>Deseja reiniciar a preparação de documentos?</p>",
      [
        {
          texto: "Preservar destino e data",
          aoClicar: () => {
            window.ContractoEtapa2?.recomecar?.();
            if (preservarAtivo()) {
              // Mantém pessoas e assinatura/destino; descarta só o trabalho.
              selected = []; fields = []; composed = false;
              changed(); render();
            } else {
              draft.people = [{ nome_completo: "", cpf: "" }];
              draft.globals.data_assinatura = "";
              draft.globals.local_assinatura = "";
              draft.output_id = null;
              $("pasta-saida").value = "";
              selected = []; fields = []; composed = false;
              changed(); render();
            }
            window.ContractoUI.mostrarTela("inicio");
          }
        },
        { texto: "Cancelar" }
      ]
    );
  }

  function limparCampos() {
    if (preservarAtivo()) {
      // Preservar ligado: mantém o preenchimento; só invalida o trabalho
      // gerado para que "Gerar" reflita o estado atual.
      window.ContractoEtapa2?.invalidar?.();
      window.ContractoEtapa2.atualizar();
      window.ContractoUI.toast("Preservar dados ativo: preenchimento mantido.", "info");
      return;
    }
    draft.people = [{nome_completo:"",cpf:""}];
    draft.globals.data_assinatura = "";
    draft.globals.local_assinatura = "";
    const pasta = $("pasta-saida");
    if (pasta) pasta.value = "";
    fields = []; composed = false; maximum = 1; selected = [];
    renderProfilesList();
    if (mode === "contrato") {
      const contratoDefault = catalog.find(p => p.mode === "contrato") || catalog[0];
      if (contratoDefault) selecionar([contratoDefault.profile_id]);
    }
    window.ContractoEtapa2.atualizar();
    window.ContractoUI.toast("Campos limpos.", "success");
  }

  function ligar() {
    // Pinta o skeleton imediatamente: a ponte pode levar segundos no boot.
    mostrarCarregamentoModelos();
    const btnNovoTrabalho = $("btn-novo-trabalho");
    if (btnNovoTrabalho) btnNovoTrabalho.addEventListener("click", novoTrabalho);
    const btnLimparCampos = $("btn-limpar-campos");
    if (btnLimparCampos) btnLimparCampos.addEventListener("click", limparCampos);
    const chkPreservar = $("chk-preservar-dados");
    if (chkPreservar) {
      try { chkPreservar.checked = localStorage.getItem("contracto-preservar") === "1"; } catch (_) {}
      chkPreservar.addEventListener("change", () => {
        try { localStorage.setItem("contracto-preservar", chkPreservar.checked ? "1" : "0"); } catch (_) {}
      });
    }
    $("btn-gerar").addEventListener("click", conferir);
    const todos=$("btn-selecionar-todos");
    if(todos)todos.addEventListener("click",()=>{
      if(busy()||!catalog.length||mode!=="simples")return;
      const simplesIds = catalog.filter(p=>p.mode === "formulario_simples" || catalog.every(item=>item.mode!=="formulario_simples")).map(p=>p.profile_id);
      selecionar(simplesIds);
    });
    document.querySelectorAll("[data-ir]").forEach(btn=>{
      btn.addEventListener("click",()=>{
        window.ContractoUI.mostrarTela("inicio");
        const alvo=document.getElementById(btn.dataset.ir);
        if(alvo){alvo.scrollIntoView({block:"center"});const foco=alvo.matches("button,input")?alvo:alvo.querySelector("button,input");if(foco)foco.focus();}
      });
    });
    $("btn-adicionar").addEventListener("click",()=>{if(busy()||draft.people.length>=maximum)return;draft.people.push({nome_completo:"",cpf:""});changed();render();});
    try {
      const salvoLocal = localStorage.getItem("contracto-local-assinatura");
      if(salvoLocal && !draft.globals.local_assinatura) {
        draft.globals.local_assinatura = salvoLocal;
        const inputLocal = $("local-assinatura");
        if(inputLocal) inputLocal.value = salvoLocal;
      }
    } catch(e) {}
    // Paridade Tk (mw_etapa1: entry_local pré-preenchido com local_padrao):
    // o padrão do backend vale quando o usuário ainda não digitou nada.
    if (window.ContractoAPI && window.ContractoAPI.getSettings) {
      window.ContractoAPI.getSettings().then(r => {
        const padrao = r.status === 200 && r.data && typeof r.data.local_padrao === "string" ? r.data.local_padrao.trim() : "";
        if (padrao && !draft.globals.local_assinatura) {
          draft.globals.local_assinatura = padrao;
          const inputLocal = $("local-assinatura");
          if (inputLocal && !inputLocal.value) inputLocal.value = padrao;
          changed();
        }
      }).catch(() => {});
    }
    ["data_assinatura","local_assinatura"].forEach(id=>{const input=$(id.replaceAll("_","-"));input.addEventListener("input",e=>{let val=e.target.value;if(id==="data_assinatura")val=form().formatDateProgressive(val);input.value=val;draft.globals[id]=val.trim();if(id==="local_assinatura"){try{localStorage.setItem("contracto-local-assinatura",val.trim());}catch(e){}}changed();});input.addEventListener("blur",()=>{touchedGlobals.add(id);atualizar();});});
    const calBtn=$("btn-calendario-data");
    const dateInput=$("data-assinatura");
    if(calBtn && dateInput) calBtn.addEventListener("click",()=>window.ContractoCalendario.abrir(dateInput,val=>{draft.globals.data_assinatura=val;changed();}));
    $("btn-pasta").addEventListener("click",async()=>{if(busy())return;try{const r=await window.ContractoAPI.selectOutput();if(r.cancelled)return;if(r.selection_id){draft.output_id=r.selection_id;$("pasta-saida").value=r.name || "Pasta selecionada";changed();}else window.ContractoUI.toast("Não foi possível selecionar a pasta.","error");}catch(_){window.ContractoUI.toast("Falha ao abrir o seletor.","error");}});
    ["simples","contrato"].forEach(name=>$("modo-"+name).addEventListener("click",()=>{
      if(busy())return;mode=name;
      ["simples","contrato"].forEach(n=>{if(n===name)$("modo-"+n).setAttribute("aria-current","page");else $("modo-"+n).removeAttribute("aria-current");});
      $("modo-conversao")?.removeAttribute("aria-current");
      window.ContractoUI.mostrarTela("inicio");
      selected=[];fields=[];composed=false;maximum=1;
      renderProfilesList();
      if(mode === "contrato") {
        const contratoDefault = catalog.find(p=>p.mode === "contrato") || catalog[0];
        if(contratoDefault) selecionar([contratoDefault.profile_id]);
      } else {
        selecionar([]);
      }
      window.ContractoEtapa2.atualizar();
    }));
    window.ContractoPerfis.ligar();

    carregar();
  }

  // Skeleton visível antes mesmo da ponte: evita o texto morto no arranque.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      if (!catalog.length && $("lista-formularios") && !$("lista-formularios").children.length) mostrarCarregamentoModelos();
    });
  }
  window.ContractoPerfis.iniciar({
    catalogo: () => catalog,
    definirCatalogo: (novo) => { catalog = novo; },
    // CRUD na aba Perfis também atualiza a Etapa 1 sem perder a seleção.
    aoAtualizarCatalogo: () => { if (loaded) { renderProfilesList(); atualizar(); } },
    recarregarCatalogo,
    recarregar: carregar,
    nomeExibicao
  });
  window.ContractoEtapa1={
    ligar,
    atualizar,
    conferir,
    novoTrabalho,
    carregarTelaPerfis:()=>window.ContractoPerfis.carregarTela(),
    pacoteProcesso,
    composto:()=>composed,
    modo:()=>mode,
    perfilIds:()=>[...selected],
    composicao:()=>ultimaComposicao,
    reconectar:()=>!loaded ? carregar() : (!composed && selected.length ? selecionar(selected) : (schedulePreview(),atualizar()))
  };
})();
