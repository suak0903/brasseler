# CLAUDE - Brasseler-Demonstrator

Redesign-Entwurf für brasseler.de (Gebr. Brasseler GmbH & Co. KG, Lemgo), gebaut am 02.10.2026 als Demonstration für Suats Bewerbung Head of Engineering (EO Executives, Peters). Unverbindlich, noindex, alle Inhalte aus der öffentlichen Bestandsseite. Live: https://suak0903.github.io/brasseler/ · Hinweisseite: /ueber-diesen-entwurf/ · Plan und Entscheidungen: Vault `_AGENTxCHG/marketingops/arbeit/2026-10-02 brasseler-website-plan.md`.

Autor: Marketing Operations (Vega), 02.10.2026. Regeln des Web-Starter-Kits gelten (`resources/Web-Starter-Kit/`), mit der KaTech-Abweichung: **alle Seiten werden erzeugt**, nicht von Hand geschrieben.

## Aufbau

```
index.html, <pfad>/index.html   203 erzeugte Seiten, Pfade wie im Original (de ohne, en mit /en/)
css/site.css · js/site.js       Design-System und Seitenlogik, Cache-Version VERSION in _src/gen_lib.py
font/                           Fira Sans (OFL), self-hosted; Ersatz für Corporate S OT (lizenzpflichtig)
media/                          Bilder als WebP 480/960/1600 plus JPG 1200, Hintergrundvideos verkleinert, Poster
_src/                           Generator und Daten, nicht Teil der Auslieferung; raw/ und assets/ nicht versioniert
```

| `_src/` | Aufgabe |
|---|---|
| `crawl.py` | holt die 207 Sitemap-URLs nach `raw/` (Azure-Host wird auf www.brasseler.de umgeschrieben) |
| `extract.py` + `paare.py` | Blöcke je Seite, Kennzahlen, Tabellen; Sprachpaare (feste Tabelle für Seiten, Heuristik für News und Chronik) → `data.json` |
| `download_media.py`, `extra_bilder.py`, `prepare_media.py` | Bilder laden und aufbereiten → `media-map.json`, `media-basis.json` |
| `bg_videos.py` | Hintergrundvideos laden, 720p, 12,5 fps, MP4 und WebM → `video-map.json` |
| `chrome_quelle.py`, `zahlen_quelle.py` | Menü, Fußzeile, Kennzahlen aus dem Bestand → `chrome.json`, `zahlen.json` |
| `gen.py`, `gen_lib.py`, `gen_chrome.py`, `inhalt.py` | Erzeugung aller Seiten; `gen_chrome.py` ist die **einzige** Quelle für Kopf, Menü, Fuß, Demo-Leiste |
| `check.py` | tote Verweise, Chrome-Gleichheit (Soll 2 und 2, je Sprache eine), noindex, H1, alt-Texte, hreflang |
| `qa.mjs` | Playwright: Konsole, fehlende Dateien, Überlauf bei 6 Breiten, Menü, Lightbox, Demo-Leiste, Video (Chromium und WebKit) |
| `messung.json` | Lighthouse-Werte alt und neu für die Hinweisseite |

## Ablauf bei jeder Änderung

```
cd _src
# VERSION in gen_lib.py erhöhen, wenn css oder js geändert wurden
python gen.py && python check.py
# im Projektwurzelverzeichnis: python -m http.server 8778
node qa.mjs
git add -A && git commit && git push      (Pages liefert aus main, Ordner /)
```

## Entschieden (Suat 02.10.2026)

- Beide Sprachen, alle 62 News je Sprache, Chronik vollständig. Nichts weglassen, nichts dazuerfinden.
- Startseiten-Video läuft automatisch wie im Bestand, aber verkleinert (10 MB auf 1,5 MB) und erst geladen, wenn sichtbar. Klickvideos (bis 164 MB) bleiben beim Original und laden erst beim Abspielen.
- Schrift: Fira Sans statt Corporate S OT, auf der Hinweisseite benannt.
- Hinweisseite kompakt, ohne Referenz-Riege, nur „Über mich“ mit Link auf akyol.de. Befunde zum Bestand dort als „gemessen, nicht geschätzt“.
- Logo und Fotos übernommen („alles im öffentlichen Raum“). Pages per noindex auf jeder Seite gesperrt. Die `robots.txt` im Projekt wirkt auf Pages nicht (Crawler lesen nur `suak0903.github.io/robots.txt`, Faber F4 02.10.2026); Bilder und Videos bleiben damit über die Bildersuche auffindbar, eine Host-robots ginge nur über ein Repo `suak0903.github.io`.
- Vier Prüfschritte durch Quality (Faber) statt einer Abnahme am Ende: F1 Quelle, F2 Gerüst, F3 Seiten, F4 live.

## Stolperfallen aus diesem Projekt

- Der Bestand hat **kein hreflang** und sein Sprachumschalter führt immer zur Startseite; die Paare stehen in `paare.py`.
- Chronik-Seiten haben ein anderes Template: Kopfleiste und Suchfeld liegen im Inhaltsbereich, deshalb entfernt `extract.py` header, nav und form vor dem Block-Scan (Befund Faber F1).
- Kennzahlen sind Divi-Zähler (`counter-number/title/text`), keine Absätze; die Tabelle auf einer News-Seite ist eine Tabelle, keine Liste.
- Vier Seiten liegen im Bestand doppelt (englisch unter deutschem Pfad): als Weiterleitung gebaut, in der Sitemap-Seite rot.
- `.lb[hidden]{display:none}` ist Pflicht, sonst überdeckt die unsichtbare Lightbox die ganze Seite (QA hat es gefunden).
- Animierte GIFs (Weltkarte-Länder) nur mit `[0]` an ImageMagick geben.
- Bilder unter 900 px Breite (Siegel, Logos) werden nicht auf volle Breite gezogen.
