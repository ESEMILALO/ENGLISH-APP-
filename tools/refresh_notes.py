"""Rewrite the Notes of rows whose verb forms were worked out wrongly.

The forms helper used to conjugate a phrasal verb as if it were one
word, so every row written from a chunk file carried "break uped" and
"blow awayed" in its notes. The helper is fixed; this puts the corrected
notes back into the rows that already have the wrong ones.

Only rows that came from a chunk file are touched, and only their Notes
column. Words, meanings, examples and ids are left exactly as they are.

    python tools/refresh_notes.py --dry-run
    python tools/refresh_notes.py
"""

import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

import glossary  # noqa: E402
from glossary import normalise  # noqa: E402
from add_504_words import verb_note, DASH  # noqa: E402

CHUNKS = HERE / "504-chunks"
NOTES_COL = 13


def note_for(entry):
    note = (list(entry) + ["", "", [], ""])[3]
    if note == "v" or str(note).startswith("v|"):
        extra = str(note)[2:].strip()
        return " ".join(x for x in (verb_note(str(entry[0]).lower()), extra) if x)
    return str(note).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wanted = {}
    for path in sorted(CHUNKS.glob("*.json")):
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not rows or not isinstance(rows[0], list) or len(rows[0]) < 3:
            continue
        if isinstance(rows[0][2], list) and rows[0][2] and isinstance(rows[0][2][0], str):
            continue                     # an enrichment file, not a word file
        for e in rows:
            wanted[normalise(e[0])] = note_for(e)
    print("%d words read from the chunk files" % len(wanted))

    import openpyxl
    wb = openpyxl.load_workbook(glossary.WORKBOOK)
    changed, same, shown = 0, 0, 0
    for sheet in wb.sheetnames:
        for row in wb[sheet].iter_rows(min_row=2):
            word = row[0].value
            if not word:
                continue
            fresh = wanted.get(normalise(word))
            if not fresh:
                continue
            if (row[NOTES_COL - 1].value or "") == fresh:
                same += 1
                continue
            if shown < 5:
                print("   %-16s %s" % (word, fresh[:88]))
                shown += 1
            row[NOTES_COL - 1].value = fresh
            changed += 1

    print("%d notes rewritten, %d already right" % (changed, same))
    if args.dry_run or not changed:
        if args.dry_run:
            print("\nDry run. Nothing written.")
        return

    glossary.BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = glossary.BACKUPS / ("ENGLISH SCHOOL.pre-notes-%s.xlsx" % stamp)
    shutil.copy(glossary.WORKBOOK, kept)
    wb.save(glossary.WORKBOOK)
    print("Saved. Copy before this: backups/%s" % kept.name)


if __name__ == "__main__":
    main()
