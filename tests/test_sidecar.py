"""Sidecar headless (ADR 0029): aperto de mão, comandos de controle e encerramento."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))

from server import LocalServer  # noqa: E402
import sidecar  # noqa: E402


def _executar(server, *comandos):
    entrada = io.StringIO("".join(json.dumps(c) + "\n" for c in comandos))
    saida = io.StringIO()
    sidecar.servir(server, entrada, saida)
    return [json.loads(linha) for linha in saida.getvalue().splitlines()]


class TestSidecar(unittest.TestCase):
    def test_register_devolve_so_id_e_nome_e_rejeita_o_invalido(self):
        with tempfile.TemporaryDirectory() as pasta, LocalServer(profiles=[]) as server:
            pdf = Path(pasta, "a.pdf")
            pdf.write_bytes(b"%PDF-1.4")
            msgs = _executar(
                server,
                {"id": 1, "cmd": "register", "kind": "file", "path": str(pdf)},
                {"id": 2, "cmd": "register", "kind": "file", "path": str(Path(pasta, "x.txt"))},
                {"id": 3, "cmd": "register", "kind": "convert"},
                {"id": 4, "cmd": "desconhecido"},
                {"id": 5, "cmd": "result_dir", "job_id": "inexistente"},
                {"id": 6, "cmd": "file_path", "file_id": "0" * 32},
            )
            pronto, ok, ausente, sem_caminho, desconhecido, sem_job, sem_arquivo = msgs
            self.assertEqual(pronto["event"], "ready")
            self.assertEqual(pronto["origin"], server.origin)
            self.assertEqual(ok["name"], "a.pdf")
            self.assertNotIn(pasta, json.dumps(ok))
            self.assertEqual(server.jobs.selections.resolve(ok["selection_id"], "file"), pdf.resolve())
            self.assertEqual(ausente, {"id": 2, "ok": False, "code": "failed"})
            self.assertEqual(sem_caminho["code"], "invalid_request")
            self.assertEqual(desconhecido["code"], "unknown_command")
            self.assertFalse(sem_job["ok"] or sem_arquivo["ok"])

    def test_result_dir_e_file_path_so_para_ids_validos(self):
        with tempfile.TemporaryDirectory() as pasta, LocalServer(profiles=[]) as server:
            pdf = Path(pasta, "a.pdf")
            pdf.write_bytes(b"%PDF-1.4")
            fid = server.jobs.selections.register(pdf, "file")
            msgs = _executar(server, {"id": 1, "cmd": "file_path", "file_id": fid})
            self.assertEqual(Path(msgs[1]["path"]), pdf.resolve())

    def test_import_export_profile_pelo_canal_de_controle(self):
        import os
        with tempfile.TemporaryDirectory() as appdata, tempfile.TemporaryDirectory() as pasta:
            anterior = {k: os.environ.get(k) for k in ("APPDATA", "LOCALAPPDATA")}
            os.environ["APPDATA"] = os.environ["LOCALAPPDATA"] = appdata
            try:
                from utils import profile_manager
                profile_manager.invalidar_cache()
                origem, destino = Path(pasta, "qa.json"), Path(pasta, "saida.json")
                origem.write_text(json.dumps({"nome": "QA Sidecar", "modo_fluxo": "formulario_simples",
                                              "formato_saida": "PDF", "max_participantes": 1,
                                              "campos_entrada": [], "formularios": []}), encoding="utf-8")
                with LocalServer(profiles=[]) as server:
                    _, imp, exp, ausente = _executar(
                        server,
                        {"id": 1, "cmd": "import_profile", "path": str(origem)},
                        {"id": 2, "cmd": "export_profile", "nome": "QA Sidecar", "path": str(destino)},
                        {"id": 3, "cmd": "export_profile", "nome": "Inexistente", "path": str(destino)},
                    )
                self.assertEqual(imp["result"], {"ok": True, "nome": "QA Sidecar"})
                self.assertEqual(exp["result"], {"ok": True, "nome": "QA Sidecar"})
                self.assertEqual(json.loads(destino.read_text(encoding="utf-8"))["nome"], "QA Sidecar")
                self.assertEqual(ausente["result"]["code"], "profile_not_found")
                profile_manager.invalidar_cache()
            finally:
                for k, v in anterior.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    @unittest.skipUnless(sys.platform == "win32", "mutex nomeado do Windows")
    def test_segunda_instancia_avisa_e_sai_sem_subir_servidor(self):
        from utils.instancia_unica import InstanciaUnica
        saida = io.StringIO()
        with InstanciaUnica():
            sidecar.main(io.StringIO(""), saida)
        self.assertEqual([json.loads(l) for l in saida.getvalue().splitlines()], [{"event": "already_running"}])

    def test_linha_invalida_nao_derruba_e_shutdown_encerra(self):
        with LocalServer(profiles=[]) as server:
            entrada = io.StringIO('nao-json\n[1]\n{"cmd":"shutdown"}\n{"id":9,"cmd":"register"}\n')
            saida = io.StringIO()
            sidecar.servir(server, entrada, saida)
            msgs = [json.loads(linha) for linha in saida.getvalue().splitlines()]
            self.assertEqual([m.get("code") for m in msgs[1:]], ["invalid_request", "invalid_request"])
            self.assertEqual(len(msgs), 3)  # nada depois do shutdown

    def test_processo_real_aperta_a_mao_serve_http_e_sai_com_eof(self):
        proc = subprocess.Popen([sys.executable, str(RAIZ / "app" / "sidecar.py")], cwd=RAIZ / "app",
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            pronto = json.loads(proc.stdout.readline())
            self.assertEqual(pronto["event"], "ready")
            import urllib.request
            req = urllib.request.Request(pronto["origin"] + "/api/v1/health", headers={
                "Authorization": "Bearer " + pronto["token"], "Origin": pronto["origin"]})
            self.assertEqual(urllib.request.urlopen(req, timeout=10).status, 200)
        finally:
            proc.stdin.close()
            self.assertEqual(proc.wait(60), 0)
            proc.stdout.close()


if __name__ == "__main__":
    unittest.main()
