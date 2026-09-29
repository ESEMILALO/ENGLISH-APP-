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

**This needs an Anthropic API key**, which you paste into the app once:

1. console.anthropic.com → **API Keys** → *Create Key*, and copy it.
2. In Word Log, open **Everything else** at the bottom of the home
   screen. There is a line there saying the lookup needs a key, with a
   box next to it.
3. Paste, press **Save**.

The key is checked against the API before it is saved, so a typo is
caught immediately rather than the next time a word quietly fails to be
added. It is written to `server/anthropic_key.txt` on this laptop, never
committed, and sent nowhere except to Anthropic. Nothing needs
restarting.

Keys do not expire — it keeps working until you delete it in the console.

Without a key nothing is lost: words wait in
`progress/pending-words.json`, the app says how many are waiting, and
once a key is in there is a button to fill them all in at once.

You choose which list it joins each time — the five topics are offered,
with the one you picked last at the top, since a run of new words usually
belongs together.

A dated copy of the spreadsheet is kept in `backups/` before every write,
and a word already somewhere in the workbook is refused rather than
duplicated.

## Using the words for real

Once the day's ten are all finished, a button appears: **use today's
words in a conversation**. Pick a situation — a shop, an interview, a
flat viewing, the doctor, an old friend — and someone plays that part
while you talk to them.

There is a sixth option above the fixed ones: **made for today's
words**. It asks for a situation those particular ten would really come
up in, rather than one off a list, and you can ask for another if you do
not like it.

**If you do not understand something, select it and ask.** A button
appears: *what does this mean?* The answer arrives underneath, in plain
English with the Spanish and a note on when people say it. It works on
whole phrases, which is usually what trips you up — "what brings you in
today" is not hard word by word.

If what you selected is a single word, you also get the *add to your
glossary* button, so it can go into your spreadsheet like any other.

Both work on practice cards too, not only in the conversation.

Your ten words sit along the top and turn green as you use them. Only
what **you** write counts: the partner is told not to use them itself,
so each one has to come from you. A word you wrote exactly as it stands
on the list always counts, whether or not the partner noticed it. Recognising a word is easy; producing
one in the middle of a conversation is the thing worth practising.

It also corrects you, briefly and in character, when you make a real
mistake — a conversation that lets everything past is pleasant and
useless.

**You can speak instead of typing.** Tap the microphone, say your reply,
and it goes in as your message — no need to press send afterwards. It
reads its own replies out loud too; *voice on* in the corner turns that
off if you would rather read.

**Or talk to it and nothing else.** *talk only*, next to the voice
switch, puts away the transcript and the typing box and leaves one
circle. It listens, you speak, it answers out loud, and the moment it
stops talking it is listening again — you never touch the screen. The
circle tells you whose turn it is: orange while it listens to you, green
while it is talking, and a tap on it interrupts and gives you the turn
back. *Show the conversation* brings the written version back with every
word that was said still there, so you can read over it afterwards.

Nothing is written on screen while you talk, which is the point: it is
the closest this gets to a person in front of you.

**Conversations are kept, and they are yours.** Close the tab
mid-sentence and the next time you open the conversation screen it
offers to carry on where you stopped, with the words you had already
used still ticked.

Every conversation you have had is listed underneath. Open one to read
it back, and **carry on with this one** picks the thread up again — the
partner still has everything that was said. Whatever was open at the
time is filed away rather than dropped, so starting or resuming one
never costs you another.

The **×** beside each one deletes it. It asks first, and the ask is in
the page rather than a browser popup, so nothing goes on a mis-tap.

The last twenty are saved to the same file as your progress, so losing
the browser does not lose them.

Time spent talking counts toward the day's hour.

This uses the same Anthropic key as adding words.

## Earning the day's words

Ten new words are not handed over just because the date changed. They
are earned: study **one hour** today and tomorrow brings ten more. Fall
short and you keep the words you have, which is what you would want
anyway — ten words you have not learnt are not helped by ten more
landing on top of them.

A bar under today's words shows how far along you are.

The time is measured honestly. It counts only while a card is on screen,
the window is focused, and you have touched something in the last two
minutes: a card left open while you make dinner is not study.

To change the hour, set `DAILY_GOAL_MIN` near the top of the study
section in `tools/template.html` and rebuild. The sentences around it
follow the number.

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
