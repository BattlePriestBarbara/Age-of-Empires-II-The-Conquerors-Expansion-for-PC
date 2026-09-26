"""dm_depth.py -- max #load-if-* nesting depth per AI script (retail vs patched)
and how deep the 8-fold catch-all really goes.
"""
import os
import re
import glob

DIRS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), r"aok_drs"), os.path.join(os.path.dirname(os.path.abspath(__file__)), r"x1_drs"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patched_scripts"), os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patch_out")]
out = []


def walk(path):
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in files:
                yield os.path.join(root, f)
    else:
        yield path


def profile(path, label=None):
    raw = open(path, "rb").read()
    text = raw.decode("latin-1")
    depth = mx = 0
    open_line = None
    deepest = 0
    deepest_line = None
    for i, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        s = line.strip()
        if s.startswith("#load-if-defined") or s.startswith("#load-if-not-defined"):
            depth += 1
            if depth > mx:
                mx = depth
                deepest_line = i
        elif s.startswith("#end-if"):
            depth -= 1
        elif s.startswith("#else") or s.startswith("#elif"):
            pass
    # where does depth stay >= 8?
    deep_lines = []
    d = 0
    for i, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        s = line.strip()
        if s.startswith("#load-if-defined") or s.startswith("#load-if-not-defined"):
            d += 1
            if d >= 8:
                deep_lines.append((i, d, s[:60]))
        elif s.startswith("#end-if"):
            d -= 1
    out.append("%-58s max depth=%2d (line %s)  lines>=8: %d  final depth=%d"
               % (label or os.path.basename(path), mx, deepest_line,
                  len(deep_lines), depth))
    for i, dd, s in deep_lines[:6]:
        out.append("      line %5d depth %d  %s" % (i, dd, s))
    return deep_lines


for d in DIRS:
    for p in sorted(walk(d)):
        if p.lower().endswith((".per", ".bin")):
            profile(p)
# the installed (patched) DRS-extracted copies
for p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patched_scripts\petersen deathmatch (Conquerors).per"),
          os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patched_scripts\petersen deathmatch (Age of Kings).per")):
    pass

out.append("\n=== direct look at the 8-fold catch-all in one file")
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patch_out\x1_drs_anib_60027.bin")
if os.path.exists(p):
    lines = open(p, "rb").read().decode("latin-1").replace("\r\n", "\n").split("\n")
    start = None
    for i, l in enumerate(lines, 1):
        if "#load-if-not-defined POPULATION-CAP" in l:
            start = i
            break
    if start:
        for i in range(start, min(len(lines) + 1, start + 60)):
            out.append("   %5d  %s" % (i, lines[i - 1][:110]))

open("dm_depth_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_depth_out.txt")
