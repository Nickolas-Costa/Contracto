"""
Script para geração automatizada da imagem de Social Media Preview (1280x640)
do repositório Contracto no GitHub.

Utiliza a identidade visual oficial do aplicativo, o ícone original em alta
resolução e as curvas matemáticas senoidais do Design System.
"""

import math
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def gerar_social_preview():
    root_dir = Path(__file__).resolve().parent.parent
    icon_src = root_dir / "app" / "assets" / "icons" / "app_icon.png"

    # Salvar cópias destacadas do ícone original nos diretórios de assets
    assets_dir = root_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    shutil.copy(icon_src, assets_dir / "LOGO_OFICIAL_CONTRACTO.png")
    shutil.copy(icon_src, assets_dir / "APP_ICON_ORIGINAL.png")
    shutil.copy(icon_src, root_dir / "app" / "assets" / "icons" / "LOGO_OFICIAL_CONTRACTO.png")

    W, H = 1280, 640
    scale = 2
    w_hd, h_hd = W * scale, H * scale

    # 1. Fundo escuro oficial do tema Dark do Contracto
    bg_color = (20, 22, 28, 255)  # #14161C
    img_hd = Image.new("RGBA", (w_hd, h_hd), bg_color)

    # 2. Curvas senoidais com anti-aliasing do aplicativo
    line_color = (36, 40, 50, 180)       # #242832
    line_accent = (45, 50, 62, 220)      # #2D323E
    cor_destaque = (1, 154, 252, 220)    # #019AFC (Azul ciano da marca)

    num_linhas = 22
    destaque_indices = {5, 12, 17}

    for i in range(num_linhas):
        y_offset = (i - 4) * (h_hd / 14)
        points = []
        steps = 140
        for s in range(steps + 1):
            x = (s / steps) * w_hd
            y = y_offset + (x * 0.28) + math.sin(s * 0.14 + i * 0.22) * (h_hd * 0.05)
            points.append((x, y))

        if i in destaque_indices:
            cor = cor_destaque
            lw = 4
        else:
            cor = line_accent if i % 2 == 0 else line_color
            lw = 2

        line_layer = Image.new("RGBA", (w_hd, h_hd), (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(line_layer)
        ldraw.line(points, fill=cor, width=lw, joint="curve")
        img_hd = Image.alpha_composite(img_hd, line_layer)

    # 3. Brilho radial suave atrás do ícone
    icon_center_y = int(h_hd * 0.36)
    glow_layer = Image.new("RGBA", (w_hd, h_hd), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    cx, cy = w_hd // 2, icon_center_y
    for r in range(260, 0, -10):
        alpha = int(30 * (1 - r / 260))
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(1, 154, 252, alpha))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(35))
    img_hd = Image.alpha_composite(img_hd, glow_layer)

    # 4. Ícone oficial original do aplicativo (tamanho 320x320 px no canvas 2x)
    icon_raw = Image.open(icon_src).convert("RGBA")
    icon_size = 310
    icon_resized = icon_raw.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

    icon_x = (w_hd - icon_size) // 2
    icon_y = icon_center_y - icon_size // 2

    # Sombra suave sob o ícone
    shadow_layer = Image.new("RGBA", (w_hd, h_hd), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)
    sdraw.rounded_rectangle(
        [icon_x + 6, icon_y + 14, icon_x + icon_size + 6, icon_y + icon_size + 14],
        radius=54,
        fill=(0, 0, 0, 150),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(18))
    img_hd = Image.alpha_composite(img_hd, shadow_layer)

    img_hd.paste(icon_resized, (icon_x, icon_y), icon_resized)

    # 5. Tipografia Segoe UI
    font_light = ImageFont.truetype("C:/Windows/Fonts/segoeuil.ttf", size=90)
    font_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", size=90)
    font_badge = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", size=32)
    font_subtitle = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", size=48)

    prefix_text = "Nickolas-Costa/"
    title_text = "Contracto"
    badge_text = "v4.5"

    bbox_p = font_light.getbbox(prefix_text)
    w_p = bbox_p[2] - bbox_p[0]

    bbox_t = font_bold.getbbox(title_text)
    w_t = bbox_t[2] - bbox_t[0]

    badge_pad_x = 22
    badge_pad_y = 7
    bbox_b = font_badge.getbbox(badge_text)
    w_b_text = bbox_b[2] - bbox_b[0]
    h_b_text = bbox_b[3] - bbox_b[1]
    w_b = w_b_text + badge_pad_x * 2
    h_b = h_b_text + badge_pad_y * 2
    badge_gap = 18

    total_title_w = w_p + w_t + badge_gap + w_b
    title_start_x = (w_hd - total_title_w) // 2
    title_y = int(h_hd * 0.64)

    text_layer = Image.new("RGBA", (w_hd, h_hd), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)

    # Prefixo repositório
    tdraw.text((title_start_x, title_y), prefix_text, font=font_light, fill=(156, 163, 175, 255))

    # Nome do aplicativo
    tdraw.text((title_start_x + w_p, title_y), title_text, font=font_bold, fill=(255, 255, 255, 255))

    # Badge de versão v4.5
    badge_x = title_start_x + w_p + w_t + badge_gap
    badge_y = title_y + 18
    tdraw.rounded_rectangle([badge_x, badge_y, badge_x + w_b, badge_y + h_b], radius=16, fill=(1, 154, 252, 230))
    tdraw.text((badge_x + badge_pad_x, badge_y + badge_pad_y - 2), badge_text, font=font_badge, fill=(255, 255, 255, 255))

    # Subtítulo descritivo
    sub_text = "Automação de Declarações Habitacionais & Conversão PDF/A-2b"
    bbox_s = font_subtitle.getbbox(sub_text)
    w_s = bbox_s[2] - bbox_s[0]
    sub_x = (w_hd - w_s) // 2
    sub_y = int(h_hd * 0.78)
    tdraw.text((sub_x, sub_y), sub_text, font=font_subtitle, fill=(160, 174, 192, 255))

    img_hd = Image.alpha_composite(img_hd, text_layer)

    # 6. Downsampling com filtro Lanczos para 1280x640 exatos
    final_img = img_hd.resize((W, H), Image.Resampling.LANCZOS)
    
    out_png = assets_dir / "social_preview.png"
    out_jpg = assets_dir / "social_preview.jpg"
    root_png = root_dir / "social_preview.png"

    final_img.save(out_png, format="PNG", optimize=True)
    final_img.convert("RGB").save(out_jpg, format="JPEG", quality=95)
    final_img.save(root_png, format="PNG", optimize=True)

    print(f"Social Preview gerado com sucesso em: {out_png}")


if __name__ == "__main__":
    gerar_social_preview()
