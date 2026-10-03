"""
Word Log server
---------------
Serves the app to this laptop, and to nothing else.

WHY THIS EXISTS:
    Opening vocabulary_practice.html as a file works, but a browser will
    not treat a file:// page as trustworthy. It refuses to remember the
    microphone permission, and it refuses to install the page as an app.

    http://localhost is trusted. Browsers count it as a secure origin in
    the same way as https, so the microphone is remembered and the app
    can still be installed -- with nothing exposed to any network.

HOW TO USE:
    python serve_word_log.py

    Leave it running, then open http://localhost:8777
"""

import argparse
import datetime
import http.client
import http.server
import json
import os
import re
import socketserver
import sys
import threading
from pathlib import Path

# Everything served lives in app/. Nothing outside it is reachable, and
# that includes the spreadsheet, the build scripts and this file.
ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "app"

# A copy of your progress, kept as an ordinary file in the project folder
# so it outlives the browser. Clearing site data, switching browser or a
# new laptop no longer costs you anything: the file is the real record
# and the browser is just where the app reads it from.
#
# No passcode guards this. The server answers 127.0.0.1 only, so the only
# thing that can reach it is this machine.
PROGRESS_DIR = ROOT / "progress"
PROGRESS_FILE = PROGRESS_DIR / "progress.json"
DAILY_DIR = PROGRESS_DIR / "daily"
KEEP_DAILY = 30

PROGRESS_LOCK = threading.Lock()
API_PROGRESS = "/api/progress"
API_GLOSSARY = "/api/glossary"
API_KEY_SET = "/api/key"
API_PENDING = "/api/glossary/pending"
API_CHAT = "/api/chat"
API_SCENARIO = "/api/scenario"
API_EXPLAIN = "/api/explain"
API_TRANSLATE = "/api/translate"
API_REVIEW = "/api/review"
API_SAY = "/api/say"
API_IMAGINE = "/api/imagine"
API_VOICES = "/api/voices"


def read_progress():
    if not PROGRESS_FILE.exists():
        return {"savedAt": None, "data": {}}
    try:
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except Exception:
        # A half-written file must not stop the app loading. The dated
        # copies in daily/ are the way back from that.
        return {"savedAt": None, "data": {}}


def keep_study(incoming, previous):
    """Carry forward the larger figure for every day already recorded.

    Time studied is the one number that can only be earned, so it must
    never come back down. A browser that has been cleared, or is simply
    behind, would otherwise write a smaller total over a real one and
    quietly take the day's work with it.
    """
    old = ((previous or {}).get("meta") or {}).get("study") or {}
    if not old:
        return incoming
    meta = incoming.setdefault("meta", {})
    study = meta.setdefault("study", {})
    for day, seconds in old.items():
        try:
            if float(seconds) > float(study.get(day, 0)):
                study[day] = seconds
        except (TypeError, ValueError):
            continue
    return incoming


def count_words(data):
    p = (data or {}).get("progress")
    return len(p) if isinstance(p, dict) else 0


def guard(incoming):
    """Decide whether a write may replace what is already stored.

    The app is open at more than one address -- the laptop, the installed
    app, a phone over the network -- and each of those is a separate
    browser store writing to this one file. A browser that has not caught
    up looks exactly like a browser that has lost everything, and letting
    it save would hand its stale copy to all the others.

    Words are only ever added, outside of an explicit reset, which comes
    through DELETE and not through here. So a write offering fewer words
    than are already stored is a browser that is behind, and it is
    refused: the app is told, and keeps its own copy until it adopts this
    one. Nothing is replaced, so nothing needs parking.

    Returns (allowed, reason, previous).
    """
    previous = read_progress()
    had = count_words(previous.get("data"))
    now = count_words(incoming)

    if had and now == 0:
        return False, "refused: %d words stored, nothing offered" % had, previous
    if had and now < had:
        return False, ("refused: %d words stored, %d offered -- that browser "
                       "is behind" % (had, now)), previous
    return True, None, previous


