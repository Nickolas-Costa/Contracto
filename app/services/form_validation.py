"""Validação declarativa reutilizável sem widgets, para clientes HTTP."""
import copy
import re
from decimal import Decimal, InvalidOperation

from services.field_calculator import calcular
from utils.cnpj_validator import validar_cnpj
from utils.cpf_validator import validar_cpf
from utils.date_formatter import validar_data
from utils.document_validator import validar_cpf_ou_cnpj, validar_email, validar_telefone
from utils.pis_pasep_validator import validar_pis_pasep
from utils.profile_manager import ordenar_campos_para_exibicao


def valor_valido(campo, valor):
    value = str(valor).strip()
    kind = campo.tipo.upper()
    if not value:
        return not campo.obrigatorio or kind == "CHECKBOX"
    if kind == "CPF":
        return validar_cpf(value)
    if kind == "CNPJ":
        return validar_cnpj(value)
    if kind == "CPF_CNPJ":
        return validar_cpf_ou_cnpj(value)[0]
    if kind == "PIS_PASEP":
        return validar_pis_pasep(value)
    if kind == "DATA":
        return validar_data(value)
    if kind in {"INTEIRO", "ANO"}:
        return (value.isascii() and value.isdigit() and (kind != "ANO" or len(value) == 4)
                and (campo.minimo is None or int(value) >= campo.minimo)
                and (campo.maximo is None or int(value) <= campo.maximo))
    if kind == "SELECAO":
        return value in campo.opcoes or (
            kind == "SELECAO" and value.upper() in (o.upper() for o in campo.opcoes))
    if kind == "CHECKBOX":
        return value in (campo.opcoes or ["SIM", "NÃO"])
    if kind in {"MOEDA", "AREA"}:
        try:
            text = value.replace("R$", "").replace(" ", "")
            if "," in text:
                text = text.replace(".", "").replace(",", ".")
            number = Decimal(text)
            return number.is_finite() and number >= 0
        except InvalidOperation:
            return False
    if kind == "TELEFONE" or "telefone" in campo.id.lower():
        return validar_telefone(value)
    if kind == "EMAIL" or "email" in campo.id.lower():
        return validar_email(value)
    return True


def preparar_participantes(participantes, perfil):
    """Aplica defaults, escopos, condições e cálculos antes de validar.

    Retorna cópias e índices/IDs dos campos inválidos, sem seus valores.
    """
    result = copy.deepcopy(participantes)
    errors = []
    fields = ordenar_campos_para_exibicao(perfil.campos_entrada)
    def visible(field, participant, index):
        if field.ate_participante and index > field.ate_participante:
            return False
        return not field.visivel_quando or any(
            all(str(participant.obter_campo(key, "")) in accepted for key, accepted in condition.items())
            for condition in field.visivel_quando)
    for index, participant in enumerate(result, 1):
        for field in fields:
            source = result[0] if field.escopo == "global" else participant
            value = source.obter_campo(field.id, "")
            if value == "":
                value = field.valor_padrao
            if field.tipo == "CHECKBOX":
                options = field.opcoes or ["SIM", "NÃO"]
                if isinstance(value, bool):
                    value = options[0] if value else options[-1]
                elif value == "":
                    value = options[-1]
                # Normaliza o case para os valores canônicos.
                elif value not in options and any(v.upper() == value.upper() for v in options):
                    match = next(v for v in options if v.upper() == value.upper())
                    participant.definir_campo(field.id, match)
                    continue
            participant.definir_campo(field.id, value)
        # Valores ocultos não podem alimentar cálculos com dados forjados.
        for field in fields:
            if not visible(field, participant, index) and field.limpar_quando_oculto:
                participant.definir_campo(field.id, "")
        pending = {f.id: f for f in fields if f.calculo}
        while pending:
            ready = [f for f in pending.values()
                     if not (set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", f.calculo)) & pending.keys())]
            if not ready:
                errors.extend({"participant": index, "field": key} for key in pending)
                break
            for field in ready:
                if visible(field, participant, index):
                    values = {f.id: participant.obter_campo(f.id, "") for f in fields}
                    participant.definir_campo(field.id, calcular(field.calculo, values))
                del pending[field.id]
        for field in fields:
            if field.ate_participante and index > field.ate_participante:
                participant.definir_campo(field.id, "")
                continue
            if not visible(field, participant, index):
                if field.limpar_quando_oculto:
                    participant.definir_campo(field.id, "")
                continue
            if not valor_valido(field, participant.obter_campo(field.id, "")):
                errors.append({"participant": index, "field": field.id})
    return result, errors
