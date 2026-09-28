"""
Decides which spreadsheet entries are verbs, and builds the forms line.

Deliberately conservative: when the evidence is weak the entry is skipped
rather than guessed at, because a wrong form in Notes teaches bad English.
"""
import re
from verb_forms import forms_for, IRREGULAR

# Spanish nouns/adjectives that end like an infinitive and would otherwise
# trip the -ar/-er/-ir test.
SPANISH_NOT_VERBS = {
    "lugar", "hogar", "collar", "dolar", "dólar", "altar", "bazar", "manjar", "pesar",
    "mujer", "taller", "placer", "alfiler", "crater", "cráter", "lider", "líder", "chofer",
    "elixir", "porvenir", "ser", "poder", "deber", "parecer", "amanecer", "atardecer",
    "anochecer", "haber", "sabor", "temor", "millar", "solar", "polar", "familiar",
    "similar", "particular", "popular", "regular", "escolar", "militar", "vulgar",
    "singular", "circular", "auxiliar", "ejemplar", "espectacular", "peculiar",
    # caught as false positives while reviewing the detector's output
    "cadáver", "cadaver", "carácter", "caracter", "quehacer",
}

# Headwords whose glosses mention an infinitive but which are not themselves
# verbs -- e.g. Worth is glossed "Valer / digno de" but is an adjective.
ENGLISH_NOT_VERBS = {"corpse", "makeup", "chore", "worth"}

# Spanish infinitives, including reflexive ones (-arse/-erse/-irse), which
# gloss verbs like Behave ("Comportarse") and Decay ("Descomponerse").
INFINITIVE = re.compile(r"^[a-záéíóúñü]+(?:ar|er|ir)(?:se)?$", re.I)


def spanish_part(meaning):
    """The text after the em dash, where the Spanish gloss lives."""
    if "—" in meaning:
        return meaning.split("—", 1)[1]
    return ""


def looks_like_infinitive(text):
    for chunk in re.split(r"[/,;()]", text):
        chunk = chunk.strip().strip(".").strip()
        if not chunk:
            continue
        # a phrase gloss can still start with an infinitive:
        # "Poner en peligro" -> poner
        token = chunk.split()[0]
        if token.lower() in SPANISH_NOT_VERBS:
            continue
        if INFINITIVE.match(token):
            return token
    return None


# Entries that are themselves an inflected form ("Gambling" is the gerund of
# gamble, "Fell out" is already past) must not be conjugated again, which
# would produce "gamblinged" or "felled out".
INFLECTED_NOTE = re.compile(
    r"\b(gerund|present participle|past participle of|past tense|past of)\b", re.I
)

_PAST_FORMS = set()
for _base, (_third, _past, _part) in IRREGULAR.items():
    for _form in (_past, _part):
        for _variant in _form.split("/"):
            _PAST_FORMS.add(_variant.strip().lower())
# verbs whose past equals the base (read, set, cut...) stay usable
_PAST_FORMS -= set(IRREGULAR)


def verb_evidence(word, meanings, note=""):
    """Returns (is_verb, base, evidence) for a headword and its meanings."""
    clean = word.strip()
    if note and INFLECTED_NOTE.search(note):
        return False, None, "entry is itself an inflected form"
    base = clean
    prefix = ""

    if clean.lower().startswith("to "):
        base = clean[3:].strip()
        prefix = "to"

    # a phrasal verb conjugates its first token: "jot down" -> "jotted down"
    parts = base.split()
    head = parts[0].lower() if parts else ""
    tail = " ".join(parts[1:])

    # entries that are grammar patterns rather than words
    if "+" in clean or "(" in clean:
        return False, None, "pattern"
    if not head or not head.isalpha():
        return False, None, "not-a-word"
    if clean.lower() in ENGLISH_NOT_VERBS:
        return False, None, "not a verb despite an infinitive in the gloss"
    if head in _PAST_FORMS:
        return False, None, "headword is already a past form"
    # "Frightening someone out of something" is a gerund phrase, not a lemma.
    # Real -ing base verbs (bring, sing, swing, string...) are all irregular,
    # so being in that table is the test.
    if head.endswith("ing") and head not in IRREGULAR:
        return False, None, "headword is an -ing form"

    evidence = []
    if prefix:
        evidence.append('headword starts with "To"')
    if head in IRREGULAR:
        evidence.append("known irregular verb")
    for m in meanings:
        inf = looks_like_infinitive(spanish_part(m))
        if inf:
            evidence.append("Spanish infinitive: " + inf)
            break

    return (len(evidence) > 0), (head, tail), "; ".join(evidence)


def forms_line(head, tail):
    third, past, part, irregular = forms_for(head)
    join = lambda v: (v + " " + tail).strip()
    label = "Irregular verb" if irregular else "Regular verb"
    return "%s: %s / %s / %s / %s." % (
        label, join(head), join(third), join(past), join(part)
    )
