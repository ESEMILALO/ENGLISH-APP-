"""Where the app's answers come from.

Two services can answer: Anthropic, which is what this started with, and
Google's Gemini, which has a free allowance big enough for one person
learning English -- about fifteen hundred requests a day against the
handful you actually use. Whichever has a key is the one used, and
Gemini wins if both are there, because the free one should be the one
that runs.

Everything above this file talks in one shape -- a system prompt and a
list of {role, content} messages, with content either a string or a list
of text and image parts -- and this translates that into whatever the
service on the other end expects. Nothing else needs to know which one
answered.

Keys live beside this file and are never committed:
    server/anthropic_key.txt
    server/gemini_key.txt
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANTHROPIC_KEY = HERE / "anthropic_key.txt"
GEMINI_KEY = HERE / "gemini_key.txt"
GEMINI_MODEL_FILE = HERE / "gemini_model.txt"
PROBLEM_FILE = HERE / "last_problem.txt"

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-5"
ANTHROPIC_VERSION = "2023-06-01"

GEMINI_ROOT = "https://generativelanguage.googleapis.com/v1beta"
# Best first. Whichever answers is remembered, so a model being renamed
# costs one failed request rather than every request after it.
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-1.5-flash",
]


class ModelError(Exception):
    """Something went wrong, said in words worth putting on screen."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def _read(path, env):
    key = os.environ.get(env, "").strip()
    if key:
        return key
    if path.exists():
        key = path.read_text(encoding="utf-8").strip()
        if key:
            return key
    return None


def anthropic_key():
    return _read(ANTHROPIC_KEY, "ANTHROPIC_API_KEY")


def gemini_key():
    return _read(GEMINI_KEY, "GEMINI_API_KEY")


def provider():
    """Which service will answer, or None if neither can."""
    if gemini_key():
        return "gemini"
    if anthropic_key():
        return "anthropic"
    return None


def have_key():
    return provider() is not None


def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def _explain_http(err, who):
    """The service said why it refused; put that where it can be read."""
    detail = ""
    try:
        body = json.loads(err.read().decode("utf-8", "replace"))
        if isinstance(body, dict):
            inner = body.get("error") or {}
            detail = str(inner.get("message") or "")
    except Exception:
        detail = ""

    low = detail.lower()
    if "credit balance" in low or "billing" in low:
        return ModelError(
            "The Anthropic credit has run out. Either add credit, or put a "
            "free Google Gemini key in server/gemini_key.txt and the app "
            "will use that instead.", err.code)
    if err.code == 429 or "quota" in low or "rate limit" in low:
        return ModelError(
            "That was too many requests for the free allowance just now. "
            "Wait a minute and try again.", err.code)
    if err.code in (401, 403):
        return ModelError(
            "The %s key was not accepted. Check the key file in the server "
            "folder." % who, err.code)
    if err.code in (500, 502, 503, 504, 529):
        return ModelError("%s is busy or down for a moment. Try again shortly."
                          % who.title(), err.code)
    if detail:
        return ModelError(detail[:200], err.code)
    return ModelError("%s did not answer (HTTP %s)." % (who.title(), err.code),
                      err.code)


# --------------------------------------------------------------- shapes --

def _parts_to_gemini(content):
    """Our content -> Gemini's parts."""
    if isinstance(content, str):
        return [{"text": content}]
    parts = []
    for bit in content or []:
        kind = bit.get("type")
        if kind == "text":
            parts.append({"text": bit.get("text", "")})
        elif kind == "image":
            source = bit.get("source") or {}
            parts.append({"inline_data": {
                "mime_type": source.get("media_type", "image/jpeg"),
                "data": source.get("data", ""),
            }})
    return parts or [{"text": ""}]


def _ask_gemini(system, messages, max_tokens, timeout):
    key = gemini_key()
    contents = []
    for m in messages:
        role = "model" if m.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": _parts_to_gemini(m.get("content"))})

    body = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}

    remembered = None
    if GEMINI_MODEL_FILE.exists():
        remembered = GEMINI_MODEL_FILE.read_text(encoding="utf-8").strip() or None
    candidates = ([remembered] if remembered else []) + \
                 [m for m in GEMINI_MODELS if m != remembered]

    last = None
    for name in candidates:
        url = "%s/models/%s:generateContent?key=%s" % (GEMINI_ROOT, name, key)
        try:
            out = _post(url, body, {"content-type": "application/json"}, timeout)
        except urllib.error.HTTPError as e:
            problem = _explain_http(e, "gemini")
            # Only a missing model is worth trying the next name for.
            if e.code == 404:
                last = problem
                continue
            raise problem
        except Exception as e:
            raise ModelError("Could not reach Gemini: %s" % str(e)[:120])

        if name != remembered:
            try:
                GEMINI_MODEL_FILE.write_text(name, encoding="utf-8")
            except OSError:
                pass

        for candidate in out.get("candidates") or []:
            parts = (candidate.get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts).strip()
            if text:
                return text
            if candidate.get("finishReason") == "MAX_TOKENS":
                raise ModelError(
                    "The answer was cut off before it started. This is a bug "
                    "worth reporting: the room given for the reply was too "
                    "small.")
        raise ModelError("Gemini answered with nothing at all.")

    raise last or ModelError("No Gemini model would answer.")


