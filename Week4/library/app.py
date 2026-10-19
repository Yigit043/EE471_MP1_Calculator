"""Flask REST API for the library (Week 4, Section 2 - Part 3/4).

The routes only translate HTTP <-> LibraryCollection method calls.
All business rules (ids, availability, editable fields) live in custom_classes.py.

Every response is JSON. Errors look like {"error": "<message>"}.
"""

from flask import Flask, jsonify, request, send_from_directory

from custom_classes import LibraryCollection, Book, DVD, ItemNotFoundError, ItemStateError

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


if __name__ == "__main__":
    app.run(debug=True)            # macOS: app.run(debug=True, port=5001)
