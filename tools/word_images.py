"""Find a picture for every word in the spreadsheet.

Searching an image library for the word itself does not work. "Recline"
brings back a reclining Buddha, "stall door" a horse's stall, "essential"
a face scrub -- a picture that teaches the wrong thing is worse than no
picture at all. So the meaning you already wrote does the choosing:
Claude reads the word, its meaning and its example and gives back a short,
concrete search term, and that term is what goes to the library.

The pictures come from Wikimedia Commons, which needs no key and asks
only that you say who you are and do not hammer it. Everything is kept in
`tools/word_images.json` and the files in `app/images/`, so stopping this
half way and running it again carries on where it left off.

    python tools/word_images.py              # everything still missing
    python tools/word_images.py --limit 20   # a taste of it first
    python tools/word_images.py --redo Lawsuit   # one word again, new picture
"""

import argparse
import base64
import hashlib
import io
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOLDER = HERE.parent
APP = FOLDER / "app"
IMAGES = APP / "images"
MAP_FILE = HERE / "word_images.json"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(FOLDER / "server"))

import build_word_log as build            # noqa: E402  (path set above)
from glossary import api_key              # noqa: E402

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"
API_VERSION = "2023-06-01"

# Commons asks for a real name and a way to be contacted. Being a good
# guest is the whole reason this needs no key.
UA = "WordLog/1.0 (personal English vocabulary study app; single user, local)"

COMMONS = "https://commons.wikimedia.org/w/api.php"
PAUSE = 1.1          # seconds between calls to the search API
BATCH = 12           # words per request to Claude
TERM_TOKENS = 3000   # its own working counts against this, not just
                     # the answer -- a tight budget returns nothing

TERMS = """You are helping a Spanish speaker learn English vocabulary. For \
each numbered entry you get an English word or phrase and the meaning and \
example the learner already has for it.

Give back, for each one, a SHORT search term for a photograph library that \
would bring back a picture showing THAT meaning.

Rules for the term:
- Two or three words. Never a sentence. "reclining chair", not "a person \
leaning back in a reclining chair".
- Concrete and photographable: a thing, a place, or a person doing \
something. Libraries hold photographs of objects and scenes, not of ideas.
- It must show the meaning given, not another sense of the word. For \
"stall door" meaning a toilet cubicle, "toilet cubicle" -- never "horse \
stall".
- Plain everyday English. No brand names, no proper nouns unless the word \
itself is one.
- The meaning given is the one to show. A word with several senses still \
gets one picture, and it is the first sense, not whichever is easiest to \
photograph.
- For a word no photograph could honestly show -- most grammar words, and \
abstractions like "whereas" or "moreover" -- give "-" instead. A wrong \
picture teaches the wrong thing. Be honest about these rather than \
reaching.

Answer with JSON only: an array of objects, one per entry, in the same \
order, each {"n": <the number>, "q": "<the term, or ->"}. No other text."""


JUDGE = """You are choosing a picture for a word in a Spanish speaker's \
English vocabulary app. You are shown a word, the meaning the learner has \
for it, and some candidate pictures found by searching an image library.

Say which picture, if any, would help someone understand THAT meaning.

It must be a photograph of the real world. An engraving, a painting, a \
drawing, a diagram or a museum object is not what a learner needs, however \
well it fits -- refuse those unless the word itself is about art.

Choose a picture only if someone who did not know the word could look at \
it and get the right idea. A picture that shows a different sense of the \
word, or that needs the caption to make sense, teaches the wrong thing and \
is worse than no picture at all -- these libraries return a lot of \
near-misses, so refusing is the normal answer, not a failure.

Answer with JSON only: {"pick": <the number of the picture, or 0 for none>, \
"why": "<six words at most>"}"""


