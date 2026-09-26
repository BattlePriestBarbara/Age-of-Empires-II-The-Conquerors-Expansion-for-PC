"""dm_dispatch.py -- find the AI preprocessor directive dispatcher by locating
references to the 4 directive strings, then read the #if-depth limit that guards
ERR3003 out of the nearby comparison.
"""
import os
import re
import struct

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []

TEXT_LO, TEXT_HI = 0x1000, 0x34e000


def s64(x):
    return x - (1 << 64) if x >= (1 << 63) else x


def va2off(va):
    return va - 0x400000


DIRECTIVES = [b"#load-if-defined", b"#load-if-not-defined", b"#else",
              b"#end-if", b"#load-if", b"load-if-defined"]

for d in DIRECTIVES:
    hits = [m.start() for m in re.finditer(re.escape(d) + b"\x00", data)]
    out.append("\n### directive string %r -> %d hit(s)" % (d.decode(), len(hits)))
    for h in hits:
        va = h + 0x400000
        out.append("   string @VA 0x%08x" % va)
        pat = struct.pack("<I", va)
        refs = [m.start() for m in re.finditer(re.escape(pat), data)
                if TEXT_LO <= m.start() < TEXT_HI]
        out.append("     %d code reference(s)" % len(refs))
        for r in refs[:6]:
            rva = r + 0x400000
            out.append("     --- ref @VA 0x%08x" % rva)
            lo, hi = max(0, r - 96), min(len(data), r + 96)
            for k in range(lo, hi, 16):
                chunk = data[k:k + 16]
                out.append("        %08x  %s   %s"
                           % (k, " ".join("%02x" % b for b in chunk),
                              "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))

# ---- hunt the depth limit: cmp <reg>, imm8 in the dispatcher neighbourhood ----
out.append("\n=== cmp reg, imm8 near the directive references (candidate limits)")
for d in DIRECTIVES:
    for h in [m.start() for m in re.finditer(re.escape(d) + b"\x00", data)]:
        va = h + 0x400000
        pat = struct.pack("<I", va)
        for m in re.finditer(re.escape(pat), data):
            if not (TEXT_LO <= m.start() < TEXT_HI):
                continue
            win = data[max(0, m.start() - 400):m.start() + 400]
            for cm in re.finditer(rb"\x83[\xf8-\xff](.)", win):
                out.append("   near %r ref 0x%08x: cmp reg, 0x%02x"
                           % (d.decode(), m.start() + 0x400000, cm.group(1)[0]))
open("dm_dispatch_out.txt", "w", encoding="utf-8").write("\n".join(out[:4000]))
print("wrote dm_dispatch_out.txt  (%d lines)" % len(out))
