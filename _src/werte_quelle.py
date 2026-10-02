# -*- coding: utf-8 -*-
"""Die fünf Werte-Kreise von /unternehmen/unsere-werte/ stehen im Bestand als Inline-SVG (je Wert eine Grafik 198×198 mit Kreis,
Buchstabe, Titel und Text), nicht als HTML, darum hat sie der Extraktor nicht. Übernimmt die SVGs unverändert → werte.json
{pfad: [svg, ...]} (Suat 03.10.: „Warum nicht einfach deren Bild nehmen?“; vorher Nachbau als farbige Kreise, verworfen).
Autor: Marketing Operations (Vega), 03.10.2026"""
import io, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
for pfad, name in (("/unternehmen/unsere-werte/", "unternehmen__unsere-werte.html"), ("/en/company/our-values/", "en__company__our-values.html")):
    p = os.path.join(HERE, "raw", name)
    if not os.path.exists(p): continue
    h = io.open(p, encoding="utf-8", errors="ignore").read()
    svgs = []
    for svg in re.findall(r"<svg[^>]*>.*?</svg>", h, re.S):
        if svg.count("<text") < 3 or 'class="gw"' not in svg: continue
        svg = re.sub(r"\s+", " ", svg)
        svg = svg.replace('class="gw"', 'class="wert-svg" role="img"')
        svgs.append(svg)
    if svgs: out[pfad] = svgs
io.open(os.path.join(HERE, "werte.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
for k, v in out.items(): print(k, len(v))
