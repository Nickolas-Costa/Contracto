"""Gera os PNG/ICO do app a partir de uma proposta em docs/icone/propostas/ (Edge headless renderiza o SVG; Pillow monta o .ico).

Uso: python scripts/gerar_icone.py [S1]   (nome da proposta; padrão S1; requer Microsoft Edge e Pillow)
Também renderiza todas as propostas em PNG (propostas/*.png) para comparação.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ICONES = RAIZ / "app" / "assets" / "icons"
FONTES = RAIZ / "docs" / "icone"  # fora de app/assets para não ir ao pacote
PROPOSTAS = FONTES / "propostas"
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
    nome = sys.argv[1] if len(sys.argv) > 1 else "S1"
    escolhida = PROPOSTAS / f"proposta_{nome}.svg"
    if not escolhida.exists():
        raise SystemExit(f"[ERRO] Proposta inexistente: {escolhida.name}")
    for svg in PROPOSTAS.glob("proposta_*.svg"):
        renderizar(svg, svg.with_suffix(".png"), 512)
    fonte = FONTES / "icone_contracto.svg"
    shutil.copy2(escolhida, fonte)
    # Cabeçalho do app: o mesmo desenho sem o tile (a barra já tem fundo próprio).
    sem_tile = FONTES / "logo_cabecalho.svg"
    sem_tile.write_text(re.sub(r'<rect id="tile"[^>]*/>', "", escolhida.read_text(encoding="utf-8")), encoding="utf-8")
    grande = renderizar(fonte, ICONES / "app_icon.png", 1024)
    grande.resize((512, 512), Image.LANCZOS).save(ICONES / "app_icon.png")
    grande.save(ICONES / "LOGO_OFICIAL_CONTRACTO.png")
    grande.save(ICONES / "app_icon.ico", sizes=[(t, t) for t in (16, 24, 32, 48, 64, 128, 256)])
    cabecalho = renderizar(sem_tile, RAIZ / "frontend" / "assets" / "logo.png", 512)
    cabecalho.resize((192, 192), Image.LANCZOS).save(RAIZ / "frontend" / "assets" / "logo.png")
    shutil.copy2(ICONES / "LOGO_OFICIAL_CONTRACTO.png", RAIZ / "assets" / "LOGO_OFICIAL_CONTRACTO.png")
    print(f"Ícone '{nome}' aplicado em app/assets/icons/, frontend/assets/logo.png e assets/.")


if __name__ == "__main__":
    main()
