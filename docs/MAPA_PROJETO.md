# Mapa do projeto — Contracto

Este documento funciona como guia rápido da arquitetura e da responsabilidade de cada área do repositório. O objetivo é manter a leitura fácil para quem entra no projeto e também para quem precisa localizar um ponto específico sem depender de arquivos espalhados.

## Visão geral

O projeto combina:

- uma aplicação desktop Windows em Python;
- uma interface principal baseada em WebView2/HTML/CSS/JS;
- uma API local em loopback para comunicação interna;
- serviços puros de geração, conversão e organização de arquivos;
- utilitários de persistência, validação, arquivos e diagnósticos;
- uma camada legada em Tkinter mantida como referência e fallback.

Em termos práticos, o fluxo geral é:

1. a interface coleta dados e dispara ações;
2. a API local recebe a requisição em localhost;
3. os serviços executam a lógica de negócio;
4. o sistema gera/organiza arquivos no disco e entrega o resultado para a UI.

---

## Estrutura principal

```text
Contracto/
├── app/                         # código principal da aplicação
│   ├── api/                    # endpoints HTTP locais e camada de integração
│   ├── assets/                 # recursos embutidos do executável
│   ├── models/                 # entidades e estruturas de dados
│   ├── ports/                  # abstrações de sistemas externos (diálogos, arquivos, bins)
│   ├── services/               # regras de negócio e processamento de documentos
│   ├── ui/                     # interface legada Tk / telas antigas (fallback)
│   ├── utils/                  # utilitários, arquivos, validações e persistência
│   ├── __init__.py             # pacote app
│   ├── main.py                 # entrypoint principal da aplicação
│   ├── server.py               # servidor loopback do backend local
│   ├── version.py              # versão centralizada do sistema
│   └── webview_shell.py        # bootstrap do WebView e ponte com a API local
├── frontend/                   # interface web atual (HTML/CSS/JS)
│   ├── assets/                 # imagens, fontes e recursos front-end
│   ├── css/                    # estilos e tokens do design system
│   ├── js/                     # lógicas da interface web
│   ├── index.html              # tela principal da interface
│   ├── lab.html                # laboratório visual isolado para testes de UI
│   └── ...
├── docs/                       # documentação técnica, arquitetura e decisões
├── tests/                      # suíte de testes (unitários, smoke, regressão e UI)
├── scripts/                    # automação de build, setup e utilitários de distribuição
├── packaging/                  # scripts de empacotamento e instaladores
├── app/Contracto_*.spec        # especificações PyInstaller
├── README.md                   # visão geral do projeto
├── CHANGELOG.md                # histórico de versões
├── requirements.txt            # dependências da aplicação
├── requirements-dev.txt        # ferramentas e dependências para desenvolvimento
├── VERSION                     # espelho da versão
├── build_exe.bat               # build do executável Windows
├── LICENSE                     # licença do projeto
└── .venv/                      # ambiente virtual local (quando presente)
```

---

## Onde fica cada coisa

### app/

Pasta principal da aplicação. Aqui vive o runtime do software e a lógica do núcleo productivo.

- `main.py`
  - ponto de entrada do processo;
  - decide se abre a interface WebView ou a legada Tk;
  - bloqueia segunda instância e registra erros globais.

- `server.py`
  - inicializa o backend local em loopback;
  - gera um token temporário em memória para autenticação simples;
  - mantém o processo HTTP exclusivo e isolado da rede.

- `webview_shell.py`
  - bootstrap do shell WebView;
  - monta a janela, conecta com a API local e valida a origem autorizada;
  - atua como ponte entre JS e backend nativo.

- `api/`
  - expõe os endpoints da aplicação pela interface local;
  - centraliza requisições em HTTP, jobs e manipulação de arquivos.

- `services/`
  - camada de negócio sem dependência de UI;
  - contém geração de documentos, conversão PDF/A, organização de pastas e processamento principal.

- `ports/`
  - abstrai detalhes do ambiente: diálogos nativos, escolhas de arquivo, binários e integrações de plataforma.

- `ui/`
  - interface antiga do projeto (CustomTkinter);
  - ainda útil como referência, manutenção de compatibilidade e fallback técnico.

- `utils/`
  - funções de apoio: validação, caminhos, logging, configuração, backup e operações de arquivo.

- `models/`
  - entidades e estruturas de dados, normalmente representando participantes, perfis e dados de processo.

- `assets/`
  - recursos embutidos da aplicação, como templates, ícones e extras que precisam viajar junto ao executável.

### frontend/

Códigos da interface atual, organizada em web assets e JavaScript. Esta é a face principal da migração para WebView.

- `index.html`
  - página principal da aplicação web.

- `css/`
  - estilos, tokens, layout e temas visuais.

- `js/`
  - scripts de interação, fluxo de telas e comunicação com o shell nativo/API local.

- `lab.html`
  - laboratório visual isolado para explorar layout, contraste e comportamento sem mexer na interface principal.

### docs/

Documentação arquitetural, decisão técnica e histórico de evolução. Aqui fica a memória do projeto.

- `ARCHITECTURE.md`: visão geral da arquitetura.
- `BASE_UI_STATUS.md`: estado da migração da UI e pendências.
- `CONTINUIDADE_CODEX_WEB.md`: contexto de continuidade e plano de execução.
- `PLANO_MIGRACAO_WEBVIEW_RESIDUAL.md`: plano residual da migração WebView.
- `DESIGN_SYSTEM.md` e `DESIGN.md`: identidade visual e design system.
- `adr/`: decisões registradas em formato de ADR.

### tests/

Suíte de validação do projeto.

- testes de utilitários e regras de negócio;
- smoke tests para GUI, WebView e motores reais;
- verificações de regressão no frontend e no backend.

### scripts/

Ferramentas de automação de build, empacotamento e setup de requisitos externos.

### packaging/

Arquivos de empacotamento e distribuição, principalmente para Windows e instalação final.

---

## Fluxo de execução

O caminho mais comum no runtime é:

```text
app/main.py
  -> escolher_interface()
  -> iniciar_web() ou iniciar_tk()
  -> webview_shell.py ou ui/main_window.py
  -> LocalServer / API local
  -> services/
  -> geração/validação/conversão de PDFs e organização de arquivos
```

Isso ajuda a entender por onde começar quando você precisa localizar uma funcionalidade ou ajustar um comportamento.

---

## Boas práticas de leitura

- Comece por `app/main.py` para ver o ponto de entrada.
- Vá para `app/server.py` para entender a base local HTTP.
- Consulte `app/webview_shell.py` para entender a ponte com a interface web.
- Use `app/services/` para entender a regra de negócio.
- Use `app/utils/` para detalhes de caminho, validação e persistência.
- Consulte `docs/` para arquitetura, decisões e histórico antes de mudar a estrutura do projeto.

Esse mapa é intencionalmente simples: ele não tenta resumir cada função, mas orienta o caminho mais rápido para encontrar o pedaço correto do sistema.
