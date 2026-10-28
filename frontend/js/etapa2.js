/* Um trabalho por vez, com snapshot imutável e polling sem sobreposição. */
(function () {
  "use strict";
  const $=id=>document.getElementById(id), api=()=>window.ContractoAPI, ui=()=>window.ContractoUI;
  let bound=false, busy=false, base=null, attachments=[], active=null, timer=null, polling=false, failures=0, previewRevision=0, pending=null, sending=false, finalized=false;
  // Modelo antigo (paridade Tk v4.5.15): formulários com checkbox + documentos
  // extras nomeados (nome_padrao). "attachments" genérico é mantido como
  // derivação para o payload (document_type) e compatibilidade de testes.
  let formsDisponiveis=[], formsSelecionados=new Set(), extrasDisponiveis=[], extrasMap=new Map();
  let filaConhecida=[];
  let eraEnvio=0;
  const online=()=>window.ContractoApp?.pronto() || false;
  let capabilities=null, formatoPadrao=null, formatoEscolhido=false, sincronizarFormato=null;
  const originLabel={generated:"Gerado pelo Contracto",attachment:"Anexo do trabalho",imported:"PDF importado"};

  function status(state,message,detail="") {
    // Foto 1: sem pill na toolbar — o andamento aparece em toast/modal.
    $("estado-trabalho").dataset.state=state;
    $("fila-status").textContent=message;
    $("fila-detalhe").textContent=detail;
    const summary=$("manifesto-status");
    if(summary)summary.textContent=message+(detail ? " — "+detail : "");
    if(state==="failed" && (message.includes("Word") || detail.includes("Word"))) {
      alertaWordTravado();
    }
  }

  function alertaWordTravado() {
    // Fase 2 (DESIGN.md §8): contagem real desde o aviso + ação prevista
    // (reparo limitado ao processo filho); sem oferta de LibreOffice.
    const corpo = document.createElement("div");
    const p1 = document.createElement("p");
    p1.textContent = "O Microsoft Word está demorando para converter os arquivos RTF.";
    const tempo = document.createElement("p");
    tempo.className = "hint";
    tempo.setAttribute("role", "status");
    const inicio = Date.now();
    const tick = () => {
      const s = Math.floor((Date.now() - inicio) / 1000);
      tempo.textContent = "Aguardando há " + s + "s. O trabalho continua em segundo plano; fechar este aviso não cancela a conversão.";
    };
    tick();
    const relogio = setInterval(() => { if (document.contains(tempo)) tick(); else clearInterval(relogio); }, 1000);
    const p2 = document.createElement("p");
    p2.className = "hint";
    p2.textContent = "Você pode tentar forçar o encerramento do Word (só o processo da conversão) e reprocessar o trabalho.";
    corpo.append(p1, tempo, p2);
    ui().abrirModal(
      "Aviso: Microsoft Word travado",
      corpo,
      [
        {
          texto: "Forçar encerramento do Word",
          aoClicar: async () => {
            try {
              await api().request("POST", "/api/v1/system/repair");
              ui().toast("Comando de reparo do Word enviado.", "info");
            } catch (_) {
              ui().toast("Falha ao enviar reparo.", "error");
            }
          }
        },
        { texto: "Aguardar" }
      ],
      () => clearInterval(relogio)
    );
  }

  function fileLabel(file,index) {return file?.name || "Documento "+(index+1);}
  function destacarAbrirPasta(ativo) {
    // Destaque maior em "Abrir pasta" quando o trabalho já está finalizado.
    const b=$("btn-abrir-pasta");if(!b)return;
    b.classList.toggle("btn-primary",!!ativo);
    b.classList.toggle("btn-secondary",!ativo);
  }
  function fileDescription(file) {
    const participants=file.participants?.length ? "Participante"+(file.participants.length>1?"s ":" ")+file.participants.join(", ") : "Participante não informado";
    return [originLabel[file.origin] || "Documento",participants,file.size_bytes ? Math.max(1,Math.ceil(file.size_bytes/1024))+" KB" : ""].filter(Boolean).join(" · ");
  }

  function atualizar() {
    const advanced=window.ContractoEtapa1?.modo() !== "simples";
    $("opcoes-processamento").hidden=!advanced;
    // Formulários e documentos extras vivem na Etapa 2 (Conferir), só no
    // fluxo de Contrato.
    const secaoForms=$("secao-forms-dinamicos"), secaoExtras=$("secao-docs-extras");
    if(secaoForms)secaoForms.hidden=!advanced;
    if(secaoExtras)secaoExtras.hidden=!advanced;
    // "FINALIZAR PROCESSO" só aparece quando há o que finalizar.
    $("btn-finalizar").hidden=!advanced||!base||finalized;
    $("btn-finalizar").disabled=!online()||busy||!base||finalized;
    $("formato-opcoes").hidden=!advanced;
    $("formato-saida").querySelector('[value="PDF/A-2b"]').disabled=!capabilities?.ghostscript;
    // Padrão = Configurações; só vale enquanto o usuário não escolheu aqui.
    if(!formatoEscolhido&&formatoPadrao)$("formato-saida").value=formatoPadrao==="PDF/A-2b"&&capabilities?.ghostscript?"PDF/A-2b":"PDF";
    if($("formato-saida").value==="PDF/A-2b"&&!capabilities?.ghostscript)$("btn-finalizar").disabled=true;
    $("capacidade-formato").textContent=capabilities?.ghostscript ? "PDF/A disponível para arquivamento." : "PDF comum disponível. PDF/A requer Ghostscript nesta instalação.";
    const btnAnexo=$("btn-anexo"), selTipo=$("anexo-tipo");
    if(btnAnexo)btnAnexo.disabled=!online()||busy||!base;
    if(selTipo)selTipo.disabled=busy||!base;
    const orgPasta=$("organizacao-pasta"), orgFmt=$("organizacao-formato");
    try {
      const pasta=document.getElementById("pasta-saida");
      if(orgPasta&&pasta&&pasta.value)orgPasta.textContent="Pasta: "+pasta.value;
      if(orgFmt)orgFmt.textContent="Formato de saída: "+$("formato-saida").value;
    } catch(_){}
    renderForms();renderExtras();
    $("formato-saida").disabled=busy;
    sincronizarFormato?.();
    $("btn-cancelar").hidden=!active;
    $("btn-cancelar").disabled=!online()||!active||active.cancelRequested;
    // "Recuperar andamento" só existe quando há andamento real: envio
    // ambíguo (pending) ou trabalho ativo cujo polling se perdeu
    // (cancelado/ocultado/queda de conexão). Erro de validação nunca acende.
    const andamentoPerdido = !!(active && (failures >= 3 || document.hidden));
    $("btn-retomar").hidden = !pending && !andamentoPerdido;
    $("btn-retomar").disabled=sending;
    $("btn-voltar").disabled=busy;
    $("fila-barra").parentElement.hidden=!busy;
    // "Fila" só quando existe trabalho conhecido ou ativo.
    const btnFila=$("btn-fila");
    if(btnFila)btnFila.hidden=!(filaConhecida.length||active||pending);
    $("lista-anexos").querySelectorAll("button").forEach(el=>el.disabled=busy);
    window.ContractoEtapa1?.atualizar();
  }

  function rotuloGeracao(g){return g==="unico"||g==="por_processo" ? "Documento único" : "Por participante";}

  async function carregarContexto() {
    // Fonte: última composição da Etapa 1 (já tem formularios/documentos_extras).
    // Fallback: compose direto com os perfilIds selecionados.
    try {
      let comp = window.ContractoEtapa1?.composicao?.();
      if((!comp || (!comp.formularios && !comp.documentos_extras)) && window.ContractoEtapa1?.perfilIds){
        const ids=window.ContractoEtapa1.perfilIds();
        if(ids && ids.length){
          const r=await api().request("POST","/api/v1/profiles/compose",{profile_ids:ids});
          if(r.status===200)comp=r.data;
        }
      }
      if(!comp)return;
      if(Array.isArray(comp.formularios)&&comp.formularios.length){
        formsDisponiveis=comp.formularios;
        if(!formsSelecionados.size)formsDisponiveis.forEach(f=>formsSelecionados.add(f.nome));
        // Remove seleções de perfil trocado.
        [...formsSelecionados].forEach(n=>{if(!formsDisponiveis.some(f=>f.nome===n))formsSelecionados.delete(n);});
      }
      if(Array.isArray(comp.documentos_extras)){
        extrasDisponiveis=comp.documentos_extras;
        [...extrasMap.keys()].forEach(k=>{if(!extrasDisponiveis.some(d=>d.nome_padrao===k))extrasMap.delete(k);});
      }
    } catch(_){}
  }

  function renderForms(){
    const host=$("lista-forms-etapa2");if(!host)return;host.replaceChildren();
    if(!formsDisponiveis.length){
      const p=document.createElement("p");p.className="hint";p.textContent="Nenhum formulário no perfil ativo.";host.append(p);return;
    }
    formsDisponiveis.forEach(f=>{
      const label=document.createElement("label");label.className="doc-extra-linha";
      const chk=document.createElement("input");chk.type="checkbox";chk.checked=formsSelecionados.has(f.nome);chk.disabled=busy;
      chk.setAttribute("aria-label",f.nome);
      chk.addEventListener("change",()=>{if(busy)return;if(chk.checked)formsSelecionados.add(f.nome);else formsSelecionados.delete(f.nome);alterarProcesso();manifesto();atualizar();});
      const txt=document.createElement("span");txt.textContent=" "+f.nome+"  ("+rotuloGeracao(f.geracao)+")";
      label.append(chk,txt);host.append(label);
    });
  }

  function renderExtras(){
    const host=$("lista-docs-extras");if(!host)return;host.replaceChildren();
    if(!extrasDisponiveis.length){
      const p=document.createElement("p");p.className="hint";p.textContent="Este perfil não tem documentos extras.";host.append(p);return;
    }
    extrasDisponiveis.forEach(doc=>{
      const atual=extrasMap.get(doc.nome_padrao);
      const row=document.createElement("div");row.className="doc-extra-linha";
      const radio=document.createElement("span");radio.className="doc-extra-marcador";radio.textContent=atual?"●":"○";radio.setAttribute("aria-hidden","true");
      const rot=document.createElement("span");rot.className="doc-extra-rotulo";rot.textContent=doc.rotulo+":";
      const campo=document.createElement("input");campo.readOnly=true;campo.placeholder="Nenhum arquivo selecionado";campo.value=atual?atual.name:"";campo.setAttribute("aria-label",doc.rotulo);
      const btn=document.createElement("button");btn.type="button";btn.className="btn btn-secondary btn-sm";btn.textContent=atual?"Trocar":"Selecionar";btn.disabled=busy||!online();
      btn.addEventListener("click",()=>selecionarExtra(doc));
      if(atual){
        const rm=document.createElement("button");rm.type="button";rm.className="btn btn-secondary btn-sm";rm.textContent="Remover";rm.disabled=busy;
        rm.addEventListener("click",()=>{if(busy)return;extrasMap.delete(doc.nome_padrao);sincronizarAttachments();alterarProcesso();manifesto();atualizar();});
        row.append(radio,rot,campo,btn,rm);
      } else row.append(radio,rot,campo,btn);
      host.append(row);
    });
  }

  async function selecionarExtra(doc){
    if(busy||!online())return;
    try{
      const r=await api().selectAttachment();
      if(r.cancelled)return;
      if(r.selection_id){extrasMap.set(doc.nome_padrao,{selection_id:r.selection_id,name:r.name});sincronizarAttachments();alterarProcesso();manifesto();atualizar();}
      else ui().toast("Não foi possível adicionar o documento.","error");
    }catch(_){ui().toast("Falha ao selecionar documento.","error");}
  }

  function sincronizarAttachments(){
    // Mantém o vetor legado derivado do mapa nomeado (payload usa document_type).
    attachments=[...extrasMap.entries()].map(([nome_padrao,v])=>({selection_id:v.selection_id,name:v.name,type:nome_padrao,label:nome_padrao}));
  }

  function formsSelecionadosLista(){return [...formsSelecionados];}

  function manifesto() {
    const box=$("lista-anexos");box.replaceChildren();
    (base?.file_ids || []).forEach((id,i)=>{const file=base.files?.find(f=>f.file_id===id) || {},row=document.createElement("div");row.className="documento-linha";const info=document.createElement("div"),name=document.createElement("strong"),detail=document.createElement("p");name.textContent=fileLabel(file,i);detail.className="hint";detail.textContent=fileDescription(file);info.append(name,detail);row.append(info);box.append(row);});
    const nForms=formsSelecionados.size || (base?.file_ids?.length || 0);
    const nExtras=extrasMap.size;
    const totalExtras=extrasDisponiveis.length;
    $("manifesto-resumo").textContent=base ? base.file_ids.length+" gerado(s) · "+nForms+" formulário(s) marcado(s) · "+nExtras+"/"+totalExtras+" documento(s) extra(s) no processo." : "Gere os documentos na Etapa 1 para organizar este processo.";
  }

  function invalidar() {
    if(busy)return;
    previewRevision++;
    if(base){status("changed","Os dados foram alterados.","Gere novamente para que os documentos reflitam as alterações.");}
    base=null;attachments=[];extrasMap.clear();finalized=false;$("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;destacarAbrirPasta(false);
    manifesto();
    $("btn-finalizar").disabled=true;const ba=$("btn-anexo");if(ba)ba.disabled=true;
  }

  function alterarProcesso() {
    if(finalized){$("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;destacarAbrirPasta(false);status("changed","Processo alterado.","Finalize novamente para atualizar os resultados.");}
    finalized=false;
  }

  function resultados(ids,jobId,files=[]) {
    $("lista-resultados").replaceChildren();
    ids.forEach((id,i)=>{
      const file=files.find(f=>f.file_id===id) || {},row=document.createElement("div"),info=document.createElement("div"),name=document.createElement("strong"),detail=document.createElement("p");
      row.className="result-row";name.textContent=fileLabel(file,i);detail.className="hint";detail.textContent=fileDescription(file);info.append(name,detail);
      const btn=document.createElement("button");btn.className="btn btn-secondary";btn.type="button";btn.textContent="Visualizar";btn.setAttribute("aria-label","Visualizar "+fileLabel(file,i));
      btn.addEventListener("click",()=>visualizar(id,fileLabel(file,i)));row.append(info,btn);$("lista-resultados").append(row);
    });
    $("btn-abrir-pasta").hidden=false;
    destacarAbrirPasta(finalized);
    $("btn-abrir-pasta").onclick=async()=>{try{const r=await api().openResult(jobId);if(!r.ok)ui().toast("Não foi possível abrir a pasta.","error");}catch(_){ui().toast("Falha ao abrir pasta.","error");}};
  }

  async function visualizar(id,name) {
    const revision=++previewRevision;
    let url=null,timeout=null;
    const panel=document.createElement("div"),message=document.createElement("p");panel.className="viewer-panel";message.className="viewer-message";message.setAttribute("role","status");message.textContent="Carregando PDF…";panel.append(message);
    ui().abrirModal("Visualização — "+name,panel,[
      { texto: "Abrir no leitor padrão", aoClicar: async () => {
        try { const r = await api().openFile(id); if (!r.ok) ui().toast("Não foi possível abrir no leitor padrão.", "error"); }
        catch (_) { ui().toast("Falha ao abrir no leitor padrão.", "error"); }
      } },
      { texto: "Expandir", aoClicar: () => { document.querySelector(".modal")?.classList.toggle("modal-viewer-expandido"); } },
      { texto: "Fechar", primario: true }
    ],()=>{if(url)URL.revokeObjectURL(url);clearTimeout(timeout);});
    document.querySelector(".modal")?.classList.add("modal-viewer");
    try {
      const res=await api().getFile(id);
      if(revision!==previewRevision)return;
      if(!res.ok){message.textContent="Não foi possível carregar a pré-visualização.";return;}
      url=URL.createObjectURL(res.blob);
      const frame=document.createElement("iframe");frame.className="pdf-preview";frame.title="Pré-visualização do documento "+name;frame.src=url;
      timeout=setTimeout(()=>{if(revision===previewRevision&&!frame.contentWindow){message.textContent="O visualizador demorou para responder. Tente abrir a pasta.";}},10000);
      frame.addEventListener("load",()=>{clearTimeout(timeout);if(revision===previewRevision)message.hidden=true;});
      panel.append(frame);
    } catch(_){if(revision===previewRevision)message.textContent="Falha ao carregar o PDF.";}
  }

  async function poll() {
    if(!active||polling)return;polling=true;
    try {
      const r=await api().getJob(active.job_id);failures=0;
      if(!active)return;
      if(r.status===200){
        const job=r.data;
        const reg=filaConhecida.find(f=>f.job_id===active.job_id);
        if(reg){reg.status=job.status;reg.progress=job.progress||0;reg.message=job.message||reg.message;}
        if(["queued","running","sending"].includes(job.status)){
          status(job.status,job.message || "Processando…",job.step ? "Etapa "+job.step.current+" de "+job.step.total : "");
          $("progresso-trabalho").hidden=false;$("fila-barra").style.width=(job.progress || 0)+"%";
        } else if(job.status==="completed"){
          const tipo = active.tipo;
          $("progresso-trabalho").hidden=true;active=null;busy=false;
          if(tipo==="generate"){
            receberBase(job);
            ui().toast("PDFs gerados com sucesso. Revise os anexos ou conclua.", "success");
          } else {
            status("completed","Trabalho concluído com sucesso.","Documentos organizados na pasta de destino.");
            finalized=true;
            resultados(job.file_ids || job.result?.output_file_ids || [],job.job_id,job.files || job.result?.files || []);
            modalConclusao(job.job_id);
          }
        } else if(job.status==="failed"){
          status("failed","Trabalho não concluído.",job.error || "Ocorreu um erro no processamento.");
          ui().toast(job.error || "Ocorreu um erro no processamento.", "error", 8000);
          if (job.error?.includes("Word")) alertaWordTravado();
          $("progresso-trabalho").hidden=true;active=null;busy=false;
        } else if(job.status==="cancelled"){
          status("cancelled","Trabalho cancelado.","Nenhum documento foi alterado.");
          ui().toast("Trabalho cancelado. Nenhum documento foi alterado.", "warning");
          $("progresso-trabalho").hidden=true;active=null;busy=false;
        }
      } else if(r.status===404){
        status("uncertain","Estado do trabalho incerto.","O servidor não encontrou a operação. Tente novamente.");
        failures++;
      } else failures++;
    } catch(_){failures++;}
    finally {
      polling=false;atualizar();
      try { window.ContractoUI?.sincronizarStepper?.(); } catch (_) {}
      // Polling a cada 2s enquanto há trabalhos ativos; para quando a fila esvazia.
      if(active)timer=setTimeout(poll,failures>2?3000:2000);
    }
  }

  function iniciar(jobId,tipo) {
    if(active)return;
    active={job_id:jobId,tipo,cancelRequested:false};busy=true;failures=0;pending=null;
    filaConhecida.unshift({job_id:jobId,tipo,status:"queued",progress:5,message:"Operação agendada…"});
    if(filaConhecida.length>8)filaConhecida.length=8;
    status("queued","Operação agendada…","Aguardando confirmação do servidor.");
    ui().toast(tipo === "process" ? "Organização iniciada. Acompanhe em Concluir." : "Geração iniciada. Acompanhe o andamento.", "info");
    $("progresso-trabalho").hidden=false;$("fila-barra").style.width="5%";
    atualizar();poll();
  }

  function painelFila() {
    const lista=document.createElement("div");
    lista.className="fila-painel-lista";
    if(!filaConhecida.length && !active){
      const vazio=document.createElement("p");
      vazio.className="hint";vazio.textContent="Nenhum trabalho na fila. Gere documentos para acompanhar aqui.";
      lista.append(vazio);
    }
    filaConhecida.forEach(item=>{
      const card=document.createElement("div");
      card.className="fila-item";
      const titulo=document.createElement("strong");
      titulo.textContent=(item.tipo==="process"?"Processar":"Gerar")+" · "+item.job_id.slice(0,8);
      const estado=document.createElement("p");
      estado.className="hint";estado.textContent=item.status+" — "+(item.message||"");
      const barra=document.createElement("div");barra.className="fila-barra";
      const preench=document.createElement("div");preench.style.width=(item.progress||0)+"%";
      barra.append(preench);
      card.append(titulo,estado,barra);
      if(["queued","running","sending"].includes(item.status)){
        const btn=document.createElement("button");
        btn.type="button";btn.className="btn btn-secondary btn-sm";btn.textContent="Cancelar";
        btn.addEventListener("click",async()=>{
          try{
            const r=await api().request("POST","/api/v1/jobs/"+item.job_id+"/cancel",{});
            if(r.status===200)ui().toast("Cancelamento enviado.","info");
            else ui().toast("Não foi possível cancelar.","error");
          }catch(_){ui().toast("Falha ao cancelar.","error");}
        });
        card.append(btn);
      }
      lista.append(card);
    });
    ui().abrirModal("Fila de trabalhos",lista,[{texto:"Ver documentos",aoClicar:()=>window.ContractoUI.mostrarTela("etapa2")},{texto:"Fechar",primario:true}]);
  }

  async function anexar() {
    if(busy||!base||!online())return;
    try {
      const r=await api().selectAttachment();
      if(r.cancelled)return;
      if(r.selection_id){
        const select=$("anexo-tipo"),tipo=(select&&select.value)||"ANEXO",label=(select&&select.selectedOptions[0]?.text)||tipo;
        attachments.push({selection_id:r.selection_id,name:r.name,type:tipo,label});
        alterarProcesso();manifesto();atualizar();
      } else ui().toast("Não foi possível adicionar o anexo.","error");
    } catch(_){ui().toast("Falha ao selecionar anexo.","error");}
  }

  function mensagemErro(r, padrao) {
    // O backend retorna {code,message,issues}; nunca "detail".
    // Sem esta leitura o motivo real (422/409) era mascarado pelo fallback genérico.
    const data = r && r.data ? r.data : {};
    const issues = Array.isArray(data.issues) && data.issues.length
      ? " (" + data.issues.slice(0, 3).map(i => i.field || i.code || "?").join(", ") + ")"
      : "";
    return (data.message || data.detail || padrao) + issues;
  }

  function envioAmbiguo(r, excecao) {
    // Só envio ambíguo (rede/timeout/5xx) justifica "Recuperar andamento".
    // Erro 4xx determinístico (validação, seleção expirada, duplicado,
    // Word/GS indisponível) nunca cura no retry e não cria pendência.
    if (excecao) return true;
    const status = r ? r.status : 0;
    return status >= 500 || status === 408 || status === 429 || status === 503 || status === 0;
  }

  function novoRequestId() {
    const rid = new Uint8Array(16);
    try { crypto.getRandomValues(rid); } catch (_) { for (let i = 0; i < 16; i++) rid[i] = Math.floor(Math.random() * 256); }
    return [...rid].map(b => b.toString(16).padStart(2, "0")).join("");
  }

  // Tela de conclusão simplificada: só abre a pasta (primário) ou fecha.
  function modalConclusao(jobId) {
    ui().abrirModal("Trabalho concluído", "Documentos organizados na pasta de destino.", [
      {
        texto: "Abrir pasta", primario: true, aoClicar: async () => {
          try { const r = await api().openResult(jobId); if (!r.ok) ui().toast("Não foi possível abrir a pasta.", "error"); }
          catch (_) { ui().toast("Falha ao abrir pasta.", "error"); }
        }
      },
      { texto: "Fechar" }
    ]);
  }

  async function finalizar() {
    // Paridade Tk (mw_etapa2.py): vazio bloqueia, parcial pede confirmação.
    // Single-flight + idempotência (request_id): o segundo clique não duplica.
    if(busy||sending||!base||!online()||finalized)return;
    await carregarContexto();
    const totalDocs=(base?.file_ids?.length||0)+extrasDisponiveis.length;
    const marcados=formsSelecionados.size+extrasMap.size;
    if(totalDocs>0&&marcados===0){
      ui().toast("Nenhum documento selecionado. Marque ao menos um formulário ou extra.","error",8000);
      return;
    }
    if(!extrasMap.size){
      ui().abrirModal(
        "Concluir sem documentos extras?",
        "Nenhum documento extra foi adicionado a este trabalho. Deseja concluir somente com os documentos gerados?",
        [
          { texto: "Voltar e anexar" },
          { texto: "Concluir mesmo assim", primario: true, aoClicar: () => _prosseguirFinalizar() }
        ]
      );
      return;
    }
    if(extrasDisponiveis.length&&extrasMap.size<extrasDisponiveis.length){
      const faltam=extrasDisponiveis.filter(d=>!extrasMap.has(d.nome_padrao)).map(d=>d.rotulo).join(", ");
      ui().abrirModal(
        "Documentos incompletos",
        "Faltam documentos extras ("+faltam+"). Deseja finalizar mesmo assim?",
        [
          { texto: "Voltar e anexar" },
          { texto: "Finalizar mesmo assim", primario: true, aoClicar: () => _prosseguirFinalizar() }
        ]
      );
      return;
    }
    _prosseguirFinalizar();
  }

  function fileIdsFiltrados(){
    // Checkbox de formulários filtra os gerados pelo prefixo do nome
    // ("PPE - ...", "1º Imóvel - ..."). Sem contexto, envia todos.
    if(!formsDisponiveis.length||!formsSelecionados.size)return [...base.file_ids];
    if(formsSelecionados.size>=formsDisponiveis.length)return [...base.file_ids];
    return (base.file_ids||[]).filter(id=>{
      const f=(base.files||[]).find(x=>x.file_id===id);
      const nome=(f&&f.name)||"";
      return [...formsSelecionados].some(sel=>nome.startsWith(sel+" -")||nome.startsWith(sel+" ")||nome===sel||nome.includes(sel));
    });
  }

  async function _prosseguirFinalizar() {
    if(busy||sending||!base||!online()||finalized)return;
    const format=$("formato-saida").value;
    if(format==="PDF/A-2b"&&!capabilities?.ghostscript){ui().toast("PDF/A requer Ghostscript.","error");return;}
    const pacote=window.ContractoEtapa1?.pacoteProcesso?.();
    if(!pacote){ui().toast("Reabra o formulário e confira os dados antes de concluir.","error");return;}
    sincronizarAttachments();
    const fileIds=fileIdsFiltrados();
    if(!fileIds.length&&!attachments.length){ui().toast("Nenhum documento selecionado para concluir.","error");return;}
    const payload={participants:pacote.participants,output_id:pacote.output_id,
      file_ids:fileIds,
      attachments:attachments.map(a=>({file_id:a.selection_id,document_type:a.type})),
      format,request_id:novoRequestId()};
    sending=true;atualizar();
    try {
      const r=await api().request("POST","/api/v1/jobs/process",payload);
      if(r.status===202){pending=null;iniciar(r.data.job_id,"process");}
      else if(envioAmbiguo(r,false)){
        pending={tipo:"process",payload};
        ui().toast(mensagemErro(r, "Conexão interrompida. Clique em 'Recuperar andamento' para tentar novamente."),"error");
      } else {
        pending=null;
        ui().toast(mensagemErro(r, "Não foi possível iniciar o processamento. Confira os dados."),"error", 8000);
      }
    } catch(_){
      pending={tipo:"process",payload};
      ui().toast("Conexão interrompida. Clique em 'Recuperar andamento' para tentar novamente.","error");
    } finally {sending=false;atualizar();}
  }

  async function cancelar() {
    if(!active||active.cancelRequested||!online())return;
    active.cancelRequested=true;atualizar();
    try {
      const r=await api().request("POST","/api/v1/jobs/"+active.job_id+"/cancel");
      if(r.status===200)ui().toast("Solicitação de cancelamento enviada.","info");
      else ui().toast("Não foi possível cancelar o trabalho.","error");
    } catch(_){ui().toast("Falha ao enviar cancelamento.","error");}
    finally {if(active)active.cancelRequested=false;atualizar();}
  }

  async function retomar() {
    if(sending||!online())return;
    if(pending){
      sending=true;atualizar();
      try {
        const r=await api().request("POST","/api/v1/jobs/"+(pending.tipo==="generate"?"generate":"process"),pending.payload);
        if(r.status===202){const tipo=pending.tipo;pending=null;iniciar(r.data.job_id,tipo);}
        else if(envioAmbiguo(r,false)){ui().toast(mensagemErro(r,"Ainda sem resposta do servidor. Tente recuperar novamente."),"error");}
        else {pending=null;ui().toast(mensagemErro(r,"Não foi possível retomar o trabalho."),"error",8000);}
      } catch(_){ui().toast("Falha ao conectar com o servidor.","error");}
      finally {sending=false;atualizar();}
      return;
    }
    if(active)poll();
  }

  function recomecar() {
    // Novo trabalho abandona o envio incerto: resposta tardia do snapshot
    // antigo não inicia job nem contamina o novo rascunho.
    eraEnvio++;
    pending=null; sending=false; busy=false;
    if(timer){clearTimeout(timer);timer=null;}
    active=null; failures=0; finalized=false;
    attachments=[];extrasMap.clear();
    formatoEscolhido=false;carregarFormatoPadrao();
    atualizar();
  }

  function carregarFormatoPadrao() {
    // Lê o formato padrão das Configurações (pode ter mudado desde a última geração).
    Promise.resolve(api().getSettings?.()).then(r=>{formatoPadrao=r?.data?.formato_saida||null;atualizar();}).catch(()=>{});
  }

  function capacidades(data) {
    // Recebe as capabilities do arranque (app.js); sem elas, ligar() busca sozinho.
    if (data) { capabilities = data; atualizar(); }
  }

  function ligar() {
    if(bound)return;bound=true;
    const ba=$("btn-anexo");if(ba)ba.addEventListener("click",anexar);
    $("btn-finalizar").addEventListener("click",finalizar);
    $("btn-cancelar").addEventListener("click",cancelar);
    $("btn-retomar").addEventListener("click",retomar);
    $("btn-voltar").addEventListener("click",()=>{window.ContractoUI.mostrarTela("inicio");});
    const gp=$("btn-gerenciar-perfis");if(gp)gp.addEventListener("click",()=>{window.ContractoUI.mostrarTela("perfis");});
    const btnFila=$("btn-fila");
    if(btnFila)btnFila.addEventListener("click",()=>painelFila());
    sincronizarFormato=window.ContractoUI.segmentar?.($("formato-saida"),"Formato de saída");
    $("formato-saida").addEventListener("change",()=>{formatoEscolhido=true;alterarProcesso();atualizar();});
    carregarFormatoPadrao();
    document.addEventListener("visibilitychange",()=>{if(!document.hidden&&active&&failures>=1)poll();});
    carregarContexto().finally(atualizar);
    api().getCapabilities().then(c=>capabilities=c).catch(()=>capabilities={pdf:true,rtf_word:false,ghostscript:false}).finally(atualizar);
  }

  function gerar(snapshot) {
    // Geração a partir do snapshot imutável da Etapa 1; retorna a resposta HTTP.
    // Single-flight: o segundo clique durante o envio é descartado (sem job duplicado).
    if (busy || sending || !online() || !snapshot) return Promise.resolve(null);
    const requestId = novoRequestId();
    const payload = { profile_ids: snapshot.profile_ids, participants: snapshot.participants, output_id: snapshot.output_id, request_id: requestId };
    if (Array.isArray(snapshot.forms_selecionados) && snapshot.forms_selecionados.length) payload.forms_selecionados = snapshot.forms_selecionados;
    const era = eraEnvio;
    sending = true; busy = true; atualizar();
    return api().request("POST", "/api/v1/jobs/generate", payload).then(r => {
      if (era !== eraEnvio) return r;
      sending = false;
      if (r.status === 202) {
        pending = null;
        iniciar(r.data.job_id, "generate");
      } else if (envioAmbiguo(r, false)) {
        // Envio ambíguo (resposta perdida/erro do servidor): mantém busy para
        // bloquear duplicatas; a retomada reusa o mesmo request_id (idempotente).
        registrarPendente(payload);
      } else {
        busy = false;
        pending = null; atualizar();
      }
      atualizar();
      return r;
    }).catch(() => {
      // Queda de conexão = envio ambíguo: mesma regra do 5xx.
      if (era !== eraEnvio) return { status: 409, data: { message: "Trabalho descartado." } };
      sending = false;
      registrarPendente(payload);
      atualizar();
      return { status: 503, data: { message: "Conexão interrompida. Clique em 'Recuperar andamento'." } };
    });
  }
  function receberBase(jobData) {
    const ids = jobData.file_ids || jobData.result?.output_file_ids || [];
    const files = jobData.files || jobData.result?.files || [];
    base={job_id:jobData.job_id,file_ids:ids,files};
    // Preserva os extras escolhidos na Conferência (Etapa 2): limpar aqui os
    // descartava antes do FINALIZAR. Rescisão acontece em invalidar/recomecar.
    finalized=false;
    carregarFormatoPadrao();
    carregarContexto().then(()=>{manifesto();atualizar();});
    status("completed","PDFs gerados com sucesso.","Revise os documentos extras ou escolha o formato antes de concluir.");
    // Gerados também aparecem como linhas com "Visualizar" (paridade com o fluxo anterior).
    resultados(ids,jobData.job_id,files);
    atualizar();
    try { window.ContractoUI?.sincronizarStepper?.(); } catch (_) {}
  }

  function registrarPendente(payload) {
    pending={tipo:"generate",payload};
    atualizar();
  }

  function reconectar() {
    // Fase 0: invocado pelo boot (app.js) quando a ponte cai e volta. Sem
    // esta função o arranque caía no catch "interface não pôde ser
    // inicializada". Reconsulta capacidades, retoma o polling se havia
    // trabalho ativo e atualiza os controles.
    api().getCapabilities().then(c=>capabilities=c).catch(()=>capabilities={pdf:true,rtf_word:false,ghostscript:false}).finally(atualizar);
    if(active)poll();
    else atualizar();
  }

  async function sincronizarContexto(){await carregarContexto();atualizar();}

  window.ContractoEtapa2={ligar,atualizar,invalidar,gerar,receberBase,registrarPendente,painelFila,capacidades:capacidades,recomecar,reconectar,sincronizarContexto,ocupado:()=>busy,temBase:()=>!!base,formsSelecionados:formsSelecionadosLista,extrasSelecionados:()=>[...extrasMap.keys()]};
})();
