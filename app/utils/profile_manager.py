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
class FormularioModelo:
    """Configuração de um formulário PDF associado ao perfil."""
    nome: str
    caminho: str
    geracao: str = "por_participante"  # "por_participante" ou "unico"
    mapeamento: dict[str, str] = field(default_factory=dict)


@dataclass
class Perfil:
    """Um perfil de configuração de modelos e formato de saída."""
    nome: str = PERFIL_PADRAO_NOME
    formularios: list[FormularioModelo] = field(default_factory=list)
    formato_saida: str = "PDF/A-2b"     # "PDF/A-2b" ou "PDF"

    def usa_modelos_embutidos(self) -> bool:
        """Retorna True se usar os formulários embutidos (PPE e 1º Imóvel sem caminhos)."""
        if not self.formularios:
            return True
        for f in self.formularios:
            if f.caminho:
                return False
        return True


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
                # Migração: Se for o formato antigo (com caminho_modelo_ppe)
                if "caminho_modelo_ppe" in item:
                    ppe_path = item.pop("caminho_modelo_ppe", "")
                    imovel_path = item.pop("caminho_modelo_imovel", "")
                    
                    # Criação dos formulários dinâmicos com o mapeamento antigo fixo
                    formularios = []
                    if ppe_path or imovel_path:
                        formularios.append(FormularioModelo(
                            nome="PPE", caminho=ppe_path, geracao="por_participante", 
                            mapeamento={"NOME COMPLETO": "participante.nome_completo", "CPF": "participante.cpf_formatado", "DIA": "data.dia", "MES": "data.mes", "ANO": "data.ano", "LOCAL ASSINATURA": "participante.local_assinatura"}
                        ))
                        formularios.append(FormularioModelo(
                            nome="1_IMOVEL", caminho=imovel_path, geracao="por_participante",
                            mapeamento={"NOME COMPLETO": "participante.nome_completo", "CPF": "participante.cpf_formatado", "ENDERECO": "participante.endereco", "DATA ASSINATURA": "participante.data_assinatura", "LOCAL ASSINATURA": "participante.local_assinatura"}
                        ))
                    item["formularios"] = formularios
                else:
                    # Formato novo: desserializar os dicionários de formulário
                    item["formularios"] = [FormularioModelo(**f) for f in item.get("formularios", [])]
                    
                perfis.append(Perfil(**item))
        except (json.JSONDecodeError, OSError, TypeError):
            perfis = []

    # Garantir que o perfil padrão sempre existe
    if not any(p.nome == PERFIL_PADRAO_NOME for p in perfis):
        perfis.insert(0, Perfil(
            nome=PERFIL_PADRAO_NOME,
            formularios=[
                FormularioModelo(nome="PPE", caminho="", geracao="por_participante", mapeamento={}),
                FormularioModelo(nome="1º Imóvel", caminho="", geracao="por_participante", mapeamento={})
            ]
        ))

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
