"""
Verb form data and rules, used by enrich_spreadsheet.py.

Kept as its own module so the irregular table can be checked and corrected
on its own. Accuracy matters more than coverage here: a wrong form in the
Notes column would actively teach bad English, so anything the rules are
not confident about is left alone rather than guessed at.
"""

# base: (third person singular, simple past, past participle)
IRREGULAR = {
    "abide": ("abides", "abode", "abode"),
    "arise": ("arises", "arose", "arisen"),
    "awake": ("awakes", "awoke", "awoken"),
    "be": ("is", "was/were", "been"),
    "bear": ("bears", "bore", "borne"),
    "beat": ("beats", "beat", "beaten"),
    "become": ("becomes", "became", "become"),
    "begin": ("begins", "began", "begun"),
    "bend": ("bends", "bent", "bent"),
    "bet": ("bets", "bet", "bet"),
    "bid": ("bids", "bid", "bid"),
    "bind": ("binds", "bound", "bound"),
    "bite": ("bites", "bit", "bitten"),
    "bleed": ("bleeds", "bled", "bled"),
    "blow": ("blows", "blew", "blown"),
    "break": ("breaks", "broke", "broken"),
    "breed": ("breeds", "bred", "bred"),
    "bring": ("brings", "brought", "brought"),
    "broadcast": ("broadcasts", "broadcast", "broadcast"),
    "build": ("builds", "built", "built"),
    "burn": ("burns", "burned/burnt", "burned/burnt"),
    "burst": ("bursts", "burst", "burst"),
    "buy": ("buys", "bought", "bought"),
    "cast": ("casts", "cast", "cast"),
    "catch": ("catches", "caught", "caught"),
    "choose": ("chooses", "chose", "chosen"),
    "cling": ("clings", "clung", "clung"),
    "come": ("comes", "came", "come"),
    "cost": ("costs", "cost", "cost"),
    "creep": ("creeps", "crept", "crept"),
    "cut": ("cuts", "cut", "cut"),
    "deal": ("deals", "dealt", "dealt"),
    "dig": ("digs", "dug", "dug"),
    "do": ("does", "did", "done"),
    "draw": ("draws", "drew", "drawn"),
    "dream": ("dreams", "dreamed/dreamt", "dreamed/dreamt"),
    "drink": ("drinks", "drank", "drunk"),
    "drive": ("drives", "drove", "driven"),
    "dwell": ("dwells", "dwelt", "dwelt"),
    "eat": ("eats", "ate", "eaten"),
    "fall": ("falls", "fell", "fallen"),
    "feed": ("feeds", "fed", "fed"),
    "feel": ("feels", "felt", "felt"),
    "fight": ("fights", "fought", "fought"),
    "find": ("finds", "found", "found"),
    "flee": ("flees", "fled", "fled"),
    "fling": ("flings", "flung", "flung"),
    "fly": ("flies", "flew", "flown"),
    "forbid": ("forbids", "forbade", "forbidden"),
    "forecast": ("forecasts", "forecast", "forecast"),
    "forget": ("forgets", "forgot", "forgotten"),
    "forgive": ("forgives", "forgave", "forgiven"),
    "freeze": ("freezes", "froze", "frozen"),
    "get": ("gets", "got", "gotten/got"),
    "give": ("gives", "gave", "given"),
    "go": ("goes", "went", "gone"),
    "grind": ("grinds", "ground", "ground"),
    "grow": ("grows", "grew", "grown"),
    "hang": ("hangs", "hung", "hung"),
    "have": ("has", "had", "had"),
    "hear": ("hears", "heard", "heard"),
    "hide": ("hides", "hid", "hidden"),
    "hit": ("hits", "hit", "hit"),
    "hold": ("holds", "held", "held"),
    "hurt": ("hurts", "hurt", "hurt"),
    "keep": ("keeps", "kept", "kept"),
    "kneel": ("kneels", "knelt", "knelt"),
    "know": ("knows", "knew", "known"),
    "lay": ("lays", "laid", "laid"),
    "lead": ("leads", "led", "led"),
    "lean": ("leans", "leaned/leant", "leaned/leant"),
    "leap": ("leaps", "leaped/leapt", "leaped/leapt"),
    "learn": ("learns", "learned/learnt", "learned/learnt"),
    "leave": ("leaves", "left", "left"),
    "lend": ("lends", "lent", "lent"),
    "let": ("lets", "let", "let"),
    "lie": ("lies", "lay", "lain"),
    "light": ("lights", "lit", "lit"),
    "lose": ("loses", "lost", "lost"),
    "make": ("makes", "made", "made"),
    "mean": ("means", "meant", "meant"),
    "meet": ("meets", "met", "met"),
    "mistake": ("mistakes", "mistook", "mistaken"),
    "overcome": ("overcomes", "overcame", "overcome"),
    "pay": ("pays", "paid", "paid"),
    "put": ("puts", "put", "put"),
    "quit": ("quits", "quit", "quit"),
    "read": ("reads", "read", "read"),
    "rid": ("rids", "rid", "rid"),
    "ride": ("rides", "rode", "ridden"),
    "ring": ("rings", "rang", "rung"),
    "rise": ("rises", "rose", "risen"),
    "run": ("runs", "ran", "run"),
    "say": ("says", "said", "said"),
    "see": ("sees", "saw", "seen"),
    "seek": ("seeks", "sought", "sought"),
    "sell": ("sells", "sold", "sold"),
    "send": ("sends", "sent", "sent"),
    "set": ("sets", "set", "set"),
    "sew": ("sews", "sewed", "sewn/sewed"),
    "shake": ("shakes", "shook", "shaken"),
    "shed": ("sheds", "shed", "shed"),
    "shine": ("shines", "shone", "shone"),
    "shoot": ("shoots", "shot", "shot"),
    "show": ("shows", "showed", "shown"),
    "shrink": ("shrinks", "shrank", "shrunk"),
    "shut": ("shuts", "shut", "shut"),
    "sing": ("sings", "sang", "sung"),
    "sink": ("sinks", "sank", "sunk"),
    "sit": ("sits", "sat", "sat"),
    "sleep": ("sleeps", "slept", "slept"),
    "slide": ("slides", "slid", "slid"),
    "sling": ("slings", "slung", "slung"),
    "smell": ("smells", "smelled/smelt", "smelled/smelt"),
    "sow": ("sows", "sowed", "sown/sowed"),
    "speak": ("speaks", "spoke", "spoken"),
    "speed": ("speeds", "sped", "sped"),
    "spell": ("spells", "spelled/spelt", "spelled/spelt"),
    "spend": ("spends", "spent", "spent"),
    "spill": ("spills", "spilled/spilt", "spilled/spilt"),
    "spin": ("spins", "spun", "spun"),
    "spit": ("spits", "spat", "spat"),
    "split": ("splits", "split", "split"),
    "spoil": ("spoils", "spoiled/spoilt", "spoiled/spoilt"),
    "spread": ("spreads", "spread", "spread"),
    "spring": ("springs", "sprang", "sprung"),
    "stand": ("stands", "stood", "stood"),
    "steal": ("steals", "stole", "stolen"),
    "stick": ("sticks", "stuck", "stuck"),
    "sting": ("stings", "stung", "stung"),
    "stink": ("stinks", "stank", "stunk"),
    "strike": ("strikes", "struck", "struck"),
    "strive": ("strives", "strove", "striven"),
    "swear": ("swears", "swore", "sworn"),
    "sweep": ("sweeps", "swept", "swept"),
    "swim": ("swims", "swam", "swum"),
    "swing": ("swings", "swung", "swung"),
    "take": ("takes", "took", "taken"),
    "teach": ("teaches", "taught", "taught"),
    "tear": ("tears", "tore", "torn"),
    "tell": ("tells", "told", "told"),
    "think": ("thinks", "thought", "thought"),
    "throw": ("throws", "threw", "thrown"),
    "thrust": ("thrusts", "thrust", "thrust"),
    "understand": ("understands", "understood", "understood"),
    "undertake": ("undertakes", "undertook", "undertaken"),
    "upset": ("upsets", "upset", "upset"),
    "wake": ("wakes", "woke", "woken"),
    "wear": ("wears", "wore", "worn"),
    "weave": ("weaves", "wove", "woven"),
    "weep": ("weeps", "wept", "wept"),
    "win": ("wins", "won", "won"),
    "wind": ("winds", "wound", "wound"),
    "withdraw": ("withdraws", "withdrew", "withdrawn"),
    "withstand": ("withstands", "withstood", "withstood"),
    "wring": ("wrings", "wrung", "wrung"),
    "write": ("writes", "wrote", "written"),
    # do not decompose into a prefix + known root
    "string": ("strings", "strung", "strung"),
    "tread": ("treads", "trod", "trodden"),
    "prove": ("proves", "proved", "proven/proved"),
    "show": ("shows", "showed", "shown"),
    "strew": ("strews", "strewed", "strewn"),
}

