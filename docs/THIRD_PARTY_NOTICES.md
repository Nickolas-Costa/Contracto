# Avisos de Terceiros — Contracto

Componentes distribuídos com o aplicativo (versões de `requirements-lock.txt`).
Uso interno; revisar licenciamento antes de qualquer distribuição comercial.

| Componente | Versão | Licença | Uso |
|---|---|---|---|
| CustomTkinter | 6.0.0 | CC0-1.0 | Interface gráfica |
| darkdetect | 0.8.0 | BSD-3-Clause | Detecção de tema do sistema |
| lxml | 6.1.1 | BSD-3-Clause | Processamento XML |
| packaging | 26.2 | Apache-2.0 / BSD-2-Clause | Utilitário de versões |
| Pillow | 12.3.0 | MIT-CMU | Imagens e ícones |
| PyMuPDF | removido na 4.5.12 (era 1.28.0, AGPL-3.0) | Pré-visualização — substituído por pypdfium2 |
| pypdfium2 | 5.13.0 | Apache-2.0 | Pré-visualização de mapeamento |
| pypdf | 6.16.1 | BSD-3-Clause | Preenchimento AcroForm |
| pikepdf | 10.11.0 | MPL-2.0 | Validação de metadados PDF/A |
| pywin32 | 312 | PSF | Automação Word / atalhos (Windows) |
| Ghostscript (binário embutido) | 10.07.1 | AGPL | Conversão para PDF/A-2b |
| reportlab (dev/testes) | 5.0.0 | BSD | PDFs sintéticos dos testes |
| PyInstaller (build) | 6.21.0 | GPL-2.0+ com exceção p/ bundles | Geração do executável |

Código-fonte do Ghostscript 10.07.1 (versão embutida):
https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/tag/gs10071
(página oficial: https://www.ghostscript.com/)

Nota: o único componente com copyleft forte no pacote é o Ghostscript,
executado como processo separado. Para distribuição comercial, confirmar
os termos com assessoria jurídica ou avaliar a licença comercial da Artifex.
