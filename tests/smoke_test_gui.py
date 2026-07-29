"""
Teste de fumaça (smoke test) que instancia a JANELA REAL do CustomTkinter
(via display virtual Xvfb) e simula a interação de um usuário:

  1. Preenche o participante principal.
  2. Clica "Adicionar Participante" duas vezes.
  3. Preenche os participantes 2 e 3 (apenas nome/CPF).
  4. Remove o participante 3 e confere a renumeração.
  5. Seleciona modelos PDF sintéticos e pasta de saída.
  6. Clica "GERAR DOCUMENTOS" e confere os arquivos gerados.

Não faz parte da suíte `unittest` porque depende de um display (Xvfb) e
não deve rodar em ambientes de CI sem GUI. Executar manualmente com:

    xvfb-run -a python3 tests/smoke_test_gui.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from reportlab.pdfgen import canvas

import ui.main_window as main_window_module

mensagens_capturadas = []


def _capturar(tipo):
    def _inner(title, message, *_a, **_kw):
        mensagens_capturadas.append((tipo, title, message))
        return "ok"

    return _inner


# Evita que caixas de diálogo modais bloqueiem o teste automatizado
main_window_module.messagebox.showerror = _capturar("error")
main_window_module.messagebox.showwarning = _capturar("warning")
main_window_module.messagebox.showinfo = _capturar("info")

from ui.main_window import MainWindow  # noqa: E402  (import após o monkeypatch)


def criar_modelo(caminho: Path, campos: list[str]) -> None:
    c = canvas.Canvas(str(caminho), pagesize=(600, 800))
    form = c.acroForm
    y = 750
    for nome in campos:
        c.drawString(50, y + 15, nome)
        form.textfield(
            name=nome, tooltip=nome, x=50, y=y, width=400, height=20,
            borderStyle="inset", forceBorder=True,
        )
        y -= 50
    c.save()


def main() -> None:
    app = MainWindow()
    app.update()

    # 1) Participante principal
    p1 = app.participant_frames[0]
    p1.entry_nome.insert(0, "João da Silva")
    p1.entry_cpf.insert(0, "111.111.111-11")
    p1.entry_endereco.insert(0, "Rua das Flores, 123")
    p1.entry_data.insert(0, "15/07/2026")

    # 2) Adicionar dois participantes
    app._adicionar_participante()
    app._adicionar_participante()
    app.update()
    assert len(app.participant_frames) == 3, f"esperado 3 participantes, obteve {len(app.participant_frames)}"

    p2 = app.participant_frames[1]
    p2.entry_nome.insert(0, "Maria Silva")
    p2.entry_cpf.insert(0, "222.222.222-22")
    assert p2.entry_endereco is None, "participante 2 não deveria ter campo de endereço"
    assert p2.entry_data is None, "participante 2 não deveria ter campo de data"

    p3 = app.participant_frames[2]
    p3.entry_nome.insert(0, "Pedro Silva")
    p3.entry_cpf.insert(0, "333.333.333-33")

    # 3) Remover participante 3 e conferir renumeração do participante 2 (agora não deveria mudar, pois ele continua sendo o 2º)
    app._remover_participante(p3)
    app.update()
    assert len(app.participant_frames) == 2, f"esperado 2 participantes após remoção, obteve {len(app.participant_frames)}"
    assert p2.label_titulo.cget("text").startswith("Participante 2"), p2.label_titulo.cget("text")

    # 4) Modelos sintéticos + pasta de saída
    tmp = tempfile.TemporaryDirectory()
    pasta = Path(tmp.name)
    modelo_ppe = pasta / "ppe.pdf"
    modelo_imovel = pasta / "imovel.pdf"
    saida = pasta / "saida"
    saida.mkdir()

    criar_modelo(modelo_ppe, ["NOME COMPLETO", "CPF", "DIA", "MES", "ANO"])
    criar_modelo(modelo_imovel, ["NOME COMPLETO", "CPF", "ENDEREÇO", "DATA"])

    app.caminho_modelo_ppe = modelo_ppe
    app.caminho_modelo_primeiro_imovel = modelo_imovel
    app.pasta_saida = saida

    # 5) Simular o clique em "GERAR DOCUMENTOS"
    app._ao_clicar_gerar()
    app.update()

    arquivos = sorted(f.name for f in saida.glob("*.pdf"))
    print("Mensagens capturadas:", mensagens_capturadas)
    print("Arquivos gerados:", arquivos)

    assert len(arquivos) == 4, f"esperado 4 arquivos (2 participantes x 2 docs), obteve {len(arquivos)}"
    assert mensagens_capturadas, "esperava alguma mensagem (sucesso) ao final da geração"
    assert mensagens_capturadas[-1][0] == "info", f"esperava mensagem de sucesso, obteve: {mensagens_capturadas}"

    app.destroy()
    tmp.cleanup()
    print("\nSMOKE TEST DA GUI: OK — janela real do CustomTkinter funcionou de ponta a ponta.")


if __name__ == "__main__":
    main()
