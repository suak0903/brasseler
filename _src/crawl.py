#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crawlt alle Seiten der Bestandsseite brasseler.de (drei Yoast-Sitemaps: page, post, timeline-eintrag)
und legt das rohe HTML unter _src/raw/<pfad>.html ab. Die page- und timeline-Sitemaps zeigen auf den
Azure-Staging-Host, die Adressen werden auf www.brasseler.de umgeschrieben (Befund 02.10.2026).
Aufruf: python crawl.py          Autor: Marketing Operations (Vega), 02.10.2026, Demonstrator Brasseler"""
import re, os, sys, json, time, urllib.request, concurrent.futures
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw"); os.makedirs(RAW, exist_ok=True)
BASE = "https://www.brasseler.de"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as r: raw = r.read()
    return raw if binary else raw.decode("utf-8", errors="replace")
urls = {}
for sm in ("page", "post", "timeline-eintrag"):
    xml = fetch(f"{BASE}/{sm}-sitemap.xml")
    for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml):
        u = re.sub(r"^https://brasselerhomepageprod\.azurewebsites\.net", BASE, u)
        urls[u] = sm
print(len(urls), "URLs aus den Sitemaps")
def pfad(u):
    p = u.replace(BASE, "").strip("/") or "index"
    return os.path.join(RAW, p.replace("/", "__") + ".html")
def hole(u):
    ziel = pfad(u)
    if os.path.exists(ziel) and os.path.getsize(ziel) > 5000: return (u, "vorhanden", os.path.getsize(ziel))
    for versuch in range(3):
        try:
            t = fetch(u); open(ziel, "w", encoding="utf-8").write(t); return (u, "ok", len(t))
        except Exception as e:
            err = str(e); time.sleep(2)
    return (u, "FEHLER " + err[:80], 0)
erg = []
with concurrent.futures.ThreadPoolExecutor(6) as ex:
    for r in ex.map(hole, sorted(urls)): erg.append(r); print(r[1], r[2], r[0].replace(BASE, ""))
json.dump({u: {"sitemap": urls[u], "datei": os.path.basename(pfad(u))} for u in urls}, open(os.path.join(HERE, "urls.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
fehler = [r for r in erg if r[1].startswith("FEHLER")]
print(f"\n{len(erg)} Seiten, {len(fehler)} Fehler"); [print("  ", f) for f in fehler]
