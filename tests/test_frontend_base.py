"""Base do frontend web: arquivos, tokens, CSP, integridade do HTML, IDs únicos e shell."""

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "frontend"

TOKENS_OBRIGATORIOS = [
    "--c-primary", "--c-bg", "--c-surface", "--c-text", "--c-success",
    "--c-warning-badge", "--c-error", "--r-card", "--r-button", "--r-input",
]


class _IDCollectorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.doctypes = 0
        self.head_count = 0
        self.body_count = 0
        self.app_count = 0

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.doctypes += 1

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.head_count += 1
        elif tag == "body":
            self.body_count += 1

        for attr, value in attrs:
            if attr == "id":
                if value == "app":
                    self.app_count += 1
                if value:
                    self.ids.append(value)


class TestFrontendBase(unittest.TestCase):
    def test_arquivos_presentes(self):
        for rel in ["index.html", "lab.html", "css/tokens.css", "css/layout.css",
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
                        'id="badge-participantes"']:
            self.assertIn(exigido, html + css, exigido)
        # ADR 0021: nenhum indicador técnico de backend exposto ao usuário final.
        self.assertNotIn('id="conexao"', html)

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
        # ADR 0021: modos dentro da toolbar, badge visível, sem painel lateral.
        self.assertIn('class="modos toolbar-mode"', html)
        self.assertIn('id="badge-participantes"', html)
        self.assertIn('id="paginacao-form"', html)
        self.assertNotIn('class="summary"', html)
        self.assertNotIn('id="resumo-participantes"', html)
        # Scroll estilizado, faixa do modal e fundo modular.
        for exigido in ["::-webkit-scrollbar", "scrollbar-width",
                        "modal-titulo-faixa", "modal-fechar",
                        "repeating-linear-gradient"]:
            self.assertIn(exigido, css)
        # Configurações no topo, fora da navegação; Sobre removido; Ajuda é toast.
        self.assertIn('id="btn-config-topo"', html)
        self.assertNotIn('id="btn-sobre-topo"', html)
        self.assertNotIn('Sobre o Contracto', (RAIZ / "js/ui.js").read_text(encoding="utf-8"))

    def test_toolbar_consolidada_adr0021(self):
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        toolbar = html.split('<header class="toolbar">', 1)[1].split("</header>", 1)[0]
        self.assertIn('id="modo-simples"', toolbar)
        self.assertIn('id="modo-avancado"', toolbar)
        self.assertIn('id="badge-participantes"', toolbar)
        self.assertNotIn('id="conexao"', toolbar)

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
        self.assertIn('<select id="anexo-tipo"', html)
        self.assertIn("selectedOptions", etapa2)

    def test_integridade_html_e_ids_unicos(self):
        """Garante que index.html possui estrutura única e sem IDs duplicados."""
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        parser = _IDCollectorParser()
        parser.feed(html)

        self.assertEqual(parser.doctypes, 1, "HTML deve conter exatamente 1 DOCTYPE")
        self.assertEqual(parser.head_count, 1, "HTML deve conter exatamente 1 tag <head>")
        self.assertEqual(parser.body_count, 1, "HTML deve conter exatamente 1 tag <body>")
        self.assertEqual(parser.app_count, 1, "HTML deve conter exatamente 1 elemento #app")

        # Verifica unicidade de IDs no DOM
        vistos = set()
        duplicados = set()
        for elem_id in parser.ids:
            if elem_id in vistos:
                duplicados.add(elem_id)
            vistos.add(elem_id)

        self.assertEqual(duplicados, set(), f"IDs duplicados encontrados no HTML: {duplicados}")

    def test_janela_maximizada_no_shell(self):
        """Garante que webview_shell.py configura a janela principal como maximizada."""
        shell_py = (RAIZ.parent / "app" / "webview_shell.py").read_text(encoding="utf-8")
        self.assertIn("maximized=True", shell_py)

    def test_ponte_api_completa(self):
        api = (RAIZ / "js/api.js").read_text(encoding="utf-8")
        for exigido in ["getJob(", "listJobs", "getCapabilities", "selectAttachment", "atob("]:
            self.assertIn(exigido, api, exigido)

    def test_fila_painel_e_paginacao(self):
        etapa2 = (RAIZ / "js/etapa2.js").read_text(encoding="utf-8")
        etapa1 = (RAIZ / "js/etapa1.js").read_text(encoding="utf-8")
        form = (RAIZ / "js/form-state.js").read_text(encoding="utf-8")
        for exigido in ["painelFila", "filaConhecida", "2000", "gerar(snapshot)", "recomecar", "eraEnvio", "capacidades(data)", "pacoteProcesso", "document_type", "novoRequestId"]:
            self.assertIn(exigido, etapa2 + etapa1, exigido)
        for exigido in ["paginacao-form", "mudarPagina", "resolverPaginas", "field-textarea", "avaliarFormulaLocal", "sincronizarSelecao", "corpo-conferencia", "limparCampos"]:
            self.assertIn(exigido, etapa1, exigido)
        for exigido in ["paginaDe", "if_field", "formula"]:
            self.assertIn(exigido, form, exigido)
        ui = (RAIZ / "js/ui.js").read_text(encoding="utf-8")
        self.assertIn("sincronizarStepper", ui)
        self.assertIn("etapaLiberada", ui)
        app = (RAIZ / "js/app.js").read_text(encoding="utf-8")
        self.assertIn("mostrarCapacidades", app)
        self.assertIn("lista-capacidades", app)
        ui = (RAIZ / "js/ui.js").read_text(encoding="utf-8")
        # Config com rascunho: aplica somente ao salvar; sem densidade.
        for exigido in ["cfgCarregarRascunho", "cfgSalvar", "cfgDescartar", "btn-cfg-salvar", "local_padrao"]:
            self.assertIn(exigido, ui, exigido)
        html = (RAIZ / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("cfg-tamanho-quadros", html)
        self.assertNotIn("(Backend)", html)
        self.assertIn('id="cfg-cores"', html)
        for exigido in ["CORES_PREDEFINIDAS", "marcarSwatch", "#1E6FB3"]:
            self.assertIn(exigido, ui, exigido)
        css = (RAIZ / "css/layout.css").read_text(encoding="utf-8")
        self.assertIn("color-swatches", css)
        self.assertNotIn("color:#fff", css.replace(" ", ""))


if __name__ == "__main__":
    unittest.main()
