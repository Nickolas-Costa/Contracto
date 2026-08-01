import math
import customtkinter as ctk
from ui.theme import *

class LoadingModal(ctk.CTkToplevel):
    def __init__(self, master, message="Carregando..."):
        super().__init__(master)
        
        self.title("")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        self.configure(fg_color=COLOR_SURFACE)
        
        # Fundo sólido preto
        import tkinter as tk
        bg_color = "#000000"
        self.overlay = tk.Frame(master, bg=bg_color)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self.overlay.lift()
        
        # Center on parent
        self.update_idletasks()
        
        # Frame for card look
        self.frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=RADIUS_CARD,
                                  border_width=1, border_color=COLOR_BORDER)
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Canvas for spinner
        self.canvas_size = 40
        self.canvas = ctk.CTkCanvas(self.frame, width=self.canvas_size, height=self.canvas_size, 
                                   bg=self._apply_appearance_mode(COLOR_SURFACE), 
                                   highlightthickness=0)
        self.canvas.pack(pady=(SPACING_LARGE, SPACING_MEDIUM))
        
        self.label = ctk.CTkLabel(self.frame, text=message, font=get_font(FONT_SIZE_BODY, "bold"), 
                                 text_color=COLOR_TEXT)
        self.label.pack(padx=SPACING_XXLARGE, pady=(0, SPACING_LARGE))
        
        self._angle = 0
        self._is_running = True
        self._animate()
        
        # Wait a tiny bit to get geometry then center
        self.after(10, self._center)
        self.grab_set()
        
    def _center(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def _animate(self):
        if not self._is_running:
            return
            
        self.canvas.delete("all")
        cx = self.canvas_size / 2
        cy = self.canvas_size / 2
        radius = 12
        
        for i in range(8):
            angle_rad = math.radians(self._angle + (i * 45))
            dot_x = cx + radius * math.cos(angle_rad)
            dot_y = cy + radius * math.sin(angle_rad)
            
            # Opacity effect using sizes
            size = 2 + (i / 8) * 4
            color = COLOR_PRIMARY
            
            self.canvas.create_oval(dot_x - size, dot_y - size, dot_x + size, dot_y + size, 
                                   fill=color, outline="")
            
        self._angle = (self._angle + 10) % 360
        self.after(30, self._animate)
        
    def update_message(self, message: str):
        self.label.configure(text=message)
        self.update_idletasks()
        
    def dismiss(self):
        self._is_running = False
        self.grab_release()
        self.destroy()
        if hasattr(self, 'overlay'):
            self.overlay.destroy()
