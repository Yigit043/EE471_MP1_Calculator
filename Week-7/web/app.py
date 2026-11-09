"""Week 7: classifier website with a side-by-side comparison of two models.

The page uploads an image to this Flask app; the app sends it to BOTH Cog containers
(the baseline model and the optimized model) at the same time and returns both answers.

    GET  /api/info       -> page title and the class names
    POST /api/classify   multipart form: image=<file>  ->  {"baseline": {...}, "optimized": {...}}

The same website is used for Fashion-MNIST and CIFAR-10; docker-compose.yml sets
DATASET, PAGE_TITLE, BASELINE_URL and OPTIMIZED_URL for each one.
"""
import base64
import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request, send_from_directory

DATASET = os.getenv("DATASET", "fashion")
PAGE_TITLE = os.getenv("PAGE_TITLE", "Garment Classifier")
MODEL_URLS = {
    "baseline": os.getenv("BASELINE_URL", "http://localhost:5010/predictions"),
    "optimized": os.getenv("OPTIMIZED_URL", "http://localhost:5011/predictions"),
}
CLASSES = {
    "fashion": ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
                "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"],
    "cifar10": ["airplane", "automobile", "bird", "cat", "deer",
                "dog", "frog", "horse", "ship", "truck"],
}
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def ask_model(url, body):
    """Send the image to one Cog container; return its output or an error message."""
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            prediction = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return {"error": f"Model error ({exc.code})"}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"error": f"Model container is not reachable at {url} ({exc})"}
    if prediction.get("status") != "succeeded":
        return {"error": f"Prediction failed: {prediction.get('error') or prediction.get('status')}"}
    return prediction["output"]


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/info")
def info():
    return jsonify({"title": PAGE_TITLE, "dataset": DATASET, "classes": CLASSES[DATASET]})


@app.route("/api/classify", methods=["POST"])
def classify():
    upload = request.files.get("image")
    if upload is None or not upload.filename:
        return jsonify({"error": "Please choose an image first."}), 400
    if upload.mimetype not in ALLOWED_TYPES:
        return jsonify({"error": "Only JPG, PNG, WEBP, GIF or BMP images are accepted."}), 400

    # Cog's HTTP API takes files as a URL; a data URL carries the image inside the JSON body.
    data_url = f"data:{upload.mimetype};base64," + base64.b64encode(upload.read()).decode()
    body = json.dumps({"input": {"image": data_url}}).encode()
    with ThreadPoolExecutor(max_workers=2) as pool:          # ask both models at the same time
        futures = {name: pool.submit(ask_model, url, body) for name, url in MODEL_URLS.items()}
        answers = {name: f.result() for name, f in futures.items()}
    if all("error" in a for a in answers.values()):
        return jsonify({"error": answers["baseline"]["error"]}), 503
    return jsonify(answers)


if __name__ == "__main__":
    app.run(debug=True, port=5012)
