"""
Build the Age of Empires II HD Deathmatch AI patch.

Patch targets (all appended at the very end of the script):

  anib_60002  =  "petersen deathmatch.per"
                (loaded ONLY in death-match games, from "petersen random game",
                 i.e. #load-if-defined DEATH-MATCH in anib_60026)
  anib_60027  =  "petersen constants.per" of the Conquerors data (gamedata_x1.drs)
  anib_60010  =  constants of the Age of Kings data (gamedata.drs)

Four fixes:

 1. continuous unit production
    The per-civ unit blocks are gated by "(goal secondary-build 1)".
    Every unit rule ends with "(set-goal secondary-build 0)" and the only
    re-arm rule in the original file is
        (can-train my-unique-unit-line) -> (train my-unique-unit-line) (set-goal secondary-build 1)
    i.e. re-arming needs a trainable unique unit (a castle for most civs,
    which the AI does not have in death-match).  Result: the goal stays 0
    after the first trained unit and the AI stops producing units.
    Fix: re-arm the goal unconditionally.

 2. population growth
    The original file only builds houses for
        (difficulty <= moderate)  /  DIFFICULTY-EASIEST  /  DIFFICULTY-EASY.
    On HARD / HARDEST there is *no* house rule in the whole death-match
    script, so population hits the starting housing limit and production
    stops.  Fix: add the same house rule for hard/hardest.

 3. unlimited resources
    Shipped idiom: (cc-add-resource <res> <amount>)  (used by anib_60001,
    anib_60008, anib_60029 - but NOT by anib_60002).
    Fix: heartbeat on timer 3 ("t-production", unused by the death-match
    script set) that tops all four resources up whenever any of them
    drops below the threshold.
  4. the AI dies completely at population limits the engine does not know,
     e.g. 500 (touches anib_60027 / anib_60010)
     The engine only ever defines one of the symbols POPULATION-CAP-25 ...
     POPULATION-CAP-200 (that symbol table sits inside AoK HD.exe, see
     dm_exe_ai.py).  At a lobby limit of 500 none of them is defined, and the
     retail constants files define

         civ-dark-rush, civ-dark, civ-castle, deathmatch-unit-max, unit-max,
         five/ten/fifteen/twenty/thirty/fifty-percent-pop, town sizes, ...

     ONLY inside those #load-if-defined blocks - with no defaults anywhere else.
     An undefined constant makes every rule that mentions it invalid, so the
     death-match script (56 x deathmatch-unit-max, 56 x unit-max, ...) stops
     firing almost completely: no villagers, no houses, no army
     ("only one villager is working").  Fix: append a catch-all block that is
     compiled only when none of the 8 classic caps is active and repeats the
     POPULATION-CAP-200 block scaled to a 500-slot game (2.5x; town sizes keep
     their cap-200 values).
"""
import os
import re
import sys

W = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(W, "patch_out")
sys.path.insert(0, W)

import dm_const_audit as audit  # noqa: E402  (constant-usage cross-check)

RES_THRESHOLD = 5000
RES_TOPUP = 10000
RES_TIMER = "t-production"          # defconst t-production 3 (anib_60027), timer 3 is unused in DM
HOUSE_HEADROOM = 10

HEADER = """\
;##############################################################################
;##  HD DEATH-MATCH AI PATCH  (appended by dm_patch.py)                      ##
;##                                                                          ##
;##  1. keeps "(goal secondary-build 1)" armed  -> the per-civ unit rules     ##
;##     of this script keep training units for ever (originally the goal was  ##
;##     only re-armed by the unique-unit rule, which needs a castle)          ##
;##  2. builds houses on hard/hardest too (the original file only houses on   ##
;##     difficulty <= moderate, so population was stuck at the start limit)   ##
;##  3. tops up food/wood/gold/stone whenever any of them drops below 5000    ##
;##############################################################################
"""

REARM_RULE = """\
;---- 1) keep the unit-production loop permanently armed ----------------------
(defrule
\t(goal secondary-build 0)
=>
\t(set-goal secondary-build 1)
)
"""

HOUSE_RULE = """\
;---- 2) keep building houses on the harder difficulties ----------------------
(defrule
\t(or
\t\t(difficulty == hard)
\t\t(difficulty == hardest)
\t)
\t(housing-headroom < %d)
\t(population-headroom > 0)
\t(can-build house)
=>
\t(build house)
)
""" % HOUSE_HEADROOM

