"""Week 6 - Task 2: cat-kind classifier website.

The page uploads a photo to this Flask app; the app forwards it to the Cog container
(the ResNet50 model) and returns the prediction to the page.

    POST /api/classify   multipart form: image=<file>   ->  the Cog model's output (JSON)
COG_URL tells the app where the model is (set in docker-compose.yml).
"""
import base64
import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, request, send_from_directory

COG_URL = os.getenv("COG_URL", "http://localhost:5002/predictions")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
MAX_BYTES = 10 * 1024 * 1024

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES


def error(message, status):
    return jsonify({"error": message}), status


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/classify", methods=["POST"])
def classify():
    upload = request.files.get("image")
    if upload is None or not upload.filename:
        return error("Please choose an image first.", 400)
    if upload.mimetype not in ALLOWED_TYPES:
        return error("Only JPG, PNG, WEBP, GIF or BMP images are accepted.", 400)

    # Cog's HTTP API takes files as a URL; a data URL carries the image inside the JSON body.
    data_url = f"data:{upload.mimetype};base64," + base64.b64encode(upload.read()).decode()
    body = json.dumps({"input": {"image": data_url}}).encode()
    req = urllib.request.Request(COG_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            prediction = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return error(f"Model error ({exc.code}): {exc.read().decode(errors='ignore')[:300]}", 502)
    except (urllib.error.URLError, TimeoutError) as exc:
        return error(f"Model container is not reachable at {COG_URL}: {exc}", 503)

    if prediction.get("status") != "succeeded":
        return error(f"Prediction failed: {prediction.get('error') or prediction.get('status')}", 502)
    return jsonify(prediction["output"])


if __name__ == "__main__":
    app.run(debug=True, port=5003)
