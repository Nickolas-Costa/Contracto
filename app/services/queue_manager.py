"""Fila de execução em segundo plano: um trabalho por vez, em thread própria.

Quem agenda é `api/jobs.py` (`adicionar_tarefa`); a tarefa recebe o `ProcessJob`
para consultar `cancel_event`.
"""

import threading
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

from services.pdfa_converter import ProcessoCanceladoError
from utils.logger import obter_logger


_logger = obter_logger("fila")


@dataclass
class ProcessJob:
    """Um item da fila."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = "na_fila"  # "na_fila", "executando", "cancelando", "concluido", "erro", "cancelado"
    cancel_event: threading.Event = field(default_factory=threading.Event)
    erro: Optional[str] = None
    tarefa: Optional[Callable] = field(default=None, repr=False)


class QueueManager:
    """Orquestrador de tarefas em fila com thread trabalhadora dedicada."""

    def __init__(self):
        self._lock = threading.Lock()
        self._fila: list[ProcessJob] = []
        self._job_ativo: Optional[ProcessJob] = None
        self._thread_trabalhadora: Optional[threading.Thread] = None
        self._executando = True

    def adicionar_tarefa(self, tarefa: Callable, job_id: str) -> ProcessJob:
        """Agenda uma operação; levanta RuntimeError se a fila já foi encerrada."""
        job = ProcessJob(id=job_id, tarefa=tarefa)
        with self._lock:
            if not self._executando:
                raise RuntimeError("Fila encerrada")
            self._fila.append(job)
        self._garantir_worker_ativo()
        return job

    def encerrar(self, timeout: float = 50) -> bool:
        """Cancela pendências e aguarda a operação ativa, sem abandonar silenciosamente."""
        with self._lock:
            self._executando = False
            for job in self._fila:
                job.cancel_event.set()
                job.status = "cancelado"
                job.tarefa = None
            self._fila.clear()
            if self._job_ativo:
                self._job_ativo.cancel_event.set()
            worker = self._thread_trabalhadora
        if worker and worker is not threading.current_thread():
            worker.join(timeout)
        return worker is None or not worker.is_alive()

    def cancelar_job(self, job_id: str) -> None:
        """Cancela um job específico (ativo ou que ainda esteja na fila)."""
        with self._lock:
            if self._job_ativo and self._job_ativo.id == job_id:
                self._job_ativo.cancel_event.set()
                self._job_ativo.status = "cancelando"
                return
            for job in list(self._fila):
                if job.id == job_id:
                    job.status = "cancelado"
                    job.cancel_event.set()
                    job.tarefa = None
                    self._fila.remove(job)
                    break

    def _garantir_worker_ativo(self) -> None:
        with self._lock:
            if self._executando and self._thread_trabalhadora is None:
                self._thread_trabalhadora = threading.Thread(
                    target=self._executar_worker_loop, daemon=True,
                    name="ContractoQueueWorker",
                )
                self._thread_trabalhadora.start()

    def _executar_worker_loop(self) -> None:
        """Retira e executa os jobs da fila, um por vez."""
        while True:
            with self._lock:
                if not (self._executando and self._fila):
                    self._job_ativo = None
                    # Publicar o encerramento sob o mesmo lock usado pelo produtor.
                    self._thread_trabalhadora = None
                    return
                job = self._fila.pop(0)
                self._job_ativo = job
                job.status = "executando"
            try:
                job.tarefa(job)
                job.status = "cancelado" if job.cancel_event.is_set() else "concluido"
            except ProcessoCanceladoError:
                job.status = "cancelado"
            except Exception:
                # Uma tarefa com erro não pode matar o worker e prender a fila.
                job.status = "erro"
                job.erro = "Falha na operação"
                _logger.error("Falha no item %s da fila.", job.id)
            finally:
                job.tarefa = None  # Não reter dados pessoais capturados pela closure.
            with self._lock:
                self._job_ativo = None
