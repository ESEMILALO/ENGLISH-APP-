# -*- coding: utf-8 -*-
"""The 55 the API never got to, written by hand in the sheet's own style.

Pronunciation follows the conventions already in the workbook: "th" is
"z" when it is voiceless (through -> zru) and "d" when it is voiced
(that -> dat), "w" is "u" (with -> uith), and the stress carries a
Spanish accent. The meaning and the example are the book's own.
"""

import datetime
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Eduar\OneDrive\Desktop\ENGLISH")
sys.path.insert(0, str(ROOT / "server"))
import glossary  # noqa: E402

SHEET = "School vocabulary"

R = "Regular verb. Base: %s \u2014 Present: %s \u2014 Past: %s \u2014 Past participle: %s."
I = "Irregular verb. Base: %s \u2014 Present: %s \u2014 Past: %s \u2014 Past participle: %s."

ROWS = [
    ("Pitch in", "pich ín", "Help with a shared task \u2014 Echar una mano.",
     "Everyone pitched in to clean the house.",
     R % ("pitch in", "pitches in", "pitched in", "pitched in")
     + " Intransitive; not separable."),
    ("Cheer up", "chír ap", "Become happier \u2014 Animarse.",
     "Emma cheered up after hearing the good news.",
     R % ("cheer up", "cheers up", "cheered up", "cheered up")
     + " Separable: cheer someone up."),
    ("Calm down", "cálm daun", "Become less upset or angry \u2014 Calmarse.",
     "Tom calmed down after a few minutes.",
     R % ("calm down", "calms down", "calmed down", "calmed down")
     + " Separable: calm someone down."),
    ("Brighten up", "bráiten ap", "Become happier or more cheerful \u2014 Alegrarse.",
     "Sarah brightened up when she saw her friends.",
     R % ("brighten up", "brightens up", "brightened up", "brightened up")
     + " Also used of weather and of rooms."),
    ("Open up", "óupen ap", "Share your feelings with someone \u2014 Abrirse.",
     "Jack opened up to his best friend.",
     R % ("open up", "opens up", "opened up", "opened up")
     + " Intransitive in this sense: open up to someone."),
    ("Bottle up", "bótel ap", "Keep your feelings inside \u2014 Reprimir los sentimientos.",
     "Emma bottled up her emotions.",
     R % ("bottle up", "bottles up", "bottled up", "bottled up")
     + " Separable: bottle something up."),
    ("Break down", "bréik daun", "Lose control of your emotions \u2014 Derrumbarse.",
     "Sarah broke down in tears.",
     I % ("break down", "breaks down", "broke down", "broken down")
     + " Intransitive in this sense; of a machine it means to stop working."),
    ("Hold back", "jóuld bak", "Stop yourself from showing emotion \u2014 Contener.",
     "Jack held back his tears.",
     I % ("hold back", "holds back", "held back", "held back")
     + " Separable: hold something back."),
    ("Bring down", "bring dáun", "Make someone feel sad \u2014 Desanimar.",
     "The bad news brought him down.",
     I % ("bring down", "brings down", "brought down", "brought down")
     + " Separable: bring someone down."),
    ("Fall apart", "fol apárt", "Become emotionally upset \u2014 Desmoronarse.",
     "Jack fell apart after the loss.",
     I % ("fall apart", "falls apart", "fell apart", "fallen apart")
     + " Intransitive; also used of things that break into pieces."),
    ("Feel up to", "fíl ap tu", "Feel able to do something \u2014 Sentirse capaz de.",
     "Tom didn't feel up to going out.",
     I % ("feel up to", "feels up to", "felt up to", "felt up to")
     + " Not separable. Followed by a noun or by -ing."),
    ("Wear down", "uér daun", "Make someone tired or stressed \u2014 Desgastar.",
     "The long week wore him down.",
     I % ("wear down", "wears down", "wore down", "worn down")
     + " Separable: wear someone down."),
    ("Ease up", "ís ap", "Become less worried or tense \u2014 Relajarse.",
     "Sarah eased up after the test.",
     R % ("ease up", "eases up", "eased up", "eased up")
     + " Intransitive. Also said of rain or pressure letting up."),
    ("Snap out of", "snáp aut of", "Stop feeling sad or worried \u2014 Salir de un estado de \u00e1nimo.",
     "Emma snapped out of her bad mood.",
     R % ("snap out of", "snaps out of", "snapped out of", "snapped out of")
     + " Not separable. Often an imperative: snap out of it."),
    ("Lighten up", "láiten ap", "Become less serious or worried \u2014 Tom\u00e1rselo con calma.",
     "Jack lightened up after hearing the joke.",
     R % ("lighten up", "lightens up", "lightened up", "lightened up")
     + " Intransitive, and usually said as an instruction."),
    ("Warm up to", "u\u00f3rm ap tu", "Gradually start liking someone \u2014 Agarrar confianza con.",
     "Sarah warmed up to her new neighbor.",
     R % ("warm up to", "warms up to", "warmed up to", "warmed up to")
     + " Not separable."),
    ("Lean on", "lín on", "Depend on someone for support \u2014 Apoyarse en.",
     "Emma leaned on her sister.",
     R % ("lean on", "leans on", "leaned on", "leaned on")
     + " Not separable. British English also uses leant."),
    ("Well up", "u\u00e9l ap", "Fill with tears or strong emotion \u2014 Llenarse de l\u00e1grimas.",
     "Tears welled up in her eyes.",
     R % ("well up", "wells up", "welled up", "welled up")
     + " Intransitive. The subject is usually tears or a feeling."),
    ("Come around", "kam ar\u00e1und", "Change your opinion or attitude \u2014 Cambiar de opini\u00f3n.",
     "Tom came around after talking to her.",
     I % ("come around", "comes around", "came around", "come around")
     + " Intransitive. Also means to regain consciousness."),
    ("Dwell on", "du\u00e9l on", "Keep thinking about something upsetting \u2014 Darle vueltas a.",
     "Emma dwelled on her mistake.",
     R % ("dwell on", "dwells on", "dwelled on", "dwelled on")
     + " Not separable. British English also uses dwelt."),
    ("Shake off", "sh\u00e9ik of", "Stop feeling something unpleasant \u2014 Quitarse de encima.",
     "Tom shook off his worries.",
     I % ("shake off", "shakes off", "shook off", "shaken off")
     + " Separable: shake something off."),
    ("Hang on to", "j\u00e1ng on tu", "Keep a feeling or a memory \u2014 Aferrarse a.",
     "Emma hung on to her childhood memories.",
     I % ("hang on to", "hangs on to", "hung on to", "hung on to")
     + " Not separable."),
    ("Sink in", "sínk in", "Be fully understood \u2014 Asimilarse.",
     "The news finally sank in.",
     I % ("sink in", "sinks in", "sank in", "sunk in")
     + " Intransitive. The subject is the news or the fact, not the person."),
    ("Live through", "lív zru", "Experience something difficult \u2014 Vivir algo dif\u00edcil.",
     "Tom lived through a stressful year.",
     R % ("live through", "lives through", "lived through", "lived through")
     + " Not separable."),
    ("Look down on", "lúk daun on", "Think you are better than someone \u2014 Menospreciar.",
     "Jack looked down on his classmates.",
     R % ("look down on", "looks down on", "looked down on", "looked down on")
     + " Not separable."),
    ("Beat yourself up", "bít yors\u00e9lf ap", "Criticise yourself too much \u2014 Culparse demasiado.",
     "Emma beat herself up over the mistake.",
     I % ("beat yourself up", "beats himself up", "beat herself up", "beaten yourself up")
     + " The middle word changes with the person: beat myself up, beat himself up."),
    ("Miss out on", "mís aut on", "Lose the chance to experience something \u2014 Perderse algo.",
     "Tom missed out on the trip.",
     R % ("miss out on", "misses out on", "missed out on", "missed out on")
     + " Not separable."),
    ("Break into", "bréik íntu", "Suddenly show an emotion \u2014 Echarse a.",
     "Emma broke into laughter.",
     I % ("break into", "breaks into", "broke into", "broken into")
     + " Not separable. Also means to enter a building by force."),
    ("Get carried away", "gu\u00e9t k\u00e1rid au\u00e9i", "Become too excited or emotional \u2014 Dejarse llevar.",
     "Tom got carried away during the celebration.",
     I % ("get carried away", "gets carried away", "got carried away", "gotten carried away")
     + " A fixed expression; the three words stay together."),
    ("Bottle out", "bótel áut", "Lose courage and back out \u2014 Echarse atr\u00e1s.",
     "Jack bottled out of giving the speech.",
     R % ("bottle out", "bottles out", "bottled out", "bottled out")
     + " Intransitive. British and informal."),
    ("Fight back", "fáit bak", "Stop yourself from showing emotion \u2014 Contener.",
     "Sarah fought back her tears.",
     I % ("fight back", "fights back", "fought back", "fought back")
     + " Separable in this sense. On its own it means to defend yourself."),
    ("Clam up", "klám ap", "Suddenly stop talking \u2014 Quedarse callado.",
     "Tom clammed up during the interview.",
     R % ("clam up", "clams up", "clammed up", "clammed up")
     + " Intransitive and informal."),
    ("Bring about", "bring ab\u00e1ut", "Cause something to happen \u2014 Provocar.",
     "The new rule brought about positive changes.",
     I % ("bring about", "brings about", "brought about", "brought about")
     + " Separable, though the object usually follows the whole verb."),
    ("Carry out", "k\u00e1ri áut", "Complete a task or a plan \u2014 Llevar a cabo.",
     "The students carried out the project successfully.",
     R % ("carry out", "carries out", "carried out", "carried out")
     + " Separable: carry it out."),
    ("Come up with", "kam ap uith", "Think of an idea or a solution \u2014 Ocurr\u00edrsele a uno.",
     "Sarah came up with a clever idea.",
     I % ("come up with", "comes up with", "came up with", "come up with")
     + " Not separable; all three words stay together."),
    ("Turn out", "tern áut", "Happen or develop in a particular way \u2014 Resultar.",
     "The party turned out great.",
     R % ("turn out", "turns out", "turned out", "turned out")
     + " Intransitive in this sense. Often: it turned out that..."),
    ("Get away with", "gu\u00e9t au\u00e9i uith", "Avoid punishment for something \u2014 Salirse con la suya.",
     "Jack got away with breaking the rules.",
     I % ("get away with", "gets away with", "got away with", "gotten away with")
     + " Not separable."),
    ("Put up with", "pút ap uith", "Tolerate something unpleasant \u2014 Aguantar.",
     "Sarah put up with the loud noise.",
     I % ("put up with", "puts up with", "put up with", "put up with")
     + " Not separable. The past looks the same as the base."),
    ("Back out", "bák áut", "Withdraw from an agreement or a plan \u2014 Echarse atr\u00e1s.",
     "Jack backed out of the deal.",
     R % ("back out", "backs out", "backed out", "backed out")
     + " Intransitive: back out of something."),
    ("Come up against", "kam ap agu\u00e9nst", "Face a difficulty \u2014 Toparse con.",
     "The team came up against many problems.",
     I % ("come up against", "comes up against", "came up against", "come up against")
     + " Not separable."),
    ("Drop out", "dr\u00e1p áut", "Leave a course before finishing \u2014 Abandonar los estudios.",
     "Jack dropped out of college.",
     R % ("drop out", "drops out", "dropped out", "dropped out")
     + " Intransitive: drop out of something."),
    ("Get over with", "gu\u00e9t óuver uith", "Finish something unpleasant \u2014 Terminar de una vez.",
     "Emma got the exam over with quickly.",
     I % ("get over with", "gets over with", "got over with", "gotten over with")
     + " The object goes in the middle: get it over with."),
    ("Pull off", "púl of", "Succeed in doing something difficult \u2014 Lograr.",
     "Sarah pulled off a great performance.",
     R % ("pull off", "pulls off", "pulled off", "pulled off")
     + " Separable: pull it off."),
    ("Turn down", "tern dáun", "Refuse an offer or a request \u2014 Rechazar.",
     "Emma turned down the job offer.",
     R % ("turn down", "turns down", "turned down", "turned down")
     + " Separable: turn it down. Also means to lower the volume."),
    ("Turn up", "tern ap", "Appear or be found unexpectedly \u2014 Aparecer.",
     "My keys turned up yesterday.",
     R % ("turn up", "turns up", "turned up", "turned up")
     + " Intransitive in this sense. Also means to raise the volume."),
    ("Work through", "u\u00e9rk zru", "Deal with a problem step by step \u2014 Resolver poco a poco.",
     "Sarah worked through her difficulties.",
     R % ("work through", "works through", "worked through", "worked through")
     + " Not separable."),
    ("Write off", "ráit of", "Consider something a loss \u2014 Dar por perdido.",
     "The company wrote off the damaged equipment.",
     I % ("write off", "writes off", "wrote off", "written off")
     + " Separable: write it off."),
    ("Pass up", "pás ap", "Miss an opportunity by not taking it \u2014 Dejar pasar.",
     "Tom passed up a great offer.",
     R % ("pass up", "passes up", "passed up", "passed up")
     + " Separable: pass it up."),
    ("Follow through", "f\u00f3lou zru", "Complete what you started \u2014 Cumplir hasta el final.",
     "Emma followed through on her promise.",
     R % ("follow through", "follows through", "followed through", "followed through")
     + " Not separable; usually follow through on something."),
    ("Let down", "lét daun", "Disappoint someone \u2014 Defraudar.",
     "Sarah let her team down.",
     I % ("let down", "lets down", "let down", "let down")
     + " Separable: let someone down. All the forms look the same."),
    ("Call for", "kol for", "Require something \u2014 Requerir.",
     "The situation called for quick action.",
     R % ("call for", "calls for", "called for", "called for")
     + " Not separable."),
    ("Rule out", "rúl áut", "Eliminate a possibility \u2014 Descartar.",
     "The doctor ruled out an infection.",
     R % ("rule out", "rules out", "ruled out", "ruled out")
     + " Separable: rule it out."),
    ("Put down to", "pút daun tu", "Explain something as caused by \u2014 Atribuir a.",
     "Tom put his success down to practice.",
     I % ("put down to", "puts down to", "put down to", "put down to")
     + " The object goes in the middle: put it down to luck."),
    ("See through", "sí zru", "Recognise the truth about something \u2014 Calar.",
     "Emma saw through the excuse.",
     I % ("see through", "sees through", "saw through", "seen through")
     + " Not separable in this sense."),
    ("Stand up for", "stand ap for", "Defend someone or something \u2014 Defender.",
     "Jack stood up for his friend.",
     I % ("stand up for", "stands up for", "stood up for", "stood up for")
     + " Not separable."),
]


