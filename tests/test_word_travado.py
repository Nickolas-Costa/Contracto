"""Aviso de Word travado: callback, encerramento seletivo e mensagens."""

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.rtf_converter import (
    RtfConversionError,
    _encerrar_word,
    _pid_do_word,
    _word_ausente,
    converter_rtf_para_pdf,
)


def _com_error(hresult=None, texto=""):
    tipo = type("com_error", (Exception,), {})
    erro = tipo(texto)
    erro.hresult = hresult
    return erro


class TestClassificacaoWordAusente(unittest.TestCase):
    def test_import_error_e_word_ausente(self):
        self.assertTrue(_word_ausente(ImportError("pywin32")))

    def test_classe_nao_registrada_e_word_ausente(self):
        self.assertTrue(_word_ausente(_com_error(-2147221164)))
        self.assertTrue(_word_ausente(_com_error(None, "Invalid class string")))

    def test_erro_generico_nao_e_ausencia(self):
        self.assertFalse(_word_ausente(ValueError("outro problema")))
        self.assertFalse(_word_ausente(_com_error(-2147467259, "falha genérica")))


class TestPidEEncerramento(unittest.TestCase):
    def test_hwnd_invalido_nao_levanta(self):
        class WordFalso:
            Hwnd = 0

        self.assertIsNone(_pid_do_word(WordFalso()))

    def test_pid_vazio_nao_encerra(self):
        self.assertFalse(_encerrar_word(None))
        self.assertFalse(_encerrar_word(0))

    def test_pid_inexistente_falha_sem_levantar(self):
        self.assertFalse(_encerrar_word(99999999))


class TestTravamentoComAviso(unittest.TestCase):
    def _rtf_valido(self, diretorio: Path) -> Path:
        rtf = diretorio / "doc.rtf"
        rtf.write_text(r"{\rtf1 teste}", encoding="utf-8")
        return rtf

    def test_avisa_com_prazo_e_encerra_no_fim(self):
        import services.rtf_converter as modulo

        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            avisos = []

            def travar_para_sempre(*args, **kwargs):
                time.sleep(30)

            with patch.object(
                modulo, "_executar_conversao_word_com", side_effect=travar_para_sempre
            ):
                with self.assertRaisesRegex(RtfConversionError, "parou de responder"):
                    converter_rtf_para_pdf(
                        self._rtf_valido(pasta),
                        pasta / "saida.pdf",
                        timeout_segundos=0,
                        prazo_aviso_segundos=1,
                        ao_travar=lambda nome, prazo, encerrar: avisos.append(
                            (nome, prazo, encerrar)
                        ),
                    )
            self.assertEqual(len(avisos), 1)
            nome, prazo, encerrar = avisos[0]
            self.assertEqual(nome, "doc.rtf")
            self.assertEqual(prazo, 1)
            encerrar()  # encerramento antecipado não levanta

    def test_word_ausente_pede_instalacao(self):
        import services.rtf_converter as modulo

        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)

            def sem_word(*args, **kwargs):
                raise ImportError("No module named 'win32com'")

            with patch.object(
                modulo, "_executar_conversao_word_com", side_effect=sem_word
            ):
                with self.assertRaisesRegex(RtfConversionError, "Microsoft Word"):
                    converter_rtf_para_pdf(
                        self._rtf_valido(pasta), pasta / "saida.pdf"
                    )


class TestModalWordTravado(unittest.TestCase):
    def test_contagem_e_fechar_agora(self):
        import customtkinter as ctk
        from ui.word_travado_modal import WordTravadoModal

        root = ctk.CTk()
        root.withdraw()
        try:
            chamadas = []
            modal = WordTravadoModal(
                root, "doc.rtf", 60, on_fechar_agora=lambda: chamadas.append(True)
            )
            self.assertIn("60", modal.lbl_contagem.cget("text"))
            modal._do_fechar_agora()
            self.assertEqual(chamadas, [True])
            self.assertIsNone(WordTravadoModal._instancia_ativa)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
