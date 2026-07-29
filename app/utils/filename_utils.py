"""
Utilitário para geração de nomes de arquivo padronizados a partir dos
nomes dos participantes.

Regras:
- Usar apenas o primeiro nome de cada participante.
- Nomes em MAIÚSCULAS.
- Múltiplos participantes separados por " E ".
- Remover acentos para compatibilidade com Windows.
- Sanitizar caracteres inválidos em nomes de arquivo do Windows.
"""

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.participant import Participant

_CARACTERES_INVALIDOS_ARQUIVO = '<>:"/\\|?*'


def remover_acentos(texto: str) -> str:
    """Remove acentos e diacríticos de uma string.

    Exemplo:
        remover_acentos("João") → "Joao"
        remover_acentos("ÉRICO") → "ERICO"
    """
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _sanitizar_nome_arquivo(nome: str) -> str:
    """Remove caracteres não permitidos em nomes de arquivo no Windows."""
    nome_seguro = "".join(c for c in nome if c not in _CARACTERES_INVALIDOS_ARQUIVO)
    return nome_seguro.strip().rstrip(".")


def extrair_primeiro_nome(nome_completo: str) -> str:
    """Extrai o primeiro nome de um nome completo e retorna em MAIÚSCULAS,
    sem acentos.

    Exemplo:
        extrair_primeiro_nome("Maria da Silva") → "MARIA"
        extrair_primeiro_nome("João Carlos Pereira") → "JOAO"
    """
    partes = nome_completo.strip().split()
    if not partes:
        return "PARTICIPANTE"
    primeiro = partes[0].upper()
    return remover_acentos(primeiro)


def gerar_sufixo_nomes(participantes: list["Participant"]) -> str:
    """Gera o sufixo de nomes para os arquivos do processo.

    Para um participante: "MARIA"
    Para dois: "MARIA E JOAO"
    Para três: "MARIA E JOAO E ANA"

    Os nomes são extraídos a partir do primeiro nome de cada participante,
    em MAIÚSCULAS e sem acentos.
    """
    nomes = []
    nomes_vistos: set[str] = set()

    for p in participantes:
        nome = extrair_primeiro_nome(p.nome_completo)
        # Evitar duplicatas no sufixo
        nome_unico = nome
        contador = 2
        while nome_unico in nomes_vistos:
            nome_unico = f"{nome}{contador}"
            contador += 1
        nomes_vistos.add(nome_unico)
        nomes.append(nome_unico)

    return " E ".join(nomes) if nomes else "PARTICIPANTE"


def nome_documento_processo(tipo: str, participantes: list["Participant"]) -> str:
    """Gera o nome padronizado de um documento do processo.

    Args:
        tipo: tipo do documento (ex: "CONTRATO", "PLANILHA DE EVOLUCAO").
        participantes: lista de participantes do processo.

    Returns:
        Nome do arquivo com extensão .pdf.
        Ex: "CONTRATO MARIA E JOAO.pdf"
    """
    sufixo = gerar_sufixo_nomes(participantes)
    nome = f"{tipo} {sufixo}.pdf"
    return _sanitizar_nome_arquivo(nome)


def nome_documento_individual(tipo: str, nome_completo: str) -> str:
    """Gera o nome padronizado de um documento individual (por participante).

    Args:
        tipo: tipo do documento (ex: "PPE", "PRIMEIRO IMOVEL").
        nome_completo: nome completo do participante.

    Returns:
        Nome do arquivo com extensão .pdf.
        Ex: "PPE - MARIA.pdf"
    """
    primeiro_nome = extrair_primeiro_nome(nome_completo)
    nome = f"{tipo} - {primeiro_nome}.pdf"
    return _sanitizar_nome_arquivo(nome)
