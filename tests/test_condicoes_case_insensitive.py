"""Condições de mapeamento/visibilidade insensíveis a caixa ("SIM" vs "Sim").

Regressão v4.5.22: os checkboxes do Form Cliente (Boleto/WhatsApp, tarifa de
avaliação) e a isenção do ITBI nunca disparavam porque o valor canônico "SIM"
não casava com as condições legadas ["Sim"].
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.mapping_engine import resolver_especificacao


class TestCondicoesCaseInsensitive(unittest.TestCase):
    def test_mapeamento_casa_sim_maiusculo(self):
        regra = {"condicoes": [{"global.autorizaBoletoWhatsapp": ["Sim"]}],
                 "valor_verdadeiro": "/Yes_ftsk", "valor_falso": "/Off"}
        resolver = lambda origem: "SIM"  # noqa: E731 - valor canônico do frontend/API
        self.assertEqual(resolver_especificacao(regra, resolver), "/Yes_ftsk")

    def test_mapeamento_mantem_negativa(self):
        regra = {"condicoes": [{"global.autorizaBoletoWhatsapp": ["Sim"]}],
                 "valor_verdadeiro": "/Yes_ftsk", "valor_falso": "/Off"}
        resolver = lambda origem: "NÃO"  # noqa: E731
        self.assertEqual(resolver_especificacao(regra, resolver), "/Off")

    def test_seed_form_cliente_usa_sim_canonico(self):
        import json
        seed = json.loads((Path(__file__).resolve().parent.parent
                           / "app" / "assets" / "config" / "perfis_iniciais.json").read_text(encoding="utf-8"))
        fc = next(p for p in seed["perfis"] if p["perfil"]["nome"] == "Form Cliente")
        mp = fc["perfil"]["formularios"][0]["mapeamento"]
        self.assertEqual(mp["BOLETO AUT"]["condicoes"],
                         [{"global.autorizaBoletoWhatsapp": ["SIM"]}])
        self.assertEqual(mp["AVALIACAO AUT COB"]["condicoes"],
                         [{"global.autorizaCobrancaAvaliacao": ["SIM"]}])
        self.assertEqual(seed["mapeamentos"]["modelo_06"]["TEXTO_ISENCAO"]["condicoes"],
                         [{"global.enquadramento_isencao": ["SIM", ""]}])

    def test_visibilidade_preparar_case_insensitive(self):
        from models.participant import Participant
        from services.form_validation import preparar_participantes
        from utils.profile_manager import CampoEntrada, Perfil
        perfil = Perfil(nome="QA", modo_fluxo="formulario_simples", campos_entrada=[
            CampoEntrada(id="flag", rotulo="Flag", tipo="CHECKBOX", escopo="global"),
            CampoEntrada(id="det", rotulo="Det", visivel_quando=[{"flag": ["Sim"]}]),
        ])
        p = Participant(nome_completo="A", cpf="529.982.247-25",
                        campos_dinamicos={"flag": "SIM", "det": "x"})
        out, erros = preparar_participantes([p], perfil)
        self.assertEqual(erros, [])
        self.assertEqual(out[0].obter_campo("det"), "x")

    def test_refresh_catalogo_preserva_ids(self):
        from api.jobs import Jobs
        from utils.profile_manager import Perfil
        jobs = Jobs(profiles=[Perfil(nome="QA Um", modo_fluxo="formulario_simples")])
        antes = {p["name"]: p["profile_id"] for p in jobs.catalog()}
        jobs.refresh_profiles()
        depois = {p["name"]: p["profile_id"] for p in jobs.catalog()}
        # Perfis do disco entram; o ID do perfil preservado por nome é estável.
        self.assertIn("QA Um", depois)
        self.assertEqual(antes["QA Um"], depois["QA Um"])
        self.assertIn("Form Cliente", depois)


if __name__ == "__main__":
    unittest.main()
