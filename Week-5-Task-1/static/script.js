// Text-to-Speech page: sends the text to Flask (/api/tts), plays and offers the WAV it returns.

const ttsText = document.getElementById("tts-text");
const ttsVoice = document.getElementById("tts-voice");
const ttsSpeak = document.getElementById("tts-speak");
const ttsClear = document.getElementById("tts-clear");
const ttsStatus = document.getElementById("tts-status");
const ttsResult = document.getElementById("tts-result");
const ttsAudio = document.getElementById("tts-audio");
const ttsDownload = document.getElementById("tts-download");

let audioUrl = null;   // object URL of the last generated WAV

function showStatus(el, message, kind) {
  el.textContent = message;
  el.className = `status status--${kind}`;
  el.hidden = false;
}

// Fill the voice dropdown from the server
async function loadVoices() {
  const response = await fetch("/api/voices");
  const voices = await response.json();
  for (const [id, label] of voices) {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = label;
    ttsVoice.appendChild(option);
  }
}

async function synthesize() {
  ttsSpeak.disabled = true;
  showStatus(ttsStatus, "Synthesizing…", "busy");

  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: ttsText.value, voice: ttsVoice.value }),
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    const blob = await response.blob();               // the WAV bytes
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = URL.createObjectURL(blob);
    ttsAudio.src = audioUrl;
    ttsDownload.href = audioUrl;
    ttsResult.hidden = false;
    ttsAudio.play();
    showStatus(ttsStatus, "✓ Speech synthesized successfully!", "ok");
  } catch (err) {
    showStatus(ttsStatus, `✗ ${err.message}`, "error");
  } finally {
    ttsSpeak.disabled = false;
  }
}

function clearTts() {
  ttsText.value = "";
  ttsStatus.hidden = true;
  ttsResult.hidden = true;
  ttsAudio.removeAttribute("src");
}

ttsSpeak.addEventListener("click", synthesize);
ttsClear.addEventListener("click", clearTts);
loadVoices();
