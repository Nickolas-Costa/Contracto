"""Cópia de segurança de perfis e configurações (ZIP com data e hora)."""

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils import backup, config_manager, profile_manager
from utils.profile_manager import CampoEntrada, Perfil


class TestBackup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.patch_perf = patch.object(
            profile_manager, "_caminho_perfis", return_value=base / "p.json"
        )
        self.patch_conf = patch.object(
            config_manager, "_caminho_config", return_value=base / "c.json"
        )
        self.patch_perf.start()
        self.patch_conf.start()
        self.addCleanup(self.patch_perf.stop)
        self.addCleanup(self.patch_conf.stop)
        profile_manager.invalidar_cache()
        config_manager.invalidar_cache()
        self.addCleanup(profile_manager.invalidar_cache)
        self.addCleanup(config_manager.invalidar_cache)
        profile_manager.salvar_perfis([
            Perfil(nome="P1", campos_entrada=[CampoEntrada(id="a", rotulo="A")])
        ])
        config_manager.salvar_config({**config_manager.obter_defaults(), "aparencia": "dark"})

    def test_criar_e_listar(self):
        destino = backup.criar_backup(Path(self.tmp.name))
        self.assertTrue(destino.name.startswith("backup-"))
        self.assertEqual(backup.listar_backups(Path(self.tmp.name)), [destino])

    def test_restaurar_substitui_tudo(self):
        destino = backup.criar_backup(Path(self.tmp.name))
        profile_manager.salvar_perfis([])
        backup.restaurar_backup(destino)
        # P1 volta; os perfis iniciais acompanham sempre a carga.
        self.assertIn("P1", profile_manager.listar_nomes_perfis())
        self.assertEqual(config_manager.obter("aparencia"), "dark")

    def test_zip_invalido_rejeita(self):
        ruim = Path(self.tmp.name) / "ruim.zip"
        ruim.write_bytes(b"nao-e-zip")
        with self.assertRaises(ValueError):
            backup.restaurar_backup(ruim)

    def test_conteudo_incompleto_rejeita(self):
        parcial = Path(self.tmp.name) / "parcial.zip"
        with zipfile.ZipFile(parcial, "w") as pacote:
            pacote.writestr("contracto_config.json", "{}")
        with self.assertRaises(ValueError):
            backup.restaurar_backup(parcial)


if __name__ == "__main__":
    unittest.main()
