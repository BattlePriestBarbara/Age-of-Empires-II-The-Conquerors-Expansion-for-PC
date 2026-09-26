"""dm_readme_verify.py -- final sanity check of the rewritten README."""
import io
import os

W = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(W, "HD_DM_AI_PATCH_README.md")

raw = open(PATH, "rb").read()
text = raw.decode("utf-8")
lines = text.splitlines()
crlf = text.count("\r\n")
lf = text.count("\n") - crlf
fence = chr(96) * 3
fences = [i + 1 for i, ln in enumerate(lines) if ln.startswith(fence)]
heads = [(i + 1, ln) for i, ln in enumerate(lines) if ln.startswith("#")]

print("file        : %s" % PATH)
print("bytes       : %d   lines: %d   CRLF: %d   bare LF: %d"
      % (len(raw), len(lines), crlf, lf))
print("BOM         : %s" % raw[:3].hex())
print("code fences : %d (even=%s) at %s" % (len(fences), len(fences) % 2 == 0,
                                             fences))
print("tab chars   : %d" % text.count("\t"))
print("")
print("=== headings")
for n, h in heads:
    print("%4d| %s" % (n, h[:96]))
print("")
for probe in ("本次更新（根因 D）", "catch-all 兜底常量块", "v2 补丁",
              "根因 D 的更正", "dm_popstr.py", "DM AI fix v2 loaded",
              "deathmatch-unit-max` = 170"):
    print("contains %-30s : %s" % (probe, probe in text))

# markdown table sanity: every table block must have a |---| separator row
bad = []
in_table = 0
for i, ln in enumerate(lines, 1):
    if ln.startswith("|"):
        in_table += 1
    else:
        if in_table == 1:
            bad.append(i - 1)
        in_table = 0
print("\nsingle-row table blocks (should be none): %s" % bad)
