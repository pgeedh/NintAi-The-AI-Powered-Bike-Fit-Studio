/**
 * NintAi Studio — Precision Workspace Logic
 */

const state = {
  config: null,
  selectedSampleId: "testvideo2.mp4",
  uploadedFile: null,
  profile: "road_endurance",
  result: null,
  scrubberIdx: 0,
  isPlaying: false,
  playTimer: null,
};

const STORAGE_KEY = "nintai_gemini_key";
const STORAGE_RIDER = "nintai_rider_name";

document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) window.lucide.createIcons();
  loadSettings();
  setupUIEvents();
  await loadConfig();
});

function loadSettings() {
  const k = localStorage.getItem(STORAGE_KEY) || "";
  const r = localStorage.getItem(STORAGE_RIDER) || "";
  const keyInput = document.getElementById("geminiKeyInput");
  const riderInput = document.getElementById("riderNameInput");
  if (keyInput) keyInput.value = k;
  if (riderInput) riderInput.value = r;

  const pill = document.getElementById("aiStatusPill");
  if (pill) {
    pill.textContent = k.length > 8 ? "AI Ready" : "AI Key";
    if (k.length > 8) pill.classList.add("text-emerald-400");
  }
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error("Failed to load config");
    state.config = await res.json();

    renderSampleList(state.config.samples || []);
  } catch (err) {
    console.error("Config error:", err);
  }
}

function renderSampleList(samples) {
  const list = document.getElementById("samplePickerList");
  if (!list) return;
  list.innerHTML = "";

  // Preferred order of samples
  const priority = ["testvideo2.mp4", "testvideo.mp4", "1.jpg", "4.jpeg"];
  const sorted = samples.sort((a, b) => {
    const ai = priority.indexOf(a.id);
    const bi = priority.indexOf(b.id);
    return (ai !== -1 ? ai : 99) - (bi !== -1 ? bi : 99);
  });

  sorted.slice(0, 4).forEach((s) => {
    const item = document.createElement("div");
    const isSelected = s.id === state.selectedSampleId && !state.uploadedFile;
    item.className = `p-2 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
      isSelected
        ? "bg-blue-950/40 border-blue-500/60 text-white font-medium"
        : "bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800/80"
    }`;
    item.dataset.id = s.id;

    const icon = s.type === "video" ? "video" : "image";
    item.innerHTML = `
      <div class="flex items-center gap-2 truncate">
        <i data-lucide="${icon}" class="w-3.5 h-3.5 text-slate-400 flex-shrink-0"></i>
        <span class="truncate">${s.id}</span>
      </div>
      <span class="text-[10px] font-mono text-slate-500 uppercase">${s.type}</span>
    `;

    item.addEventListener("click", () => {
      state.selectedSampleId = s.id;
      state.uploadedFile = null;
      document.getElementById("activeSourceLabel").textContent = `${s.id} (${s.type})`;
      renderSampleList(samples);
    });

    list.appendChild(item);
  });

  if (window.lucide) window.lucide.createIcons();
}

