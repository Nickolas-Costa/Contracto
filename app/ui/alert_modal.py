import customtkinter as ctk
from ui import theme
from ui.base_modal import BaseModal


class AlertModal(BaseModal):
    """Modal de alerta/erro: título, subtítulo, lista de erros e botão único."""

    _instancia_ativa = None

    def __init__(self, master, titulo: str, subtitulo: str, erros: list[str] | None = None, on_close=None):
        erros = list(erros or [])
        w = 580
        h = min(360 + len(erros) * 32, 600)
        super().__init__(master, w, h)
        self.on_close_cb = on_close
        self.frame.grid_rowconfigure(1, weight=1)

        self.montar_cabecalho(
            titulo, subtitulo, icone="warning",
            cores_caixa=("#FEF3C7", "#3B2703"),
            cores_borda=("#F59E0B", "#D97706"),
        )

        if erros:
            scroll = ctk.CTkScrollableFrame(self.frame, fg_color="transparent", label_text="")
            scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
            scroll.grid_columnconfigure(0, weight=1)

            for i, erro in enumerate(erros):
                ef = ctk.CTkFrame(scroll, fg_color=theme.COLOR_SURFACE_VARIANT, corner_radius=8)
                ef.grid(row=i, column=0, sticky="ew", pady=4)
                ctk.CTkLabel(ef, text="• " + erro, font=theme.get_font(theme.FONT_SIZE_BODY), text_color=theme.COLOR_TEXT, wraplength=480, justify="left").pack(anchor="w", padx=12, pady=8)

        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 20))
        footer.grid_columnconfigure(0, weight=1)

        btn = self.botao_primario(
            footer, "ENTENDI, VOU CORRIGIR", self.dismiss,
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"), height=44,
        )
        btn.grid(row=0, column=0, sticky="ew")
        self.focar(btn)

    def dismiss(self):
        super().dismiss()
        if getattr(self, "on_close_cb", None):
            self.on_close_cb()
