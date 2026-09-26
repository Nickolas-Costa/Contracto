"""P0 release: PUT/DELETE perfis, backup/restore, settings restore, active profile."""
import gc
import json
import os
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from server import LocalServer


class TestP0Release(unittest.TestCase):
    def setUp(self):
        # Isolamento Tk→servidor: finalizadores pendentes de tkinter.font.Font
        # travam dentro de json.dump quando o GC os alcança numa thread do
        # Uvicorn após o root Tk ter sido destruído. Coletar no thread
        # principal antes de subir o servidor elimina a condição.
        gc.collect()
        self.temp = tempfile.TemporaryDirectory(prefix="contracto-p0-")
        self.env = patch.dict(os.environ, {"APPDATA": self.temp.name, "LOCALAPPDATA": self.temp.name})
        self.env.start()
        self.server = LocalServer([]).start()
        self.addCleanup(self.cleanup)

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

    def test_put_delete_profile_roundtrip(self):
        dados = {"nome": "P0 Perfil", "modo_fluxo": "contrato", "formato_saida": "PDF",
                 "max_participantes": 1, "campos_entrada": []}
        status, _ = self.http("/api/v1/profiles", dados)
        self.assertIn(status, (200, 201))
        # PUT atualiza sem 405
        dados2 = dict(dados, max_participantes=2)
        status, body = self.http("/api/v1/profiles/P0%20Perfil", dados2, method="PUT")
        self.assertEqual(status, 200, body)
        self.assertEqual(body.get("status"), "updated")
        # DELETE remove sem 405
        status, body = self.http("/api/v1/profiles/P0%20Perfil", method="DELETE")
        # DELETE sem corpo: urllib envia sem body; middleware permite DELETE
        self.assertEqual(status, 200, body)
        self.assertEqual(body.get("status"), "deleted")

    def test_settings_restore_and_active_and_backup(self):
        status, cfg = self.http("/api/v1/settings")
        self.assertEqual(status, 200)
        status, cfg2 = self.http("/api/v1/settings", {"local_padrao": "TESTE-XX", "tamanho_quadros": "Grande"})
        self.assertEqual(status, 200)
        self.assertEqual(cfg2["local_padrao"], "TESTE-XX")
        self.assertEqual(cfg2["tamanho_quadros"], "Grande")
        status, restaurado = self.http("/api/v1/settings/restore", {})
        self.assertEqual(status, 200)
        self.assertEqual(restaurado["local_padrao"], "CAMOCIM-CE")
        # backup cria ZIP nomeado sem vazar caminho
        status, bk = self.http("/api/v1/system/backup", {})
        self.assertEqual(status, 200)
        self.assertTrue(str(bk.get("name", "")).endswith(".zip"))
        self.assertNotIn(":\\", json.dumps(bk))
        self.assertNotIn("/", json.dumps(bk).replace(".zip", ""))

    def test_frontend_p0_ids_present(self):
        raiz = Path(__file__).resolve().parent.parent / "frontend"
        html = (raiz / "index.html").read_text(encoding="utf-8")
        for exigido in ["chk-preservar-dados", "btn-backup-perfis",
                        "btn-restaurar-perfis", "btn-cfg-restaurar", 'id="cfg-tamanho"',
                        'id="cfg-formato"', 'id="secao-sobre"', 'id="sobre-versao"']:
            self.assertIn(exigido, html, exigido)
        # btn-sobre-topo removido: Sobre agora vive dentro de Configs
        self.assertNotIn('id="btn-sobre-topo"', html)
        api = (raiz / "js/api.js").read_text(encoding="utf-8")
        for exigido in ["selectBackup", "activateProfile", "backupSystem", "restoreSystem", "restoreSettings"]:
            self.assertIn(exigido, api, exigido)
        ui = (raiz / "js/ui.js").read_text(encoding="utf-8")
        for exigido in ["cfgRestaurar", "ajudaModal", "carregarSobre", "boasVindasSePreciso", "primeira_execucao"]:
            self.assertIn(exigido, ui, exigido)
        # sobreModal substituído por carregarSobre (inline na seção Configs)
        self.assertNotIn("sobreModal", ui)


if __name__ == "__main__":
    unittest.main()
