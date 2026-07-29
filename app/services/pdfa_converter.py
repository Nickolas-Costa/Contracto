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
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from utils.ghostscript_setup import localizar_ghostscript


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
) -> ResultadoConversao:
    """Converte um PDF para o formato PDF/A utilizando Ghostscript.

    Args:
        caminho_entrada: caminho do PDF original.
        caminho_saida: caminho onde o PDF/A será salvo.
        perfil: perfil PDF/A desejado (padrão: "PDF/A-2b").
                Suporta: "PDF/A-1b", "PDF/A-2b", "PDF/A-3b".

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
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    # Criar um arquivo PostScript auxiliar para definir o perfil PDF/A

    # Criar arquivo PostScript auxiliar com as definições de conformidade PDF/A.
    # O Ghostscript precisa dessas definições para gerar PDF/A correto.
    ps_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps", delete=False, encoding="utf-8"
        ) as ps_file:
            ps_file.write(_gerar_pdfa_def(nivel_pdfa))
            ps_path = Path(ps_file.name)

        comando = [
            str(caminho_gs),
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
            str(ps_path),
            str(caminho_entrada),
        ]

        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minutos de timeout por arquivo
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
        if ps_path is not None:
            try:
                ps_path.unlink(missing_ok=True)
            except OSError:
                pass


def validar_pdfa(caminho_pdf: Path) -> bool:
    """Verifica se um PDF possui metadados indicando conformidade PDF/A.

    Esta é uma validação básica que verifica os metadados XMP do documento.
    Para validação completa, considere usar VeraPDF (futuro).

    Verifica:
    1. Se o arquivo existe e não está vazio
    2. Se os metadados XMP contêm as marcações de PDF/A (pdfa:part e pdfa:conformance)

    Args:
        caminho_pdf: caminho do arquivo PDF a validar.

    Returns:
        True se os metadados indicam conformidade PDF/A, False caso contrário.
    """
    if not caminho_pdf.exists() or caminho_pdf.stat().st_size == 0:
        return False

    try:
        # Tentar usar pikepdf para validação de metadados XMP (mais precisa)
        return _validar_via_pikepdf(caminho_pdf)
    except ImportError:
        # Se pikepdf não estiver disponível, fazer validação básica
        return _validar_basica(caminho_pdf)


def _validar_via_pikepdf(caminho_pdf: Path) -> bool:
    """Validação via pikepdf — verifica metadados XMP de conformidade PDF/A."""
    import pikepdf

    try:
        with pikepdf.open(caminho_pdf) as pdf:
            # Verificar metadados XMP
            with pdf.open_metadata() as meta:
                # Verificar se existe a marcação pdfaid:part (indica PDF/A)
                ns_pdfaid = "http://www.aiim.org/pdfa/ns/id/"
                part = meta.get(f"{{{ns_pdfaid}}}part")
                if part is not None:
                    return True

                # Verificar via string raw do XMP
                xmp_str = str(meta)
                if "pdfaid:part" in xmp_str or "pdfa:part" in xmp_str:
                    return True

        return False
    except Exception:
        return False


def _validar_basica(caminho_pdf: Path) -> bool:
    """Validação básica sem pikepdf — busca marcações PDF/A nos bytes do arquivo.

    Esta é uma verificação superficial que procura strings de metadados XMP
    no conteúdo do PDF. Menos precisa que a validação via pikepdf.
    """
    try:
        conteudo = caminho_pdf.read_bytes()
        # Buscar marcações comuns de PDF/A nos metadados XMP
        marcadores = [b"pdfaid:part", b"pdfa:part", b"PDF/A"]
        return any(marcador in conteudo for marcador in marcadores)
    except OSError:
        return False


def converter_e_validar(
    caminho_entrada: Path,
    caminho_saida: Path,
    perfil: str = "PDF/A-2b",
) -> ResultadoConversao:
    """Converte um PDF para PDF/A e valida o resultado.

    Este é o fluxo completo recomendado:
    1. Converter via Ghostscript
    2. Validar conformidade do resultado

    Args:
        caminho_entrada: caminho do PDF original.
        caminho_saida: caminho onde o PDF/A será salvo.
        perfil: perfil PDF/A desejado (padrão: "PDF/A-2b").

    Returns:
        ResultadoConversao com informação de validação.

    Raises:
        PdfAConversionError: se a conversão falhar.
        GhostscriptNaoEncontradoError: se o Ghostscript não estiver instalado.
    """
    resultado = converter_para_pdfa(caminho_entrada, caminho_saida, perfil)

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
) -> ResultadoLote:
    """Converte múltiplos arquivos PDF para PDF/A.

    Args:
        arquivos: lista de tuplas (caminho_entrada, caminho_saida).
        perfil: perfil PDF/A desejado (padrão: "PDF/A-2b").

    Returns:
        ResultadoLote com os resultados individuais e erros.
    """
    resultado_lote = ResultadoLote()

    for caminho_entrada, caminho_saida in arquivos:
        try:
            resultado = converter_e_validar(caminho_entrada, caminho_saida, perfil)
            resultado_lote.convertidos.append(resultado)
        except PdfAConversionError as exc:
            resultado_lote.erros.append(
                f"Erro ao converter '{caminho_entrada.name}': {exc}"
            )

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

