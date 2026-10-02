# -*- coding: utf-8 -*-
"""Liest aus den Rohseiten (Start de/en) die Navigation mit Untermenüs, die Fußzeilen-Links, die Social-Links und
die Zahlen des Startseiten-Karussells. Ergebnis chrome.json für gen_chrome.py. Autor: Marketing Operations (Vega), 02.10.2026"""
import re, os, json, html, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw"); BASE = "https://www.brasseler.de"
def text(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()
out = {}
for lang, datei in (("de", "index.html"), ("en", "en.html")):
    doc = open(os.path.join(RAW, datei), encoding="utf-8").read()
    kopf = doc[:doc.find('id="et-boc"')] if 'id="et-boc"' in doc else doc[:60000]
    fuss = doc[doc.rfind("<footer"):] if "<footer" in doc else doc[-60000:]
    # Hauptmenü: Divi/WP-Menü als <ul id="top-menu"> oder class="menu"
    menu = re.search(r'<ul[^>]+(?:id="top-menu"|class="[^"]*\bmenu\b[^"]*")[^>]*>(.*?)</ul>\s*(?:</nav>|</div>)', kopf, re.S)
    eintraege = []
    if menu:
        m = menu.group(1)
        for li in re.finditer(r'<li[^>]*class="([^"]*)"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=<li[^>]*class="[^"]*menu-item-depth-0|\Z)', m, re.S):
            pass
    # robust: alle Links im Kopf mit Pfad auf die eigene Domain, in Reihenfolge, mit Tiefe aus sub-menu-Verschachtelung
    tiefe = 0; items = []
    # auch karriere.brasseler.de: „Stellenangebote“ steht im Bestandsmenü als externer Link (Suat 02.10.2026, hatte gefehlt)
    for tok in re.finditer(r'<ul[^>]*class="[^"]*sub-menu[^"]*"[^>]*>|</ul>|<a[^>]+href="(https://(?:www|karriere)\.brasseler\.de[^"#?]*)"[^>]*>(.*?)</a>', kopf, re.S):
        if tok.group(0).startswith("<ul"): tiefe += 1
        elif tok.group(0) == "</ul>": tiefe = max(0, tiefe - 1)
        else:
            t = text(tok.group(2))
            if t and len(t) < 40 and not re.match(r"^(de|en)$", t, re.I): items.append({"tiefe": tiefe, "text": t, "pfad": tok.group(1).replace(BASE, "")})
    # Duplikate (mobil und Desktop gleich) entfernen
    gesehen = set(); nav = []
    for i in items:
        k = (i["tiefe"], i["pfad"])
        if k in gesehen: continue
        gesehen.add(k); nav.append(i)
    fusslinks = []
    for a in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', fuss, re.S):
        h, t = html.unescape(a.group(1)), text(a.group(2))
        if h.startswith("http") and "brasseler.de" not in h and not t: fusslinks.append({"social": h})
        elif "brasseler.de" in h and t and len(t) < 40: fusslinks.append({"text": t, "pfad": h.replace(BASE, "")})
    social = sorted({l["social"] for l in fusslinks if "social" in l} | set(re.findall(r'href="(https?://(?:www\.)?(?:kununu|linkedin|xing|facebook|instagram|youtube)\.[^"]+)"', fuss)))
    zahlen = re.findall(r'<div class="[^"]*(?:zahl|counter|number|slide)[^"]*"[^>]*>(.*?)</div>', doc, re.S)
    out[lang] = {"nav": nav, "fuss": [l for l in fusslinks if "text" in l], "social": social}
    print(lang, "Nav:", [(i["tiefe"], i["text"], i["pfad"]) for i in nav][:30])
    print(lang, "Fuss:", out[lang]["fuss"][:12], "| Social:", social)
# Zahlen-Karussell: Suche nach Mustern "Jahre"/"Years" in der Nähe großer Zahlen
doc = open(os.path.join(RAW, "index.html"), encoding="utf-8").read()
k = re.findall(r'(?s)<(?:div|span|p|h\d)[^>]*>\s*([0-9][0-9\.]{0,6})\s*</(?:div|span|p|h\d)>\s*<(?:div|span|p|h\d)[^>]*>\s*([A-Za-zÄÖÜäöüß ]{3,20})\s*</(?:div|span|p|h\d)>\s*<(?:div|p|span)[^>]*>(.*?)</(?:div|p|span)>', doc)
print("Zahlen:", [(a, b, text(c)[:80]) for a, b, c in k][:8])
out["zahlen_roh"] = [(a, b, text(c)) for a, b, c in k]
json.dump(out, open(os.path.join(HERE, "chrome.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
