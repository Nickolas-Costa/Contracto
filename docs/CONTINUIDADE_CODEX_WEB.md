# Continuidade remota — Contracto

Preparado em 12/09/2026. Repositório: `Nickolas-Costa/Contracto`; base: `main`.

## Estado entregue e validação

A base de código validada é `30163f7` (v4.5.15). Após `git fetch --all --prune`, todas as 35 branches locais, incluindo main, e todas as branches remotas estavam contidas nela. Não havia commits exclusivos fora de main, alterações de trabalho, stashes nem outros worktrees. Foram conferidos 148 commits alcançáveis em main; a execução dos testes foi sobre o resultado integrado, não sobre cada revisão histórica isoladamente.

| Verificação em Windows / Python 3.14.6 | Resultado |
| --- | --- |
| `python -m unittest discover -s tests -v` | 269 testes, 53,665 segundos, OK, sem skips |
| `python -m unittest discover -s tests -p test_headless_backend.py -v` em processo separado | 4 testes, OK |
| `python tests/smoke_test_gui.py` após atualização | Janela real, adição/remoção, dois participantes, fila e quatro PDFs com nome/CPF preenchidos: OK |
| `python -m pip check` | Nenhuma dependência quebrada |
| `python -m pip_audit -r requirements.txt --no-deps --disable-pip` | Nenhuma vulnerabilidade conhecida nas dependências diretas consultadas; não é auditoria das transitivas |
| Ghostscript real 10.07.1 | PDF sintético convertido; uma página e metadados PDF/A conferidos pelo validador interno |
| Microsoft Word COM real | RTF sintético convertido; uma página e texto do PDF conferidos |

O smoke antigo usava o perfil real do usuário e pressupunha que apenas o titular teria endereço. Foi substituído por uma massa sintética em APPDATA/LOCALAPPDATA temporários, compatível com campos declarativos. Exercita os botões de avançar/finalizar, espera a fila e lê os campos dos PDFs. Usa PDF comum para permitir execução sem Word ou Ghostscript.

Limites: não foi feita homologação manual de todas as telas/resoluções/DPI, novo executável/instalador ou certificação PDF/A por ferramenta externa. A suíte passou, mas emitiu ResourceWarnings de imagens de ícones abertas; investigar fechamento dos arquivos sem invalidar imagens em uso. As mensagens de Word/Ghostscript ausentes durante a suíte correspondem a cenários negativos simulados e passaram.

## Disponibilidade dos arquivos

Código, modelos oficiais, recursos e documentos versionados estão na main. `.venv`, builds, executáveis gerados e auditorias locais ignoradas não são necessários como fonte para o trabalho remoto.

`Protótipo-webview-do-sistema.zip` permanece fora do Git conforme `.gitignore` e ADR 0010. Contém HTML/CSS/JS, catálogo, imagens/PDFs e documentos de design; o Codex remoto não terá esse arquivo. A etapa de API abaixo independe dele. Para a implementação visual fiel, fornecer essa referência em uma tarefa futura; não afirmar que o protótipo foi consultado quando estiver ausente. Usar os documentos de design versionados para avançar nas especificações.

## Preparação do ambiente remoto

Selecionar este repositório e a branch `main` atualizada. O ambiente cloud faz checkout da branch/commit selecionado e executa o setup configurado. Configurar dependências no setup e informar eventuais variáveis nas configurações do ambiente, pois um `export` no setup não persiste automaticamente na fase do agente. Fonte: [OpenAI — Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment).

Roteiro proposto para container Linux; **não executado neste notebook Windows**:

```bash
# Se faltarem Tk/display virtual no container (requer permissão de instalação):
sudo apt-get update
sudo apt-get install -y python3-tk python3-venv xvfb xauth ghostscript
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
xvfb-run -a .venv/bin/python -m unittest discover -s tests -v
xvfb-run -a .venv/bin/python tests/smoke_test_gui.py
```

Selecionar uma versão de Python compatível com os pins, preferindo a 3.14 validada aqui quando disponível. Verificar `import tkinter` com esse interpretador: o pacote do sistema precisa corresponder à versão escolhida. Não remover testes para esconder erro de setup. `requirements-lock.txt` é uma fotografia do ambiente Windows, inclui pacotes específicos; não instalar esse lock cegamente em Linux. `requirements.txt` já condiciona pywin32 ao Windows. Registrar qualquer impossibilidade de instalar versões fixadas, sem atualização arbitrária de dependências.

