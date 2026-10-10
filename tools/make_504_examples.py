"""Write the book's own example sentences, three to a word.

Every one of the 504 is taught with three sentences using it. The
spreadsheet keeps one short sentence per meaning, written for a Spanish
reader; these are the book's, kept beside them rather than instead of
them.

The text comes out of the PDF with the page's furniture attached: the
last sentence of a lesson runs straight into "Words in Use", into the
next entry's numbered heading, or into a running head. Those are cut
off here rather than shown to anybody.

Keyed by the headword in lower case, like the synonyms, so renaming or
merging the sheet leaves it alone.

    python tools/make_504_examples.py path/to/flat504.json
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "504_examples.json"

# Everything that can follow the last sentence of a word on the page.
TAIL = re.compile(
    r"\s*(?:"
    r"Words\s+in\s+[lU][JS]?se"            # "Words in Use", and its OCR twin
    r"|Read\s+the\s+following\s+passage"
    r"|Creativity\s+Exercise"
    r"|Spotlight\s+On"
    r"|Picture\s+It"
    r"|Word\s+Review"
    r"|No\s+Context"
    r"|\d{1,2}\s*\.\s*\S{0,24}?\s*\("      # the next entry's heading
    r"|(?<=\.)\s[\dSl]\s*\.\s+[a-z]"      # ...and the same heading with
                                             # its bracket lost to the scan
    r"|\d{1,3}\s+504\s+ABSOLUTELY"         # the running head
    r"|LESSON\s+\d{1,2}"
    r").*$",
    re.I | re.S)


# The scan turned a few letters into punctuation, always the same way.
# Repairing them is safer than guessing, and anything still carrying a
# character that does not belong in an English sentence is dropped
# rather than shown.
GLYPHS = [
    ("ha<:>", "has"),
    ("bigam}\'", "bigamy"),
    ("re\'(eal", "reveal"),
    ("~ticking", "sticking"),
    ("Th~", "The"),
    ("i~", "is"),
    ("conclude~", "conclude"),
]
ODD = re.compile(r"[^A-Za-z0-9\s.,;:!?'\"()$%&/-]")


def clean(sentence):
    s = sentence
    for wrong, right in GLYPHS:
        s = s.replace(wrong, right)
    s = TAIL.sub("", s).strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"[\s.,;:]+$", "", s)
    ends = s[-1:] if s else ""
    # a sentence cut mid-clause is worse than no sentence
    if len(s) < 18 or len(s) > 200:
        return ""
    if not re.match(r"^[A-Z\"'(]", s):
        return ""
    if s.count('"') % 2:
        s = s.replace('"', "")
    if ODD.search(s):
        return ""
    # A question keeps its question mark. Stripping the trailing
    # punctuation and then always adding a full stop gave "How scarce are
    # good cooks?." on every question in the book.
    return s if ends in "?!" else s + "."


def main():
    book = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    table, kept, dropped = {}, 0, 0
    for e in book:
        good = []
        for raw in e["ex"]:
            s = clean(raw)
            if s and s not in good:
                good.append(s)
            elif not s:
                dropped += 1
        if good:
            table[e["word"].lower()] = good
            kept += len(good)
    OUT.write_text(json.dumps(table, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    print("%d sentences kept for %d of the %d words (%d set aside as damaged)"
          % (kept, len(table), len(book), dropped))
    print("written to tools/%s" % OUT.name)


if __name__ == "__main__":
    main()
