"""
Testes unitários para o módulo de loaders animados, ciclo de rotação e carregamento de ícones adaptativos.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Adiciona o diretório app ao path
app_dir = Path(__file__).resolve().parent.parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from ui.animated_loader import (
    SimpleLoader,
    AnimatedGifLabel,
)
from ui.theme import get_icon
import version


class TestVisualAssets(unittest.TestCase):
    """Valida a existência dos ícones vetoriais e o componente de carregamento leve."""

    def tearDown(self):
        # CTkImage guarda internamente PhotoImages vinculadas ao interpretador Tk.
        # Cada teste cria sua própria raiz, portanto o cache precisa ser renovado.
        from ui import theme
        theme._ICONS_CACHE.clear()

    def test_version_is_current(self):
        """Verifica se a versão centralizada está definida como 4.5.12."""
        self.assertEqual(version.__version__, "4.5.12")

    def test_simple_loader_instantiation(self):
        """Verifica se o componente SimpleLoader pode ser instanciado sem erros."""
        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()
        try:
            loader = SimpleLoader(root, width=150, height=6)
            self.assertIsNotNone(loader)
            loader.stop_animation()
            
            compat_label = AnimatedGifLabel(root)
            self.assertIsNotNone(compat_label)
            compat_label.stop_animation()
        finally:
            root.destroy()

    def test_get_icon_loads_valid_ctk_image(self):
        """Verifica se a função get_icon retorna CTkImage com sucesso para ícones padrão."""
        icon_names = [
            "home", "profiles", "settings", "help", "question_circle",
            "calendar", "location", "advance", "back", "success", "folder",
            "trash", "check", "edit", "copy", "user_add", "finish"
        ]
        for nome in icon_names:
            dark_file = app_dir / "assets" / "icons" / f"{nome}_dark.png"
            light_file = app_dir / "assets" / "icons" / f"{nome}_light.png"
            self.assertTrue(dark_file.exists(), f"Ícone escuro {dark_file} não existe.")
            self.assertTrue(light_file.exists(), f"Ícone claro {light_file} não existe.")

            img = get_icon(nome, (20, 20))
            self.assertIsNotNone(img)

    def test_placeholder_nao_vira_texto_editavel_apos_limpar(self):
        import customtkinter as ctk
        from ui.campo_dinamico_widget import CampoDinamicoWidget
        from utils.profile_manager import CampoEntrada

        root = ctk.CTk()
        root.withdraw()
        try:
            widget = CampoDinamicoWidget(
                root,
                CampoEntrada(
                    id="pisPasep", rotulo="PIS/PASEP", tipo="PIS_PASEP",
                    placeholder="000.00000.00-0",
                ),
            )
            widget.pack()
            widget.entry.focus_force()
            root.update()
            widget.entry.delete(0, "end")
            widget._ao_digitar(type("Event", (), {"keysym": "BackSpace"})())
            widget.entry._entry.insert("end", "164.85838.49-0")

            self.assertEqual(widget.entry._entry.get(), "164.85838.49-0")
        finally:
            root.destroy()

    def test_cartao_de_participante_some_em_pagina_sem_campos(self):
        import customtkinter as ctk
        from ui.participant_frame import ParticipantFrame
        from utils.profile_manager import CampoEntrada

        root = ctk.CTk()
        root.withdraw()
        try:
            frame = ParticipantFrame(
                root, indice=1, principal=True,
                campos_customizados=[
                    CampoEntrada(id="endereco", rotulo="Endereço", aba="Dados do Comprador")
                ],
            )
            frame.grid()

            self.assertFalse(frame.aplicar_pagina("Dados do Vendedor", primeira=False))
            self.assertEqual(frame.winfo_manager(), "")
            self.assertTrue(frame.aplicar_pagina("Dados do Comprador", primeira=True))
            self.assertEqual(frame.winfo_manager(), "grid")
        finally:
            root.destroy()

    def test_campos_padrao_reaparecem_ao_sair_de_perfil_paginado(self):
        import customtkinter as ctk
        from ui.participant_frame import ParticipantFrame
        from utils.profile_manager import CampoEntrada

        root = ctk.CTk()
        root.withdraw()
        try:
            frame = ParticipantFrame(
                root, indice=1, principal=True,
                campos_customizados=[
                    CampoEntrada(id="campo_final", rotulo="Campo final", aba="Página final")
                ],
            )
            frame.grid()
            frame.aplicar_pagina("Página final", primeira=False)
            self.assertEqual(frame.entry_nome.winfo_manager(), "")
            self.assertEqual(frame.entry_cpf.winfo_manager(), "")

            frame.reconstruir_campos_customizados([
                CampoEntrada(id="endereco", rotulo="Endereço", aba="Geral")
            ])
            frame.aplicar_pagina(None)

            self.assertEqual(frame.entry_nome.winfo_manager(), "grid")
            self.assertEqual(frame.entry_cpf.winfo_manager(), "grid")
            self.assertTrue(all(
                controle.winfo_manager() == "grid"
                for controle in frame._controles_campos_padrao
            ))
        finally:
            root.destroy()

    def test_main_window_initialization(self):
        """Verifica se MainWindow inicializa e carrega todas as telas e ícones sem exceções."""
        from ui.main_window import MainWindow
        win = MainWindow()
        win.withdraw()
        try:
            self.assertIsNotNone(win.icon_home)
            self.assertIsNotNone(win.icon_profiles)
            self.assertIsNotNone(win.icon_settings)
            self.assertIsNotNone(win.icon_calendar)
            self.assertIsNotNone(win.icon_help)
            self.assertEqual(win.botao_avancar.cget("state"), "normal")
            self.assertEqual(win.frame_pendencias.winfo_manager(), "")

            win._pendencias_reveladas = True
            win._atualizar_estado_geracao()
            self.assertEqual(win.frame_pendencias.winfo_manager(), "grid")
            self.assertIn("Faltam", win.label_pendencias_titulo.cget("text"))

            # Testar navegação entre telas
            win._mostrar_tela("perfis")
            win._mostrar_tela("config")
            win._mostrar_tela("inicio")
        finally:
            win.destroy()

    def test_pendencias_aparecem_somente_depois_do_toast(self):
        from ui.main_window import MainWindow

        win = MainWindow()
        win.withdraw()
        try:
            self.assertEqual(win.frame_pendencias.winfo_manager(), "")
            with patch("ui.main_window.show_toast") as toast:
                win._ao_clicar_avancar()

            self.assertEqual(win.frame_pendencias.winfo_manager(), "")
            self.assertEqual(toast.call_count, 1)
            self.assertEqual(toast.call_args.args[2], "warning")

            toast.call_args.kwargs["on_dismiss"]()
            self.assertEqual(win.frame_pendencias.winfo_manager(), "grid")
        finally:
            win.destroy()

    def test_navegacao_distingue_formulario_de_pagina(self):
        from ui.main_window import MainWindow

        win = MainWindow()
        win.withdraw()
        try:
            win._paginas_perfil = [
                "DAMP • Dados pessoais",
                "DAMP • Modalidade",
                "ITBI • Partes da operação",
            ]
            win._indice_pagina = 0
            win._mostrar_pagina_atual()

            self.assertEqual(win.label_formulario_contador.cget("text"), "FORMULÁRIO 1/2")
            self.assertEqual(win.label_formulario_nome.cget("text"), "DAMP")
            self.assertEqual(win.label_pagina_contador.cget("text"), "PÁGINA 1/2")
            self.assertEqual(win.label_pagina.cget("text"), "Dados pessoais")
        finally:
            win.destroy()

    def test_calendario_libera_captura_ao_fechar(self):
        import customtkinter as ctk
        from ui.date_picker import DatePickerPopup

        root = ctk.CTk()
        root.withdraw()
        try:
            entry = ctk.CTkEntry(root)
            entry.pack()
            popup = DatePickerPopup(root, entry)
            self.assertIs(root.grab_current(), popup)

            popup.destroy()
            root.update_idletasks()

            self.assertIsNone(root.grab_current())
            self.assertEqual(entry.cget("state"), "normal")
        finally:
            root.destroy()

    def test_janela_recupera_campos_de_texto_bloqueados(self):
        from ui.main_window import MainWindow

        win = MainWindow()
        win.withdraw()
        try:
            participante = win.participant_frames[0]
            participante.entry_nome.configure(state="disabled")
            participante.entry_cpf.configure(state="disabled")

            win._recuperar_interacao_campos()

            self.assertEqual(participante.entry_nome.cget("state"), "normal")
            self.assertEqual(participante.entry_cpf.cget("state"), "normal")
        finally:
            win.destroy()


if __name__ == "__main__":
    unittest.main()
