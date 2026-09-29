# mistralelectric.com

The Mistral Électrique website. One page, in French (`/`) and English (`/en/`).

## Change the words

All copy lives in three files. You never need to open the HTML to change a sentence.

| File | What is in it |
|---|---|
| `content/fr.json` | every French sentence on the page |
| `content/en.json` | the same keys, in English |
| `content/site.json` | facts shared by both: email, NEQ, RBQ, legal and trade names, domain |

Edit the text between the quotes, keep the quotes and commas. Both language files must have
the same keys; the build tells you if one is missing.

**Adding the RBQ licence number:** put it in `site.json` under `"rbq"`. It then appears in the
ownership card and the footer automatically, and the copy is allowed to mention the licence.

## Preview

```
py build.py --serve
```

Builds the site, opens it in Edge at http://localhost:8000, and serves it until you press Ctrl+C.
First time on a new computer: `py -m pip install -r requirements.txt`.

## Publish

Push to `main`. GitHub builds and publishes in about a minute
(Actions tab, "Publish site"). If any rule fails, nothing is published and the live site
stays as it was.

## The rules the build enforces (`check.py`)

A failed rule stops the build locally and the publish on GitHub. Each one exists because it
was broken once.

- French and English have exactly the same keys, no empty text
- no em or en dashes
- no superlatives: "le seul", "the only", "leader", "meilleur", "best", "#1"
- never "Mohawk" in client copy; "autochtone" / "Indigenous"
- no number in the copy unless it is a fact recorded in `site.json` (no invented stats)
- no licence claim until `site.json` has an RBQ number
- Indigenous ownership stated in the hero tag and the ownership section, in both languages
- every link, image and font the pages point to exists; no requests to other websites;
  no single file over 400 KB

If a rule is wrong, change it in `check.py` with the reason. Don't work around it in the copy.

## Change the design

| File | What |
|---|---|
| `site/page.html` | the page structure (one template, both languages) |
| `site/styles.css` | colours, type, spacing. The palette comes from the logo; the rules at the top are decisions, not taste |
| `site/main.js` | the logo intro, the phone menu, the sticky bar |

## Change an image

Replace the original in `source/` (hero photo, mark, wordmark), then:

```
py tools/make_images.py
```

It regenerates every size in `static/img/`: three hero widths, logo files, favicons and the
link-preview image (`og.jpg`, what LinkedIn and iMessage show). Needs Pillow.

The hero is framed for this layout: text on the left over solid ink, the photo in the right
two thirds. A new photo needs its subject on the right, and the headline contrast re-checked.

## Layout

```
content/     the words (edit these)
site/        template, stylesheet, script
static/      fonts and images, copied as-is to dist/assets/
source/      original images, input to tools/make_images.py
tools/       one-off helpers: make_images.py, fetch_fonts.py
build.py     content + site + static -> dist/
check.py     the rules
dist/        the built site (not committed)
_archive/    earlier builds and working files (not committed)
```

## Domain

Hosted on GitHub Pages (repo settings, Pages, custom domain `mistralelectric.com`, HTTPS on).
DNS is at Network Solutions. The website needs:

| Type | Host | Value |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | themeatmusic.github.io |

The MX record (`smtp.google.com`) and the Google verification TXT record are for email.
Never touch them when changing website records.