def keep_superseded(previous):
    """Park the copy a shrinking write is about to replace."""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = DAILY_DIR / ("superseded-%s.json" % stamp)
    path.write_text(json.dumps(previous, indent=1), encoding="utf-8")
    return path


def write_progress(data):
    PROGRESS_DIR.mkdir(exist_ok=True)
    DAILY_DIR.mkdir(exist_ok=True)
    payload = {"savedAt": datetime.datetime.now().isoformat(timespec="seconds"),
               "data": data}
    text = json.dumps(payload, indent=1)

    # Write beside the real file and swap it in, so a crash mid-write
    # cannot leave a truncated backup where a good one used to be.
    tmp = PROGRESS_FILE.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(PROGRESS_FILE)

    # One dated copy a day, so a mistake is recoverable rather than
    # immediately overwritten by the next save.
    day_file = DAILY_DIR / ("progress-%s.json" % datetime.date.today().isoformat())
    day_file.write_text(text, encoding="utf-8")

    old = sorted(DAILY_DIR.glob("progress-*.json"))[:-KEEP_DAILY]
    for f in old:
        try:
            f.unlink()
        except OSError:
            pass
    return payload
DEFAULT_PORT = 8777
NL = chr(10)  # written this way so the banner stays easy to edit

# Only these are served. The spreadsheet, the build scripts and the
# backups sit in the same folder and have no business going over the
# network, so the server refuses anything not named here.
ALLOWED = {
    "/": "vocabulary_practice.html",
    "/index.html": "vocabulary_practice.html",
    "/vocabulary_practice.html": "vocabulary_practice.html",
    "/manifest.webmanifest": "manifest.webmanifest",
    "/sw.js": "sw.js",
    "/icon-192.png": "icon-192.png",
    "/icon-512.png": "icon-512.png",
    "/icon-maskable-512.png": "icon-maskable-512.png",
    "/apple-touch-icon.png": "apple-touch-icon.png",
    "/favicon.ico": "icon-192.png",
}

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

