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

FOLDER = Path(__file__).resolve().parent
TEMPLATE = FOLDER / "template.html"
OUTPUT = FOLDER / "vocabulary_practice.html"


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

            words.append(entry)

    return words, dupes


def main():
    spreadsheet = find_spreadsheet()
    if not TEMPLATE.exists():
        sys.exit(f"Can't find {TEMPLATE.name} in:\n  {FOLDER}\n"
                  f"That's the app shell Claude gave you -- add it and try again.")

    print(f"Using spreadsheet: {spreadsheet.name}\n")
    words, dupes = extract_words(spreadsheet)
    categories = sorted(set(w["cat"] for w in words))
    print(f"Found {len(words)} words across {len(categories)} categories:")
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

    final = shell.replace(
        marker,
        "const WORDS = " + json.dumps(words, ensure_ascii=True) + ";"
    )
    OUTPUT.write_text(final, encoding="utf-8")
    print(f"\nDone. Wrote {OUTPUT.name} -- open it in your browser.")


if __name__ == "__main__":
    main()
