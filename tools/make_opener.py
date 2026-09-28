"""
Makes the files that open Word Log.

Run this once (and again only if you change the port):

    python make_opener.py

It writes into this folder:

    Open Word Log.url    the shortcut you click to use the app, with
                         the app's own icon; pin it to the taskbar or Start
    app/wordlog.ico      the icon it uses

The app is served from this laptop and reachable from nowhere else, so
the address never changes and is written in below.
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
APP_URL = "http://localhost:8777/"

INK = "#1B2124"
PANEL = "#232B31"
RULE = "#3A4650"
TEXT = "#E9E6DC"
SOFT = "#96A0A6"
AMBER = "#E39A3A"
AMBER_INK = "#241804"


def write_url_shortcut(url, icon):
    # Windows wants an .ico here; a .png is quietly ignored.
    lines = ["[InternetShortcut]", "URL=" + url]
    if icon and icon.exists():
        lines += ["IconFile=" + str(icon), "IconIndex=0"]
    path = ROOT / "Open Word Log.url"
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return path


def write_icon():
    source = APP / "icon-512.png"
    if not source.exists():
        return None
    path = APP / "wordlog.ico"
    img = Image.open(source).convert("RGBA")
    img.save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return path


def main():
    if not (APP / "vocabulary_practice.html").exists():
        sys.exit("vocabulary_practice.html is not here yet.\n"
                 "Run  python build_word_log.py  first.")
    print("Address: %s" % APP_URL)
    icon = write_icon()
    for path in (write_url_shortcut(APP_URL, icon),):
        print("  wrote %s" % path.name)
    if icon:
        print("  wrote %s" % icon.name)
    print("")
    print('Double-click "Open Word Log" to start practicing.')


if __name__ == "__main__":
    main()
