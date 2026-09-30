"""The voice the app speaks with, when a better one than the browser's exists.

Chrome offers whatever Windows happens to have, and on this machine the
best of those is a serviceable robot. Edge ships a set of neural voices
that sound like people, and they can be reached from here without a key.

So: the page asks this for a sentence, gets an MP3 back, and plays it. If
anything at all goes wrong -- the package is missing, the line is down,
the voice has been renamed -- the page is told so and falls back to the
browser voice it was using before. A conversation must never go silent
because the nicer voice was unavailable.

Every clip is kept in server/voice-cache, because the same words are said
again and again: a word on a practice card, a sentence read twice. The
cache is capped and the oldest goes first.
"""

import asyncio
import hashlib
import io
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "voice-cache"
CACHE_MAX = 400            # clips, not bytes; each is tens of kilobytes
TEXT_MAX = 1200

# The ones worth offering. Others exist; these are the four that sound
# like someone talking to you rather than reading to you.
VOICES = [
    {"id": "en-US-AvaNeural", "name": "Ava", "note": "warm, friendly"},
    {"id": "en-US-AndrewNeural", "name": "Andrew", "note": "warm, confident"},
    {"id": "en-US-EmmaNeural", "name": "Emma", "note": "clear, cheerful"},
    {"id": "en-US-BrianNeural", "name": "Brian", "note": "casual, sincere"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia", "note": "British"},
    {"id": "en-GB-RyanNeural", "name": "Ryan", "note": "British"},
]
KNOWN = {v["id"] for v in VOICES}
DEFAULT = "en-US-AvaNeural"


def available():
    """Whether the better voices can be reached at all."""
    try:
        import edge_tts  # noqa: F401
        return True
    except Exception:
        return False


def voices():
    return {"ok": available(), "voices": VOICES, "default": DEFAULT}


def _cache_path(voice, text, rate):
    key = "%s|%s|%s" % (voice, rate, text)
    return CACHE / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".mp3")


def _trim_cache():
    try:
        clips = sorted(CACHE.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return
    for old in clips[:-CACHE_MAX]:
        try:
            old.unlink()
        except OSError:
            pass


async def _fetch(text, voice, rate):
    import edge_tts
    out = io.BytesIO()
    speaker = edge_tts.Communicate(text, voice, rate=rate)
    async for chunk in speaker.stream():
        if chunk["type"] == "audio":
            out.write(chunk["data"])
    return out.getvalue()


def say(text, voice="", rate=0):
    """Returns (audio_bytes, error). One of the two is always None."""
    text = (text or "").strip()
    if not text:
        return None, "nothing to say"
    if len(text) > TEXT_MAX:
        text = text[:TEXT_MAX]
    if voice not in KNOWN:
        voice = DEFAULT

    # edge-tts wants it as a signed percentage, and a card reading one
    # word wants it slower than a sentence in a conversation.
    try:
        rate = int(rate)
    except (TypeError, ValueError):
        rate = 0
    rate = max(-40, min(40, rate))
    rate_s = "%+d%%" % rate

    cached = _cache_path(voice, text, rate_s)
    if cached.exists():
        try:
            data = cached.read_bytes()
            if data:
                os.utime(cached, None)      # keep the ones being used
                return data, None
        except OSError:
            pass

    if not available():
        return None, "the better voices are not installed"

    try:
        data = asyncio.run(_fetch(text, voice, rate_s))
    except Exception as e:
        return None, str(e)[:140]
    if not data:
        return None, "no audio came back"

    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(data)
        if int(time.time()) % 20 == 0:
            _trim_cache()
    except OSError:
        pass                                 # a clip that cannot be kept still plays

    return data, None
