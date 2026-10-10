"""Read a scanned book into text, one page at a time, with no API.

Both copies of The Ultimate Phrasal Verb Book are photographs: there is
no text in them at all, so nothing can be pulled out the way the 504 was.
This runs RapidOCR over every page locally -- no key, no allowance, no
network -- and writes each page as it is read, so stopping it and running
it again carries on rather than starting the book over.

    python tools/ocr_book.py "C:\\...\\book.pdf" tools/ocr/book.jsonl
    python tools/ocr_book.py "...pdf" out.jsonl --from 100 --to 140
"""

import argparse
import io
import json
import sys
import time
import types
from pathlib import Path

import numpy as np


# RapidOCR wants shapely for one area-over-perimeter sum on a simple
# polygon. This machine's application-control policy blocks shapely's
# native library, so the two numbers are worked out here instead: the
# shoelace formula, and a sum of the edge lengths.
class _Polygon:
    def __init__(self, points):
        self.p = np.asarray(points, dtype=float)

    @property
    def area(self):
        x, y = self.p[:, 0], self.p[:, 1]
        return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

    @property
    def length(self):
        d = np.diff(np.vstack([self.p, self.p[:1]]), axis=0)
        return float(np.hypot(d[:, 0], d[:, 1]).sum())


def _stub_shapely():
    if "shapely.geometry" in sys.modules:
        return
    shapely = types.ModuleType("shapely")
    geometry = types.ModuleType("shapely.geometry")
    geometry.Polygon = _Polygon
    shapely.geometry = geometry
    sys.modules["shapely"] = shapely
    sys.modules["shapely.geometry"] = geometry


def page_image(page):
    """The page as a PIL image, or None if there is nothing on it."""
    from PIL import Image
    try:
        images = list(page.images)
    except Exception:
        return None
    if not images:
        return None
    biggest = max(images, key=lambda im: len(im.data))
    try:
        return Image.open(io.BytesIO(biggest.data)).convert("RGB")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--from", dest="first", type=int, default=0)
    ap.add_argument("--to", dest="last", type=int, default=0)
    ap.add_argument("--width", type=int, default=1600,
                    help="pages are scaled to this before reading")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["page"])
            except Exception:
                pass
        print("%d pages already read" % len(done))

    _stub_shapely()
    from pypdf import PdfReader
    from rapidocr_onnxruntime import RapidOCR

    reader = PdfReader(args.pdf)
    total = len(reader.pages)
    last = args.last or total
    todo = [i for i in range(args.first, min(last, total)) if i not in done]
    print("%s: %d pages, %d to read" % (Path(args.pdf).name, total, len(todo)))
    if not todo:
        return

    ocr = RapidOCR()
    started = time.time()
    with out.open("a", encoding="utf-8") as fh:
        for n, i in enumerate(todo, 1):
            try:
                im = page_image(reader.pages[i])
                if im is None:
                    lines = []
                else:
                    if im.width > args.width:
                        h = round(im.height * args.width / im.width)
                        im = im.resize((args.width, h))
                    res, _ = ocr(np.array(im))
                    # The left edge of each line comes with it. This book
                    # tells a definition from its examples by indentation
                    # and nothing else -- the italics the page uses do not
                    # survive being read -- so the position is the only
                    # thing that can separate them later.
                    lines = []
                    for box, text, _score in (res or []):
                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        lines.append({"t": text,
                                      "x": round(min(xs)),
                                      "y": round(min(ys)),
                                      "w": round(max(xs) - min(xs)),
                                      "h": round(max(ys) - min(ys))})
            except Exception as e:                      # a bad page is not the book
                lines = []
                print("  page %d could not be read (%s)" % (i, str(e)[:60]), flush=True)
            fh.write(json.dumps({"page": i, "width": getattr(im, "width", 0),
                                 "lines": lines}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 10 == 0 or n == len(todo):
                per = (time.time() - started) / n
                left = per * (len(todo) - n)
                print("  %d/%d  %.1fs a page, about %d min left"
                      % (n, len(todo), per, round(left / 60)), flush=True)

    print("Done. %s" % out)


if __name__ == "__main__":
    main()
