"""Dump the exe's AI command-name table neighbourhood and collect unit names used in AI scripts."""
import re
import sys

EXE = ("D:\\\u65b0\u5efa\u6587\u4ef6\u5939 (10)\\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       "\\Age of Empires II HD\\AoK HD.exe")


def exe_window(anchor, before=6000, after=4000):
    data = open(EXE, "rb").read()
    i = data.find(anchor.encode())
    print("anchor %r at %d" % (anchor, i))
    chunk = data[max(0, i - before):i + after]
    strings = [s.decode("latin-1") for s in re.findall(rb"[\x20-\x7e]{2,}", chunk)]
    print("--- strings in window ---")
    for s in strings:
        print("   %s" % s)


def unit_names(folder):
    pats = [r"\(train\s+([a-z0-9-]+)", r"\(can-train\s+([a-z0-9-]+)",
            r"unit-type-count-total\s+([a-z0-9-]+)", r"\(build\s+([a-z0-9-]+)"]
    found = {p: {} for p in pats}
    import os
    for name in sorted(os.listdir(folder)):
        txt = open(os.path.join(folder, name), "rb").read().decode("latin-1")
        for p in pats:
            for m in re.finditer(p, txt, re.I):
                u = m.group(1).lower()
                found[p][u] = found[p].get(u, 0) + 1
    for p in pats:
        items = sorted(found[p].items(), key=lambda kv: -kv[1])
        print("--- %s : %d unique ---" % (p, len(items)))
        print("   " + " ".join("%s(%d)" % kv for kv in items))


if __name__ == "__main__":
    exe_window("set-strategic-number")
    unit_names(sys.argv[1] if len(sys.argv) > 1 else "x1_drs")
