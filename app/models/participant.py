"""
Modelo de dados que representa um participante (comprador) do contrato
habitacional.

Este módulo não contém nenhuma lógica de interface ou de manipulação de
PDF — apenas a estrutura de dados e regras mínimas que dizem respeito
exclusivamente ao próprio participante.
"""

from dataclasses import dataclass


@dataclass
class Participant:
    """Dados de um participante do contrato habitacional."""

    nome_completo: str = ""
    cpf: str = ""
    endereco: str = ""
    data_assinatura: str = ""  # Sempre no formato DD/MM/AAAA, exatamente como digitado.
    local_assinatura: str = "CAMOCIM-CE"  # Município/UF onde o contrato será assinado.

    def copiar_dados_compartilhados(self, principal: "Participant") -> None:
        """
        Copia o endereço, a data e o local de assinatura do participante principal.

        Regra de negócio (ver especificação): a partir do 2º participante,
        o endereço, a data e o local da assinatura não são digitados novamente
        — eles sempre repetem os valores do participante principal (o primeiro).
        """
        self.endereco = principal.endereco
        self.data_assinatura = principal.data_assinatura
        self.local_assinatura = principal.local_assinatura

