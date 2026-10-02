# -*- coding: utf-8 -*-
"""Breadcrumbs des Bestands je Seite (Yoast: <span class="breadcrumb_last">, davor Links) aus raw/ lesen → krumen.json
{pfad: [[text, href], ...]} ohne „Start“ und ohne die Seite selbst, nur die Zwischenstufen, plus "last": Kurzname der Seite.
Suat 03.10.2026: „Breadcrumbs wie im Original, Unternehmen statt Über…, kurze Namen.“ Autor: Marketing Operations (Vega)"""
import io, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); BASE = "https://www.brasseler.de"
daten = json.load(io.open(os.path.join(HERE, "data.json"), encoding="utf-8"))
def raw_name(pfad): return "index.html" if pfad == "/" else ("en.html" if pfad == "/en/" else pfad.strip("/").replace("/", "__") + ".html")
out = {}
for d in daten:
    p = os.path.join(HERE, "raw", raw_name(d["pfad"]))
    if not os.path.exists(p): continue
    h = io.open(p, encoding="utf-8", errors="ignore").read()
    m = re.search(r'<span class="breadcrumb_last"[^>]*>(.*?)</span>', h, re.S)
    if not m: continue
    last = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    vor = h[max(0, m.start() - 1500):m.start()]
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', vor, re.S)
    kette = []
    for href, t in links[-4:]:
        t = re.sub(r"<[^>]+>", "", t).strip(); href = href.replace(BASE, "")
        if t and href.startswith("/") and t.lower() not in ("start", "home") and href not in ("/", "/en/"): kette.append([t, href])
    out[d["pfad"]] = {"kette": kette, "last": last}
io.open(os.path.join(HERE, "krumen.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print(len(out), "Seiten mit Breadcrumb"); [print(" ", k, v) for k, v in list(out.items())[:6] if k.count("/") > 1]
