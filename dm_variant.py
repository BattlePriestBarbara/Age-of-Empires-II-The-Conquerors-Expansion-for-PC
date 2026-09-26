"""Compare the AoK (gamedata.drs) and X1 DM scripts: vocabulary + structure."""
import os

W = os.path.dirname(os.path.abspath(__file__))
KEYS = ["secondary-build", "unit-max", "deathmatch-unit-max", "need-deathmatch-villagers",
        "my-unique-unit-line", "cc-add-resource", "can-train", "(train ", "pop-cap", "POPULATION-CAP",
        "population", "disable-self", "can-train villager", "can-train my-unique-unit-line",
        "set-goal secondary-build 1", "set-goal secondary-build 0", "food-amount", "wood-amount"]
out = []
for d in ("aok_drs", "x1_drs"):
    p = os.path.join(W, d, "anib_60002.bin")
    raw = open(p, "rb").read()
    t = raw.decode("latin-1")
    rows = t.split("\n")
    out.append("=" * 70)
    out.append("%s : %s  %d bytes  %d lines" % (d, p, len(raw), len(rows)))
    for k in KEYS:
        out.append("   %-32s %4d" % (k, t.count(k)))
    out.append("   last 4 lines: %r" % [r.rstrip() for r in rows[-4:]])
    # any rule that sets secondary-build back to 1 (the re-arm)
    hits = [i + 1 for i, r in enumerate(rows) if "set-goal secondary-build 1" in r]
    out.append("   set-goal secondary-build 1 at lines: %s" % hits)
    # rules whose action contains (train my-unique-unit-line)
    for i, r in enumerate(rows):
        if "(train my-unique-unit-line)" in r:
            out.append("   train-unique rule at line %d; action context:" % (i + 1))
            for j in range(max(0, i - 1), min(len(rows), i + 3)):
                out.append("     %5d| %s" % (j + 1, rows[j].rstrip()))
    out.append("")

open(os.path.join(W, "dm_variant_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_variant_out.txt")
