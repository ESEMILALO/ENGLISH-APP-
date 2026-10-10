"""
Word Log builder
-----------------
Rebuilds vocabulary_practice.html from your ENGLISH_SCHOOL.xlsx spreadsheet.
Run this any time you add or edit words in the spreadsheet.

SETUP (only once):
    pip install openpyxl

HOW TO USE:
    1. Keep these three files in the same folder:
         - build_word_log.py    (this script)
         - template.html        (the app shell -- never edit this by hand)
         - ENGLISH_SCHOOL.xlsx  (your spreadsheet)
    2. Open a terminal in that folder and run:
         python build_word_log.py
    3. A fresh vocabulary_practice.html appears in the same folder.
       Open it in your browser to practice.
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

try:
    import openpyxl
except ImportError:
    sys.exit("Missing dependency. Run this first:\n\n    pip install openpyxl\n")

from detect_verbs import verb_evidence
from verb_forms import forms_for

# tools/ holds this script and the template; the spreadsheet sits in the
# project root beside it, and the built page goes into app/, which is the
# only folder the server ever hands anything out of.
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
FOLDER = ROOT                      # where the spreadsheet is looked for
TEMPLATE = TOOLS / "template.html"
OUTPUT = ROOT / "app" / "vocabulary_practice.html"
IMAGE_MAP = TOOLS / "word_images.json"
IMAGES = ROOT / "app" / "images"


# The little words that turn a verb into a different verb. "Take" and
# "take off" are not the same thing, which is exactly why they are worth
# a block of their own.
PARTICLES = {
    "up", "down", "out", "in", "on", "off", "over", "away", "back",
    "through", "around", "about", "along", "across", "by", "for", "into",
    "to", "with", "after", "ahead", "apart", "aside", "forward",
    "together", "under", "upon", "round", "past", "behind",
}


def is_phrasal(word, notes, meaning):
    """Two or three words ending in a particle, and a verb.

    The notes say "Regular verb" or "Irregular verb" for anything that is
    one, which is what separates "back down" from "service dog". A few
    entries say in their meaning that they are not really phrasal verbs
    at all; they are taken at their word.
    """
    parts = str(word or "").lower().replace("-", " ").split()
    if not 2 <= len(parts) <= 4:
        return False
    if parts[-1] not in PARTICLES:
        return False
    if "verb" not in str(notes or "").lower():
        return False
    said = str(meaning or "").lower()
    if "not an actual phrasal verb" in said or "false pattern" in said:
        return False
    return True


def find_spreadsheet():
    # Looks for any .xlsx file in the folder instead of one exact name,
    # since downloads/renames can end up with slightly different names
    # (spaces vs underscores, etc). Ignores Excel's temporary "~$..." files.
    candidates = [p for p in FOLDER.glob("*.xlsx") if not p.name.startswith("~$")]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        sys.exit(f"No spreadsheet (.xlsx file) found in:\n  {FOLDER}\n"
                  f"Put your word-list spreadsheet there and run this again.")
    names = "\n".join(f"  - {p.name}" for p in candidates)
    sys.exit(f"Found more than one .xlsx file in this folder:\n{names}\n"
              f"Keep just your word-list spreadsheet here and try again.")


def _ing_guesses(head):
    """All the ways -ing might be spelled onto a verb. Loose on purpose."""
    head = head.lower()
    out = {head + "ing"}
    if head.endswith("e") and not head.endswith("ee"):
        out.add(head[:-1] + "ing")
    if head.endswith("ie"):
        out.add(head[:-2] + "ying")
    if len(head) > 2 and head[-1] not in "aeiouwxy" and head[-2] in "aeiou"             and head[-3] not in "aeiou":
        out.add(head + head[-1] + "ing")
    return out


def _plural_guesses(head):
    """Plural and third-person spellings, equally loose and equally safe."""
    head = head.lower()
    out = {head + "s"}
    if head.endswith("y") and len(head) > 1 and head[-2] not in "aeiou":
        out.add(head[:-1] + "ies")
    if head.endswith(("s", "x", "z", "ch", "sh")):
        out.add(head + "es")
    return out


def alternate_forms(word, meanings, note):
    """Other ways the headword may be written inside its own examples.

    Covers "To hatch" appearing as "hatch", and a verb appearing in an
    inflected form ("endangers", "withdrew"). Only forms that actually turn
    up in one of the word's examples are kept, so the list stays small and
    every entry in it is known to be useful.
    """
    candidates = []

    bare = word[3:].strip() if word.lower().startswith("to ") else ""
    if bare:
        candidates.append(bare)

    meaning_texts = [m["m"] for m in meanings]
    is_verb, base, _ = verb_evidence(word, meaning_texts, note)
    if is_verb and base:
        head, tail = base
        third, past, part, _ = forms_for(head)
        for variant in (third, past, part):
            for piece in variant.split("/"):
                candidates.append((piece.strip() + " " + tail).strip())
        # The -ing form as well. "Grieve" is written "grieving" in its own
        # sentence, and without this the word cannot be found there at all,
        # so the sentence card is simply never built.
        for piece in _ing_guesses(head):
            candidates.append((piece + " " + tail).strip())

    # Nouns say themselves in the plural: "authority" in the sentence about
    # the authorities, "difficulty" in the one about difficulties. Guessing
    # loosely is safe here, because a guess is only kept if it is actually
    # written in one of the word's own examples.
    head_word = (base[0] if (is_verb and base) else word).lower()
    if head_word and " " not in head_word:
        candidates.extend(_plural_guesses(head_word))

    examples = [m["e"] for m in meanings if m["e"]]
    keep = []
    for cand in candidates:
        if not cand or cand.lower() == word.lower() or cand in keep:
            continue
        pattern = re.compile(r"\b" + re.escape(cand) + r"\b", re.I)
        if any(pattern.search(ex) for ex in examples):
            keep.append(cand)
    return keep


def extract_words(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    words = []
    seen = Counter()
    dupes = []

    for sheet_name in wb.sheetnames:
        category = sheet_name.strip()
        ws = wb[sheet_name]
        for row in ws.iter_rows(min_row=2, values_only=True):
            word = row[0]
            if word is None or str(word).strip() == "":
                continue
            word = str(word).strip()

            pron = row[1] if len(row) > 1 and row[1] else ""
            meanings = []
            for m_col, e_col in [(2, 3), (4, 5), (6, 7)]:
                m = row[m_col] if m_col < len(row) else None
                e = row[e_col] if e_col < len(row) else None
                if m and str(m).strip():
                    meanings.append({
                        "m": str(m).strip(),
                        "e": str(e).strip() if e else ""
                    })
            notes = row[8] if len(row) > 8 and row[8] else ""

            # Stable id: built from category + word, not row position, so
            # inserting or reordering rows later never scrambles your
            # saved progress. If the same word appears twice in one
            # category, a #2 / #3 suffix keeps ids unique.
            base_id = f"{category}::{word}"
            seen[base_id] += 1
            word_id = base_id if seen[base_id] == 1 else f"{base_id}#{seen[base_id]}"
            if seen[base_id] > 1:
                dupes.append(base_id)

            entry = {
                "id": word_id,
                "cat": category,
                "w": word,
                "p": str(pron).strip(),
                "me": meanings,
                "n": str(notes).strip() if notes else "",
            }

            # Other spellings the word can take in its own example sentence.
            # "Endanger" is written "endangers" in its example, so without
            # these the sentence-completion card could not be built at all.
            alts = alternate_forms(word, meanings, entry["n"])
            if alts:
                entry["alt"] = alts

            if is_phrasal(entry.get("w"), entry.get("n"),
                          (entry.get("me") or [{}])[0].get("m")):
                entry["pv"] = 1
            words.append(entry)

    return words, dupes


def load_pictures(known):
    """What word_images.py found, for the words that are still in the sheet.

    Only the four things the page needs travel with it: the file, who to
    credit, the licence, and where it came from. A word whose picture file
    has since been deleted is left without one rather than showing a gap.
    """
    if not IMAGE_MAP.exists():
        return {}
    try:
        found = json.loads(IMAGE_MAP.read_text(encoding="utf-8"))
    except Exception:
        print("  (tools/word_images.json is unreadable -- carrying on without pictures)")
        return {}

    out = {}
    for word_id, row in found.items():
        name = (row or {}).get("file")
        if not name or word_id not in known:
            continue
        if not (IMAGES / name).exists():
            continue
        out[word_id] = {"file": name, "by": row.get("by", ""),
                        "lic": row.get("lic", ""), "page": row.get("page", "")}
    return out


SYNONYMS = TOOLS / "504_synonyms.json"


def attach_synonyms(words):
    """Hang the words the book prints beside each of the 504 on the word.

    Keyed on the word itself rather than on its "<topic>::<word>" id, so
    that merging or renaming the sheet cannot quietly empty it -- which is
    exactly what happened to the picture map the first time. Returns how
    many words were given a list.
    """
    if not SYNONYMS.exists():
        return 0
    try:
        table = json.loads(SYNONYMS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    found = 0
    for w in words:
        got = table.get(w["w"].strip().lower())
        if got:
            w["syn"] = got
            found += 1
    return found


def main():
    spreadsheet = find_spreadsheet()
    if not TEMPLATE.exists():
        sys.exit(f"Can't find {TEMPLATE.name} in:\n  {FOLDER}\n"
                  f"That's the app shell Claude gave you -- add it and try again.")

    print(f"Using spreadsheet: {spreadsheet.name}\n")
    words, dupes = extract_words(spreadsheet)
    categories = sorted(set(w["cat"] for w in words))
    phrasal = sum(1 for w in words if w.get("pv"))
    print(f"Found {len(words)} words across {len(categories)} categories "
          f"({phrasal} of them phrasal verbs):")
    for cat in categories:
        n = sum(1 for w in words if w["cat"] == cat)
        print(f"  - {cat}: {n}")

    if dupes:
        print(f"\nHeads up: {len(dupes)} word(s) appear more than once in the "
              f"same category (still fine to use, just worth a look):")
        for d in dupes:
            print(f"  - {d.split('::')[1]} ({d.split('::')[0]})")

    shell = TEMPLATE.read_text(encoding="utf-8")
    marker = "const WORDS = [];"
    if marker not in shell:
        sys.exit("template.html doesn't look right -- the WORDS marker is missing.")

    # Attached before the words are written out, so a word carries the
    # other ways of saying it the same way it carries its meanings.
    beside = attach_synonyms(words)
    if beside:
        print("\n%d of them carry the other words the book prints "
              "beside them." % beside)

    final = shell.replace(
        marker,
        "const WORDS = " + json.dumps(words, ensure_ascii=True) + ";"
    )

    pictures = load_pictures({w["id"] for w in words})
    if pictures:
        print(f"\n{len(pictures)} of them have a picture in app/images/.")
    final = final.replace(
        "const WORD_IMAGES = {};",
        "const WORD_IMAGES = " + json.dumps(pictures, ensure_ascii=True) + ";"
    )
    OUTPUT.write_text(final, encoding="utf-8")
    print(f"\nDone. Wrote {OUTPUT.name} -- open it in your browser.")


if __name__ == "__main__":
    main()
