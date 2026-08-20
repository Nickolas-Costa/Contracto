import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.profile_manager import (
    PERFIL_PADRAO_NOME,
    DocumentoExtra,
    Perfil,
    carregar_perfis,
    obter_perfil,
    salvar_perfis,
    _documentos_extras_padrao,
    _documentos_extras_sbpe,
)
from app.utils import config_manager


class TestProfileManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.profiles_path = Path(self.temp_dir.name) / "contracto_profiles.json"
        self.config_path = Path(self.temp_dir.name) / "contracto_config.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_profiles_created(self):
        """Verifica se os perfis MCMV e SBPE são criados por padrão."""
        with patch("app.utils.profile_manager._caminho_perfis", return_value=self.profiles_path):
            perfis = carregar_perfis()
            nomes = [p.nome for p in perfis]
            self.assertIn("MCMV", nomes)
            self.assertIn("SBPE", nomes)

            mcmv = next(p for p in perfis if p.nome == "MCMV")
            sbpe = next(p for p in perfis if p.nome == "SBPE")

            # MCMV deve ter 5 documentos extras padrão
            self.assertEqual(len(mcmv.documentos_extras), 5)
            # SBPE deve ter 6 documentos extras (incluindo Cédula de Crédito)
            self.assertEqual(len(sbpe.documentos_extras), 6)
            rotulos_sbpe = [d.rotulo for d in sbpe.documentos_extras]
            self.assertIn("Cédula de Crédito", rotulos_sbpe)

    def test_migration_from_legacy_padrao(self):
        """Verifica se perfil antigo com nome 'Padrão' é migrado para 'MCMV'."""
        legacy_data = [
            {
                "nome": "Padrão",
                "formularios": [],
                "documentos_extras": [
                    {"rotulo": "Contrato", "nome_padrao": "CONTRATO"}
                ],
                "formato_saida": "PDF/A-2b"
            }
        ]
        with open(self.profiles_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)

        with patch("app.utils.profile_manager._caminho_perfis", return_value=self.profiles_path):
            perfis = carregar_perfis()
            nomes = [p.nome for p in perfis]
            self.assertNotIn("Padrão", nomes)
            self.assertIn("MCMV", nomes)
            self.assertIn("SBPE", nomes)

    def test_config_manager_migration(self):
        """Verifica se config_manager migra perfil_ativo 'Padrão' para 'MCMV'."""
        legacy_config = {
            "perfil_ativo": "Padrão",
            "aparencia": "light"
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(legacy_config, f)

        with patch("app.utils.config_manager._caminho_config", return_value=self.config_path):
            cfg = config_manager.carregar_config()
            self.assertEqual(cfg["perfil_ativo"], "MCMV")


if __name__ == "__main__":
    unittest.main()
