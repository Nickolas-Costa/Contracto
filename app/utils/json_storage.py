"""Leitura e gravação segura dos arquivos JSON do aplicativo."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def salvar_json(caminho: Path, dados: Any) -> None:
    """Grava primeiro em um arquivo temporário para evitar arquivo incompleto."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            json.dump(dados, arquivo, indent=2, ensure_ascii=False)
            arquivo.flush()
            os.fsync(arquivo.fileno())
            temporario = Path(arquivo.name)
        os.replace(temporario, caminho)
    finally:
        if temporario and temporario.exists():
            try:
                temporario.unlink()
            except OSError:
                pass
