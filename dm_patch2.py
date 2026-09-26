"""
Build v3 of the Age of Empires II HD death-match AI fix.

v3 repairs the single hard error the v2 block produced in game:

    Player 8   File  petersen deathmatch per
    Line 3021: ERR2011: Missing closing parenthesis

Cause, measured instead of guessed: AoK HD.exe gives every logical condition
block (or / and / nor / not) exactly **two** argument slots.  A census of every
shipped AI script (dm_blockshape.py) shows that not one block anywhere in the
game has more than two children - the retail authors always *nest* two-child
blocks instead.  The retail "resources are low" tests of the death-match script
itself are the perfect twin of the rule that failed (lines 1511-1523 and
1533-1542):

    (defrule
        (strategic-number sn-percent-civilian-gatherers == 85)
        (or
            (or
                (wood-amount < 500)
                (food-amount < 500)
            )
            (or
                (gold-amount < 500)
                (stone-amount < 100)
            )
        )
    =>
        ...

v2's S1 rule fed a single (or ...) **four** children.  The parser took the
first two, then wanted the closing parenthesis, found the third child instead
and reported ERR2011 on that child's line (3021 = "(gold-amount < 5000)"); the
remainder of the file was dropped.

v3 writes the identical condition in the retail nesting shape above, and
verify_retail_shapes() now enforces both shape rules - at most two children per
logical block, and no fact arity that no shipped script uses - so this class of
error cannot come back unnoticed.

Why a v2?  v1 (dm_patch.py) patched

  * anib_60002 "petersen deathmatch"  - house rule, unit re-arm, resources
  * anib_60027 / anib_60010 "petersen constants" - catch-all constant block

and the game behaviour did not change.  Two later findings destroyed v1's
assumptions:

  * the catch-all block was pointless: AoK HD.exe maps a 500 slot population
    limit onto POPULATION-CAP-200 (dm_popswitch.py), so the retail constants
    were always defined; the block was dead code (it also carried a wrong
    "root cause D" story into the shipped archive).
  * gamedata_x1_p1.drs contains no AI script at all (dm_p1check.py), so the
    patch really was in the archive the engine reads.

v2 therefore rebuilds the death-match script from the pristine backup (never
from the already patched file, so a patch can never stack) and appends a block
whose rules are *copies of the retail rules* with nothing but the difficulty /
human-player gates removed.  Every fact, every action and every constant used
below occurs verbatim in the shipped scripts - dm_patch2.py proves that
automatically (the "token attestation" part of the report) before writing the
payloads, because in this AI dialect an unknown keyword invalidates the rule
without any visible error.

What is appended (the dataset tag [x1]/[aok] appears only in the chat text):

  M1  in-game proof that this script runs: one "chat-to-all" line at start-up
  H1  retail 1675-1680  (building-type-count-total house <= fifteen-percent-pop)
  H2  retail 1694-1701  ((housing-headroom < 5) (population-headroom > 0))
  H3  retail 1683-1690  (same, but (military-population < 10))
      The three retail house rules sit inside "(difficulty <= moderate)",
      "#load-if-defined DIFFICULTY-EASIEST" and "#load-if-defined
      DIFFICULTY-EASY" blocks, so HARD and HARDEST compile no house rule at
      all and unit production stalls at the starting housing.
  H4  timer-driven house maintenance: 30 s after start and then every 20 s,
      build one while the AI owns fewer than HOUSES_MAX houses - independent of
      the meaning of the two headroom facts on this engine build.
  A1  retail 1594-1604 (feudal age)   }  retail wraps every age rule in
  A2  retail 1614-1624 (castle age)   }  (or (players-current-age every-human
  A3  retail 1634-1647 (imperial age) }  >= <age>) (difficulty <= moderate))
      so in a death-match game without a human player the AI stays in the dark
      age for ever.  Conditions, actions, t-ageup timer and age-advancement
      goal stay exactly as shipped.
  R1  re-arm "(goal secondary-build 1)": the retail file clears that goal in
      all 50 unit rules and re-arms it only in the unique-unit rule (line
      2343), which needs a castle - so the AI trains one unit and stops.
  S1  resource top-up on retail timer index 2 ("t-attackgroup", declared by the
      constants file and triggered by no death-match rule) plus the start-up
      rule that enables it.  The "any resource is low" test uses the two-child
      nested (or ...) shape of retail lines 1511-1523 / 1533-1542, because the
      engine accepts at most two children per logical block.
"""
import hashlib
import os
import re
import sys

W = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(W, "patch_out2")
BACKUP = os.path.join(W, "backup_drs")
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
EXE = os.path.join(GAME, "AoK HD.exe")

V1_MARKER = b"HD DEATH-MATCH AI PATCH"
V2_MARKER = b"AI FIX V2"         # superseded: it carried the 4-child (or ...)
MARKER = b"AI FIX V3"            # header comment of the appended death-match block
BASE_MARKER = b"AI FIX BASE"     # header comment of the anib_60001 marker block

# every block an earlier version of this script appended; used to cut a stale
# tail off if the source archive is not pristine after all
OLD_MARKERS = (V1_MARKER, V2_MARKER)


def has_marker(payload, marker):
    return marker.lower() in payload.lower()

HOUSES_MAX = 40                  # 40 * 5 = 200 population slots
HOUSE_TIMER_TIME = 30            # first house check, seconds after start
HOUSE_TIMER_REPEAT = 20          # then every 20 s
RES_TIMER_TIME = 10              # first resource check
RES_TIMER_REPEAT = 60            # then every 60 s (rarely needed at all)

# Timer names.  This dialect has no (defconst ...) inside the death-match script
# at all; every "t-..." name is declared in the constants file of the dataset
# (anib_60027: t-tribute 1, t-attackgroup 2, t-production 3, t-chat 5,
#  t-chathelp 6, t-tower 7, t-chatmore 8, t-lumbercamp 9, t-ageup 10) and index
# 4 has no name.  A name of my own would therefore be an undefined symbol, and
# the ships-with-the-game rule (unknown symbol = rule silently dropped) makes
# that unusable, so two retail names that no death-match script touches are
# reused instead:
#   t-tribute     index 1 - 60001/60002 use 10, 9 and 3/8/6/5, never 1 or 2
#   t-attackgroup index 2 - same, and the other users (60013/60017/60021,
#                           60020/60029) are not loaded in a death match
HOUSE_TIMER = "t-tribute"        # retail index 1, unused by the DM scripts
RES_TIMER = "t-attackgroup"      # retail index 2, unused by the DM scripts

DATASETS = [
    # folder in the work dir, archive in <game>\Data, dataset tag for the chat
    ("x1_drs", "gamedata_x1.drs", "x1"),
    ("aok_drs", "gamedata.drs", "aok"),
]

# tokens that are allowed to be new: none - the patch only uses shipped symbols
OWN_TOKENS = ()

# ---------------------------------------------------------------------------
# The appended blocks.  No "%-formatting" on purpose: @T@ etc. are replaced
# with str.replace() below so that the comments may contain any character.
# ---------------------------------------------------------------------------
CHAT_RULE = """\
;##############################################################################
;##  HD DEATH-MATCH AI FIX v3              (appended by dm_patch2.py)        ##
;##############################################################################

;------------------------------------------------------------------------------
; 0.  M1 - in-game proof that the engine runs this patched script: the AI
;     says so in the chat panel at start-up.  The number in the text also
;     separates this build from the superseded one: that build's start-up line
;     still ended in the tag but its number was one lower, and it tripped
;     ERR2011 (missing closing parenthesis) at line 3021 - see the header of
;     this file for the measured reason.
;------------------------------------------------------------------------------
(defrule
\t(true)
=>
\t(chat-to-all "DM AI fix v3 loaded [@TAG@]")
\t(disable-self)
)
"""

