/* Tour guiado simples: balão ancorado em elementos reais da Etapa 1. */
(function () {
  "use strict";
  const PASSOS = [
    ["#modo-contrato", "Modo de geração", "Simples gera vários formulários; Contrato monta o processo completo; Conversão transforma arquivos avulsos em PDF."],
    ["#seletor-modelos", "Modelo", "Escolha o modelo do documento. No modo Contrato é apenas um contrato."],
    ["#btn-adicionar", "Participantes", "Adicione compradores ou signatários; cada um tem o seu cartão de dados."],
    ["#pasta-saida", "Pasta de saída", "Defina onde salvar. Cada trabalho cria a sua própria subpasta."],
    ["#btn-gerar", "Gerar", "Libera quando não há campos pendentes. Depois você confere (Etapa 2) e conclui (Etapa 3)."],
    ["#btn-ajuda-topo", "Ajuda", "O guia completo está sempre aqui — ou aperte F1."]
  ];
  let balao = null, indice = 0, alvoAtual = null;

  function limpar() {
    alvoAtual?.classList.remove("tour-alvo");
    alvoAtual = null;
  }
  function posicionar() {
    if (!balao || !alvoAtual) return;
    const r = alvoAtual.getBoundingClientRect(), b = balao.getBoundingClientRect();
    const abaixo = r.bottom + 12 + b.height < window.innerHeight;
    const top = abaixo ? r.bottom + 12 : Math.max(8, r.top - b.height - 12);
    const left = Math.min(Math.max(8, r.left + r.width / 2 - b.width / 2), window.innerWidth - b.width - 8);
    balao.style.top = top + "px";
    balao.style.left = left + "px";
  }
  function mostrar() {
    limpar();
    const [seletor, titulo, texto] = PASSOS[indice];
    const alvo = document.querySelector(seletor);
    // Alvo ausente (ex.: seção oculta pelo modo): pula para o próximo passo.
    if (!alvo || alvo.closest("[hidden]")) {
      if (indice < PASSOS.length - 1) { indice++; mostrar(); } else fechar();
      return;
    }
    alvoAtual = alvo;
    alvo.classList.add("tour-alvo");
    alvo.scrollIntoView({ block: "center" });
    balao.replaceChildren();
    const cab = document.createElement("strong");
    cab.textContent = titulo;
    const p = document.createElement("p");
    p.textContent = texto;
    const rod = document.createElement("div");
    rod.className = "tour-rodape";
    const pos = document.createElement("span");
    pos.className = "hint";
    pos.textContent = (indice + 1) + " de " + PASSOS.length;
    const pular = document.createElement("button");
    pular.type = "button"; pular.className = "btn btn-subtle"; pular.textContent = "Pular";
    pular.addEventListener("click", fechar);
    const ultimo = indice === PASSOS.length - 1;
    const avancar = document.createElement("button");
    avancar.type = "button"; avancar.className = "btn btn-primary btn-sm"; avancar.textContent = ultimo ? "Concluir" : "Próximo";
    avancar.addEventListener("click", () => { if (ultimo) fechar(); else { indice++; mostrar(); } });
    rod.append(pos, pular, avancar);
    balao.append(cab, p, rod);
    posicionar();
    avancar.focus({ preventScroll: true });
  }
  function fechar() {
    limpar();
    balao?.remove();
    balao = null;
    window.removeEventListener("resize", posicionar);
    document.removeEventListener("keydown", teclas, true);
  }
  function teclas(ev) {
    if (ev.key === "Escape") { ev.preventDefault(); fechar(); }
  }
  function iniciar() {
    fechar();
    window.ContractoUI?.mostrarTela("inicio");
    balao = document.createElement("div");
    balao.className = "tour";
    balao.setAttribute("role", "dialog");
    balao.setAttribute("aria-label", "Tour guiado");
    document.body.append(balao);
    indice = 0;
    window.addEventListener("resize", posicionar);
    document.addEventListener("keydown", teclas, true);
    mostrar();
  }
  window.ContractoTour = { iniciar, fechar };
})();