def _ask_anthropic(system, messages, max_tokens, timeout):
    key = anthropic_key()
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        body["system"] = system
    try:
        out = _post(ANTHROPIC_URL, body, {
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
        }, timeout)
    except urllib.error.HTTPError as e:
        raise _explain_http(e, "anthropic")
    except Exception as e:
        raise ModelError("Could not reach Anthropic: %s" % str(e)[:120])
    return "".join(p.get("text", "") for p in out.get("content", [])).strip()


# Having a key file and having a key that works are different things,
# and the difference is invisible until something is asked. So the last
# answer is remembered: the app can then say "the key stopped working,
# here is why" in the place where you would fix it, instead of failing
# quietly in six different corners.
LAST_PROBLEM = None
_ASKED_ONCE = False


def _remember(problem):
    """Across restarts too, or the app forgets every time it is started.

    Restarting the server does not put credit on an account, and an app
    that cheerfully reports "all fine" until the next thing fails is how
    somebody ends up hunting for a box that is not being shown.
    """
    global LAST_PROBLEM
    LAST_PROBLEM = problem
    try:
        if problem:
            PROBLEM_FILE.write_text(problem, encoding="utf-8")
        elif PROBLEM_FILE.exists():
            PROBLEM_FILE.unlink()
    except OSError:
        pass


def last_problem():
    global LAST_PROBLEM
    if LAST_PROBLEM is None and PROBLEM_FILE.exists():
        try:
            LAST_PROBLEM = PROBLEM_FILE.read_text(encoding="utf-8").strip() or None
        except OSError:
            pass
    return LAST_PROBLEM


def health():
    """Is there a key, and can it actually answer?

    A key file proves nothing: the one here is real, correctly spelled,
    and out of money. So the first time anybody asks, the question is put
    to the service itself -- one word, a fraction of a penny if it works
    at all -- and the answer is kept.
    """
    global _ASKED_ONCE
    if provider() is None:
        return False, None
    known = last_problem()
    if known:
        return False, known
    if _ASKED_ONCE:
        return True, None
    _ASKED_ONCE = True
    try:
        ask("Answer with one word: ok",
            [{"role": "user", "content": "ok"}], max_tokens=300, timeout=20)
    except ModelError as e:
        return False, str(e)
    except Exception:
        return True, None          # a network blip is not a broken key
    return True, None


def ask(system, messages, max_tokens=2000, timeout=60):
    """One question, one answer, from whichever service has a key."""
    global LAST_PROBLEM
    which = provider()
    if which is None:
        raise ModelError("This needs a key. The free one is from Google AI "
                         "Studio and takes two minutes.")
    try:
        if which == "gemini":
            text = _ask_gemini(system, messages, max_tokens, timeout)
        else:
            text = _ask_anthropic(system, messages, max_tokens, timeout)
    except ModelError as e:
        _remember(str(e))
        raise
    _remember(None)
    return text


# --------------------------------------------------------- checking keys --

def check_gemini(key, timeout=20):
    """Is this a working key? Returns (ok, what to say)."""
    key = (key or "").strip()
    if not key:
        return False, "no key given"
    url = "%s/models?key=%s" % (GEMINI_ROOT, key)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as res:
            out = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (400, 401, 403):
            return False, "that key was not accepted"
        return False, "the check failed (HTTP %s)" % e.code
    except Exception as e:
        return False, "could not reach Google (%s)" % str(e)[:60]
    names = [m.get("name", "") for m in (out.get("models") or [])]
    if not names:
        return False, "the key works but offers no models"
    return True, "%d models available" % len(names)


def save_gemini(key):
    global _ASKED_ONCE
    ok, why = check_gemini(key)
    if not ok:
        return False, why
    _remember(None)
    _ASKED_ONCE = False
    GEMINI_KEY.write_text(key.strip(), encoding="utf-8")
    try:
        GEMINI_MODEL_FILE.unlink()        # find the best one again
    except OSError:
        pass
    return True, why
