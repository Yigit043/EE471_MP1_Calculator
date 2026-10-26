// Azure Speech website.
// Every tab sends its data to the Flask backend (app.py); all speech work happens on Azure.
// Audio (microphone recordings and uploaded files) is converted in the browser to a
// 16 kHz mono WAV before it is sent, because that is the format Azure reads directly.

// ===========================================================================
// Shared helpers
// ===========================================================================
const $ = (id) => document.getElementById(id);

function showStatus(el, message, kind) {
  el.textContent = message;
  el.className = `status status--${kind}`;
  el.hidden = false;
}

function fillSelect(select, pairs) {
  for (const [value, label] of pairs) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  }
}

// POST a WAV (+ extra form fields) to an endpoint; return the JSON or throw the API's error.
async function postAudio(url, blob, fields = {}) {
  const form = new FormData();
  form.append("audio", await toWav(blob), "audio.wav");
  for (const [key, value] of Object.entries(fields)) form.append(key, value);
  const response = await fetch(url, { method: "POST", body: form });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

// Run an async task with a busy message and a disabled button; show ok/error at the end.
async function runTask(button, statusEl, busyText, okText, task) {
  button.disabled = true;
  showStatus(statusEl, busyText, "busy");
  try {
    await task();
    showStatus(statusEl, okText, "ok");
  } catch (err) {
    showStatus(statusEl, `✗ ${err.message}`, "error");
  } finally {
    button.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Audio -> 16 kHz mono 16-bit WAV
// ---------------------------------------------------------------------------
async function toWav(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  const decoder = new AudioContext();
  const decoded = await decoder.decodeAudioData(arrayBuffer);   // webm, mp3, wav, ogg ...
  await decoder.close();

  // Resample + mix down to mono with an OfflineAudioContext
  const targetRate = 16000;
  const length = Math.ceil(decoded.duration * targetRate);
  const offline = new OfflineAudioContext(1, length, targetRate);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start();
  const rendered = await offline.startRendering();
  return encodeWav(rendered.getChannelData(0), targetRate);
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset, text) => {
    for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i));
  };
  writeText(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE");
  writeText(12, "fmt ");
  view.setUint32(16, 16, true);          // fmt chunk size
  view.setUint16(20, 1, true);           // PCM
  view.setUint16(22, 1, true);           // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);          // 16-bit
  writeText(36, "data");
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (const s of samples) {
    const clipped = Math.max(-1, Math.min(1, s));
    view.setInt16(offset, clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff, true);
    offset += 2;
  }
  return new Blob([view], { type: "audio/wav" });
}

// ---------------------------------------------------------------------------
// Reusable "record or upload" control. Every audio tab has the same four elements:
// <prefix>-start, <prefix>-stop, <prefix>-file, <prefix>-recording, and a <prefix>-run button.
// ---------------------------------------------------------------------------
function createAudioInput(prefix, statusEl) {
  const start = $(`${prefix}-start`);
  const stop = $(`${prefix}-stop`);
  const file = $(`${prefix}-file`);
  const recording = $(`${prefix}-recording`);
  const run = $(`${prefix}-run`);
  let recorder = null;
  let chunks = [];
  const input = { blob: null };

  input.set = (blob, message) => {
    input.blob = blob;
    run.disabled = !blob;
    if (blob && message) showStatus(statusEl, message, "busy");
  };

  start.addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());          // release the microphone
        recording.hidden = true;
        input.set(new Blob(chunks, { type: recorder.mimeType }), "Recording ready.");
      };
      recorder.start();
      file.value = "";
      start.disabled = true;
      stop.disabled = false;
      recording.hidden = false;
      statusEl.hidden = true;
    } catch (err) {
      showStatus(statusEl, `✗ Microphone not available: ${err.message}`, "error");
    }
  });

  stop.addEventListener("click", () => {
    if (recorder && recorder.state === "recording") recorder.stop();
    start.disabled = false;
    stop.disabled = true;
  });

  file.addEventListener("change", () => {
    const chosen = file.files[0] || null;
    input.set(chosen, chosen ? `File selected: ${chosen.name}` : null);
  });

  input.clear = () => {
    file.value = "";
    input.set(null);
    statusEl.hidden = true;
  };
  return input;
}

