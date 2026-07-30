"""
Gerenciador de perfis da aplicação.

Cada perfil armazena configurações de modelos e formato de saída,
similar ao sistema de perfis do PDFCreator.

Os perfis são salvos em %APPDATA%/Contracto/contracto_profiles.json.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


_PROFILES_FILE_NAME = "contracto_profiles.json"

PERFIL_PADRAO_NOME = "Padrão"


@dataclass
class Perfil:
    """Um perfil de configuração de modelos e formato de saída."""
    nome: str = PERFIL_PADRAO_NOME
    caminho_modelo_ppe: str = ""        # Vazio = usar embutido
    caminho_modelo_imovel: str = ""     # Vazio = usar embutido
    formato_saida: str = "PDF/A-2b"     # "PDF/A-2b" ou "PDF"

    def usa_modelos_embutidos(self) -> bool:
        """Retorna True se ambos os modelos são os embutidos (caminhos vazios)."""
        return not self.caminho_modelo_ppe and not self.caminho_modelo_imovel


def _diretorio_perfis() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        config_dir = Path(appdata) / "Contracto"
    else:
        config_dir = Path(__file__).resolve().parent.parent / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _caminho_perfis() -> Path:
    return _diretorio_perfis() / _PROFILES_FILE_NAME


def carregar_perfis() -> list[Perfil]:
    """Carrega todos os perfis do disco. Sempre inclui o perfil Padrão."""
    caminho = _caminho_perfis()
    perfis: list[Perfil] = []

    if caminho.exists():
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            for item in dados:
                perfis.append(Perfil(**item))
        except (json.JSONDecodeError, OSError, TypeError):
            perfis = []

    # Garantir que o perfil padrão sempre existe
    if not any(p.nome == PERFIL_PADRAO_NOME for p in perfis):
        perfis.insert(0, Perfil())

    return perfis


def salvar_perfis(perfis: list[Perfil]) -> None:
    """Salva todos os perfis no disco."""
    caminho = _caminho_perfis()
    dados = [asdict(p) for p in perfis]
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def obter_perfil(nome: str) -> Optional[Perfil]:
    """Retorna um perfil pelo nome, ou None se não existir."""
    perfis = carregar_perfis()
    for p in perfis:
        if p.nome == nome:
            return p
    return None


def adicionar_perfil(perfil: Perfil) -> None:
    """Adiciona um novo perfil. Erro se já existir um com o mesmo nome."""
    perfis = carregar_perfis()
    if any(p.nome == perfil.nome for p in perfis):
        raise ValueError(f"Já existe um perfil com o nome '{perfil.nome}'.")
    perfis.append(perfil)
    salvar_perfis(perfis)


def atualizar_perfil(perfil: Perfil) -> None:
    """Atualiza um perfil existente."""
    perfis = carregar_perfis()
    for i, p in enumerate(perfis):
        if p.nome == perfil.nome:
            perfis[i] = perfil
            salvar_perfis(perfis)
            return
    raise ValueError(f"Perfil '{perfil.nome}' não encontrado.")


def excluir_perfil(nome: str) -> None:
    """Exclui um perfil. O perfil Padrão não pode ser excluído."""
    if nome == PERFIL_PADRAO_NOME:
        raise ValueError("O perfil Padrão não pode ser excluído.")
    perfis = carregar_perfis()
    perfis = [p for p in perfis if p.nome != nome]
    salvar_perfis(perfis)


def listar_nomes_perfis() -> list[str]:
    """Retorna a lista de nomes de todos os perfis."""
    return [p.nome for p in carregar_perfis()]
