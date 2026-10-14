/**
 * NintAi Studio — Client-side Application Logic.
 */

// Application State
const state = {
  config: null,
  selectedProfile: "road_endurance",
  selectedSampleId: null,
  uploadedFile: null,
  currentResult: null,
  scrubberIndex: 0,
  isPlaying: false,
  playTimer: null,
};

// Storage Keys
const STORAGE_API_KEY = "nintai_gemini_api_key";
const STORAGE_RIDER_NAME = "nintai_rider_name";
const STORAGE_RIDER_NOTES = "nintai_rider_notes";

document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) window.lucide.createIcons();
  loadSavedSettings();
  initEventListeners();
  await fetchConfig();
});

function loadSavedSettings() {
  const savedKey = localStorage.getItem(STORAGE_API_KEY) || "";
  const savedName = localStorage.getItem(STORAGE_RIDER_NAME) || "";
  const savedNotes = localStorage.getItem(STORAGE_RIDER_NOTES) || "";

  const keyInput = document.getElementById("geminiApiKeyInput");
  const nameInput = document.getElementById("riderNameInput");
  const notesInput = document.getElementById("riderNotesInput");

  if (keyInput) keyInput.value = savedKey;
  if (nameInput) nameInput.value = savedName;
  if (notesInput) notesInput.value = savedNotes;

  updateAIStatusPill(savedKey);
}

function updateAIStatusPill(key) {
  const pill = document.getElementById("aiStatusPill");
  if (!pill) return;
  if (key && key.trim().length > 10) {
    pill.textContent = "AI Connected";
    pill.classList.add("text-emerald-400");
  } else {
    pill.textContent = "AI Coach Key";
    pill.classList.remove("text-emerald-400");
  }
}

async function fetchConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error("Failed to load config");
    state.config = await res.json();
    renderSamples(state.config.samples || []);
    renderProfiles(state.config.profiles || {});
  } catch (err) {
    console.error("Config fetch error:", err);
  }
}

