// Voice-activated calculator (Week 5 - Task 2).
// - Calculation: same as Week 4, every operation goes to Flask (POST /api/calculate).
// - Voice output: every key press is spoken ("three", "plus", "five", "is eight") with Azure TTS
//   (POST /api/speak).
// - Voice input: the microphone button starts Azure speech recognition in the browser
//   (Azure Speech JS SDK + a short-lived token from GET /api/speech-token). Every recognised
//   word is turned into a key press.

const display = document.getElementById("display");
const micButton = document.getElementById("mic");
const voiceStatus = document.getElementById("voice-status");

// ===========================================================================
// 1. Calculator logic (Week 4)
// ===========================================================================
let current = "0";       // digits being typed right now
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
  if (!response.ok) throw new Error(data.error || "Unknown error");
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

// Returns the text to speak after "=" ("is 8" or the error message)
async function pressEquals() {
  if (operator === null || firstOperand === null) return `is ${current}`;
  let spoken;
  try {
    const result = await callApi(firstOperand, operator, Number(current));
    show(String(result));
    current = String(result);
    spoken = `is ${result}`;
  } catch (err) {
    show(err.message, true);
    current = "0";
    spoken = err.message;
  }
  firstOperand = null;
  operator = null;
  justEvaluated = true;
  return spoken;
}

// ===========================================================================
// 2. Voice output – the "magical" buttons
// ===========================================================================
// Words from the command table in the exercise
const KEY_WORDS = {
  "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
  "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
  ".": "point", "/": "over", "*": "times", "+": "plus", "-": "minus",
};

const audioCache = new Map();   // text -> object URL (each word is fetched from Azure only once)
let speechQueue = Promise.resolve();
let speakingUntil = 0;          // while the calculator talks, the microphone ignores what it hears

async function fetchAudio(text) {
  if (!audioCache.has(text)) {
    const response = await fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) throw new Error((await response.json()).error);
    audioCache.set(text, URL.createObjectURL(await response.blob()));
  }
  return audioCache.get(text);
}

// Queue the phrases so fast key presses are spoken one after another, never on top of each other
function say(text) {
  const audioPromise = fetchAudio(text);      // start downloading right away
  speechQueue = speechQueue.then(async () => {
    try {
      const audio = new Audio(await audioPromise);
      speakingUntil = Infinity;
      await new Promise((resolve) => {
        audio.onended = resolve;
        audio.onerror = resolve;
        audio.play().catch(resolve);
      });
    } catch (err) {
      voiceStatus.textContent = `🔇 ${err.message}`;
    } finally {
      speakingUntil = Date.now() + 400;        // small tail so the echo is not recognised
    }
  });
  return speechQueue;
}

// Pre-load the 15 key words so the first presses are not delayed
function preloadWords() {
  for (const word of Object.values(KEY_WORDS)) fetchAudio(word).catch(() => {});
}

// ===========================================================================
// 3. One entry point for every key, whatever pressed it (mouse, keyboard or voice)
// ===========================================================================
function flash(key) {
  const selector =
    key === "=" ? '[data-action="equals"]'
    : /[0-9.]/.test(key) ? `[data-digit="${key}"]`
    : `[data-op="${key}"]`;
  const button = document.querySelector(selector);
  if (!button) return;
  button.classList.add("is-pressed");
  setTimeout(() => button.classList.remove("is-pressed"), 250);
}

// speakKey: true for mouse/keyboard (every key talks), false for voice (only the result talks,
// so the calculator does not repeat every word the user just said)
async function pressKey(key, speakKey = true) {
  flash(key);
  if (key === "=") {
    const spoken = await pressEquals();
    say(spoken);
    return;
  }
  if (speakKey) say(KEY_WORDS[key]);
  if (/[0-9.]/.test(key)) pressDigit(key);
  else await pressOperator(key);
}

// ===========================================================================
// 4. Voice input – Azure speech recognition in the browser
// ===========================================================================
// Spoken word -> key. Includes words Azure often returns for single numbers ("to", "for").
const COMMANDS = {
  zero: "0", oh: "0", one: "1", won: "1", two: "2", to: "2", too: "2",
  three: "3", four: "4", for: "4", five: "5", six: "6", seven: "7",
  eight: "8", ate: "8", nine: "9",
  point: ".", dot: ".",
  over: "/", divided: "/", divide: "/",
  times: "*", multiplied: "*", multiply: "*", x: "*",
  plus: "+", add: "+",
  minus: "-", subtract: "-",
  is: "=", equals: "=", equal: "=",
};

