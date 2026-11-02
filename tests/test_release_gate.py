import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestReleaseGate(unittest.TestCase):
    def test_release_gate_script_exists_and_is_callable(self):
        script = RAIZ / "scripts" / "check_release_gate.py"
        self.assertTrue(script.exists(), "Falta o script de gate de release")

        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(RAIZ),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("release gate", result.stdout.lower())

    def test_release_gate_checks_required_release_artifacts(self):
        required = [
            RAIZ / "app" / "version.py",
            RAIZ / "VERSION",
            RAIZ / "src-tauri" / "tauri.conf.json",
            RAIZ / "tests" / "smoke_webview.py",
            RAIZ / "tests" / "smoke_api_engines.py",
            RAIZ / "app" / "api" / "http.py",
        ]
        for artifact in required:
            self.assertTrue(artifact.exists(), f"Arquivo obrigatório ausente: {artifact}")

    def test_build_exe_bat_sem_caracteres_de_controle_e_com_crlf(self):
        # Regressão: barra-b e barra-t nos caminhos viraram backspace/tab e o .bat chamava "x08uild_tauri.py".
        dados = (RAIZ / "build_exe.bat").read_bytes()
        self.assertEqual([c for c in dados if c < 32 and c not in (10, 13)], [])
        self.assertEqual(dados.count(b"\n"), dados.count(b"\r\n"), "build_exe.bat precisa de CRLF")
        self.assertIn(rb"scripts\build_tauri.py", dados)


if __name__ == "__main__":
    unittest.main()
