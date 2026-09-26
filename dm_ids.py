"""dm_ids.py -- (1) which AI script names does the exe know, (2) what is in
every anib entry of every gamedata archive?

The `(load "...")` name -> DRS resource id mapping is the thing my patch depends
on, so it has to be read out of the engine, not guessed.
"""
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
EXE = os.path.join(GAME, "AoK HD.exe")
DRS = [os.path.join(GAME, "Data", "gamedata.drs"),
       os.path.join(GAME, "Data", "gamedata_x1.drs"),
       os.path.join(GAME, "Data", "gamedata_x1_p1.drs")]
NAMES = ["petersen", "random game", "random-game", "deathmatch", "map loads",
         "diplomacy", "supplement", "groups", "resign", "constants",
         "difficulty", "wonder kill", "per files", "ai files", "*.per"]


def drs_entries(path):
    d = open(path, "rb").read()
    n_tables, _ = struct.unpack_from("<ii", d, 56)
    out = []
    for t in range(n_tables):
        pos = 64 + 12 * t
        ext = d[pos:pos + 4]
        info_off, n = struct.unpack_from("<ii", d, pos + 4)
        for i in range(n):
            eid, off, size = struct.unpack_from("<iii", d, info_off + 12 * i)
            out.append((ext, eid, d[off:off + size]))
    return out


def main():
    exe = open(EXE, "rb").read()
    print("=== 1) AI script names inside AoK HD.exe")
    for n in NAMES:
        hits = [m.start() for m in re.finditer(re.escape(n.encode()), exe, re.I)]
        print("\n  %-14s %d hit(s)" % (n, len(hits)))
        for off in hits[:8]:
            ctx = exe[max(0, off - 80):off + 120]
            print("     @0x%08x %s" % (off, "".join(
                chr(b) if 32 <= b < 127 else "." for b in ctx)))

    print("\n\n=== 2) anib entries per archive")
    for path in DRS:
        if not os.path.exists(path):
            print("\n-- %s : MISSING" % os.path.basename(path))
            continue
        print("\n-- %s (%d bytes)" % (os.path.basename(path), os.path.getsize(path)))
        for ext, eid, blob in drs_entries(path):
            if ext != b"anib":
                continue
            text = blob.decode("latin-1")
            caps = sorted(set(int(c) for c in re.findall(r"POPULATION-CAP-(\d+)", text)))
            loads = re.findall(r'\(load\s+"([^"]+)"\)', text, re.I)
            first = next((l.strip() for l in text.split("\n") if l.strip()), "")
            print("   %-6d %7d B  rules=%-4d caps=%-22s loads=%s"
                  % (eid, len(blob), len(re.findall(r"\(defrule", text)),
                     ",".join(map(str, caps)) or "-",
                     "; ".join(loads[:6]) or "-"))
            print("          first: %s" % first[:110])


if __name__ == "__main__":
    main()
