"""
NintAi Biomechanical Kinematics Engine.
Mathematical formulations for cycling dynamic motion capture.
"""

import math
import cv2
import numpy as np

class OneEuroFilter:
    """
    Adaptive 1€ Filter for low-latency signal smoothing.
    """
    def __init__(self, t0=0, x0=None, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        if x0 is None:
            x0 = np.zeros(2)
        self.t_prev = float(t0)
        self.x_prev = np.array(x0, dtype=float)
        self.dx_prev = np.zeros_like(self.x_prev, dtype=float)
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, t, x):
        x = np.array(x, dtype=float)
        if self.x_prev is None or self.x_prev.shape != x.shape:
            self.x_prev = x.copy()
            self.dx_prev = np.zeros_like(x, dtype=float)
            self.t_prev = float(t)
            return x

        dt = float(t) - self.t_prev
        if dt <= 1e-5:
            return self.x_prev

        dx = (x - self.x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        cutoff = self.min_cutoff + self.beta * np.linalg.norm(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1.0 - a) * self.x_prev

        self.t_prev = float(t)
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat

    def __call__(self, t, x):
        return self.filter(t, x)


class BoneLengthEnforcer:
    """
    Constrains anatomical segment lengths (femur, tibia, torso) to constant bounds.
    """
    def __init__(self, tolerance=0.08):
        self.tolerance = tolerance
        self.calibrated = False
        self.bone_lengths = {}
        self.samples = {'femur': [], 'tibia': [], 'torso': []}

    def calibrate_step(self, landmarks):
        if 'hip' in landmarks and 'knee' in landmarks:
            self.samples['femur'].append(np.linalg.norm(np.array(landmarks['knee']) - np.array(landmarks['hip'])))
        if 'knee' in landmarks and 'ankle' in landmarks:
            self.samples['tibia'].append(np.linalg.norm(np.array(landmarks['ankle']) - np.array(landmarks['knee'])))
        if 'hip' in landmarks and 'shoulder' in landmarks:
            self.samples['torso'].append(np.linalg.norm(np.array(landmarks['shoulder']) - np.array(landmarks['hip'])))

        if len(self.samples['femur']) >= 25:
            self.bone_lengths['femur'] = float(np.median(self.samples['femur']))
            self.bone_lengths['tibia'] = float(np.median(self.samples['tibia']))
            self.bone_lengths['torso'] = float(np.median(self.samples['torso']))
            self.calibrated = True

    def enforce(self, landmarks):
        if not self.calibrated or 'hip' not in landmarks or 'knee' not in landmarks or 'ankle' not in landmarks:
            return landmarks

        hip = np.array(landmarks['hip'], dtype=float)
        knee = np.array(landmarks['knee'], dtype=float)
        ankle = np.array(landmarks['ankle'], dtype=float)

        vec_fk = knee - hip
        dist_fk = np.linalg.norm(vec_fk)
        if dist_fk > 0 and abs(dist_fk - self.bone_lengths['femur']) / self.bone_lengths['femur'] > self.tolerance:
            knee = hip + (vec_fk / dist_fk) * self.bone_lengths['femur']
            landmarks['knee'] = knee.tolist()

        vec_ka = ankle - knee
        dist_ka = np.linalg.norm(vec_ka)
        if dist_ka > 0 and abs(dist_ka - self.bone_lengths['tibia']) / self.bone_lengths['tibia'] > self.tolerance:
            ankle = knee + (vec_ka / dist_ka) * self.bone_lengths['tibia']
            landmarks['ankle'] = ankle.tolist()

        return landmarks


def calculate_angle_2d(a, b, c) -> float:
    """
    Computes interior 2D planar angle ABC (vertex at B).
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360.0 - angle

    return float(angle)


def calculate_angle_3d(a, b, c) -> float:
    """
    Computes 3D spatial angle ABC in degrees using metric world coordinates.
    """
    ba = np.array(a, dtype=float) - np.array(b, dtype=float)
    bc = np.array(c, dtype=float) - np.array(b, dtype=float)

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 0.0

    cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def calculate_torso_angle(shoulder, hip) -> float:
    dx = shoulder[0] - hip[0]
    dy = hip[1] - shoulder[1]
    return float(abs(math.degrees(math.atan2(dy, abs(dx)))))


def calculate_ankling_angle(knee, ankle, heel, toe) -> float:
    tibia_vec = np.array(ankle) - np.array(knee)
    foot_vec = np.array(toe) - np.array(heel)

    norm_t = np.linalg.norm(tibia_vec)
    norm_f = np.linalg.norm(foot_vec)
    if norm_t < 1e-6 or norm_f < 1e-6:
        return 90.0

    cosine = np.dot(tibia_vec, foot_vec) / (norm_t * norm_f)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def detect_rider_side(landmarks: dict) -> str:
    left_score = sum(1 for k in landmarks if k.startswith('left_'))
    right_score = sum(1 for k in landmarks if k.startswith('right_'))
    return 'left' if left_score >= right_score else 'right'


def extract_primary_side_landmarks(landmarks: dict, side: str) -> dict:
    primary = {}
    for key in ['shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle', 'heel', 'toe', 'ear', 'eye']:
        side_key = f"{side}_{key}"
        if side_key in landmarks:
            primary[key] = landmarks[side_key]
        elif key in landmarks:
            primary[key] = landmarks[key]
    if 'nose' in landmarks:
        primary['nose'] = landmarks['nose']
    return primary


def compute_postural_angles(lm: dict) -> dict:
    angles = {}
    if 'hip' in lm and 'knee' in lm and 'ankle' in lm:
        angles['knee'] = calculate_angle_2d(lm['hip'], lm['knee'], lm['ankle'])
    if 'shoulder' in lm and 'hip' in lm and 'knee' in lm:
        angles['hip'] = calculate_angle_2d(lm['shoulder'], lm['hip'], lm['knee'])
    if 'shoulder' in lm and 'hip' in lm:
        angles['back'] = calculate_torso_angle(lm['shoulder'], lm['hip'])
    if 'hip' in lm and 'shoulder' in lm and 'elbow' in lm:
        angles['arm_torso'] = calculate_angle_2d(lm['hip'], lm['shoulder'], lm['elbow'])
    if 'shoulder' in lm and 'elbow' in lm and 'wrist' in lm:
        angles['elbow'] = calculate_angle_2d(lm['shoulder'], lm['elbow'], lm['wrist'])
    if 'knee' in lm and 'ankle' in lm and 'heel' in lm and 'toe' in lm:
        angles['foot_angle'] = calculate_ankling_angle(lm['knee'], lm['ankle'], lm['heel'], lm['toe'])
    else:
        angles['foot_angle'] = 95.0
    return angles


def draw_skeleton_and_angles(frame: np.ndarray, unified_lm: dict, angles: dict, side: str):
    # Foot shoe polygon
    if 'ankle' in unified_lm and 'heel' in unified_lm and 'toe' in unified_lm:
        a = tuple(map(int, unified_lm['ankle']))
        h = tuple(map(int, unified_lm['heel']))
        t = tuple(map(int, unified_lm['toe']))
        pts = np.array([a, h, t], np.int32)
        cv2.polylines(frame, [pts], True, (0, 229, 255), 2, cv2.LINE_AA)
        cv2.fillPoly(frame, [pts], (30, 45, 60))

    # Kinetic Chain Lines
    skel_lines = [
        ('shoulder', 'elbow', (255, 0, 128)),
        ('elbow', 'wrist', (255, 0, 128)),
        ('shoulder', 'hip', (0, 229, 255)),
        ('hip', 'knee', (16, 185, 129)),
        ('knee', 'ankle', (16, 185, 129))
    ]
    for k1, k2, col in skel_lines:
        if k1 in unified_lm and k2 in unified_lm:
            p1 = tuple(map(int, unified_lm[k1]))
            p2 = tuple(map(int, unified_lm[k2]))
            cv2.line(frame, p1, p2, col, 3, cv2.LINE_AA)

    # Knee Angle Arc
    if 'hip' in unified_lm and 'knee' in unified_lm and 'ankle' in unified_lm and 'knee' in angles:
        kp = tuple(map(int, unified_lm['knee']))
        cv2.circle(frame, kp, 6, (16, 185, 129), -1, cv2.LINE_AA)
        cv2.putText(frame, f"{angles['knee']:.1f} deg", (kp[0] + 14, kp[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    # Open-BikeFit Telemetry HUD Card (Top Left)
    overlay = frame.copy()
    cv2.rectangle(overlay, (15, 15), (290, 155), (18, 18, 20), -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
    cv2.rectangle(frame, (15, 15), (290, 155), (58, 58, 60), 1)

    cv2.putText(frame, "OPEN-BIKEFIT", (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 159, 10), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Knee Ext:   {angles.get('knee', 0):.1f} deg", (25, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (245, 245, 247), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Closed Hip: {angles.get('hip', 0):.1f} deg", (25, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (245, 245, 247), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Torso:      {angles.get('back', 0):.1f} deg", (25, 116), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (245, 245, 247), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Ankling:    {angles.get('foot_angle', 0):.1f} deg", (25, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (245, 245, 247), 1, cv2.LINE_AA)


# Target Benchmarks
FIT_TARGETS = {
    "ROAD": {
        "knee_ext_max": (140, 150),
        "knee_flex_min": (68, 75),
        "hip_closed_min": (45, 55),
        "back_avg": (40, 50),
        "arm_avg": (85, 95),
        "ankling_bdc": (90, 105),
    },
    "TRIATHLON_TT": {
        "knee_ext_max": (145, 153),
        "knee_flex_min": (65, 72),
        "hip_closed_min": (40, 48),
        "back_avg": (15, 25),
        "arm_avg": (80, 90),
        "ankling_bdc": (95, 110),
    },
    "GRAVEL_ENDURANCE": {
        "knee_ext_max": (138, 148),
        "knee_flex_min": (70, 78),
        "hip_closed_min": (50, 60),
        "back_avg": (45, 55),
        "arm_avg": (85, 95),
        "ankling_bdc": (90, 100),
    },
    "MTB": {
        "knee_ext_max": (135, 145),
        "knee_flex_min": (72, 80),
        "hip_closed_min": (55, 65),
        "back_avg": (50, 60),
        "arm_avg": (90, 100),
        "ankling_bdc": (85, 95),
    }
}
