import customtkinter as ctk
from ui.theme import *

class FeedbackToast(ctk.CTkFrame):
    def __init__(self, master, message: str, type: str = 'success'):
        super().__init__(master, fg_color="transparent")
        
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
        
        # Simple auto-dismiss after 4 seconds
        self.after(4000, self.destroy)

def show_toast(parent, message: str, type: str = 'success'):
    toast = FeedbackToast(parent, message, type)
    # Wait for the widget to be ready
    parent.update_idletasks()
    toast.show(parent.winfo_width(), parent.winfo_height())
