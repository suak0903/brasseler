# -*- coding: utf-8 -*-
"""Berufe-Karussell des Bestands (/karriere/ausbildung/ und /en/careers/…): je Kachel Titel und Hintergrundbild aus dem
Markup <div class="ausbildung …" style="background-image:url(…)"> … <div class="ausbildung-title">…</div>. Ergebnis berufe.json
{titel_klein: bild-url}. Aufruf: python berufe_quelle.py    Autor: Marketing Operations (Vega), 03.10.2026 (Faber: „Zuordnung aus dem Original-Karussell übernehmen statt raten“)"""
import io, json, os, re, glob
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = "https://www.brasseler.de"
out = {}
for p in glob.glob(os.path.join(HERE, "raw", "*.html")):
    h = io.open(p, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'<div class="ausbildung slide-\d+"[^>]*style="[^"]*url\(([^)]+)\)[^"]*"[^>]*>(.*?)<div class="ausbildung-buttons">', h, re.S):
        url = m.group(1).strip("'\" "); url = url if url.startswith("http") else BASE + url
        t = re.search(r'<div class="ausbildung-title">(.*?)</div>', m.group(2), re.S)
        if not t: continue
        titel = re.sub(r"<[^>]+>", " ", t.group(1)); titel = re.sub(r"\s+", " ", titel).strip().lower()
        out[titel] = url
io.open(os.path.join(HERE, "berufe.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print(len(out), "Berufe"); [print(" ", k, "->", v.split("/")[-1]) for k, v in out.items()]
