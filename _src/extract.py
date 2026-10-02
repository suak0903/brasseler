#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrahiert aus den rohen Divi-Seiten (raw/) je Seite Kopfdaten und die Inhaltsblöcke in Dokumentreihenfolge:
Überschriften, Absätze, Listen, Bilder (Icons markiert), Videos (Hintergrund oder Klick), Buttons, Zitate.
Dazu Sprache, Datum (Yoast-JSON-LD) und die Sprachpartner. Die Bestandsseite hat kein hreflang und ihr
Sprachumschalter führt immer auf die Startseite der anderen Sprache (Befund 02.10.2026), deshalb werden die
Paare hier zugeordnet: gleiches Bild, gleiches Änderungsdatum, Nachbarschaft in der Sitemap, Slug-Ähnlichkeit.
Ergebnis: data.json. Autor: Marketing Operations (Vega), 02.10.2026"""
import re, os, sys, json, html, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw")
BASE = "https://www.brasseler.de"
urls = json.load(open(os.path.join(HERE, "urls.json"), encoding="utf-8"))
sitemap_pos = {}
try:
    import urllib.request
    for sm in ("page", "post", "timeline-eintrag"):
        p = os.path.join(HERE, f"sitemap-{sm}.xml")
        if not os.path.exists(p):
            req = urllib.request.Request(f"{BASE}/{sm}-sitemap.xml", headers={"User-Agent": "Mozilla/5.0"})
            open(p, "w", encoding="utf-8").write(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
        for i, u in enumerate(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", open(p, encoding="utf-8").read())):
            sitemap_pos[re.sub(r"^https://brasselerhomepageprod\.azurewebsites\.net", BASE, u)] = (sm, i)
except Exception as e:
    print("Sitemap-Reihenfolge nicht verfügbar:", e)

def text(frag):
    frag = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", frag)
    frag = re.sub(r"(?is)<br\s*/?>", "\n", frag)
    frag = re.sub(r"(?s)<[^>]+>", "", frag)
    frag = html.unescape(frag).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", frag).strip()

def inline(frag):
    frag = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", frag)
    frag = re.sub(r"(?is)<br\s*/?>", "\n", frag)
    frag = re.sub(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', lambda m: "[%s](%s)" % (text(m.group(2)), html.unescape(m.group(1))), frag)
    frag = re.sub(r"(?is)<(strong|b)>(.*?)</\1>", lambda m: "**%s**" % text(m.group(2)), frag)
    frag = re.sub(r"(?s)<[^>]+>", "", frag)
    frag = html.unescape(frag).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", frag).strip()

def bild_url(src):
    src = html.unescape(src)
    if src.startswith("//"): src = "https:" + src
    if src.startswith("/"): src = BASE + src
    return re.sub(r"-\d{2,4}x\d{2,4}(?=\.(jpg|jpeg|png|webp|gif))", "", src)

BLOCK = re.compile(r"(?is)<(h[1-6])[^>]*>(.*?)</\1>|<p(?:\s[^>]*)?>(.*?)</p>|<(ul|ol)[^>]*>(.*?)</\4>|<img\s[^>]*>|<video\b.*?</video>|<iframe\s[^>]*>|<blockquote[^>]*>(.*?)</blockquote>|<table\b.*?</table>|<zahl>(.*?)</zahl>")

def knopf(m):
    tag = m.group(0); href = re.search(r'href="([^"]+)"', tag)
    return '<p data-button="%s">%s</p>' % (html.escape(html.unescape(href.group(1)), quote=True) if href else "#", m.group(1))

def zaehler(body):
    """Kennzahlen-Kacheln (Divi-Zähler: counter-number, counter-title, counter-text) als eigene Blöcke markieren
    (Befund Faber F1, 02.10.2026). Fehlt die Zahl im Markup (animierter Zähler), kommt sie aus dem Satz."""
    muster = r'(?is)<div[^>]+class="[^"]*\bcounter-(number|title|text)\b[^"]*"[^>]*>(.*?)</div>'
    teile = list(re.finditer(muster, body))
    if not teile: return body
    kacheln, akt = [], {}
    for m in teile:
        art, t = m.group(1), text(m.group(2))
        if art == "number": akt = {"zahl": t}
        elif art == "title": akt["einheit"] = t
        else: akt["satz"] = t; kacheln.append(akt); akt = {}
    tags = []
    for k in kacheln:
        zahl = k.get("zahl", "")
        if not zahl:
            z = re.search(r"\d[\d.,]*", k.get("satz", "")); zahl = z.group(0) if z else ""
        tags.append("<zahl>%s|%s|%s</zahl>" % (zahl, k.get("einheit", ""), k.get("satz", "")))
    start = teile[0].start()
    return body[:start] + "".join(tags) + re.sub(muster, " ", body[start:])

def bloecke(body):
    out = []
    body = re.sub(r'(?is)<a\s[^>]*class="[^"]*\bet_pb_button\b[^"]*"[^>]*>(.*?)</a>', knopf, body)
    body = zaehler(body)
    for m in BLOCK.finditer(body):
        s = m.group(0); davor = body[max(0, m.start() - 400):m.start()]
        if s.lower().startswith("<table"):
            zeilen = [[inline(z) for z in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)] for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", s)]
            zeilen = [[c for c in z] for z in zeilen if any(c.strip() for c in z)]
            if zeilen: out.append({"t": "tabelle", "zeilen": zeilen})
            continue
        if m.group(7) is not None:
            zahl, einheit, satz = (m.group(7).split("|") + ["", "", ""])[:3]
            if satz or zahl: out.append({"t": "zahl", "zahl": zahl, "einheit": einheit, "x": (zahl + " " + einheit + " " + satz).strip()})
            continue
        if m.group(1):
            t = text(m.group(2))
            if t: out.append({"t": m.group(1), "x": t})
        elif s.lower().startswith("<p"):
            if 'data-button="' in s:
                out.append({"t": "button", "x": text(m.group(3)), "href": html.unescape(re.search(r'data-button="([^"]+)"', s).group(1))})
            else:
                t = inline(m.group(3))
                if t and len(t) > 1: out.append({"t": "p", "x": t})
        elif m.group(4):
            items = [inline(i) for i in re.findall(r"(?is)<li[^>]*>(.*?)</li>", m.group(5))]
            items = [i for i in items if i]
            if items: out.append({"t": m.group(4), "items": items})
        elif s.lower().startswith("<img"):
            src = re.search(r'\s(?:data-src|src)="([^"]+)"', s); alt = re.search(r'\salt="([^"]*)"', s)
            if src and not re.search(r"/logo[^/]*\.svg|data:image|gravatar|lepopup|et-core", src.group(1)):
                b = {"t": "img", "src": bild_url(src.group(1)), "alt": html.unescape(alt.group(1)) if alt else ""}
                if "et_pb_main_blurb_image" in davor or "et_pb_blurb" in davor[-200:]: b["icon"] = True
                w = re.search(r'\swidth="(\d+)"', s); h = re.search(r'\sheight="(\d+)"', s)
                if w and h: b["w"], b["h"] = int(w.group(1)), int(h.group(1))
                out.append(b)
        elif s.lower().startswith("<video"):
            srcs = re.findall(r'(?:src)="([^"]+\.(?:mp4|webm))"', s)
            poster = re.search(r'poster="([^"]+)"', s)
            if srcs: out.append({"t": "video", "src": [bild_url(x) for x in dict.fromkeys(srcs)], "bg": "section_video_bg" in davor or "et_pb_section_video" in davor, "poster": bild_url(poster.group(1)) if poster else ""})
        elif s.lower().startswith("<iframe"):
            src = re.search(r'\s(?:data-src|src)="([^"]+)"', s)
            if src and not re.search(r"usercentrics|googletagmanager|about:blank", src.group(1)): out.append({"t": "iframe", "src": html.unescape(src.group(1))})
        elif m.group(6):
            out.append({"t": "zitat", "x": text(m.group(6))})
    return out

daten = []
for u, info in sorted(urls.items()):
    doc = open(os.path.join(RAW, info["datei"]), encoding="utf-8").read()
    kopf = doc.split("<body", 1)[0]
    lang = (re.search(r'<html[^>]+lang="([a-z]{2})', doc) or [None, "de"])[1]
    titel = text((re.search(r"<title>(.*?)</title>", kopf, re.S) or [None, ""])[1])
    desc = html.unescape((re.search(r'name="description" content="([^"]*)"', kopf) or [None, ""])[1])
    og = (re.search(r'property="og:image" content="([^"]*)"', kopf) or [None, ""])[1]
    ld = re.search(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', kopf, re.S)
    pub = mod = ""
    if ld:
        pub = (re.search(r'"datePublished":"([^"]+)"', ld.group(1)) or [None, ""])[1]
        mod = (re.search(r'"dateModified":"([^"]+)"', ld.group(1)) or [None, ""])[1]
    if not mod: mod = (re.search(r'property="article:modified_time" content="([^"]*)"', kopf) or [None, ""])[1]
    start = doc.find('id="et-boc"')
    if start < 0: start = doc.find("et_pb_section")
    if start < 0: start = doc.find('class="entry-content')
    body = doc[start:] if start >= 0 else doc
    ende = re.search(r'<footer|<div[^>]+id="footer|class="et-l et-l--footer"', body)
    if ende: body = body[:ende.start()]
    # Chronik-Seiten (anderes Template) tragen Kopfleiste, Menü und Suchfeld innerhalb des Inhaltsbereichs
    # (Befund Faber F1, 02.10.2026): Header, Navigation und Formulare vor dem Block-Scan entfernen.
    body = re.sub(r"(?is)<header\b.*?</header>|<nav\b.*?</nav>|<form\b.*?</form>|<div[^>]+id=\"et-secondary-menu\".*?</div>", " ", body)
    bl = bloecke(body)
    # Menülisten, die trotzdem durchrutschen: Listen, deren Einträge nur Links auf die Bestandsseite sind
    bl = [b for b in bl if not (b["t"] in ("ul", "ol") and all(re.fullmatch(r"(\s*\[[^\]]+\]\(https://www\.brasseler\.de/(?!uploads/)[^)]*\)\s*)+", i) for i in b["items"]))]
    bl = [b for b in bl if not (b["t"] == "p" and b["x"].strip() in ("Wonach suchen Sie?", "What are you searching for?"))]
    h1 = next((b["x"] for b in bl if b["t"] == "h1"), "")
    woerter = sum(len(b.get("x", "").split()) for b in bl) + sum(len(" ".join(b.get("items", [])).split()) for b in bl) + sum(len(" ".join(c for z in b.get("zeilen", []) for c in z).split()) for b in bl)
    pfad = u.replace(BASE, "")
    daten.append({"url": u, "pfad": pfad, "typ": info["sitemap"], "lang": lang, "titel": titel, "desc": desc, "h1": h1,
                  "og": bild_url(og) if og else "", "modified": mod[:10], "published": pub[:10], "pos": sitemap_pos.get(u, ("", -1))[1],
                  "woerter": woerter, "bilder": [b["src"] for b in bl if b["t"] == "img"], "bloecke": bl})

# Sprachpartner und Duplikate (paare.py)
import paare
daten = paare.zuordnen(daten)
json.dump(daten, open(os.path.join(HERE, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(len(daten), "Seiten;", dict(collections.Counter(d["typ"] + "/" + d["lang"] for d in daten)))
print("Paare:", sum(1 for d in daten if d["partner"] and d["lang"]=="de"), "| ohne Partner:", [d["pfad"] for d in daten if not d["partner"]][:20])
print("Heuristische Paare (Score, Grund):"); [print("   ", d["partner_score"], d["partner_grund"], d["pfad"][:50], "<->", d["partner"][:50]) for d in daten if d["lang"]=="de" and d["partner"] and d["partner_grund"]!=["fest"]]
print("unter 60 Wörtern:", [(d["pfad"], d["woerter"]) for d in daten if d["woerter"] < 60])
print("Bilder gesamt:", len({b for d in daten for b in d["bilder"]}), "| Hintergrundvideos:", sum(1 for d in daten for b in d["bloecke"] if b["t"] == "video" and b["bg"]), "| Klickvideos:", sum(1 for d in daten for b in d["bloecke"] if b["t"] == "video" and not b["bg"]))
print("ohne Datum (post):", [d["pfad"] for d in daten if d["typ"] == "post" and not d["published"]][:5])
for p in ("/", "/karriere/", "/unternehmen/unsere-meilensteine/"):
    d = by[p]; print("--", p, d["woerter"], "W, Partner", d["partner"], "|", [(b["t"], (b.get("x") or b.get("src", [""]) if b["t"] != "video" else "video")[:38] if isinstance(b.get("x") or b.get("src"), str) else b["t"]) for b in d["bloecke"][:14]])
