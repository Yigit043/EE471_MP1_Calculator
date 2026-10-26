"""Week 5 - Task 1: Flask backend for the Azure Speech website.

Merged result of the "text-to-speech" and "speech-to-text" branches (Part 3).
    POST /api/tts  {"text": "...", "voice": "..."}                 -> audio/wav
    POST /api/stt  (multipart: audio=<16 kHz mono WAV>, language)  -> {"text": "..."}
"""
import os
import tempfile
import threading

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # finds the .env file in the repo root (walks up from this folder)
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024   # 20 MB upload limit

VOICES = {
    "en-US-AvaMultilingualNeural": "English (US) - Ava",
    "en-US-AndrewMultilingualNeural": "English (US) - Andrew",
    "en-GB-SoniaNeural": "English (UK) - Sonia",
    "tr-TR-EmelNeural": "Turkish - Emel",
    "tr-TR-AhmetNeural": "Turkish - Ahmet",
}
LANGUAGES = {
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "tr-TR": "Turkish",
}
MAX_CHARS = 1000


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------
def error(message, status):
    return jsonify({"error": message}), status


def speech_config():
    """Build the Azure config from the .env values."""
    if not SPEECH_KEY or not SPEECH_REGION:
        raise RuntimeError("SPEECH_KEY / SPEECH_REGION missing in .env")
    return speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# --------------------------------------------------------------------------
# Text to speech (from branch text-to-speech)
# --------------------------------------------------------------------------
@app.route("/api/voices")
def voices():
    """List of [voice_id, label] pairs (a list keeps the order; JSON objects get sorted)."""
    return jsonify([[vid, label] for vid, label in VOICES.items()])


@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    """Convert text to a WAV file with Azure and send the bytes back."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    voice = data.get("voice", "en-US-AvaMultilingualNeural")

    if not text:
        return error("Please enter some text.", 400)
    if len(text) > MAX_CHARS:
        return error(f"Text is too long (max {MAX_CHARS} characters).", 400)
    if voice not in VOICES:
        return error("Unknown voice.", 400)

    try:
        config = speech_config()
    except RuntimeError as exc:
        return error(str(exc), 500)
    config.speech_synthesis_voice_name = voice
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )

    # audio_config=None -> keep the audio in memory instead of playing it on the server
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return Response(
            result.audio_data,
            mimetype="audio/wav",
            headers={"Content-Disposition": "inline; filename=speech.wav"},
        )

    details = result.cancellation_details
    return error(f"Azure error: {details.reason} {details.error_details or ''}".strip(), 502)


# --------------------------------------------------------------------------
# Speech to text (from branch speech-to-text)
# --------------------------------------------------------------------------
def save_wav_upload():
    """Validate the uploaded WAV and store it in a temp file. Returns (path, language)."""
    upload = request.files.get("audio")
    language = request.form.get("language", "en-US")
    if upload is None:
        raise ValueError("No audio received.")
    if language not in LANGUAGES:
        raise ValueError("Unknown language.")
    data = upload.read()
    if len(data) < 44 or data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Audio must be a WAV file.")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(data)
    tmp.close()
    return tmp.name, language


def remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass   # Windows may still hold the file for a moment; it is a temp file anyway


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


@app.route("/api/languages")
def languages():
    return jsonify([[code, label] for code, label in LANGUAGES.items()])


@app.route("/api/stt", methods=["POST"])
def speech_to_text():
    """Receive a WAV file, transcribe it with Azure, return the text."""
    try:
        path, language = save_wav_upload()
    except ValueError as exc:
        return error(str(exc), 400)
    try:
        text = transcribe_wav(path, language)
    except RuntimeError as exc:
        return error(f"Azure error: {exc}", 502)
    finally:
        remove_file(path)

    if not text:
        return error("No speech could be recognised in the audio.", 422)
    return jsonify({"text": text, "language": language})


if __name__ == "__main__":
    app.run(debug=True)   # macOS: app.run(debug=True, port=5001)
