"""
NintAi - The AI-Powered Bike Fit Studio
Interactive Web UI powered by Streamlit, MediaPipe, OpenCV, and Google Gemini AI.
"""

import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import time
import pandas as pd

# Page config
st.set_page_config(
    page_title="NintAi — AI Bike Fit Studio",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric { background-color: #161f30; padding: 15px; border-radius: 10px; border: 1px solid #1e293b; }
    .phase-card { background: #161f30; padding: 15px; border-radius: 8px; border-left: 4px solid #00f2fe; margin-bottom: 10px; }
    .metric-badge-optimal { color: #10b981; font-weight: bold; background: #064e3b; padding: 3px 8px; border-radius: 5px; }
    .metric-badge-warning { color: #f43f5e; font-weight: bold; background: #881337; padding: 3px 8px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

from src import core
from src import tracking_mp as tracking
from src import report
from src import ai_report

# Header
st.title("🚴 NintAi: The AI-Powered Bike Fit Studio")
st.caption("⚡ Professional Bio-Mechanical Motion Capture • MediaPipe Heavy 33-Keypoint Engine • Google Gemini AI Coach")

# Sidebar
with st.sidebar:
    st.header("⚙️ Studio Settings")
    discipline = st.selectbox(
        "Riding Discipline",
        options=["ROAD", "TRIATHLON_TT", "GRAVEL_ENDURANCE", "MTB"],
        index=0,
        help="Calibrates the target biomechanical angle ranges."
    )
    
    st.subheader("🤖 AI Coach Integration")
    api_key = st.text_input("Gemini API Key", type="password", help="Optional: Get a key at aistudio.google.com")
    
    st.markdown("---")
    st.markdown("### 📋 Quick Target Angles")
    targets = core.FIT_TARGETS[discipline]
    st.write(f"• **Knee Extension (BDC):** {targets['knee_ext_max'][0]}° - {targets['knee_ext_max'][1]}°")
    st.write(f"• **Knee Flexion (TDC):** {targets['knee_flex_min'][0]}° - {targets['knee_flex_min'][1]}°")
    st.write(f"• **Hip Angle (Closed):** {targets['hip_closed_min'][0]}° - {targets['hip_closed_min'][1]}°")
    st.write(f"• **Torso Incline:** {targets['back_avg'][0]}° - {targets['back_avg'][1]}°")

# Tabs
tab_video, tab_image, tab_ai, tab_guide = st.tabs([
    "🎥 Dynamic Video Studio", 
    "📷 Static Image Fit", 
    "🧠 AI Coach Verdict", 
    "📚 Biomechanics Reference"
])

# Video Studio
with tab_video:
    st.subheader("📹 Dynamic Video Motion Capture Analysis")
    
    col_input1, col_input2 = st.columns([2, 1])
    with col_input1:
        video_file = st.file_uploader("Upload Cycling Video (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])
    with col_input2:
        use_sample = st.checkbox("Or use built-in sample video", value=False)
        sample_choice = st.selectbox("Select Sample", ["assets/examples/videos/testvideo2.mp4", "assets/examples/videos/testvideo.mp4"])
    
    input_path = None
    if video_file:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tfile.write(video_file.read())
        input_path = tfile.name
    elif use_sample and os.path.exists(sample_choice):
        input_path = sample_choice

    if input_path and st.button("🚀 Run AI Biomechanical Fit", type="primary"):
        with st.spinner("Analyzing motion capture landmarks & crank rotation..."):
            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            detector = tracking.PoseDetectorMP()
            
            knee_angles = []
            hip_angles = []
            back_angles = []
            arm_angles = []
            ankling_angles = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            frame_idx = 0
            best_frames = {'tdc': None, 'bdc': None, 'power': None, 'recovery': None}
            min_knee = 999
            max_knee = -999
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp_ms = int((frame_idx / fps) * 1000)
                results = detector.predict(frame, timestamp_ms)
                lms = detector.get_landmarks_dict(results, frame.shape)
                
                # Auto side selection
                side = 'left' if 'left_knee' in lms else 'right' if 'right_knee' in lms else None
                
                if side:
                    hip = lms.get(f'{side}_hip')
                    knee = lms.get(f'{side}_knee')
                    ankle = lms.get(f'{side}_ankle')
                    shoulder = lms.get(f'{side}_shoulder')
                    elbow = lms.get(f'{side}_elbow')
                    wrist = lms.get(f'{side}_wrist')
                    heel = lms.get(f'{side}_heel', ankle)
                    toe = lms.get(f'{side}_toe', ankle)
                    
                    if hip and knee and ankle:
                        k_ang = core.calculate_angle(hip, knee, ankle)
                        knee_angles.append(k_ang)
                        
                        if k_ang < min_knee:
                            min_knee = k_ang
                            best_frames['tdc'] = frame.copy()
                        if k_ang > max_knee:
                            max_knee = k_ang
                            best_frames['bdc'] = frame.copy()
                            
                    if shoulder and hip and knee:
                        h_ang = core.calculate_angle(shoulder, hip, knee)
                        hip_angles.append(h_ang)
                    if shoulder and hip:
                        b_ang = core.calculate_torso_angle(shoulder, hip)
                        back_angles.append(b_ang)
                    if hip and shoulder and elbow:
                        a_ang = core.calculate_angle(hip, shoulder, elbow)
                        arm_angles.append(a_ang)
                    if knee and ankle and heel and toe:
                        ank_ang = core.calculate_ankling_angle(knee, ankle, heel, toe)
                        ankling_angles.append(ank_ang)
                        
                frame_idx += 1
                if total_frames > 0 and frame_idx % 5 == 0:
                    progress_bar.progress(min(frame_idx / total_frames, 1.0))
                    status_text.text(f"Processed frame {frame_idx}/{total_frames}...")

            cap.release()
            progress_bar.progress(1.0)
            status_text.text("✅ Kinematic Analysis Complete!")

            # Statistics & Diagnostics
            stats = {
                'knee_ext_max': float(np.percentile(knee_angles, 95)) if knee_angles else 145.0,
                'knee_flex_min': float(np.percentile(knee_angles, 5)) if knee_angles else 70.0,
                'hip_closed_min': float(np.percentile(hip_angles, 5)) if hip_angles else 48.0,
                'back_avg': float(np.mean(back_angles)) if back_angles else 42.0,
                'arm_avg': float(np.mean(arm_angles)) if arm_angles else 90.0,
                'ankling_avg': float(np.mean(ankling_angles)) if ankling_angles else 95.0,
            }
            
            st.session_state['stats'] = stats
            st.session_state['best_frames'] = best_frames
            
            # Metric Scorecards
            st.markdown("### 📊 Biomechanical Angle Scorecard")
            c1, c2, c3, c4 = st.columns(4)
            
            def render_stat(col, title, val, target_range, unit="°"):
                t_min, t_max = target_range
                is_opt = t_min <= val <= t_max
                badge = f"<span class='{'metric-badge-optimal' if is_opt else 'metric-badge-warning'}'>{'OPTIMAL' if is_opt else 'ADJUST'}</span>"
                col.markdown(f"**{title}**<br><h2>{val:.1f}{unit}</h2>Target: {t_min}-{t_max}{unit} • {badge}", unsafe_allow_html=True)
                
            render_stat(c1, "Knee Extension (BDC)", stats['knee_ext_max'], targets['knee_ext_max'])
            render_stat(c2, "Knee Flexion (TDC)", stats['knee_flex_min'], targets['knee_flex_min'])
            render_stat(c3, "Hip Angle (Closed)", stats['hip_closed_min'], targets['hip_closed_min'])
            render_stat(c4, "Torso Incline", stats['back_avg'], targets['back_avg'])

            # 4-Phase Breakdown Preview
            st.markdown("### 🔄 4-Phase Dynamic Stroke Decomposition")
            p_col1, p_col2 = st.columns(2)
            if best_frames['tdc'] is not None:
                p_col1.image(cv2.cvtColor(best_frames['tdc'], cv2.COLOR_BGR2RGB), caption="Top Dead Center (TDC 12 o'clock - Max Flexion)", use_container_width=True)
            if best_frames['bdc'] is not None:
                p_col2.image(cv2.cvtColor(best_frames['bdc'], cv2.COLOR_BGR2RGB), caption="Bottom Dead Center (BDC 6 o'clock - Max Extension)", use_container_width=True)

# AI Tab
with tab_ai:
    st.subheader("🤖 AI Biomechanical Coach Consultation")
    if 'stats' in st.session_state:
        stats = st.session_state['stats']
        if st.button("Generate Expert Gemini AI Verdict"):
            with st.spinner("Consulting Google Gemini AI Coach..."):
                recs = []
                if stats['knee_ext_max'] < targets['knee_ext_max'][0]:
                    recs.append("Raise Saddle 5-10mm (Knee over-flexed at bottom).")
                elif stats['knee_ext_max'] > targets['knee_ext_max'][1]:
                    recs.append("Lower Saddle 5-10mm (Knee hyper-extended at bottom).")
                    
                ai_text = ai_report.generate_ai_analysis(stats, recs, api_key=api_key)
                st.markdown(ai_text)
    else:
        st.info("Please run a video analysis in the Dynamic Video Studio first to generate your AI coach verdict.")

# Biomechanics Reference Tab
with tab_guide:
    st.subheader("📚 Clinical Bike Fitting Reference Table")
    df_guide = pd.DataFrame([
        {"Discipline": "Road Race / Sportive", "Knee Extension (BDC)": "140° - 150°", "Knee Flexion (TDC)": "68° - 75°", "Hip Closed": "45° - 55°", "Torso Angle": "40° - 50°"},
        {"Discipline": "Triathlon / TT", "Knee Extension (BDC)": "145° - 153°", "Knee Flexion (TDC)": "65° - 72°", "Hip Closed": "40° - 48°", "Torso Angle": "15° - 25°"},
        {"Discipline": "Gravel / Endurance", "Knee Extension (BDC)": "138° - 148°", "Knee Flexion (TDC)": "70° - 78°", "Hip Closed": "50° - 60°", "Torso Angle": "45° - 55°"},
        {"Discipline": "MTB (Cross-Country / Trail)", "Knee Extension (BDC)": "135° - 145°", "Knee Flexion (TDC)": "72° - 80°", "Hip Closed": "55° - 65°", "Torso Angle": "50° - 60°"}
    ])
    st.dataframe(df_guide, use_container_width=True)
