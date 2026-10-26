# Vibe coding transcript – Week 5, Task 2 (voice-activated calculator)

AI tool: Claude (claude.ai). The conversation was in Turkish; prompts are summarised in English.

## Prompts

1. *"Read the Week 5 exercise and tell me step by step what I have to do."*
   → The AI split the exercise into Task 1 (speech website, Parts 0–4) and Task 2 (voice calculator)
   and noted that both need an Azure Speech key.

2. *"Improve my Week 4 calculator so it is voice-activated. A microphone button on the left starts
   voice commands; the words come from the command table (zero … nine, point, over, times, plus,
   minus, is). Every button must also speak its word, and '=' must speak the result
   ('is eight'). Keep the calculation on the Flask server like in Week 4. Put it in a new folder
   Week-5-Task-2 and don't touch Week4."*

3. *"Keep the Azure key secret – it must stay in .env and never reach the browser or GitHub."*
   → The backend got `/api/speech-token`, which exchanges the key for a 10-minute token; the browser
   only ever sees the token.

## Problems handled in the design

1. **Echo problem.** If every key – including the ones pressed by voice – were spoken while the
   microphone is open, the calculator would hear itself say "five" and press 5 again. Fix:
   while the calculator is talking (plus 400 ms), recognised speech is ignored, and keys pressed by
   voice do not repeat the word; only the result ("is 7") is spoken.

2. **Single words are recognised badly.** Azure often returns "to" for "two", "for" for "four"
   and converts words to symbols ("5 + 2"). Fixes: a phrase list with the command words is
   given to the recogniser, the parser accepts both words and digits/symbols, and common
   homophones (to/too, for, ate, won) are mapped to the right key.

3. **Slow first key presses.** Synthesising a word on its first press adds a delay, so the 15 key
   words are pre-loaded when the page opens and cached, so only the result phrase is fetched later.

4. **Overlapping speech.** Pressing keys quickly could play several words on top of each other. A small
   queue plays the phrases one after another.

5. **Azure region.** Creating the Speech resource in West Europe failed with
   `RequestDisallowedByAzure` (student subscription policy). The resource was created in
   Germany West Central instead.

## Corrections after testing

_(Add here anything that did not work on the first try when you tested on your own computer
and how it was fixed.)_
