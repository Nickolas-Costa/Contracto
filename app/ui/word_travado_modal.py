import customtkinter as ctk
from ui import theme


class WordTravadoModal:
    """Aviso de Word sem resposta com contagem regressiva visível.

    Exibe o prazo antes do encerramento automático da instância travada.
    "Fechar agora" encerra de imediato; fechar a janela apenas dispensa
    o aviso (o prazo do serviço continua valendo).
    """

    _instancia_ativa = None

    def __init__(self, master, nome_arquivo: str, prazo_segundos: int, on_fechar_agora=None):
        if WordTravadoModal._instancia_ativa is not None:
            try:
                WordTravadoModal._instancia_ativa.dismiss()
            except Exception:
                pass
        WordTravadoModal._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root
        self.on_fechar_agora = on_fechar_agora
        self.restantes = max(1, int(prazo_segundos))

        w, h = 560, 300
        self.overlay = ctk.CTkToplevel(root)
        self.card = ctk.CTkToplevel(root)

        theme.configurar_janela_modal(root, self.card, self.overlay, w, h)
        self.card.bind("<Escape>", lambda e: self.dismiss())

        self.frame = ctk.CTkFrame(
            self.card,
            fg_color=theme.COLOR_SURFACE,
            corner_radius=theme.RADIUS_CARD,
            border_width=1,
            border_color=theme.COLOR_BORDER,
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 6))
        header.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(
            header, width=42, height=42, corner_radius=10,
            fg_color=("#FEF3C7", "#3B2703"), border_width=1,
            border_color=("#F59E0B", "#B45309"),
        )
        icon_box.grid(row=0, column=0, padx=(0, 12))
        icon_box.grid_propagate(False)
        ctk.CTkLabel(
            icon_box, text="",
            image=theme.get_icon("warning", (24, 24)),
        ).pack(expand=True)

        ctk.CTkLabel(
            header, text="O Word parou de responder",
            font=theme.get_font(theme.FONT_SIZE_H3, "bold"),
            text_color=theme.COLOR_TEXT,
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            self.frame,
            text=(
                f"O Word parece travado ao converter '{nome_arquivo}'. "
                "Ele será fechado automaticamente para o processo continuar."
            ),
            font=theme.get_font(theme.FONT_SIZE_BODY),
            text_color=theme.COLOR_TEXT_SECONDARY,
            wraplength=480,
            justify="left",
        ).grid(row=1, column=0, sticky="nw", padx=24, pady=(0, 4))

        self.lbl_contagem = ctk.CTkLabel(
            self.frame, text=f"{self.restantes} s",
            font=theme.get_font(theme.FONT_SIZE_H2, "bold"),
            text_color=theme.get_color_primary_text(),
        )
        self.lbl_contagem.grid(row=2, column=0, sticky="n", padx=24, pady=(0, 4))

        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=24, pady=(4, 20))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(
            footer, text="Fechar agora",
            fg_color=theme.get_color_primary(),
            text_color="#FFFFFF",
            hover_color=theme.get_color_primary_hover(),
            corner_radius=theme.RADIUS_BUTTON,
            height=38,
            command=self._do_fechar_agora,
        ).grid(row=0, column=0, sticky="ew")

        self._agendar_tick()

    def _agendar_tick(self) -> None:
        try:
            if not self.card.winfo_exists():
                return
            self.card.after(1000, self._tick)
        except Exception:
            pass

    def _tick(self) -> None:
        try:
            if not self.card.winfo_exists():
                return
            self.restantes -= 1
            if self.restantes <= 0:
                self.dismiss()
                return
            self.lbl_contagem.configure(text=f"{self.restantes} s")
            self._agendar_tick()
        except Exception:
            pass

    def _do_fechar_agora(self):
        self.dismiss()
        if self.on_fechar_agora:
            self.on_fechar_agora()

    def dismiss(self):
        if WordTravadoModal._instancia_ativa is self:
            WordTravadoModal._instancia_ativa = None
        try:
            if hasattr(self, "card") and self.card and self.card.winfo_exists():
                self.card.destroy()
        except Exception:
            pass
        try:
            if hasattr(self, "overlay") and self.overlay and self.overlay.winfo_exists():
                self.overlay.destroy()
        except Exception:
            pass
        try:
            self.master.update_idletasks()
        except Exception:
            pass
