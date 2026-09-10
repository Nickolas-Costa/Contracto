"""Confere a ligação entre uma configuração de perfil e os campos de um PDF."""

from dataclasses import dataclass, field
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


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


def retangulos_dos_campos(caminho_pdf: Path, pagina: int) -> dict[str, tuple[float, float, float, float]]:
    """Retângulos dos widgets AcroForm da página (coordenadas PDF, origem inferior-esquerda)."""
    from pypdf import PdfReader

    leitor = PdfReader(str(caminho_pdf))
    paginas = leitor.pages
    if not paginas:
        raise ValueError("O PDF não possui páginas para exibir.")
    indice = max(0, min(pagina, len(paginas) - 1))
    retangulos: dict[str, tuple[float, float, float, float]] = {}
    for anotacao in paginas[indice].get("/Annots", []) or []:
        widget = anotacao.get_object()
        nome = widget.get("/T")
        ret = widget.get("/Rect")
        if nome and ret and len(ret) == 4:
            retangulos[str(nome)] = tuple(float(v) for v in ret)
    return retangulos


def renderizar_pagina_destacada(
    caminho_pdf: Path,
    pagina: int,
    conferencia: ResultadoConferencia,
    largura_maxima: int = 620,
    altura_maxima: int = 650,
) -> tuple[Image.Image, int]:
    """Renderiza uma página e contorna os campos conforme a conferência."""
    cores = {
        **{nome: (26, 158, 89) for nome in conferencia.ligados},
        **{nome: (235, 153, 20) for nome in conferencia.sem_ligacao},
        **{nome: (209, 46, 46) for nome in conferencia.estados_invalidos},
    }
    documento = pdfium.PdfDocument(str(caminho_pdf))
    try:
        total = len(documento)
        if total < 1:
            raise ValueError("O PDF não possui páginas para exibir.")
        indice = max(0, min(pagina, total - 1))
        pagina_pdf = documento[indice]
        largura_pt, altura_pt = pagina_pdf.get_size()
        proporcao = min(
            largura_maxima / largura_pt,
            altura_maxima / altura_pt,
        )
        escala = max(proporcao, 0.5)
        imagem = pagina_pdf.render(scale=escala).to_pil().convert("RGB")

        desenho = ImageDraw.Draw(imagem)
        espessura = max(2, round(2.2 * escala))
        for nome, (x0, y0, x1, y1) in retangulos_dos_campos(caminho_pdf, indice).items():
            cor = cores.get(nome)
            if not cor:
                continue
            desenho.rectangle(
                [x0 * escala, (altura_pt - y1) * escala,
                 x1 * escala, (altura_pt - y0) * escala],
                outline=cor,
                width=espessura,
            )
        return imagem, total
    finally:
        documento.close()