function renderSamples(samples) {
  const container = document.getElementById("sampleCardsContainer");
  if (!container) return;
  container.innerHTML = "";

  // Highlight 4 flagship demo samples
  const priority = ["testvideo2.mp4", "testvideo.mp4", "1.jpg", "4.jpeg"];
  const displaySamples = samples.sort((a, b) => {
    const ai = priority.indexOf(a.id);
    const bi = priority.indexOf(b.id);
    return (ai !== -1 ? ai : 99) - (bi !== -1 ? bi : 99);
  }).slice(0, 4);

  displaySamples.forEach((s) => {
    const card = document.createElement("div");
    card.className = "sample-card p-4 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-blue-500/50 cursor-pointer transition-all space-y-2 group";
    card.dataset.id = s.id;

    const isVideo = s.type === "video";
    const icon = isVideo ? "video" : "image";
    const tag = isVideo ? "Demo Clip" : "Demo Photo";

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">${tag}</span>
        <i data-lucide="${icon}" class="w-4 h-4 text-slate-400 group-hover:text-blue-400"></i>
      </div>
      <div>
        <p class="font-bold text-xs text-slate-200 group-hover:text-white truncate">${s.id}</p>
        <p class="text-[11px] text-slate-400 mt-0.5">${isVideo ? "Full dynamic pedalling cycle" : "Static posture check"}</p>
      </div>
      <div class="pt-1 flex items-center gap-1 text-[11px] font-semibold text-blue-400">
        <span>Click to load</span>
        <i data-lucide="arrow-right" class="w-3 h-3 group-hover:translate-x-1 transition-transform"></i>
      </div>
    `;

    card.addEventListener("click", () => selectSample(s));
    container.appendChild(card);
  });

  if (window.lucide) window.lucide.createIcons();
}

function selectSample(sample) {
  state.selectedSampleId = sample.id;
  state.uploadedFile = null;

  // Clear upload styling
  const tag = document.getElementById("activeSelectionTag");
  if (tag) {
    tag.textContent = `Selected: ${sample.id}`;
    tag.className = "text-xs font-mono px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30";
  }

  // Highlight card
  document.querySelectorAll(".sample-card").forEach((c) => {
    if (c.dataset.id === sample.id) {
      c.classList.add("border-blue-500", "bg-blue-500/10");
    } else {
      c.classList.remove("border-blue-500", "bg-blue-500/10");
    }
  });

  // Smooth scroll down to workbench
  document.getElementById("workbenchCard")?.scrollIntoView({ behavior: "smooth" });
}

function renderProfiles(profiles) {
  const container = document.getElementById("profileSelector");
  if (!container) return;
  container.innerHTML = "";

  Object.entries(profiles).forEach(([key, prof]) => {
    const pill = document.createElement("div");
    pill.className = `profile-pill ${key === state.selectedProfile ? "active" : ""}`;
    pill.dataset.key = key;

    pill.innerHTML = `
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xl">${prof.emoji || "🚲"}</span>
        <span class="font-bold text-xs text-slate-100">${prof.name}</span>
      </div>
      <p class="text-[11px] text-slate-400 leading-snug">${prof.blurb}</p>
    `;

    pill.addEventListener("click", () => {
      document.querySelectorAll(".profile-pill").forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.selectedProfile = key;
    });

    container.appendChild(pill);
  });
}

function initEventListeners() {
  // Drop Zone & File Input
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");

  if (dropZone && fileInput) {
    dropZone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0]);
      }
    });

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("border-blue-500", "bg-slate-900/80");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("border-blue-500", "bg-slate-900/80");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("border-blue-500", "bg-slate-900/80");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });
  }

  // Toggle Advanced Calibration
  const toggleAdv = document.getElementById("toggleAdvancedBtn");
  const advPanel = document.getElementById("advancedPanel");
  const advChevron = document.getElementById("advChevron");
  if (toggleAdv && advPanel) {
    toggleAdv.addEventListener("click", () => {
      const isHidden = advPanel.classList.toggle("hidden");
      if (advChevron) {
        advChevron.style.transform = isHidden ? "rotate(0deg)" : "rotate(180deg)";
      }
    });
  }

  // Modals
  const guideModal = document.getElementById("guideModal");
  const btnOpenGuide = document.getElementById("btnOpenGuide");
  const btnCloseGuide = document.getElementById("btnCloseGuide");
  const btnGotItGuide = document.getElementById("btnGotItGuide");

  if (btnOpenGuide && guideModal) {
    btnOpenGuide.addEventListener("click", () => guideModal.classList.add("open"));
    btnCloseGuide?.addEventListener("click", () => guideModal.classList.remove("open"));
    btnGotItGuide?.addEventListener("click", () => guideModal.classList.remove("open"));
  }

  const settingsModal = document.getElementById("settingsModal");
  const btnOpenSettings = document.getElementById("btnOpenSettings");
  const btnCloseSettings = document.getElementById("btnCloseSettings");
  const btnSaveSettings = document.getElementById("btnSaveSettings");

  if (btnOpenSettings && settingsModal) {
    btnOpenSettings.addEventListener("click", () => settingsModal.classList.add("open"));
    btnCloseSettings?.addEventListener("click", () => settingsModal.classList.remove("open"));
    btnSaveSettings?.addEventListener("click", () => {
      const key = document.getElementById("geminiApiKeyInput")?.value || "";
      const name = document.getElementById("riderNameInput")?.value || "";
      const notes = document.getElementById("riderNotesInput")?.value || "";

      localStorage.setItem(STORAGE_API_KEY, key);
      localStorage.setItem(STORAGE_RIDER_NAME, name);
      localStorage.setItem(STORAGE_RIDER_NOTES, notes);

      updateAIStatusPill(key);
      settingsModal.classList.remove("open");
    });
  }

  // Start Analysis CTA
  document.getElementById("btnStartAnalysis")?.addEventListener("click", runAnalysis);

  // Analyze Another CTA
  document.getElementById("btnNewAnalysis")?.addEventListener("click", () => {
    document.getElementById("resultsSection")?.classList.add("hidden");
    document.getElementById("workbenchCard")?.classList.remove("hidden");
    document.getElementById("workbenchCard")?.scrollIntoView({ behavior: "smooth" });
  });

  // Download PDF
  document.getElementById("btnDownloadPDF")?.addEventListener("click", downloadPDF);

  // Scrubber Controls
  initScrubberControls();
}

function handleFileSelection(file) {
  state.uploadedFile = file;
  state.selectedSampleId = null;

  document.querySelectorAll(".sample-card").forEach((c) => c.classList.remove("border-blue-500", "bg-blue-500/10"));

  const tag = document.getElementById("activeSelectionTag");
  if (tag) {
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
    tag.textContent = `Uploaded: ${file.name} (${sizeMb} MB)`;
    tag.className = "text-xs font-mono px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
  }
}

async function runAnalysis() {
  if (!state.uploadedFile && !state.selectedSampleId) {
    alert("Please select a sample or upload a side-on video/photo first.");
    return;
  }

  // Show Loading View
  const workbench = document.getElementById("workbenchCard");
  const loading = document.getElementById("loadingState");
  const results = document.getElementById("resultsSection");

  if (workbench) workbench.classList.add("hidden");
  if (results) results.classList.add("hidden");
  if (loading) {
    loading.classList.remove("hidden");
    loading.scrollIntoView({ behavior: "smooth" });
  }

  // Animate loading step ticker
  animateLoadingSteps();

  const formData = new FormData();
  if (state.uploadedFile) {
    formData.append("file", state.uploadedFile);
  } else if (state.selectedSampleId) {
    formData.append("sample_id", state.selectedSampleId);
  }

  formData.append("profile", state.selectedProfile);

  const backend = document.getElementById("backendSelect")?.value || "auto";
  formData.append("backend", backend);

  const crankMm = document.getElementById("crankMmInput")?.value || "172.5";
  formData.append("crank_mm", crankMm);

  const riderHeight = document.getElementById("riderHeightInput")?.value;
  if (riderHeight) formData.append("rider_height", riderHeight);

  const apiKey = localStorage.getItem(STORAGE_API_KEY) || "";
  if (apiKey) formData.append("api_key", apiKey);

  const riderName = localStorage.getItem(STORAGE_RIDER_NAME) || "";
  if (riderName) formData.append("rider_name", riderName);

  const riderNotes = localStorage.getItem(STORAGE_RIDER_NOTES) || "";
  if (riderNotes) formData.append("rider_notes", riderNotes);

  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Analysis request failed");
    }

    const data = await resp.json();
    state.currentResult = data;

    renderResults(data);

    if (loading) loading.classList.add("hidden");
    if (results) {
      results.classList.remove("hidden");
      results.scrollIntoView({ behavior: "smooth" });
    }
  } catch (err) {
    console.error("Analysis Error:", err);
    alert(`Analysis Failed: ${err.message}`);
    if (loading) loading.classList.add("hidden");
    if (workbench) workbench.classList.remove("hidden");
  }
}

function animateLoadingSteps() {
  const steps = [
    { id: "stepTrack", title: "Tracking Kinematics...", sub: "Extracting 33 biomechanical landmarks per frame" },
    { id: "stepSmooth", title: "Filtering & Cycles...", sub: "Zero-phase Savitzky-Golay smoothing & stroke segmentation" },
    { id: "stepKinematics", title: "Fitting Geometry...", sub: "Fitting crank circle, KOPS, and calculating angle deviations" },
    { id: "stepAI", title: "Generating Coach Report...", sub: "Synthesizing biomechanical verdicts and PDF documentation" },
  ];

  let current = 0;
  const interval = setInterval(() => {
    current++;
    if (current >= steps.length) {
      clearInterval(interval);
      return;
    }

    steps.forEach((s, idx) => {
      const el = document.getElementById(s.id);
      if (!el) return;
      if (idx === current) {
        el.className = "p-2 rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/40 animate-pulse";
        document.getElementById("loadingStageTitle").textContent = s.title;
        document.getElementById("loadingStageSub").textContent = s.sub;
      } else if (idx < current) {
        el.className = "p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      }
    });
  }, 1400);
}

function renderResults(data) {
  // 1. Fit Score & Gauge
  const score = data.score !== null ? data.score : "--";
  document.getElementById("scoreValue").textContent = score;

  const circle = document.getElementById("scoreCircle");
  if (circle && typeof score === "number") {
    // 264 circumference (2 * pi * 42)
    const offset = 264 - (264 * score) / 100;
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#f43f5e";
  }

  const verdictBadge = document.getElementById("fitVerdictBadge");
  if (verdictBadge) {
    if (score >= 80) {
      verdictBadge.textContent = "Optimal Fit";
      verdictBadge.className = "badge badge-ok";
    } else if (score >= 60) {
      verdictBadge.textContent = "Minor Adjustments";
      verdictBadge.className = "badge badge-watch";
    } else {
      verdictBadge.textContent = "Adjustments Needed";
      verdictBadge.className = "badge badge-fix";
    }
  }

  // Profile subtitle
  document.getElementById("fitProfileSub").textContent = 
    `Discipline: ${data.profile_name} · Engine: ${data.backend_name || data.backend}`;

  // 2. Telemetry Pills
  const pillsContainer = document.getElementById("telemetryPills");
  if (pillsContainer) {
    pillsContainer.innerHTML = "";
    const b = data.biomech || {};
    const e = data.extra || {};

    const items = [];
    if (b.cadence_rpm) items.push({ label: "Cadence", val: `${b.cadence_rpm.toFixed(0)} RPM` });
    if (b.kops_mm !== undefined && b.kops_mm !== null) {
      items.push({ label: "KOPS", val: `${b.kops_mm > 0 ? "+" : ""}${b.kops_mm.toFixed(0)} mm` });
    }
    if (b.hip_rock_mm !== undefined && b.hip_rock_mm !== null) {
      items.push({ label: "Hip Rock", val: `${b.hip_rock_mm.toFixed(0)} mm` });
    }
    if (e.duration_s) items.push({ label: "Duration", val: `${e.duration_s.toFixed(1)}s` });
    if (e.side) items.push({ label: "Tracked Side", val: e.side.toUpperCase() });

    items.forEach((it) => {
      const span = document.createElement("span");
      span.className = "px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 font-medium text-slate-300";
      span.innerHTML = `<span class="text-slate-400 font-normal">${it.label}:</span> <strong class="text-white">${it.val}</strong>`;
      pillsContainer.appendChild(span);
    });
  }

  // 3. Scrubber Setup
  setupScrubber(data.previews || []);

  // 4. Capture Warnings
  const warnCard = document.getElementById("warningsCard");
  const warnList = document.getElementById("warningsList");
  if (warnCard && warnList) {
    if (data.warnings && data.warnings.length > 0) {
      warnList.innerHTML = data.warnings.map((w) => `<li>${w}</li>`).join("");
      warnCard.classList.remove("hidden");
    } else {
      warnCard.classList.add("hidden");
    }
  }

  // 5. Kinematics Range List
  renderMetricsList(data);

  // 6. Snapshots Grid
  renderSnapshots(data.snapshots || {});

  // 7. Recommendations
  renderRecommendations(data.recommendations || []);

  // 8. AI Coach
  const coachCard = document.getElementById("coachText");
  const coachSource = document.getElementById("coachSourceTag");
  if (coachCard) {
    coachCard.textContent = data.coach?.text || "No coach remarks available.";
  }
  if (coachSource && data.coach?.source) {
    coachSource.textContent = data.coach.source === "gemini" ? "GEMINI 2.5 AI COACH" : "OFFLINE EXPERT COACH";
  }

  if (window.lucide) window.lucide.createIcons();
}

function renderMetricsList(data) {
  const container = document.getElementById("metricsList");
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
    row.className = "space-y-1.5 p-3 rounded-xl bg-slate-900/40 border border-slate-800/60";

    const badgeClass = status === "ok" ? "badge-ok" : status === "watch" ? "badge-watch" : "badge-fix";
    const statusText = status === "ok" ? "Optimal" : status === "watch" ? "Borderline" : "Adjust";

    // Min and Max bounds for range bar visualization
    const minBound = Math.min(range[0] - 20, val - 10);
    const maxBound = Math.max(range[1] + 20, val + 10);
    const totalSpan = maxBound - minBound;

    const targetLeft = Math.max(0, ((range[0] - minBound) / totalSpan) * 100);
    const targetWidth = Math.min(100, ((range[1] - range[0]) / totalSpan) * 100);
    const pointerLeft = Math.min(100, Math.max(0, ((val - minBound) / totalSpan) * 100));

    row.innerHTML = `
      <div class="flex items-center justify-between text-xs">
        <div>
          <span class="font-bold text-slate-200">${meta.label}</span>
          <span class="text-slate-400 text-[11px] block">${meta.explain}</span>
        </div>
        <div class="text-right flex items-center gap-2">
          <span class="font-mono text-sm font-bold text-white">${val.toFixed(1)}°</span>
          <span class="badge ${badgeClass}">${statusText}</span>
        </div>
      </div>

      <div class="metric-bar-bg my-2">
        <div class="metric-target-zone" style="left: ${targetLeft}%; width: ${targetWidth}%;"></div>
        <div class="metric-current-pointer" style="left: ${pointerLeft}%; color: ${status === 'ok' ? '#10b981' : status === 'watch' ? '#f59e0b' : '#f43f5e'}"></div>
      </div>

      <div class="flex justify-between text-[10px] text-slate-500 font-mono">
        <span>${range[0]}° Target Min</span>
        <span>${range[1]}° Target Max</span>
      </div>
    `;

    container.appendChild(row);
  });
}

function renderSnapshots(snapshots) {
  const container = document.getElementById("snapshotsGrid");
  if (!container) return;
  container.innerHTML = "";

  Object.entries(snapshots).forEach(([k, snap]) => {
    const card = document.createElement("div");
    card.className = "rounded-xl overflow-hidden bg-slate-900 border border-slate-800 space-y-2 group";

    card.innerHTML = `
      <div class="relative aspect-video bg-black flex items-center justify-center overflow-hidden image-outline">
        <img src="${snap.data_url}" alt="${snap.title}" class="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300">
        <span class="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-900/80 text-white backdrop-blur border border-white/10">
          ${snap.title}
        </span>
      </div>
    `;

    container.appendChild(card);
  });
}

function renderRecommendations(recommendations) {
  const container = document.getElementById("recommendationsList");
  if (!container) return;
  container.innerHTML = "";

  if (recommendations.length === 0) {
    container.innerHTML = `
      <div class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
        <i data-lucide="check-circle" class="w-5 h-5 flex-shrink-0"></i>
        <span>All measured angles are within recommended ranges for this riding style. Keep pedalling smoothly!</span>
      </div>
    `;
    return;
  }

  recommendations.forEach((r, idx) => {
    const item = document.createElement("div");
    item.className = "p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 hover:border-slate-700 transition-colors";

    const badgeCol = r.priority === 1 ? "bg-red-500/20 text-red-400 border-red-500/30" :
                     r.priority === 2 ? "bg-amber-500/20 text-amber-400 border-amber-500/30" :
                     "bg-blue-500/20 text-blue-400 border-blue-500/30";

    item.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeCol}">Priority ${r.priority}</span>
        <h5 class="font-bold text-xs text-slate-100">${idx + 1}. ${r.title}</h5>
      </div>
      <p class="text-xs text-slate-400 pl-0 sm:pl-2 leading-relaxed">${r.detail}</p>
    `;

    container.appendChild(item);
  });
}