function setupUIEvents() {
  // Segmented discipline control
  const segments = document.querySelectorAll("#profileSegmented .segment-item");
  segments.forEach((seg) => {
    seg.addEventListener("click", () => {
      segments.forEach((s) => s.classList.remove("active"));
      seg.classList.add("active");
      state.profile = seg.dataset.profile;

      const desc = document.getElementById("profileDescription");
      if (desc && state.config?.profiles[state.profile]) {
        desc.textContent = state.config.profiles[state.profile].blurb;
      }
    });
  });

  // Upload trigger
  const btnBrowse = document.getElementById("btnBrowseCustom");
  const fileInput = document.getElementById("fileInput");
  btnBrowse?.addEventListener("click", () => fileInput?.click());

  fileInput?.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      state.uploadedFile = f;
      state.selectedSampleId = null;
      document.getElementById("activeSourceLabel").textContent = `${f.name} (Custom Upload)`;
      renderSampleList(state.config?.samples || []);
    }
  });

  // Run analysis
  document.getElementById("btnRunFit")?.addEventListener("click", executeFitAnalysis);

  // Timeline scrubber controls
  const slider = document.getElementById("scrubberSlider");
  slider?.addEventListener("input", (e) => {
    stopPlay();
    renderScrubberFrame(parseInt(e.target.value, 10));
  });

  document.getElementById("btnPlayPause")?.addEventListener("click", togglePlay);
  document.getElementById("btnPrevFrame")?.addEventListener("click", () => {
    stopPlay();
    renderScrubberFrame(Math.max(0, state.scrubberIdx - 1));
  });
  document.getElementById("btnNextFrame")?.addEventListener("click", () => {
    stopPlay();
    const previews = state.result?.previews || [];
    renderScrubberFrame(Math.min(previews.length - 1, state.scrubberIdx + 1));
  });

  // Export PDF
  document.getElementById("btnDownloadPDF")?.addEventListener("click", exportPDF);

  // Modals
  const guideModal = document.getElementById("guideModal");
  document.getElementById("btnOpenGuide")?.addEventListener("click", () => guideModal?.classList.add("open"));
  document.getElementById("btnCloseGuide")?.addEventListener("click", () => guideModal?.classList.remove("open"));
  document.getElementById("btnDismissGuide")?.addEventListener("click", () => guideModal?.classList.remove("open"));

  const settingsModal = document.getElementById("settingsModal");
  document.getElementById("btnOpenSettings")?.addEventListener("click", () => settingsModal?.classList.add("open"));
  document.getElementById("btnCloseSettings")?.addEventListener("click", () => settingsModal?.classList.remove("open"));
  document.getElementById("btnSaveSettings")?.addEventListener("click", () => {
    const key = document.getElementById("geminiKeyInput")?.value || "";
    const name = document.getElementById("riderNameInput")?.value || "";
    localStorage.setItem(STORAGE_KEY, key);
    localStorage.setItem(STORAGE_RIDER, name);
    loadSettings();
    settingsModal?.classList.remove("open");
  });
}

async function executeFitAnalysis() {
  const loading = document.getElementById("stageLoading");
  const placeholder = document.getElementById("stagePlaceholder");
  const stageImg = document.getElementById("stageImg");
  const btnRun = document.getElementById("btnRunFit");

  loading?.classList.remove("hidden");
  placeholder?.classList.add("hidden");
  if (btnRun) btnRun.disabled = true;

  const formData = new FormData();
  if (state.uploadedFile) {
    formData.append("file", state.uploadedFile);
  } else if (state.selectedSampleId) {
    formData.append("sample_id", state.selectedSampleId);
  } else {
    alert("Please select a sample or upload a video.");
    loading?.classList.add("hidden");
    if (btnRun) btnRun.disabled = false;
    return;
  }

  formData.append("profile", state.profile);
  formData.append("backend", document.getElementById("backendSelect")?.value || "auto");
  formData.append("crank_mm", document.getElementById("crankMmInput")?.value || "172.5");

  const apiKey = localStorage.getItem(STORAGE_KEY) || "";
  if (apiKey) formData.append("api_key", apiKey);

  const rider = localStorage.getItem(STORAGE_RIDER) || "";
  if (rider) formData.append("rider_name", rider);

  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Analysis failed");
    }

    const data = await resp.json();
    state.result = data;

    renderStudioResults(data);
  } catch (err) {
    console.error("Analysis failure:", err);
    alert(`Analysis Error: ${err.message}`);
    placeholder?.classList.remove("hidden");
  } finally {
    loading?.classList.add("hidden");
    if (btnRun) btnRun.disabled = false;
  }
}

