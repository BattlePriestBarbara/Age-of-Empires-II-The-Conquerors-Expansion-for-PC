"""Print all printable ASCII strings (>=4 chars) within a byte range of a file."""
import re
import sys

PATTERN = re.compile(rb"[ -~]{4,}")


def main():
    path, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    data = open(path, "rb").read()[start:end]
    for m in PATTERN.finditer(data):
        print("  @%-9d %s" % (start + m.start(), m.group().decode("ascii")))


if __name__ == "__main__":
    main()
