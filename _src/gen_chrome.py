# -*- coding: utf-8 -*-
"""Einzige Quelle für Kopf (Head), Kopfleiste, mobiles Menü, Fußzeile und Demo-Leiste. Wird vom Generator in jede Seite
gesetzt; check.py misst, dass es über alle Seiten genau eine Kopf- und eine Fußvariante gibt.
Autor: Marketing Operations (Vega), 02.10.2026"""
import json, os
from gen_lib import e, VERSION, BASE, DEMO, json_ld
HERE = os.path.dirname(os.path.abspath(__file__))
chrome = json.load(open(os.path.join(HERE, "chrome.json"), encoding="utf-8"))
T = {
    "de": {"skip": "Zum Inhalt springen", "menu": "Menü", "lang_other": "en", "lang_label": "English", "suche": "Suche",
           "demo": "Unverbindlicher Redesign-Entwurf von Dr.-Ing. Suat Akyol, keine Seite der Gebr. Brasseler GmbH & Co. KG.",
           "anders": "Was ist anders?", "sitemap": "Sitemap", "original": "Originalseite", "zu": "Schließen",
           "social": "Brasseler in sozialen Netzwerken", "entwurf": "Über diesen Entwurf", "impressum": "Impressum", "fuss_hinweis": "Entwurf, Inhalte und Bilder aus brasseler.de, nicht indexiert."},
    "en": {"skip": "Skip to content", "menu": "Menu", "lang_other": "de", "lang_label": "Deutsch", "suche": "Search",
           "demo": "Non-binding redesign draft by Dr.-Ing. Suat Akyol, not a website of Gebr. Brasseler GmbH & Co. KG.",
           "anders": "What is different?", "sitemap": "Sitemap", "original": "Original site", "zu": "Close",
           "social": "Brasseler on social networks", "entwurf": "About this draft", "impressum": "Legal notice", "fuss_hinweis": "Draft, content and images from brasseler.de, not indexed."},
}
# Social-Zeichen: dieselben SVG-Pfade wie im Fuß des Bestands (social_quelle.py), Kachelfarben wie dort (Suat 02.10.2026)
SOCIAL = json.load(open(os.path.join(HERE, "social.json"), encoding="utf-8"))
SOCIAL_FARBE = {s["name"]: s["farbe"] for s in SOCIAL}  # Farben aus den Original-SVGs
KURVE = '<svg class="fuss__kurve" viewBox="0 0 1159 252" preserveAspectRatio="none" aria-hidden="true"><path d="M1 194.249c437.461 116.783 823.258 52.367 1157.391-193.249" stroke="#007fff" stroke-width="2" fill="none" vector-effect="non-scaling-stroke"/></svg>'
LOGO = '<svg class="logo" viewBox="0 0 220 44" aria-hidden="true"><text x="0" y="33" font-family="Fira Sans, Arial, sans-serif" font-weight="300" font-size="40" fill="currentColor">Brasseler<tspan fill="#007fff">.</tspan></text></svg>'
# Flaggen für den Sprachwechsel (Suat 02.10.2026): schlicht gezeichnet, 3:2
FLAGGE = {"de": '<svg class="flag" viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="2" fill="#000"/><rect y=".667" width="3" height="1.333" fill="#d00"/><rect y="1.333" width="3" height=".667" fill="#ffce00"/></svg>',
          "en": '<svg class="flag" viewBox="0 0 60 40" aria-hidden="true"><rect width="60" height="40" fill="#012169"/><path d="M0 0l60 40M60 0L0 40" stroke="#fff" stroke-width="8"/><path d="M0 0l60 40M60 0L0 40" stroke="#c8102e" stroke-width="3"/><path d="M30 0v40M0 20h60" stroke="#fff" stroke-width="12"/><path d="M30 0v40M0 20h60" stroke="#c8102e" stroke-width="7"/></svg>'}

