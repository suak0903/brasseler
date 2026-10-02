# -*- coding: utf-8 -*-
"""Weltkarte als SVG mit gerader linker Kante: das Bestands-SVG (viewBox 0 0 302.925 158.109) hat links eine schräge Kante,
die Suat nicht wollte; hier wird der viewBox um 8,1 Prozent (178 von 2200 px, wie beim Raster) nach rechts verschoben.
Schreibt media/weltkarte.svg. Am Desktop zeigt die Seite das SVG (scharf wie im Bestand), am Handy die WebP-Fassung.
Aufruf: python karte_svg.py    Autor: Marketing Operations (Vega), 02.10.2026"""
import io, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(os.path.dirname(HERE), "media")
s = io.open(os.path.join(M, "brasseler-world-map-2.svg"), encoding="utf-8").read()
m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s); w, h = float(m.group(1)), float(m.group(2))
x0 = round(w * 178 / 2200, 3); neu = f'viewBox="{x0} 0 {round(w - x0, 3)} {h}"'
s = s.replace(m.group(0), neu, 1)
io.open(os.path.join(M, "weltkarte.svg"), "w", encoding="utf-8").write(s)
print(neu, len(s), "Zeichen")
