"""Inventory of AI action tokens used in the DM scripts (validates my patch vocabulary)."""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
FILES = [("x1_drs", "anib_60002.bin"), ("aok_drs", "anib_60002.bin"),
         ("x1_drs", "anib_60029.bin"), ("x1_drs", "anib_60001.bin"),
         ("x1_drs", "anib_60008.bin"), ("x1_drs", "anib_60027.bin")]
out = []
allt = {}
for d, f in FILES:
    p = os.path.join(W, d, f)
    if not os.path.exists(p):
        out.append("missing %s/%s" % (d, f))
        continue
    t = open(p, "rb").read().decode("latin-1")
    toks = set(re.findall(r"\(([a-z][a-z0-9]*(?:-[a-z0-9]+)*)", t))
    out.append("%-10s %-18s %6d lines, %4d distinct tokens" % (d, f, t.count("\n") + 1, len(toks)))
    for x in toks:
        allt[x] = allt.get(x, 0) + 1
    out.append("")

want = ["cc-add-resource", "train", "build", "set-goal", "goal", "enable-timer", "disable-timer",
        "disable-self", "generate-random-number", "up-reset-unit-counts", "reset-unit-counts",
        "set-strategic-number", "population", "population-headroom", "housing-headroom",
        "can-train", "can-build", "unit-type-count", "building-type-count", "building-type-count-total",
        "current-age", "difficulty", "timer-triggered", "strategic-number", "up-get-fact",
        "up-full-reset-search", "up-reset-search", "up-find-remote", "release-escrow",
        "craft-random-number", "random-number", "set-difficulty-parameter", "set-timer"]
out.append("=== tokens used in the DM scripts, checked against my patch vocabulary ===")
for w in want:
    out.append("  %-32s files_using=%d  %s" % (w, allt.get(w, 0), "OK" if allt.get(w) else "*** NOT FOUND ***"))

out.append("")
out.append("=== ALL distinct tokens (sorted) ===")
out.append("  " + " ".join(sorted(allt)))
out.append("")
out.append("=== lines mentioning reset/escrow ===")
for d, f in FILES:
    p = os.path.join(W, d, f)
    if not os.path.exists(p):
        continue
    for i, r in enumerate(open(p, "rb").read().decode("latin-1").split("\n")):
        if "reset" in r or "escrow" in r:
            out.append("  %s/%s %4d| %s" % (d, f, i + 1, r.strip()))

open(os.path.join(W, "dm_tokens_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_tokens_out.txt", len(out), "lines")
