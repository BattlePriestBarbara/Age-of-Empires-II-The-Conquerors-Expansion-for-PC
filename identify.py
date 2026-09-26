"""Print head lines of every extracted AI script so the files can be identified."""
import os
import sys


def read_text(path):
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", "replace")


def main():
    folder = sys.argv[1]
    head = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    prefix = sys.argv[3] if len(sys.argv) > 3 else "anib_60"
    for name in sorted(os.listdir(folder)):
        if not name.startswith(prefix):
            continue
        path = os.path.join(folder, name)
        txt = read_text(path)
        lines = [l for l in txt.splitlines() if l.strip()]
        print("-" * 72)
        print("%s size=%d lines=%d" % (name, os.path.getsize(path), len(lines)))
        for ln in lines[:head]:
            s = "".join(ch if 32 <= ord(ch) < 127 else "." for ch in ln.strip())
            print("   | %s" % s[:160])


if __name__ == "__main__":
    main()
