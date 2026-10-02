# -*- coding: utf-8 -*-
"""Lückenanalyse Bilder und Module je Hauptseite: Bilder im Bestandsinhalt (ohne Logo, Icons, Flaggen) gegen Bilder in der
erzeugten Seite, dazu Divi-Module (Slider, Tabs, Galerie, Video) und Videos. Aufruf: python luecken_bilder.py
Autor: Marketing Operations (Vega), 02.10.2026"""
import io, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SEITEN = ["/", "/unternehmen/", "/unternehmen/gesellschafterkreis/", "/unternehmen/management/", "/unternehmen/unsere-werte/", "/unternehmen/unsere-verantwortung/", "/unternehmen/unsere-meilensteine/", "/unternehmen/brasseler-100-years/", "/geschaeftsbereiche/", "/international/", "/karriere/", "/karriere/ausbildung/", "/karriere/studierende/", "/news/"]
def raw_name(pfad): return "index.html" if pfad == "/" else pfad.strip("/").replace("/", "__") + ".html"
for pfad in SEITEN:
    rp = os.path.join(HERE, "raw", raw_name(pfad))
    if not os.path.exists(rp): print(pfad, "kein raw"); continue
    h = io.open(rp, encoding="utf-8", errors="ignore").read()
    m = re.search(r'<div[^>]+id="et-boc"[\s\S]*?(<footer|id="main-footer"|et-l--footer)', h); inhalt = m.group(0) if m else h
    inhalt = re.sub(r"<header[\s\S]*?</header>", " ", inhalt, flags=re.I)
    bilder = [s for s in re.findall(r'<img[^>]+src="([^"]+)"', inhalt) if not re.search(r"logo|favicon|flag|icon|\.svg", s, re.I)]
    bg = re.findall(r'background-image:\s*url\(([^)]+)\)', inhalt)
    videos = re.findall(r'<video[^>]*>|\.mp4', inhalt)
    module = sorted(set(re.findall(r'et_pb_(slider|slide\b|tabs|toggle|accordion|blurb|team_member|testimonial|gallery|video\b|counter|number_counter|cta|image|code|fullwidth_\w+|blog|post_slider|divider)', inhalt)))
    ep = os.path.join(ROOT, pfad.strip("/"), "index.html") if pfad.strip("/") else os.path.join(ROOT, "index.html")
    e = io.open(ep, encoding="utf-8").read(); mm = re.search(r'<main[^>]*>([\s\S]*)</main>', e); e = mm.group(1) if mm else e
    e_bilder = len(re.findall(r'<picture|<img[^>]+src="[^"]*(?<!svg)"', e)); e_video = len(re.findall(r"<video", e))
    print(f"{pfad:40s} Bestand: {len(set(bilder)):3d} Bilder, {len(set(bg)):2d} Hintergründe, {len(videos):2d} Video-Spuren | Entwurf: {e_bilder:3d} Bilder, {e_video} Videos | Module: {','.join(module)}")
