"""dm_oruse.py -- precise census of the logical blocks (or / and / nor / not)
in the shipped AI scripts.

The in-game error

    Line 3021: ERR2011: Missing closing parenthesis

points at the *third* child of the (or ...) block of our appended S1 rule.
The suspicion is that the engine's condition parser is a hand written
recursive descent parser with fixed size argument slots, i.e. it stops
reading children after N of them and then complains that the block was never
closed ("Missing closing parenthesis").  So: how many children do the shipped
blocks have, which keywords do they contain and in which position of a rule
do they appear?
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(W, "backup_drs")

SRC = [
    ("x1 anib_60002 death match", "gamedata_x1.drs.orig", 60002),
    ("x1 anib_60003", "gamedata_x1.drs.orig", 60003),
    ("x1 anib_60029", "gamedata_x1.drs.orig", 60029),
    ("x1 anib_60010", "gamedata_x1.drs.orig", 60010),
    ("x1 anib_60008", "gamedata_x1.drs.orig", 60008),
    ("x1 anib_60026", "gamedata_x1.drs.orig", 60026),
    ("aok anib_60002 death match", "gamedata.drs.orig", 60002),
    ("aok anib_60003", "gamedata.drs.orig", 60003),
    ("aok anib_60008", "gamedata.drs.orig", 60008),
    ("aok anib_60026", "gamedata.drs.orig", 60026),
]

BLOCK = ("or", "and", "nor", "not")
TOK = re.compile(r"\(|\)|[^\s()]+")


def strip_code(line):
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == ";":
            break
        out.append(ch)
    return "".join(out)


def tokens(lines):
    """(token, line number) stream, comments and strings removed"""
    for i, raw in enumerate(lines, 1):
        for t in TOK.findall(strip_code(raw)):
            yield t, i


def blocks(stream):
    """recursive walk: yield (keyword, line, [child keywords], n_children)"""
    stack = []            # each: dict(kw, line, kids=[], )
    for tok, line in stream:
        if tok == "(":
            stack.append({"kw": None, "line": line, "kids": []})
        elif tok == ")":
            if not stack:
                continue
            node = stack.pop()
            kw = node["kw"]
            if kw in BLOCK:
                yield kw, node["line"], [k for k in node["kids"]], len(node["kids"])
            if stack:
                stack[-1]["kids"].append(kw or "<fact>")
        else:
            if stack and stack[-1]["kw"] is None:
                stack[-1]["kw"] = tok


for label, arch, eid in SRC:
    path = os.path.join(BACKUP, arch)
    text = Drs(path).payload(b"anib", eid).decode("latin-1")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    hist = Counter()
    kidkind = Counter()
    examples = {}
    n_blocks = 0
    for kw, line, kids, n in blocks(tokens(lines)):
        n_blocks += 1
        hist[n] += 1
        for k in kids:
            kidkind[k] += 1
        key = (kw, n)
        if key not in examples:
            examples[key] = line
    print("=" * 92)
    print("=== %s   lines=%d   logical blocks=%d" % (label, len(lines), n_blocks))
    print("    children-per-block histogram: %s" % dict(sorted(hist.items())))
    print("    child keyword census        : %s" % dict(kidkind.most_common(12)))
    for key in sorted(examples, key=lambda k: (-k[1], k[0])):
        kw, n = key
        print("      (%s ...) with %2d children  first seen at line %d" % (kw, n, examples[key]))
    biggest = max(examples, key=lambda k: k[1]) if examples else (None, 0)
    if not biggest[0]:
        print("    (this script has no logical block at all)")
        continue
    print("    biggest block: (%s ...) %d children at line %d"
          % (biggest[0], biggest[1], examples[biggest]))
    a = examples[biggest]
    for i in range(a - 1, min(a + biggest[1] + 2, len(lines))):
        print("      %5d | %s" % (i + 1, lines[i].rstrip("\r")[:96]))
