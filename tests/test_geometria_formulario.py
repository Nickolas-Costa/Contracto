"""Geometria de formulários: auditoria genérica e correções declarativas."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from services.geometria_formulario import (
    AjustarBordaEsquerda,
    DefinirRetangulo,
    DividirCampo,
    ErroGeometria,
    aplicar_correcoes,
    auditar_geometria,
    carregar_regras,
)
from utils.resource_path import caminho_recurso, modelo_configurado


def _pdf_sintetico(caminho: Path) -> None:
    doc = canvas.Canvas(str(caminho), pagesize=(600, 800))
    doc.acroForm.textfield(name="normal", x=50, y=700, width=200, height=20)
    doc.acroForm.textfield(name="sobreposto_a", x=50, y=600, width=200, height=20)
    doc.acroForm.textfield(name="sobreposto_b", x=50, y=600, width=200, height=20)
    doc.acroForm.textfield(name="sem_area", x=50, y=500, width=0, height=0)
    doc.showPage()
    doc.save()


class TestAuditoriaGenerica(unittest.TestCase):
    def test_detecta_area_zero_e_sobreposicao(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / "modelo.pdf"
            _pdf_sintetico(caminho)
            tipos = {(a.campo, a.tipo) for a in auditar_geometria(caminho)}
            self.assertIn(("sem_area", "area_zero"), tipos)
            self.assertTrue(
                any(tipo == "sobreposicao" and "sobreposto" in campo for campo, tipo in tipos)
            )
            self.assertFalse(any(campo == "normal" for campo, _ in tipos))

    def test_pdf_sem_formulario_nao_quebra(self):
        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / "vazio.pdf"
            doc = canvas.Canvas(str(caminho), pagesize=(600, 800))
            doc.drawString(50, 700, "sem campos")
            doc.showPage()
            doc.save()
            self.assertEqual(auditar_geometria(caminho), [])


class TestRegrasPolimorficas(unittest.TestCase):
    def _base(self, diretorio: Path) -> Path:
        caminho = diretorio / "base.pdf"
        doc = canvas.Canvas(str(caminho), pagesize=(600, 800))
        doc.acroForm.textfield(name="valor", x=10, y=700, width=200, height=20)
        doc.showPage()
        doc.save()
        return caminho

    def test_mesma_chamada_para_tipos_diferentes(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            regras = carregar_regras({
                "ajustar_borda_esquerda": {"valor": 300},
                "definir_retangulo": {"valor": {"ret": [300, 690, 500, 710], "tooltip": "Valor"}},
            })
            self.assertEqual(len(regras), 2)
            aplicadas = aplicar_correcoes(
                self._base(pasta), pasta / "saida.pdf", regras, esperados={"valor"}
            )
            self.assertEqual(aplicadas, ["valor", "valor"])
            leitor = PdfReader(str(pasta / "saida.pdf"))
            ret = [float(v) for v in leitor.pages[0]["/Annots"][0].get_object()["/Rect"]]
            self.assertEqual(ret[0], 300)

    def test_dividir_reaproveita_original_e_cria_irmas(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            regra = DividirCampo(
                origens=["data"],
                partes={
                    "dia": {"ret": [10, 700, 60, 720], "tooltip": "Dia"},
                    "mes": {"ret": [70, 700, 200, 720], "tooltip": "Mês"},
                },
            )
            base = pasta / "base.pdf"
            doc = canvas.Canvas(str(base), pagesize=(600, 800))
            doc.acroForm.textfield(name="data", x=10, y=700, width=200, height=20)
            doc.showPage()
            doc.save()
            aplicadas = aplicar_correcoes(base, pasta / "saida.pdf", [regra])
            self.assertEqual(aplicadas, ["dia", "mes"])
            campos = PdfReader(str(pasta / "saida.pdf")).get_fields() or {}
            self.assertIn("dia", campos)
            self.assertIn("mes", campos)
            self.assertNotIn("data", campos)

    def test_origem_ausente_falha_explicito(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            regra = DividirCampo(origens=["fantasma"], partes={"a": {"ret": [1, 1, 2, 2]}})
            with self.assertRaises(ErroGeometria):
                aplicar_correcoes(self._base(pasta), pasta / "saida.pdf", [regra])


class TestConfigDampRegressao(unittest.TestCase):
    def test_config_existe_e_cobre_damp(self):
        config = json.loads(
            caminho_recurso("assets", "config", "geometria_modelos.json").read_text(encoding="utf-8")
        )
        self.assertIn("modelo_01", config)
        self.assertIn("valor_imovel_concluido", config["modelo_01"]["ajustar_borda_esquerda"])

    def test_regras_mantem_geometria_do_asset(self):
        config = json.loads(
            caminho_recurso("assets", "config", "geometria_modelos.json").read_text(encoding="utf-8")
        )["modelo_01"]
        origem = modelo_configurado("modelo_01")
        self.assertIsNotNone(origem)
        with tempfile.TemporaryDirectory() as d:
            copia = Path(d) / "damp.pdf"
            shutil.copy2(str(origem), copia)
            esperados = (
                set(config["ajustar_borda_esquerda"])
                | set(config["dividir_campo"]["partes"])
            )
            aplicadas = aplicar_correcoes(copia, copia, carregar_regras(config), esperados)
            self.assertTrue(set(aplicadas) >= esperados)
            leitor = PdfReader(str(copia))
            widgets = {}
            for pagina in leitor.pages:
                for ref in pagina.get("/Annots", []) or []:
                    w = ref.get_object()
                    if w.get("/T"):
                        widgets[str(w["/T"])] = [float(v) for v in w["/Rect"]]
            for campo, esquerda in config["ajustar_borda_esquerda"].items():
                self.assertEqual(widgets[campo][0], esquerda, campo)


if __name__ == "__main__":
    unittest.main()
