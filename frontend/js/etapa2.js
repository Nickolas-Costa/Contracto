/* Um trabalho por vez, com snapshot imutável e polling sem sobreposição. */
(function () {
  "use strict";
  const $=id=>document.getElementById(id), api=()=>window.ContractoAPI, ui=()=>window.ContractoUI;
  let bound=false, busy=false, base=null, attachments=[], active=null, timer=null, polling=false, failures=0, previewRevision=0, pending=null, sending=false, finalized=false;
  const online=()=>window.ContractoApp?.pronto() || false;
  let capabilities=null;
  const originLabel={generated:"Gerado pelo Contracto",attachment:"Anexo do trabalho",imported:"PDF importado"};

  function status(state,message,detail="") {
    $("estado-trabalho").dataset.state=state;
    $("fila-status").textContent=message;
    $("fila-detalhe").textContent=detail;
    const summary=$("manifesto-status");
    if(summary)summary.textContent=message+(detail ? " — "+detail : "");
    const badge=$("indicador-fila-global");
    if(badge) {
      if(state==="running"||state==="queued"||state==="sending") {
        badge.hidden=false;
        badge.dataset.state=state;
        badge.textContent="⚡ "+message;
      } else if(state==="completed") {
        badge.hidden=false;
        badge.dataset.state=state;
        badge.textContent="✓ Concluído";
      } else if(state==="failed" && (message.includes("Word") || detail.includes("Word"))) {
        badge.hidden=false;
        badge.dataset.state="failed";
        badge.textContent="⚠️ Word travado";
        alertaWordTravado();
      } else {
        badge.hidden=true;
      }
    }
  }

  function alertaWordTravado() {
    ui().abrirModal(
      "Aviso: Microsoft Word travado",
      "<p>O Microsoft Word está demorando para converter os arquivos RTF.</p><p class='hint'>Você pode tentar forçar o encerramento do Word e reprocessar o trabalho.</p>",
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
        { texto: "Fechar" }
      ]
    );
  }

  function fileLabel(file,index) {return file?.name || "Documento "+(index+1);}
  function fileDescription(file) {
    const participants=file.participants?.length ? "Participante"+(file.participants.length>1?"s ":" ")+file.participants.join(", ") : "Participante não informado";
    return [originLabel[file.origin] || "Documento",participants,file.size_bytes ? Math.max(1,Math.ceil(file.size_bytes/1024))+" KB" : ""].filter(Boolean).join(" · ");
  }

  function atualizar() {
    const advanced=window.ContractoEtapa1?.modo() !== "simples";
    $("opcoes-processamento").hidden=!advanced;
    $("btn-finalizar").hidden=!advanced;
    $("btn-finalizar").disabled=!online()||busy||!base||finalized;
    $("formato-opcoes").hidden=!advanced;
    $("formato-saida").querySelector('[value="PDF/A-2b"]').disabled=!capabilities?.ghostscript;
    if($("formato-saida").value==="PDF/A-2b"&&!capabilities?.ghostscript)$("btn-finalizar").disabled=true;
    $("capacidade-formato").textContent=capabilities?.ghostscript ? "PDF/A disponível para arquivamento." : "PDF comum disponível. PDF/A requer Ghostscript nesta instalação.";
    $("btn-anexo").disabled=!online()||busy||!base;
    $("anexo-tipo").disabled=busy||!base;
    $("formato-saida").disabled=busy;
    $("btn-cancelar").hidden=!active;
    $("btn-cancelar").disabled=!online()||!active||active.cancelRequested;
    $("btn-retomar").hidden=(!active||failures<3)&&!pending;
    $("btn-retomar").disabled=sending;
    $("btn-voltar").disabled=busy;
    $("fila-barra").parentElement.hidden=!busy;
    $("lista-anexos").querySelectorAll("button").forEach(el=>el.disabled=busy);
    window.ContractoEtapa1?.atualizar();
  }

  function manifesto() {
    const box=$("lista-anexos");box.replaceChildren();
    (base?.file_ids || []).forEach((id,i)=>{const file=base.files?.find(f=>f.file_id===id) || {},row=document.createElement("div");row.className="documento-linha";const info=document.createElement("div"),name=document.createElement("strong"),detail=document.createElement("p");name.textContent=fileLabel(file,i);detail.className="hint";detail.textContent=fileDescription(file);info.append(name,detail);row.append(info);box.append(row);});
    attachments.forEach((a,i)=>{
      const row=document.createElement("div");row.className="documento-linha";
      const name=document.createElement("span");name.textContent="Anexo: "+a.name+" — "+a.label;
      const remove=document.createElement("button");remove.type="button";remove.className="btn btn-secondary";remove.textContent="Remover";remove.setAttribute("aria-label","Remover "+a.name);
      remove.addEventListener("click",()=>{if(busy)return;attachments.splice(i,1);alterarProcesso();manifesto();atualizar();});row.append(name,remove);box.append(row);
    });
    $("manifesto-resumo").textContent=base ? base.file_ids.length+" gerado(s) + "+attachments.length+" anexo(s) no processo." : "Gere os documentos na Etapa 1 para organizar este processo.";
  }

  function invalidar() {
    if(busy)return;
    previewRevision++;
    if(base){status("changed","Os dados foram alterados.","Gere novamente para que os documentos reflitam as alterações.");}
    base=null;attachments=[];finalized=false;$("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;
    manifesto();
    $("btn-finalizar").disabled=true;$("btn-anexo").disabled=true;
  }

  function alterarProcesso() {
    if(finalized){$("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;status("changed","Processo alterado.","Finalize novamente para atualizar os resultados.");}
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
    $("btn-abrir-pasta").onclick=async()=>{try{const r=await api().openResult(jobId);if(!r.ok)ui().toast("Não foi possível abrir a pasta.","error");}catch(_){ui().toast("Falha ao abrir pasta.","error");}};
  }

  async function visualizar(id,name) {
    const revision=++previewRevision;
    let url=null,timeout=null;
    const panel=document.createElement("div"),message=document.createElement("p");panel.className="viewer-panel";message.className="viewer-message";message.setAttribute("role","status");message.textContent="Carregando PDF…";panel.append(message);
    ui().abrirModal("Visualização — "+name,panel,[{texto:"Fechar"}],()=>{if(url)URL.revokeObjectURL(url);clearTimeout(timeout);});
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
        if(["queued","running","sending"].includes(job.status)){
          status(job.status,job.message || "Processando…",job.step ? "Etapa "+job.step.current+" de "+job.step.total : "");
          $("progresso-trabalho").hidden=false;$("fila-barra").style.width=(job.progress || 0)+"%";
        } else if(job.status==="completed"){
          status("completed","Trabalho concluído com sucesso.","Documentos organizados na pasta de destino.");
          $("progresso-trabalho").hidden=true;active=null;busy=false;finalized=true;
          resultados(job.result?.output_file_ids || [],job.job_id,job.result?.files || []);
        } else if(job.status==="failed"){
          status("failed","Trabalho não concluído.",job.error || "Ocorreu um erro no processamento.");
          if (job.error?.includes("Word")) alertaWordTravado();
          $("progresso-trabalho").hidden=true;active=null;busy=false;
        } else if(job.status==="cancelled"){
          status("cancelled","Trabalho cancelado.","Nenhum documento foi alterado.");
          $("progresso-trabalho").hidden=true;active=null;busy=false;
        }
      } else if(r.status===404){
        status("uncertain","Estado do trabalho incerto.","O servidor não encontrou a operação. Tente novamente.");
        failures++;
      } else failures++;
    } catch(_){failures++;}
    finally {
      polling=false;atualizar();
      if(active)timer=setTimeout(poll,failures>2?3000:1000);
    }
  }

  function iniciar(jobId,tipo) {
    if(active)return;
    active={job_id:jobId,tipo,cancelRequested:false};busy=true;failures=0;pending=null;
    status("queued","Operação agendada…","Aguardando confirmação do servidor.");
    $("progresso-trabalho").hidden=false;$("fila-barra").style.width="5%";
    atualizar();poll();
  }

  async function anexar() {
    if(busy||!base||!online())return;
    try {
      const r=await api().selectAttachment();
      if(r.cancelled)return;
      if(r.selection_id){
        const select=$("anexo-tipo"),tipo=select.value,label=select.selectedOptions[0]?.text || tipo;
        attachments.push({selection_id:r.selection_id,name:r.name,type:tipo,label});
        alterarProcesso();manifesto();atualizar();
      } else ui().toast("Não foi possível adicionar o anexo.","error");
    } catch(_){ui().toast("Falha ao selecionar anexo.","error");}
  }

  async function finalizar() {
    if(busy||!base||!online()||finalized)return;
    const format=$("formato-saida").value;
    if(format==="PDF/A-2b"&&!capabilities?.ghostscript){ui().toast("PDF/A requer Ghostscript.","error");return;}
    const files=base.file_ids.map(id=>({file_id:id,type:"GERADO"}));
    attachments.forEach(a=>files.push({selection_id:a.selection_id,type:a.type}));
    const payload={base_job_id:base.job_id,files,output_format:format};
    sending=true;atualizar();
    try {
      const r=await api().request("POST","/api/v1/jobs/process",payload);
      if(r.status===202){iniciar(r.data.job_id,"process");}
      else {
        pending={tipo:"process",payload};
        ui().toast(r.data?.detail || "Falha ao iniciar processamento. Clique em 'Recuperar andamento' para tentar novamente.","error");
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
        if(r.status===202){iniciar(r.data.job_id,pending.tipo);}
        else ui().toast(r.data?.detail || "Não foi possível retomar o trabalho.","error");
      } catch(_){ui().toast("Falha ao conectar com o servidor.","error");}
      finally {sending=false;atualizar();}
      return;
    }
    if(active)poll();
  }

  function ligar() {
    if(bound)return;bound=true;
    $("btn-anexo").addEventListener("click",anexar);
    $("btn-finalizar").addEventListener("click",finalizar);
    $("btn-cancelar").addEventListener("click",cancelar);
    $("btn-retomar").addEventListener("click",retomar);
    $("btn-voltar").addEventListener("click",()=>{window.ContractoUI.mostrarTela("inicio");});
    $("formato-saida").addEventListener("change",()=>{alterarProcesso();atualizar();});
    api().getCapabilities().then(c=>capabilities=c).catch(()=>capabilities={pdf:true,rtf_word:false,ghostscript:false}).finally(atualizar);
  }

  function receberBase(jobData) {
    base={job_id:jobData.job_id,file_ids:jobData.result?.output_file_ids || [],files:jobData.result?.files || []};
    attachments=[];finalized=false;
    $("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;
    manifesto();status("completed","PDFs gerados com sucesso.","Revise os anexos ou escolha o formato antes de concluir.");
    atualizar();
  }

  function registrarPendente(payload) {
    pending={tipo:"generate",payload};
    atualizar();
  }

  window.ContractoEtapa2={ligar,atualizar,invalidar,receberBase,registrarPendente,ocupado:()=>busy,temBase:()=>!!base};
})();
