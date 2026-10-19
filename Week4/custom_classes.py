class Calculator:
    """Calculator class from Mini Project 1, extended for the Week 4 web app."""

    # Operator symbols accepted from the web page / API, mapped to a method name.
    OPERATIONS = {
        "+": "add",
        "-": "subtract",
        "*": "multiply",
        "/": "divide",
    }

    def __init__(self):
        self._current_val = 0

    def add(self, x, y):
        self._current_val = x + y
        return self._current_val

    def subtract(self, x, y):
        self._current_val = x - y
        return self._current_val

    def multiply(self, x, y):
        self._current_val = x * y
        return self._current_val

    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero")
        self._current_val = x / y
        return self._current_val

    # --- Week 4 extension -------------------------------------------------
    def calculate(self, a, op, b):
        """Run one operation chosen by its symbol. Raises ValueError on bad input."""
        if op not in self.OPERATIONS:
            raise ValueError(f"Unknown operator: {op!r}")
        method = getattr(self, self.OPERATIONS[op])
        return method(a, b)
