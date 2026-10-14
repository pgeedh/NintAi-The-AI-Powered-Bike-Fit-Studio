/**
 * NintAi Studio — Precision Motion Biomechanics Studio Logic
 * Adheres to UI Skills & Design Engineering Standards
 */

const state = {
  config: null,
  selectedSampleId: "testvideo2.mp4",
  uploadedFile: null,
  profile: "tri_tt",
  result: null,
  scrubberIdx: 0,
  isPlaying: false,
  playTimer: null,
  playSpeed: 1.0,
};

const STORAGE_KEY = "nintai_gemini_key";
const STORAGE_RIDER = "nintai_rider_name";

document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) window.lucide.createIcons();
  loadSettings();
  setupUIEvents();
  setupKeyboardShortcuts();
  await loadConfig();

  // Instant gratification: Auto-run initial analysis on default sample so the user lands on an active studio
  setTimeout(() => {
    executeFitAnalysis(true);
  }, 300);
});

function showToast(message, icon = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `
    <i data-lucide="${icon}" class="w-4 h-4 text-blue-400 flex-shrink-0"></i>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  if (window.lucide) window.lucide.createIcons();

  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 200);
  }, 3200);
}

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
    if (!res.ok) throw new Error("Failed to load studio configuration");
    state.config = await res.json();

    renderSampleList(state.config.samples || []);
  } catch (err) {
    console.error("Config load error:", err);
    showToast("Failed to connect to NintAi backend engine", "alert-circle");
  }
}

function renderSampleList(samples) {
  const list = document.getElementById("samplePickerList");
  if (!list) return;
  list.innerHTML = "";

  // Priority display for standard test clips
  const priority = ["testvideo2.mp4", "testvideo.mp4", "1.jpg", "4.jpeg"];
  const sorted = [...samples].sort((a, b) => {
    const ai = priority.indexOf(a.id);
    const bi = priority.indexOf(b.id);
    return (ai !== -1 ? ai : 99) - (bi !== -1 ? bi : 99);
  });

  sorted.slice(0, 4).forEach((s) => {
    const item = document.createElement("div");
    const isSelected = s.id === state.selectedSampleId && !state.uploadedFile;
    item.className = `p-2.5 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
      isSelected
        ? "bg-blue-950/40 border-blue-500/70 text-white font-medium"
        : "bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800/80"
    }`;
    item.dataset.id = s.id;

    const icon = s.type === "video" ? "film" : "image";
    const label = s.id === "testvideo2.mp4" ? "Triathlon TT (testvideo2.mp4)" : s.id === "testvideo.mp4" ? "Road Race (testvideo.mp4)" : s.id;

    item.innerHTML = `
      <div class="flex items-center gap-2 truncate">
        <i data-lucide="${icon}" class="w-3.5 h-3.5 ${isSelected ? 'text-blue-400' : 'text-slate-400'} flex-shrink-0"></i>
        <span class="truncate">${label}</span>
      </div>
      <span class="text-[10px] font-mono text-slate-500 uppercase">${s.type}</span>
    `;

    item.addEventListener("click", () => {
      state.selectedSampleId = s.id;
      state.uploadedFile = null;
      document.getElementById("activeSourceLabel").textContent = `${s.id} (${s.type})`;
      renderSampleList(samples);
      showToast(`Selected sample: ${s.id}`, "check");
      executeFitAnalysis(false);
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
      showToast(`Profile: ${state.config?.profiles[state.profile]?.name || state.profile}`, "activity");
      
      // If we already have results, re-score instantly with new profile ranges!
      if (state.result) {
        executeFitAnalysis(false);
      }
    });
  });

  // Speed controls
  const btn1x = document.getElementById("btnSpeed1x");
  const btn05x = document.getElementById("btnSpeed05x");
  btn1x?.addEventListener("click", () => {
    state.playSpeed = 1.0;
    btn1x.className = "px-1.5 py-0.5 rounded text-white font-semibold bg-slate-800";
    btn05x.className = "px-1.5 py-0.5 rounded hover:text-white";
    if (state.isPlaying) {
      stopPlay();
      startPlay();
    }
  });
  btn05x?.addEventListener("click", () => {
    state.playSpeed = 0.5;
    btn05x.className = "px-1.5 py-0.5 rounded text-white font-semibold bg-slate-800";
    btn1x.className = "px-1.5 py-0.5 rounded hover:text-white";
    if (state.isPlaying) {
      stopPlay();
      startPlay();
    }
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
      showToast(`Uploaded ${f.name}. Click Analyze.`, "upload");
    }
  });

  // Run analysis button
  document.getElementById("btnRunFit")?.addEventListener("click", () => executeFitAnalysis(false));

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
    const key = document.getElementById("geminiKeyInput")?.value.trim() || "";
    const name = document.getElementById("riderNameInput")?.value.trim() || "";
    localStorage.setItem(STORAGE_KEY, key);
    localStorage.setItem(STORAGE_RIDER, name);
    loadSettings();
    settingsModal?.classList.remove("open");
    showToast("Settings saved successfully", "check");
  });
}

function setupKeyboardShortcuts() {
  window.addEventListener("keydown", (e) => {
    // Ignore keystrokes inside input / select
    if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
      if (e.key === "Escape") {
        document.getElementById("settingsModal")?.classList.remove("open");
        document.getElementById("guideModal")?.classList.remove("open");
      }
      return;
    }

    if (e.code === "Space") {
      e.preventDefault();
      togglePlay();
    } else if (e.code === "ArrowLeft") {
      e.preventDefault();
      stopPlay();
      const delta = e.shiftKey ? 5 : 1;
      renderScrubberFrame(Math.max(0, state.scrubberIdx - delta));
    } else if (e.code === "ArrowRight") {
      e.preventDefault();
      stopPlay();
      const previews = state.result?.previews || [];
      const delta = e.shiftKey ? 5 : 1;
      renderScrubberFrame(Math.min(previews.length - 1, state.scrubberIdx + delta));
    } else if (e.key === "1") {
      selectDisciplineByIndex(0);
    } else if (e.key === "2") {
      selectDisciplineByIndex(1);
    } else if (e.key === "3") {
      selectDisciplineByIndex(2);
    } else if (e.key === "4") {
      selectDisciplineByIndex(3);
    } else if (e.key === "e" || e.key === "E") {
      const btn = document.getElementById("btnDownloadPDF");
      if (btn && !btn.disabled) exportPDF();
    } else if (e.key === "?") {
      document.getElementById("guideModal")?.classList.toggle("open");
    } else if (e.key === "Escape") {
      document.getElementById("settingsModal")?.classList.remove("open");
      document.getElementById("guideModal")?.classList.remove("open");
    }
  });
}

function selectDisciplineByIndex(index) {
  const segments = document.querySelectorAll("#profileSegmented .segment-item");
  if (segments[index]) {
    segments[index].click();
  }
}

async function executeFitAnalysis(isSilentInit = false) {
  const loading = document.getElementById("stageLoading");
  const placeholder = document.getElementById("stagePlaceholder");
  const stageImg = document.getElementById("stageImg");
  const btnRun = document.getElementById("btnRunFit");

  loading?.classList.remove("hidden");
  placeholder?.classList.add("hidden");
  if (btnRun) btnRun.disabled = true;

  if (!isSilentInit) {
    showToast("Analyzing biomechanics with SOTA pose estimation...", "loader-2");
  }

  const formData = new FormData();
  if (state.uploadedFile) {
    formData.append("file", state.uploadedFile);
  } else if (state.selectedSampleId) {
    formData.append("sample_id", state.selectedSampleId);
  } else {
    showToast("Please select a sample or upload a video clip", "alert-circle");
    loading?.classList.add("hidden");
    placeholder?.classList.remove("hidden");
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
    showToast(`Biomechanics computed: Score ${data.score}/100`, "award");
  } catch (err) {
    console.error("Analysis failure:", err);
    showToast(`Error: ${err.message}`, "alert-triangle");
    placeholder?.classList.remove("hidden");
  } finally {
    loading?.classList.add("hidden");
    if (btnRun) btnRun.disabled = false;
  }
}

function renderStudioResults(data) {
  // 1. Overall Fit Score & Pill
  const scoreCard = document.getElementById("scoreSummaryCard");
  const scoreVal = document.getElementById("scoreValue");
  const statusPill = document.getElementById("fitStatusPill");
  if (scoreCard && scoreVal && statusPill) {
    scoreCard.classList.remove("hidden");
    scoreVal.textContent = data.score !== null ? data.score : "--";
    if (data.score >= 80) {
      statusPill.textContent = "Optimal";
      statusPill.className = "status-pill status-ok";
      scoreVal.className = "text-2xl font-bold font-mono text-emerald-400";
      scoreCard.className = "inspector-card space-y-3 border-l-4 border-l-emerald-500";
    } else if (data.score >= 60) {
      statusPill.textContent = "Borderline";
      statusPill.className = "status-pill status-watch";
      scoreVal.className = "text-2xl font-bold font-mono text-amber-400";
      scoreCard.className = "inspector-card space-y-3 border-l-4 border-l-amber-500";
    } else {
      statusPill.textContent = "Adjust";
      statusPill.className = "status-pill status-fix";
      scoreVal.className = "text-2xl font-bold font-mono text-rose-400";
      scoreCard.className = "inspector-card space-y-3 border-l-4 border-l-rose-500";
    }
  }

  // 2. HUD Chips & Dots
  const m = data.metrics || {};
  const b = data.biomech || {};
  
  const kneeEl = document.getElementById("hudKneeExt");
  if (kneeEl) kneeEl.textContent = m.knee_ext ? `${m.knee_ext.toFixed(1)}°` : "--°";

  const hipEl = document.getElementById("hudHip");
  if (hipEl) hipEl.textContent = m.hip_closed ? `${m.hip_closed.toFixed(1)}°` : "--°";

  const cadEl = document.getElementById("hudCadence");
  if (cadEl) cadEl.textContent = b.cadence_rpm ? `${b.cadence_rpm.toFixed(0)} RPM` : "-- RPM";

  const kopsEl = document.getElementById("hudKops");
  if (kopsEl) {
    kopsEl.textContent = b.kops_mm !== undefined && b.kops_mm !== null
      ? `${b.kops_mm > 0 ? "+" : ""}${b.kops_mm.toFixed(0)} mm`
      : "-- mm";
  }

  const engineLabel = document.getElementById("hudEngineLabel");
  if (engineLabel && data.backend_name) {
    engineLabel.textContent = data.backend_name;
  }

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
    const stageImg = document.getElementById("stageImg");
    if (stageImg) stageImg.src = data.snapshots.photo.data_url;
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

  // Update dynamic phase indicator chip
  const phaseName = document.getElementById("hudPhaseName");
  if (phaseName && previews.length > 0) {
    const progress = idx / previews.length;
    if (progress < 0.20) {
      phaseName.textContent = "Top Dead Center (0°)";
    } else if (progress < 0.45) {
      phaseName.textContent = "Power Phase / KOPS (90°)";
    } else if (progress < 0.70) {
      phaseName.textContent = "Bottom Dead Center (180°)";
    } else {
      phaseName.textContent = "Recovery Upstroke (270°)";
    }
  }
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
  if (icon) {
    icon.setAttribute("data-lucide", "pause");
    icon.classList.remove("icon-play-nudge");
  }
  if (window.lucide) window.lucide.createIcons();

  const interval = (66 / state.playSpeed);
  state.playTimer = setInterval(() => {
    let next = state.scrubberIdx + 1;
    if (next >= previews.length) next = 0;
    renderScrubberFrame(next);
  }, interval);
}

function stopPlay() {
  state.isPlaying = false;
  if (state.playTimer) {
    clearInterval(state.playTimer);
    state.playTimer = null;
  }
  const icon = document.getElementById("playIcon");
  if (icon) {
    icon.setAttribute("data-lucide", "play");
    icon.classList.add("icon-play-nudge");
  }
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

    const card = document.createElement("div");
    card.className = "range-gauge-card space-y-1.5";

    const statusPillClass = status === "ok" ? "status-ok" : status === "watch" ? "status-watch" : "status-fix";
    const statusText = status === "ok" ? "In Range" : status === "watch" ? "Watch" : "Adjust";

    const span = Math.max(range[1] - range[0], 20);
    const minBound = range[0] - span * 0.7;
    const maxBound = range[1] + span * 0.7;
    const total = maxBound - minBound;

    const leftPct = Math.max(0, ((range[0] - minBound) / total) * 100);
    const widthPct = Math.min(100, ((range[1] - range[0]) / total) * 100);
    const dotPct = Math.min(100, Math.max(0, ((val - minBound) / total) * 100));

    card.innerHTML = `
      <div class="flex items-center justify-between text-xs">
        <div>
          <span class="text-slate-200 font-semibold block">${meta.short || meta.label}</span>
          <span class="text-[10px] text-slate-500">${meta.label}</span>
        </div>
        <div class="flex items-center gap-2 font-mono">
          <span class="font-bold text-white text-sm">${val.toFixed(1)}°</span>
          <span class="status-pill ${statusPillClass}">${statusText}</span>
        </div>
      </div>

      <div class="range-track">
        <div class="range-zone" style="left: ${leftPct}%; width: ${widthPct}%;"></div>
        <div class="range-dot" style="left: ${dotPct}%;"></div>
      </div>

      <div class="flex justify-between text-[10px] text-slate-500 font-mono">
        <span>Min: ${range[0]}°</span>
        <span class="text-emerald-500/80">Target Band</span>
        <span>Max: ${range[1]}°</span>
      </div>
    `;

    container.appendChild(card);
  });
}

function renderPrescriptions(data) {
  const container = document.getElementById("prescriptionsList");
  if (!container) return;
  container.innerHTML = "";

  const recs = data.recommendations || [];
  if (recs.length === 0) {
    container.innerHTML = `
      <div class="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
        <i data-lucide="check-circle" class="w-4 h-4 flex-shrink-0"></i>
        <span>All observed joint angles are in optimal alignment with ${data.profile_name} target specifications.</span>
      </div>
    `;
  } else {
    recs.forEach((r) => {
      const el = document.createElement("div");
      el.className = "p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1";
      el.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800/60">P${r.priority}</span>
            <strong class="text-slate-200 text-xs">${r.title}</strong>
          </div>
          <span class="text-[10px] text-slate-500 font-mono">${r.key || 'Adjustment'}</span>
        </div>
        <p class="text-[11px] text-slate-400 leading-snug text-pretty">${r.detail}</p>
      `;
      container.appendChild(el);
    });
  }

  // Coach verdict narrative
  const coachBox = document.getElementById("coachBox");
  const coachTag = document.getElementById("coachTypeTag");
  if (coachBox && data.coach?.text) {
    coachBox.textContent = data.coach.text;
    coachBox.classList.remove("hidden");
  }
  if (coachTag && data.coach?.source) {
    coachTag.textContent = data.coach.source === "gemini" ? "Google Gemini 2.5 AI" : "Built-in Biomechanist";
  }
}

