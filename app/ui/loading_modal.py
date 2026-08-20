import math
from typing import Callable, Optional
import customtkinter as ctk
from ui.theme import *


class LoadingModal:
    """Modal de carregamento reutilizável com overlay escuro translúcido, indicação de etapas e botão de parar opcional."""

    def __init__(
        self,
        master,
        message: str = "Carregando...",
        submessage: str = "",
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        self.master = master
        self.on_cancel = on_cancel
        self._cancel_requested = False

        try:
            master.update_idletasks()
        except Exception:
            pass

        sw = master.winfo_screenwidth()
        sh = master.winfo_screenheight()

        # Dimensões dinâmicas conforme a presença do botão de parar ou submensagem
        if on_cancel:
            w, h = 380, 200
        else:
            w, h = 340, 160

        offset_x = 110
        offset_y = 35

        x = (sw - w) // 2 + offset_x
        y = (sh - h) // 2 + offset_y

        # 1. Overlay escuro translúcido cobrindo a tela inteira
        self.overlay = ctk.CTkToplevel(master)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.configure(fg_color="#000000")
        try:
            self.overlay.attributes("-alpha", 0.60)
        except Exception:
            pass
        self.overlay.geometry(f"{sw}x{sh}+0+0")
        self.overlay.deiconify()
        self.overlay.lift()

        # 2. Cartão de carregamento sólido no topo
        self.card = ctk.CTkToplevel(master)
        self.card.withdraw()
        self.card.overrideredirect(True)
        self.card.configure(fg_color=COLOR_SURFACE)
        try:
            self.card.attributes("-topmost", True)
        except Exception:
            pass
        self.card.geometry(f"{w}x{h}+{x}+{y}")

        self.frame = ctk.CTkFrame(
            self.card,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Canvas para o spinner
        self.canvas_size = 36
        self.canvas = ctk.CTkCanvas(
            self.frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=self.card._apply_appearance_mode(COLOR_SURFACE),
            highlightthickness=0,
        )
        self.canvas.pack(pady=(SPACING_MEDIUM, SPACING_SMALL))

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

        self.card.deiconify()
        self.card.lift()

        self._angle = 0
        self._is_running = True
        self._animate()

    def _ao_clicar_cancelar(self) -> None:
        if self._cancel_requested:
            return
        self._cancel_requested = True
        if self.btn_cancel and self.btn_cancel.winfo_exists():
            self.btn_cancel.configure(text="Cancelando...", state="disabled")
        if self.on_cancel:
            self.on_cancel()

    def _animate(self):
        if not self._is_running:
            return

        try:
            self.canvas.delete("all")
            cx = self.canvas_size / 2
            cy = self.canvas_size / 2
            radius = 11

            for i in range(8):
                angle_rad = math.radians(self._angle + (i * 45))
                dot_x = cx + radius * math.cos(angle_rad)
                dot_y = cy + radius * math.sin(angle_rad)

                size = 2 + (i / 8) * 3.5
                color = COLOR_PRIMARY

                self.canvas.create_oval(
                    dot_x - size,
                    dot_y - size,
                    dot_x + size,
                    dot_y + size,
                    fill=color,
                    outline="",
                )

            self._angle = (self._angle + 10) % 360
            if self._is_running and hasattr(self, "card") and self.card.winfo_exists():
                self.card.after(30, self._animate)
        except Exception:
            pass

    def update_message(self, message: str, submessage: str = ""):
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

    def atualizar_etapa(self, etapa: int, total: int, descricao: str):
        """Atualiza a mensagem de progresso com formato amigável em etapas (ex: Etapa 1/4)."""
        sub = f"(Etapa {etapa}/{total}: {descricao})"
        self.update_message("Processando documentos...", sub)

    def dismiss(self):
        self._is_running = False
        try:
            if hasattr(self, "card") and self.card.winfo_exists():
                self.card.destroy()
        except Exception:
            pass
        try:
            if hasattr(self, "overlay") and self.overlay.winfo_exists():
                self.overlay.destroy()
        except Exception:
            pass