// ===========================================================================
// Tabs
// ===========================================================================
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("is-active", t === tab));
    document.querySelectorAll(".panel").forEach((panel) => {
      panel.hidden = panel.id !== `panel-${tab.dataset.tab}`;
    });
  });
});

// ===========================================================================
// TEXT TO SPEECH (Part 1)
// ===========================================================================
let ttsUrl = null;   // object URL of the last generated WAV

async function fetchSpeech(text, voice) {
  const response = await fetch("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return response.blob();                            // the WAV bytes
}

$("tts-speak").addEventListener("click", () =>
  runTask($("tts-speak"), $("tts-status"), "Synthesizing…", "✓ Speech synthesized successfully!",
    async () => {
      const blob = await fetchSpeech($("tts-text").value, $("tts-voice").value);
      if (ttsUrl) URL.revokeObjectURL(ttsUrl);
      ttsUrl = URL.createObjectURL(blob);
      $("tts-audio").src = ttsUrl;
      $("tts-download").href = ttsUrl;
      $("tts-result").hidden = false;
      $("tts-audio").play();
    }));

$("tts-clear").addEventListener("click", () => {
  $("tts-text").value = "";
  $("tts-status").hidden = true;
  $("tts-result").hidden = true;
  $("tts-audio").removeAttribute("src");
});

// ===========================================================================
// SPEECH TO TEXT (Part 2)
// ===========================================================================
const sttInput = createAudioInput("stt", $("stt-status"));

$("stt-run").addEventListener("click", () =>
  runTask($("stt-run"), $("stt-status"), "Transcribing…", "✓ Audio transcribed successfully!",
    async () => {
      const data = await postAudio("/api/stt", sttInput.blob, { language: $("stt-language").value });
      $("stt-text").textContent = data.text;
      $("stt-result").hidden = false;
    }));

$("stt-clear").addEventListener("click", () => {
  sttInput.clear();
  $("stt-text").textContent = "";
  $("stt-result").hidden = true;
});
$("stt-copy").addEventListener("click", () => navigator.clipboard.writeText($("stt-text").textContent));

// ===========================================================================
// DIARIZATION (Part 4)
// ===========================================================================
const diaInput = createAudioInput("dia", $("dia-status"));
const SPEAKER_COLORS = ["#667eea", "#e67e22", "#16a085", "#c0392b", "#8e44ad"];

$("dia-sample").addEventListener("click", () =>
  runTask($("dia-sample"), $("dia-status"), "Generating conversation…",
    "✓ Sample ready – listen to it, then press Identify Speakers.",
    async () => {
      const response = await fetch("/api/sample-conversation", { method: "POST" });
      if (!response.ok) throw new Error((await response.json()).error);
      const blob = await response.blob();
      diaInput.set(blob);
      $("dia-audio").src = URL.createObjectURL(blob);
      $("dia-audio").hidden = false;
    }));

$("dia-run").addEventListener("click", () =>
  runTask($("dia-run"), $("dia-status"), "Identifying speakers…", "✓ Diarization finished!",
    async () => {
      const data = await postAudio("/api/diarize", diaInput.blob, { language: $("dia-language").value });
      const colors = {};
      const box = $("dia-segments");
      box.innerHTML = "";
      for (const seg of data.segments) {
        if (!(seg.speaker in colors)) {
          colors[seg.speaker] = SPEAKER_COLORS[Object.keys(colors).length % SPEAKER_COLORS.length];
        }
        const row = document.createElement("div");
        row.className = "segment";
        const who = document.createElement("span");
        who.className = "speaker";
        who.style.background = colors[seg.speaker];
        who.textContent = seg.speaker;
        const said = document.createElement("p");
        said.textContent = seg.text;
        row.append(who, said);
        box.appendChild(row);
      }
      $("dia-result").hidden = false;
    }));

$("dia-clear").addEventListener("click", () => {
  diaInput.clear();
  $("dia-segments").innerHTML = "";
  $("dia-result").hidden = true;
  $("dia-audio").hidden = true;
});

// ===========================================================================
// TRANSLATION (Part 4)
// ===========================================================================
const trInput = createAudioInput("tr", $("tr-status"));
let trVoice = null;   // voice suggested by the server for the target language

$("tr-run").addEventListener("click", () =>
  runTask($("tr-run"), $("tr-status"), "Translating…", "✓ Translation finished!",
    async () => {
      const data = await postAudio("/api/translate", trInput.blob, {
        source: $("tr-source").value,
        target: $("tr-target").value,
      });
      $("tr-original").textContent = data.original;
      $("tr-translation").textContent = data.translation;
      trVoice = data.voice;
      $("tr-result").hidden = false;
    }));

// Reuses the Part 1 text-to-speech endpoint to read the translation aloud
$("tr-speak").addEventListener("click", () =>
  runTask($("tr-speak"), $("tr-status"), "Synthesizing translation…", "✓ Playing translation.",
    async () => {
      const blob = await fetchSpeech($("tr-translation").textContent, trVoice);
      $("tr-audio").src = URL.createObjectURL(blob);
      await $("tr-audio").play();
    }));

$("tr-clear").addEventListener("click", () => {
  trInput.clear();
  $("tr-original").textContent = "";
  $("tr-translation").textContent = "";
  $("tr-result").hidden = true;
});

// ===========================================================================
// PRONUNCIATION ASSESSMENT (Part 4)
// ===========================================================================
const paInput = createAudioInput("pa", $("pa-status"));

function wordClass(word) {
  if (word.error === "Omission") return "word--omission";
  if (word.error === "Insertion") return "word--insertion";
  if (word.accuracy >= 80) return "word--good";
  if (word.accuracy >= 60) return "word--ok";
  return "word--bad";
}

$("pa-run").addEventListener("click", () =>
  runTask($("pa-run"), $("pa-status"), "Assessing pronunciation…", "✓ Assessment finished!",
    async () => {
      const data = await postAudio("/api/pronunciation", paInput.blob, {
        reference: $("pa-reference").value,
        language: $("pa-language").value,
      });

      const scores = [
        ["Pronunciation", data.pronunciation],
        ["Accuracy", data.accuracy],
        ["Fluency", data.fluency],
        ["Completeness", data.completeness],
        ["Prosody", data.prosody],
      ];
      const scoreBox = $("pa-scores");
      scoreBox.innerHTML = "";
      for (const [name, value] of scores) {
        if (value === null || value === undefined) continue;      // prosody: en-US only
        const card = document.createElement("div");
        card.className = "score";
        card.innerHTML = `<b>${Math.round(value)}</b><span>${name}</span>`;
        scoreBox.appendChild(card);
      }

      const wordBox = $("pa-words");
      wordBox.innerHTML = "";
      for (const w of data.words) {
        const chip = document.createElement("span");
        chip.className = `word ${wordClass(w)}`;
        chip.textContent = w.word;
        const small = document.createElement("small");
        small.textContent = w.error === "None" ? Math.round(w.accuracy) : w.error;
        chip.appendChild(small);
        wordBox.appendChild(chip);
      }
      $("pa-result").hidden = false;
    }));

$("pa-clear").addEventListener("click", () => {
  paInput.clear();
  $("pa-scores").innerHTML = "";
  $("pa-words").innerHTML = "";
  $("pa-result").hidden = true;
});

// ===========================================================================
// Start-up: fill every dropdown from the server
// ===========================================================================
(async () => {
  const options = await (await fetch("/api/options")).json();
  fillSelect($("tts-voice"), options.voices);
  for (const id of ["stt-language", "dia-language", "tr-source"]) fillSelect($(id), options.languages);
  fillSelect($("tr-target"), options.targets);
  fillSelect($("pa-language"), options.pronunciation);
})();
