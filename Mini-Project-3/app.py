"""Mini Project 3 - a simple chatbot with image generation (Flask back end).

    python app.py      -> open http://127.0.0.1:5000

    GET  /               the web page
    GET  /api/status     which models are loaded
    POST /api/image      {"prompt": "..."}                  -> {"image": data URL, "seconds": ...}
    POST /api/transcribe form file "audio" (WAV)            -> {"text": "..."}
    POST /api/chat       {"history": [{role, content}, ...]} -> {"reply": "..."}
"""
import os
import threading
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")         # all models are already in the local cache

from flask import Flask, jsonify, render_template, request  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from ai_models import ChatBot, ImageGenerator, SpeechToText  # noqa: E402

app = Flask(__name__)
chatbot = ChatBot()
speech = SpeechToText()
painter = ImageGenerator()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def status():
    return jsonify(chat=chatbot.ready, speech=speech.ready, image=painter.ready)


@app.post("/api/image")
def generate_image():
    prompt = (request.get_json(silent=True) or {}).get("prompt", "").strip()
    if not prompt:
        return jsonify(error="Write a prompt first."), 400
    start = time.time()
    image = painter.generate(prompt)
    return jsonify(image=image, seconds=round(time.time() - start, 1))


@app.post("/api/transcribe")
def transcribe():
    audio = request.files.get("audio")
    if audio is None:
        return jsonify(error="No audio received."), 400
    return jsonify(text=speech.transcribe(audio.read()))


@app.post("/api/chat")
def chat():
    history = (request.get_json(silent=True) or {}).get("history", [])
    history = [m for m in history if m.get("role") in ("user", "assistant") and m.get("content")]
    if not history or history[-1]["role"] != "user":
        return jsonify(error="Send a message first."), 400
    return jsonify(reply=chatbot.reply(history))


@app.errorhandler(Exception)
def on_error(exc):
    if isinstance(exc, HTTPException):              # 404 and friends stay as they are
        return exc
    app.logger.exception(exc)
    return jsonify(error=str(exc)), 500


def warm_up():
    """Load the three models in the background, so the first click does not wait."""
    for model in (chatbot, speech, painter):
        try:
            model.load()
            print(f"  loaded {model.model_id}")
        except Exception as exc:
            print(f"  could not load {model.model_id}: {exc}")


if __name__ == "__main__":
    threading.Thread(target=warm_up, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, threaded=True)
