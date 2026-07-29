"""
Serviço responsável pela criação e gerenciamento da estrutura de pastas
de um processo/cliente.

Estrutura criada automaticamente:
    <pasta_base>/
    └── PDF-A/
        └── ASSINADOS/
            └── REGISTRADOS/
"""

from pathlib import Path


class ProcessFolderError(Exception):
    """Erro relacionado à criação ou acesso das pastas do processo."""


def criar_estrutura_pastas(pasta_base: Path) -> Path:
    """Cria a estrutura hierárquica de pastas do processo.

    Verifica se já existe uma pasta 'PDFA' ou 'PDF-A'. Se 'PDFA' existir,
    reaproveita ela. Caso contrário, usa/cria 'PDF-A'.
    Cria a hierarquia: PDF-A → ASSINADOS → REGISTRADOS.

    Args:
        pasta_base: caminho da pasta raiz do processo/cliente.

    Returns:
        O caminho da pasta principal criada/utilizada.

    Raises:
        ProcessFolderError: se não for possível criar as pastas.
    """
    try:
        pasta_pdfa_sem_traco = pasta_base / "PDFA"
        pasta_pdfa_com_traco = pasta_base / "PDF-A"
        
        if pasta_pdfa_sem_traco.exists():
            pasta_principal = pasta_pdfa_sem_traco
        else:
            pasta_principal = pasta_pdfa_com_traco

        pasta_assinados = pasta_principal / "ASSINADOS"
        pasta_registrados = pasta_assinados / "REGISTRADOS"

        pasta_principal.mkdir(parents=True, exist_ok=True)
        pasta_assinados.mkdir(exist_ok=True)
        pasta_registrados.mkdir(exist_ok=True)

        return pasta_principal
    except OSError as exc:
        raise ProcessFolderError(
            f"Não foi possível criar a estrutura de pastas em '{pasta_base}': {exc}"
        ) from exc


def caminho_pasta_pdfa(pasta_base: Path) -> Path:
    """Retorna o caminho da pasta PDF-A (ou PDFA) dentro da pasta-base do processo."""
    pasta_pdfa_sem_traco = pasta_base / "PDFA"
    if pasta_pdfa_sem_traco.exists():
        return pasta_pdfa_sem_traco
    return pasta_base / "PDF-A"
