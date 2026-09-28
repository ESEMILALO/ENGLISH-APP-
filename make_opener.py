"""
Makes the files that open Word Log.

Run this once (and again only if you change the port):

    python make_opener.py

It writes into this folder:

    Open Word Log.url    a normal Windows shortcut with the app's icon,
                         for pinning to the taskbar or Start
    Open Word Log.html   the same thing as a page, for when you would
                         rather double-click an ordinary file
    wordlog.ico          the icon those two use

The app is served from this laptop and reachable from nowhere else, so
the address never changes and is written in below.
"""

import sys
from pathlib import Path

from PIL import Image

FOLDER = Path(__file__).resolve().parent
APP_URL = "http://localhost:8777/"

INK = "#1B2124"
PANEL = "#232B31"
RULE = "#3A4650"
TEXT = "#E9E6DC"
SOFT = "#96A0A6"
AMBER = "#E39A3A"
AMBER_INK = "#241804"


def write_html(url):
    # Redirects three ways over -- meta refresh, location.replace and a
    # button -- so it still works if any one of them is blocked.
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
  <p class="note">The app is served from this laptop. If it will not load, it is not
  running &mdash; double-click <b>start_word_log.cmd</b>.</p>
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


def main():
    if not (FOLDER / "vocabulary_practice.html").exists():
        sys.exit("vocabulary_practice.html is not here yet.\n"
                 "Run  python build_word_log.py  first.")
    print("Address: %s" % APP_URL)
    icon = write_icon()
    for path in (write_html(APP_URL), write_url_shortcut(APP_URL, icon)):
        print("  wrote %s" % path.name)
    if icon:
        print("  wrote %s" % icon.name)
    print("")
    print('Double-click "Open Word Log" to start practicing.')


if __name__ == "__main__":
    main()
