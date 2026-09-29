"""
Conversation practice.

Once the day's words are finished, you can talk to someone who is playing
a part -- a shop assistant, an interviewer, a neighbour -- and the words
you have just learnt are the ones the conversation is built to need.

WHY IT IS NOT JUST A CHATBOT:
    Recognising a word is easy and producing one is hard, so the only
    thing scored here is what you actually write. Each reply comes back
    with the target words you used, and they tick off as you go. The
    partner is told not to use them itself, so they have to come from
    you.

    It also corrects you, briefly, and in character -- a conversation
    that lets every mistake past is pleasant and useless.

Needs the same Anthropic key as the glossary, in server/anthropic_key.txt.
"""

import json
import re
import urllib.error
import urllib.request

from glossary import API_VERSION, api_key

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"
MAX_TURNS = 40

SYSTEM = """You are a conversation partner for %(name)s, a Spanish speaker \
learning English. You are playing this role:

%(scenario)s

Stay in that role. Reply the way a real person in that situation would: two \
or three short sentences, everyday English, and end in a way that invites a \
reply -- a question, a choice, a small problem to solve.

THE WORDS THEY ARE PRACTISING:
%(words)s

Steer the conversation so these words become the natural thing to say. Ask \
about the things they describe. Do not use the words yourself -- if you say \
them, there is nothing left for them to produce. Do not list them, hint at \
them in brackets, or mention that they are being practised.

Their English is intermediate. Do not simplify to nothing, and do not show \
off with idioms they will not know.

Return ONLY a JSON object, no other text:

{"reply": "what you say, in character",
 "used": ["target words they used correctly in their last message"],
 "correction": "one short note about a real mistake, or empty"}

For "used": only words from the list above, spelled as they are in the list, \
and only when used with the right meaning. A word they merely copied out of \
your own question does not count.

For "correction": only when it matters -- a wrong verb form, a word used with \
the wrong meaning, a phrasing no one says. Write it as one friendly line, for \
example: You said "I have 25 years" -- in English it is "I am 25 years old". \
Leave it empty for small slips and for anything you understood fine."""


EXPLAIN = """Someone learning English, whose first language is Spanish, \
has picked out something they did not understand. Explain it.

Keep it short. Three lines at most:
- what it means, in plain English
- the Spanish for it
- when people say it, if that is not obvious, or why it is worded that way

If it is an idiom, say so and give the nearest Spanish equivalent rather than \
a word-for-word translation. If it is ordinary language they simply have not \
met, just say what it means without making a fuss of it. Do not lecture, do \
not list grammar rules, and do not repeat the phrase back at them before \
starting.

Return ONLY a JSON object, no other text:

{"meaning": "what it means in plain English",
 "spanish": "the Spanish",
 "note": "when it is used or why it is put that way, or empty"}"""


def explain(phrase, context=""):
    """What does that mean? Asked of something they read, not something
    they wrote, so there is nothing to correct -- only to make clear."""
    phrase = (phrase or "").strip()
    if not phrase:
        return {"ok": False, "message": "nothing selected"}
    if len(phrase) > 300:
        return {"ok": False, "message": "that is too long to explain in one go"}

    key = api_key()
    if not key:
        return {"ok": False, "message": "Explaining needs an Anthropic API key."}

    user = "They did not understand: " + phrase
    if context:
        user += "\n\nIt appeared here, which may matter:\n" + context

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1500,
        "system": EXPLAIN,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": API_VERSION,
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "message": "The explanation did not arrive.",
                "detail": str(e)[:160]}

    text = "".join(p.get("text", "") for p in payload.get("content", [])).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        out = json.loads(text)
    except Exception:
        return {"ok": True, "phrase": phrase, "meaning": text, "spanish": "", "note": ""}

    return {"ok": True, "phrase": phrase,
            "meaning": (out.get("meaning") or "").strip(),
            "spanish": (out.get("spanish") or "").strip(),
            "note": (out.get("note") or "").strip()}


TRANSLATE = """Give the Spanish for a piece of English. Nothing else.

The person reading it speaks Spanish and is learning English. They have \
highlighted something while reading and want to know, straight away, what \
it says.

- Translate the sense it has HERE, in the sentence it came from, not the \
first sense in a dictionary.
- Natural Spanish, the way someone would actually say it. For an idiom, \
the Spanish people really use, not word for word.
- A single word may have two close translations: give at most two, \
separated by " / ".
- Keep a phrase a phrase and a sentence a sentence. Do not explain, do not \
add notes, do not repeat the English.

Return ONLY a JSON object, no other text: {"es": "the Spanish"}"""


