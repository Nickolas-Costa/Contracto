# ADR 0004 — Temporários de RTF isolados por trabalho

- **Estado:** aceita
- **Data:** 2026-09-12
- **Contexto:** a Etapa 2 convertia RTF para um PDF em uma pasta temporária global com nome derivado do documento. Dois trabalhos da fila com o mesmo nome podiam escrever, copiar ou excluir o arquivo um do outro. O nome do documento também ficava exposto no caminho temporário global.
- **Decisão:** cada chamada de `executar_etapa2` cria, quando necessário, um diretório temporário exclusivo para seus PDFs intermediários de RTF. O diretório é removido ao sair da operação, inclusive em erro ou cancelamento.
- **Alternativas consideradas:** continuar usando `temp_{nome}` no diretório global (colisão entre trabalhos); gerar apenas um sufixo aleatório no arquivo global (exigiria gerir e limpar cada arquivo separadamente).
- **Consequências:** trabalhos simultâneos não compartilham intermediários; a limpeza pode falhar se outro processo mantiver o PDF aberto e nesse caso é registrada uma advertência. A prova headless cobre agora a geração e a organização reais em modo PDF, além de verificar a separação dos temporários de RTF.
- **Arquivos:** `app/services/stage2_service.py`, `tests/test_headless_backend.py`.
