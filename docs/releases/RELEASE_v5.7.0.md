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
- `Contracto_Setup_v5.7.0.exe`, instalador.
- `Contracto_v5.7.0.zip`, portátil.
- `latest.json`, lido pelo atualizador do aplicativo.