Teste mínimo sem janela:

```bash
.venv/bin/python -m unittest discover -s tests -p test_headless_backend.py -v
```

Word COM, mutex Windows, WebView2, instalador e DPI precisam de validação em Windows. Sucesso com mocks no Linux não prova execução dessas integrações. Classificar skips por plataforma e falhas de infraestrutura explicitamente.

## Plano em entregas pequenas

1. **Baseline remoto reproduzível.** Ler `ARCHITECTURE.md`, `SPEC_PRE_WEBVIEW.md`, `DEPENDENCY_REVIEW.md`, `DECISIONS.md` e ADRs 0001–0010. Executar a suíte e smoke conforme ambiente; corrigir somente incompatibilidades demonstradas. Registrar comandos, resultados e limites. Investigar os ResourceWarnings de ícones como correção isolada.
2. **Contrato e servidor loopback.** Implementar `app/server.py` e `app/api/` sem importar UI/Tk. Modelos tipados, `/api/v1/health`, `/capabilities`, ciclo de vida, porta livre em `127.0.0.1`, token efêmero em memória e origem autorizada. Testar credenciais/origens inválidas, validação de entrada e encerramento. Capabilities consulta Word/GS sem iniciar Word. Seguir integralmente a especificação existente.
3. **Fachada de trabalhos.** Adaptar QueueManager e serviços para composição, geração e processamento opcional. IDs não previsíveis, progresso, erros estruturados, cancelamento e limpeza dos temporários por trabalho. Arquivos devem ser autorizados pelo port/identificadores de seleção, sem caminhos arbitrários recebidos do frontend. Testar geração simples sem etapa 2, processamento separado, trabalhos concorrentes e cancelamento.
4. **Privacidade e ausência de capacidades.** Testes HTTP para Word/GS ausentes, PDF simples funcionando sem ambos, rejeição de caminhos/corpos/métodos inválidos e logs sem tokens/dados pessoais/conteúdo/caminhos absolutos. Qualquer nova dependência, inclusive de testes, responde às sete perguntas do gate de dependências.
5. **Shell WebView após API aprovada.** Port de diálogos, bootstrap e encerramento do servidor. Aplicar `DESIGN.md`, `GUIA_OPEN_DESIGN.md`, ADRs 0009/0010 e referência visual quando disponível. Stepper navegável, toolbar em 1024px, foco/teclado, modais limitados à viewport e redução de movimento. Preservar lógica de documentos nos serviços; não portar o monólito para JavaScript.
6. **Validação Windows e distribuição.** Testar WebView2, Word real, Ghostscript real, encerramento/cancelamento, 100/125/150/200% DPI e instalador Inno Setup (ADR 0008). Gerar release apenas depois desse gate. Documentar tudo que permaneceu pendente por ausência de máquina Windows.

Para cada entrega: branch própria a partir de main atualizada, diff focado, testes relevantes e PR com problema, comportamento final, evidência e limitações. Não misturar API empresarial hospedada, login, multitenancy ou armazenamento em nuvem nesta fase (ADR 0006).

## Texto pronto para colar no Codex web

> Trabalhe no repositório Nickolas-Costa/Contracto, a partir da main mais recente. Leia AGENTS.md e docs/CONTINUIDADE_CODEX_WEB.md, depois as especificações e ADRs referenciados. Primeiro reproduza a baseline e registre os testes disponíveis no ambiente cloud, distinguindo dependências de Windows e falhas de setup. Em seguida execute as entregas 1 e 2 do plano: baseline e contrato/servidor FastAPI loopback, sem começar a tela WebView. Preserve o núcleo Python, a UI atual e o comportamento dos documentos. Siga docs/SPEC_PRE_WEBVIEW.md e o gate docs/DEPENDENCY_REVIEW.md. Faça testes reais de HTTP para os endpoints implementados e as rejeições previstas, mantenha a suíte anterior passando e entregue uma branch com PR revisável. Não trate mocks como homologação de Word/WebView2 e não exponha o servidor à internet. Ao final informe arquivos alterados, testes, limitações e a próxima entrega do plano. O ZIP do protótipo é local e não está disponível nesta tarefa; ele não bloqueia o trabalho de API.
