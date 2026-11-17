"""
Gerenciador de configurações persistentes da aplicação.

As configurações são salvas em JSON na pasta %APPDATA%/Contracto/
para que sobrevivam a atualizações do executável.
"""

import json
from pathlib import Path

from utils.caminhos import diretorio_dados_local, guardar_copia_corrompida
from utils.json_storage import salvar_json
from typing import Any


_CONFIG_DIR_NAME = "Contracto"
_CONFIG_FILE_NAME = "contracto_config.json"

_DEFAULTS = {
    "aparencia": "light",           # "system", "light", "dark"
    "cor_destaque": "#1E6FB3",      # Azul Institucional
    "formato_saida": "PDF/A-2b",    # "PDF/A-2b" ou "PDF"
    "perfil_ativo": "MCMV",
    "formularios_basicos_selecionados": [],
    "local_padrao": "CAMOCIM-CE",
    "tamanho_quadros": "Médio",     # "Pequeno", "Médio", "Grande"
    "primeira_execucao": True,
    # Municípios do ITBI: prefeitura, comarca e texto da isenção (a lei é municipal).
    "municipios_itbi": [{
        "prefeitura": "CAMOCIM-CE", "comarca": "CAMOCIM-CE",
        "texto_isencao": "Conforme Lei Municipal nº 1648/2023, de 29 de dezembro de 2023, bem como a Lei Federal nº 14620/2023. Declaro que cumpro os requisitos para ser contemplado com os benefícios da Lei supracitada.",
    }],
    "municipios_itbi_padrao": "CAMOCIM-CE",
    # Padrões de leitura de documentos criados pelo usuário: {tipo, antes, ate} (ver services/pdf_extraction.py).
    "padroes_leitura": [],
}

_CHAVES_MUNICIPIO = ("prefeitura", "comarca", "texto_isencao")


TIPOS_PADRAO_LEITURA = ("nome", "vendedor", "razao", "endereco", "endereco_imovel", "mae", "pai", "matricula")
ATE_PADRAO_LEITURA = ("virgula", "ponto", "ponto_e_virgula", "fim_da_linha")


def normalizar_padroes_leitura(lista: Any) -> list[dict[str, str]]:
    """Mantém só padrões válidos (tipo e término conhecidos, frase de 1 a 120 caracteres); config vem da UI."""
    itens = []
    for bruto in lista if isinstance(lista, list) else []:
        if not isinstance(bruto, dict):
            continue
        item = {"tipo": str(bruto.get("tipo", "")), "antes": " ".join(str(bruto.get("antes", "")).split())[:120], "ate": str(bruto.get("ate", ""))}
        if item["tipo"] in TIPOS_PADRAO_LEITURA and item["antes"] and item["ate"] in ATE_PADRAO_LEITURA and item not in itens:
            itens.append(item)
    return itens[:30]


def normalizar_municipios(lista: Any) -> list[dict[str, str]]:
    """Mantém só itens com prefeitura, textos limitados e sem repetir prefeitura (config vem da UI)."""
    itens, vistos = [], set()
    for bruto in lista if isinstance(lista, list) else []:
        if not isinstance(bruto, dict):
            continue
        item = {k: str(bruto.get(k, "")).strip()[:2000] for k in _CHAVES_MUNICIPIO}
        if item["prefeitura"] and item["prefeitura"].casefold() not in vistos:
            vistos.add(item["prefeitura"].casefold())
            itens.append(item)
    return itens[:50]

# Cache em memória para evitar I/O repetitivo a cada leitura
_config_cache: dict[str, Any] | None = None


def _diretorio_config() -> Path:
    """Retorna o diretório de configuração (primeiro local gravável)."""
    return diretorio_dados_local(_CONFIG_DIR_NAME)


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
        except json.JSONDecodeError:
            copia = guardar_copia_corrompida(caminho)
            from utils.logger import obter_logger

            obter_logger("config").warning(
                "Configuração ilegível; padrões restaurados (cópia: %s).", copia
            )
        except OSError:
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
    salvar_json(caminho, config)

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

