"""Checkbox com par de opções (ex: SIM/NÃO) e legado Sim/Não."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from services.mapping_engine import resolver_especificacao
from utils.profile_manager import CampoEntrada


class TestCheckboxComOpcoes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import customtkinter as ctk

        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def tearDown(self):
        from ui import theme

        theme._ICONS_CACHE.clear()

    def _widget(self, **kwargs):
        from ui.campo_dinamico_widget import CampoDinamicoWidget

        base = dict(id="teste", rotulo="Teste", tipo="CHECKBOX")
        base.update(kwargs)
        widget = CampoDinamicoWidget(self.root, CampoEntrada(**base))
        widget.pack()
        self.addCleanup(widget.destroy)
        return widget

    def test_par_sim_nao(self):
        widget = self._widget(opcoes=["SIM", "NÃO"])
        self.assertEqual(widget.obter_valor(), "NÃO")
        widget.var_check.set(True)
        self.assertEqual(widget.obter_valor(), "SIM")

    def test_legado_sem_opcoes_mantem_sim_nao(self):
        widget = self._widget()
        self.assertEqual(widget.obter_valor(), "Não")
        widget.definir_valor("Sim")
        self.assertEqual(widget.obter_valor(), "Sim")

    def test_definir_valor_respeita_par(self):
        widget = self._widget(opcoes=["SIM", "NÃO"])
        widget.definir_valor("SIM")
        self.assertEqual(widget.obter_valor(), "SIM")
        widget.definir_valor("NÃO")
        self.assertEqual(widget.obter_valor(), "NÃO")

    def test_condicao_sim_continua_valendo(self):
        regra = {
            "condicoes": [{"participante.possuiImovel": ["SIM"]}],
            "valor_verdadeiro": "/Yes",
            "valor_falso": "/Off",
        }
        resolver = lambda origem: {"participante.possuiImovel": "SIM"}.get(origem, "")
        self.assertEqual(resolver_especificacao(regra, resolver), "/Yes")

    def test_damp_tem_sete_checks_sim_nao(self):
        from utils.resource_path import carregar_configuracao_inicial

        cfg = carregar_configuracao_inicial()
        checks = [
            c["id"]
            for entrada in cfg["perfis"]
            for c in entrada["perfil"].get("campos_entrada", [])
            if c.get("tipo") == "CHECKBOX"
            and [str(o) for o in (c.get("opcoes") or [])] == ["SIM", "NÃO"]
        ]
        self.assertEqual(
            sorted(checks),
            sorted([
                "mantemUniaoEstavel", "possuiImovel", "possui36MesesFgts",
                "jaRecebeuSubsidio", "fgtsFuturo", "utilizaContaFgts",
                "autorizaSaqueFgts",
            ]),
        )


if __name__ == "__main__":
    unittest.main()
