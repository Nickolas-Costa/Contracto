import calendar
from datetime import datetime
import customtkinter as ctk

from ui.theme import (
    COLOR_SURFACE, COLOR_SURFACE_VARIANT, COLOR_TEXT, COLOR_TEXT_SECONDARY, COLOR_BORDER,
    FONT_SIZE_BODY, FONT_SIZE_CAPTION, FONT_SIZE_H3,
    RADIUS_CARD, RADIUS_BUTTON, SPACING_SMALL, SPACING_MEDIUM, SPACING_LARGE,
    get_font, get_color_primary, get_color_primary_hover
)

class DatePickerPopup(ctk.CTkToplevel):
    """Popup de seleção de data ancorado logo abaixo do botão do calendário.

    Frameless card sem barra de título do SO, posicionado exatamente abaixo do
    ícone/campo, com grade de 7 colunas perfeitamente alinhada para não cortar
    o sábado.
    """

    def __init__(self, master, target_entry: ctk.CTkEntry, anchor_widget: ctk.CTkBaseClass | None = None):
        super().__init__(master)

        self.target_entry = target_entry
        self.anchor_widget = anchor_widget or target_entry
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLOR_SURFACE)

        self.current_date = datetime.now()
        self.year = self.current_date.year
        self.month = self.current_date.month

        # Tamanho otimizado para caber 7 dias sem cortar o sábado
        popup_width = 285
        popup_height = 290

        # Posicionar exatamente abaixo do botão/campo ancorado
        self.anchor_widget.update_idletasks()
        rx = self.anchor_widget.winfo_rootx()
        ry = self.anchor_widget.winfo_rooty()
        rw = self.anchor_widget.winfo_width()
        rh = self.anchor_widget.winfo_height()

        x = rx + rw - popup_width if (rx + popup_width > self.winfo_screenwidth()) else rx
        y = ry + rh + 4

        if y + popup_height > self.winfo_screenheight():
            y = max(ry - popup_height - 4, 10)

        self.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        self.grab_set()

        # Frame Card com borda elevada
        self.card = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_SURFACE,
        )
        self.card.pack(fill="both", expand=True, padx=2, pady=2)

        self._build_header()
        self._build_calendar()

    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self.card, fg_color=get_color_primary(), corner_radius=0, height=40)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        btn_prev = ctk.CTkButton(
            self.header_frame, text="<", width=28, height=28,
            fg_color="transparent", text_color="#FFFFFF", font=get_font(13, "bold"),
            hover_color=get_color_primary_hover(), command=self._prev_month
        )
        btn_prev.pack(side="left", padx=4, pady=6)

        self.lbl_month_year = ctk.CTkLabel(
            self.header_frame, text="", text_color="#FFFFFF", font=get_font(14, "bold")
        )
        self.lbl_month_year.pack(side="left", expand=True)

        btn_next = ctk.CTkButton(
            self.header_frame, text=">", width=28, height=28,
            fg_color="transparent", text_color="#FFFFFF", font=get_font(13, "bold"),
            hover_color=get_color_primary_hover(), command=self._next_month
        )
        btn_next.pack(side="right", padx=4, pady=6)

        btn_close = ctk.CTkButton(
            self.header_frame, text="✕", width=24, height=24,
            fg_color="transparent", text_color="#FFFFFF", font=get_font(12, "bold"),
            hover_color=get_color_primary_hover(), command=self.destroy
        )
        btn_close.pack(side="right", padx=(0, 4), pady=6)

    def _build_calendar(self):
        if hasattr(self, "cal_frame"):
            self.cal_frame.destroy()

        self.cal_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.cal_frame.pack(fill="both", expand=True, padx=6, pady=6)

        for col in range(7):
            self.cal_frame.grid_columnconfigure(col, weight=1, minsize=36)

        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

        self.lbl_month_year.configure(text=f"{meses[self.month-1]} {self.year}")

        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for col, dia in enumerate(dias_semana):
            ctk.CTkLabel(
                self.cal_frame, text=dia, font=get_font(11, "bold"), text_color=COLOR_TEXT
            ).grid(row=0, column=col, padx=1, pady=(2, 6))

        cal = calendar.Calendar(firstweekday=6) # Domingo como primeiro dia
        row = 1

        def select_date(d):
            return lambda: self._on_date_select(d)

        for week in cal.monthdayscalendar(self.year, self.month):
            for col, day in enumerate(week):
                if day != 0:
                    is_today = (day == self.current_date.day and 
                                self.month == self.current_date.month and 
                                self.year == self.current_date.year)

                    btn = ctk.CTkButton(
                        self.cal_frame, text=str(day), width=32, height=26,
                        font=get_font(11, "bold" if is_today else "normal"),
                        fg_color=get_color_primary() if is_today else COLOR_SURFACE_VARIANT,
                        text_color="#FFFFFF" if is_today else COLOR_TEXT,
                        hover_color=get_color_primary_hover() if is_today else COLOR_BORDER,
                        corner_radius=6,
                        command=select_date(day)
                    )
                    btn.grid(row=row, column=col, padx=1, pady=1)
            row += 1

    def _prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self._build_calendar()

    def _next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self._build_calendar()

    def _on_date_select(self, day):
        data_str = f"{day:02d}/{self.month:02d}/{self.year}"
        self.target_entry.delete(0, "end")
        self.target_entry.insert(0, data_str)
        self.grab_release()
        self.destroy()
