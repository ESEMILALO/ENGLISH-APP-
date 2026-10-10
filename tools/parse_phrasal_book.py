"""Turn the OCR'd phrasal verb book into entries.

`ocr_book.py` leaves one JSON object per page: every line of text with
where it sat on the page. That position is the whole trick. The book
prints its example sentences in italics, which do not survive being
read, but it also indents them -- the body of an entry starts near
x=200 and its examples near x=243 -- so the left edge is what tells a
definition from the sentences under it.

A page reads like this:

    x=127   Infinitive                        <- a new verb starts
    x=276   present tense  -ing form  ...     <- the forms table
    x=124   go with
    x=250   go with & goes with   going with  ...
    x=203   1. go with p.v. When one thing ...   <- a sense
    x=201   each other.                          <- its definition wraps
    x=244   A lot of responsibility goes ...     <- an example
    x=201   fixed up part.adj. After you ...     <- a form of the verb

    python tools/parse_phrasal_book.py tools/ocr/clean.jsonl out.json
"""

import argparse
import json
import re
from pathlib import Path

# The margins are mirrored -- a left-hand page starts its body around
# 0.12 of the width and a right-hand one around 0.156 -- so the columns
# are worked out for each page rather than assumed. What is constant is
# the step: an example is indented about 0.034 of the width further in
# than the definition above it.
INDENT = 0.034
LONG = 0.25          # a line this wide is prose, not a heading or a column

SENSE = re.compile(
    r"^(\d{1,2})\s*[\.\)]\s*"                    # 1. -- the scan drops the
                                                 # space after the dot now
                                                 # and then: "1.put up with"
    r"([a-z][a-z'\- ]*?"                         # fix
    r"(?:\s*[\.…]{2,}\s*|\s+)"              # ... or a space
    r"[a-z'\-]+(?:\s+[a-z'\-]+)?)"               # up (with)
    r"\s*(\([^)]{1,14}\))?"                      # (with)
    r"\s*(p\.?\s?v\.?)"                          # p.v.
    r"\s*(\[[^\]]{1,20}\])?"                     # [informal]
    r"\s*(.*)$", re.I)

FORM = re.compile(
    r"^([a-z][a-z'\- ]{1,24}?)\s+"                # fixed up
    r"(part\.?\s?adj\.?|n\.?|adj\.?|adv\.?)"      # part.adj.
    r"\s*(\[[^\]]{1,20}\])?"
    r"\s+(.*)$", re.I)

TABLE_HEAD = re.compile(r"^(infinitive|present tense|-?ing form|past tense|past participle)$", re.I)


# The running title is printed across the top of every page and the
# photographs catch it, sometimes with the letters squashed together and
# sometimes in full-width characters. It is stripped wherever it lands.
TITLE = re.compile(r"\s*TH\s*E?\s*[U\uff35]\s*L?\s*T?\s*I?\s*M?\s*A?\s*T?\s*E?\s*"
                   r"[P\uff30]?\s*H?\s*[R\uff32]?\s*A?\s*S?\s*A?\s*L?\s*"
                   r"[V\uff36]?\s*E?\s*[R\uff32]?\s*B?\s*B?\s*O?\s*O?\s*K?\s*",
                   re.I)
# A row of the forms table reads "go down & goes down"; it is not a
# sentence, and it turns up when the table sits beside an entry.
FORMS_ROW = re.compile(r"^[a-z][a-z' ]{1,22}&\s*[a-z][a-z' ]{1,22}$", re.I)


def keep_sentence(text):
    """Is this a sentence from the book, or wreckage from the page?

    The exercise pages are full of half-sentences with the answer left
    blank, and those sit in the same column as the real examples. A
    sentence that does not start like one or end like one is not one.
    """
    text = TITLE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 22 or " " not in text:
        return ""
    if FORMS_ROW.match(text):
        return ""
    if not re.match(r"^[\"\u201c(A-Z]", text):
        return ""
    if not re.search(r"[.!?\"\u201d]$", text):
        return ""
    # whole words run together, which the scan does now and then
    if re.search(r"[a-z]{16,}", text):
        return ""
    return text


OCR_SLIPS = [
    ("[informall", "[informal]"), ("[informaI]", "[informal]"),
    ("p. v.", "p.v."), ("part. adj.", "part.adj."),
]


