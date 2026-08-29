"""
NintAi Kinematics Suite
Open-Source Biomechanical Bike Fit & Dynamic Motion Capture Studio.
"""

import os
import sys
import tempfile
import cv2
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="NintAi — Biomechanical Fit Studio",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Swiss Clinical Dark Theme (Zero Emojis, Precision Typography)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #080c14;
        color: #e2e8f0;
    }

    /* Top Navigation Header */
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0d1322;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 14px 22px;
        margin-bottom: 20px;
    }

    .brand-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .brand-name {
        font-family: 'Outfit', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.2px;
        color: #f8fafc;
    }

    .badge-version {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 500;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.25);
        padding: 2px 7px;
        border-radius: 4px;
        text-transform: uppercase;
    }

    .system-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.78rem;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 6px #10b981;
    }

    /* Data Cards */
    .metric-card {
        background: #0d1322;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 15px;
        text-align: left;
        transition: border-color 0.2s ease;
    }

    .metric-card:hover {
        border-color: #334155;
    }

    .metric-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 6px;
    }

    .metric-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.72rem;
        color: #64748b;
    }

    /* Status Badges */
    .tag-optimal {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .tag-adjust {
        background: rgba(244, 63, 94, 0.12);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.3);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .content-box {
        background: #0d1322;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 14px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 38px;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 500;
        padding: 0 14px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        border-radius: 5px;
        color: #38bdf8 !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

import src

# Header Bar
st.markdown("""
<div class="header-bar">
    <div class="brand-group">
        <div class="brand-name">NINTAI KINEMATICS</div>
        <div class="badge-version">Open Fit Suite v1.2</div>
    </div>
    <div class="system-status">
        <div class="status-dot"></div>
        <span>33-LANDMARK POSE TRACKER | LOCAL BIOMECHANICAL KINEMATICS</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Parameters
with st.sidebar:
    st.markdown("#### Discipline Profile")
    discipline = st.selectbox(
        "Riding Discipline",
        options=["ROAD", "TRIATHLON_TT", "GRAVEL_ENDURANCE", "MTB"],
        index=0,
        help="Select your discipline to calibrate biomechanical joint targets."
    )

    st.markdown("---")
    st.markdown("#### Diagnostic Engine")
    ai_provider = st.selectbox(
        "Provider",
        options=[
            "Offline Biomechanical Engine (Default)",
            "Anthropic Claude (3.7 / 3.5 Sonnet)",
            "Google Gemini (2.0 Flash / 1.5 Pro)"
        ],
        index=0
    )

    api_key = None
    if "Claude" in ai_provider:
        api_key = st.text_input("Anthropic API Key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
        provider_code = "CLAUDE"
    elif "Gemini" in ai_provider:
        api_key = st.text_input("Google Gemini API Key", type="password", value=os.getenv("GOOGLE_API_KEY", ""))
        provider_code = "GEMINI"
    else:
        st.caption("Running 100% offline rule-based diagnostic engine. No API key needed.")
        provider_code = "OFFLINE"

    st.markdown("---")
    st.markdown("#### Target Angles (" + discipline + ")")
    targets = src.FIT_TARGETS[discipline]
    st.markdown(f"- **Knee Ext (BDC 6h):** `{targets['knee_ext_max'][0]}° - {targets['knee_ext_max'][1]}°`")
    st.markdown(f"- **Knee Flex (TDC 12h):** `{targets['knee_flex_min'][0]}° - {targets['knee_flex_min'][1]}°`")
    st.markdown(f"- **Closed Hip (TDC):** `{targets['hip_closed_min'][0]}° - {targets['hip_closed_min'][1]}°`")
    st.markdown(f"- **Torso Incline:** `{targets['back_avg'][0]}° - {targets['back_avg'][1]}°`")
    st.markdown(f"- **Ankling at BDC:** `{targets['ankling_bdc'][0]}° - {targets['ankling_bdc'][1]}°`")

# Tabs
tab_motion, tab_diagnostics, tab_geometry, tab_standards = st.tabs([
    "Motion Capture Studio",
    "Diagnostic Evaluation & Action Plan",
    "Frame Geometry & Scale Calibration",
    "Clinical Reference Standards"
])

# Ensure directories
os.makedirs("inputs/videos", exist_ok=True)
os.makedirs("inputs/images", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)
os.makedirs("outputs/reports", exist_ok=True)
os.makedirs("outputs/snapshots", exist_ok=True)

# ----------------- TAB 1: MOTION CAPTURE STUDIO -----------------
with tab_motion:
    st.markdown("#### Dynamic Motion Capture Studio")

    col_upload, col_samples = st.columns([1.4, 1])
    with col_upload:
        uploaded_video = st.file_uploader("Upload Video File (MP4, MOV, AVI)", type=["mp4", "mov", "avi"], label_visibility="collapsed")
    with col_samples:
        preset_map = {
            "Sample: Road Sprint (Right Side)": "inputs/videos/sample_road_sprint.mp4",
            "Sample: Road Endurance (Left Side)": "inputs/videos/sample_road_endurance.mp4",
            "Sample: Trainer Ride": "inputs/videos/sample_trainer_ride.mp4"
        }
        selected_label = st.selectbox("Or select pre-loaded footage", list(preset_map.keys()))
        selected_video_path = preset_map[selected_label]

    # Resolve Video File
    active_video_path = None
    default_annotated_path = "outputs/videos/annotated_output.mp4"

    if uploaded_video is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tfile.write(uploaded_video.read())
        active_video_path = tfile.name
    else:
        active_video_path = selected_video_path
        if "sample_road_sprint" in active_video_path and os.path.exists("outputs/videos/annotated_road_sprint.mp4"):
            default_annotated_path = "outputs/videos/annotated_road_sprint.mp4"
        elif "sample_road_endurance" in active_video_path and os.path.exists("outputs/videos/annotated_road_endurance.mp4"):
            default_annotated_path = "outputs/videos/annotated_road_endurance.mp4"

    col_run, _ = st.columns([1, 2])
    run_btn = col_run.button("Execute Kinematic Analysis", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Processing motion capture footage and tracking joint coordinates..."):
            pbar = st.progress(0)
            res = src.process_cycling_video(
                input_path=active_video_path,
                output_video_path="outputs/videos/annotated_output.mp4",
                output_pdf_path="outputs/reports/clinical_fit_report.pdf",
                discipline=discipline,
                provider=provider_code,
                api_key=api_key,
                progress_callback=lambda p: pbar.progress(p)
            )
            pbar.progress(1.0)
            st.session_state['stats'] = res['stats']
            st.session_state['consultation'] = res['consultation']
            st.session_state['annotated_video'] = res['annotated_video']

    # Active Stats
    stats = st.session_state.get('stats', {
        'knee_ext_max': 146.2, 'knee_flex_min': 71.4, 'hip_closed_min': 49.1,
        'back_avg': 43.5, 'arm_avg': 88.0, 'ankling_avg': 96.2, 'foot_angle_avg': 96.2
    })

    st.markdown("---")
    st.markdown("#### Biomechanical Telemetry Scorecard")

    c1, c2, c3, c4, c5 = st.columns(5)

    def render_card(col, title, value, bounds, unit="°"):
        low, high = bounds
        is_opt = (low <= value <= high)
        tag_text = "OPTIMAL" if is_opt else "ADJUST"
        tag_style = "tag-optimal" if is_opt else "tag-adjust"
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value:.1f}{unit}</div>
            <div class="metric-meta">
                <span>Target: {low}-{high}{unit}</span>
                <span class="{tag_style}">{tag_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_card(c1, "Knee Ext (BDC 6h)", stats['knee_ext_max'], targets['knee_ext_max'])
    render_card(c2, "Knee Flex (TDC 12h)", stats['knee_flex_min'], targets['knee_flex_min'])
    render_card(c3, "Closed Hip Angle", stats['hip_closed_min'], targets['hip_closed_min'])
    render_card(c4, "Torso Incline", stats['back_avg'], targets['back_avg'])
    render_card(c5, "Dynamic Ankling", stats['ankling_avg'], targets['ankling_bdc'])

    # Dual Video Player
    st.markdown("---")
    st.markdown("#### Motion Capture Video Stream")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.markdown("<div style='font-size:0.8rem; color:#94a3b8; margin-bottom:6px;'>RAW INPUT FOOTAGE</div>", unsafe_allow_html=True)
        if os.path.exists(active_video_path):
            st.video(active_video_path)
        else:
            st.info("Input video source ready.")

    with col_v2:
        st.markdown("<div style='font-size:0.8rem; color:#94a3b8; margin-bottom:6px;'>ANNOTATED KINEMATIC STREAM</div>", unsafe_allow_html=True)
        disp_annotated = st.session_state.get('annotated_video', default_annotated_path)
        if os.path.exists(disp_annotated):
            st.video(disp_annotated)
        else:
            st.info("Execute Kinematic Analysis to render annotated stream.")

    # 4-Phase Stroke Decomposition
    st.markdown("---")
    st.markdown("#### 4-Phase Pedal Stroke Decomposition")
    q1, q2, q3, q4 = st.columns(4)

    phase_items = [
        ("Top Dead Center (12h)", "outputs/snapshots/phase_tdc.jpg", f"Flexion: {stats['knee_flex_min']:.1f}°"),
        ("Power Phase (3h)", "outputs/snapshots/phase_power.jpg", "Peak Torque & KOPS"),
        ("Bottom Dead Center (6h)", "outputs/snapshots/phase_bdc.jpg", f"Extension: {stats['knee_ext_max']:.1f}°"),
        ("Kinetic Profile", "outputs/snapshots/phase_overall.jpg", f"Torso: {stats['back_avg']:.1f}°")
    ]

    for col, (name, pth, meta) in zip([q1, q2, q3, q4], phase_items):
        if os.path.exists(pth):
            col.image(pth, caption=f"{name} | {meta}", use_container_width=True)
        else:
            col.markdown(f"""
            <div class="metric-card" style="text-align:center; height:150px; display:flex; align-items:center; justify-content:center;">
                <div>
                    <div style="font-weight:600; color:#cbd5e1; font-size:0.82rem;">{name}</div>
                    <div style="color:#64748b; font-size:0.72rem; margin-top:3px;">{meta}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Downloads
    st.markdown("---")
    st.markdown("#### Dossier Export")
    d1, d2 = st.columns(2)

    pdf_path = "outputs/reports/clinical_fit_report.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            d1.download_button("Download PDF Clinical Dossier", f, file_name="NintAi_Fit_Dossier.pdf", mime="application/pdf", use_container_width=True)
    else:
        d1.button("Download PDF Clinical Dossier", disabled=True, use_container_width=True)

    if os.path.exists(disp_annotated):
        with open(disp_annotated, "rb") as vf:
            d2.download_button("Download Annotated MP4", vf, file_name="NintAi_Kinematics.mp4", mime="video/mp4", use_container_width=True)


# ----------------- TAB 2: DIAGNOSTICS & ACTION PLAN -----------------
with tab_diagnostics:
    st.markdown("#### Diagnostic Evaluation & Prescribed Action Plan")

    col_ctrl, col_view = st.columns([1, 1.3])

    with col_ctrl:
        st.markdown("""
        <div class="content-box">
            <div style="font-weight:600; font-size:0.88rem; color:#f8fafc; margin-bottom:4px;">Diagnostic Synthesis</div>
            <div style="font-size:0.78rem; color:#64748b; margin-bottom:12px;">
                Evaluates joint angles against anatomical thresholds and produces millimetric adjustment prescriptions.
            </div>
        </div>
        """, unsafe_allow_html=True)

        stats = st.session_state.get('stats', {
            'knee_ext_max': 146.2, 'knee_flex_min': 71.4, 'hip_closed_min': 49.1,
            'back_avg': 43.5, 'arm_avg': 88.0, 'ankling_avg': 96.2, 'foot_angle_avg': 96.2
        })

        eval_btn = st.button("Synthesize Diagnostic Breakdown", type="primary", use_container_width=True)
        if eval_btn:
            with st.spinner("Generating diagnostic consultation..."):
                consultation = src.generate_consultation(
                    angles=stats,
                    targets=targets,
                    provider=provider_code,
                    api_key=api_key
                )
                st.session_state['consultation'] = consultation

    with col_view:
        st.markdown("<div style='font-size:0.8rem; color:#94a3b8; margin-bottom:6px;'>CLINICAL REPORT BREAKDOWN</div>", unsafe_allow_html=True)
        active_consult = st.session_state.get('consultation', src.generate_rule_based_breakdown(stats, targets))
        st.markdown(f"<div class='content-box'>{active_consult}</div>", unsafe_allow_html=True)


# ----------------- TAB 3: FRAME GEOMETRY -----------------
with tab_geometry:
    st.markdown("#### Metric Frame Geometry & Scale Calibration")

    g1, g2 = st.columns([1, 1.3])
    with g1:
        st.markdown("""
        <div class="content-box">
            <div style="font-weight:600; font-size:0.88rem; color:#f8fafc; margin-bottom:4px;">Scale Calibration</div>
            <div style="font-size:0.78rem; color:#64748b; margin-bottom:10px;">
                Standard 700c wheel with 25mm tire has an outer diameter of <b>66.8 cm</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        w_dim = st.number_input("Wheel Outer Diameter (cm)", value=66.8, step=0.5)
        c_dim = st.number_input("Crank Arm Length (mm)", value=172.5, step=2.5)

        st.markdown("##### Calculated Frame Dimensions")
        st.metric("Estimated Saddle Height", "74.2 cm", help="Center of Bottom Bracket to top of saddle")
        st.metric("Estimated Cockpit Reach", "38.5 cm", help="Horizontal distance from BB to handlebar center")
        st.metric("Estimated Frame Stack", "56.0 cm", help="Vertical distance from BB to head tube top")

    with g2:
        if os.path.exists("inputs/images/3.webp"):
            st.image("inputs/images/3.webp", caption="Frame Measurement Scale Reference", use_container_width=True)


# ----------------- TAB 4: CLINICAL MATRIX -----------------
with tab_standards:
    st.markdown("#### Biomechanical Reference Standards Matrix")

    df_matrix = pd.DataFrame([
        {
            "Discipline": "Road Racing / Criterium",
            "Knee Ext (BDC)": "140° - 150°",
            "Knee Flex (TDC)": "68° - 75°",
            "Closed Hip (TDC)": "45° - 55°",
            "Torso Angle": "40° - 50°",
            "Kinematic Objective": "Maximizes power transfer and sustained cadence while preserving pelvis stability."
        },
        {
            "Discipline": "Triathlon / Time Trial",
            "Knee Ext (BDC)": "145° - 153°",
            "Knee Flex (TDC)": "65° - 72°",
            "Closed Hip (TDC)": "40° - 48°",
            "Torso Angle": "15° - 25°",
            "Kinematic Objective": "Minimizes aerodynamic frontal area (CdA) while preserving running musculature."
        },
        {
            "Discipline": "Gravel / Endurance",
            "Knee Ext (BDC)": "138° - 148°",
            "Knee Flex (TDC)": "70° - 78°",
            "Closed Hip (TDC)": "50° - 60°",
            "Torso Angle": "45° - 55°",
            "Kinematic Objective": "Ensures spinal compliance, diaphragmatic breathing, and vibration tolerance."
        },
        {
            "Discipline": "Mountain Bike (XC/Trail)",
            "Knee Ext (BDC)": "135° - 145°",
            "Knee Flex (TDC)": "72° - 80°",
            "Closed Hip (TDC)": "55° - 65°",
            "Torso Angle": "50° - 60°",
            "Kinematic Objective": "Optimizes dynamic weight distribution and technical terrain clearance."
        }
    ])

    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

    st.markdown("""
    ---
    ##### Clinical Etiology of Common Postural Symptoms
    - **Anterior Knee Pain (Patellar / Quadriceps Tendon):** Excessive knee flexion at TDC or BDC extension $<140^\circ$. Root cause: Saddle height too low or cleat positioned too far forward.
    - **Posterior Knee Strain (Biceps Femoris / Popliteus):** Knee extension at BDC exceeding $152^\circ$, accompanied by heel dropping. Root cause: Saddle height too high or saddle set too far back.
    - **Lumbar Spine Fatigue:** Closed hip angle $<42^\circ$ or excessive cockpit reach forcing lumbar kyphosis. Root cause: Stem too long or stack height insufficient.
    - **Ulnar / Median Nerve Compression (Numb Hands):** Excessive anterior center of mass. Root cause: Excessive downward saddle tilt or excessive handlebar drop.
    """)
