"""Grep AoE2 AI script text files with context; writes plain ASCII to stdout."""
import os
import re
import sys


def read_text(path):
    raw = open(path, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", "replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", "replace")


def ascii_safe(s, width=170):
    s = "".join(ch if 32 <= ord(ch) < 127 else "." for ch in s)
    return s[:width]


def main():
    folder, pattern = sys.argv[1], sys.argv[2]
    ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    only = sys.argv[4] if len(sys.argv) > 4 else None
    for name in sorted(os.listdir(folder), key=lambda n: (len(n), n)):
        if only and only not in name:
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        lines = read_text(path).splitlines()
        hits = [i for i, ln in enumerate(lines) if re.search(pattern, ln, re.I)]
        if not hits:
            continue
        print("=" * 72)
        print("%s  (%d lines, %d hits)" % (name, len(lines), len(hits)))
        shown = set()
        for i in hits:
            lo = max(0, i - ctx)
            hi = min(len(lines), i + ctx + 1)
            for j in range(lo, hi):
                if j in shown:
                    continue
                shown.add(j)
                mark = "*" if j == i else " "
                print("  %s L%-5d %s" % (mark, j + 1, ascii_safe(lines[j].rstrip())))


if __name__ == "__main__":
    main()