def translate(phrase, context=""):
    """The quick one: what does this say, in Spanish.

    This fires whenever something is highlighted, so it is kept small and
    fast on purpose. Anything more than the translation belongs to
    explain(), which is a button away.
    """
    phrase = (phrase or "").strip()
    if not phrase:
        return {"ok": False, "message": "nothing selected"}
    if len(phrase) > 300:
        return {"ok": False, "message": "too long"}

    key = api_key()
    if not key:
        return {"ok": False, "message": "Translating needs an Anthropic API key."}

    user = phrase
    if context:
        user += "\n\n(from: " + context[:300] + ")"

    body = json.dumps({
        "model": MODEL,
        # Its own working counts against this, not just the answer, so a
        # budget that looks generous for one line is the right size.
        "max_tokens": 800,
        "system": TRANSLATE,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": API_VERSION,
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "message": "no answer", "detail": str(e)[:120]}

    text = "".join(p.get("text", "") for p in payload.get("content", [])).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        out = json.loads(text)
        es = (out.get("es") or "").strip()
    except Exception:
        es = text.strip().strip('"')
    if not es:
        return {"ok": False, "message": "no answer"}
    return {"ok": True, "phrase": phrase, "es": es}


SUGGEST = """You invent a situation for someone practising English.

These are the words they have just learnt:
%(words)s

Invent one everyday situation in which most of those words would come up naturally in conversation -- not a lesson about them, a real situation where someone would happen to need them. Look at what the words have in common and build the situation around that. If they pull in different directions, pick the largest group and let the rest fit where they can.

Return ONLY a JSON object, no other text:

{"name": "three or four words, like 'At the hardware shop'",
 "blurb": "one short line saying what is happening, addressed to them as 'You'",
 "role": "instructions to whoever plays the other part: who they are, what they want, and what they should ask about. Two or three sentences, written to them as 'You are...'"}"""


def suggest(words):
    """A situation built around the words, rather than one off a list."""
    key = api_key()
    if not key:
        return {"ok": False, "message": "Suggesting a situation needs an API key."}

    body = json.dumps({
        "model": MODEL,
        # generous, because the budget covers the model's own working
        # as well as the answer: too small and the reply comes back empty
        "max_tokens": 2000,
        "system": SUGGEST % {"words": "\n".join("- " + w for w in words)},
        "messages": [{"role": "user", "content": "Invent the situation."}],
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": API_VERSION,
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "message": "Could not think of one just now.",
                "detail": str(e)[:160]}

    text = "".join(p.get("text", "") for p in payload.get("content", [])).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        out = json.loads(text)
    except Exception:
        return {"ok": False, "message": "Could not think of one just now."}

    if not out.get("name") or not out.get("role"):
        return {"ok": False, "message": "Could not think of one just now."}
    return {"ok": True, "name": out["name"].strip(),
            "blurb": (out.get("blurb") or "").strip(),
            "role": out["role"].strip()}


def opening(scenario, words, name="the learner"):
    """The first thing the partner says, before the learner has spoken."""
    return ask([], scenario, words, name, first=True)


def ask(history, scenario, words, name="the learner", first=False):
    """One turn. history is [{role, content}, ...] of the real conversation."""
    key = api_key()
    if not key:
        return {"ok": False, "error": "no key",
                "message": "Conversation practice needs an Anthropic API key."}

    system = SYSTEM % {
        "name": name,
        "scenario": scenario,
        "words": "\n".join("- " + w for w in words),
    }

    messages = list(history)[-MAX_TURNS:]
    if first or not messages:
        messages = [{"role": "user",
                     "content": "Start the conversation. Say the first thing."}]

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 2000,
        "system": system,
        "messages": messages,
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": API_VERSION,
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": "http %s" % e.code,
                "message": "The reply did not arrive (HTTP %s)." % e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120],
                "message": "The reply did not arrive."}

    text = "".join(p.get("text", "") for p in payload.get("content", [])).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        out = json.loads(text)
    except Exception:
        # Rather than lose the turn, treat the whole thing as what was said.
        return {"ok": True, "reply": text, "used": [], "correction": ""}

    # Only ever tick off a word that really is on the list.
    lower = {w.lower(): w for w in words}
    used = []
    for w in (out.get("used") or []):
        hit = lower.get(str(w).strip().lower())
        if hit and hit not in used:
            used.append(hit)

    # The model sometimes overlooks a word that is plainly there. If the
    # learner wrote it exactly as it stands on the list, it counts --
    # nobody should have to argue with the tally about a word they used.
    said = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            said = str(m.get("content") or "")
            break
    if said:
        for w in words:
            if w in used:
                continue
            if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", said, re.I):
                used.append(w)

    return {"ok": True,
            "reply": (out.get("reply") or "").strip(),
            "used": used,
            "correction": (out.get("correction") or "").strip()}
