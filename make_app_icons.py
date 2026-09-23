"""
Draws the Word Log app icons.

Run once (and again only if you want to change the look):

    python make_app_icons.py

Android and the desktop both want real PNGs before they will offer to
install a page as an app, and they want two shapes: a plain one, and a
"maskable" one with padding so a launcher can crop it to a circle or a
squircle without cutting into the mark.

The mark is a W drawn as three strokes, in the app's own amber on its
own dark panel colour, so the icon on your home screen matches what
opens when you tap it.
"""

from pathlib import Path

from PIL import Image, ImageDraw

FOLDER = Path(__file__).resolve().parent

# taken straight from :root in template.html, so the icon and the app
# are the same colours
INK = (0x1B, 0x21, 0x24)    # --bg
PANEL = (0x23, 0x2B, 0x31)  # --panel
AMBER = (0xE3, 0x9A, 0x3A)  # --amber
GOOD = (0x5C, 0xAE, 0x7C)   # --good
RULE = (0x3A, 0x46, 0x50)   # --rule


def draw_icon(size, padding_ratio):
    """One icon. padding_ratio is the share of the edge left empty, which
    is what makes a maskable icon safe to crop."""
    scale = 4  # draw big, shrink down: cheap antialiasing
    big = size * scale
    img = Image.new("RGB", (big, big), INK)
    d = ImageDraw.Draw(img)

    pad = int(big * padding_ratio)
    inner = big - 2 * pad

    # rounded panel behind the mark
    radius = int(inner * 0.22)
    d.rounded_rectangle([pad, pad, big - pad, big - pad], radius=radius, fill=PANEL)

    # the W, as four strokes of a zigzag
    w = inner * 0.60
    h = inner * 0.38
    x0 = pad + (inner - w) / 2
    y0 = pad + (inner - h) / 2 - inner * 0.02
    stroke = max(2, int(inner * 0.085))

    points = [
        (x0, y0),
        (x0 + w * 0.25, y0 + h),
        (x0 + w * 0.50, y0 + h * 0.34),
        (x0 + w * 0.75, y0 + h),
        (x0 + w, y0),
    ]
    d.line(points, fill=AMBER, width=stroke, joint="curve")
    # round the ends off by hand -- PIL's line does not do caps
    for px, py in (points[0], points[-1]):
        r = stroke / 2
        d.ellipse([px - r, py - r, px + r, py + r], fill=AMBER)

    # a small progress underline, the one thing the app is always showing
    bar_w = w * 0.62
    bar_x = pad + (inner - bar_w) / 2
    bar_y = y0 + h + inner * 0.13
    bar_h = max(2, int(inner * 0.045))
    d.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                        radius=bar_h / 2, fill=RULE)
    d.rounded_rectangle([bar_x, bar_y, bar_x + bar_w * 0.58, bar_y + bar_h],
                        radius=bar_h / 2, fill=GOOD)

    return img.resize((size, size), Image.LANCZOS)


def main():
    jobs = [
        ("icon-192.png", 192, 0.06),
        ("icon-512.png", 512, 0.06),
        # maskable needs the mark inside the middle 80%, so the launcher
        # can crop to any shape without clipping it
        ("icon-maskable-512.png", 512, 0.14),
        ("apple-touch-icon.png", 180, 0.06),
    ]
    for name, size, pad in jobs:
        img = draw_icon(size, pad)
        img.save(FOLDER / name, "PNG", optimize=True)
        print("wrote %-24s %dx%d" % (name, size, size))
    print("\nDone. Restart the server if it is running.")


if __name__ == "__main__":
    main()
