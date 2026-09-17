# ADR 0017 — Persistência Backend de Preferências e Configurações

Status: aceita e implementada em 17/09/2026.

## Contexto

Anteriormente, o frontend web armazenava o tema (`contracto-tema`), a cor de destaque (`contracto-cor`) e o local de assinatura (`contracto-local-assinatura`) apenas em `localStorage` no navegador WebView. Isso causava uma inconsistência com a versão clássica do Contracto, na qual todas as configurações e preferências do usuário (tema, cor, local padrão, tamanho dos quadros, formato de saída e primeira execução) continuavam persistidas no backend Python em `%APPDATA%/Contracto/contracto_config.json`.

## Decisão

1. **APIs Locais de Configuração (`GET /api/v1/settings` e `POST /api/v1/settings`)**:
   - Disponibilizar endpoints REST locais na API Python para leitura e gravação das configurações usando `config_manager`.

2. **Migração do Frontend**:
   - Atualizar a interface do frontend (`frontend/js/api.js`, `ui.js` e a tela de configurações) para carregar e salvar todas as preferências diretamente na API local Python, removendo a dependência exclusiva de `localStorage`.
   - Garantir sincronização automática entre a WebView e o backend Python em tempo de execução.

3. **Reparo e Diagnóstico Local (`POST /api/v1/system/repair`)**:
   - Adicionar rota para reparo e encerramento de processos travados do Word (`WINWORD.EXE`) e limpeza de arquivos temporários órfãos.

## Consequências e Evidência

As configurações salvas pela WebView passam a ser 100% compatíveis e persistentes na máquina do usuário do mesmo modo que a aplicação Tkinter. Ao atualizar o executável ou abrir a interface web, as preferências de cor, local de assinatura, formato de saída e densidade são preservadas no arquivo de configuração nativo do Contracto.
