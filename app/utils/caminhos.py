"""Caminhos de pastas do aplicativo com fallbacks seguros.

Centraliza a resolução de diretórios graváveis para que nenhum ponto do
código presuma variável de ambiente ou pasta existente:

- `diretorio_dados_local`: %APPDATA% → %LOCALAPPDATA% → perfil do usuário
  → temporária do sistema (primeira que aceitar escrita).
- `pasta_downloads`: pasta de Downloads real (inclui redirecionamento
  do OneDrive) ou a pasta do usuário como último recurso.
- `guardar_copia_corrompida`: renomeia um JSON ilegível para
  `<nome>.corrompido-<data-hora>`, preservando evidência antes do reset.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path


def _gravavel(diretorio: Path) -> Path | None:
    """Devolve o diretório se for possível criar e escrever nele."""
    try:
        diretorio.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    try:
        teste = diretorio / ".escrita_teste"
        teste.touch()
        teste.unlink()
    except OSError:
        return None
    return diretorio


def diretorio_dados_local(nome: str = "Contracto") -> Path:
    """Primeiro diretório gravável da cascata de locais de dados."""
    candidatos: list[Path] = []
    for variavel in ("APPDATA", "LOCALAPPDATA"):
        base = os.environ.get(variavel)
        if base:
            candidatos.append(Path(base) / nome)
    try:
        candidatos.append(Path.home() / "AppData" / "Roaming" / nome)
    except (RuntimeError, OSError):
        pass
    candidatos.append(Path(tempfile.gettempdir()) / nome)
    for candidato in candidatos:
        resolvido = _gravavel(candidato)
        if resolvido is not None:
            return resolvido
    ultimo = candidatos[-1]
    ultimo.mkdir(parents=True, exist_ok=True)
    return ultimo


def pasta_downloads() -> Path:
    """Pasta de Downloads existente ou a pasta do usuário."""
    candidatos: list[Path] = []
    perfil = os.environ.get("USERPROFILE")
    if perfil:
        candidatos.append(Path(perfil) / "Downloads")
    try:
        candidatos.append(Path.home() / "Downloads")
    except (RuntimeError, OSError):
        pass
    for candidato in candidatos:
        try:
            if candidato.is_dir():
                return candidato
        except OSError:
            continue
    try:
        return Path.home()
    except (RuntimeError, OSError):
        return Path(tempfile.gettempdir())


def guardar_copia_corrompida(caminho: Path) -> Path | None:
    """Renomeia um arquivo ilegível para `<nome>.corrompido-<data-hora>`."""
    try:
        if not caminho.exists():
            return None
        marca = datetime.now().strftime("%Y%m%d-%H%M%S")
        copia = caminho.with_name(f"{caminho.name}.corrompido-{marca}")
        caminho.rename(copia)
        return copia
    except OSError:
        return None
