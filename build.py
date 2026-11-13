"""Build the site into dist/.

    py build.py            check the copy, build, check the result
    py build.py --serve    same, then preview at http://localhost:8000 in Edge (Ctrl+C stops)

Inputs:  content/*.json (copy), site/ (template, styles, script), static/ (fonts, images)
Output:  dist/index.html (FR), dist/en/index.html (EN), dist/assets/..., sitemap, robots, 404.
Any rule in check.py that fails stops the build, locally and in the publish pipeline.
"""
import hashlib, json, pathlib, shutil, subprocess, sys
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import check

ROOT = pathlib.Path(__file__).resolve().parent
DIST = ROOT / "dist"


def fingerprint(name, data):
    """site.css -> site.3f2a9c1e.css, so a changed file is never served stale from a cache."""
    stem, ext = name.rsplit(".", 1)
    return f"{stem}.{hashlib.sha256(data.encode()).hexdigest()[:8]}.{ext}"


def clear(folder):
    """Empty dist/. OneDrive marks folders read-only (copied into dist/ by copytree) and Windows
    will not delete a read-only folder, so clear the flag and retry that one entry."""
    import os, stat

    def force(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if folder.exists():
        shutil.rmtree(folder, onexc=force)


def fail(title, errors):
    print(f"\n{title}:\n  " + "\n  ".join(errors))
    sys.exit(1)


def main():
    content, site = check.load()
    errors = check.check_content(content, site)
    if errors:
        fail("Copy rules failed (content/*.json)", errors)

    clear(DIST)
    shutil.copytree(ROOT / "static", DIST / "assets")

    css = (ROOT / "site/fonts.css").read_text(encoding="utf-8") + "\n" + (ROOT / "site/styles.css").read_text(encoding="utf-8")
    js = (ROOT / "site/main.js").read_text(encoding="utf-8")
    css_name, js_name = fingerprint("site.css", css), fingerprint("site.js", js)
    (DIST / "assets" / css_name).write_text(css, encoding="utf-8")
    (DIST / "assets" / js_name).write_text(js, encoding="utf-8")

    env = Environment(loader=FileSystemLoader(ROOT / "site"), autoescape=True, undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True)
    page = env.get_template("page.html")
    base = f"https://{site['domain']}/"
    urls = {"fr": base, "en": base + "en/"}
    for lang, root, out in (("fr", "", DIST / "index.html"), ("en", "../", DIST / "en/index.html")):
        alt = "en" if lang == "fr" else "fr"
        srcset = ", ".join(f"{root}assets/img/hero-{w}.webp {w}w" for w in (1280, 1920, 2880))
        ld = {
            "@context": "https://schema.org", "@type": "Electrician",
            "name": site[f"trade_name_{lang}"], "legalName": site["legal_name_fr"],
            "url": urls[lang], "email": site["email"], "telephone": site["phone_tel"], "logo": base + "assets/img/apple-touch-icon.png",
            "image": base + "assets/img/og.jpg",
            "address": {"@type": "PostalAddress", "addressLocality": "Montréal", "addressRegion": "QC", "addressCountry": "CA"},
            "areaServed": "Québec",
        }
        html = page.render(
            t=content[lang], s=site, lang=lang, root=root, css=css_name, js=js_name,
            url=urls[lang], url_fr=urls["fr"], url_en=urls["en"],
            alt_lang=alt, alt_href="en/" if lang == "fr" else "../",
            hero_srcset=srcset, ld_json=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"),
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n", encoding="utf-8")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls.values()) + "</urlset>\n", encoding="utf-8")
    (DIST / "404.html").write_text(
        '<!doctype html><html lang="fr-CA"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        f'<title>Page introuvable · {site["trade_name_fr"]}</title>'
        '<body style="background:#0c0d14;color:#e8e4dc;font:16px/1.6 system-ui;padding:48px 24px">'
        '<p>Cette page n\'existe pas. / This page does not exist.</p>'
        '<p><a style="color:#e8e4dc" href="/">Accueil</a> · <a style="color:#e8e4dc" href="/en/">Home</a></p>', encoding="utf-8")
    (DIST / "CNAME").write_text(site["domain"] + "\n", encoding="utf-8")

    errors = check.check_dist(DIST, site["domain"])
    if errors:
        fail("Built site failed its checks (dist/)", errors)
    size = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file()) // 1024
    print(f"built dist/  ·  FR + EN  ·  {size} KB  ·  all rules pass")

    if "--serve" in sys.argv:
        # a real server, not file://, so folder links like en/ resolve to their index.html
        import functools, http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler)
        subprocess.run(["cmd", "/c", "start", "msedge", "http://localhost:8000/"], check=False)
        print("previewing at http://localhost:8000/  (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
