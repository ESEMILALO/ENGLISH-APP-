"""
Adding a word to the glossary.

When you tap a word while practising, it comes here. Claude writes the
entry in the same style as the rest of your spreadsheet, and the row is
appended to ENGLISH SCHOOL.xlsx.

THE KEY:
    Fully automatic filling needs an Anthropic API key. Put it in

        server/anthropic_key.txt

    (one line, nothing else) or set ANTHROPIC_API_KEY in the environment.
    Get one from console.anthropic.com. Without a key nothing is lost --
    words are queued in progress/pending-words.json and filled in the
    moment a key appears.

THE FORMAT:
    Column A  Word/expression
    Column B  Pronunciation, respelled for a Spanish reader ("yat daun")
    Column C  Meaning 1, as "English gloss - Spanish."
    Column D  Example sentence using the word
    Column E/F, G/H  further meanings and examples, if the word has them
    Column I  Notes: verb forms, register, anything worth knowing
"""

import datetime
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

import model

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "ENGLISH SCHOOL.xlsx"
KEY_FILE = Path(__file__).resolve().parent / "anthropic_key.txt"
PENDING = ROOT / "progress" / "pending-words.json"
BACKUPS = ROOT / "backups"

# Where a word goes when nothing says otherwise. You are asked each time,
# so this is only the fallback.
TARGET_SHEET = "School vocabulary"

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"
API_VERSION = "2023-06-01"

MEANING_COLS = [(3, 4), (5, 6), (7, 8)]  # (meaning, example) column pairs
NOTES_COL = 9


def api_key():
    """Any key at all, whichever service it belongs to.

    Everything that used to ask for the Anthropic key is really asking
    "can we look things up?", and the free Gemini key answers that just
    as well.
    """
    return model.anthropic_key() or model.gemini_key()


def which_service(key):
    """Whose key is this? They do not look alike.

    Anthropic's begin sk-ant. Anything else is treated as Google's,
    because that is the free one and therefore the one most likely to be
    getting pasted.
    """
    return "anthropic" if (key or "").strip().startswith("sk-ant") else "gemini"


def check_key(key, timeout=20):
    """Is this key usable? Asked of the models list, which costs nothing.

    Worth doing at the moment it is pasted: a typo found now is a
    sentence on screen, and a typo found later is a word that silently
    fails to be added.
    """
    if which_service(key) == "gemini":
        return model.check_gemini(key, timeout)
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/models?limit=1",
        headers={"x-api-key": key, "anthropic-version": API_VERSION})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status == 200, None
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, "that key was not accepted"
        return False, "the check failed (HTTP %s)" % e.code
    except Exception as e:
        return False, "could not reach the API (%s)" % str(e)[:80]


def save_key(key):
    """Write the key, but only once it is known to work."""
    key = (key or "").strip()
    if not key:
        return {"ok": False, "message": "no key given"}
    if len(key) > 300 or "\n" in key:
        return {"ok": False, "message": "that does not look like a key"}
    ok, why = check_key(key)
    if not ok:
        return {"ok": False, "message": why}
    # A key that works means the old complaint is no longer true, and
    # leaving it set would keep the banner up over a working key.
    model._remember(None)
    model._ASKED_ONCE = False
    if which_service(key) == "gemini":
        model.GEMINI_KEY.write_text(key + "\n", encoding="utf-8")
        try:
            model.GEMINI_MODEL_FILE.unlink()      # choose the model afresh
        except OSError:
            pass
        return {"ok": True,
                "message": "Google key saved and working. Nothing costs anything now."}
    KEY_FILE.write_text(key + "\n", encoding="utf-8")
    return {"ok": True, "message": "key saved and working"}


# --- the queue, for when there is no key yet --------------------------------

def read_pending():
    if not PENDING.exists():
        return []
    try:
        return json.loads(PENDING.read_text(encoding="utf-8"))
    except Exception:
        return []


def write_pending(items):
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    tmp = PENDING.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(PENDING)


def queue_word(word, context, sheet=None):
    items = read_pending()
    if any(i.get("word", "").lower() == word.lower() for i in items):
        return items, False
    items.append({"word": word, "context": context, "sheet": sheet or TARGET_SHEET,
                  "addedAt": datetime.datetime.now().isoformat(timespec="seconds")})
    write_pending(items)
    return items, True


def drop_pending(word):
    items = [i for i in read_pending() if i.get("word", "").lower() != word.lower()]
    write_pending(items)


# --- looking the word up ----------------------------------------------------

