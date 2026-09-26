"""dm_popstr.py -- print the symbol strings the engine's population-cap switch
pushes, so we can read off which POPULATION-CAP-* a lobby limit of 500 maps to.

The switch at 0x0045c900 compares the lobby limit against 25/50/75/100/125/150/
175/200/300/400/500 and then `push`es the address of a symbol name (opcode 0x68
followed by a 4 byte VA in the read-only data section).  This script decodes
every such push inside the switch and resolves the string it points at.
"""
import os

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
BASE = 0x400000
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()


def cstr(va):
    off = va - BASE
    end = data.find(b"\0", off)
    raw = data[off:end]
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError:
        return "<not ascii: %s>" % " ".join("%02x" % b for b in raw)


out = []
out.append("=== push operands inside the difficulty/pop-cap switch")
out.append("    (scan window 0x0045c900..0x0045ca70, only VAs of the 'push imm32'"
           " form)")
out.append("    exe size 0x%06x bytes" % len(data))
for i in range(0x45c900 - BASE, 0x45ca70 - BASE):
    if data[i] != 0x68:                       # push imm32
        continue
    va = int.from_bytes(data[i + 1:i + 5], "little")
    if BASE <= va < BASE + len(data):
        off = va - BASE
        # the image is mapped with RVA == file offset for the sections we need,
        # but fall back to a scan of the 64 bytes before the terminator
        txt = cstr(va)
        if not txt or txt.startswith("<"):
            end = data.find(b"\0", off)
            txt = "<raw %s>" % " ".join("%02x" % b for b in data[off:off + 32])
        out.append("    0x%08x -> 0x%08x  %r" % (BASE + i, va, txt))

out.append("")
out.append("=== reference: every POPULATION-CAP-* symbol in the exe")
import re
for m in sorted(set(re.findall(rb"POPULATION-CAP-[0-9]+", data))):
    out.append("    " + m.decode("ascii"))

open(os.path.join(W, "dm_popstr_out.txt"), "w", encoding="utf-8").write(
    "\n".join(out))
print("\n".join(out))
