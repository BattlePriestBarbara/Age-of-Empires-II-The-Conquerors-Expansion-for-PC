"""Scan AoK HD.exe for path / AI-loading related strings (ASCII + UTF-16LE)."""
import os
import re

EXE = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\AoK HD.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"exe_paths_out.txt")
PATS = [b"AI\\", b"anib", b".per", b".ai", b"gamedata", b"AI.txt", b"Load", b"DRS", b"drs\\",
        b"Load\\", b"Random\\", b"mods", b"Scenario", b"open_read", b"fopen"]

raw = open(EXE, "rb").read()
lines = ["=== EXE %s (%d bytes) ===" % (os.path.basename(EXE), len(raw)), ""]

for pat in PATS:
    lines.append("### pattern %r" % pat)
    # ASCII
    n = 0
    for m in re.finditer(re.escape(pat), raw):
        n += 1
        if n > 40:
            lines.append("   ... more ASCII hits truncated")
            break
        a = max(0, m.start() - 24)
        ctx = raw[a:m.start() + 64]
        printable = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        lines.append("   A 0x%08X  %s" % (m.start(), printable))
    # UTF-16LE
    wide = re.compile(re.escape(pat.decode("latin-1").encode("utf-16-le")))
    n = 0
    for m in wide.finditer(raw):
        n += 1
        if n > 40:
            lines.append("   ... more UTF16 hits truncated")
            break
        a = max(0, m.start() - 24)
        ctx = raw[a:m.start() + 80]
        printable = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx[::2])
        lines.append("   W 0x%08X  %s" % (m.start(), printable))
    lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
