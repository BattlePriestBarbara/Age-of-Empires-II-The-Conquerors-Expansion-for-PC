"""dm_chatcheck.py -- which chat actions does AoK HD.exe accept?

The AI action keyword table of the exe was already dumped (dm_tokdump_all.txt),
but this script proves the *chat* family directly and also lists every AI
keyword containing 'acknowledge'/'log', because those are the actions we want
to use as an in-game "patch is loaded" marker (a chat message is visible to the
player without needing the AILog directory).
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXE = (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       r"\Age of Empires II HD\AoK HD.exe")
PATTERNS = ("chat", "acknowledge", "log", "taunt", "attack-now", "research",
            "build", "escrow", "train", "town-size", "housing-headroom",
            "population-headroom", "can-build", "can-research", "difficulty")

data = open(EXE, "rb").read()
# the AI keyword table lives in the read-only data section: plain ASCII,
# NUL separated.  Take every printable ASCII run of length >= 4.
runs = re.findall(rb"[ -~]{4,}", data)
seen = {}
for r in runs:
    s = r.decode("ascii")
    for p in PATTERNS:
        if p in s:
            seen.setdefault(p, set()).add(s)
            break

out = ["exe: %s  (%d bytes, %d printable runs)" % (EXE, len(data), len(runs))]
for p in PATTERNS:
    hits = sorted(seen.get(p, ()))
    out.append("")
    out.append("=== strings containing %r : %d" % (p, len(hits)))
    for s in hits[:40]:
        out.append("    %s" % s)
    if len(hits) > 40:
        out.append("    ... (%d more)" % (len(hits) - 40))

txt = "\n".join(out)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), r"dm_chatcheck_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
