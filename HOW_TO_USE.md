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
progress/              your progress, backed up as a file
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

## Adding a word you do not know

While practising, select any word on a card. A button appears offering
to add it to your glossary. Tap it and the word is looked up, written
into `ENGLISH SCHOOL.xlsx` in the same style as everything else, and the
app is rebuilt — refresh and you can practice it.

The sentence it came from is sent with it, so the right sense is chosen:
a harness on a dog is not a harness on an engine.

**This needs an Anthropic API key.** Get one from console.anthropic.com
and put it, on one line and nothing else, in:

```
servernthropic_key.txt
```

Then restart the app. Without a key nothing is lost — words are saved in
`progress/pending-words.json` and filled in as soon as a key appears.

You choose which list it joins each time — the five topics are offered,
with the one you picked last at the top, since a run of new words usually
belongs together.

A dated copy of the spreadsheet is kept in `backups/` before every write,
and a word already somewhere in the workbook is refused rather than
duplicated.

## Your progress

It is kept in two places: in this browser, and as a plain file in
`progress/`. The file is written a few seconds after anything you
answer, and you do not have to do anything to make that happen — the
line under the counters says when it last saved.

If this browser ever loses its copy — you clear site data, start a new
profile, move to another browser, or a new laptop — the app reads the
file back on the next start and tells you it did.

It only ever works that way round. The file follows the browser; the
browser is only read back from the file when it has nothing at all, so a
backup can never undo something you just did.

`progress/daily/` keeps one dated copy per day for the last thirty days,
so a bad day is recoverable and not immediately written over. And since
this folder is inside OneDrive, all of it is carried off this machine
without you arranging anything.

Nothing goes anywhere else. The server that writes the file answers this
machine only.

**One thing that does lose progress:** renaming a word in the
spreadsheet. Progress is filed under `category::word`, so a rename looks
like a brand-new word and the old record is orphaned. Reordering rows,
adding words and editing meanings are all safe.

## What the server will hand out

Only what is in `app/`: the page, its icons, its manifest and its
service worker. The spreadsheet, the build scripts, the template and the
backups are all outside that folder and are refused.

The one other thing it answers is your progress backup, at
`/api/progress`. That is the only address it will accept a write on, and
it only ever listens to this machine.

## If you change the port

Run `python tools\make_opener.py` to rewrite the shortcut.
