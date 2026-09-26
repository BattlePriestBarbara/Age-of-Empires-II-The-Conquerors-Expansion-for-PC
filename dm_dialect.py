"""dm_dialect.py -- post-install validator for the shape rules of this AI dialect.

The in-game error of the superseded build was

    Player 8   File  petersen deathmatch per
    Line 3021: ERR2011: Missing closing parenthesis

and it came from one rule that handed a single (or ...) four children: the
engine's condition parser has two argument slots per logical block, took the
first two, then wanted the closing parenthesis and walked into the third child.
Not one block in any shipped script has more than two children - they always
nest (dm_blockshape.py).

This script is the *independent* check of that model and of whatever is
installed right now:

  1. control: it runs the model over dm_block_v2_broken_fixture.txt, the byte
     copy of the broken appended block, placed behind the 2883 retail lines of
     gamedata_x1.drs - and it has to name exactly line 3021.
  2. audit: it checks the archive installed in the game tree:
       * retail script is a byte-exact prefix of the patched script
       * every logical block (also in the appended part) has <= 2 children
       * every rule closes before the next (defrule, final depth is 0
       * every block shape and fact arity occurs in a pristine shipped script
"""
import hashlib
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
BACKUP = os.path.join(W, "backup_drs")
FIXTURE = os.path.join(W, "dm_block_v2_broken_fixture.txt")
CONTROL_LINE = 3021          # what AoK HD.exe reported for that broken block
CONTROL_PREFIX = 2883        # pristine death-match lines of gamedata_x1.drs

MAX_CHILDREN = 2
BLOCK = ("or", "and", "nor", "not")
TOK = re.compile(r"\(|\)|[^\s()]+")
ENTRIES = ("anib_60002.bin", "anib_60027.bin", "anib_60010.bin", "anib_60001.bin",
           "anib_60029.bin", "anib_60008.bin", "anib_60003.bin", "anib_60026.bin")
DATASETS = (("x1_drs", "gamedata_x1.drs"), ("aok_drs", "gamedata.drs"))


def code_only(text):
    """drop comments and string literals, one *line* at a time

    Per line, because a quoted word inside a comment (the shipped comments say
    e.g. "(difficulty <= moderate)") would otherwise pair with a quote several
    lines further down, swallow every newline in between and shift all line
    numbers - which is exactly how the first version of this helper missed the
    in-game error line by one.
    """
    out = []
    for line in text.split("\n"):
        buf, in_str = [], False
        for ch in line:
            if ch == '"':
                if in_str:
                    in_str = False
                    buf.append('""')            # one placeholder per literal
                else:
                    in_str = True
                continue
            if in_str:
                continue
            if ch == ";":
                break
            buf.append(ch)
        out.append("".join(buf))
    return "\n".join(out)


def walk(code):
    """yield ('block', line, kw, payload) / ('fact', line, kw, nargs)"""
    stack = []
    for lineno, raw in enumerate(code.split("\n"), 1):
        for tok in TOK.findall(raw):
            if tok == "(":
                stack.append({"kw": None, "line": lineno, "kids": [], "args": []})
            elif tok == ")":
                if not stack:
                    continue
                node = stack.pop()
                if node["kw"] in BLOCK:
                    kids = node["kids"]
                    payload = (tuple(k["kw"] if k["kw"] in BLOCK else "<fact>"
                                     for k in kids),
                               sum(k["leaves"] for k in kids),
                               [k["line"] for k in kids])
                    node["leaves"] = payload[1]
                    yield ("block", node["line"], node["kw"], payload)
                else:
                    node["leaves"] = 1
                    yield ("fact", node["line"], node["kw"], len(node["args"]))
                if stack:
                    stack[-1]["kids"].append(node)
            elif stack:
                if stack[-1]["kw"] is None:
                    stack[-1]["kw"] = tok
                else:
                    stack[-1]["args"].append(tok)


def audit(text):
    """returns a dict with problems, block census, arities and structure numbers"""
    code = code_only(text)
    rows = text.split("\n")
    if rows and rows[-1] == "":
        rows = rows[:-1]
    res = {"problems": [], "blocks": [], "facts": [], "lines": len(rows),
           "crlf": text.count("\r\n"), "bytes": len(text.encode("latin-1"))}
    for kind, line, kw, payload in walk(code):
        if kind == "block":
            kids, leaves, klines = payload
            res["blocks"].append((line, kw, kids, leaves))
            if len(kids) > MAX_CHILDREN:
                res["problems"].append(
                    "line %d: (%s ...) has %d children - the engine takes %d, "
                    "then blames the child at line %d"
                    % (line, kw, len(kids), MAX_CHILDREN, klines[MAX_CHILDREN]))
        else:
            res["facts"].append((line, kw, payload))
    depth, rules, bad_rule = 0, [], []
    for i, raw in enumerate(code.split("\n"), 1):
        s = raw.strip()
        if s.startswith("(defrule"):
            rules.append(i)
            if depth != 0:
                bad_rule.append((i, depth))
        depth += raw.count("(") - raw.count(")")
    res["rules"], res["rule_lines"], res["depth"] = len(rules), rules, depth
    if depth:
        res["problems"].append("parenthesis depth at EOF is %d, not 0" % depth)
    for i, d in bad_rule:
        res["problems"].append("rule at line %d starts at depth %d "
                               "(the previous rule never closed)" % (i, d))
    return res


