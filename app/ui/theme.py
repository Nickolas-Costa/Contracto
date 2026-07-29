import customtkinter as ctk

# Cores
COLOR_PRIMARY = "#005CA9"  # Azul Caixa
COLOR_PRIMARY_HOVER = "#004785"
COLOR_SUCCESS = "#2E7D32"
COLOR_WARNING = "#F57C00"
COLOR_ERROR = "#D32F2F"

COLOR_BACKGROUND = ("#F5F5F5", "#1E1E1E")
COLOR_SURFACE = ("#FFFFFF", "#2B2B2B")
COLOR_SURFACE_VARIANT = ("#F0F0F0", "#333333")

COLOR_TEXT = ("#212121", "#E0E0E0")
COLOR_TEXT_SECONDARY = ("#666666", "#AAAAAA")
COLOR_TEXT_DISABLED = ("#9E9E9E", "#757575")

COLOR_BORDER = ("#E0E0E0", "#424242")
COLOR_BORDER_FOCUS = COLOR_PRIMARY
COLOR_BORDER_ERROR = COLOR_ERROR

# Tipografia
FONT_FAMILY = "Segoe UI"
FONT_SIZE_H1 = 24
FONT_SIZE_H2 = 20
FONT_SIZE_H3 = 16
FONT_SIZE_BODY = 14
FONT_SIZE_CAPTION = 12

def get_font(size: int, weight: str = "normal") -> tuple:
    return (FONT_FAMILY, size, weight)

# Espaçamento (Grid System)
SPACING_XSMALL = 4
SPACING_SMALL = 8
SPACING_MEDIUM = 12
SPACING_LARGE = 16
SPACING_XLARGE = 24
SPACING_XXLARGE = 32

# Bordas
RADIUS_CARD = 12
RADIUS_BUTTON = 8
RADIUS_INPUT = 8

def configure_appearance():
    """Configurações globais de aparência da aplicação."""
    ctk.set_appearance_mode("system")  # Segue o sistema (Light/Dark)
    ctk.set_default_color_theme("blue")
