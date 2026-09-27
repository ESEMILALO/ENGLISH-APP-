"""
Makes the files that open Word Log.

Run this once (and again only if your Tailscale machine name ever
changes):

    python make_opener.py

It writes three things into this folder:

    Open Word Log.html   double-click it on the laptop, or open it from
                         the OneDrive app on your phone -- either way it
                         goes straight to the app
    Open Word Log.url    a normal Windows shortcut with the app's icon,
                         for pinning to the taskbar or Start
    phone-qr.png         point your phone's camera at it to get the
                         address across without typing

The address is not written down here. It is asked of Tailscale, so these
files stay correct if the machine is ever renamed.
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    import segno
except ImportError:
    sys.exit("Missing dependency. Run this first:\n\n    pip install segno\n")

from PIL import Image

FOLDER = Path(__file__).resolve().parent
TAILSCALE = Path(r"C:\Program Files\Tailscale\tailscale.exe")
HTTPS_PORT = 8443

INK = "#1B2124"
PANEL = "#232B31"
RULE = "#3A4650"
TEXT = "#E9E6DC"
SOFT = "#96A0A6"
AMBER = "#E39A3A"
AMBER_INK = "#241804"


def tailnet_url():
    exe = TAILSCALE if TAILSCALE.exists() else Path("tailscale")
    try:
        out = subprocess.run([str(exe), "status", "--json"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return None
        host = json.loads(out.stdout)["Self"]["DNSName"].rstrip(".")
        return "https://%s:%d/" % (host, HTTPS_PORT) if host else None
    except Exception:
        return None


def write_html(url):
    # Redirects on its own, three ways over, because this one file has to
    # work when double-clicked from the desktop and when tapped inside the
    # OneDrive app on a phone. If every one of them is blocked, the button
    # is still there to press.
    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Opening Word Log&hellip;</title>
<meta http-equiv="refresh" content="0; url=URL_HERE">
<style>
  html,body{ margin:0; height:100%%; background:%(ink)s; color:%(text)s;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
  .wrap{ min-height:100%%; display:flex; flex-direction:column; align-items:center;
    justify-content:center; gap:18px; padding:32px 20px; text-align:center; box-sizing:border-box; }
  h1{ font-size:1.3rem; font-weight:700; margin:0; letter-spacing:-.01em; }
  p{ margin:0; color:%(soft)s; font-size:.9rem; line-height:1.5; max-width:30rem; }
  a.go{ display:inline-block; background:%(amber)s; color:%(amber_ink)s; text-decoration:none;
    font-weight:700; font-size:1rem; padding:15px 28px; border-radius:10px; }
  a.go:hover{ filter:brightness(1.08); }
  code{ font-family:ui-monospace,Menlo,Consolas,monospace; font-size:.8rem; color:%(soft)s;
    background:%(panel)s; border:1px solid %(rule)s; border-radius:7px; padding:8px 12px;
    display:inline-block; word-break:break-all; max-width:100%%; box-sizing:border-box; }
  .note{ font-size:.8rem; color:%(soft)s; border-top:1px solid %(rule)s; padding-top:16px; margin-top:6px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Opening Word Log&hellip;</h1>
  <a class="go" href="URL_HERE">Open Word Log</a>
  <p>If nothing happened, tap the button.</p>
  <code>URL_HERE</code>
  <p class="note">Only your own devices can reach this address. If it will not load,
  your phone may not be signed in to Tailscale, or the laptop may not be running
  <b>start_word_log.cmd</b>.</p>
</div>
<script>
  // Replace rather than assign, so the back button does not bounce you
  // straight back to this page.
  location.replace("URL_HERE");
</script>
</body>
</html>
""" % {"ink": INK, "panel": PANEL, "rule": RULE, "text": TEXT,
       "soft": SOFT, "amber": AMBER, "amber_ink": AMBER_INK}

    page = page.replace("URL_HERE", url)
    path = FOLDER / "Open Word Log.html"
    path.write_text(page, encoding="utf-8")
    return path


def write_url_shortcut(url, icon):
    # Windows wants an .ico here; a .png is quietly ignored.
    lines = ["[InternetShortcut]", "URL=" + url]
    if icon and icon.exists():
        lines += ["IconFile=" + str(icon), "IconIndex=0"]
    path = FOLDER / "Open Word Log.url"
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return path


def write_icon():
    source = FOLDER / "icon-512.png"
    if not source.exists():
        return None
    path = FOLDER / "wordlog.ico"
    img = Image.open(source).convert("RGBA")
    img.save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return path


def write_qr(url):
    path = FOLDER / "phone-qr.png"
    qr = segno.make(url, error="m")
    # dark modules in the app's amber on its own background, with a wide
    # quiet zone so a phone camera locks on quickly
    qr.save(str(path), scale=10, border=4, dark=AMBER, light=INK)
    return path


def main():
    url = tailnet_url()
    if not url:
        sys.exit("Tailscale is not answering, so I cannot tell what this machine's\n"
                 "address is. Start Tailscale, then run this again.")

    print("Address: %s\n" % url)
    icon = write_icon()
    for path in (write_html(url), write_url_shortcut(url, icon), write_qr(url)):
        print("  wrote %s" % path.name)
    if icon:
        print("  wrote %s" % icon.name)

    print("\nDouble-click \"Open Word Log\" to start practicing.")
    print("Scan phone-qr.png with your phone to get the address across.")


if __name__ == "__main__":
    main()
