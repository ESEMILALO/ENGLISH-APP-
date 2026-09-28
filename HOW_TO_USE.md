# Word Log — running it on this laptop

Word Log runs from this laptop and is reachable from nowhere else.

## The address

```
http://localhost:8777
```

`localhost` means this machine and only this machine. The server binds to
the loopback address, so the app cannot be reached from the wifi, from
the internet, or from any other device — that comes from the socket
itself, not from a setting that could drift.

Browsers trust `localhost` the same way they trust `https`, so the
microphone permission is still remembered after you allow it once, and
the app can still be installed with its own icon and window.

## Opening it

Double-click **`Open Word Log`** in this folder. There are two, and
either will do:

- **`Open Word Log.url`** — a normal Windows shortcut with the app's
  icon. Drag it to the taskbar or Start to pin it.
- **`Open Word Log.html`** — the same, as an ordinary page.

If you ever change the port, run `python make_opener.py` to rewrite both.

## Starting the server

It starts on its own at login. You only need this if you stopped it:
double-click **`start_word_log.cmd`**. Leave the window open while you
practice.

To turn the login start-up on or off, run **`install_startup.cmd`**.

## Installing it as an app

Open the address in Chrome or Edge and click the install icon at the
right-hand end of the address bar, or menu → *Cast, save and share* →
*Install page as app*. It gets its own window with no address bar, and
its own icon in the taskbar.

## Your progress

It lives in this browser, on this laptop. Nothing is uploaded anywhere
and nothing leaves the machine.

Because it is stored per address, clearing this browser's site data for
`localhost` clears your progress too.

## Adding words

1. Edit `ENGLISH SCHOOL.xlsx`
2. Run `python build_word_log.py`
3. Refresh the app

The server never hands out a stale page, so the new words are there on
the next load.

## What the server will hand out

The app, its icons, its manifest and its service worker — nothing else.
The spreadsheet, the build scripts, `template.html` and the backups all
sit in the same folder and are refused. It answers GET only.
