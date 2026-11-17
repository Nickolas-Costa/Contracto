"""Documentos do cliente (intake) e "gerar mesmo assim" em perfis simples."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from server import LocalServer
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil


class Base(unittest.TestCase):
    perfis = []

    def setUp(self):
        import gc
        gc.collect()
        self.temp = tempfile.TemporaryDirectory(prefix="contracto-intake-test-")
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"APPDATA": self.temp.name, "LOCALAPPDATA": self.temp.name})
        self.env.start()
        self.server = LocalServer(self.perfis).start()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.server.close()
        self.env.stop()
        self.temp.cleanup()

    def http(self, path, data=None):
        h = {"Authorization": f"Bearer {self.server.token}", "Origin": self.server.origin, "Content-Type": "application/json"}
        body = json.dumps(data).encode() if data is not None else None
        req = Request(self.server.origin + path, data=body, headers=h, method="POST" if body is not None else "GET")
        try:
            response = build_opener(ProxyHandler({})).open(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read())

    def wait_job(self, key):
        for _ in range(200):
            status, job = self.http(f"/api/v1/jobs/{key}")
            if job["status"] in {"completed", "failed", "cancelled"}:
                return job
            time.sleep(0.02)
        self.fail("Trabalho não terminou")


class TestIntake(Base):
    def _pdf(self, nome):
        from reportlab.pdfgen import canvas
        caminho = self.root / nome
        doc = canvas.Canvas(str(caminho))
        doc.drawString(50, 700, "Documento do cliente")
        doc.showPage()
        doc.save()
        return caminho

    def test_pdf_entra_numa_area_privada_e_o_original_fica_intacto(self):
        original = self._pdf("rg.pdf")
        bytes_antes = original.read_bytes()
        ids = [self.server.jobs.selections.register(original, "convert")]
        status, job = self.http("/api/v1/jobs/intake", {"file_ids": ids})
        self.assertEqual(status, 202, job)
        pronto = self.wait_job(job["job_id"])
        self.assertEqual(pronto["status"], "completed", pronto)
        self.assertEqual([f["name"] for f in pronto["files"]], ["rg.pdf"])
        copia = self.server.jobs.selections.resolve(pronto["files"][0]["file_id"], "file")
        self.assertNotEqual(copia.parent, original.parent)
        self.assertEqual(original.read_bytes(), bytes_antes)
        pasta = self.server.jobs._intake_dir
        self.server.jobs.close()
        self.assertFalse(pasta.exists(), "a área privada some ao encerrar a sessão")

    def test_formato_fora_da_lista_e_recusado(self):
        txt = self.root / "nota.txt"
        txt.write_text("x")
        with self.assertRaises(Exception):
            self.server.jobs.selections.register(txt, "convert")


class TestGerarMesmoAssim(Base):
    def setUp(self):
        from reportlab.pdfgen import canvas
        self.perfis = []
        super().setUp()
        modelo = self.root / "modelo.pdf"
        doc = canvas.Canvas(str(modelo))
        for i, nome in enumerate(("NOME", "OBS")):
            doc.acroForm.textfield(name=nome, x=40, y=700 - i * 40, width=300, height=25)
        doc.showPage()
        doc.save()
        campos = [CampoEntrada(id="obs", rotulo="Observação", obrigatorio=True, escopo="participante")]
        for modo in ("formulario_simples", "contrato"):
            perfil = Perfil(nome="QA " + modo, modo_fluxo=modo, max_participantes=1, formato_saida="PDF", campos_entrada=campos,
                            formularios=[FormularioModelo("DOC", str(modelo), mapeamento={"NOME": "participante.nome", "OBS": "participante.obs"})])
            self.server.jobs.profiles[f"{len(self.server.jobs.profiles):032x}"] = perfil
        self.saida = self.root / "saida"
        self.saida.mkdir()
        self.saida_id = self.server.jobs.selections.register(self.saida, "directory")

    def _gerar(self, modo, ignorar):
        pid = next(k for k, p in self.server.jobs.profiles.items() if p.modo_fluxo == modo)
        participante = {"nome_completo": "FULANO", "cpf": "52998224725", "data_assinatura": "01/09/2026",
                        "local_assinatura": "X", "campos_dinamicos": {"obs": ""}}
        return self.http("/api/v1/jobs/generate", {"profile_ids": [pid], "participants": [participante], "output_id": self.saida_id,
                                                   "ignorar_pendencias": ignorar})

    def test_simples_gera_com_campo_obrigatorio_vazio_so_quando_o_usuario_aceita(self):
        status, dados = self._gerar("formulario_simples", False)
        self.assertEqual(status, 422, dados)
        status, job = self._gerar("formulario_simples", True)
        self.assertEqual(status, 202, job)
        self.assertEqual(self.wait_job(job["job_id"])["status"], "completed")

    def test_contrato_continua_estrito(self):
        status, dados = self._gerar("contrato", True)
        self.assertEqual(status, 422, dados)

    def test_identidade_continua_obrigatoria_mesmo_assim(self):
        pid = next(k for k, p in self.server.jobs.profiles.items() if p.modo_fluxo == "formulario_simples")
        participante = {"nome_completo": "FULANO", "cpf": "11111111111", "data_assinatura": "01/09/2026",
                        "local_assinatura": "X", "campos_dinamicos": {"obs": ""}}
        status, dados = self.http("/api/v1/jobs/generate", {"profile_ids": [pid], "participants": [participante],
                                                           "output_id": self.saida_id, "ignorar_pendencias": True})
        self.assertEqual(status, 422, dados)


if __name__ == "__main__":
    unittest.main()
