"""
Serviço responsável exclusivamente pela leitura e preenchimento de PDFs
com campos de formulário (AcroForm), utilizando pypdf.

Este módulo não processa regras de participantes ou documentos. Ele recebe
um PDF modelo e um dicionário {nome_do_campo: valor} e devolve um PDF preenchido.
As regras declarativas ficam na configuração do perfil e são avaliadas pelo
motor genérico de mapeamento.

Isso mantém baixo acoplamento: se no futuro o formato dos PDFs mudar, ou
se novos tipos de documentos forem adicionados, apenas o mapeamento precisa ser atualizado.
"""

from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError
from pypdf.generic import DictionaryObject, NameObject


class PdfServiceError(Exception):
    """Erro amigável relacionado à leitura, preenchimento ou escrita de um PDF."""


_detalhes_cache: dict[tuple[str, int, int], dict[str, dict[str, object]]] = {}


def _copiar_detalhes(detalhes: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        nome: {"tipo": item.get("tipo", ""), "estados": list(item.get("estados", []) or [])}
        for nome, item in detalhes.items()
    }


def obter_campos_do_formulario(caminho_pdf: Path) -> set[str]:
    """Retorna os nomes de todos os campos de formulário (AcroForm) de um PDF.

    Útil para depuração: caso os nomes dos campos no PDF real do modelo
    sejam diferentes dos configurados em `generator_service.py`, este
    conjunto ajuda a descobrir os nomes corretos.
    """
    reader = _abrir_pdf(caminho_pdf)
    campos = reader.get_fields()
    return set(campos.keys()) if campos else set()


def obter_detalhes_campos(caminho_pdf: Path) -> dict[str, dict[str, object]]:
    """Retorna tipo e estados de exportação para configurar mapeamentos pela UI."""
    try:
        estado = caminho_pdf.stat()
        chave_cache = (str(caminho_pdf.resolve()), estado.st_mtime_ns, estado.st_size)
    except OSError:
        chave_cache = (str(caminho_pdf), 0, 0)
    if chave_cache in _detalhes_cache:
        return _copiar_detalhes(_detalhes_cache[chave_cache])

    reader = _abrir_pdf(caminho_pdf)
    campos = reader.get_fields() or {}
    detalhes = {
        nome: {
            "tipo": str(campo.get("/FT", "")),
            "estados": [str(estado) for estado in (campo.get("/_States_") or [])],
        }
        for nome, campo in campos.items()
    }
    # Alguns PDFs guardam as aparências somente nos widgets filhos.
    for pagina in reader.pages:
        for ref in pagina.get("/Annots") or []:
            widget = ref.get_object()
            parent_ref = widget.get("/Parent")
            parent = parent_ref.get_object() if parent_ref else None
            nome = (parent.get("/T") if parent else widget.get("/T"))
            tipo = (parent.get("/FT") if parent else widget.get("/FT"))
            if not nome or str(tipo) != "/Btn":
                continue
            estados = list(((widget.get("/AP") or {}).get("/N") or {}).keys())
            if estados:
                detalhes.setdefault(str(nome), {"tipo": "/Btn", "estados": []})
                detalhes[str(nome)]["estados"] = [str(estado) for estado in estados]
    if len(_detalhes_cache) >= 24:
        _detalhes_cache.pop(next(iter(_detalhes_cache)))
    _detalhes_cache[chave_cache] = _copiar_detalhes(detalhes)
    return detalhes


def carregar_template_reader(caminho_pdf: Path) -> PdfReader:
    """Abre e retorna uma instância do PdfReader para reutilização em preenchimento múltiplo."""
    return _abrir_pdf(caminho_pdf)


def preencher_formulario(
    caminho_template: Path,
    valores: dict[str, str],
    caminho_saida: Path,
    reader: Optional[PdfReader] = None,
) -> list[str]:
    """Preenche os campos de formulário (AcroForm) de um PDF modelo e salva o
    resultado em `caminho_saida`.

    Args:
        caminho_template: caminho do PDF modelo (com campos de formulário).
        valores: dicionário {nome_do_campo_no_pdf: valor_a_preencher}.
        caminho_saida: caminho completo do PDF final a ser gerado.
        reader: instância opcional do PdfReader para evitar re-leitura do arquivo.

    Returns:
        Lista com os nomes de campos em `valores` que não foram encontrados
        no PDF modelo.

    Raises:
        PdfServiceError: se o arquivo não puder ser lido/escrito ou campos estiverem inválidos.
    """
    if reader is None:
        reader = _abrir_pdf(caminho_template)

    campos_existentes = reader.get_fields() or {}
    campos_ausentes = [nome for nome in valores if nome not in campos_existentes]

    if valores and campos_ausentes and len(campos_ausentes) == len(valores):
        raise PdfServiceError(
            f"Nenhum dos campos esperados foi encontrado no PDF "
            f"'{caminho_template.name}'. Verifique se este é o modelo "
            f"correto ou ajuste o mapeamento nas configurações do perfil "
            f"(campos disponíveis no PDF: {sorted(campos_existentes.keys())})."
        )

    try:
        writer = PdfWriter(clone_from=reader)

        acroform_ref = writer.root_object.get("/AcroForm")
        if acroform_ref:
            acroform = acroform_ref.get_object()
            recursos = acroform.get("/DR")
            if not isinstance(recursos, DictionaryObject):
                recursos = DictionaryObject()
                acroform[NameObject("/DR")] = recursos
            fontes = recursos.get("/Font")
            if not isinstance(fontes, DictionaryObject):
                fontes = DictionaryObject()
                recursos[NameObject("/Font")] = fontes
            if "/Helv" not in fontes:
                fontes[NameObject("/Helv")] = DictionaryObject({
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                    NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
                })

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