def main():
    assert len(ROWS) == 55, "expected 55 rows, have %d" % len(ROWS)

    import openpyxl

    # nothing that is already somewhere in the workbook
    wb = openpyxl.load_workbook(glossary.WORKBOOK, read_only=True)
    have = {}
    for name in wb.sheetnames:
        for cells in wb[name].iter_rows(min_row=2, max_col=1, values_only=True):
            if cells[0]:
                have.setdefault(glossary.normalise(cells[0]), name)
    wb.close()

    fresh = [r for r in ROWS if glossary.normalise(r[0]) not in have]
    skipped = [(r[0], have[glossary.normalise(r[0])]) for r in ROWS
               if glossary.normalise(r[0]) in have]
    for word, where in skipped:
        print("  already in %s: %s" % (where, word))
    if not fresh:
        print("Nothing to add.")
        return

    glossary.BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = glossary.BACKUPS / ("ENGLISH SCHOOL.pre-rest-%s.xlsx" % stamp)
    shutil.copy(glossary.WORKBOOK, kept)
    print("workbook copied to backups/%s" % kept.name)

    wb = openpyxl.load_workbook(glossary.WORKBOOK)
    ws = wb[SHEET]
    at = ws.max_row
    for word, pron, meaning, example, notes in fresh:
        at += 1
        ws.cell(row=at, column=1).value = word
        ws.cell(row=at, column=2).value = pron
        ws.cell(row=at, column=3).value = glossary.tidy(meaning)
        ws.cell(row=at, column=4).value = example
        ws.cell(row=at, column=glossary.NOTES_COL).value = glossary.tidy(notes)
    wb.save(glossary.WORKBOOK)
    print("added %d verbs to %s (now %d rows)" % (len(fresh), SHEET, at))


if __name__ == "__main__":
    main()
