"""Prova headless: backend roda sem Tk/CustomTkinter (gate pywebview/Tauri).

Cobre: combinar_perfis (multi-seleção v4.5.9) → gerar_documentos_de_perfis →
ports (storage/binaries/dialog-interface) sem instanciar UI.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from models.participant import Participant
from services.generator_service import gerar_documentos_de_perfis
from services.profile_composer import combinar_perfis
from services.stage2_service import executar_etapa2
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil


def _criar_pdf(caminho: Path, campo: str) -> None:
    doc = canvas.Canvas(str(caminho), pagesize=(300, 200))
    doc.drawString(20, 140, campo)
    doc.acroForm.textfield(name=campo, x=20, y=100, width=200, height=20)
    doc.showPage()
    doc.save()


class TestHeadlessBackend(unittest.TestCase):
    def test_combinar_gerar_e_organizar_sem_ui(self):
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

            etapa2 = executar_etapa2(
                pasta_base=pasta,
                participantes=[Participant(nome_completo="Maria", cpf="52998224725")],
                arquivos_gerados_etapa1=res.arquivos_gerados,
                documentos_externos={},
                formato_saida="PDF",
            )
            self.assertTrue(etapa2["sucesso"], etapa2["mensagem"])
            self.assertEqual(len(etapa2["resultado_lote"].convertidos), 2)
            for arq in res.arquivos_gerados:
                self.assertFalse(arq.exists())
                self.assertTrue((etapa2["pasta_pdfa"] / arq.name).exists())

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

    def test_rtfs_de_trabalhos_distintos_usam_pastas_temporarias_distintas(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            origem = raiz / "contrato.rtf"
            origem.write_text(r"{\rtf1 contrato}", encoding="utf-8")
            temporarios = []

            def converter(_origem, destino, **_kwargs):
                temporarios.append(destino)
                destino.write_bytes(b"%PDF-1.4\n")
                return destino

            with patch("services.rtf_converter.converter_rtf_para_pdf", side_effect=converter):
                for indice in (1, 2):
                    base = raiz / f"trabalho-{indice}"
                    base.mkdir()
                    resultado = executar_etapa2(
                        pasta_base=base,
                        participantes=[Participant(nome_completo="Maria", cpf="52998224725")],
                        arquivos_gerados_etapa1=[],
                        documentos_externos={"CONTRATO": origem},
                        formato_saida="PDF",
                    )
                    self.assertTrue(resultado["sucesso"], resultado["mensagem"])
                    self.assertEqual(len(resultado["resultado_lote"].convertidos), 1)

            self.assertEqual(len(temporarios), 2)
            self.assertNotEqual(temporarios[0].parent, temporarios[1].parent)
            self.assertFalse(any(caminho.parent.exists() for caminho in temporarios))

    @unittest.skipUnless(sys.platform == "win32", "Registro COM específico do Windows")
    def test_word_sem_registro_nao_e_reportado_como_disponivel(self):
        from ports.binaries import word_status

        with patch("winreg.OpenKey", side_effect=FileNotFoundError):
            status = word_status()

        self.assertFalse(status.disponivel)
        self.assertIsNone(status.caminho)


if __name__ == "__main__":
    unittest.main()
