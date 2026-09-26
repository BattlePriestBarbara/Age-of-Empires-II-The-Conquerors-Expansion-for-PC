"""dm_symbols.py -- (A) list the exe's preprocessor-symbol table,
(B) find the code that *defines* the POPULATION-CAP-* / DEATH-MATCH symbols,
so we can tell from static evidence which of them is active at a 500 pop cap.
"""
import os
import re
import struct

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def s_at(va):
    off = va - 0x400000
    e = data.find(b"\x00", off)
    return data[off:e].decode("latin-1")


out.append("=== strings in the preprocessor-symbol table region 0x374300..0x374600")
off = 0x374300 - 0x400000
for m in re.finditer(rb"[\x20-\x7e]{3,}", data[off:off + 0x300]):
    va = 0x374300 + m.start()
    out.append("   0x%08x  %s" % (va, s_at(va)))

names = [s_at(va) for va in [0x3743c8]]
out.append("\n=== every POPULATION-CAP-*/DIFFICULTY-*/GAME-MODE symbol string found")
targets = {}
for m in re.finditer(rb"(POPULATION-CAP-[0-9]+|DIFFICULTY-[A-Z]+|DEATH-MATCH|"
                     rb"REGICIDE|RANDOM-MAP|WONDER-RACE|KING-OF-THE-HILL|"
                     rb"GAME-SPEED-[A-Z]+|[A-Z-]*RESOURCES-START|SCENARIO|"
                     rb"DEFEND-THE-WONDER|SUDDEN-DEATH|TURBO-RANDOM-MAP|"
                     rb"FULL-RANDOM-MAP)\x00", data):
    va = 0x400000 + m.start()
    targets[va] = m.group(1).decode()
    out.append("   0x%08x  %s" % (va, targets[va]))

out.append("\n=== who references them (imm32 xrefs in .text, 0x401000..0x6f0000)")
for va, name in sorted(targets.items()):
    pat = struct.pack("<I", va)
    sites = []
    i = data.find(pat, 0x1000, 0x2f0000)
    while i != -1:
        sva = 0x400000 + i
        pre = data[i - 6:i]
        kind = "push imm32" if pre[-5:-4] == b"\x68" else (
               "mov  imm32" if pre[-6:-5] in (b"\xc7", b"\xc6") else "imm32")
        sites.append("0x%08x (%s)" % (sva - 4, kind))
        i = data.find(pat, i + 1)
    out.append("   0x%08x %-22s %s" % (va, name, ", ".join(sites) or "NONE"))

out.append("\n=== code around the first refs of each symbol")
for va, name in sorted(targets.items()):
    pat = struct.pack("<I", va)
    i = data.find(pat, 0x1000, 0x2f0000)
    if i == -1:
        continue
    start = max(0x1000, i - 0x40)
    out.append("\n--- %s  ref @0x%08x" % (name, 0x400000 + i - 4))
    for k in range(start, i + 0x14, 16):
        chunk = data[k:k + 16]
        out.append("   %08x  %s   %s"
                   % (k, " ".join("%02x" % b for b in chunk),
                      "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))

open(os.path.join(W, "dm_symbols_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_symbols_out.txt")