HOUSE_RULES = """\

;------------------------------------------------------------------------------
; 1.  H1 - the retail house rule of the "(difficulty <= moderate)" block
;     (line 1675-1680), gate removed
;------------------------------------------------------------------------------
(defrule
\t(building-type-count-total house <= fifteen-percent-pop)
\t(can-build house)
=>
\t(build house)
)

;------------------------------------------------------------------------------
; 2.  H2 - the retail house rule of the "#load-if-defined DIFFICULTY-EASY"
;     block (line 1694-1701); "(military-population < civ-dark-rush)" dropped
;     because it is a difficulty handicap, not a housing requirement
;------------------------------------------------------------------------------
(defrule
\t(housing-headroom < 5)
\t(population-headroom > 0)
\t(can-build house)
=>
\t(build house)
)

;------------------------------------------------------------------------------
; 3.  H3 - the retail house rule of the "#load-if-defined DIFFICULTY-EASIEST"
;     block (line 1683-1690); "(military-population < 10)" dropped
;------------------------------------------------------------------------------
(defrule
\t(housing-headroom < 5)
\t(can-build house)
=>
\t(build house)
)

;------------------------------------------------------------------------------
; 4.  H4 - housing safety net that does not depend on the meaning of the two
;     headroom facts: while the AI owns fewer than @H@ houses (@H@ x 5 = @S@
;     population slots), build one - first check @TT@ s after start, then
;     every @TR@ s.  Timer @HT@ is retail timer index 1 (declared in the
;     constants file) and is touched by neither anib_60001 nor anib_60002.
;------------------------------------------------------------------------------
(defrule
\t(true)
=>
\t(enable-timer @HT@ @TT@)
\t(disable-self)
)
(defrule
\t(timer-triggered @HT@)
\t(building-type-count-total house < @H@)
\t(can-build house)
=>
\t(build house)
)
(defrule
\t(timer-triggered @HT@)
=>
\t(disable-timer @HT@)
\t(enable-timer @HT@ @TR@)
)
"""

AGE_RULES = """\

;------------------------------------------------------------------------------
; 5.  A1-A3 - the three retail age rules, lines 1594-1604 (feudal),
;     1614-1624 (castle) and 1634-1647 (imperial), with their
;         (or (players-current-age every-human >= <age>) (difficulty <= moderate))
;     gate removed.  Conditions, actions, the t-ageup timer and the
;     age-advancement goal are the retail ones, so the retail rules that react
;     to t-ageup (lines 1606-1612, 1626-1632, 1658-1671) keep working.
;------------------------------------------------------------------------------
(defrule
\t(can-research feudal-age)
=>
\t(research feudal-age)
\t(set-goal age-advancement NOTICE)
\t(enable-timer t-ageup 140)
)
(defrule
\t(can-research castle-age)
=>
\t(research castle-age)
\t(set-goal age-advancement NOTICE)
\t(enable-timer t-ageup 170)
)
(defrule
\t(can-research imperial-age)
=>
\t(research imperial-age)
\t(set-goal age-advancement NOTICE)
\t(enable-timer t-ageup 200)
)
"""

REARM_RULE = """\

;------------------------------------------------------------------------------
; 6.  R1 - keep the per-civ unit rules armed.  The retail file clears
;     "(goal secondary-build 1)" in all 50 unit rules and re-arms it only in
;     the unique-unit rule (line 2343), which needs a castle; in death-match
;     the AI has none, so the goal stays 0 and production stops.
;------------------------------------------------------------------------------
(defrule
\t(goal secondary-build 0)
=>
\t(set-goal secondary-build 1)
)
"""

RESOURCE_RULES = """\

;------------------------------------------------------------------------------
; 7.  S1 - top the four resources up (shipped idiom "(cc-add-resource
;     <resource> <amount>)": anib_60001 uses amounts from 100 to 10000, so the
;     10000 below is a shipped value too).  Timer @T@ is retail timer index 2:
;     the constants file declares it and no death-match rule triggers it, so
;     the countdown below is its only user.  The resources test is written as
;     the two-child nested (or ...) that retail uses for exactly this check
;     (lines 1511-1523 and 1533-1542) - a block with more than two children is
;     what made v2 die with "ERR2011: Missing closing parenthesis".
;------------------------------------------------------------------------------
(defrule
\t(true)
=>
\t(enable-timer @T@ @RT@)
\t(disable-self)
)
(defrule
\t(timer-triggered @T@)
\t(or
\t\t(or
\t\t\t(wood-amount < 5000)
\t\t\t(food-amount < 5000)
\t\t)
\t\t(or
\t\t\t(gold-amount < 5000)
\t\t\t(stone-amount < 5000)
\t\t)
\t)
=>
\t(cc-add-resource wood 10000)
\t(cc-add-resource food 10000)
\t(cc-add-resource gold 10000)
\t(cc-add-resource stone 10000)
)
(defrule
\t(timer-triggered @T@)
=>
\t(disable-timer @T@)
\t(enable-timer @T@ @RR@)
)
"""

