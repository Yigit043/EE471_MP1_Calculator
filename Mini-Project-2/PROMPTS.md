# PROMPTS.md – Mini Project 2 (voice-activated library)

AI tool: Claude (claude.ai). The conversation was in Turkish; prompts are summarised in English.

## Main prompts

1. *"Here is Mini Project 2. It reuses the projects we did together (Week 4 library, Week 5
   speech). Do everything except the deliverables. I have about an hour."*

2. *"Start from the Week 4 library app (REST API with 8 endpoints + web page). Add voice
   activation with Azure Speech: every endpoint must be callable by voice, and at the end of each
   run the app must say what it did – exactly like the examples in the PDF ('Successfully created
   book … with ID 3', 'Item 3, … has been checked out', 'Sorry, item 3 is already checked
   out')."*

3. *"Keep the Azure key in the root .env (already in .gitignore). Reuse what worked in Week 5:
   the token endpoint, the Azure Speech JS SDK in the browser, and /api/speak for the voice."*

## Design decisions

- **Voice goes through the real REST endpoints.** `/api/voice` parses the sentence into a REST
  request and sends it to the app's own endpoint (Flask test client). Voice users therefore get
  the same validation and status codes (201/200/204/400/404/409) as Postman users, and no library
  rule is duplicated in the voice code.
- **Parsing is separate from Flask** (`voice_commands.py`), so it can be tested without a
  microphone (`test_voice_commands.py`) and explained on its own.
- **Typed commands** use the same path as spoken ones – useful for testing and for the demo.
- **The microphone ignores the librarian's own voice** (500 ms after it stops talking), as in
  the Week 5 voice calculator.
- **Longer pause allowed** (1.5 s) before a sentence is considered finished, because create
  commands are long and people pause between fields.

## Things the AI got wrong that were fixed

1. **Number glued to the author.** In "Add a new DVD title Blade Runner author Ridley Scott 117
   minutes" the author was parsed as "Ridley Scott 117". Fixed: when the next keyword is
   "minutes", a trailing number is moved from the previous field to the duration.
2. **Unrelated questions read the catalogue.** "What is the weather today?" was treated as
   "list items" because "what" was a list keyword. Fixed: listing now needs words like list,
   show, items, books, DVDs or available; anything else gets "Sorry, I did not understand".

## Corrections after testing with the microphone

_(Add anything that did not work on the first try on your own computer and how it was fixed.)_
