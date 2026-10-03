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

## The key, and why it costs nothing

Four things in the app ask a model a question: the conversation, the
translation that appears when you select something, **Explain it**, and
the feedback at the end of a conversation. Adding a word does too.

**The free one is Google's.** Go to **aistudio.google.com/apikey**, sign
in with a Google account, press *Create API key*, and copy it. There is
no card and no payment. The free allowance is about fifteen hundred
requests a day, and a long day of studying uses a few dozen.

Paste it into the box under *Everything else* on the home screen, or put
it straight in `server\gemini_key.txt`. It is checked before it is
saved.

An Anthropic key still works and goes in `server\anthropic_key.txt`. If
both are there the Google one is used, because that is the one that is
free.

With no key at all, everything that does not need one carries on exactly
as before: the cards, the recall check, your progress, the pictures
already fetched, and the voice.

## What it needs installed

    pip install openpyxl edge-tts

`openpyxl` reads the spreadsheet. `edge-tts` is what fetches the neural
voices; without it the app falls back to the browser's own voices and
everything else works exactly the same.

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

**Say "imagine we are..." and the conversation goes there.** At any
point, typed or out loud: *"imagine we are at the airport and the
airline has lost my bag"*. The situation you asked for is the one you
get -- it fills in only what you left out, who the other person is and
what they want, and it does not quietly redirect you towards the day's
words. A line appears in the conversation saying where you now are, the
partner starts again as somebody new, and everything said before stays
on the page as a record without the new person having read it.

It needs three words after "imagine" to count, so "imagine that" on its
own is just something you said.

**Selecting something now shows the Spanish straight away.** Highlight a
word or a phrase, anywhere on a card or in the conversation, and the
translation appears above it before you press anything. If the word is
one of your own, the Spanish comes out of your spreadsheet instantly and
nothing is asked of anybody; otherwise Claude translates it, using the
sentence around it, so you get the sense it has *there* rather than the
first one in a dictionary. Idioms come back as the Spanish people
actually say: "hate someone's guts" gives *odiar a alguien a muerte*,
not a word-for-word version.

The two buttons are still underneath. **Explain it** gives the longer
answer -- what it means, when people say it, why it is worded that way --
and **+ Add** puts a word into your spreadsheet. Most of the time the
translation alone is what you wanted, which is why it no longer takes a
click to see it.

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

**It waits while you think.** A pause of up to four seconds is not the
end of your turn, and the browser stopping to listen part-way through
does not end it either -- it starts again underneath while your clock
keeps running. Stop mid-sentence to find a word and it will still be
there when you carry on. Fifteen seconds of complete silence before you
have said anything hands the turn back, and a single turn can run a
minute and a half.

**A mistake is shown beside the circle.** If you say something the
partner would fix, it appears next to the microphone under *say it like
this* -- your words and the way to say them -- and takes itself away
after nine seconds. It is there long enough to read and not long enough
to become something you ignore.

**When you did not catch it, three buttons are under the circle.**
*What did it say?* shows the last thing it said, written out, without
leaving the mode. *Say it again* repeats it out loud and then goes back
to listening. And on the line it shows, *What does it mean?* explains
the whole sentence in English and in Spanish — the whole sentence,
because when you miss something by ear you do not yet know which word
lost you.

What you asked to see stays until the next thing is said, and then the
screen is bare again.

**The voice can be changed.** Under *Everything else* on the home screen
there is a **Voice** picker with a *Hear it* button, and it now has two
groups in it.

The **neural** ones -- Ava, Andrew, Emma, Brian, and two British voices --
do not come from the browser at all. The app server fetches them, and
they are a different thing to listen to: not a better robot, a person.
One of them is what you get unless you choose otherwise. The first time
a sentence is said it takes about a second to arrive; every time after
that it is instant, because each clip is kept in `server/voice-cache`.

Under them are the voices your browser offers, which is what the app used
before.

If the neural voice cannot be reached -- offline, the package missing,
anything at all -- the browser voice finishes the sentence instead. That
includes the awkward case where a clip arrives but never starts playing:
after four seconds of nothing the app stops waiting and says it the old
way, because a conversation you are holding by ear must never just go
quiet.

The same voice reads words, examples and the conversation. Single words
are read a little slower than sentences, because a word is worth hearing
carefully and a sentence read that slowly stops sounding like someone
talking to you.

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

### How it went

Every conversation is read back when you end it, without being asked
for. A partner staying in character cannot stop to mark every slip
without wrecking the conversation, so it is done afterwards, over the
whole thing at once:

