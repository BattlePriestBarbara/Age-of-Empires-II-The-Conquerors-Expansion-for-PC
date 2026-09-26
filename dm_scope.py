"""
Audit every rule gated by "(goal secondary-build 1)" in petersen deathmatch.per:
what does it do, and does it carry its own population check (so that the
unconditional re-arm rule can never over-produce)?
"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(W, "x1_drs", "anib_60002.bin")
text = open(path, encoding="latin-1").read()
rows = text.split("\n")


def strip_comment(line):
    out = []
    in_str = False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == ";" and not in_str:
            break
        out.append(ch)
    return "".join(out)


# split the file into top-level s-expressions
rules = []
depth = 0
start = None
for i, r in enumerate(rows):
    code = strip_comment(r)
    if depth == 0 and code.strip().startswith("("):
        start = i
    depth += code.count("(") - code.count(")")
    if depth == 0 and start is not None:
        rules.append((start + 1, i + 1, "\n".join(rows[start:i + 1])))
        start = None

consumers = []
for l0, l1, body in rules:
    if "(goal secondary-build 1)" not in body.replace("\t", ""):
        continue
    if "=>" not in body:
        continue
    cond, _, act = body.partition("=>")
    consumers.append({
        "lines": (l0, l1),
        "cond_pop": bool(re.search(r"\(population\s*<", cond)),
        "cond_dm_pop": bool(re.search(r"\(population\s*<", cond)) and "deathmatch-unit-max" in cond,
        "trains": re.findall(r"\(train[^)]*\)", act),
        "sets_goal_zero": "(set-goal secondary-build 0)" in act.replace("\t", ""),
        "actions": [a.strip() for a in act.replace("\t", "").split("\n") if a.strip()][:4],
    })

out = []
out.append("total top-level forms parsed: %d" % len(rules))
out.append("rules gated by (goal secondary-build 1): %d" % len(consumers))
n_train = sum(1 for c in consumers if c["trains"])
n_pop = sum(1 for c in consumers if c["cond_pop"])
n_dmpop = sum(1 for c in consumers if c["cond_dm_pop"])
n_zero = sum(1 for c in consumers if c["sets_goal_zero"])
out.append("  of those: %d train something, %d carry (population < ...), %d use deathmatch-unit-max, %d reset the goal to 0"
           % (n_train, n_pop, n_dmpop, n_zero))
out.append("  train rules WITHOUT any population guard:")
for c in consumers:
    if c["trains"] and not c["cond_pop"]:
        out.append("    lines %s -> %s   %s" % (c["lines"], c["trains"], c["actions"]))
out.append("")
out.append("first 12 consumers:")
for c in consumers[:12]:
    out.append("  %s pop-gate=%s dm-max=%s zero=%s %s %s"
               % (c["lines"], c["cond_pop"], c["cond_dm_pop"], c["sets_goal_zero"], c["trains"], c["actions"][:2]))
txt = "\n".join(out)
open(os.path.join(W, "dm_scope_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
