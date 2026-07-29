"""
Serviço responsável pelas regras de negócio da geração dos documentos:

- Sabe quais campos de cada PDF (PPE / Primeiro Imóvel) devem receber quais
  dados do participante (o "mapeamento" abaixo).
- Sabe que a Declaração PPE precisa da data separada em DIA / MÊS / ANO,
  enquanto a de Primeiro Imóvel usa a data exatamente como digitada.
- Sabe como nomear os arquivos de saída.
- Valida os dados antes de gerar.

A manipulação "mecânica" do PDF (abrir, preencher campos, salvar) fica
inteiramente em `pdf_service.py`. Este arquivo não importa pypdf.
"""

from dataclasses import dataclass, field
from pathlib import Path

from models.participant import Participant
from services.pdf_service import preencher_formulario
from utils.cpf_validator import CpfInvalidoError, formatar_cpf, validar_cpf
from utils.date_formatter import DataInvalidaError, separar_data_por_extenso, validar_data
from utils.filename_utils import nome_documento_individual

# ---------------------------------------------------------------------------
# Mapeamento entre os dados do participante e os nomes dos campos (AcroForm)
# dentro de cada PDF modelo.
#
# Nomes CONFIRMADOS diretamente nos PDFs oficiais fornecidos pela CAIXA
# (app/assets/templates/PPE.pdf e app/assets/templates/1_IMOVEL.pdf), via
# `pdf_service.obter_campos_do_formulario`. Caso a CAIXA emita uma nova versão
# desses formulários com nomes de campo diferentes, ajuste os valores abaixo
# — nenhuma outra parte do sistema precisa ser alterada.
# ---------------------------------------------------------------------------

CAMPO_PRIMEIRO_IMOVEL_NOME = "NOME COMPLETO"
CAMPO_PRIMEIRO_IMOVEL_CPF = "CPF"
CAMPO_PRIMEIRO_IMOVEL_ENDERECO = "ENDERECO"
CAMPO_PRIMEIRO_IMOVEL_DATA = "DATA ASSINATURA"
CAMPO_PRIMEIRO_IMOVEL_LOCAL = "LOCAL ASSINATURA"

CAMPO_PPE_NOME = "NOME COMPLETO"
CAMPO_PPE_CPF = "CPF"
CAMPO_PPE_DIA = "DIA"
CAMPO_PPE_MES = "MES"  # sem acento — confirmado no PDF real da CAIXA (PPE.pdf)
CAMPO_PPE_ANO = "ANO"
CAMPO_PPE_LOCAL = "LOCAL ASSINATURA"


@dataclass
class ResultadoGeracao:
    """Resultado consolidado de uma execução de `gerar_documentos`."""

    arquivos_gerados: list[Path] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def validar_antes_de_gerar(
    participantes: list[Participant],
    caminho_modelo_ppe: Path | None,
    caminho_modelo_primeiro_imovel: Path | None,
    pasta_saida: Path | None,
) -> list[str]:
    """Valida os dados informados antes de iniciar a geração dos documentos.

    Retorna uma lista de mensagens de erro amigáveis. Lista vazia significa
    que está tudo certo para prosseguir.
    """
    erros: list[str] = []

    if not participantes:
        erros.append("Adicione ao menos um participante.")
        return erros

    for indice, participante in enumerate(participantes, start=1):
        if not participante.nome_completo.strip():
            erros.append(f"Participante {indice}: o Nome Completo é obrigatório.")
        if not participante.cpf.strip():
            erros.append(f"Participante {indice}: o CPF é obrigatório.")
        elif not validar_cpf(participante.cpf):
            erros.append(
                f"Participante {indice}: o CPF informado é inválido. "
                f"Verifique os dígitos e tente novamente."
            )

    principal = participantes[0]
    if not principal.endereco.strip():
        erros.append("O Endereço Completo é obrigatório.")
    if not principal.data_assinatura.strip():
        erros.append("A Data da assinatura é obrigatória.")
    elif not validar_data(principal.data_assinatura):
        erros.append(
            "A Data da assinatura é inválida. Utilize o formato DD/MM/AAAA "
            "(ex.: 15/07/2026)."
        )

    if not caminho_modelo_ppe:
        erros.append("Selecione o PDF modelo da Declaração PPE.")
    if not caminho_modelo_primeiro_imovel:
        erros.append("Selecione o PDF modelo da Declaração de Primeiro Imóvel.")
    if not pasta_saida:
        erros.append("Selecione a pasta de saída.")

    return erros


