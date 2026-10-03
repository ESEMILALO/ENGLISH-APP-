"""Read the phrasal verb book out of a folder of screenshots.

Each page holds two or three phrasal verbs, each with a meaning and an
example sentence. This pulls them out into `tools/book_verbs.json`, which
`add_book_words.py` then turns into rows in the spreadsheet.

Pages are sent a few at a time and the answers are written out as they
arrive, so stopping this and running it again carries on where it left
off rather than starting the book over.

    python tools/read_book.py "C:\\Users\\Eduar\\OneDrive\\Pictures\\libro"
"""

import argparse
import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "server"))

from glossary import api_key  # noqa: E402

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"
API_VERSION = "2023-06-01"
OUT = HERE / "book_verbs.json"

PER_CALL = 4          # pages per request
PAGE_WIDTH = 760      # what the model is shown

SYSTEM = """You are reading pages from a book of English phrasal verbs.

Each page has two or three entries. An entry has the phrasal verb as its \
heading, a "Meaning" and an "Example" sentence. Copy them out exactly as \
printed -- do not reword, do not improve, do not add entries that are not \
there.

The pages are given in order and numbered. For each entry return:
- "page": the number of the page it came from, as given to you
- "verb": the phrasal verb, exactly as the heading prints it
- "meaning": the meaning, exactly as printed
- "example": the example sentence, exactly as printed

A page with no entries on it -- a cover, a chapter divider, a contents \
list, a blank -- contributes nothing. Say nothing about it.

Return ONLY a JSON array of those objects, no other text."""


def encode(path):
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def first_json(text):
    """The first complete JSON array in a reply, whatever surrounds it."""
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    at = text.find("[")
    while at >= 0:
        depth, in_str, esc = 0, False, False
        for i in range(at, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[at:i + 1])
                    except Exception:
                        break
        at = text.find("[", at + 1)
    return None


def ask(pages, key, attempts=4):
    content = []
    for number, path in pages:
        content.append({"type": "text", "text": "Page %d:" % number})
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": encode(path)}})

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": content}],
    }).encode("utf-8")

    last = None
    for attempt in range(attempts):
        req = urllib.request.Request(API_URL, data=body, method="POST", headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": API_VERSION,
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                payload = json.loads(res.read().decode("utf-8"))
            text = "".join(p.get("text", "") for p in payload.get("content", []))
            got = first_json(text.strip())
            if got is None:
                raise ValueError("no entries in the reply")
            return got
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (408, 409, 429, 500, 502, 503, 504, 529):
                raise
        except Exception as e:
            last = e
        time.sleep(3 * (attempt + 1))
    raise last


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", nargs="?",
                    default=str(HERE.parent.parent.parent / "Pictures" / "libro"),
                    help="the folder of screenshots")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many pages")
    args = ap.parse_args()

    key = api_key()
    if not key:
        sys.exit("This needs your Anthropic key -- the same one the app uses.")

    try:
        from PIL import Image, ImageChops
    except ImportError:
        sys.exit("This needs Pillow:  pip install pillow")

    src = Path(args.folder)
    shots = sorted(src.glob("*.jpg")) + sorted(src.glob("*.png"))
    if not shots:
        sys.exit("No pictures in %s" % src)
    print("%d pictures in %s\n" % (len(shots), src.name))

    # The screenshots are phone-shaped with black bars; the page is the
    # part in the middle, and it is all the model needs to see.
    work = HERE / "book-pages"
    work.mkdir(exist_ok=True)
    pages = []
    for i, shot in enumerate(shots, 1):
        trimmed = work / ("page-%03d.jpg" % i)
        if not trimmed.exists():
            im = Image.open(shot).convert("RGB")
            grey = im.convert("L")
            mask = ImageChops.invert(grey).point(lambda p: 255 if p < 240 else 0)
            box = mask.getbbox()
            if box:
                im = im.crop(box)
            im = im.resize((PAGE_WIDTH, round(im.height * PAGE_WIDTH / im.width)),
                           Image.LANCZOS)
            im.save(trimmed, "JPEG", quality=80, optimize=True)
        pages.append((i, trimmed))

    if args.limit:
        pages = pages[:args.limit]

    found = {}
    if OUT.exists():
        try:
            for row in json.loads(OUT.read_text(encoding="utf-8")):
                found.setdefault(row["page"], []).append(row)
        except Exception:
            found = {}

    todo = [p for p in pages if p[0] not in found]
    if not todo:
        print("Every page has been read already.")
    else:
        print("%d pages to read.\n" % len(todo))

    for start in range(0, len(todo), PER_CALL):
        batch = todo[start:start + PER_CALL]
        try:
            rows = ask(batch, key)
        except Exception as e:
            print("  pages %s failed: %s" % ([n for n, _ in batch], str(e)[:70]))
            continue
        for row in rows:
            try:
                page = int(row.get("page"))
            except (TypeError, ValueError):
                continue
            verb = str(row.get("verb") or "").strip()
            if not verb:
                continue
            found.setdefault(page, []).append({
                "page": page, "verb": verb,
                "meaning": str(row.get("meaning") or "").strip(),
                "example": str(row.get("example") or "").strip()})
        # pages with nothing on them are still read, so they are not re-read
        for number, _ in batch:
            found.setdefault(number, [])
        flat = [r for page in sorted(found) for r in found[page]]
        OUT.write_text(json.dumps(flat, indent=1, ensure_ascii=False), encoding="utf-8")
        print("  read %d/%d pages, %d verbs so far"
              % (min(start + PER_CALL, len(todo)), len(todo), len(flat)))

    flat = [r for page in sorted(found) for r in found[page]]
    print("\n%d phrasal verbs in %s" % (len(flat), OUT.name))


if __name__ == "__main__":
    main()
