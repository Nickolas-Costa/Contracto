/* Modo Conversão: arquivos avulsos → PDF/PDF-A, sem perfis nem participantes. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const api = () => window.ContractoAPI, ui = () => window.ContractoUI;
  const online = () => window.ContractoApp?.pronto() || false;
  let arquivos = [], outputId = null, active = null, timer = null,
      polling = false, failures = 0, sending = false, bound = false, caps = null;

  function status(state, message, detail) {
    $("conversao-estado").dataset.state = state;
    $("conversao-status").textContent = message;
    $("conversao-detalhe").textContent = detail || "";
    const badge = $("indicador-fila-global");
    if (badge && (state === "running" || state === "queued" || state === "sending")) {
      badge.hidden = false;
      badge.dataset.state = state;
      badge.textContent = "⚡ " + message;
    } else if (badge && document.getElementById("estado-trabalho").dataset.state !== "running") {
      badge.hidden = true;
    }
  }

  function atualizar() {
    const formato = $("conversao-formato").value;
    const nomeOk = arquivos.length !== 1 || $("conversao-nome").value.trim().length <= 100;
    $("btn-converter").disabled = !online() || sending || !!active || !arquivos.length || !outputId || !nomeOk;
    $("btn-conversao-pasta").disabled = !online() || !!active;
    $("btn-conversao-cancelar").hidden = !active;
    $("conversao-formato").disabled = !!active;
    $("conversao-nome").disabled = !!active || arquivos.length !== 1;
    $("drop-conversao").classList.toggle("ocupado", !!active);
    const optPDFA = $("conversao-formato").querySelector('[value="PDF/A-2b"]');
    if (optPDFA) optPDFA.disabled = !caps?.ghostscript;
    $("conversao-formato-nota").textContent = caps?.ghostscript
      ? "PDF/A disponível para arquivamento."
      : "PDF comum disponível. PDF/A requer Ghostscript nesta instalação.";
  }

  function renderLista() {
    const box = $("lista-conversao");
    box.replaceChildren();
    arquivos.forEach((a, i) => {
      const row = document.createElement("div");
      row.className = "documento-linha";
      const info = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = a.name;
      const detail = document.createElement("p");
      detail.className = "hint";
      detail.textContent = "Original preservado";
      info.append(name, detail);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn btn-secondary btn-sm";
      remove.textContent = "Remover";
      remove.setAttribute("aria-label", "Remover " + a.name);
      remove.disabled = !!active;
      remove.addEventListener("click", () => {
        if (active) return;
        arquivos.splice(i, 1);
        renderLista();
        atualizar();
      });
      row.append(info, remove);
      box.append(row);
    });
  }

  async function anexar() {
    if (active || !online()) return;
    try {
      const r = await api().selectDocuments();
      if (r.cancelled) return;
      const ids = r.selection_ids || (r.selection_id ? [r.selection_id] : []);
      const nomes = r.names || (r.name ? [r.name] : []);
      if (!ids.length) { ui().toast("Não foi possível anexar os arquivos.", "error"); return; }
      ids.forEach((id, i) => {
        if (!arquivos.some(a => a.selection_id === id) && arquivos.length < 20)
          arquivos.push({ selection_id: id, name: nomes[i] || "Documento" });
      });
      if (r.rejected) ui().toast(r.rejected + " arquivo(s) ignorado(s): use PDF, RTF, DOC ou DOCX.", "warning");
      renderLista();
      atualizar();
    } catch (_) { ui().toast("Falha ao abrir o seletor.", "error"); }
  }

  function novoRequestId() {
    const rid = new Uint8Array(16);
    try { crypto.getRandomValues(rid); }
    catch (_) { for (let i = 0; i < 16; i++) rid[i] = Math.floor(Math.random() * 256); }
    return [...rid].map(b => b.toString(16).padStart(2, "0")).join("");
  }

  async function converter() {
    if (sending || active || !online() || !arquivos.length || !outputId) return;
    const formato = $("conversao-formato").value;
    if (formato === "PDF/A-2b" && !caps?.ghostscript) { ui().toast("PDF/A requer Ghostscript.", "error"); return; }
    const nome = $("conversao-nome").value.trim();
    if (arquivos.length === 1 && nome && !/^[\w\-. ]{1,100}$/.test(nome)) {
      ui().toast("Nome inválido: use letras, números, espaços, ponto ou hífen (máx. 100).", "warning");
      return;
    }
    const payload = { file_ids: arquivos.map(a => a.selection_id), output_id: outputId,
                      format: formato, request_id: novoRequestId() };
    if (arquivos.length === 1 && nome) payload.nome_saida = nome;
    sending = true;
    atualizar();
    try {
      const r = await api().request("POST", "/api/v1/jobs/convert", payload);
      if (r.status === 202) {
        active = { job_id: r.data.job_id };
        failures = 0;
        status("queued", "Conversão agendada…", "Aguardando confirmação do servidor.");
        $("conversao-progresso").hidden = false;
        $("conversao-barra").style.width = "5%";
        poll();
      } else {
        ui().toast(r.data?.message || "Não foi possível iniciar a conversão.", "error");
      }
    } catch (_) {
      ui().toast("Conexão interrompida. Tente novamente.", "error");
    } finally { sending = false; atualizar(); }
  }

  async function poll() {
    if (!active || polling) return;
    polling = true;
    try {
      const r = await api().getJob(active.job_id);
      failures = 0;
      if (!active) return;
      if (r.status === 200) {
        const job = r.data;
        if (["queued", "running", "sending"].includes(job.status)) {
          status(job.status, job.message || "Convertendo…",
                 job.total ? "Arquivo " + Math.min(job.completed + 1, job.total) + " de " + job.total : "");
          $("conversao-progresso").hidden = false;
          $("conversao-barra").style.width = (job.progress || job.total
            ? Math.round(100 * (job.completed || 0) / Math.max(1, job.total || 100)) : 5) + "%";
        } else if (job.status === "completed") {
          $("conversao-progresso").hidden = true;
          mostrarResultados(job);
          const id = active.job_id;
          active = null;
          status("completed", "Conversão concluída.", "Arquivos salvos na pasta de destino.");
          ui().abrirModal("Conversão concluída", (job.file_ids || []).length + " arquivo(s) convertido(s) para " + $("conversao-formato").value + ".", [
            { texto: "Abrir pasta", primario: true, aoClicar: async () => {
              try { const o = await api().openResult(id); if (!o.ok) ui().toast("Não foi possível abrir a pasta.", "error"); }
              catch (_) { ui().toast("Falha ao abrir pasta.", "error"); }
            }},
            { texto: "Concluir" }
          ]);
        } else if (job.status === "failed") {
          $("conversao-progresso").hidden = true;
          active = null;
          const msg = job.error?.message || "Ocorreu um erro na conversão.";
          status("failed", "Não foi possível concluir.", msg);
          if (/Word/i.test(msg)) ui().toast("A conversão precisa do Microsoft Word instalado.", "error", 0);
        } else if (job.status === "cancelled") {
          $("conversao-progresso").hidden = true;
          active = null;
          status("cancelled", "Conversão cancelada.", "Nenhum arquivo foi alterado.");
        }
      } else if (r.status === 404) {
        failures++;
        status("uncertain", "Estado incerto.", "O servidor não encontrou a operação.");
      } else { failures++; }
    } catch (_) { failures++; }
    finally {
      polling = false;
      atualizar();
      if (active) timer = setTimeout(poll, failures > 2 ? 3000 : 2000);
    }
  }

  function mostrarResultados(job) {
    const box = $("conversao-resultados");
    box.replaceChildren();
    (job.files || []).forEach((f) => {
      const row = document.createElement("div");
      row.className = "result-row";
      const info = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = f.name;
      const detail = document.createElement("p");
      detail.className = "hint";
      detail.textContent = Math.max(1, Math.ceil((f.size_bytes || 0) / 1024)) + " KB";
      info.append(name, detail);
      const btn = document.createElement("button");
      btn.className = "btn btn-secondary";
      btn.type = "button";
      btn.textContent = "Visualizar";
      btn.setAttribute("aria-label", "Visualizar " + f.name);
      btn.addEventListener("click", () => window.ContractoEtapa2 && visualizarViaEtapa2(f));
      row.append(info, btn);
      box.append(row);
    });
    const abrir = $("btn-conversao-abrir");
    abrir.hidden = false;
    abrir.onclick = async () => {
      try { const o = await api().openResult(job.job_id); if (!o.ok) ui().toast("Não foi possível abrir a pasta.", "error"); }
      catch (_) { ui().toast("Falha ao abrir pasta.", "error"); }
    };
  }

  async function visualizarViaEtapa2(f) {
    // Reaproveita o visualizador de PDF da Etapa 2 sem duplicar código.
    try {
      const r = await api().getFile(f.file_id);
      if (!r.ok) { ui().toast("Não foi possível carregar a pré-visualização.", "error"); return; }
      const url = URL.createObjectURL(r.blob);
      const panel = document.createElement("div");
      panel.className = "viewer-panel";
      const frame = document.createElement("iframe");
      frame.className = "pdf-preview";
      frame.title = "Pré-visualização de " + f.name;
      frame.src = url;
      panel.append(frame);
      ui().abrirModal("Visualização — " + f.name, panel, [{ texto: "Fechar" }],
        () => URL.revokeObjectURL(url));
    } catch (_) { ui().toast("Falha ao carregar o PDF.", "error"); }
  }

  async function cancelar() {
    if (!active || !online()) return;
    try {
      const r = await api().request("POST", "/api/v1/jobs/" + active.job_id + "/cancel", {});
      if (r.status === 200) ui().toast("Cancelamento enviado.", "info");
      else ui().toast("Não foi possível cancelar.", "error");
    } catch (_) { ui().toast("Falha ao enviar cancelamento.", "error"); }
  }

  async function carregarCapacidades() {
    try {
      caps = await api().getCapabilities();
      const partes = ["PDF: disponível",
        "Word (RTF/DOC/DOCX→PDF): " + (caps.word ? "disponível" : "indisponível — instale o Word"),
        "PDF/A: " + (caps.ghostscript ? "disponível" : "indisponível — sem Ghostscript")];
      $("conversao-capacidades").textContent = partes.join(" · ");
    } catch (_) {
      caps = { pdf: true, word: false, ghostscript: false };
      $("conversao-capacidades").textContent = "Sem conexão: conversão indisponível.";
    }
    atualizar();
  }

  function ligar() {
    if (bound) return;
    bound = true;
    const btnModo = $("modo-conversao");
    if (btnModo && !btnModo.dataset.ligado) {
      btnModo.dataset.ligado = "1";
      btnModo.addEventListener("click", () => {
        ["modo-simples", "modo-contrato"].forEach(id => $(id)?.removeAttribute("aria-current"));
        btnModo.setAttribute("aria-current", "page");
        ui().mostrarTela("conversao");
        carregarCapacidades();
      });
    }
    const drop = $("drop-conversao");
    drop.addEventListener("click", anexar);
    drop.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); anexar(); }
    });
    // O shell não expõe caminhos de arquivos arrastados (segurança): o gesto
    // abre o diálogo nativo para concluir a seleção.
    ["dragenter", "dragover"].forEach(ev => drop.addEventListener(ev, (e) => {
      e.preventDefault();
      drop.classList.add("arrastando");
    }));
    ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, (e) => {
      e.preventDefault();
      drop.classList.remove("arrastando");
    }));
    drop.addEventListener("drop", () => { anexar(); });
    $("btn-converter").addEventListener("click", converter);
    $("btn-conversao-cancelar").addEventListener("click", cancelar);
    $("btn-conversao-limpar").addEventListener("click", () => {
      if (active) return;
      arquivos = [];
      $("conversao-resultados").replaceChildren();
      $("btn-conversao-abrir").hidden = true;
      status("idle", "Nenhuma conversão", "Selecione ao menos um arquivo e a pasta de saída.");
      renderLista();
      atualizar();
    });
    $("btn-conversao-pasta").addEventListener("click", async () => {
      if (active) return;
      try {
        const r = await api().selectOutput();
        if (r.cancelled) return;
        if (r.selection_id) {
          outputId = r.selection_id;
          $("conversao-pasta").value = r.name || "Pasta selecionada";
          atualizar();
        } else ui().toast("Não foi possível selecionar a pasta.", "error");
      } catch (_) { ui().toast("Falha ao abrir o seletor.", "error"); }
    });
    $("conversao-formato").addEventListener("change", atualizar);
    $("conversao-nome").addEventListener("input", atualizar);
    document.addEventListener("DOMContentLoaded", carregarCapacidades);
    if (document.readyState !== "loading") carregarCapacidades();
  }

  window.ContractoConversao = { ligar, atualizar: () => { renderLista(); atualizar(); } };
})();