def head(seite, r, lang, titel, desc, canonical_pfad, partner_pfad, ld, og_bild=""):
    """Kopf mit noindex (Demo), hreflang-Paar, Open Graph, JSON-LD, vorgeladener Schrift und CSS."""
    t = T[lang]
    alt = f'<link rel="alternate" hreflang="{"en" if lang == "de" else "de"}" href="{DEMO}{partner_pfad.strip("/")}{"/" if partner_pfad.strip("/") else ""}">' if partner_pfad else ""
    og = f'<meta property="og:image" content="{e(og_bild)}">' if og_bild else ""
    # Die 404-Seite liegt nicht unter /404/, also kein canonical und kein hreflang auf eine Adresse, die 404 gibt (Faber F4)
    kp = canonical_pfad.strip("/"); kanon = "" if kp == "404" else f'<link rel="canonical" href="{DEMO}{kp}{"/" if kp else ""}">\n<link rel="alternate" hreflang="{lang}" href="{DEMO}{kp}{"/" if kp else ""}">\n{alt}'
    return f'''<!DOCTYPE html>
<html lang="{lang}" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.classList.replace('no-js','has-js')</script>
<title>{e(titel)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="noindex, nofollow">
{kanon}
<meta property="og:type" content="website">
<meta property="og:title" content="{e(titel)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:locale" content="{"de_DE" if lang == "de" else "en_GB"}">
{og}
<meta name="theme-color" content="#007fff">
<link rel="icon" href="{r}media/favicon.svg" type="image/svg+xml">
<link rel="preload" as="font" type="font/woff2" href="{r}font/fira-sans-latin-400-normal.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="{r}font/fira-sans-latin-300-normal.woff2" crossorigin>
<link rel="stylesheet" href="{r}css/site.css?v={VERSION}">
{ld}
</head>'''

def kopfleiste(r, lang, aktiv_pfad, partner_pfad, hell=False):
    """Kopfleiste mit Hauptmenü (Untermenüs als Aufklapper), Sprachwechsel und mobilem Menü. Alles aus chrome.json."""
    t = T[lang]; nav = chrome[lang]["nav"]
    start = "/" if lang == "de" else "/en/"
    def aktiv(p): return ' aria-current="page"' if p == aktiv_pfad else (' data-zweig="1"' if p != start and aktiv_pfad.startswith(p) else "")
    def href(p): return r + p.strip("/") + ("/" if p.strip("/") else "")
    items = []; i = 0
    while i < len(nav):
        n = nav[i]
        if n["tiefe"] != 0: i += 1; continue
        kinder = []; j = i + 1
        while j < len(nav) and nav[j]["tiefe"] == 1: kinder.append(nav[j]); j += 1
        if kinder:
            items.append(f'<li class="nav__li nav__li--sub"><a class="nav__a" href="{href(n["pfad"])}"{aktiv(n["pfad"])}>{e(n["text"])}</a><button class="nav__plus" type="button" aria-expanded="false" aria-label="{e(n["text"])}: {t["menu"]}"><span></span></button><ul class="nav__sub">' + "".join(f'<li><a href="{href(k["pfad"])}"{aktiv(k["pfad"])}>{e(k["text"])}</a></li>' for k in kinder) + "</ul></li>")
        else:
            items.append(f'<li class="nav__li"><a class="nav__a" href="{href(n["pfad"])}"{aktiv(n["pfad"])}>{e(n["text"])}</a></li>')
        i = j
    sprache = href(partner_pfad) if partner_pfad else href("/en/" if lang == "de" else "/")
    sprach_titel = "" if partner_pfad else (' title="Diese Seite gibt es im Bestand nur auf Deutsch, der Wechsel führt zur englischen Startseite."' if lang == "de" else ' title="This page exists only in German on the original site; the switch leads to the German start page."')
    return f'''<a class="skip" href="#inhalt">{t["skip"]}</a>
<header class="nav{" nav--hell" if hell else ""}" id="nav">
  <div class="nav__in">
    <a class="nav__logo" href="{href(start)}">{LOGO.replace('aria-hidden="true"', 'role="img" aria-label="Brasseler"')}<span class="nav__claim">{"Medizintechnik made in Lemgo" if lang == "de" else "Medical technology made in Lemgo"}</span></a>
    <nav class="nav__menu" aria-label="{"Hauptnavigation" if lang == "de" else "Main navigation"}"><ul class="nav__ul">{"".join(items)}</ul></nav>
    <div class="nav__r">
      <a class="nav__lang" href="{sprache}" lang="{t["lang_other"]}" hreflang="{t["lang_other"]}"{sprach_titel}>{FLAGGE[t["lang_other"]]}<span>{t["lang_other"].upper()}</span></a>
      <button class="burger" id="burger" type="button" aria-expanded="false" aria-controls="mmenu" aria-label="{t["menu"]}"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<nav class="mmenu" id="mmenu" hidden aria-label="{t["menu"]}"><ul class="mmenu__ul">{"".join(items)}</ul><a class="mmenu__lang" href="{sprache}">{FLAGGE[t["lang_other"]]}<span>{t["lang_label"]}</span></a></nav>'''