PROMPT = """You are filling in one row of a Spanish speaker's English vocabulary \
spreadsheet. Match the existing style exactly.

The columns, and real rows from the sheet so you can see the style:

Word: Supper
Pronunciation: super
Meaning 1: Evening meal — Cena.
Example: We had soup for supper.
Notes: More common in some regions than dinner.

Word: Jot down
Pronunciation: yat daun
Meaning 1: Write quickly — Anotar.
Example: Jot down the phone number.
Notes: Regular verb. Base: jot down — Present: jots down — Past: jotted down — \
Past participle: jotted down. Separable: jot something down.

Rules:
- Pronunciation is respelled so a Spanish reader says it correctly. Not IPA. \
Use Spanish spelling conventions, and mark the stressed syllable with an accent \
where Spanish would (for example "super" becomes "super" with an accent on the u).
- Each meaning reads "English gloss — Spanish." The separator is the em dash
  character shown in the examples above, not a hyphen, and the line ends in a
  full stop.
- Give a second and third meaning only if the word genuinely has distinct common \
senses. Most words have one.
- Every meaning gets its own natural example sentence that uses the word.
- Notes: if it is a verb, give its forms in the style above (Regular verb. Base: \
... Present: ... Past: ... Past participle: ...), plus anything else worth knowing \
such as register, separability or a common confusion. If it is not a verb, give a \
short useful note or leave it empty.
- Write the word in column A the way it should be studied: bare, and capitalised, \
like "Harness" or "Jot down". Not "to harness".

Return ONLY a JSON object, no other text:
{"word": "...", "pronunciation": "...", "meanings": [{"meaning": "...", \
"example": "..."}], "notes": "..."}"""


def ask_claude(word, context, key, timeout=45, attempts=3):
    """Ask for the entry, retrying a stumble.

    A dropped connection or a busy minute at the API is not a reason to
    make you come back later, so a failure that might pass is tried again
    after a short wait. A refusal that will not pass -- a bad key, a
    malformed request -- is raised at once.
    """
    last = None
    for attempt in range(attempts):
        try:
            return _ask_once(word, context, key, timeout)
        except urllib.error.HTTPError as e:
            # a 4xx is our fault and waiting will not change it; 429 and 5xx may pass
            # 529 is Anthropic's own "overloaded", which is the most
            # likely one to pass on a second try
            if e.code not in (408, 409, 429, 500, 502, 503, 504, 529):
                raise
            last = e
        except Exception as e:
            last = e
        if attempt + 1 < attempts:
            time.sleep(1.5 * (attempt + 1))
    raise last


def _ask_once(word, context, key, timeout):
    """One attempt. Raises on anything that is not a usable answer."""
    user = "The word to add: " + word
    if context:
        user += "\n\nIt appeared in this sentence, which may disambiguate it:\n" + context

    # Room for the model's own working as well as the entry itself.
    text = model.ask(PROMPT, [{"role": "user", "content": user}],
                     max_tokens=2000, timeout=timeout).strip()
    # Be forgiving about a fenced block, even though the prompt asks for none.
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    entry = json.loads(text)

    if not entry.get("word") or not entry.get("meanings"):
        raise ValueError("the answer had no word or no meanings")
    return entry


# --- writing it into the workbook ------------------------------------------

def sheet_names():
    import openpyxl
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def resolve_sheet(wanted):
    """The sheet to write to, matched loosely.

    The name comes back from the app, and a stray difference in case or
    spacing should send the word to the right list rather than to the
    fallback -- and must never be taken as a new sheet to create.
    """
    names = sheet_names()
    if wanted:
        for n in names:
            if n.strip().lower() == str(wanted).strip().lower():
                return n
    return TARGET_SHEET if TARGET_SHEET in names else names[0]


def normalise(word):
    """How a word is compared against the sheet.

    "To strip", "strip" and "Strip" are all the same entry, so the
    comparison ignores case and a leading "to ".
    """
    w = str(word or "").strip().lower()
    if w.startswith("to "):
        w = w[3:].strip()
    return w


def already_there(word):
    """Where the word already lives, and what it says there.

    Returns (sheet, meaning) or (None, None). The meaning comes back so
    the app can show it: "already in Series" is a dead end, while seeing
    the entry tells you at a glance whether it is really the word you
    meant.
    """
    import openpyxl
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True)
    target = normalise(word)
    try:
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(min_row=2, max_col=3, values_only=True):
                if row[0] and normalise(row[0]) == target:
                    return sheet, (row[2] if len(row) > 2 else None)
    finally:
        wb.close()
    return None, None