function renderStudioResults(data) {
  // 1. Fit score & status
  const scoreCard = document.getElementById("scoreSummaryCard");
  const scoreVal = document.getElementById("scoreValue");
  const statusPill = document.getElementById("fitStatusPill");
  if (scoreCard && scoreVal && statusPill) {
    scoreCard.classList.remove("hidden");
    scoreVal.textContent = data.score !== null ? data.score : "--";
    if (data.score >= 80) {
      statusPill.textContent = "Optimal";
      statusPill.className = "status-pill status-ok";
      scoreVal.className = "text-2xl font-extrabold font-mono text-emerald-400";
    } else if (data.score >= 60) {
      statusPill.textContent = "Borderline";
      statusPill.className = "status-pill status-watch";
      scoreVal.className = "text-2xl font-extrabold font-mono text-amber-400";
    } else {
      statusPill.textContent = "Adjust";
      statusPill.className = "status-pill status-fix";
      scoreVal.className = "text-2xl font-extrabold font-mono text-rose-400";
    }
  }

  // 2. HUD Chips
  const m = data.metrics || {};
  const b = data.biomech || {};
  document.getElementById("hudKneeExt").textContent = m.knee_ext ? `${m.knee_ext.toFixed(1)}°` : "--°";
  document.getElementById("hudHip").textContent = m.hip_closed ? `${m.hip_closed.toFixed(1)}°` : "--°";
  document.getElementById("hudCadence").textContent = b.cadence_rpm ? `${b.cadence_rpm.toFixed(0)} RPM` : "-- RPM";
  document.getElementById("hudKops").textContent = b.kops_mm !== undefined && b.kops_mm !== null
    ? `${b.kops_mm > 0 ? "+" : ""}${b.kops_mm.toFixed(0)} mm`
    : "-- mm";

  // 3. Scrubber Timeline
  const previews = data.previews || [];
  const slider = document.getElementById("scrubberSlider");
  if (slider) {
    slider.disabled = previews.length === 0;
    slider.min = 0;
    slider.max = Math.max(0, previews.length - 1);
    slider.value = 0;
  }
  if (previews.length > 0) {
    renderScrubberFrame(0);
  } else if (data.snapshots?.photo) {
    document.getElementById("stageImg").src = data.snapshots.photo.data_url;
  }

  // Enable Export PDF button
  const btnPDF = document.getElementById("btnDownloadPDF");
  if (btnPDF) {
    btnPDF.disabled = false;
    btnPDF.classList.remove("hidden");
  }

  // 4. Kinematics List
  renderKinematics(data);

  // 5. Prescriptions & Coach
  renderPrescriptions(data);

  // 6. Phase Snapshots Strip
  renderSnapshotsStrip(data.snapshots || {});

  if (window.lucide) window.lucide.createIcons();
}

function renderScrubberFrame(idx) {
  const previews = state.result?.previews || [];
  if (!previews[idx]) return;

  state.scrubberIdx = idx;
  const p = previews[idx];

  const img = document.getElementById("stageImg");
  if (img) img.src = p.data_url;

  const slider = document.getElementById("scrubberSlider");
  if (slider) slider.value = idx;

  const timeEl = document.getElementById("scrubberTime");
  if (timeEl) {
    const mins = Math.floor(p.t / 60);
    const secs = (p.t % 60).toFixed(2);
    timeEl.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(5, '0')}`;
  }

  const counter = document.getElementById("scrubberFrameCounter");
  if (counter) counter.textContent = `Frame ${idx + 1} / ${previews.length}`;
}

function togglePlay() {
  if (state.isPlaying) {
    stopPlay();
  } else {
    startPlay();
  }
}

function startPlay() {
  const previews = state.result?.previews || [];
  if (previews.length === 0) return;

  state.isPlaying = true;
  const icon = document.getElementById("playIcon");
  if (icon) icon.setAttribute("data-lucide", "pause");
  if (window.lucide) window.lucide.createIcons();

  state.playTimer = setInterval(() => {
    let next = state.scrubberIdx + 1;
    if (next >= previews.length) next = 0;
    renderScrubberFrame(next);
  }, 66);
}

function stopPlay() {
  state.isPlaying = false;
  if (state.playTimer) {
    clearInterval(state.playTimer);
    state.playTimer = null;
  }
  const icon = document.getElementById("playIcon");
  if (icon) icon.setAttribute("data-lucide", "play");
  if (window.lucide) window.lucide.createIcons();
}

function renderKinematics(data) {
  const container = document.getElementById("kinematicsList");
  if (!container) return;
  container.innerHTML = "";

  const metricsConfig = state.config?.metrics || {};
  const ranges = state.config?.profiles[data.profile]?.ranges || {};

  Object.entries(metricsConfig).forEach(([key, meta]) => {
    const val = data.metrics[key];
    if (val === undefined || val === null || val <= 0) return;

    const range = ranges[key] || [0, 0];
    const status = data.statuses[key] || "na";

    const row = document.createElement("div");
    row.className = "space-y-1";

    const statusPillClass = status === "ok" ? "status-ok" : status === "watch" ? "status-watch" : "status-fix";
    const statusText = status === "ok" ? "In Range" : status === "watch" ? "Watch" : "Adjust";

    const span = Math.max(range[1] - range[0], 20);
    const minBound = range[0] - span * 0.8;
    const maxBound = range[1] + span * 0.8;
    const total = maxBound - minBound;

    const leftPct = Math.max(0, ((range[0] - minBound) / total) * 100);
    const widthPct = Math.min(100, ((range[1] - range[0]) / total) * 100);
    const dotPct = Math.min(100, Math.max(0, ((val - minBound) / total) * 100));

    row.innerHTML = `
      <div class="flex items-center justify-between text-xs">
        <span class="text-slate-300 font-medium">${meta.short || meta.label}</span>
        <div class="flex items-center gap-2 font-mono">
          <span class="font-bold text-white">${val.toFixed(1)}°</span>
          <span class="status-pill ${statusPillClass}">${statusText}</span>
        </div>
      </div>

      <div class="range-track my-1">
        <div class="range-zone" style="left: ${leftPct}%; width: ${widthPct}%;"></div>
        <div class="range-dot" style="left: ${dotPct}%;"></div>
      </div>

      <div class="flex justify-between text-[10px] text-slate-500 font-mono">
        <span>${range[0]}°</span>
        <span>${range[1]}°</span>
      </div>
    `;

    container.appendChild(row);
  });
}

function renderPrescriptions(data) {
  const container = document.getElementById("prescriptionsList");
  if (!container) return;
  container.innerHTML = "";

  const recs = data.recommendations || [];
  if (recs.length === 0) {
    container.innerHTML = `
      <div class="p-3 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs">
        All observed joint angles are in alignment with ${data.profile_name} specifications.
      </div>
    `;
  } else {
    recs.forEach((r, idx) => {
      const el = document.createElement("div");
      el.className = "p-2.5 rounded bg-slate-900 border border-slate-800 space-y-0.5";
      el.innerHTML = `
        <div class="flex items-center gap-2">
          <span class="text-[10px] font-bold font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">P${r.priority}</span>
          <strong class="text-slate-200 text-xs">${r.title}</strong>
        </div>
        <p class="text-[11px] text-slate-400 leading-snug">${r.detail}</p>
      `;
      container.appendChild(el);
    });
  }

  // Coach verdict
  const coachBox = document.getElementById("coachBox");
  const coachTag = document.getElementById("coachTypeTag");
  if (coachBox && data.coach?.text) {
    coachBox.textContent = data.coach.text;
    coachBox.classList.remove("hidden");
  }
  if (coachTag && data.coach?.source) {
    coachTag.textContent = data.coach.source === "gemini" ? "Google Gemini 2.5" : "Offline Biomechanist";
  }
}

function renderSnapshotsStrip(snaps) {
  const strip = document.getElementById("snapshotsStrip");
  const container = document.getElementById("snapshotsContainer");
  if (!strip || !container) return;

  const entries = Object.entries(snaps);
  if (entries.length === 0) {
    strip.classList.add("hidden");
    return;
  }

  strip.classList.remove("hidden");
  container.innerHTML = "";

  entries.forEach(([key, s]) => {
    const card = document.createElement("div");
    card.className = "rounded-lg overflow-hidden bg-black border border-slate-800 relative group cursor-pointer aspect-video";
    card.innerHTML = `
      <img src="${s.data_url}" alt="${s.title}" class="w-full h-full object-contain">
      <span class="absolute bottom-1 left-1.5 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-slate-300">
        ${s.title}
      </span>
    `;

    card.addEventListener("click", () => {
      document.getElementById("stageImg").src = s.data_url;
      stopPlay();
    });

    container.appendChild(card);
  });
}

async function exportPDF() {
  if (!state.result) return;
  const btn = document.getElementById("btnDownloadPDF");
  const orig = btn?.innerHTML;
  if (btn) btn.innerHTML = "<span>Generating PDF...</span>";

  try {
    const rider = localStorage.getItem(STORAGE_RIDER) || "Cyclist";
    const coach = state.result.coach?.text || "";

    const resp = await fetch("/api/generate_pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        result: state.result,
        rider_name: rider,
        coach_text: coach,
      }),
    });

    if (!resp.ok) throw new Error("PDF failed");

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nintai_fit_report_${state.result.profile}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (err) {
    alert(`Export Error: ${err.message}`);
  } finally {
    if (btn && orig) btn.innerHTML = orig;
    if (window.lucide) window.lucide.createIcons();
  }
}