function setupScrubber(previews) {
  state.scrubberIndex = 0;
  stopPlayback();

  const slider = document.getElementById("scrubberSlider");
  const img = document.getElementById("scrubberImg");
  const ph = document.getElementById("scrubberPlaceholder");

  if (!previews || previews.length === 0) {
    if (ph) ph.textContent = "No scrubber frames available (photo mode).";
    if (img) img.src = "";
    if (slider) slider.disabled = true;
    return;
  }

  if (slider) {
    slider.disabled = false;
    slider.min = 0;
    slider.max = previews.length - 1;
    slider.value = 0;
  }

  updateScrubberFrame(0);
}

function updateScrubberFrame(idx) {
  const previews = state.currentResult?.previews || [];
  if (!previews[idx]) return;

  state.scrubberIndex = idx;
  const item = previews[idx];

  const img = document.getElementById("scrubberImg");
  const ph = document.getElementById("scrubberPlaceholder");
  const slider = document.getElementById("scrubberSlider");
  const timeText = document.getElementById("scrubberTime");
  const counter = document.getElementById("scrubberFrameCounter");

  if (img) {
    img.src = item.data_url;
    img.classList.remove("hidden");
  }
  if (ph) ph.classList.add("hidden");
  if (slider) slider.value = idx;
  if (timeText) timeText.textContent = `${item.t.toFixed(2)}s`;
  if (counter) counter.textContent = `Frame ${idx + 1} / ${previews.length}`;
}

