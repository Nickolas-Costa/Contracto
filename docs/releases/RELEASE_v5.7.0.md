## Contracto v5.7.0

Leitura de documentos escaneados e correção na leitura de contratos com um só comprador.

### Novo
- **Documentos escaneados**: páginas que são só imagem passam a ser lidas pelo OCR do próprio Windows (em português). Nada a instalar além do idioma Português (Brasil) do Windows.
- **Ler como imagem (OCR)**: botão em cada documento da Leitura de documentos, para ler de novo o documento inteiro pela imagem.
- Valores lidos da imagem aparecem com "lida da imagem; confira" e vários vêm desmarcados: confira antes de aplicar.

### Corrigido
- Contrato com um só comprador: o "e" de "filho(a) de MÃE e PAI" criava um 2º participante (o pai) e o endereço ia para ele. Agora fica com o comprador.

### Validação
- Testes unitários: OK, incluindo OCR real num PDF de imagem gerado no teste.
- **Não verificado:** PDF escaneado real de cliente, o executável instalado e `smoke_webview_ui.py` no shell Tauri.

### Artefatos
- `Contracto_Setup_v5.7.0.exe` (51.4 MiB), instalador. SHA-256: `6272B09393E81B2FA1EB4231DF8CB6171F5950CA1E41672BE6F90449B3B4F676`
- `Contracto_v5.7.0.zip` (66.6 MiB), portátil. SHA-256: `90F9A46FE84603959CB0C12713D07946DBED14D4419B0D90F9BF18916FD67A8F`
- `latest.json`, lido pelo atualizador do aplicativo.
