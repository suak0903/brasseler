# -*- coding: utf-8 -*-
"""Die fünf Werte-Kreise von /unternehmen/unsere-werte/ stehen im Bestand als SVG-Text (nicht als HTML), darum hat sie der
Extraktor nicht. Liest je Sprache Titel und Textzeilen aus den <svg><text>-Knoten → werte.json {pfad: [[titel, text], ...]}.
Autor: Marketing Operations (Vega), 03.10.2026 (Suat: „Die Seite unsere Werte sieht völlig anders aus“)"""
import io, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}
for pfad, name in (("/unternehmen/unsere-werte/", "unternehmen__unsere-werte.html"), ("/en/company/our-values/", "en__company__our-values.html")):
    p = os.path.join(HERE, "raw", name)
    if not os.path.exists(p): continue
    h = io.open(p, encoding="utf-8", errors="ignore").read()
    werte = []
    for svg in re.findall(r"<svg[^>]*>.*?</svg>", h, re.S):
        texte = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip() for t in re.findall(r"<text[^>]*>(.*?)</text>", svg, re.S)]
        texte = [t for t in texte if t]
        if len(texte) < 3: continue
        titel = texte[0]; rest = " ".join(texte[1:])
        if len(titel.split()) <= 3 and len(rest) > 40: werte.append([titel, rest])
    if werte: out[pfad] = werte
io.open(os.path.join(HERE, "werte.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
for k, v in out.items(): print(k, len(v), [w[0] for w in v])
