"""Sanity-check a .per AI script (paren balance + preprocessor balance) and diff original vs patched."""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))


def strip_comment(line):
    """Remove an AI-language ';' comment but keep ';' inside "..." strings."""
    out = []
    in_str = False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == ";" and not in_str:
            break
        out.append(ch)
    return "".join(out)


def check(path):
    raw = open(path, "rb").read()
    text = raw.decode("latin-1")
    rows = text.split("\n")
    depth = 0
    mind = 0
    line_of_min = 0
    for i, r in enumerate(rows, 1):
        code = strip_comment(r)
        for ch in code:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < mind:
                    mind = depth
                    line_of_min = i
    pp = 0
    pp_bad = 0
    for r in rows:
        s = r.strip()
        if s.startswith("#load-if") or (s.startswith("#if") and not s.startswith("#ifdef") and not s.startswith("#ifndef")):
            pp += 1
        elif s.startswith("#end-if"):
            pp -= 1
            if pp < 0:
                pp_bad += 1
    return {
        "file": path,
        "bytes": len(raw),
        "lines": len(rows),
        "crlf_lines": text.count("\r\n"),
        "paren_depth_end": depth,
        "paren_min_depth": mind,
        "paren_min_line": line_of_min,
        "n_defrule": len(re.findall(r"\(defrule", text)),
        "pp_depth_end": pp,
        "pp_stray_end": pp_bad,
        "non_ascii_bytes": sum(1 for b in raw if b > 127),
    }


def main():
    out = []
    pairs = [
        (os.path.join(W, "x1_drs", "anib_60002.bin"), os.path.join(W, "patch_out", "x1_drs_anib_60002.bin"),
         "petersen deathmatch (Conquerors)"),
        (os.path.join(W, "aok_drs", "anib_60002.bin"), os.path.join(W, "patch_out", "aok_drs_anib_60002.bin"),
         "petersen deathmatch (Age of Kings)"),
        (os.path.join(W, "x1_drs", "anib_60027.bin"), os.path.join(W, "patch_out", "x1_drs_anib_60027.bin"),
         "petersen constants (Conquerors) - fix 4"),
        (os.path.join(W, "aok_drs", "anib_60010.bin"), os.path.join(W, "patch_out", "aok_drs_anib_60010.bin"),
         "constants (Age of Kings) - fix 4"),
    ]
    for orig, patched, label in pairs:
        out.append("=" * 78)
        out.append("--- %s" % label)
        out.append("--- ORIGINAL  %s" % check(orig))
        out.append("--- PATCHED   %s" % check(patched))
        ot = open(orig, encoding="latin-1").read()
        pt = open(patched, encoding="latin-1").read()
        assert pt[:len(ot)] == ot, "patched file is not a pure append of the original!"
        added = pt[len(ot):]
        out.append("--- appended %d bytes, %d rules, %d lines, %d x #load-if-not-defined" %
                   (len(added), len(re.findall(r"\(defrule", added)), added.count("\r\n"),
                    len(re.findall(r"#load-if-not-defined", added))))
        out.append(added.replace("\r\n", "\n").rstrip("\n"))
        out.append("")
    txt = "\n".join(out)
    open(os.path.join(W, "dm_verify_out.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
