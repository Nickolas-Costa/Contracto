"""Confere a ligação entre uma configuração de perfil e os campos de um PDF."""

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image


@dataclass
class ResultadoConferencia:
    ligados: list[str] = field(default_factory=list)
    sem_ligacao: list[str] = field(default_factory=list)
    nao_encontrados: list[str] = field(default_factory=list)
    estados_invalidos: list[str] = field(default_factory=list)


def conferir_mapeamento(
    campos_pdf: dict[str, dict[str, object]],
    mapeamento: dict[str, str | dict],
) -> ResultadoConferencia:
    """Separa os campos por situação sem depender da interface gráfica."""
    nomes_pdf = set(campos_pdf)
    nomes_mapeados = set(mapeamento)
    encontrados = sorted(nomes_pdf & nomes_mapeados)
    estados_invalidos: list[str] = []

    for nome in encontrados:
        regra = mapeamento.get(nome)
        if not isinstance(regra, dict) or "valor_verdadeiro" not in regra:
            continue
        esperado = str(regra.get("valor_verdadeiro", ""))
        detalhes = campos_pdf.get(nome, {})
        estados = [str(valor) for valor in detalhes.get("estados", []) or []]
        if esperado and detalhes.get("tipo") == "/Btn" and esperado not in estados:
            estados_invalidos.append(nome)

    invalidos = set(estados_invalidos)
    return ResultadoConferencia(
        ligados=[nome for nome in encontrados if nome not in invalidos],
        sem_ligacao=sorted(nomes_pdf - nomes_mapeados),
        nao_encontrados=sorted(nomes_mapeados - nomes_pdf),
        estados_invalidos=estados_invalidos,
    )


def renderizar_pagina_destacada(
    caminho_pdf: Path,
    pagina: int,
    conferencia: ResultadoConferencia,
    largura_maxima: int = 620,
    altura_maxima: int = 650,
) -> tuple[Image.Image, int]:
    """Renderiza uma página e contorna os campos conforme a conferência."""
    import fitz

    cores = {
        **{nome: (0.10, 0.62, 0.35) for nome in conferencia.ligados},
        **{nome: (0.92, 0.60, 0.08) for nome in conferencia.sem_ligacao},
        **{nome: (0.82, 0.18, 0.18) for nome in conferencia.estados_invalidos},
    }
    with fitz.open(caminho_pdf) as documento:
        total = len(documento)
        if total < 1:
            raise ValueError("O PDF não possui páginas para exibir.")
        indice = max(0, min(pagina, total - 1))
        pagina_pdf = documento[indice]
        for widget in pagina_pdf.widgets() or []:
            cor = cores.get(widget.field_name)
            if cor:
                pagina_pdf.draw_rect(widget.rect, color=cor, width=2.2, overlay=True)

        proporcao = min(
            largura_maxima / pagina_pdf.rect.width,
            altura_maxima / pagina_pdf.rect.height,
        )
        matriz = fitz.Matrix(max(proporcao, 0.5), max(proporcao, 0.5))
        imagem = pagina_pdf.get_pixmap(matrix=matriz, alpha=False)
        pil = Image.frombytes("RGB", (imagem.width, imagem.height), imagem.samples)
        return pil, total