# appended to "petersen rules" (anib_60001), loaded in *every* game: marker
# only, no behaviour change - it tells a dead death-match fix apart from
# "the engine is not reading the archive we patched"
BASE_RULE = """\

;------------------------------------------------------------------------------
;  HD AI FIX BASE - marker only, no behaviour change.
;------------------------------------------------------------------------------
(defrule
\t(true)
=>
\t(chat-to-all "AI fix base loaded [@TAG@]")
\t(disable-self)
)
"""

def strip_v1(text, markers=OLD_MARKERS):
    """remove a patch block appended by an earlier version of this script

    v1 and v2 both appended their block at EOF and opened it with a header
    comment that carries their marker, so cutting at the beginning of the
    earliest marker line restores the shipped script exactly.  Returns
    (text, removed_bytes).
    """
    raw = text.encode("latin-1")
    hits = [raw.find(m) for m in markers]
    hits = [h for h in hits if h >= 0]
    if not hits:
        return text, 0
    idx = min(hits)
    line_start = raw.rfind(b"\n", 0, idx) + 1
    return raw[:line_start].decode("latin-1"), len(raw) - line_start


def build_dm_block(tag):
    block = CHAT_RULE + HOUSE_RULES + AGE_RULES + REARM_RULE + RESOURCE_RULES
    for key, val in (("@TAG@", tag),
                     ("@TT@", str(HOUSE_TIMER_TIME)),
                     ("@TR@", str(HOUSE_TIMER_REPEAT)),
                     ("@RT@", str(RES_TIMER_TIME)),
                     ("@RR@", str(RES_TIMER_REPEAT)),
                     ("@HT@", HOUSE_TIMER),
                     ("@S@", str(HOUSES_MAX * 5)),
                     ("@H@", str(HOUSES_MAX)),
                     ("@T@", RES_TIMER)):
        block = block.replace(key, val)
    assert "@" not in code_only(block), "unsubstituted placeholder in the dm block"
    return block.replace("\n", "\r\n")


def build_base_block(tag):
    block = BASE_RULE.replace("@TAG@", tag)
    assert "@" not in code_only(block), "unsubstituted placeholder in the base block"
    return block.replace("\n", "\r\n")


def attestation_sources():
    """name -> text of every shipped AI script plus the exe keyword tables"""
    out = []
    for folder, _archive, _tag in DATASETS:
        for name in ("anib_60002.bin", "anib_60027.bin", "anib_60010.bin",
                     "anib_60001.bin", "anib_60029.bin", "anib_60008.bin",
                     "anib_60003.bin", "anib_60026.bin"):
            path = os.path.join(W, folder, name)
            if os.path.exists(path):
                out.append(("%s/%s" % (folder, name),
                            open(path, "rb").read().decode("latin-1")))
    data = open(EXE, "rb").read()
    exe_text = " ".join(m.group().decode("ascii")
                        for m in re.finditer(rb"[ -~]{4,}", data))
    out.append(("AoK HD.exe keyword tables", exe_text))
    return out


def code_only(text):
    """drop comments and string literals, one *line* at a time

    Doing this per line matters: a quoted word inside a comment of a shipped
    script, e.g. the "(difficulty <= moderate)" of the retail comments, would
    otherwise pair with a quote several lines further down and swallow every
    newline in between - which silently moves all following line numbers.  That
    bug made the first version of this helper miss the in-game error line by
    one.
    """
    out = []
    for line in text.split("\n"):
        buf, in_str = [], False
        for ch in line:
            if ch == '"':
                if in_str:
                    in_str = False
                    buf.append('""')            # one placeholder per literal
                else:
                    in_str = True
                continue
            if in_str:
                continue
            if ch == ";":
                break
            buf.append(ch)
        out.append("".join(buf))
    return "\n".join(out)


def tokens_of(text):
    return sorted(set(re.findall(r"[a-z][a-z0-9-]*", code_only(text))))


