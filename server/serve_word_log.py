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
import http.client
import http.server
import json
import os
import socketserver
import subprocess
import sys
from pathlib import Path

# Everything served lives in app/. Nothing outside it is reachable, and
# that includes the spreadsheet, the build scripts and this file.
FOLDER = Path(__file__).resolve().parent.parent / "app"
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

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
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
