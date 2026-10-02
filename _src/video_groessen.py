# Größen aller Videoquellen per HEAD, für die Entscheidung komprimieren oder verlinken. Autor: Vega, 02.10.2026
import json, urllib.request, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("D:/Claude/VS Code/brasseler/_src/data.json", encoding="utf-8"))
q = collections.OrderedDict()
for x in d:
    for b in x["bloecke"]:
        if b["t"] == "video":
            for s in b["src"]: q.setdefault(s, {"bg": b["bg"], "seiten": []})["seiten"].append(x["pfad"])
ges = 0
for s, v in q.items():
    try:
        r = urllib.request.urlopen(urllib.request.Request(s, method="HEAD", headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
        mb = int(r.headers.get("Content-Length", 0)) / 1e6
    except Exception as e: mb = -1
    ges += max(mb, 0)
    print(f"{mb:7.1f} MB  {'bg ' if v['bg'] else 'klk'}  {s.split('/')[-1][:55]:55s}  {len(v['seiten'])}x  {v['seiten'][0][:40]}")
print(f"gesamt {ges:.0f} MB, {len(q)} Dateien")
