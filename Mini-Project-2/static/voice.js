// Mini Project 2 – voice librarian.
// 1. The microphone button starts Azure speech recognition in the browser (Azure Speech JS SDK,
//    with a short-lived token from GET /api/speech-token – the key never reaches the browser).
// 2. Every recognised sentence goes to POST /api/voice. The server turns it into one of the
//    eight REST calls (e.g. "check out item 3" -> POST /api/items/3/checkout) and returns the
//    librarian's sentence.
// 3. The sentence is spoken with Azure TTS (POST /api/speak) and the item list is reloaded.

const micBtn = document.getElementById("mic");
const voiceStatus = document.getElementById("voice-status");
const voiceForm = document.getElementById("voice-form");
const voiceText = document.getElementById("voice-text");
const voiceLog = document.getElementById("voice-log");

let recognizer = null;
let tokenTimer = null;
let speakingUntil = 0;          // while the librarian talks, the microphone ignores what it hears
let speechQueue = Promise.resolve();

// ---------------------------------------------------------------------------
// The librarian's voice
// ---------------------------------------------------------------------------
function say(text) {
  const audioPromise = fetch("/api/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then(async (r) => {
    if (!r.ok) throw new Error((await r.json()).error);
    return URL.createObjectURL(await r.blob());
  });

  // One answer after another, never on top of each other
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
      speakingUntil = Date.now() + 500;
    }
  });
  return speechQueue;
}

// ---------------------------------------------------------------------------
// One voice command: text -> /api/voice -> log + speech + refresh the list
// ---------------------------------------------------------------------------
function addLogEntry(result) {
  const li = document.createElement("li");
  const heard = document.createElement("div");
  heard.className = "voice__heard";
  heard.textContent = `🗣️ “${result.heard}”`;
  li.appendChild(heard);

  if (result.request) {
    const call = document.createElement("div");
    call.className = "voice__call";
    const ok = result.status >= 200 && result.status < 300;
    call.innerHTML = `→ <b></b> <span class="${ok ? "code-ok" : "code-err"}">${result.status}</span>`;
    call.querySelector("b").textContent = `${result.request.method} ${result.request.path}`;
    li.appendChild(call);
  }

  const reply = document.createElement("div");
  reply.className = "voice__reply";
  reply.textContent = `📚 ${result.reply}`;
  li.appendChild(reply);
  voiceLog.prepend(li);                     // newest on top
}

async function runCommand(text) {
  voiceStatus.textContent = `Heard: “${text}”`;
  try {
    const response = await fetch("/api/voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    addLogEntry(result);
    if (typeof loadItems === "function") loadItems();      // refresh the list (script.js)
    await say(result.reply);
  } catch (err) {
    voiceStatus.textContent = `✗ ${err.message}`;
  } finally {
    if (recognizer) voiceStatus.textContent = "🎙️ Listening…";
  }
}

// ---------------------------------------------------------------------------
// Microphone: Azure speech recognition in the browser
// ---------------------------------------------------------------------------
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
  // Commands are long ("create item, type book, title …"): allow short pauses inside them
  config.setProperty(SpeechSDK.PropertyId.Speech_SegmentationSilenceTimeoutMs, "1500");

  recognizer = new SpeechSDK.SpeechRecognizer(config, SpeechSDK.AudioConfig.fromDefaultMicrophoneInput());

  // Words the librarian should expect -> better recognition
  SpeechSDK.PhraseListGrammar.fromRecognizer(recognizer).addPhrases([
    "create item", "type book", "type DVD", "title", "author", "pages", "duration", "minutes",
    "check out item", "return item", "delete item", "get item", "list available books",
    "list DVDs", "replace item", "update item", "change item",
  ]);

  recognizer.recognizing = (_s, e) => {
    if (Date.now() >= speakingUntil) voiceStatus.textContent = `🎙️ … ${e.result.text}`;
  };
  recognizer.recognized = (_s, e) => {
    if (e.result.reason !== SpeechSDK.ResultReason.RecognizedSpeech || !e.result.text) return;
    if (Date.now() < speakingUntil) return;                 // that was the librarian talking
    runCommand(e.result.text);
  };
  recognizer.canceled = (_s, e) => {
    voiceStatus.textContent = `✗ ${e.errorDetails || "Recognition stopped"}`;
    stopListening();
  };

  await new Promise((resolve, reject) =>
    recognizer.startContinuousRecognitionAsync(resolve, reject));

  tokenTimer = setInterval(async () => {                    // tokens last 10 minutes
    try { recognizer.authorizationToken = (await getToken()).token; } catch { /* retry later */ }
  }, 9 * 60 * 1000);

  micBtn.classList.add("is-listening");
  micBtn.setAttribute("aria-pressed", "true");
  voiceStatus.textContent = "🎙️ Listening… e.g. “list available books”";
}

function stopListening() {
  clearInterval(tokenTimer);
  if (recognizer) {
    const r = recognizer;
    recognizer = null;
    r.stopContinuousRecognitionAsync(() => r.close(), () => r.close());
  }
  micBtn.classList.remove("is-listening");
  micBtn.setAttribute("aria-pressed", "false");
}

micBtn.addEventListener("click", async () => {
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

// Typed commands use exactly the same path (handy for testing without a microphone)
voiceForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = voiceText.value.trim();
  if (!text) return;
  voiceText.value = "";
  runCommand(text);
});
