"""
Serviço responsável pelas regras de negócio da geração dos documentos:

- Gerencia quais campos de cada formulário PDF devem receber os dados dos participantes.
- Formata datas e campos específicos conforme a especificação de cada modelo.
- Padroniza a nomenclatura dos arquivos gerados.
- Valida os dados antes da execução.

A manipulação de baixo nível do PDF (abrir, preencher campos, salvar) fica
inteiramente em `pdf_service.py`.
"""

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from models.participant import Participant
from services.pdf_service import carregar_template_reader, preencher_formulario
from services.pdfa_converter import ProcessoCanceladoError
from utils.cpf_validator import formatar_cpf, validar_cpf
from utils.date_formatter import DataInvalidaError, separar_data_por_extenso, validar_data
from utils.filename_utils import nome_documento_individual
from utils.profile_manager import Perfil


from utils.resource_path import modelo_padrao_ppe, modelo_padrao_primeiro_imovel, modelo_padrao_formulario_caixa
from utils.filename_utils import nome_documento_individual, nome_documento_processo


@dataclass
class ResultadoGeracao:
    """Resultado consolidado de uma execução de `gerar_documentos`."""
    arquivos_gerados: list[Path] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


_caminho_modelo_cache: dict[tuple[str, str], Path | None] = {}


def resolver_caminho_formulario(f) -> Path | None:
    """Resolve o caminho de um formulário com cache em memória."""
    key = (getattr(f, "nome", ""), getattr(f, "caminho", ""))
    if key in _caminho_modelo_cache:
        return _caminho_modelo_cache[key]

    caminho_resolvido: Path | None = None
    if f.caminho and Path(f.caminho).exists():
        caminho_resolvido = Path(f.caminho)
    else:
        nome = f.nome.lower()
        if "ppe" in nome:
            caminho_resolvido = modelo_padrao_ppe()
        elif "imóvel" in nome or "imovel" in nome or "1" in nome:
            caminho_resolvido = modelo_padrao_primeiro_imovel()
        elif "caixa" in nome or "30844" in nome or "30.844" in nome or "mo" in nome or "cliente" in nome:
            caminho_resolvido = modelo_padrao_formulario_caixa()

    _caminho_modelo_cache[key] = caminho_resolvido
    return caminho_resolvido


def mapeamento_padrao_mo30844011() -> dict[str, str]:
    """Mapeamento padrão oficial para o formulário CAIXA MO 30.844 v011."""
    return {
        "NOME_CLIENTE_1": "participante.1.nome_completo",
        "CPF1": "participante.1.cpf_formatado",
        "AGENCIA": "global.agencia",
        "CONTA_CAIXA": "global.conta_caixa",
        "checkbox_AUTORIZO_PARCELA": "global.checkbox_autorizo_parcela",
        "checkbox_GARANTIA": "global.checkbox_garantia",
        "NOMEPROP1PROPOSTA": "participante.1.nome_completo",
        "CPFPROP1": "participante.1.cpf_formatado",
        "NOMEPROP2PROPOSTA": "participante.2.nome_completo",
        "CPFPROP2": "participante.2.cpf_formatado",
        "NOMEPROP3PROPOSTA": "participante.3.nome_completo",
        "CPFPROP3": "participante.3.cpf_formatado",
        "NOMEPROP4PROPOSTA": "participante.4.nome_completo",
        "CPFPROP4": "participante.4.cpf_formatado",
        "MIP1": "participante.1.mip",
        "MIP2": "participante.2.mip",
        "MIP3": "participante.3.mip",
        "MIP4": "participante.4.mip",
        "LOCAL": "participante.local_assinatura",
        "DATA DD/MM/AAAA": "participante.data_assinatura",
        "PARTICIP1NOME": "participante.1.nome_completo",
        "PARTICIP1CPF": "participante.1.cpf_formatado",
        "PARTICIP2NOME": "participante.2.nome_completo",
        "PARTICIP2CPF": "participante.2.cpf_formatado",
        "PARTICIP3NOME": "participante.3.nome_completo",
        "PARTICIP3CPF": "participante.3.cpf_formatado",
        "PARTICIP4NOME": "participante.4.nome_completo",
        "PARTICIP4CPF": "participante.4.cpf_formatado",
    }


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
    elif "caixa" in nome or "30844" in nome or "30.844" in nome or "mo" in nome or "cliente" in nome:
        return mapeamento_padrao_mo30844011()

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