- two sentences on how it went, spoken to you directly
- where this conversation sits, like *"basic, struggling to move past
  fixed short phrases"*
- **say these differently** -- your own words struck through, the right
  version under them, and the habit behind the mistake. *"I no can walk
  good"* comes back as *"I can't walk well"*, with the reason: Spanish
  *no puedo* word order carried over
- what you genuinely did well, quoted, or nothing if there was nothing
- one thing to work on next time. One, concrete enough to actually do

It is kept with the conversation, so opening an old one shows the same
feedback again without asking for it twice. Conversations from before
this existed have a **How did I do?** button instead.

Time spent talking counts toward the day's hour.

This uses the same Anthropic key as adding words.

## Adding a book of words at once

Photograph or screenshot the pages, put them in one folder, and:

    python tools\read_book.py "C:\Users\Eduar\OneDrive\Pictures\libro"
    python tools\add_book_words.py --sheet "School vocabulary"
    python tools\build_word_log.py

The first reads the pages and writes what it finds to
`tools\book_verbs.json` -- the word, the meaning and the example, exactly
as the book prints them. It trims the black bars off a phone screenshot
by itself, ignores covers and contents pages, and remembers which pages
it has read, so stopping it and running it again carries on rather than
starting the book over.

The second turns those into rows in your sheet: the Spanish, a
pronunciation you can say, and the verb's forms in the notes, in the same
style as every other row. **The book's own meaning and example are kept**
-- it is dressing them for the sheet, not inventing better ones.

Anything already in your workbook is left where it is and reported, so a
book that overlaps the lists you already have does not fill the sheet
with second copies. Add `--dry-run` to see what it would write without
writing it, and `--limit 10` to try a few first. A copy of the workbook
goes into `backups\` before anything is added.

## Pictures

Under the meaning, some words carry a photograph. Not all of them, and
that is deliberate.

Searching an image library for the word itself does not work: "recline"
brings back a reclining Buddha, "supper" brings back the Leonardo,
"essential" brings back a face scrub. So the meaning you already have
does the choosing. Claude turns the word, its meaning and its example
into a short, concrete search term, Wikimedia Commons is searched with
it, and then Claude is shown the pictures that came back and asked which
one, if any, would teach the right thing to somebody who did not know
the word.

Most of the time the answer is none, and then the word simply has no
picture. "Brief" was refused with "no image shows short duration";
"behave" with "needs caption text to convey meaning". A wrong picture is
worse than no picture, so nothing is shown rather than something close.
Abstract words, linking words and most phrasal verbs end up with none.
Concrete ones -- *finch*, *binder*, *hailstones*, *hatching* -- come out
well.

They are photographs only. An old engraving of a severe-looking man fits
"stern" perfectly and is still not what you want to learn from, so
artwork is turned away twice: once in the search and again by the judge.

The small grey line under a picture is who took it and the licence it is
shared under, which is what those licences ask for in return.

### Getting them, or getting them again

    python tools\word_images.py

It works through every word that does not have a picture yet, and keeps
what it finds in `tools\word_images.json` with the files in
`app\images\`. It is deliberately unhurried -- Commons is free and asks
to be treated gently -- so the whole spreadsheet takes a few hours. Stop
it whenever you like with Ctrl-C and run it again later; it picks up
where it stopped and never fetches the same word twice.

If one picture is wrong, ask for another:

    python tools\word_images.py --redo Lawsuit

It remembers the one you rejected and will not offer it again. Run
`python tools\build_word_log.py` afterwards to put the changes in the
app.

## The check at the door

When you open the app it asks you about words you have already mastered,
before it lets you at anything new. Type the word and press **Enter**;
the answer appears, and **Enter** again moves to the next one. The whole
run is keyboard-only -- you never have to reach for the mouse in the
middle of it.

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

Only what is in `app/`: the page, its icons, its manifest, its service
worker and the word pictures in `app/images/`. The spreadsheet, the
build scripts, the template and the backups are all outside that folder
and are refused.

The pictures are the one thing whose names are not known in advance, so
they are checked rather than listed: an ordinary file name ending in
.jpg or .png, and the finished path has to still be inside
`app/images/`. A name that tries to climb out of it gets the same 404 as
anything else.

The one other thing it answers is your progress backup, at
`/api/progress`. That is the only address it will accept a write on, and
it only ever listens to this machine.

## If you change the port

Run `python tools\make_opener.py` to rewrite the shortcut.
