"""
Serviço de conversão de arquivos RTF para PDF utilizando o Microsoft Word via COM
ou LibreOffice como fallback, com proteção contra bloqueios de arquivo, supressão
de diálogos e timeouts rígidos para evitar travamentos silenciosos.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Optional

from utils.logger import obter_logger


_logger = obter_logger("rtf")


class RtfConversionError(Exception):
    """Erro ao tentar converter um arquivo RTF para PDF."""


def _localizar_libreoffice() -> Optional[Path]:
    """Tenta localizar o executável do LibreOffice (soffice) no Windows ou Linux."""
    # 1. Procurar no PATH
    caminho_which = shutil.which("soffice") or shutil.which("soffice.exe")
    if caminho_which:
        return Path(caminho_which)

    # 2. Caminhos padrão de instalação no Windows
    candidatos_windows = [
        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "LibreOffice" / "program" / "soffice.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "LibreOffice" / "program" / "soffice.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "LibreOffice" / "program" / "soffice.exe",
    ]
    for c in candidatos_windows:
        if c.exists():
            return c

    return None


def _converter_via_libreoffice(caminho_rtf: Path, caminho_pdf: Path, timeout: int = 30) -> Path:
    """Converte RTF para PDF usando o LibreOffice em modo headless."""
    soffice = _localizar_libreoffice()
    if not soffice:
        raise RtfConversionError("LibreOffice não encontrado no sistema.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir)
        cmd = [
            str(soffice),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(caminho_rtf.resolve()),
        ]
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            creationflags=flags,
        )
        if proc.returncode != 0:
            raise RtfConversionError(f"LibreOffice retornou código {proc.returncode}: {proc.stderr}")

        esperado = out_dir / (caminho_rtf.stem + ".pdf")
        if not esperado.exists():
            raise RtfConversionError("LibreOffice concluiu mas não gerou o arquivo PDF esperado.")

        shutil.copy2(str(esperado), str(caminho_pdf))
        return caminho_pdf


def _executar_conversao_word_com(caminho_rtf: Path, caminho_pdf: Path) -> None:
    """Executa a conversão via MS Word COM com supressão de alertas e modo somente-leitura."""
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        raise RtfConversionError("Biblioteca pywin32 não está disponível no ambiente.")

    pythoncom.CoInitialize()
    abs_in = str(caminho_rtf.resolve())
    abs_out = str(caminho_pdf.resolve())
    wdFormatPDF = 17

    word = None
    doc = None
    try:
        # Abrir uma instância limpa e isolada do Word
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        # 0 = wdAlertsNone: suprime diálogos de confirmação, substituição ou bloqueio
        word.DisplayAlerts = 0
        word.ScreenUpdating = False
        try:
            word.FeatureInstall = 0
        except Exception:
            _logger.debug("O Word não aceitou a configuração de instalação de recursos.", exc_info=True)

        # Abrir explicitamente em ReadOnly e sem confirmação de conversão para não conflitar com arquivos abertos
        doc = word.Documents.Open(
            FileName=abs_in,
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
            Visible=False,
            Revert=False,
            NoEncodingDialog=True,
        )

        doc.SaveAs(abs_out, FileFormat=wdFormatPDF)

        if not caminho_pdf.exists() or caminho_pdf.stat().st_size == 0:
            raise RtfConversionError("O MS Word concluiu a exportação, mas o PDF de saída não foi gerado.")

    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=0)
            except Exception:
                _logger.warning("Não foi possível fechar o documento aberto pelo Word.", exc_info=True)
        if word is not None:
            try:
                word.Quit()
            except Exception:
                _logger.warning("Não foi possível encerrar a instância do Word.", exc_info=True)
        try:
            pythoncom.CoUninitialize()
        except Exception:
            _logger.debug("Não foi possível liberar o acesso COM desta thread.", exc_info=True)


def converter_rtf_para_pdf(caminho_rtf: Path, caminho_pdf: Path, timeout_segundos: int = 25) -> Path:
    """
    Converte um arquivo RTF para PDF utilizando o Microsoft Word via COM,
    com proteção contra loops/conflitos e fallback automático para LibreOffice.

    Args:
        caminho_rtf: Caminho do arquivo RTF original.
        caminho_pdf: Caminho de saída do PDF temporário gerado.
        timeout_segundos: Tempo limite máximo para conversão antes de abortar.

    Returns:
        O caminho_pdf criado.

    Raises:
        RtfConversionError: Caso ocorra erro ou timeout na conversão.
    """
    if not caminho_rtf.exists():
        raise RtfConversionError(f"Arquivo RTF não encontrado: '{caminho_rtf}'")

    # Pré-verificação se o arquivo é legível
    try:
        with open(caminho_rtf, "rb") as f:
            f.read(1024)
    except OSError as exc:
        raise RtfConversionError(
            f"O arquivo RTF '{caminho_rtf.name}' está bloqueado ou inacessível no sistema:\n{exc}"
        ) from exc

    # Criar pasta de saída se não existir
    caminho_pdf.parent.mkdir(parents=True, exist_ok=True)

    erro_thread = []
    concluido = threading.Event()

    def _worker():
        try:
            _executar_conversao_word_com(caminho_rtf, caminho_pdf)
        except Exception as exc:
            _logger.error("Falha do Word ao converter '%s'.", caminho_rtf, exc_info=True)
            erro_thread.append(exc)
        finally:
            concluido.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout_segundos)

    if not concluido.is_set():
        # Timeout ocorreu: Word travou ou está bloqueado por caixa de diálogo modal
        # Tentar fallback com LibreOffice antes de falhar
        try:
            return _converter_via_libreoffice(caminho_rtf, caminho_pdf, timeout=20)
        except (OSError, subprocess.SubprocessError, RtfConversionError):
            _logger.warning("O LibreOffice também falhou ao converter '%s'.", caminho_rtf, exc_info=True)

        raise RtfConversionError(
            f"O Microsoft Word não respondeu a tempo na conversão de '{caminho_rtf.name}'.\n\n"
            "Possível causa: O arquivo pode estar aberto no Word com alterações pendentes "
            "ou bloqueado por outra janela do sistema. Feche o Word e tente novamente."
        )

    if erro_thread:
        erro_word = erro_thread[0]
        # Tentar fallback via LibreOffice se o Word falhou
        try:
            return _converter_via_libreoffice(caminho_rtf, caminho_pdf, timeout=25)
        except (OSError, subprocess.SubprocessError, RtfConversionError):
            _logger.warning("O LibreOffice também falhou ao converter '%s'.", caminho_rtf, exc_info=True)

        raise RtfConversionError(
            f"Falha ao converter '{caminho_rtf.name}' para PDF: {erro_word}\n"
            "Verifique se o arquivo RTF é válido e se não está bloqueado em outra aplicação."
        ) from erro_word

    return caminho_pdf
