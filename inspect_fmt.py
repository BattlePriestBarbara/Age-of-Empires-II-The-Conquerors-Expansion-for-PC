"""Inspect (a) the byte format of extracted AI scripts, (b) AI engine strings in the exe."""
import binascii
import os
import re
import sys

EXE = ("D:\\\u65b0\u5efa\u6587\u4ef6\u5939 (10)\\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       "\\Age of Empires II HD\\AoK HD.exe")


def fmt_check(path):
    raw = open(path, "rb").read()
    print("== %s size=%d" % (path, len(raw)))
    counts = {}
    for b in raw:
        if b < 32 or b > 126:
            counts[b] = counts.get(b, 0) + 1
    for b in sorted(counts):
        print("   byte 0x%02x (%d times)" % (b, counts[b]))
    txt = raw.decode("latin-1")
    lines = txt.split("\n")
    odd = [ln for ln in lines if any(c not in "\r" and (ord(c) < 32 or ord(c) > 126) for c in ln)]
    for ln in odd[:8]:
        print("   odd line: %r" % ln[:80])


def show_around(path, needle, span=40):
    raw = open(path, "rb").read()
    i = raw.find(needle)
    print("== %s needle=%r at %d" % (path, needle, i))
    if i >= 0:
        print("   %s" % binascii.hexlify(raw[max(0, i - span):i + span + len(needle)]).decode())


def exe_scan(patterns):
    data = open(EXE, "rb").read()
    print("== exe %s size=%d (full path exists: %s)" % (EXE, len(data), os.path.exists(EXE)))
    for pat in patterns:
        b = pat.encode()
        print("   %-28s count=%d" % (pat, data.count(b)))


def exe_strings(regex, limit=400):
    data = open(EXE, "rb").read()
    found = []
    for m in re.finditer(rb"[\x20-\x7e]{3,}", data):
        s = m.group().decode("latin-1")
        if re.fullmatch(regex, s):
            found.append(s)
    seen = []
    for s in found:
        if s not in seen:
            seen.append(s)
    print("== exe strings matching %r: %d unique" % (regex, len(seen)))
    for s in seen[:limit]:
        print("   %s" % s)


if __name__ == "__main__":
    fmt_check("x1_drs/anib_60026.bin")
    fmt_check("x1_drs/anib_60027.bin")
    show_around("x1_drs/anib_60027.bin", b"(defconst NO 0)")
    exe_scan(["add-resource", "defrule", "attack-now", "set-strategic-number",
              "randomgame.per", "unit-type-count-total", "enable-timer", "cc-"])
    exe_strings(r"sn-[a-z0-9-]+")
