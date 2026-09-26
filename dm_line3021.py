"""dm_line3021.py -- forensic check and regression check of the in-game error

    Player 8
    File  petersen deathmatch per
    Line 3021: ERR2011: Missing closing parenthesis

The superseded (v2) build appended a resources rule whose test was a single
(or ...) with four children.  AoK HD.exe takes two children per logical block,
so it wanted the closing parenthesis exactly where the third child began and
named that line: 3021.  dm_dialect.py proves the model by reproducing that very
line from the preserved broken sample.

Run this script after every rebuild: in the current build line 3021 has to be
an ordinary nested condition, every rule has to close, no line may drop below
depth 0 and the file has to end at depth 0.

The line counter of the engine counts the lines of the payload as stored in
the DRS, so we reproduce that: split on LF, keep the CR.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
BACKUP = os.path.join(W, "backup_drs")
PATCH_OUT = os.path.join(W, "patch_out2")

ERROR_LINE = 3021

JOBS = [
    ("RETAIL x1", os.path.join(BACKUP, "gamedata_x1.drs.orig"), b"anib", 60002),
    ("PATCHED x1 (patch_out2)", os.path.join(PATCH_OUT, "x1_drs_anib_60002.bin"), None, None),
    ("LIVE x1 (game Data)", os.path.join(GAME, "Data", "gamedata_x1.drs"), b"anib", 60002),
    ("RETAIL aok", os.path.join(BACKUP, "gamedata.drs.orig"), b"anib", 60002),
    ("PATCHED aok (patch_out2)", os.path.join(PATCH_OUT, "aok_drs_anib_60002.bin"), None, None),
    ("LIVE aok (game Data)", os.path.join(GAME, "Data", "gamedata.drs"), b"anib", 60002),
]


def load(path, ext, eid):
    if ext is None:
        return open(path, "rb").read()
    return Drs(path).payload(ext, eid)


def strip_code(line):
    """code part of a line: drop the ';' comment and every quoted string"""
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


def scan(text):
    """per line: (line no, raw, depth before, depth after, delta, kind)"""
    rows = text.split("\n")
    if rows and rows[-1] == "":
        rows = rows[:-1]            # trailing EOL is not a line
    depth = 0
    info = []
    for i, raw in enumerate(rows, 1):
        code = strip_code(raw)
        d0 = depth
        depth += code.count("(") - code.count(")")
        info.append((i, raw, d0, depth, code.count("(") - code.count(")"), code.strip()))
    return info, rows


def rules(text):
    """(start line, closing line, ok) for every rule

    ok = the rule's parenthesis depth really returns to 0 on a line that holds
    nothing but ")".  The previous version of this helper compared the depth
    right after the "(defrule" line (which is 1 by construction) and therefore
    flagged every first rule as broken.
    """
    info, _ = scan(text)
    starts = [i for i, _r, _d0, _d1, _dl, code in info
              if code.lower().startswith("(defrule")]
    out = []
    for j, s in enumerate(starts):
        limit = starts[j + 1] - 1 if j + 1 < len(starts) else len(info)
        end, ok = limit, False
        for k in range(s - 1, limit):
            if info[k][3] == 0:
                end, ok = info[k][0], info[k][5] == ")"
                break
        out.append((s, end, ok))
    return out


report = []
for label, path, ext, eid in JOBS:
    if not os.path.exists(path):
        report.append("=== %-26s MISSING %s" % (label, path))
        continue
    raw = load(path, ext, eid)
    text = raw.decode("latin-1")
    info, rows = scan(text)
    nl = text.count("\n")
    crlf = text.count("\r\n")
    report.append("")
    report.append("=" * 92)
    report.append("=== %s" % label)
    report.append("    path            : %s" % path)
    report.append("    bytes=%d  LF=%d  CRLF=%d  lines(engine)=%d  final depth=%d"
                  % (len(raw), nl, crlf, len(rows), info[-1][3] if info else -1))
    report.append("    last line       : %r" % (rows[-1][:70] if rows else ""))
    if 1 <= ERROR_LINE <= len(rows):
        i, r, d0, d1, delta, code = info[ERROR_LINE - 1]
        report.append("    LINE %d depth %d->%d : %r" % (i, d0, d1, r[:110]))
    else:
        report.append("    LINE %d -> FILE HAS ONLY %d LINES" % (ERROR_LINE, len(rows)))
    # every rule must close again before the next (defrule / EOF
    rl = rules(text)
    report.append("    rules=%d  first=%d  last=%d"
                  % (len(rl), rl[0][0] if rl else -1, rl[-1][0] if rl else -1))
    neg = [i for i, _r, _d0, d1, _dl, _c in info if d1 < 0]
    report.append("    lines with negative depth: %s" % (neg or "none"))
    for s, e, ok in rl:
        if not ok:
            report.append("    !! rule at line %d never closes (searched to line %d)"
                          % (s, e))
            for k in range(s - 1, min(e, len(rows))):
                ii, rr, dd0, dd1, dl, cc = info[k]
                report.append("       %5d | d%d->%d %s" % (ii, dd0, dd1, rr[:96]))
            break
    report.append("    --- lines %d..%d with running depth ---" % (ERROR_LINE - 12, ERROR_LINE + 12))
    for k in range(ERROR_LINE - 13, ERROR_LINE + 12):
        if 0 <= k < len(rows):
            ii, rr, dd0, dd1, dl, cc = info[k]
            report.append("       %5d | d%d->%d | %s" % (ii, dd0, dd1, rr.rstrip("\r")[:96]))

txt = "\n".join(report)
open(os.path.join(W, "dm_line3021_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
