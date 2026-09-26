"""Verify the fact/action names used by the patch really exist in the shipped AI scripts."""
import glob
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []


def scan(pattern, label, limit=12, dirs=("x1_drs", "aok_drs")):
    hits = []
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(W, d, "anib_*.bin"))):
            rows = open(p, encoding="latin-1").read().split("\n")
            for i, r in enumerate(rows):
                if re.search(pattern, r):
                    hits.append("%s:%d: %s" % (os.path.basename(p), i + 1, r.strip()))
    out.append("### %s  (%d hits)" % (label, len(hits)))
    out.extend(hits[:limit])
    out.append("")


scan(r"headroom", "fact names containing 'headroom'", 20)
scan(r"^\s*\(housing-headroom\s*<", "housing-headroom < N usage", 10)
scan(r"^\s*\(population-headroom", "population-headroom usage", 10)
scan(r"^\s*\(build house\)", "(build house) usage", 10)
scan(r"^\s*\(enable-timer\s+t-production", "timer t-production definition/use", 10)
scan(r"^\s*\(timer-triggered\s+t-production", "timer t-production trigger", 10)
scan(r"^\(defconst\s+t-production", "defconst t-production", 10)
scan(r"^\s*\(goal secondary-build\s+1\)", "(goal secondary-build 1) consumers", 30)
scan(r"^\s*\(goal secondary-build\s+0\)", "(goal secondary-build 0) - producers/re-arm", 30)

open(os.path.join(W, "dm_factcheck_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