def first_json(text, opener):
    """The first complete JSON value in a reply, ignoring anything around it.

    A sentence before the answer, a fenced block, a stray bracket in
    "here is the list [in order]" -- none of that should cost a batch of
    twenty-five words, so every candidate is tried, not just the first.
    """
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    closer = "]" if opener == "[" else "}"
    at = text.find(opener)
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
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[at:i + 1])
                    except Exception:
                        break          # not it; look for the next one
        at = text.find(opener, at + 1)
    return None


def load_map():
    if MAP_FILE.exists():
        try:
            return json.loads(MAP_FILE.read_text(encoding="utf-8"))
        except Exception:
            print("  (the map file was unreadable; starting a fresh one)")
    return {}


def save_map(m):
    MAP_FILE.write_text(json.dumps(m, indent=1, ensure_ascii=False, sort_keys=True),
                        encoding="utf-8")


def ask_claude(payload, key, attempts=4):
    """One request, retried through the failures that tend to pass."""
    body = json.dumps(payload).encode("utf-8")
    last = None
    for attempt in range(attempts):
        req = urllib.request.Request(API_URL, data=body, method="POST", headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": API_VERSION,
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (408, 409, 429, 500, 502, 503, 504, 529):
                raise
        except Exception as e:
            last = e
        time.sleep(2 * (attempt + 1))
    raise last


def terms_for(chunk, key):
    """Ask for one search term per word. Returns {id: term}."""
    lines = []
    for i, w in enumerate(chunk, 1):
        senses = w.get("me") or []
        bits = ["%d. %s" % (i, w["w"])]
        first = senses[0] if senses else {}
        if first.get("m"):
            bits.append("   meaning: %s" % first["m"])
        if first.get("e"):
            bits.append("   example: %s" % first["e"])
        # The other senses are named only so it does not wander into one
        # of them: a word with three meanings still gets one picture.
        others = [x.get("m", "") for x in senses[1:3] if x.get("m")]
        if others:
            bits.append("   (not these other senses: %s)" % "; ".join(others))
        lines.append("\n".join(bits))

    out = ask_claude({
        "model": MODEL,
        "max_tokens": TERM_TOKENS,
        "system": TERMS,
        "messages": [{"role": "user", "content": "\n".join(lines)}],
    }, key)

    text = "".join(p.get("text", "") for p in out.get("content", [])).strip()
    got = first_json(text, "[")
    if got is None:
        wrapped = first_json(text, "{")
        if isinstance(wrapped, dict):
            for value in wrapped.values():
                if isinstance(value, list):
                    got = value
                    break
    if not isinstance(got, list):
        (HERE / "last-bad-reply.txt").write_text(text, encoding="utf-8")
        raise ValueError("no list of terms in the reply "
                         "(it is in tools/last-bad-reply.txt)")

    terms = {}
    for row in got:
        try:
            n = int(row.get("n"))
        except (TypeError, ValueError):
            continue
        if 1 <= n <= len(chunk):
            q = str(row.get("q") or "").strip()
            terms[chunk[n - 1]["id"]] = q
    return terms


NOT_ART = (" -painting -drawing -engraving -lithograph -etching -woodcut"
           " -sculpture -manuscript -coat -arms -stamp -medal -fresco -map")


def commons_search(query, limit=6, tries=5):
    """Search Commons, backing off when told to slow down."""
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query + NOT_ART, "gsrnamespace": "6", "gsrlimit": str(limit),
        "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "480",
    }
    url = COMMONS + "?" + urllib.parse.urlencode(params)
    wait = 2.0
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < tries - 1:
                time.sleep(wait)
                wait *= 2
                continue
            raise
        except Exception:
            if attempt < tries - 1:
                time.sleep(wait)
                wait *= 2
                continue
            raise
    return {}


def plain(html):
    """Commons gives credit as little scraps of HTML."""
    text = re.sub(r"<[^>]+>", "", html or "")
    text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&#039;", "'")
    return " ".join(text.split())[:80]


