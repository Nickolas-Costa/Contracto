"""Conversão direta de arquivos (modo Conversão): PDF→PDF/PDF-A sem Word/GS."""
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from server import LocalServer


class TestConvertAPI(unittest.TestCase):
    def setUp(self):
        import gc
        gc.collect()
        self.temp = tempfile.TemporaryDirectory(prefix="contracto-convert-test-")
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"APPDATA": self.temp.name, "LOCALAPPDATA": self.temp.name})
        self.env.start()
        from reportlab.pdfgen import canvas
        self.pdf = self.root / "entrada.pdf"
        doc = canvas.Canvas(str(self.pdf))
        doc.drawString(50, 700, "Documento sintético para conversão")
        doc.showPage()
        doc.save()
        self.server = LocalServer([]).start()
        self.addCleanup(self.cleanup)
        self.output = self.root / "saida"
        self.output.mkdir()
        self.output_id = self.server.jobs.selections.register(self.output, "directory")
        self.file_id = self.server.jobs.selections.register(self.pdf, "convert")

    def cleanup(self):
        self.server.close()
        self.env.stop()
        self.temp.cleanup()

    def http(self, path, data=None, method=None):
        h = {"Authorization": f"Bearer {self.server.token}", "Origin": self.server.origin,
             "Content-Type": "application/json"}
        body = json.dumps(data).encode() if data is not None else None
        req = Request(self.server.origin + path, data=body, headers=h,
                      method=method or ("POST" if body is not None else "GET"))
        try:
            response = build_opener(ProxyHandler({})).open(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read())

    def wait_job(self, key):
        for _ in range(150):
            status, job = self.http(f"/api/v1/jobs/{key}")
            self.assertEqual(status, 200)
            if job["status"] in {"completed", "failed", "cancelled"}:
                return job
            time.sleep(0.02)
        self.fail("Trabalho não terminou")

    def test_capabilities_anunciam_conversao(self):
        status, caps = self.http("/api/v1/capabilities")
        self.assertEqual(status, 200)
        self.assertIn(".pdf", caps["convert_in"])
        self.assertIn(".docx", caps["convert_in"])
        self.assertEqual(caps["convert_out"], ["PDF", "PDF/A-2b"])
        self.assertNotIn(str(self.root), json.dumps(caps))

    def test_convert_pdf_para_pdf_com_nome_personalizado(self):
        payload = {"file_ids": [self.file_id], "output_id": self.output_id,
                   "format": "PDF", "nome_saida": "guia quitado",
                   "request_id": "d" * 32}
        status, job = self.http("/api/v1/jobs/convert", payload)
        self.assertEqual(status, 202, job)
        done = self.wait_job(job["job_id"])
        self.assertEqual(done["status"], "completed", done)
        self.assertEqual([f["name"] for f in done["files"]], ["guia quitado.pdf"])
        self.assertEqual(done["files"][0]["origin"], "imported")
        self.assertGreater(done["files"][0]["size_bytes"], 0)
        # Idempotência: mesmo request_id recupera o trabalho.
        status, again = self.http("/api/v1/jobs/convert", payload)
        self.assertEqual(status, 202)
        self.assertEqual(again["job_id"], job["job_id"])

    def test_convert_rejeita_duplicado_e_nome_multiplo(self):
        base = {"file_ids": [self.file_id], "output_id": self.output_id, "format": "PDF"}
        status, data = self.http("/api/v1/jobs/convert",
                                 {**base, "file_ids": [self.file_id, self.file_id]})
        self.assertEqual(status, 422)
        self.assertEqual(data["code"], "duplicate_files")
        status, data = self.http("/api/v1/jobs/convert", {**base, "nome_saida": "x"})
        # Um arquivo com nome personalizado é válido; o erro só vale p/ múltiplos.
        self.assertEqual(status, 202)
        outro = self.root / "outro.pdf"
        outro.write_bytes(self.pdf.read_bytes())
        outro_id = self.server.jobs.selections.register(outro, "convert")
        status, data = self.http("/api/v1/jobs/convert",
                                 {**base, "file_ids": [self.file_id, outro_id], "nome_saida": "x"})
        self.assertEqual(status, 422)

    def test_convert_exige_capacidade_antes_do_job(self):
        rtf = self.root / "doc.rtf"
        rtf.write_text(r"{\rtf1 teste}")
        rtf_id = self.server.jobs.selections.register(rtf, "convert")
        payload = {"file_ids": [rtf_id], "output_id": self.output_id, "format": "PDF"}
        with patch("api.jobs.capabilities",
                   return_value={"word": False, "ghostscript": False, "pdf": True,
                                 "convert_in": [".pdf"], "convert_out": ["PDF"]}):
            status, data = self.http("/api/v1/jobs/convert", payload)
            self.assertEqual(status, 409)
            self.assertEqual(data["code"], "word_unavailable")
            status, data = self.http("/api/v1/jobs/convert",
                                     {"file_ids": [self.file_id], "output_id": self.output_id,
                                      "format": "PDF/A-2b"})
            self.assertEqual(status, 409)
            self.assertEqual(data["code"], "ghostscript_unavailable")
        self.assertFalse(self.server.jobs._states)

    def test_convert_kind_rejeita_extensao_invalida(self):
        txt = self.root / "nota.txt"
        txt.write_text("texto")
        with self.assertRaises(Exception):
            self.server.jobs.selections.register(txt, "convert")


if __name__ == "__main__":
    unittest.main()
