# NintAi: The Open-Source Biomechanical Bike Fit & Kinematics Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-334155.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Pose Tracking](https://img.shields.io/badge/Pose%20Engine-33--Landmark%20BlazePose%20Heavy-0284c7.svg?style=flat-square)](https://developers.google.com/mediapipe)
[![AI Diagnostics](https://img.shields.io/badge/Diagnostic%20Engine-Claude%20%7C%20Gemini%20%7C%20Offline-475569.svg?style=flat-square)](https://claude.ai/)
[![Interface](https://img.shields.io/badge/Studio%20UI-Streamlit-0f172a.svg?style=flat-square)](https://streamlit.io/)
[![Colab Demo](https://img.shields.io/badge/Cloud%20Demo-Google%20Colab-d97706.svg?style=flat-square)](https://colab.research.google.com/github/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio/blob/main/notebooks/NintAi_Google_Colab_Demo.ipynb)

A high-precision, open-source dynamic motion capture suite and clinical bike fitting platform. Operates on standard 2D video footage using 33-point sub-millimeter computer vision kinematics, adaptive 1€ signal filtering, and multi-provider AI diagnostic consultations (Anthropic Claude, Google Gemini, and 100% Offline Rule-Based Biomechanical Engine).

---

## The Human Story: Why Bike Fit Matters

Cycling is a sport of brutal, continuous repetition. At a standard cadence of 90 RPM, your legs complete **5,400 pedal revolutions every single hour**. Over a typical 50-mile weekend ride, that exceeds 16,000 continuous joint cycles.

When your contact points are misaligned by as little as **4 to 6 millimeters**, that tiny geometric error compounds into 16,000 micro-traumas. The patellar tendon gets crushed against the femoral groove (saddle too low), the biceps femoris is repeatedly over-stretched at the bottom of the stroke (saddle too high), or the lumbar spine flexes into severe kyphosis to compensate for an excessively long reach.

### The Mechanic & The Car Analogy

> **Taking your bike to an experienced, certified professional bike fitter is like taking a car to a certified master mechanic.**

A master fitter in a clinical studio evaluates your physical mobility off the bike, checks for leg-length discrepancies, measures pelvic tilt, and applies custom footbed orthotics. **A certified in-person professional fit is the gold standard, and we wholeheartedly recommend getting a professional fit done.**

However, commercial in-studio fits typically cost **$350 to $500+ per session**, making regular checkups, saddle swaps, or seasonal adjustments financially inaccessible for millions of cyclists worldwide.

Just like a passionate car enthusiast uses an OBD-II diagnostic scanner in their garage to analyze engine telemetry, monitor fuel trims, and tune their own suspension—**if you understand the underlying principles, you can dial in your fit too**.

**NintAi is built to be your open-source diagnostic telemetry suite.** It gives you the dynamic motion capture, sub-millimeter angle tracking, 4-phase stroke decomposition, and structured action plans to iterate quickly at home for free. You can use it as a foundation to refine your position, or as a diagnostic baseline before visiting a professional fitter.

---

## Biomechanical Thesis & Literature

The kinematic models and angular thresholds implemented in NintAi are grounded in established clinical cycling biomechanics literature:

1. **Holmes Knee Angle Method (1994):** Evaluates knee flexion/extension at Bottom Dead Center (BDC 6 o'clock). Recommends an included knee angle of **140°–150°** (equivalent to 30°–40° flexion from full extension) to minimize patellofemoral compressive force while preventing hamstring strain.
2. **Pruitt Dynamic Flexion Bounds:** Evaluates maximum knee flexion at Top Dead Center (TDC 12 o'clock), enforcing a minimum of **68°–75°** to avoid acute patellar shear stress and hip impingement.
3. **Closed Hip Angle & Diaphragmatic Clearance:** Enforces a minimum hip angle of **45°–55°** (Road) / **40°–48°** (TT) at TDC to ensure unobstructed diaphragmatic breathing and preserve power output.
4. **Knee Over Pedal Spindle (KOPS):** Plumb-line spatial tracking at 3 o'clock power phase to balance quadriceps vs gluteal recruitment.
5. **Dynamic Ankling Dynamics:** Evaluates ankle plantarflexion vs dorsiflexion at BDC (**90°–105°**) to detect compensatory toe-pointing caused by excessive saddle height.

---

## Comparison Matrix

| Parameter | Retül 3D Vantage | MyVeloFit | Bike Fast Fit | NintAi Kinematics Suite |
| :--- | :---: | :---: | :---: | :---: |
| **Licensing** | Commercial ($350+/session) | Subscription ($75–$150/yr) | iOS App ($4.99/mo) | **100% Free & Open Source (MIT)** |
| **Tracking Density** | 8 LED active markers | 17 standard 2D keypoints | 8 manual/auto points | **33 Anatomical 3D Landmarks** |
| **Foot Kinematics** | Physical Wand | Virtual Approximation | 2D Foot Angle | **True Heel & Toe Vector Tracking** |
| **Temporal Filtering** | Hardware Filter | Moving Average | Frame Interpolation | **Adaptive 1€ Filter + Bone Invariance** |
| **Diagnostic Engine** | In-Person Technician | Template AI Coach | Manual Angle Protractor | **Claude 3.7/3.5 + Gemini + Offline Engine** |
| **Data Privacy** | In-Studio Only | Cloud Server Upload | Local Device | **100% Local / Offline Processing** |

---

## Core Capabilities

- **33-Keypoint BlazePose Heavy Tracker:** High-frequency skeletal tracking including heel, toe, ankle, knee, hip, shoulder, elbow, wrist, and neck coordinates.
- **Harmonic 4-Phase Stroke Decomposition:** Automatically segments pedaling cycles into Top Dead Center (TDC 12h), Peak Power Delivery (3h), Bottom Dead Center (BDC 6h), and Kinetic Profile.
- **Physiological Bone Invariance:** Enforces rigid segment constraints along the femur, tibia, and torso axes to eliminate perspective jitter.
- **Multi-Provider AI Diagnostic Engine:**
  - **Anthropic Claude (3.7 / 3.5 Sonnet):** Deep physiological reasoning with exact millimeter prescriptions.
  - **Google Gemini (2.0 Flash / 1.5 Pro):** Rapid multimodal diagnostic consultations.
  - **Offline Biomechanical Engine:** 100% local, zero-API-key deterministic clinical evaluation.
- **Dossier Generation:** Compiles multi-page PDF reports with annotated high-resolution stills, metric tables, and clinical action plans.

---

## Biomechanical Reference Standards

```
                          BIOMECHANICAL REFERENCE RANGES
 ┌───────────────────────────┬──────────────┬──────────────┬──────────────┐
 │ Kinematic Metric          │ Road Racing  │ TT / Tri     │ Gravel/Endur │
 ├───────────────────────────┼──────────────┼──────────────┼──────────────┤
 │ Knee Extension (BDC 6h)   │ 140° - 150°  │ 145° - 153°  │ 138° - 148°  │
 │ Knee Flexion (TDC 12h)    │ 68° - 75°    │ 65° - 72°    │ 70° - 78°    │
 │ Closed Hip Angle (TDC)    │ 45° - 55°    │ 40° - 48°    │ 50° - 60°    │
 │ Torso Incline to Horiz.   │ 40° - 50°    │ 15° - 25°    │ 45° - 55°    │
 │ Shoulder / Cockpit Angle  │ 85° - 95°    │ 80° - 90°    │ 85° - 95°    │
 │ Ankle Angle at BDC        │ 90° - 105°   │ 95° - 110°   │ 90° - 100°   │
 └───────────────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## Directory Architecture

```
NintAi/
├── inputs/
│   ├── videos/              # Raw cycling video footage
│   └── images/              # Frame and geometry photos
├── outputs/
│   ├── videos/              # Annotated kinematic video streams
│   ├── reports/             # Clinical PDF dossiers
│   └── snapshots/           # 4-phase diagnostic stills
├── models/                  # Neural weights & task models
├── src/
│   ├── __init__.py          # Package initialization
│   ├── tracker.py           # Unified 33-point pose tracker
│   ├── kinematics.py        # Biomechanical formulations & 1€ filter
│   ├── analyzer.py          # Dynamic video kinematics processor
│   ├── ai_fitter.py         # Multi-provider diagnostic engine (Claude/Gemini/Offline)
│   └── pdf_generator.py     # Clean vector PDF report compiler
├── notebooks/
│   └── NintAi_Google_Colab_Demo.ipynb # Cloud GPU demo
├── scripts/
│   └── download_models.py   # Model dependency installer
├── app.py                   # Studio Web UI
├── Dockerfile               # Production container image
├── docker-compose.yml       # Local compose configuration
├── pyproject.toml           # Package configuration
└── requirements.txt         # Dependency manifest
```

---

## Quickstart

### 1. Installation

```bash
git clone https://github.com/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio.git
cd NintAi-The-AI-Powered-Bike-Fit-Studio

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_models.py
```

### 2. Launch Web Studio

```bash
streamlit run app.py --server.port=8080
```
Navigate to `http://localhost:8080` in your web browser.

---

## Disclaimer & Safety Note

NintAi is an educational and diagnostic software tool designed for cyclists and fit enthusiasts. It is not a replacement for medical diagnosis or physical therapy. If you experience persistent sharp pain, neurological numbness, or weakness while cycling, cease adjustments immediately and consult a certified medical professional or sports physiotherapist.

---

## License

Distributed under the MIT License. See `LICENSE` for details.
