# Week 4 – Calculator

## Section 1 – Part 1: Figma Design

Figma (view-only): https://www.figma.com/design/UyaD1O5YcDovKtfeVoh53b/EE471-Week4-Calculator?node-id=2-68&t=4M9PMSd4KfgpLdvf-1

![Calculator design](design/calculator.png)

## Section 1 – Part 2: Web page + Flask backend

```
Week4/
├── app.py              Flask server: serves the page, exposes POST /api/calculate
├── custom_classes.py   Calculator class from Mini Project 1 (+ calculate() dispatcher)
├── main.py             Mini Project 1 demo script (unchanged)
├── requirements.txt
├── PROMPTS.md          prompts used with the AI tool and the corrections made
├── design/calculator.png
└── static/
    ├── index.html
    ├── style.css
    └── script.js       sends every operation to the API; no arithmetic in JS
```

### Run

```
cd Week4
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

### API

`POST /api/calculate` – all arithmetic is done on the server by the `Calculator` class (no `eval()`).

| Request body (JSON)                 | Response                                   |
|-------------------------------------|--------------------------------------------|
| `{"a": 10, "op": "+", "b": 5}`      | `200` `{"result": 15}`                     |
| `{"a": 7,  "op": "/", "b": 0}`      | `400` `{"error": "Cannot divide by zero"}` |
| `{"a": 7,  "op": "^", "b": 2}`      | `400` `{"error": "Invalid operator: '^'"}` |
| `{"a": "7", "op": "+", "b": 2}`     | `400` `{"error": "Operands must be numbers"}` |
| `{"a": 7}`                          | `400` `{"error": "Missing field(s): op, b"}` |

`op` accepts `+  -  *  /` and also the display symbols `−  ×  ÷`.

Example with curl:

```
curl -X POST http://127.0.0.1:5000/api/calculate -H "Content-Type: application/json" -d "{\"a\": 10, \"op\": \"+\", \"b\": 5}"
```

## Section 2 – Part 1: Library App Figma Design (bonus)

Figma (view-only): https://www.figma.com/design/zVe5WMORIavA4ihry0FLMm/EE471-Week4-Library?node-id=2-2&t=K84LFk1KQJWkVATH-1

![Library design](design/library.png)
## Section 2 – Part 2: CRUD methods

`library/custom_classes.py`: exceptions, unique ids, `to_dict()`, CRUD methods on `LibraryCollection`.
`library/main.py` calls every method and triggers every exception.

Run: `python library/main.py`
## Section 2 – Part 4: Frontend

`library/static/` (index.html, style.css, script.js) is served by Flask at http://127.0.0.1:5000.
Every action calls the REST API; API error messages (e.g. 409 on deleting a checked-out item)
are shown in the error area. Prompts and fixes: `library/PROMPTS.md`.