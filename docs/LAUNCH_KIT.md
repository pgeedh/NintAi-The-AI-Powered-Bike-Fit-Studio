# 🚀 NintAi Viral Launch & Growth Playbook

This kit provides ready-to-publish social copy, viral hooks, and distribution strategies to launch **NintAi** to thousands of cyclists, triathletes, and AI/CV developers.

---

## 1. 🐦 X (Twitter) Viral Thread Template

**Tweet 1 (Hook + Video/GIF):**
> 🚴 Professional 3D bike fits like Retül cost $350+.
> 
> So I built **NintAi** — a completely free, open-source AI Bike Fit Studio that turns your laptop into a clinical motion lab.
> 
> Powered by MediaPipe 33-Keypoint Heavy Pose + Google Gemini AI.
> 
> Here's how it works (and why it's 100% open-source) 🧵👇
> [ATTACH: demo_tracking.gif]

**Tweet 2 (The Problem with existing tools):**
> Most fit tools only use 17 COCO keypoints (ignoring ankles, heels, and toes).
> 
> In cycling, ankle dorsiflexion/plantarflexion is everything.
> If your heel drops or points at BDC (Bottom Dead Center), your knee extension reading is completely wrong.
> 
> NintAi solves this with full 3D foot kinematics. 🦶

**Tweet 3 (Harmonic Crank Cycle Decomposition):**
> We built a harmonic circle solver that tracks the continuous 360° crank rotation:
> 
> • 12 o'clock (TDC): Maximum Knee & Hip Flexion
> • 3 o'clock: Peak Torque & KOPS (Knee Over Pedal Spindle)
> • 6 o'clock (BDC): Holmes Method Saddle Height Extrema
> • 9 o'clock: Recovery Phase

**Tweet 4 (Gemini AI Coach):**
> Instead of just showing raw numbers, NintAi uses Google Gemini to generate a clinical consultation report:
> • Explains *why* your knee angle causes anterior knee pain
> • Calculates millimetric saddle height & fore-aft adjustments
> • Produces a multi-page PDF fit report in 1-click.

**Tweet 5 (Call to Action / Link):**
> Try it out (Star the repo on GitHub ⭐):
> 🔗 https://github.com/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio
> 
> Run it on Colab or locally via Docker with 1 command!
> RT if you ride road, gravel, or triathlon! 🚴💨

---

## 2. 🔴 Reddit Post Templates

### Subreddits: `r/cycling`, `r/triathlon`, `r/bicycling`
**Title:** *I built an open-source AI Bike Fitting studio (NintAi) that does dynamic video tracking and generates clinical PDF reports for free*

**Post Body:**
> Hey everyone!
> 
> Like many of you, I love cycling/triathlon, but paying $300-$400 for a commercial 3D bike fit isn't always accessible when testing minor saddle adjustments or cleat positions.
> 
> Over the past few months, I built **NintAi**, an open-source dynamic bike fitting studio that runs locally on your laptop:
> 
> **Key Features:**
> 1. **Dynamic Motion Capture:** Tracks 33 anatomical landmarks (including heels & toes) from any side-on video on your turbo trainer.
> 2. **Automatic 4-Phase Breakdown:** Decomposes your pedal stroke into Top Dead Center (TDC), Power Phase (3 o'clock), Bottom Dead Center (BDC), and Recovery.
> 3. **AI Biomechanics Coach (Gemini):** Translates your knee extension, closed hip angle, and torso incline into actionable millimeter adjustments.
> 4. **Clinical PDF Report:** Exports a professional multi-page summary with angle overlays and scorecards.
> 
> It's 100% free and open-source on GitHub:
> 👉 **GitHub:** https://github.com/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio
> 
> Would love your feedback on the kinematics and target angle ranges!

---

### Subreddits: `r/computervision`, `r/MachineLearning`, `r/Python`
**Title:** *NintAi: Real-time 3D Biomechanical Bike Fitting Studio using MediaPipe BlazePose, 1€ Dynamic Filtering, and Gemini AI*

**Post Body:**
> Hi r/computervision!
> 
> I wanted to share **NintAi**, an open-source kinematic analysis pipeline designed for dynamic cycling biomechanics.
> 
> **Tech Stack:**
> - **Pose Estimation:** Google MediaPipe Tasks API (`pose_landmarker_heavy.task`) with 3D world landmark extraction.
> - **Temporal Filtering:** Real-time adaptive 1€ filter + bone-length invariance enforcement.
> - **Kinematics:** Continuous harmonic crank phase decomposition ($\theta(t) = \text{atan2}(y-y_c, x-x_c)$).
> - **LLM Integration:** Google Gemini 2.0/3 API for biomechanical consultation.
> - **UI:** Streamlit Web Studio (`app.py`) + FPDF for PDF report generation.
> 
> Check out the repo and Colab demo:
> 🔗 https://github.com/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio

---

## 3. 🟠 Hacker News (Show HN)

**Title:** *Show HN: NintAi – Open-source AI bike fitting studio using MediaPipe and Gemini*

**Text:**
> Hi HN! I built NintAi (https://github.com/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio), an open-source tool that turns any video of a cyclist on a turbo trainer into a dynamic biomechanical analysis report.
> 
> It tracks 33 anatomical landmarks at 30+ FPS, extracts 4-phase crank dynamics (TDC, BDC, KOPS), and uses Google Gemini to generate natural-language fit consultations and PDF reports.
> 
> Code and Colab demo are on GitHub. Feedback appreciated!

---

## 4. 🚀 Product Hunt Launch Checklist
- **Tagline:** Free, clinical-grade AI bike fitting studio on your laptop.
- **Topics:** Artificial Intelligence, Sports Tech, Computer Vision, Health & Fitness, Open Source.
- **Thumbnail:** Dark-mode cybernetic cyclist wireframe with neon angle meters.
- **Pricing:** 100% Free & Open Source.
