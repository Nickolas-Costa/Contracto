"""Base do frontend web: arquivos, tokens, CSP e integridade das referências."""

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "frontend"

TOKENS_OBRIGATORIOS = [
    "--c-primary", "--c-bg", "--c-surface", "--c-text", "--c-success",
    "--c-warning-badge", "--c-error", "--r-card", "--r-button", "--r-input",
]


class TestFrontendBase(unittest.TestCase):
    def test_arquivos_presentes(self):
        for rel in ["index.html", "css/tokens.css", "css/layout.css",
                    "js/api.js", "js/ui.js", "js/etapa1.js", "js/etapa2.js",
                    "js/app.js"]:
            self.assertTrue((RAIZ / rel).is_file(), rel)

    def test_referencias_resolvem(self):
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        for attr, pasta in (("src", "js"), ("href", "css")):
            for alvo in re.findall(rf'{attr}="([^"]+)"', html):
                if alvo.startswith(("http", "#")):
                    continue
                self.assertTrue((RAIZ / alvo).is_file(), alvo)

    def test_tokens_presentes(self):
        css = (RAIZ / "css/tokens.css").read_text(encoding="utf-8")
        for token in TOKENS_OBRIGATORIOS:
            self.assertIn(token, css, token)
        self.assertIn('[data-theme="dark"]', css)

    def test_sem_rede_externa_e_sem_inline(self):
        for nome in ["index.html"] + [f"js/{n}.js" for n in ["api", "ui", "etapa1", "etapa2", "app"]]:
            texto = (RAIZ / nome).read_text(encoding="utf-8")
            self.assertNotIn("http://", texto, nome)
            self.assertNotIn("https://", texto, nome)
            self.assertNotIn('setAttribute("onclick"', texto, nome)
        self.assertNotIn("onclick=", (RAIZ / "index.html").read_text(encoding="utf-8"))
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        self.assertIn("Content-Security-Policy", html)

    def test_js_balanceado(self):
        for nome in ["api.js", "ui.js", "etapa1.js", "etapa2.js", "app.js"]:
            texto = (RAIZ / "js" / nome).read_text(encoding="utf-8")
            for abre, fecha in [("{", "}"), ("(", ")"), ("[", "]")]:
                self.assertEqual(
                    texto.count(abre), texto.count(fecha), f"{nome} {abre}{fecha}"
                )

    def test_acessibilidade_basica(self):
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        for exigido in ['lang="pt-BR"', "aria-current", 'role="status"',
                        'aria-modal="true"', "<label", "prefers-reduced-motion"]:
            self.assertIn(exigido, html + (RAIZ / "css/layout.css").read_text(encoding="utf-8"), exigido)


if __name__ == "__main__":
    unittest.main()
