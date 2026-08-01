import customtkinter as ctk
from ui import theme


class ConfirmModal(ctk.CTkFrame):
    """Modal de confirmação customizado."""

    def __init__(self, master, titulo: str, subtitulo: str, on_confirm=None, on_cancel=None):
        super().__init__(
            master,
            corner_radius=16,
            fg_color=theme.COLOR_SURFACE,
            bg_color="transparent",
        )
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        width = 480
        height = 240
        
        import tkinter as tk
        # Fundo sólido preto
        bg_color = "#000000"
        self.overlay = tk.Frame(master, bg=bg_color)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.overlay.lift()
        
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.configure(width=width, height=height)
        self.grid_propagate(False)

        self.lift()
        
        # Opcional: fechar com ESC no master (necessita bind no master)
        master.bind("<Escape>", lambda e: self._on_cancel(), add="+")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        lbl_icon = ctk.CTkLabel(self.header_frame, text="❓", font=theme.get_font(24))
        lbl_icon.grid(row=0, column=0, padx=(0, 12))

        lbl_title = ctk.CTkLabel(
            self.header_frame,
            text=titulo,
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            text_color=theme.COLOR_TEXT,
            anchor="w",
        )
        lbl_title.grid(row=0, column=1, sticky="w")

        btn_close = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=32,
            height=32,
            fg_color="transparent",
            text_color=theme.COLOR_TEXT_SECONDARY,
            hover_color=theme.COLOR_SURFACE_VARIANT,
            command=self._on_cancel,
        )
        btn_close.grid(row=0, column=2, sticky="e")

        # Corpo
        lbl_sub = ctk.CTkLabel(
            self,
            text=subtitulo,
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
            wraplength=432,
            justify="left",
            anchor="nw"
        )
        lbl_sub.grid(row=1, column=0, padx=24, pady=(0, 20), sticky="nsew")

        # Rodapé
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", pady=(0, 24), padx=24)
        
        # Distribui igualmente o espaço
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)

        btn_cancel = ctk.CTkButton(
            self.footer_frame,
            text="CANCELAR",
            font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
            fg_color=theme.COLOR_SURFACE_VARIANT,
            text_color=theme.COLOR_TEXT,
            hover_color=theme.COLOR_BORDER,
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._on_cancel,
        )
        btn_cancel.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        btn_action = ctk.CTkButton(
            self.footer_frame,
            text="EXECUTAR ASSIM MESMO",
            font=theme.get_font(theme.FONT_SIZE_BODY, "bold"),
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            height=44,
            corner_radius=theme.RADIUS_BUTTON,
            command=self._on_confirm_click,
        )
        btn_action.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _on_cancel(self) -> None:
        self.destroy()
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
        if self.on_cancel:
            self.on_cancel()

    def _on_confirm_click(self) -> None:
        self.destroy()
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
        if self.on_confirm:
            self.on_confirm()
