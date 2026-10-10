"""Write the list of words the book prints beside each of the 504.

The entry for abandon reads "abandon (a ban' dan) desert; leave without
planning to come back; quit". The short parts of that -- desert, quit --
are other ways of saying the word, which is the thing a learner wants
next to the headword. The long parts are definitions, and those are
already the word's meanings in the spreadsheet, so they are left out.

The result is keyed by the headword in lower case rather than by the
app's "<topic>::<word>" id, so renaming or merging the sheet leaves it
alone.

    python tools/make_504_synonyms.py path/to/flat504.json
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "504_synonyms.json"


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def synonyms(gloss, headword):
    out = []
    for part in gloss.split(";"):
        p = part.strip().strip(".").lower()
        # Three words is where a synonym stops and a definition starts:
        # "quit" and "use up" are other ways of saying it, "leave without
        # planning to come back" is the meaning, which the word already has.
        if not p or len(p.split()) > 3:
            continue
        if not re.fullmatch(r"[a-z][a-z \-']+", p):
            continue
        if norm(p) == norm(headword) or p in out:
            continue
        out.append(p)
    return out


def main():
    src = Path(sys.argv[1])
    book = json.loads(src.read_text(encoding="utf-8"))
    table = {}
    for e in book:
        syns = synonyms(e["gloss"], e["word"])
        if syns:
            table[e["word"].lower()] = syns
    OUT.write_text(json.dumps(table, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    print("%d of %d headwords have words printed beside them" % (len(table), len(book)))
    for w in ("abandon", "keen", "typical", "valiant"):
        print("   %-10s %s" % (w, ", ".join(table.get(w, []))))
    print("written to tools/%s" % OUT.name)


if __name__ == "__main__":
    main()
