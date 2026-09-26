"""What else is gated by (goal secondary-build 1) in the DM scripts?"""
import collections
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d, idx in (("x1_drs", 60002), ("aok_drs", 60002)):
    p = os.path.join(W, d, "anib_%d.bin" % idx)
    t = open(p, "rb").read().decode("latin-1")
    rows = t.split("\n")
    acts = collections.Counter()
    total = 0
    for i, r in enumerate(rows):
        if "secondary-build" not in r:
            continue
        s = i
        while s > 0 and "(defrule" not in rows[s]:
            s -= 1
        e = i
        while e < len(rows) - 1 and rows[e].strip() != ")":
            e += 1
        block = rows[s:e + 1]
        conds = [b.strip() for b in block if b.strip() not in ("", "=>")]
        # is it a condition or an action?
        is_cond = any(b.strip().startswith("(goal secondary-build") for b in conds)
        if is_cond:
            total += 1
            stripped = [b.strip() for b in block]
            body = block[stripped.index("=>") + 1:] if "=>" in stripped else []
            for b in body:
                m = re.match(r"\(([a-z-]+)", b.strip())
                if m:
                    acts[m.group(1)] += 1
    out.append("=== %s/anib_%d.bin : %d rules gated by (goal secondary-build ...)" % (d, idx, total))
    for k, v in acts.most_common():
        out.append("    %-28s %d" % (k, v))
    out.append("")

open(os.path.join(W, "dm_secbuild_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_secbuild_out.txt")
