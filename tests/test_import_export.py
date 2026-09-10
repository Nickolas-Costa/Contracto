"""Exportação e importação de perfis (.json com envelope e validação)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from utils import profile_manager
from utils.profile_manager import CampoEntrada, Perfil


def _perfil_base(nome="Exportado"):
    return Perfil(
        nome=nome,
        identificador="id-fixo-1",
        campos_entrada=[CampoEntrada(id="nome", rotulo="Nome")],
    )


class TestImportExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.arquivo = Path(self.tmp.name) / "perfis.json"
        self.patch = patch.object(
            profile_manager, "_caminho_perfis", return_value=self.arquivo
        )
        self.patch.start()
        self.addCleanup(self.patch.stop)
        profile_manager.invalidar_cache()
        self.addCleanup(profile_manager.invalidar_cache)

    def test_ida_e_volta_preserva_conteudo(self):
        profile_manager.salvar_perfis([_perfil_base()])
        destino = Path(self.tmp.name) / "exportado.json"
        profile_manager.exportar_perfil("Exportado", destino)
        envelope = json.loads(destino.read_text(encoding="utf-8"))
        self.assertEqual(envelope["formato"], "contracto-perfil")

        profile_manager.salvar_perfis([])
        novo = profile_manager.importar_perfil(destino)
        self.assertEqual(novo.nome, "Exportado")
        self.assertEqual([c.id for c in novo.campos_entrada], ["nome"])

    def test_nome_em_colisao_ganha_copia(self):
        profile_manager.salvar_perfis([_perfil_base()])
        destino = Path(self.tmp.name) / "exportado.json"
        profile_manager.exportar_perfil("Exportado", destino)
        novo = profile_manager.importar_perfil(destino)
        self.assertEqual(novo.nome, "Exportado (Cópia)")
        self.assertNotEqual(novo.identificador, "id-fixo-1")

    def test_arquivo_ilegivel_rejeita(self):
        ruim = Path(self.tmp.name) / "ruim.json"
        ruim.write_text("{invalido", encoding="utf-8")
        with self.assertRaises(ValueError):
            profile_manager.importar_perfil(ruim)

    def test_formato_estrangeiro_rejeita(self):
        outro = Path(self.tmp.name) / "outro.json"
        outro.write_text(json.dumps({"nome": "X"}), encoding="utf-8")
        with self.assertRaises(ValueError):
            profile_manager.importar_perfil(outro)

    def test_perfil_invalido_rejeita(self):
        invalido = Path(self.tmp.name) / "invalido.json"
        invalido.write_text(json.dumps({
            "formato": "contracto-perfil",
            "versao": 1,
            "perfil": {"nome": "  ", "campos_entrada": []},
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            profile_manager.importar_perfil(invalido)

    def test_exportar_inexistente_rejeita(self):
        profile_manager.salvar_perfis([])
        with self.assertRaises(ValueError):
            profile_manager.exportar_perfil(
                "Fantasma", Path(self.tmp.name) / "x.json"
            )


if __name__ == "__main__":
    unittest.main()
