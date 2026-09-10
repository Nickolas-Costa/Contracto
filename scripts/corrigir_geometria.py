"""Aplica correções declarativas de geometria a qualquer modelo (ver geometria_modelos.json).

Exemplos:
    Auditar sem alterar:
        python scripts/corrigir_geometria.py --modelo modelo_01 --auditar
    Corrigir para um arquivo ao lado do original:
        python scripts/corrigir_geometria.py --modelo modelo_01
    Gravar de volta no asset (com cópia .bak):
        python scripts/corrigir_geometria.py --modelo modelo_01 --aplicar
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.geometria_formulario import (
    aplicar_correcoes,
    auditar_geometria,
    carregar_regras,
)
from utils.resource_path import caminho_recurso, modelo_configurado


def carregar_config() -> dict:
    """Lê o mapa de correções que acompanha o aplicativo."""
    caminho = caminho_recurso("assets", "config", "geometria_modelos.json")
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", required=True, help="Chave do modelo (ex: modelo_01)")
    parser.add_argument("--origem", type=Path, help="PDF de entrada (padrão: o asset do modelo)")
    parser.add_argument("--destino", type=Path, help="PDF de saída")
    parser.add_argument("--aplicar", action="store_true", help="Grava de volta no asset (com .bak)")
    parser.add_argument("--auditar", action="store_true", help="Só lista anomalias, sem alterar")
    args = parser.parse_args(argumentos)

    config = carregar_config().get(args.modelo)
    if config is None:
        print(f"[ERRO] Sem correções configuradas para '{args.modelo}'.")
        return 1

    origem = args.origem or modelo_configurado(args.modelo)
    if not origem or not Path(origem).exists():
        print(f"[ERRO] Modelo '{args.modelo}' não encontrado.")
        return 1
    origem = Path(origem)

    if args.auditar:
        anomalias = auditar_geometria(origem)
        if not anomalias:
            print("Nenhuma anomalia de geometria encontrada.")
            return 0
        for anomalia in anomalias:
            print(f"- {anomalia.campo} (pág. {anomalia.pagina}): [{anomalia.tipo}] {anomalia.detalhe}")
        return 0

    destino = args.destino
    if destino is None:
        if args.aplicar:
            copia = origem.with_suffix(origem.suffix + ".bak")
            copia.write_bytes(origem.read_bytes())
            print(f"Cópia de segurança em: {copia}")
            destino = origem
        else:
            destino = origem.with_name(f"{origem.stem}.corrigido{origem.suffix}")

    regras = carregar_regras(config)
    aplicadas = aplicar_correcoes(origem, Path(destino), regras)
    print(f"Aplicadas {len(aplicadas)} correções em {len(regras)} regra(s): {', '.join(aplicadas)}")
    print(f"Saída em: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
