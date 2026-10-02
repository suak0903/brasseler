#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hauptlauf des Generators: erzeugt aus data.json alle Seiten des Demonstrators (Startseite, Seiten, News, Chronik,
Weiterleitungen für Duplikate), dazu Sitemap-Seite, Hinweisseite, Impressum des Entwurfs, 404, sitemap.xml,
robots.txt, llms.txt. Aufruf: python gen.py        Autor: Marketing Operations (Vega), 02.10.2026"""
import os, re, json, html, sys, datetime
sys.stdout.reconfigure(encoding="utf-8")
from gen_lib import *
from gen_chrome import head, kopfleiste, fuss, demobar, lightbox, ende, T, chrome
import inhalt as I
HERE = os.path.dirname(os.path.abspath(__file__))
daten = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
by = {d["pfad"]: d for d in daten}
HEUTE = datetime.date.today().isoformat()
MESSUNG = json.load(open(os.path.join(HERE, "messung.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "messung.json")) else {}

# Hierarchie aus dem Menü: Elternseite je Pfad
eltern = {}
for lang in ("de", "en"):
    letzte = None
    for n in chrome[lang]["nav"]:
        if n["tiefe"] == 0: letzte = n["pfad"]
        else: eltern[n["pfad"]] = letzte
eltern["/karriere/studierende/abschlussarbeiten/"] = "/karriere/studierende/"
eltern["/en/careers/university-students/thesis-projects/"] = "/en/careers/university-students/"
NAVTEXT = {n["pfad"]: n["text"] for lang in ("de", "en") for n in chrome[lang]["nav"]}
PFADE = {d["pfad"] for d in daten if not d["duplikat_von"]} | {"/impressum/", "/en/legal-notice/", "/sitemap/", "/ueber-diesen-entwurf/"}
START = {"de": "/", "en": "/en/"}; NEWS = {"de": "/news/", "en": "/en/news/"}; CHRONIK = {"de": "/unternehmen/unsere-meilensteine/", "en": "/en/company/our-milestones/"}
TROPHAEE = "https://www.brasseler.de/uploads/t100_26_trophaee_rechts.png"
ORG = {"@type": "Organization", "@id": BASE + "/#organization", "name": "Gebr. Brasseler GmbH & Co. KG", "alternateName": "Brasseler", "brand": [{"@type": "Brand", "name": "Komet"}],
       "url": BASE + "/", "foundingDate": "1923", "numberOfEmployees": {"@type": "QuantitativeValue", "value": 1500},
       "address": {"@type": "PostalAddress", "streetAddress": "Trophagener Weg 25", "postalCode": "32657", "addressLocality": "Lemgo", "addressCountry": "DE"},
       "sameAs": ["https://www.linkedin.com/company/gebr.-brasseler-gmbh-&-co.-kg/", "https://www.xing.com/pages/gebr-brasseler", "https://www.kununu.com/de/gebr-brasseler", "https://www.facebook.com/Gebr.Brasseler", "https://www.instagram.com/vollbrasseler/"]}

def titel_rein(t):
    t = re.sub(r"\s*[|–-]\s*(Gebr\. )?Brasseler.*$", "", t); t = re.sub(r"^Brasseler\s*[|–-]\s*", "", t)
    return t.strip() or "Brasseler"
def seitentitel(d):
    for b in d["bloecke"]:
        if b["t"] in ("h1", "h2"): return b["x"].replace("\n", " ")
    return titel_rein(d["titel"])
def beschreibung(d):
    if d["desc"]: return d["desc"][:300]
    for b in d["bloecke"]:
        if b["t"] == "p" and len(b["x"].split()) > 8 and not re.fullmatch(r"[\d.]+", b["x"].strip()): return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", b["x"]).replace("**", "")[:300]
    return "Brasseler, Medizintechnik made in Lemgo."
def datum_fmt(iso, lang):
    if not iso: return ""
    y, m, dd = iso[:10].split("-"); return f"{dd}.{m}.{y}" if lang == "de" else f"{dd} {['','January','February','March','April','May','June','July','August','September','October','November','December'][int(m)]} {y}"
def erstes_bild(d):
    """Teaser- und Hero-Bild: Open-Graph-Bild, sonst das erste Querformat (Portraits der Zitatgeber überspringen)."""
    if d["og"] and media_basis.get(d["og"]): return d["og"]
    kandidaten = [b["src"] for b in d["bloecke"] if b["t"] == "img" and not ist_icon(b) and b["src"] != TROPHAEE]
    for src in kandidaten:
        w, h = bild_masse(media_basis.get(src, ""))
        if w and h and w / h >= 1.25: return src
    return kandidaten[0] if kandidaten else ""
def krumen(d, lang):
    p = d["pfad"]; k = [(T[lang]["skip"] and I.UI[lang]["start"], START[lang])]
    if d["typ"] == "post": k.append((I.UI[lang]["news"], NEWS[lang]))
    elif d["typ"] == "timeline-eintrag": k += [(NAVTEXT.get("/unternehmen/" if lang == "de" else "/en/company/", ""), "/unternehmen/" if lang == "de" else "/en/company/"), (I.UI[lang]["chronik"], CHRONIK[lang])]
    else:
        kette = []; e = eltern.get(p)
        while e and e not in START.values(): kette.insert(0, (NAVTEXT.get(e, e), e)); e = eltern.get(e)
        k += kette
    return k
def krumen_html(k, titel, r):
    return '<nav class="crumbs" aria-label="Pfad">' + "".join(f'<a href="{r}{p.strip("/")}{"/" if p.strip("/") else ""}">{e(t)}</a><span aria-hidden="true">›</span>' for t, p in k) + f'<strong>{e(titel)}</strong></nav>'
def ld_seite(d, lang, titel, desc, k, r):
    url = DEMO + d["pfad"].strip("/") + ("/" if d["pfad"].strip("/") else "")
    g = [ORG, {"@type": "WebSite", "@id": DEMO + "#website", "url": DEMO, "name": "Brasseler", "inLanguage": lang, "publisher": {"@id": BASE + "/#organization"}}]
    if d["typ"] == "post":
        g.append({"@type": "NewsArticle", "headline": titel, "description": desc, "datePublished": d["published"], "dateModified": d["modified"] or d["published"], "inLanguage": lang, "image": [DEMO + "media/" + media_basis[erstes_bild(d)] + "-1200.jpg"] if media_basis.get(erstes_bild(d)) else [], "author": {"@id": BASE + "/#organization"}, "publisher": {"@id": BASE + "/#organization"}, "mainEntityOfPage": url})
    else:
        g.append({"@type": "WebPage", "@id": url, "url": url, "name": titel, "description": desc, "inLanguage": lang, "isPartOf": {"@id": DEMO + "#website"}, "about": {"@id": BASE + "/#organization"}, "dateModified": d["modified"] or HEUTE})
    g.append({"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t, "item": DEMO + p.strip("/") + ("/" if p.strip("/") else "")} for i, (t, p) in enumerate(k + [(titel, d["pfad"])])]})
    if d["pfad"] in I.FAQ: g.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in I.FAQ[d["pfad"]]]})
    if d["pfad"] in ("/geschaeftsbereiche/", "/en/business-areas/"):
        g.append({"@type": "ItemList", "name": "Geschäftsbereiche" if lang == "de" else "Business areas", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Service", "name": n, "provider": {"@id": BASE + "/#organization"}, "audience": {"@type": "Audience", "audienceType": a}}} for i, (n, a) in enumerate([("Komet Dental", "Zahnärzte, Zahntechniker, Kieferchirurgen" if lang == "de" else "dentists, dental technicians, oral surgeons"), ("Komet Medical", "Medizintechnikunternehmen, Chirurgie, Implantologie" if lang == "de" else "medical device companies, surgery, implantology"), ("Komet Jewellery", "Schmuckindustrie" if lang == "de" else "jewellery industry")])]})
    return json_ld(g)

def rahmen(d_pfad, lang, titel, desc, partner, ld, innen, r, og="", hell=False, mit_lb=False, mit_demobar=True):
    return (head(None, r, lang, titel, desc, d_pfad, partner, ld, og) + "\n<body>\n" + kopfleiste(r, lang, d_pfad, partner, hell) + "\n<main id=\"inhalt\">\n" + innen + "\n</main>\n" + fuss(r, lang) + "\n" + (demobar(r, lang) if mit_demobar else '<script>document.body.classList.add("demobar-zu")</script>') + "\n" + (lightbox(lang) if mit_lb else "") + ende(r))

def schreiben(pfad, inhalt_html):
    z = ausgabe_pfad(pfad); os.makedirs(os.path.dirname(z), exist_ok=True); open(z, "w", encoding="utf-8").write(inhalt_html)

def hero_html(d, r, lang, titel, k, hat_badge, video, bild):
    kr = krumen_html(k, titel, r)
    badge = f'<div class="subhero__badge">{picture(TROPHAEE, "TOP 100 Innovator 2026", r, sizes="140px")}</div>' if hat_badge else ""
    if video and video in video_map:
        n = video_map[video]
        return f'<section class="subhero subhero--medium">{badge}<img class="subhero__bg" src="{r}media/{n}-poster.jpg" alt="" width="1600" height="900" fetchpriority="high"><video class="subhero__v" autoplay muted loop playsinline preload="none" {video_quellen(n, r)} aria-hidden="true"></video><div class="subhero__in">{kr}<h1>{e(titel)}</h1></div></section>'
    if bild and media_basis.get(bild):
        return f'<section class="subhero subhero--medium">{badge}{picture(bild, "", r, klasse="subhero__bg", eager=True, sizes="100vw")}<div class="subhero__in">{kr}<h1>{e(titel)}</h1></div></section>'
    return f'<section class="subhero subhero--text">{badge}<div class="subhero__in">{kr}<h1>{e(titel)}</h1></div></section>'

def seite_generisch(d):
    lang = d["lang"]; r = root(d["pfad"]); bl = list(d["bloecke"]); titel = seitentitel(d); k = krumen(d, lang)
    hat_badge = any(b["t"] == "img" and b["src"] == TROPHAEE for b in bl); bl = [b for b in bl if not (b["t"] == "img" and b["src"] == TROPHAEE)]
    video = next((b["src"][0] for b in bl[:3] if b["t"] == "video" and b["bg"]), None)
    if video: bl = [b for b in bl if not (b["t"] == "video" and b["bg"] and b["src"][0] == video)]
    # erste Überschrift wird H1 des Heros
    for i, b in enumerate(bl):
        if b["t"] in ("h1", "h2") and b["x"].replace("\n", " ") == titel: del bl[i]; break
    bild = None
    if d["typ"] == "post": bild = erstes_bild(d)
    if bild:
        for i, b in enumerate(bl):
            if b["t"] == "img" and b["src"] == bild: del bl[i]; break
    innen = hero_html(d, r, lang, titel, k, hat_badge, video, bild if d["typ"] == "post" else None)
    datum = f'<p class="datum">{I.UI[lang]["datum"]} {datum_fmt(d["published"], lang)}</p>' if d["typ"] == "post" and d["published"] else ""
    klasse = "chronik" if d["pfad"] in CHRONIK.values() else ""
    lang_hinweis = f'<p class="hinweis">{I.UI[lang]["nur_de"]}</p>' if lang == "de" and not d["partner"] and d["typ"] == "page" else ""
    faq = ""
    if d["pfad"] in I.FAQ:
        faq = '<section class="sektion sektion--grau"><div class="wrap schmal"><h2 class="t-h2">' + ("Häufige Fragen" if lang == "de" else "Frequently asked questions") + "</h2>" + "".join(f'<h3 class="t-h3">{e(q)}</h3><p>{e(a)}</p>' for q, a in I.FAQ[d["pfad"]]) + "</div></section>"
    weiter = ""
    if d["typ"] == "post": weiter = f'<nav class="weiter"><a href="{r}{NEWS[lang].strip("/")}/">‹ {I.UI[lang]["zurueck"]}</a></nav>'
    elif d["typ"] == "timeline-eintrag": weiter = f'<nav class="weiter"><a href="{r}{CHRONIK[lang].strip("/")}/">‹ {I.UI[lang]["chronik"]}</a></nav>'
    innen += f'<section class="sektion{" sektion--lang" if d["woerter"] > 900 else ""}"><div class="wrap"><div class="prosa {klasse}">{datum}{lang_hinweis}{bloecke_html(bl, r, PFADE, lang)}{weiter}</div></div></section>{faq}'
    desc = beschreibung(d)
    return rahmen(d["pfad"], lang, f"{titel} | Brasseler", desc, d["partner"], ld_seite(d, lang, titel, desc, k, r), innen, r, og=(DEMO + "media/" + media_basis[erstes_bild(d)] + "-1200.jpg") if media_basis.get(erstes_bild(d)) else "", mit_lb=("data-lb" in innen))

def startseite(d):
    lang = d["lang"]; r = root(d["pfad"]); bl = [b for b in d["bloecke"] if not (b["t"] == "img" and b["src"] == TROPHAEE) and not (b["t"] == "video" and b["bg"])]
    KONTEXT["r"], KONTEXT["pfade"] = r, PFADE
    u = I.UI[lang]; titel = "Brasseler, Medizintechnik made in Lemgo" if lang == "de" else "Brasseler, medical technology made in Lemgo"
    h1 = next((b["x"] for b in bl if b["t"] == "h1"), titel); claim = h1.split("–")[-1].strip() if "–" in h1 else ("Medizintechnik made in Lemgo." if lang == "de" else "Medical technology made in Lemgo.")
    # Sektionen aus der Blockfolge
    intro = []; i = next((j for j, b in enumerate(bl) if b["t"] == "h1"), 0) + 1
    while i < len(bl) and bl[i]["t"] == "p": intro.append(bl[i]); i += 1
    luft = bl[i]["src"] if i < len(bl) and bl[i]["t"] == "img" else None; i += 1 if luft else 0
    teaser = []; film = None; zahlen = []; karte = None; azubi = None; karten2 = []
    while i < len(bl):
        b = bl[i]
        if ist_kurz(b) and i + 2 < len(bl) and bl[i + 1]["t"] == "p" and bl[i + 2]["t"] in ("img", "video"):
            m = bl[i + 2]
            if m["t"] == "video": film = (b["x"], bl[i + 1]["x"], m)
            else: teaser.append((b["x"], bl[i + 1]["x"], m["src"]))
            i += 3; continue
        if b["t"] == "zahl": zahlen.append(b); i += 1; continue
        if b["t"] == "p" and i + 1 < len(bl) and bl[i + 1]["t"] == "button":
            if karte is None: karte = (b["x"], bl[i + 1])
            else: azubi = (b["x"], bl[i + 1])
            i += 2; continue
        if b["t"] == "h2" and i + 1 < len(bl) and bl[i + 1]["t"] == "button": karten2.append((b["x"], bl[i + 1])); i += 2; continue
        i += 1
    ziel = {}
    for kick, lead, src in teaser:
        for n in chrome[lang]["nav"]:
            if n["tiefe"] == 0 and (n["text"].split()[-1].lower()[:5] in kick.lower()): ziel[kick] = n["pfad"]
    def pf(p): return r + p.strip("/") + ("/" if p.strip("/") else "")
    hs = [f'<section class="hero"><picture><source type="image/webp" srcset="{r}media/start-poster-480.webp 480w, {r}media/start-poster-960.webp 960w, {r}media/start-poster-1600.webp 1600w" sizes="100vw"><img class="hero__p" src="{r}media/start-poster-1200.jpg" alt="" width="1600" height="900" fetchpriority="high"></picture><video class="hero__v" autoplay muted loop playsinline preload="none" {video_quellen("start_1920_12fr", r)} aria-hidden="true"></video>'
          f'<h2 class="sr">{e(h1)}</h2>'
          f'<div class="hero__badge">{picture(TROPHAEE, "TOP 100 Innovator 2026", r, sizes="180px", eager=True)}</div></section>']
    hs.append(f'<section class="sektion"><div class="wrap schmal prosa rv"><h1 class="t-h2">{e(h1)}</h1>{"".join(f"<p>{inline_html(p[chr(120)])}</p>" for p in intro)}</div>' + (f'<div class="wrap rv"><figure class="bild">{picture(luft, "Brasseler in Lemgo, Luftbild" if lang == "de" else "Brasseler in Lemgo, aerial view", r)}</figure></div>' if luft else "") + "</section>")
    if film:
        kick, lead, m = film; poster = "https://www.brasseler.de/uploads/BRASSELER_23_2473_Imagefilm_1080p_thumbnail-2025.jpg"
        hs.append(f'<section class="sektion sektion--grau"><div class="wrap rv"><div class="sek"><p class="kicker">{e(kick)}</p><p class="lead">{inline_html(lead)}</p></div><figure class="vid vid--klick"><video class="vid__v" controls preload="none" poster="{r}media/{media_basis.get(poster, "")}-1200.jpg">' + "".join(f'<source src="{e(s)}" type="video/{"webm" if s.endswith("webm") else "mp4"}">' for s in m["src"]) + f'</video><figcaption class="vid__c">{u["video_hinweis"]}</figcaption></figure></div></section>')
    if teaser:
        hs.append('<section class="sektion"><div class="wrap"><div class="teaser">' + "".join(f'<a class="teaser__i rv" href="{pf(ziel.get(kick, START[lang]))}"><p class="kicker">{e(kick)}</p><p class="lead">{inline_html(lead)}</p>{picture(src, "", r, sizes="(max-width: 860px) 100vw, 380px")}</a>' for kick, lead, src in teaser) + "</div></div></section>")
    if zahlen:
        def teile(z):
            m = re.match(r"\s*([\d.,+]+)\s*(.*)", z["zahl"]); zahl = m.group(1) if m else z["zahl"]; einheit = z["einheit"] or (m.group(2) if m else "")
            return zahl, einheit
        hs.append(f'<section class="sektion sektion--grau"><div class="wrap rv"><p class="kicker">{e(u["zahlen"])}</p><div class="zahlen">' + "".join(f'<div class="zahlen__i"><div class="zahlen__z">{e(teile(z)[0])}</div><div class="zahlen__e">{e(teile(z)[1])}</div><p class="zahlen__s">{e(z["x"][len(z["zahl"]) + len(z["einheit"]) + 2:].strip() if z["x"].startswith(z["zahl"]) else z["x"])}</p></div>' for z in zahlen) + "</div></div></section>")
    if karte:
        hs.append(f'<section class="sektion"><div class="wrap karte rv"><img class="karte__svg" src="{r}media/brasseler-world-map-2.svg" alt="{"Weltkarte mit den Standorten der Brasseler-Gruppe" if lang == "de" else "World map with the locations of the Brasseler group"}" width="1200" height="600" loading="lazy"><div class="karte__t"><p class="lead">{inline_html(karte[0])}</p><a class="btn" href="{link_lokal(karte[1]["href"], r, PFADE)}">{e(karte[1]["x"])}</a></div></div></section>')
    if azubi:
        hs.append(f'<section class="banner rv">{picture("https://www.brasseler.de/uploads/brasseler-home-azubis.jpg", "", r, sizes="50vw")}<div class="banner__t"><p class="lead">{inline_html(azubi[0])}</p><a class="btn" href="{link_lokal(azubi[1]["href"], r, PFADE)}">{e(azubi[1]["x"])}</a></div></section>')
    if karten2:
        bilder = ["https://www.brasseler.de/uploads/IMAG_20190930_56_2Pers-Monitor-Besp_902.jpg", "https://www.brasseler.de/uploads/brasseler-home-nachhaltigkeit-2.jpg"]
        hs.append('<section class="sektion"><div class="wrap"><div class="karten2">' + "".join(f'<div class="karten2__i{" karten2__i--dunkel" if j == 0 else ""} rv"><div class="karten2__t"><h2>{inline_html(t)}</h2><a class="btn" href="{link_lokal(btn["href"], r, PFADE)}">{e(btn["x"])}</a></div>{picture(bilder[j % 2], "", r, sizes="(max-width: 1000px) 50vw, 300px")}</div>' for j, (t, btn) in enumerate(karten2)) + "</div></div></section>")
    k = []; desc = beschreibung(d)
    return rahmen(d["pfad"], lang, titel, desc, d["partner"], ld_seite(d, lang, titel, desc, k, r), "\n".join(hs), r, og=DEMO + "media/start_1920_12fr-poster.jpg")

def news_uebersicht(d):
    lang = d["lang"]; r = root(d["pfad"]); u = I.UI[lang]; titel = seitentitel(d); k = krumen(d, lang)
    posts = sorted([p for p in daten if p["typ"] == "post" and p["lang"] == lang and not p["duplikat_von"]], key=lambda p: p["published"], reverse=True)
    # Teaser-Bilder der Bestands-Übersicht (Bild vor der Überschrift) den Beiträgen per Titel zuordnen
    teaserbild = {}; letztes = None
    for b in d["bloecke"]:
        if b["t"] == "img" and not ist_icon(b): letztes = b["src"]
        elif b["t"] == "h3" and letztes: teaserbild[b["x"].strip().lower()[:40]] = letztes; letztes = None
    def bild_fuer(p): return teaserbild.get(seitentitel(p).strip().lower()[:40]) or erstes_bild(p)
    def teaser(p):
        for b in p["bloecke"]:
            if b["t"] == "p" and len(b["x"].split()) > 10: return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", b["x"]).replace("**", "")
        return ""
    karten = "".join(f'<a class="news__i rv" href="{r}{p["pfad"].strip("/")}/">' + (picture(bild_fuer(p), "", r, sizes="(max-width: 860px) 100vw, 380px") if media_basis.get(bild_fuer(p)) else f'<img src="{r}media/start-poster-960.webp" alt="" loading="lazy" width="960" height="540">') + f'<p class="news__d">{datum_fmt(p["published"], lang)}</p><h2 class="news__h">{e(seitentitel(p))}</h2><p class="news__p">{e(teaser(p))}</p></a>' for p in posts)
    bl = d["bloecke"]; j = next((i for i, b in enumerate(bl) if b["t"] == "p" and ("Pressekontakt" in b["x"] or "Press contact" in b["x"] or "press contact" in b["x"].lower())), None)
    presse = ""
    if j is not None:
        pb = [b for b in bl[max(0, j - 1):] if b["t"] in ("p", "img")]
        presse = f'<section class="sektion sektion--grau"><div class="wrap schmal prosa">{bloecke_html(pb, r, PFADE, lang)}</div></section>'
    innen = hero_html(d, r, lang, titel, k, False, None, None) + f'<section class="sektion"><div class="wrap"><p class="hinweis">{len(posts)} {"Beiträge" if lang == "de" else "articles"}</p><div class="news">{karten}</div></div></section>' + presse
    desc = beschreibung(d)
    return rahmen(d["pfad"], lang, f"{titel} | Brasseler", desc, d["partner"], ld_seite(d, lang, titel, desc, k, r), innen, r)

def weiterleitung(d):
    ziel = d["duplikat_von"]; r = root(d["pfad"]); lang = "en"
    return f'<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow"><meta http-equiv="refresh" content="0; url={r}{ziel.strip("/")}/"><title>Redirect</title></head><body><p>{I.UI[lang]["weiterleitung"]} <a href="{r}{ziel.strip("/")}/">{ziel}</a></p></body></html>'

def ampel(a, b):
    """a deutsch, b englisch (eines darf fehlen). Rot nur für wirklich leer, Duplikat oder Weiterleitung;
    kurze Einträge sind grün, wenn beide Sprachen da sind (Hinweis Faber F3)."""
    for x in (a, b):
        leer = x and x["woerter"] < 15 and not any(b["t"] == "button" for b in x["bloecke"])  # Download-Seiten (AGB) sind nicht leer
        if x and (leer or x["duplikat_von"]): return "rot"
    if not a or not b: return "gelb"
    lo, hi = min(a["woerter"], b["woerter"]), max(a["woerter"], b["woerter"])
    if lo < 0.6 * hi and hi - lo > 40: return "gelb"
    return "gruen"

def sitemap_seite(lang):
    s = I.SITEMAP[lang]; r = root("/sitemap/" if lang == "de" else "/en/sitemap/"); u = I.UI[lang]
    def zeile(a, b, ebene=0):
        amp = ampel(a, b); de = a; en = b
        def links(x, l):
            if not x: return f'<span class="sm__o">{s["fehlt"]}</span>'
            if x["duplikat_von"]: return f'<span class="sm__o">{s["dup"]} → {e(x["duplikat_von"])}</span>'
            return f'<a href="{r}{x["pfad"].strip("/")}{"/" if x["pfad"].strip("/") else ""}">{e(seitentitel(x))}</a> <span class="sm__o">({x["woerter"]} {s["woerter"]})</span>'
        def orig(x): return f'<a href="{e(x["url"])}" target="_blank" rel="noopener">{e(x["pfad"])}</a>' if x else "–"
        return f'<li class="sm__r sm__ebene-{ebene}"><span class="amp amp--{amp}" title="{amp}"></span><span>{s["de"]}: {links(de, "de")}<br>{s["en"]}: {links(en, "en")}</span><span class="sm__o">{orig(de)}<br>{orig(en)}</span><span class="sm__o">{amp}</span></li>'
    gruppen = []
    # Seiten in Menüreihenfolge (deutsch), englische Partner daneben; danach englische ohne deutsches Pendant
    seiten = []; gesehen = set()
    for n in chrome["de"]["nav"]:
        d = by.get(n["pfad"]);
        if not d: continue
        p = by.get(d["partner"]); seiten.append(zeile(d, p, n["tiefe"])); gesehen.update({d["pfad"], d["partner"]})
    for d in daten:
        if d["typ"] == "page" and d["pfad"] not in gesehen and not d["duplikat_von"] and d["pfad"] not in START.values():
            a, b = (d, by.get(d["partner"])) if d["lang"] == "de" else (by.get(d["partner"]), d); seiten.append(zeile(a, b)); gesehen.update({d["pfad"], d["partner"]})
    for d in daten:
        if d["duplikat_von"]: seiten.append(zeile(None, d))
    gruppen.append((s["seiten"], seiten))
    for typ, name in (("post", s["news"]), ("timeline-eintrag", s["chronik"])):
        zeilen = []; gesehen = set()
        for d in sorted([x for x in daten if x["typ"] == typ], key=lambda x: (x["published"] or x["modified"]), reverse=True):
            if d["pfad"] in gesehen or d["duplikat_von"]: continue  # Duplikate stehen gesammelt im Block oben
            a, b = (d, by.get(d["partner"])) if d["lang"] == "de" else (by.get(d["partner"]), d); zeilen.append(zeile(a, b)); gesehen.update({d["pfad"], d["partner"]})
        gruppen.append((name, zeilen))
    kopf = f'<li class="sm__r sm__r--kopf"><span></span><span>{s["kopf"][1]}</span><span>{s["kopf"][2]}</span><span>{s["kopf"][3]}</span></li>'
    innen = f'<section class="subhero subhero--text"><div class="subhero__in"><nav class="crumbs"><a href="{r}{START[lang].strip("/")}{"/" if START[lang].strip("/") else ""}">{u["start"]}</a><span aria-hidden="true">›</span><strong>{s["titel"]}</strong></nav><h1>{s["titel"]}</h1></div></section><section class="sektion"><div class="wrap"><p>{s["intro"]}</p><p class="legende">' + "".join(f'<span><span class="amp amp--{a}"></span>{t}</span>' for a, t in s["legende"]) + "</p>" + "".join(f'<div class="sm__g"><h2>{n} ({len(z)})</h2><ul class="sm">{kopf}{"".join(z)}</ul></div>' for n, z in gruppen) + "</div></section>"
    pfad = "/sitemap/" if lang == "de" else "/en/sitemap/"
    return rahmen(pfad, lang, s["titel"] + " | Brasseler", s["intro"], "/en/sitemap/" if lang == "de" else "/sitemap/", json_ld([ORG]), innen, r if lang == "de" else root(pfad))

def hinweisseite():
    r = root("/ueber-diesen-entwurf/"); lang = "de"; m = MESSUNG
    def kachel(l, alt, neu): return f'<div class="mess__i"><p class="mess__l">{l}</p><p class="mess__alt">{alt}</p><p class="mess__neu">{neu}</p></div>'
    mess = ""
    if m:
        mess = '<h2 class="t-h2">Gemessen, nicht geschätzt</h2><p>Lighthouse mobil, beide Seiten mit derselben Methode am selben Tag. Links der Wert der Bestandsseite, rechts der Entwurf.</p><div class="mess">' + "".join(kachel(l, m["alt"].get(k, "–"), m["neu"].get(k, "–")) for k, l in [("perf", "Leistung mobil (0 bis 100)"), ("lcp", "Hauptbild sichtbar"), ("tbt", "Blockierzeit"), ("cls", "Layoutsprünge"), ("bytes", "Datenmenge Startseite"), ("req", "Anfragen Startseite")]) + f'</div><p class="hinweis">Stand {m.get("datum", HEUTE)}. Bestand: {m["alt"].get("quelle", "")}. Entwurf: {m["neu"].get("quelle", "")}.</p>'
    PAARE = sum(1 for d in daten if d["lang"] == "de" and d["partner"] and not d["duplikat_von"])  # gezählt, nicht getippt
    befunde = [
        ("Sitemap zeigt auf den falschen Server", "Die Seiten- und Chronik-Sitemap von brasseler.de nennt als Adresse brasselerhomepageprod.azurewebsites.net, einen Azure-Host, statt www.brasseler.de. Suchmaschinen bekommen so die falschen Adressen gemeldet."),
        ("Die Seite existiert zweimal", "Der Azure-Host ist öffentlich erreichbar und liefert dieselben Seiten. Dazu liegen fünf englische Seiten zusätzlich unter deutschem Pfad, vier Seiten und eine News (zum Beispiel /careers/ und /en/careers/). Für Suchmaschinen ist das doppelter Inhalt."),
        ("Kein Sprachwechsel je Seite", f"Der Umschalter Deutsch/Englisch führt immer zur Startseite der anderen Sprache, und hreflang-Angaben fehlen. Dieser Entwurf verbindet {PAARE} Seitenpaare direkt miteinander."),
        ("Bilder vom Entwicklungs-Server", "Rund 70 Bilder (326 Verweise samt Größenvarianten auf 61 Seiten, vor allem der Chronik) werden von einem Azure-Entwicklungs-Slot geladen, nicht von brasseler.de."),
        ("PHP ohne Sicherheitsupdates", "Der Server meldet PHP 7.4.30. Diese Version bekommt seit November 2022 keine Sicherheitsupdates mehr."),
        ("Ladeleistung", "Ein Startseiten-Video mit 10 MB im Autoplay, Bilder in Originalgröße, Cookie-Banner und Tag Manager mit rund 400 KB Skripten und der Divi-Baukasten. Mobil Leistung 12 von 100, das Hauptbild erscheint nach über 10 Sekunden."),
        ("Strukturierte Daten", "Das Schema nennt nur Seite, Website und Organisation ohne Anschrift, Kontakt, Gründungsjahr oder Marke; kein FAQ, keine Artikel, das Logo in der E-Mail-Variante. KI-Suchen finden so wenig zum Zitieren."),
    ]
    anders = [("Technik", "WordPress mit Divi-Baukasten, 25 Skripte, 5 bis 8 MB je Lauf", "Statisches HTML, ein Stylesheet, ein Skript, Bilder als WebP in drei Größen"),
              ("Video", "10 MB Autoplay", "Dieselbe Szene, 1,5 MB, lädt erst, wenn sie im Bild ist"),
              ("Sprachen", "Umschalter führt zur Startseite", "Jede Seite kennt ihr Gegenstück, hreflang gesetzt"),
              ("Auffindbarkeit", "Schema ohne Anschrift, Marke, FAQ", "Organisation vollständig, Breadcrumbs, News als Artikel, FAQ, Geschäftsbereiche als Leistungen, llms.txt"),
              ("Cookies", "Banner und Tag Manager vor dem Inhalt", "Keine Verfolgung, kein Banner nötig"),
              ("Schrift", "Corporate S OT (lizenzpflichtig)", "Fira Sans, frei lizenziert (OFL), ähnlicher Charakter: schlicht, ohne Serifen, gut lesbar")]
    innen = f'''<section class="subhero subhero--text"><div class="subhero__in"><nav class="crumbs"><a href="{r}">Start</a><span aria-hidden="true">›</span><strong>{I.HINWEIS_TITEL}</strong></nav><h1>{I.HINWEIS_TITEL}</h1></div></section>
<section class="sektion"><div class="wrap schmal prosa">
<p class="lead" style="max-width:none">{I.HINWEIS_INTRO}</p>
<div class="kasten"><p><strong>Bitte beachten.</strong> {I.HINWEIS_BITTE}</p></div>
<h2 class="t-h2">Was dieser Entwurf ist</h2>
<p>Dieselben Inhalte wie brasseler.de, neu gebaut: alle 41 Seiten des Bestands, wo vorhanden in beiden Sprachen, alle 124 News, die Chronik mit 42 Einträgen, Videos, Bilder. Nichts ist weggelassen, nichts dazuerfunden. Die <a href="{r}sitemap/">Sitemap</a> zeigt jede Seite mit Link auf den Entwurf und auf das Original.</p>
{mess}
<h2 class="t-h2">Was ist anders</h2>
<table class="cmp"><thead><tr><th>Merkmal</th><th>Bestandsseite</th><th>Dieser Entwurf</th></tr></thead><tbody>{"".join(f'<tr><td data-l="Merkmal"><strong>{a}</strong></td><td data-l="Bestand">{b}</td><td data-l="Entwurf">{c}</td></tr>' for a, b, c in anders)}</tbody></table>
<h2 class="t-h2">Was mir beim Bestand aufgefallen ist</h2>
<p>Gemessen am {HEUTE[8:10]}.{HEUTE[5:7]}.{HEUTE[:4]} an der Live-Seite. Keine Geschmacksfragen, sondern Dinge, die sich nachprüfen lassen.</p>
<div class="hin">{"".join(f'<div class="hin__i"><h3>{t}</h3><p>{x}</p></div>' for t, x in befunde)}</div>
<h2 class="t-h2">Gestaltung</h2>
<p>Die Marke bleibt: das Brasseler-Blau, die Wortmarke mit dem Punkt, viel Weiß, die blaue Linie über jedem Abschnitt. Neu ist nur, dass alles aus einem Guss ist.</p>
<div class="ds"><div class="ds__f"><div class="ds__c" style="background:#007fff"></div>Brasseler-Blau #007fff</div><div class="ds__f"><div class="ds__c" style="background:#0062c4"></div>Blau dunkel #0062c4</div><div class="ds__f"><div class="ds__c" style="background:#3b4248"></div>Anthrazit #3b4248</div><div class="ds__f"><div class="ds__c" style="background:#f2f3f4"></div>Hellgrau #f2f3f4</div></div>
<p><strong>Schrift:</strong> Der Bestand nutzt Corporate S OT, eine Schrift, für die eine Lizenz nötig ist. Dieser Entwurf setzt Fira Sans, frei lizenziert und selbst gehostet. Sie hat denselben Charakter: schlicht, ohne Serifen, offen und gut lesbar, mit einem leichten Schnitt für die großen Überschriften.</p>
<h2 class="t-h2">Über mich</h2>
<p>Ich bin Dr.-Ing. Suat Akyol, Interim Manager für Transformation mit KI, mit 18 Jahren Linienverantwortung in einem Medizintechnik- und Industriekonzern. Diesen Entwurf habe ich an einem Abend mit KI-Werkzeugen gebaut, so wie ich im Betrieb arbeite: Bewährtes, mit KI viel schneller. Mehr auf <a href="https://akyol.de/" target="_blank" rel="noopener">akyol.de</a>.</p>
<p><a class="btn" href="mailto:contact@akyol.de?subject=Brasseler-Entwurf">Anmerkungen an contact@akyol.de</a></p>
</div></section>'''
    return rahmen("/ueber-diesen-entwurf/", lang, I.HINWEIS_TITEL + " | Brasseler-Entwurf", I.HINWEIS_INTRO[:200], "", json_ld([ORG]), innen, r, mit_demobar=False)

def kleine_seite(pfad, lang, titel, text, partner=""):
    r = root(pfad)
    innen = f'<section class="subhero subhero--text"><div class="subhero__in"><nav class="crumbs"><a href="{r}{START[lang].strip("/")}{"/" if START[lang].strip("/") else ""}">{I.UI[lang]["start"]}</a><span aria-hidden="true">›</span><strong>{e(titel)}</strong></nav><h1>{e(titel)}</h1></div></section><section class="sektion"><div class="wrap schmal prosa"><p>{e(text)}</p><p><a href="https://akyol.de/impressum.html" target="_blank" rel="noopener">akyol.de/impressum</a> · <a href="{BASE}/impressum/" target="_blank" rel="noopener">brasseler.de/impressum</a></p></div></section>'
    return rahmen(pfad, lang, f"{titel} | Brasseler", text[:160], partner, json_ld([ORG]), innen, r)

# ---------------------------------------------------------------- Lauf
if os.path.exists(os.path.join(HERE, "..", "media")) and not video_map: print("Hinweis: video-map.json fehlt, Hintergrundvideos werden als Poster gezeigt")
zaehler = {"seiten": 0, "weiter": 0}
for d in daten:
    if d["duplikat_von"]: schreiben(d["pfad"], weiterleitung(d)); zaehler["weiter"] += 1; continue
    if d["pfad"] in START.values(): h = startseite(d)
    elif d["pfad"] in NEWS.values(): h = news_uebersicht(d)
    else: h = seite_generisch(d)
    schreiben(d["pfad"], h); zaehler["seiten"] += 1
for lang in ("de", "en"): schreiben("/sitemap/" if lang == "de" else "/en/sitemap/", sitemap_seite(lang))
schreiben("/ueber-diesen-entwurf/", hinweisseite())
schreiben("/impressum/", kleine_seite("/impressum/", "de", *I.IMPRESSUM["de"], partner="/en/legal-notice/"))
schreiben("/en/legal-notice/", kleine_seite("/en/legal-notice/", "en", *I.IMPRESSUM["en"], partner="/impressum/"))
open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(kleine_seite("/404/", "de", *I.NICHT_GEFUNDEN["de"]).replace('href="../', 'href="/brasseler/').replace('src="../', 'src="/brasseler/'))
alle = sorted(PFADE | {"/en/sitemap/"})
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f'  <url><loc>{DEMO}{p.strip("/")}{"/" if p.strip("/") else ""}</loc><lastmod>{HEUTE}</lastmod></url>\n' for p in alle) + "</urlset>\n")
open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write("User-agent: *\nDisallow: /\n")
open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write(f"# Brasseler, Redesign-Entwurf (nicht die offizielle Website)\n\nUnverbindlicher Entwurf von Dr.-Ing. Suat Akyol (https://akyol.de/), gebaut am {HEUTE} aus den öffentlichen Inhalten von https://www.brasseler.de/. Für Suchmaschinen und KI-Suche gesperrt. Die offizielle Website ist https://www.brasseler.de/.\n\n- Über den Entwurf: {DEMO}ueber-diesen-entwurf/\n- Sitemap des Entwurfs: {DEMO}sitemap/\n")
print(f'{zaehler["seiten"]} Seiten, {zaehler["weiter"]} Weiterleitungen, 2 Sitemap-Seiten, Hinweisseite, 2 Impressum, 404, sitemap.xml, robots.txt, llms.txt')
