"""
Gerenciador de configurações persistentes da aplicação.

As configurações são salvas em JSON na pasta %APPDATA%/Contracto/
para que sobrevivam a atualizações do executável.
"""

import json
import os
from pathlib import Path
from typing import Any


_CONFIG_DIR_NAME = "Contracto"
_CONFIG_FILE_NAME = "contracto_config.json"

_DEFAULTS = {
    "aparencia": "light",           # "system", "light", "dark"
    "cor_destaque": "#005CA9",      # Azul CAIXA
    "formato_saida": "PDF/A-2b",    # "PDF/A-2b" ou "PDF"
    "perfil_ativo": "Padrão",
    "local_padrao": "CAMOCIM-CE",
    "tamanho_quadros": "Médio",     # "Pequeno", "Médio", "Grande"
    "primeira_execucao": True,
}


def _diretorio_config() -> Path:
    """Retorna o diretório de configuração (%APPDATA%/Contracto/)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        config_dir = Path(appdata) / _CONFIG_DIR_NAME
    else:
        # Fallback: ao lado do executável
        config_dir = Path(__file__).resolve().parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _caminho_config() -> Path:
    return _diretorio_config() / _CONFIG_FILE_NAME


def carregar_config() -> dict[str, Any]:
    """Carrega as configurações do disco, retornando os defaults se não existir."""
    caminho = _caminho_config()
    config = dict(_DEFAULTS)
    if caminho.exists():
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                salvo = json.load(f)
            config.update(salvo)
        except (json.JSONDecodeError, OSError):
            pass
    return config


def salvar_config(config: dict[str, Any]) -> None:
    """Salva as configurações no disco."""
    caminho = _caminho_config()
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def obter(chave: str) -> Any:
    """Retorna o valor de uma configuração específica."""
    config = carregar_config()
    return config.get(chave, _DEFAULTS.get(chave))


def definir(chave: str, valor: Any) -> None:
    """Define o valor de uma configuração e salva imediatamente."""
    config = carregar_config()
    config[chave] = valor
    salvar_config(config)


def restaurar_padroes() -> dict[str, Any]:
    """Restaura todas as configurações para os valores padrão."""
    config = dict(_DEFAULTS)
    salvar_config(config)
    return config


def obter_defaults() -> dict[str, Any]:
    """Retorna uma cópia dos valores padrão."""
    return dict(_DEFAULTS)
