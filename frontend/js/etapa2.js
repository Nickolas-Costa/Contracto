/* Um trabalho por vez, com snapshot imutável e polling sem sobreposição. */
(function () {
  "use strict";
  const $=id=>document.getElementById(id), api=()=>window.ContractoAPI, ui=()=>window.ContractoUI;
  let bound=false, busy=false, base=null, attachments=[], active=null, timer=null, polling=false, failures=0, previewRevision=0, pending=null, sending=false, finalized=false;
  const online=()=>window.ContractoApp?.pronto() || false;
  function atualizar() {
    const advanced=window.ContractoEtapa1?.modo() !== "simples";
    $("opcoes-processamento").hidden=!advanced;
    $("btn-finalizar").hidden=!advanced;
    $("btn-finalizar").disabled=!online()||busy||!base||finalized;
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
    (base?.file_ids || []).forEach((id,i)=>{const row=document.createElement("p");row.textContent="Gerado: documento "+(i+1);box.append(row);});
    attachments.forEach((a,i)=>{
      const row=document.createElement("div");row.className="documento-linha";
      const name=document.createElement("span");name.textContent="Anexo: "+a.name+" — "+a.document_type;
      const remove=document.createElement("button");remove.type="button";remove.className="btn btn-secondary";remove.textContent="Remover";remove.setAttribute("aria-label","Remover "+a.name);
      remove.addEventListener("click",()=>{if(busy)return;attachments.splice(i,1);alterarProcesso();manifesto();atualizar();});row.append(name,remove);box.append(row);
    });
    $("manifesto-resumo").textContent=base ? base.file_ids.length+" gerado(s) + "+attachments.length+" anexo(s) no processo." : "Gere os documentos na Etapa 1 para organizar este processo.";
  }
  function invalidar() {
    if(busy)return;
    previewRevision++;
    if(base){$("fila-status").textContent="Dados alterados. Gere novamente antes de finalizar.";}
    base=null;attachments=[];finalized=false;$("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;
    manifesto();
    // O chamador atualiza pendências; evita recursão.
    $("btn-finalizar").disabled=true;$("btn-anexo").disabled=true;
  }
  function alterarProcesso() {
    if(finalized){$("lista-resultados").replaceChildren();$("btn-abrir-pasta").hidden=true;$("fila-status").textContent="Processo alterado. Finalize novamente para atualizar os resultados.";}
    finalized=false;
  }
  function resultados(ids,jobId) {
    $("lista-resultados").replaceChildren();
    ids.forEach((id,i)=>{
      const btn=document.createElement("button");btn.className="btn btn-secondary";btn.type="button";btn.textContent="Ver documento "+(i+1);
      btn.addEventListener("click",()=>visualizar(id,i+1));$("lista-resultados").append(btn);
    });
    $("btn-abrir-pasta").hidden=false;
    $("btn-abrir-pasta").onclick=async()=>{try{const r=await api().openResult(jobId);if(!r.ok)ui().toast("Não foi possível abrir a pasta.","error");}catch(_){ui().toast("Falha ao abrir pasta.","error");}};
  }
  async function visualizar(id,number) {
    const revision=++previewRevision;
    try {
      const r=await api().getFile(id);
      if(revision!==previewRevision)return;
      if(!r.ok){ui().toast(r.code === "preview_too_large" ? "PDF excede o limite de visualização de 20 MiB. Abra pela pasta." : "Não foi possível visualizar este PDF.","error");return;}
      const bytes=Uint8Array.from(atob(r.base64),c=>c.charCodeAt(0));
      const url=URL.createObjectURL(new Blob([bytes],{type:"application/pdf"}));
      const frame=document.createElement("iframe");frame.title="Documento "+number;frame.className="pdf-preview";frame.src=url;
      ui().abrirModal("Documento "+number,frame,[{texto:"Fechar",primario:true}],()=>URL.revokeObjectURL(url));
    } catch(_){ui().toast("Falha ao abrir o visualizador.","error");}
  }
  async function poll() {
    if(!active||polling)return;
    const job=active;polling=true;
    try {
      const r=await api().request("GET","/api/v1/jobs/"+job.id);
      if(active!==job)return;
      if(r.status!==200){
        failures++;
        $("fila-status").textContent="Não foi possível consultar o trabalho. "+(failures>=3 ? "Retome a consulta antes de iniciar outro processo." : "Tentando novamente…");
        if(failures>=3){atualizar();return;}
      } else {
        failures=0;const s=r.data;
        const labels={queued:"Na fila",running:"Em andamento",cancelling:"Cancelando",completed:"Concluído",failed:"Falhou",cancelled:"Cancelado"};
        $("fila-status").textContent=(labels[s.status] || "Em andamento")+": "+(s.completed || 0)+" de "+(s.total || 0)+" documento(s).";
        const progress=Math.min(100,Math.round(100*(s.completed||0)/Math.max(1,s.total||0)));
        $("fila-barra").style.width=progress+"%";
        $("progresso-trabalho").setAttribute("aria-valuenow",String(progress));
        if(["completed","failed","cancelled"].includes(s.status)){
          active=null;busy=false;
          if(s.status === "completed"){
            finalized=job.kind === "process";
            if(job.kind === "generate")base={...job.snapshot,file_ids:[...(s.file_ids||[])]};
            resultados(s.file_ids || [],job.id);manifesto();
            ui().toast(job.kind === "generate" ? "Documentos gerados." : "Processo concluído.","success");
          } else if(s.status === "failed"){
            $("fila-status").textContent=s.error?.message || "O trabalho falhou. Nenhum resultado parcial foi publicado.";
          }
          atualizar();return;
        }
      }
    } catch(_){failures++;$("fila-status").textContent="Consulta indisponível. Retome a consulta para conferir o resultado.";atualizar();}
    finally{polling=false;}
    if(active===job && failures<3)timer=setTimeout(poll,800);
  }
  async function submit(kind,payload,snapshot) {
    if(busy||!online())return null;
    busy=true;failures=0;previewRevision++;
    $("btn-abrir-pasta").hidden=true;$("lista-resultados").replaceChildren();
    $("fila-status").textContent="Enviando trabalho…";ui().irEtapa(2);atualizar();
    payload.request_id=Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,"0")).join("");
    pending={kind,payload,snapshot:structuredClone(snapshot)};
    return enviarPending();
  }
  async function enviarPending() {
    if(!pending||sending)return null;
    const {kind,payload,snapshot}=pending;
    sending=true;atualizar();
    let r;
    try{r=await api().request("POST","/api/v1/jobs/"+kind,payload);}catch(_){r={status:503,data:{message:"Falha ao enviar trabalho."}};}
    finally{sending=false;}
    if(r.status>=500){$("fila-status").textContent="Envio sem confirmação. Retome a consulta para recuperar o mesmo trabalho, sem duplicá-lo.";atualizar();return null;}
    pending=null;
    if(r.status!==202){busy=false;$("fila-status").textContent=r.data?.message || "Não foi possível iniciar.";if(kind === "generate")ui().irEtapa(1);atualizar();return r;}
    active={id:r.data.job_id,kind,snapshot:structuredClone(snapshot),cancelRequested:false};
    ui().irEtapa(2);atualizar();poll();return r;
  }
  async function gerar(snapshot) {
    if(busy)return null;
    base=null;attachments=[];finalized=false;manifesto();
    const {profile_ids,participants,output_id}=snapshot;
    return submit("generate",{profile_ids,participants,output_id},snapshot);
  }
  async function finalizar() {
    if(busy||!base||!online()||finalized)return;
    const payload={participants:structuredClone(base.participants),output_id:base.output_id,
      file_ids:[...base.file_ids],attachments:attachments.map(a=>({file_id:a.file_id,document_type:a.document_type})),format:$("formato-saida").value};
    const r=await submit("process",payload,base);
    if(r&&r.status!==202)ui().toast(r.data?.message || "Falha ao processar.","error");
  }
  let selecting=false;
  async function anexar() {
    if(busy||!base||selecting||!online())return;
    const type=$("anexo-tipo").value.trim();
    if(!/^[A-Za-z0-9_-]{1,50}$/.test(type)||attachments.some(a=>a.document_type===type)){ui().toast("Use um tipo válido e diferente dos anexos existentes.","warning");return;}
    selecting=true;const original=base;
    try{const r=await api().selectFile();if(r.cancelled)return;if(base!==original||busy)return;if(!r.selection_id){ui().toast("Não foi possível anexar.","error");return;}
      attachments.push({file_id:r.selection_id,document_type:type,name:r.name || type});alterarProcesso();manifesto();atualizar();
    }catch(_){ui().toast("Falha ao abrir o seletor.","error");}finally{selecting=false;}
  }
  async function cancelar() {
    if(!active||active.cancelRequested)return;
    const job=active;job.cancelRequested=true;atualizar();
    try{const r=await api().request("POST","/api/v1/jobs/"+job.id+"/cancel",{});if(r.status!==200){job.cancelRequested=false;ui().toast("Não foi possível cancelar; confira o estado do trabalho.","error");}}
    catch(_){job.cancelRequested=false;}
    atualizar();
  }
  function reconectar(){failures=0;clearTimeout(timer);if(pending)enviarPending();else if(active)poll();atualizar();}
  function ligar(){
    if(bound)return;bound=true;
    $("btn-anexo").addEventListener("click",anexar);$("btn-finalizar").addEventListener("click",finalizar);
    $("btn-cancelar").addEventListener("click",cancelar);$("btn-retomar").addEventListener("click",reconectar);
    $("formato-saida").addEventListener("change",()=>{if(busy)return;alterarProcesso();atualizar();});
    $("btn-voltar").addEventListener("click",()=>ui().irEtapa(1));manifesto();atualizar();
  }
  window.ContractoEtapa2={ligar,gerar,atualizar,invalidar,cancelar,reconectar,ocupado:()=>busy};
})();
