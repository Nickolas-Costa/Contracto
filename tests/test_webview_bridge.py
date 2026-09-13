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
