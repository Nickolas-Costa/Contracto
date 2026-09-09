"""Falha explícita do setup do Ghostscript e registro da versão."""

import subprocess
import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch


def carregar_setup_gs():
    caminho = (
        Path(__file__).resolve().parent.parent / "scripts" / "setup_gs.py"
    )
    spec = spec_from_file_location("setup_gs", caminho)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


setup_gs = carregar_setup_gs()


class TestSetupGs(unittest.TestCase):
    def test_sem_ghostscript_falha(self):
        with patch.object(setup_gs, "localizar_ghostscript", return_value=None):
            self.assertEqual(setup_gs.main([]), 1)

    def test_sem_ghostscript_com_flag_permite(self):
        with patch.object(setup_gs, "localizar_ghostscript", return_value=None):
            self.assertEqual(setup_gs.main(["--allow-without-gs"]), 0)

    def test_ghostscript_em_assets_nada_a_fazer(self):
        from utils.ghostscript_setup import localizar_ghostscript

        gs_exe = localizar_ghostscript()
        self.assertIsNotNone(gs_exe)
        with patch.object(setup_gs, "localizar_ghostscript", return_value=gs_exe):
            self.assertEqual(setup_gs.main([]), 0)

    def test_versao_desconhecida_sem_executavel(self):
        self.assertEqual(
            setup_gs.versao_ghostscript(Path("gs_inexistente.exe")), "desconhecida"
        )

    def test_versao_lida_do_executavel(self):
        proc = subprocess.CompletedProcess(
            args=["gs", "--version"], returncode=0, stdout="10.03.0\n", stderr=""
        )
        with patch.object(setup_gs.subprocess, "run", return_value=proc):
            self.assertEqual(
                setup_gs.versao_ghostscript(Path("gs")), "10.03.0"
            )


if __name__ == "__main__":
    unittest.main()
