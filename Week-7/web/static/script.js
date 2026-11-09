// Week 7 classifier page: send the image once, show both models' answers side by side.
const fileInput = document.getElementById("image");
const preview = document.getElementById("preview");
const dropText = document.getElementById("drop-text");
const classifyBtn = document.getElementById("classify");
const clearBtn = document.getElementById("clear");
const statusBox = document.getElementById("status");
const compare = document.getElementById("compare");
const verdict = document.getElementById("verdict");

function showStatus(text, kind) {
  statusBox.textContent = text;
  statusBox.className = `status status--${kind}`;
  statusBox.hidden = false;
}

function pct(x) {
  return `${(100 * x).toFixed(1)}%`;
}

function describeSettings(s) {
  const arch = Object.entries(s.arch).map(([k, v]) => `${k} ${v}`).join(", ");
  return `${s.optimizer.toUpperCase()}, lr ${s.lr}, batch ${s.batch_size}, ${s.epochs} epochs, ${arch}` +
         (s.augment ? ", augmentation" : "");
}

// Fill one model card (baseline or optimized) with its answer.
function showModel(id, out) {
  const card = document.getElementById(id);
  const meta = card.querySelector(".meta");
  const answer = card.querySelector(".answer");
  const bars = card.querySelector(".bars");
  bars.innerHTML = "";
  if (out.error) {
    meta.textContent = "";
    answer.innerHTML = `<span class="error">${out.error}</span>`;
    return;
  }
  meta.textContent = `Test accuracy ${pct(out.test_accuracy)} · ${describeSettings(out.settings)}`;
  answer.textContent = `${out.predicted_class} (${pct(out.confidence)})`;
  for (const item of out.top3) {
    const row = document.createElement("div");
    row.className = "bar";
    row.innerHTML = `<span>${item.label}</span>
      <div class="bar__track"><div class="bar__fill" style="width:${100 * item.probability}%"></div></div>
      <span class="bar__value">${pct(item.probability)}</span>`;
    bars.appendChild(row);
  }
}

async function loadInfo() {
  const info = await (await fetch("/api/info")).json();
  document.title = info.title;
  document.getElementById("title").textContent = info.title;
  document.getElementById("classes").textContent = `Classes: ${info.classes.join(", ")}`;
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  dropText.hidden = true;
  classifyBtn.disabled = false;
  compare.hidden = true;
  verdict.hidden = true;
  statusBox.hidden = true;
});

classifyBtn.addEventListener("click", async () => {
  const form = new FormData();
  form.append("image", fileInput.files[0]);
  classifyBtn.disabled = true;
  showStatus("⏳ Both models are thinking...", "busy");
  try {
    const response = await fetch("/api/classify", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    showModel("baseline", data.baseline);
    showModel("optimized", data.optimized);
    compare.hidden = false;
    const a = data.baseline.predicted_class, b = data.optimized.predicted_class;
    verdict.textContent = a && b ? (a === b ? `✅ Both models say: ${a}` : `⚖️ The models disagree: ${a} vs ${b}`) : "";
    verdict.hidden = !(a && b);
    showStatus("Done", "ok");
  } catch (err) {
    showStatus(`❌ ${err.message}`, "error");
  } finally {
    classifyBtn.disabled = false;
  }
});

clearBtn.addEventListener("click", () => {
  fileInput.value = "";
  preview.hidden = true;
  dropText.hidden = false;
  classifyBtn.disabled = true;
  compare.hidden = true;
  verdict.hidden = true;
  statusBox.hidden = true;
});

loadInfo();
