# Mini Project 3 – Imagine: chat & create

A web app that generates images from a prompt and talks with you through a chatbot.
You can type or speak: the mic records your voice, it is turned into text, and the chatbot answers.
Both messages appear in the chat history; any bot answer can be copied into the prompt box
with **"Use as image prompt"**.

| Feature | Model (runs locally on the CPU) |
|---|---|
| Chatbot | HuggingFaceTB/SmolLM2-360M-Instruct |
| Speech to text | openai/whisper-small |
| Text to image | stabilityai/sd-turbo (Stable Diffusion, 2 steps) |

## Setup
```
pip install --only-binary=:all: diffusers accelerate flask "transformers==4.57.6" "huggingface-hub==0.36.2"
python download_models.py        # once, ~4.3 GB into the Hugging Face cache
```

## Run
```
python app.py                    # open http://127.0.0.1:5000
```
The three models load in the background when the app starts; the badge at the top turns green
("Models ready") when everything is loaded.

## Files
- `app.py` – Flask back end with the API routes (`/api/image`, `/api/transcribe`, `/api/chat`)
- `ai_models.py` – one class per model (`ChatBot`, `SpeechToText`, `ImageGenerator`), loaded lazily
- `templates/index.html`, `static/style.css`, `static/app.js` – the web page (mic recording with the Web Audio API, sent as WAV)
- `download_models.py` – downloads the models once

## Design
The Figma design follows the example layout of the assignment (title + icon, image output box with
paint button, prompt box, chat history, mic – message – send). `design/imagine-design.svg` is the
source that was imported into Figma; the web page uses the same colours, icons and layout.

## Figma
https://www.figma.com/design/pMki32l6F6DralmhfCSGij/EE471-Mini-Project-3-%E2%80%93-Imagine?node-id=0-1
