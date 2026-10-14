"""
NintAi analysis engine.

Pure functions that turn a video or photo into fit metrics, annotated frames and
recommendations. No GUI calls (cv2.imshow etc.) so it can power both the
FastAPI/Streamlit web apps and the command-line scripts.
"""
import os
import sys

import cv2
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import core  # noqa: E402
from src import fit_profiles as fp  # noqa: E402
from src import pose_backends as pb  # noqa: E402
from src import biomech  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

FILTER_KEYS = ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
               'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
               'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
               'left_knee', 'right_knee', 'left_ankle', 'right_ankle',
               'left_heel', 'right_heel', 'left_toe', 'right_toe']

SKELETON = [('shoulder', 'elbow'), ('elbow', 'wrist'), ('shoulder', 'hip'),
            ('hip', 'knee'), ('knee', 'ankle'), ('ear', 'shoulder')]

# Apple-inspired aesthetic palette (BGR)
C_BONE = (245, 200, 40)        # Electric cyan-blue
C_JOINT = (60, 60, 255)       # Coral red
C_FOOT = (0, 215, 255)        # Vibrant amber
C_OK = (94, 197, 34)          # Emerald green
C_WATCH = (0, 170, 255)       # Amber warning
C_FIX = (68, 68, 239)         # Crimson alert
STATUS_BGR = {'ok': C_OK, 'watch': C_WATCH, 'fix': C_FIX, 'na': (200, 200, 200)}


class AnalysisError(Exception):
    """Raised with a user-friendly message when analysis can't proceed."""


# --------------------------------------------------------------------------- #
# Drawing & Overlay
# --------------------------------------------------------------------------- #
def _pt(v):
    return int(round(v[0])), int(round(v[1]))


