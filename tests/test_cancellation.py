import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.participant import Participant
from services.pdfa_converter import ProcessoCanceladoError, converter_lote
from services.stage2_service import executar_etapa2
from services.generator_service import gerar_documentos
from utils.profile_manager import obter_perfil, PERFIL_PADRAO_NOME


class TestCancellationAndStages(unittest.TestCase):
    def test_converter_lote_cancelamento(self):
        cancel_event = threading.Event()
        cancel_event.set()

        arquivos = [(Path("in.pdf"), Path("out.pdf"))]
        with self.assertRaises(ProcessoCanceladoError):
            converter_lote(arquivos, cancel_event=cancel_event)

    def test_converter_lote_progresso(self):
        arquivos = [
            (Path("in1.pdf"), Path("out1.pdf")),
            (Path("in2.pdf"), Path("out2.pdf")),
        ]
        chamadas_progresso = []

        def _progresso(idx, total, nome):
            chamadas_progresso.append((idx, total, nome))

        with patch("services.pdfa_converter.converter_e_validar") as mock_converter:
            from services.pdfa_converter import ResultadoConversao
            mock_converter.return_value = ResultadoConversao(caminho_saida=Path("out.pdf"), perfil="PDF/A-2b", validado=True)
            resultado = converter_lote(arquivos, on_file_progress=_progresso)

            self.assertEqual(len(chamadas_progresso), 2)
            self.assertEqual(chamadas_progresso[0], (1, 2, "in1.pdf"))
            self.assertEqual(chamadas_progresso[1], (2, 2, "in2.pdf"))

    def test_executar_etapa2_cancelamento_imediato(self):
        cancel_event = threading.Event()
        cancel_event.set()

        res = executar_etapa2(
            pasta_base=Path("tmp"),
            participantes=[],
            arquivos_gerados_etapa1=[],
            documentos_externos={},
            cancel_event=cancel_event,
        )
        self.assertFalse(res["sucesso"])
        self.assertTrue(res["cancelado"])
        self.assertIn("cancelado", res["mensagem"].lower())

    def test_gerar_documentos_cancelamento(self):
        cancel_event = threading.Event()
        cancel_event.set()

        perfil = obter_perfil(PERFIL_PADRAO_NOME)
        participante = Participant(nome_completo="João Teste", cpf="111.444.777-35", endereco="Rua A")

        with self.assertRaises(ProcessoCanceladoError):
            gerar_documentos([participante], perfil, Path("tmp"), cancel_event=cancel_event)


if __name__ == "__main__":
    unittest.main()
