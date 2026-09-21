/* Um trabalho por vez, com snapshot imutável e polling sem sobreposição. */
(function () {
  "use strict";
  const $=id=>document.getElementById(id), api=()=>window.ContractoAPI, ui=()=>window.ContractoUI;
  let bound=false, busy=false, base=null, attachments=[], active=null, timer=null, polling=false, failures=0, previewRevision=0, pending=null, sending=false, finalized=false;
  let filaConhecida=[];
  let eraEnvio=0;
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
          } else {
            status("completed","Trabalho concluído com sucesso.","Documentos organizados na pasta de destino.");
            finalized=true;
            resultados(job.file_ids || job.result?.output_file_ids || [],job.job_id,job.files || job.result?.files || []);
          }
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
        const select=$("anexo-tipo"),tipo=select.value,label=select.selectedOptions[0]?.text || tipo;
        attachments.push({selection_id:r.selection_id,name:r.name,type:tipo,label});
        alterarProcesso();manifesto();atualizar();
      } else ui().toast("Não foi possível adicionar o anexo.","error");
    } catch(_){ui().toast("Falha ao selecionar anexo.","error");}
  }

  function novoRequestId() {
    const rid = new Uint8Array(16);
    try { crypto.getRandomValues(rid); } catch (_) { for (let i = 0; i < 16; i++) rid[i] = Math.floor(Math.random() * 256); }
    return [...rid].map(b => b.toString(16).padStart(2, "0")).join("");
  }

  async function finalizar() {
    // Single-flight + idempotência (request_id): o segundo clique não duplica o processo.
    if(busy||sending||!base||!online()||finalized)return;
    const format=$("formato-saida").value;
    if(format==="PDF/A-2b"&&!capabilities?.ghostscript){ui().toast("PDF/A requer Ghostscript.","error");return;}
    const pacote=window.ContractoEtapa1?.pacoteProcesso?.();
    if(!pacote){ui().toast("Reabra o formulário e confira os dados antes de concluir.","error");return;}
    const payload={participants:pacote.participants,output_id:pacote.output_id,
      file_ids:[...base.file_ids],
      attachments:attachments.map(a=>({file_id:a.selection_id,document_type:a.type})),
      format,request_id:novoRequestId()};
    sending=true;atualizar();
    try {
      const r=await api().request("POST","/api/v1/jobs/process",payload);
      if(r.status===202){pending=null;iniciar(r.data.job_id,"process");}
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

  function recomecar() {
    // Novo trabalho abandona o envio incerto: resposta tardia do snapshot
    // antigo não inicia job nem contamina o novo rascunho.
    eraEnvio++;
    pending=null; sending=false; busy=false;
    if(timer){clearTimeout(timer);timer=null;}
    active=null; failures=0; finalized=false;
    atualizar();
  }

  function capacidades(data) {
    // Recebe as capabilities do arranque (app.js); sem elas, ligar() busca sozinho.
    if (data) { capabilities = data; atualizar(); }
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

  function gerar(snapshot) {
    // Geração a partir do snapshot imutável da Etapa 1; retorna a resposta HTTP.
    // Single-flight: o segundo clique durante o envio é descartado (sem job duplicado).
    if (busy || sending || !online() || !snapshot) return Promise.resolve(null);
    const requestId = novoRequestId();
    const payload = { profile_ids: snapshot.profile_ids, participants: snapshot.participants, output_id: snapshot.output_id, request_id: requestId };
    const era = eraEnvio;
    sending = true; busy = true; atualizar();
    return api().request("POST", "/api/v1/jobs/generate", payload).then(r => {
      if (era !== eraEnvio) return r;
      sending = false;
      if (r.status === 202) {
        pending = null;
        iniciar(r.data.job_id, "generate");
      } else if (r.status >= 500) {
        // Envio ambíguo (resposta perdida/erro do servidor): mantém busy para
        // bloquear duplicatas; a retomada reusa o mesmo request_id (idempotente).
        registrarPendente(payload);
      } else {
        busy = false;
        registrarPendente(payload);
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
    attachments=[];finalized=false;
    manifesto();status("completed","PDFs gerados com sucesso.","Revise os anexos ou escolha o formato antes de concluir.");
    // Gerados também aparecem como linhas com "Visualizar" (paridade com o fluxo anterior).
    resultados(ids,jobData.job_id,files);
    atualizar();
    try { window.ContractoUI?.sincronizarStepper?.(); } catch (_) {}
  }

  function registrarPendente(payload) {
    pending={tipo:"generate",payload};
    atualizar();
  }

  window.ContractoEtapa2={ligar,atualizar,invalidar,gerar,receberBase,registrarPendente,painelFila,capacidades:capacidades,recomecar,ocupado:()=>busy,temBase:()=>!!base};
})();
