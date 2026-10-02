# -*- coding: utf-8 -*-
"""Bausteine des Generators: Pfade, Bilder (WebP in drei Größen mit JPG-Fallback), Blockrenderer (Inhalt der
Bestandsseite in Sektionen), JSON-LD, Seitenrahmen. Alles statisch, kein Laufzeit-Include.
Autor: Marketing Operations (Vega), 02.10.2026, Demonstrator Brasseler. VERSION bei CSS- oder JS-Änderung erhöhen."""
import os, re, json, html
VERSION = "8"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
BASE = "https://www.brasseler.de"
DEMO = "https://suak0903.github.io/brasseler/"
media_basis = json.load(open(os.path.join(HERE, "media-basis.json"), encoding="utf-8"))
video_map = json.load(open(os.path.join(HERE, "video-map.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "video-map.json")) else {}
masse_cache = {}

def e(s): return html.escape(s or "", quote=True)

def root(pfad):
    """Relativer Präfix zum Wurzelverzeichnis für eine Seite mit Pfad wie /unternehmen/werte/ (-> ../../)."""
    tiefe = len([p for p in pfad.strip("/").split("/") if p])
    return "../" * tiefe if tiefe else ""

def ausgabe_pfad(pfad):
    p = pfad.strip("/")
    return os.path.join(ROOT, p.replace("/", os.sep), "index.html") if p else os.path.join(ROOT, "index.html")

def bild_masse(basis):
    """Breite und Höhe der 1600er-Fassung (oder der größten vorhandenen), für width/height-Attribute."""
    if basis in masse_cache: return masse_cache[basis]
    import struct
    w = h = 0
    for b in (1600, 960, 480):
        f = os.path.join(ROOT, "media", f"{basis}-{b}.webp")
        if os.path.exists(f):
            d = open(f, "rb").read(40)
            if d[12:16] == b"VP8 ": w, h = struct.unpack("<HH", d[26:30]); w &= 0x3fff; h &= 0x3fff
            elif d[12:16] == b"VP8L": bits = struct.unpack("<I", d[21:25])[0]; w = (bits & 0x3fff) + 1; h = ((bits >> 14) & 0x3fff) + 1
            elif d[12:16] == b"VP8X": w = int.from_bytes(d[24:27], "little") + 1; h = int.from_bytes(d[27:30], "little") + 1
            break
    masse_cache[basis] = (w, h); return (w, h)

def picture(src, alt, r, klasse="", lazy=True, sizes="(max-width: 700px) 100vw, 1200px", eager=False):
    """<picture> mit WebP-srcset und JPG-Fallback. SVG direkt. Unbekannte Bilder bleiben beim Original (lazy)."""
    basis = media_basis.get(src)
    if not basis:
        return f'<img src="{e(src)}" alt="{e(alt)}" loading="lazy" decoding="async"{(" class=" + chr(34) + klasse + chr(34)) if klasse else ""}>'
    if src.lower().endswith(".svg"):
        return f'<img src="{r}media/{basis}.svg" alt="{e(alt)}"{(" class=" + chr(34) + klasse + chr(34)) if klasse else ""} loading="{"eager" if eager else "lazy"}" decoding="async">'
    w, h = bild_masse(basis)
    dim = f' width="{w}" height="{h}"' if w and h else ""
    ld = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture{(" class=" + chr(34) + klasse + chr(34)) if klasse else ""}><source type="image/webp" srcset="{r}media/{basis}-480.webp 480w, {r}media/{basis}-960.webp 960w, {r}media/{basis}-1600.webp 1600w" sizes="{sizes}">'
            f'<img src="{r}media/{basis}-1200.jpg" alt="{e(alt)}"{dim} {ld}></picture>')

def ist_icon(b): return b.get("icon") or re.search(r"/icon[-_]", b["src"].lower()) is not None
def ist_kurz(b, n=5): return b["t"] == "p" and len(b["x"].split()) <= n and b["x"].rstrip().endswith((".", ":")) and "[" not in b["x"]
KONTEXT = {"r": "", "pfade": frozenset()}  # aktuelle Seite: Wurzelpräfix und gebaute Pfade, gesetzt vom Generator

def inline_html(s, r=None, pfade=None):
    """Links aus dem Bestand: auf gebaute Seiten relativ, sonst auf das Original; Links ohne Ziel werden Text."""
    if r is None: r = KONTEXT["r"]
    if pfade is None: pfade = KONTEXT["pfade"]
    s = e(s)
    def link(m):
        txt, href = m.group(1), html.unescape(m.group(2))
        if not re.match(r"^(https?:|mailto:|tel:|/|#)", href): return txt  # kaputter Bestandslink ohne Ziel
        ziel = link_lokal(href, r, pfade)
        ext = ziel.startswith("http") and not ziel.startswith(DEMO)
        return '<a href="%s"%s>%s</a>' % (e(ziel), ' target="_blank" rel="noopener"' if ext else "", txt)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s.replace("\n", "<br>")

def link_lokal(href, r, pfade):
    """Verweise auf Bestandsseiten zeigen in der Demo auf die eigene Fassung, alle anderen auf das Original."""
    h = html.unescape(href)
    if h.startswith("#") or h.startswith("mailto:") or h.startswith("tel:"): return h
    if h.startswith(BASE):
        p = h[len(BASE):].split("#")[0].split("?")[0]
        if not p.endswith("/"): p += "/"
        if p in pfade: return r + p.strip("/") + ("/" if p.strip("/") else "")
    if h.startswith("/") and not h.startswith("//"):
        p = h.split("#")[0].split("?")[0]
        if not p.endswith("/"): p += "/"
        if p in pfade: return r + p.strip("/") + ("/" if p.strip("/") else "")
        return BASE + h
    return h

def bloecke_html(bl, r, pfade, lang, lightbox=True):
    """Rendert die extrahierten Blöcke als Sektionen. Erkennt Kicker plus Leitzeile, Bildgruppen (Galerie), Icon-Raster,
    Bild-mit-Knopf-Kacheln, Personenkarten (Bild, Name, Rolle) und Jahresmarken der Chronik."""
    out = []; i = 0; n = len(bl); galerie_index = 0; hstapel = []  # Überschriften ohne Sprung: der Bestand hat h6 nach h2 (Faber F4); Stapel aus (Original, vergeben)
    KONTEXT["r"], KONTEXT["pfade"] = r, pfade
    def p_html(b): return f'<p>{inline_html(b["x"])}</p>'
    while i < n:
        b = bl[i]
        # Bildgruppe: zwei oder mehr Bilder hintereinander (keine Icons)
        if b["t"] == "img" and not ist_icon(b) and i + 1 < n and bl[i + 1]["t"] == "img" and not ist_icon(bl[i + 1]):
            j = i
            while j < n and bl[j]["t"] == "img" and not ist_icon(bl[j]): j += 1
            gruppe = bl[i:j]; i = j
            # Bild-plus-Knopf-Kacheln? (img, button, img, button ...) wird unten behandelt; hier reine Galerie
            spalten = 2 if len(gruppe) == 2 else (3 if len(gruppe) in (3, 5, 6, 9) else 4)
            out.append(f'<div class="gal gal--{spalten}">' + "".join(
                f'<figure class="gal__i"><button type="button" class="gal__b" data-lb data-full="{(r + "media/" + media_basis[x["src"]] + "-1600.webp") if media_basis.get(x["src"]) else e(x["src"])}" aria-label="{e(x["alt"] or ("Bild vergrößern" if lang == "de" else "Enlarge image"))}">{picture(x["src"], x["alt"], r, sizes="(max-width: 700px) 50vw, 400px")}</button></figure>' for x in gruppe) + "</div>")
            continue
        # Icon-Raster: mehrere Icons hintereinander
        if b["t"] == "img" and ist_icon(b):
            j = i
            while j < n and bl[j]["t"] == "img" and ist_icon(bl[j]): j += 1
            gruppe = bl[i:j]; i = j
            out.append('<ul class="icons">' + "".join(f'<li class="icons__i">{picture(x["src"], "", r, klasse="icons__img", sizes="96px")}<span>{e(x["alt"] or re.sub(r"[-_]", " ", x["src"].split("/")[-1].rsplit(".", 1)[0].replace("icon", "").strip("-_ ")).capitalize())}</span></li>' for x in gruppe) + "</ul>")
            continue
        # Bild mit Knopf: Kachel; mehrere davon ein Raster
        if b["t"] == "img" and i + 1 < n and bl[i + 1]["t"] == "button":
            kacheln = []; j = i
            while j + 1 < n and bl[j]["t"] == "img" and bl[j + 1]["t"] == "button":
                kacheln.append((bl[j], bl[j + 1])); j += 2
            i = j
            out.append(f'<div class="kacheln kacheln--{min(3, len(kacheln))}">' + "".join(
                f'<a class="kachel" href="{e(link_lokal(k["href"], r, pfade))}"{" target=_blank rel=noopener" if k["href"].startswith("http") and "brasseler.de/" not in k["href"] and not k["href"].startswith(BASE) else ""}>{picture(x["src"], x["alt"], r, sizes="(max-width: 700px) 100vw, 400px")}<span class="kachel__l">{e(k["x"])}</span></a>' for x, k in kacheln) + "</div>")
            continue
        # Personenkarte: Bild, dann h4 (Name), dann p (Rolle) und optional h5 (Bereiche)
        if b["t"] == "img" and i + 1 < n and bl[i + 1]["t"] == "h4":
            name = bl[i + 1]["x"]; rolle = ""; bereiche = ""; j = i + 2
            if j < n and bl[j]["t"] == "p" and len(bl[j]["x"].split()) <= 8: rolle = bl[j]["x"]; j += 1
            if j < n and bl[j]["t"] == "h5": bereiche = bl[j]["x"]; j += 1
            out.append(f'<div class="person">{picture(b["src"], name, r, klasse="person__bild", sizes="(max-width: 700px) 100vw, 360px")}<div class="person__t"><h3 class="person__n">{e(name)}</h3>{("<p class=person__r>" + e(rolle) + "</p>") if rolle else ""}{("<p class=person__b>" + inline_html(bereiche) + "</p>") if bereiche else ""}</div></div>')
            i = j; continue
        # Kicker plus Leitzeile: kurzes p mit Punkt, dann kurzes p
        if ist_kurz(b) and i + 1 < n and bl[i + 1]["t"] == "p" and len(bl[i + 1]["x"].split()) <= 14 and "[" not in bl[i + 1]["x"]:
            out.append(f'<div class="sek"><p class="kicker">{e(b["x"])}</p><p class="lead">{inline_html(bl[i + 1]["x"])}</p></div>'); i += 2; continue
        if ist_kurz(b, 4) and i + 1 < n and bl[i + 1]["t"] == "button":
            out.append(f'<div class="sek"><p class="lead">{inline_html(b["x"])}</p></div>'); i += 1; continue
        # Jahresmarke der Chronik: h3 dann p mit Jahreszahl
        if b["t"] == "h3" and i + 1 < n and bl[i + 1]["t"] == "p" and re.fullmatch(r"(19|20)\d\d(\s*[-–/]\s*(19|20)?\d\d)?", bl[i + 1]["x"].strip()):
            out.append(f'<div class="jahr"><span class="jahr__z">{e(bl[i + 1]["x"].strip())}</span><h3 class="jahr__h">{e(b["x"])}</h3></div>'); i += 2; continue
        if b["t"] in ("h1", "h2", "h3", "h4", "h5", "h6"):
            orig = int(b["t"][1])
            while hstapel and hstapel[-1][0] >= orig: hstapel.pop()
            ebene = min(max(orig, 2), (hstapel[-1][1] + 1) if hstapel else 2); hstapel.append((orig, ebene))
            out.append(f'<h{ebene} class="t-{b["t"]}">{inline_html(b["x"])}</h{ebene}>')
        elif b["t"] == "p": out.append(p_html(b))
        elif b["t"] in ("ul", "ol"): out.append(f'<{b["t"]}>' + "".join(f"<li>{inline_html(x)}</li>" for x in b["items"]) + f'</{b["t"]}>')
        elif b["t"] == "zitat": out.append(f'<blockquote>{inline_html(b["x"])}</blockquote>')
        elif b["t"] == "button":
            ext = b["href"].startswith("http") and not b["href"].startswith(BASE)
            out.append(f'<p class="btn-zeile"><a class="btn" href="{e(link_lokal(b["href"], r, pfade))}"{" target=_blank rel=noopener" if ext else ""}>{e(b["x"])}</a></p>')
        elif b["t"] == "img":
            w, h = bild_masse(media_basis.get(b["src"], ""))
            klein = f' style="max-width:{w}px"' if 0 < w < 900 else ""  # Siegel, Logos, kleine Grafiken nicht aufziehen
            quadrat = " bild--quadrat" if w and h and 0.9 <= w / h <= 1.1 else ""  # Siegel und Logos sind meist quadratisch
            out.append(f'<figure class="bild{quadrat}"{klein}>{picture(b["src"], b["alt"], r, sizes=f"(max-width: 700px) 100vw, {w}px" if klein else ("(max-width: 700px) 100vw, 400px" if quadrat else "(max-width: 700px) 100vw, 1200px"))}</figure>')
        elif b["t"] == "video":
            out.append(video_html(b, r, lang))
        elif b["t"] == "iframe":
            out.append(f'<p class="hinweis">{"Eingebetteter Inhalt der Bestandsseite:" if lang == "de" else "Embedded content of the original site:"} <a href="{e(b["src"])}" target="_blank" rel="noopener">{e(b["src"][:60])}</a></p>')
        i += 1
    return "\n".join(out)

def video_quellen(n, r):
    """data-Attribute für ein Hintergrundvideo: WebM nur, wenn sie kleiner als die MP4 ist (Befund Faber F2)."""
    mp4 = os.path.join(ROOT, "media", n + ".mp4"); webm = os.path.join(ROOT, "media", n + ".webm")
    attr = f'data-src-mp4="{r}media/{n}.mp4"'
    if os.path.exists(webm) and os.path.exists(mp4) and os.path.getsize(webm) < os.path.getsize(mp4): attr += f' data-src-webm="{r}media/{n}.webm"'
    return attr

def video_html(b, r, lang):
    """Hintergrundvideos laufen automatisch (verkleinerte Kopie), Klickvideos laden erst beim Klick vom Original."""
    mp4 = next((s for s in b["src"] if s.endswith(".mp4")), b["src"][0])
    if b.get("bg") and mp4 in video_map:
        n = video_map[mp4]
        return (f'<figure class="vid vid--auto"><video class="vid__v" autoplay muted loop playsinline preload="none" poster="{r}media/{n}-poster.jpg" {video_quellen(n, r)} aria-hidden="true"></video></figure>')
    poster = b.get("poster") or ""
    pb = media_basis.get(poster)
    ph = f'poster="{r}media/{pb}-1200.jpg"' if pb else f'poster="{r}media/video-poster.jpg"'
    quellen = "".join(f'<source src="{e(s)}" type="video/{"webm" if s.endswith(".webm") else "mp4"}">' for s in b["src"])
    return (f'<figure class="vid vid--klick"><video class="vid__v" controls preload="none" {ph}>{quellen}</video>'
            f'<figcaption class="vid__c">{"Video der Bestandsseite, lädt erst beim Abspielen vom Original." if lang == "de" else "Video from the original site, loads from the original only when played."}</figcaption></figure>')

def json_ld(objs):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": objs}, ensure_ascii=False, separators=(",", ":")) + "</script>"