# Das mobile Menü steht bewusst außerhalb des <header>: der Kopfbalken hat backdrop-filter, und der macht ihn zum
# Bezugsrahmen für position:fixed, das Menü wäre dann 76 px hoch (Befund Suat 02.10.2026, Handy-Screenshot).

def fuss(r, lang):
    t = T[lang]; links = chrome[lang]["fuss"]
    def href(p):
        if p in ("/impressum/", "/en/legal-notice/"): return r + ("impressum/" if lang == "de" else "en/legal-notice/")
        if p == "/gtcs/": p = "/en/gtcs/"
        return r + p.strip("/") + "/"
    social = "".join(f'<li><a class="fuss__s" style="--f:{SOCIAL_FARBE.get(s["name"], "#3b4248")}" href="{s["href"]}" target="_blank" rel="noopener" aria-label="{e(s["name"])}">{s["svg"]}</a></li>' for s in SOCIAL)
    return f'''<footer class="fuss">
  <div class="fuss__oben">
    {KURVE}
    <ul class="fuss__social" aria-label="{t["social"]}">{social}</ul>
    <img class="fuss__komet" src="{r}media/logo-kometdental-3.svg" alt="Komet" width="96" height="96">
  </div>
  <div class="fuss__in">
    <ul class="fuss__links">{"".join(f'<li><a href="{href(l["pfad"])}">{e(l["text"])}</a></li>' for l in links)}<li><a href="{r}ueber-diesen-entwurf/">{t["entwurf"]}</a></li></ul>
    <p class="fuss__hinweis">{t["fuss_hinweis"]} <a href="https://akyol.de/" target="_blank" rel="noopener">Dr.-Ing. Suat Akyol</a></p>
  </div>
</footer>'''

def demobar(r, lang):
    t = T[lang]
    return f'''<div class="demobar" id="demobar" role="note">
  <span class="demobar__t">{t["demo"]}</span>
  <span class="demobar__l"><a href="{r}ueber-diesen-entwurf/">{t["anders"]}</a><span aria-hidden="true"> · </span><a href="{r}sitemap/">{t["sitemap"]}</a><span aria-hidden="true"> · </span><a href="{BASE}/" target="_blank" rel="noopener">{t["original"]}</a></span>
  <button class="demobar__x" id="demoClose" type="button" aria-label="{t["zu"]}"><span aria-hidden="true">×</span></button>
</div>'''

def lightbox(lang):
    return f'''<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="{"Großansicht" if lang == "de" else "Enlarged view"}">
  <button class="lb__close" type="button" aria-label="{"Schließen" if lang == "de" else "Close"}"><span aria-hidden="true">×</span></button>
  <button class="lb__prev" type="button" aria-label="{"Voriges Bild" if lang == "de" else "Previous image"}"><span aria-hidden="true">‹</span></button>
  <img alt="">
  <button class="lb__next" type="button" aria-label="{"Nächstes Bild" if lang == "de" else "Next image"}"><span aria-hidden="true">›</span></button>
  <span class="lb__count"></span>
</div>'''

def ende(r):
    return f'<script src="{r}js/site.js?v={VERSION}" defer></script>\n</body>\n</html>\n'