def gerar_documentos(
    participantes: list[Participant],
    caminho_modelo_ppe: Path,
    caminho_modelo_primeiro_imovel: Path,
    pasta_saida: Path,
) -> ResultadoGeracao:
    """Gera os PDFs de Declaração PPE e de Primeiro Imóvel para cada participante.

    Pressupõe que os dados já foram validados com `validar_antes_de_gerar`.
    """
    resultado = ResultadoGeracao()
    nomes_de_arquivo_usados: set[str] = set()
    campos_ausentes_imovel: set[str] = set()
    campos_ausentes_ppe: set[str] = set()

    for participante in participantes:
        # Formata o CPF para o padrão NNN.NNN.NNN-NN
        cpf_formatado = formatar_cpf(participante.cpf)

        # Nome de arquivo padronizado V2 (primeiro nome em maiúsculas)
        nome_imovel = nome_documento_individual("PRIMEIRO IMOVEL", participante.nome_completo)
        nome_ppe = nome_documento_individual("PPE", participante.nome_completo)

        # --- Declaração de Primeiro Imóvel ---
        valores_imovel = {
            CAMPO_PRIMEIRO_IMOVEL_NOME: participante.nome_completo,
            CAMPO_PRIMEIRO_IMOVEL_CPF: cpf_formatado,
            CAMPO_PRIMEIRO_IMOVEL_ENDERECO: participante.endereco,
            CAMPO_PRIMEIRO_IMOVEL_DATA: participante.data_assinatura,
            CAMPO_PRIMEIRO_IMOVEL_LOCAL: participante.local_assinatura,
        }
        caminho_imovel = _proximo_caminho_disponivel(
            pasta_saida, nome_imovel, nomes_de_arquivo_usados
        )
        ausentes = preencher_formulario(caminho_modelo_primeiro_imovel, valores_imovel, caminho_imovel)
        campos_ausentes_imovel.update(ausentes)
        resultado.arquivos_gerados.append(caminho_imovel)

        # --- Declaração PPE ---
        try:
            dia, mes, ano = separar_data_por_extenso(participante.data_assinatura)
        except DataInvalidaError as exc:
            resultado.avisos.append(
                f"Não foi possível gerar a Declaração PPE de "
                f"'{participante.nome_completo}': {exc}"
            )
            continue

        valores_ppe = {
            CAMPO_PPE_NOME: participante.nome_completo,
            CAMPO_PPE_CPF: cpf_formatado,
            CAMPO_PPE_DIA: dia,
            CAMPO_PPE_MES: mes,
            CAMPO_PPE_ANO: ano,
            CAMPO_PPE_LOCAL: participante.local_assinatura,
        }
        caminho_ppe = _proximo_caminho_disponivel(
            pasta_saida, nome_ppe, nomes_de_arquivo_usados
        )
        ausentes = preencher_formulario(caminho_modelo_ppe, valores_ppe, caminho_ppe)
        campos_ausentes_ppe.update(ausentes)
        resultado.arquivos_gerados.append(caminho_ppe)

    if campos_ausentes_imovel:
        resultado.avisos.append(
            "Estes campos não foram encontrados no modelo 'Primeiro Imóvel' "
            "e ficaram em branco: " + ", ".join(sorted(campos_ausentes_imovel))
        )
    if campos_ausentes_ppe:
        resultado.avisos.append(
            "Estes campos não foram encontrados no modelo 'PPE' e ficaram "
            "em branco: " + ", ".join(sorted(campos_ausentes_ppe))
        )

    return resultado


def _proximo_caminho_disponivel(pasta: Path, nome_arquivo: str, usados: set[str]) -> Path:
    """Evita sobrescrever arquivos caso dois participantes gerem o mesmo nome
    (ex.: dois participantes com o mesmo nome completo)."""
    candidato = nome_arquivo
    contador = 2
    caminho_candidato = Path(nome_arquivo)
    while candidato in usados:
        candidato = f"{caminho_candidato.stem} ({contador}){caminho_candidato.suffix}"
        contador += 1
    usados.add(candidato)
    return pasta / candidato
