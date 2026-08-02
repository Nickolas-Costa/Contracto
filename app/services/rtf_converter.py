"""
Serviço de conversão de arquivos RTF para PDF utilizando o Microsoft Word via COM.

Algumas instituições financeiras costumam emitir documentos contratuais no formato .rtf.
Esta funcionalidade permite anexá-los diretamente na Etapa 2.
"""

from pathlib import Path


class RtfConversionError(Exception):
    """Erro ao tentar converter um arquivo RTF para PDF."""


def converter_rtf_para_pdf(caminho_rtf: Path, caminho_pdf: Path) -> Path:
    """
    Usa a API COM do Windows (win32com) para abrir o Word em background,
    carregar o RTF e salvar como PDF.

    Args:
        caminho_rtf: Caminho do arquivo RTF original.
        caminho_pdf: Caminho de saída do PDF temporário gerado.

    Returns:
        O próprio caminho_pdf após a criação.

    Raises:
        RtfConversionError: Caso ocorra erro na conversão ou Word não esteja instalado.
    """
    try:
        import win32com.client
    except ImportError:
        raise RtfConversionError(
            "Biblioteca pywin32 não está instalada. "
            "A conversão de RTF para PDF não é suportada neste ambiente."
        )

    # Word exige caminhos absolutos como strings para COM API
    abs_in = str(caminho_rtf.resolve())
    abs_out = str(caminho_pdf.resolve())

    # Formato 17 = wdFormatPDF
    wdFormatPDF = 17

    word = None
    doc = None
    try:
        # Tenta conectar ao Word já aberto, senão abre uma instância oculta
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(abs_in)
        doc.SaveAs(abs_out, FileFormat=wdFormatPDF)

        if not caminho_pdf.exists():
            raise FileNotFoundError("O Word reportou sucesso, mas o arquivo PDF não foi encontrado.")

        return caminho_pdf

    except Exception as exc:
        raise RtfConversionError(f"Falha na conversão via MS Word: {exc}") from exc
    finally:
        if doc is not None:
            # Fechar sem salvar alterações no RTF original
            doc.Close(SaveChanges=0)
        if word is not None:
            word.Quit()