RESOURCE_RULES = """\
;---- 3) effectively unlimited resources --------------------------------------
(defrule
\t(true)
=>
\t(enable-timer %s 10)
\t(disable-self)
)

(defrule
\t(timer-triggered %s)
\t(or
\t\t(food-amount < %d)
\t\t(wood-amount < %d)
\t\t(gold-amount < %d)
\t\t(stone-amount < %d)
\t)
=>
\t(disable-timer %s)
\t(enable-timer %s 5)
\t(cc-add-resource food %d)
\t(cc-add-resource wood %d)
\t(cc-add-resource gold %d)
\t(cc-add-resource stone %d)
)
""" % (RES_TIMER, RES_TIMER,
       RES_THRESHOLD, RES_THRESHOLD, RES_THRESHOLD, RES_THRESHOLD,
       RES_TIMER, RES_TIMER,
       RES_TOPUP, RES_TOPUP, RES_TOPUP, RES_TOPUP)

# ------------------------------------------------------- fix 4: constants ----
# Catch-all for population limits the engine does not know (e.g. 500).
CONST_TARGETS = [
    ("x1_drs", "anib_60027.bin"),        # Conquerors constants, gamedata_x1.drs
    ("aok_drs", "anib_60010.bin"),       # Age of Kings constants, gamedata.drs
]
CAP_TEMPLATE = 200          # the block that is copied (and scaled)
CAP_TARGET = 500            # the lobby limit this patch is tuned for
SCALE = float(CAP_TARGET) / CAP_TEMPLATE            # 2.5
CLASSIC_CAPS = (25, 50, 75, 100, 125, 150, 175, 200)
# things that are *map distances / building counts*, not population shares:
# they keep their well tested cap-200 values
KEEP_AS_IS = ("feudal-town-size", "castle-town-size", "imperial-town-size",
              "town-center-count")
DEFCONST_RE = re.compile(r"^(\s*)\(defconst\s+([A-Za-z0-9\-_]+)\s+(\d+)\s*\)\s*$")

CONST_HEADER = """\
;##############################################################################
;##  HD DEATH-MATCH AI PATCH - catch-all for unknown population limits        ##
;##                                                                          ##
;##  Problem: the engine defines only POPULATION-CAP-25/50/75/100/125/150/   ##
;##  175/200 (that symbol table lives in AoK HD.exe).  At any other lobby    ##
;##  limit - e.g. 500 - NOT ONE of them is defined, so every constant the    ##
;##  retail file defines *only* inside those blocks (deathmatch-unit-max,     ##
;##  unit-max, civ-*, *-percent-pop, town sizes ...) stays undefined.  A rule ##
;##  that mentions an undefined constant is invalid, which killed the whole   ##
;##  death-match AI: no villagers, no houses, no army.                        ##
;##                                                                          ##
;##  Fix: this block is compiled only if none of the 8 classic caps is        ##
;##  active.  It repeats the POPULATION-CAP-200 block scaled to a %d slot      ##
;##  game (x%.1f); town sizes keep their cap-200 values.                     ##
;##############################################################################
""" % (CAP_TARGET, SCALE)


def cap_block(rows, cap):
    """Return the body lines of the `#load-if-defined POPULATION-CAP-<cap>` block."""
    head = "#load-if-defined POPULATION-CAP-%d" % cap
    for i, r in enumerate(rows):
        if r.strip() == head:
            break
    else:
        raise AssertionError("no %r block in this file" % head)
    depth = 1
    body = []
    for r in rows[i + 1:]:
        s = r.strip()
        if s.startswith("#load-if-defined") or s.startswith("#load-if-not-defined"):
            depth += 1
        elif s.startswith("#end-if"):
            depth -= 1
            if depth == 0:
                return body
        body.append(r)
    raise AssertionError("unterminated %r block" % head)


def scale_block(body):
    """Copy the cap-200 block, scaling the population derived numbers."""
    out, changed = [], []
    for r in body:
        m = DEFCONST_RE.match(r)
        if m and m.group(2) not in KEEP_AS_IS:
            old = int(m.group(3))
            new = int(old * SCALE + 0.5)
            changed.append((m.group(2), old, new))
            r = "%s(defconst %s %d)" % (m.group(1), m.group(2), new)
        out.append(r)
    return out, changed


def constants_patch(src):
    """Build the catch-all constants block for one constants file."""
    rows = [x.rstrip("\r") for x in open(src, "rb").read().decode("latin-1").split("\n")]
    lines = CONST_HEADER.rstrip("\n").split("\n")
    for cap in CLASSIC_CAPS:
        lines.append("#load-if-not-defined POPULATION-CAP-%d" % cap)
    body, changed = scale_block(cap_block(rows, CAP_TEMPLATE))
    lines.extend(body)
    lines.extend(["#end-if"] * len(CLASSIC_CAPS))
    defined = set()
    for r in body:
        m = DEFCONST_RE.match(r)
        if m:
            defined.add(m.group(2))
    return "\r\n".join(lines) + "\r\n", changed, defined


