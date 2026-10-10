"""Append hand-written 504 rows to the combined topic.

Each chunk file is a JSON array; one entry looks like

    ["Abate", "abéit",
     [["Become less \u2014 Disminuir / amainar.", "The storm abated at dawn."],
      ["Make something less \u2014 Reducir.", "The law abated the noise."]],
     "v"]

The last field is the Notes column: "v" asks for the verb's forms to be
worked out and written in the sheet's usual style, anything else is used
as it stands. Rows whose word is already anywhere in the workbook are
skipped and reported, so a chunk can be run twice without doubling up.

    python tools/add_504_words.py chunk1.json chunk2.json
    python tools/add_504_words.py --dry-run chunk1.json
    python tools/add_504_words.py --sheet "Phrasal verbs" chunk1.json

A sheet that does not exist yet is created, with the same nine columns
as the others, so a new topic needs nothing doing to it by hand.
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
from verb_forms import forms_for  # noqa: E402

DEFAULT_SHEET = "504 Essential words"
DASH = "\u2014"
HEADER = ["Word/expression", "Pronunciation",
          "Meaning 1", "Example", "Meaning 2", "Example", "Meaning 3", "Example",
          "Meaning 4", "Example", "Meaning 5", "Example", "Notes"]


def verb_note(base):
    third, past, part, irregular = forms_for(base)
    if not third:
        return ""
    label = "Irregular verb." if irregular else "Regular verb."
    return "%s Base: %s %s Present: %s %s Past: %s %s Past participle: %s." % (
        label, base, DASH, third, DASH, past, DASH, part)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("chunks", nargs="+")
    ap.add_argument("--sheet", default=DEFAULT_SHEET)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sheet = args.sheet

    entries = []
    for name in args.chunks:
        path = Path(name)
        if not path.exists():
            path = HERE / "504-chunks" / name
        entries += json.loads(path.read_text(encoding="utf-8"))
    print("%d rows offered" % len(entries))

    import openpyxl
    wb = openpyxl.load_workbook(glossary.WORKBOOK)
    fresh = sheet not in wb.sheetnames
    if fresh:
        print("%r does not exist yet; it will be created." % sheet)
    have = set()
    for name in wb.sheetnames:
        for row in wb[name].iter_rows(min_row=2, max_col=1, values_only=True):
            if row[0]:
                have.add(normalise(row[0]))

    rows, skipped, bad = [], [], []
    for e in entries:
        word, pron, meanings, note = (list(e) + ["", "", [], ""])[:4]
        word = str(word).strip()
        if not word or not meanings:
            bad.append(word or "(blank)"); continue
        key = normalise(word)
        if key in have:
            skipped.append(word); continue
        have.add(key)
        # "v" asks for the forms; "v|..." asks for the forms and then
        # says one more thing, which is usually where the real difficulty
        # of the word lives.
        if note == "v" or str(note).startswith("v|"):
            extra = str(note)[2:].strip()
            note = " ".join(x for x in (verb_note(word.lower()), extra) if x)
        cells = [word, str(pron).strip() or None]
        for i in range(5):
            if i < len(meanings):
                m, ex = (list(meanings[i]) + ["", ""])[:2]
                cells += [str(m).strip(), str(ex).strip() or None]
            else:
                cells += [None, None]
        cells.append(str(note).strip() or None)
        rows.append(cells)

    print("%d to add, %d already in the sheets, %d unusable"
          % (len(rows), len(skipped), len(bad)))
    if skipped:
        print("   already here: %s%s" % (", ".join(skipped[:10]),
                                         " ..." if len(skipped) > 10 else ""))
    if bad:
        print("   unusable: %s" % ", ".join(bad))
    if not rows:
        return
    for r in rows[:3]:
        print("   %-16s %-14s %s" % (r[0], r[1] or "", str(r[2])[:54]))

    if args.dry_run:
        print("\nDry run. Nothing written.")
        return

    glossary.BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = glossary.BACKUPS / ("ENGLISH SCHOOL.pre-504-%s.xlsx" % stamp)
    shutil.copy(glossary.WORKBOOK, kept)

    if fresh:
        ws = wb.create_sheet(sheet)
        ws.append(HEADER)
    else:
        ws = wb[sheet]
    for r in rows:
        ws.append(r)
    wb.save(glossary.WORKBOOK)
    print("\nAdded %d rows to %r (now %d)." % (len(rows), sheet, ws.max_row - 1))
    print("Copy of the workbook before this: backups/%s" % kept.name)


if __name__ == "__main__":
    main()
