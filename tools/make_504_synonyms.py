"""Write the list of words the book prints beside each of the 504.

The entry for abandon reads "abandon (a ban' dan) desert; leave without
planning to come back; quit". The short parts of that -- desert, quit --
are other ways of saying the word, which is the thing a learner wants
next to the headword. The long parts are definitions, and those are
already the word's meanings in the spreadsheet, so they are left out.

The result is keyed by the headword in lower case rather than by the
app's "<topic>::<word>" id, so renaming or merging the sheet leaves it
alone.

Any number of sources can be given; the bonus lesson at the back of the
book is laid out the same way, so it goes through here too.

    python tools/make_504_synonyms.py flat504.json tools/bonus125.json
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
    table = {}
    total = 0
    for name in sys.argv[1:]:
        book = json.loads(Path(name).read_text(encoding="utf-8"))
        total += len(book)
        for e in book:
            syns = synonyms(e.get("gloss", ""), e["word"])
            if syns:
                table.setdefault(e["word"].lower(), syns)
    OUT.write_text(json.dumps(table, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    print("%d of %d headwords have words printed beside them" % (len(table), total))
    for w in ("abandon", "keen", "typical", "valiant"):
        print("   %-10s %s" % (w, ", ".join(table.get(w, []))))
    print("written to tools/%s" % OUT.name)


if __name__ == "__main__":
    main()
