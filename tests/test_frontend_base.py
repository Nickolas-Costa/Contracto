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
                    "assets/logo.png",
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
        css = (RAIZ / "css/layout.css").read_text(encoding="utf-8")
        for exigido in ['lang="pt-BR"', "aria-current", 'role="status"',
                        'aria-modal="true"', "<label", "prefers-reduced-motion",
                        'id="conexao"']:
            self.assertIn(exigido, html + css, exigido)

    def test_estrutura_revisao_visual(self):
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        css = (RAIZ / "css/layout.css").read_text(encoding="utf-8")
        # Logo no lugar do "C" genérico + favicon.
        self.assertIn('assets/logo.png', html)
        self.assertIn('rel="icon"', html)
        # Stepper em 4 etapas: preencher, conferir, revisar, enviar.
        for n in ["1", "2", "3", "4"]:
            self.assertIn(f'data-etapa="{n}"', html)
        # Sem contador de selecionados e sem bloco "antes de gerar".
        self.assertNotIn("selecao-resumo", html)
        self.assertNotIn("Antes de gerar", html)
        self.assertIn('id="btn-selecionar-todos"', html)
        # Resumo com links para edição.
        self.assertIn('data-ir="btn-pasta"', html)
        # Scroll estilizado, faixa do modal e fundo modular.
        for exigido in ["::-webkit-scrollbar", "scrollbar-width",
                        "modal-titulo-faixa", "modal-fechar",
                        "repeating-linear-gradient"]:
            self.assertIn(exigido, css)
        # Configurações no topo, fora da navegação.
        self.assertIn('id="btn-config-topo"', html)

    def test_boot_aguarda_ponte(self):
        app_js = (RAIZ / "js/app.js").read_text(encoding="utf-8")
        self.assertIn("pywebviewready", app_js)
        self.assertIn("finalizarArranque", app_js)
        # Corridas e recuperação são exercitadas no teste de comportamento JS.
        self.assertIn("conectando", app_js)
        self.assertIn("ContractoEtapa2.ligar()", app_js)

    def test_build_embarca_frontend(self):
        bat = (RAIZ.parent / "build_exe.bat").read_text(encoding="utf-8")
        self.assertIn("../frontend;frontend", bat)
        app_js = (RAIZ / "js/app.js").read_text(encoding="utf-8")
        # Capacidades carregadas no arranque para não desativar PDF/A à toa.
        self.assertIn("/api/v1/capabilities", app_js)
        self.assertIn("capacidades(", app_js)

    def test_etapa2_sem_ids_fantasmas(self):
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        etapa2 = (RAIZ / "js/etapa2.js").read_text(encoding="utf-8")
        for exigido in ['id="formato-opcoes"', 'id="capacidade-formato"',
                        'id="estado-trabalho"', 'id="fila-detalhe"']:
            self.assertIn(exigido, html)
        # Todo id lido pelo JS da Etapa 2 existe no HTML.
        for usado in sorted(set(re.findall(r'\$\("([\w-]+)"\)', etapa2))):
            self.assertIn(f'id="{usado}"', html, usado)
# Categoria é uma seleção finita: o valor técnico continua validado pela API,
        # enquanto o texto da opção é apresentado ao usuário.
        self.assertIn('<select id="anexo-tipo"', html)
        self.assertIn("selectedOptions", etapa2)


if __name__ == "__main__":
    unittest.main()
