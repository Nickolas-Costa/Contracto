# ADR 0011 — Base HTTP local e ponte nativa da WebView

- **Estado:** aceita (base implementada; UI de produção não migrada).
- **Data:** 2026-09-13.
- **Contexto:** preparar a troca de UI com geração e processamento independentes, sem expor caminhos arbitrários nem levar Tk para a API.
- **Decisão:** `LocalServer` reserva e entrega ao Uvicorn o mesmo socket em `127.0.0.1`, porta efêmera. Token de 256 bits em memória, Host/Origin exatos, sem proxy, CORS, docs públicas ou access log. A ponte Python da WebView chama HTTP com `urllib`, mantendo credenciais fora do JavaScript. Aceita somente a página HTML interna. GET do navegador nem sempre inclui Origin; o transporte nativo inclui esse cabeçalho de maneira consistente. A ponte não é autenticação contra outro processo comprometido do mesmo usuário.
- **Arquivos:** `app/server.py`, `app/api/`, `app/webview_shell.py`, `app/ports/webview_dialog.py`, `app/services/form_validation.py` e extensões de `queue_manager.py`.
- **Trabalhos:** UUID completo, fila única com produtor/worker sincronizados e encerramento. Cada operação escreve em pasta temporária exclusiva dentro da saída autorizada; publica uma subpasta `Contracto-<job_id>` apenas no sucesso. Erro/cancelamento limpa a área exclusiva. Processamento copia as entradas, porque o serviço legado remove arquivos intermediários. IDs de seleção expiram e são revogados no encerramento. Saídas já concluídas permanecem.
- **Privacidade:** respostas de falha não incluem inputs, exceções nem caminhos. ContextVar e filtro de logger removem conteúdo de logs dos serviços durante a operação de API; contexto é propagado ao worker COM. Falhas de limpeza são explícitas. Catálogo retorna campos declarativos, sem caminho/mapeamento de templates.
- **Alternativas:** chamar serviços diretamente pelo JS aumenta acoplamento; outra fila duplicaria cancelamento e concorrência; servir arquivos por caminhos HTTP ampliaria a superfície de acesso; TestClient exigiria dependência adicional para testes, evitada por HTTP real via biblioteca padrão.
- **Consequências:** UI atual preservada; nova UI usará `ShellBridge.request`, `select_file`, `select_output`. Os perfis são snapshots da sessão, sem CRUD nesta entrega. Não há site hospedado, login, upload remoto ou troca automática de conversor.
- **Aceite/testes:** `test_local_api.py` cobre HTTP real, segurança, geração, composição, processamento, ausência de capacidades, concorrência, cancelamento e shutdown. `smoke_webview.py` cobre WebView2 real; `smoke_api_engines.py` cobre Word e GS reais. `ContractoBase.exe --self-test` verifica o bundle. Detalhes e pendências em `BASE_UI_STATUS.md`.

## Gate de dependências (ADR 0007)

| Questão | FastAPI / Pydantic / Uvicorn | pywebview / WebView2 |
| --- | --- | --- |
| 1. Capacidade concreta | HTTP tipado, validação estrita e servidor ASGI; sem eles não há contrato local | Janela HTML e diálogos nativos para a UI nova |
| 2. Pode ser código próprio/nativo? | `http.server` exigiria implementar validação/ciclo de vida; não compensa | Navegador externo não oferece integração desktop equivalente |
| 3. Alternativas | Chamada JS direta acopla cliente e serviços; não escolhida | Tauri mantém-se futuro; nesta fase reaproveitamos Python |
| 4. Requisitos | Socket local, threads e temporários; sem admin ou rede externa | WebView2 no Windows, runtime .NET/pythonnet transitivo, sessão gráfica; não faz download silencioso |
| 5. Ambientes | API pode executar em Linux; Word continua Windows; apenas loopback nesta fase | Smoke foi validado em Windows; não homologado em Linux ou servidor sem display |
| 6. Testes reais | `test_local_api.py`, `smoke_api_engines.py` | `smoke_webview.py`, executável de diagnóstico |
| 7. Remoção/substituição | DTOs/HTTP em `api/`, serviços continuam sem FastAPI | Substituir shell/port mantendo API e serviços |

Versões já estavam instaladas e no lock. Pydantic 2.13.5 agora é explicitamente dependência direta, pois o código importa seus modelos; não houve atualização de versão. Testes HTTP usam `urllib`, `unittest`, sockets e threads da biblioteca padrão, sem adicionar httpx/pytest. O script de diagnóstico usa o PyInstaller já previsto em requirements-dev.

Referências técnicas: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/), [middleware ASGI](https://fastapi.tiangolo.com/advanced/middleware/) e [API pywebview](https://pywebview.flowrl.com/api/).
