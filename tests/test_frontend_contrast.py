"""Contraste dos pares realmente usados no CSS, sem dependência adicional."""
from pathlib import Path
import re
import unittest


def luminance(value):
    channels = [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
    return sum(weight*(c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4)
               for weight, c in zip((.2126, .7152, .0722), channels))


class TestFrontendContrast(unittest.TestCase):
    def test_semantic_pairs_both_themes(self):
        css = (Path(__file__).resolve().parent.parent / "frontend/css/tokens.css").read_text(encoding="utf-8")
        palettes = re.findall(r"\{([^{}]+)\}", css)
        base = {}
        for theme, block in zip(("light", "dark"), palettes):
            base.update(dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})", block)))
            pairs = [(fg, bg, 4.5) for fg in ("text", "text-secondary", "success", "error", "primary")
                     for bg in ("bg", "surface", "surface-variant")]
            pairs += [("on-primary", "primary", 4.5), ("on-primary", "primary-hover", 4.5),
                      ("primary", "primary-light", 4.5)]
            pairs += [(fg, bg, 3) for fg in ("focus", "control-border") for bg in ("surface", "bg")]
            for foreground, background, minimum in pairs:
                with self.subTest(theme=theme, foreground=foreground, background=background):
                    values = sorted((luminance(base["--c-"+foreground]), luminance(base["--c-"+background])))
                    self.assertGreaterEqual((values[1]+.05)/(values[0]+.05), minimum)
