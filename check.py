"""The site's rules, as code. build.py runs every check; a failure stops the build and the publish.

Each rule is here because it was broken once. If a rule is wrong, change it here, with a reason,
never by working around it in the copy.
"""
import json, pathlib, re
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
LANGS = ("fr", "en")

# Claims the company cannot back (yet), or has been told never to make.
BANNED = {
    r"\ble seul\b|\bla seule\b|\bthe only\b|\bonly indigenous\b": "superlative claim: other Indigenous electrical firms exist",
    r"\bmohawk\b": "client copy says autochtone / Indigenous, never Mohawk",
    r"\bleader\b|\bnuméro 1\b|#1|\bmeilleur|\bbest\b": "unprovable superlative",
    r"lorem|ipsum|\bTODO\b|\bXXX\b|\[X\]": "placeholder left in the copy",
}
DASHES = "—–"   # em and en dash read as machine-written; use commas or full stops


def load():
    content = {lang: json.loads((ROOT / f"content/{lang}.json").read_text(encoding="utf-8")) for lang in LANGS}
    site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
    return content, site


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, node


def _shape(node):
    if isinstance(node, dict):
        return {k: _shape(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_shape(v) for v in node]
    return type(node).__name__


def check_content(content, site):
    errors = []
    # 1. both languages carry exactly the same keys and list lengths
    if _shape(content["fr"]) != _shape(content["en"]):
        fr = {p for p, _ in _walk(content["fr"])}
        en = {p for p, _ in _walk(content["en"])}
        for p in sorted(fr ^ en):
            errors.append(f"{p}: present in {'fr' if p in fr else 'en'} only")
    allowed_numbers = {n for v in site.values() if isinstance(v, str) for n in re.findall(r"\d+", v)}
    for lang in LANGS:
        for path, value in _walk(content[lang]):
            where = f"{lang}.json {path}"
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}: empty or not text")
                continue
            if any(d in value for d in DASHES):
                errors.append(f"{where}: em/en dash, use a comma or a full stop")
            for pattern, why in BANNED.items():
                if re.search(pattern, value, re.I):
                    errors.append(f"{where}: {why}: {value!r}")
            # 2. no number reaches the page unless it is a fact recorded in site.json
            for n in re.findall(r"\d+", value):
                if n not in allowed_numbers:
                    errors.append(f"{where}: number {n} has no source; add the fact to site.json first")
            # 3. no licence claim until the licence number exists
            if not site.get("rbq") and re.search(r"\bRBQ\b|licenci|licensed", value, re.I):
                errors.append(f"{where}: licence mentioned but site.json has no RBQ number")
    # 4. Indigenous ownership must be stated, plainly, in both languages
    for lang, word in (("fr", "autochtone"), ("en", "Indigenous")):
        for key in ("hero.tag", "ownership.statement"):
            node = content[lang]
            for part in key.split("."):
                node = node.get(part, {})
            if not isinstance(node, str) or word.lower() not in node.lower():
                errors.append(f"{lang}.json {key}: must state Indigenous ownership ('{word}')")
    return errors


class _Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])
        for part in (a.get("srcset") or "").split(","):
            if part.strip():
                self.refs.append(part.split()[0])


def check_dist(dist, domain):
    errors = []
    pages = sorted(dist.rglob("*.html"))
    if not pages:
        return ["dist: no pages were built"]
    for page in pages:
        p = _Refs()
        p.feed(page.read_text(encoding="utf-8"))
        rel = page.relative_to(dist)
        for ref in p.refs:
            if ref.startswith(("mailto:", "tel:")):
                continue
            if ref.startswith("#"):
                if ref != "#" and ref[1:] not in p.ids:
                    errors.append(f"{rel}: link {ref} has no target")
                continue
            if re.match(rf"https://(www\.)?{re.escape(domain)}/", ref):
                continue   # canonical and hreflang links to our own pages
            if re.match(r"https?://", ref):
                errors.append(f"{rel}: external request {ref} (self-host it)")
                continue
            path = ref.split("#")[0]
            target = (dist / path.lstrip("/")) if path.startswith("/") else (page.parent / path).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{rel}: missing file {ref}")
    # files a stylesheet points at (fonts): the HTML check cannot see these
    for css in dist.rglob("*.css"):
        for ref in re.findall(r"url\(['\"]?([^'\")]+)", css.read_text(encoding="utf-8")):
            if not ref.startswith("data:") and not (css.parent / ref).resolve().exists():
                errors.append(f"{css.relative_to(dist)}: missing file {ref}")
    for f in dist.rglob("*"):
        if f.is_file() and f.stat().st_size > 400 * 1024:
            errors.append(f"{f.relative_to(dist)}: {f.stat().st_size // 1024} KB, keep single files under 400 KB")
    return errors


if __name__ == "__main__":
    import sys
    content, site = load()
    errs = check_content(content, site)
    dist = ROOT / "dist"
    if dist.exists():
        errs += check_dist(dist, site["domain"])
    print("\n".join(errs) if errs else "check: all rules pass")
    sys.exit(1 if errs else 0)
