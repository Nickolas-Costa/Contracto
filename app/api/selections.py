"""Capacidades de arquivo: só o código Python do shell registra seleções."""
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path


class SelectionError(ValueError):
    pass


@dataclass(frozen=True)
class Selection:
    path: Path
    kind: str
    expires: float


class Selections:
    def __init__(self, ttl=3600, limit=2000):
        self.ttl, self.limit = ttl, limit
        self._items = {}
        self._lock = threading.RLock()
        self._closed = False

    def register(self, path: Path, kind: str) -> str:
        path = Path(path).resolve(strict=True)
        if kind not in {"file", "directory"}:
            raise SelectionError("Seleção inválida")
        if kind == "file" and (not path.is_file() or path.suffix.lower() not in {".pdf", ".rtf"}):
            raise SelectionError("Arquivo inválido")
        if kind == "directory" and not path.is_dir():
            raise SelectionError("Pasta inválida")
        with self._lock:
            self._items = {k: v for k, v in self._items.items() if v.expires > time.monotonic()}
            if self._closed or len(self._items) >= self.limit:
                raise SelectionError("Seleções indisponíveis")
            key = secrets.token_hex(16)
            self._items[key] = Selection(path, kind, time.monotonic() + self.ttl)
            return key

    def resolve(self, key: str, kind: str) -> Path:
        with self._lock:
            item = self._items.get(key)
            if self._closed or not item or item.kind != kind or item.expires <= time.monotonic():
                raise SelectionError("Seleção ausente ou expirada; selecione novamente")
            try:
                resolved = item.path.resolve(strict=True)
                # Rejeita substituição por symlink/junction após a seleção.
                if resolved != item.path or (kind == "directory" and not resolved.is_dir()) or (kind == "file" and not resolved.is_file()):
                    raise SelectionError("Seleção alterada")
                return resolved
            except OSError:
                raise SelectionError("Seleção indisponível") from None

    def revoke(self, keys):
        with self._lock:
            for key in keys:
                self._items.pop(key, None)

    def close(self):
        with self._lock:
            self._closed = True
            self._items.clear()
