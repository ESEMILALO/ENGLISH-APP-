"""Add senses to phrasal verbs the app already has, without disturbing them.

The Ultimate Phrasal Verb Book gives several numbered senses to verbs
that arrived here with one. Rather than put a second copy of "break
down" in a second topic, the extra senses go into the empty Meaning
slots of the row that is already there.

Only empty slots are written. A meaning that is already in the sheet is
never replaced, the word and its topic do not change, so no id changes
and no progress is lost.

    python tools/enrich_phrasal_rows.py extra.json --dry-run
    python tools/enrich_phrasal_rows.py extra.json

One entry is ["<topic>", "<word>", [[meaning, example], ...]].
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

import glossary  # noqa: E402
from glossary import normalise  # noqa: E402

SLOTS = [(3, 4), (5, 6), (7, 8)]       # 1-based columns: meaning, example


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    wanted = []
    for name in args.files:
        wanted += json.loads(Path(name).read_text(encoding="utf-8"))
    print("%d rows offered" % len(wanted))

    import openpyxl
    wb = openpyxl.load_workbook(glossary.WORKBOOK)

    index = {}
    for sheet in wb.sheetnames:
        for row in wb[sheet].iter_rows(min_row=2):
            if row[0].value:
                index[(sheet, normalise(row[0].value))] = row

    added, skipped, missing, full = 0, 0, [], []
    for entry in wanted:
        sheet, word, extras = entry[0], entry[1], entry[2]
        row = index.get((sheet, normalise(word)))
        if row is None:
            missing.append("%s / %s" % (sheet, word))
            continue
        free = [(m, e) for m, e in SLOTS if not row[m - 1].value]
        if not free:
            full.append(word)
            continue
        for (m, e), pair in zip(free, extras):
            row[m - 1].value = str(pair[0]).strip()
            row[e - 1].value = str(pair[1]).strip() or None
            added += 1
        skipped += max(0, len(extras) - len(free))

    print("%d meanings written into empty slots" % added)
    if skipped:
        print("%d had nowhere to go (the row was already full)" % skipped)
    if full:
        print("rows already full: %s" % ", ".join(full[:8]))
    if missing:
        print("not found: %s" % ", ".join(missing))

    if args.dry_run:
        print("\nDry run. Nothing written.")
        return
    if not added:
        return

    glossary.BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = glossary.BACKUPS / ("ENGLISH SCHOOL.pre-enrich-%s.xlsx" % stamp)
    shutil.copy(glossary.WORKBOOK, kept)
    wb.save(glossary.WORKBOOK)
    print("\nSaved. Copy of the workbook before this: backups/%s" % kept.name)


if __name__ == "__main__":
    main()