function renderSnapshotsStrip(snaps) {
  const strip = document.getElementById("snapshotsStrip");
  const container = document.getElementById("snapshotsContainer");
  if (!strip || !container) return;

  const keys = Object.keys(snaps);
  if (keys.length === 0) {
    strip.classList.add("hidden");
    return;
  }

  strip.classList.remove("hidden");
  container.innerHTML = "";

  keys.slice(0, 3).forEach((k) => {
    const s = snaps[k];
    const col = document.createElement("div");
    col.className = "rounded-lg overflow-hidden border border-slate-800 bg-slate-900 group cursor-pointer";
    col.innerHTML = `
      <div class="aspect-video relative overflow-hidden bg-black">
        <img src="${s.data_url}" alt="${s.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200">
      </div>
      <div class="p-2 text-center text-[10px] font-mono text-slate-400 truncate">
        ${s.title}
      </div>
    `;
    col.addEventListener("click", () => {
      const stage = document.getElementById("stageImg");
      if (stage) stage.src = s.data_url;
      showToast(`Viewing snapshot: ${s.title}`, "image");
    });
    container.appendChild(col);
  });
}

async function exportPDF() {
  if (!state.result) {
    showToast("Please run analysis first before exporting report", "alert-circle");
    return;
  }

  showToast("Generating publication-quality PDF report...", "file-text");

  try {
    const resp = await fetch("/api/report/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        metrics: state.result.metrics,
        profile: state.profile,
        profile_name: state.result.profile_name,
        score: state.result.score,
        statuses: state.result.statuses,
        recommendations: state.result.recommendations,
        warnings: state.result.warnings,
        coach_text: state.result.coach?.text || "",
        coach_source: state.result.coach?.source || "",
        biomech: state.result.biomech || {},
        backend_name: state.result.backend_name || "",
        rider_name: localStorage.getItem(STORAGE_RIDER) || "Rider",
      }),
    });

    if (!resp.ok) throw new Error("PDF generation failed");

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `NintAi_Fit_Report_${state.profile}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    showToast("Fit Report PDF downloaded successfully!", "download");
  } catch (err) {
    console.error("PDF export failure:", err);
    showToast(`PDF Error: ${err.message}`, "alert-triangle");
  }
}
