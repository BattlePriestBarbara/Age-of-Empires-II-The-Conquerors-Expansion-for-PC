"""How are timers defined/started/used in the shipped DM scripts? (+ (true) idiom)"""
import os

W = os.path.dirname(os.path.abspath(__file__))
FILES = [("x1_drs", "anib_60002.bin"), ("x1_drs", "anib_60001.bin"), ("x1_drs", "anib_60029.bin"),
         ("x1_drs", "anib_60027.bin"), ("x1_drs", "anib_60026.bin"), ("x1_drs", "anib_60008.bin"),
         ("x1_drs", "anib_60007.bin"), ("aok_drs", "anib_60002.bin"), ("aok_drs", "anib_60027.bin")]
out = []
for d, f in FILES:
    p = os.path.join(W, d, f)
    if not os.path.exists(p):
        out.append("missing %s/%s" % (d, f))
        continue
    rows = open(p, "rb").read().decode("latin-1").split("\n")
    out.append("=" * 70)
    out.append("%s/%s (%d lines)" % (d, f, len(rows)))
    out.append("--- defconst lines ---")
    for i, r in enumerate(rows):
        if "defconst" in r:
            out.append("   %5d| %s" % (i + 1, r.rstrip()))
    out.append("--- timer names seen ---")
    import re
    names = sorted(set(re.findall(r"\bt-[a-z0-9-]+", "\n".join(rows))))
    out.append("   " + " ".join(names))
    out.append("--- (true) rules (first 6) ---")
    n = 0
    for i, r in enumerate(rows):
        if r.strip() == "(true)":
            s = i
            for j in range(i, min(i + 8, len(rows))):
                out.append("   %5d| %s" % (j + 1, rows[j].rstrip()))
            out.append("   ---")
            n += 1
            if n >= 6:
                break
    if n == 0:
        out.append("   none")
    out.append("")

open(os.path.join(W, "dm_timers_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_timers_out.txt", len(out), "lines")
