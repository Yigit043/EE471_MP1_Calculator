// Frontend for the library app. All data lives on the server; this file only
// calls the REST API (library/app.py) and renders what comes back.
// No availability / validation logic is duplicated here.

const API = "/api/items";

const els = {
  error: document.getElementById("error-area"),
  list: document.getElementById("item-list"),
  empty: document.getElementById("empty-state"),
  filterAvailable: document.getElementById("filter-available"),
  filterType: document.getElementById("filter-type"),
  form: document.getElementById("item-form"),
  formTitle: document.getElementById("form-title"),
  fTitle: document.getElementById("f-title"),
  fAuthor: document.getElementById("f-author"),
  fType: document.getElementById("f-type"),
  fExtra: document.getElementById("f-extra"),
  fSubmit: document.getElementById("f-submit"),
  fCancel: document.getElementById("f-cancel"),
};

let typeFilter = "";      // "", "book" or "dvd"
let editingId = null;     // null = add mode, number = edit mode

// ---------------------------------------------------------------------------
// API helper: every request goes through here; non-2xx -> throws the API's
// {"error": "..."} message so the caller can show it in the error area.
// ---------------------------------------------------------------------------
async function api(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(path, options);
  if (response.status === 204) return null;            // DELETE success has no body
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

function showError(message) {
  els.error.textContent = message;
  els.error.hidden = false;
}

function clearError() {
  els.error.hidden = true;
  els.error.textContent = "";
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
async function loadItems() {
  const params = new URLSearchParams();
  if (els.filterAvailable.checked) params.set("available", "true");
  if (typeFilter) params.set("type", typeFilter);
  const query = params.toString() ? `?${params}` : "";

  try {
    const items = await api("GET", API + query);
    renderItems(items);
  } catch (err) {
    showError(err.message);
  }
}

function renderItems(items) {
  els.list.innerHTML = "";
  els.empty.hidden = items.length > 0;

  for (const item of items) {
    const row = document.createElement("div");
    row.className = "item";
    const extra = item.type === "book" ? `${item.page_count} pages` : `${item.duration} min`;
    const typeLabel = item.type === "book" ? "Book" : "DVD";

    row.innerHTML = `
      <span class="item__title"></span>
      <span class="item__author"></span>
      <span class="chip">${typeLabel}</span>
      <span class="item__extra">${extra}</span>
      <span class="badge ${item.is_available ? "badge--available" : "badge--out"}">
        ${item.is_available ? "Available" : "Checked out"}
      </span>
      <span class="item__actions">
        <button class="btn ${item.is_available ? "btn--primary" : "btn--return"}" data-action="toggle">
          ${item.is_available ? "Checkout" : "Return"}
        </button>
        <button class="btn btn--icon" data-action="edit" title="Edit">✎</button>
        <button class="btn btn--icon" data-action="delete" title="Delete">🗑</button>
      </span>`;

    // textContent (not innerHTML) for user-entered strings
    row.querySelector(".item__title").textContent = item.title;
    row.querySelector(".item__author").textContent = item.author;

    row.querySelector('[data-action="toggle"]').onclick = () => toggleItem(item);
    row.querySelector('[data-action="edit"]').onclick = () => startEdit(item);
    row.querySelector('[data-action="delete"]').onclick = () => deleteItem(item);
    els.list.appendChild(row);
  }
}

// ---------------------------------------------------------------------------
// Actions (each one: call API -> on success reload list, on error show message)
// ---------------------------------------------------------------------------
async function toggleItem(item) {
  clearError();
  const action = item.is_available ? "checkout" : "return";
  try {
    await api("POST", `${API}/${item.id}/${action}`);
    await loadItems();
  } catch (err) {
    showError(err.message);          // e.g. 409 "already checked out"
  }
}

async function deleteItem(item) {
  clearError();
  try {
    await api("DELETE", `${API}/${item.id}`);
    await loadItems();
  } catch (err) {
    showError(err.message);          // 409 "Cannot delete ...: it is checked out"
  }
}

function startEdit(item) {
  clearError();
  editingId = item.id;
  els.formTitle.textContent = `Edit item #${item.id}`;
  els.fTitle.value = item.title;
  els.fAuthor.value = item.author;
  els.fType.value = item.type;
  els.fType.disabled = true;         // type is not editable (API rule)
  updateExtraField();
  els.fExtra.value = item.type === "book" ? item.page_count : item.duration;
  els.fSubmit.textContent = "Save";
  els.fCancel.hidden = false;
  els.fTitle.focus();
}

function resetForm() {
  editingId = null;
  els.form.reset();
  els.fType.disabled = false;
  els.formTitle.textContent = "Add item";
  els.fSubmit.textContent = "Add";
  els.fCancel.hidden = true;
  updateExtraField();
}

// The last field switches between "Page count" (book) and "Duration (min)" (dvd)
function updateExtraField() {
  els.fExtra.placeholder = els.fType.value === "book" ? "Page count" : "Duration (min)";
}

async function submitForm(event) {
  event.preventDefault();
  clearError();

  const type = els.fType.value;
  const extraKey = type === "book" ? "page_count" : "duration";
  const fields = {
    title: els.fTitle.value,
    author: els.fAuthor.value,
    [extraKey]: Number(els.fExtra.value),
  };

  try {
    if (editingId === null) {
      await api("POST", API, { type, ...fields });               // 201
    } else {
      await api("PUT", `${API}/${editingId}`, fields);            // 200 (all editable fields)
    }
    resetForm();
    await loadItems();
  } catch (err) {
    showError(err.message);          // 400 from the server's validation
  }
}

// ---------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------
els.form.addEventListener("submit", submitForm);
els.fCancel.addEventListener("click", resetForm);
els.fType.addEventListener("change", updateExtraField);
els.filterAvailable.addEventListener("change", loadItems);
els.filterType.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-type]");
  if (!button) return;
  typeFilter = button.dataset.type;
  for (const b of els.filterType.querySelectorAll("button")) {
    b.classList.toggle("is-active", b === button);
  }
  loadItems();
});

updateExtraField();
loadItems();