def check_uppercase(block, sources):
    """uppercase words are enum names in this dialect (NOTICE, ...).

    The lowercase sweep cannot see them, so they get their own check; they must
    appear in one of the shipped scripts.
    """
    up = sorted(set(re.findall(r"[A-Z][A-Z0-9-]+", code_only(block))))
    bad = [tok for tok in up if not any(tok in text for _name, text in sources)]
    return up, bad


def check_tokens(block, sources):
    ok, bad = [], []
    for tok in tokens_of(block):
        if tok in OWN_TOKENS:
            ok.append((tok, "introduced by this patch (allowed: %s)" % ", ".join(OWN_TOKENS)))
            continue
        where = next((name for name, text in sources if tok in text), None)
        if where:
            ok.append((tok, where))
        else:
            bad.append(tok)
    return ok, bad


def paren_balance(text):
    depth = 0
    for i, line in enumerate(text.split("\n")):
        line = re.sub(r";.*$", "", line)
        depth += line.count("(") - line.count(")")
        if depth < 0:
            return depth, i + 1
    return depth, None


def preprocessor_balance(rows):
    """returns (depth, stray closing lines, openers, closers)

    counts every "#load-if-defined" *and* "#load-if-not-defined" as an opener,
    which the first version of this helper forgot.
    """
    depth, bad, n_open, n_close = 0, [], 0, 0
    for i, s in enumerate(rows):
        t = s.strip().lower()
        if t.startswith("#else"):
            continue
        if t.startswith("#load-if") or t.startswith("#if"):
            depth += 1
            n_open += 1
        elif t.startswith("#end-if"):
            depth -= 1
            n_close += 1
            if depth < 0:
                bad.append((i + 1, s))
                depth = 0
    return depth, bad, n_open, n_close


# ---------------------------------------------------------------------------
# The two shape rules of this AI dialect.  They are the lesson of the in-game
# "ERR2011: Missing closing parenthesis" that v2 produced, and they are
# *measured* from the shipped scripts (dm_blockshape.py):
#   * no logical block in the whole game carries more than two children
#   * every fact is used with an argument count that retail also uses
# ---------------------------------------------------------------------------
BLOCK_KW = ("or", "and", "nor", "not")
TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")
MAX_BLOCK_CHILDREN = 2

# Shapes the patch uses on purpose although no shipped *script* uses them.
# Deliberately tiny and justified one by one; everything else must be shipped.
SHAPE_EXCEPTIONS = {
    ("chat-to-all", 1):
        "M1, the in-game 'this patched script is running' marker.  chat-to-all "
        "is in the exe AI keyword table and takes one string; the shipped "
        "scripts only ever call the localised chat-to-all-using-id variant, so "
        "no shipped script attests the argument form.  AoK HD.exe does lex "
        "string literals (it ships ERR2010 'Missing closing quote'), and the v2 "
        "run reported no error for M1 although M1 sits at line ~2890, i.e. "
        "*before* the reported line 3021.",
}


def node_census(code):
    """walk pre-processed script text (comments/strings already gone)

    Returns (blocks, facts):
      blocks: (line, keyword, child keywords, leaf facts, depth) - child
              keywords are "<fact>" for plain facts
      facts : (line, keyword, number of argument tokens)
    """
    blocks, facts, stack = [], [], []
    for lineno, raw in enumerate(code.split("\n"), 1):
        for tok in TOKEN_RE.findall(raw):
            if tok == "(":
                stack.append({"kw": None, "line": lineno, "kids": [], "args": []})
            elif tok == ")":
                if not stack:
                    continue
                node = stack.pop()
                node["leaves"] = sum(k["leaves"] if k["kw"] in BLOCK_KW else 1
                                     for k in node["kids"])
                node["depth"] = max([(k["depth"] + 1) if k["kw"] in BLOCK_KW else 1
                                     for k in node["kids"]] or [0])
                if node["kw"] in BLOCK_KW:
                    blocks.append((node["line"], node["kw"],
                                   tuple(k["kw"] if k["kw"] in BLOCK_KW else "<fact>"
                                         for k in node["kids"]),
                                   node["leaves"], node["depth"]))
                else:
                    facts.append((node["line"], node["kw"], len(node["args"])))
                if stack:
                    stack[-1]["kids"].append(node)
            elif stack:
                if stack[-1]["kw"] is None:
                    stack[-1]["kw"] = tok
                else:
                    stack[-1]["args"].append(tok)
    return blocks, facts


