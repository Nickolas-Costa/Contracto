"""Cópia de segurança de perfis e configurações (sem histórico de dossiês).

O backup é um `.zip` com data e hora em `%APPDATA%/Contracto/backups/`
contendo `contracto_profiles.json` + `contracto_config.json`. A restauração
só substitui após validar os dois arquivos.
"""

import json
import zipfile
from datetime import datetime
from pathlib import Path

from utils import config_manager
from utils import profile_manager

_ARQUIVO_PERFIS = "contracto_profiles.json"
_ARQUIVO_CONFIG = "contracto_config.json"


def pasta_backups() -> Path:
    """Pasta de backups dentro do diretório de dados (criada se ausente)."""
    pasta = config_manager._diretorio_config() / "backups"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def criar_backup(destino_dir: Path | str | None = None) -> Path:
    """Gera o ZIP de backup e devolve o caminho criado."""
    destino_dir = Path(destino_dir) if destino_dir else pasta_backups()
    destino_dir.mkdir(parents=True, exist_ok=True)
    caminho = destino_dir / f"backup-{datetime.now():%Y%m%d-%H%M%S}.zip"
    perfis = profile_manager._caminho_perfis()
    config = config_manager._caminho_config()
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as pacote:
        for origem, nome in ((perfis, _ARQUIVO_PERFIS), (config, _ARQUIVO_CONFIG)):
            if origem.exists():
                pacote.write(origem, nome)
    return caminho


def listar_backups(destino_dir: Path | str | None = None) -> list[Path]:
    """Backups existentes, do mais recente ao mais antigo."""
    pasta = Path(destino_dir) if destino_dir else pasta_backups()
    if not pasta.is_dir():
        return []
    return sorted(pasta.glob("backup-*.zip"), reverse=True)


def _validar_conteudo(pacote: zipfile.ZipFile) -> dict[str, object]:
    """Lê e valida os dois JSONs; levanta ValueError se incompletos."""
    try:
        perfis = json.loads(pacote.read(_ARQUIVO_PERFIS).decode("utf-8"))
        config = json.loads(pacote.read(_ARQUIVO_CONFIG).decode("utf-8"))
    except (KeyError, ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Backup incompleto ou ilegível.") from exc
    if not isinstance(perfis, list) or not isinstance(config, dict):
        raise ValueError("Backup incompleto ou ilegível.")
    try:
        montados = [
            profile_manager._perfil_de_dict(item) for item in perfis
            if isinstance(item, dict)
        ]
        if len(montados) != len(perfis):
            raise ValueError("Backup com perfis malformados.")
        profile_manager.validar_perfis(montados)
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError(f"Backup com perfis inválidos: {exc}") from exc
    return {"perfis": perfis, "config": config}


def restaurar_backup(arquivo: Path | str) -> None:
    """Substitui perfis e config pelo conteúdo do ZIP, após validação."""
    from utils.json_storage import salvar_json

    arquivo = Path(arquivo)
    try:
        with zipfile.ZipFile(arquivo) as pacote:
            conteudo = _validar_conteudo(pacote)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"'{arquivo.name}' não é um backup válido.") from exc
    salvar_json(profile_manager._caminho_perfis(), conteudo["perfis"])
    salvar_json(config_manager._caminho_config(), conteudo["config"])
    profile_manager.invalidar_cache()
    config_manager.invalidar_cache()
