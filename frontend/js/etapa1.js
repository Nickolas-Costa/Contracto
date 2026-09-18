/* Rascunho preservado por campo e participante; DOM apenas apresenta valores. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id), form = () => window.ContractoForm;
  const draft = {people: [{nome_completo:"",cpf:""}], globals:{data_assinatura:"",local_assinatura:""}};
  let catalog = [], selected = [], fields = [], maximum = 1, revision = 0, compositionRevision = 0;
  let composing = false, composed = false, loaded = false, bound = false, issues = [], mode = "avancado";
  const controls = [];
  const touched = new WeakMap(), touchedGlobals = new Set();
  let reviewing = false;
  function touch(owner, id) { if(!touched.has(owner))touched.set(owner,new Set());touched.get(owner).add(id); }
  let previewTimer=null, previewPending=false;
  const busy = () => window.ContractoEtapa2?.ocupado() || false;
  const online = () => window.ContractoApp?.pronto() || false;
  function changed() {
    issues = []; revision++;
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
  function fieldControl(field,index,host) {
    const id = form().canonical(field.id), global = field.escopo === "global";
    const owner = global ? draft.globals : draft.people[index];
    if (owner[id] === undefined) owner[id] = field.valor_padrao ?? "";
    const wrap = document.createElement("div"); wrap.className = "field";
    if(id === "endereco" || field.tipo === "TEXTO_LONGO" || field.tipo === "MULTILINHA") wrap.classList.add("field-wide");
    const isTextarea = field.tipo === "TEXTO_LONGO" || field.tipo === "MULTILINHA";
    const label = document.createElement("label");
    const input = document.createElement(field.tipo === "SELECAO" ? "select" : (isTextarea ? "textarea" : "input"));
    if (isTextarea) input.rows = 3;
    input.id = "campo-" + (global ? "global" : index) + "-" + id;
    label.htmlFor = input.id; label.textContent = (field.rotulo || id) + (field.obrigatorio && !field.calculo ? " *" : "");
    input.autocomplete = "off";
    if (field.tipo === "SELECAO") {
      for (const value of ["",...(field.opcoes || [])]) {
        const option=document.createElement("option"); option.value=value; option.textContent=value || "Selecione"; input.append(option);
      }
    } else if (field.tipo === "CHECKBOX") {
      input.type="checkbox"; const options=field.opcoes?.length ? field.opcoes : ["SIM","NÃO"];
      if (owner[id] === "") owner[id]=options[options.length-1];
      input.checked = owner[id] === options[0] || owner[id] === true;
    } else {
      input.type = "text";
      if (["CPF","CNPJ","CPF_CNPJ","INTEIRO","ANO","DATA","MOEDA","AREA"].includes(field.tipo)) input.inputMode = "decimal";
      if (field.tipo === "DATA") input.placeholder="DD/MM/AAAA";
      input.maxLength = 4000;
    }
    if (field.tipo !== "CHECKBOX") input.value=owner[id];
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
      }
      owner[id] = val.trim();
      changed();
    });
    wrap.append(label,input,error); host.append(wrap);
    if(field.calculo){const note=document.createElement("p");note.className="field-note";note.id=input.id+"-nota";note.textContent="Calculado a partir dos dados informados.";wrap.append(note);input.setAttribute("aria-describedby",error.id+" "+note.id);}
    controls.push({field,index,id,owner,wrap,input,error});
  }
  function group(card, title) {
    const section=document.createElement("fieldset");section.className="field-section";
    const legend=document.createElement("legend");legend.textContent=title;
    const grid=document.createElement("div");grid.className="field-grid";
    section.append(legend,grid);card.append(section);return grid;
  }
  function render() {
    controls.length=0; $("participantes").replaceChildren(); $("campos-globais").replaceChildren();
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
      if(details.length){const grid=group(card,"Dados do formulário");details.forEach(f=>fieldControl(f,index,grid));}
      if (index) {
        const remove=document.createElement("button"); remove.type="button"; remove.className="btn btn-subtle"; remove.textContent="Remover";remove.setAttribute("aria-label","Remover participante "+(index+1));
        remove.dataset.editable="true";
        remove.addEventListener("click",()=>{if(busy())return; window.ContractoUI.abrirModal("Remover participante?","Os dados deste participante serão removidos do rascunho.",[{texto:"Manter participante"},{texto:"Remover",aoClicar:()=>{draft.people.splice(index,1);changed();render();$("btn-adicionar").focus();}}]);}); header.append(remove);
      }
      $("participantes").append(card);
    });
    const globals=fields.filter(f=>f.escopo === "global" && !["nome_completo","cpf","data_assinatura","local_assinatura"].includes(form().canonical(f.id)));
    if(globals.length){const card=document.createElement("div");card.className="card";const title=document.createElement("h2");title.textContent="Dados compartilhados";card.append(title);const grid=document.createElement("div");grid.className="field-grid";card.append(grid);globals.forEach(f=>fieldControl(f,0,grid));$("campos-globais").append(card);}
    schedulePreview();atualizar();
  }
  function localIssues() {
    const result=[];
    controls.forEach(c=>{
      const show=form().visible(c.field,values(c.index),c.index+1); c.wrap.hidden=!show;
      if(!show || c.field.calculo)return;
      const value=String(c.owner[c.id] ?? "").trim();
      let message="";
      if(c.field.obrigatorio && !value && c.field.tipo !== "CHECKBOX")message="Preencha este campo.";
      if(value && c.field.tipo === "CPF" && !form().cpfValid(value))message="CPF inválido.";
      if(value && c.field.tipo === "DATA" && !form().dateValid(value))message="Use uma data válida em DD/MM/AAAA.";
      if(c.field.tipo === "SELECAO" && value && !c.field.opcoes.includes(value))message="Selecione uma opção válida.";
      if(message)result.push({participant:c.index+1,field:c.id,message});
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
    $("resumo-formularios").textContent=catalog.filter(p=>selected.includes(p.profile_id)).map(p=>p.name).join(", ") || "Nenhum selecionado";
    $("resumo-participantes").textContent=draft.people.map((p,i)=>p.nome_completo || "Participante "+(i+1)).join(" · ");
    $("resumo-destino").textContent=$("pasta-saida").value || "Escolha uma pasta";
    document.querySelectorAll('[data-editable], #lista-formularios input, #data-assinatura, #local-assinatura, #modo-simples, #modo-avancado').forEach(el=>el.disabled=busy());
    const btn=$("btn-ver-pendencias");btn.hidden=!pending.length;
    btn.onclick=()=>{
      reviewing=true;atualizar();const list=document.createElement("ul"),offset=pending.length-errors.length;
      pending.forEach((p,i)=>{const li=document.createElement("li"),target=i>=offset ? targetFor(errors[i-offset]) : p.includes("pasta") ? $("btn-pasta") : null;
        if(target){const link=document.createElement("button");link.className="btn-link";link.type="button";link.textContent=p;link.addEventListener("click",()=>{window.ContractoUI.fecharModal();target.focus();target.scrollIntoView({block:"center"});});li.append(link);}else li.textContent=p;list.append(li);});
      window.ContractoUI.abrirModal("Revise os dados",list,[{texto:"Voltar ao formulário"}]);
    };
    return pending;
  }
  async function selecionar(ids) {
    if(busy())return;
    const isSimple = mode === "simples";
    const finalIds = isSimple ? ids : (ids[0] ? [ids[0]] : []);
    changed(); const request=++compositionRevision; selected=finalIds; composing=!!finalIds.length; composed=false;
    atualizar();
    if(!finalIds.length){fields=[];render();return;}
    const r=await window.ContractoAPI.request("POST","/api/v1/profiles/compose",{profile_ids:finalIds});
    if(request!==compositionRevision)return;
    composing=false;
    if(r.status!==200){issues=[{field:"Formulários",message:r.data?.message || "Falha ao carregar campos."}];atualizar();return;}
    fields=r.data.fields || []; draft.computed=[]; maximum=r.data.max_participants || 1;
    if(catalog.some(p=>finalIds.includes(p.profile_id)&&p.mode === "contrato") && !fields.some(f=>f.id === "endereco"))fields.push({id:"endereco",tipo:"TEXTO",rotulo:"Endereço",obrigatorio:true});
    composed=true;render();
  }
  async function carregar() {
    const r=await window.ContractoAPI.request("GET","/api/v1/profiles");
    if(r.status!==200){issues=[{field:"Formulários",message:"Não foi possível carregar o catálogo."}];atualizar();return;}
    catalog=r.data;loaded=true;
    renderProfilesList();
    const defaultProfile = catalog.find(p=>p.mode === "contrato") || catalog[0];
    await selecionar(mode === "simples" ? [] : (defaultProfile?.profile_id ? [defaultProfile.profile_id] : []));
  }
  function renderProfilesList() {
    $("lista-formularios").replaceChildren();
    const isSimple = mode === "simples";
    const todosWrap = $("wrapper-selecionar-todos");
    const explicacao = $("modo-explicacao");
    const titulo = $("titulo-selecao-secao");
    if(todosWrap) todosWrap.hidden = !isSimple;
    if(titulo) titulo.textContent = isSimple ? "Formulários simples" : "Modelo de contrato";
    if(explicacao) explicacao.innerHTML = isSimple ? "No modo <strong>Só gerar</strong> selecione um ou mais formulários em lote." : "No modo <strong>Gerar e organizar</strong> escolha apenas 1 contrato.";
    const filtrados = catalog.filter(p => isSimple ? (p.mode === "formulario_simples" || catalog.every(item => item.mode !== "formulario_simples")) : (p.mode === "contrato" || catalog.every(item => item.mode !== "contrato")));
    if(!filtrados.length){
      const msg = document.createElement("p"); msg.className="hint"; msg.textContent="Nenhum perfil disponível para este modo."; $("lista-formularios").append(msg); return;
    }
    filtrados.forEach(p=>{
      const label=document.createElement("label");
      const input=document.createElement("input");
      input.type = isSimple ? "checkbox" : "radio";
      input.name = isSimple ? "" : "profile-radio";
      input.value=p.profile_id;
      input.checked=selected.includes(p.profile_id);
      input.addEventListener("change",()=>{
        if(busy()){input.checked=!input.checked;return;}
        if(isSimple){
          selecionar([...$("lista-formularios").querySelectorAll("input:checked")].map(el=>el.value));
        }else{
          selecionar(input.checked ? [p.profile_id] : []);
        }
      });
      label.append(input,document.createTextNode(" "+p.name));
      $("lista-formularios").append(label);
    });
    const search=$("buscar-perfis");
    if(search&&!search.dataset.ligado){search.dataset.ligado="1";search.addEventListener("input",()=>renderProfilesList());}
  }
  async function gerar() {
    if(atualizar().length||busy())return;
    const snapshot={profile_ids:[...selected],participants:form().participants(draft,fields),output_id:draft.output_id,revision};
    const r=await window.ContractoEtapa2.gerar(snapshot);
    if(r && r.status!==202){issues=r.data?.issues?.length ? r.data.issues : [{field:"Geração",message:r.data?.message || "Não foi possível gerar."}];atualizar();window.ContractoUI.toast(r.data?.message || "Confira os campos indicados.","error");controls.find(c=>c.input.hasAttribute("aria-invalid")&&!c.wrap.hidden)?.input.focus();}
  }
  function abrirCalendario(input) {
    const today = new Date();
    const year = today.getFullYear(), month = today.getMonth(), day = today.getDate();
    const months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const diasSemana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
    const overlay = document.createElement("div");
    overlay.className = "calendario-overlay";
    overlay.innerHTML = `
      <div class="calendario-card">
        <div class="calendario-header">
          <button type="button" class="cal-btn" data-acao="prev">◄</button>
          <strong id="cal-mes-ano">${months[month]} ${year}</strong>
          <button type="button" class="cal-btn cal-fechar" data-acao="fechar">✕</button>
        </div>
        <div class="cal-dias-semana">
          ${diasSemana.map(d=>`<span>${d}</span>`).join("")}
        </div>
        <div class="cal-grid" id="cal-grid" tabindex="0"></div>
      </div>
    `;
    document.body.append(overlay);
    function renderCal(y, m) {
      const firstDay = new Date(y, m, 1).getDay();
      const lastDate = new Date(y, m + 1, 0).getDate();
      const grid = overlay.querySelector("#cal-grid");
      grid.dataset.ano = y; grid.dataset.mes = m;
      overlay.querySelector("#cal-mes-ano").textContent = `${months[m]} ${y}`;
      grid.innerHTML = "";
      for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement("span"); grid.append(empty);
      }
      for (let d = 1; d <= lastDate; d++) {
        const btn = document.createElement("button");
        btn.type = "button"; btn.className = "cal-dia";
        if (d === day && m === month && y === year) btn.classList.add("hoje");
        btn.textContent = d; btn.dataset.dia = d;
        grid.append(btn);
      }
    }
    renderCal(year, month);
    overlay.addEventListener("click", e => {
      const btn = e.target.closest("button");
      if (!btn) return;
      if (btn.dataset.acao === "fechar") { overlay.remove(); input.focus(); return; }
      const grid = overlay.querySelector("#cal-grid");
      if (btn.dataset.acao === "prev") { let m = Number(grid.dataset.mes) - 1, y = Number(grid.dataset.ano); if (m < 0) { m = 11; y--; } renderCal(y, m); return; }
      if (btn.dataset.acao === "next") { let m = Number(grid.dataset.mes) + 1, y = Number(grid.dataset.ano); if (m > 11) { m = 0; y++; } renderCal(y, m); return; }
      if (btn.classList.contains("cal-dia")) {
        const d = Number(btn.dataset.dia), m = Number(grid.dataset.mes), y = Number(grid.dataset.ano);
        const val = `${String(d).padStart(2,"0")}/${String(m+1).padStart(2,"0")}/${y}`;
        input.value = val;
        draft.globals.data_assinatura = val;
        changed();
        overlay.remove();
        input.focus();
      }
    });
    overlay.addEventListener("keydown", e => { if (e.key === "Escape") { overlay.remove(); input.focus(); } });
    overlay.querySelector(".cal-grid").focus();
  }
  function conferir() {
    atualizar();
    if (!selected.length) {
      window.ContractoUI.toast("Selecione ao menos um modelo para conferir.", "warning");
      window.ContractoUI.mostrarTela("inicio");
      return;
    }
    const val = form().participants(draft, fields);
    const pendentes = issues.filter(i => i.severity === "error");
    if (pendentes.length > 0) {
      window.ContractoUI.toast("Existem pendências no formulário. Revise os campos antes de avançar.", "warning");
      const btn = $("btn-ver-pendencias");
      if (btn && !btn.hidden) btn.click();
      window.ContractoUI.mostrarTela("inicio");
      return;
    }

    const container = $("corpo-conferencia");
    if (container) {
      container.innerHTML = "";
      const infoBox = document.createElement("div");
      infoBox.className = "card-header";
      infoBox.innerHTML = `<div><strong style="font-size:16px;">Modelos selecionados:</strong> <p class="hint">${selected.map(id => catalog.find(p => p.profile_id === id)?.nome || id).join(", ")}</p></div>`;
      container.appendChild(infoBox);

      const dl = document.createElement("dl");
      dl.className = "field-grid";
      dl.style.gridTemplateColumns = "repeat(auto-fit, minmax(260px, 1fr))";
      dl.style.margin = "16px 0";

      const dtData = document.createElement("dt"); dtData.innerHTML = "<strong>Data da assinatura:</strong> " + (draft.globals.data_assinatura || "Não informada");
      const dtLocal = document.createElement("dt"); dtLocal.innerHTML = "<strong>Local da assinatura:</strong> " + (draft.globals.local_assinatura || "Não informado");
      const dtDestino = document.createElement("dt"); dtDestino.className = "field-wide"; dtDestino.innerHTML = "<strong>Salvar em:</strong> " + ($("pasta-saida")?.value || "Nenhuma pasta selecionada");

      dl.append(dtData, dtLocal, dtDestino);
      container.appendChild(dl);

      draft.people.forEach((p, idx) => {
        const pBox = document.createElement("fieldset");
        pBox.className = "field-section";
        const legend = document.createElement("legend");
        legend.textContent = idx ? "Participante " + (idx + 1) : "Participante Principal";
        pBox.appendChild(legend);

        const pGrid = document.createElement("div");
        pGrid.className = "field-grid";
        pGrid.innerHTML = `
          <div><strong>Nome:</strong> ${p.nome_completo || "Pendente"}</div>
          <div><strong>CPF:</strong> ${p.cpf || "Pendente"}</div>
        `;

        fields.forEach(f => {
          const id = form().canonical(f.id);
          if (f.escopo !== "global" && p[id] && !["nome_completo", "cpf"].includes(id)) {
            const item = document.createElement("div");
            item.innerHTML = `<strong>${f.rotulo || id}:</strong> ${p[id]}`;
            pGrid.appendChild(item);
          }
        });

        pBox.appendChild(pGrid);
        container.appendChild(pBox);
      });
    }

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

    window.ContractoUI.mostrarTela("conferir");
  }

  function novoTrabalho() {
    window.ContractoUI.abrirModal(
      "Iniciar novo trabalho",
      "<p>Deseja reiniciar a preparação de documentos?</p>",
      [
        {
          texto: "Preservar destino e data",
          aoClicar: () => {
            draft.people = [{ nome_completo: "", cpf: "" }];
            selected = [];
            fields = [];
            composed = false;
            changed();
            render();
            window.ContractoUI.mostrarTela("inicio");
          }
        },
        {
          texto: "Limpar tudo",
          aoClicar: () => {
            draft.people = [{ nome_completo: "", cpf: "" }];
            draft.globals.data_assinatura = "";
            draft.globals.local_assinatura = "";
            draft.output_id = null;
            $("pasta-saida").value = "";
            selected = [];
            fields = [];
            composed = false;
            changed();
            render();
            window.ContractoUI.mostrarTela("inicio");
          }
        },
        { texto: "Cancelar" }
      ]
    );
  }

  function ligar() {
    const btnNovo = $("btn-novo-trabalho");
    if (btnNovo) btnNovo.addEventListener("click", novoTrabalho);
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
    ["data_assinatura","local_assinatura"].forEach(id=>{const input=$(id.replaceAll("_","-"));input.addEventListener("input",e=>{let val=e.target.value;if(id==="data_assinatura")val=form().formatDateProgressive(val);input.value=val;draft.globals[id]=val.trim();if(id==="local_assinatura"){try{localStorage.setItem("contracto-local-assinatura",val.trim());}catch(e){}}changed();});input.addEventListener("blur",()=>{touchedGlobals.add(id);atualizar();});});
    const calBtn=$("btn-calendario-data");
    const dateInput=$("data-assinatura");
    if(calBtn && dateInput) calBtn.addEventListener("click",()=>abrirCalendario(dateInput));
    $("btn-pasta").addEventListener("click",async()=>{if(busy())return;try{const r=await window.ContractoAPI.selectOutput();if(r.cancelled)return;if(r.selection_id){draft.output_id=r.selection_id;$("pasta-saida").value=r.name || "Pasta selecionada";changed();}else window.ContractoUI.toast("Não foi possível selecionar a pasta.","error");}catch(_){window.ContractoUI.toast("Falha ao abrir o seletor.","error");}});
    ["simples","avancado"].forEach(name=>$("modo-"+name).addEventListener("click",()=>{
      if(busy())return;mode=name;
      ["simples","avancado"].forEach(n=>{if(n===name)$("modo-"+n).setAttribute("aria-current","page");else $("modo-"+n).removeAttribute("aria-current");});
      selected=[];fields=[];composed=false;maximum=1;
      renderProfilesList();
      if(mode === "avancado") {
        const contratoDefault = catalog.find(p=>p.mode === "contrato") || catalog[0];
        if(contratoDefault) selecionar([contratoDefault.profile_id]);
      } else {
        selecionar([]);
      }
      window.ContractoEtapa2.atualizar();
    }));
    const btnNovoPerfil = $("btn-novo-perfil");
    if (btnNovoPerfil) btnNovoPerfil.addEventListener("click", novoPerfilModal);
    const btnImpPerfil = $("btn-importar-perfil");
    if (btnImpPerfil) btnImpPerfil.addEventListener("click", importarPerfilModal);
    const busqPerfil = $("buscar-perfis");
    if (busqPerfil && !busqPerfil.dataset.gerenciado) {
      busqPerfil.dataset.gerenciado = "1";
      busqPerfil.addEventListener("input", renderProfilesManagement);
    }

    carregar();
  }

  async function carregarTelaPerfis() {
    const r = await window.ContractoAPI.getProfiles();
    if (r.status === 200 && Array.isArray(r.data)) {
      catalog = r.data;
    }
    renderProfilesManagement();
  }

  function renderProfilesManagement() {
    const container = $("lista-perfis");
    if (!container) return;
    container.replaceChildren();

    const search = $("buscar-perfis");
    const termo = (search?.value || "").trim().toLowerCase();

    const filtrados = catalog.filter(p => {
      if (!termo) return true;
      const nome = (p.nome || p.name || "").toLowerCase();
      const modo = (p.modo_fluxo || p.mode || "").toLowerCase();
      const desc = (p.descricao || "").toLowerCase();
      return nome.includes(termo) || modo.includes(termo) || desc.includes(termo);
    });

    const vazio = $("perfis-vazio");
    if (vazio) vazio.hidden = filtrados.length > 0;

    filtrados.forEach(p => {
      const card = document.createElement("div");
      card.className = "card profile-item-card";
      card.style.padding = "16px";
      card.style.display = "flex";
      card.style.flexDirection = "column";
      card.style.gap = "8px";

      const header = document.createElement("div");
      header.style.display = "flex";
      header.style.justifyContent = "space-between";
      header.style.alignItems = "center";
      header.style.flexWrap = "wrap";
      header.style.gap = "10px";

      const titleGroup = document.createElement("div");
      titleGroup.style.display = "flex";
      titleGroup.style.alignItems = "center";
      titleGroup.style.gap = "10px";

      const title = document.createElement("h3");
      title.style.margin = "0";
      title.textContent = p.nome || p.name || p.profile_id;

      const badge = document.createElement("span");
      badge.style.fontSize = "0.75rem";
      badge.style.padding = "2px 8px";
      badge.style.borderRadius = "12px";
      badge.style.background = "var(--bg-accent-soft, #e6f0fa)";
      badge.style.color = "var(--color-primary, #005ca9)";
      badge.style.fontWeight = "600";
      badge.textContent = (p.modo_fluxo || p.mode) === "formulario_simples" ? "Formulário Simples" : "Contrato Completo";

      titleGroup.append(title, badge);

      const actionsGroup = document.createElement("div");
      actionsGroup.style.display = "flex";
      actionsGroup.style.gap = "6px";
      actionsGroup.style.flexWrap = "wrap";

      const btnDup = document.createElement("button");
      btnDup.type = "button";
      btnDup.className = "btn btn-secondary";
      btnDup.textContent = "Duplicar";
      btnDup.addEventListener("click", () => duplicarPerfilModal(p));

      const btnEdt = document.createElement("button");
      btnEdt.type = "button";
      btnEdt.className = "btn btn-secondary";
      btnEdt.textContent = "Editar";
      btnEdt.addEventListener("click", () => editarPerfilModal(p));

      const btnExp = document.createElement("button");
      btnExp.type = "button";
      btnExp.className = "btn btn-secondary";
      btnExp.textContent = "Exportar";
      btnExp.addEventListener("click", () => exportarPerfilModal(p));

      const btnExc = document.createElement("button");
      btnExc.type = "button";
      btnExc.className = "btn btn-secondary";
      btnExc.style.color = "var(--color-error, #d93025)";
      btnExc.textContent = "Excluir";
      btnExc.addEventListener("click", () => excluirPerfilModal(p));

      actionsGroup.append(btnDup, btnEdt, btnExp, btnExc);
      header.append(titleGroup, actionsGroup);

      const details = document.createElement("p");
      details.className = "hint";
      details.style.margin = "0";
      const campos = p.campos_entrada || p.fields || [];
      details.textContent = `${campos.length} campos configurados • Formato: ${p.formato_saida || "PDF/A-2b"} • Máx. participantes: ${p.max_participantes || 4}`;

      card.append(header, details);
      container.append(card);
    });
  }

  function duplicarPerfilModal(p) {
    const nomeAtual = p.nome || p.name;
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <p class="hint">Digite o nome para a cópia do perfil "${nomeAtual}":</p>
      <div class="field" style="margin-top:10px;">
        <label for="dup-nome-input">Novo nome</label>
        <input id="dup-nome-input" value="${nomeAtual} (Cópia)" autocomplete="off">
      </div>
    `;
    window.ContractoUI.abrirModal("Duplicar perfil", wrap, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Duplicar",
        primario: true,
        aoClicar: async () => {
          const novoNome = wrap.querySelector("#dup-nome-input").value.trim();
          if (!novoNome) return;
          const r = await window.ContractoAPI.duplicateProfile(nomeAtual, novoNome);
          if (r.status === 200 || r.status === 201) {
            window.ContractoUI.toast(`Perfil "${novoNome}" criado com sucesso!`, "success");
            await carregarTelaPerfis();
          } else {
            window.ContractoUI.toast(r.data?.message || "Erro ao duplicar perfil.", "error");
          }
        }
      }
    ]);
  }

  function excluirPerfilModal(p) {
    const nome = p.nome || p.name;
    window.ContractoUI.abrirModal("Excluir perfil", `Deseja realmente excluir o perfil "${nome}"? Esta ação não pode ser desfeita.`, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Excluir definitivamente",
        primario: true,
        aoClicar: async () => {
          const r = await window.ContractoAPI.deleteProfile(nome);
          if (r.status === 200) {
            window.ContractoUI.toast(`Perfil "${nome}" excluído.`, "success");
            await carregarTelaPerfis();
          } else {
            window.ContractoUI.toast(r.data?.message || "Não foi possível excluir o perfil.", "error");
          }
        }
      }
    ]);
  }

  function exportarPerfilModal(p) {
    const jsonStr = JSON.stringify(p, null, 2);
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <p class="hint">Copie o JSON do perfil "${p.nome || p.name}":</p>
      <div class="field" style="margin-top:10px;">
        <textarea id="json-export-area" rows="12" readonly style="font-family:monospace; font-size:0.85rem;">${jsonStr}</textarea>
      </div>
    `;
    window.ContractoUI.abrirModal("Exportar perfil", wrap, [
      {
        texto: "Copiar JSON",
        primario: true,
        aoClicar: () => {
          const area = wrap.querySelector("#json-export-area");
          area.select();
          navigator.clipboard.writeText(jsonStr);
          window.ContractoUI.toast("JSON copiado para a área de transferência!", "success");
        }
      },
      { texto: "Fechar", primario: false }
    ]);
  }

  function novoPerfilModal() {
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <div class="field-grid">
        <div class="field">
          <label for="novo-nome">Nome do perfil</label>
          <input id="novo-nome" placeholder="Ex: Novo Formulário" autocomplete="off">
        </div>
        <div class="field">
          <label for="novo-modo">Modo de fluxo</label>
          <select id="novo-modo">
            <option value="contrato">Contrato Completo</option>
            <option value="formulario_simples">Formulário Simples</option>
          </select>
        </div>
        <div class="field">
          <label for="novo-formato">Formato de saída</label>
          <select id="novo-formato">
            <option value="PDF/A-2b">PDF/A-2b</option>
            <option value="PDF">PDF Simples</option>
          </select>
        </div>
        <div class="field">
          <label for="novo-max">Máx. participantes</label>
          <input id="novo-max" type="number" min="1" max="4" value="4">
        </div>
      </div>
    `;
    window.ContractoUI.abrirModal("Criar novo perfil", wrap, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Salvar perfil",
        primario: true,
        aoClicar: async () => {
          const nome = wrap.querySelector("#novo-nome").value.trim();
          const modo = wrap.querySelector("#novo-modo").value;
          const formato = wrap.querySelector("#novo-formato").value;
          const maxPart = parseInt(wrap.querySelector("#novo-max").value || "4", 10);
          if (!nome) {
            window.ContractoUI.toast("Informe o nome do perfil.", "warning");
            return;
          }
          const dados = { nome, modo_fluxo: modo, formato_saida: formato, max_participantes: maxPart, campos_entrada: [] };
          const r = await window.ContractoAPI.createProfile(dados);
          if (r.status === 200 || r.status === 201) {
            window.ContractoUI.toast(`Perfil "${nome}" criado!`, "success");
            await carregarTelaPerfis();
          } else {
            window.ContractoUI.toast(r.data?.message || "Erro ao criar perfil.", "error");
          }
        }
      }
    ]);
  }

  function importarPerfilModal() {
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <p class="hint">Cole a estrutura JSON do perfil que deseja importar:</p>
      <div class="field" style="margin-top:10px;">
        <textarea id="import-json-area" rows="10" placeholder='{ "nome": "Novo Perfil", "modo_fluxo": "contrato", ... }' style="font-family:monospace; font-size:0.85rem;"></textarea>
      </div>
    `;
    window.ContractoUI.abrirModal("Importar perfil JSON", wrap, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Importar",
        primario: true,
        aoClicar: async () => {
          const text = wrap.querySelector("#import-json-area").value.trim();
          if (!text) return;
          try {
            const parsed = JSON.parse(text);
            const r = await window.ContractoAPI.createProfile(parsed);
            if (r.status === 200 || r.status === 201) {
              window.ContractoUI.toast(`Perfil "${parsed.nome || 'Importado'}" importado com sucesso!`, "success");
              await carregarTelaPerfis();
            } else {
              window.ContractoUI.toast(r.data?.message || "Falha na validação do perfil importado.", "error");
            }
          } catch (e) {
            window.ContractoUI.toast("JSON inválido: " + e.message, "error");
          }
        }
      }
    ]);
  }

  function editarPerfilModal(p) {
    const jsonStr = JSON.stringify(p, null, 2);
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <p class="hint">Edite as propriedades JSON do perfil "${p.nome || p.name}":</p>
      <div class="field" style="margin-top:10px;">
        <textarea id="edit-json-area" rows="12" style="font-family:monospace; font-size:0.85rem;">${jsonStr}</textarea>
      </div>
    `;
    window.ContractoUI.abrirModal("Editar perfil", wrap, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Salvar alterações",
        primario: true,
        aoClicar: async () => {
          const text = wrap.querySelector("#edit-json-area").value.trim();
          try {
            const parsed = JSON.parse(text);
            const nomeOriginal = p.nome || p.name;
            const r = await window.ContractoAPI.updateProfile(nomeOriginal, parsed);
            if (r.status === 200) {
              window.ContractoUI.toast(`Perfil "${parsed.nome || nomeOriginal}" atualizado com sucesso!`, "success");
              await carregarTelaPerfis();
            } else {
              window.ContractoUI.toast(r.data?.message || "Erro ao salvar alterações no perfil.", "error");
            }
          } catch (e) {
            window.ContractoUI.toast("JSON inválido: " + e.message, "error");
          }
        }
      }
    ]);
  }

  function revisar() {
    const btn=$("btn-ver-pendencias");
    if(btn && !btn.hidden){btn.click();return;}
    atualizar();
    window.ContractoUI.abrirModal("Revise os dados","Tudo pronto para gerar.",[{texto:"Voltar ao formulário"}]);
  }
  window.ContractoEtapa1={
    ligar,
    atualizar,
    revisar,
    conferir,
    novoTrabalho,
    carregarTelaPerfis,
    composto:()=>composed,
    modo:()=>mode,
    reconectar:()=>!loaded ? carregar() : (!composed && selected.length ? selecionar(selected) : (schedulePreview(),atualizar()))
  };
})();
