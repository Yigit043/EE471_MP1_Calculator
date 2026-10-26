"""Week 5 - Task 2: voice-activated calculator.

Built on the Week 4 calculator (same Calculator class and POST /api/calculate).
New in Week 5:
    GET  /api/speech-token  short-lived Azure token so the browser can listen to the
                            microphone with the Azure Speech JS SDK (the key stays on the server)
    POST /api/speak         {"text": "five"} -> WAV spoken by Azure (the "magical" buttons)
"""
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
import azure.cognitiveservices.speech as speechsdk

from custom_classes import Calculator

load_dotenv()  # finds the .env file in the repo root (walks up from this folder)
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
VOICE = "en-US-AvaMultilingualNeural"

app = Flask(__name__, static_folder="static", static_url_path="")
calc = Calculator()

# Symbols the frontend may send, normalised to the four the Calculator knows.
OPERATOR_ALIASES = {
    "+": "+",
    "-": "-", "−": "-",
    "*": "*", "×": "*", "x": "*",
    "/": "/", "÷": "/",
}


@app.route("/")
def index():
    """Serve the calculator page."""
    return send_from_directory(app.static_folder, "index.html")


# --------------------------------------------------------------------------
# Week 4: calculation (unchanged)
# --------------------------------------------------------------------------
def _to_number(value):
    """Accept int/float JSON numbers only (bool is rejected on purpose)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Operands must be numbers")
    return value


@app.route("/api/calculate", methods=["POST"])
def calculate():
    """
    Request JSON : {"a": <number>, "op": "+" | "-" | "*" | "/", "b": <number>}
    Success 200 : {"result": <number>}
    Error   400 : {"error": "<message>"}
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be JSON"}), 400

    missing = [key for key in ("a", "op", "b") if key not in data]
    if missing:
        return jsonify({"error": f"Missing field(s): {', '.join(missing)}"}), 400

    try:
        a = _to_number(data["a"])
        b = _to_number(data["b"])
        op = OPERATOR_ALIASES.get(str(data["op"]))
        if op is None:
            raise ValueError(f"Invalid operator: {data['op']!r}")
        result = calc.calculate(a, op, b)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"result": result}), 200


# --------------------------------------------------------------------------
# Week 5: voice input (token for the browser) and voice output (speak)
# --------------------------------------------------------------------------
def keys_ok():
    return bool(SPEECH_KEY and SPEECH_REGION)


@app.route("/api/speech-token")
def speech_token():
    """Exchange the secret key for a 10-minute token the browser may use."""
    if not keys_ok():
        return jsonify({"error": "SPEECH_KEY / SPEECH_REGION missing in .env"}), 500
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    req = urllib.request.Request(url, data=b"", method="POST",
                                 headers={"Ocp-Apim-Subscription-Key": SPEECH_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            token = response.read().decode()
    except (urllib.error.URLError, TimeoutError) as exc:
        return jsonify({"error": f"Could not get an Azure token: {exc}"}), 502
    return jsonify({"token": token, "region": SPEECH_REGION})


@app.route("/api/speak", methods=["POST"])
def speak():
    """Text -> WAV with Azure TTS. Used for every key press and for the result."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Nothing to say."}), 400
    if len(text) > 100:
        return jsonify({"error": "Text is too long."}), 400
    if not keys_ok():
        return jsonify({"error": "SPEECH_KEY / SPEECH_REGION missing in .env"}), 500

    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    config.speech_synthesis_voice_name = VOICE
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = result.cancellation_details
        return jsonify({"error": f"Azure error: {details.error_details}"}), 502
    return Response(result.audio_data, mimetype="audio/wav")


if __name__ == "__main__":
    app.run(debug=True)   # macOS: app.run(debug=True, port=5001)
