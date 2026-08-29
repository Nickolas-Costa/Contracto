"""
Modelo de dados que representa um participante (comprador) do contrato
habitacional.

Este módulo não contém nenhuma lógica de interface ou de manipulação de
PDF — apenas a estrutura de dados e regras mínimas que dizem respeito
exclusivamente ao próprio participante.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Participant:
    """Dados de um participante do processo com suporte a campos dinâmicos configuráveis por perfil."""

    nome_completo: str = ""
    cpf: str = ""
    endereco: str = ""
    data_assinatura: str = ""  # Sempre no formato DD/MM/AAAA
    local_assinatura: str = "CAMOCIM-CE"
    campos_dinamicos: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.endereco and "endereco" not in self.campos_dinamicos:
            self.campos_dinamicos["endereco"] = self.endereco
        if self.data_assinatura and "data_assinatura" not in self.campos_dinamicos:
            self.campos_dinamicos["data_assinatura"] = self.data_assinatura
        if self.local_assinatura and "local_assinatura" not in self.campos_dinamicos:
            self.campos_dinamicos["local_assinatura"] = self.local_assinatura

    def obter_campo(self, campo_id: str, padrao: Any = "") -> Any:
        """Obtém o valor de um campo dinâmico ou fixo."""
        if campo_id in ("nome_completo", "nome"):
            return self.nome_completo
        if campo_id == "cpf":
            return self.cpf
        if campo_id == "endereco":
            return self.endereco or self.campos_dinamicos.get("endereco", padrao)
        if campo_id == "data_assinatura":
            return self.data_assinatura or self.campos_dinamicos.get("data_assinatura", padrao)
        if campo_id == "local_assinatura":
            return self.local_assinatura or self.campos_dinamicos.get("local_assinatura", padrao)
        return self.campos_dinamicos.get(campo_id, padrao)

    def definir_campo(self, campo_id: str, valor: Any) -> None:
        """Define o valor de um campo dinâmico ou fixo."""
        str_val = str(valor)
        if campo_id in ("nome_completo", "nome"):
            self.nome_completo = str_val
        elif campo_id == "cpf":
            self.cpf = str_val
        elif campo_id == "endereco":
            self.endereco = str_val
            self.campos_dinamicos["endereco"] = str_val
        elif campo_id == "data_assinatura":
            self.data_assinatura = str_val
            self.campos_dinamicos["data_assinatura"] = str_val
        elif campo_id == "local_assinatura":
            self.local_assinatura = str_val
            self.campos_dinamicos["local_assinatura"] = str_val
        else:
            self.campos_dinamicos[campo_id] = valor

    def copiar_dados_compartilhados(self, principal: "Participant") -> None:
        """Copia todos os dados compartilhados/globais do participante principal."""
        self.endereco = principal.endereco
        self.data_assinatura = principal.data_assinatura
        self.local_assinatura = principal.local_assinatura
        for chave, valor in principal.campos_dinamicos.items():
            self.campos_dinamicos[chave] = valor

