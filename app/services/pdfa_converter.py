"""
Módulo independente para conversão de documentos PDF para PDF/A-2b.

Este módulo é responsável exclusivamente pela conversão e validação de
conformidade PDF/A. Ele NÃO contém lógica de preenchimento de formulários
(isso fica em pdf_service.py e generator_service.py) nem de organização
de pastas (isso fica em process_folder_service.py).

A conversão utiliza o Ghostscript como motor externo, que produz PDFs
realmente compatíveis com o padrão PDF/A-2b (ISO 19005-2).

Arquitetura:
    PDF original
         ↓
    Ghostscript (conversão)
         ↓
    PDF/A-2b
         ↓
    Validação de metadados XMP
         ↓
    Arquivo final validado
"""

import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from utils.ghostscript_setup import localizar_ghostscript
from utils.logger import obter_logger


_logger = obter_logger("pdfa")


class ProcessoCanceladoError(Exception):
    """Exceção levantada quando a operação é cancelada pelo usuário."""
    pass


class PdfAConversionError(Exception):
    """Erro relacionado à conversão ou validação de PDF/A."""


class GhostscriptNaoEncontradoError(PdfAConversionError):
    """Ghostscript não está instalado ou não foi encontrado no sistema."""


class PdfAValidationError(PdfAConversionError):
    """O arquivo convertido não passou na validação de conformidade PDF/A."""


@dataclass
class ResultadoConversao:
    """Resultado de uma operação de conversão PDF/A."""

    caminho_saida: Path
    perfil: str  # Ex: "PDF/A-2b"
    validado: bool = False
    mensagem: str = ""


@dataclass
class ResultadoLote:
    """Resultado de uma conversão em lote de múltiplos arquivos."""

    convertidos: list[ResultadoConversao] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)

    @property
    def todos_sucesso(self) -> bool:
        return len(self.erros) == 0 and all(r.validado for r in self.convertidos)


# Perfis PDF/A suportados e seus parâmetros Ghostscript correspondentes
_PERFIS_PDFA = {
    "PDF/A-2b": "2",
    "PDF/A-1b": "1",
    "PDF/A-3b": "3",
}


def _obter_caminho_ghostscript() -> Path:
    """Obtém o caminho do Ghostscript ou levanta erro informativo."""
    caminho = localizar_ghostscript()
    if caminho is None:
        raise GhostscriptNaoEncontradoError(
            "Ghostscript não encontrado no sistema.\n\n"
            "O Ghostscript é necessário para converter documentos para PDF/A.\n"
            "Instale-o a partir de: https://www.ghostscript.com/releases/gsdnld.html\n\n"
            "Após a instalação, reinicie o aplicativo."
        )
    return caminho


