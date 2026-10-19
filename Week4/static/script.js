// All arithmetic happens on the Flask server (POST /api/calculate).
// This file only collects key presses and shows what the server returns.

const display = document.getElementById("display");

let current = "0";      // digits being typed right now
let firstOperand = null; // number waiting on the left side of the operator
let operator = null;     // "+", "-", "*" or "/"
let justEvaluated = false;

function show(text, isError = false) {
  display.textContent = text;
  display.classList.toggle("is-error", isError);
}

function reset() {
  current = "0";
  firstOperand = null;
  operator = null;
  justEvaluated = false;
  show("0");
}

async function callApi(a, op, b) {
  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ a, op, b }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Unknown error");
  }
  return data.result;
}

function pressDigit(digit) {
  if (justEvaluated) {          // start a fresh number after "="
    current = "0";
    justEvaluated = false;
  }
  if (digit === "." && current.includes(".")) return;
  current = current === "0" && digit !== "." ? digit : current + digit;
  show(current);
}

async function pressOperator(op) {
  // Chained input like 2 + 3 * : evaluate "2 + 3" first, then wait for the next number.
  if (operator !== null && !justEvaluated) {
    try {
      const result = await callApi(firstOperand, operator, Number(current));
      firstOperand = result;
      show(String(result));
    } catch (err) {
      show(err.message, true);
      firstOperand = null;
      operator = null;
      current = "0";
      return;
    }
  } else {
    firstOperand = Number(current);
  }
  operator = op;
  current = "0";
  justEvaluated = false;
}

async function pressEquals() {
  if (operator === null || firstOperand === null) return;
  try {
    const result = await callApi(firstOperand, operator, Number(current));
    show(String(result));
    current = String(result);
  } catch (err) {
    show(err.message, true);
    current = "0";
  }
  firstOperand = null;
  operator = null;
  justEvaluated = true;
}

document.querySelectorAll(".key").forEach((key) => {
  key.addEventListener("click", () => {
    if (key.dataset.digit !== undefined) pressDigit(key.dataset.digit);
    else if (key.dataset.op !== undefined) pressOperator(key.dataset.op);
    else if (key.dataset.action === "equals") pressEquals();
  });
});

// Keyboard support: digits, . + - * / Enter Escape
document.addEventListener("keydown", (event) => {
  const k = event.key;
  if (/^[0-9.]$/.test(k)) pressDigit(k);
  else if (["+", "-", "*", "/"].includes(k)) pressOperator(k);
  else if (k === "Enter" || k === "=") pressEquals();
  else if (k === "Escape") reset();
});
