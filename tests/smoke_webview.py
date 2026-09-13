"""Smoke real Windows/WebView2: JavaScript -> bridge -> HTTP -> encerramento."""
import os
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))


def main():
    import webview
    from server import LocalServer
    from webview_shell import ShellBridge, DIAGNOSTIC_HTML

    errors = []
    with tempfile.TemporaryDirectory(prefix="contracto-webview-") as folder:
        # Processo dedicado de teste: não carrega perfis pessoais.
        os.environ["APPDATA"] = folder
        os.environ["LOCALAPPDATA"] = folder
        with LocalServer(profiles=[]) as server:
            bridge = ShellBridge(server)
            window = webview.create_window("Contracto smoke", html=DIAGNOSTIC_HTML,
                                           js_api=bridge, hidden=True)
            bridge._attach(window)

            def probe():
                try:
                    if not window.events.loaded.wait(15):
                        raise AssertionError("WebView2 não carregou em 15s")
                    window.evaluate_js("window.pywebview.api.request('GET','/api/v1/capabilities').then(r=>{window.__contractoSmoke=r})")
                    deadline = time.monotonic() + 10
                    result = None
                    while time.monotonic() < deadline:
                        result = window.evaluate_js("window.__contractoSmoke || null")
                        if result:
                            break
                        time.sleep(0.1)
                    assert result and result["status"] == 200, result
                    assert result["data"]["pdf"] is True, result
                    assert "tkinter" not in sys.modules
                except Exception as exc:
                    errors.append(str(exc))
                finally:
                    window.destroy()

            webview.start(probe, gui="edgechromium", debug=False)
        assert server.closed and not server.token
    assert not errors, errors
    print("SMOKE WEBVIEW2: OK — JS, bridge, HTTP e encerramento reais.")


if __name__ == "__main__":
    main()
