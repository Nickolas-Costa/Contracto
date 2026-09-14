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
            self.assertEqual(bridge.request("GET", "/api/v1/health")["status"], 403)
            public = {name for name in dir(bridge) if not name.startswith("_") and callable(getattr(bridge, name))}
            self.assertEqual(public, {"request", "select_file", "select_output", "open_result", "get_file"})
