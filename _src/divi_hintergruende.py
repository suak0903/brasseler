# -*- coding: utf-8 -*-
"""Hintergrundbilder der Divi-Abschnitte aus dem Bestand holen. Divi schreibt Abschnitts- und Modul-Hintergründe nicht ins
HTML, sondern in ein CSS je Seite (/wp-content/et-cache/<id>/et-divi-builder-dynamic-<id>.css und -late.css). Dieses
Skript liest je Seite in raw/ die et-cache-Verweise, lädt die CSS-Dateien nach raw/etcache/ und sammelt alle
url(...)-Bilder aus /uploads/ in Reihenfolge ihres Auftretens. Ergebnis: hintergruende.json {pfad: [bild-urls]}.
Aufruf: python divi_hintergruende.py    Autor: Marketing Operations (Vega), 02.10.2026 (Unterseiten-Runde, Suat: „Go“)"""
import io, json, os, re, sys, time, urllib.request, concurrent.futures
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "raw"); CACHE = os.path.join(RAW, "etcache"); os.makedirs(CACHE, exist_ok=True)
BASE = "https://www.brasseler.de"; UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
daten = json.load(io.open(os.path.join(HERE, "data.json"), encoding="utf-8"))

def raw_name(pfad): return "index.html" if pfad == "/" else ("en.html" if pfad == "/en/" else pfad.strip("/").replace("/", "__") + ".html")

def laden(url):
    ziel = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9._-]", "_", url.split("/wp-content/")[-1]))
    if os.path.exists(ziel): return ziel
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r: io.open(ziel, "wb").write(r.read())
        time.sleep(0.2); return ziel
    except Exception as ex:
        print("fehlt", url, ex); return None

def bilder_aus_css(text):
    out = []
    for u in re.findall(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', text):
        if "/uploads/" not in u or re.search(r"\.svg(\?|$)|icon|flag|logo|favicon|/btt\b|arrow|pfeil|_hover|-hover", u, re.I): continue  # btt = Zurück-nach-oben-Knopf, hover = Kachel-Wechselbild
        u = u.split("?")[0]; u = u if u.startswith("http") else BASE + u
        if u not in out: out.append(u)
    return out

ergebnis = {}; fehlend = []
def arbeit(d):
    p = os.path.join(RAW, raw_name(d["pfad"]))
    if not os.path.exists(p): return d["pfad"], None
    h = io.open(p, encoding="utf-8", errors="ignore").read()
    # Die Hintergründe stehen im unified-deferred-CSS, nicht im builder-dynamic (gemessen 02.10.2026 an Seite 32)
    links = sorted(set(re.findall(r'(/wp-content/et-cache/\d+/(?:et-divi-builder-dynamic-\d+(?:-late)?\.css|et-core-unified-deferred-\d+\.min\.css))', h)))
    bilder = bilder_aus_css(h)  # Inline-Styles und style-Attribute der Seite selbst (Divi liefert Startseiten-CSS inline)
    for l in links:
        z = laden(BASE + l)
        if z:
            for b in bilder_aus_css(io.open(z, encoding="utf-8", errors="ignore").read()):
                if b not in bilder: bilder.append(b)
    return d["pfad"], bilder

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for pfad, bilder in ex.map(arbeit, daten):
        if bilder is None: fehlend.append(pfad); continue
        if bilder: ergebnis[pfad] = bilder
io.open(os.path.join(HERE, "hintergruende.json"), "w", encoding="utf-8").write(json.dumps(ergebnis, ensure_ascii=False, indent=1))
alle = sorted(set(u for v in ergebnis.values() for u in v))
print(len(ergebnis), "Seiten mit Hintergrundbildern,", len(alle), "verschiedene Bilder,", len(fehlend), "ohne raw-Datei")
for pfad in list(ergebnis)[:12]: print(" ", pfad, len(ergebnis[pfad]), ergebnis[pfad][0].split("/")[-1])
