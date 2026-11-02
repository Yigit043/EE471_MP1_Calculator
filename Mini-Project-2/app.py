"""Mini Project 2: voice-activated library.

Week 4 REST API (unchanged) + voice:
    GET  /api/speech-token  short-lived Azure token for speech recognition in the browser
    POST /api/speak         text -> WAV (Azure TTS): the librarian's voice
    POST /api/voice         {"text": "check out item 3"} -> parsed, sent to the real REST
                            endpoint, and answered with a sentence for the librarian to say

The REST routes only translate HTTP <-> LibraryCollection method calls.
All business rules (ids, availability, editable fields) live in custom_classes.py.
Every response is JSON. Errors look like {"error": "<message>"}.
"""
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_from_directory
import azure.cognitiveservices.speech as speechsdk

from custom_classes import LibraryCollection, Book, DVD, ItemNotFoundError, ItemStateError
from voice_commands import HELP_TEXT, parse_command, reply_for

load_dotenv()  # SPEECH_KEY and SPEECH_REGION from the .env file (repo root, never committed)
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
VOICE = "en-US-AvaMultilingualNeural"

app = Flask(__name__, static_folder="static", static_url_path="")

# One collection for the whole app, seeded with 3 items of mixed types.
library = LibraryCollection()
library.add_item(Book("Dune", "Frank Herbert", 412))
library.add_item(DVD("Arrival", "Denis Villeneuve", 116))
library.add_item(Book("Neuromancer", "William Gibson", 271))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def error(message, status):
    """Build the standard error response."""
    return jsonify({"error": message}), status


def get_json_body():
    """Return the request body as a dict, or raise ValueError."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")
    return data


def parse_bool(value):
    """'true'/'false' query strings -> bool. Anything else raises ValueError."""
    if value is None:
        return None
    lowered = value.lower()
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    raise ValueError("available must be true or false")


# Map the two domain exceptions to HTTP codes in one place.
@app.errorhandler(ItemNotFoundError)
def handle_not_found(exc):
    return error(str(exc), 404)


@app.errorhandler(ItemStateError)
def handle_state_conflict(exc):
    return error(str(exc), 409)


@app.errorhandler(ValueError)
def handle_bad_request(exc):
    return error(str(exc), 400)


@app.errorhandler(404)
def handle_unknown_route(_exc):
    return error("Route not found", 404)


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
@app.route("/")
def index():
    """Serve the single-page frontend (Part 4)."""
    return send_from_directory(app.static_folder, "index.html")


# --------------------------------------------------------------------------
# /api/items
# --------------------------------------------------------------------------
@app.route("/api/items", methods=["GET"])
def list_items():
    """List items. Filters: ?available=true|false and ?type=book|dvd -> 200 / 400."""
    available = parse_bool(request.args.get("available"))      # ValueError -> 400
    item_type = request.args.get("type")                         # ValueError -> 400
    items = library.list_items(available=available, item_type=item_type)
    return jsonify([item.to_dict() for item in items]), 200


@app.route("/api/items", methods=["POST"])
def create_item():
    """Create a Book or DVD -> 201 + the new item / 400."""
    data = get_json_body()
    item = library.create_item(data)                             # ValueError -> 400
    return jsonify(item.to_dict()), 201


# --------------------------------------------------------------------------
# /api/items/<id>
# --------------------------------------------------------------------------
@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Get one item -> 200 / 404."""
    return jsonify(library.get_item(item_id).to_dict()), 200


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def replace_item(item_id):
    """Replace ALL editable fields -> 200 / 400 / 404."""
    data = get_json_body()
    item = library.get_item(item_id)                             # 404 first
    missing = [f for f in item.EDITABLE_FIELDS if f not in data]
    if missing:
        raise ValueError(f"PUT requires all editable fields; missing: {', '.join(missing)}")
    extra = [f for f in data if f not in item.EDITABLE_FIELDS]
    if extra:
        raise ValueError(f"Field(s) cannot be changed: {', '.join(extra)}")
    item = library.update_item(item_id, **data)
    return jsonify(item.to_dict()), 200


