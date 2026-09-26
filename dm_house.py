"""Do the DM-relevant scripts build houses / manage pop limit?"""
import os

W = os.path.dirname(os.path.abspath(__file__))
DM_FILES = [60027, 60010, 60013, 60007, 60022, 60023, 60002, 60019, 60016, 60026]
out = []


def load(idx, d="x1_drs"):
    p = os.path.join(W, d, "anib_%d.bin" % idx)
    if not os.path.exists(p):
        return None
    return open(p, "rb").read().decode("latin-1")


out.append("=== (build house) rules with their conditions, per DM-loaded file ===")
for idx in DM_FILES:
    t = load(idx)
    if t is None:
        out.append("anib_%d missing" % idx)
        continue
    rows = t.split("\n")
    n = t.count("(build house)")
    out.append("--- anib_%d : (build house)=%d  housing-headroom=%d  population-headroom=%d" %
               (idx, n, t.count("housing-headroom"), t.count("population-headroom")))
    for i, r in enumerate(rows):
        if "(build house)" in r:
            s = i
            while s > 0 and "(defrule" not in rows[s]:
                s -= 1
            conds = [rows[j].strip() for j in range(s + 1, i) if rows[j].strip() and rows[j].strip() != "=>"]
            out.append("    line %5d | %s" % (i + 1, " ".join(conds)))
    out.append("")

out.append("=== every x1 script mentioning (build house) ===")
p = os.path.join(W, "x1_drs")
for f in sorted(os.listdir(p)):
    if not f.startswith("anib_"):
        continue
    t = open(os.path.join(p, f), "rb").read().decode("latin-1")
    if "(build house)" in t:
        out.append("   %s : %d" % (f, t.count("(build house)")))

open(os.path.join(W, "dm_house_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_house_out.txt")
