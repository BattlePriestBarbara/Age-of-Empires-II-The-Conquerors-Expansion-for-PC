"""List extracted DRS dirs and dump the first lines of the AI script candidates."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "heads_out.txt")
lines = []

for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(BASE, d)
    if os.path.isdir(p):
        lines.append("== %s : %d files ==" % (d, len(os.listdir(p))))
        for f in sorted(os.listdir(p), key=lambda s: (len(s), s)):
            lines.append("   %-24s %d" % (f, os.path.getsize(os.path.join(p, f))))
        lines.append("")

for d, names in (("x1_drs", ["anib_60002", "anib_60026", "anib_60027", "anib_60028", "anib_60029"]),
                 ("aok_drs", ["anib_60026"])):
    for nm in names:
        p = os.path.join(BASE, d, nm)
        if not os.path.isfile(p):
            p2 = p + ".bin"
            if os.path.isfile(p2):
                p = p2
            else:
                lines.append("!! missing %s" % p)
                continue
        with open(p, "rb") as f:
            raw = f.read()
        txt = raw.decode("latin-1")
        nl = "\r\n" if "\r\n" in txt else "\n"
        rows = txt.split(nl)
        lines.append("---- %s\\%s  (%d bytes, %d lines) first 60 lines ----" % (d, os.path.basename(p), len(raw), len(rows)))
        for i, r in enumerate(rows[:60], 1):
            lines.append("  %4d | %s" % (i, r.rstrip("\r")))
        lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
