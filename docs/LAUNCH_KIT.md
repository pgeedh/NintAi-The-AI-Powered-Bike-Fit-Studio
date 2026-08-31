# 🚀 Open-BikeFit Launch & Community Playbook

This kit provides ready-to-publish social copy, launch announcements, and distribution strategies for **Open-BikeFit** — the open-source biomechanical bike fit studio.

---

## 1. 🐦 X (Twitter) Viral Thread Template

**Tweet 1 (Hook + Video/GIF):**
> 🚴 Professional 3D bike fits cost $350-$500.
> 
> So I built **Open-BikeFit** — a 100% free, open-source biomechanical bike fitting studio that turns your laptop into a precision kinematic analysis studio.
> 
> Apple HIG design + MediaPipe 33-Keypoint Heavy Pose + Claude/Gemini report generation.
> 
> Here's how it works (and why it's 100% open-source) 🧵👇
> [ATTACH: demo_tracking.gif]

**Tweet 2 (The Problem with existing tools):**
> Most fit tools only use 17 COCO keypoints (ignoring ankles, heels, and toes).
> 
> In cycling, ankle dorsiflexion/plantarflexion is everything.
> If your heel drops or points at BDC (Bottom Dead Center), your knee extension reading is completely wrong.
> 
> Open-BikeFit solves this with full 3D foot kinematics. 🦶

**Tweet 3 (Harmonic Crank Cycle Decomposition):**
> Built with 4-phase crank rotation tracking:
> 
> • 12 o'clock (TDC): Maximum Knee & Hip Flexion
> • 3 o'clock: Peak Torque & KOPS (Knee Over Pedal Spindle)
> • 6 o'clock (BDC): Holmes Method Saddle Height Extrema
> • 9 o'clock: Recovery Phase

**Tweet 4 (Studio Fit Report with Guardrails):**
> The AI engine is used strictly for formatting narrative reports & wrench instructions:
> • Explains *why* your knee angle causes anterior knee pain
> • Calculates millimetric saddle height & fore-aft adjustments
> • Produces a multi-page PDF fit report in 1-click.

**Tweet 5 (Call to Action / Link):**
> Try it out (Star the repo on GitHub ⭐):
> 🔗 https://github.com/pgeedh/Open-BikeFit-The-AI-Powered-Bike-Fit-Studio
> 
> Run it on Colab or locally via Streamlit with 1 command!
> RT if you ride road, gravel, or triathlon! 🚴💨

---

## 2. 🔴 Reddit Post Templates

### Subreddits: `r/cycling`, `r/triathlon`, `r/bicycling`
**Title:** *I built an open-source bike fitting studio (Open-BikeFit) that does dynamic video tracking and generates studio PDF reports for free*

**Post Body:**
> Hey everyone!
> 
> Like many of you, I love cycling and triathlon, but paying $350-$500 for a commercial bike fit isn't always feasible when testing minor saddle adjustments, changing shoes, or wanting a fast baseline.
> 
> I built **Open-BikeFit**, an open-source dynamic bike fitting studio that runs locally on your laptop:
> 
> **Key Features:**
> 1. **Dynamic Motion Capture:** Tracks 33 anatomical landmarks (including heels & toes) from any side-on video on your turbo trainer.
> 2. **Automatic 4-Phase Breakdown:** Decomposes your pedal stroke into Top Dead Center (TDC), Power Phase (3 o'clock), Bottom Dead Center (BDC), and Recovery.
> 3. **Studio Fit Report Engine:** Translates your knee extension, closed hip angle, and torso incline into actionable millimeter wrench adjustments.
> 4. **High-Resolution PDF Report:** Exports a professional multi-page summary with angle overlays and scorecards.
> 
> It's 100% free and open-source on GitHub:
> 👉 **GitHub:** https://github.com/pgeedh/Open-BikeFit-The-AI-Powered-Bike-Fit-Studio
> 
> Would love your feedback on the kinematics and target angle ranges!

---

### Subreddits: `r/computervision`, `r/MachineLearning`, `r/Python`
**Title:** *Open-BikeFit: Real-time 3D Biomechanical Bike Fitting Studio using MediaPipe BlazePose, 1€ Dynamic Filtering, and Apple HIG Web Studio*

**Post Body:**
> Hi r/computervision!
> 
> I wanted to share **Open-BikeFit**, an open-source kinematic analysis pipeline designed for dynamic cycling biomechanics.
> 
> **Tech Stack:**
> - **Pose Estimation:** Google MediaPipe Tasks API (`pose_landmarker_heavy.task`) with 3D world landmark extraction.
> - **Temporal Filtering:** Real-time adaptive 1€ filter + bone-length invariance enforcement.
> - **Kinematics:** Continuous harmonic crank phase decomposition.
> - **LLM Integration:** Claude 3.7 / Gemini 2.0 Flash / Offline Rule Engine for narrative report formatting.
> - **UI:** Streamlit Web Studio with Apple Human Interface Guidelines (`app.py`) + FPDF for PDF report generation.
> 
> Check out the repo and Colab demo:
> 🔗 https://github.com/pgeedh/Open-BikeFit-The-AI-Powered-Bike-Fit-Studio

---

## 3. 🟠 Hacker News (Show HN)

**Title:** *Show HN: Open-BikeFit – Open-source biomechanical bike fit studio*

**Text:**
> Hi HN! I built Open-BikeFit (https://github.com/pgeedh/Open-BikeFit-The-AI-Powered-Bike-Fit-Studio), an open-source tool that turns any video of a cyclist on a turbo trainer into a dynamic biomechanical analysis report.
> 
> It tracks 33 anatomical landmarks at 30+ FPS, extracts 4-phase crank dynamics (TDC, BDC, KOPS), and uses an offline engine or LLMs to generate natural-language fit consultations and PDF reports.
> 
> Code is on GitHub. Feedback appreciated!
