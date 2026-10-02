# -*- coding: utf-8 -*-
"""Sprachpaare und Duplikate: feste Zuordnung für die 41 Seiten (aus den Adressen eindeutig), strenge Heuristik für
News und Chronik (gleiches Bild oder gemeinsame Bilder, oder gleiches Datum plus Slug-Treffer). Vier englische Seiten
liegen im Bestand zusätzlich unter deutschem Pfad; sie werden als Duplikat markiert und nicht gebaut, sondern leiten
auf die /en/-Fassung. Wird von extract.py am Ende aufgerufen. Autor: Marketing Operations (Vega), 02.10.2026"""
import re
SEITEN = {  # de -> en
    "/": "/en/", "/unternehmen/": "/en/company/", "/unternehmen/gesellschafterkreis/": "/en/company/shareholders/",
    "/unternehmen/management/": "/en/company/management/", "/unternehmen/unsere-werte/": "/en/company/our-values/",
    "/unternehmen/unsere-verantwortung/": "/en/company/our-responsibility/", "/unternehmen/unsere-meilensteine/": "/en/company/our-milestones/",
    "/unternehmen/brasseler-100-years/": "/en/company/brasseler-100-years/", "/geschaeftsbereiche/": "/en/business-areas/",
    "/international/": "/en/international/", "/karriere/": "/en/careers/", "/karriere/studierende/": "/en/careers/university-students/",
    "/karriere/studierende/abschlussarbeiten/": "/en/careers/university-students/thesis-projects/", "/news/": "/en/news/",
    "/zertifikate/": "/en/certificates/", "/agb/": "/en/gtcs/", "/datenschutz/": "/en/data-protection/", "/verhaltenskodex/": "/en/code-of-conduct/",
}
DUPLIKATE = {"/careers/": "/en/careers/", "/certificates/": "/en/certificates/", "/gtcs/": "/en/gtcs/", "/thesis-projects/": "/en/careers/university-students/thesis-projects/"}
OHNE_PARTNER = {"/karriere/ausbildung/"}  # nur deutsch im Bestand

def slug_tokens(p): return set(t for t in re.split(r"[/\-]+", p.replace("/en/", "/").replace("/timeline-eintrag/", "/")) if len(t) > 3 and not t.isdigit())
def score(a, b):
    s = 0; grund = []
    if a["og"] and a["og"] == b["og"]: s += 4; grund.append("og")
    gem = len(set(a["bilder"]) & set(b["bilder"]))
    if gem: s += min(3, gem); grund.append("bilder%d" % gem)
    if a["published"] and a["published"] == b["published"]: s += 2; grund.append("datum")
    if abs(a["pos"] - b["pos"]) <= 2: s += 1; grund.append("nachbar")
    st = len(slug_tokens(a["pfad"]) & slug_tokens(b["pfad"]))
    if st: s += min(2, st); grund.append("slug%d" % st)
    zahlen = set(re.findall(r"\d{2,}", a["titel"])) & set(re.findall(r"\d{2,}", b["titel"]))
    if zahlen: s += 1; grund.append("zahl")
    sicher = ("og" in grund) or (gem >= 1) or ("datum" in grund and st >= 1) or (st >= 2 and "nachbar" in grund)
    return (s if sicher else 0), grund

def zuordnen(daten):
    by = {d["pfad"]: d for d in daten}
    for d in daten: d["partner"] = ""; d["partner_score"] = 0; d["partner_grund"] = []; d["duplikat_von"] = DUPLIKATE.get(d["pfad"], "")
    for de, en in SEITEN.items():
        if de in by and en in by: by[de]["partner"], by[en]["partner"] = en, de; by[de]["partner_score"] = by[en]["partner_score"] = 9; by[de]["partner_grund"] = by[en]["partner_grund"] = ["fest"]
    rest_de = [d for d in daten if d["lang"] == "de" and d["typ"] != "page" and not d["partner"] and not d["duplikat_von"]]
    rest_en = [d for d in daten if d["lang"] == "en" and d["typ"] != "page" and not d["partner"]]
    kand = sorted(((score(a, b), a["pfad"], b["pfad"]) for a in rest_de for b in rest_en if a["typ"] == b["typ"]), key=lambda k: -k[0][0])
    vergeben = set()
    for (s, grund), pa, pb in kand:
        if s < 3 or pa in vergeben or pb in vergeben: continue
        by[pa]["partner"], by[pb]["partner"] = pb, pa; by[pa]["partner_score"] = by[pb]["partner_score"] = s; by[pa]["partner_grund"] = by[pb]["partner_grund"] = grund; vergeben.update((pa, pb))
    return daten
