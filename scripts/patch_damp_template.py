"""Corrige a geometria dos campos AcroForm do modelo oficial MO 29300 (DAMP)."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    TextStringObject,
)


VALUE_FIELD_LEFTS = {
    "valor_imovel_concluido": 300,
    "valor_imovel_construcao": 412,
    "valor_terreno_construcao": 420,
    "valor_construcao_terreno_proprio": 297,
    "valor_reforma_ampliacao": 310,
    "valor_conclusao": 252,
    "valor_material_construcao": 365,
}

DATE_FIELDS = {
    "data_assinatura_dia": ([278, 595.54, 317, 610.54], "Dia"),
    "data_assinatura_mes": ([337, 595.54, 468, 610.54], "Mês"),
    "data_assinatura_ano": ([486, 595.54, 539, 610.54], "Ano"),
}


def _rect(values: list[float]) -> ArrayObject:
    return ArrayObject(FloatObject(value) for value in values)


def _new_text_widget(source: DictionaryObject, name: str, rect: list[float], tooltip: str) -> DictionaryObject:
    widget = DictionaryObject()
    for key in ("/Type", "/Subtype", "/FT", "/F", "/BS", "/DA", "/Ff"):
        if key in source:
            widget[NameObject(key)] = source[key]
    widget[NameObject("/T")] = TextStringObject(name)
    widget[NameObject("/NM")] = TextStringObject(f"contracto-{name}")
    widget[NameObject("/TU")] = TextStringObject(tooltip)
    widget[NameObject("/Rect")] = _rect(rect)
    if "/MK" in source:
        widget[NameObject("/MK")] = source["/MK"]
    return widget


def patch_template(source: Path, destination: Path) -> None:
    reader = PdfReader(str(source))
    writer = PdfWriter(clone_from=reader)
    acroform = writer.root_object["/AcroForm"].get_object()

    widgets_by_name = {}
    pages_by_name = {}
    for page in writer.pages:
        for reference in page.get("/Annots", []):
            widget = reference.get_object()
            name = str(widget.get("/T", ""))
            widgets_by_name[name] = widget
            pages_by_name[name] = page
            if name in VALUE_FIELD_LEFTS:
                values = [float(value) for value in widget["/Rect"]]
                values[0] = VALUE_FIELD_LEFTS[name]
                widget[NameObject("/Rect")] = _rect(values)
                widget.pop(NameObject("/AP"), None)

    date_widget = widgets_by_name.get("data_assinatura_dia") or widgets_by_name.get("data_assinatura_titular")
    date_page = pages_by_name.get("data_assinatura_dia") or pages_by_name.get("data_assinatura_titular")
    if date_widget is None or date_page is None:
        raise RuntimeError("Campo de data do DAMP não encontrado.")

    # Reaproveita o campo original para o dia e cria campos irmãos para mês e ano.
    day_rect, day_tooltip = DATE_FIELDS["data_assinatura_dia"]
    date_widget[NameObject("/T")] = TextStringObject("data_assinatura_dia")
    date_widget[NameObject("/NM")] = TextStringObject("contracto-data_assinatura_dia")
    date_widget[NameObject("/TU")] = TextStringObject(day_tooltip)
    date_widget[NameObject("/Rect")] = _rect(day_rect)
    date_widget.pop(NameObject("/AP"), None)

    for name in ("data_assinatura_mes", "data_assinatura_ano"):
        rect, tooltip = DATE_FIELDS[name]
        existing_widget = widgets_by_name.get(name)
        if existing_widget is not None:
            existing_widget[NameObject("/Rect")] = _rect(rect)
            existing_widget.pop(NameObject("/AP"), None)
        else:
            new_widget = _new_text_widget(date_widget, name, rect, tooltip)
            reference = writer._add_object(new_widget)
            date_page["/Annots"].append(reference)
            acroform["/Fields"].append(reference)

    writer.set_need_appearances_writer(True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as stream:
        writer.write(stream)

    reopened = PdfReader(str(destination))
    fields = reopened.get_fields() or {}
    expected = {*VALUE_FIELD_LEFTS, *DATE_FIELDS}
    missing = expected - set(fields)
    if missing:
        raise RuntimeError(f"Campos ausentes após correção: {sorted(missing)}")
    if "data_assinatura_titular" in fields:
        raise RuntimeError("O campo de data legado ainda está presente.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    patch_template(args.source, args.destination)


if __name__ == "__main__":
    main()
