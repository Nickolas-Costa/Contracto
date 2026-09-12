"""
Serviço de conversão de arquivos RTF para PDF utilizando o Microsoft Word via COM,
com proteção contra bloqueios
de arquivo, supressão de diálogos e timeouts rígidos para evitar travamentos.

Quando o Word para de responder, o chamador pode ser avisado (callback
`ao_travar`) para exibir contagem regressiva ao usuário; esgotado o prazo,
apenas a instância filha criada pelo aplicativo é encerrada.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from utils.logger import obter_logger


_logger = obter_logger("rtf")


class RtfConversionError(Exception):
    """Erro ao tentar converter um arquivo RTF para PDF."""


# Chamada ao travar: (nome_do_arquivo, prazo_em_segundos, encerrar_agora).
AoTravarCallback = Callable[[str, int, Callable[[], None]], None]


def _word_ausente(exc: BaseException) -> bool:
    """Diz se a falha indica Word não instalado (pywin32 ausente ou classe COM não registrada)."""
    if isinstance(exc, ImportError):
        return True
    if type(exc).__name__ == "com_error":
        codigo = getattr(exc, "hresult", None)
        if codigo in (-2147221005, -2147221164):
            return True
        texto = str(exc).lower()
        if "invalid class string" in texto or "classe não registrada" in texto:
            return True
    return False


def _mensagem_word_ausente() -> str:
    return (
        "Para converter arquivos RTF é necessário o Microsoft Word "
        "instalado nesta máquina."
    )


def _pid_do_word(word) -> Optional[int]:
    """PID do processo da instância do Word (para encerrar só a nossa)."""
    try:
        import ctypes

        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(
            int(word.Hwnd), ctypes.byref(pid)
        )
        return pid.value or None
    except Exception:
        return None


def _encerrar_word(pid: Optional[int]) -> bool:
    """Encerra pelo PID a instância filha do Word. Devolve True se encerrou."""
    if not pid or sys.platform != "win32":
        return False
    try:
        flags = subprocess.CREATE_NO_WINDOW
        proc = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            creationflags=flags,
            timeout=10,
        )
        encerrado = proc.returncode == 0
        _logger.warning(
            "Instância do Word (PID %s) encerrada após travamento: %s.",
            pid,
            encerrado,
        )
        return encerrado
    except (OSError, subprocess.SubprocessError):
        _logger.warning("Não foi possível encerrar o Word (PID %s).", pid)
        return False


def _executar_conversao_word_com(
    caminho_rtf: Path,
    caminho_pdf: Path,
    pid_destino: Optional[dict] = None,
) -> None:
    """Executa a conversão via MS Word COM com supressão de alertas e modo somente-leitura.

    Se `pid_destino` for informado, o PID da instância criada é guardado
    nele (chave `"pid"`) para encerramento seletivo em caso de travamento.
    """
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RtfConversionError(_mensagem_word_ausente()) from exc

    pythoncom.CoInitialize()
    abs_in = str(caminho_rtf.resolve())
    abs_out = str(caminho_pdf.resolve())
    wdFormatPDF = 17

    word = None
    doc = None
    try:
        # Abrir uma instância limpa e isolada do Word
        try:
            word = win32com.client.DispatchEx("Word.Application")
        except Exception as exc:
            if _word_ausente(exc):
                raise RtfConversionError(_mensagem_word_ausente()) from exc
            raise
        if pid_destino is not None:
            pid_destino["pid"] = _pid_do_word(word)
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


def converter_rtf_para_pdf(
    caminho_rtf: Path,
    caminho_pdf: Path,
    timeout_segundos: int = 25,
    prazo_aviso_segundos: int = 15,
    ao_travar: Optional[AoTravarCallback] = None,
) -> Path:
    """
    Converte um arquivo RTF para PDF utilizando o Microsoft Word via COM,
    com proteção contra loops/conflitos e rota alternativa silenciosa.

    Args:
        caminho_rtf: Caminho do arquivo RTF original.
        caminho_pdf: Caminho de saída do PDF temporário gerado.
        timeout_segundos: Tempo limite da conversão antes de considerar travamento.
        prazo_aviso_segundos: Prazo exibido ao usuário antes do encerramento
            automático da instância travada.
        ao_travar: Callback `(nome_arquivo, prazo, encerrar_agora)` chamado
            ao detectar travamento; `encerrar_agora()` encerra de imediato.

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
    pid_filho: dict = {}
    pedido_encerramento = threading.Event()

    def _worker():
        try:
            _executar_conversao_word_com(caminho_rtf, caminho_pdf, pid_filho)
        except Exception as exc:
            _logger.error("Falha do Word ao converter '%s'.", caminho_rtf, exc_info=True)
            erro_thread.append(exc)
        finally:
            concluido.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout_segundos)

    if not concluido.is_set():
        # Travamento: avisa (com prazo visível) e encerra só a instância filha.
        def _encerrar_agora() -> None:
            pedido_encerramento.set()
            _encerrar_word(pid_filho.get("pid"))

        if ao_travar is not None:
            try:
                ao_travar(caminho_rtf.name, prazo_aviso_segundos, _encerrar_agora)
            except Exception:
                _logger.warning("Callback de aviso de travamento falhou.", exc_info=True)

        limite = time.monotonic() + prazo_aviso_segundos
        while (
            time.monotonic() < limite
            and not concluido.is_set()
            and not pedido_encerramento.is_set()
        ):
            concluido.wait(0.5)

        if not concluido.is_set():
            _encerrar_word(pid_filho.get("pid"))
            _logger.warning(
                "Word encerrado após travar na conversão de '%s'.", caminho_rtf.name
            )

    if concluido.is_set() and not erro_thread:
        return caminho_pdf

    if erro_thread and (
        _word_ausente(erro_thread[0])
        or isinstance(erro_thread[0], RtfConversionError)
        and str(erro_thread[0]) == _mensagem_word_ausente()
    ):
        raise RtfConversionError(_mensagem_word_ausente()) from erro_thread[0]

    if not concluido.is_set() or erro_thread:
        if not concluido.is_set():
            raise RtfConversionError(
                f"O Microsoft Word parou de responder ao converter '{caminho_rtf.name}' "
                "e foi encerrado.\n\n"
                "Feche janelas abertas do Word e tente novamente."
            )

        erro_word = erro_thread[0]
        raise RtfConversionError(
            f"Falha ao converter '{caminho_rtf.name}' para PDF: {erro_word}\n"
            "Verifique se o arquivo RTF é válido e se não está bloqueado em outra aplicação."
        ) from erro_word

    return caminho_pdf
