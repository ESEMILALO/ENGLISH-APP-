# Word Log

Your English vocabulary, tracked as you learn it. It runs on this laptop
and is reachable from nowhere else.

## Day to day

**To practice** — double-click **`Open Word Log`**. That is the only
thing you need.

**To add or change words** — edit `ENGLISH SCHOOL.xlsx`, save it, then
double-click **`Update words`**. Refresh the app and they are there.

Everything else in this folder runs itself.

## What is in the folder

```
Open Word Log.url      click this to use the app
Update words.cmd       click this after editing the spreadsheet
ENGLISH SCHOOL.xlsx    your words
HOW_TO_USE.md          this file

app/                   the app itself, and the only folder the
                       server will hand anything out of
tools/                 the template and the scripts that build the
                       app from the spreadsheet
server/                the little web server and its launchers
backups/               dated copies of the spreadsheet
```

## The address

```
http://localhost:8777
```

`localhost` means this machine and nothing else. The server binds to the
loopback address, so the app cannot be reached from the wifi, from the
internet, or from any other device — that comes from the socket itself,
not from a setting that could drift.

Browsers trust `localhost` the same way they trust `https`, so the
microphone permission is remembered after you allow it once, and the app
can be installed with its own icon and window.

## Installing it as an app

Open the address in Chrome or Edge and click the install icon at the
right-hand end of the address bar, or menu → *Cast, save and share* →
*Install page as app*. You get a window with no address bar and an icon
in the taskbar.

## The server

It starts on its own at login, so the app is always ready. You only need
to touch it if you have stopped it: double-click
**`server\start_word_log.cmd`** and leave the window open.

To turn the login start-up on or off, run **`server\install_startup.cmd`**.

## Your progress

It lives in this browser, on this laptop. Nothing is uploaded anywhere.
Because browsers store it per address, clearing site data for
`localhost` clears your progress with it.

## What the server will hand out

Only what is in `app/`: the page, its icons, its manifest and its
service worker. The spreadsheet, the build scripts, the template and the
backups are all outside that folder and are refused. It answers GET
requests only.

## If you change the port

Run `python tools\make_opener.py` to rewrite the shortcut.
