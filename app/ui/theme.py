"""
Design system centralizado da aplicação Contracto.

Todas as cores, tipografia, espaçamentos e raios de borda são
definidos aqui. Suporta modo claro e escuro, cores dinâmicas
carregadas das configurações do usuário, e gradientes de fundo.
"""

import customtkinter as ctk

from utils import config_manager

# ---------------------------------------------------------------------------
# Cores — Carregadas dinamicamente do config_manager
# ---------------------------------------------------------------------------

def _cor_primaria() -> str:
    return config_manager.obter("cor_destaque") or "#1E6FB3"


def _cor_primaria_hover() -> str:
    """Gera um tom mais escuro da cor primária."""
    cor = _cor_primaria()
    try:
        r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
        fator = 0.78
        r, g, b = int(r * fator), int(g * fator), int(b * fator)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return "#004785"


def _cor_primaria_light() -> str:
    """Gera um tom mais claro da cor primária misturando com branco."""
    cor = _cor_primaria()
    try:
        r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
        fator_cor = 0.4   # 40% da cor original
        fator_white = 0.6 # 60% de branco
        
        r = int(r * fator_cor + 255 * fator_white)
        g = int(g * fator_cor + 255 * fator_white)
        b = int(b * fator_cor + 255 * fator_white)
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return "#E8F0FA"


def _cor_primaria_dark_gradient() -> str:
    """Gera um tom da cor primária para gradiente em dark mode (mais saturado/destacado)."""
    cor = _cor_primaria()
    try:
        r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
        # Em vez de escurecer muito, vamos manter a cor num tom médio
        # misturando levemente com o fundo escuro para não perder a vivacidade
        fator_cor = 0.6
        bg = 30 # 0x1E
        r = int(r * fator_cor + bg * (1 - fator_cor))
        g = int(g * fator_cor + bg * (1 - fator_cor))
        b = int(b * fator_cor + bg * (1 - fator_cor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return "#003A70"

def get_color_primary_text() -> str:
    """Gera uma cor primária adequada para textos, melhorando o contraste em temas escuros."""
    if ctk.get_appearance_mode() == "Dark":
        return _cor_primaria_light()
    return _cor_primaria()


# Propriedades dinâmicas (recalculadas a cada acesso)
COLOR_PRIMARY = property(lambda self: _cor_primaria())
COLOR_PRIMARY_HOVER = property(lambda self: _cor_primaria_hover())

# Exportar como funções para uso fora de classes
def get_color_primary() -> str:
    return _cor_primaria()

def get_color_primary_hover() -> str:
    return _cor_primaria_hover()

def get_color_primary_light() -> str:
    return _cor_primaria_light()

def get_color_primary_dark_gradient() -> str:
    return _cor_primaria_dark_gradient()

# Cores estáticas (não mudam com config)
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
COLOR_BORDER_ERROR = COLOR_ERROR

# Aliases dinâmicos que serão recalculados
COLOR_PRIMARY = "#005CA9"       # Será sobrescrito por reload_theme()
COLOR_PRIMARY_HOVER = "#004785"
COLOR_BORDER_FOCUS = COLOR_PRIMARY

# ---------------------------------------------------------------------------
# Tipografia
# ---------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"
FONT_SIZE_H1 = 24
FONT_SIZE_H2 = 20
FONT_SIZE_H3 = 16
FONT_SIZE_BODY = 14
FONT_SIZE_CAPTION = 12


def get_font(size: int, weight: str = "normal") -> tuple:
    return (FONT_FAMILY, size, weight)


# ---------------------------------------------------------------------------
# Espaçamento (Grid System)
# ---------------------------------------------------------------------------
SPACING_XSMALL = 4
SPACING_SMALL = 8
SPACING_MEDIUM = 12
SPACING_LARGE = 14
SPACING_XLARGE = 24
SPACING_XXLARGE = 32

# ---------------------------------------------------------------------------
# Bordas
# ---------------------------------------------------------------------------
RADIUS_CARD = 12
RADIUS_BUTTON = 8
RADIUS_INPUT = 8

# ---------------------------------------------------------------------------
# Gradiente
# ---------------------------------------------------------------------------

def aplicar_gradiente(canvas, largura: int, altura: int, cor1: str, cor2: str, vertical: bool = True) -> None:
    """Pinta um gradiente linear num widget Canvas do tkinter.

    Args:
        canvas: Canvas do tkinter (não CTkCanvas)
        largura: largura em pixels
        altura: altura em pixels
        cor1: cor inicial (hex)
        cor2: cor final (hex)
        vertical: se True, gradiente de cima→baixo; se False, esquerda→direita
    """
    canvas.delete("gradient")

    r1, g1, b1 = int(cor1[1:3], 16), int(cor1[3:5], 16), int(cor1[5:7], 16)
    r2, g2, b2 = int(cor2[1:3], 16), int(cor2[3:5], 16), int(cor2[5:7], 16)

    passos = altura if vertical else largura
    # Desenhar em blocos de 2px para performance
    bloco = 2
    for i in range(0, passos, bloco):
        t = i / max(passos - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        cor = f"#{r:02x}{g:02x}{b:02x}"

        if vertical:
            canvas.create_rectangle(0, i, largura, i + bloco, fill=cor, outline="", tags="gradient")
        else:
            canvas.create_rectangle(i, 0, i + bloco, altura, fill=cor, outline="", tags="gradient")


# ---------------------------------------------------------------------------
# Configuração global
# ---------------------------------------------------------------------------

def reload_theme() -> None:
    """Recarrega as cores dinâmicas a partir das configurações salvas.
    
    Deve ser chamado após alterar a cor de destaque no config_manager.
    """
    global COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_BORDER_FOCUS
    COLOR_PRIMARY = get_color_primary()
    COLOR_PRIMARY_HOVER = get_color_primary_hover()
    COLOR_BORDER_FOCUS = COLOR_PRIMARY


def configure_appearance() -> None:
    """Configurações globais de aparência da aplicação."""
    aparencia = config_manager.obter("aparencia") or "system"
    ctk.set_appearance_mode(aparencia)
    ctk.set_default_color_theme("blue")
    reload_theme()
