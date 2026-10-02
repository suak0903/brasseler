#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lädt alle in data.json referenzierten Bilder (Originalgröße) plus Logo und og-Bilder nach _src/assets/img/.
Dateiname = Originalname. Vorhandene Dateien werden übersprungen. Autor: Marketing Operations (Vega), 02.10.2026"""
import json, os, sys, re, time, urllib.request, concurrent.futures
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ZIEL = os.path.join(HERE, "assets", "img"); os.makedirs(ZIEL, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
d = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
urls = set(["https://www.brasseler.de/uploads/logo.svg", "https://www.brasseler.de/uploads/logo-kometdental-3.svg"])
for x in d:
    urls.update(x["bilder"]);
    if x["og"]: urls.add(x["og"])
# Hintergrundbilder der Divi-Abschnitte (divi_hintergruende.py), seit 02.10.2026 abends: Hero-Bilder der Unterseiten
hg = os.path.join(HERE, "hintergruende.json")
if os.path.exists(hg):
    for v in json.load(open(hg, encoding="utf-8")).values(): urls.update(v)
def name(u): return re.sub(r"[^A-Za-z0-9._-]", "_", u.split("/")[-1].split("?")[0])
def hole(u):
    z = os.path.join(ZIEL, name(u))
    if os.path.exists(z) and os.path.getsize(z) > 0: return (u, "vorhanden")
    for v in range(3):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r: b = r.read()
            open(z, "wb").write(b); return (u, "ok %d" % len(b))
        except Exception as e:
            err = str(e)[:60]; time.sleep(1.5)
    # Originalgröße nicht vorhanden: eine große Variante versuchen
    return (u, "FEHLER " + err)
erg = []
with concurrent.futures.ThreadPoolExecutor(6) as ex:
    for r in ex.map(hole, sorted(urls)): erg.append(r)
fehler = [r for r in erg if r[1].startswith("FEHLER")]
print(len(erg), "Bilder,", len(fehler), "Fehler"); [print("  ", f[0].split("/")[-1][:70], f[1]) for f in fehler[:40]]
json.dump({u: name(u) for u in urls}, open(os.path.join(HERE, "media-map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
