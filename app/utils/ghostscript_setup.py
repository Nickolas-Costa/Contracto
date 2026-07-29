"""
Utilitário para localizar e verificar a disponibilidade do Ghostscript
no sistema.

O Ghostscript é utilizado como motor de conversão para PDF/A-2b. Este
módulo encapsula a lógica de localização do executável, facilitando a
futura lógica de download/instalação automática.
"""

import shutil
import subprocess
from pathlib import Path


# Locais comuns de instalação do Ghostscript no Windows
_CAMINHOS_COMUNS_WINDOWS = [
    Path("C:/Program Files/gs"),
    Path("C:/Program Files (x86)/gs"),
]

# Nome do executável do Ghostscript Console (Windows)
_NOMES_EXECUTAVEL = ["gswin64c.exe", "gswin32c.exe", "gs"]


def localizar_ghostscript() -> Path | None:
    """Localiza o executável do Ghostscript no sistema.

    Busca na seguinte ordem:
    1. No PATH do sistema (via shutil.which)
    2. Nos diretórios de instalação padrão do Windows

    Returns:
        Caminho absoluto do executável, ou None se não encontrado.
    """
    from utils.resource_path import caminho_recurso
    
    # 0. Buscar no diretório embutido pelo PyInstaller
    caminho_embutido = caminho_recurso("assets", "gs", "bin")
    if caminho_embutido.exists():
        for nome in _NOMES_EXECUTAVEL:
            candidato = caminho_embutido / nome
            if candidato.exists():
                return candidato

    # 1. Buscar no PATH do sistema
    for nome in _NOMES_EXECUTAVEL:
        caminho = shutil.which(nome)
        if caminho:
            return Path(caminho)

    # 2. Buscar nos diretórios de instalação comuns do Windows
    for diretorio_base in _CAMINHOS_COMUNS_WINDOWS:
        if not diretorio_base.exists():
            continue
        # Ghostscript instala em subpastas como gs10.03.0/bin/
        for subpasta in sorted(diretorio_base.iterdir(), reverse=True):
            if not subpasta.is_dir():
                continue
            for nome in _NOMES_EXECUTAVEL:
                candidato = subpasta / "bin" / nome
                if candidato.exists():
                    return candidato

    return None


def obter_versao_ghostscript(caminho_gs: Path | None = None) -> str | None:
    """Retorna a versão do Ghostscript instalado, ou None se não disponível.

    Args:
        caminho_gs: caminho do executável. Se None, tenta localizar
                    automaticamente.
    """
    if caminho_gs is None:
        caminho_gs = localizar_ghostscript()
    if caminho_gs is None:
        return None

    try:
        resultado = subprocess.run(
            [str(caminho_gs), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if resultado.returncode == 0:
            return resultado.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass

    return None


def esta_disponivel() -> bool:
    """Retorna True se o Ghostscript está instalado e acessível."""
    return localizar_ghostscript() is not None