def candidates(result, most=3):
    """The photographs worth putting in front of the judge."""
    pages = (result.get("query", {}) or {}).get("pages", {}) or {}
    # `index` keeps the search's own order, which the dict has lost.
    ordered = sorted(pages.values(), key=lambda p: p.get("index", 999))
    out = []
    for page in ordered:
        info = (page.get("imageinfo") or [{}])[0]
        if info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        thumb = info.get("thumburl")
        if not thumb:
            continue
        meta = info.get("extmetadata") or {}
        out.append({
            "thumb": thumb,
            "page": info.get("descriptionurl", ""),
            "title": page.get("title", "")[5:],
            "by": plain((meta.get("Artist") or {}).get("value", "")),
            "lic": plain((meta.get("LicenseShortName") or {}).get("value", "")),
        })
        if len(out) >= most:
            break
    return out


def grab(url):
    """Fetch the bytes without writing them down yet."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def judge(word, sense, shots, key):
    """Show the candidates to Claude and take its answer, or none.

    Searching finds pictures whose caption matches the words. Whether the
    picture actually shows the meaning is a different question, and the
    only way to answer it is to look.
    """
    content = [{"type": "text",
                "text": "Word: %s\nMeaning: %s" % (word, sense or "(not given)")}]
    for i, (data, ext) in enumerate(shots, 1):
        content.append({"type": "text", "text": "Picture %d:" % i})
        content.append({"type": "image", "source": {
            "type": "base64",
            "media_type": "image/png" if ext == ".png" else "image/jpeg",
            "data": base64.b64encode(data).decode("ascii"),
        }})

    out = ask_claude({
        "model": MODEL,
        "max_tokens": 300,
        "system": JUDGE,
        "messages": [{"role": "user", "content": content}],
    }, key)

    text = "".join(p.get("text", "") for p in out.get("content", [])).strip()
    got = first_json(text, "{")
    if not isinstance(got, dict):
        return 0, ""
    try:
        n = int(got.get("pick") or 0)
    except (TypeError, ValueError):
        return 0, ""
    if not (1 <= n <= len(shots)):
        return 0, str(got.get("why") or "")[:40]
    return n, str(got.get("why") or "")[:40]


def shrink(data, ext):
    """A card shows it small, and this folder is inside OneDrive."""
    try:
        from PIL import Image
    except ImportError:
        return data, ext
    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGB")
        if im.width > 400:
            im = im.resize((400, max(1, round(im.height * 400 / im.width))),
                           Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True, progressive=True)
        small = buf.getvalue()
        if small and len(small) < len(data):
            return small, ".jpg"
    except Exception:
        pass
    return data, ext


def keep(data, ext, word_id):
    """Write the chosen picture where the app can serve it."""
    stamp = hashlib.sha1(word_id.encode("utf-8")).hexdigest()[:10]
    name = re.sub(r"[^a-z0-9]+", "-", word_id.split("::")[-1].lower()).strip("-")[:28]
    data, ext = shrink(data, ext)
    out = IMAGES / ("%s-%s%s" % (name or "word", stamp, ext))
    out.write_bytes(data)
    return out.name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0,
                    help="stop after this many words (for a first look)")
    ap.add_argument("--redo", default="",
                    help="one word, looked up again for a different picture")
    args = ap.parse_args()

    key = api_key()
    if not key:
        sys.exit("This needs your Anthropic key -- the same one the app uses.")

    IMAGES.mkdir(parents=True, exist_ok=True)
    spreadsheet = build.find_spreadsheet()
    words, _ = build.extract_words(spreadsheet)
    by_id = {w["id"]: w for w in words}
    print("%d words in %s\n" % (len(words), spreadsheet.name))

    have = load_map()

    if args.redo:
        hits = [w for w in words if w["w"].lower() == args.redo.lower()]
        if not hits:
            sys.exit("No word called %r in the spreadsheet." % args.redo)
        for w in hits:
            old = have.pop(w["id"], None)
            if old and old.get("file"):
                try:
                    (IMAGES / old["file"]).unlink()
                except OSError:
                    pass
            # a different one this time: remember what was already turned
            # down so the search does not hand back the same picture
            seen = list((old or {}).get("seen") or [])
            if (old or {}).get("page"):
                seen.append(old["page"])
            have[w["id"]] = {"q": (old or {}).get("q", ""), "seen": seen}
        words = hits

    todo = [w for w in words if not (have.get(w["id"], {}) or {}).get("file")
            and not (have.get(w["id"], {}) or {}).get("none")]
    if args.limit:
        todo = todo[:args.limit]

    if not todo:
        print("Every word already has a picture. Nothing to do.")
        return

    print("%d to find. This is slow on purpose -- Commons is free and asks\n"
          "to be treated gently. Stop it whenever you like and run it again.\n"
          % len(todo))

    # --- the search terms, in batches ------------------------------------
    missing = [w for w in todo if not (have.get(w["id"], {}) or {}).get("q")]
    for start in range(0, len(missing), BATCH):
        chunk = missing[start:start + BATCH]
        try:
            terms = terms_for(chunk, key)
        except Exception as e:
            print("  terms failed for a batch (%s) -- carrying on" % str(e)[:60])
            continue
        for wid, q in terms.items():
            row = have.setdefault(wid, {})
            row["q"] = q
        save_map(have)
        print("  terms: %d/%d" % (min(start + BATCH, len(missing)), len(missing)))

    # --- the pictures ----------------------------------------------------
    found = refused = failed = 0
    for i, w in enumerate(todo, 1):
        row = have.setdefault(w["id"], {})
        q = (row.get("q") or "").strip()
        if not q:
            # the asking failed for this one; leave it for the next run
            failed += 1
            continue
        if q == "-":
            row["none"] = "nothing to photograph"
            refused += 1
            continue

        sense = ((w.get("me") or [{}])[0].get("m") or "")
        try:
            # Ask for a few extra when a different picture was wanted, so
            # the ones already turned down can be stepped over.
            past = row.get("seen") or []
            result = commons_search(q, limit=4 + len(past) + 2)
            shots = [c for c in candidates(result, most=3 + len(past))
                     if c["page"] not in past][:3]
            if not shots:
                row["none"] = "nothing found"
                refused += 1
            else:
                loaded = []
                for c in shots:
                    try:
                        data = grab(c["thumb"])
                        if len(data) >= 800:
                            loaded.append((c, data,
                                           ".png" if c["thumb"].lower().split("?")[0]
                                           .endswith(".png") else ".jpg"))
                    except Exception:
                        pass
                if not loaded:
                    row["none"] = "nothing found"
                    refused += 1
                else:
                    n, why = judge(w["w"], sense,
                                   [(d, e) for _, d, e in loaded], key)
                    if not n:
                        row["none"] = why or "none of them showed it"
                        row["seen"] = past + [c["page"] for c, _, _ in loaded]
                        refused += 1
                    else:
                        chosen, data, ext = loaded[n - 1]
                        name = keep(data, ext, w["id"])
                        row.update({"file": name, "title": chosen["title"],
                                    "by": chosen["by"], "lic": chosen["lic"],
                                    "page": chosen["page"], "why": why})
                        row.pop("none", None)
                        row.pop("seen", None)
                        found += 1
        except Exception as e:
            failed += 1
            print("  %-28s failed: %s" % (w["w"][:28], str(e)[:50]))

        if i % 5 == 0 or i == len(todo):
            save_map(have)
            print("  %d/%d  kept %d, no good picture %d, failed %d"
                  % (i, len(todo), found, refused, failed))
        time.sleep(PAUSE + random.uniform(0, 0.3))

    save_map(have)
    total = sum(1 for v in have.values() if v.get("file"))
    none = sum(1 for v in have.values() if v.get("none"))
    print("\nDone. %d words have a picture in app/images/; %d were left without "
          "one\nbecause nothing found really showed the meaning." % (total, none))
    print("Run  python tools/build_word_log.py  to put them in the app.")


if __name__ == "__main__":
    main()
