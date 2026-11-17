"""Propõe retângulo e fonte dos campos de texto de um modelo, sem sobrepor o texto fixo da linha.

Para cada campo de texto, o texto vizinho (à esquerda e à direita, na mesma linha) limita a largura;
campos muito baixos ganham altura mínima e a fonte deixa de ser automática (o visualizador escolhia
corpos fora de proporção). A saída é o bloco `definir_retangulo` de `geometria_modelos.json`.

    python scripts/sugerir_geometria.py --modelo modelo_01            # só mostra
    python scripts/sugerir_geometria.py --modelo modelo_01 --gravar   # mescla no JSON de configuração
Depois: python scripts/corrigir_geometria.py --modelo modelo_01 --aplicar
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import pypdfium2
from pypdf import PdfReader

from services.geometria_formulario import ler_widgets
from utils.resource_path import caminho_recurso, modelo_configurado

FOLGA_ESQUERDA, FOLGA_DIREITA = 2.5, 1.5
ALTURA_MINIMA = 13.0
FONTE_PADRAO = 10.0
VAO_MINIMO = 9.0  # espaço entre caracteres da linha que já conta como "vão" para um campo
# Largura do valor esperado, em em (Helvetica: dígito 0,556; pontuação 0,278), para escolher o corpo da fonte.
EM_ESPERADO = (("cpf", 7.0), ("pis", 7.0), ("data", 5.0), ("ano_", 2.3), ("anos_", 1.2), ("meses_", 1.2), ("valor", 5.0), ("n_da_operacao", 7.3))


FONTES_FIXAS = {"local_imovel": 9.0}  # endereço longo numa linha só: corpo menor


def _fonte(nome: str, largura: float) -> float:
    if nome in FONTES_FIXAS:
        return FONTES_FIXAS[nome]
    em = next((n for chave, n in EM_ESPERADO if chave in nome.lower()), 0)
    if not em:
        return FONTE_PADRAO
    return max(7.5, min(FONTE_PADRAO, int((largura - 3) / em * 2) / 2))


def _vaos(caixas: list[tuple]) -> list[tuple[float, float]]:
    """Intervalos livres da linha, entre o texto fixo (as pontas ficam abertas: -inf/+inf)."""
    xs = sorted(caixas, key=lambda b: b[0])
    vaos, fim = [], float("-inf")
    for b in xs:
        if b[0] - fim >= VAO_MINIMO:
            vaos.append((fim, b[0]))
        fim = max(fim, b[2])
    vaos.append((fim, float("inf")))
    return vaos


def _ajustar_x(x0: float, x1: float, vaos: list[tuple[float, float]]) -> tuple[float, float]:
    """Põe o campo no vão da linha que o contém (ou no mais próximo), sem tocar no texto fixo."""
    centro = (x0 + x1) / 2
    vao = min(vaos, key=lambda v: 0 if v[0] <= centro <= v[1] else min(abs(centro - v[0]), abs(centro - v[1])))
    inicio, fim = vao[0] + FOLGA_ESQUERDA, vao[1] - FOLGA_DIREITA
    if inicio <= x0 and x1 <= fim:  # já cabe no vão: não mexe
        return x0, x1
    largura = x1 - x0
    if x1 > fim:  # invade o texto da direita: encosta no fim do vão (sem texto à esquerda, só encurta)
        x1 = fim
        if inicio != float("-inf"):
            x0 = max(inicio, x1 - largura)
    if x0 < inicio:  # invade o texto da esquerda
        x0 = inicio
        x1 = min(x1, fim) if x1 > x0 else x0 + largura
    return x0, x1


def propor(caminho: Path, bordas: dict[str, float] | None = None) -> dict[str, dict]:
    campos = PdfReader(str(caminho)).get_fields() or {}
    texto = {nome for nome, c in campos.items() if str(c.get("/FT")) == "/Tx"}
    widgets, _ = ler_widgets(caminho)
    pdf = pypdfium2.PdfDocument(str(caminho))
    paginas: dict[int, list] = {}
    resultado: dict[str, dict] = {}
    for w in widgets:
        if w.nome not in texto:
            continue
        if w.pagina not in paginas:
            tp = pdf[w.pagina].get_textpage()
            paginas[w.pagina] = [(tp.get_charbox(i), tp.get_text_range(i, 1)) for i in range(tp.count_chars())]
        x0, y0, x1, y1 = w.ret
        cy = (y0 + y1) / 2
        linha = [b for b, c in paginas[w.pagina] if c.strip() and b[1] - 2 <= cy <= b[3] + 2]
        x0, x1 = _ajustar_x(x0, x1, _vaos(linha))
        x0 = (bordas or {}).get(w.nome, x0)  # borda esquerda já curada na configuração
        if y1 - y0 < ALTURA_MINIMA:
            falta = ALTURA_MINIMA - (y1 - y0)
            y0, y1 = y0 - falta / 2, y1 + falta / 2
        resultado[w.nome] = {"ret": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                             "fonte": _fonte(w.nome, x1 - x0)}
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", required=True)
    parser.add_argument("--gravar", action="store_true")
    args = parser.parse_args()
    origem = modelo_configurado(args.modelo)
    if origem is None:
        print(f"[ERRO] Modelo '{args.modelo}' não encontrado.")
        return 1
    caminho = caminho_recurso("assets", "config", "geometria_modelos.json")
    config = json.loads(caminho.read_text(encoding="utf-8"))
    proposta = propor(origem, config.get(args.modelo, {}).get("ajustar_borda_esquerda"))
    for nome, spec in proposta.items():
        print(f"{nome:40} {spec['ret']}  fonte {spec['fonte']}")
    if args.gravar:
        bruto = caminho.read_bytes()
        config.setdefault(args.modelo, {}).setdefault("definir_retangulo", {}).update(proposta)
        quebra = "\r\n" if b"\r\n" in bruto else "\n"
        texto = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        caminho.write_bytes(re.sub(r"\r?\n", quebra, texto).encode("utf-8"))
        print(f"Gravado em {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
