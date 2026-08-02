import math
import customtkinter as ctk
from ui.theme import *


class LoadingModal:
    """Modal de carregamento reutilizável com overlay escuro translúcido e cartão alinhado."""

    def __init__(self, master, message="Carregando..."):
        self.master = master

        try:
            master.update_idletasks()
        except Exception:
            pass

        sw = master.winfo_screenwidth()
        sh = master.winfo_screenheight()

        w, h = 340, 160

        offset_x = 110
        offset_y = 35

        x = (sw - w) // 2 + offset_x
        y = (sh - h) // 2 + offset_y

        # 1. Overlay escuro translúcido (60% opacidade / vidro escuro) cobrindo a tela inteira (0,0)
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

        # 2. Cartão de carregamento sólido no topo (alinhado sobre o conteúdo)
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
        self.canvas_size = 40
        self.canvas = ctk.CTkCanvas(
            self.frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=self.card._apply_appearance_mode(COLOR_SURFACE),
            highlightthickness=0,
        )
        self.canvas.pack(pady=(SPACING_LARGE, SPACING_MEDIUM))

        self.label = ctk.CTkLabel(
            self.frame,
            text=message,
            font=get_font(FONT_SIZE_BODY, "bold"),
            text_color=COLOR_TEXT,
        )
        self.label.pack(padx=SPACING_XXLARGE, pady=(0, SPACING_LARGE))

        self.card.deiconify()
        self.card.lift()

        self._angle = 0
        self._is_running = True
        self._animate()

    def _animate(self):
        if not self._is_running:
            return

        try:
            self.canvas.delete("all")
            cx = self.canvas_size / 2
            cy = self.canvas_size / 2
            radius = 12

            for i in range(8):
                angle_rad = math.radians(self._angle + (i * 45))
                dot_x = cx + radius * math.cos(angle_rad)
                dot_y = cy + radius * math.sin(angle_rad)

                size = 2 + (i / 8) * 4
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

    def update_message(self, message: str):
        if hasattr(self, "label") and self.label.winfo_exists():
            self.label.configure(text=message)

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
