"""Week 5 - Task 1: Flask backend for the Azure Speech website.

Branch: speech-to-text
POST /api/stt  (multipart: audio=<16 kHz mono WAV>, language=en-US)  ->  {"text": "..."}
The browser converts both microphone recordings and uploaded files to WAV before sending.
"""
import os
import tempfile
import threading

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # finds the .env file in the repo root (walks up from this folder)
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024   # 20 MB upload limit

LANGUAGES = {
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "tr-TR": "Turkish",
}


def error(message, status):
    return jsonify({"error": message}), status


def speech_config():
    """Build the Azure config from the .env values."""
    if not SPEECH_KEY or not SPEECH_REGION:
        raise RuntimeError("SPEECH_KEY / SPEECH_REGION missing in .env")
    return speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)


def transcribe_wav(path, language):
    """Continuous recognition over the whole file (recognize_once stops after ~30 s).

    Returns the recognised text. Raises RuntimeError with Azure's message on failure.
    """
    config = speech_config()
    config.speech_recognition_language = language
    audio = speechsdk.audio.AudioConfig(filename=path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=config, audio_config=audio)

    pieces, problems = [], []
    finished = threading.Event()

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text:
            pieces.append(evt.result.text)

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            problems.append(evt.cancellation_details.error_details)
        finished.set()

    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(lambda _evt: finished.set())

    recognizer.start_continuous_recognition()
    finished.wait(timeout=120)
    recognizer.stop_continuous_recognition()

    if problems and not pieces:
        raise RuntimeError(problems[0])
    return " ".join(pieces)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/languages")
def languages():
    return jsonify([[code, label] for code, label in LANGUAGES.items()])


@app.route("/api/stt", methods=["POST"])
def speech_to_text():
    """Receive a WAV file, transcribe it with Azure, return the text."""
    upload = request.files.get("audio")
    language = request.form.get("language", "en-US")

    if upload is None:
        return error("No audio received.", 400)
    if language not in LANGUAGES:
        return error("Unknown language.", 400)

    data = upload.read()
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return error("Audio must be a WAV file.", 400)

    # The SDK reads from a file path, so store the upload in a temporary file.
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    try:
        tmp.write(data)
        tmp.close()
        text = transcribe_wav(tmp.name, language)
    except RuntimeError as exc:
        return error(f"Azure error: {exc}", 502)
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass   # Windows may still hold the file for a moment; it is a temp file anyway

    if not text:
        return error("No speech could be recognised in the audio.", 422)
    return jsonify({"text": text, "language": language})


if __name__ == "__main__":
    app.run(debug=True)   # macOS: app.run(debug=True, port=5001)
