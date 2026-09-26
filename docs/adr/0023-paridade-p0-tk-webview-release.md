# ADR 0023 — Paridade P0 Tk → WebView para release

- **Estado:** aceita / implementada
- **Data:** 2026-09-26
- **Contexto:** blocos 0–6 do plano residual concluídos, mas o gate de release exigia paridade P0 (`DESIGN.md §10`): PUT/DELETE de perfis quebravam no middleware, backup/restore só existia no Tk, settings sem tamanho/formato/restaurar, sem ativar-perfil, ajuda/sobre incompletos e validação cliente só CPF/DATA.
- **Decisão:** completar o P0 sem reescrever serviços:
  - `app/api/http.py`: `LocalOnly` aceita `GET/POST/PUT/DELETE`; `PUT` exige JSON como `POST`; `DELETE` sem corpo liberado. Rotas inexistentes seguem 405 via roteador.
  - Novos endpoints: `POST /settings/restore` (padrões), `POST /profiles/active` (valida e define `perfil_ativo`), `POST /system/backup` (retorna só `name`, sem caminho), `POST /system/restore` (`selection_id` kind `backup` `.zip` validado).
  - `app/api/selections.py`: kind `backup` (`.zip`); `app/ports/webview_dialog.py`: `selecionar_backup()`; `app/webview_shell.py`: `select_backup()`.
  - Frontend: `api.js` (`selectBackup/activateProfile/backupSystem/restoreSystem/restoreSettings`); `index.html` (`btn-sobre-topo`, `chk-preservar-dados` persistido, `btn-backup/restaurar-perfis`, `cfg-tamanho`, `cfg-formato`, `btn-cfg-restaurar`); `ui.js` (ajuda modal 4 passos, sobre com versão, boas-vindas via `primeira_execucao`, cfg salva `aparencia/cor/local/tamanho/formato`, restaurar padrões com confirmação); `etapa1.js` (botão Ativar por perfil, backup/restore, validações `CNPJ/CPF_CNPJ/PIS/EMAIL/TELEFONE/ANO`); `form-state.js` (helpers `cnpj/doc/pis/email/telefone/ano`).
  - `VERSION` sincronizado com `app/version.py` (4.5.18).
- **Alternativas:** manter backup só no Tk (descartado: primeira execução WebView ficaria sem recuperação); retornar caminho do ZIP (descartado: vaza path, viola `SPEC_PRE_WEBVIEW.md`).
- **Consequências:** edição/exclusão de perfil via WebView volta a funcionar; backup/restore e ativar-perfil têm paridade; settings persistem no backend + tema/cor em `localStorage`; primeira execução abre ajuda 1 vez.
- **Aceite:** `tests/test_p0_release.py` (PUT/DELETE roundtrip, settings restore, backup sem path, IDs/funções P0 presentes) + suíte existente sem regressão.
- **Testes:** `python -m unittest tests.test_p0_release -v`; `tests.test_local_api`, `test_frontend_base`, `test_release_gate/installer`; gate manual Windows (WebView2 real, Word/GS, DPI, instalador).
