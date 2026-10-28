/* Tela Perfis: lista por modo, CRUD, importação/exportação e backup (ADR 0020).
 * O estado do catálogo continua na Etapa 1; aqui só chega pelo contexto de `iniciar`. */
(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  let ctx = null;
  const nomeExibicao = (p) => ctx.nomeExibicao(p);

  function carregarTelaPerfis() {
    // Ligue a busca antes da atualização assíncrona. O catálogo já pode estar
    // em memória quando a tela abre; nesse caso o usuário consegue digitar
    // antes da resposta HTTP terminar.
    const search = $("buscar-perfis");
    if (search && !search.dataset.ligado) {
      search.dataset.ligado = "1";
      search.addEventListener("input", renderProfilesManagement);
      search.oninput = renderProfilesManagement;
    }
    if (ctx.catalogo() && ctx.catalogo().length) {
      renderProfilesManagement();
    }
    window.ContractoAPI.getProfiles().then(r => {
      if (r.status === 200 && Array.isArray(r.data)) {
        ctx.definirCatalogo(r.data);
        renderProfilesManagement();
        // CRUD na aba Perfis também atualiza a Etapa 1 sem perder a seleção.
        ctx.aoAtualizarCatalogo();
      }
    });
  }

  function renderProfilesManagement() {
    const container = $("lista-perfis");
    if (!container) return;
    container.replaceChildren();

    const search = $("buscar-perfis");
    const termo = (search?.value || "").trim().toLowerCase();

    // Qualquer modo que não seja simples conta como contrato (mesmo critério do badge e do backend).
    const modoDe = p => ((p.modo_fluxo || p.mode) === "formulario_simples" ? "formulario_simples" : "contrato");
    const rotuloModo = { formulario_simples: "Modo Simples", contrato: "Modo Contrato" };
    const filtrados = ctx.catalogo().filter(p => {
      if (!termo) return true;
      const nome = (p.nome || p.name || "").toLowerCase();
      const modo = ((p.modo_fluxo || p.mode || "") + " " + rotuloModo[modoDe(p)] + " " + (modoDe(p) === "contrato" ? "completo" : "formulário")).toLowerCase();
      const desc = (p.descricao || "").toLowerCase();
      return nome.includes(termo) || modo.includes(termo) || desc.includes(termo);
    });

    const vazio = $("perfis-vazio");
    if (vazio) vazio.hidden = filtrados.length > 0;

    const grupos = {};
    Object.keys(rotuloModo).forEach(chave => {
      const itens = filtrados.filter(p => modoDe(p) === chave);
      if (!itens.length) return;
      const sec = document.createElement("section");
      sec.className = "perfis-grupo";
      sec.setAttribute("aria-labelledby", "perfis-grupo-" + chave);
      const h = document.createElement("h3");
      h.id = "perfis-grupo-" + chave;
      h.className = "perfis-grupo-titulo";
      h.textContent = rotuloModo[chave];
      const n = document.createElement("span");
      n.className = "seletor-count";
      n.textContent = "(" + itens.length + ")";
      h.append(n);
      sec.append(h);
      container.append(sec);
      grupos[chave] = sec;
    });

    filtrados.forEach(p => {
      const card = document.createElement("div");
      card.className = "profile-item-card";

      const header = document.createElement("div");
      header.className = "profile-item-header";

      const titleGroup = document.createElement("div");
      titleGroup.className = "profile-item-title";

      const title = document.createElement("h4");
      title.textContent = (typeof nomeExibicao === "function" ? nomeExibicao({ name: p.nome || p.name, nome: p.nome || p.name }) : (p.nome || p.name)) || p.profile_id;

      const badge = document.createElement("span");
      badge.className = "profile-badge";
      badge.textContent = (p.modo_fluxo || p.mode) === "formulario_simples" ? "Formulário Simples" : "Contrato Completo";

      titleGroup.append(title, badge);

      const actionsGroup = document.createElement("div");
      actionsGroup.className = "profile-actions";
      const btnAtivar = document.createElement("button");
      btnAtivar.type = "button";
      btnAtivar.className = "btn btn-primary btn-sm";
      btnAtivar.textContent = "Ativar";
      btnAtivar.addEventListener("click", () => ativarPerfil(p.nome || p.name));
      const btnEdt = document.createElement("button");
      btnEdt.type = "button";
      btnEdt.className = "btn btn-secondary btn-sm";
      btnEdt.textContent = "Editar";
      btnEdt.addEventListener("click", () => editarPerfilModal(p));
      const menu = document.createElement("details");
      menu.className = "profile-menu";
      const sum = document.createElement("summary");
      sum.className = "btn btn-secondary btn-sm";
      sum.textContent = "Mais ações";
      menu.append(sum);
      const menuBox = document.createElement("div");
      menuBox.className = "profile-menu-box";
      [["Duplicar", () => duplicarPerfilModal(p)], ["Exportar", () => exportarPerfilModal(p)], ["Excluir", () => excluirPerfilModal(p)]].forEach(([rot, fn])=>{
        const b = document.createElement("button");
        b.type = "button"; b.className = "btn btn-secondary btn-sm";
        b.textContent = rot;
        if (rot === "Excluir") b.classList.add("btn-danger");
        b.addEventListener("click", ()=>{ menu.open = false; fn(); });
        menuBox.append(b);
      });
      menu.append(menuBox);
      actionsGroup.append(btnAtivar, btnEdt, menu);
      header.append(titleGroup, actionsGroup);

      const details = document.createElement("p");
      details.className = "hint profile-item-meta";
      const campos = p.campos_entrada || p.fields || [];
      details.textContent = `${campos.length} campos configurados • Formato: ${p.formato_saida || "PDF/A-2b"} • Máx. participantes: ${p.max_participantes || 4}`;

      card.append(header, details);
      grupos[modoDe(p)].append(card);
    });
  }

  function duplicarPerfilModal(p) {
    const nomeAtual = p.nome || p.name;
    const wrap = document.createElement("div");
    const dica = document.createElement("p");
    dica.className = "hint";
    dica.textContent = `Digite o nome para a cópia do perfil "${nomeAtual}":`;
    const campo = document.createElement("div");
    campo.className = "field";
    campo.style.marginTop = "10px";
    const rotulo = document.createElement("label");
    rotulo.htmlFor = "dup-nome-input";
    rotulo.textContent = "Novo nome";
    const entrada = document.createElement("input");
    entrada.id = "dup-nome-input";
    entrada.autocomplete = "off";
    entrada.value = nomeAtual + " (Cópia)";
    campo.append(rotulo, entrada);
    wrap.append(dica, campo);
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
    const dica = document.createElement("p");
    dica.className = "hint";
    dica.textContent = `Copie o JSON do perfil "${p.nome || p.name}":`;
    const campo = document.createElement("div");
    campo.className = "field";
    campo.style.marginTop = "10px";
    const area = document.createElement("textarea");
    area.id = "json-export-area";
    area.rows = 12;
    area.readOnly = true;
    area.style.fontFamily = "monospace";
    area.style.fontSize = "0.85rem";
    area.value = jsonStr;
    campo.append(area);
    wrap.append(dica, campo);
    window.ContractoUI.abrirModal("Exportar perfil", wrap, [
      {
        texto: "Salvar .json",
        primario: true,
        aoClicar: async () => {
          const nome = p.nome || p.name;
          try {
            const r = await window.ContractoAPI.exportProfile(nome);
            if (r.cancelled) return;
            if (r.ok) window.ContractoUI.toast(`Perfil "${nome}" salvo em .json.`, "success");
            else window.ContractoUI.toast("Não foi possível salvar o arquivo.", "error");
          } catch (_) { window.ContractoUI.toast("Falha ao salvar o arquivo.", "error"); }
        }
      },
      {
        texto: "Copiar JSON",
        primario: false,
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
      {
        texto: "Escolher arquivo .json",
        primario: true,
        aoClicar: async () => {
          try {
            const r = await window.ContractoAPI.importProfile();
            if (r.cancelled) return;
            if (r.ok) {
              window.ContractoUI.toast(`Perfil "${r.nome}" importado com sucesso!`, "success");
              await ctx.recarregarCatalogo();
              await carregarTelaPerfis();
            } else {
              window.ContractoUI.toast("Arquivo inválido: selecione um .json de perfil.", "error");
            }
          } catch (_) { window.ContractoUI.toast("Falha ao importar o arquivo.", "error"); }
        }
      },
      { texto: "Cancelar", primario: false },
      {
        texto: "Importar texto colado",
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
    const dica = document.createElement("p");
    dica.className = "hint";
    dica.textContent = `Edite a identificação abaixo ou o JSON completo do perfil "${p.nome || p.name}":`;
    // Fase 3: cabeçalho estruturado (identificação/modo/formato/participantes)
    // para não exigir JSON em ajustes simples; mesclado ao salvar.
    const grade = document.createElement("div");
    grade.className = "field-grid";
    grade.style.marginTop = "10px";
    const modos = [["contrato", "Contrato Completo"], ["formulario_simples", "Formulário Simples"]];
    const modoAtual = p.modo_fluxo || p.mode || "contrato";
    if (!modos.some(([v]) => v === modoAtual)) modos.push([modoAtual, modoAtual]);
    const formatos = ["PDF/A-2b", "PDF"];
    const formatoAtual = p.formato_saida || "PDF/A-2b";
    if (!formatos.includes(formatoAtual)) formatos.push(formatoAtual);
    // Valores vindos do perfil nunca vão crus ao innerHTML (DESIGN.md §9).
    const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    grade.innerHTML = `
      <div class="field"><label for="edit-nome">Nome do perfil</label><input id="edit-nome" autocomplete="off"></div>
      <div class="field"><label for="edit-modo">Modo de fluxo</label><select id="edit-modo">${modos.map(([v, r]) => `<option value="${esc(v)}">${esc(r)}</option>`).join("")}</select></div>
      <div class="field"><label for="edit-formato">Formato de saída</label><select id="edit-formato">${formatos.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join("")}</select></div>
      <div class="field"><label for="edit-max">Máx. participantes</label><input id="edit-max" type="number" min="1" max="4"></div>
    `;
    grade.querySelector("#edit-nome").value = p.nome || p.name || "";
    grade.querySelector("#edit-modo").value = modoAtual;
    grade.querySelector("#edit-formato").value = formatoAtual;
    grade.querySelector("#edit-max").value = p.max_participantes || p.max_participants || 4;
    const campo = document.createElement("div");
    campo.className = "field";
    campo.style.marginTop = "10px";
    const area = document.createElement("textarea");
    area.id = "edit-json-area";
    area.rows = 12;
    area.style.fontFamily = "monospace";
    area.style.fontSize = "0.85rem";
    area.value = jsonStr;
    area.setAttribute("aria-label", "JSON completo do perfil");
    campo.append(area);
    wrap.append(dica, grade, campo);
    window.ContractoUI.abrirModal("Editar perfil", wrap, [
      { texto: "Cancelar", primario: false },
      {
        texto: "Salvar alterações",
        primario: true,
        aoClicar: async () => {
          const text = wrap.querySelector("#edit-json-area").value.trim();
          try {
            const parsed = JSON.parse(text);
            const nomeCabecalho = wrap.querySelector("#edit-nome").value.trim();
            if (nomeCabecalho) { parsed.nome = nomeCabecalho; parsed.name = nomeCabecalho; }
            parsed.modo_fluxo = wrap.querySelector("#edit-modo").value;
            parsed.mode = wrap.querySelector("#edit-modo").value;
            parsed.formato_saida = wrap.querySelector("#edit-formato").value;
            const max = parseInt(wrap.querySelector("#edit-max").value || "4", 10);
            parsed.max_participantes = Math.min(4, Math.max(1, max || 4));
            parsed.max_participants = parsed.max_participantes;
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

  async function ativarPerfil(nome) {
    const r = await window.ContractoAPI.activateProfile(nome);
    if (r.status === 200) {
      window.ContractoUI.toast(`Perfil "${nome}" ativado.`, "success");
      await carregarTelaPerfis();
    } else {
      window.ContractoUI.toast(r.data?.message || "Não foi possível ativar o perfil.", "error");
    }
  }
  async function backupPerfis() {
    const r = await window.ContractoAPI.backupSystem();
    if (r.status === 200) window.ContractoUI.toast(`Backup criado (${r.data.name}).`, "success");
    else window.ContractoUI.toast(r.data?.message || "Não foi possível criar o backup.", "error");
  }
  async function restaurarPerfis() {
    const sel = await window.ContractoAPI.selectBackup();
    if (!sel || sel.cancelled) return;
    if (!sel.selection_id) { window.ContractoUI.toast("Não foi possível selecionar o backup.", "error"); return; }
    const r = await window.ContractoAPI.restoreSystem(sel.selection_id);
    if (r.status === 200) {
      window.ContractoUI.toast("Backup restaurado. Recarregando perfis.", "success");
      await ctx.recarregar();
      await carregarTelaPerfis();
    } else {
      window.ContractoUI.toast(r.data?.message || "Backup inválido.", "error");
    }
  }

  function ligar() {
    const btnNovoPerfil = $("btn-novo-perfil");
    if (btnNovoPerfil && !btnNovoPerfil.dataset.ligado) { btnNovoPerfil.dataset.ligado = "1"; btnNovoPerfil.addEventListener("click", novoPerfilModal); }
    const btnImpPerfil = $("btn-importar-perfil");
    if (btnImpPerfil && !btnImpPerfil.dataset.ligado) { btnImpPerfil.dataset.ligado = "1"; btnImpPerfil.addEventListener("click", importarPerfilModal); }
    const btnBackup = $("btn-backup-perfis");
    if (btnBackup && !btnBackup.dataset.ligado) { btnBackup.dataset.ligado = "1"; btnBackup.addEventListener("click", backupPerfis); }
    const btnRestore = $("btn-restaurar-perfis");
    if (btnRestore && !btnRestore.dataset.ligado) { btnRestore.dataset.ligado = "1"; btnRestore.addEventListener("click", restaurarPerfis); }
    const busqPerfil = $("buscar-perfis");
    if (busqPerfil && !busqPerfil.dataset.gerenciado) {
      busqPerfil.dataset.gerenciado = "1";
      busqPerfil.addEventListener("input", renderProfilesManagement);
      // Também use a propriedade DOM: alguns hosts WebView restauram a árvore
      // durante a primeira navegação entre telas e podem descartar listeners.
      busqPerfil.oninput = renderProfilesManagement;
    }
  }

  window.ContractoPerfis = { iniciar: (contexto) => { ctx = contexto; }, ligar, carregarTela: carregarTelaPerfis };
})();
