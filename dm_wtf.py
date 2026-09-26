"""dm_wtf.py -- why is the pop-500 catch-all apparently not taking effect?

Checks
  1) does AoK HD.exe know the directive tokens we used?
  2) which "#load-if-*" forms do the *retail* scripts use (60002 / 60026 / 60027 / 60010)?
  3) same for our patched files (should only add #load-if-not-defined at the tail)
"""
import os
import re

EXE = (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       r"\Age of Empires II HD\AoK HD.exe")
WORK = os.path.dirname(os.path.abspath(__file__))
RETAIL = [r"x1_drs\anib_60002.bin", r"x1_drs\anib_60026.bin",
          r"x1_drs\anib_60027.bin", r"aok_drs\anib_60002.bin",
          r"aok_drs\anib_60010.bin"]
PATCHED = [r"patched_scripts\petersen deathmatch (Conquerors).per",
           r"petersen constants (Conquerors).per",
           r"petersen constants (Age of Kings).per"]
DIRECTIVES = [b"#load-if-defined", b"#load-if-not-defined", b"#else",
              b"#end-if", b"#include", b"POPULATION-CAP-", b"DEATH-MATCH"]
OPTOKENS = [b"LOAD-IF-DEFINED", b"LOAD-IF-NOT-DEFINED", b"END-IF",
            b"ELSE", b"INCLUDE", b"POPULATION-CAP-%", b"POPULATION-CAP-"]


def scan(path, needles, label, limit=6):
    blob = open(path, "rb").read()
    print("\n== %s (%d bytes)" % (label, len(blob)))
    for n in needles:
        hits = [m.start() for m in re.finditer(re.escape(n), blob, re.I)]
        print("   %-24s %d" % (n.decode(), len(hits)))
        for off in hits[:limit]:
            ctx = blob[max(0, off - 90):off + 110]
            print("      @0x%08x %s" % (
                off, "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)))


def counts(path, label):
    raw = open(path, "rb").read()
    text = raw.decode("latin-1")
    if not os.path.isabs(path):
        path = os.path.join(WORK, path)
    print("\n-- %s" % label)
    for pat in ("#load-if-defined", "#load-if-not-defined", "#else",
                "#end-if", "#include"):
        print("   %-24s %d" % (pat, len(re.findall(re.escape(pat), text, re.I))))


def main():
    scan(EXE, OPTOKENS, "AoK HD.exe token/string table", limit=3)
    for rel in RETAIL:
        counts(os.path.join(WORK, rel), "RETAIL " + rel)
    for rel in PATCHED:
        counts(os.path.join(WORK, rel), "PATCHED " + rel)


if __name__ == "__main__":
    main()
