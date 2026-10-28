import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent


class TestReleaseInstallerGate(unittest.TestCase):
    def test_build_script_uses_installer_gate(self):
        texto = (RAIZ / "build_exe.bat").read_text(encoding="utf-8")
        self.assertIn("build_installer.py", texto)
        # Gate: a detecção do ISCC (inclusive instalação por usuário, fora do
        # PATH) fica em build_installer.py --check; sem ele, o passo é pulado.
        self.assertIn("build_installer.py --check", texto)

    def test_iss_uses_versioned_variable(self):
        texto = (RAIZ / "packaging" / "Contracto.iss").read_text(encoding="utf-8")
        self.assertIn("#ifndef MyAppVersion", texto)
        self.assertIn("AppVersion={#MyAppVersion}", texto)

    def test_iscc_check_mode(self):
        # `--check` reconhece a instalação por usuário e não é fatal sem ISCC.
        script = (RAIZ / "scripts" / "build_installer.py").read_text(encoding="utf-8")
        self.assertIn("_iscc_descobertos", script)
        self.assertIn("Inno Setup *", script)
        self.assertIn('"--check"', script)

    def test_compilacao_repete_quando_o_exe_novo_ainda_esta_bloqueado(self):
        # Regressão: logo após o PyInstaller o ISCC falhava na 1ª tentativa e o
        # instalador só saía ao rodar o build de novo.
        sys.path.insert(0, str(RAIZ / "scripts"))
        import build_installer as bi
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "app" / "dist").mkdir(parents=True)
            (raiz / "app" / "dist" / "Contracto_v9.9.9.exe").write_bytes(b"x")
            (raiz / "packaging").mkdir()
            iss = raiz / "packaging" / "Contracto.iss"
            iss.write_text("; teste")
            saida = raiz / "dist"
            chamadas = []

            def iscc(cmd, cwd=None):
                chamadas.append(cmd)
                if len(chamadas) == 1:
                    return type("R", (), {"returncode": 2})()
                saida.mkdir(exist_ok=True)
                (saida / "Contracto_Installer_v9.9.9.exe").write_bytes(b"i")
                return type("R", (), {"returncode": 0})()

            with patch.object(bi, "REPO_ROOT", raiz), patch.object(bi, "ISS_FILE", iss),                     patch.object(bi, "DIST_DIR", saida), patch.object(bi, "read_version", return_value="9.9.9"),                     patch.object(bi, "find_iscc", return_value="iscc"),                     patch.object(bi.subprocess, "run", side_effect=iscc), patch.object(bi.time, "sleep"):
                self.assertEqual(bi.main(), 0)
            self.assertEqual(len(chamadas), 2)


if __name__ == "__main__":
    unittest.main()
