import os
import re, sys
W = os.path.dirname(os.path.abspath(__file__))
path = W + r"\x1_drs\anib_60002.bin"
text = open(path, "rb").read().decode("latin-1")
lines = [l.rstrip("\r") for l in text.split("\n")]

def blocks_of(rx, cap=8):
    """return the enclosing top-level (defrule ...) form of every match"""
    out, seen = [], set()
    for i, l in enumerate(lines):
        if not rx.search(l):
            continue
        start = None
        for j in range(i, -1, -1):
            s = lines[j].lstrip()
            if s.startswith("(defrule"):
                start = j
                break
            if s.startswith(")"):     # already past the previous form
                break
        if start is None or start in seen:
            continue
        depth = 0
        for k in range(start, len(lines)):
            depth += lines[k].count("(") - lines[k].count(")")
            if depth <= 0 and k > start:
                seen.add(start)
                out.append((start + 1, k + 1, lines[start:k + 1]))
                break
        if len(out) >= cap:
            break
    return out

pats = ["feudal-age", "castle-age", "imperial-age", "housing-headroom",
        "population-headroom", "build house", "chat-to-all", "can-research"]
rep = []
for p in pats:
    rx = re.compile(p, re.I)
    hits = [i + 1 for i, l in enumerate(lines) if rx.search(l)]
    rep.append("=== %-20s %d line(s): %s" % (p, len(hits), hits[:30]))
    for a, b, body in blocks_of(rx):
        rep.append("    --- rule lines %d-%d ---" % (a, b))
        for l in body:
            rep.append("      %5d| %s" % (a + body.index(l), l))
rep.append("==== can-build house / house-count lines")
for i, l in enumerate(lines):
    if re.search("house", l, re.I):
        rep.append("  %5d| %s" % (i + 1, l))
txt = "\n".join(rep)
open(W + r"\dm_snip_out.txt", "w", encoding="utf-8").write(txt + "\n")
print(txt)