@app.route("/api/items/<int:item_id>", methods=["PATCH"])
def patch_item(item_id):
    """Change SOME editable fields -> 200 / 400 / 404."""
    data = get_json_body()
    item = library.update_item(item_id, **data)                  # 404 or 400 from the class
    return jsonify(item.to_dict()), 200


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Remove an item -> 204 / 404 / 409 if checked out."""
    library.remove_item(item_id)
    return "", 204


# --------------------------------------------------------------------------
# checkout / return
# --------------------------------------------------------------------------
@app.route("/api/items/<int:item_id>/checkout", methods=["POST"])
def checkout_item(item_id):
    """Check an item out -> 200 / 404 / 409 if already out."""
    item = library.get_item(item_id)
    message = item.checkout()
    return jsonify({"message": message, "item": item.to_dict()}), 200


@app.route("/api/items/<int:item_id>/return", methods=["POST"])
def return_item(item_id):
    """Return an item -> 200 / 404 / 409 if not checked out."""
    item = library.get_item(item_id)
    message = item.return_item()
    return jsonify({"message": message, "item": item.to_dict()}), 200



# --------------------------------------------------------------------------
# Voice: token, speech output, voice commands
# --------------------------------------------------------------------------
def keys_missing():
    return not (SPEECH_KEY and SPEECH_REGION)


@app.route("/api/speech-token")
def speech_token():
    """Exchange the secret key for a 10-minute token the browser may use."""
    if keys_missing():
        return error("SPEECH_KEY / SPEECH_REGION missing in .env", 500)
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    req = urllib.request.Request(url, data=b"", method="POST",
                                 headers={"Ocp-Apim-Subscription-Key": SPEECH_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            token = response.read().decode()
    except (urllib.error.URLError, TimeoutError) as exc:
        return error(f"Could not get an Azure token: {exc}", 502)
    return jsonify({"token": token, "region": SPEECH_REGION})


@app.route("/api/speak", methods=["POST"])
def speak():
    """Text -> WAV with Azure TTS (the librarian's answer)."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return error("Nothing to say.", 400)
    if len(text) > 600:
        return error("Text is too long.", 400)
    if keys_missing():
        return error("SPEECH_KEY / SPEECH_REGION missing in .env", 500)

    config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    config.speech_synthesis_voice_name = VOICE
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        return error(f"Azure error: {result.cancellation_details.error_details}", 502)
    return Response(result.audio_data, mimetype="audio/wav")


def call_endpoint(method, path, body=None):
    """Send a request to this app's own REST API (same rules, same status codes)."""
    with app.test_client() as client:
        response = client.open(path, method=method, json=body)
    data = response.get_json(silent=True) if response.data else None
    return response.status_code, data


@app.route("/api/voice", methods=["POST"])
def voice_command():
    """Recognised sentence -> REST call -> sentence for the librarian to speak."""
    text = str((request.get_json(silent=True) or {}).get("text", "")).strip()
    if not text:
        return error("No text received.", 400)

    cmd = parse_command(text)
    if cmd.intent == "help":
        return jsonify({"heard": text, "intent": "help", "reply": HELP_TEXT})
    if cmd.intent == "unknown":
        return jsonify({"heard": text, "intent": "unknown",
                        "reply": "Sorry, I did not understand. Say help to hear what I can do."})
    if cmd.intent == "missing_id":
        return jsonify({"heard": text, "intent": "missing_id",
                        "reply": "Which item? Please say the item number, for example item 3."})

    # For DELETE remember the title first: a successful DELETE returns no body.
    before = None
    if cmd.intent == "delete":
        status, before = call_endpoint("GET", f"/api/items/{cmd.item_id}")
        before = before if status == 200 else None

    status, data = call_endpoint(cmd.method, cmd.path, cmd.body)
    return jsonify({
        "heard": text,
        "intent": cmd.intent,
        "request": {"method": cmd.method, "path": cmd.path, "body": cmd.body},
        "status": status,
        "response": data,
        "reply": reply_for(cmd, status, data, before),
    })


if __name__ == "__main__":
    app.run(debug=True)            # macOS: app.run(debug=True, port=5001)
