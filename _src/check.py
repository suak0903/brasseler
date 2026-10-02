#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüfung vor dem Deploy: tote interne Verweise und Medien, Chrome-Gleichheit (md5 je Sprache), noindex auf jeder
Seite, genau eine H1, Gedankenstrich-Gate, alt-Texte, hreflang-Paare symmetrisch. Nach KaTech check.py.
Autor: Marketing Operations (Vega), 02.10.2026"""
import hashlib, os, re, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
IGNORIEREN = {"_src", ".git", "font", "media", "node_modules"}
fehler = defaultdict(list); seiten = []; fehler_ziele = defaultdict(int)
for basis, ordner, dateien in os.walk(ROOT):
    ordner[:] = [o for o in ordner if o not in IGNORIEREN]
    for d in dateien:
        if d.endswith(".html"): seiten.append(os.path.join(basis, d))
print(f"HTML-Dateien: {len(seiten)}")
kopf_md5, fuss_md5 = defaultdict(list), defaultdict(list); weiter = 0; hreflang = {}
for pfad in seiten:
    rel = os.path.relpath(pfad, ROOT).replace(os.sep, "/"); doc = open(pfad, encoding="utf-8").read(); verz = os.path.dirname(pfad)
    if rel == "404.html": continue  # absolute Pfade unter /brasseler/, nur live auflösbar
    eigene = rel.startswith(("ueber-diesen-entwurf", "sitemap", "en/sitemap", "impressum", "en/legal-notice"))
    m_um = re.search(r'<meta http-equiv="refresh" content="0; url=([^"]+)"', doc)
    if m_um:
        ziel = os.path.normpath(os.path.join(verz, m_um.group(1)))
        if not os.path.exists(os.path.join(ziel, "index.html")) and not os.path.exists(ziel): fehler["Weiterleitung ins Leere"].append(f"{rel} -> {m_um.group(1)}")
        weiter += 1; continue
    if 'content="noindex, nofollow"' not in doc: fehler["kein noindex"].append(rel)
    h1 = len(re.findall(r"<h1[ >]", doc))
    if h1 != 1: fehler[f"H1-Anzahl {h1}"].append(rel)
    tr = re.findall(r"—|&mdash;|&#8212;", doc)
    if tr and eigene: fehler[f"Gedankenstrich in eigenem Text ({len(tr)}x)"].append(rel)
    lang = re.search(r'<html lang="(\w+)"', doc).group(1)
    m = re.search(r'<header class="nav.*?</header>', doc, re.S)
    if m:
        norm = re.sub(r'(href|src)="[^"]*"', "", m.group(0)).replace(' aria-current="page"', "").replace(' data-zweig="1"', "")
        norm = re.sub(r' title="[^"]*"', "", norm)
        kopf_md5[lang + ":" + hashlib.md5(norm.encode()).hexdigest()].append(rel)
    f = re.search(r'<footer class="fuss">.*?</footer>', doc, re.S)
    if f: fuss_md5[lang + ":" + hashlib.md5(re.sub(r'(href|src)="[^"]*"', "", f.group(0)).encode()).hexdigest()].append(rel)
    for attr, wert in re.findall(r'(href|src|srcset|data-full|data-src-mp4|data-src-webm|poster)="([^"]+)"', doc):
        for teil in (wert.split(",") if attr == "srcset" else [wert]):
            w = teil.strip().split()[0] if teil.strip() else ""
            if not w or w.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")): continue
            rein = w.split("#")[0].split("?")[0]
            if not rein: continue
            ziel = os.path.normpath(os.path.join(verz, rein))
            if os.path.isdir(ziel): ziel = os.path.join(ziel, "index.html")
            if not os.path.exists(ziel): fehler["toter Verweis"].append(f"{rel} -> {w}"); fehler_ziele[re.sub(r"^(\.\./)+", "", rein)] += 1
    for tag in re.findall(r"<img [^>]*>", doc):
        if "alt=" not in tag: fehler["img ohne alt"].append(rel); break
    can = re.search(r'<link rel="canonical" href="([^"]+)"', doc); alt = re.search(r'<link rel="alternate" hreflang="(?:de|en)" href="([^"]+)">\n<link rel="alternate" hreflang="(?:de|en)" href="([^"]+)"', doc)
    if can: hreflang[can.group(1)] = re.findall(r'<link rel="alternate" hreflang="(\w+)" href="([^"]+)"', doc)
for url, alts in hreflang.items():
    for l, ziel in alts:
        if ziel != url and ziel in hreflang and url not in [z for _, z in hreflang[ziel]]: fehler["hreflang nicht symmetrisch"].append(f"{url} -> {ziel}")
print(f"Weiterleitungen: {weiter} | Kopf-Varianten: {len(kopf_md5)} (Soll 2, je Sprache eine) | Fuß-Varianten: {len(fuss_md5)} (Soll 2)")
for h, s in list(kopf_md5.items()):
    if len(kopf_md5) > 2: print(f"   Kopf {h[:12]}: {len(s)} Seiten, z. B. {s[0]}")
for h, s in list(fuss_md5.items()):
    if len(fuss_md5) > 2: print(f"   Fuß {h[:12]}: {len(s)} Seiten, z. B. {s[0]}")
if fehler_ziele: print("Fehlende Ziele, gruppiert:"); [print(f"   {n:4d}x {z}") for z, n in sorted(fehler_ziele.items(), key=lambda x: -x[1])[:15]]
if not fehler: print("Keine Befunde.")
for art, liste in sorted(fehler.items(), key=lambda x: -len(x[1])):
    print(f"{art}: {len(liste)}"); [print("   ", e) for e in liste[:6]]
    if len(liste) > 6: print(f"    ... und {len(liste) - 6} weitere")
sys.exit(1 if fehler else 0)
