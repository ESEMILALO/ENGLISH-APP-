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
import shutil
import urllib.error
import urllib.request
from pathlib import Path

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
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key
    return None


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
Meaning 1: Evening meal - Cena.
Example: We had soup for supper.
Notes: More common in some regions than dinner.

Word: Jot down
Pronunciation: yat daun
Meaning 1: Write quickly - Anotar.
Example: Jot down the phone number.
Notes: Regular verb. Base: jot down - Present: jots down - Past: jotted down - \
Past participle: jotted down. Separable: jot something down.

Rules:
- Pronunciation is respelled so a Spanish reader says it correctly. Not IPA. \
Use Spanish spelling conventions, and mark the stressed syllable with an accent \
where Spanish would (for example "super" becomes "super" with an accent on the u).
- Each meaning reads "English gloss - Spanish." with an em dash and a final full stop.
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


def ask_claude(word, context, key, timeout=45):
    """Ask for the entry. Raises on anything that is not a usable answer."""
    user = "The word to add: " + word
    if context:
        user += "\n\nIt appeared in this sentence, which may disambiguate it:\n" + context

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "system": PROMPT,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": API_VERSION,
    })
    with urllib.request.urlopen(req, timeout=timeout) as res:
        payload = json.loads(res.read().decode("utf-8"))

    text = "".join(part.get("text", "") for part in payload.get("content", []))
    text = text.strip()
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


def already_there(word):
    import openpyxl
    wb = openpyxl.load_workbook(WORKBOOK, read_only=True)
    target = word.strip().lower()
    try:
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
                if row[0] and str(row[0]).strip().lower() == target:
                    return sheet
    finally:
        wb.close()
    return None


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
        ws.cell(row=row, column=m_col).value = (sense.get("meaning") or "").strip() or None
        ws.cell(row=row, column=e_col).value = (sense.get("example") or "").strip() or None
    ws.cell(row=row, column=NOTES_COL).value = (entry.get("notes") or "").strip() or None

    wb.save(WORKBOOK)
    return row


def rebuild():
    """Regenerate the app so the new word is there on the next refresh."""
    import subprocess
    import sys
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "build_word_log.py")],
                         capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    return out.returncode == 0


def add(word, context="", sheet=None):
    """The whole job. Returns a dict the app can show the user."""
    word = (word or "").strip()
    if not word:
        return {"ok": False, "error": "no word given"}
    if len(word) > 60:
        return {"ok": False, "error": "that is too long to be a word"}
    target = resolve_sheet(sheet)

    where = already_there(word)
    if where:
        return {"ok": False, "already": True, "sheet": where,
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
        return {"ok": False, "queued": True,
                "message": "Saved for later; the lookup failed (HTTP %s)." % e.code,
                "detail": detail}
    except Exception as e:
        queue_word(word, context, target)
        return {"ok": False, "queued": True,
                "message": "Saved for later; the lookup failed.",
                "detail": str(e)[:200]}

    row = append_row(entry, target)
    drop_pending(word)
    rebuilt = rebuild()
    return {"ok": True, "added": True, "row": row, "sheet": target,
            "rebuilt": rebuilt, "entry": entry,
            "message": "“%s” added to %s." % (entry["word"], target)}
