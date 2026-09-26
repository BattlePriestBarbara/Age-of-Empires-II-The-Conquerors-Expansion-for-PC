"""dm_exe_logs.py -- does AoK HD.exe write AI script errors somewhere?

The preprocessor/parser has a full set of error codes (ERR2004, ERR3006, ...);
if the game logs them we get a runtime feedback channel for "did my appended
block parse?" without any extra tooling.
"""
import re

PATH = (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD\AoK HD.exe")
NEEDLES = [br"ERR2004", br"ERR3006", br"ai error", br"AI error", br"AIError",
           br"ai_error", br"AIERR", br"script error", br"\.per", br"log\b"]


def main():
    blob = open(PATH, "rb").read()
    for needle in NEEDLES:
        hits = [m.start() for m in re.finditer(needle, blob, re.I)]
        print("\n%-16s %d hit(s)" % (needle.decode(), len(hits)))
        for off in hits[:4]:
            ctx = blob[max(0, off - 120):off + 160]
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
            print("   @0x%08x %s" % (off, text))


if __name__ == "__main__":
    main()
