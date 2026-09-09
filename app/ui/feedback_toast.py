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
        super().__init__(
            master,
            fg_color=COLOR_SURFACE,
            corner_radius=RADIUS_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self._on_dismiss = on_dismiss
        self._duration_ms = duration_ms
        self._dismiss_timer = None
        
        self.type_config = {
            'success': {'color': COLOR_SUCCESS, 'icon': '✓'},
            'info': {'color': get_color_primary(), 'icon': 'i'},
            'warning': {'color': COLOR_WARNING, 'icon': '!'},
            'error': {'color': COLOR_ERROR, 'icon': '✕'}
        }
        
        config = self.type_config.get(type, self.type_config['success'])
        
        self.toast_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=RADIUS_BUTTON)
        self.toast_frame.pack(padx=SPACING_SMALL, pady=SPACING_SMALL, fill="both", expand=True)
        
        self.icon_label = ctk.CTkLabel(
            self.toast_frame, text=config['icon'], width=32, height=32,
            fg_color=config['color'], corner_radius=RADIUS_BUTTON,
            font=get_font(FONT_SIZE_BODY, "bold"), text_color="#FFFFFF",
        )
        self.icon_label.pack(side="left", padx=(SPACING_XSMALL, SPACING_SMALL), pady=SPACING_XSMALL)
        
        self.msg_label = ctk.CTkLabel(
            self.toast_frame, text=message, wraplength=390, justify="left",
            font=get_font(FONT_SIZE_BODY), text_color=COLOR_TEXT,
        )
        self.msg_label.pack(side="left", padx=(0, SPACING_MEDIUM), pady=SPACING_SMALL)
        
    def show(self, parent_width, parent_height):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        x = max(SPACING_MEDIUM, parent_width - width - SPACING_LARGE)
        self.place(x=x, y=58)
        self.lift()
        self._dismiss_timer = self.after(self._duration_ms, self._dismiss)

    def _dismiss(self):
        if not self.winfo_exists():
            return
        if self._dismiss_timer is not None:
            try:
                self.after_cancel(self._dismiss_timer)
            except Exception:
                pass
            self._dismiss_timer = None
        callback = self._on_dismiss
        self._on_dismiss = None
        if getattr(self.master, "_feedback_toast_ativo", None) is self:
            self.master._feedback_toast_ativo = None
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
    anterior = getattr(parent, "_feedback_toast_ativo", None)
    if anterior is not None and anterior.winfo_exists():
        anterior._dismiss()
    toast = FeedbackToast(parent, message, type, on_dismiss, duration_ms)
    parent._feedback_toast_ativo = toast
    parent.update_idletasks()
    toast.show(parent.winfo_width(), parent.winfo_height())
    return toast
