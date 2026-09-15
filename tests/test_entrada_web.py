"""Entrada padrão WebView, legada Tk sob flag (sem abrir janelas)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import main as entrada


class TestEscolhaInterface(unittest.TestCase):
    def test_padrao_eh_web(self):
        self.assertEqual(entrada.escolher_interface([]), "web")
        self.assertEqual(entrada.escolher_interface(["--diagnostico"]), "web")

    def test_flag_tk(self):
        self.assertEqual(entrada.escolher_interface(["--tk"]), "tk")
        self.assertEqual(entrada.escolher_interface(["--tk", "--outra"]), "tk")

    def test_despacho_chama_shell_certo(self):
        with patch.object(entrada, "iniciar_web") as web, \
             patch.object(entrada, "iniciar_tk") as tk, \
             patch.object(entrada, "configurar_logger"), \
             patch.object(entrada, "InstanciaUnica") as mutex, \
             patch.object(entrada.sys, "argv", ["main.py"]):
            entrada.main()
            self.assertTrue(web.called)
            self.assertFalse(tk.called)

    def test_despacho_flag_tk(self):
        with patch.object(entrada, "iniciar_web") as web, \
             patch.object(entrada, "iniciar_tk") as tk, \
             patch.object(entrada, "configurar_logger"), \
             patch.object(entrada, "InstanciaUnica") as mutex, \
             patch.object(entrada.sys, "argv", ["main.py", "--tk"]):
            entrada.main()
            self.assertFalse(web.called)
            self.assertTrue(tk.called)


if __name__ == "__main__":
    unittest.main()
