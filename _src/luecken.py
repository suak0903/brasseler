# -*- coding: utf-8 -*-
"""Lückenanalyse: Wörter im Hauptinhalt des Bestands (raw/*.html, Divi-Inhalt ohne Kopf/Fuß/Menü) gegen Wörter in der
erzeugten Seite. Zeigt je Seite Bestand, Entwurf, Differenz, sortiert nach größter Lücke. Dazu die Divi-Module, die im
Bestand vorkommen und möglicherweise nicht übernommen sind. Aufruf: python luecken.py [min_diff]
Autor: Marketing Operations (Vega), 02.10.2026 (Suat: „nach unten hin fehlt total viel an Inhalt“)"""
import io, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
daten = json.load(io.open(os.path.join(HERE, "data.json"), encoding="utf-8"))
MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 60

def text(h):
    h = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h); h = re.sub(r"&[a-z#0-9]+;", " ", h)
    return re.sub(r"\s+", " ", h).strip()

def bestand(pfad):
    name = "index.html" if pfad == "/" else ("en.html" if pfad == "/en/" else ("en__" if pfad.startswith("/en/") else "") + pfad.strip("/").split("/")[-1] + ".html")
    p = os.path.join(HERE, "raw", name)
    if not os.path.exists(p):
        kand = [f for f in os.listdir(os.path.join(HERE, "raw")) if f.endswith(pfad.strip("/").split("/")[-1] + ".html")]
        if not kand: return None, None
        p = os.path.join(HERE, "raw", kand[0])
    h = io.open(p, encoding="utf-8", errors="ignore").read()
    m = re.search(r'<div[^>]+id="et-boc"[\s\S]*?(<footer|<div[^>]+id="main-footer"|<div[^>]+class="[^"]*et-l--footer)', h)
    inhalt = m.group(0) if m else h
    inhalt = re.sub(r"<header[\s\S]*?</header>", " ", inhalt, flags=re.I)
    inhalt = re.sub(r'<ul[^>]*id="top-menu"[\s\S]*?</ul>', " ", inhalt)
    module = sorted(set(re.findall(r'et_pb_(slider|tabs|toggle|accordion|blurb|team_member|testimonial|gallery|video|counter|number_counter|map|cta|pricing|image|code|contact_form|portfolio|post_slider|blog|fullwidth_\w+|countdown|circle_counter|bar_counters|comments|social_media_follow|sidebar|search|signup|menu|divider)\b', inhalt)))
    return len(text(inhalt).split()), module

def entwurf(pfad):
    p = os.path.join(ROOT, pfad.strip("/"), "index.html") if pfad.strip("/") else os.path.join(ROOT, "index.html")
    if not os.path.exists(p): return None
    h = io.open(p, encoding="utf-8").read()
    m = re.search(r'<main[^>]*>([\s\S]*)</main>', h)
    return len(text(m.group(1) if m else h).split())

zeilen = []
for d in daten:
    if d["duplikat_von"]: continue
    b, module = bestand(d["pfad"]); e = entwurf(d["pfad"])
    if b is None or e is None: continue
    zeilen.append((b - e, b, e, d["pfad"], d["typ"], ",".join(module)))
zeilen.sort(reverse=True)
print(f"{'Diff':>6} {'Bestand':>8} {'Entwurf':>8}  Pfad  [Typ]  Divi-Module")
for diff, b, e, pfad, typ, module in zeilen:
    if diff >= MIN: print(f"{diff:6d} {b:8d} {e:8d}  {pfad}  [{typ}]  {module}")
print(len([z for z in zeilen if z[0] >= MIN]), "Seiten mit mindestens", MIN, "Wörtern weniger als der Bestand (Bestandszählung enthält Menü-/Fußreste, daher grob)")
