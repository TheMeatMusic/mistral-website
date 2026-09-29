"""One-off: download the site's two typefaces from Google Fonts and self-host them.

Run again only to change a family or weight range: py tools/fetch_fonts.py
Writes static/fonts/*.woff2 and site/fonts.css (build.py prepends it to the stylesheet). Self-hosting keeps visitors' IPs away from a third party (Quebec Law 25)
and removes a render-blocking request.
"""
import pathlib, re, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAMILIES = "family=Archivo:wdth,wght@62..125,300..900&family=JetBrains+Mono:wght@400"
KEEP = ("latin", "latin-ext")   # French needs latin-ext for Œ œ and friends
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()

css = get("https://fonts.googleapis.com/css2?" + FAMILIES + "&display=swap").decode()
out = []
for subset, block in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S):
    if subset not in KEEP:
        continue
    family = re.search(r"font-family: '([^']+)'", block).group(1)
    url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
    name = f"{family.lower().replace(' ', '-')}-{subset}.woff2"
    (ROOT / "static/fonts" / name).write_bytes(get(url))
    # the stylesheet is served from assets/, next to assets/fonts/
    out.append(f"/* {family}, {subset} */\n" + block.replace(url, "fonts/" + name))
(ROOT / "site/fonts.css").write_text("\n".join(out) + "\n", encoding="utf-8")
print("fonts:", sorted(p.name for p in (ROOT / "static/fonts").iterdir()))
