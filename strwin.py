"""Dump printable strings in windows around given exe offsets (ASCII)."""
import re
import sys

EXE = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\AoK HD.exe"
if len(sys.argv) > 1 and sys.argv[1].endswith(".exe"):
    EXE = sys.argv[1]
    offs = [int(x, 0) for x in sys.argv[2:]]
else:
    offs = [3636302, 3636411, 3636491, 3662243, 3677600, 3677710, 3722505, 3725364,
            3613408, 3613252, 3681576, 3681660, 3681840, 3685360, 3685941, 3686068]

with open(EXE, "rb") as f:
    data = f.read()

for o in offs:
    s = max(0, o - 160)
    e = min(len(data), o + 320)
    chunk = data[s:e]
    out = []
    cur = b""
    for i, c in enumerate(chunk):
        if 32 <= c < 127:
            cur += bytes([c])
        else:
            if len(cur) >= 4:
                out.append((s + i - len(cur), cur.decode("latin-1")))
            cur = b""
    if len(cur) >= 4:
        out.append((s + len(chunk) - len(cur), cur.decode("latin-1")))
    print("---- offset 0x%x (%d) ----" % (o, o))
    for a, t in out:
        print("   0x%08x  %s" % (a, t))