def script_sources():
    """the shipped AI *scripts* (the exe keyword table is no parser input)"""
    out = []
    for folder, _archive, _tag in DATASETS:
        for name in ("anib_60002.bin", "anib_60027.bin", "anib_60010.bin",
                     "anib_60001.bin", "anib_60029.bin", "anib_60008.bin",
                     "anib_60003.bin", "anib_60026.bin"):
            path = os.path.join(W, folder, name)
            if os.path.exists(path):
                out.append(("%s/%s" % (folder, name),
                            open(path, "rb").read().decode("latin-1")))
    return out


def retail_shapes(sources):
    """what the shipped scripts contain: one witness per shape / per arity"""
    sig, arity, max_leaves = {}, {}, 0
    for name, text in sources:
        blocks, facts = node_census(code_only(text))
        for line, kw, kids, leaves, _depth in blocks:
            sig.setdefault((kw, kids), (name, line))
            max_leaves = max(max_leaves, leaves)
        for line, kw, nargs in facts:
            if kw:
                arity.setdefault((kw, nargs), (name, line))
    return sig, arity, max_leaves


def verify_retail_shapes(block, sources, label="appended block"):
    """enforce the two shape rules on `block`; returns (report lines, problems)"""
    sig, arity, max_leaves = retail_shapes(sources)
    blocks, facts = node_census(code_only(block))
    rep, bad = [], []
    hist, shapes = {}, {}
    for line, kw, kids, _leaves, _depth in blocks:
        hist[len(kids)] = hist.get(len(kids), 0) + 1
        shapes[(kw, kids)] = shapes.get((kw, kids), 0) + 1
        if len(kids) > MAX_BLOCK_CHILDREN:
            bad.append("%s line %d: (%s ...) with %d children"
                       % (label, line, kw, len(kids)))
    rep.append("    rule 1  at most %d children per logical block "
               "(the engine has two argument slots):" % MAX_BLOCK_CHILDREN)
    rep.append("            %s blocks by child count : %s"
               % (label, dict(sorted(hist.items())) or "{} (no logical block)"))
    rep.append("            its deepest block       : %d leaf fact(s) "
               "(shipped scripts use up to %d)"
               % (max([b[3] for b in blocks] or [0]), max_leaves))
    for (kw, kids), n in sorted(shapes.items()):
        witness = sig.get((kw, kids))
        if witness is None:
            bad.append("%s: (%s %s) - no shipped script uses this shape"
                       % (label, kw, " ".join(kids)))
            rep.append("            *** (%s %s) x%d  NO SHIPPED SCRIPT USES THIS SHAPE"
                       % (kw, " ".join(kids), n))
        else:
            rep.append("            (%s %s) x%d   attested: %s line %d"
                       % (kw, " ".join(kids), n, witness[0], witness[1]))
    rep.append("    rule 2  every fact arity is one a shipped script already uses:")
    for kw, na in sorted(set((k, n) for _l, k, n in facts if k)):
        witness = arity.get((kw, na))
        if witness is not None:
            rep.append("            %-26s %d arg(s)   attested: %s line %d"
                       % (kw, na, witness[0], witness[1]))
        elif (kw, na) in SHAPE_EXCEPTIONS:
            rep.append("            %-26s %d arg(s)   allowed exception: %s"
                       % (kw, na, SHAPE_EXCEPTIONS[(kw, na)]))
        else:
            bad.append("%s: (%s ...) with %d argument(s) is not shipped"
                       % (label, kw, na))
            rep.append("            *** %-26s %d arg(s)  NOT SHIPPED" % (kw, na))
    return rep, bad


