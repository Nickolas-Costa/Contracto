import customtkinter as ctk
from ui import theme
from ui.base_modal import BaseModal


class ConfirmModal(BaseModal):
    """Modal de confirmação binária (Confirmar/Cancelar). Não fecha no overlay."""

    _instancia_ativa = None

    def __init__(
        self,
        master,
        titulo: str,
        subtitulo: str,
        on_confirm=None,
        on_cancel=None,
        texto_confirmar="Confirmar",
        texto_cancelar="Cancelar",
    ):
        super().__init__(master, 540, 250, fechar_no_overlay=False)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.frame.grid_rowconfigure(1, weight=1)

        self.montar_cabecalho(titulo, subtitulo)

        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 20))
        footer.grid_columnconfigure(1, weight=1)

        self.botao_secundario(footer, texto_cancelar, self._do_cancel).grid(
            row=0, column=0, padx=(0, 12)
        )
        btn_confirmar = self.botao_primario(footer, texto_confirmar, self._do_confirm)
        btn_confirmar.grid(row=0, column=1, sticky="ew")
        self.focar(btn_confirmar)

    def _do_confirm(self):
        self.dismiss()
        if self.on_confirm:
            self.on_confirm()

    def _do_cancel(self):
        self.dismiss()
        if self.on_cancel:
            self.on_cancel()