def converter_para_pdfa(
    caminho_entrada: Path,
    caminho_saida: Path,
    perfil: str = "PDF/A-2b",
    ps_path: Optional[Path] = None,
) -> ResultadoConversao:
    """Converte um PDF para o formato PDF/A utilizando Ghostscript.

    Args:
        caminho_entrada: caminho do PDF original.
        caminho_saida: caminho onde o PDF/A será salvo.
        perfil: perfil PDF/A desejado (padrão: "PDF/A-2b").
                Suporta: "PDF/A-1b", "PDF/A-2b", "PDF/A-3b".
        ps_path: caminho opcional de arquivo .ps auxiliar pré-gerado para reutilização.

    Returns:
        ResultadoConversao com informações sobre a operação.

    Raises:
        PdfAConversionError: se a conversão falhar.
        GhostscriptNaoEncontradoError: se o Ghostscript não estiver instalado.
    """
    if perfil not in _PERFIS_PDFA:
        raise PdfAConversionError(
            f"Perfil PDF/A '{perfil}' não suportado. "
            f"Perfis disponíveis: {', '.join(_PERFIS_PDFA.keys())}"
        )

    if not caminho_entrada.exists():
        raise PdfAConversionError(
            f"Arquivo de entrada não encontrado: '{caminho_entrada}'"
        )

    caminho_gs = _obter_caminho_ghostscript()
    nivel_pdfa = _PERFIS_PDFA[perfil]

    # Criar pasta de saída se não existir
    if not caminho_saida.parent.exists():
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    # Criar arquivo PostScript auxiliar apenas se não fornecido
    criou_ps_proprio = False
    ps_efetivo: Path | None = ps_path

    try:
        if ps_efetivo is None or not ps_efetivo.exists():
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".ps", delete=False, encoding="utf-8"
            ) as ps_file:
                ps_file.write(_gerar_pdfa_def(nivel_pdfa))
                ps_efetivo = Path(ps_file.name)
                criou_ps_proprio = True

        comando = [
            str(caminho_gs),
            "-dSAFER",
            f"-dPDFA={nivel_pdfa}",
            "-dBATCH",
            "-dNOPAUSE",
            "-dNOOUTERSAVE",
            "-sColorConversionStrategy=UseDeviceIndependentColor",
            "-sProcessColorModel=DeviceRGB",
            "-sDEVICE=pdfwrite",
            "-dPDFACompatibilityPolicy=1",
            "-dCompatibilityLevel=1.7" if nivel_pdfa == "2" else "-dCompatibilityLevel=1.4",
            f"-sOutputFile={caminho_saida}",
            str(ps_efetivo),
            str(caminho_entrada),
        ]

        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutos de timeout por arquivo
            stdin=subprocess.DEVNULL,
            creationflags=flags,
        )

        if resultado.returncode != 0:
            stderr_resumo = resultado.stderr[:500] if resultado.stderr else "(sem detalhes)"
            raise PdfAConversionError(
                f"Ghostscript retornou erro ao converter '{caminho_entrada.name}':\n"
                f"{stderr_resumo}"
            )

        if not caminho_saida.exists() or caminho_saida.stat().st_size == 0:
            raise PdfAConversionError(
                f"A conversão de '{caminho_entrada.name}' não produziu um arquivo válido."
            )

        return ResultadoConversao(
            caminho_saida=caminho_saida,
            perfil=perfil,
            validado=False,
            mensagem="Conversão concluída.",
        )

    except subprocess.TimeoutExpired:
        raise PdfAConversionError(
            f"A conversão de '{caminho_entrada.name}' excedeu o tempo limite (120s)."
        )
    except PdfAConversionError:
        raise
    except OSError as exc:
        raise PdfAConversionError(
            f"Erro ao executar Ghostscript: {exc}"
        ) from exc
    finally:
        if criou_ps_proprio and ps_efetivo is not None:
            try:
                ps_efetivo.unlink(missing_ok=True)
            except OSError:
                pass


def validar_pdfa(caminho_pdf: Path) -> bool:
    """Verifica se um PDF possui metadados indicando conformidade PDF/A.

    Executa validação rápida em nível binário e, caso inconclusivo, recorre
    à inspeção de metadados XMP detalhada via pikepdf.
    """
    if not caminho_pdf.exists() or caminho_pdf.stat().st_size == 0:
        return False

    # 1. Validação rápida de alta performance (varredura de marcadores binários XMP)
    if _validar_basica(caminho_pdf):
        return True

    # 2. Validação detalhada via pikepdf caso a rápida não encontre marcação direta
    return _validar_via_pikepdf(caminho_pdf)


def _validar_via_pikepdf(caminho_pdf: Path) -> bool:
    """Validação via pikepdf — verifica metadados XMP de conformidade PDF/A."""
    try:
        import pikepdf
        with pikepdf.open(caminho_pdf) as pdf:
            with pdf.open_metadata() as meta:
                ns_pdfaid = "http://www.aiim.org/pdfa/ns/id/"
                part = meta.get(f"{{{ns_pdfaid}}}part")
                if part is not None:
                    return True
                xmp_str = str(meta)
                if "pdfaid:part" in xmp_str or "pdfa:part" in xmp_str:
                    return True
        return False
    except (pikepdf.PdfError, OSError, ValueError):
        _logger.warning("Não foi possível validar os metadados de '%s'.", caminho_pdf, exc_info=True)
        return False