def main():
    out = []
    sig, arity = retail_vocabulary()
    out.append("pristine corpus: %d block shapes, %d fact arities"
               % (len(sig), len(arity)))

    # ---- 1. control: the model must reproduce the in-game line number ------
    fixture = open(FIXTURE, "rb").read().decode("latin-1")
    ctl = audit("\n" * CONTROL_PREFIX + fixture)
    out.append("")
    out.append("=" * 92)
    out.append("=== control test on the superseded (broken) appended block")
    out.append("    %s (%d bytes, put behind %d retail lines)"
               % (FIXTURE, len(fixture), CONTROL_PREFIX))
    out.append("    problems found : %d" % len(ctl["problems"]))
    for p in ctl["problems"]:
        out.append("      %s" % p)
    hit = [p for p in ctl["problems"] if "blames the child at line" in p]
    named = hit[0].split("blames the child at line ")[-1] if hit else "?"
    ok_control = named == str(CONTROL_LINE)
    out.append("    engine reported: line %d" % CONTROL_LINE)
    out.append("    model names    : line %s   -> %s"
               % (named, "MATCH" if ok_control else "MISMATCH"))
    assert ok_control, "the model does not reproduce the in-game error line"

    # ---- 2. audit what is installed right now -------------------------------
    verdicts = []
    for folder, archive in DATASETS:
        retail = Drs(os.path.join(BACKUP, archive + ".orig")).payload(b"anib", 60002)
        live_path = os.path.join(GAME, "Data", archive)
        live_raw = open(live_path, "rb").read()
        live = Drs(live_path).payload(b"anib", 60002)
        prefix_ok = live[:len(retail)] == retail
        tail = live[len(retail):]
        text = live.decode("latin-1")
        out.append("")
        out.append("=" * 92)
        out.append("=== %s  (%s)" % (archive, folder))
        out.append("    live file       : %s  md5 %s  (%d bytes)"
                   % (live_path, hashlib.md5(live_raw).hexdigest(), len(live_raw)))
        out.append("    retail script   : %d bytes, patched entry %d bytes "
                   "(+%d appended)" % (len(retail), len(live), len(tail)))
        out.append("    retail prefix   : %s"
                   % ("byte-exact" if prefix_ok else "*** NOT A PREFIX ***"))
        for label, sub in (("whole script", text), ("appended tail", tail.decode("latin-1"))):
            a = audit(sub)
            hist = Counter(len(k) for _l, _kw, k, _le in a["blocks"])
            unsig = sorted(set((kw, k) for _l, kw, k, _le in a["blocks"]
                               if (kw, k) not in sig))
            unar = sorted(set((kw, n) for _l, kw, n in a["facts"]
                              if kw and (kw, n) not in arity
                              and (kw, n) != ("chat-to-all", 1)))
            out.append("    --- %s: %d lines, %d CRLF, %d rules, final paren depth %d"
                       % (label, a["lines"], a["crlf"], a["rules"], a["depth"]))
            out.append("        blocks by child count: %s    deepest block: %d leaves"
                       % (dict(sorted(hist.items())),
                          max([b[3] for b in a["blocks"]] or [0])))
            out.append("        block shapes not attested in pristine retail : %s"
                       % (unsig or "none"))
            out.append("        fact arities not attested in pristine retail  : %s"
                       % (unar or "none (chat-to-all 1 arg is the documented M1 exception)"))
            for p in a["problems"]:
                out.append("        PROBLEM %s" % p)
            if label == "appended tail":
                verdicts.append((archive, not (a["problems"] or unsig or unar)))
        idx = text.find("(timer-triggered t-attackgroup)")
        if idx > 0:
            start = text.rfind("\n", 0, idx)
            out.append("        the resources rule as installed:")
            for s in text[start:start + 340].split("\n")[:14]:
                out.append("          | %s" % s.rstrip("\r"))

    out.append("")
    out.append("VERDICT: control reproduces line %d; appended tails clean: %s"
               % (CONTROL_LINE, verdicts))
    txt = "\n".join(out)
    with open(os.path.join(W, "dm_dialect_out.txt"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(txt + "\n")
    print(txt)



def retail_vocabulary():
    sig, arity = {}, {}
    for folder, _archive in DATASETS:
        for name in ENTRIES:
            path = os.path.join(W, folder, name)
            if not os.path.exists(path):
                continue
            for kind, _line, kw, payload in walk(code_only(
                    open(path, "rb").read().decode("latin-1"))):
                if kind == "block":
                    sig.setdefault((kw, payload[0]), "%s/%s" % (folder, name))
                elif kw:
                    arity.setdefault((kw, payload), "%s/%s" % (folder, name))
    return sig, arity



if __name__ == "__main__":
    main()
