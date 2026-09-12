"""Port de storage: abstrai %APPDATA%/Contracto vs appDataDir (Tauri).

- Hoje: %APPDATA%/Contracto (utils.config_manager/profile_manager/logger).
- Futuro: appDataDir Tauri + migração JSONs legados (script dedicado).
"""

import os
from pathlib import Path

try:
    from app.utils.config_manager import _diretorio_config
    from app.utils.resource_path import caminho_recurso
except ImportError:  # executado com app/ direto no path (ex: .exe, dev)
    from utils.config_manager import _diretorio_config
    from utils.resource_path import caminho_recurso


def get_config_dir() -> Path:
    return _diretorio_config()


def get_templates_dir() -> Path:
    return caminho_recurso("assets", "templates")


def get_log_dir() -> Path:
    diretorio = get_config_dir() / "logs"
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio


def legacy_appdata_dir() -> Path | None:
    appdata = os.environ.get("APPDATA")
    return Path(appdata) / "Contracto" if appdata else None
