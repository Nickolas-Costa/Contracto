/* Padrões de leitura de documentos (Configurações): "o dado X vem depois da frase Y e vai até Z".
 * Servem para contratos e textos corridos em que não há rótulo fixo ("Nome:"); somam-se aos padrões do app.
 * Os dados vivem em contracto_config.json (padroes_leitura). */
(function () {
  "use strict";
  const TIPOS = [["nome", "Nome do comprador / proponente"], ["vendedor", "Nome do vendedor"], ["razao", "Razão social"],
    ["endereco", "Endereço da pessoa"], ["endereco_imovel", "Endereço do imóvel"], ["mae", "Nome da mãe"], ["pai", "Nome do pai"], ["matricula", "Matrícula do imóvel"]];
  const ATE = [["virgula", "a vírgula"], ["ponto", "o ponto final"], ["ponto_e_virgula", "o ponto e vírgula"], ["fim_da_linha", "o fim da linha"]];

  function seletor(opcoes, valor, rotulo) {
    const s = document.createElement("select");
    s.setAttribute("aria-label", rotulo);
    opcoes.forEach(([v, t]) => s.append(new Option(t, v)));
    s.value = valor || opcoes[0][0];
    return s;
  }

  function linha(item) {
    const box = document.createElement("div");
    box.className = "padrao-leitura";
    const tipo = seletor(TIPOS, item.tipo, "Dado a ler"); tipo.className = "pl-tipo";
    const antes = document.createElement("input");
    antes.type = "text"; antes.className = "pl-antes"; antes.value = item.antes || ""; antes.maxLength = 120;
    antes.placeholder = "Frase que vem antes. Ex.: doravante denominado(s) DEVEDOR(ES):"; antes.setAttribute("aria-label", "Frase que vem antes do dado");
    const ate = seletor(ATE, item.ate, "Onde o dado termina"); ate.className = "pl-ate";
    const rotuloAte = document.createElement("span"); rotuloAte.className = "hint"; rotuloAte.textContent = "até";
    const remover = document.createElement("button");
    remover.type = "button"; remover.className = "btn btn-subtle"; remover.textContent = "Remover";
    remover.prepend(window.ContractoUI.icone("trash"));
    remover.addEventListener("click", () => box.remove());
    box.append(tipo, antes, rotuloAte, ate, remover);
    return box;
  }

  function montar(host, lista) {
    if (!host) return;
    host.replaceChildren(...(lista || []).map(linha));
  }
  function adicionar(host) {
    const nova = linha({});
    host.append(nova);
    nova.querySelector(".pl-antes").focus();
  }
  // Linhas sem a frase ficam de fora (o servidor também as descarta).
  function ler(host) {
    return [...host.querySelectorAll(".padrao-leitura")].map(b => ({
      tipo: b.querySelector(".pl-tipo").value, antes: b.querySelector(".pl-antes").value.trim(), ate: b.querySelector(".pl-ate").value,
    })).filter(p => p.antes);
  }

  window.ContractoPadroes = {montar, adicionar, ler};
})();
