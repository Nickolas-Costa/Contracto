"""Janela real -> participantes -> fila -> quatro PDFs validados.

Windows: python tests/smoke_test_gui.py
Linux: xvfb-run -a python tests/smoke_test_gui.py
APPDATA e perfil sintéticos; PDF comum independe de Word/Ghostscript.
"""
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))


def criar_modelo(caminho):
    from reportlab.pdfgen import canvas
    doc = canvas.Canvas(str(caminho), pagesize=(600, 800))
    for indice, nome in enumerate(("NOME", "CPF")):
        doc.acroForm.textfield(name=nome, x=50, y=700 - indice * 50,
                              width=400, height=20, forceBorder=True)
    doc.showPage()
    doc.save()


def preencher(entry, texto):
    entry.delete(0, "end")
    entry.insert(0, texto)


def main():
    with tempfile.TemporaryDirectory(prefix="contracto-smoke-") as temporario:
        pasta = Path(temporario)
        with patch.dict(os.environ, {"APPDATA": temporario, "LOCALAPPDATA": temporario}):
            # Importar somente depois de isolar os caminhos persistentes.
            from pypdf import PdfReader
            from utils import config_manager
            from utils.profile_manager import CampoEntrada, FormularioModelo, Perfil, adicionar_perfil
            from ui.main_window import MainWindow

            modelos = [pasta / "a.pdf", pasta / "b.pdf"]
            for modelo in modelos:
                criar_modelo(modelo)
            perfil = Perfil(
                nome="SMOKE GUI", formato_saida="PDF",
                formularios=[FormularioModelo(
                    nome=f"DOC-{indice}", caminho=str(modelo),
                    mapeamento={"NOME": "participante.nome", "CPF": "participante.cpf"},
                ) for indice, modelo in enumerate(modelos, start=1)],
                campos_entrada=[CampoEntrada(id="endereco", rotulo="Endereço")],
            )
            adicionar_perfil(perfil)
            for chave, valor in {"perfil_ativo": perfil.nome, "modo_operacao": "avancado",
                                 "primeira_execucao": False, "abrir_pasta_ao_concluir": False}.items():
                config_manager.definir(chave, valor)
            saida = pasta / "saida"
            saida.mkdir()
            app = MainWindow()
            erros_tk = []
            app.report_callback_exception = lambda *erro: erros_tk.append(erro)
            try:
                app.update()
                app._adicionar_participante()
                app._adicionar_participante()
                app.update()
                assert len(app.participant_frames) == 3
                app._remover_participante(app.participant_frames[2])
                app.update()
                assert len(app.participant_frames) == 2
                assert app.participant_frames[1].label_titulo.cget("text").startswith("Participante 2")
                nomes = ["João da Silva", "Maria Silva"]
                for frame, nome, cpf in zip(app.participant_frames, nomes,
                                             ["529.982.247-25", "111.444.777-35"]):
                    preencher(frame.entry_nome, nome)
                    preencher(frame.entry_cpf, cpf)
                    assert frame.entry_endereco is not None  # Declarado pelo perfil.
                    preencher(frame.entry_endereco, "Rua de Teste, 123")
                preencher(app.entry_data, "12/09/2026")
                preencher(app.entry_local, "CAMOCIM-CE")
                preencher(app.entry_pasta_saida, str(saida))
                app._ao_editar_pasta_saida()
                assert not app._listar_pendencias_etapa1(), app._listar_pendencias_etapa1()
                app.botao_avancar.invoke()
                app.update()
                assert len(app.participantes_etapa1) == 2
                for selecionado in app._vars_forms_dinamicos.values():
                    selecionado.set(True)
                app.botao_finalizar.invoke()
                prazo = time.monotonic() + 30
                while app.queue_manager.tem_trabalho_ativo() and time.monotonic() < prazo:
                    app.update()
                    time.sleep(0.05)
                app.update()
                assert not app.queue_manager.tem_trabalho_ativo(), "Fila não concluiu em 30s"
                arquivos = list(saida.rglob("*.pdf"))
                assert len(arquivos) == 4, [str(p) for p in arquivos]
                valores = []
                for arquivo in arquivos:
                    with arquivo.open("rb") as stream:
                        campos = PdfReader(stream).get_fields()
                        valores.append(campos["NOME"]["/V"])
                        assert campos["CPF"]["/V"]
                for nome in nomes:
                    assert valores.count(nome) == 2, valores
                assert not erros_tk, erros_tk
                print("SMOKE GUI: OK — 2 participantes, fila concluída, 4 PDFs preenchidos.")
            finally:
                app.destroy()


if __name__ == "__main__":
    main()