def main():
    sys.path.insert(0, W)
    from drs_lib import Drs

    os.makedirs(OUT, exist_ok=True)
    sources = attestation_sources()
    report = ["=== token attestation sources"]
    for name, text in sources:
        report.append("    %-32s %9d bytes" % (name, len(text)))

    dm_block = build_dm_block(DATASETS[0][2])
    base_block = build_base_block(DATASETS[0][2])
    depth, bad_line = paren_balance(dm_block)
    assert depth == 0 and bad_line is None, "unbalanced parentheses at line %s" % bad_line
    code = code_only(dm_block)
    for gate in ("every-human", "difficulty", "players-current-age"):
        assert gate not in code, "the gate %r is still in the appended code" % gate
    ok, bad = check_tokens(dm_block, sources)
    report.append("")
    report.append("=== appended block: %d rules, %d bytes, parentheses balanced, "
                  "no difficulty/multiplayer gate left in the code, every"
                  % (dm_block.count("(defrule"), len(dm_block)))
    report.append("    logical block with at most %d children" % MAX_BLOCK_CHILDREN)
    report.append("    %d symbols used, %d unattested" % (len(ok) + len(bad), len(bad)))
    for tok, where in ok:
        report.append("      %-28s %s" % (tok, where))
    for tok in bad:
        report.append("      %-28s *** NOT FOUND IN ANY SHIPPED SCRIPT OR THE EXE ***" % tok)
    assert not bad, "unattested AI symbols: %s" % bad
    up, up_bad = check_uppercase(dm_block, sources)
    report.append("    uppercase enum symbols: %s" % (", ".join(up) or "(none)"))
    assert not up_bad, "unattested uppercase symbols: %s" % up_bad

    # the lesson of the in-game "ERR2011: Missing closing parenthesis": a token
    # may be attested and the parenthesis balance may be perfect, and the rule
    # still does not compile because the engine has two argument slots per
    # logical block.  So the *shape* of the appended code is checked too.
    script_src = script_sources()
    shape_lines, shape_bad = verify_retail_shapes(dm_block, script_src,
                                                 "appended dm block")
    report.append("")
    report.append("=== engine shape rules (measured with dm_blockshape.py)")
    report.extend(shape_lines)
    report.append("    verdict: the appended block breaks neither rule")
    assert not shape_bad, "shape problems in the appended block: %s" % shape_bad

    ok_b, bad_b = check_tokens(base_block, sources)
    assert not bad_b, "unattested AI symbols in the base marker: %s" % bad_b
    base_shape, base_shape_bad = verify_retail_shapes(base_block, script_src,
                                                      "base marker")
    assert not base_shape_bad, "shape problems in the base marker: %s" % base_shape_bad
    report.append("    (the base marker is rule %s and uses %d logical block(s))"
                  % ("(defrule (true) => ...)", len(node_census(code_only(base_block))[0])))
    report.append("    base marker: %d symbols, all attested, shape clean" % len(ok_b))
    report.append("")
    report.append("=== gates removed (retail rule -> appended rule)")
    report.append("    house    L1675 (difficulty <= moderate)                  -> H1")
    report.append("    house    L1694 #load-if-defined DIFFICULTY-EASY          -> H2")
    report.append("                    (military-population < civ-dark-rush) dropped")
    report.append("    house    L1683 #load-if-defined DIFFICULTY-EASIEST       -> H3")
    report.append("                    (military-population < 10) dropped")
    report.append("    feudal   L1597 (or (players-current-age every-human >= feudal-age)")
    report.append("                   (difficulty <= moderate))                  -> A1")
    report.append("    castle   L1617 same gate                                 -> A2")
    report.append("    imperial L1639 (or (difficulty <= moderate)")
    report.append("                   (and (players-current-age every-human == imperial-age)")
    report.append("                   (difficulty == easy)))                     -> A3")

    for folder, archive, tag in DATASETS:
        pristine = os.path.join(BACKUP, archive + ".orig")
        live_path = os.path.join(GAME, "Data", archive)
        assert os.path.exists(pristine), "missing pristine backup %s" % pristine
        pr = Drs(pristine)
        report.append("")
        report.append("=== %s   (%s, dataset tag %s)" % (archive, folder, tag))
        report.append("    pristine : %s" % pristine)
        report.append("      md5 %s" % hashlib.md5(open(pristine, "rb").read()).hexdigest())
        if os.path.exists(live_path):
            lv = Drs(live_path)
            report.append("    installed: %s  md5 %s"
                          % (live_path, hashlib.md5(open(live_path, "rb").read()).hexdigest()))
            report.append("      v1 patch currently present in the installed anib_60002: %s"
                          % (V1_MARKER in lv.payload(b"anib", 60002)))
        dm_raw = pr.payload(b"anib", 60002)
        dm_text, stripped = strip_v1(dm_raw.decode("latin-1"))
        assert not any(m in dm_text.encode("latin-1") for m in OLD_MARKERS), \
            "an earlier patch block could not be removed from %s" % pristine
        if stripped:
            report.append("    NOTE: the backup carried a %d byte v1 block, removed" % stripped)
            dm_raw = dm_text.encode("latin-1")
        dm_old = dm_raw
        dm_text = dm_old.decode("latin-1")
        rows = [x.rstrip("\r") for x in dm_text.split("\n")]
        depth, bad, n_open, n_close = preprocessor_balance(rows)
        report.append("    anib_60002 preprocessor: %d opener(s) (#load-if/#if), "
                      "%d #end-if, final depth %d%s"
                      % (n_open, n_close, depth, "  stray: %s" % bad if bad else ""))
        assert depth == 0 and not bad, \
            "retail script has unbalanced preprocessor blocks (%d, %s)" % (depth, bad)
        if not dm_text.endswith("\n"):
            dm_text += "\r\n"
        dm_new = (dm_text + build_dm_block(tag)).encode("latin-1")
        p_dm = os.path.join(OUT, "%s_anib_60002.bin" % folder)
        open(p_dm, "wb").write(dm_new)
        base_text = pr.payload(b"anib", 60001).decode("latin-1")
        base_text, b_stripped = strip_v1(base_text, (BASE_MARKER,))
        if b_stripped:
            report.append("    NOTE: the backup anib_60001 carried a %d byte marker, removed"
                          % b_stripped)
        rows = [x.rstrip("\r") for x in base_text.split("\n")]
        depth, bad, n_open, n_close = preprocessor_balance(rows)
        report.append("    anib_60001 preprocessor: %d opener(s), %d #end-if, final depth %d%s"
                      % (n_open, n_close, depth, "  stray: %s" % bad if bad else ""))
        assert depth == 0 and not bad, \
            "anib_60001 preprocessor is unbalanced (depth %d, %s)" % (depth, bad)
        if not base_text.endswith("\n"):
            base_text += "\r\n"
        base_old_size = len(base_text.encode("latin-1"))
        base_new = (base_text + build_base_block(tag)).encode("latin-1")
        p_base = os.path.join(OUT, "%s_anib_60001.bin" % folder)
        open(p_base, "wb").write(base_new)
        assert has_marker(dm_new, MARKER) and has_marker(base_new, BASE_MARKER)
        report.append("    anib_60002  %d -> %d bytes (+%d)"
                      % (len(dm_old), len(dm_new), len(dm_new) - len(dm_old)))
        report.append("      md5 %s -> %s" % (hashlib.md5(dm_old).hexdigest(),
                                             hashlib.md5(dm_new).hexdigest()))
        report.append("      -> %s" % p_dm)
        report.append("    anib_60001  %d -> %d bytes (+%d)  marker only"
                      % (base_old_size, len(base_new), len(base_new) - base_old_size))
        report.append("      -> %s" % p_base)

    report.append("")
    report.append("=== settings used")
    report.append("    houses max            : %d  (%d population slots)" % (HOUSES_MAX, HOUSES_MAX * 5))
    report.append("    house timer           : %s (retail index 1), first %ds, repeat %ds"
                  % (HOUSE_TIMER, HOUSE_TIMER_TIME, HOUSE_TIMER_REPEAT))
    report.append("    resource timer        : %s (retail index 2), first %ds, repeat %ds"
                  % (RES_TIMER, RES_TIMER_TIME, RES_TIMER_REPEAT))
    report.append("    new symbols           : none - every token is a shipped one")
    report.append("    shape rules           : <= %d children per logical block and"
                  % MAX_BLOCK_CHILDREN)
    report.append("                            fact arities as shipped (the lesson")
    report.append("                            of the in-game ERR2011 of v2)")
    report.append("    caveat                : timers 1 and 2 are unused by every script of")
    report.append("                            a death match, but a scenario-embedded AI")
    report.append("                            could still use them")
    txt = "\n".join(report)
    open(os.path.join(W, "dm_patch2_report.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()

