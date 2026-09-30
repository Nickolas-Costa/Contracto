import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestReleaseInstallerGate(unittest.TestCase):
    def test_build_script_uses_installer_gate(self):
        texto = (RAIZ / "build_exe.bat").read_text(encoding="utf-8")
        self.assertIn("build_installer.py", texto)
        # Gate: o passo do instalador só roda com ISCC no PATH (`where /q`).
        self.assertRegex(texto.lower(), r"where( /q)? iscc")

    def test_iss_uses_versioned_variable(self):
        texto = (RAIZ / "packaging" / "Contracto.iss").read_text(encoding="utf-8")
        self.assertIn("#define MyAppVersion", texto)
        self.assertIn("AppVersion={#MyAppVersion}", texto)


if __name__ == "__main__":
    unittest.main()