function initScrubberControls() {
  const slider = document.getElementById("scrubberSlider");
  slider?.addEventListener("input", (e) => {
    stopPlayback();
    updateScrubberFrame(parseInt(e.target.value, 10));
  });

  const btnPrev = document.getElementById("btnScrubPrev");
  const btnNext = document.getElementById("btnScrubNext");
  const btnPlay = document.getElementById("btnScrubPlay");

  btnPrev?.addEventListener("click", () => {
    stopPlayback();
    const previews = state.currentResult?.previews || [];
    const nextIdx = Math.max(0, state.scrubberIndex - 1);
    updateScrubberFrame(nextIdx);
  });

  btnNext?.addEventListener("click", () => {
    stopPlayback();
    const previews = state.currentResult?.previews || [];
    const nextIdx = Math.min(previews.length - 1, state.scrubberIndex + 1);
    updateScrubberFrame(nextIdx);
  });

  btnPlay?.addEventListener("click", togglePlayback);
}

function togglePlayback() {
  if (state.isPlaying) {
    stopPlayback();
  } else {
    startPlayback();
  }
}

function startPlayback() {
  const previews = state.currentResult?.previews || [];
  if (previews.length === 0) return;

  state.isPlaying = true;
  const playIcon = document.getElementById("playIcon");
  if (playIcon) playIcon.setAttribute("data-lucide", "pause");
  if (window.lucide) window.lucide.createIcons();

  state.playTimer = setInterval(() => {
    let next = state.scrubberIndex + 1;
    if (next >= previews.length) next = 0;
    updateScrubberFrame(next);
  }, 66); // ~15 fps playback
}

function stopPlayback() {
  state.isPlaying = false;
  if (state.playTimer) {
    clearInterval(state.playTimer);
    state.playTimer = null;
  }
  const playIcon = document.getElementById("playIcon");
  if (playIcon) playIcon.setAttribute("data-lucide", "play");
  if (window.lucide) window.lucide.createIcons();
}

async function downloadPDF() {
  if (!state.currentResult) return;

  const btn = document.getElementById("btnDownloadPDF");
  const origHtml = btn?.innerHTML;
  if (btn) btn.innerHTML = "<span>Generating PDF...</span>";

  try {
    const riderName = localStorage.getItem(STORAGE_RIDER_NAME) || "Cyclist";
    const coachText = state.currentResult.coach?.text || "";

    const resp = await fetch("/api/generate_pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        result: state.currentResult,
        rider_name: riderName,
        coach_text: coachText,
      }),
    });

    if (!resp.ok) throw new Error("PDF generation failed");

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `nintai_fit_report_${state.currentResult.profile}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (err) {
    console.error("PDF Download error:", err);
    alert(`PDF generation failed: ${err.message}`);
  } finally {
    if (btn && origHtml) btn.innerHTML = origHtml;
    if (window.lucide) window.lucide.createIcons();
  }
}
