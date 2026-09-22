"""
Enriches ENGLISH SCHOOL.xlsx in place:

  1. For every entry detected as a verb, writes the verb forms into Notes
     (base / present / past / past participle, and regular or irregular),
     keeping whatever note was already there.
  2. Fixes small defects: trailing spaces in sheet names, the header and one
     headword, and the two rows missing a note.

Run it again safely: an existing "Regular verb." / "Irregular verb." prefix
is replaced rather than stacked, so re-running does not duplicate the line.
"""
import os
import re
import shutil
import sys
from datetime import datetime

import openpyxl

from detect_verbs import verb_evidence
from verb_forms import forms_for

FILE = "ENGLISH SCHOOL.xlsx"
FORMS_PREFIX = re.compile(r"^(Regular|Irregular) verb\.\s*Base:.*?(?:Past participle:[^.]*\.)\s*", re.S)

# The old notes restate the verb forms, sometimes wrongly ("Carry" was
# labelled irregular). Now that the forms are generated, those clauses are
# stripped so the note does not contradict itself -- but only the clause
# that lists forms, never the surrounding advice like "separable" or
# "British spelling: ...".
LEGACY_FORM_CLAUSES = [
    re.compile(r"\b(?:Irregular|Regular)(?:\s+(?:verb|forms?))?\s*[:;]\s*[^.;]*[.;]\s*", re.I),
    re.compile(r"\bVerb\s+forms?\s*[:;]\s*[^.;]*[.;]\s*", re.I),
    re.compile(r"\bPast(?:\s+tense)?(?:\s+and\s+past\s+participle)?\s*:\s*[^.;]*[.;]\s*", re.I),
    re.compile(r"\b(?:Irregular|Regular)\s+verb\.\s*", re.I),
    re.compile(r"\bpast\s+tense\s*:\s*[^.;]*[.;]\s*", re.I),
]


def clean_legacy_forms(text):
    out = text
    for rx in LEGACY_FORM_CLAUSES:
        out = rx.sub("", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    out = re.sub(r"^[;,.\s]+", "", out)
    # removing a clause can leave a dangling connector: "Can be a noun or
    # verb;" or "...itself; Do not confuse..." -- close those off properly
    out = re.sub(r";\s*(?=[A-Z])", ". ", out)
    out = re.sub(r"[;,]\s*$", ".", out)
    out = out.strip()
    if out:
        out = out[0].upper() + out[1:]
        if not out.endswith((".", "!", "?")):
            out += "."
    return out


MISSING_NOTES = {
    ("School books", "Hump"): "A rounded lump, most often on a camel's back; also a rise in a road.",
    ("School books", "Mammal"): "A warm-blooded animal that feeds its young with milk.",
}


def forms_note(head, tail):
    third, past, part, irregular = forms_for(head)
    join = lambda v: (v + " " + tail).strip()
    label = "Irregular verb." if irregular else "Regular verb."
    return "%s Base: %s · Present: %s · Past: %s · Past participle: %s." % (
        label, join(head), join(third), join(past), join(part)
    )


def main(apply_changes):
    if apply_changes:
        # backups live in a subfolder: build_word_log.py refuses to run when
        # it finds more than one .xlsx beside it
        os.makedirs("backups", exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy(FILE, os.path.join("backups", "ENGLISH SCHOOL.pre-enrich-%s.xlsx" % stamp))

    wb = openpyxl.load_workbook(FILE)
    verbs = 0
    notes_added = 0
    trimmed = 0
    renamed = []

    for name in list(wb.sheetnames):
        ws = wb[name]

        # header cell keeps a trailing space
        h = ws.cell(row=1, column=1)
        if isinstance(h.value, str) and h.value != h.value.strip():
            if apply_changes:
                h.value = h.value.strip()
            trimmed += 1

        for r in range(2, ws.max_row + 1):
            raw = ws.cell(row=r, column=1).value
            if raw is None or not str(raw).strip():
                continue
            word = str(raw).strip()
            if str(raw) != word:
                if apply_changes:
                    ws.cell(row=r, column=1).value = word
                trimmed += 1

            meanings = []
            for mc in (3, 5, 7):  # 1-indexed columns for Meaning 1/2/3
                v = ws.cell(row=r, column=mc).value
                if v and str(v).strip():
                    meanings.append(str(v).strip())

            note_cell = ws.cell(row=r, column=9)
            note = str(note_cell.value).strip() if note_cell.value else ""

            filled = MISSING_NOTES.get((name.strip(), word))
            if not note and filled:
                note = filled
                notes_added += 1

            # strip any line a previous run wrote first, so an entry that is
            # no longer treated as a verb does not keep a stale one
            note = FORMS_PREFIX.sub("", note).strip()

            is_verb, base, _ = verb_evidence(word, meanings, note)
            if is_verb and base:
                note = clean_legacy_forms(note)
                line = forms_note(*base)
                note = (line + " " + note).strip() if note else line
                verbs += 1

            if apply_changes and note:
                note_cell.value = note

        if name != name.strip():
            renamed.append((name, name.strip()))
            if apply_changes:
                ws.title = name.strip()

    if apply_changes:
        wb.save(FILE)

    print("verbs given forms:      %d" % verbs)
    print("missing notes filled:   %d" % notes_added)
    print("whitespace trimmed:     %d" % trimmed)
    print("sheets renamed:         %s" % (renamed or "none"))
    print("MODE: %s" % ("WRITTEN" if apply_changes else "dry run, nothing saved"))


if __name__ == "__main__":
    main("--apply" in sys.argv)
