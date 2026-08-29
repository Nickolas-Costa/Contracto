"""
Design system centralizado da aplicação Contracto.

Todas as cores, tipografia, espaçamentos e raios de borda são
definidos aqui. Suporta modo claro e escuro, cores dinâmicas
carregadas das configurações do usuário, e gradientes de fundo.
"""

import customtkinter as ctk

from utils import config_manager

# ---------------------------------------------------------------------------
# Cores — Carregadas dinamicamente do config_manager com cache em memória
# ---------------------------------------------------------------------------

_cor_primaria_cache: str | None = None
_cor_hover_cache: str | None = None
_cor_light_cache: str | None = None
_cor_dark_grad_cache: str | None = None


def _cor_primaria() -> str:
    global _cor_primaria_cache
    if _cor_primaria_cache is None:
        _cor_primaria_cache = config_manager.obter("cor_destaque") or "#1E6FB3"
    return _cor_primaria_cache


def _cor_primaria_hover() -> str:
    """Gera um tom mais escuro da cor primária."""
    global _cor_hover_cache
    if _cor_hover_cache is not None:
        return _cor_hover_cache
    cor = _cor_primaria()
    try:
        r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
        fator = 0.78
        r, g, b = int(r * fator), int(g * fator), int(b * fator)
        _cor_hover_cache = f"#{r:02x}{g:02x}{b:02x}"
        return _cor_hover_cache
    except (ValueError, IndexError):
        return "#004785"


def _cor_primaria_light() -> str:
    """Gera um tom mais claro da cor primária misturando com branco."""
    global _cor_light_cache
    if _cor_light_cache is not None:
        return _cor_light_cache
    cor = _cor_primaria()
    try:
        r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
        fator_cor = 0.4   # 40% da cor original
        fator_white = 0.6 # 60% de branco
        
        r = int(r * fator_cor + 255 * fator_white)
        g = int(g * fator_cor + 255 * fator_white)
        b = int(b * fator_cor + 255 * fator_white)
        _cor_light_cache = f"#{r:02x}{g:02x}{b:02x}"
        return _cor_light_cache
    except (ValueError, IndexError):
        return "#E8F0FA"


def _cor_primaria_dark_gradient() -> str:
    """Gera um tom da cor primária para gradiente em dark mode (mais saturado/destacado)."""
    global _cor_dark_grad_cache
    if _cor_dark_grad_cache is not None:
        return _cor_dark_grad_cache
    cor = _cor_primaria()
    try:
        r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
        fator_cor = 0.6
        bg = 30 # 0x1E
        r = int(r * fator_cor + bg * (1 - fator_cor))
        g = int(g * fator_cor + bg * (1 - fator_cor))
        b = int(b * fator_cor + bg * (1 - fator_cor))
        _cor_dark_grad_cache = f"#{r:02x}{g:02x}{b:02x}"
        return _cor_dark_grad_cache
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
RADIUS_BUTTON = 12
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
    global _cor_primaria_cache, _cor_hover_cache, _cor_light_cache, _cor_dark_grad_cache
    global COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_BORDER_FOCUS

    _cor_primaria_cache = None
    _cor_hover_cache = None
    _cor_light_cache = None
    _cor_dark_grad_cache = None

    COLOR_PRIMARY = get_color_primary()
    COLOR_PRIMARY_HOVER = get_color_primary_hover()
    COLOR_BORDER_FOCUS = COLOR_PRIMARY


def configure_appearance() -> None:
    """Configurações globais de aparência da aplicação."""
    aparencia = config_manager.obter("aparencia") or "system"
    ctk.set_appearance_mode(aparencia)
    ctk.set_default_color_theme("blue")
    reload_theme()


