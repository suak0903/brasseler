# -*- coding: utf-8 -*-
"""Sprachpaare in data.json neu zuordnen, ohne den Crawl oder die Extraktion zu wiederholen (nach Änderung an paare.py).
Aufruf: python paare_neu.py        Autor: Marketing Operations (Vega), 02.10.2026"""
import io, json, os
import paare
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "data.json")
daten = json.load(io.open(P, encoding="utf-8"))
vorher = {d["pfad"]: d["partner"] for d in daten}
paare.zuordnen(daten)
io.open(P, "w", encoding="utf-8").write(json.dumps(daten, ensure_ascii=False, indent=2))
neu = [(d["pfad"], d["partner"]) for d in daten if d["partner"] != vorher[d["pfad"]]]
print(len(neu), "Zuordnungen geändert")
for a, b in neu: print(" ", a, "->", b or "(keiner)")
ohne = [d["pfad"] for d in daten if d["lang"] == "de" and not d["partner"] and not d["duplikat_von"]]
print(len(ohne), "deutsche Seiten ohne Partner:", *ohne, sep="\n  ")
