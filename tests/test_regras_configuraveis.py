import unittest

from app.services.field_calculator import calcular, validar_calculo
from app.services.mapping_engine import resolver_especificacao
from app.utils.profile_manager import CampoEntrada, Perfil


class TestRegrasConfiguraveis(unittest.TestCase):
    def test_valor_padrao_do_mapeamento(self):
        regra = {"origem": "global.campo_vazio", "valor_padrao": "0,00"}
        self.assertEqual(resolver_especificacao(regra, lambda origem: ""), "0,00")

    def test_calculo_configurado_no_campo(self):
        valores = {
            "valor_total": "180.000,00",
            "entrada": "20.000,00",
            "adicional": "5.000,00",
        }
        self.assertEqual(
            calcular("valor_total - entrada + adicional", valores),
            "165.000,00",
        )

    def test_calculo_nao_executa_codigo(self):
        self.assertFalse(validar_calculo("__import__('os').system('x')"))
        self.assertEqual(calcular("__import__('os').system('x')", {}), "")

    def test_paginacao_nao_tem_limite_fixo(self):
        perfil = Perfil(
            nome="Perfil de teste",
            usar_paginacao=True,
            campos_entrada=[
                CampoEntrada(id=f"campo_{indice}", rotulo=f"Campo {indice}", aba=f"Página {indice}")
                for indice in range(1, 13)
            ],
        )
        self.assertEqual(len(perfil.obter_abas_disponiveis()), 12)
        self.assertEqual(perfil.obter_abas_disponiveis()[-1], "Página 12")


if __name__ == "__main__":
    unittest.main()
