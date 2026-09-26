"""dm_blockshape.py -- exact shape census of every logical block in the
shipped AI scripts.

Finding so far: in the whole shipped code base *every* (or/and/nor/not) block
has at most **2** children.  Our appended S1 rule feeds an (or ...) with 4
children and the engine answers

    Line 3021: ERR2011: Missing closing parenthesis

where line 3021 is the *third* child of that block.  So the parser seems to
have fixed argument slots.

This script answers the follow-up question: which block shapes are provably
retail-legal?  Especially, does retail ever write an (or ...) whose children
are themselves (or ...) blocks, i.e. is nesting allowed to give more leaves?
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
    ("aok anib_60002 death match", "gamedata.drs.orig", 60002),
    ("aok anib_60003", "gamedata.drs.orig", 60003),
    ("aok anib_60008", "gamedata.drs.orig", 60008),
    ("aok anib_60027 constants", "gamedata.drs.orig", 60027),
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


def token_stream(lines):
    for i, raw in enumerate(lines, 1):
        for t in TOK.findall(strip_code(raw)):
            yield t, i


class Node(object):
    __slots__ = ("kw", "line", "kids", "leaves", "depth")

    def __init__(self, kw, line):
        self.kw, self.line, self.kids = kw, line, []
        self.leaves, self.depth = 0, 0

    def child_kinds(self):
        return tuple(k.kw if k.kw in BLOCK else "<fact>" for k in self.kids)


def parse_rules(stream):
    """yield the top level node of every (defrule ...)"""
    root = None
    stack = []
    for tok, line in stream:
        if tok == "(":
            n = Node(None, line)
            stack.append(n)
        elif tok == ")":
            if not stack:
                continue
            n = stack.pop()
            for k in n.kids:
                n.leaves += k.leaves if k.kw in BLOCK else 1
                n.depth = max(n.depth, (k.depth + 1) if k.kw in BLOCK else 1)
            if not stack:
                yield n
            else:
                stack[-1].kids.append(n)
        else:
            if stack and stack[-1].kw is None:
                stack[-1].kw = tok


def walk(node, f):
    f(node)
    for k in node.kids:
        walk(k, f)


def analyse(label, text):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    sig = Counter()
    child_hist = Counter()
    top_leaves = Counter()
    top_depth = Counter()
    biggest = (0, 0)
    # collect every logical block anywhere, plus every block that is a direct
    # child of a rule (i.e. a top level condition block)
    n_rules = 0
    for rule in parse_rules(token_stream(lines)):
        n_rules += 1
        for c in rule.kids:
            if c.kw in BLOCK:
                top_leaves[c.leaves] += 1
                top_depth[c.depth] += 1
                if c.leaves > biggest[0]:
                    biggest = (c.leaves, c.line)
        stack = [rule]
        while stack:
            n = stack.pop()
            for k in n.kids:
                if k.kw in BLOCK:
                    sig[(k.kw, k.child_kinds())] += 1
                    child_hist[len(k.kids)] += 1
                    stack.append(k)
    res = []
    res.append("=" * 92)
    res.append("=== %s   lines=%d  rules=%d" % (label, len(lines), n_rules))
    res.append("    children per logical block      : %s" % dict(sorted(child_hist.items())))
    res.append("    leaves of a top level block     : %s" % dict(sorted(top_leaves.items())))
    res.append("    depth of a top level block      : %s" % dict(sorted(top_depth.items())))
    res.append("    biggest top level block: %d leaves at line %d" % biggest)
    res.append("    --- block shapes used by retail (keyword + child kinds) ---")
    for (kw, kids), n in sig.most_common():
        res.append("      (%s %s)  x%d" % (kw, " ".join(kids), n))
    return res, lines, biggest


allres = []
for label, arch, eid in SRC:
    text = Drs(os.path.join(BACKUP, arch)).payload(b"anib", eid).decode("latin-1")
    res, lines, biggest = analyse(label, text)
    allres += res
    if biggest[0] >= 4:
        a = biggest[1]
        allres.append("    --- the %d leaf block (line %d) ---" % (biggest[0], a))
        for i in range(a - 1, min(a + 14, len(lines))):
            allres.append("      %5d | %s" % (i + 1, lines[i].rstrip("\r")[:96]))

txt = "\n".join(allres)
with open(os.path.join(W, "dm_blockshape_out.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(txt + "\n")
print(txt)
