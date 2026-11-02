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
import time
from datetime import datetime
from pathlib import Path


def _gravavel(diretorio: Path) -> Path | None:
    """Devolve o diretório se for possível criar e escrever nele.

    O antivírus/OneDrive segura o arquivo de teste por instantes: sem repetir, uma falha passageira jogava
    configurações e perfis para outra pasta (tema voltava ao padrão sem ninguém mexer).
    """
    for tentativa in range(3):
        try:
            diretorio.mkdir(parents=True, exist_ok=True)
            teste = diretorio / ".escrita_teste"
            teste.touch()
        except OSError:
            time.sleep(0.15)
            continue
        try:
            teste.unlink()
        except OSError:
            pass  # o arquivo existe e foi criado: a escrita funciona
        return diretorio
    return None


_dados_resolvidos: dict[tuple, Path] = {}


def diretorio_dados_local(nome: str = "Contracto") -> Path:
    """Primeiro diretório gravável da cascata de locais de dados.

    O local do usuário (primeiro candidato) é resolvido uma vez por processo e reaproveitado: ele não troca de
    pasta no meio da sessão por causa de uma falha passageira.
    """
    chave = (nome, os.environ.get("APPDATA"), os.environ.get("LOCALAPPDATA"))
    fixo = _dados_resolvidos.get(chave)
    if fixo is not None:
        fixo.mkdir(parents=True, exist_ok=True)
        return fixo
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
    for indice, candidato in enumerate(candidatos):
        resolvido = _gravavel(candidato)
        if resolvido is not None:
            if indice == 0:
                _dados_resolvidos[chave] = resolvido
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
