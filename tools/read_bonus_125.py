"""Read the bonus lesson at the back of the 504 book.

After lesson 42 comes "125 More Difficult (But Essential) Words", laid
out exactly like the 504: a numbered headword, a respelling, a short
definition and three sentences. This pulls them out and cleans the page
furniture off, the same way the 504's own sentences are cleaned.

Three entries lose their number to the scan -- it reads "1 OS." for 105
and swallows the heading of 47 and 64 -- so those are picked up by name.

    python tools/read_bonus_125.py "<the pdf>" 
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_504_examples import clean  # noqa: E402  the same cleaning

OUT = HERE / "bonus125.json"
FIRST, LAST = 146, 159          # the pages the lesson runs across

# The opening bracket is optional: the scan reads "(jes" as "Ues" and
# "(joo" as "Uoo", which loses it on two of the entries. The closing one
# survives, so the definition is whatever follows the LAST bracket --
# which also copes with "torment (torment' or tor' ment) cause...".
HEAD = re.compile(r"^\s*(\d{1,3}|1\s*OS)\s*\.\s+([a-zA-Z][a-zA-Z'\- ]{1,22}?)\s*[\(A-Z](.*)$")
EX = re.compile(r"^\s*([a-c])\s*\.\s+(\S.*)$")
# the scan drops the number on these three and leaves the word stranded
BY_NAME = {"gesticulate": 47, "judicious": 64, "prognosticate": 105}
LOOSE = re.compile(r"^\s*(?:\d{0,3}\s*)?(%s)\s*[A-Za-z]?\(?"
                   % "|".join(BY_NAME), re.I)


def number(raw):
    raw = raw.replace(" ", "")
    return 105 if raw.upper() == "1OS" else int(raw)


def main():
    from pypdf import PdfReader
    pages = PdfReader(sys.argv[1]).pages
    body = "\n".join((pages[i].extract_text() or "") for i in range(FIRST, LAST))

    got, cur, field = {}, None, None
    for line in body.split("\n"):
        m = HEAD.match(line)
        if not m:
            mm = LOOSE.match(line)
            if mm and BY_NAME[mm.group(1).lower()] not in got:
                n = BY_NAME[mm.group(1).lower()]
                rest = line[mm.end(1):]
                i = rest.rfind(")")
                cur = {"n": n, "word": mm.group(1).lower(),
                       "gloss": rest[i + 1:].strip() if i >= 0 else "", "ex": []}
                got[n] = cur
                field = "gloss"
                continue
        if m:
            n = number(m.group(1))
            if 1 <= n <= 125 and n not in got:
                rest = m.group(3)
                i = rest.rfind(")")
                cur = {"n": n, "word": m.group(2).strip().lower(),
                       "gloss": rest[i + 1:].strip() if i >= 0 else "", "ex": []}
                got[n] = cur
                field = "gloss"
                continue
        m = EX.match(line)
        if m and cur is not None:
            cur["ex"].append(m.group(2).strip())
            field = "ex"
            continue
        s = line.strip()
        if cur is None or not s:
            continue
        if field == "gloss" and len(cur["gloss"]) < 90:
            if not cur["gloss"] and ")" in s:
                cur["gloss"] = s[s.rfind(")") + 1:].strip()
            elif cur["gloss"] and not s[0].isdigit():
                cur["gloss"] = (cur["gloss"] + " " + s).strip()
        elif field == "ex" and cur["ex"] and len(cur["ex"][-1]) < 240:
            cur["ex"][-1] += " " + s

    out = []
    for n in sorted(got):
        e = got[n]
        sentences = []
        for raw in e["ex"][:3]:
            s = clean(raw)
            if s and s not in sentences:
                sentences.append(s)
        gloss = re.sub(r"\s+", " ", e["gloss"]).strip().strip(".")
        out.append({"n": n, "word": e["word"], "gloss": gloss, "ex": sentences})

    missing = [n for n in range(1, 126) if n not in got]
    print("read %d of 125%s" % (len(out), "" if not missing else ", missing %s" % missing))
    print("with three sentences: %d, with fewer: %d"
          % (sum(1 for e in out if len(e["ex"]) == 3),
             sum(1 for e in out if len(e["ex"]) < 3)))
    bad = [e["word"] for e in out if not re.fullmatch(r"[a-z][a-z\-']{2,18}", e["word"])
           or len(e["gloss"]) < 3]
    print("entries that do not look right: %s" % (bad or "none"))
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("written to tools/%s" % OUT.name)


if __name__ == "__main__":
    main()
