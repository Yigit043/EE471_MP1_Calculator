// Speech-to-Text page.
// Records from the microphone (or takes an uploaded file), converts the audio in the
// browser to a 16 kHz mono WAV (the format Azure reads directly), sends it to Flask
// (/api/stt) and shows the returned transcription.

const sttStart = document.getElementById("stt-start");
const sttStop = document.getElementById("stt-stop");
const sttFile = document.getElementById("stt-file");
const sttLanguage = document.getElementById("stt-language");
const sttRecording = document.getElementById("stt-recording");
const sttTranscribe = document.getElementById("stt-transcribe");
const sttClear = document.getElementById("stt-clear");
const sttResult = document.getElementById("stt-result");
const sttText = document.getElementById("stt-text");
const sttCopy = document.getElementById("stt-copy");
const sttStatus = document.getElementById("stt-status");

let mediaRecorder = null;
let recordedChunks = [];
let audioBlob = null;     // the audio waiting to be transcribed (recording or upload)

function showStatus(el, message, kind) {
  el.textContent = message;
  el.className = `status status--${kind}`;
  el.hidden = false;
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
// Recording
// ---------------------------------------------------------------------------
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => recordedChunks.push(e.data);
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());          // release the microphone
      audioBlob = new Blob(recordedChunks, { type: mediaRecorder.mimeType });
      sttRecording.hidden = true;
      sttTranscribe.disabled = false;
      showStatus(sttStatus, "Recording ready – press Transcribe Audio.", "busy");
    };
    mediaRecorder.start();
    sttFile.value = "";
    sttStart.disabled = true;
    sttStop.disabled = false;
    sttRecording.hidden = false;
    sttStatus.hidden = true;
  } catch (err) {
    showStatus(sttStatus, `✗ Microphone not available: ${err.message}`, "error");
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
  sttStart.disabled = false;
  sttStop.disabled = true;
}

// ---------------------------------------------------------------------------
// Transcription
// ---------------------------------------------------------------------------
async function transcribe() {
  if (!audioBlob) return;
  sttTranscribe.disabled = true;
  showStatus(sttStatus, "Transcribing…", "busy");

  try {
    const wav = await toWav(audioBlob);
    const form = new FormData();
    form.append("audio", wav, "audio.wav");
    form.append("language", sttLanguage.value);

    const response = await fetch("/api/stt", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);

    sttText.textContent = data.text;
    sttResult.hidden = false;
    showStatus(sttStatus, "✓ Audio transcribed successfully!", "ok");
  } catch (err) {
    showStatus(sttStatus, `✗ ${err.message}`, "error");
  } finally {
    sttTranscribe.disabled = false;
  }
}

function clearStt() {
  audioBlob = null;
  sttFile.value = "";
  sttText.textContent = "";
  sttResult.hidden = true;
  sttStatus.hidden = true;
  sttTranscribe.disabled = true;
}

async function loadLanguages() {
  const response = await fetch("/api/languages");
  for (const [code, label] of await response.json()) {
    const option = document.createElement("option");
    option.value = code;
    option.textContent = label;
    sttLanguage.appendChild(option);
  }
}

sttStart.addEventListener("click", startRecording);
sttStop.addEventListener("click", stopRecording);
sttFile.addEventListener("change", () => {
  audioBlob = sttFile.files[0] || null;
  sttTranscribe.disabled = !audioBlob;
  if (audioBlob) showStatus(sttStatus, `File selected: ${audioBlob.name}`, "busy");
});
sttTranscribe.addEventListener("click", transcribe);
sttClear.addEventListener("click", clearStt);
sttCopy.addEventListener("click", () => navigator.clipboard.writeText(sttText.textContent));
loadLanguages();
