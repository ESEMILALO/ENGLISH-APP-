# Word Log — running it as an app

Word Log now runs from your own laptop and installs as a real app on
your phone and your desktop. Tailscale carries it between them, and
nobody else can reach it.

## The address

```
https://eduardo-cruz.tail16a220.ts.net:8443
```

Only devices signed in to your tailnet get an answer. It is not on the
public internet.

## Starting it

Double-click **`start_word_log.cmd`**. It prints the address and then
serves the app. Leave the window open while you practice.

To have it start on its own every time you log in, run
**`install_startup.cmd`** once. Run it again to undo that.

## Installing it as an app

Your phone needs the Tailscale app installed and signed in to the same
account — that is what lets it reach the laptop.

**Android (Chrome):** open the address, then menu ⋮ → *Add to Home
screen* → *Install*. It gets its own icon and opens without an address
bar.

**iPhone (Safari):** open the address, then Share → *Add to Home
Screen*.

**Desktop (Chrome or Edge):** open the address and click the install
icon at the right-hand end of the address bar, or menu → *Cast, save
and share* → *Install page as app*.

## Adding words

Nothing has changed here:

1. Edit `ENGLISH SCHOOL.xlsx`
2. Run `python build_word_log.py`
3. Refresh the app on the phone

No commit, no push, no waiting. The server never serves a stale page.

## When the laptop is off

The app still opens on your phone with every word in it — it keeps a
copy of itself. Your progress was always stored on the device you are
holding, so that keeps working too. You only need the laptop awake to
pick up words you have just added.

## What it can reach

The server hands out the app and its icons and nothing else. The
spreadsheet, the build scripts and the backups sit in the same folder
and are refused — `ENGLISH SCHOOL.xlsx`, `template.html` and
`build_word_log.py` all return 404 by design.

## Turning it off

```
tailscale serve --https=8443 off
```

That removes the address. `install_startup.cmd` removes the login entry.
Neither touches your words or your progress.

## A separate thing worth knowing

`tailscale serve status` also shows a **Funnel** on port 443 pointing at
`http://127.0.0.1:3210` — the old SPEECH prototype. Funnel means the
public internet, not just your devices. Word Log is not part of it and
was deliberately put on port 8443 instead, which is tailnet-only.

To take that old one down:

```
tailscale funnel --https=443 off
```