def tidy(text):
    """Make the separator match the rest of the sheet.

    The spreadsheet puts an em dash between the English gloss and the
    Spanish. A hyphen or en dash with spaces around it is that separator
    written wrongly; a hyphen inside a word has no spaces round it and is
    left alone.
    """
    if not text:
        return text
    return re.sub(r"\s+[-\u2013]\s+", " \u2014 ", str(text).strip())


def append_row(entry, sheet=None):
    """Add the entry to the workbook, keeping a dated copy of it first."""
    import openpyxl

    BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy(WORKBOOK, BACKUPS / ("ENGLISH SCHOOL.pre-glossary-%s.xlsx" % stamp))

    wb = openpyxl.load_workbook(WORKBOOK)
    ws = wb[sheet or TARGET_SHEET]
    row = ws.max_row + 1

    ws.cell(row=row, column=1).value = entry["word"].strip()
    ws.cell(row=row, column=2).value = (entry.get("pronunciation") or "").strip()
    for (m_col, e_col), sense in zip(MEANING_COLS, entry["meanings"][:3]):
        ws.cell(row=row, column=m_col).value = tidy(sense.get("meaning")) or None
        ws.cell(row=row, column=e_col).value = (sense.get("example") or "").strip() or None
    ws.cell(row=row, column=NOTES_COL).value = tidy(entry.get("notes")) or None

    wb.save(WORKBOOK)
    return row


def rebuild():
    """Regenerate the app so the new word is there on the next refresh."""
    import subprocess
    import sys
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "build_word_log.py")],
                         capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    return out.returncode == 0


def fill_pending(limit=25):
    """Work through the words that were waiting for a key."""
    if not api_key():
        return {"ok": False, "message": "still no key"}
    done, failed = [], []
    for item in list(read_pending())[:limit]:
        result = add(item.get("word", ""), item.get("context", ""), item.get("sheet"))
        if result.get("added") or result.get("already"):
            done.append(item.get("word"))
            drop_pending(item.get("word", ""))
        else:
            failed.append({"word": item.get("word"), "why": result.get("message")})
    return {"ok": True, "added": done, "failed": failed,
            "left": len(read_pending()),
            "message": "%d added, %d left" % (len(done), len(read_pending()))}


def add(word, context="", sheet=None):
    """The whole job. Returns a dict the app can show the user."""
    word = (word or "").strip()
    if not word:
        return {"ok": False, "error": "no word given"}
    if len(word) > 60:
        return {"ok": False, "error": "that is too long to be a word"}
    target = resolve_sheet(sheet)

    where, meaning = already_there(word)
    if where:
        return {"ok": False, "already": True, "sheet": where, "meaning": meaning,
                "word": word,
                "message": "“%s” is already in %s." % (word, where)}

    key = api_key()
    if not key:
        queue_word(word, context, target)
        return {"ok": True, "queued": True, "sheet": target,
                "message": "“%s” is saved to fill in later — no API key yet." % word}

    try:
        entry = ask_claude(word, context, key)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        queue_word(word, context, target)
        low = detail.lower()
        if "credit balance" in low or "billing" in low or "quota" in low:
            why = ("Your Anthropic credit has run out, so the meaning could not "
                   "be written. The word is saved and will be filled in as soon "
                   "as there is credit.")
        elif e.code in (401, 403):
            why = ("The API key was not accepted. The word is saved and will be "
                   "filled in once the key works.")
        else:
            why = "Saved for later; the lookup failed (HTTP %s)." % e.code
        return {"ok": False, "queued": True,
                "message": why,
                "detail": detail}
    except Exception as e:
        queue_word(word, context, target)
        why = "%s: %s" % (type(e).__name__, e)
        return {"ok": False, "queued": True,
                "message": "Saved for later %s the lookup failed after three tries." % DASH,
                "detail": why[:300]}

    # Look again with the word the lookup settled on. You may have typed
    # "to strip" or "cubicles"; what comes back is "Strip" and "Cubicle",
    # and that is the spelling that has to be checked, or the same word
    # goes into the sheet twice under two names.
    where, meaning = already_there(entry["word"])
    if where:
        drop_pending(word)
        same = normalise(entry["word"]) == normalise(word)
        return {"ok": False, "already": True, "sheet": where, "meaning": meaning,
                "word": entry["word"],
                "message": ("“%s” is already in %s." % (entry["word"], where))
                if same else
                ("“%s” is already in %s — you typed “%s”." %
                 (entry["word"], where, word))}

    row = append_row(entry, target)
    drop_pending(word)
    rebuilt = rebuild()
    return {"ok": True, "added": True, "row": row, "sheet": target,
            "rebuilt": rebuilt, "entry": entry,
            "message": "“%s” added to %s." % (entry["word"], target)}
