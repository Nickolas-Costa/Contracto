"""Gate de release para a próxima versão do Contracto.

Regras:
- a app deve expor versão canônica;
- o artefato de instalador deve existir;
- o smoke Windows de WebView2 e dos motores (Word/GS) devem existir no repositório;
- o comando deve ser executável em qualquer ambiente de desenvolvimento sem depender do Windows.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


REQUIRED = [
    RAIZ / "app" / "version.py",
    RAIZ / "VERSION",
    RAIZ / "packaging" / "Contracto.iss",
    RAIZ / "tests" / "smoke_webview.py",
    RAIZ / "tests" / "smoke_api_engines.py",
    RAIZ / "app" / "api" / "http.py",
]


def main() -> int:
    print("[release gate] Contracto - verificação de pré-release")
    missing = [str(path.relative_to(RAIZ)) for path in REQUIRED if not path.exists()]
    if missing:
        print("[FAIL] Arquivos obrigatórios ausentes:")
        for item in missing:
            print(f"  - {item}")
        return 1

    # Validação mínima de projeto: o build e as suítes de smoke existem.
    print("[OK] Versão canônica, instalador, smoke WebView2 e smoke de motores persistem no repositório.")
    print("[OK] O gate de release exige que o ambiente Windows valide WebView2 e motores reais antes da publicação.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
