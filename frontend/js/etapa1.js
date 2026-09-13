/* Etapa 1: perfis, participantes, destino, geração e fila. */
(function () {
  "use strict";

  const api = () => window.ContractoAPI;
  const ui = () => window.ContractoUI;

  const estado = {
    perfis: [],
    perfilId: null,
    campos: [],
    participantes: 1,
    outputId: null,
    jobId: null,
    pollTimer: null,
    ultimo: null,
  };

  function lerParaEtapa2() {
    return estado.ultimo;
  }

  function texto(el, msg) {
    el.textContent = msg;
  }

  function campoTexto(rotulo, id, attrs) {
    const wrap = document.createElement("div");
    wrap.className = "field";
    const lab = document.createElement("label");
    lab.setAttribute("for", id);
    lab.textContent = rotulo;
    const inp = document.createElement("input");
    inp.id = id;
    Object.assign(inp, attrs || {});
    inp.setAttribute("autocomplete", "off");
    const err = document.createElement("div");
    err.className = "erro";
    err.hidden = true;
    wrap.append(lab, inp, err);
    return { wrap, inp, err };
  }

  function marcarErro(input, errEl, msg) {
    if (!msg) {
      input.removeAttribute("aria-invalid");
      errEl.hidden = true;
      errEl.textContent = "";
      return;
    }
    input.setAttribute("aria-invalid", "true");
    errEl.hidden = false;
    errEl.textContent = msg;
  }

  async function carregar() {
    const r = await api().request("GET", "/api/v1/profiles");
    if (r.status !== 200) {
      ui().toast("Não foi possível carregar os formulários.", "error");
      return;
    }
    estado.perfis = r.data;
    const caixa = document.getElementById("lista-formularios");
    caixa.innerHTML = "";
    estado.perfis.forEach((p) => {
      const lab = document.createElement("label");
      const chk = document.createElement("input");
      chk.type = "checkbox";
      chk.value = p.profile_id;
      chk.checked = estado.perfilId === null;
      chk.addEventListener("change", () => {
        const marcados = [...caixa.querySelectorAll("input:checked")].map((c) => c.value);
        selecionar(marcados);
      });
      lab.append(chk, document.createTextNode(" " + p.name));
      caixa.append(lab, document.createElement("br"));
    });
    const iniciais = estado.perfis.filter((p) => p.mode === "contrato").map((p) => p.profile_id);
    selecionar(iniciais.length ? [iniciais[0]] : estado.perfis.slice(0, 1).map((p) => p.profile_id));
  }

  async function selecionar(ids) {
    if (!ids.length) return;
    const r = await api().request("POST", "/api/v1/profiles/compose", { profile_ids: ids });
    if (r.status !== 200) {
      ui().toast((r.data && r.data.message) || "Formulários incompatíveis.", "error");
      return;
    }
    estado.perfilId = ids;
    estado.campos = r.data.fields || [];
    renderParticipantes();
    atualizarPendencias();
  }

  function escopoCampos() {
    return estado.campos.filter((c) => (c.escopo || "participante") === "participante");
  }

  function renderParticipantes() {
    const caixa = document.getElementById("participantes");
    caixa.innerHTML = "";
    for (let i = 0; i < estado.participantes; i++) {
      const card = document.createElement("div");
      card.className = "card";
      const h = document.createElement("h2");
      h.textContent = i === 0 ? "Participante principal" : "Participante " + (i + 1);
      card.append(h);
      const nome = campoTexto("Nome completo", "nome-" + i, {});
      const cpf = campoTexto("CPF", "cpf-" + i, { inputMode: "numeric" });
      card.append(nome.wrap, cpf.wrap);
      escopoCampos().forEach((c) => {
        const f = campoTexto(c.rotulo || c.id, "dyn-" + i + "-" + c.id, {});
        f.inp.dataset.campoId = c.id;
        card.append(f.wrap);
      });
      caixa.append(card);
    }
  }

  function lerParticipantes() {
    const lista = [];
    for (let i = 0; i < estado.participantes; i++) {
      const get = (id) => document.getElementById(id).value.trim();
      const dinamicos = {};
      document.querySelectorAll("#participantes [data-campo-id]").forEach((inp) => {
        const pagina = Number(inp.closest(".card") ? [...document.getElementById("participantes").children].indexOf(inp.closest(".card")) : 0);
        if (pagina === i && inp.value.trim()) dinamicos[inp.dataset.campoId] = inp.value.trim();
      });
      lista.push({
        nome_completo: get("nome-" + i),
        cpf: get("cpf-" + i),
        endereco: "",
        data_assinatura: document.getElementById("data-assinatura").value.trim(),
        local_assinatura: document.getElementById("local-assinatura").value.trim(),
        campos_dinamicos: dinamicos,
      });
    }
    return lista;
  }

  function validarLocal() {
    const faltas = [];
    const lista = lerParticipantes();
    lista.forEach((p, i) => {
      if (!p.nome_completo) faltas.push("Participante " + (i + 1) + ": nome");
      if (!p.cpf) faltas.push("Participante " + (i + 1) + ": CPF");
    });
    if (!document.getElementById("data-assinatura").value.trim()) faltas.push("Data da assinatura");
    if (!document.getElementById("local-assinatura").value.trim()) faltas.push("Local da assinatura");
    if (!estado.outputId) faltas.push("Diretório de saída");
    return { lista, faltas };
  }

  function atualizarPendencias() {
    const { faltas } = validarLocal();
    const el = document.getElementById("pendencias");
    const btn = document.getElementById("btn-ver-pendencias");
    const gerar = document.getElementById("btn-gerar");
    if (!faltas.length) {
      el.textContent = "Pronto para gerar.";
      el.classList.add("pronto");
      btn.hidden = true;
      gerar.disabled = false;
    } else {
      el.textContent = faltas.length + " pendência(s).";
      el.classList.remove("pronto");
      btn.hidden = false;
      gerar.disabled = true;
      btn.onclick = () => {
        const ul = document.createElement("ul");
        faltas.forEach((f) => {
          const li = document.createElement("li");
          li.textContent = f;
          ul.append(li);
        });
        ui().abrirModal("Campos pendentes", ul, [{ texto: "Entendi", primario: true }]);
      };
    }
  }

  async function escolherPasta() {
    const r = await api().selectOutput();
    if (r.cancelled) return;
    if (r.selection_id) {
      estado.outputId = r.selection_id;
      document.getElementById("pasta-saida").value = "Pasta selecionada";
    } else {
      ui().toast("Não foi possível selecionar a pasta.", "error");
    }
    atualizarPendencias();
  }

  async function gerar() {
    const { lista, faltas } = validarLocal();
    if (faltas.length || !estado.perfilId) { atualizarPendencias(); return; }
    estado.ultimaLista = lista;
    const r = await api().request("POST", "/api/v1/jobs/generate", {
      profile_ids: estado.perfilId,
      participants: lista,
      output_id: estado.outputId,
    });
    if (r.status !== 202) {
      const det = r.data && r.data.issues ? ": " + r.data.issues.map((x) => x.field).join(", ") : "";
      ui().toast(((r.data && r.data.message) || "Falha ao gerar.") + det, "error");
      return;
    }
    estado.jobId = r.data.job_id;
    ui().irEtapa(2);
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
          estado.ultimo = {
            participants: estado.ultimaLista || [],
            output_id: estado.outputId,
            file_ids: s.file_ids || [],
          };
          statusEl.textContent += " Concluído.";
          const btn = document.getElementById("btn-abrir-pasta");
          btn.hidden = false;
          btn.onclick = async () => {
            const o = await api().openResult(estado.jobId);
            if (!o.ok) ui().toast("Não foi possível abrir a pasta.", "error");
          };
          ui().toast("Documentos gerados.", "success");
        } else if (s.status === "failed") {
          ui().toast((s.error && s.error.message) || "Falha no processo.", "error");
        }
      }
    };
    estado.pollTimer = setInterval(sondar, 800);
    sondar();
  }

  function ligar() {
    document.getElementById("btn-pasta").addEventListener("click", escolherPasta);
    document.getElementById("btn-gerar").addEventListener("click", gerar);
    document.getElementById("tela-inicio").addEventListener("input", atualizarPendencias);
    document.getElementById("modo-simples").addEventListener("click", () => {
      document.getElementById("modo-simples").setAttribute("aria-current", "page");
      document.getElementById("modo-avancado").removeAttribute("aria-current");
      ui().toast("Modo Simples: marque os formulários desejados.", "info");
    });
    document.getElementById("modo-avancado").addEventListener("click", () => {
      document.getElementById("modo-avancado").setAttribute("aria-current", "page");
      document.getElementById("modo-simples").removeAttribute("aria-current");
      carregar();
    });
    carregar();
  }

  window.ContractoEtapa1 = { ligar, lerParaEtapa2 };
})();
