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
    if(id === "endereco")wrap.classList.add("field-wide");
    const label = document.createElement("label"), input = document.createElement(field.tipo === "SELECAO" ? "select" : "input");
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
      owner[id]=field.tipo === "CHECKBOX" ? (input.checked ? options[0] : options[options.length-1]) : input.value.trim();
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
    $("selecao-resumo").textContent=selected.length+" selecionado(s)";
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
    changed(); const request=++compositionRevision; selected=ids; composing=!!ids.length; composed=false;
    atualizar();
    if(!ids.length){fields=[];render();return;}
    const r=await window.ContractoAPI.request("POST","/api/v1/profiles/compose",{profile_ids:ids});
    if(request!==compositionRevision)return;
    composing=false;
    if(r.status!==200){issues=[{field:"Formulários",message:r.data?.message || "Falha ao carregar campos."}];atualizar();return;}
    fields=r.data.fields || []; draft.computed=[]; maximum=r.data.max_participants || 1;
    if(catalog.some(p=>ids.includes(p.profile_id)&&p.mode === "contrato") && !fields.some(f=>f.id === "endereco"))fields.push({id:"endereco",tipo:"TEXTO",rotulo:"Endereço",obrigatorio:true});
    composed=true;render();
  }
  async function carregar() {
    const r=await window.ContractoAPI.request("GET","/api/v1/profiles");
    if(r.status!==200){issues=[{field:"Formulários",message:"Não foi possível carregar o catálogo."}];atualizar();return;}
    catalog=r.data;loaded=true;
    const initial=catalog.find(p=>p.mode === "contrato") || catalog[0];
    selected=initial ? [initial.profile_id] : [];
    $("lista-formularios").replaceChildren();$("lista-perfis").replaceChildren();
    catalog.forEach(p=>{
      const label=document.createElement("label"),check=document.createElement("input");check.type="checkbox";check.value=p.profile_id;check.checked=selected.includes(p.profile_id);
      check.addEventListener("change",()=>selecionar([...$("lista-formularios").querySelectorAll("input:checked")].map(el=>el.value)));
      label.append(check,document.createTextNode(" "+p.name));$("lista-formularios").append(label);
      const item=document.createElement("p");item.textContent=p.name+" — até "+p.max_participants+" participante(s), "+p.fields.length+" campo(s).";$("lista-perfis").append(item);
    });
    if(!catalog.length)$("lista-perfis").textContent="Nenhum perfil disponível nesta instalação.";
    await selecionar(selected);
  }
  async function gerar() {
    if(atualizar().length||busy())return;
    const snapshot={profile_ids:[...selected],participants:form().participants(draft,fields),output_id:draft.output_id,revision};
    const r=await window.ContractoEtapa2.gerar(snapshot);
    if(r && r.status!==202){issues=r.data?.issues?.length ? r.data.issues : [{field:"Geração",message:r.data?.message || "Não foi possível gerar."}];atualizar();window.ContractoUI.toast(r.data?.message || "Confira os campos indicados.","error");controls.find(c=>c.input.hasAttribute("aria-invalid")&&!c.wrap.hidden)?.input.focus();}
  }
  function ligar() {
    if(bound)return;bound=true;
    $("btn-gerar").addEventListener("click",gerar);
    $("btn-adicionar").addEventListener("click",()=>{if(busy()||draft.people.length>=maximum)return;draft.people.push({nome_completo:"",cpf:""});changed();render();});
    ["data_assinatura","local_assinatura"].forEach(id=>{const input=$(id.replaceAll("_","-"));input.addEventListener("input",e=>{draft.globals[id]=e.target.value.trim();changed();});input.addEventListener("blur",()=>{touchedGlobals.add(id);atualizar();});});
    $("btn-pasta").addEventListener("click",async()=>{if(busy())return;try{const r=await window.ContractoAPI.selectOutput();if(r.cancelled)return;if(r.selection_id){draft.output_id=r.selection_id;$("pasta-saida").value=r.name || "Pasta selecionada";changed();}else window.ContractoUI.toast("Não foi possível selecionar a pasta.","error");}catch(_){window.ContractoUI.toast("Falha ao abrir o seletor.","error");}});
    ["simples","avancado"].forEach(name=>$("modo-"+name).addEventListener("click",()=>{if(busy())return;mode=name;["simples","avancado"].forEach(n=>{if(n===name)$("modo-"+n).setAttribute("aria-current","page");else $("modo-"+n).removeAttribute("aria-current");});window.ContractoEtapa2.atualizar();}));
    carregar();
  }
  window.ContractoEtapa1={ligar,atualizar,modo:()=>mode,reconectar:()=>!loaded ? carregar() : (!composed && selected.length ? selecionar(selected) : (schedulePreview(),atualizar()))};
})();
