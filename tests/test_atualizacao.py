"""Atualização dentro do app (ADR 0032): manifesto do build e configuração do atualizador."""
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _build_tauri():
    spec = spec_from_file_location("build_tauri", RAIZ / "scripts" / "build_tauri.py")
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestAtualizacao(unittest.TestCase):
    def test_manifesto_aponta_para_o_instalador_da_release(self):
        quando = datetime(2026, 11, 15, 10, 0, tzinfo=timezone(timedelta(hours=-3)))
        m = _build_tauri().manifesto("9.8.7", "ASSINATURA\n", quando)
        self.assertEqual(m["version"], "9.8.7")
        self.assertEqual(m["pub_date"], "2026-11-15T13:00:00Z")  # sempre em UTC
        alvo = m["platforms"]["windows-x86_64"]
        self.assertEqual(alvo["signature"], "ASSINATURA")
        # Mesmo nome que o build grava em dist/ e a release publica; a tag não leva "v".
        self.assertEqual(alvo["url"], "https://github.com/Nickolas-Costa/Contracto/releases/download/9.8.7/Contracto_Setup_v9.8.7.exe")

    def test_configuracao_so_usa_https_e_tem_chave_publica(self):
        conf = json.loads((RAIZ / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
        atualizador = conf["plugins"]["updater"]
        self.assertTrue(conf["bundle"]["createUpdaterArtifacts"])
        self.assertGreater(len(atualizador["pubkey"]), 100)
        for endereco in atualizador["endpoints"]:
            self.assertTrue(endereco.startswith("https://github.com/Nickolas-Costa/Contracto/"), endereco)
        # A página segue sem rede: quem consulta é o Rust.
        self.assertIn("connect-src ipc: http://ipc.localhost;", conf["app"]["security"]["csp"])

    def test_chave_privada_nao_esta_no_repositorio(self):
        suspeitos = [p for p in RAIZ.glob("**/*.key") if ".venv" not in p.parts and "node_modules" not in p.parts
                     and "target" not in p.parts]
        self.assertEqual(suspeitos, [])


if __name__ == "__main__":
    unittest.main()