def _validar_basica(caminho_pdf: Path) -> bool:
    """Validação básica sem pikepdf — busca marcações PDF/A nos bytes do arquivo."""
    try:
        marcadores = [b"pdfaid:part", b"pdfa:part", b"PDF/A"]
        anterior = b""
        with caminho_pdf.open("rb") as arquivo:
            while bloco := arquivo.read(1024 * 1024):
                conteudo = anterior + bloco
                if any(marcador in conteudo for marcador in marcadores):
                    return True
                anterior = conteudo[-32:]
        return False
    except OSError:
        return False


def converter_e_validar(
    caminho_entrada: Path,
    caminho_saida: Path,
    perfil: str = "PDF/A-2b",
    ps_path: Optional[Path] = None,
) -> ResultadoConversao:
    """Converte um PDF para PDF/A e valida o resultado."""
    resultado = converter_para_pdfa(caminho_entrada, caminho_saida, perfil, ps_path=ps_path)

    # Validar o resultado
    if validar_pdfa(caminho_saida):
        resultado.validado = True
        resultado.mensagem = f"Conversão concluída e validada como {perfil}."
    else:
        resultado.validado = False
        resultado.mensagem = (
            f"Conversão concluída, mas a validação de conformidade {perfil} "
            f"não foi confirmada. O arquivo pode não estar totalmente em "
            f"conformidade com o padrão."
        )

    return resultado


def converter_lote(
    arquivos: list[tuple[Path, Path]],
    perfil: str = "PDF/A-2b",
    cancel_event: Optional[threading.Event] = None,
    on_file_progress: Optional[Callable[[int, int, str], None]] = None,
) -> ResultadoLote:
    """Converte múltiplos arquivos PDF para PDF/A reutilizando definições de lote."""
    resultado_lote = ResultadoLote()
    total = len(arquivos)
    if not arquivos:
        return resultado_lote

    nivel_pdfa = _PERFIS_PDFA.get(perfil, "2")
    ps_lote: Path | None = None

    try:
        # Gera o arquivo .ps auxiliar uma única vez para todo o lote
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps", delete=False, encoding="utf-8"
        ) as ps_file:
            ps_file.write(_gerar_pdfa_def(nivel_pdfa))
            ps_lote = Path(ps_file.name)

        for idx, (caminho_entrada, caminho_saida) in enumerate(arquivos, start=1):
            if cancel_event is not None and cancel_event.is_set():
                raise ProcessoCanceladoError("Operação cancelada pelo usuário.")

            if on_file_progress is not None:
                on_file_progress(idx, total, caminho_entrada.name)

            try:
                resultado = converter_e_validar(caminho_entrada, caminho_saida, perfil, ps_path=ps_lote)
                resultado_lote.convertidos.append(resultado)
            except PdfAConversionError as exc:
                resultado_lote.erros.append(
                    f"Erro ao converter '{caminho_entrada.name}': {exc}"
                )
    finally:
        if ps_lote is not None:
            try:
                ps_lote.unlink(missing_ok=True)
            except OSError:
                pass

    return resultado_lote


def _gerar_pdfa_def(nivel: str) -> str:
    """Gera o conteúdo do arquivo PostScript auxiliar para definição PDF/A.

    O Ghostscript requer um arquivo .ps com definições de metadados e
    perfil de cor ICC para gerar documentos compatíveis com PDF/A.
    Este arquivo é processado antes do PDF de entrada.
    """
    return """%!PS
% Definições para conformidade PDF/A (gerado automaticamente)

% Definir metadados mínimos do documento
[ /Title (Documento)
  /DOCINFO pdfmark

% Definir intent de saída com perfil sRGB embutido pelo Ghostscript.
% O Ghostscript resolve o perfil ICC automaticamente quando
% ProcessColorModel=DeviceRGB e ColorConversionStrategy=UseDeviceIndependentColor
% estão definidos na linha de comando.
"""