# The word pictures are the one place a name is not known in advance, so
# the name is checked instead of listed: plain characters, one of two
# extensions, and nothing that could climb out of app/images.
IMAGES = FOLDER / "images"
IMAGE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}\.(jpg|jpeg|png)$")


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "WordLog"
    sys_version = ""

    def _resolve(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        name = ALLOWED.get(path)
        if name:
            return FOLDER / name
        if path.startswith("/images/"):
            leaf = path[len("/images/"):]
            if "/" not in leaf and ".." not in leaf and IMAGE_NAME.match(leaf):
                target = (IMAGES / leaf).resolve()
                # resolved, so a link or a clever name cannot point outside
                if str(target).startswith(str(IMAGES.resolve())):
                    return target
        return None

    def _send(self, body, ctype, extra=None):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        return body

    # --- the progress backup ------------------------------------------

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        """Adding a word to the glossary.

        The work is slow by web standards -- it asks Claude and rewrites
        the workbook -- but the server threads requests, so the app stays
        responsive while it happens.
        """
        route = self.path.split("?", 1)[0]
        if route not in (API_GLOSSARY, API_KEY_SET, API_PENDING, API_CHAT,
                         API_SCENARIO, API_EXPLAIN, API_TRANSLATE,
                         API_REVIEW, API_SAY, API_IMAGINE):
            self.send_error(501, "Not supported")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 64 * 1024:
            self._json({"ok": False, "error": "bad length"}, 400)
            return
        try:
            sent = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._json({"ok": False, "error": "bad json"}, 400)
            return

        if route == API_SAY:
            # Audio, not JSON -- the page plays what comes back, and falls
            # back to the browser's own voice if this says no.
            import say
            audio, why = say.say(sent.get("text", ""), sent.get("voice", ""),
                                 sent.get("rate", 0))
            if audio is None:
                self._json({"ok": False, "message": why or "no audio"}, 502)
                return
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(audio)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(audio)
            return

        if route == API_IMAGINE:
            import chat
            result = chat.imagine(sent.get("request", ""), sent.get("words") or [])
            sys.stdout.write("  imagine: %s\n" % result.get("name", result.get("message")))
            sys.stdout.flush()
            self._json(result, 200 if result.get("ok") else 502)
            return

        if route == API_REVIEW:
            import chat
            result = chat.review(sent.get("turns") or [],
                                 sent.get("scenario", ""),
                                 sent.get("words") or [],
                                 sent.get("used") or [])
            self._json(result, 200 if result.get("ok") else 502)
            return

        if route == API_TRANSLATE:
            import chat
            result = chat.translate(sent.get("phrase", ""), sent.get("context", ""))
            self._json(result, 200 if result.get("ok") else 502)
            return

        if route == API_EXPLAIN:
            import chat
            result = chat.explain(sent.get("phrase", ""), sent.get("context", ""))
            self._json(result, 200 if result.get("ok") else 502)
            return

        if route == API_SCENARIO:
            import chat
            result = chat.suggest(sent.get("words") or [])
            sys.stdout.write("  scenario: %s\n" % result.get("name", result.get("message")))
            sys.stdout.flush()
            self._json(result, 200 if result.get("ok") else 502)
            return

        if route == API_CHAT:
            import chat
            result = chat.ask(sent.get("history") or [],
                              sent.get("scenario") or "",
                              sent.get("words") or [],
                              first=bool(sent.get("first")))
            if result.get("ok") and result.get("used"):
                sys.stdout.write("  chat: used %s\n" % ", ".join(result["used"]))
                sys.stdout.flush()
            self._json(result, 200 if result.get("ok") else 502)
            return

        import glossary
        if route == API_KEY_SET:
            # The key itself is never echoed back, logged or stored anywhere
            # but the file it belongs in.
            result = glossary.save_key(sent.get("key", ""))
            sys.stdout.write("  api key: %s\n" % result.get("message"))
            sys.stdout.flush()
            self._json(result, 200 if result.get("ok") else 400)
            return
        if route == API_PENDING:
            result = glossary.fill_pending()
            sys.stdout.write("  pending: %s\n" % result.get("message"))
            sys.stdout.flush()
            self._json(result, 200 if result.get("ok") else 409)
            return

        result = glossary.add(sent.get("word", ""), sent.get("context", ""),
                              sent.get("sheet"))
        note = result.get("message", result)
        if result.get("detail"):
            note = "%s  [%s]" % (note, result["detail"])
        sys.stdout.write("  glossary: %s\n" % note)
        sys.stdout.flush()
        self._json(result, 200 if result.get("ok") else 409)

    def do_PUT(self):
        if self.path.split("?", 1)[0] != API_PROGRESS:
            self.send_error(501, "Not supported")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 16 * 1024 * 1024:
            self._json({"error": "bad length"}, 400)
            return
        try:
            sent = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._json({"error": "bad json"}, 400)
            return
        if not isinstance(sent.get("data"), dict):
            self._json({"error": "no data"}, 400)
            return
        with PROGRESS_LOCK:
            allowed, reason, previous = guard(sent["data"])
            if not allowed:
                # Not an error the app should act on -- it simply keeps its
                # own copy. Saying so out loud makes it visible in the log.
                sys.stdout.write("  backup %s\n" % reason)
                sys.stdout.flush()
                self._json({"savedAt": previous.get("savedAt"),
                            "ignored": True, "reason": reason}, 409)
                return
            # whatever else this write says, it cannot shorten a day
            sent["data"] = keep_study(sent["data"], previous.get("data"))
            if reason:
                kept = keep_superseded(previous)
                sys.stdout.write("  backup %s -> %s\n" % (reason, kept.name))
                sys.stdout.flush()
            saved = write_progress(sent["data"])
        self._json({"savedAt": saved["savedAt"]})

    def do_DELETE(self):
        """Emptying the backup on purpose.

        The guard exists to stop an app that has lost its storage wiping
        the file by accident. Someone choosing Reset progress is not an
        accident, so this way through is deliberate -- and the copy it
        clears is parked first, because "cannot be undone" should still
        leave something to undo it with.
        """
        if self.path.split("?", 1)[0] != API_PROGRESS:
            self.send_error(501, "Not supported")
            return
        with PROGRESS_LOCK:
            previous = read_progress()
            kept = None
            if count_words(previous.get("data")):
                kept = keep_superseded(previous)
                sys.stdout.write("  backup cleared on request -> %s\n" % kept.name)
                sys.stdout.flush()
            saved = write_progress({})
        self._json({"savedAt": saved["savedAt"], "cleared": True,
                    "keptAs": kept.name if kept else None})

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        if self.path.split("?", 1)[0] == API_PROGRESS:
            with PROGRESS_LOCK:
                self._json(read_progress())
            return
        if self.path.split("?", 1)[0] == API_VOICES:
            import say
            self._json(say.voices())
            return
        if self.path.split("?", 1)[0] == API_GLOSSARY:
            # what is waiting, and whether it can be filled in yet
            import glossary
            self._json({"pending": glossary.read_pending(),
                        "hasKey": bool(glossary.api_key())})
            return
        target = self._resolve()
        if target is None:
            self.send_error(404, "Not part of Word Log")
            return
        if not target.exists():
            missing = target.name
            hint = ("Run  python build_word_log.py  first."
                    if missing == "vocabulary_practice.html"
                    else "Run  python make_app_icons.py  to create it.")
            self.send_error(404, "%s is missing. %s" % (missing, hint))
            return

        body = target.read_bytes()
        ctype = TYPES.get(target.suffix, "application/octet-stream")

        # The page and the service worker must never be served stale, or a
        # rebuilt spreadsheet would not reach the phone until the browser
        # felt like checking. The icons can be cached hard; they change
        # only when you regenerate them.
        if target.suffix in (".html", ".js", ".webmanifest"):
            cache = {"Cache-Control": "no-cache, must-revalidate"}
        else:
            cache = {"Cache-Control": "public, max-age=604800"}

        self._send(body, ctype, cache)
        if not head_only:
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        # One tidy line per request instead of the default noise.
        sys.stdout.write("  %s %s\n" % (self.command, self.path))
        sys.stdout.flush()


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    # Deliberately not allow_reuse_address on Windows. There it does not
    # mean "reuse a port in TIME_WAIT", it means "bind a port somebody
    # else already has", and a second copy would quietly steal traffic
    # from the first instead of failing.
    allow_reuse_address = (os.name != "nt")


def already_running(port):
    """True when a Word Log server is already answering on this port.

    The login shortcut fires at every login, and you may well double-click
    the launcher as well, so starting twice has to be handled rather than
    left to chance."""
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("HEAD", "/")
        response = conn.getresponse()
        served_by = response.getheader("Server", "")
        conn.close()
        return served_by.startswith("WordLog")
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Serve Word Log to your own devices.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="local port to listen on (default %d)" % DEFAULT_PORT)
    args = parser.parse_args()

    if not (FOLDER / "vocabulary_practice.html").exists():
        sys.exit("vocabulary_practice.html is not here yet.\n"
                 "Run  python build_word_log.py  first, then start this again.")

    address = "http://localhost:%d" % args.port

    # Starting a second copy would not fail on Windows, it would quietly
    # take the port off the first one, so say so and stop instead.
    if already_running(args.port):
        print("  Word Log is already running." + NL)
        print("      %s" % address + NL)
        print("  Nothing to do -- just open that address." + NL)
        return

    print("  Open this on this laptop:" + NL)
    print("      %s" % address + NL)
    print("  It listens on this machine only, so nothing else can reach it.")
    print("  Leave this window open while you practice. Ctrl+C stops it." + NL)

    # Bound to loopback, so the app cannot be reached from the wifi,
    # from the internet, or from any other device. That is a property
    # of the socket, not a setting somewhere that could drift.
    with Server(("127.0.0.1", args.port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
