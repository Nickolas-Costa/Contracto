import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from api.jobs import Jobs, ApiError
from api.models import ParticipantInput


class TestCanonicalParticipantAPI(unittest.TestCase):
    def test_omitted_legacy_default_does_not_erase_dynamic_address(self):
        data = ParticipantInput(nome_completo="Pessoa QA", cpf="52998224725",
                                campos_dinamicos={"endereco": "Rua QA", "data_assinatura": "14/09/2026"})
        participant = Jobs._participants(None, [data])[0]
        self.assertEqual(participant.endereco, "Rua QA")
        self.assertEqual(participant.data_assinatura, "14/09/2026")

    def test_conflicting_explicit_alias_is_rejected_without_values(self):
        data = ParticipantInput(nome_completo="Pessoa QA", cpf="52998224725", endereco="Outro",
                                campos_dinamicos={"endereco": "Rua QA"})
        with self.assertRaises(ApiError) as caught:
            Jobs._participants(None, [data])
        self.assertEqual(caught.exception.status, 422)
        self.assertEqual(caught.exception.issues, [{"participant": 1, "field": "endereco"}])
        self.assertNotIn("Rua QA", str(caught.exception))

    def test_legacy_and_equal_alias_remain_supported(self):
        for dynamic in ({}, {"endereco": "Rua QA"}):
            data = ParticipantInput(nome_completo="Pessoa QA", cpf="52998224725", endereco="Rua QA",
                                    campos_dinamicos=dynamic)
            self.assertEqual(Jobs._participants(None, [data])[0].endereco, "Rua QA")
