import { callApi } from "./api-client.js";
import { getApiBase, getApiKey, saveSettings } from "./config.js";
import { TEST_SECTIONS } from "./tests-catalog.js";

const els = {
  base: document.getElementById("apiBase"),
  key: document.getElementById("apiKey"),
  saveBtn: document.getElementById("saveSettings"),
  tabs: document.getElementById("tabs"),
  panels: document.getElementById("panels"),
  globalStatus: document.getElementById("globalStatus"),
};

function initSettings() {
  els.base.value = getApiBase();
  els.key.value = getApiKey();
  els.saveBtn.addEventListener("click", () => {
    saveSettings(els.base.value, els.key.value);
    flashStatus("Definições guardadas.", "ok");
  });
}

function flashStatus(msg, type = "info") {
  els.globalStatus.textContent = msg;
  els.globalStatus.className = `status-banner ${type}`;
}

function renderTests() {
  TEST_SECTIONS.forEach((section, i) => {
    const tabBtn = document.createElement("button");
    tabBtn.type = "button";
    tabBtn.className = `tab-btn${i === 0 ? " active" : ""}`;
    tabBtn.textContent = section.label;
    tabBtn.dataset.tab = section.id;
    els.tabs.appendChild(tabBtn);

    const panel = document.createElement("section");
    panel.className = `panel${i === 0 ? " active" : ""}`;
    panel.id = `panel-${section.id}`;

    section.tests.forEach((test) => {
      panel.appendChild(createTestCard(test));
    });
    els.panels.appendChild(panel);
  });

  els.tabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab-btn");
    if (!btn) return;
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");
  });
}

function createTestCard(test) {
  const card = document.createElement("article");
  card.className = "test-card";
  card.innerHTML = `
    <div class="test-head">
      <h3>${test.title}</h3>
      <span class="badge ${test.needsKey === false ? "badge-public" : ""}">${test.needsKey === false ? "público" : "API key"}</span>
    </div>
    <p class="purpose">${test.purpose}</p>
    <code class="path">${test.path}</code>
    <div class="test-actions">
      <button type="button" class="btn btn-run">Testar</button>
      <button type="button" class="btn btn-ghost btn-open">Abrir URL</button>
    </div>
    <div class="result hidden">
      <div class="result-meta"></div>
      <pre class="result-body"></pre>
    </div>
  `;

  const runBtn = card.querySelector(".btn-run");
  const openBtn = card.querySelector(".btn-open");
  const result = card.querySelector(".result");
  const meta = card.querySelector(".result-meta");
  const body = card.querySelector(".result-body");

  openBtn.addEventListener("click", () => {
    const base = getApiBase().replace(/\/$/, "");
    let url = base + test.path;
    const key = getApiKey();
    const needsKey = test.needsKey !== false;
    if (needsKey && key) {
      url += (test.path.includes("?") ? "&" : "?") + "api_key=" + encodeURIComponent(key);
    }
    window.open(url, "_blank");
  });

  runBtn.addEventListener("click", async () => {
    saveSettings(els.base.value, els.key.value);
    if (test.openInTab) {
      openBtn.click();
      return;
    }

    runBtn.disabled = true;
    runBtn.textContent = "A testar…";
    result.classList.remove("hidden", "ok", "err");
    meta.textContent = "A aguardar resposta…";
    body.textContent = "";

    const out = await callApi(test.path, { needsKey: test.needsKey !== false });

    runBtn.disabled = false;
    runBtn.textContent = "Testar";
    result.classList.add(out.ok ? "ok" : "err");
    meta.textContent = `${out.status} · ${out.ms} ms · ${out.url}`;
    body.textContent =
      typeof out.data === "string"
        ? out.data
        : JSON.stringify(out.data, null, 2);
  });

  return card;
}

initSettings();
renderTests();