def resolver_variavel(
    mapeamento_str: str,
    participante: Participant,
    todos_participantes: Optional[list[Participant]] = None,
) -> str:
    """Resolve uma string de mapeamento (ex: 'participante.nome_completo') para o valor real."""
    if not mapeamento_str:
        return ""
        
    try:
        cpf_formatado = formatar_cpf(participante.cpf) if participante.cpf else ""
    except Exception:
        cpf_formatado = participante.cpf
    
    # Extração de data de assinatura se disponível
    data_raw = participante.data_assinatura or str(participante.campos_dinamicos.get("data_assinatura", ""))
    try:
        dia, mes, ano = separar_data_por_extenso(data_raw)
    except DataInvalidaError:
        dia, mes, ano = "", "", ""

    # Dicionário base de variáveis padrão
    variaveis = {
        "participante.nome_completo": participante.nome_completo,
        "participante.nome": participante.nome_completo,
        "participante.cpf": participante.cpf,
        "participante.cpf_formatado": cpf_formatado,
        "participante.endereco": participante.endereco,
        "participante.data_assinatura": participante.data_assinatura,
        "participante.local_assinatura": participante.local_assinatura,
        "data.dia": dia,
        "data.mes": mes,
        "data.ano": ano,
    }

    # Suporte a CNPJ (se informado)
    cnpj_raw = participante.obter_campo("cnpj", "")
    if cnpj_raw:
        try:
            from utils.cnpj_validator import formatar_cnpj
            cnpj_fmt = formatar_cnpj(cnpj_raw)
        except Exception:
            cnpj_fmt = cnpj_raw
        variaveis["participante.cnpj"] = cnpj_raw
        variaveis["participante.cnpj_formatado"] = cnpj_fmt
        variaveis["cnpj"] = cnpj_raw
        variaveis["cnpj_formatado"] = cnpj_fmt

    # Inclusão dinâmica de todos os campos personalizados
    for campo_id, valor in participante.campos_dinamicos.items():
        str_val = str(valor)
        variaveis[f"participante.{campo_id}"] = str_val
        variaveis[f"global.{campo_id}"] = str_val
        variaveis[campo_id] = str_val

        # Se for campo de data, tentar desmembrar dia/mês/ano
        if "/" in str_val and len(str_val) == 10:
            try:
                d_dia, d_mes, d_ano = separar_data_por_extenso(str_val)
                variaveis[f"{campo_id}.dia"] = d_dia
                variaveis[f"{campo_id}.mes"] = d_mes
                variaveis[f"{campo_id}.ano"] = d_ano
            except Exception:
                pass
        # Se for campo de CNPJ dinâmico, gerar versão formatada
        elif ("cnpj" in campo_id.lower()) and len(str_val.replace(".", "").replace("/", "").replace("-", "")) == 14:
            try:
                from utils.cnpj_validator import formatar_cnpj
                variaveis[f"{campo_id}_formatado"] = formatar_cnpj(str_val)
                variaveis[f"participante.{campo_id}_formatado"] = formatar_cnpj(str_val)
            except Exception:
                pass

    # Suporte a múltiplos participantes indexados (ex: participante.1.nome_completo, participante.2.cpf_formatado, etc.)
    lista_parts = todos_participantes if todos_participantes else [participante]
    for idx in range(1, 5):
        if idx <= len(lista_parts):
            p_idx = lista_parts[idx - 1]
            try:
                p_cpf_fmt = formatar_cpf(p_idx.cpf) if p_idx.cpf else ""
            except Exception:
                p_cpf_fmt = p_idx.cpf
            variaveis[f"participante.{idx}.nome_completo"] = p_idx.nome_completo
            variaveis[f"participante.{idx}.nome"] = p_idx.nome_completo
            variaveis[f"participante.{idx}.cpf"] = p_idx.cpf
            variaveis[f"participante.{idx}.cpf_formatado"] = p_cpf_fmt
            variaveis[f"participante.{idx}.mip"] = "/Yes_uonn"
            variaveis[f"participante.{idx}.endereco"] = p_idx.endereco
            for cid, cval in p_idx.campos_dinamicos.items():
                variaveis[f"participante.{idx}.{cid}"] = str(cval)
        else:
            variaveis[f"participante.{idx}.nome_completo"] = ""
            variaveis[f"participante.{idx}.nome"] = ""
            variaveis[f"participante.{idx}.cpf"] = ""
            variaveis[f"participante.{idx}.cpf_formatado"] = ""
            variaveis[f"participante.{idx}.mip"] = ""
            variaveis[f"participante.{idx}.endereco"] = ""

    # Resolução de checkboxes com nomes técnicos ou globais
    val_debito_parcela = str(participante.obter_campo("autorizo_debito_parcela", "Sim")).lower()
    chk_parcela = "/Yes_uonn" if val_debito_parcela in ("sim", "true", "1", "yes", "") else "/Off"
    variaveis["global.checkbox_autorizo_parcela"] = chk_parcela
    variaveis["checkbox_autorizo_parcela"] = chk_parcela
    variaveis["checkbox_AUTORIZO_PARCELA"] = chk_parcela

    val_tarifa_aval = str(participante.obter_campo("autorizo_tarifa_avaliacao", "Não")).lower()
    chk_garantia = "/Yes_uonn" if val_tarifa_aval in ("sim", "true", "1", "yes") else "/Off"
    variaveis["global.checkbox_garantia"] = chk_garantia
    variaveis["checkbox_garantia"] = chk_garantia
    variaveis["checkbox_GARANTIA"] = chk_garantia

    # Retorna o valor mapeado ou a própria string literal caso não seja uma variável conhecida
    return variaveis.get(mapeamento_str, mapeamento_str)


