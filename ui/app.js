// Plain vanilla JS front end for the Enterprise Vision RAG API.
// No build step, no framework. Talks to the FastAPI backend on the same origin.

const API_BASE = "";
const sessionId = "session-" + Math.random().toString(36).slice(2, 10);

const statusIndicator = document.getElementById("status-indicator");
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const uploadResult = document.getElementById("upload-result");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatWindow = document.getElementById("chat-window");

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      statusIndicator.textContent = "backend online";
      statusIndicator.className = "status online";
    } else {
      throw new Error("not ok");
    }
  } catch (err) {
    statusIndicator.textContent = "backend offline";
    statusIndicator.className = "status offline";
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;

  uploadResult.textContent = "Uploading and indexing...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      uploadResult.innerHTML = `<span class="error-text">${data.detail || "Upload failed"}</span>`;
      return;
    }
    uploadResult.innerHTML = `Indexed <strong>${data.filename}</strong> into ${data.chunk_count} chunks (status: ${data.status}).`;
    if (data.warnings && data.warnings.length) {
      uploadResult.innerHTML += `<br><span class="error-text">Warnings: ${data.warnings.join(", ")}</span>`;
    }
  } catch (err) {
    uploadResult.innerHTML = `<span class="error-text">${err}</span>`;
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = searchInput.value.trim();
  if (!query) return;

  searchResults.textContent = "Searching...";

  try {
    const response = await fetch(`${API_BASE}/documents/search?query=${encodeURIComponent(query)}&top_k=5`);
    const data = await response.json();
    if (!response.ok) {
      searchResults.innerHTML = `<span class="error-text">${data.detail || "Search failed"}</span>`;
      return;
    }
    if (!data.results.length) {
      searchResults.textContent = "No results found.";
      return;
    }
    searchResults.innerHTML = data.results
      .map(
        (r) => `
        <div class="result-item">
          <div class="score">score: ${r.score.toFixed(3)} - document: ${r.metadata.filename || r.metadata.document_id}</div>
          <div>${escapeHtml(r.text).slice(0, 400)}</div>
        </div>`
      )
      .join("");
  } catch (err) {
    searchResults.innerHTML = `<span class="error-text">${err}</span>`;
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  chatInput.value = "";

  const thinkingId = appendMessage("assistant", "Thinking...");

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    const data = await response.json();

    if (!response.ok) {
      updateMessage(thinkingId, `Error: ${data.detail || "request failed"}`);
      return;
    }

    let html = escapeHtml(data.answer);
    if (data.citations && data.citations.length) {
      html += `<div class="citations">Sources: ${data.citations.map((c) => c.chunk_id.slice(0, 8)).join(", ")}</div>`;
    }
    html += `<span class="meta">via ${data.used_provider}${data.guardrail_flags.length ? " - flags: " + data.guardrail_flags.join(", ") : ""}</span>`;
    updateMessage(thinkingId, html, true);
  } catch (err) {
    updateMessage(thinkingId, `Error: ${err}`);
  }
});

function appendMessage(role, text) {
  const div = document.createElement("div");
  const id = "msg-" + Date.now() + "-" + Math.random().toString(36).slice(2, 6);
  div.id = id;
  div.className = `message ${role}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return id;
}

function updateMessage(id, html, isHtml = false) {
  const el = document.getElementById(id);
  if (!el) return;
  if (isHtml) {
    el.innerHTML = html;
  } else {
    el.textContent = html;
  }
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

checkHealth();
setInterval(checkHealth, 15000);