def _label(img, text, org, color, scale=0.6):
    """Text with a frosted dark rounded background pill for legibility."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    th = max(1, int(round(scale * 2)))
    (w, h), base = cv2.getTextSize(text, font, scale, th)
    x, y = org
    x = max(2, min(x, img.shape[1] - w - 8))
    y = max(h + 6, min(y, img.shape[0] - 6))
    cv2.rectangle(img, (x - 6, y - h - 6), (x + w + 6, y + base + 3), (16, 18, 24), -1)
    cv2.rectangle(img, (x - 6, y - h - 6), (x + w + 6, y + base + 3), (45, 50, 65), 1, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), font, scale, color, th, cv2.LINE_AA)


def draw_overlay(img, lm, angles=None, statuses=None, title=None):
    """Draw skeleton, foot polygon and joint angle labels onto img (in place)."""
    angles = angles or {}
    statuses = statuses or {}
    scale = max(0.5, min(1.4, img.shape[1] / 1100.0))
    thick = max(2, int(3 * scale))

    if all(k in lm for k in ('ankle', 'heel', 'toe')):
        pts = np.array([_pt(lm['ankle']), _pt(lm['heel']), _pt(lm['toe'])], np.int32)
        overlay = img.copy()
        cv2.fillPoly(overlay, [pts], C_FOOT)
        cv2.addWeighted(overlay, 0.35, img, 0.65, 0, img)
        cv2.polylines(img, [pts], True, C_FOOT, thick, cv2.LINE_AA)

    for a, b in SKELETON:
        if a in lm and b in lm:
            cv2.line(img, _pt(lm[a]), _pt(lm[b]), C_BONE, thick + 1, cv2.LINE_AA)

    for k in ('ear', 'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle'):
        if k in lm:
            cv2.circle(img, _pt(lm[k]), int(7 * scale), (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(img, _pt(lm[k]), int(5 * scale), C_JOINT, -1, cv2.LINE_AA)

    # Angle labels next to joints
    joint_for = {'knee': ('knee', 'knee_ext'), 'hip': ('hip', 'hip_closed'),
                 'elbow': ('elbow', 'elbow'), 'arm_torso': ('shoulder', 'shoulder')}
    for akey, (joint, mkey) in joint_for.items():
        v = angles.get(akey, 0)
        if v and joint in lm:
            col = STATUS_BGR.get(statuses.get(mkey), (255, 255, 255))
            x, y = _pt(lm[joint])
            _label(img, f"{v:.0f}°", (x + int(14 * scale), y - int(10 * scale)), col, 0.55 * scale + 0.1)

    if title:
        _label(img, title, (int(18 * scale), int(40 * scale)), (255, 255, 255), 0.8 * scale)
    return img


def _resize(frame, max_width):
    h, w = frame.shape[:2]
    if max_width and w > max_width:
        s = max_width / float(w)
        frame = cv2.resize(frame, (max_width, int(round(h * s))), interpolation=cv2.INTER_AREA)
    return frame


def _to_jpeg(img, width=640, quality=80):
    small = _resize(img, width)
    ok, buf = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ok else None


# --------------------------------------------------------------------------- #
# Video Analysis
# --------------------------------------------------------------------------- #
def analyze_video(path, profile_key=fp.DEFAULT_PROFILE, progress_cb=None,
                  target_fps=15, max_seconds=60, max_width=1280, keep_preview=True,
                  output_video=None, backend='auto', crank_mm=172.5, rider_height_cm=None):
    """
    Analyse a side-on cycling video.

    backend: 'auto' (chooses rtmpose if available, else mediapipe), 'rtmpose', or 'mediapipe'.
    progress_cb(fraction, message) is called periodically if provided.
    Returns a result dict.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise AnalysisError("Couldn't open this video. Try exporting it as .mp4 (H.264).")

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if src_fps <= 1 or src_fps > 240:
        src_fps = 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    stride = max(1, int(round(src_fps / float(target_fps))))
    max_src_frames = int(max_seconds * src_fps) if max_seconds else None
    if max_src_frames and total:
        total = min(total, max_src_frames)

    # Resolve backend
    avail = pb.available()
    if backend == 'auto':
        backend = 'rtmpose' if avail.get('rtmpose') else 'mediapipe'
    elif backend not in avail or not avail[backend]:
        backend = 'mediapipe'

    detector = pb.make_backend(backend, mode='video')
    filters = {k: core.LazyOneEuroFilter() for k in FILTER_KEYS}

    frames = []          # per processed frame data
    raw_landmarks_list = []
    times_list = []
    previews = []        # JPEG bytes of annotated frames
    side_votes = {'left': 0, 'right': 0}
    locked_side = None
    processed = detected_count = 0
    writer = None

    src_idx = -1
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        src_idx += 1
        if max_src_frames and src_idx >= max_src_frames:
            break
        if src_idx % stride:
            continue

        frame = _resize(frame, max_width)
        t = src_idx / src_fps
        processed += 1

        raw = detector.process(frame, ts_ms=int(t * 1000))
        # raw is dict {name: (x, y, conf)}
        raw_xy = {k: [v[0], v[1]] for k, v in raw.items()}
        clean = {k: (filters[k](t, v) if k in filters else np.asarray(v)) for k, v in raw_xy.items()}

        angles = {}
        unified = {}
        if clean:
            detected_count += 1
            side = core.detect_side(clean)
            if locked_side is None:
                side_votes[side] += 1
                if sum(side_votes.values()) >= 15:
                    locked_side = 'left' if side_votes['left'] >= side_votes['right'] else 'right'
            cur_side = locked_side or side
            unified = core.get_primary_landmarks(clean, cur_side)
            angles = core.analyze_posture(unified)
            frames.append({'src_idx': src_idx, 't': t, 'angles': angles,
                           'lm': {k: np.asarray(v).tolist() for k, v in unified.items() if k != 'side'}})
            raw_landmarks_list.append(raw)
            times_list.append(t)

        if keep_preview or output_video:
            vis = frame.copy()
            if unified:
                draw_overlay(vis, unified, angles)
            else:
                _label(vis, "Locating rider...", (20, 40), (0, 170, 255), 0.8)
            if keep_preview and len(previews) < 600:
                previews.append({'t': t, 'jpg': _to_jpeg(vis)})
            if output_video:
                if writer is None:
                    h, w = vis.shape[:2]
                    writer = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(*'mp4v'),
                                             src_fps / stride, (w, h))
                writer.write(vis)

        if progress_cb and processed % 5 == 0:
            frac = (src_idx / total) if total else 0.0
            progress_cb(min(frac, 0.99), f"Tracking rider with {pb.BACKENDS[backend]['name']}... {t:.1f}s")

    cap.release()
    detector.close()
    if writer is not None:
        writer.release()

    duration = (src_idx + 1) / src_fps if src_idx >= 0 else 0
    if processed == 0:
        raise AnalysisError("The video appears to be empty or unreadable.")
    if not frames:
        raise AnalysisError(
            "No rider was detected. Make sure the whole body and bike are in frame, "
            "filmed from the side, with adequate lighting.")

    df = pd.DataFrame([dict(f['angles'], t=f['t'], i=n) for n, f in enumerate(frames)])
    valid = df[df['knee'] > 0]
    if len(valid) < 5:
        raise AnalysisError("The leg wasn't visible clearly enough to measure. "
                            "Film from the side with hip, knee and ankle clearly in view.")

    chosen_side = locked_side or 'right'
    facing_right = chosen_side == 'right'

    # Advanced biomechanical sequence analysis
    bio = biomech.analyze_sequence(raw_landmarks_list, times_list, chosen_side, facing_right,
                                   crank_mm=crank_mm, rider_height_cm=rider_height_cm)

    # Extract metrics from biomech per-stroke analysis if available, otherwise robust percentiles
    ps = bio.get('per_stroke', {})
    def metric_val(key, fallback_col, q):
        if key in ps and ps[key] and ps[key].get('median') is not None:
            return float(ps[key]['median'])
        s = valid[fallback_col]
        s = s[s > 0]
        return float(np.percentile(s, q)) if len(s) else 0.0

    metrics = {
        'knee_ext': metric_val('knee_ext', 'knee', 97),
        'knee_flex': metric_val('knee_flex', 'knee', 3),
        'hip_closed': metric_val('hip_closed', 'hip', 3),
        'torso': metric_val('torso', 'back', 50),
        'shoulder': metric_val('shoulder', 'arm_torso', 50),
        'elbow': metric_val('elbow', 'elbow', 50),
    }

    torso_s = valid['back'][valid['back'] > 0]
    torso_range = float(np.percentile(torso_s, 95) - np.percentile(torso_s, 5)) if len(torso_s) > 5 else None
    knee_range = metrics['knee_ext'] - metrics['knee_flex']

    # Quality checks -> friendly warnings
    warnings = []
    det_rate = detected_count / float(processed)
    if det_rate < 0.6:
        warnings.append(f"Rider was only detected in {det_rate:.0%} of frames — results may be noisy. "
                        "Better lighting and a contrasting background help.")
    if duration < 5:
        warnings.append("Video is shorter than 5s. Record 10–30s of steady pedalling for optimal accuracy.")
    if knee_range < 35:
        warnings.append("The knee barely changed angle — pedal through multiple continuous strokes.")
    side_ratio = _shoulder_overlap(frames)
    if side_ratio is not None and side_ratio > 0.45:
        warnings.append("Camera does not look fully side-on (both shoulders visible). "
                        "Align perpendicular (90°) to the bike frame.")

    # Key frames selection
    def nearest(col, target):
        return int((valid[col] - target).abs().idxmin())

    key = {
        'bdc': (nearest('knee', metrics['knee_ext']), "Bottom of Stroke (BDC)"),
        'tdc': (nearest('knee', metrics['knee_flex']), "Top of Stroke (TDC)"),
    }
    toe_xs = [(n, f['lm']['toe'][0]) for n, f in enumerate(frames) if 'toe' in f['lm']]
    if toe_xs:
        n_front = max(toe_xs, key=lambda p: p[1] if facing_right else -p[1])[0]
        key['front'] = (n_front, "3 o'clock (Power Phase)")

    statuses = {k: fp.status_for(v, fp.PROFILES[profile_key]['ranges'][k]) for k, v in metrics.items()}
    snapshots = _grab_snapshots(path, frames, key, max_width, statuses)

    recs = fp.build_recommendations(metrics, profile_key, {'torso_range': torso_range, 'mode': 'video'})

    # Geometric saddle adjustment (law-of-cosines)
    der = bio.get('derived', {})
    target_ext = fp.PROFILES[profile_key]['ranges']['knee_ext']
    target_mid = (target_ext[0] + target_ext[1]) / 2.0
    calc_saddle_adj = biomech.saddle_change_mm(metrics['knee_ext'], target_mid,
                                              der.get('thigh_px'), der.get('shank_px'), der.get('mm_per_px'))
    if calc_saddle_adj is not None:
        der['saddle_adj_mm'] = float(calc_saddle_adj)

    return {
        'mode': 'video',
        'backend': backend,
        'backend_name': pb.BACKENDS[backend]['name'],
        'profile': profile_key,
        'metrics': metrics,
        'statuses': statuses,
        'score': fp.fit_score(metrics, profile_key),
        'recommendations': recs,
        'warnings': warnings,
        'snapshots': snapshots,
        'timeseries': df.rename(columns={'back': 'torso', 'arm_torso': 'shoulder'}),
        'previews': previews,
        'biomech': {
            'cadence_rpm': der.get('cadence_rpm'),
            'kops_mm': der.get('kops_mm'),
            'hip_rock_mm': der.get('hip_rock_mm'),
            'scale_source': der.get('scale_source'),
            'per_stroke': ps,
            'cycles_detected': len(bio.get('cycles', [])),
            'saddle_adj_mm': der.get('saddle_adj_mm'),
        },
        'extra': {
            'duration_s': duration, 'frames_analysed': processed,
            'detection_rate': det_rate, 'side': chosen_side,
            'torso_range': torso_range, 'knee_range': knee_range,
        },
    }


