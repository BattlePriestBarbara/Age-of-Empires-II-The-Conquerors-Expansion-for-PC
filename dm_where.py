"""Where do the AI scripts live (which DRS), and where is cc-add-resource used?"""
import hashlib
import os

W = os.path.dirname(os.path.abspath(__file__))
DIRS = ["aok_drs", "x1_drs", "x1p1_drs"]
out = []

for d in DIRS:
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        out.append("MISSING DIR %s" % p)
        continue
    fs = sorted(f for f in os.listdir(p) if f.startswith("anib_") and f.endswith(".bin"))
    out.append("=== %s : %d anib files ===" % (d, len(fs)))
    for f in fs:
        fp = os.path.join(p, f)
        h = hashlib.md5(open(fp, "rb").read()).hexdigest()
        out.append("   %-18s %8d  %s" % (f, os.path.getsize(fp), h))

out.append("")
out.append("=== cc-add-resource occurrences (all dirs) ===")
for d in DIRS:
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        continue
    for f in sorted(os.listdir(p)):
        if not f.startswith("anib_"):
            continue
        raw = open(os.path.join(p, f), "rb").read()
        t = raw.decode("latin-1")
        if "cc-add-resource" in t:
            rows = t.split("\n")
            out.append("-- %s/%s : %d hits" % (d, f, t.count("cc-add-resource")))
            for i, r in enumerate(rows):
                if "cc-add-resource" in r:
                    s = i
                    while s > 0 and "(defrule" not in rows[s]:
                        s -= 1
                    for j in range(s, min(i + 2, len(rows))):
                        out.append("   %5d| %s" % (j + 1, rows[j].rstrip()))
                    out.append("")

open(os.path.join(W, "dm_where_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_where_out.txt", len(out), "lines")
