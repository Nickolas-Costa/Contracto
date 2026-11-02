"""Gera os PNG/ICO do app a partir de app/assets/icons/svg/ (Edge headless renderiza o SVG; Pillow monta o .ico).

Uso: python scripts/gerar_icone.py   (requer Microsoft Edge e Pillow)
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
SVG = RAIZ / "app" / "assets" / "icons" / "svg"
ICONES = RAIZ / "app" / "assets" / "icons"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def renderizar(svg: Path, destino: Path, lado: int) -> Image.Image:
    # Página com o SVG em tamanho fixo e fundo transparente: o Edge salva o PNG com alfa.
    with tempfile.TemporaryDirectory() as pasta:
        html = Path(pasta, "i.html")
        html.write_text(f'<body style="margin:0;background:transparent"><img src="{svg.as_uri()}" width="{lado}" height="{lado}" style="display:block">', encoding="utf-8")
        subprocess.run([str(EDGE), "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--default-background-color=00000000", f"--window-size={lado},{lado}",
                        f"--screenshot={destino}", html.as_uri()], check=True, capture_output=True)
    return Image.open(destino).convert("RGBA")


def main() -> None:
    if not EDGE.exists():
        raise SystemExit("[ERRO] Microsoft Edge não encontrado.")
    grande = renderizar(SVG / "icone_contracto.svg", ICONES / "app_icon.png", 1024)
    grande.resize((512, 512), Image.LANCZOS).save(ICONES / "app_icon.png")
    grande.save(ICONES / "LOGO_OFICIAL_CONTRACTO.png")
    tamanhos = [16, 24, 32, 48, 64, 128, 256]
    grande.save(ICONES / "app_icon.ico", sizes=[(t, t) for t in tamanhos])
    cabecalho = renderizar(SVG / "logo_cabecalho.svg", RAIZ / "frontend" / "assets" / "logo.png", 512)
    cabecalho.resize((192, 192), Image.LANCZOS).save(RAIZ / "frontend" / "assets" / "logo.png")
    print("Ícones gerados em app/assets/icons/ e frontend/assets/logo.png")


if __name__ == "__main__":
    main()