def gerar_documentos(
    participantes: list[Participant],
    perfil: Perfil,
    pasta_saida: Path,
    formularios_ativos: Optional[list[str] | set[str]] = None,
    cancel_event: Optional[threading.Event] = None,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> ResultadoGeracao:
    """Gera os PDFs configurados no Perfil dinamicamente."""
    resultado = ResultadoGeracao()
    nomes_de_arquivo_usados: set[str] = set()

    formularios_para_gerar = [
        f for f in perfil.formularios 
        if formularios_ativos is None or f.nome in formularios_ativos
    ]

    total_formularios = len(formularios_para_gerar)

    for idx, formulario in enumerate(formularios_para_gerar, start=1):
        if cancel_event is not None and cancel_event.is_set():
            raise ProcessoCanceladoError("Operação cancelada pelo usuário.")

        if on_progress:
            on_progress(idx, total_formularios, formulario.nome)

        campos_ausentes_form: set[str] = set()
        caminho_modelo = resolver_caminho_formulario(formulario)

        if not caminho_modelo or not caminho_modelo.exists():
            resultado.avisos.append(f"Modelo '{formulario.nome}' não foi encontrado e foi ignorado.")
            continue

        mapeamento = obter_mapeamento_formulario(formulario)
        
        # Decide se gera 1 para todos ou 1 para cada participante
        is_por_processo = (formulario.geracao == "por_processo")
        alvos = [participantes[0]] if is_por_processo else participantes
        
        try:
            reader_modelo = carregar_template_reader(caminho_modelo)
        except Exception:
            reader_modelo = None

        for participante in alvos:
            if cancel_event is not None and cancel_event.is_set():
                raise ProcessoCanceladoError("Operação cancelada pelo usuário.")

            # Constrói o dicionário de valores baseado no mapeamento do formulário
            valores_pdf = {}
            for campo_pdf, var_sistema in mapeamento.items():
                valores_pdf[campo_pdf] = resolver_variavel(
                    var_sistema,
                    participante,
                    todos_participantes=participantes if is_por_processo else None,
                )
                
            if is_por_processo:
                nome_arquivo = nome_documento_processo(formulario.nome, participantes)
            else:
                nome_arquivo = nome_documento_individual(formulario.nome, participante.nome_completo)

            caminho_saida = _proximo_caminho_disponivel(pasta_saida, nome_arquivo, nomes_de_arquivo_usados)
            
            ausentes = preencher_formulario(caminho_modelo, valores_pdf, caminho_saida, reader=reader_modelo)
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