def configurar_janela_modal(
    master,
    card: ctk.CTkToplevel,
    overlay: ctk.CTkToplevel,
    w: int,
    h: int,
) -> None:
    """Configura e posiciona perfeitamente o overlay escuro e o card do modal.
    
    Calcula as dimensões e coordenadas físicas para centralizar no aplicativo
    com precisão absoluta em qualquer resolução ou escala DPI do Windows.
    """
    root = master.winfo_toplevel()
    try:
        root.update_idletasks()
    except Exception:
        pass

    rx = root.winfo_rootx()
    ry = root.winfo_rooty()
    rw = root.winfo_width()
    rh = root.winfo_height()

    scaling = getattr(root, "_get_window_scaling", lambda: 1.0)()

    # Dimensões físicas que o CustomTkinter gerará para o card
    pw = int(round(w * scaling))
    ph = int(round(h * scaling))

    # Posição física na tela para centralização exata na janela do app
    x = rx + (rw - pw) // 2
    y = ry + (rh - ph) // 2

    # 1. Configuração do Overlay translúcido
    if overlay is not None:
        overlay.withdraw()
        overlay.overrideredirect(True)
        overlay.configure(fg_color="#000000")
        try:
            overlay.attributes("-alpha", 0.60)
        except Exception:
            pass
        ow = int(round(rw / scaling))
        oh = int(round(rh / scaling))
        overlay.geometry(f"{ow}x{oh}+{rx}+{ry}")
        overlay.deiconify()
        overlay.lift()

    # 2. Configuração do Cartão do modal
    if card is not None:
        card.withdraw()
        card.overrideredirect(True)
        card.configure(fg_color=COLOR_SURFACE)
        card.geometry(f"{w}x{h}+{x}+{y}")
        card.deiconify()
        card.lift()


def configurar_autoscroll(scroll_frame: ctk.CTkScrollableFrame) -> None:
    """Oculta automaticamente a barra de rolagem do CTkScrollableFrame de forma otimizada (sem loops de eventos)."""
    timer_attr = "_autoscroll_timer_id"

    def _do_check():
        try:
            if not scroll_frame.winfo_exists():
                return
            setattr(scroll_frame, timer_attr, None)
            
            # Se o próprio scroll_frame estiver oculto (grid_remove), não alterar visibilidade da barra de rolagem
            if not scroll_frame.winfo_ismapped():
                return

            bbox = scroll_frame._parent_canvas.bbox("all")
            if bbox:
                content_height = bbox[3] - bbox[1]
                visible_height = scroll_frame._parent_canvas.winfo_height()
                if content_height > visible_height + 5 and visible_height > 1:
                    if not scroll_frame._scrollbar.grid_info():
                        scroll_frame._scrollbar.grid()
                else:
                    if scroll_frame._scrollbar.grid_info():
                        scroll_frame._scrollbar.grid_remove()
        except Exception:
            pass

    def _agendar_verificacao(event=None):
        try:
            timer_id = getattr(scroll_frame, timer_attr, None)
            if timer_id is not None:
                scroll_frame.after_cancel(timer_id)
            new_timer_id = scroll_frame.after(60, _do_check)
            setattr(scroll_frame, timer_attr, new_timer_id)
        except Exception:
            pass

    try:
        scroll_frame._parent_canvas.bind("<Configure>", _agendar_verificacao, add="+")
        scroll_frame._parent_frame.bind("<Configure>", _agendar_verificacao, add="+")
        _agendar_verificacao()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Ícones Adaptativos (Design System)
# ---------------------------------------------------------------------------

_ICONS_CACHE = {}


def get_icon(name: str, size: tuple[int, int] = (20, 20), light_only: bool = False, dark_only: bool = False) -> ctk.CTkImage:
    """Retorna um CTkImage com suporte a tema claro e escuro a partir dos ativos de app/assets/icons/.
    
    Se light_only=True, retorna sempre o ícone claro/branco (para botões coloridos/toolbar).
    Se dark_only=True, retorna sempre o ícone escuro/grafite.
    Caso contrário, associa {name}_dark.png para Light mode e {name}_light.png para Dark mode.
    """
    key = (name, size, light_only, dark_only)
    if key in _ICONS_CACHE:
        return _ICONS_CACHE[key]

    from PIL import Image
    from utils.resource_path import caminho_recurso

    dark_path = caminho_recurso("assets", "icons", f"{name}_dark.png")
    light_path = caminho_recurso("assets", "icons", f"{name}_light.png")
    standard_path = caminho_recurso("assets", "icons", f"{name}.png")

    if light_only:
        p = light_path if light_path.exists() else (standard_path if standard_path.exists() else dark_path)
        if p.exists():
            img = Image.open(p)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        else:
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    elif dark_only:
        p = dark_path if dark_path.exists() else (standard_path if standard_path.exists() else light_path)
        if p.exists():
            img = Image.open(p)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        else:
            img = Image.new("RGBA", size, (0, 0, 0, 0))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    elif dark_path.exists() and light_path.exists():
        img_dark = Image.open(dark_path)
        img_light = Image.open(light_path)
        ctk_img = ctk.CTkImage(light_image=img_dark, dark_image=img_light, size=size)
    elif standard_path.exists():
        img = Image.open(standard_path)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
    else:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)

    _ICONS_CACHE[key] = ctk_img
    return ctk_img


