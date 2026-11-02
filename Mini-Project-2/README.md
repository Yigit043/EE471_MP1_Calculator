# Mini Project 2 – Voice-activated Library

The Week 4 library (REST API + web page) with a **voice librarian**: every endpoint can be
called by speaking, and the app answers out loud with Azure Speech Services.

```
Mini-Project-2/
├── app.py                 Week 4 REST API + /api/speech-token, /api/speak, /api/voice
├── voice_commands.py      spoken sentence -> REST request, response -> librarian's sentence
├── custom_classes.py      Week 4 library model (unchanged)
├── main.py                Week 4 demo script (unchanged)
├── test_voice_commands.py tests:  python -m unittest -v
├── requirements.txt
└── static/
    ├── index.html, style.css, script.js   Week 4 page + voice panel
    ├── voice.js                           microphone, voice commands, spoken answers
    └── vendor/speech-sdk-1.51.0.min.js    official Azure Speech SDK for the browser
```

## Setup

1. Azure Speech key in a `.env` file in the **repository root** (it is in `.gitignore`, so it is never pushed):
   ```
   SPEECH_KEY=<your key>
   SPEECH_REGION=<your region, e.g. germanywestcentral>
   ```
2. Install and run:
   ```
   cd Mini-Project-2
   pip install -r requirements.txt
   python app.py
   ```
3. Open http://127.0.0.1:5000 , press the microphone and speak (allow microphone access).
   Commands can also be typed into the box next to it.

## How it works

1. **Listen:** `voice.js` gets a 10-minute token from `/api/speech-token` (the key stays on the
   server) and runs Azure speech recognition on the microphone in the browser.
2. **Understand:** each recognised sentence is sent to `POST /api/voice`. `voice_commands.py`
   turns it into one of the REST calls below.
3. **Act:** `app.py` sends that request to its own REST endpoint, so voice and normal HTTP
   clients get exactly the same rules and status codes.
4. **Answer:** the response is turned into a sentence, spoken with Azure TTS (`/api/speak`),
   shown in the voice log, and the item list is refreshed.

## Voice commands

| Say | REST call | Librarian answers (examples) |
|---|---|---|
| "Create item, type book, title The Catcher in the Rye, author J.D. Salinger, pages 220" | `POST /api/items` | "Successfully created book 'The Catcher in the Rye' with ID 4." |
| "Create a DVD, title Interstellar, author Christopher Nolan, duration 169 minutes" | `POST /api/items` | "Successfully created DVD 'Interstellar' with ID 5." |
| "List all items" / "List available books" / "Show me the DVDs" | `GET /api/items?available=true&type=book` | "I found 2 available books: 'Dune' and 'Neuromancer'." |
| "Get item 2" / "What is item 2?" | `GET /api/items/2` | "Item 2 is the DVD 'Arrival' by Denis Villeneuve, 116 minutes, currently available." |
| "Replace item 2, title Arrival, author Denis Villeneuve, duration 116" | `PUT /api/items/2` | "Item 2 has been updated: title Arrival, author Denis Villeneuve, duration 116." |
| "Change item 1 title to Dune Messiah" / "Update item 3, pages 300" | `PATCH /api/items/1` | "Item 1 has been updated: title Dune Messiah." |
| "Check out item 3" | `POST /api/items/3/checkout` | "Item 3, 'Neuromancer', has been checked out." |
| "Check out item 3" (again) | `POST /api/items/3/checkout` → 409 | "Sorry, item 3 is already checked out." |
| "Return item 3" | `POST /api/items/3/return` | "Item 3, 'Neuromancer', has been returned. Thank you." |
| "Delete item 3" | `DELETE /api/items/3` | "Item 3, 'Neuromancer', has been deleted." / 409: "…is checked out, so it cannot be deleted." |
| any command with an unknown id | → 404 | "Sorry, I could not find item 99." |
| "List magazines" | → 400 bad filter | "Sorry, type filter must be 'book' or 'dvd'" |
| "Help" | – | lists example commands |

Numbers can be said as digits or words ("item three"). The REST API itself is unchanged
from Week 4 and still works with Postman / Thunder Client.