def constants_check(const_rows, dm_src, fallback_defined):
    """Every cap-only constant the DM script uses must now be defined."""
    in_caps, other = audit.scan_constants("\n".join(const_rows))
    dm = open(dm_src, "rb").read().decode("latin-1")
    missing = []
    for name in sorted(in_caps):
        if name in other or name in fallback_defined:
            continue
        if re.search(r"(?<![A-Za-z0-9\-_])%s(?![A-Za-z0-9\-_])" % re.escape(name), dm):
            missing.append((name, in_caps[name][0]))
    return missing




def preprocessor_balance(rows):
    depth = 0
    bad = []
    for i, r in enumerate(rows):
        s = r.strip()
        if s.startswith("#load-if-defined") or s.startswith("#load-if-not-defined"):
            depth += 1
        elif s.startswith("#if") and not s.startswith("#ifdef") and not s.startswith("#ifndef"):
            depth += 1
        elif s.startswith("#else"):
            pass
        elif s.startswith("#end-if"):
            depth -= 1
            if depth < 0:
                bad.append((i + 1, s))
                depth = 0
    return depth, bad


def main():
    os.makedirs(OUT, exist_ok=True)
    patch = HEADER + REARM_RULE + HOUSE_RULE + RESOURCE_RULES
    patch = patch.replace("\n", "\r\n")           # DRS AI files use CRLF
    report = []
    for d in ("aok_drs", "x1_drs"):
        src = os.path.join(W, d, "anib_60002.bin")
        raw = open(src, "rb").read()
        text = raw.decode("latin-1")
        rows = [x.rstrip("\r") for x in text.split("\n")]
        depth, bad = preprocessor_balance(rows)
        report.append("%s: %d bytes, %d lines, final #if depth=%d, stray #end-if=%s"
                      % (d, len(raw), len(rows), depth, bad))
        # preprocessor must be balanced, otherwise appended rules could sit in a false branch
        assert depth == 0, "unbalanced preprocessor in %s" % src
        assert not bad, "stray #end-if in %s" % src
        assert rows[-1] == "", "file does not end with a newline: %s" % src
        new = text + patch
        dst = os.path.join(OUT, d + "_anib_60002.bin")
        open(dst, "wb").write(new.encode("latin-1"))
        report.append("  -> %s  (%d bytes, +%d)" % (dst, len(new), len(new) - len(raw)))

    report.append("")
    report.append("=== fix 4: catch-all constants for population limits the engine does not know")
    report.append("    (engine only knows %s -> at e.g. 500 none of them is defined)"
                  % "/".join(str(c) for c in CLASSIC_CAPS))
    for folder, fname in CONST_TARGETS:
        src = os.path.join(W, folder, fname)
        raw = open(src, "rb").read()
        text = raw.decode("latin-1")
        rows = [x.rstrip("\r") for x in text.split("\n")]
        depth, bad = preprocessor_balance(rows)
        assert depth == 0, "unbalanced preprocessor in %s (%d, %s)" % (src, depth, bad)
        assert not bad, "stray #end-if in %s" % src
        if not text.endswith("\n"):
            # the retail anib_60010 ends without a newline - add one so the
            # appended block starts on its own line
            text += "\r\n"
        block, changed, defined = constants_patch(src)
        new = (text + block).encode("latin-1")
        dst = os.path.join(OUT, "%s_%s" % (folder, fname))
        open(dst, "wb").write(new)
        report.append("%s/%s: %d -> %d bytes (+%d), catch-all defines %d constants, "
                      "scaled x%.1f to cap %d"
                      % (folder, fname, len(raw), len(new), len(new) - len(raw),
                         len(defined), SCALE, CAP_TARGET))
        for name, old, val in changed:
            report.append("    %-22s %4d -> %d" % (name, old, val))
        for name in KEEP_AS_IS:
            if name in defined:
                report.append("    %-22s kept at the cap-%d value" % (name, CAP_TEMPLATE))
        # the DM script of the same data set must not be left with undefined constants
        missing = constants_check(rows, os.path.join(W, folder, "anib_60002.bin"), defined)
        assert not missing, "still undefined for the DM script: %s" % missing
        report.append("  cross-check against %s/anib_60002.bin: every population-cap "
                      "constant it uses is covered" % folder)
        report.append("  -> %s" % dst)
    print("\n".join(report))
    open(os.path.join(W, "dm_patch_report.txt"), "w", encoding="utf-8").write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
