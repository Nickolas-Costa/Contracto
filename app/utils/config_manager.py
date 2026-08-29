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
    "cor_destaque": "#005CA9",      # Azul Institucional
    "formato_saida": "PDF/A-2b",    # "PDF/A-2b" ou "PDF"
    "perfil_ativo": "MCMV",
    "local_padrao": "CAMOCIM-CE",
    "tamanho_quadros": "Médio",     # "Pequeno", "Médio", "Grande"
    "primeira_execucao": True,
}

# Cache em memória para evitar I/O repetitivo a cada leitura
_config_cache: dict[str, Any] | None = None


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


def invalidar_cache() -> None:
    """Invalida o cache em memória forçando releitura na próxima chamada."""
    global _config_cache
    _config_cache = None


def carregar_config(forcar_disco: bool = False) -> dict[str, Any]:
    """Carrega as configurações do disco (ou do cache), retornando os defaults se não existir."""
    global _config_cache

    if _config_cache is not None and not forcar_disco:
        return dict(_config_cache)

    caminho = _caminho_config()
    config = dict(_DEFAULTS)
    if caminho.exists():
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                salvo = json.load(f)
            config.update(salvo)
        except (json.JSONDecodeError, OSError):
            pass

    # Migração: perfil "Padrão" renomeado para "MCMV"
    if config.get("perfil_ativo") == "Padrão":
        config["perfil_ativo"] = "MCMV"
        salvar_config(config)
        return config

    _config_cache = dict(config)
    return config


def salvar_config(config: dict[str, Any]) -> None:
    """Salva as configurações no disco e atualiza o cache imediatamente."""
    global _config_cache

    caminho = _caminho_config()
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    _config_cache = dict(config)


def obter(chave: str) -> Any:
    """Retorna o valor de uma configuração específica com acesso instantâneo da memória."""
    global _config_cache
    if _config_cache is None:
        carregar_config()
    return _config_cache.get(chave, _DEFAULTS.get(chave))


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