# A prefixed verb inherits its root's irregularity: foretell -> foretold,
# mislead -> misled, overrun -> overran. Without this they would be treated
# as regular and produce "foretelled" / "misleaded".
VERB_PREFIXES = (
    "over", "under", "fore", "with", "mis", "out", "up", "down", "off",
    "re", "un", "dis", "inter", "counter",
)

VOWELS = "aeiou"

def _vowel_groups(word):
    groups = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in VOWELS or ch == "y" and prev_vowel is False and groups > 0
        if ch in VOWELS:
            if not prev_vowel:
                groups += 1
            prev_vowel = True
        else:
            prev_vowel = False
    return groups


def _is_cvc(word):
    """Consonant-vowel-consonant ending, the pattern that doubles."""
    if len(word) < 3:
        return False
    a, b, c = word[-3], word[-2], word[-1]
    return (a not in VOWELS) and (b in VOWELS) and (c not in VOWELS) and c not in "wxy"


# Multi-syllable verbs stressed on the final syllable also double, and
# spelling alone does not reveal stress -- so those stay an explicit list.
# Single-syllable verbs are handled by the CVC rule above instead, which is
# what "tar -> tarred" and "cop -> copped" need.
DOUBLING = {
    "bag", "ban", "bar", "beg", "bet", "bid", "bob", "brag", "bud", "chat", "chop", "clap",
    "clip", "cram", "crop", "dam", "dip", "drag", "drip", "drop", "drum", "dub", "fan", "fit",
    "flap", "flip", "grab", "grin", "grip", "hop", "hug", "hum", "jam", "jog", "jot", "knit",
    "knot", "lag", "map", "mob", "mop", "nag", "nod", "pat", "peg", "pin", "plan", "plot",
    "plug", "pop", "prop", "rap", "rid", "rip", "rob", "rot", "rub", "sag", "scan", "scar",
    "ship", "shop", "shrug", "sin", "sip", "skip", "slam", "slap", "slip", "snap", "sob",
    "spot", "stab", "star", "stem", "step", "stir", "stop", "strap", "strip", "stun", "sum",
    "swap", "tag", "tan", "tap", "tip", "top", "trap", "trek", "trim", "trip", "tug", "wag",
    "whip", "wrap", "zip",
    # two-syllable verbs stressed on the last syllable
    "admit", "commit", "compel", "confer", "control", "equip", "excel", "expel", "forget",
    "occur", "omit", "patrol", "permit", "prefer", "propel", "rebel", "refer", "regret",
    "submit", "transfer", "transmit",
}


