import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from models.participant import Participant
from services.form_validation import preparar_participantes, valor_valido
from utils.profile_manager import CampoEntrada, Perfil


class TestFormValidation(unittest.TestCase):
    def test_required_conditional_and_hidden_value_cleared(self):
        profile = Perfil(campos_entrada=[CampoEntrada("situacao", "Situação", tipo="SELECAO", opcoes=["ATIVO", "INATIVO"]),
                                        CampoEntrada("pis", "PIS", tipo="PIS_PASEP", visivel_quando=[{"situacao": ["ATIVO"]}])])
        participant = Participant(campos_dinamicos={"situacao": "INATIVO", "pis": "invalid"})
        result, errors = preparar_participantes([participant], profile)
        self.assertFalse(errors)
        self.assertEqual(result[0].obter_campo("pis"), "")
        self.assertEqual(participant.obter_campo("pis"), "invalid")
        participant.definir_campo("situacao", "ATIVO")
        self.assertEqual(preparar_participantes([participant], profile)[1], [{"participant": 1, "field": "pis"}])

    def test_calculated_value_cannot_be_overridden(self):
        profile = Perfil(campos_entrada=[CampoEntrada("salario", "Salário", tipo="MOEDA"),
                                        CampoEntrada("extra", "Extra", tipo="MOEDA", valor_padrao="10,00"),
                                        CampoEntrada("total", "Total", tipo="MOEDA", calculo="salario+extra")])
        participant = Participant(campos_dinamicos={"salario": "100,00", "total": "999,00"})
        result, errors = preparar_participantes([participant], profile)
        self.assertFalse(errors)
        self.assertEqual(result[0].obter_campo("total"), "110,00")

    def test_global_and_participant_limit(self):
        profile = Perfil(campos_entrada=[CampoEntrada("local", "Local", escopo="global", valor_padrao="Teste"),
                                        CampoEntrada("titular", "Titular", ate_participante=1)])
        values = [Participant(campos_dinamicos={"titular": "Sim"}), Participant()]
        result, errors = preparar_participantes(values, profile)
        self.assertFalse(errors)
        self.assertEqual(result[1].obter_campo("local"), "Teste")

    def test_formats_and_bounds(self):
        examples = [("CPF", "12345678900"), ("EMAIL", "abc"), ("DATA", "31/02/2026"),
                    ("ANO", "123"), ("INTEIRO", "2.5"), ("MOEDA", "NaN"), ("AREA", "-5")]
        for kind, value in examples:
            self.assertFalse(valor_valido(CampoEntrada("x", "X", tipo=kind), value), kind)
        self.assertFalse(valor_valido(CampoEntrada("x", "X", tipo="INTEIRO", maximo=4), "5"))
        self.assertFalse(valor_valido(CampoEntrada("x", "X", tipo="SELECAO", opcoes=["A"]), "B"))

    def test_calculation_order_and_cycle(self):
        profile = Perfil(campos_entrada=[CampoEntrada("total", "Total", calculo="parcial+base"),
                                        CampoEntrada("parcial", "Parcial", calculo="base+base"),
                                        CampoEntrada("base", "Base", valor_padrao="10,00")])
        values, errors = preparar_participantes([Participant()], profile)
        self.assertFalse(errors)
        self.assertEqual(values[0].obter_campo("total"), "30,00")
        profile.campos_entrada[1].calculo = "total+base"
        self.assertTrue(preparar_participantes([Participant()], profile)[1])


if __name__ == "__main__":
    unittest.main()
