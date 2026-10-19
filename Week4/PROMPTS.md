# PROMPTS.md – Section 1 (Calculator)

AI tool used: Claude (claude.ai chat).

## Main prompts

1. *"Design the calculator above on Figma with Auto Layout"* – I built the Figma frame by hand following
   step-by-step instructions (text → Shift+A auto layout key → duplicate into rows → rows into a
   vertical auto-layout body).

2. *"Turn my Figma calculator design into a working web page (HTML/CSS/JS). Same colours and layout:
   blue body, white display with the number right-aligned, gray digit keys, light-blue operator keys,
   dark-blue = key. Keys 7 8 9 ÷ / 4 5 6 × / 1 2 3 − / 0 . = +."*

3. *"Move all calculations to a Flask server on localhost. Flask must serve the page and expose
   POST /api/calculate that takes {"a": number, "op": "+|-|*|/", "b": number} and returns
   {"result": number}. Do not use eval(). Return {"error": "<message>"} with status 400 for invalid
   input and division by zero. Reuse the Calculator class from Mini Project 1 for the arithmetic."*

4. *"Add keyboard support and let the user chain operations (e.g. 2 + 3 × 4 =) – but every single
   operation must still go through the API, no arithmetic in JavaScript."*

## Corrections I made

1. **Wrong starting assumption.** The first plan treated the Mini Project 1 calculator as an
   HTML/CSS/JS page and tried to copy `*.html, *.css, *.js` into Week4. The Mini Project 1 calculator
   is actually a Python class (`custom_classes.py`). Fixed by copying `custom_classes.py` / `main.py`
   into Week4 and extending the class with a `calculate(a, op, b)` dispatcher that the Flask route calls.

2. **Missing JSON spec.** The exercise says "using the JSON format given above" but no format is
   given in the PDF. I defined the format explicitly and documented it in README.md so the API is
   self-describing:
   request `{"a": 10, "op": "+", "b": 5}` → `200 {"result": 15}`; errors → `400 {"error": "..."}`.

3. **Operator symbols.** The page shows `÷ × −` but the Calculator only knows `/ * -`. Instead of
   changing the class, the Flask route normalises the symbols (`OPERATOR_ALIASES`) so both the page
   and API clients like Thunder Client can send either form.

4. **Boolean operands.** `isinstance(True, int)` is `True` in Python, so `{"a": true}` would have
   been accepted as 1. Added an explicit `bool` check in `_to_number()` so it returns 400.
