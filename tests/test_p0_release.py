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

    def _catalogo_do_disco(self):
        """Troca o servidor por um sem perfis injetados: o catálogo é o do disco, como em produção."""
        self.server.close()
        self.server = LocalServer().start()
        return lambda: [p["name"] for p in self.http("/api/v1/profiles")[1]]

    def test_perfil_excluido_some_do_catalogo_e_erro_tem_motivo(self):
        nomes = self._catalogo_do_disco()
        dados = {"nome": "P0 Some", "modo_fluxo": "contrato", "campos_entrada": []}
        self.assertEqual(self.http("/api/v1/profiles", dados)[0], 200)
        self.assertIn("P0 Some", nomes())
        # Nome repetido e JSON com chave desconhecida: 422 com motivo, não o 500 genérico.
        status, body = self.http("/api/v1/profiles", dados)
        self.assertEqual((status, body["code"]), (422, "invalid_profile"), body)
        self.assertIn("P0 Some", body["message"])
        status, body = self.http("/api/v1/profiles", {"nome": "Outro", "chave_que_nao_existe": 1})
        self.assertEqual((status, body["code"]), (422, "invalid_profile"), body)
        # Regressão: o perfil excluído seguia na lista até reiniciar o aplicativo.
        self.assertEqual(self.http("/api/v1/profiles/P0%20Some", method="DELETE")[0], 200)
        self.assertNotIn("P0 Some", nomes())

    def test_editar_pela_tela_nunca_da_500_nem_perde_mapeamento(self):
        """A tela Perfis envia a entrada do catálogo (apelidos, sem mapeamento) no PUT."""
        from utils import profile_manager
        nomes = self._catalogo_do_disco()
        self.http("/api/v1/profiles", {"nome": "P0 Edita", "modo_fluxo": "contrato", "formularios": [
            {"nome": "DOC", "caminho": "modelo.pdf", "mapeamento": {"NOME": "participante.nome"}}]})
        entrada = next(p for p in self.http("/api/v1/profiles")[1] if p["name"] == "P0 Edita")
        enviado = dict(entrada, nome="P0 Edita", modo_fluxo="contrato", formato_saida="PDF",
                       max_participantes=2, max_participants=2)
        status, body = self.http("/api/v1/profiles/P0%20Edita", enviado, method="PUT")
        self.assertEqual(status, 200, body)
        salvo = profile_manager.obter_perfil("P0 Edita")
        self.assertEqual(salvo.formularios[0].mapeamento, {"NOME": "participante.nome"})
        self.assertEqual(salvo.formularios[0].caminho, "modelo.pdf")
        self.assertEqual(salvo.max_participantes, 2)
        self.assertEqual(nomes().count("P0 Edita"), 1)
        # Renomear pela tela mantém o identificador (o catálogo nem o mostra) e os formulários.
        identificador = salvo.identificador
        status, body = self.http("/api/v1/profiles/P0%20Edita", dict(enviado, nome="P0 Novo", name="P0 Novo"), method="PUT")
        self.assertEqual(status, 200, body)
        renomeado = profile_manager.obter_perfil("P0 Novo")
        self.assertEqual((renomeado.identificador, renomeado.formularios[0].caminho), (identificador, "modelo.pdf"))
        # Chave que o perfil não tem: recusa com o nome dela, sem gravar.
        status, body = self.http("/api/v1/profiles/P0%20Novo", dict(enviado, inventada=1), method="PUT")
        self.assertEqual(status, 422, body)
        self.assertIn("inventada", body["message"])

    def test_perfil_de_fabrica_nao_e_excluido(self):
        """Excluído, ele voltava sozinho na abertura seguinte, apesar do aviso de ação definitiva."""
        nomes = self._catalogo_do_disco()
        fabrica = next(n for n in nomes() if n != "MCMV")
        status, body = self.http("/api/v1/profiles/" + fabrica.replace(" ", "%20"), method="DELETE")
        self.assertEqual((status, body["code"]), (422, "invalid_profile"), body)
        self.assertIn(fabrica, nomes())

    def test_restaurar_backup_atualiza_o_catalogo(self):
        nomes = self._catalogo_do_disco()
        self.assertEqual(self.http("/api/v1/system/backup", {})[0], 200)
        self.http("/api/v1/profiles", {"nome": "Criado Depois"})
        self.assertIn("Criado Depois", nomes())
        pacote = next((Path(self.temp.name) / "Contracto" / "backups").glob("backup-*.zip"))
        selecao = self.server.jobs.selections.register(pacote, "backup")
        status, body = self.http("/api/v1/system/restore", {"selection_id": selecao})
        self.assertEqual(status, 200, body)
        self.assertNotIn("Criado Depois", nomes())

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
                        'id="cfg-formato"']:
            self.assertIn(exigido, html, exigido)
        # Foto 6: seção Sobre saiu da Config; a versão vive no modal de Ajuda.
        self.assertNotIn('id="secao-sobre"', html)
        self.assertNotIn('id="sobre-versao"', html)
        # btn-sobre-topo removido: Sobre agora vive dentro de Configs
        self.assertNotIn('id="btn-sobre-topo"', html)
        api = (raiz / "js/api.js").read_text(encoding="utf-8")
        for exigido in ["selectBackup", "activateProfile", "backupSystem", "restoreSystem", "restoreSettings"]:
            self.assertIn(exigido, api, exigido)
        ui = (raiz / "js/ui.js").read_text(encoding="utf-8")
        for exigido in ["cfgRestaurar", "ajudaModal", "boasVindasSePreciso", "primeira_execucao"]:
            self.assertIn(exigido, ui, exigido)
        # sobreModal/carregarSobre substituídos pela versão dentro do modal de Ajuda
        self.assertNotIn("sobreModal", ui)
        self.assertNotIn("carregarSobre", ui)


if __name__ == "__main__":
    unittest.main()
