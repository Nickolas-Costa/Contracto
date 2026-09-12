# ADR 0003 — Conversão RTF pelo Microsoft Word

- **Estado:** aceita
- **Data:** 2026-09-12
- **Contexto:** a direção atual do produto é oferecer conversão RTF no Windows com Microsoft Word. O serviço, porém, ainda chamava o LibreOffice silenciosamente quando o Word faltava ou falhava, contrariando a decisão de produto e a documentação de arquitetura. A verificação de capacidade confundia a presença da biblioteca COM com a instalação do Word e podia apontar o executável do LibreOffice como caminho do Word.
- **Decisão:** usar apenas Microsoft Word via COM para converter RTF. Quando o Word não estiver disponível, a operação informa essa dependência; quando travar, mantém o aviso com prazo e encerra somente a instância filha criada pelo aplicativo. O port de binários consulta o registro COM do Word sem abrir o programa e não associa o caminho de outro produto ao status do Word.
- **Alternativas consideradas:** fallback silencioso para LibreOffice (resultado e suporte divergiriam da decisão de produto); oferecer seleção de motor agora (exigiria fluxo de UI, empacotamento e testes próprios antes da WebView).
- **Consequências:** máquinas sem Word não convertem RTF nesta fase; a conversão de PDF e as demais funções seguem independentes. A checagem do registro COM indica registro disponível, mas a conversão real ainda pode falhar e precisa manter mensagens claras. A futura adoção de LibreOffice requer uma nova decisão e testes de equivalência dos documentos.
- **Arquivos:** `app/services/rtf_converter.py`, `app/ports/binaries.py`, `tests/test_word_travado.py`, `tests/test_headless_backend.py`.
