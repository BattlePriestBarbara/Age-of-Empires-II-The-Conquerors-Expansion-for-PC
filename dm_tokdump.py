"""dm_tokdump.py -- dump the AI command/token table baked into AoK HD.exe.

Around 0x37372x there is a NUL separated, dot padded list of the AI language
tokens ("#end-if", "#else", "#load-if-not-defined", "defrule", "load-random",
"load" ...).  Dumping the whole block gives the authoritative vocabulary of the
engine, which lets us prove whether a command I wrote is known to the game.
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EXE = (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       r"\Age of Empires II HD\AoK HD.exe")
ANCHOR = b"#load-if-not-defined"
START_BACK, END_FWD = 0x1800, 0x3000


def main():
    blob = open(EXE, "rb").read()
    at = blob.find(ANCHOR)
    print("anchor '#load-if-not-defined' @ 0x%08x" % at)
    lo, hi = max(0, at - 0x4000), min(len(blob), at + 0x14000)
    chunk = blob[lo:hi]
    runs = [t.decode("ascii") for t in re.findall(rb"[ -~]{2,}", chunk)]
    keep = sorted(set(t for t in runs if re.match(r"^[a-z][a-z0-9\-]*$", t)
                      and len(t) >= 3))
    print("region 0x%08x..0x%08x : %d runs, %d distinct command-like\n"
          % (lo, hi, len(runs), len(keep)))
    open("dm_tokdump_all.txt", "w", encoding="utf-8").write("\n".join(keep))

    watch = ["chat-to-all", "chat-to-player", "chat-to-player-using-id",
             "chat-local-to-self", "population-headroom", "housing-headroom",
             "cc-add-resource", "can-build", "build", "difficulty", "hard",
             "hardest", "moderate", "true", "or", "and", "nand", "goal",
             "set-goal", "timer-triggered", "enable-timer", "up-get-fact",
             "up-find-remote", "up-reset-search", "up-full-reset-search",
             "log-trace", "building-type-count-total", "house-count"]
    print("%-30s %s" % ("token", "in engine token pool?"))
    for w in watch:
        print("%-30s %s" % (w, "YES" if w in keep else "*** NO ***"))


if __name__ == "__main__":
    main()
