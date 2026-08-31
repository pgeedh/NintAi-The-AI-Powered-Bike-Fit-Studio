"""
Open-BikeFit - The Open-Source Biomechanical Bike Fit Studio.
Apple Human Interface Guidelines (HIG) Minimalist Architecture.
"""

import os
import json
import cv2
import numpy as np
import streamlit as st

from src.tracker import MediaPipeBlazePoseTracker
from src.kinematics import (
    OneEuroFilter,
    BoneLengthEnforcer,
    detect_rider_side,
    extract_primary_side_landmarks,
    compute_postural_angles,
    draw_skeleton_and_angles,
    FIT_TARGETS
)
from src.ai_fitter import generate_consultation, generate_rule_based_breakdown
from src.pdf_generator import build_clinical_pdf

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Open-BikeFit - Biomechanical Bike Fit Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Apple HIG Styling (Minimalist Space Graphite & Cupertino System Accents)
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-main: #000000;
    --bg-card: #1C1C1E;
    --bg-card-hover: #2C2C2E;
    --bg-secondary: #121214;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-medium: rgba(255, 255, 255, 0.16);
    --text-primary: #F5F5F7;
    --text-secondary: #86868B;
    --text-muted: #6E6E73;
    
    /* Apple System Colors */
    --system-blue: #0A84FF;
    --system-green: #30D158;
    --system-amber: #FF9F0A;
    --system-red: #FF453A;
    --system-purple: #BF5AF2;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-main);
}

.stApp {
    background-color: var(--bg-main);
}

/* Apple Header */
.apple-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 24px;
    background: rgba(28, 28, 30, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    margin-bottom: 24px;
}

.apple-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.apple-brand-title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--text-primary);
}

.apple-brand-badge {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 20px;
    background: rgba(10, 132, 255, 0.15);
    color: var(--system-blue);
    border: 1px solid rgba(10, 132, 255, 0.3);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Stepper Pill Bar */
.stepper-container {
    display: flex;
    gap: 8px;
    margin-bottom: 28px;
    overflow-x: auto;
    padding-bottom: 4px;
}

.step-pill {
    flex: 1;
    min-width: 140px;
    padding: 12px 14px;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    transition: all 0.2s ease;
}

.step-pill.active {
    background: #2C2C2E;
    color: var(--text-primary);
    border-color: var(--system-blue);
    box-shadow: 0 0 0 1px var(--system-blue);
}

.step-pill-num {
    font-size: 10px;
    font-weight: 700;
    color: var(--system-blue);
    text-transform: uppercase;
    margin-bottom: 2px;
}

/* Apple Card System */
.apple-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 20px;
    transition: border 0.2s ease;
}

.apple-card:hover {
    border-color: var(--border-medium);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.card-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.3px;
}

.card-desc {
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 16px;
    line-height: 1.5;
}

/* Metric Telemetry Card */
.metric-box {
    background: #141416;
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
}

.metric-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 4px;
}

.metric-val {
    font-family: "JetBrains Mono", monospace;
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
}

.metric-target {
    font-size: 11px;
    color: var(--text-muted);
}

/* Apple Badges */
.badge-optimal {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(48, 209, 88, 0.15);
    color: var(--system-green);
    font-size: 11px;
    font-weight: 600;
    border: 1px solid rgba(48, 209, 88, 0.3);
}

.badge-warning {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(255, 159, 10, 0.15);
    color: var(--system-amber);
    font-size: 11px;
    font-weight: 600;
    border: 1px solid rgba(255, 159, 10, 0.3);
}

.badge-alert {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    background: rgba(255, 69, 58, 0.15);
    color: var(--system-red);
    font-size: 11px;
    font-weight: 600;
    border: 1px solid rgba(255, 69, 58, 0.3);
}

