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
        "max_tokens": 700,
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

    return {"ok": True,
            "reply": (out.get("reply") or "").strip(),
            "used": used,
            "correction": (out.get("correction") or "").strip()}
