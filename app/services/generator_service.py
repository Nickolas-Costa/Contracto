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
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.date_formatter import DataInvalidaError, separar_data_por_extenso, validar_data
from utils.filename_utils import nome_documento_individual
from utils.profile_manager import Perfil


from utils.resource_path import modelo_padrao_ppe, modelo_padrao_primeiro_imovel


@dataclass
class ResultadoGeracao:
    """Resultado consolidado de uma execução de `gerar_documentos`."""
    arquivos_gerados: list[Path] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def resolver_caminho_formulario(f) -> Path | None:
    """Resolve o caminho de um formulário.
    
    Se `f.caminho` estiver preenchido e existir no disco, retorna ele.
    Se `f.caminho` estiver vazio (Perfil Padrão), resolve para o modelo oficial embutido em assets/templates/.
    """
    if f.caminho and Path(f.caminho).exists():
        return Path(f.caminho)

    nome = f.nome.lower()
    if "ppe" in nome:
        return modelo_padrao_ppe()
    elif "imóvel" in nome or "imovel" in nome or "1" in nome:
        return modelo_padrao_primeiro_imovel()

    return None


def obter_mapeamento_formulario(f) -> dict[str, str]:
    """Retorna o mapeamento de campos do formulário, ou o mapeamento padrão caso esteja vazio."""
    if f.mapeamento:
        return f.mapeamento

    nome = f.nome.lower()
    if "ppe" in nome:
        return {
            "NOME COMPLETO": "participante.nome_completo",
            "CPF": "participante.cpf_formatado",
            "DIA": "data.dia",
            "MES": "data.mes",
            "ANO": "data.ano",
            "LOCAL ASSINATURA": "participante.local_assinatura",
        }
    elif "imóvel" in nome or "imovel" in nome or "1" in nome:
        return {
            "NOME COMPLETO": "participante.nome_completo",
            "CPF": "participante.cpf_formatado",
            "ENDERECO": "participante.endereco",
            "DATA ASSINATURA": "participante.data_assinatura",
            "LOCAL ASSINATURA": "participante.local_assinatura",
        }

    return {}


def validar_antes_de_gerar(
    participantes: list[Participant],
    perfil: Perfil,
    pasta_saida: Path | None,
) -> list[str]:
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

    if not perfil.formularios:
        erros.append(f"O perfil '{perfil.nome}' não possui nenhum formulário configurado.")
    else:
        for f in perfil.formularios:
            caminho_resolvido = resolver_caminho_formulario(f)
            if not caminho_resolvido or not caminho_resolvido.exists():
                erros.append(f"O formulário '{f.nome}' aponta para um arquivo inexistente.")

    if not pasta_saida:
        erros.append("Selecione a pasta de saída.")

    return erros


def resolver_variavel(mapeamento_str: str, participante: Participant) -> str:
    """Resolve uma string de mapeamento (ex: 'participante.nome_completo') para o valor real."""
    if not mapeamento_str:
        return ""
        
    cpf_formatado = formatar_cpf(participante.cpf)
    
    try:
        dia, mes, ano = separar_data_por_extenso(participante.data_assinatura)
    except DataInvalidaError:
        dia, mes, ano = "", "", ""

    # Dicionário de variáveis disponíveis
    variaveis = {
        "participante.nome_completo": participante.nome_completo,
        "participante.cpf": participante.cpf,
        "participante.cpf_formatado": cpf_formatado,
        "participante.endereco": participante.endereco,
        "participante.data_assinatura": participante.data_assinatura,
        "participante.local_assinatura": participante.local_assinatura,
        "data.dia": dia,
        "data.mes": mes,
        "data.ano": ano,
    }
    
    # Retorna o valor mapeado ou a própria string literal caso não seja uma variável conhecida
    return variaveis.get(mapeamento_str, mapeamento_str)


def gerar_documentos(
    participantes: list[Participant],
    perfil: Perfil,
    pasta_saida: Path,
) -> ResultadoGeracao:
    """Gera os PDFs configurados no Perfil dinamicamente."""
    resultado = ResultadoGeracao()
    nomes_de_arquivo_usados: set[str] = set()

    for formulario in perfil.formularios:
        campos_ausentes_form: set[str] = set()
        caminho_modelo = resolver_caminho_formulario(formulario)

        if not caminho_modelo or not caminho_modelo.exists():
            resultado.avisos.append(f"Modelo '{formulario.nome}' não foi encontrado e foi ignorado.")
            continue

        mapeamento = obter_mapeamento_formulario(formulario)
        
        # Decide se gera 1 para todos ou 1 para cada participante
        alvos = participantes if formulario.geracao == "por_participante" else [participantes[0]]
        
        for participante in alvos:
            # Constrói o dicionário de valores baseado no mapeamento do formulário
            valores_pdf = {}
            for campo_pdf, var_sistema in mapeamento.items():
                valores_pdf[campo_pdf] = resolver_variavel(var_sistema, participante)
                
            nome_arquivo = nome_documento_individual(formulario.nome, participante.nome_completo if formulario.geracao == "por_participante" else "")
            caminho_saida = _proximo_caminho_disponivel(pasta_saida, nome_arquivo, nomes_de_arquivo_usados)
            
            ausentes = preencher_formulario(caminho_modelo, valores_pdf, caminho_saida)
            campos_ausentes_form.update(ausentes)
            resultado.arquivos_gerados.append(caminho_saida)
            
        if campos_ausentes_form:
            resultado.avisos.append(
                f"Estes campos não foram encontrados no modelo '{formulario.nome}' "
                f"e ficaram em branco: " + ", ".join(sorted(campos_ausentes_form))
            )

    return resultado


def _proximo_caminho_disponivel(pasta: Path, nome_arquivo: str, usados: set[str]) -> Path:
    candidato = nome_arquivo
    contador = 2
    caminho_candidato = Path(nome_arquivo)
    while candidato in usados:
        candidato = f"{caminho_candidato.stem} ({contador}){caminho_candidato.suffix}"
        contador += 1
    usados.add(candidato)
    return pasta / candidato
