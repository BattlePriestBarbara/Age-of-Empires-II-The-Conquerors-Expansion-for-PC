"""dm_capsym.py -- is POPULATION-CAP-<n> a fixed symbol table or built at
runtime via sprintf?  Also: which AI tokens exist for difficulty / building /
chat / research (to validate patch syntax).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def ctx(off, n=150):
    b = data[max(0, off - n):off + n]
    return "".join(chr(c) if 32 <= c < 127 else ("|" if c == 0 else ".") for c in b)


out.append("=== every POPULATION-CAP occurrence in AoK HD.exe")
pats = [b"POPULATION-CAP", b"CAP-%", b"POPULATION"]
for p in pats[:2]:
    hits = [m.start() for m in re.finditer(re.escape(p), data)]
    out.append("  %-16s : %d occurrence(s)" % (p.decode(), len(hits)))
    for off in hits:
        out.append("     @0x%08x  %s" % (off, ctx(off, 90)))
    if p == b"POPULATION-CAP":
        out.append("  --- distinct full symbol names found ---")
        names = sorted(set(m.group(0).decode() for m in
                           re.finditer(rb"POPULATION-CAP-[0-9A-Za-z%$]+", data)))
        for n in names:
            out.append("     %s" % n)

out.append("\n=== AI tokens: difficulty / build / chat / research / goal")
toks = [b"hardest", b"hard", b"moderate", b"easy", b"easiest",
        b"housing-headroom", b"population-headroom", b"can-build",
        b"build", b"chat-to-all", b"chat-local-to-self", b"enable-timer",
        b"disable-self", b"can-research", b"set-goal", b"cc-add-resource",
        b"secondary-build", b"sn-maximum-town-size", b"house", b"difficulty",
        b"#load-if-not-defined", b"#load-if-defined", b"#else", b"#end-if",
        b"#include"]
for t in toks:
    hits = [m.start() for m in re.finditer(re.escape(t), data)]
    out.append("  %-24s %4d hit(s)" % (t.decode(), len(hits)))
    if t.startswith(b"#"):
        for off in hits[:4]:
            out.append("        @0x%08x %s" % (off, ctx(off, 60)))

open("dm_capsym_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_capsym_out.txt")
