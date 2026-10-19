from flask import Flask, jsonify, request, send_from_directory

from custom_classes import Calculator

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


if __name__ == "__main__":
    app.run(debug=True)
