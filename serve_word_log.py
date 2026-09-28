"""
Word Log server
---------------
Serves the app to your own devices over Tailscale.

WHY THIS EXISTS:
    Opening vocabulary_practice.html as a file works, but a browser will
    not treat a file:// page as trustworthy. It refuses to remember the
    microphone permission, and it refuses to install the page as an app.
    Both of those need a real https:// address.

    Tailscale gives you one. This script serves the folder on your laptop,
    and `tailscale serve` puts a genuine certificate in front of it at
    https://<your-machine>.<your-tailnet>.ts.net -- reachable from your
    phone, and from nothing that is not your device.

HOW TO USE:
    python serve_word_log.py

    Leave it running. Then on the laptop or the phone, open the tailnet
    address that start_word_log.cmd prints.

    Nothing here is exposed to the internet: Tailscale only answers
    devices signed in to your own tailnet.
"""

import argparse
import hmac
import http.client
import http.server
import json
import os
import secrets
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
DEFAULT_PORT = 8777
DEFAULT_HTTPS_PORT = 8443

# Where the shared progress lives, and the passcode that guards it. Both
# stay on this machine; neither belongs in git.
STATE_FILE = FOLDER / "wordlog_state.json"
KEY_FILE = FOLDER / "wordlog_key.txt"

# One writer at a time. Two devices syncing at the same moment would
# otherwise interleave a read and a write and lose one of them.
STATE_LOCK = threading.Lock()


def load_key():
    """The passcode both devices must present. Made once, then reused.

    The app is on the public internet, so without this anyone with the
    address could read the progress or overwrite it. Six words of hex is
    short enough to type on a phone and far too long to guess."""
    if KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key
    key = secrets.token_hex(4)
    KEY_FILE.write_text(key + "\n", encoding="utf-8")
    return key


def read_state():
    if not STATE_FILE.exists():
        return {"rev": 0, "data": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        # A half-written file should not take the sync down for good.
        return {"rev": 0, "data": {}}


def write_state(data, rev):
    payload = {"rev": rev, "data": data}
    # Write beside the real file and swap it in, so a crash mid-write
    # cannot leave a truncated state behind.
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(STATE_FILE)
    return payload

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

# Answered instead of a file, and only with the passcode.
API_STATE = "/api/state"

TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
}


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "WordLog"
    sys_version = ""

    def _resolve(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        name = ALLOWED.get(path)
        return (FOLDER / name) if name else None

    def _send(self, body, ctype, extra=None):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        return body

    # --- the shared progress ------------------------------------------

    def _authorised(self):
        given = self.headers.get("X-Word-Log-Key", "")
        # compare_digest so a wrong key takes the same time as a right one
        return hmac.compare_digest(given, self.server.wordlog_key)

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _handle_state_get(self):
        if not self._authorised():
            self._json({"error": "bad key"}, 403)
            return
        with STATE_LOCK:
            self._json(read_state())

    def _handle_state_put(self):
        if not self._authorised():
            self._json({"error": "bad key"}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 8 * 1024 * 1024:
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
        with STATE_LOCK:
            current = read_state()
            # The client merges before sending, so the newest write wins;
            # rev only exists so a device can tell whether it is behind.
            self._json(write_state(sent["data"], current.get("rev", 0) + 1))

    def do_PUT(self):
        if self.path.split("?", 1)[0] == API_STATE:
            self._handle_state_put()
            return
        self.send_error(501, "Not supported")

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        if self.path.split("?", 1)[0] == API_STATE:
            self._handle_state_get()
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
    wordlog_key = ""
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


TAILSCALE = Path(r"C:\Program Files\Tailscale\tailscale.exe")


def tailnet_name():
    """This machine's name on your tailnet, or None if Tailscale is not
    running. Asking Tailscale beats hard-coding it, since the name follows
    the machine rather than the folder."""
    exe = TAILSCALE if TAILSCALE.exists() else Path("tailscale")
    try:
        out = subprocess.run([str(exe), "status", "--json"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)["Self"]["DNSName"].rstrip(".") or None
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Serve Word Log to your own devices.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="local port to listen on (default %d)" % DEFAULT_PORT)
    parser.add_argument("--https-port", type=int, default=DEFAULT_HTTPS_PORT,
                        help="the port tailscale serve answers on (default %d)"
                             % DEFAULT_HTTPS_PORT)
    args = parser.parse_args()

    if not (FOLDER / "vocabulary_practice.html").exists():
        sys.exit("vocabulary_practice.html is not here yet.\n"
                 "Run  python build_word_log.py  first, then start this again.")

    key = load_key()
    host = tailnet_name()

    # Starting a second copy would not fail on Windows, it would quietly
    # take the port off the first one, so say so and stop instead.
    if already_running(args.port):
        print("  Word Log is already running.\n")
        if host:
            print("      https://%s:%d\n" % (host, args.https_port))
        print("  Nothing to do -- just open that address.\n")
        return

    if host:
        print("  Open this on your laptop and on your phone:\n")
        print("      https://%s:%d\n" % (host, args.https_port))
        print("  This address is public: any device can open it, no VPN needed.")
    else:
        print("  Tailscale is not answering, so only this laptop can reach it:\n")
        print("      http://127.0.0.1:%d\n" % args.port)
        print("  Start Tailscale and run this again for the phone to work.")
    print("  Leave this window open while you practice. Ctrl+C stops it.\n")
    print("  Sync passcode (type it once on each device):  %s" % key)
    print("  It is kept in %s.\n" % KEY_FILE.name)

    # 127.0.0.1 only. Tailscale reaches it from the inside; nothing else
    # on a cafe wifi can, even for a moment.
    with Server(("127.0.0.1", args.port), Handler) as httpd:
        httpd.wordlog_key = key
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
