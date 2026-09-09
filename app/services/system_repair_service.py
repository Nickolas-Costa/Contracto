"""
Serviço de Diagnóstico e Reparo do Sistema Contracto.

Realiza checagens de integridade, limpeza de processos órfãos (Word/Ghostscript),
remoção de arquivos temporários, verificação de dependências e atualização do atalho.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from utils.ghostscript_setup import localizar_ghostscript, obter_versao_ghostscript
from utils.resource_path import caminho_recurso, listar_modelos_configurados
from utils.logger import obter_logger


_logger = obter_logger("reparo")


@dataclass
class ResultadoReparo:
    sucesso: bool
    titulo: str
    detalhes: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)


def executar_diagnostico_e_reparo() -> ResultadoReparo:
    """Executa a rotina completa de diagnóstico e reparo."""
    detalhes: list[str] = []
    alertas: list[str] = []
    sucesso_geral = True

    # 1. Encerramento de processos órfãos
    processos_encerrados = _encerrar_processos_orfaos()
    if processos_encerrados > 0:
        detalhes.append(f"Processos em segundo plano finalizados: {processos_encerrados} processo(s) órfão(s).")
    else:
        detalhes.append("Nenhum processo órfão ou travado em segundo plano.")

    # 2. Limpeza de arquivos temporários
    arquivos_limpos = _limpar_arquivos_temporarios()
    detalhes.append(f"Arquivos temporários e resíduos limpos: {arquivos_limpos} arquivo(s) removido(s).")

    # 3. Verificação do Ghostscript
    caminho_gs = localizar_ghostscript()
    if caminho_gs and caminho_gs.exists():
        versao_gs = obter_versao_ghostscript(caminho_gs) or "desconhecida"
        detalhes.append(f"Ghostscript operacional: Versão {versao_gs} localizada em '{caminho_gs.name}'.")
    else:
        alertas.append("Ghostscript não encontrado. Conversões para PDF/A-2b podem falhar até que o Ghostscript seja reinstalado.")
        sucesso_geral = False

    # 4. Verificação de modelos de formulário padrão
    modelos_ok = _verificar_modelos_padrao()
    if modelos_ok:
        detalhes.append("Modelos incluídos no aplicativo verificados com sucesso.")
    else:
        alertas.append("Um ou mais modelos padrão de documentos não foram encontrados na pasta de assets.")
        sucesso_geral = False

    # 5. Recriação do atalho na Área de Trabalho
    atalho_criado = _atualizar_atalho_desktop()
    if atalho_criado:
        detalhes.append("Atalho do Contracto na Área de Trabalho verificado/atualizado.")
    else:
        detalhes.append("Atalho na Área de Trabalho mantido sem alterações.")

    titulo = "Reparo do Sistema Concluído com Sucesso" if sucesso_geral else "Reparo Concluído com Alertas"
    return ResultadoReparo(
        sucesso=sucesso_geral,
        titulo=titulo,
        detalhes=detalhes,
        alertas=alertas,
    )


def _encerrar_processos_orfaos() -> int:
    """Encerra instâncias em background de ferramentas que possam ter travado (Windows)."""
    if sys.platform != "win32":
        return 0

    encerrados = 0
    processos_alvo = ["gswin64c.exe", "gswin32c.exe", "gs.exe", "WINWORD.EXE"]
    usuario_atual = os.environ.get("USERNAME", "")
    filtro_usuario = ["/FI", f"USERNAME eq {usuario_atual}"] if usuario_atual else []

    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    for proc in processos_alvo:
        try:
            cmd = ["taskkill", "/F", "/IM", proc] + filtro_usuario
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                creationflags=flags,
                timeout=5,
            )
            if res.returncode == 0:
                encerrados += 1
        except (OSError, subprocess.SubprocessError):
            _logger.warning("Não foi possível encerrar o processo '%s'.", proc, exc_info=True)

    return encerrados


def _limpar_arquivos_temporarios() -> int:
    """Remove arquivos temporários criados pelo Contracto (conversões RTF, pós-processamento)."""
    removidos = 0
    temp_dir = Path(tempfile.gettempdir())

    padroes = ["temp_*.pdf", "temp_*.rtf", "temp_*.ps", "Contracto_tmp_*"]
    for padrao in padroes:
        for arq in temp_dir.glob(padrao):
            try:
                if arq.is_file():
                    arq.unlink(missing_ok=True)
                    removidos += 1
            except OSError:
                pass

    return removidos


def _verificar_modelos_padrao() -> bool:
    """Verifica se os modelos cadastrados existem no pacote."""
    modelos = listar_modelos_configurados()
    return bool(modelos) and all(modelo.exists() for modelo in modelos)


def _atualizar_atalho_desktop() -> bool:
    """Tenta recriar o atalho da aplicação na área de trabalho se estiver no Windows."""
    if sys.platform != "win32":
        return False

    try:
        import win32com.client
    except ImportError:
        return False

    try:
        user_profile = os.environ.get("USERPROFILE", "")
        desktop_candidates = [
            os.path.join(user_profile, "OneDrive", "Desktop"),
            os.path.join(user_profile, "Desktop"),
        ]
        desktop = None
        for d in desktop_candidates:
            if os.path.exists(d):
                desktop = d
                break

        if not desktop:
            return False

        path_lnk = os.path.join(desktop, "Contracto.lnk")

        # Localizar executável da aplicação
        exe_path = Path(sys.executable)
        # Se estiver rodando via Python script, não sobrescreve com python.exe a menos que seja Contracto.exe
        if "python" in exe_path.name.lower() and getattr(sys, "frozen", False) is False:
            # Em modo dev, buscar na pasta dist se existir
            projeto_raiz = Path(__file__).resolve().parent.parent.parent
            dist_exes = list((projeto_raiz / "app" / "dist").glob("Contracto_v*.exe"))
            if dist_exes:
                exe_path = dist_exes[0]
            else:
                return False

        icon_path = caminho_recurso("assets", "icons", "app_icon.ico")

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path_lnk)
        shortcut.Targetpath = str(exe_path)
        shortcut.WorkingDirectory = str(exe_path.parent)
        if icon_path.exists():
            shortcut.IconLocation = f"{icon_path},0"
        else:
            shortcut.IconLocation = f"{exe_path},0"
        shortcut.save()
        return True
    except (OSError, AttributeError):
        _logger.warning("Não foi possível atualizar o atalho do aplicativo.", exc_info=True)
        return False
