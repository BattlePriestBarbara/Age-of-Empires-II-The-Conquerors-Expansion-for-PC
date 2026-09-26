"""Inspect the game folder for AI-related files (drs / per / ai / exe) and load lists."""
import os

ROOT = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"game_files_out.txt")
lines = []

interesting = (".drs", ".per", ".ai", ".ai2", ".exe", ".dll", ".dat", ".txt")
hits = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    if depth > 4:
        dirnames[:] = []
        continue
    for f in filenames:
        if f.lower().endswith(interesting):
            fp = os.path.join(dirpath, f)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                sz = -1
            hits.append((sz, os.path.join(rel, f)))

lines.append("=== interesting files (size, relpath), sorted by path ===")
for sz, p in sorted(hits, key=lambda x: x[1].lower()):
    lines.append("%10d  %s" % (sz, p))

lines.append("")
lines.append("=== .drs only ===")
for sz, p in sorted(hits, key=lambda x: x[1].lower()):
    if p.lower().endswith(".drs"):
        lines.append("%10d  %s" % (sz, p))

lines.append("")
lines.append("=== text previews of small AI-ish files ===")
for sz, p in sorted(hits, key=lambda x: x[1].lower()):
    base = os.path.basename(p)
    if base.lower() in ("ai.txt", "load.txt", "learn.txt", "random.txt", "support.txt", "avi.txt", "docs.txt") or p.lower().endswith((".per", ".ai", ".ai2")):
        fp = os.path.join(ROOT, p)
        try:
            raw = open(fp, "rb").read()
        except OSError as e:
            lines.append("ERR %s %s" % (p, e))
            continue
        lines.append("--- %s (%d bytes) ---" % (p, len(raw)))
        lines.append(repr(raw[:1500]))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
