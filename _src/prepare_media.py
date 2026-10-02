#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bereitet die Bestandsbilder für die Auslieferung auf: je Bild WebP in 480, 960 und 1600 px Breite plus ein JPG-Fallback
in 1200 px, Metadaten entfernt, SVG unverändert kopiert. Ziel media/<name>-<breite>.webp. Nur Bilder, die data.json
nennt. Vorhandene Ausgaben werden übersprungen. Autor: Marketing Operations (Vega), 02.10.2026"""
import json, os, re, sys, subprocess, concurrent.futures
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, "assets", "img"); ZIEL = os.path.join(HERE, "..", "media"); os.makedirs(ZIEL, exist_ok=True)
karte = json.load(open(os.path.join(HERE, "media-map.json"), encoding="utf-8"))
BREITEN = (480, 960, 1600)
def basis(name): return re.sub(r"\.(jpe?g|png|webp|gif|svg)$", "", name, flags=re.I).lower()
def arbeit(name):
    q = os.path.join(IMG, name)
    if not os.path.exists(q) or os.path.getsize(q) == 0: return (name, "fehlt")
    b = basis(name)
    if name.lower().endswith(".svg"):
        z = os.path.join(ZIEL, b + ".svg")
        if not os.path.exists(z): open(z, "wb").write(open(q, "rb").read())
        return (name, "svg")
    out = []
    if name.lower().endswith(".gif"): q = q + "[0]"  # animierte GIFs: nur das erste Bild
    for w in BREITEN:
        z = os.path.join(ZIEL, f"{b}-{w}.webp")
        if not os.path.exists(z):
            subprocess.run(["magick", q, "-auto-orient", "-strip", "-resize", f"{w}x>", "-quality", "80", "-define", "webp:method=4", z], check=True, capture_output=True)
        out.append(w)
    z = os.path.join(ZIEL, f"{b}-1200.jpg")
    if not os.path.exists(z):
        subprocess.run(["magick", q, "-auto-orient", "-strip", "-resize", "1200x>", "-quality", "82", "-interlace", "Plane", z], check=True, capture_output=True)
    return (name, "ok")
erg = []
with concurrent.futures.ThreadPoolExecutor(4) as ex:
    for r in ex.map(arbeit, sorted(set(karte.values()))): erg.append(r)
import collections; print(collections.Counter(r[1] for r in erg)); [print("  fehlt:", r[0]) for r in erg if r[1] == "fehlt"][:10]
json.dump({u: basis(n) for u, n in karte.items()}, open(os.path.join(HERE, "media-basis.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
