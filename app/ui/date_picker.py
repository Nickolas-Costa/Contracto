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
    def __init__(self, master, target_entry: ctk.CTkEntry):
        super().__init__(master)
        
        self.target_entry = target_entry
        self.title("Selecionar Data")
        self.geometry("260x320")
        self.resizable(False, False)
        
        # Make it a popup
        self.transient(master.winfo_toplevel())
        self.grab_set()
        
        self.current_date = datetime.now()
        self.year = self.current_date.year
        self.month = self.current_date.month
        
        self.configure(fg_color=COLOR_SURFACE)
        
        self._build_header()
        self._build_calendar()
        
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color=get_color_primary(), corner_radius=0)
        self.header_frame.pack(fill="x")
        
        btn_prev = ctk.CTkButton(
            self.header_frame, text="<", width=30, height=30,
            fg_color="transparent", text_color="#FFFFFF", font=get_font(FONT_SIZE_H3, "bold"),
            hover_color=get_color_primary_hover(), command=self._prev_month
        )
        btn_prev.pack(side="left", padx=SPACING_SMALL, pady=SPACING_MEDIUM)
        
        self.lbl_month_year = ctk.CTkLabel(
            self.header_frame, text="", text_color="#FFFFFF", font=get_font(FONT_SIZE_H3, "bold")
        )
        self.lbl_month_year.pack(side="left", expand=True)
        
        btn_next = ctk.CTkButton(
            self.header_frame, text=">", width=30, height=30,
            fg_color="transparent", text_color="#FFFFFF", font=get_font(FONT_SIZE_H3, "bold"),
            hover_color=get_color_primary_hover(), command=self._next_month
        )
        btn_next.pack(side="right", padx=SPACING_SMALL, pady=SPACING_MEDIUM)
        
    def _build_calendar(self):
        if hasattr(self, "cal_frame"):
            self.cal_frame.destroy()
            
        self.cal_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cal_frame.pack(fill="both", expand=True, padx=SPACING_SMALL, pady=SPACING_SMALL)
        
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                 
        self.lbl_month_year.configure(text=f"{meses[self.month-1]} {self.year}")
        
        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for col, dia in enumerate(dias_semana):
            ctk.CTkLabel(
                self.cal_frame, text=dia, font=get_font(FONT_SIZE_BODY, "bold"), text_color=COLOR_TEXT
            ).grid(row=0, column=col, padx=2, pady=5)
            
        cal = calendar.Calendar(firstweekday=6) # Sunday first
        row = 1
        
        # Helper to select date
        def select_date(d):
            return lambda: self._on_date_select(d)
            
        for week in cal.monthdayscalendar(self.year, self.month):
            for col, day in enumerate(week):
                if day != 0:
                    is_today = (day == self.current_date.day and 
                                self.month == self.current_date.month and 
                                self.year == self.current_date.year)
                    
                    btn = ctk.CTkButton(
                        self.cal_frame, text=str(day), width=30, height=30,
                        font=get_font(FONT_SIZE_BODY, "bold" if is_today else "normal"),
                        fg_color=get_color_primary() if is_today else COLOR_SURFACE_VARIANT,
                        text_color="#FFFFFF" if is_today else get_color_primary(),
                        hover_color=get_color_primary_hover() if is_today else COLOR_BORDER,
                        corner_radius=RADIUS_BUTTON,
                        command=select_date(day)
                    )
                    btn.grid(row=row, column=col, padx=2, pady=2)
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
        self.destroy()
