"""Integração HTTP real em porta loopback; sem TestClient ou nova dependência."""
import concurrent.futures
import copy
import io
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from api.models import ComposeInput
from api.selections import SelectionError, Selections
from server import LocalServer
from services.generator_service import ResultadoGeracao
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil


class TestLocalAPI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="contracto-api-test-")
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"APPDATA": self.temp.name, "LOCALAPPDATA": self.temp.name})
        self.env.start()
        from reportlab.pdfgen import canvas
        self.template = self.root / "template.pdf"
        doc = canvas.Canvas(str(self.template))
        doc.acroForm.textfield(name="NOME", x=50, y=700, width=300, height=20)
        doc.showPage()
        doc.save()
        self.profile = Perfil(nome="Teste", modo_fluxo="formulario_simples", formato_saida="PDF",
                              formularios=[FormularioModelo("DOC", str(self.template), mapeamento={"NOME": "participante.nome"})])
        self.server = LocalServer([self.profile]).start()
        self.addCleanup(self.cleanup)
        self.output = self.root / "output"
        self.output.mkdir()
        self.output_id = self.server.jobs.selections.register(self.output, "directory")
        self.profile_id = next(iter(self.server.jobs.profiles))
        self.participant = {"nome_completo": "Pessoa Sintética", "cpf": "52998224725",
                            "data_assinatura": "13/09/2026", "local_assinatura": "CAMOCIM-CE"}
        self.payload = {"profile_ids": [self.profile_id], "participants": [self.participant], "output_id": self.output_id}

    def cleanup(self):
        self.server.close()
        self.env.stop()
        self.temp.cleanup()

    def http(self, path, data=None, method=None, headers=None, raw=None):
        h = {"Authorization": f"Bearer {self.server.token}", "Origin": self.server.origin,
             "Content-Type": "application/json"}
        for k, v in (headers or {}).items():
            if v is None:
                h.pop(k, None)
            else:
                h[k] = v
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        req = Request(self.server.origin + path, data=body, headers=h, method=method or ("POST" if body is not None else "GET"))
        ultimo_erro = None
        for _ in range(2):
            try:
                response = build_opener(ProxyHandler({})).open(req, timeout=5)
                break
            except HTTPError as exc:
                response = exc
                break
            except (ConnectionAbortedError, ConnectionResetError) as exc:
                ultimo_erro = exc
        else:
            raise ultimo_erro
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

    def test_health_and_no_paths_in_capabilities_or_catalog(self):
        for route in ("health", "capabilities", "profiles"):
            status, data = self.http("/api/v1/" + route)
            self.assertEqual(status, 200)
            self.assertNotIn(str(self.root), json.dumps(data))

    def test_auth_origin_host_methods(self):
        for headers, expected in [({"Authorization": None}, 401), ({"Authorization": "Bearer wrong"}, 401),
                                  ({"Origin": "null"}, 403), ({"Origin": None}, 403),
                                  ({"Origin": "https://evil.invalid"}, 403), ({"Host": "evil.invalid"}, 403)]:
            self.assertEqual(self.http("/api/v1/health", headers=headers)[0], expected)
        self.assertEqual(self.http("/api/v1/health", method="DELETE")[0], 405)
        self.assertEqual(self.http("/api/v1/health?token=secret")[0], 400)
        self.assertEqual(self.http("/docs")[0], 404)
        self.assertEqual(self.http("/openapi.json")[0], 404)

    def test_invalid_json_size_and_paths_rejected(self):
        for payload in ({**self.payload, "pasta_saida": str(self.root)},
                        {**self.payload, "output_id": "../../escape"},
                        {**self.payload, "participants": []}):
            status, response = self.http("/api/v1/jobs/generate", payload)
            self.assertEqual(status, 422)
            self.assertNotIn(self.participant["cpf"], json.dumps(response))
        self.assertEqual(self.http("/api/v1/jobs/generate", raw=b"{")[0], 422)
        self.assertEqual(self.http("/api/v1/jobs/generate", raw=b"x" * (1024 * 1024 + 1))[0], 413)
        self.assertEqual(self.http("/api/v1/jobs/generate", self.payload, headers={"Content-Type": "text/plain"})[0], 415)
        self.assertFalse(list(self.output.iterdir()))

    def test_unknown_selection_profile_and_job(self):
        self.assertEqual(self.http("/api/v1/jobs/generate", {**self.payload, "output_id": "a" * 32})[0], 422)
        self.assertEqual(self.http("/api/v1/profiles/compose", {"profile_ids": ["b" * 32]})[0], 404)
        self.assertEqual(self.http("/api/v1/jobs/absent")[0], 404)
        self.assertEqual(self.http("/api/v1/jobs/absent/cancel", {})[0], 404)

    def test_compose_conflict(self):
        first = self.server.jobs.profiles[self.profile_id]
        first.campos_entrada = [CampoEntrada("campo", "Campo", tipo="TEXTO")]
        second = copy.deepcopy(first)
        second.campos_entrada[0].tipo = "DATA"
        self.server.jobs.profiles["c" * 32] = second
        self.assertEqual(self.http("/api/v1/profiles/compose", {"profile_ids": [self.profile_id]})[0], 200)
        self.assertEqual(self.http("/api/v1/profiles/compose", {"profile_ids": [self.profile_id, "c" * 32]})[0], 409)

    def test_generate_without_word_gs_then_process_keeps_original(self):
        with patch("api.jobs.capabilities", return_value={"word": False, "ghostscript": False, "pdf": True}):
            status, job = self.http("/api/v1/jobs/generate", self.payload)
            self.assertEqual(status, 202, job)
            generated = self.wait_job(job["job_id"])
            self.assertEqual(generated["status"], "completed", generated)
            original = self.server.jobs.selections.resolve(generated["file_ids"][0], "file")
            from pypdf import PdfReader
            with original.open("rb") as stream:
                self.assertEqual(PdfReader(stream).get_fields()["NOME"]["/V"], self.participant["nome_completo"])
            status, process = self.http("/api/v1/jobs/process", {
                "participants": [self.participant], "output_id": self.output_id,
                "file_ids": generated["file_ids"], "format": "PDF"})
            self.assertEqual(status, 202)
            self.assertEqual(self.wait_job(process["job_id"])["status"], "completed")
            self.assertTrue(original.is_file())
            self.assertFalse(list(self.output.glob(".contracto-*")))

    def test_missing_capabilities_reject_before_job(self):
        rtf = self.root / "input.rtf"
        rtf.write_text(r"{\rtf1 test}")
        file_id = self.server.jobs.selections.register(rtf, "file")
        payload = {"participants": [self.participant], "output_id": self.output_id,
                   "attachments": [{"file_id": file_id, "document_type": "CONTRATO"}]}
        with patch("api.jobs.capabilities", return_value={"word": False, "ghostscript": False}):
            self.assertEqual(self.http("/api/v1/jobs/process", payload)[1]["code"], "word_unavailable")
            self.assertEqual(self.http("/api/v1/jobs/process", {**payload, "format": "PDF/A-2b"})[1]["code"], "ghostscript_unavailable")
        self.assertFalse(self.server.jobs._states)

    def test_cancel_running_and_queued_cleanup(self):
        started = threading.Event()
        def blocking(_participants, _profiles, folder, cancel_event, **kwargs):
            (folder / "partial.pdf").write_bytes(b"partial")
            started.set()
            cancel_event.wait(5)
            from services.pdfa_converter import ProcessoCanceladoError
            raise ProcessoCanceladoError()
        with patch("api.jobs.gerar_documentos_de_perfis", side_effect=blocking):
            _, first = self.http("/api/v1/jobs/generate", self.payload)
            self.assertTrue(started.wait(2))
            _, second = self.http("/api/v1/jobs/generate", self.payload)
            self.assertEqual(self.http(f"/api/v1/jobs/{second['job_id']}/cancel", {})[1]["status"], "cancelled")
            self.http(f"/api/v1/jobs/{first['job_id']}/cancel", {})
            self.assertEqual(self.wait_job(first["job_id"])["status"], "cancelled")
        # O estado terminal deve corresponder ao fim da limpeza.
        self.assertFalse(list(self.output.iterdir()))

    def test_worker_errors_do_not_leak_and_next_job_runs(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        logger = logging.getLogger("contracto")
        logger.addHandler(handler)
        try:
            def fail(*args, **kwargs):
                from utils.logger import obter_logger
                obter_logger("geracao").error("private %s %s", self.participant, self.root)
                raise ValueError(str(self.root) + self.participant["cpf"])
            with patch("api.jobs.gerar_documentos_de_perfis", side_effect=fail):
                _, job = self.http("/api/v1/jobs/generate", self.payload)
                result = self.wait_job(job["job_id"])
            self.assertEqual(result["status"], "failed")
            self.assertNotIn(str(self.root), json.dumps(result) + output.getvalue())
            self.assertNotIn(self.participant["cpf"], json.dumps(result) + output.getvalue())
            _, job = self.http("/api/v1/jobs/generate", self.payload)
            self.assertEqual(self.wait_job(job["job_id"])["status"], "completed")
        finally:
            logger.removeHandler(handler)

    def test_concurrent_submissions_unique_complete(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(lambda _: self.http("/api/v1/jobs/generate", self.payload), range(12)))
        keys = [r[1]["job_id"] for r in results]
        self.assertEqual(len(set(keys)), 12)
        for key in keys:
            self.assertEqual(self.wait_job(key)["status"], "completed")

    def test_shutdown_invalidates_token_selections_and_socket(self):
        port = int(self.server.authority.split(":")[1])
        self.server.close()
        self.assertEqual(self.server.token, "")
        with self.assertRaises(SelectionError):
            self.server.jobs.selections.resolve(self.output_id, "directory")
        with socket.socket() as sock:
            self.assertNotEqual(sock.connect_ex(("127.0.0.1", port)), 0)

    def test_declared_required_field_rejected_over_http(self):
        self.server.jobs.profiles[self.profile_id].campos_entrada = [CampoEntrada("renda", "Renda", tipo="MOEDA")]
        status, result = self.http("/api/v1/jobs/generate", self.payload)
        self.assertEqual(status, 422)
        self.assertEqual(result["code"], "invalid_fields")
        self.assertEqual(result["issues"], [{"participant": 1, "field": "renda"}])
        self.assertFalse(self.server.jobs._states)

    def test_bridge_opens_only_completed_result_by_id(self):
        from webview_shell import ShellBridge
        from unittest.mock import Mock
        bridge = ShellBridge(self.server)
        window = Mock()
        window.get_current_url.return_value = None
        bridge._attach(window)
        self.assertFalse(bridge.open_result(str(self.root))["ok"])
        _, job = self.http("/api/v1/jobs/generate", self.payload)
        self.assertEqual(self.wait_job(job["job_id"])["status"], "completed")
        with patch("utils.files_fs.abrir_pasta", return_value=True) as open_folder:
            self.assertTrue(bridge.open_result(job["job_id"])["ok"])
            self.assertEqual(open_folder.call_args.args[0].parent, self.output)

    def test_undeclared_dynamic_field_rejected(self):
        participant = {**self.participant, "campos_dinamicos": {"undeclared": "value"}}
        status, result = self.http("/api/v1/jobs/generate", {**self.payload, "participants": [participant]})
        self.assertEqual(status, 422)
        self.assertEqual(result["code"], "unknown_fields")

    def test_process_cancellation_cleans_partial_and_keeps_input(self):
        file_id = self.server.jobs.selections.register(self.template, "file")
        started = threading.Event()
        def blocking(folder, *_args, cancel_event, **kwargs):
            (folder / "partial.pdf").write_bytes(b"partial")
            started.set()
            cancel_event.wait(3)
            from services.pdfa_converter import ProcessoCanceladoError
            raise ProcessoCanceladoError()
        with patch("api.jobs.executar_etapa2", side_effect=blocking):
            _, job = self.http("/api/v1/jobs/process", {"participants": [self.participant],
                                "output_id": self.output_id, "file_ids": [file_id]})
            self.assertTrue(started.wait(1))
            self.http(f"/api/v1/jobs/{job['job_id']}/cancel", {})
            self.assertEqual(self.wait_job(job["job_id"])["status"], "cancelled")
        self.assertTrue(self.template.is_file())
        self.assertFalse(list(self.output.iterdir()))

    def test_shutdown_waits_for_cleanup_of_active_job(self):
        started = threading.Event()
        def blocking(_participants, _profiles, folder, cancel_event, **kwargs):
            (folder / "partial.pdf").write_bytes(b"partial")
            started.set()
            cancel_event.wait(3)
            from services.pdfa_converter import ProcessoCanceladoError
            raise ProcessoCanceladoError()
        with patch("api.jobs.gerar_documentos_de_perfis", side_effect=blocking):
            self.http("/api/v1/jobs/generate", self.payload)
            self.assertTrue(started.wait(1))
            self.server.close()
        self.assertFalse(list(self.output.iterdir()))


class TestSelections(unittest.TestCase):
    def test_expiry_and_wrong_kind(self):
        with tempfile.TemporaryDirectory() as folder:
            selections = Selections(ttl=0)
            key = selections.register(Path(folder), "directory")
            with self.assertRaises(SelectionError):
                selections.resolve(key, "directory")
            selections = Selections()
            key = selections.register(Path(folder), "directory")
            with self.assertRaises(SelectionError):
                selections.resolve(key, "file")

    def test_import_without_tk(self):
        code = "import app.server,sys; assert not any(x in sys.modules for x in ('tkinter','customtkinter','ui.main_window'))"
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
