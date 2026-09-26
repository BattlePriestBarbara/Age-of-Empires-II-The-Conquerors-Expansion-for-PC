"""Extract printable ASCII strings from a binary file and grep for keywords."""
import re
import sys

PATTERN = re.compile(rb"[ -~]{4,}")


def scan(path, keywords):
    data = open(path, "rb").read()
    print("FILE: %s size=%d" % (path, len(data)))
    seen = set()
    for m in PATTERN.finditer(data):
        s = m.group().decode("ascii")
        if any(k.lower() in s.lower() for k in keywords):
            if s in seen:
                continue
            seen.add(s)
            print("  @%-9d %s" % (m.start(), s))


if __name__ == "__main__":
    kw = sys.argv[2:]
    scan(sys.argv[1], kw)
