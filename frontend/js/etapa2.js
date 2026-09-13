/* Etapa 2: anexos, processamento e finalização. */
(function () {
  "use strict";

  const api = () => window.ContractoAPI;
  const ui = () => window.ContractoUI;

  const estado = { anexos: [], jobId: null, pollTimer: null };

  function renderAnexos() {
    const caixa = document.getElementById("lista-anexos");
    if (!caixa) return;
    caixa.innerHTML = "";
    estado.anexos.forEach((a, i) => {
      const linha = document.createElement("div");
      const nome = document.createElement("span");
      nome.textContent = (a.nome || "Anexo") + " (" + a.document_type + ")";
      const rm = document.createElement("button");
      rm.type = "button";
      rm.className = "btn btn-secondary";
      rm.textContent = "Remover";
      rm.setAttribute("aria-label", "Remover anexo " + (i + 1));
      rm.addEventListener("click", () => { estado.anexos.splice(i, 1); renderAnexos(); });
      linha.append(nome, rm);
      caixa.append(linha);
    });
  }

  async function adicionarAnexo() {
    const tipoEl = document.getElementById("anexo-tipo");
    const tipo = (tipoEl && tipoEl.value.trim()) || "ANEXO";
    if (!/^[A-Za-z0-9_-]{1,50}$/.test(tipo)) {
      ui().toast("Tipo de documento inválido (letras, números, _ ou -).", "error");
      return;
    }
    const r = await window.pywebview.api.select_file();
    if (r.cancelled) return;
    if (!r.selection_id) {
      ui().toast("Não foi possível anexar.", "error");
      return;
    }
    // Nome exibido vem do tipo; o arquivo real fica só no backend, por ID.
    estado.anexos.push({ file_id: r.selection_id, document_type: tipo, nome: tipo });
    renderAnexos();
  }

  function participantesAtuais() {
    return window.ContractoEtapa1 && window.ContractoEtapa1.lerParaEtapa2
      ? window.ContractoEtapa1.lerParaEtapa2()
      : null;
  }

  async function finalizar() {
    const dados = participantesAtuais();
    if (!dados || !dados.participants.length || !dados.output_id) {
      ui().toast("Volte à Etapa 1 e gere os documentos primeiro.", "warning");
      return;
    }
    const formato = document.getElementById("formato-saida").value === "PDF/A-2b" ? "PDF/A-2b" : "PDF";
    const corpo = {
      participants: dados.participants,
      output_id: dados.output_id,
      format: formato,
    };
    if (estado.anexos.length) {
      corpo.attachments = estado.anexos.map((a) => ({ file_id: a.file_id, document_type: a.document_type }));
    } else if (dados.file_ids && dados.file_ids.length) {
      corpo.file_ids = dados.file_ids;
    }
    const r = await api().request("POST", "/api/v1/jobs/process", corpo);
    if (r.status !== 202) {
      ui().toast((r.data && r.data.message) || "Falha ao processar.", "error");
      return;
    }
    estado.jobId = r.data.job_id;
    acompanhar();
  }

  async function acompanhar() {
    const statusEl = document.getElementById("fila-status");
    const barra = document.getElementById("fila-barra");
    barra.parentElement.hidden = false;
    clearInterval(estado.pollTimer);
    const sondar = async () => {
      const r = await api().request("GET", "/api/v1/jobs/" + estado.jobId);
      if (r.status !== 200) return;
      const s = r.data;
      const total = s.total || 1;
      barra.style.width = Math.round((100 * (s.completed || 0)) / total) + "%";
      statusEl.textContent = "Estado: " + s.status + " (" + (s.completed || 0) + "/" + total + ")";
      if (["completed", "failed", "cancelled"].includes(s.status)) {
        clearInterval(estado.pollTimer);
        if (s.status === "completed") {
          statusEl.textContent += " Processo concluído.";
          ui().toast("Processo concluído.", "success");
        } else if (s.status === "failed") {
          ui().toast((s.error && s.error.message) || "Falha no processo.", "error");
        }
      }
    };
    estado.pollTimer = setInterval(sondar, 800);
    sondar();
  }

  async function cancelar() {
    if (!estado.jobId) return;
    await api().request("POST", "/api/v1/jobs/" + estado.jobId + "/cancel", {});
    clearInterval(estado.pollTimer);
  }

  function ligar() {
    const btnAnexo = document.getElementById("btn-anexo");
    if (btnAnexo) btnAnexo.addEventListener("click", adicionarAnexo);
    document.getElementById("btn-finalizar").addEventListener("click", finalizar);
  }

  window.ContractoEtapa2 = { ligar, cancelar };
})();