def tidy(text):
    for wrong, right in OCR_SLIPS:
        text = text.replace(wrong, right)
    text = re.sub(r"[…]+", "...", text)
    text = re.sub(r"\s*\.\.\.\s*", " ... ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def verb_name(raw):
    """"back  up" and "back...up" are both back up."""
    return re.sub(r"\s+", " ", re.sub(r"[\.…]+", " ", raw)).strip().lower()


def body_margin(lines, width):
    """Where this page's definitions start, and where its examples do.

    Taken from the prose on the page itself: short lines are headings,
    page numbers and the columns of a forms table, and any of those
    would drag the margin to the wrong place.
    """
    prose = [l["x"] / width for l in lines
             if l["w"] > width * LONG and 0.05 < l["x"] / width < 0.35]
    if len(prose) < 3:
        return None
    prose.sort()
    body = prose[max(0, int(len(prose) * 0.1))]
    # Three columns, not two: the definition, the sentence under it, and
    # the second line of a sentence that ran on. Guessing the third from
    # the first two was what glued two separate sentences into one.
    return (body * width,
            (body + INDENT / 2) * width,
            (body + INDENT + 0.012) * width)


def page_number(lines):
    for l in reversed(lines[-5:]):
        t = l["t"].strip()
        if t.isdigit() and len(t) <= 3:
            return int(t)
    for l in lines[:3]:
        t = l["t"].strip()
        if t.isdigit() and len(t) <= 3:
            return int(t)
    return None


def read(path):
    pages = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("lines"):
            d["printed"] = page_number(d["lines"])
            pages.append(d)
    return pages


def parse(pages):
    """Collect the senses, then group them by the verb each one names.

    The forms table is not what decides which verb a sense belongs to.
    It cannot be: 84 printed pages are missing from the clean scan, so a
    table is often on a page that is not there, and every sense after it
    would be filed under whichever verb came last. The heading says the
    verb itself -- "3. put ... back p.v." -- so that is what is trusted,
    and the table only supplies the four forms.
    """
    tables, found, holder, where = {}, [], None, None
    holder_x = None

    for d in pages:
        width = d.get("width") or 1280
        lines = sorted(d["lines"], key=lambda l: l["y"])
        margins = body_margin(lines, width)
        if margins is None:
            continue
        body_x, example_x, wrap_x = margins

        skip_until = -1
        for i, l in enumerate(lines):
            if l["y"] < skip_until:
                continue
            text = l["t"].strip()
            if not text or (text.isdigit() and len(text) <= 3):
                continue
            # The running title of the section is printed sideways down
            # the outer edge. It is text, and it is nowhere near the
            # columns, so it is left where it is.
            if l["x"] > width * 0.70 and not TABLE_HEAD.match(text):
                continue

            # A forms table opens a new verb. Its rows sit across the
            # page in columns, so they are stepped over by position
            # rather than by trying to read them as prose.
            if TABLE_HEAD.match(text):
                table = [x for x in lines if l["y"] - 10 <= x["y"] <= l["y"] + 150]
                # The verb stands alone to the left of the body margin,
                # which is what separates it from the four form columns
                # ranged across the page beside it.
                left = [x for x in table
                        if abs(x["x"] - l["x"]) < 0.025 * width
                        and x["y"] > l["y"]
                        and not TABLE_HEAD.match(x["t"].strip())
                        and not x["t"].strip().isdigit()]
                name = ""
                for x in sorted(left, key=lambda x: x["y"]):
                    cand = verb_name(x["t"])
                    if cand and re.fullmatch(r"[a-z][a-z' \-]{1,28}", cand):
                        name = cand
                        break
                if name:
                    forms = [x["t"].strip() for x in sorted(table, key=lambda x: (x["y"], x["x"]))
                             if x["x"] >= body_x and not TABLE_HEAD.match(x["t"].strip())]
                    tables.setdefault(name, forms[:4])
                    holder_x = None
                skip_until = l["y"] + 150
                continue

            # A line that reads "3. break ... up p.v. ..." is a sense
            # heading wherever it sits. Position is only asked about a
            # line that is not obviously one thing or the other: on a
            # page that opens with a section introduction the margins
            # shift, and three senses of break up were being filed as
            # sentences because they sat a few pixels too far right.
            looks_like_heading = bool(SENSE.match(text))

            # Once a heading has been seen, its own left edge is a
            # better ruler than the page average: the sentences under it
            # are indented from where it starts, whatever the page is
            # doing elsewhere.
            here = holder_x if holder_x is not None else body_x
            ex_x = max(example_x, here + INDENT / 2 * width)
            wr_x = max(wrap_x, here + (INDENT + 0.012) * width)

            # indented: a sentence, or the rest of one
            if l["x"] >= ex_x and not looks_like_heading:
                if holder is None:
                    continue
                if holder["ex"] and l["x"] >= wr_x:
                    holder["ex"][-1] += " " + text
                else:
                    holder["ex"].append(text)
                continue

            # at the margin: a new sense, a form of the verb, or a wrap
            m = SENSE.match(text)
            if m:
                where = verb_name(m.group(2))
                holder = {"kind": "sense", "verb": where,
                          "n": int(m.group(1)),
                          "pattern": tidy(m.group(2)),
                          "with": (m.group(3) or "").strip("()"),
                          "label": (m.group(5) or "").strip("[]"),
                          "page": d.get("printed"),
                          "def": m.group(6).strip(), "ex": []}
                found.append(holder)
                holder_x = l["x"]
                continue
            m = FORM.match(text)
            if m and len(text.split()) > 4:
                holder = {"kind": m.group(2).lower().replace(" ", ""),
                          "verb": where, "word": verb_name(m.group(1)),
                          "label": (m.group(3) or "").strip("[]"),
                          "page": d.get("printed"),
                          "def": m.group(4).strip(), "ex": []}
                found.append(holder)
                holder_x = l["x"]
                continue
            if holder is not None and not holder["ex"]:
                holder["def"] = (holder["def"] + " " + text).strip()

    for item in found:
        item["def"] = tidy(TITLE.sub(" ", item["def"]))
        kept = []
        for x in item["ex"]:
            good = keep_sentence(tidy(x))
            if good and good not in kept:
                kept.append(good)
        item["ex"] = kept

    verbs = {}
    for item in found:
        name = item.get("verb")
        if not name:
            continue
        v = verbs.setdefault(name, {"verb": name, "forms": tables.get(name, []),
                                    "page": item.get("page"), "senses": [], "related": []})
        if item["kind"] == "sense":
            v["senses"].append(item)
        else:
            v["related"].append(item)
    return sorted(verbs.values(), key=lambda v: v["verb"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ocr", nargs="+")
    ap.add_argument("out")
    args = ap.parse_args()

    # Two readings of the same book. Where both have a page the clean
    # scan wins, because it is a scan and the other is a photograph of
    # paper; where only the photograph has it, the photograph is used.
    # Sources are taken in the order given, best first.
    pages, seen = [], set()
    for name in args.ocr:
        taken = 0
        for d in read(name):
            key = d["printed"]
            if key is None or key in seen:
                continue
            seen.add(key)
            pages.append(d)
            taken += 1
        print("%-28s %d pages used" % (Path(name).name, taken))
    pages.sort(key=lambda d: d["printed"])
    print("%d printed pages between them, %d to %d"
          % (len(pages), pages[0]["printed"], pages[-1]["printed"]))
    missing = [n for n in range(pages[0]["printed"], pages[-1]["printed"] + 1)
               if n not in seen]
    print("still missing: %d %s" % (len(missing), missing if len(missing) < 20 else ""))

    verbs = parse(pages)
    senses = sum(len(v["senses"]) for v in verbs)
    related = sum(len(v["related"]) for v in verbs)
    examples = sum(len(s["ex"]) for v in verbs for s in v["senses"] + v["related"])
    print("verbs: %d   senses: %d   other forms: %d   sentences: %d"
          % (len(verbs), senses, related, examples))
    noex = sum(1 for v in verbs for s in v["senses"] if not s["ex"])
    print("senses with no sentence under them: %d" % noex)
    thin = sum(1 for v in verbs for s in v["senses"] if len(s["def"]) < 25)
    print("senses whose definition came out too short: %d" % thin)

    Path(args.out).write_text(json.dumps(verbs, indent=1, ensure_ascii=False),
                              encoding="utf-8")
    print("written to %s" % args.out)


if __name__ == "__main__":
    main()
