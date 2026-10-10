"""Pull the book's own sentences out of the parsed phrasal verb book.

Same shape and same job as make_504_examples.py, keyed by the verb, so
the builder can hang them on the word and the card can show them under
the meanings in a "From the book" block.

    python tools/make_phrasal_examples.py tools/ocr/book.json
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "phrasal_examples.json"
MOST = 6                      # a verb with eight senses would swamp the card


def main():
    book = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    table = {}
    for v in book:
        sentences = []
        for item in v["senses"] + v["related"]:
            for s in item["ex"]:
                if s not in sentences:
                    sentences.append(s)
        if sentences:
            table[v["verb"]] = sentences[:MOST]
    OUT.write_text(json.dumps(table, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    print("%d verbs carry %d sentences between them"
          % (len(table), sum(len(v) for v in table.values())))
    print("written to tools/%s" % OUT.name)


if __name__ == "__main__":
    main()
