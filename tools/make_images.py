"""Derive every web image from the originals in source/. Run after replacing one:

    py tools/make_images.py

source/hero.webp     the hero photograph (landscape, at least 2880 px wide)
source/mark.png      the three-band mark, version for DARK grounds
source/wordmark.png  MISTRAL wordmark, version for DARK grounds
Writes static/img/. Needs Pillow (pip install pillow). Outputs are committed, so the
publish pipeline never needs Pillow.
"""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "source", ROOT / "static/img"
INK = (12, 13, 20)
OUT.mkdir(parents=True, exist_ok=True)

hero = Image.open(SRC / "hero.webp").convert("RGB")
for w in (1280, 1920, 2880):
    hero.resize((w, round(hero.height * w / hero.width)), Image.LANCZOS).save(OUT / f"hero-{w}.webp", quality=74, method=6)

mark = Image.open(SRC / "mark.png").convert("RGBA")
word = Image.open(SRC / "wordmark.png").convert("RGBA")
mark.resize((52, round(mark.height * 52 / mark.width)), Image.LANCZOS).save(OUT / "mark.png", optimize=True)
word.resize((280, round(word.height * 280 / word.width)), Image.LANCZOS).save(OUT / "wordmark.png", optimize=True)

def icon(size, pad):
    im = Image.new("RGBA", (size, size), INK + (255,))
    m = mark.copy(); m.thumbnail((size - 2 * pad, size - 2 * pad), Image.LANCZOS)
    im.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return im
icon(32, 3).save(OUT / "favicon-32.png", optimize=True)
icon(180, 28).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)

# link preview (Facebook, LinkedIn, iMessage): photo on the right, ink and logo on the left
og = Image.new("RGB", (1200, 630), INK)
ph = hero.copy(); ph = ph.resize((round(ph.width * 630 / ph.height), 630), Image.LANCZOS)
x0 = int(ph.width * 0.62) - 320
og.paste(ph.crop((x0, 0, x0 + 640, 630)), (560, 0))
fade = Image.new("L", (300, 630))                     # ink at the photo's left edge, clear by 300 px
fade.putdata([round(255 * (1 - x / 299)) for y in range(630) for x in range(300)])
og.paste(Image.new("RGB", (300, 630), INK), (560, 0), fade)
m = mark.copy(); m.thumbnail((88, 88), Image.LANCZOS); og.paste(m, (72, 250), m)
w = word.copy(); w.thumbnail((300, 60), Image.LANCZOS); og.paste(w, (178, 250 + (m.height - w.height) // 2), w)
og.save(OUT / "og.jpg", quality=84, optimize=True)

for p in sorted(OUT.iterdir()):
    print(f"{p.name:22} {p.stat().st_size // 1024:>5} KB")
