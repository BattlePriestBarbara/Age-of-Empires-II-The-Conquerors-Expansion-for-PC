"""Find occurrences of byte patterns inside files and show surrounding text."""
import sys


def find(path, needles, ctx=120, limit=40):
    data = open(path, "rb").read()
    print("FILE %s size=%d" % (path, len(data)))
    for needle in needles:
        nb = needle.encode()
        idx = 0
        count = 0
        print("--- pattern %r ---" % needle)
        while True:
            idx = data.find(nb, idx)
            if idx < 0:
                break
            chunk = data[max(0, idx - ctx):idx + ctx]
            txt = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
            print("  @%d: %s" % (idx, txt))
            idx += 1
            count += 1
            if count >= limit:
                print("  ... (truncated)")
                break
        if count == 0:
            print("  (none)")


if __name__ == "__main__":
    find(sys.argv[1], sys.argv[2:])
