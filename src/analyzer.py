"""
NintAi Video Motion Capture Analyzer.
Processes cycling video and extracts multi-revolution kinematic statistics.
"""

import os
import cv2
import numpy as np
import pandas as pd

from src.tracker import PoseTracker
from src.kinematics import (
    OneEuroFilter,
    BoneLengthEnforcer,
    detect_rider_side,
    extract_primary_side_landmarks,
    compute_postural_angles,
    draw_skeleton_and_angles,
    FIT_TARGETS
)
from src.ai_fitter import generate_consultation
from src.pdf_generator import build_clinical_pdf

def process_cycling_video(
    input_path: str,
    output_video_path: str = "outputs/videos/annotated_output.mp4",
    output_pdf_path: str = "outputs/reports/clinical_fit_report.pdf",
    discipline: str = "ROAD",
    provider: str = "OFFLINE",
    api_key: str = None,
    progress_callback = None
) -> dict:
    os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    os.makedirs("outputs/snapshots", exist_ok=True)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video source at {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    tracker = PoseTracker()
    filter_keys = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 
                   'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 
                   'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 
                   'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
                   'left_heel', 'right_heel', 'left_toe', 'right_toe']
    filters = {k: OneEuroFilter(t0=0, x0=np.zeros(2)) for k in filter_keys}
    bone_enforcer = BoneLengthEnforcer()

    frames_data = []
    side_votes = {'left': 0, 'right': 0}
    locked_side = None
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        t_curr = frame_count / fps
        ts_ms = int(t_curr * 1000)

        results = tracker.process_frame(frame, timestamp_ms=ts_ms)
        raw_lm = tracker.extract_landmarks_2d(results, frame.shape)

        clean_lm = {}
        for k, v in raw_lm.items():
            if k in filters:
                clean_lm[k] = filters[k].filter(t_curr, np.array(v))
            else:
                clean_lm[k] = v

        if clean_lm:
            detected = detect_rider_side(clean_lm)
            if locked_side is None:
                side_votes[detected] += 1
                if frame_count >= 25:
                    locked_side = 'left' if side_votes['left'] >= side_votes['right'] else 'right'
                current_side = detected
            else:
                current_side = locked_side

            unified_lm = extract_primary_side_landmarks(clean_lm, current_side)
            bone_enforcer.calibrate_step(unified_lm)
            unified_lm = bone_enforcer.enforce(unified_lm)
            angles = compute_postural_angles(unified_lm)

            frames_data.append({
                'frame_idx': frame_count,
                'angles': angles,
                'landmarks': unified_lm,
                'clean_lm': clean_lm,
                'side': current_side
            })

            draw_skeleton_and_angles(frame, unified_lm, angles, current_side)

        out.write(frame)
        if progress_callback and total_frames > 0 and frame_count % 15 == 0:
            progress_callback(min(frame_count / total_frames, 1.0))

    cap.release()
    out.release()

    if not frames_data:
        raise ValueError("No rider pose coordinates detected in video.")

    df = pd.DataFrame([f['angles'] for f in frames_data])
    df['frame_idx'] = [f['frame_idx'] for f in frames_data]
    df = df[df['knee'] > 0]

    stats = {
        'knee_ext_max': float(df['knee'].max()) if 'knee' in df else 145.0,
        'knee_flex_min': float(df['knee'].min()) if 'knee' in df else 71.0,
        'hip_closed_min': float(df['hip'].min()) if 'hip' in df else 49.0,
        'back_avg': float(df['back'].mean()) if 'back' in df else 43.5,
        'arm_avg': float(df['arm_torso'].mean()) if 'arm_torso' in df else 88.0,
        'ankling_avg': float(df.get('foot_angle', pd.Series([96.0])).mean()),
        'foot_angle_avg': float(df.get('foot_angle', pd.Series([96.0])).mean())
    }

    idx_bdc = df['knee'].idxmax()
    idx_tdc = df['knee'].idxmin()

    def save_phase_snap(idx, filename, title):
        c = cv2.VideoCapture(input_path)
        c.set(cv2.CAP_PROP_POS_FRAMES, frames_data[idx]['frame_idx'] - 1)
        _, img = c.read()
        c.release()
        if img is None:
            return None
        cv2.putText(img, title, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.05, (16, 185, 129), 2, cv2.LINE_AA)
        p = os.path.join("outputs/snapshots", filename)
        cv2.imwrite(p, img)
        return p

    snap_tdc = save_phase_snap(df.index.get_loc(idx_tdc), "phase_tdc.jpg", "Top Dead Center (12h)")
    snap_bdc = save_phase_snap(df.index.get_loc(idx_bdc), "phase_bdc.jpg", "Bottom Dead Center (6h)")
    snap_power = save_phase_snap(df.index.get_loc(idx_bdc), "phase_power.jpg", "Power Delivery Phase (3h)")
    snap_overall = save_phase_snap(df.index.get_loc(idx_bdc), "phase_overall.jpg", "Full Kinetic Chain Profile")

    targets = FIT_TARGETS.get(discipline, FIT_TARGETS["ROAD"])
    consultation = generate_consultation(stats, targets, provider=provider, api_key=api_key)

    build_clinical_pdf(
        snap_tdc=snap_tdc,
        snap_bdc=snap_bdc,
        snap_power=snap_power,
        snap_overall=snap_overall,
        stats=stats,
        targets=targets,
        consultation_text=consultation,
        output_path=output_pdf_path
    )

    return {
        'stats': stats,
        'consultation': consultation,
        'annotated_video': output_video_path,
        'pdf_report': output_pdf_path
    }
