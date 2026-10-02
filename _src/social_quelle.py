# -*- coding: utf-8 -*-
"""Social-Icons des Bestands (inline SVG im Fuß von brasseler.de) aus raw/index.html ziehen und als social.json ablegen,
damit der Fuß des Entwurfs dieselben Zeichen zeigt. Aufruf: python social_quelle.py
Autor: Marketing Operations (Vega), 02.10.2026"""
import io, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
h = io.open(os.path.join(HERE, "raw", "index.html"), encoding="utf-8").read()
m = re.search(r'<div class="social_media">(.*?)</div>', h, re.S)
out = []
for a in re.finditer(r'<a href="([^"]+)"[^>]*title="([^"]*)"[^>]*>(<svg.*?</svg>)', m.group(1), re.S):
    href, titel, svg = a.groups()
    name = re.sub(r"^Besuche Brasseler bei ", "", titel)
    farbe = re.search(r'fill="(#[0-9a-fA-F]{6})"', svg); farbe = farbe.group(1).lower() if farbe else "#3b4248"
    # Markenfarbe wird Kachel, das Zeichen selbst weiß (currentColor), sonst verschwindet es auf der eigenen Farbe
    svg = re.sub(r'fill="#[0-9a-fA-F]{3,6}"', 'fill="currentColor"', svg)
    out.append({"name": name, "href": href, "farbe": farbe, "svg": re.sub(r"\s+", " ", svg)})
io.open(os.path.join(HERE, "social.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
for o in out: print(o["name"], o["href"], len(o["svg"]), o["svg"][:80])
