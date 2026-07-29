"""
Serviço responsável exclusivamente pela leitura e preenchimento de PDFs
com campos de formulário (AcroForm), utilizando pypdf.

Este módulo é intencionalmente "burro" em relação a regras de negócio: ele
não sabe o que é um "participante", uma "Declaração PPE" ou o que é a
CAIXA. Ele apenas recebe um PDF modelo e um dicionário
{nome_do_campo: valor} e devolve um PDF preenchido. Toda regra de negócio
(quais campos preencher, com quais dados, para quais documentos) vive em
`generator_service.py`.

Isso mantém baixo acoplamento: se no futuro o formato dos PDFs mudar, ou
se quisermos preencher outros tipos de documento, apenas este arquivo
(ou o mapeamento em generator_service.py) precisa ser tocado.
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class PdfServiceError(Exception):
    """Erro amigável relacionado à leitura, preenchimento ou escrita de um PDF."""


def obter_campos_do_formulario(caminho_pdf: Path) -> set[str]:
    """Retorna os nomes de todos os campos de formulário (AcroForm) de um PDF.

    Útil para depuração: caso os nomes dos campos no PDF real fornecido pela
    CAIXA sejam diferentes dos configurados em `generator_service.py`, este
    conjunto ajuda a descobrir os nomes corretos.
    """
    reader = _abrir_pdf(caminho_pdf)
    campos = reader.get_fields()
    return set(campos.keys()) if campos else set()


def preencher_formulario(
    caminho_template: Path,
    valores: dict[str, str],
    caminho_saida: Path,
) -> list[str]:
    """Preenche os campos de formulário (AcroForm) de um PDF modelo e salva o
    resultado em `caminho_saida`.

    Args:
        caminho_template: caminho do PDF modelo (com campos de formulário).
        valores: dicionário {nome_do_campo_no_pdf: valor_a_preencher}.
        caminho_saida: caminho completo do PDF final a ser gerado.

    Returns:
        Lista com os nomes de campos em `valores` que não foram encontrados
        no PDF modelo. Uma lista não vazia não impede a geração do arquivo,
        mas serve de aviso para a camada de negócio/interface.

    Raises:
        PdfServiceError: se o arquivo não puder ser aberto/lido/escrito, ou
            se NENHUM dos campos esperados existir no PDF modelo (nesse
            caso, é muito provável que o modelo selecionado esteja errado
            ou que os nomes dos campos precisem ser ajustados).
    """
    reader = _abrir_pdf(caminho_template)

    campos_existentes = reader.get_fields() or {}
    campos_ausentes = [nome for nome in valores if nome not in campos_existentes]

    if valores and campos_ausentes and len(campos_ausentes) == len(valores):
        raise PdfServiceError(
            f"Nenhum dos campos esperados foi encontrado no PDF "
            f"'{caminho_template.name}'. Verifique se este é o modelo "
            f"correto ou ajuste os nomes dos campos em generator_service.py "
            f"(campos disponíveis no PDF: {sorted(campos_existentes.keys())})."
        )

    try:
        writer = PdfWriter(clone_from=reader)

        for pagina in writer.pages:
            writer.update_page_form_field_values(pagina, valores, auto_regenerate=False)

        writer.set_need_appearances_writer(True)

        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_saida, "wb") as arquivo_saida:
            writer.write(arquivo_saida)
    except (OSError, PdfReadError) as exc:
        raise PdfServiceError(
            f"Não foi possível gerar o arquivo '{caminho_saida.name}': {exc}"
        ) from exc

    return campos_ausentes


def _abrir_pdf(caminho: Path) -> PdfReader:
    """Abre um PDF e traduz erros técnicos em PdfServiceError (mensagem amigável)."""
    if not caminho.exists():
        raise PdfServiceError(f"Arquivo não encontrado: '{caminho}'.")
    try:
        return PdfReader(str(caminho))
    except (PdfReadError, OSError) as exc:
        raise PdfServiceError(
            f"Não foi possível abrir o PDF '{caminho.name}': {exc}"
        ) from exc
