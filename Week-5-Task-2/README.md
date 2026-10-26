# Week 5 – Task 2: Voice-activated calculator

The Week 4 calculator with a microphone button and "magical" talking keys.

- **Voice input:** press the microphone (it turns red) and say the commands below.
  Recognition runs in the browser with the Azure Speech JS SDK; the browser gets a
  short-lived token from `/api/speech-token`, so the secret key never leaves the server.
- **Voice output:** every key press is spoken with Azure TTS (`/api/speak`),
  e.g. 3, +, 5, = → "three", "plus", "five", "is 8".
- **Calculation:** unchanged from Week 4 – `POST /api/calculate` with the `Calculator` class.

| Key | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | . | ÷ | × | + | − | = |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Word | zero | one | two | three | four | five | six | seven | eight | nine | point | over | times | plus | minus | is |

## Run

```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 . Needs `SPEECH_KEY` and `SPEECH_REGION` in the `.env` file in the repo root.

`static/vendor/speech-sdk-1.51.0.min.js` is the official Azure Speech SDK for the browser
(npm package `microsoft-cognitiveservices-speech-sdk`), stored locally so the page works without a CDN.
