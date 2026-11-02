// Cat kind classifier page: shows the chosen photo, sends it to Flask (/api/classify),
// which forwards it to the Cog model container, and draws the answer.

const input = document.getElementById("image");
const preview = document.getElementById("preview");
const dropText = document.getElementById("drop-text");
const classifyBtn = document.getElementById("classify");
const clearBtn = document.getElementById("clear");
const statusEl = document.getElementById("status");
const result = document.getElementById("result");
const answer = document.getElementById("answer");
const bars = document.getElementById("bars");
const detail = document.getElementById("detail");

function showStatus(message, kind) {
  statusEl.textContent = message;
  statusEl.className = `status status--${kind}`;
  statusEl.hidden = false;
}

input.addEventListener("change", () => {
  const file = input.files[0];
  result.hidden = true;
  statusEl.hidden = true;
  classifyBtn.disabled = !file;
  if (!file) return;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  dropText.hidden = true;
});

classifyBtn.addEventListener("click", async () => {
  const form = new FormData();
  form.append("image", input.files[0]);
  classifyBtn.disabled = true;
  showStatus("Classifying… (the first prediction can take a few seconds)", "busy");

  try {
    const response = await fetch("/api/classify", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    drawResult(data);
    showStatus("✓ Classified!", "ok");
  } catch (err) {
    showStatus(`✗ ${err.message}`, "error");
  } finally {
    classifyBtn.disabled = false;
  }
});

function drawResult(data) {
  answer.textContent = data.is_cat ? `🐈 ${data.cat_kind}` : "🤔 This does not look like a cat";
  bars.innerHTML = "";
  if (data.is_cat) {
    for (const item of data.top3) {
      const pct = Math.round(item.probability * 100);
      const row = document.createElement("div");
      row.className = "bar";
      row.innerHTML = `<span></span><div class="bar__track"><div class="bar__fill"></div></div>
                       <span class="bar__value">${pct}%</span>`;
      row.querySelector("span").textContent = item.kind;
      row.querySelector(".bar__fill").style.width = `${pct}%`;
      bars.appendChild(row);
    }
  }
  detail.textContent = `Cat probability: ${Math.round(data.cat_probability * 100)}% · ` +
                       `model's top ImageNet label: "${data.model_top_label}"`;
  result.hidden = false;
}

clearBtn.addEventListener("click", () => {
  input.value = "";
  preview.hidden = true;
  dropText.hidden = false;
  classifyBtn.disabled = true;
  result.hidden = true;
  statusEl.hidden = true;
});
