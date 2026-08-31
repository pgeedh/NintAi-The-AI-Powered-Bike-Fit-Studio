# Open-BikeFit ⚡
### The Open-Source Biomechanical Bike Fit Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-black.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-BlazePose%2033KP-0A84FF.svg?style=flat-square)](https://developers.google.com/mediapipe)
[![Streamlit](https://img.shields.io/badge/Studio-Apple%20HIG%20Dark-30D158.svg?style=flat-square)](http://localhost:8080)

**Open-BikeFit** is a high-precision, open-source dynamic bike fitting studio. It transforms standard 30/60 FPS trainer video into multi-revolution biomechanical joint angle telemetry, 4-phase pedal stroke breakdowns, and professional millimeter hardware adjustment reports.

---

## 📖 The Story: Why Open-BikeFit Exists

### The $500 Barrier in Cycling
A professional 3D bike fitting session at a specialized studio costs between **$350 and $500**. For many cyclists, triathletes, and beginners, this cost is a significant barrier.

Furthermore, dynamic bike fitting is not a one-time static event — it is an **iterative process**. Whenever you:
- Swap your saddle or saddle height,
- Install new cycling shoes or cleats,
- Upgrade handlebars, stems, or crank lengths,
- Experience fitness, flexibility, or weight changes over a season,

you need to re-verify your joint angles. Waiting weeks and paying hundreds of dollars for every minor adjustment slows down your progression and comfort.

### The Mechanic & Car Analogy
> *"Taking your car to a certified master mechanic is great for deep diagnostic work and complex overhauls. But if you understand how your engine works and have access to diagnostic telemetry, you can tune, maintain, and iterate on your vehicle with precision."*

Getting an in-person fitting by a master fitter is valuable. But **Open-BikeFit** provides every cyclist and enthusiast with an accessible, high-precision computer vision baseline tool at home — enabling rapid kinematic angle calculation and actionable millimeter wrench guidance in minutes.

> [!NOTE]
> **Kinematic Baseline Disclaimer:** Open-BikeFit is a geometric kinematic posture estimation tool designed to assist riders and bike fitters. It is not a medical device or physical therapy diagnostic service.

---

## ✨ Features & Architecture

```
                                  OPEN-BIKEFIT STUDIO PIPELINE
  ┌──────────────────┐     ┌─────────────────────┐     ┌────────────────────────┐
  │  Rider Intake &  │ ──► │  Studio Setup &     │ ──► │  BlazePose 33-Landmark │
  │  Profile Goal    │     │  Calibration Check  │     │  Sub-Pixel CV Engine   │
  └──────────────────┘     └─────────────────────┘     └────────────────────────┘
                                                                   │
                                                                   ▼
  ┌──────────────────┐     ┌─────────────────────┐     ┌────────────────────────┐
  │ Professional Fit │ ◄── │  Apple HIG Studio   │ ◄── │  1€ Adaptive Filter &  │
  │ Report & Wrench  │     │  Telemetry Gauges   │     │  Kinematic Math Solver │
  └──────────────────┘     └─────────────────────┘     └────────────────────────┘
```

1. **Apple Human Interface Guidelines (HIG) UI:**
   - Deep monochromatic dark design (`#000000`, `#1C1C1E`, `#2C2C2E`).
   - Cupertino system accent color palette (`#0A84FF` Blue, `#30D158` Green, `#FF9F0A` Amber, `#FF453A` Red).
   - Zero cartoon emojis; clean typography and high-contrast telemetry cards.
2. **Multi-Step Onboarding Stepper (MyVeloFit Inspired):**
   - **Step 1: Rider Intake & Account:** Name, Email, Height, Inseam, Discipline (Road, Gravel, TT/Triathlon, MTB), Flexibility, and Pain Point Checklist.
   - **Step 2: Setup & Calibration:** 5-point studio checklist for camera distance (2.5–3.5m), height (~70cm), orientation, and attire.
   - **Step 3: Video Input & Inspection:** Instant sample datasets or custom video upload with pre-flight resolution/FPS validation.
   - **Step 4: Kinematic Motion Capture:** MediaPipe BlazePose Heavy 33-landmark tracking + 1€ adaptive filtering + bone length constraint.
   - **Step 5: Telemetry Dashboard:** Metric cards with target range gauges, side-by-side video playback, and 4-phase stills (TDC, Power, BDC, Overall).
   - **Step 6: Studio Fit Report & Wrench Guide:** Multi-provider report generation (Claude 3.7 / Claude 3.5, Gemini 2.0 Flash, or 100% Offline Rule Engine) + high-res PDF export + JSON fit profile.
3. **Deterministic Kinematic Math & Guardrails:**
   - All joint angle mathematics are calculated locally using strict deterministic trigonometry.
   - External LLM API keys are used **strictly for formatting and generating the written narrative report & wrench instructions**.

---

## 📐 Kinematic Math & Reference Targets

### 1. Knee Extension at BDC (6 o'clock)
Measured at maximum pedal extension (Bottom Dead Center) using the **Holmes et al. protocol**:
$$\theta_{\text{knee}} = \arccos\left(\frac{\mathbf{v}_{\text{femur}} \cdot \mathbf{v}_{\text{tibia}}}{\|\mathbf{v}_{\text{femur}}\| \|\mathbf{v}_{\text{tibia}}\|}\right)$$
- **Road Target:** $140^\circ - 150^\circ$ (Prevents patellar compression while avoiding hamstring strain).

### 2. Knee Flexion at TDC (12 o'clock)
Measured at minimum leg extension (Top Dead Center) using the **Pruitt formulation**:
- **Road Target:** $68^\circ - 75^\circ$ (Protects the anterior knee and ensures hip clearance).

### 3. Closed Hip Angle (12 o'clock)
Interior angle formed by the torso vector and femur vector at top of pedal stroke:
$$\theta_{\text{hip}} = \arccos\left(\frac{(\mathbf{p}_{\text{shoulder}} - \mathbf{p}_{\text{hip}}) \cdot (\mathbf{p}_{\text{knee}} - \mathbf{p}_{\text{hip}})}{\|\mathbf{p}_{\text{shoulder}} - \mathbf{p}_{\text{hip}}\| \|\mathbf{p}_{\text{knee}} - \mathbf{p}_{\text{hip}}\|}\right)$$
- **Road Target:** $45^\circ - 55^\circ$ (Maintains open diaphragm and smooth breathing).

### 4. Reference Range Comparison by Discipline

| Kinematic Metric | Road Endurance | Road Race / Aero | Gravel & All-Road | Triathlon & TT | MTB (XC) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Knee Extension (BDC 6h)** | $140^\circ - 148^\circ$ | $142^\circ - 150^\circ$ | $138^\circ - 148^\circ$ | $145^\circ - 153^\circ$ | $135^\circ - 145^\circ$ |
| **Knee Flexion (TDC 12h)** | $70^\circ - 76^\circ$ | $68^\circ - 74^\circ$ | $70^\circ - 78^\circ$ | $65^\circ - 72^\circ$ | $72^\circ - 80^\circ$ |
| **Closed Hip Angle (TDC)** | $48^\circ - 56^\circ$ | $44^\circ - 52^\circ$ | $50^\circ - 60^\circ$ | $40^\circ - 48^\circ$ | $55^\circ - 65^\circ$ |
| **Torso Incline (to horiz.)**| $42^\circ - 50^\circ$ | $36^\circ - 44^\circ$ | $45^\circ - 55^\circ$ | $15^\circ - 25^\circ$ | $50^\circ - 60^\circ$ |
| **Shoulder / Reach Angle** | $85^\circ - 92^\circ$ | $88^\circ - 95^\circ$ | $85^\circ - 95^\circ$ | $80^\circ - 90^\circ$ | $90^\circ - 100^\circ$ |
| **Ankling at BDC** | $90^\circ - 102^\circ$ | $92^\circ - 105^\circ$ | $90^\circ - 100^\circ$ | $95^\circ - 110^\circ$ | $85^\circ - 95^\circ$ |

---

## ⚡ Comparison with Commercial Systems

| Feature | Retül 3D Studio | MyVeloFit | BikeFastFit | **Open-BikeFit** |
| :--- | :---: | :---: | :---: | :---: |
| **Cost** | $350 – $500 | $35 – $75/yr | $15 App | **100% Free & Open Source** |
| **Hardware Required** | Optical LED Harness | Web Browser / Cam | iOS Device | **Any Computer (Linux/Mac/Win)** |
| **Keypoint Density** | 8 LED Markers | 17 Keypoints | Manual Taps | **33 Heavy Landmarks (BlazePose)** |
| **Foot Kinematics** | Heel Only | Basic Ankle | None | **Ankle, Heel & Toe (3D Vector)** |
| **Studio Report Engine** | Proprietary PDF | Cloud Automated | Basic Overlay | **Claude 3.7 / Gemini / 100% Offline** |
| **Privacy / Local Run** | Studio Only | Cloud Upload | Local Device | **100% Local Processing** |

---

## 🚀 Quick Start Guide

### 1. Clone & Setup Environment
```bash
git clone https://github.com/pgeedh/Open-BikeFit-The-AI-Powered-Bike-Fit-Studio.git
cd Open-BikeFit-The-AI-Powered-Bike-Fit-Studio

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Download Model Weights
```bash
python scripts/download_models.py
```

### 3. Launch the Studio Web App
```bash
streamlit run app.py --server.port=8080
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

---

## 📁 Repository Directory Structure

```
Open-BikeFit/
├── app.py                     # Apple HIG Multi-Step Studio Web App
├── src/
│   ├── tracker.py             # MediaPipe BlazePose Heavy 33-Landmark Tracker
│   ├── kinematics.py          # Biomechanical Angle Formulations & 1€ Filter
│   ├── ai_fitter.py           # Studio Report Engine (Claude / Gemini / Offline)
│   ├── pdf_generator.py       # High-Resolution PDF Studio Report Builder
│   └── analyzer.py            # Video Motion Capture Pipeline CLI
├── inputs/
│   ├── videos/                # Sample and uploaded trainer rides
│   └── images/                # Reference test frames & geometry
├── outputs/
│   ├── videos/                # Annotated motion capture MP4s
│   ├── snapshots/             # 4-Phase cycle stills (TDC, Power, BDC, Overall)
│   └── reports/               # Compiled PDF fit reports
├── models/                    # Model tasks and checkpoints
└── scripts/
    └── download_models.py     # Automated neural asset downloader
```

---

## 📄 License
This project is licensed under the **MIT License**.
