# -*- coding: utf-8 -*-
"""Die blaue Schwungkurve aus dem Fuß von brasseler.de (inline SVG 1159x252) aus raw/index.html ziehen und als
media/fuss-kurve.svg ablegen. Aufruf: python kurve_quelle.py    Autor: Marketing Operations (Vega), 02.10.2026"""
import io, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
h = io.open(os.path.join(HERE, "raw", "index.html"), encoding="utf-8").read()
m = re.search(r'<svg width="1159" height="252".*?</svg>', h, re.S)
svg = m.group(0)
print(len(svg), re.findall(r'(stroke|fill)="([^"]*)"', svg)[:6], svg[:200])
io.open(os.path.join(ROOT, "media", "fuss-kurve.svg"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
