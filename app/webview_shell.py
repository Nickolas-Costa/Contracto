"""Bootstrap de diagnóstico da base WebView; não substitui a UI de produção."""
import json
import re
import sys
import time
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from server import LocalServer
from ports.webview_dialog import WebViewDialogs


class ShellBridge:
    """JS envia DTOs, nunca token ou caminho. A autenticação fica no processo nativo."""
    def __init__(self, server):
        self._server = server
        self._window = None
        self._dialogs = None

    def _attach(self, window):
        self._window = window
        self._dialogs = WebViewDialogs(window)

    def _authorized(self):
        return (not self._server.closed and self._window is not None
                and self._window.get_current_url() in {None, "about:blank"})

    def request(self, method, path, payload=None):
        if not self._authorized():
            return {"status": 403, "data": {"code": "unauthorized_page"}}
        if method not in {"GET", "POST"} or not isinstance(path, str) or not re.fullmatch(r"/api/v1/[a-z0-9/-]+", path):
            return {"status": 400, "data": {"code": "invalid_request"}}
        try:
            body = json.dumps(payload, allow_nan=False).encode() if method == "POST" else None
            if body and len(body) > 1024 * 1024:
                return {"status": 413, "data": {"code": "body_too_large"}}
            request = Request(self._server.origin + path, data=body, method=method,
                              headers={"Authorization": f"Bearer {self._server.token}",
                                       "Origin": self._server.origin, "Content-Type": "application/json"})
            try:
                response = build_opener(ProxyHandler({})).open(request, timeout=10)
            except HTTPError as exc:
                response = exc
            with response:
                return {"status": response.status, "data": json.loads(response.read())}
        except Exception:
            return {"status": 503, "data": {"code": "local_server_unavailable"}}

    def select_file(self):
        return self._select("file")

    def select_output(self):
        return self._select("directory")

    def open_result(self, job_id):
        if not self._authorized():
            return {"ok": False, "code": "unauthorized_page"}
        try:
            from utils.files_fs import abrir_pasta
            from utils.logger import contexto_log_api
            path = self._server.jobs.result_directory(job_id)
            with contexto_log_api():
                ok = abrir_pasta(path)
            return {"ok": ok, "code": "opened" if ok else "open_failed"}
        except Exception:
            return {"ok": False, "code": "result_unavailable"}

    def _select(self, kind):
        if not self._authorized():
            return {"code": "unauthorized_page"}
        try:
            path = self._dialogs.selecionar_arquivo() if kind == "file" else self._dialogs.selecionar_pasta()
            if path is None:
                return {"cancelled": True}
            if not self._authorized():
                return {"code": "unauthorized_page"}
            return {"selection_id": self._server.jobs.selections.register(path, kind)}
        except Exception:
            return {"code": "selection_failed"}


DIAGNOSTIC_HTML = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contracto — diagnóstico local</title>
<style>body{font:16px system-ui;margin:clamp(16px,4vw,48px);color:#172435;background:#f5f7fa}
main{max-width:720px}button{font:inherit;padding:12px}pre{white-space:pre-wrap}</style>
<main><h1>Base local do Contracto</h1><p>Diagnóstico técnico. A interface de produção continua no aplicativo atual.</p>
<p id="status" role="status">Conectando…</p><button id="check" disabled>Verificar capacidades</button><pre id="result"></pre></main>
<script>window.addEventListener('pywebviewready',async()=>{
 const health=await window.pywebview.api.request('GET','/api/v1/health');
 document.getElementById('status').textContent=health.status===200?'Servidor local pronto.':'Falha ao conectar.';
 const button=document.getElementById('check');button.disabled=false;
 button.onclick=async()=>{const r=await window.pywebview.api.request('GET','/api/v1/capabilities');document.getElementById('result').textContent=JSON.stringify(r.data,null,2)};
});</script></html>"""


def main(self_test=False):
    import webview
    # Diagnóstico também funciona sem modelos: a carga real ocorre no servidor.
    errors = []
    with LocalServer(profiles=[] if self_test else None) as server:
        bridge = ShellBridge(server)
        window = webview.create_window("Contracto — diagnóstico da base", html=DIAGNOSTIC_HTML,
                                       js_api=bridge, width=900, height=650, hidden=self_test)
        bridge._attach(window)
        # O finally do context manager revoga credenciais e cancela a fila ao fechar.
        def probe():
            try:
                if not window.events.loaded.wait(15):
                    raise RuntimeError("WebView2 não iniciou")
                window.evaluate_js("window.pywebview.api.request('GET','/api/v1/health').then(r=>{window.__probe=r})")
                limit = time.monotonic() + 10
                while time.monotonic() < limit:
                    result = window.evaluate_js("window.__probe || null")
                    if result:
                        if result["status"] != 200:
                            raise RuntimeError("Bridge indisponível")
                        return
                    time.sleep(0.1)
                raise RuntimeError("Bridge não respondeu")
            except Exception as exc:
                errors.append(str(exc))
            finally:
                window.destroy()

        webview.start(probe if self_test else None, gui="edgechromium", debug=False)
    if errors:
        raise RuntimeError("; ".join(errors))
    if self_test:
        print("WEBVIEW SELF-TEST OK")


if __name__ == "__main__":
    main(self_test="--self-test" in sys.argv)
