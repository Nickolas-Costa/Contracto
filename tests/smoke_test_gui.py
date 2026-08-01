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
    p1.entry_cpf.insert(0, "529.982.247-25")
    p1.entry_endereco.insert(0, "Rua das Flores, 123")
    app.entry_data.insert(0, "15/07/2026")

    # 2) Adicionar dois participantes
    app._adicionar_participante()
    app._adicionar_participante()
    app.update()
    assert len(app.participant_frames) == 3, f"esperado 3 participantes, obteve {len(app.participant_frames)}"

    p2 = app.participant_frames[1]
    p2.entry_nome.insert(0, "Maria Silva")
    p2.entry_cpf.insert(0, "111.444.777-35")
    assert p2.entry_endereco is None, "participante 2 não deveria ter campo de endereço"

    p3 = app.participant_frames[2]
    p3.entry_nome.insert(0, "Pedro Silva")
    p3.entry_cpf.insert(0, "222.555.888-46")

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

    from utils import config_manager
    from utils.profile_manager import obter_perfil, atualizar_perfil, PERFIL_PADRAO_NOME
    perfil_nome = config_manager.obter("perfil_ativo") or PERFIL_PADRAO_NOME
    perfil = obter_perfil(perfil_nome)
    if perfil and len(perfil.formularios) >= 2:
        perfil.formularios[0].caminho = str(modelo_ppe)
        perfil.formularios[1].caminho = str(modelo_imovel)
        atualizar_perfil(perfil)

    app.pasta_saida = saida

    # 5) Simular o clique em "GERAR DOCUMENTOS"
    app._ao_clicar_avancar()
    
    # Aguardar thread em background concluir a geração
    import time
    for _ in range(50):
        app.update()
        time.sleep(0.05)
        if len(list(saida.glob("*.pdf"))) >= 4:
            break

    arquivos = sorted(f.name for f in saida.glob("*.pdf"))
    print("Mensagens capturadas:", mensagens_capturadas)
    print("Arquivos gerados:", arquivos)

    assert len(arquivos) == 4, f"esperado 4 arquivos (2 participantes x 2 docs), obteve {len(arquivos)}"

    app.destroy()
    tmp.cleanup()
    print("\nSMOKE TEST DA GUI: OK — janela real do CustomTkinter funcionou de ponta a ponta.")


if __name__ == "__main__":
    main()
