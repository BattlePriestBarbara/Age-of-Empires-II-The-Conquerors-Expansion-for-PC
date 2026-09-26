"""Final structural read of the DM main script: init, one civ block, secondary-build usage."""
import os

W = os.path.dirname(os.path.abspath(__file__))
out = []
p = os.path.join(W, "x1_drs", "anib_60002.bin")
rows = open(p, "rb").read().decode("latin-1").split("\n")


def dump(lo, hi, title):
    out.append("---- %s (lines %d..%d) ----" % (title, lo, hi))
    for i in range(lo - 1, min(hi, len(rows))):
        out.append("   %5d| %s" % (i + 1, rows[i].rstrip()))
    out.append("")


dump(1, 40, "INIT / goal defaults")
dump(41, 160, "AZTEC + start of HUN blocks")

out.append("---- every line mentioning secondary-build (x1 60002) ----")
for i, r in enumerate(rows):
    if "secondary-build" in r:
        out.append("   %5d| %s" % (i + 1, r.rstrip()))
out.append("")

out.append("---- every line mentioning t-lumbercamp (x1 60002) ----")
for i, r in enumerate(rows):
    if "t-lumbercamp" in r:
        out.append("   %5d| %s" % (i + 1, r.rstrip()))
out.append("")

dump(1300, 1330, "t-lumbercamp re-arm rule region (x1)")

open(os.path.join(W, "dm_struct_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_struct_out.txt", len(out), "lines")
