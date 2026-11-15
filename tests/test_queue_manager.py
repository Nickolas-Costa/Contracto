import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.queue_manager import QueueManager


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.qm = QueueManager()
        self.addCleanup(self.qm.encerrar)

    def test_encerramento_cancela_ativo_e_recusa_novos(self):
        started = threading.Event()
        def work(job):
            started.set()
            job.cancel_event.wait(2)
        job = self.qm.adicionar_tarefa(work, "shutdown")
        self.assertTrue(started.wait(1))
        self.assertTrue(self.qm.encerrar(timeout=3))
        self.assertEqual(job.status, "cancelado")
        with self.assertRaises(RuntimeError):
            self.qm.adicionar_tarefa(lambda _: None, "late")

    def test_tarefa_com_erro_nao_prende_worker(self):
        def falha(_job):
            raise ValueError("tarefa")
        job = self.qm.adicionar_tarefa(falha, "erro")
        finished = threading.Event()
        self.qm.adicionar_tarefa(lambda _: finished.set(), "after-error")
        self.assertTrue(finished.wait(2))
        self.assertEqual(job.status, "erro")

    def test_cancelar_job_na_fila(self):
        with patch.object(self.qm, "_garantir_worker_ativo"):
            self.qm.adicionar_tarefa(lambda _: None, "um")
            job2 = self.qm.adicionar_tarefa(lambda _: None, "dois")
            self.qm.cancelar_job("dois")
            self.assertEqual(job2.status, "cancelado")
            self.assertTrue(job2.cancel_event.is_set())
            self.assertEqual([j.id for j in self.qm._fila], ["um"])

    def test_execucao_em_ordem_e_status_concluido(self):
        ordem = []
        fim = threading.Event()
        primeiro = self.qm.adicionar_tarefa(lambda j: ordem.append(j.id), "a")
        self.qm.adicionar_tarefa(lambda j: (ordem.append(j.id), fim.set()), "b")
        self.assertTrue(fim.wait(2))
        self.assertEqual(ordem, ["a", "b"])
        self.assertEqual(primeiro.status, "concluido")


if __name__ == "__main__":
    unittest.main()
