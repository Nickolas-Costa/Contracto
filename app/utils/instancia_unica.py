"""Garante uma única instância do aplicativo por sessão do Windows.

Usa um mutex nomeado do sistema (`Local\\ContractoDesktopApp`): a segunda
execução detecta o cadeado existente e encerra com aviso, em vez de abrir
outra janela concorrendo pelos mesmos arquivos em `%APPDATA%\\Contracto`.
"""

import sys

_NOME_MUTEX = r"Local\ContractoDesktopApp"
_ERRO_JA_EXISTE = 183  # ERROR_ALREADY_EXISTS (Win32)


class InstanciaJaEmExecucao(Exception):
    """Levantado quando outra cópia do aplicativo já está rodando."""


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
