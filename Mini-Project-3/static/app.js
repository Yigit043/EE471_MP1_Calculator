// Mini Project 3 - front end: image generation, microphone recording and chat.
const $ = (id) => document.getElementById(id);
const chatHistory = [];                  // [{role: "user" | "assistant", content: "..."}]

async function postJSON(url, body) {
  const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

// ---------------------------------------------------------------- model status
async function checkStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    const ready = s.chat && s.speech && s.image;
    $("status").textContent = ready ? "Models ready" : "Loading models…";
    $("status").className = "status " + (ready ? "ready" : "loading");
    if (!ready) setTimeout(checkStatus, 3000);
  } catch { setTimeout(checkStatus, 3000); }
}
checkStatus();

// ---------------------------------------------------------------- 1) prompt -> image
async function generateImage() {
  const prompt = $("prompt").value.trim();
  if (!prompt) return $("prompt").focus();
  $("generate").disabled = true;
  $("imageBox").classList.add("busy");
  $("imageInfo").textContent = "Generating…";
  $("imageInfo").hidden = false;
  try {
    const data = await postJSON("/api/image", { prompt });
    $("output").src = data.image;
    $("output").hidden = false;
    $("imageHint").hidden = true;
    $("download").href = data.image;
    $("download").hidden = false;
    $("imageInfo").textContent = `Done in ${data.seconds} s`;
  } catch (err) {
    $("imageInfo").textContent = "Error: " + err.message;
  } finally {
    $("generate").disabled = false;
    $("imageBox").classList.remove("busy");
  }
}
$("generate").onclick = generateImage;

// ---------------------------------------------------------------- 2) chat
function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + (role === "user" ? "user" : "bot");
  div.textContent = text;
  if (role === "assistant") {                       // copy a bot answer into the prompt box
    const use = document.createElement("button");
    use.className = "use";
    use.textContent = "↳ Use as image prompt";
    use.onclick = () => { $("prompt").value = text; $("prompt").focus(); };
    div.appendChild(use);
  }
  $("history").appendChild(div);
  $("history").scrollTop = $("history").scrollHeight;
  return div;
}

async function sendMessage() {
  const text = $("message").value.trim();
  if (!text) return;
  $("message").value = "";
  chatHistory.push({ role: "user", content: text });
  addMessage("user", text);
  const typing = addMessage("typing", "Thinking…");
  typing.classList.add("typing");
  $("send").disabled = true;
  try {
    const data = await postJSON("/api/chat", { history: chatHistory });
    chatHistory.push({ role: "assistant", content: data.reply });
    typing.remove();
    addMessage("assistant", data.reply);
  } catch (err) {
    typing.textContent = "Error: " + err.message;
  } finally {
    $("send").disabled = false;
  }
}
$("send").onclick = sendMessage;
$("message").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ---------------------------------------------------------------- 3) microphone -> text
// The browser records raw samples with the Web Audio API and we pack them into a WAV file,
// so the server can read it without ffmpeg.
let recorder = null;

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const ctx = new AudioContext();
  const source = ctx.createMediaStreamSource(stream);
  const node = ctx.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  node.onaudioprocess = (e) => chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
  source.connect(node);
  node.connect(ctx.destination);
  recorder = { stream, ctx, source, node, chunks };
  $("mic").classList.add("recording");
  $("chatInfo").textContent = "Listening… press the mic again to stop.";
}

async function stopRecording() {
  const { stream, ctx, source, node, chunks } = recorder;
  recorder = null;
  source.disconnect(); node.disconnect();
  stream.getTracks().forEach((t) => t.stop());
  await ctx.close();
  $("mic").classList.remove("recording");
  $("chatInfo").textContent = "Converting speech to text…";
  $("mic").disabled = true;
  try {
    const form = new FormData();
    form.append("audio", encodeWav(chunks, ctx.sampleRate), "speech.wav");
    const res = await fetch("/api/transcribe", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    $("message").value = data.text;
    $("chatInfo").textContent = data.text ? "Check the text, then press Send." : "I did not hear anything, try again.";
  } catch (err) {
    $("chatInfo").textContent = "Error: " + err.message;
  } finally {
    $("mic").disabled = false;
  }
}

function encodeWav(chunks, sampleRate) {
  const length = chunks.reduce((n, c) => n + c.length, 0);
  const buffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(buffer);
  const text = (offset, s) => [...s].forEach((ch, i) => view.setUint8(offset + i, ch.charCodeAt(0)));
  text(0, "RIFF"); view.setUint32(4, 36 + length * 2, true); text(8, "WAVE");
  text(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);      // PCM
  view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true);                // mono
  view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  text(36, "data"); view.setUint32(40, length * 2, true);
  let offset = 44;
  for (const chunk of chunks) for (const x of chunk) {
    view.setInt16(offset, Math.max(-1, Math.min(1, x)) * 0x7fff, true);
    offset += 2;
  }
  return new Blob([view], { type: "audio/wav" });
}

$("mic").onclick = async () => {
  try {
    recorder ? await stopRecording() : await startRecording();
  } catch (err) {
    $("chatInfo").textContent = "Microphone error: " + err.message;
    $("mic").classList.remove("recording");
  }
};
