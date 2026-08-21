"""
Script para processar e converter os ativos vetoriais (SVG) e loaders (GIF)
de app/assets/new para as pastas oficiais app/assets/icons e app/assets/loaders.
Gera versões claras (dark icons para light mode) e versões escuras (light/white icons para dark mode).
"""

import os
import shutil
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ASSETS_NEW = ROOT / "app" / "assets" / "new"
ICONS_DIR = ROOT / "app" / "assets" / "icons"
LOADERS_DIR = ROOT / "app" / "assets" / "loaders"

ICONS_DIR.mkdir(parents=True, exist_ok=True)
LOADERS_DIR.mkdir(parents=True, exist_ok=True)

# Mapeamento semântico dos SVGs para nomes padronizados
SVG_MAP = {
    "system-outline-63-home-morph-select.svg": "home",
    "system-outline-1388-grid-bento.svg": "profiles",
    "system-outline-409-wrench.svg": "settings",
    "system-outline-364-calendar-dots.svg": "calendar",
    "system-outline-475-lifebuoy.svg": "help",
    "system-outline-18-location-pin.svg": "location",
    "system-outline-360-person-accessibility.svg": "person",
    "system-outline-372-figures.svg": "participants",
    "system-outline-56-file-text.svg": "document",
    "system-outline-362-article.svg": "form",
    "system-outline-3971-clipboard-text.svg": "contract",
    "system-outline-120-folder-morph-select.svg": "folder",
    "system-outline-185-trash-bin.svg": "trash",
    "system-outline-187-briefcase.svg": "briefcase",
    "system-outline-19-magnifier.svg": "search",
    "system-outline-1140-warning-triangle.svg": "warning",
    "system-outline-260-warning-circle.svg": "alert_circle",
    "system-outline-1103-confetti.svg": "success",
    "system-outline-400-bookmark.svg": "save",
    "system-outline-4014-calculator-simple.svg": "calculator",
    "system-outline-4094-arrow-trending-up.svg": "advance",
    "wired-outline-3466-turn-left-sign.svg": "back",
    "system-outline-27-globe.svg": "globe",
    "system-outline-363-ratio.svg": "ratio",
    "system-outline-4092-book.svg": "book",
    "system-outline-1384-grid-array.svg": "grid_array",
    "system-outline-1387-grid-columns.svg": "grid_columns",
    "system-outline-365-grid-sections.svg": "grid_sections",
    "system-outline-368-anchor.svg": "anchor",
    "system-outline-4092-book-morph-book.svg": "book_morph",
}

GIF_LOADERS = [
    ("system-outline-4017-spinner-horizontal-dashed-circle-loop-expand.gif", "spinner_expand.gif"),
    ("system-outline-4018-spinner-three-dots-loop-spin.gif", "spinner_dots_spin.gif"),
    ("system-outline-4021-spinner-circle-loop-snake.gif", "spinner_snake.gif"),
    ("system-outline-4018-spinner-three-dots-loop-juggle.gif", "spinner_dots_juggle.gif"),
    ("system-outline-4021-spinner-circle-loop-spiral.gif", "spinner_spiral.gif"),
    ("system-outline-4035-spinner-turbine-hover-rotation.gif", "spinner_turbine.gif"),
    ("system-outline-4018-spinner-three-dots-loop-queue.gif", "spinner_dots_queue.gif"),
    ("system-outline-4022-spinner-half-circles-hover-pinch.gif", "spinner_half_circles.gif"),
    ("system-outline-4017-spinner-horizontal-dashed-circle-loop-transparency.gif", "spinner_transparency.gif"),
    ("system-outline-4018-spinner-three-dots-loop-line.gif", "spinner_dots_line.gif"),
]


def render_svg_to_png(svg_path: Path, output_base_name: str, target_size: int = 128):
    """Renderiza um SVG em duas variantes: Dark icon (para Light Mode) e Light/White icon (para Dark Mode)."""
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Variante Branca (para fundos escuros / Dark Mode)
    # Garante que as cores de preenchimento e traço fiquem brancas
    svg_white = svg_content.replace('stroke="#121331"', 'stroke="#FFFFFF"').replace('fill="#121331"', 'fill="#FFFFFF"')
    if 'stroke="' not in svg_white and 'fill="' not in svg_white:
        svg_white = svg_white.replace('<svg ', '<svg fill="#FFFFFF" stroke="#FFFFFF" ')

    # Variante Escura (para fundos claros / Light Mode: #334155 / grafite moderno)
    svg_dark = svg_content.replace('stroke="#fff"', 'stroke="#334155"').replace('fill="#fff"', 'fill="#334155"')
    svg_dark = svg_dark.replace('stroke="#FFFFFF"', 'stroke="#334155"').replace('fill="#FFFFFF"', 'fill="#334155"')
    svg_dark = svg_dark.replace('stroke="#121331"', 'stroke="#334155"').replace('fill="#121331"', 'fill="#334155"')

    # Renderizar com PyMuPDF
    doc_white = fitz.open(stream=svg_white.encode("utf-8"), filetype="svg")
    pix_white = doc_white[0].get_pixmap(dpi=300, alpha=True)
    img_white = Image.frombytes("RGBA", [pix_white.width, pix_white.height], pix_white.samples)
    img_white = img_white.resize((target_size, target_size), Image.Resampling.LANCZOS)
    img_white.save(ICONS_DIR / f"{output_base_name}_light.png")  # Usado no Dark Mode

    doc_dark = fitz.open(stream=svg_dark.encode("utf-8"), filetype="svg")
    pix_dark = doc_dark[0].get_pixmap(dpi=300, alpha=True)
    img_dark = Image.frombytes("RGBA", [pix_dark.width, pix_dark.height], pix_dark.samples)
    img_dark = img_dark.resize((target_size, target_size), Image.Resampling.LANCZOS)
    img_dark.save(ICONS_DIR / f"{output_base_name}_dark.png")  # Usado no Light Mode

    # Salva também a versão padrão (dark para light mode)
    img_dark.save(ICONS_DIR / f"{output_base_name}.png")


def main():
    print("Processando SVGs...")
    for svg_file, base_name in SVG_MAP.items():
        svg_path = ASSETS_NEW / svg_file
        if svg_path.exists():
            render_svg_to_png(svg_path, base_name)
            print(f"  [OK] {svg_file} -> {base_name}.png / {base_name}_light.png / {base_name}_dark.png")
        else:
            print(f"  [AVISO] {svg_file} não encontrado.")

    print("\nProcessando Loaders GIF...")
    for src_gif, dst_name in GIF_LOADERS:
        src_path = ASSETS_NEW / src_gif
        if src_path.exists():
            shutil.copy2(src_path, LOADERS_DIR / dst_name)
            print(f"  [OK] {src_gif} -> {dst_name}")
        else:
            print(f"  [AVISO] {src_gif} não encontrado.")

    print("\nAtivos processados com sucesso!")


if __name__ == "__main__":
    main()
