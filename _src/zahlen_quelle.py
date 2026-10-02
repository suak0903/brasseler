# -*- coding: utf-8 -*-
"""Liest die Kennzahlen-Kacheln (counter) der Startseite de/en aus dem Roh-HTML: Zahl, Einheit, Satz. Ergebnis zahlen.json.
Autor: Marketing Operations (Vega), 02.10.2026"""
import re, os, json, html, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
def text(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
out = {}
for lang, datei in (("de", "index.html"), ("en", "en.html")):
    doc = open(os.path.join(HERE, "raw", datei), encoding="utf-8").read()
    kacheln = []
    for m in re.finditer(r'(?s)<div[^>]+class="[^"]*counter-number[^"]*"[^>]*>(.*?)</div>\s*<div[^>]+class="[^"]*counter-(?:label|unit|title)[^"]*"[^>]*>(.*?)</div>\s*<div[^>]+class="[^"]*counter-text[^"]*"[^>]*>(.*?)</div>', doc):
        kacheln.append({"zahl": text(m.group(1)), "einheit": text(m.group(2)), "satz": text(m.group(3))})
    if not kacheln:  # allgemeiner: jede Klasse mit counter, Reihenfolge Zahl, Einheit, Text
        teile = re.findall(r'(?s)<div[^>]+class="[^"]*\bcounter-([a-z]+)[^"]*"[^>]*>(.*?)</div>', doc)
        akt = {}
        for art, inhalt in teile:
            t = text(inhalt)
            if art in ("number", "zahl"): akt = {"zahl": t}
            elif art in ("label", "unit", "title", "einheit"): akt["einheit"] = t
            elif art == "text": akt["satz"] = t; kacheln.append(akt); akt = {}
    out[lang] = kacheln
    print(lang, kacheln)
json.dump(out, open(os.path.join(HERE, "zahlen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
