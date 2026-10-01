import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from server import LocalServer
from webview_shell import ShellBridge
from ports.webview_dialog import WebViewDialogs


class TestWebViewBridge(unittest.TestCase):
    def test_http_bridge_and_navigation_rejection(self):
        with LocalServer(profiles=[]) as server:
            bridge = ShellBridge(server)
            window = Mock()
            window.get_current_url.return_value = None
            bridge._attach(window)
            result = bridge.request("GET", "/api/v1/health")
            self.assertEqual(result["status"], 200)
            self.assertNotIn(server.token, str(result))
            self.assertEqual(bridge.request("GET", "https://evil.invalid")["status"], 400)
            window.get_current_url.return_value = "https://evil.invalid"
            self.assertEqual(bridge.request("GET", "/api/v1/health")["status"], 403)
            self.assertEqual(bridge.select_output()["code"], "unauthorized_page")

    def test_native_dialog_cancel_and_selection_id(self):
        with tempfile.TemporaryDirectory() as folder, LocalServer(profiles=[]) as server:
            window = Mock()
            window.get_current_url.return_value = None
            window.create_file_dialog.return_value = None
            bridge = ShellBridge(server)
            bridge._attach(window)
            self.assertEqual(bridge.select_file(), {"cancelled": True})
            window.create_file_dialog.return_value = [folder]
            result = bridge.select_output()
            self.assertNotIn(folder, str(result))
            self.assertEqual(server.jobs.selections.resolve(result["selection_id"], "directory"), Path(folder).resolve())
            self.assertEqual(WebViewDialogs(window).selecionar_pasta(), Path(folder))

    def test_apenas_url_local_registrada_autorizada(self):
        with LocalServer(profiles=[]) as server:
            local = "file:///C:/app/frontend/index.html"
            bridge = ShellBridge(server, frontend_url=local)
            window = Mock()
            bridge._attach(window)
            window.get_current_url.return_value = local
            self.assertEqual(bridge.request("GET", "/api/v1/health")["status"], 200)
            window.get_current_url.return_value = local + "?x=1"
            self.assertEqual(bridge.request("GET", "/api/v1/health")["status"], 403)
            window.get_current_url.return_value = None
            self.assertEqual(bridge.request("GET", "/api/v1/health")["status"], 200)
            public = {name for name in dir(bridge) if not name.startswith("_") and callable(getattr(bridge, name))}
            self.assertEqual(public, {"request", "select_file", "select_output", "select_backup", "select_documents", "open_result", "open_file", "import_profile", "export_profile", "get_file"})

    def test_select_documents_registra_multiplos_para_conversao(self):
        with tempfile.TemporaryDirectory() as folder, LocalServer(profiles=[]) as server:
            a = Path(folder, "a.pdf")
            b = Path(folder, "b.docx")
            a.write_bytes(b"%PDF-1.4 sintese")
            b.write_bytes(b"PK sintese")
            txt = Path(folder, "c.txt")
            txt.write_text("ignorado")
            window = Mock()
            window.get_current_url.return_value = None
            bridge = ShellBridge(server)
            bridge._attach(window)
            window.create_file_dialog.return_value = None
            self.assertEqual(bridge.select_documents(), {"cancelled": True})
            window.create_file_dialog.return_value = [str(a), str(b), str(txt)]
            result = bridge.select_documents()
            self.assertEqual(len(result["selection_ids"]), 2)
            self.assertEqual(result["names"], ["a.pdf", "b.docx"])
            self.assertEqual(result["rejected"], 1)
            for sid in result["selection_ids"]:
                self.assertTrue(server.jobs.selections.resolve(sid, "convert").is_file())
            self.assertNotIn(folder, str(result))

    def test_open_file_no_leitor_padrao(self):
        import sys
        with tempfile.TemporaryDirectory() as folder, LocalServer(profiles=[]) as server:
            pdf = Path(folder, "doc.pdf")
            pdf.write_bytes(b"%PDF-1.4 sintese")
            sid = server.jobs.selections.register(pdf, "file")
            window = Mock()
            window.get_current_url.return_value = None
            bridge = ShellBridge(server)
            bridge._attach(window)
            self.assertEqual(bridge.open_file("nao-hex"), {"ok": False, "code": "invalid_request"})
            modest = sys.modules.get("utils.files_fs")
            from unittest.mock import patch
            with patch.object(modest, "abrir_arquivo", return_value=True) as abrir:
                self.assertEqual(bridge.open_file(sid), {"ok": True, "code": "opened"})
                abrir.assert_called_once()
            rtf = Path(folder, "nota.rtf")
            rtf.write_bytes(b"{\\rtf1 sintese}")
            sid_rtf = server.jobs.selections.register(rtf, "file")
            with patch.object(modest, "abrir_arquivo") as abrir:
                self.assertEqual(bridge.open_file(sid_rtf), {"ok": False, "code": "unsupported_preview"})
                abrir.assert_not_called()

    def test_import_export_profile_por_arquivo(self):
        import json
        import os
        with tempfile.TemporaryDirectory() as appdata, tempfile.TemporaryDirectory() as folder:
            anterior = {k: os.environ.get(k) for k in ("APPDATA", "LOCALAPPDATA")}
            os.environ["APPDATA"] = os.environ["LOCALAPPDATA"] = appdata
            try:
                from utils import profile_manager
                profile_manager.invalidar_cache()
                with LocalServer(profiles=[]) as server:
                    window = Mock()
                    window.get_current_url.return_value = None
                    bridge = ShellBridge(server)
                    bridge._attach(window)
                    dados = {"nome": "QA Arquivo", "modo_fluxo": "formulario_simples",
                             "formato_saida": "PDF", "max_participantes": 1,
                             "campos_entrada": [], "formularios": []}
                    origem = Path(folder, "qa.json")
                    origem.write_text(json.dumps(dados), encoding="utf-8")
                    window.create_file_dialog.return_value = [str(origem)]
                    r = bridge.import_profile()
                    self.assertEqual(r, {"ok": True, "nome": "QA Arquivo"})
                    self.assertIn("QA Arquivo", [p["name"] for p in server.jobs.catalog()])
                    # Reimportar o mesmo nome falha com validação, sem crash.
                    window.create_file_dialog.return_value = [str(origem)]
                    r2 = bridge.import_profile()
                    self.assertFalse(r2.get("ok"))
                    # Exporta para .json válido e reimportável.
                    destino = Path(folder, "saida.json")
                    window.create_file_dialog.return_value = [str(destino)]
                    re = bridge.export_profile("QA Arquivo")
                    self.assertEqual(re, {"ok": True, "nome": "QA Arquivo"})
                    recarregado = json.loads(destino.read_text(encoding="utf-8"))
                    self.assertEqual(recarregado["nome"], "QA Arquivo")
                    # Cancelamento e nomes inválidos.
                    window.create_file_dialog.return_value = None
                    self.assertEqual(bridge.import_profile(), {"cancelled": True})
                    self.assertEqual(bridge.export_profile("Inexistente"),
                                     {"ok": False, "code": "profile_not_found"})
                    self.assertEqual(bridge.export_profile(""), {"ok": False, "code": "invalid_request"})
                profile_manager.invalidar_cache()
            finally:
                for k, v in anterior.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def test_abrir_arquivo_puro(self):
        from utils import files_fs
        with tempfile.TemporaryDirectory() as folder:
            pdf = Path(folder, "doc.pdf")
            pdf.write_bytes(b"%PDF-1.4 sintese")
            self.assertFalse(files_fs.abrir_arquivo(Path(folder, "ausente.pdf")))
            self.assertFalse(files_fs.abrir_arquivo(Path(folder)))
            from unittest.mock import patch
            with patch.object(files_fs.os, "startfile", create=True) as abrir:
                self.assertTrue(files_fs.abrir_arquivo(pdf))
                abrir.assert_called_once()

    def test_url_about_blank_nao_deve_terminar_em_falha_temporaria(self):
        with LocalServer(profiles=[]) as server:
            bridge = ShellBridge(server)
            window = Mock()
            bridge._attach(window)
            window.get_current_url.return_value = "about:blank"
            self.assertEqual(bridge.request("GET", "/api/v1/health")["status"], 200)
            local = "file:///C:/app/frontend/index.html"
            bridge_ui = ShellBridge(server, frontend_url=local)
            window_ui = Mock()
            bridge_ui._attach(window_ui)
            window_ui.get_current_url.return_value = "about:blank"
            self.assertEqual(bridge_ui.request("GET", "/api/v1/health")["status"], 200)