// "Five plus two is." / "5 + 2 is" / "9 ÷ 3" -> ["5", "+", "2", "="]
function textToKeys(text) {
  const tokens = text.toLowerCase().match(/\d+(?:\.\d+)?|[+\-−×x÷\/*=]|[a-z]+/g) || [];
  const keys = [];
  for (const token of tokens) {
    if (/^\d/.test(token)) keys.push(...token.split(""));          // "12" -> "1", "2"
    else if ("+-−×÷/*=".includes(token)) {
      keys.push({ "−": "-", "×": "*", "÷": "/" }[token] || token);
    } else if (token === "clear" || token === "reset") keys.push("C");
    else if (token in COMMANDS) keys.push(COMMANDS[token]);
    // other words ("by", "the" ...) are ignored
  }
  return keys;
}

let recognizer = null;
let tokenTimer = null;

async function getToken() {
  const response = await fetch("/api/speech-token");
  const data = await response.json();
  if (!response.ok) throw new Error(data.error);
  return data;
}

async function startListening() {
  const { token, region } = await getToken();
  const config = SpeechSDK.SpeechConfig.fromAuthorizationToken(token, region);
  config.speechRecognitionLanguage = "en-US";
  // Short pause = end of a command, so single words are executed quickly
  config.setProperty(SpeechSDK.PropertyId.Speech_SegmentationSilenceTimeoutMs, "500");

  const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
  recognizer = new SpeechSDK.SpeechRecognizer(config, audioConfig);

  // Tell Azure which words to expect -> much better accuracy for single words
  const phrases = SpeechSDK.PhraseListGrammar.fromRecognizer(recognizer);
  phrases.addPhrases(["zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "point", "over", "times", "plus", "minus", "is"]);

  recognizer.recognizing = (_s, e) => {
    voiceStatus.textContent = `🎙️ … ${e.result.text}`;
  };
  recognizer.recognized = async (_s, e) => {
    if (e.result.reason !== SpeechSDK.ResultReason.RecognizedSpeech || !e.result.text) return;
    if (Date.now() < speakingUntil) return;                   // that was the calculator talking
    const keys = textToKeys(e.result.text);
    voiceStatus.textContent = `🎙️ Heard: “${e.result.text}”`;
    for (const key of keys) {
      if (key === "C") reset();
      else await pressKey(key, false);
    }
  };
  recognizer.canceled = (_s, e) => {
    voiceStatus.textContent = `✗ ${e.errorDetails || "Recognition stopped"}`;
    stopListening();
  };

  await new Promise((resolve, reject) =>
    recognizer.startContinuousRecognitionAsync(resolve, reject));

  // Tokens expire after 10 minutes – refresh every 9
  tokenTimer = setInterval(async () => {
    try { recognizer.authorizationToken = (await getToken()).token; } catch { /* next time */ }
  }, 9 * 60 * 1000);

  micButton.classList.add("is-listening");
  micButton.setAttribute("aria-pressed", "true");
  voiceStatus.textContent = "🎙️ Listening… say “five”, “plus”, “two”, “is”.";
}

function stopListening() {
  clearInterval(tokenTimer);
  if (recognizer) {
    const r = recognizer;
    recognizer = null;
    r.stopContinuousRecognitionAsync(() => r.close(), () => r.close());
  }
  micButton.classList.remove("is-listening");
  micButton.setAttribute("aria-pressed", "false");
}

micButton.addEventListener("click", async () => {
  if (recognizer) {
    stopListening();
    voiceStatus.textContent = "🎙️ Microphone off.";
    return;
  }
  try {
    voiceStatus.textContent = "🎙️ Starting…";
    await startListening();
  } catch (err) {
    stopListening();
    voiceStatus.textContent = `✗ ${err.message || err}`;
  }
});

// ===========================================================================
// 5. Mouse and keyboard
// ===========================================================================
document.querySelectorAll(".key").forEach((key) => {
  key.addEventListener("click", () => {
    if (key.dataset.digit !== undefined) pressKey(key.dataset.digit);
    else if (key.dataset.op !== undefined) pressKey(key.dataset.op);
    else if (key.dataset.action === "equals") pressKey("=");
  });
});

document.addEventListener("keydown", (event) => {
  const k = event.key;
  if (/^[0-9.]$/.test(k) || ["+", "-", "*", "/"].includes(k)) pressKey(k);
  else if (k === "Enter" || k === "=") { event.preventDefault(); pressKey("="); }
  else if (k === "Escape") reset();
});

preloadWords();
