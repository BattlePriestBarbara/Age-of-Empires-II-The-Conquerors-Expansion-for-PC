"""dm_grep.py -- tiny line-numbered grep over the extracted AI scripts.

usage: python dm_grep.py <file> <regex> [<regex> ...]
"""
import re
import sys

path = sys.argv[1]
pats = [re.compile(p, re.I) for p in sys.argv[2:]]
with open(path, "rb") as fh:
    lines = fh.read().decode("latin-1").split("\n")
print("%s : %d lines" % (path, len(lines)))
for i, line in enumerate(lines, 1):
    if any(p.search(line) for p in pats):
        print("%5d| %s" % (i, line.rstrip()))
