import cv2
import argparse
import sys
import os
import time
import pandas as pd
import numpy as np
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import core
from src import tracking_mp as tracking 
from src import report
from src import ai_report

def main():
    parser = argparse.ArgumentParser(description="NintAi Ultimate BikeFit Video Motion Capture")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input video path")
    parser.add_argument("--output_video", "-ov", type=str, default="assets/examples/videos/annotated_output.mp4", help="Output video path")
    parser.add_argument("--output_excel", "-oe", type=str, default="output/fit_metrics.xlsx", help="Output Excel / PDF path base")
    parser.add_argument("--api_key", type=str, default=None, help="Google Gemini API Key")
    parser.add_argument("--discipline", type=str, default="ROAD", choices=["ROAD", "TRIATHLON_TT", "GRAVEL_ENDURANCE", "MTB"], help="Riding discipline")
    parser.add_argument("--no_display", action="store_true", help="Run in headless mode without cv2.imshow")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output_excel)), exist_ok=True)
    if args.output_video:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_video)), exist_ok=True)
    report_dir = os.path.dirname(os.path.abspath(args.output_excel))

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"❌ Error: Cannot open input video {args.input}")
        sys.exit(1)
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    out = None
    if args.output_video:
        # Try mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(args.output_video, fourcc, fps, (width, height))

    print("🚀 Initializing NintAi 33-Keypoint Biomechanical Tracking (MediaPipe Heavy)...")
    detector = tracking.PoseDetectorMP()

    # Temporal Smoothing Filters
    filter_keys = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 
                   'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 
                   'left_wrist', 'right_wrist', 'left_hip', 'right_hip', 
                   'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
                   'left_heel', 'right_heel', 'left_toe', 'right_toe']
                   
    filters = {k: core.OneEuroFilter(t0=0, x0=np.zeros(2)) for k in filter_keys}
    bone_enforcer = core.BoneLengthEnforcer()

    frames_data = []
    side_votes = {'left': 0, 'right': 0}
    locked_side = None
    FRAMES_TO_LOCK = 25
    frame_count = 0

    print(f"🎬 Processing video: {args.input} ({total_frames} frames @ {fps:.1f} FPS)...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        t_curr = frame_count / fps
        ts_ms = int(t_curr * 1000)

        results = detector.predict(frame, timestamp_ms=ts_ms)
        raw_lm = detector.get_landmarks_dict(results, frame.shape)
        
        clean_lm = {}
        for k, v in raw_lm.items():
            if k in filters:
                clean_lm[k] = filters[k].filter(t_curr, np.array(v))
            else:
                clean_lm[k] = v
            
        if clean_lm:
            detected = core.detect_side(clean_lm)
            
            if locked_side is None:
                side_votes[detected] += 1
                if frame_count >= FRAMES_TO_LOCK:
                    locked_side = 'left' if side_votes['left'] >= side_votes['right'] else 'right'
                    print(f"✅ Camera Perspective Locked to Rider's: {locked_side.upper()} side")
                current_side = detected 
            else:
                current_side = locked_side
                
            unified_lm = core.get_primary_landmarks(clean_lm, current_side)
            
            # Bone-length consistency
            bone_enforcer.calibrate_step(unified_lm)
            unified_lm = bone_enforcer.enforce(unified_lm)
            
            angles = core.analyze_posture(unified_lm)
            
            frames_data.append({
                'frame_idx': frame_count,
                'angles': angles,
                'landmarks': unified_lm,
                'clean_lm': clean_lm, 
                'side': current_side
            })
            
            # --- Visual Overlays ---
            # 1. Real Foot & Shoe geometry
            if 'ankle' in unified_lm and 'heel' in unified_lm and 'toe' in unified_lm:
                a = tuple(map(int, unified_lm['ankle']))
                h = tuple(map(int, unified_lm['heel']))
                t = tuple(map(int, unified_lm['toe']))
                pts = np.array([a, h, t], np.int32)
                cv2.polylines(frame, [pts], True, (0, 242, 254), 2, cv2.LINE_AA)
                cv2.fillPoly(frame, [pts], (40, 100, 120))

            # 2. Main Skeleton Neon Lines
            skel_lines = [
                ('shoulder', 'elbow', (255, 0, 128)),
                ('elbow', 'wrist', (255, 0, 128)),
                ('shoulder', 'hip', (0, 242, 254)),
                ('hip', 'knee', (0, 255, 128)),
                ('knee', 'ankle', (0, 255, 128))
            ]
            for k1, k2, color in skel_lines:
                if k1 in unified_lm and k2 in unified_lm:
                    p1 = tuple(map(int, unified_lm[k1]))
                    p2 = tuple(map(int, unified_lm[k2]))
                    cv2.line(frame, p1, p2, color, 3, cv2.LINE_AA)

            # 3. Anatomical Joint Dots
            for k, v in clean_lm.items():
                if current_side in k or 'nose' in k:
                    try:
                        pt = tuple(map(int, v))
                        cv2.circle(frame, pt, 5, (0, 0, 255), -1, cv2.LINE_AA)
                        cv2.circle(frame, pt, 7, (255, 255, 255), 1, cv2.LINE_AA)
                    except Exception:
                        pass

            # 4. Angle Labels
            if 'knee' in angles and 'hip' in unified_lm and 'knee' in unified_lm and 'ankle' in unified_lm:
                p1 = tuple(map(int, unified_lm['hip']))
                p2 = tuple(map(int, unified_lm['knee']))
                p3 = tuple(map(int, unified_lm['ankle']))
                core.draw_angle_arc(frame, p1, p2, p3, angles['knee'], (0, 255, 0))

            # 5. Cyberpunk HUD Telemetry Overlay (Top Left)
            overlay = frame.copy()
            cv2.rectangle(overlay, (15, 15), (320, 180), (15, 20, 30), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
            cv2.rectangle(frame, (15, 15), (320, 180), (0, 242, 254), 1)

            cv2.putText(frame, "NINTAI KINEMATICS", (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 242, 254), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Knee Angle: {angles.get('knee', 0):.1f} deg", (25, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Hip Angle:  {angles.get('hip', 0):.1f} deg", (25, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Torso Angle: {angles.get('back', 0):.1f} deg", (25, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Ankling:     {angles.get('foot_angle', 0):.1f} deg", (25, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f"Side: {current_side.upper()} | Frame: {frame_count}", (25, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1, cv2.LINE_AA)

        if out:
            out.write(frame)

        if not args.no_display:
            try:
                cv2.imshow('NintAi Dynamic BikeFit Studio', frame)
                if cv2.waitKey(1) == ord('q'):
                    break
            except Exception:
                pass

        if frame_count % 30 == 0:
            print(f"  -> Processed {frame_count}/{total_frames} frames ({int(frame_count*100/max(total_frames,1))}%)")

    cap.release()
    if out:
        out.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
    
    if not frames_data:
        print("❌ Error: No cyclist motion capture data detected.")
        sys.exit(1)
    
    print(f"✅ Tracking complete! Video saved to: {args.output_video}")
    
    df = pd.DataFrame([f['angles'] for f in frames_data])
    df['frame_idx'] = [f['frame_idx'] for f in frames_data]
    df = df[df['knee'] > 0]
    
    if df.empty:
        sys.exit(0)
    
    # 4-Phase Stroke Extrema
    idx_bdc = df['knee'].idxmax()
    vals_bdc = df.loc[idx_bdc]
    idx_tdc = df['knee'].idxmin()
    vals_tdc = df.loc[idx_tdc]
    
    facing_right = (frames_data[0]['side'] != 'left')
    best_x = -1e9 if facing_right else 1e9
    idx_front = 0
    target_k = 'toe'
    
    for i, f in enumerate(frames_data):
        if target_k in f['landmarks']:
            x = f['landmarks'][target_k][0]
            if (facing_right and x > best_x) or (not facing_right and x < best_x):
                best_x = x
                idx_front = i
    vals_front = df.iloc[idx_front]

    stats = {
        'knee_ext_max': float(df['knee'].max()),
        'knee_flex_min': float(df['knee'].min()),
        'hip_closed_min': float(df['hip'].min()),
        'back_avg': float(df['back'].mean()),
        'back_range': float(df['back'].max() - df['back'].min()),
        'arm_avg': float(df['arm_torso'].mean()),
        'neck_avg': float(df['neck'].mean()),
        'wrist_tilt_avg': float(df['wrist_tilt'].mean()),
        'foot_angle_avg': float(df.get('foot_angle', pd.Series([95.0])).mean())
    }
    
    print("📸 Extracting 4-Phase Diagnostic Snapshots...")
    
    def create_snapshot(idx, filename, title, overlay_metrics):
        c = cv2.VideoCapture(args.input)
        c.set(cv2.CAP_PROP_POS_FRAMES, frames_data[idx]['frame_idx'] - 1)
        _, img = c.read()
        c.release()
        if img is None:
            return None
        
        lm = frames_data[idx]['landmarks']
        clean_lm = frames_data[idx]['clean_lm']

        if 'ankle' in lm and 'heel' in lm and 'toe' in lm:
            a = tuple(map(int, lm['ankle']))
            h = tuple(map(int, lm['heel']))
            t = tuple(map(int, lm['toe']))
            pts = np.array([a, h, t], np.int32)
            cv2.polylines(img, [pts], True, (0, 242, 254), 2)
            cv2.fillPoly(img, [pts], (40, 100, 120))

        skel = [('shoulder', 'elbow'), ('elbow', 'wrist'), 
                ('shoulder', 'hip'), ('hip', 'knee'), ('knee', 'ankle')]
        for k1, k2 in skel:
            if k1 in lm and k2 in lm:
                p1 = tuple(map(int, lm[k1]))
                p2 = tuple(map(int, lm[k2]))
                cv2.line(img, p1, p2, (0, 255, 255), 3, cv2.LINE_AA)
        
        for k, v in clean_lm.items():
            if frames_data[idx]['side'] in k or 'nose' in k:
                try:
                    cv2.circle(img, tuple(map(int, v)), 5, (0, 0, 255), -1)
                except Exception:
                    pass

        cv2.putText(img, title, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 128), 2, cv2.LINE_AA)
        y = 90
        for k, v in overlay_metrics.items():
            label = f"{k}: {v:.1f} deg"
            cv2.putText(img, label, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
            y += 35
            
        path = os.path.join(report_dir, filename)
        cv2.imwrite(path, img)
        return path

    snap_tdc = create_snapshot(df.index.get_loc(idx_tdc), "quad_tdc.jpg", "Top (TDC 12h)", 
                               {'Knee Flex': vals_tdc['knee'], 'Hip Closed': vals_tdc['hip']})
    snap_bdc = create_snapshot(df.index.get_loc(idx_bdc), "quad_bdc.jpg", "Bottom (BDC 6h)", 
                               {'Knee Ext': vals_bdc['knee'], 'Hip Open': vals_bdc['hip']})
    snap_front = create_snapshot(idx_front, "quad_front.jpg", "Power Phase (3h)", 
                                 {'Knee': vals_front['knee'], 'Ankling': vals_front.get('foot_angle', 95.0)})
    snap_over = create_snapshot(df.index.get_loc(idx_bdc), "quad_overall.jpg", "Overall Posture", 
                                {'Back': stats['back_avg'], 'Torso Incline': stats['back_avg']})
    
    clinical_data = {'stats': stats}
    print("🤖 Consulting Gemini AI Bike Fitter...")
    ai_text = ai_report.generate_ai_analysis(stats, [], api_key=args.api_key)
    
    pdf_path = args.output_excel.replace(".xlsx", ".pdf")
    print(f"📄 Compiling Clinical PDF Dossier to {pdf_path}...")
    report.generate_quad_report(snap_tdc, snap_bdc, snap_front, snap_over, clinical_data, pdf_path, ai_text)
    print(f"🎉 Complete! Report generated: {pdf_path}")

if __name__ == "__main__":
    main()
