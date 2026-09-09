"""Reúne os requisitos de vários perfis selecionados no modo básico."""

import copy
from dataclasses import dataclass

from utils.profile_manager import CampoEntrada, Perfil


@dataclass
class ResultadoComposicao:
    perfil: Perfil | None
    erros: list[str]


def limite_participantes_para_pagina(perfis: list[Perfil], pagina: str | None = None) -> int:
    """Resolve quantos proponentes se aplicam ao formulário da página atual."""
    if not perfis:
        return 1

    if pagina and " • " in pagina:
        nome_formulario = pagina.split(" • ", 1)[0]
        perfil_pagina = next((perfil for perfil in perfis if perfil.nome == nome_formulario), None)
        if perfil_pagina is not None:
            return max(1, perfil_pagina.max_participantes)

    if len(perfis) == 1:
        return max(1, perfis[0].max_participantes)
    return max(1, max(perfil.max_participantes for perfil in perfis))


def _unir_condicoes(
    primeira: list[dict[str, list[str]]],
    segunda: list[dict[str, list[str]]],
) -> list[dict[str, list[str]]]:
    if not primeira or not segunda:
        return []
    resultado = copy.deepcopy(primeira)
    for alternativa in segunda:
        if alternativa not in resultado:
            resultado.append(copy.deepcopy(alternativa))
    return resultado


def _unir_campo(atual: CampoEntrada, novo: CampoEntrada) -> str | None:
    if atual.escopo != novo.escopo:
        return "é usado uma vez em um perfil e por participante em outro"
    if atual.tipo != novo.tipo:
        return f"usa os tipos {atual.tipo} e {novo.tipo}"

    atual.obrigatorio = atual.obrigatorio or novo.obrigatorio
    atual.opcoes = list(dict.fromkeys([*atual.opcoes, *novo.opcoes]))
    atual.visivel_quando = _unir_condicoes(atual.visivel_quando, novo.visivel_quando)
    atual.limpar_quando_oculto = atual.limpar_quando_oculto and novo.limpar_quando_oculto

    limites = [valor for valor in (atual.ate_participante, novo.ate_participante) if valor]
    atual.ate_participante = max(limites) if limites else None

    if atual.minimo is None:
        atual.minimo = novo.minimo
    elif novo.minimo is not None:
        atual.minimo = max(atual.minimo, novo.minimo)
    if atual.maximo is None:
        atual.maximo = novo.maximo
    elif novo.maximo is not None:
        atual.maximo = min(atual.maximo, novo.maximo)
    if atual.minimo is not None and atual.maximo is not None and atual.minimo > atual.maximo:
        return "possui limites numéricos incompatíveis"

    if atual.calculo and novo.calculo and atual.calculo != novo.calculo:
        return "possui cálculos automáticos diferentes"
    if not atual.calculo:
        atual.calculo = novo.calculo
    return None


def combinar_perfis(perfis: list[Perfil]) -> ResultadoComposicao:
    """Cria a tela combinada sem alterar os perfis originais."""
    if not perfis:
        return ResultadoComposicao(None, ["Selecione ao menos um formulário."])

    campos: list[CampoEntrada] = []
    campos_por_id: dict[str, CampoEntrada] = {}
    erros: list[str] = []
    agrupamento_paginas: dict[str, str] = {}

    separar_por_formulario = len(perfis) > 1
    for perfil in perfis:
        for campo_original in perfil.campos_entrada:
            campo = copy.deepcopy(campo_original)
            if separar_por_formulario:
                nome_secao = campo.aba.strip() if campo.aba else "Geral"
                campo.aba = f"{perfil.nome} • {nome_secao}"
                pagina = perfil.obter_pagina_do_campo(campo_original)
                agrupamento_paginas[campo.aba] = f"{perfil.nome} • {pagina}"
            if campo.escopo == "participante":
                campo.ate_participante = campo.ate_participante or perfil.max_participantes

            existente = campos_por_id.get(campo.id)
            if existente is None:
                campos_por_id[campo.id] = campo
                campos.append(campo)
                continue
            motivo = _unir_campo(existente, campo)
            if motivo:
                erros.append(
                    f"O campo interno '{campo.id}' {motivo}. "
                    "Altere um dos nomes internos nas configurações dos perfis."
                )

    if erros:
        return ResultadoComposicao(None, list(dict.fromkeys(erros)))

    nomes = [perfil.nome for perfil in perfis]
    perfil_combinado = Perfil(
        nome=nomes[0] if len(nomes) == 1 else f"{len(nomes)} formulários selecionados",
        formularios=[copy.deepcopy(formulario) for perfil in perfis for formulario in perfil.formularios],
        documentos_extras=[],
        campos_entrada=campos,
        formato_saida="PDF",
        modo_fluxo="formulario_simples",
        max_participantes=max(perfil.max_participantes for perfil in perfis),
        usar_paginacao=any(perfil.usar_paginacao for perfil in perfis) or len(perfis) > 1,
        agrupamento_paginas=(
            agrupamento_paginas if separar_por_formulario
            else dict(perfis[0].agrupamento_paginas)
        ),
    )
    return ResultadoComposicao(perfil_combinado, [])
