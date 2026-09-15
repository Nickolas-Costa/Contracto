"""Behavioral JS checks use Node when available; real WebView flow is separate."""
from pathlib import Path
import os
import shutil
import subprocess
import unittest


def _node():
    encontrado = shutil.which("node") or shutil.which("nodejs")
    if encontrado:
        return encontrado
    for candidato in [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs\node.exe"),
        "/usr/bin/node",
        "/usr/local/bin/node",
    ]:
        if candidato and Path(candidato).is_file():
            return candidato
    return None


NODE_EXE = _node()


class TestFrontendBehavior(unittest.TestCase):
    @unittest.skipUnless(NODE_EXE, "Node is required for frontend behavior tests")
    def test_real_scripts(self):
        script = Path(__file__).with_name("frontend_behavior.cjs")
        result = subprocess.run([NODE_EXE, str(script)], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