def third_person(base):
    if base.endswith(("s", "x", "z", "ch", "sh")):
        return base + "es"
    if base.endswith("o"):
        return base + "es"
    if base.endswith("y") and len(base) > 1 and base[-2] not in VOWELS:
        return base[:-1] + "ies"
    return base + "s"


def past_regular(base):
    if base.endswith("e"):
        return base + "d"
    if base.endswith("y") and len(base) > 1 and base[-2] not in VOWELS:
        return base[:-1] + "ied"
    if base.endswith("c"):
        return base + "ked"
    if base in DOUBLING or (_vowel_groups(base) == 1 and _is_cvc(base)):
        return base + base[-1] + "ed"
    return base + "ed"


def _prefixed_irregular(low):
    """foretell -> fore + tell, so it inherits told/told."""
    for prefix in VERB_PREFIXES:
        if not low.startswith(prefix):
            continue
        root = low[len(prefix):]
        if len(root) < 2 or root not in IRREGULAR:
            continue
        _, past, part = IRREGULAR[root]
        # keep any "got/gotten" style alternatives intact
        join = lambda v: "/".join(prefix + p for p in v.split("/"))
        return third_person(low), join(past), join(part)
    return None


def forms_for(base):
    """Returns (third, past, participle, is_irregular) for a single verb."""
    low = base.lower()
    if low in IRREGULAR:
        third, past, part = IRREGULAR[low]
        return third, past, part, True
    prefixed = _prefixed_irregular(low)
    if prefixed:
        return prefixed[0], prefixed[1], prefixed[2], True
    third = third_person(low)
    past = past_regular(low)
    return third, past, past, False