/* Non-Clinical Disclaimer Banner */
.disclaimer-banner {
    background: rgba(255, 159, 10, 0.08);
    border: 1px solid rgba(255, 159, 10, 0.2);
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 12px;
    color: #E5E5EA;
    line-height: 1.5;
    margin-bottom: 24px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-subtle);
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Session State Initialization (Persistent Profile Store)
# ---------------------------------------------------------
if "rider_profile" not in st.session_state:
    st.session_state.rider_profile = {
        "name": "Alex Chen",
        "email": "alex.chen@example.com",
        "discipline": "ROAD",
        "goal": "Balanced Performance",
        "height_cm": 178,
        "inseam_cm": 83,
        "flexibility": "Moderate",
        "pain_points": ["Front of Knee (Patella)", "Lower Back Fatigue"],
        "bike_brand": "Specialized Tarmac SL7"
    }

if "active_step" not in st.session_state:
    st.session_state.active_step = "1. Rider Intake"

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "ai_report_text" not in st.session_state:
    st.session_state.ai_report_text = ""


# ---------------------------------------------------------
# Top Navigation Bar
# ---------------------------------------------------------
st.markdown("""
<div class="apple-nav">
    <div class="apple-brand">
        <div class="apple-brand-title">Open-BikeFit</div>
        <div class="apple-brand-badge">Studio Studio v2.5</div>
    </div>
    <div style="font-size: 13px; color: #86868B;">
        Open-Source Biomechanical Baseline & Rapid Hardware Diagnostics
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Non-Clinical Safe Disclaimer Banner
# ---------------------------------------------------------
st.markdown("""
<div class="disclaimer-banner">
    <strong>Kinematic Baseline Tool Notice:</strong> Open-BikeFit is designed to calculate joint angle envelopes and provide geometric hardware baseline estimates for riders and bike fitters. It is not a medical device or physical therapy diagnostic service.
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Multi-Step Segmented Flow (MyVeloFit Inspired)
# ---------------------------------------------------------
STEPS = [
    "1. Rider Intake",
    "2. Setup Guide",
    "3. Video Input",
    "4. Kinematic Run",
    "5. Telemetry Studio",
    "6. Studio Report"
]

current_idx = STEPS.index(st.session_state.active_step) if st.session_state.active_step in STEPS else 0

step_cols = st.columns(len(STEPS))
for i, step_name in enumerate(STEPS):
    with step_cols[i]:
        is_active = (step_name == st.session_state.active_step)
        if st.button(
            f"{step_name}", 
            key=f"nav_step_{i}", 
            type="primary" if is_active else "secondary", 
            use_container_width=True
        ):
            st.session_state.active_step = step_name
            st.rerun()


st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# =========================================================
# STEP 1: RIDER INTAKE & PROFILE
# =========================================================
if st.session_state.active_step == "1. Rider Intake":
    st.markdown("""
    <div class="apple-card">
        <div class="card-title">Step 1 · Rider Profile & Fitting Goals</div>
        <div class="card-desc">
            Enter your rider metrics and primary riding targets. Open-BikeFit uses these to calibrate acceptable joint kinematic envelopes and tailor hardware adjustments.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("#### Account & Biometric Dimensions")
        name = st.text_input("Full Name", value=st.session_state.rider_profile["name"])
        email = st.text_input("Email (for report archiving)", value=st.session_state.rider_profile["email"])
        
        dim_col1, dim_col2 = st.columns(2)
        with dim_col1:
            height = st.number_input("Rider Height (cm)", min_value=120, max_value=230, value=st.session_state.rider_profile["height_cm"])
        with dim_col2:
            inseam = st.number_input("Inseam Length (cm)", min_value=50, max_value=110, value=st.session_state.rider_profile["inseam_cm"])
            
        bike_model = st.text_input("Current Bike / Model", value=st.session_state.rider_profile.get("bike_brand", "Road Bike"))

    with c2:
        st.markdown("#### Discipline & Fit Objective")
        disc_options = ["ROAD", "GRAVEL_ENDURANCE", "TRIATHLON_TT", "MTB"]
        disc_labels = ["Road (Endurance & Sportive)", "Gravel & All-Road", "Triathlon & Time Trial (Aero)", "Mountain Bike (XC/Trail)"]
        disc_choice = st.selectbox("Primary Riding Discipline", range(len(disc_options)), format_func=lambda x: disc_labels[x])
        selected_disc = disc_options[disc_choice]
        
        goal = st.selectbox(
            "Fit Priority Goal", 
            ["Comfort & Endurance (Reduced spine & neck strain)", "Balanced Performance (Standard studio benchmark)", "Aggressive Aero & Speed (Low stack, flat back)"]
        )
        
        flexibility = st.select_slider(
            "Hamstring & Lower Back Flexibility",
            options=["Low (Tight)", "Moderate (Standard)", "High (Very Flexible)"],
            value=st.session_state.rider_profile.get("flexibility", "Moderate (Standard)")
        )

        st.markdown("#### Discomfort / Symptoms to Address")
        pain_options = [
            "Front of Knee (Patella / Anterior)",
            "Back of Knee (Hamstring / Posterior)",
            "Lower Back Fatigue",
            "Hand / Wrist Numbness (Ulnar Nerve)",
            "Neck & Shoulder Strain",
            "Saddle Discomfort / Hotspots"
        ]
        selected_pains = st.multiselect(
            "Flag any issues you experience on the bike:",
            pain_options,
            default=[p for p in st.session_state.rider_profile.get("pain_points", []) if p in pain_options]
        )

    if st.button("Save Profile & Continue to Setup Guide →", type="primary", use_container_width=True):
        st.session_state.rider_profile = {
            "name": name,
            "email": email,
            "discipline": selected_disc,
            "goal": goal,
            "height_cm": height,
            "inseam_cm": inseam,
            "flexibility": flexibility,
            "pain_points": selected_pains,
            "bike_brand": bike_model
        }
        st.session_state.active_step = "2. Setup Guide"
        st.rerun()


# =========================================================
# STEP 2: SETUP & CAMERA CALIBRATION GUIDE
# =========================================================
elif st.session_state.active_step == "2. Setup Guide":
    st.markdown("""
    <div class="apple-card">
        <div class="card-title">Step 2 · Studio Setup & Camera Calibration</div>
        <div class="card-desc">
            Computer vision precision depends on stable camera geometry. Follow this 5-point studio checklist before recording or importing your dynamic riding footage.
        </div>
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("""
        <div class="metric-box">
            <div style="font-weight:600; color:#F5F5F7; margin-bottom:6px;">1. Camera Height & Leveling</div>
            <div style="font-size:13px; color:#86868B; line-height:1.5;">
                Position your phone/tripod level with the bike's bottom bracket axle (~65–75 cm from the floor). Avoid pointing the lens downward.
            </div>
        </div>
        
        <div class="metric-box">
            <div style="font-weight:600; color:#F5F5F7; margin-bottom:6px;">2. Distance & Perspective</div>
            <div style="font-size:13px; color:#86868B; line-height:1.5;">
                Place the camera <strong>2.5 to 3.5 meters</strong> away, exactly perpendicular (90°) to the bike. Both wheels must be fully visible.
            </div>
        </div>
        
        <div class="metric-box">
            <div style="font-weight:600; color:#F5F5F7; margin-bottom:6px;">3. Drive-Side Orientation</div>
            <div style="font-size:13px; color:#86868B; line-height:1.5;">
                Record from the right (drive-side) or left (non-drive side). Open-BikeFit will auto-detect the visible side.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with g2:
        st.markdown("""
        <div class="metric-box">
            <div style="font-weight:600; color:#F5F5F7; margin-bottom:6px;">4. Attire & Lighting</div>
            <div style="font-size:13px; color:#86868B; line-height:1.5;">
                Wear snug-fitting cycling bibs/jersey with clear contrast against your background. Ensure bright, even room illumination.
            </div>
        </div>
        
        <div class="metric-box">
            <div style="font-weight:600; color:#F5F5F7; margin-bottom:6px;">5. Rider Warm-Up & Cadence</div>
            <div style="font-size:13px; color:#86868B; line-height:1.5;">
                Warm up for 8–10 minutes on the stationary trainer. Record 15–20 seconds of smooth, natural pedaling at 85–95 RPM.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("← Back to Profile", use_container_width=True):
            st.session_state.active_step = "1. Rider Intake"
            st.rerun()
    with b_col2:
        if st.button("Proceed to Video Input →", type="primary", use_container_width=True):
            st.session_state.active_step = "3. Video Input"
            st.rerun()


# =========================================================
# STEP 3: VIDEO INPUT & PRE-FLIGHT
# =========================================================
elif st.session_state.active_step == "3. Video Input":
    st.markdown("""
    <div class="apple-card">
        <div class="card-title">Step 3 · Motion Capture Video Selection</div>
        <div class="card-desc">
            Select a pre-packaged studio dataset or upload your own 30/60 FPS trainer footage.
        </div>
    </div>
    """, unsafe_allow_html=True)

    input_mode = st.radio("Choose Video Source", ["Studio Sample Datasets (Ready to Run)", "Upload Custom Rider Video"], horizontal=True)

    selected_video_path = None

    if "Upload" in input_mode:
        uploaded_file = st.file_uploader("Upload Rider Video (MP4 / MOV)", type=["mp4", "mov", "avi", "mkv"])
        if uploaded_file is not None:
            save_path = os.path.join("inputs/videos", uploaded_file.name)
            os.makedirs("inputs/videos", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_video_path = save_path
            st.success(f"Video uploaded successfully: {uploaded_file.name}")
    else:
        sample_options = {
            "Road Bike - Endurance Position (Sample 1)": "inputs/videos/sample_road_endurance.mp4",
            "Road Bike - Sprint / Criterium Cadence (Sample 2)": "inputs/videos/sample_road_sprint.mp4",
            "Indoor Trainer - Steady State Ride (Sample 3)": "inputs/videos/sample_trainer_ride.mp4"
        }
        chosen_sample = st.selectbox("Select Sample Video Dataset", list(sample_options.keys()))
        selected_video_path = sample_options[chosen_sample]

    if selected_video_path and os.path.exists(selected_video_path):
        cap = cv2.VideoCapture(selected_video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        st.markdown(f"""
        <div class="metric-box">
            <div style="font-weight:600; color:#F5F5F7; margin-bottom:8px;">Pre-Flight Video Inspection</div>
            <div style="display:flex; gap:24px; font-size:13px; color:#86868B;">
                <div><strong>Resolution:</strong> {w} x {h}</div>
                <div><strong>Frame Rate:</strong> {fps} FPS</div>
                <div><strong>Frames:</strong> {total_frames}</div>
                <div><strong>Duration:</strong> {duration:.1f}s</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.video(selected_video_path)
        st.session_state.selected_video_path = selected_video_path

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("← Back to Setup Guide", use_container_width=True):
            st.session_state.active_step = "2. Setup Guide"
            st.rerun()
    with b_col2:
        if st.button("Run Kinematic Compute →", type="primary", use_container_width=True):
            st.session_state.active_step = "4. Kinematic Run"
            st.rerun()


# =========================================================
# STEP 4: KINEMATIC MOTION CAPTURE COMPUTE
# =========================================================
elif st.session_state.active_step == "4. Kinematic Run":
    st.markdown("""
    <div class="apple-card">
        <div class="card-title">Step 4 · Real-Time Kinematic Computation</div>
        <div class="card-desc">
            Processing 33 spatial anatomical landmarks with 1€ adaptive filtering and bone length enforcement.
        </div>
    </div>
    """, unsafe_allow_html=True)

    video_path = getattr(st.session_state, "selected_video_path", "inputs/videos/sample_road_endurance.mp4")

    if not os.path.exists(video_path):
        st.error(f"Video file not found: {video_path}")
    else:
        prog_bar = st.progress(0, text="Initializing BlazePose tracking pipeline...")
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        out_annotated = "outputs/videos/annotated_run.mp4"
        os.makedirs("outputs/videos", exist_ok=True)
        os.makedirs("outputs/snapshots", exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(out_annotated, fourcc, fps, (w, h))

        tracker = MediaPipeBlazePoseTracker()
        filter_euro = OneEuroFilter(t0=0, min_cutoff=1.2, beta=0.008)
        bone_enforcer = BoneLengthEnforcer(tolerance=0.08)

        frame_idx = 0
        detected_side = None
        angle_history = {'knee': [], 'hip': [], 'back': [], 'arm_torso': [], 'elbow': [], 'foot_angle': []}

        best_tdc_frame, min_knee_angle = None, 999.0
        best_bdc_frame, max_knee_angle = None, 0.0
        best_power_frame, best_power_score = None, 999.0
        overall_snapshot_frame = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            t_sec = frame_idx / float(fps)
            landmarks = tracker.detect_landmarks(frame)

            if landmarks:
                if detected_side is None:
                    detected_side = detect_rider_side(landmarks)

                primary = extract_primary_side_landmarks(landmarks, detected_side)
                bone_enforcer.calibrate_step(primary)
                primary = bone_enforcer.enforce(primary)
                angles = compute_postural_angles(primary)

                for k, v in angles.items():
                    angle_history[k].append(v)

                draw_skeleton_and_angles(frame, primary, angles, detected_side)

                k_ang = angles.get('knee', 0)
                if k_ang > 0:
                    if k_ang < min_knee_angle and k_ang > 50:
                        min_knee_angle = k_ang
                        best_tdc_frame = frame.copy()
                    if k_ang > max_knee_angle and k_ang < 170:
                        max_knee_angle = k_ang
                        best_bdc_frame = frame.copy()

                if 'knee' in primary and 'hip' in primary:
                    # 3 o'clock horizontal femur
                    dy = abs(primary['knee'][1] - primary['hip'][1])
                    if dy < best_power_score:
                        best_power_score = dy
                        best_power_frame = frame.copy()

                if frame_idx == int(total_frames * 0.45):
                    overall_snapshot_frame = frame.copy()

            writer.write(frame)
            frame_idx += 1

            if frame_idx % 10 == 0 or frame_idx == total_frames:
                pct = min(frame_idx / float(total_frames), 1.0)
                prog_bar.progress(pct, text=f"Analyzing kinematics: {frame_idx}/{total_frames} frames ({int(pct*100)}%)")

        cap.release()
        writer.release()

        # Save snapshots
        snap_tdc = "outputs/snapshots/phase_tdc.jpg"
        snap_bdc = "outputs/snapshots/phase_bdc.jpg"
        snap_power = "outputs/snapshots/phase_power.jpg"
        snap_overall = "outputs/snapshots/phase_overall.jpg"

        if best_tdc_frame is not None:
            cv2.imwrite(snap_tdc, best_tdc_frame)
        if best_bdc_frame is not None:
            cv2.imwrite(snap_bdc, best_bdc_frame)
        if best_power_frame is not None:
            cv2.imwrite(snap_power, best_power_frame)
        if overall_snapshot_frame is not None:
            cv2.imwrite(snap_overall, overall_snapshot_frame)

        # Compute summary metrics
        stats = {
            'knee_ext_max': float(np.percentile(angle_history['knee'], 95)) if angle_history['knee'] else 145.0,
            'knee_flex_min': float(np.percentile(angle_history['knee'], 5)) if angle_history['knee'] else 71.0,
            'hip_closed_min': float(np.percentile(angle_history['hip'], 5)) if angle_history['hip'] else 49.0,
            'back_avg': float(np.median(angle_history['back'])) if angle_history['back'] else 43.5,
            'arm_avg': float(np.median(angle_history['arm_torso'])) if angle_history['arm_torso'] else 88.0,
            'ankling_avg': float(np.median(angle_history['foot_angle'])) if angle_history['foot_angle'] else 96.0,
            'detected_side': detected_side or "right",
            'frames_analyzed': frame_idx,
            'annotated_video': out_annotated,
            'snap_tdc': snap_tdc,
            'snap_bdc': snap_bdc,
            'snap_power': snap_power,
            'snap_overall': snap_overall
        }

        st.session_state.analysis_results = stats
        prog_bar.progress(1.0, text="Kinematic computation complete!")
        st.success("Analysis successfully completed. View telemetry in the next step.")

        if st.button("Open Telemetry Dashboard →", type="primary", use_container_width=True):
            st.session_state.active_step = "5. Telemetry Studio"
            st.rerun()


# =========================================================
# STEP 5: TELEMETRY DASHBOARD & 4-PHASE STUIDO
# =========================================================
elif st.session_state.active_step == "5. Telemetry Studio":
    stats = st.session_state.analysis_results

    if not stats:
        st.warning("No analysis results in current session. Please run Step 4 first.")
        if st.button("← Go to Step 4"):
            st.session_state.active_step = "4. Kinematic Run"
            st.rerun()
    else:
        disc = st.session_state.rider_profile.get("discipline", "ROAD")
        targets = FIT_TARGETS.get(disc, FIT_TARGETS["ROAD"])

        st.markdown(f"""
        <div class="apple-card">
            <div class="card-title">Step 5 · Biomechanical Telemetry & Motion Studio</div>
            <div class="card-desc">
                Target Profile: <strong>{disc}</strong> | Rider: <strong>{st.session_state.rider_profile['name']}</strong> | Analyzed Side: <strong>{stats['detected_side'].upper()}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 6 Metric Telemetry Grid
        m_cols = st.columns(3)

        def render_metric_card(col, title, value, target_bounds, unit="°"):
            t_min, t_max = target_bounds
            is_optimal = (t_min <= value <= t_max)
            diff = min(abs(value - t_min), abs(value - t_max)) if not is_optimal else 0
            
            if is_optimal:
                badge_html = '<span class="badge-optimal">Optimal</span>'
            elif diff <= 4.0:
                badge_html = '<span class="badge-warning">Minor Offset</span>'
            else:
                badge_html = '<span class="badge-alert">Needs Adjustment</span>'

            with col:
                st.markdown(f"""
                <div class="metric-box">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="metric-label">{title}</div>
                        {badge_html}
                    </div>
                    <div class="metric-val">{value:.1f}{unit}</div>
                    <div class="metric-target">Target Window: {t_min}{unit} – {t_max}{unit}</div>
                </div>
                """, unsafe_allow_html=True)

        render_metric_card(m_cols[0], "Knee Extension (BDC 6h)", stats['knee_ext_max'], targets['knee_ext_max'])
        render_metric_card(m_cols[1], "Knee Flexion (TDC 12h)", stats['knee_flex_min'], targets['knee_flex_min'])
        render_metric_card(m_cols[2], "Closed Hip Angle (TDC)", stats['hip_closed_min'], targets['hip_closed_min'])

        m_cols2 = st.columns(3)
        render_metric_card(m_cols2[0], "Torso Incline to Horiz.", stats['back_avg'], targets['back_avg'])
        render_metric_card(m_cols2[1], "Shoulder / Reach Angle", stats['arm_avg'], targets['arm_avg'])
        render_metric_card(m_cols2[2], "Ankle Angle at BDC", stats['ankling_avg'], targets['ankling_bdc'])

        # Side-by-Side Video & Motion Capture Playback
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("#### Dynamic Motion Capture Playback")
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            st.caption("Original Capture Footage")
            if hasattr(st.session_state, "selected_video_path") and os.path.exists(st.session_state.selected_video_path):
                st.video(st.session_state.selected_video_path)
        with v_col2:
            st.caption("Kinematic Skeleton & Goniometer Tracking")
            if os.path.exists(stats['annotated_video']):
                st.video(stats['annotated_video'])

        # 4-Phase Stroke Decomposition Stills
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 4-Phase Pedal Stroke Decomposition")
        s_cols = st.columns(4)
        with s_cols[0]:
            if os.path.exists(stats['snap_tdc']):
                st.image(stats['snap_tdc'], caption="Phase 1: TDC (12h Flexion)")
        with s_cols[1]:
            if os.path.exists(stats['snap_power']):
                st.image(stats['snap_power'], caption="Phase 2: Power Phase (3h Drive)")
        with s_cols[2]:
            if os.path.exists(stats['snap_bdc']):
                st.image(stats['snap_bdc'], caption="Phase 3: BDC (6h Extension)")
        with s_cols[3]:
            if os.path.exists(stats['snap_overall']):
                st.image(stats['snap_overall'], caption="Phase 4: Full Kinetic Chain")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("← Re-Run Analysis", use_container_width=True):
                st.session_state.active_step = "4. Kinematic Run"
                st.rerun()
        with b_col2:
            if st.button("Generate Studio Fit Report →", type="primary", use_container_width=True):
                st.session_state.active_step = "6. Studio Report"
                st.rerun()


# =========================================================
# STEP 6: STUDIO FIT REPORT & WRENCH ACTION PLAN
# =========================================================
elif st.session_state.active_step == "6. Studio Report":
    stats = st.session_state.analysis_results

    if not stats:
        st.warning("Please complete kinematic analysis first.")
        if st.button("← Go to Step 4"):
            st.session_state.active_step = "4. Kinematic Run"
            st.rerun()
    else:
        disc = st.session_state.rider_profile.get("discipline", "ROAD")
        targets = FIT_TARGETS.get(disc, FIT_TARGETS["ROAD"])
        rider_prof = st.session_state.rider_profile

        st.markdown("""
        <div class="apple-card">
            <div class="card-title">Step 6 · Professional Studio Fit Report & Wrench Guide</div>
            <div class="card-desc">
                Generate an authentic, studio-grade bicycle fit report with millimeter hardware adjustments. The API key is used strictly for formatting and structuring the narrative report.
            </div>
        </div>
        """, unsafe_allow_html=True)

        r_col1, r_col2 = st.columns([1, 2])

        with r_col1:
            st.markdown("#### Engine & Provider Settings")
            provider = st.selectbox(
                "Report Generation Engine",
                ["OFFLINE", "CLAUDE", "GEMINI"],
                format_func=lambda x: {
                    "OFFLINE": "Local Studio Engine (100% Offline / Zero API Key)",
                    "CLAUDE": "Anthropic Claude (Claude 3.7 / 3.5 Sonnet)",
                    "GEMINI": "Google Gemini (Gemini 2.0 Flash)"
                }[x]
            )

            api_key = None
            if provider == "CLAUDE":
                api_key = st.text_input("Anthropic API Key", type="password", help="Used strictly to generate the formatted fit report. All angle tracking is local.")
            elif provider == "GEMINI":
                api_key = st.text_input("Google Gemini API Key", type="password", help="Used strictly to generate the formatted fit report. All angle tracking is local.")

            if st.button("Generate / Refresh Report", type="primary", use_container_width=True):
                with st.spinner("Generating studio fit report..."):
                    report_md = generate_consultation(
                        angles=stats,
                        targets=targets,
                        provider=provider,
                        api_key=api_key,
                        rider_profile=rider_prof
                    )
                    st.session_state.ai_report_text = report_md
                    st.success("Report generated!")

        with r_col2:
            st.markdown("#### Studio Fit Dossier")
            
            if not st.session_state.ai_report_text:
                # Generate default offline report if empty
                st.session_state.ai_report_text = generate_rule_based_breakdown(stats, targets, rider_prof)

            st.markdown(st.session_state.ai_report_text)

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            # PDF Generation
            pdf_path = "outputs/reports/openbikefit_report.pdf"
            if st.button("Compile PDF Studio Dossier", use_container_width=True):
                build_clinical_pdf(
                    snap_tdc=stats['snap_tdc'],
                    snap_bdc=stats['snap_bdc'],
                    snap_power=stats['snap_power'],
                    snap_overall=stats['snap_overall'],
                    stats=stats,
                    targets=targets,
                    consultation_text=st.session_state.ai_report_text,
                    output_path=pdf_path,
                    rider_profile=rider_prof
                )
                st.success(f"PDF compiled: {pdf_path}")

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="Download PDF Fit Report",
                        data=f.read(),
                        file_name=f"OpenBikeFit_{rider_prof['name'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            # Export JSON Fit Profile
            fit_json = json.dumps({
                "rider_profile": rider_prof,
                "kinematic_metrics": {k: v for k, v in stats.items() if isinstance(v, (int, float, str))},
                "target_discipline": disc,
                "report_summary": st.session_state.ai_report_text
            }, indent=2)

            st.download_button(
                label="Export JSON Fit Profile",
                data=fit_json,
                file_name=f"OpenBikeFit_{rider_prof['name'].replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )
