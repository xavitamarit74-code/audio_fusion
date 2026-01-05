const API_BASE = ""; // mismo origen

const els = {
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("fileInput"),
  fileList: document.getElementById("fileList"),
  filesMeta: document.getElementById("filesMeta"),

  crossfade: document.getElementById("crossfade"),
  fadeIn: document.getElementById("fadeIn"),
  fadeOut: document.getElementById("fadeOut"),
  normalize: document.getElementById("normalize"),
  format: document.getElementById("format"),

  crossfadeValue: document.getElementById("crossfadeValue"),
  fadeInValue: document.getElementById("fadeInValue"),
  fadeOutValue: document.getElementById("fadeOutValue"),

  previewBtn: document.getElementById("previewBtn"),
  mergeBtn: document.getElementById("mergeBtn"),
  clearBtn: document.getElementById("clearBtn"),
  hardResetBtn: document.getElementById("hardResetBtn"),

  previewProgress: document.getElementById("previewProgress"),
  previewBar: document.getElementById("previewBar"),
  previewStage: document.getElementById("previewStage"),

  mergeProgress: document.getElementById("mergeProgress"),
  mergeBar: document.getElementById("mergeBar"),
  mergeStage: document.getElementById("mergeStage"),

  message: document.getElementById("message"),

  previewPanel: document.getElementById("previewPanel"),
  previewAudio: document.getElementById("previewAudio"),

  resultPanel: document.getElementById("resultPanel"),
  resultAudio: document.getElementById("resultAudio"),
  downloadLink: document.getElementById("downloadLink"),
  resultHint: document.getElementById("resultHint"),
};

let files = []; // {file_id, filename, duration, format, volumeDb}
let messageTimer = null;
let cancelPreviewPoll = null;
let cancelMergePoll = null;
let uiEpoch = 0;

function msToSeconds(ms) {
  return (ms / 1000).toFixed(1);
}

function syncParamLabels() {
  els.crossfadeValue.textContent = msToSeconds(Number(els.crossfade.value));
  els.fadeInValue.textContent = msToSeconds(Number(els.fadeIn.value));
  els.fadeOutValue.textContent = msToSeconds(Number(els.fadeOut.value));
}

function showMessage(text, type = "info") {
  els.message.hidden = false;
  els.message.textContent = text;
  els.message.className = `message message--${type}`;
  if (messageTimer) window.clearTimeout(messageTimer);
  messageTimer = window.setTimeout(() => {
    els.message.hidden = true;
  }, 6000);
}

function cancelAllPolling() {
  if (typeof cancelPreviewPoll === "function") cancelPreviewPoll();
  if (typeof cancelMergePoll === "function") cancelMergePoll();
  cancelPreviewPoll = null;
  cancelMergePoll = null;
}

function clearUIOutputsOnly() {
  els.previewProgress.hidden = true;
  els.previewBar.value = 0;
  els.previewStage.textContent = "Preview";
  els.previewPanel.hidden = true;
  try {
    els.previewAudio.pause();
  } catch (_) {}
  els.previewAudio.removeAttribute("src");
  els.previewAudio.load();

  els.mergeProgress.hidden = true;
  els.mergeBar.value = 0;
  els.mergeStage.textContent = "Fusión";
  els.resultPanel.hidden = true;
  els.downloadLink.href = "#";
  els.resultHint.hidden = true;
  els.resultAudio.hidden = true;
  try {
    els.resultAudio.pause();
  } catch (_) {}
  els.resultAudio.removeAttribute("src");
  els.resultAudio.load();

  els.message.hidden = true;
}

function restoreParamsToDefaults() {
  els.crossfade.value = els.crossfade.defaultValue;
  els.fadeIn.value = els.fadeIn.defaultValue;
  els.fadeOut.value = els.fadeOut.defaultValue;
  els.normalize.checked = els.normalize.defaultChecked;
  els.format.value = els.format.defaultValue;
  syncParamLabels();
}

function setResetButtonsDisabled(disabled) {
  if (els.clearBtn) els.clearBtn.disabled = disabled;
  if (els.hardResetBtn) els.hardResetBtn.disabled = disabled;
  els.previewBtn.disabled = disabled || !canProcess();
  els.mergeBtn.disabled = disabled || !canProcess();
}

async function callResetEndpoint(mode) {
  const res = await fetch(`${API_BASE}/v1/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });

  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || "Error en reset");
  }
}

async function handleSoftClear() {
  const needsConfirm = files.length > 0 || !els.previewProgress.hidden || !els.mergeProgress.hidden;
  if (needsConfirm) {
    const ok = window.confirm(
      "Esto borrará archivos subidos y resultados del servidor. ¿Continuar?"
    );
    if (!ok) return;
  }

  uiEpoch += 1;
  cancelAllPolling();
  setResetButtonsDisabled(true);
  showMessage("Limpiando archivos/resultados...", "info");

  try {
    await callResetEndpoint("soft");
  } catch (e) {
    showMessage(`No se pudo limpiar en servidor: ${String(e.message || e)}`, "error");
  }

  files = [];
  renderList();
  clearUIOutputsOnly();
  showMessage("✓ Limpieza completada", "success");
  setResetButtonsDisabled(false);
}

async function handleHardReset() {
  const ok = window.confirm(
    "RESET: borrará archivos/resultados y restaurará los parámetros. ¿Continuar?"
  );
  if (!ok) return;

  uiEpoch += 1;
  cancelAllPolling();
  setResetButtonsDisabled(true);
  showMessage("Haciendo reset fuerte...", "info");

  try {
    await callResetEndpoint("hard");
  } catch (e) {
    showMessage(`No se pudo resetear en servidor: ${String(e.message || e)}`, "error");
  }

  files = [];
  renderList();
  restoreParamsToDefaults();
  clearUIOutputsOnly();
  showMessage("✓ Reset fuerte completado", "success");
  setResetButtonsDisabled(false);
}

function paramsFromUI() {
  return {
    crossfade_ms: Number(els.crossfade.value),
    fade_in_ms: Number(els.fadeIn.value),
    fade_out_ms: Number(els.fadeOut.value),
    normalizar: Boolean(els.normalize.checked),
    volumenes: files.map((f) => Number(f.volumeDb || 0)),
  };
}

function canProcess() {
  return files.length >= 2 && files.length <= 10;
}

function updateButtons() {
  const enabled = canProcess();
  els.previewBtn.disabled = !enabled;
  els.mergeBtn.disabled = !enabled;
}

function updateMeta() {
  els.filesMeta.textContent = `${files.length} archivo${files.length === 1 ? "" : "s"}`;
}

function supportsInlinePlayback(ext) {
  const e = (ext || "").toLowerCase();
  return ["mp3", "m4a", "m4r", "mp4", "wav"].includes(e);
}

function renderList() {
  els.fileList.innerHTML = "";

  files.forEach((f, idx) => {
    const li = document.createElement("li");
    li.className = "file";

    const left = document.createElement("div");
    left.className = "file__left";

    const order = document.createElement("div");
    order.className = "file__order";
    order.textContent = String(idx + 1);

    const info = document.createElement("div");
    info.className = "file__info";

    const name = document.createElement("div");
    name.className = "file__name";
    name.textContent = f.filename;

    const meta = document.createElement("div");
    meta.className = "file__meta";
    meta.textContent = `${f.duration.toFixed(1)}s • ${String(f.format).toUpperCase()}`;

    info.appendChild(name);
    info.appendChild(meta);

    left.appendChild(order);
    left.appendChild(info);

    const controls = document.createElement("div");
    controls.className = "file__controls";

    const vol = document.createElement("input");
    vol.type = "range";
    vol.min = "-20";
    vol.max = "20";
    vol.step = "1";
    vol.value = String(f.volumeDb || 0);
    vol.className = "file__volume";
    vol.setAttribute("aria-label", `Volumen ${f.filename}`);
    vol.addEventListener("input", () => {
      f.volumeDb = Number(vol.value);
    });

    const up = document.createElement("button");
    up.className = "icon-btn";
    up.textContent = "↑";
    up.disabled = idx === 0;
    up.addEventListener("click", () => {
      if (idx <= 0) return;
      const tmp = files[idx - 1];
      files[idx - 1] = files[idx];
      files[idx] = tmp;
      renderList();
    });

    const down = document.createElement("button");
    down.className = "icon-btn";
    down.textContent = "↓";
    down.disabled = idx === files.length - 1;
    down.addEventListener("click", () => {
      if (idx >= files.length - 1) return;
      const tmp = files[idx + 1];
      files[idx + 1] = files[idx];
      files[idx] = tmp;
      renderList();
    });

    const del = document.createElement("button");
    del.className = "icon-btn icon-btn--danger";
    del.textContent = "✕";
    del.addEventListener("click", () => {
      files = files.filter((x) => x.file_id !== f.file_id);
      renderList();
    });

    controls.appendChild(vol);
    controls.appendChild(up);
    controls.appendChild(down);
    controls.appendChild(del);

    li.appendChild(left);
    li.appendChild(controls);

    els.fileList.appendChild(li);
  });

  updateMeta();
  updateButtons();
}

async function uploadFiles(fileList) {
  const list = Array.from(fileList || []);
  if (list.length === 0) return;

  if (list.length + files.length > 10) {
    showMessage("Máximo 10 archivos", "error");
    return;
  }

  const fd = new FormData();
  for (const f of list) fd.append("files", f, f.name);

  showMessage("Subiendo archivos...", "info");

  const res = await fetch(`${API_BASE}/v1/uploads`, {
    method: "POST",
    body: fd,
  });

  if (!res.ok) {
    const t = await res.text();
    showMessage(`Error al subir: ${t}`, "error");
    return;
  }

  const data = await res.json();
  const incoming = (data.files || []).map((x) => ({
    ...x,
    volumeDb: 0,
  }));

  files = files.concat(incoming);
  renderList();
  showMessage(`✓ ${incoming.length} archivo(s) añadidos`, "success");
}

function pollJob(jobId, onUpdate) {
  let cancelled = false;
  const epochAtStart = uiEpoch;

  async function tick() {
    if (cancelled) return;
    if (epochAtStart !== uiEpoch) return;
    const res = await fetch(`${API_BASE}/v1/jobs/${jobId}`);
    if (!res.ok) {
      // Si se hizo reset y el job desaparece, dejamos de poll.
      return;
    }
    const data = await res.json();
    if (epochAtStart !== uiEpoch) return;
    onUpdate(data);
    if (data.state === "done" || data.state === "error") return;
    window.setTimeout(tick, 600);
  }

  tick();
  return () => {
    cancelled = true;
  };
}

async function createPreview() {
  if (!canProcess()) return;

  cancelAllPolling();

  els.previewProgress.hidden = false;
  els.previewBar.value = 0;
  els.previewStage.textContent = "Iniciando";
  els.previewPanel.hidden = true;

  const res = await fetch(`${API_BASE}/v1/previews`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_ids: files.map((f) => f.file_id),
      params: paramsFromUI(),
    }),
  });

  if (!res.ok) {
    const t = await res.text();
    showMessage(`Error: ${t}`, "error");
    els.previewProgress.hidden = true;
    return;
  }

  const { job_id, preview_url } = await res.json();

  cancelPreviewPoll = pollJob(job_id, (s) => {
    els.previewBar.value = s.progress || 0;
    els.previewStage.textContent = `Preview: ${s.stage || ""} (${s.progress || 0}%)`;

    if (s.state === "error") {
      els.previewProgress.hidden = true;
      showMessage(s.error || "Error en preview", "error");
    }

    if (s.state === "done") {
      els.previewProgress.hidden = true;
      els.previewPanel.hidden = false;
      els.previewAudio.src = preview_url;
      showMessage("Preview lista", "success");
    }
  });
}

async function createMerge() {
  if (!canProcess()) return;

  cancelAllPolling();

  els.mergeProgress.hidden = false;
  els.mergeBar.value = 0;
  els.mergeStage.textContent = "Iniciando";
  els.resultPanel.hidden = true;

  const res = await fetch(`${API_BASE}/v1/merges`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_ids: files.map((f) => f.file_id),
      params: paramsFromUI(),
      output: { format: els.format.value },
    }),
  });

  if (!res.ok) {
    const t = await res.text();
    showMessage(`Error: ${t}`, "error");
    els.mergeProgress.hidden = true;
    return;
  }

  const { job_id, download_url } = await res.json();

  cancelMergePoll = pollJob(job_id, (s) => {
    els.mergeBar.value = s.progress || 0;
    els.mergeStage.textContent = `Fusión: ${s.stage || ""} (${s.progress || 0}%)`;

    if (s.state === "error") {
      els.mergeProgress.hidden = true;
      showMessage(s.error || "Error en fusión", "error");
    }

    if (s.state === "done") {
      els.mergeProgress.hidden = true;
      els.resultPanel.hidden = false;
      els.downloadLink.href = download_url;

      const fmt = String(els.format.value);
      els.resultHint.hidden = supportsInlinePlayback(fmt);
      els.resultAudio.hidden = !supportsInlinePlayback(fmt);
      if (supportsInlinePlayback(fmt)) {
        els.resultAudio.src = download_url;
      }

      showMessage("¡Fusión completada!", "success");
    }
  });
}

function bindUI() {
  syncParamLabels();

  els.crossfade.addEventListener("input", syncParamLabels);
  els.fadeIn.addEventListener("input", syncParamLabels);
  els.fadeOut.addEventListener("input", syncParamLabels);

  els.previewBtn.addEventListener("click", createPreview);
  els.mergeBtn.addEventListener("click", createMerge);

  if (els.clearBtn) els.clearBtn.addEventListener("click", handleSoftClear);
  if (els.hardResetBtn) els.hardResetBtn.addEventListener("click", handleHardReset);

  els.dropzone.addEventListener("click", () => els.fileInput.click());
  els.dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      els.fileInput.click();
    }
  });

  els.fileInput.addEventListener("change", (e) => {
    uploadFiles(e.target.files);
    els.fileInput.value = "";
  });

  els.dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    els.dropzone.classList.add("dropzone--over");
  });
  els.dropzone.addEventListener("dragleave", () => {
    els.dropzone.classList.remove("dropzone--over");
  });
  els.dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    els.dropzone.classList.remove("dropzone--over");
    uploadFiles(e.dataTransfer.files);
  });
}

bindUI();
renderList();
