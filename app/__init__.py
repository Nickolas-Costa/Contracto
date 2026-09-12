"""Pacote da aplicação (permite `import app.*` a partir da raiz, ex: servidor web).

O código interno usa imports curtos (`from utils...`, `from services...`);
este bootstrap coloca `app/` no path para que os dois estilos coexistam
sem reescrever dezenas de arquivos (ver passo de separação em camadas).
"""

import os as _os
import sys as _sys

_base = _os.path.dirname(_os.path.abspath(__file__))
if _base not in _sys.path:
    _sys.path.insert(0, _base)
