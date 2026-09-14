"""Behavioral JS checks use Node when available; real WebView flow is separate."""
from pathlib import Path
import shutil
import subprocess
import unittest


class TestFrontendBehavior(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for frontend behavior tests")
    def test_real_scripts(self):
        script=Path(__file__).with_name("frontend_behavior.cjs")
        result=subprocess.run([shutil.which("node"), str(script)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
