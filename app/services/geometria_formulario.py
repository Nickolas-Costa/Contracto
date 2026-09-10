"""Auditoria e correção declarativa da geometria de campos AcroForm.

Substitui scripts pontuais por formulário: anomalias (área zerada, campo
fora da página, sobreposição) são detectadas por regras genéricas e as
correções vêm de configuração (`assets/config/geometria_modelos.json`),
não de código por modelo.

Desenho (POO): `RegraGeometria` é a abstração; cada correção concreta
(`AjustarBordaEsquerda`, `DefinirRetangulo`, `DividirCampo`) implementa
`aplicar()` do seu jeito (polimorfismo) sobre o mesmo contexto.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    TextStringObject,
)


class ErroGeometria(Exception):
    """Falha ao auditar ou corrigir a geometria de um formulário."""


@dataclass
class WidgetInfo:
    """Um campo de formulário e seu retângulo na página."""

    nome: str
    pagina: int
    ret: tuple[float, float, float, float]


@dataclass
class AnomaliaGeometria:
    """Problema encontrado: área zerada, fora da página ou sobreposição."""

    campo: str
    pagina: int
    tipo: str
    detalhe: str


@dataclass
class ContextoCorrecao:
    """Estado compartilhado da escrita (encapsula writer, widgets e páginas)."""

    writer: PdfWriter
    widgets: dict[str, DictionaryObject] = field(default_factory=dict)
    paginas: dict[str, object] = field(default_factory=dict)
    aplicadas: list[str] = field(default_factory=list)
    acroform: DictionaryObject | None = None

    def retangulo(self, valores: list[float]) -> ArrayObject:
        """Converte coordenadas em objeto de retângulo do PDF."""
        return ArrayObject(FloatObject(valor) for valor in valores)

    def limpar_aparencia(self, widget: DictionaryObject) -> None:
        """Remove aparência fixa para o visualizador redesenhar o campo."""
        widget.pop(NameObject("/AP"), None)

    def novo_widget_texto(
        self, modelo: DictionaryObject, nome: str,
        ret: list[float], tooltip: str,
    ) -> DictionaryObject:
        """Clona estilo do modelo para um campo irmão (mesma fonte e borda)."""
        widget = DictionaryObject()
        for chave in ("/Type", "/Subtype", "/FT", "/F", "/BS", "/DA", "/Ff"):
            if chave in modelo:
                widget[NameObject(chave)] = modelo[chave]
        widget[NameObject("/T")] = TextStringObject(nome)
        widget[NameObject("/NM")] = TextStringObject(f"contracto-{nome}")
        widget[NameObject("/TU")] = TextStringObject(tooltip)
        widget[NameObject("/Rect")] = self.retangulo(ret)
        if "/MK" in modelo:
            widget[NameObject("/MK")] = modelo["/MK"]
        return widget

    def adicionar_widget(
        self, pagina: object, acroform: DictionaryObject, widget: DictionaryObject,
    ) -> None:
        """Registra um widget novo na página e no formulário."""
        referencia = self.writer._add_object(widget)
        pagina["/Annots"].append(referencia)
        acroform["/Fields"].append(referencia)


def ler_widgets(caminho_pdf: Path) -> tuple[list[WidgetInfo], list[tuple[float, float, float, float]]]:
    """Lê widgets e caixas das páginas (somente leitura, sem alterar o arquivo)."""
    leitor = PdfReader(str(caminho_pdf))
    caixas: list[tuple[float, float, float, float]] = []
    for pagina in leitor.pages:
        caixa = pagina.mediabox
        caixas.append((float(caixa.left), float(caixa.bottom), float(caixa.right), float(caixa.top)))
    widgets: list[WidgetInfo] = []
    for indice, pagina in enumerate(leitor.pages):
        for referencia in pagina.get("/Annots", []) or []:
            try:
                widget = referencia.get_object()
            except Exception:
                continue
            nome = widget.get("/T")
            ret = widget.get("/Rect")
            if nome and ret and len(ret) == 4:
                try:
                    widgets.append(WidgetInfo(
                        nome=str(nome), pagina=indice,
                        ret=tuple(float(v) for v in ret),
                    ))
                except (TypeError, ValueError):
                    continue
    return widgets, caixas


def _area(ret: tuple[float, float, float, float]) -> float:
    return max(0.0, ret[2] - ret[0]) * max(0.0, ret[3] - ret[1])


def _intersecao(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def auditar_geometria(caminho_pdf: Path) -> list[AnomaliaGeometria]:
    """Detecta campos com área zerada, fora da página ou sobrepostos."""
    widgets, caixas = ler_widgets(caminho_pdf)
    anomalias: list[AnomaliaGeometria] = []
    for widget in widgets:
        x0, y0, x1, y1 = widget.ret
        caixa = caixas[widget.pagina]
        if _area(widget.ret) <= 0:
            anomalias.append(AnomaliaGeometria(
                widget.nome, widget.pagina, "area_zero",
                f"Retângulo sem área: {list(widget.ret)}.",
            ))
        if x0 < caixa[0] or y0 < caixa[1] or x1 > caixa[2] or y1 > caixa[3]:
            anomalias.append(AnomaliaGeometria(
                widget.nome, widget.pagina, "fora_da_pagina",
                f"Retângulo {list(widget.ret)} escapa da página {list(caixa)}.",
            ))
    vistos: dict[int, list[WidgetInfo]] = {}
    for widget in widgets:
        vistos.setdefault(widget.pagina, []).append(widget)
    for pagina, itens in vistos.items():
        for i, primeiro in enumerate(itens):
            for segundo in itens[i + 1:]:
                area_primeiro = _area(primeiro.ret)
                area_segundo = _area(segundo.ret)
                menor = min(area_primeiro, area_segundo)
                if menor > 0 and _intersecao(primeiro.ret, segundo.ret) > 0.5 * menor:
                    anomalias.append(AnomaliaGeometria(
                        f"{primeiro.nome} x {segundo.nome}", pagina, "sobreposicao",
                        "Campos com mais da metade da área sobreposta.",
                    ))
    return anomalias


class RegraGeometria(ABC):
    """Abstração: cada correção sabe se aplicar sobre o contexto."""

    @abstractmethod
    def aplicar(self, ctx: ContextoCorrecao) -> list[str]:
        """Aplica a regra e devolve os nomes dos campos ajustados."""


class AjustarBordaEsquerda(RegraGeometria):
    """Move a borda esquerda de campos de valor (alinha colunas)."""

    def __init__(self, campos: dict[str, float]) -> None:
        self.campos = dict(campos)

    def aplicar(self, ctx: ContextoCorrecao) -> list[str]:
        ajustados = []
        for nome, esquerda in self.campos.items():
            widget = ctx.widgets.get(nome)
            if widget is None:
                continue
            valores = [float(v) for v in widget["/Rect"]]
            valores[0] = float(esquerda)
            widget[NameObject("/Rect")] = ctx.retangulo(valores)
            ctx.limpar_aparencia(widget)
            ajustados.append(nome)
        return ajustados


class DefinirRetangulo(RegraGeometria):
    """Define retângulo e dica exatos de campos existentes."""

    def __init__(self, campos: dict[str, dict]) -> None:
        self.campos = {nome: dict(spec) for nome, spec in campos.items()}

    def aplicar(self, ctx: ContextoCorrecao) -> list[str]:
        ajustados = []
        for nome, spec in self.campos.items():
            widget = ctx.widgets.get(nome)
            if widget is None:
                continue
            widget[NameObject("/Rect")] = ctx.retangulo(list(spec["ret"]))
            if spec.get("tooltip"):
                widget[NameObject("/TU")] = TextStringObject(spec["tooltip"])
            ctx.limpar_aparencia(widget)
            ajustados.append(nome)
        return ajustados


class DividirCampo(RegraGeometria):
    """Reaproveita um campo original para a primeira parte e cria as irmãs.

    Generaliza a divisão dia/mês/ano: procura o original entre `origens`
    e garante uma parte por entrada de `partes`.
    """

    def __init__(self, origens: list[str], partes: dict[str, dict]) -> None:
        self.origens = list(origens)
        self.partes = {nome: dict(spec) for nome, spec in partes.items()}

    def aplicar(self, ctx: ContextoCorrecao) -> list[str]:
        nomes = list(self.partes)
        if not nomes:
            return []
        original = next(
            (ctx.widgets[nome] for nome in self.origens if nome in ctx.widgets),
            None,
        )
        if original is None:
            raise ErroGeometria(f"Campo original não encontrado: {self.origens}.")
        pagina_nome = next(
            (nome for nome in self.origens if nome in ctx.paginas), self.origens[0]
        )
        primeiro, *restantes = nomes
        spec = self.partes[primeiro]
        original[NameObject("/T")] = TextStringObject(primeiro)
        original[NameObject("/NM")] = TextStringObject(f"contracto-{primeiro}")
        if spec.get("tooltip"):
            original[NameObject("/TU")] = TextStringObject(spec["tooltip"])
        original[NameObject("/Rect")] = ctx.retangulo(list(spec["ret"]))
        ctx.limpar_aparencia(original)
        ctx.widgets[primeiro] = original
        ajustados = [primeiro]
        acroform = ctx.acroform
        for nome in restantes:
            spec = self.partes[nome]
            existente = ctx.widgets.get(nome)
            if existente is not None:
                existente[NameObject("/Rect")] = ctx.retangulo(list(spec["ret"]))
                ctx.limpar_aparencia(existente)
            else:
                pagina = ctx.paginas.get(pagina_nome)
                if pagina is None or acroform is None:
                    raise ErroGeometria(f"Sem página para criar '{nome}'.")
                novo = ctx.novo_widget_texto(original, nome, list(spec["ret"]), spec.get("tooltip", ""))
                ctx.adicionar_widget(pagina, acroform, novo)
                ctx.widgets[nome] = novo
            ajustados.append(nome)
        return ajustados


def carregar_regras(config: dict) -> list[RegraGeometria]:
    """Monta as regras a partir de configuração declarativa (JSON)."""
    regras: list[RegraGeometria] = []
    if config.get("ajustar_borda_esquerda"):
        regras.append(AjustarBordaEsquerda(config["ajustar_borda_esquerda"]))
    if config.get("definir_retangulo"):
        regras.append(DefinirRetangulo(config["definir_retangulo"]))
    if config.get("dividir_campo"):
        spec = config["dividir_campo"]
        regras.append(DividirCampo(spec.get("origens", []), spec.get("partes", {})))
    return regras


def aplicar_correcoes(
    origem: Path,
    destino: Path,
    regras: list[RegraGeometria],
    esperados: set[str] | None = None,
) -> list[str]:
    """Clona o PDF, aplica as regras e valida os campos esperados."""
    leitor = PdfReader(str(origem))
    writer = PdfWriter(clone_from=leitor)
    try:
        acroform = writer.root_object["/AcroForm"].get_object()
    except Exception as exc:
        raise ErroGeometria("O PDF não possui formulário AcroForm.") from exc

    ctx = ContextoCorrecao(writer=writer, acroform=acroform)
    for pagina in writer.pages:
        for referencia in pagina.get("/Annots", []) or []:
            try:
                widget = referencia.get_object()
            except Exception:
                continue
            nome = widget.get("/T")
            if nome:
                nome = str(nome)
                ctx.widgets.setdefault(nome, widget)
                ctx.paginas.setdefault(nome, pagina)

    aplicadas: list[str] = []
    for regra in regras:
        aplicadas.extend(regra.aplicar(ctx))

    writer.set_need_appearances_writer(True)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("wb") as stream:
        writer.write(stream)

    if esperados:
        campos = set((PdfReader(str(destino)).get_fields() or {}).keys())
        faltando = set(esperados) - campos
        if faltando:
            raise ErroGeometria(f"Campos ausentes após correção: {sorted(faltando)}.")
    return aplicadas
