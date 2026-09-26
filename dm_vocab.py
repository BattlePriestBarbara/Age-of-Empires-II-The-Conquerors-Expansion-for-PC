"""dm_vocab.py -- authoritative check: is every token in the DM script known
to AoK HD.exe?

The exe stores AI tokens in a pooled string table (MSVC /GF style), so a token
that is a suffix of another token ("build" inside "can-build") exists as a
substring only -> the test is "is T a substring of some pooled identifier run".
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EXE = (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       r"\Age of Empires II HD\AoK HD.exe")
PS = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patched_scripts")
SCRIPTS = [os.path.join(PS, "petersen deathmatch (Conquerors).per"),
           os.path.join(PS, "petersen deathmatch (Age of Kings).per"),
           os.path.join(PS, "petersen constants (Conquerors).per"),
           os.path.join(PS, "petersen constants (Age of Kings).per")]
POOL_RE = re.compile(rb"[a-z][a-z0-9\-]{1,}")


def main():
    blob = open(EXE, "rb").read()
    runs = [m.group().decode("ascii") for m in POOL_RE.finditer(blob)]
    pool = "\x00".join(runs)
    print("pool: %d identifier runs, %d bytes" % (len(runs), len(pool)))

    def known(tok):
        return tok in pool

    for path in SCRIPTS:
        text = open(path, "rb").read().decode("latin-1")
        used = sorted(set(re.findall(r"\(([a-z][a-z0-9\-]*)", text)))
        defined = set(re.findall(r"\(defconst\s+([a-z0-9\-]+)", text))
        unknown = [t for t in used if not known(t) and t not in defined]
        print("\n== %s" % os.path.basename(path))
        print("   distinct tokens used : %d" % len(used))
        print("   NOT in the exe pool : %d" % len(unknown))
        for t in unknown:
            n = len(re.findall(r"\(" + re.escape(t) + r"[\s\)]", text))
            print("      %-32s %d use(s)" % (t, n))

    watch = ["population-headroom", "housing-headroom", "can-build", "build",
             "difficulty", "hard", "hardest", "set-goal", "timer-triggered",
             "enable-timer", "disable-timer", "chat-to-all", "or", "and",
             "true", "cc-add-resource", "disable-self", "goal"]
    print("\n== spot check of the vocabulary my patches rely on")
    print("   " + ", ".join("%s=%s" % (w, "ok" if known(w) else "MISSING")
                            for w in watch))


if __name__ == "__main__":
    main()
