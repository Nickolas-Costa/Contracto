"""Prova headless: backend roda sem Tk/CustomTkinter (gate pywebview/Tauri).

Cobre: combinar_perfis (multi-seleção v4.5.9) → gerar_documentos_de_perfis →
ports (storage/binaries/dialog-interface) sem instanciar UI.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from models.participant import Participant
from services.generator_service import gerar_documentos_de_perfis
from services.profile_composer import combinar_perfis
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil


def _criar_pdf(caminho: Path, campo: str) -> None:
    doc = canvas.Canvas(str(caminho), pagesize=(300, 200))
    doc.drawString(20, 140, campo)
    doc.acroForm.textfield(name=campo, x=20, y=100, width=200, height=20)
    doc.showPage()
    doc.save()


class TestHeadlessBackend(unittest.TestCase):
    def test_combinar_e_gerar_sem_ui(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            a, b = pasta / "a.pdf", pasta / "b.pdf"
            _criar_pdf(a, "NOME")
            _criar_pdf(b, "NOME")
            p1 = Perfil(
                nome="ITBI-like",
                formularios=[FormularioModelo("DOC-A", str(a), mapeamento={"NOME": "participante.nome"})],
                campos_entrada=[CampoEntrada(id="nome", rotulo="Nome")],
                modo_fluxo="formulario_simples",
            )
            p2 = Perfil(
                nome="Isencao-like",
                formularios=[FormularioModelo("DOC-B", str(b), mapeamento={"NOME": "participante.nome"})],
                campos_entrada=[CampoEntrada(id="telefone", rotulo="Telefone")],
                modo_fluxo="formulario_simples",
            )
            combinado = combinar_perfis([p1, p2])
            self.assertEqual(combinado.erros, [])
            self.assertIn("formulários selecionados", combinado.perfil.nome)

            res = gerar_documentos_de_perfis(
                [Participant(nome_completo="Maria", cpf="52998224725")],
                [p1, p2],
                pasta,
            )
            self.assertEqual(len(res.arquivos_gerados), 2)
            for arq in res.arquivos_gerados:
                self.assertEqual(PdfReader(str(arq)).get_fields()["NOME"].value, "Maria")

    def test_ports_sem_tkinter(self):
        import ports.binaries as binaries
        import ports.storage as storage

        # storage não deve exigir Tk
        self.assertTrue(str(storage.get_templates_dir()).endswith("templates"))
        # binaries só reporta status, nunca levanta por falta de Word/GS
        gs = binaries.ghostscript_status()
        word = binaries.word_status()
        self.assertEqual(gs.nome, "ghostscript")
        self.assertEqual(word.nome, "word")
        # dialog expõe interface sem importar tkinter no import do módulo
        import ports.dialog as dialog

        self.assertTrue(callable(dialog.selecionar_pasta))


if __name__ == "__main__":
    unittest.main()
