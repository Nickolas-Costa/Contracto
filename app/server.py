"""Servidor local embutido do Contracto.

Este backend é usado apenas em loopback para a interface WebView e não expõe um
serviço público na rede. O token de autenticação é gerado em memória para cada
instância do processo e ajuda a restringir acessos entre a UI local e o servidor.
"""
import secrets
import socket
import threading
import time

import uvicorn

from api.http import create_app
from api.jobs import Jobs


class LocalServer:
    def __init__(self, profiles=None):
        self.jobs = Jobs(profiles)
        self.token = secrets.token_urlsafe(32)
        self.closed = False
        self.shutdown_failed = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # O mesmo socket reservado é entregue ao Uvicorn, sem corrida pela porta.
        self._socket.bind(("127.0.0.1", 0))
        self.authority = f"127.0.0.1:{self._socket.getsockname()[1]}"
        self.origin = f"http://{self.authority}"
        self.app = create_app(self)
        self._server = uvicorn.Server(uvicorn.Config(
            self.app, host="127.0.0.1", log_config=None, log_level="critical",
            access_log=False, proxy_headers=False, server_header=False,
            timeout_keep_alive=2, timeout_graceful_shutdown=10,
            limit_concurrency=32, ws="none",
        ))
        self._thread = None

    def start(self, timeout=10):
        if self.closed or self._thread is not None:
            raise RuntimeError("Sessão já iniciada ou encerrada")
        self._thread = threading.Thread(target=self._server.run,
                                        kwargs={"sockets": [self._socket]},
                                        name="ContractoLocalHTTP", daemon=True)
        self._thread.start()
        deadline = time.monotonic() + timeout
        while not self._server.started:
            if not self._thread.is_alive() or time.monotonic() > deadline:
                self.close()
                raise RuntimeError("Servidor local não iniciou")
            time.sleep(0.01)
        return self

    def invalidate(self):
        self.closed = True
        self.token = ""

    def close(self):
        self.invalidate()
        self._server.should_exit = True
        if self._thread:
            self._thread.join(55)
            if self._thread.is_alive():
                raise RuntimeError("Servidor local ainda está encerrando")
        else:
            self.jobs.close()
        self._socket.close()
        if self.shutdown_failed:
            raise RuntimeError("Não foi possível concluir o encerramento dos trabalhos")

    def __enter__(self):
        return self.start()

    def __exit__(self, *_args):
        self.close()
