# Contributing to NintAi 🚴

Thank you for your interest in improving **NintAi**! We are building the most accurate, accessible open-source bike fitting tool in the world.

---

## 🎯 Areas We Want Help With

1. **Biomechanical Kinematics:**
   - Improved 3D joint angle calculation & parallax elimination.
   - Frontal plane knee tracking (Q-angle, medial/lateral wobble).
   - Automatic crank arm length & wheel diameter detection.
2. **AI & Machine Learning:**
   - Multi-agent bike fitting prompts with Gemini.
   - Real-time posture voice feedback ("Raise chest", "Relax shoulders").
3. **Web UI & Visualization:**
   - 3D interactive skeleton viewers (Three.js / Plotly).
   - Strava / Garmin FIT file export integration.

---

## 🛠️ Development Setup

```bash
git clone https://github.com/pgeedh/NintAi-The-AI-Powered-Bike-Fit-Studio.git
cd NintAi-The-AI-Powered-Bike-Fit-Studio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/download_models.py
streamlit run app.py
```

---

## 📝 Pull Request Guidelines

1. Fork the repo and create a feature branch (`feature/your-feature-name`).
2. Verify all models and tests run cleanly.
3. Submit a PR describing your changes, with before/after screenshots or GIFs if UI or kinematics were altered.
