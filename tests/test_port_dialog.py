"""Guarda da migração web: tkinter só onde o shell atual exige."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

RAIZ_APP = Path(__file__).resolve().parent.parent / "app"

# Únicos lugares que podem tocar em tkinter: telas atuais + implementação
# Tk do port + testes. services/, models/, resto de utils/ e ports/ não.
PERMITIDOS_TKINTER = {
    "main.py",
    "ui/main_window.py",
    "ui/profiles_frame.py",
    "ui/document_frame.py",
    "ui/participant_frame.py",
    "ui/campo_dinamico_widget.py",
    "ui/date_picker.py",
    "ui/animated_loader.py",
    "ui/theme.py",
    "ui/settings_frame.py",
    "ui/welcome_modal.py",
    "ui/alert_modal.py",
    "ui/confirm_modal.py",
    "ui/loading_modal.py",
    "ui/success_modal.py",
    "ui/word_travado_modal.py",
    "ui/base_modal.py",
    "ui/feedback_toast.py",
    "utils/file_picker.py",
}


class TestSemTkinterForaDaUI(unittest.TestCase):
    def test_apenas_arquivos_permitidos_importam_tkinter(self):
        import re

        invasores = []
        for arquivo in RAIZ_APP.rglob("*.py"):
            rel = arquivo.relative_to(RAIZ_APP).as_posix()
            if rel in PERMITIDOS_TKINTER or rel.startswith("tests/"):
                continue
            texto = arquivo.read_text(encoding="utf-8")
            if re.search(r"(^|\n)\s*(import tkinter|from tkinter)", texto):
                invasores.append(rel)
        self.assertEqual(invasores, [])

    def test_port_dialog_nao_importa_tkinter(self):
        import re

        from pathlib import Path as _Path

        texto = (_Path(__file__).resolve().parent.parent / "app" / "ports" / "dialog.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"(^|\n)\s*(import tkinter|from tkinter)", texto))
        import ports.dialog

        self.assertTrue(callable(ports.dialog.selecionar_arquivo))
        self.assertTrue(callable(ports.dialog.selecionar_pasta))
        self.assertTrue(callable(ports.dialog.salvar_arquivo))

    def test_cancelamento_devolve_none(self):
        import ports.dialog

        with patch("utils.file_picker.filedialog") as dialogo:
            dialogo.askopenfilename.return_value = ""
            dialogo.asksaveasfilename.return_value = ""
            dialogo.askdirectory.return_value = ""
            self.assertIsNone(ports.dialog.selecionar_arquivo("T"))
            self.assertIsNone(ports.dialog.salvar_arquivo("T", "x.json"))
            self.assertIsNone(ports.dialog.selecionar_pasta())


if __name__ == "__main__":
    unittest.main()
