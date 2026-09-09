import customtkinter as ctk
from typing import Callable, Optional

from ui.theme import *

class FeedbackToast(ctk.CTkFrame):
    def __init__(
        self,
        master,
        message: str,
        type: str = 'success',
        on_dismiss: Optional[Callable[[], None]] = None,
        duration_ms: int = 4000,
    ):
        super().__init__(master, fg_color="transparent")
        self._on_dismiss = on_dismiss
        self._duration_ms = duration_ms
        
        self.type_config = {
            'success': {'color': COLOR_SUCCESS, 'icon': '✓'},
            'warning': {'color': COLOR_WARNING, 'icon': '⚠'},
            'error': {'color': COLOR_ERROR, 'icon': '✕'}
        }
        
        config = self.type_config.get(type, self.type_config['success'])
        
        self.toast_frame = ctk.CTkFrame(self, fg_color=config['color'], corner_radius=RADIUS_BUTTON)
        self.toast_frame.pack(padx=SPACING_MEDIUM, pady=SPACING_MEDIUM, fill="both", expand=True)
        
        self.icon_label = ctk.CTkLabel(self.toast_frame, text=config['icon'], 
                                      font=get_font(FONT_SIZE_H3, "bold"), text_color="#FFFFFF")
        self.icon_label.pack(side="left", padx=(SPACING_MEDIUM, SPACING_SMALL), pady=SPACING_SMALL)
        
        self.msg_label = ctk.CTkLabel(self.toast_frame, text=message, 
                                     font=get_font(FONT_SIZE_BODY), text_color="#FFFFFF")
        self.msg_label.pack(side="left", padx=(0, SPACING_MEDIUM), pady=SPACING_SMALL)
        
    def show(self, parent_width, parent_height):
        # We will position it at the bottom center of the parent
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        x = (parent_width // 2) - (width // 2)
        y = parent_height - height - SPACING_XXLARGE
        
        self.place(x=x, y=y)
        
        self.after(self._duration_ms, self._dismiss)

    def _dismiss(self):
        callback = self._on_dismiss
        self._on_dismiss = None
        try:
            self.destroy()
        finally:
            if callback:
                callback()

def show_toast(
    parent,
    message: str,
    type: str = 'success',
    on_dismiss: Optional[Callable[[], None]] = None,
    duration_ms: int = 4000,
):
    toast = FeedbackToast(parent, message, type, on_dismiss, duration_ms)
    # Wait for the widget to be ready
    parent.update_idletasks()
    toast.show(parent.winfo_width(), parent.winfo_height())
    return toast
