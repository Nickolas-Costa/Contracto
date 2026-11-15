## Contracto v5.5.0

**Atualização pelo próprio aplicativo.** A partir desta versão não é mais preciso baixar o instalador pelo navegador.

### Novo
- Em **Configurações → Atualização**, o botão "Verificar atualizações" consulta a lista de versões, mostra a novidade e, se você confirmar, baixa o instalador, confere a assinatura e instala. O aplicativo fecha, atualiza e abre de novo; perfis e configurações são mantidos.
- **Só quando você clica.** Nada é consultado ao abrir o aplicativo e nenhum dado seu é enviado (o GitHub vê apenas o endereço IP, como em qualquer download).
- **Sem alerta do SmartScreen** nas atualizações feitas pelo app, e sem certificado pago: o instalador só roda se a assinatura dele conferir com a chave embutida no aplicativo.
- Com trabalho em andamento a instalação é recusada. Na cópia portátil (ZIP) o botão abre a página de versões.

### Importante
- Quem está na **5.4.0 ou anterior** instala esta versão à mão uma última vez. Daqui em diante, é pelo aplicativo.

### Alterado
- `tauri-plugin-updater` 2.14.1 entra no shell (revisão em `DEPENDENCY_REVIEW.md`). A página continua sem acesso à rede: quem consulta é a parte nativa.
- `PRIVACIDADE.md` e README passam a citar essa única conexão externa.

### Validação
- 376 testes unitários, testes do front em Node, 2 testes Rust e `smoke_webview_ui.py`: OK.
- Verificado no executável de release: abre em 1,5 s com o atualizador carregado e fecha encerrando o servidor; a assinatura do instalador foi feita com a chave cuja parte pública está no aplicativo; `latest.json` aponta para o instalador desta release.
- **Não verificado:** o caminho completo de atualização (exige duas versões publicadas: será testado ao sair a próxima); o botão e os avisos no executável real; instalação sobre a 5.4.0; DPI 100–200%.

### Artefatos
- `Contracto_Setup_v5.5.0.exe` (51.3 MiB), instalador. SHA-256: `29107ABC1FE82C22638BB71F4D44AB85872FE19CB20F9406BB06D91F6A11ACD8`
- `Contracto_v5.5.0.zip` (66.5 MiB), portátil. SHA-256: `4C60753EC17F32F84A9469FE3A40C971ACCC0F0D863E4B2AF0C2FFB5D5B080B8`
- `latest.json`, lido pelo atualizador do aplicativo.
