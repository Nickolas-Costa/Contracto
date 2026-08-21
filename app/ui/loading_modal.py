"""
Modal de carregamento dinâmico e profissional da aplicação Contracto.
Utiliza animações GIF rotativas em alta definição para proporcionar uma experiência fluida.
"""

from typing import Callable, Optional
import customtkinter as ctk
from ui.theme import *
from ui.animated_loader import AnimatedGifLabel


class LoadingModal:
    """Modal de carregamento reutilizável com overlay escuro translúcido, indicação de etapas e loaders animados em rotação."""

    _instancia_ativa = None

    def __init__(
        self,
        master,
        message: str = "Carregando...",
        submessage: str = "",
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        if LoadingModal._instancia_ativa is not None:
            try:
                LoadingModal._instancia_ativa.dismiss()
            except Exception:
                pass
        LoadingModal._instancia_ativa = self

        root = master.winfo_toplevel()
        self.master = root
        self.on_cancel = on_cancel
        self._cancel_requested = False

        # Dimensões dinâmicas conforme a presença do botão de parar ou submensagem
        if on_cancel:
            w, h = 380, 210
        else:
            w, h = 340, 170

        # 1. Overlay escuro translúcido
        self.overlay = ctk.CTkToplevel(root)
        # 2. Cartão de carregamento sólido
        self.card = ctk.CTkToplevel(root)

        configurar_janela_modal(root, self.card, self.overlay, w, h)

        self.frame = ctk.CTkFrame(
            self.card,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Loader animado com GIF rotativo em alta resolução
        self.spinner = AnimatedGifLabel(self.frame, size=(46, 46))
        self.spinner.pack(pady=(SPACING_LARGE, SPACING_SMALL))

        self.label = ctk.CTkLabel(
            self.frame,
            text=message,
            font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=COLOR_TEXT,
        )
        self.label.pack(padx=SPACING_LARGE, pady=(0, 2))

        self.sublabel = ctk.CTkLabel(
            self.frame,
            text=submessage,
            font=get_font(FONT_SIZE_CAPTION),
            text_color=COLOR_TEXT_SECONDARY,
        )
        if submessage:
            self.sublabel.pack(padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
        else:
            self.sublabel.pack_forget()

        # Botão opcional de Parar / Cancelar
        if on_cancel is not None:
            self.btn_cancel = ctk.CTkButton(
                self.frame,
                text="⏹ Parar Processo",
                width=140,
                height=30,
                corner_radius=RADIUS_BUTTON,
                fg_color=COLOR_SURFACE_VARIANT,
                text_color=COLOR_TEXT,
                hover_color=COLOR_BORDER,
                border_width=1,
                border_color=COLOR_BORDER,
                font=get_font(FONT_SIZE_CAPTION, "bold"),
                command=self._ao_clicar_cancelar,
            )
            self.btn_cancel.pack(pady=(SPACING_SMALL, SPACING_MEDIUM))
        else:
            self.btn_cancel = None

    def _ao_clicar_cancelar(self) -> None:
        if self._cancel_requested:
            return
        self._cancel_requested = True
        if self.btn_cancel and self.btn_cancel.winfo_exists():
            self.btn_cancel.configure(text="Cancelando...", state="disabled")
        if self.on_cancel:
            self.on_cancel()

    def update_message(self, message: str, submessage: str = "") -> None:
        try:
            if hasattr(self, "label") and self.label.winfo_exists():
                self.label.configure(text=message)
            if hasattr(self, "sublabel") and self.sublabel.winfo_exists():
                if submessage:
                    self.sublabel.configure(text=submessage)
                    if not self.sublabel.winfo_ismapped():
                        if self.btn_cancel and self.btn_cancel.winfo_ismapped():
                            self.sublabel.pack(before=self.btn_cancel, padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
                        else:
                            self.sublabel.pack(padx=SPACING_LARGE, pady=(0, SPACING_SMALL))
                else:
                    self.sublabel.pack_forget()
        except Exception:
            pass

    def atualizar_etapa(self, etapa: int, total: int, descricao: str) -> None:
        """Atualiza a mensagem de progresso com formato amigável em etapas (ex: Etapa 1/4)."""
        sub = f"(Etapa {etapa}/{total}: {descricao})"
        self.update_message("Processando documentos...", sub)

    def dismiss(self) -> None:
        if LoadingModal._instancia_ativa is self:
            LoadingModal._instancia_ativa = None
        try:
            if hasattr(self, "spinner") and self.spinner and self.spinner.winfo_exists():
                self.spinner.stop_animation()
        except Exception:
            pass
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
