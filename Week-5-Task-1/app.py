"""Week 5 - Task 1: Flask backend for the Azure Speech website.

Branch: text-to-speech
POST /api/tts  {"text": "...", "voice": "en-US-AvaMultilingualNeural"}  ->  audio/wav
"""
import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # finds the .env file in the repo root (walks up from this folder)
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")

app = Flask(__name__, static_folder="static", static_url_path="")

VOICES = {
    "en-US-AvaMultilingualNeural": "English (US) - Ava",
    "en-US-AndrewMultilingualNeural": "English (US) - Andrew",
    "en-GB-SoniaNeural": "English (UK) - Sonia",
    "tr-TR-EmelNeural": "Turkish - Emel",
    "tr-TR-AhmetNeural": "Turkish - Ahmet",
}
MAX_CHARS = 1000


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


if __name__ == "__main__":
    app.run(debug=True)   # macOS: app.run(debug=True, port=5001)
