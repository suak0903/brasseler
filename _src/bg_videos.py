# Hintergrundvideos der Bestandsseite laden und wie das Startvideo verkleinern (720p, 12,5 fps, ohne Ton, MP4 und WebM,
# Poster). Klickvideos bleiben beim Original und laden erst beim Klick. Autor: Marketing Operations (Vega), 02.10.2026
import json, os, re, sys, subprocess, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "assets"); M = os.path.join(HERE, "..", "media")
d = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))
quellen = {}
for x in d:
    for b in x["bloecke"]:
        if b["t"] == "video" and b["bg"]:
            for s in b["src"]:
                if s.endswith(".mp4") and "420p" not in s: quellen.setdefault(s, []).append(x["pfad"])
karte = {}
for s, seiten in quellen.items():
    name = re.sub(r"[^A-Za-z0-9_-]", "_", s.split("/")[-1].rsplit(".", 1)[0]).lower()[:40]
    name = re.sub(r"^000_brasseler_2020-04(?:-22)?_", "", name).strip("_") or "bg"
    roh = os.path.join(A, name + "-roh.mp4")
    if not os.path.exists(roh):
        u = urllib.parse.quote(s, safe=":/")
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            open(roh, "wb").write(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            print("FEHLER", s[-50:], e); continue
    mp4, webm, poster = os.path.join(M, name + ".mp4"), os.path.join(M, name + ".webm"), os.path.join(M, name + "-poster.jpg")
    if not os.path.exists(mp4):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", roh, "-an", "-vf", "scale=1280:-2", "-r", "12.5", "-c:v", "libx264", "-preset", "slow", "-crf", "33", "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-map_metadata", "-1", mp4], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", roh, "-an", "-vf", "scale=1280:-2", "-r", "12.5", "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "42", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-map_metadata", "-1", webm], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", roh, "-frames:v", "1", "-vf", "scale=1600:-2", "-q:v", "3", poster], check=True)
    karte[s] = name
    print(f"{name}: roh {os.path.getsize(roh)/1e6:.1f} MB -> mp4 {os.path.getsize(mp4)/1e6:.2f} MB, webm {os.path.getsize(webm)/1e6:.2f} MB | {seiten[:2]}")
json.dump(karte, open(os.path.join(HERE, "video-map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
