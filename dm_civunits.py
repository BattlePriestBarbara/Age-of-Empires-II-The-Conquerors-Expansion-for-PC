"""Summarise the per-civ DEATH-MATCH unit blocks of petersen deathmatch.per.

Goal: extract, for every #load-if-defined <CIV>-CIV block, the (generate-random-number N)
dice and the (random-number == M) / (can-train U) / (train U) triples, so a patch can be
generated that keeps training those same units without the deathmatch-unit-max / unit-max gate.
"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d in ("x1_drs", "aok_drs"):
    p = os.path.join(W, d, "anib_60002.bin")
    rows = open(p, "rb").read().decode("latin-1").split("\n")
    out.append("=" * 78)
    out.append("%s/anib_60002.bin  (%d lines)" % (d, len(rows)))

    # find civ blocks
    stack = []
    blocks = []          # (civname, start, end)
    for i, r in enumerate(rows):
        s = r.strip()
        if s.startswith("#load-if-defined") and s.endswith("-CIV"):
            stack.append((s.split()[1], i))
        elif s.startswith("#end-if") and stack:
            civ, st = stack.pop()
            blocks.append((civ, st, i))
    blocks.sort(key=lambda b: b[1])
    out.append("civ blocks found: %d -> %s" % (len(blocks), ", ".join(b[0] for b in blocks)))

    dicts = {}
    for civ, st, en in blocks:
        seg = rows[st:en + 1]
        civshort = civ.replace("-CIV", "").lower()
        dice = [int(m.group(1)) for m in
                (re.search(r"generate-random-number\s+(\d+)", x) for x in seg) if m]
        triples = []
        cur_rand = None
        for j, x in enumerate(seg):
            mr = re.match(r"\s*\(\s*random-number\s*==\s*(\d+)\s*\)", x)
            if mr:
                cur_rand = int(mr.group(1))
            mc = re.match(r"\s*\(\s*can-train\s+([a-z0-9-]+)\s*\)", x)
            mt = re.match(r"\s*\(\s*train\s+([a-z0-9-]+)\s*\)", x)
            if mt:
                triples.append((cur_rand, mt.group(1)))
        # analyse whether every train is preceded by a can-train of the same unit
        ok = True
        for rand, unit in triples:
            if not any(re.match(r"\s*\(\s*can-train\s+%s\s*\)" % re.escape(unit), x) for x in seg):
                ok = False
        out.append("  %-14s lines %5d..%-5d dice=%s trains=%s" %
                   (civshort, st + 1, en + 1, dice,
                    ", ".join("%s->%s" % (r, u) for r, u in triples)))
        if not ok:
            out.append("      *** a (train ...) without a matching (can-train ...) ***")
        dicts[d] = dicts.get(d, {})
        dicts[d][civshort] = triples
    # any (train ) inside civ blocks not captured?
    for civ, st, en in blocks:
        seg = rows[st:en + 1]
        for j, x in enumerate(seg):
            if re.search(r"\(\s*train\s+", x) and not re.match(r"\s*\(\s*train\s+[a-z0-9-]+\s*\)\s*$", x):
                out.append("  %-14s ODD train line %5d| %s" % (civ, st + j + 1, x.rstrip()))
    out.append("")

open(os.path.join(W, "dm_civunits_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_civunits_out.txt", len(out), "lines")
