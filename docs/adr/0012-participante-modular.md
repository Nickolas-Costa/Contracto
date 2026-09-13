# ADR 0012 — Participante modular dirigido pelo perfil

- **Estado:** aceita
- **Data:** 2026-09-13
- **Contexto:** `Participant` duplicava endereço/data/local entre atributos e dicionário, com ramificações por nome em `obter/definir_campo`, e `copiar_dados_compartilhados` fixava quais campos eram compartilhados. Qualquer mudança de esquema por perfil exigia tocar modelo, resolvedor e UI.
- **Decisão:** fonte única em `campos_dinamicos`; endereço/data/local viram propriedades de conveniência (mesma API de leitura/escrita); `obter/definir_campo` genéricos com mapa de aliases; `copiar_dados_compartilhados(principal, campos)` copia só `escopo=="global"` quando recebe os campos do perfil (sem `campos`, legado preservado); `resolver_variavel` lê pelo modelo, mantendo as chaves. Construtor absorve chaves legadas para compatibilidade (API, testes, UI).
- **Alternativas consideradas:** subclasses por perfil (explosão de classes para variação de dados); dicionário puro sem modelo (perde identidade nome/CPF e quebra chamadores); manter espelhos (estado duplicado, causa original).
- **Consequências:** novo campo de perfil funciona sem alterar modelo; remover um campo exige só tirar do perfil. Risco: igualdade dataclass agora sobre 3 campos — equivalente na prática pelos espelhos.
- **Arquivos:** `app/models/participant.py`, `app/services/generator_service.py`, `app/ui/mw_etapa1.py`, `tests/test_participant_modular.py`.
- **Revisão:** compatível com ADRs 0001 (mixins intactos) e 0002 (imports inalterados); `DECISIONS.md §9` (reuso/docstring).
- **Aceite:** suíte verde; `Participant(endereco=...)` e testes legados passam sem edição; herança global só copia `escopo=="global"`.
- **Testes:** `tests/test_participant_modular.py` (fonte única, herança por perfil, resolvedor estável) + suíte completa.
