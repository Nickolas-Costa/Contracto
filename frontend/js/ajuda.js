/* Guia de ajuda (F1 e botão Ajuda): abas com passo a passo, documentos do cliente, dicas e problemas comuns.
 * Só texto e montagem do diálogo; para mudar o conteúdo basta editar GUIA. */
(function () {
  "use strict";
  const GUIA = {
    "Passo a passo": [
      ["Escolha o modo", "Simples gera vários formulários de uma vez; Contrato monta o processo completo (1 contrato + formulários); Conversão transforma arquivos avulsos em PDF."],
      ["Selecione o modelo e preencha", "Informe os dados de cada participante. Nome, CPF, data e local são necessários; os demais campos podem ficar para depois."],
      ["Defina assinatura e pasta", "Data, local e a pasta onde os documentos serão salvos. Cada trabalho cria a sua própria subpasta."],
      ["Confira o resumo (Etapa 2)", "Revise participantes, campos e modelos; clique em um valor para corrigi-lo. Anexe documentos extras (PDF ou RTF) se o processo pedir."],
      ["Confirme e conclua", "No Contrato, escolha PDF ou PDF/A-2b na Conferência: ao confirmar, os documentos são gerados, convertidos e organizados de uma vez. A Etapa 3 mostra o resultado. Os originais nunca são alterados."]
    ],
    "Documentos do cliente": [
      ["Abra a leitura", "Escolha o modelo e clique em Ler documentos (faixa no topo), ou simplesmente arraste os arquivos para a janela."],
      ["Formatos aceitos", "PDF, RTF, DOC e DOCX, até 20 arquivos. RTF, DOC e DOCX viram PDF na hora (precisa do Microsoft Word); PDF segue como está."],
      ["O que é lido", "Nome, CPF, CNPJ, PIS/PASEP, data de nascimento, e-mail, telefone, CEP, endereço, matrícula e formulários gerados pelo próprio Contracto. Imagens escaneadas não têm texto para ler."],
      ["Confira ao lado do documento", "Cada valor vem com a página e o grau de confiança; ao clicar no valor, o documento mostra a página. Edite o que precisar e desmarque o que não quiser."],
      ["Escolha de quem são os dados", "Para cada arquivo, escolha o participante (ou dados compartilhados, como vendedor e imóvel). Valores que trocam algo já preenchido avisam \"será substituído\"."],
      ["Ensine seus padrões", "Se o seu contrato escreve o nome ou o endereço de um jeito próprio, cadastre em Configurações > Padrões de leitura: a frase que vem antes e onde o dado termina."],
      ["Aplique e, se quiser, desfaça", "Só o que estiver marcado entra no formulário, com as mesmas máscaras da digitação. O botão Desfazer última leitura volta ao que havia antes. Seus originais nunca são alterados."]
    ],
    "Dicas e atalhos": [
      ["F1", "Abre este guia em qualquer tela."],
      ["Esc", "Fecha diálogos e avisos."],
      ["Tab / Shift+Tab", "Percorre campos e botões; Enter ou Espaço aciona."],
      ["Páginas do formulário", "Clique em qualquer aba para ir direto à página; o número ao lado do nome mostra quantos campos faltam nela (✓ quando nada falta)."],
      ["Perfis", "Guarde modelos prontos (campos e formatos) e reutilize em novos trabalhos; faça backup em Configurações."],
      ["Configurações", "Tema claro/escuro, cor de destaque, largura dos quadros, formato de saída padrão e municípios do ITBI."]
    ],
    "Problemas comuns": [
      ["Campos pendentes", "No modo Simples dá para gerar mesmo assim: a lista de pendências mostra o que falta e oferece Gerar mesmo assim. No modo Contrato todos os campos são necessários."],
      ["Botão Gerar desativado", "Falta nome, CPF, data, local, pasta de saída ou modelo. Use Revisar campos pendentes para ir direto a cada um."],
      ["PDF/A indisponível", "Exige o Ghostscript no computador. Sem ele, use PDF simples."],
      ["RTF/DOC/DOCX não converte", "A conversão depende do Microsoft Word instalado."],
      ["Serviço local indisponível", "Feche e abra o Contracto. Se persistir, rode Diagnóstico e reparo em Configurações."]
    ]
  };
  const NUMERADAS = ["Passo a passo", "Documentos do cliente"];

  function abrir() {
    const wrap = document.createElement("div");
    wrap.className = "guia";
    const abas = document.createElement("div");
    abas.className = "guia-abas";
    abas.setAttribute("role", "tablist");
    const painel = document.createElement("div");
    painel.className = "guia-painel";
    painel.setAttribute("role", "tabpanel");
    const botoes = [];
    function mostrar(nome) {
      botoes.forEach(b => b.setAttribute("aria-selected", String(b.dataset.aba === nome)));
      const atalhos = nome === "Dicas e atalhos";
      const novo = document.createElement(atalhos ? "dl" : "div");
      if (atalhos) novo.className = "guia-lista";
      GUIA[nome].forEach(([t, d], i) => {
        if (atalhos) {
          const dt = document.createElement("dt"), dd = document.createElement("dd");
          const k = document.createElement(i < 3 ? "kbd" : "strong"); k.textContent = t; dt.append(k); dd.textContent = d;
          novo.append(dt, dd);
          return;
        }
        const passo = document.createElement("div"); passo.className = "guia-passo";
        const n = document.createElement("span"); n.className = "guia-num"; n.setAttribute("aria-hidden", "true"); n.textContent = NUMERADAS.includes(nome) ? String(i + 1) : "?";
        const corpo = document.createElement("div"), st = document.createElement("strong"), p = document.createElement("p");
        st.textContent = t; p.textContent = d; corpo.append(st, p); passo.append(n, corpo); novo.append(passo);
      });
      painel.replaceChildren(novo);
    }
    Object.keys(GUIA).forEach(nome => {
      const b = document.createElement("button");
      b.type = "button"; b.dataset.aba = nome; b.textContent = nome; b.setAttribute("role", "tab");
      b.addEventListener("click", () => mostrar(nome));
      botoes.push(b); abas.append(b);
    });
    wrap.append(abas, painel);
    mostrar("Passo a passo");
    // A versão vive aqui (a seção Sobre saiu da Config).
    const versao = document.createElement("p");
    versao.className = "hint";
    versao.id = "versao-app";
    versao.textContent = "Consultando versão…";
    wrap.append(versao);
    window.ContractoUI.abrirModal("Ajuda — Guia do Contracto", wrap, [{ texto: "Fazer tour guiado", aoClicar: () => window.ContractoTour?.iniciar() }, { texto: "Entendi, começar!", primario: true }]);
    window.ContractoAPI?.request("GET", "/api/v1/health").then(r => {
      const el = document.getElementById("versao-app");
      if (!el) return;
      const sufixo = "100% local, sem telemetria. Termos de Uso, Privacidade e Avisos de Terceiros acompanham o aplicativo em docs/.";
      el.textContent = r.status === 200 && r.data?.version ? "Contracto v" + r.data.version + " — " + sufixo : sufixo;
    }).catch(() => {});
  }

  window.ContractoAjuda = {abrir};
})();
