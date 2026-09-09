"""Caminhos seguros: fallbacks sem KeyError e backup de JSON corrompido."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils import config_manager, profile_manager
from utils.caminhos import (
    diretorio_dados_local,
    guardar_copia_corrompida,
    pasta_downloads,
)


class TestPastaDownloads(unittest.TestCase):
    def test_sem_userprofile_nao_levanta_keyerror(self):
        ambiente = {k: v for k, v in os.environ.items() if k != "USERPROFILE"}
        with patch.dict(os.environ, ambiente, clear=True):
            resultado = pasta_downloads()
        self.assertIsInstance(resultado, Path)

    def test_prefere_downloads_do_userprofile(self):
        with tempfile.TemporaryDirectory() as d:
            downloads = Path(d) / "Downloads"
            downloads.mkdir()
            with patch.dict(os.environ, {"USERPROFILE": d}):
                self.assertEqual(pasta_downloads(), downloads)

    def test_sem_downloads_cai_para_home(self):
        with tempfile.TemporaryDirectory() as d:
            casa = Path(d) / "casa"
            casa.mkdir()
            with patch.dict(os.environ, {"USERPROFILE": d}), patch.object(
                Path, "home", return_value=casa
            ):
                self.assertEqual(pasta_downloads(), casa)


class TestDiretorioDadosLocal(unittest.TestCase):
    def test_sem_appdata_usa_primeiro_gravavel(self):
        ambiente = {
            k: v
            for k, v in os.environ.items()
            if k not in ("APPDATA", "LOCALAPPDATA")
        }
        with patch.dict(os.environ, ambiente, clear=True):
            resultado = diretorio_dados_local("ContractoTeste")
        self.assertEqual(resultado.name, "ContractoTeste")
        self.assertTrue(os.access(resultado, os.W_OK))


class TestCopiaCorrompida(unittest.TestCase):
    def test_renomeia_com_marca_de_data(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "config.json"
            alvo.write_text("{invalido", encoding="utf-8")
            copia = guardar_copia_corrompida(alvo)
            self.assertIsNotNone(copia)
            self.assertFalse(alvo.exists())
            self.assertTrue(copia.exists())
            self.assertIn(".corrompido-", copia.name)

    def test_inexistente_devolve_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(
                guardar_copia_corrompida(Path(d) / "ausente.json")
            )


class TestConfigCorrompida(unittest.TestCase):
    def test_backup_e_padroes(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "contracto_config.json"
            alvo.write_text("{invalido", encoding="utf-8")
            with patch.object(
                config_manager, "_caminho_config", return_value=alvo
            ):
                config_manager.invalidar_cache()
                try:
                    config = config_manager.carregar_config(forcar_disco=True)
                finally:
                    config_manager.invalidar_cache()
            self.assertEqual(config["aparencia"], "light")
            copias = list(Path(d).glob("contracto_config.json.corrompido-*"))
            self.assertEqual(len(copias), 1)


class TestPerfisCorrompidos(unittest.TestCase):
    def test_backup_e_iniciais_preservados(self):
        with tempfile.TemporaryDirectory() as d:
            alvo = Path(d) / "contracto_profiles.json"
            alvo.write_text("[invalido", encoding="utf-8")
            with patch.object(
                profile_manager, "_caminho_perfis", return_value=alvo
            ):
                profile_manager.invalidar_cache()
                try:
                    perfis = profile_manager.carregar_perfis(forcar_disco=True)
                finally:
                    profile_manager.invalidar_cache()
            self.assertTrue(len(perfis) > 0)
            copias = list(Path(d).glob("contracto_profiles.json.corrompido-*"))
            self.assertEqual(len(copias), 1)


class TestAbrirPasta(unittest.TestCase):
    def test_inexistente_nao_levanta(self):
        from ui.main_window import MainWindow

        self.assertFalse(MainWindow._abrir_pasta(Path("pasta_que_nao_existe")))

    def test_valida_abre_uma_vez(self):
        from ui.main_window import MainWindow

        with tempfile.TemporaryDirectory() as d:
            with patch("os.startfile", create=True) as abrir:
                self.assertTrue(MainWindow._abrir_pasta(Path(d)))
                abrir.assert_called_once()


if __name__ == "__main__":
    unittest.main()
