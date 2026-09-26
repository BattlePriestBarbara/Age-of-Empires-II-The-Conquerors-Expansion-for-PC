"""dm_exe_ai.py -- scan AoK HD.exe for AI-preprocessor related strings.

We want to know whether the engine builds the symbol `POPULATION-CAP-<n>` from the
actual population limit (in which case a pop limit of 500 produces
POPULATION-CAP-500, which no script in the DRS knows about), and which
preprocessor directives the parser understands.
"""
import re
import sys

PATH = (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD\AoK HD.exe")
NEEDLES = [b"POPULATION-CAP", b"POPULATION", b"DIFFICULTY-", b"#load-if-defined",
           b"#load-if-not-defined", b"#else", b"#end-if", b"#load",
           b"constant", b"Constant", b"unknown", b"not defined", b"already defined"]


def main():
    with open(PATH, "rb") as fh:
        blob = fh.read()
    print("exe: %d bytes" % len(blob))
    for needle in NEEDLES:
        hits = [m.start() for m in re.finditer(re.escape(needle), blob)]
        print("\n%-22s %d hit(s)" % (needle.decode(), len(hits)))
        for off in hits[:6]:
            start = max(0, off - 70)
            ctx = blob[start:off + 90]
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
            print("   @0x%08x  %s" % (off, text))


if __name__ == "__main__":
    main()