def _shoulder_overlap(frames):
    """Ratio of left/right shoulder separation to torso length (0 = perfect side view)."""
    vals = []
    for f in frames[:: max(1, len(frames) // 50)]:
        lm = f['lm']
        if all(k in lm for k in ('left_shoulder', 'right_shoulder', 'shoulder', 'hip')):
            sep = np.linalg.norm(np.subtract(lm['left_shoulder'], lm['right_shoulder']))
            torso = np.linalg.norm(np.subtract(lm['shoulder'], lm['hip']))
            if torso > 1:
                vals.append(sep / torso)
    return float(np.median(vals)) if vals else None


def _grab_snapshots(path, frames, key, max_width, statuses):
    cap = cv2.VideoCapture(path)
    out = {}
    for name, (n, title) in key.items():
        f = frames[n]
        cap.set(cv2.CAP_PROP_POS_FRAMES, f['src_idx'])
        ok, img = cap.read()
        if not ok:
            continue
        img = _resize(img, max_width)
        st = dict(statuses)
        if name == 'tdc':
            st['knee_ext'] = statuses.get('knee_flex', 'na')
        elif name != 'bdc':
            st['knee_ext'] = 'na'
        draw_overlay(img, f['lm'], f['angles'], st, title=title)
        out[name] = {'title': title, 'jpg': _to_jpeg(img, width=1100, quality=88),
                     'angles': f['angles']}
    cap.release()
    return out


# --------------------------------------------------------------------------- #
# Photo Analysis
# --------------------------------------------------------------------------- #
def load_image(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        arr = np.frombuffer(path_or_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(path_or_bytes)
    if img is None:
        raise AnalysisError("Couldn't read this image. Use JPG, PNG or WEBP.")
    return img


def analyze_image(path_or_bytes, profile_key=fp.DEFAULT_PROFILE, crank_position='auto',
                  max_width=1600, backend='auto'):
    """
    Analyse a single side-on photo.

    backend: 'auto', 'rtmpose', or 'mediapipe'.
    crank_position: 'bottom' (6 o'clock), 'top' (12 o'clock), 'other' or 'auto'.
    """
    img = _resize(load_image(path_or_bytes), max_width)

    avail = pb.available()
    if backend == 'auto':
        backend = 'rtmpose' if avail.get('rtmpose') else 'mediapipe'
    elif backend not in avail or not avail[backend]:
        backend = 'mediapipe'

    detector = pb.make_backend(backend, mode='image')
    try:
        raw = detector.process(img)
    finally:
        detector.close()
    if not raw:
        raise AnalysisError("No rider detected. Use a side-on photo with the whole body in frame.")

    raw_xy = {k: [v[0], v[1]] for k, v in raw.items()}
    side = core.detect_side(raw_xy)
    lm = core.get_primary_landmarks(raw_xy, side)
    angles = core.analyze_posture(lm)
    knee = angles.get('knee', 0)

    if crank_position == 'auto':
        crank_position = 'bottom' if knee >= 125 else ('top' if 0 < knee <= 95 else 'other')

    metrics = {'torso': angles.get('back', 0), 'shoulder': angles.get('arm_torso', 0),
               'elbow': angles.get('elbow', 0), 'knee_ext': 0, 'knee_flex': 0, 'hip_closed': 0}
    if crank_position == 'bottom':
        metrics['knee_ext'] = knee
    elif crank_position == 'top':
        metrics['knee_flex'] = knee
        metrics['hip_closed'] = angles.get('hip', 0)

    warnings = []
    if crank_position == 'other':
        warnings.append("Pedals aren't at 6 o'clock (BDC) or 12 o'clock (TDC). "
                        "For saddle height measurement, take a photo with the pedal nearest the camera at 6 o'clock.")
    elif crank_position == 'top':
        warnings.append("Pedal is at TDC (12 o'clock). For complete saddle height verification, capture at 6 o'clock.")
    if not angles.get('knee'):
        warnings.append("Couldn't see the leg clearly (hip / knee / ankle).")
    warnings.append("A photo represents a static snapshot. For dynamic pedalling biomechanics, upload a 10–30s video.")

    statuses = {k: fp.status_for(v, fp.PROFILES[profile_key]['ranges'][k]) for k, v in metrics.items()}
    vis = img.copy()
    draw_overlay(vis, lm, angles, statuses)

    return {
        'mode': 'image',
        'backend': backend,
        'backend_name': pb.BACKENDS[backend]['name'],
        'profile': profile_key,
        'metrics': metrics,
        'raw_angles': angles,
        'statuses': statuses,
        'score': fp.fit_score(metrics, profile_key),
        'recommendations': fp.build_recommendations(metrics, profile_key, {'mode': 'image'}),
        'warnings': warnings,
        'snapshots': {'photo': {'title': 'Your Position', 'jpg': _to_jpeg(vis, width=1400, quality=90),
                                'angles': angles}},
        'timeseries': None,
        'previews': [],
        'biomech': {},
        'extra': {'side': side, 'crank_position': crank_position},
    }


def save_snapshots(result, out_dir):
    """Write snapshot JPEGs to disk (for PDF generation). Returns {key: path}."""
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for k, s in result['snapshots'].items():
        if s.get('jpg'):
            p = os.path.join(out_dir, f"snap_{k}.jpg")
            with open(p, 'wb') as fh:
                fh.write(s['jpg'])
            paths[k] = p
    return paths
