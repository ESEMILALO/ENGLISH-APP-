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
import http.server
import json
import socketserver
import subprocess
import sys
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
DEFAULT_PORT = 8777
DEFAULT_HTTPS_PORT = 8443

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
    allow_reuse_address = True


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

    host = tailnet_name()
    if host:
        print("  Open this on your laptop and on your phone:\n")
        print("      https://%s:%d\n" % (host, args.https_port))
        print("  Only your own devices can reach it.")
    else:
        print("  Tailscale is not answering, so only this laptop can reach it:\n")
        print("      http://127.0.0.1:%d\n" % args.port)
        print("  Start Tailscale and run this again for the phone to work.")
    print("  Leave this window open while you practice. Ctrl+C stops it.\n")

    # 127.0.0.1 only. Tailscale reaches it from the inside; nothing else
    # on a cafe wifi can, even for a moment.
    with Server(("127.0.0.1", args.port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
