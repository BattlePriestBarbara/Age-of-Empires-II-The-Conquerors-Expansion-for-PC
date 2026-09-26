"""Analyze extracted AoE2 AI script files: list them and grep patterns with context."""
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


def show(folder, pattern=None, max_lines=4, head_lines=8):
    print("#" * 72)
    print("# FOLDER", folder)
    files = sorted(os.listdir(folder), key=lambda n: (len(n), n))
    for name in files:
        path = os.path.join(folder, name)
        txt = read_text(path)
        lines = txt.splitlines()
        print("-" * 72)
        print("%s  size=%d lines=%d" % (name, os.path.getsize(path), len(lines)))
        for ln in lines[:head_lines]:
            if ln.strip():
                print("    | %s" % ln[:150])
        if pattern:
            for i, ln in enumerate(lines):
                if re.search(pattern, ln, re.I):
                    print("    * L%-5d %s" % (i + 1, ln.strip()[:170]))
                    for extra in lines[i + 1:i + max_lines]:
                        print("      +      %s" % extra.strip()[:170])


if __name__ == "__main__":
    show(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
