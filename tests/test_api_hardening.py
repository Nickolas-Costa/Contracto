"""Bateria adversarial na API local: autenticação, limites e vazamentos.

Usa HTTP real em loopback. Nada aqui deve expor traceback, caminho local
ou aceitar requisição sem token/origem válidos.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from reportlab.pdfgen import canvas

from server import LocalServer
from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil


class BaseHardening(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="contracto-hard-")
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {"APPDATA": self.temp.name, "LOCALAPPDATA": self.temp.name})
        self.env.start()
        doc = canvas.Canvas(str(self.root / "t.pdf"))
        doc.acroForm.textfield(name="NOME", x=50, y=700, width=300, height=20)
        doc.showPage()
        doc.save()
        self.profile = Perfil(
            nome="Teste", modo_fluxo="formulario_simples", formato_saida="PDF",
            formularios=[FormularioModelo("DOC", str(self.root / "t.pdf"),
                                          mapeamento={"NOME": "participante.nome"})],
            campos_entrada=[CampoEntrada(id="apelido", rotulo="Apelido")],
        )
        self.server = LocalServer([self.profile]).start()
        self.addCleanup(self.cleanup)
        self.output = self.root / "out"
        self.output.mkdir()
        self.output_id = self.server.jobs.selections.register(self.output, "directory")
        self.profile_id = next(iter(self.server.jobs.profiles))
        self.participant = {"nome_completo": "Pessoa Sintética", "cpf": "52998224725",
                            "data_assinatura": "13/09/2026", "local_assinatura": "CAMOCIM-CE",
                            "campos_dinamicos": {"apelido": "Lico"}}
        self.payload = {"profile_ids": [self.profile_id], "participants": [self.participant],
                        "output_id": self.output_id}

    def cleanup(self):
        try:
            self.server.close()
        except Exception:
            pass
        self.env.stop()
        self.temp.cleanup()

    def http(self, path, data=None, method=None, headers=None, raw=None, token=None):
        h = {"Authorization": f"Bearer {self.server.token if token is None else token}",
             "Origin": self.server.origin, "Content-Type": "application/json"}
        for k, v in (headers or {}).items():
            if v is None:
                h.pop(k, None)
            else:
                h[k] = v
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        req = Request(self.server.origin + path, data=body, headers=h,
                      method=method or ("POST" if body is not None else "GET"))
        ultimo_erro = None
        for _ in range(2):
            try:
                response = build_opener(ProxyHandler({})).open(req, timeout=5)
                break
            except HTTPError as exc:
                response = exc
                break
            except (ConnectionAbortedError, ConnectionResetError) as exc:
                # Loopback sob carga pode derrubar a conexão; o alvo do
                # teste é o comportamento HTTP, não o TCP. Uma repetição.
                ultimo_erro = exc
        else:
            raise ultimo_erro
        with response:
            bruto = response.read()
        try:
            return response.status, json.loads(bruto) if bruto.strip() else {}
        except ValueError:
            return response.status, {}


class TestAuthLimites(BaseHardening):
    def test_bearer_case_e_espacos_rejeitados(self):
        # Espaços extras ao redor do valor são aparados pelo HTTP (RFC 7230);
        # sem o token exato, tudo abaixo deve falhar.
        for auth in ["bearer " + self.server.token, "Bearer", "Bearer ",
                     "Token " + self.server.token, ""]:
            status, data = self.http("/api/v1/health", headers={"Authorization": auth})
            self.assertEqual(status, 401, repr(auth))
            self.assertEqual(data["code"], "unauthorized")

    def test_metodos_indevidos(self):
        for method in ["PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]:
            status, _ = self.http("/api/v1/health", method=method)
            self.assertIn(status, (403, 404, 405), method)

    def test_post_em_rota_get(self):
        status, _ = self.http("/api/v1/health", data={})
        self.assertEqual(status, 405)

    def test_rota_desconhecida(self):
        for path in ["/api/v1/admin", "/api/v1/jobs-desconhecido", "/docs", "/openapi.json", "/"]:
            status, data = self.http(path)
            self.assertIn(status, (403, 404), path)
            if status == 404:
                self.assertEqual(data["code"], "invalid_route")

    def test_origem_ausente_ou_trocada(self):
        status, _ = self.http("/api/v1/health", headers={"Origin": None})
        self.assertEqual(status, 403)
        status, _ = self.http("/api/v1/health", headers={"Origin": "http://127.0.0.1:1"})
        self.assertEqual(status, 403)
        status, _ = self.http("/api/v1/health",
                              headers={"Origin": self.server.origin.replace("http://", "https://")})
        self.assertEqual(status, 403)

    def test_host_trocado(self):
        status, _ = self.http("/api/v1/health", headers={"Host": "127.0.0.1:1"})
        self.assertEqual(status, 403)
        status, _ = self.http("/api/v1/health", headers={"Host": "localhost:80"})
        self.assertEqual(status, 403)


class TestCorpoLimites(BaseHardening):
    def test_json_invalido_sem_vazamento(self):
        status, data = self.http("/api/v1/jobs/generate", raw=b"{nao-json")
        self.assertIn(status, (400, 422))
        self._sem_vazamento(data)

    def test_aninhamento_profundo_sem_vazamento(self):
        profundo = {"a": None}
        atual = profundo
        for _ in range(500):
            atual["a"] = {"a": None}
            atual = atual["a"]
        status, data = self.http("/api/v1/jobs/generate", raw=json.dumps(
            {"profile_ids": [self.profile_id], "participants": [self.participant],
             "output_id": self.output_id, "x": profundo}).encode())
        self.assertIn(status, (400, 422, 500))
        self._sem_vazamento(data)

    def test_corpo_grande_rejeitado(self):
        status, data = self.http("/api/v1/jobs/generate",
                                 raw=b'{"x":"' + b"y" * (1024 * 1024 + 10) + b'"}')
        self.assertEqual(status, 413)
        self.assertEqual(data["code"], "body_too_large")

    def test_get_com_corpo_rejeitado(self):
        status, _ = self.http("/api/v1/health", raw=b"{}", method="GET")
        self.assertEqual(status, 400)

    def test_content_type_errado(self):
        status, _ = self.http("/api/v1/jobs/generate", raw=b"{}",
                              headers={"Content-Type": "text/plain"})
        self.assertEqual(status, 415)
        status, _ = self.http("/api/v1/jobs/generate", raw=b"{}",
                              headers={"Content-Type": None})
        self.assertEqual(status, 415)

    def test_query_string_rejeitada(self):
        status, data = self.http("/api/v1/health?token=" + self.server.token)
        self.assertEqual(status, 400)
        self.assertEqual(data["code"], "invalid_query")

    def _sem_vazamento(self, data):
        texto = json.dumps(data)
        for proibido in ["Traceback", "C:\\", ".py", 'File "']:
            self.assertNotIn(proibido, texto, proibido)


class TestModelosLimites(BaseHardening):
    def _gerar(self, payload):
        return self.http("/api/v1/jobs/generate", data=payload)

    def test_participantes_fora_do_limite(self):
        p = dict(self.payload, participants=[])
        self.assertEqual(self._gerar(p)[0], 422)
        p = dict(self.payload, participants=[self.participant] * 5)
        self.assertEqual(self._gerar(p)[0], 422)

    def test_campos_dinamicos_fora_do_limite(self):
        p = dict(self.participant, campos_dinamicos={f"k{i}": "v" for i in range(201)})
        self.assertEqual(self._gerar(dict(self.payload, participants=[p]))[0], 422)
        p = dict(self.participant, campos_dinamicos={"k" * 101: "v"})
        self.assertEqual(self._gerar(dict(self.payload, participants=[p]))[0], 422)

    def test_nan_rejeitado(self):
        corpo = json.dumps({**self.payload, "x": float("nan")})
        status, data = self.http("/api/v1/jobs/generate", raw=corpo.encode())
        self.assertIn(status, (400, 422))
        self.assertNotIn("Traceback", json.dumps(data))

    def test_campo_extra_e_ids_invalidos(self):
        p = dict(self.payload, inesperado=1)
        self.assertEqual(self._gerar(p)[0], 422)
        p = dict(self.payload, profile_ids=[])
        self.assertEqual(self._gerar(p)[0], 422)
        p = dict(self.payload, profile_ids=[self.profile_id] * 2)
        status, data = self._gerar(p)
        self.assertEqual(status, 400)
        self.assertEqual(data["code"], "duplicate_profiles")
        p = dict(self.payload, profile_ids=["nao-hex"])
        self.assertEqual(self._gerar(p)[0], 422)
        p = dict(self.payload, profile_ids=["0" * 32])
        status, data = self._gerar(p)
        self.assertEqual(status, 404)
        self.assertEqual(data["code"], "profile_not_found")
        p = dict(self.payload, output_id="zzz")
        self.assertEqual(self._gerar(p)[0], 422)

    def test_formato_invalido_e_cpf_invalido(self):
        proc = {"participants": [self.participant], "output_id": self.output_id, "format": "EXE"}
        self.assertEqual(self.http("/api/v1/jobs/process", data=proc)[0], 422)
        ruim = dict(self.participant, cpf="00000000000")
        status, data = self._gerar(dict(self.payload, participants=[ruim]))
        self.assertEqual(status, 422)
        self.assertEqual(data["code"], "invalid_participants")


class TestRoteamentoTrabalhos(BaseHardening):
    def test_job_desconhecido_e_travessia(self):
        for job_id in ["0" * 32, "x" * 200, "..%2F..%2Fetc", "null", "undefined"]:
            status, data = self.http(f"/api/v1/jobs/{job_id}")
            self.assertEqual(status, 404, job_id)
            self.assertIn(data["code"], {"job_not_found", "invalid_route"})
            self.assertNotIn("Traceback", json.dumps(data))
            status, _ = self.http(f"/api/v1/jobs/{job_id}/cancel", data={})
            self.assertEqual(status, 404, job_id)

    def test_cancel_idempotente_apos_concluir(self):
        status, job = self.http("/api/v1/jobs/generate", data=self.payload)
        self.assertEqual(status, 202)
        for _ in range(150):
            status, job = self.http(f"/api/v1/jobs/{job['job_id']}")
            if job["status"] in {"completed", "failed", "cancelled"}:
                break
        self.assertEqual(job["status"], "completed")
        status, mesmo = self.http(f"/api/v1/jobs/{job['job_id']}/cancel", data={})
        self.assertEqual(status, 200)
        self.assertEqual(mesmo["status"], "completed")

    def test_cancel_sem_corpo_rejeitado(self):
        status, job = self.http("/api/v1/jobs/generate", data=self.payload)
        self.assertEqual(status, 202)
        status, _ = self.http(f"/api/v1/jobs/{job['job_id']}/cancel", raw=b"")
        self.assertEqual(status, 422)


class TestArquivosVisualizacao(BaseHardening):
    def _file_id(self):
        pdf = self.root / "ver.pdf"
        pdf.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]>>endobj\n"
                        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
                        b"0000000058 00000 n \n0000000115 00000 n \ntrailer\n"
                        b"<< /Size 4 /Root 1 0 R >>\nstartxref\n200\n%%EOF")
        return self.server.jobs.selections.register(pdf, "file")

    def test_pdf_valido_devolve_bytes(self):
        status, _ = self.http(f"/api/v1/files/{self._file_id()}")
        self.assertEqual(status, 200)

    def test_desconhecido_e_travessia(self):
        for fid in ["0" * 32, "..%2F..%2Fsegredo", "x" * 300]:
            status, data = self.http(f"/api/v1/files/{fid}")
            self.assertEqual(status, 404, fid)
            self.assertIn(data["code"], {"file_not_found", "invalid_route"})
            self.assertNotIn("Traceback", json.dumps(data))

    def test_nao_pdf_rejeitado(self):
        rtf = self.root / "doc.rtf"
        rtf.write_text("{\\rtf1 teste}", encoding="utf-8")
        fid = self.server.jobs.selections.register(rtf, "file")
        status, data = self.http(f"/api/v1/files/{fid}")
        self.assertEqual(status, 415)
        self.assertEqual(data["code"], "unsupported_preview")

    def test_sem_token_rejeitado(self):
        status, _ = self.http(f"/api/v1/files/{self._file_id()}",
                              headers={"Authorization": None})
        self.assertEqual(status, 401)

    def test_ponte_get_file(self):
        from webview_shell import ShellBridge

        class Janela:
            def get_current_url(self):
                return None

        ponte = ShellBridge(self.server)
        ponte._window = Janela()
        ok = ponte.get_file(self._file_id())
        self.assertTrue(ok["ok"])
        self.assertTrue(ok["base64"].startswith("JVBER"))
        ruim = ponte.get_file("0" * 32)
        self.assertFalse(ruim["ok"])
        self.assertFalse(ponte.get_file("")[ "ok"])


class TestIsolamentoSessao(BaseHardening):
    def test_tokens_nao_cruzam_servidores(self):
        outro = LocalServer([self.profile]).start()
        try:
            status, _ = self.http("/api/v1/health", token=outro.token)
            self.assertEqual(status, 401)
            self.assertNotEqual(outro.token, self.server.token)
        finally:
            outro.close()

    def test_sessao_encerrada_recusa(self):
        self.server.close()
        try:
            self.http("/api/v1/health")
            self.fail("conexão deveria falhar")
        except URLError:
            pass
        except Exception as exc:  # noqa: BLE001 - qualquer falha de conexão vale
            self.assertIn(type(exc).__name__, {"URLError", "ConnectionError", "RemoteDisconnected"})


if __name__ == "__main__":
    unittest.main()
