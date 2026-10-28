"""form-state.js (validadores e máscaras da UI) contra o validador Python, rodando em Node."""
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path[:0] = [str(RAIZ), str(RAIZ.parent / "app")]

from test_frontend_behavior import NODE_EXE  # noqa: E402
from utils.cnpj_validator import validar_cnpj  # noqa: E402
from utils.cpf_validator import validar_cpf  # noqa: E402

_PESOS = ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])


def _cnpj_com_dv(base12: str) -> str:
    cnpj = base12
    for pesos in _PESOS:
        soma = sum((ord(c) - 48) * p for c, p in zip(cnpj, pesos))
        cnpj += str(0 if soma % 11 < 2 else 11 - soma % 11)
    return cnpj


class TestFormStateJs(unittest.TestCase):
    @unittest.skipUnless(NODE_EXE, "Node é necessário")
    def test_validadores_e_mascaras_batem_com_o_python(self):
        rng = random.Random(7)
        alfabeto = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        validos = ["00000000000191", "11222333000181", "12ABC34501DE35"] + [
            _cnpj_com_dv("".join(rng.choice(alfabeto) for _ in range(12))) for _ in range(200)]
        cnpjs = [(c, validar_cnpj(c)) for c in validos]
        cnpjs += [("00.000.000/0001-91", True), ("00.000.000/0001-92", False), ("11111111111111", False),
                  ("1122233300018", False), ("12ABC34501DEXX", False)]
        cnpjs += [(c[:-1] + str((int(c[-1]) + 1) % 10), False) for c in validos[:50]]
        self.assertTrue(validar_cnpj("00000000000191"))  # o caso do print: CNPJ real e válido
        cpfs = [(c, validar_cpf(c)) for c in ("529.982.247-25", "52998224725", "111.111.111-11", "123")]
        moeda = [["180000", "180.000,00", "180.000"], ["1234.5", "1.234,50", "1.234,5"],
                 ["0,5", "0,50", "0,5"], ["", "", ""], ["1.234.567,891", "1.234.567,89", "1.234.567,89"],
                 ["R$ 10", "10,00", "10"]]
        r = subprocess.run([NODE_EXE, str(RAIZ / "form_state.cjs")], input=json.dumps(
            {"cnpj": cnpjs, "cpf": cpfs, "moeda": moeda}), capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("FORM-STATE OK", r.stdout)

    @unittest.skipUnless(NODE_EXE, "Node é necessário")
    def test_adaptador_nativo_mantem_o_contrato_sob_pywebview_e_tauri(self):
        r = subprocess.run([NODE_EXE, str(RAIZ / "api_adapter.cjs")], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("API-ADAPTER OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
