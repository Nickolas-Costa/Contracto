"""Testes das novidades v4.5.10 (release estável).

Cobre sem abrir janelas (headless): ordenação por dependência,
validação estrutural, correções aplicadas, limites de PDF,
realocação dos modelos e nome versionado no passo SHA-256 do build.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.pdf_service import PdfServiceError, validar_pdf_para_configuracao
from utils.profile_manager import (
    CampoEntrada,
    Perfil,
    ordenar_campos_para_exibicao,
    validar_perfis,
)
from utils.resource_path import listar_modelos_configurados, modelo_configurado

RAIZ = Path(__file__).resolve().parent.parent


class TestOrdenacaoPorDependencia(unittest.TestCase):
    def test_controle_vem_antes_do_dependente(self):
        controle = CampoEntrada(id="situacaoOcupacional", rotulo="Situação")
        dependente = CampoEntrada(
            id="pisPasep",
            rotulo="PIS",
            visivel_quando=[{"situacaoOcupacional": ["ATIVO"]}],
        )
        ordem = [c.id for c in ordenar_campos_para_exibicao([dependente, controle])]
        self.assertEqual(ordem, ["situacaoOcupacional", "pisPasep"])

    def test_ciclo_nao_trava_nem_perde_campo(self):
        a = CampoEntrada(id="a", rotulo="A", visivel_quando=[{"b": ["x"]}])
        b = CampoEntrada(id="b", rotulo="B", visivel_quando=[{"a": ["y"]}])
        self.assertEqual(
            {c.id for c in ordenar_campos_para_exibicao([a, b])}, {"a", "b"}
        )


class TestValidacaoEstrutural(unittest.TestCase):
    def test_nome_repetido_rejeita(self):
        with self.assertRaises(ValueError):
            validar_perfis([Perfil(nome="X"), Perfil(nome="X")])

    def test_identificador_repetido_rejeita(self):
        with self.assertRaises(ValueError):
            validar_perfis([
                Perfil(nome="A", identificador="id-1"),
                Perfil(nome="B", identificador="id-1"),
            ])

    def test_campo_repetido_no_perfil_rejeita(self):
        perfil = Perfil(
            nome="C",
            campos_entrada=[
                CampoEntrada(id="nome", rotulo="Nome"),
                CampoEntrada(id="nome", rotulo="Nome 2"),
            ],
        )
        with self.assertRaises(ValueError):
            validar_perfis([perfil])

    def test_perfil_valido_passa(self):
        validar_perfis([
            Perfil(
                nome="OK",
                identificador="ok-1",
                campos_entrada=[CampoEntrada(id="nome", rotulo="Nome")],
            )
        ])


class TestLimitesDePdf(unittest.TestCase):
    def test_arquivo_inexistente_rejeita_com_mensagem_amigavel(self):
        with self.assertRaises(PdfServiceError):
            validar_pdf_para_configuracao(Path("nao_existe_12345.pdf"))

    def test_acima_de_50mb_rejeita_sem_ler_o_pdf(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            grande = Path(d) / "grande.pdf"
            with open(grande, "wb") as f:
                f.seek(51 * 1024 * 1024 - 1)
                f.write(b"\0")
            with self.assertRaisesRegex(PdfServiceError, "50 MB"):
                validar_pdf_para_configuracao(grande)

    def test_mais_de_100_paginas_rejeita(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / "muitas.pdf"
            caminho.write_bytes(b"%PDF-1.4 fake")
            leitor = type("Leitor", (), {})()
            leitor.pages = list(range(101))
            leitor.get_fields = lambda: {}
            with patch(
                "services.pdf_service._abrir_pdf", return_value=leitor
            ):
                with self.assertRaisesRegex(PdfServiceError, "100 páginas"):
                    validar_pdf_para_configuracao(caminho)

    def test_mais_de_1000_campos_rejeita(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / "campos.pdf"
            caminho.write_bytes(b"%PDF-1.4 fake")
            leitor = type("Leitor", (), {})()
            leitor.pages = [1]
            leitor.get_fields = lambda: {f"c{i}": {} for i in range(1001)}
            with patch(
                "services.pdf_service._abrir_pdf", return_value=leitor
            ):
                with self.assertRaisesRegex(PdfServiceError, "1.000 campos"):
                    validar_pdf_para_configuracao(caminho)


class TestModelosRealocados(unittest.TestCase):
    def test_todos_os_modelos_resolvem_sem_subpasta_novos(self):
        from utils.resource_path import carregar_configuracao_inicial

        mapa = carregar_configuracao_inicial().get("modelos", {})
        self.assertNotIn("novos/", "".join(mapa.values()))
        modelos = listar_modelos_configurados()
        self.assertGreaterEqual(len(modelos), 7)
        for modelo in modelos:
            self.assertTrue(modelo.exists(), f"Modelo ausente: {modelo}")
            self.assertNotIn("novos", modelo.parts)

    def test_damp_seguro_e_form_cliente_encontrados(self):
        for chave in ("modelo_01", "modelo_02", "modelo_03"):
            caminho = modelo_configurado(chave)
            self.assertIsNotNone(caminho, f"{chave} não resolveu")
            self.assertTrue(caminho.exists())


class TestBuildSha256Versionado(unittest.TestCase):
    def test_hash_usa_o_zip_da_versao_atual(self):
        texto = (RAIZ / "build_exe.bat").read_text(encoding="utf-8")
        self.assertIn("Contracto_v%APP_VERSION%.zip.sha256.txt", texto)
        self.assertNotIn("Get-FileHash 'dist\\Contracto.zip'", texto)


if __name__ == "__main__":
    unittest.main()
