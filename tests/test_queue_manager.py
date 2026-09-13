import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.participant import Participant
from services.queue_manager import ProcessJob, QueueManager
from utils.profile_manager import Perfil


class TestQueueManager(unittest.TestCase):
    def setUp(self):
        self.qm = QueueManager()
        self.addCleanup(self.qm.encerrar)

    def test_callback_de_cancelamento_pode_consultar_fila(self):
        with patch.object(self.qm, "_garantir_worker_ativo"):
            job = self.qm.adicionar_tarefa(lambda _: None, "abc")
            self.qm.on_queue_changed = lambda: self.qm.obter_total_fila()
            cancel = threading.Thread(target=lambda: self.qm.cancelar_job(job.id), daemon=True)
            cancel.start()
            cancel.join(1)
            self.assertFalse(cancel.is_alive(), "Callback ficou preso no lock da fila")

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

    def test_callback_com_erro_nao_prende_worker(self):
        self.qm.on_job_started = lambda _: (_ for _ in ()).throw(ValueError("callback"))
        job = self.qm.adicionar_job([], Path("tmp"), {}, [], "PDF", Perfil())
        finished = threading.Event()
        self.qm.adicionar_tarefa(lambda _: finished.set(), "after-error")
        self.assertTrue(finished.wait(2))
        self.assertEqual(job.status, "erro")

    def test_adicionar_e_obter_status_fila(self):
        p = Participant(nome_completo="Carlos Lima", cpf="123.456.789-00")
        perfil = Perfil(nome="Padrão", formularios=[], documentos_extras=[])

        self.assertFalse(self.qm.tem_trabalho_ativo())
        self.assertEqual(self.qm.obter_status_resumo(), "FILA: Ociosa")

        with patch.object(self.qm, "_garantir_worker_ativo"):
            job = self.qm.adicionar_job(
                participantes=[p],
                pasta_saida=Path("tmp"),
                documentos_externos={},
                forms_selecionados=[],
                formato_saida="PDF/A-2b",
                perfil=perfil,
            )
            self.assertEqual(job.status, "na_fila")
            self.assertEqual(self.qm.obter_total_fila(), 1)
            self.assertTrue(self.qm.tem_trabalho_ativo())

    def test_cancelar_job_na_fila(self):
        p = Participant(nome_completo="Maria Silva", cpf="111.222.333-44")
        perfil = Perfil(nome="Padrão", formularios=[], documentos_extras=[])

        with patch.object(self.qm, "_garantir_worker_ativo"):
            job1 = self.qm.adicionar_job([p], Path("tmp"), {}, [], "PDF/A-2b", perfil)
            job2 = self.qm.adicionar_job([p], Path("tmp"), {}, [], "PDF/A-2b", perfil)

            self.qm.cancelar_job(job2.id)
            self.assertEqual(job2.status, "cancelado")
            self.assertEqual(len(self.qm._fila), 1)

    def test_execucao_job_sucesso(self):
        p = Participant(nome_completo="Ana Souza", cpf="999.888.777-66")
        perfil = Perfil(nome="Padrão", formularios=[], documentos_extras=[])

        iniciado = []
        concluido = []

        self.qm.on_job_started = lambda j: iniciado.append(j.id)
        self.qm.on_job_completed = lambda j, res: concluido.append(j.id)

        with patch("services.queue_manager.gerar_documentos") as mock_gerar, \
             patch("services.queue_manager.executar_etapa2") as mock_etapa2:
            
            mock_gerar.return_value = MagicMock(arquivos_gerados=[Path("tmp/doc.pdf")])
            mock_etapa2.return_value = {
                "sucesso": True,
                "pasta_pdfa": Path("tmp/PDF-A"),
                "resultado_lote": MagicMock(convertidos=[]),
                "mensagem": "Sucesso",
                "cancelado": False,
            }

            job = self.qm.adicionar_job([p], Path("tmp"), {}, [], "PDF/A-2b", perfil)

            # Esperar worker finalizar
            max_wait = 2.0
            start = time.time()
            while job.status != "concluido" and (time.time() - start) < max_wait:
                time.sleep(0.05)

            self.assertEqual(job.status, "concluido")
            self.assertIn(job.id, iniciado)
            self.assertIn(job.id, concluido)


if __name__ == "__main__":
    unittest.main()
