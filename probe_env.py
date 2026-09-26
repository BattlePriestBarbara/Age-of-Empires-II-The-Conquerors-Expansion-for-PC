"""Probe the AoE2 HD install + exe for AI-script loading mechanism."""
import os
import sys

GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"probe_env.txt")
lines = []


def w(s=""):
    lines.append(str(s))


def hexdump(b, n=48):
    return " ".join("%02x" % c for c in b[:n]) + (" ..." if len(b) > n else "")


def looks_text(b):
    if not b:
        return False
    printable = sum(1 for c in b if 9 <= c <= 13 or 32 <= c < 127)
    return printable / len(b) > 0.9


w("== game root: %s (exists=%s) ==" % (GAME, os.path.isdir(GAME)))
if os.path.isdir(GAME):
    for name in sorted(os.listdir(GAME)):
        p = os.path.join(GAME, name)
        if os.path.isdir(p):
            n = 0
            try:
                n = len(os.listdir(p))
            except Exception:
                pass
            w("  DIR  %-28s items=%d" % (name, n))
        else:
            try:
                w("  FILE %-28s size=%d" % (name, os.path.getsize(p)))
            except Exception as e:
                w("  FILE %-28s err=%s" % (name, e))

for sub in ("AI", "ai", "Random", "random", "Data", "data", "SaveGame", "Games"):
    d = os.path.join(GAME, sub)
    if not os.path.isdir(d):
        continue
    w("")
    w("== listing %s ==" % sub)
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isdir(p):
            w("  DIR  %s" % name)
            continue
        sz = os.path.getsize(p)
        with open(p, "rb") as f:
            head = f.read(64)
        w("  FILE %-32s size=%-8d text=%-5s head=%s" % (name, sz, looks_text(head), hexdump(head, 32)))

# ---- exe string probes -------------------------------------------------
cands = [os.path.join(GAME, n) for n in ("AoK HD.exe", "AoK HD.exe.bak")]
for exe in cands:
    if not os.path.isfile(exe):
        continue
    with open(exe, "rb") as f:
        data = f.read()
    w("")
    w("== exe %s size=%d ==" % (os.path.basename(exe), len(data)))
    for pat in (b".per", b".ai", b"ai\\", b"ai/", b"random\\", b"anib", b"AI\\", b"\\AI\\",
                b"gamedata.drs", b"*.per", b"*.ai", b"petersen", b"deathmatch"):
        lo = data.lower()
        idx = []
        start = 0
        while True:
            i = lo.find(pat.lower(), start)
            if i < 0 or len(idx) >= 8:
                break
            idx.append(i)
            start = i + 1
        w("  %-14s hits=%s" % (pat.decode("latin-1"), idx))
    # utf-16le probes
    for pat in (".per", ".ai", "ai\\", "AI\\", "anib"):
        u = pat.encode("utf-16-le")
        lo = data.lower()
        idx = []
        start = 0
        while True:
            i = lo.find(u.lower(), start)
            if i < 0 or len(idx) >= 8:
                break
            idx.append(i)
            start = i + 1
        w("  utf16 %-10s hits=%s" % (pat, idx))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("written", OUT, len(lines), "lines")
