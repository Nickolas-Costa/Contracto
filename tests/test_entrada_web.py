"""Entrada única: sempre o shell WebView (sem abrir janelas)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import main as entrada


class TestEntradaWeb(unittest.TestCase):
    def test_sem_vestigios_da_interface_tk(self):
        self.assertFalse(hasattr(entrada, "iniciar_tk"))
        self.assertFalse(hasattr(entrada, "escolher_interface"))

    def test_main_inicia_o_shell_web_e_libera_a_instancia(self):
        with patch.object(entrada, "iniciar_web") as web, \
             patch.object(entrada, "configurar_logger"), \
             patch.object(entrada, "InstanciaUnica") as mutex, \
             patch.object(entrada.sys, "argv", ["main.py"]):
            entrada.main()
            self.assertTrue(web.called)
            mutex.return_value.liberar.assert_called_once()

    def test_flag_tk_nao_muda_o_comportamento(self):
        with patch.object(entrada, "iniciar_web") as web, \
             patch.object(entrada, "configurar_logger"), \
             patch.object(entrada, "InstanciaUnica"), \
             patch.object(entrada.sys, "argv", ["main.py", "--tk"]):
            entrada.main()
            self.assertTrue(web.called)


if __name__ == "__main__":
    unittest.main()
