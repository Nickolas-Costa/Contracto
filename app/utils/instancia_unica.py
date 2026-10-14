"""Garante uma única instância do aplicativo por sessão do Windows.

Usa um mutex nomeado do sistema (`Local\\ContractoDesktopApp`): a segunda
execução apenas traz a janela existente para frente e encerra em silêncio,
sem nenhum modal — em vez de abrir outra janela concorrendo pelos mesmos
arquivos em `%APPDATA%\\Contracto`.
"""

import sys

_NOME_MUTEX = r"Local\ContractoDesktopApp"
_ERRO_JA_EXISTE = 183  # ERROR_ALREADY_EXISTS (Win32)


class InstanciaJaEmExecucao(Exception):
    """Levantado quando outra cópia do aplicativo já está rodando."""


def focar_janela_existente(prefixo: str = "Contracto") -> bool:
    """Traz a janela existente do app para frente (sem nenhum modal).

    Procura a primeira janela visível de nível superior cujo título comece
    com `prefixo`, restaura se estiver minimizada e dá o foco do Windows.
    Retorna True se encontrou e focou, False caso contrário.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd_encontrado = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def _enum_proc(hwnd, _lparam):
            try:
                if not user32.IsWindowVisible(hwnd):
                    return True
                tamanho = user32.GetWindowTextLengthW(hwnd)
                if tamanho <= 0:
                    return True
                buffer = ctypes.create_unicode_buffer(tamanho + 1)
                user32.GetWindowTextW(hwnd, buffer, tamanho + 1)
                if buffer.value.startswith(prefixo):
                    hwnd_encontrado.append(hwnd)
                    return False  # Para a enumeração.
            except Exception:
                pass
            return True

        user32.EnumWindows(_enum_proc, 0)
        if not hwnd_encontrado:
            return False
        hwnd = hwnd_encontrado[0]
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


class InstanciaUnica:
    """Guarda o mutex durante a vida do processo (usar como context manager)."""

    def __init__(self, nome: str = _NOME_MUTEX) -> None:
        self._nome = nome
        self._handle = None

    def adquirir(self) -> "InstanciaUnica":
        """Tenta adquirir o mutex; levanta InstanciaJaEmExecucao se ocupado."""
        if sys.platform != "win32":
            return self
        import ctypes

        nucleo = ctypes.windll.kernel32
        handle = nucleo.CreateMutexW(None, False, self._nome)
        if not handle:
            raise OSError("Não foi possível criar o mutex de instância única.")
        if nucleo.GetLastError() == _ERRO_JA_EXISTE:
            nucleo.CloseHandle(handle)
            raise InstanciaJaEmExecucao(
                "O Contracto já está em execução nesta sessão."
            )
        self._handle = handle
        return self

    def liberar(self) -> None:
        """Devolve o mutex (chamado automaticamente ao sair do contexto)."""
        if self._handle and sys.platform == "win32":
            import ctypes

            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self) -> "InstanciaUnica":
        return self.adquirir()

    def __exit__(self, *args) -> None:
        self.liberar()
