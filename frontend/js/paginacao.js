/* Paginação do formulário (abas livres com selo de pendências) e lista de pendências com "Gerar mesmo assim".
 * Só desenha; o estado (página atual, erros) fica na Etapa 1. */
(function () {
  "use strict";
  const ui = () => window.ContractoUI;

  // Abas livres: dá para ir a qualquer página sem preencher a anterior.
  function renderizar(host, {paginas, atual, ir}) {
    host.replaceChildren();
    const abas = document.createElement("div");
    abas.className = "pag-abas"; abas.setAttribute("role", "tablist"); abas.setAttribute("aria-label", "Páginas do formulário");
    paginas.forEach((nome, i) => {
      const aba = document.createElement("button");
      aba.type = "button"; aba.className = "pag-aba"; aba.id = "pag-aba-" + i; aba.setAttribute("role", "tab");
      aba.setAttribute("aria-selected", String(i === atual)); aba.tabIndex = i === atual ? 0 : -1;
      const num = document.createElement("span"); num.className = "pag-num"; num.textContent = i + 1;
      const texto = document.createElement("span"); texto.className = "pag-nome"; texto.textContent = nome;
      const estado = document.createElement("span"); estado.className = "pag-estado"; estado.hidden = true;
      aba.append(num, texto, estado);
      aba.addEventListener("click", () => ir(i));
      aba.addEventListener("keydown", e => {
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); ir(i + (e.key === "ArrowRight" ? 1 : -1), true); }
      });
      abas.append(aba);
    });
    const nav = document.createElement("div");
    nav.className = "pag-nav";
    const botao = (texto, icone, desativado, destino, antes) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "btn btn-secondary btn-sm"; b.textContent = texto; b.disabled = desativado;
      antes ? b.prepend(ui().icone(icone)) : b.append(ui().icone(icone));
      b.addEventListener("click", () => ir(destino));
      return b;
    };
    const info = document.createElement("span");
    info.className = "paginacao-indicador"; info.textContent = "Página " + (atual + 1) + " de " + paginas.length;
    nav.append(botao("Anterior", "back", atual === 0, atual - 1, true), info, botao("Próxima", "advance", atual >= paginas.length - 1, atual + 1, false));
    host.append(abas, nav);
  }

  // Selo de cada aba: quantas pendências a página tem (✓ quando nenhuma).
  function selos(contagens) {
    contagens.forEach((n, i) => {
      const estado = document.getElementById("pag-aba-" + i)?.querySelector(".pag-estado");
      if (!estado) return;
      estado.hidden = false; estado.classList.toggle("pendente", n > 0);
      estado.textContent = n ? String(n) : "✓";
      estado.title = n ? n + " pendência(s) nesta página" : "Sem pendências";
    });
  }

  // `bloqueios`: textos que impedem gerar; `opcionais`: [{texto, erro}] que o usuário pode ignorar.
  function listaPendencias({bloqueios, opcionais, ir, gerarMesmoAssim}) {
    const wrap = document.createElement("div");
    const intro = document.createElement("p");
    intro.className = "hint";
    intro.textContent = bloqueios.length ? "Toque em um item para ir até o campo e corrigir."
      : "Estes campos estão vazios ou fora do formato. Você pode preenchê-los agora ou gerar assim mesmo.";
    const lista = document.createElement("div");
    lista.className = "pendencias-lista";
    [...bloqueios.map(texto => ({texto, erro: null})), ...opcionais].forEach(({texto, erro}) => {
      const item = document.createElement("button");
      item.type = "button"; item.className = "pendencia-item"; item.textContent = texto;
      item.addEventListener("click", () => { ui().fecharModal(); ir(texto, erro); });
      lista.append(item);
    });
    wrap.append(intro, lista);
    const podeIgnorar = !bloqueios.length && opcionais.length > 0;
    const botoes = [{texto: podeIgnorar ? "Voltar e preencher" : "Fechar", primario: !podeIgnorar}];
    if (podeIgnorar) botoes.push({texto: "Gerar mesmo assim", primario: true, aoClicar: gerarMesmoAssim});
    ui().abrirModal(bloqueios.length ? "Revise os campos pendentes" : "Campos sem preencher", wrap, botoes);
  }

  window.ContractoPaginacao = {renderizar, selos, listaPendencias};
})();
