# Drei Bilder der Startseite liegen im Bestand nur als CSS-Hintergrund (Werte, Verantwortung, Azubi-Banner) und
# fehlen deshalb in data.json. Hier gezielt laden und in media-map und media-basis eintragen, dann prepare_media.
# Autor: Marketing Operations (Vega), 02.10.2026
import json, os, re, urllib.request, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
EXTRA = ["https://www.brasseler.de/uploads/brasseler-home-nachhaltigkeit-2.jpg", "https://www.brasseler.de/uploads/IMAG_20190930_56_2Pers-Monitor-Besp_902.jpg",
         "https://www.brasseler.de/uploads/brasseler-world-map-2.svg", "https://www.brasseler.de/uploads/BRASSELER_23_2473_Imagefilm_1080p_thumbnail-2025.jpg"]
doc = open(os.path.join(HERE, "raw", "index.html"), encoding="utf-8").read()
# Hintergrundbilder der Startseite aus inline-Styles mitnehmen
for u in re.findall(r"background-image:\s*url\(['\"]?(https://www\.brasseler\.de/uploads/[^'\")]+)", doc): EXTRA.append(re.sub(r"-\d{2,4}x\d{2,4}(?=\.)", "", u))
karte = json.load(open(os.path.join(HERE, "media-map.json"), encoding="utf-8"))
def name(u): return re.sub(r"[^A-Za-z0-9._-]", "_", u.split("/")[-1].split("?")[0])
for u in dict.fromkeys(EXTRA):
    z = os.path.join(HERE, "assets", "img", name(u))
    if not os.path.exists(z):
        try: open(z, "wb").write(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()); print("geladen", name(u))
        except Exception as e: print("FEHLER", u[-50:], e); continue
    karte[u] = name(u)
json.dump(karte, open(os.path.join(HERE, "media-map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Hintergrundbilder Start:", [n for n in dict.fromkeys(EXTRA)][4:])
