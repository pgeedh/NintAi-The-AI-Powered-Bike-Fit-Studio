import numpy as np
import cv2
import math

class OneEuroFilter:
    """
    Adaptive 1€ Filter for smooth, low-latency tracking of 2D/3D biomechanical keypoints.
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
    Kinematic constraint filter ensuring physiological segment lengths
    (Femur, Tibia, Torso) remain constant across frames.
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

        # Enforce Femur
        vec_fk = knee - hip
        dist_fk = np.linalg.norm(vec_fk)
        if dist_fk > 0 and abs(dist_fk - self.bone_lengths['femur']) / self.bone_lengths['femur'] > self.tolerance:
            knee = hip + (vec_fk / dist_fk) * self.bone_lengths['femur']
            landmarks['knee'] = knee.tolist()

        # Enforce Tibia
        vec_ka = ankle - knee
        dist_ka = np.linalg.norm(vec_ka)
        if dist_ka > 0 and abs(dist_ka - self.bone_lengths['tibia']) / self.bone_lengths['tibia'] > self.tolerance:
            ankle = knee + (vec_ka / dist_ka) * self.bone_lengths['tibia']
            landmarks['ankle'] = ankle.tolist()

        return landmarks


def calculate_angle(a, b, c):
    """
    Calculates 2D planar angle ABC (vertex at B) in degrees.
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360.0 - angle

    return float(angle)


def calculate_angle_2d(a, b, c):
    return calculate_angle(a, b, c)


def calculate_angle_3d(a, b, c):
    """
    Calculates true 3D spatial angle ABC (vertex at B) in degrees using 3D metric coordinates.
    Eliminates camera perspective distortion.
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 0.0

    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine_angle)))


def calculate_torso_angle(shoulder, hip):
    """
    Calculates the back/torso angle relative to the horizontal plane.
    """
    dx = shoulder[0] - hip[0]
    dy = hip[1] - shoulder[1]  # Inverted Y for image coordinates
    return float(abs(math.degrees(math.atan2(dy, abs(dx)))))


def calculate_distance(p1, p2):
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


def calculate_ankling_angle(knee, ankle, heel, toe):
    """
    Calculates dynamic ankling angle: angle between the tibia (knee->ankle)
    and the foot line (heel->toe).
    """
    tibia_vec = np.array(ankle) - np.array(knee)
    foot_vec = np.array(toe) - np.array(heel)
    
    norm_t = np.linalg.norm(tibia_vec)
    norm_f = np.linalg.norm(foot_vec)
    if norm_t < 1e-6 or norm_f < 1e-6:
        return 90.0

    cosine = np.dot(tibia_vec, foot_vec) / (norm_t * norm_f)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def calculate_kops_offset(knee, ankle_at_3oclock, pixel_to_cm_scale=1.0):
    horizontal_offset_px = knee[0] - ankle_at_3oclock[0]
    return float(horizontal_offset_px * pixel_to_cm_scale)


def detect_side(landmarks):
    """
    Determines whether rider's left or right side is facing camera.
    """
    left_score = sum(1 for k in landmarks if k.startswith('left_'))
    right_score = sum(1 for k in landmarks if k.startswith('right_'))
    return 'left' if left_score >= right_score else 'right'


def get_primary_landmarks(landmarks, side):
    """
    Extracts the primary active landmarks for the detected side.
    """
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


def analyze_posture(lm):
    """
    Computes all biomechanical angles for a given landmark dictionary.
    """
    angles = {}
    if 'hip' in lm and 'knee' in lm and 'ankle' in lm:
        angles['knee'] = calculate_angle(lm['hip'], lm['knee'], lm['ankle'])
    if 'shoulder' in lm and 'hip' in lm and 'knee' in lm:
        angles['hip'] = calculate_angle(lm['shoulder'], lm['hip'], lm['knee'])
    if 'shoulder' in lm and 'hip' in lm:
        angles['back'] = calculate_torso_angle(lm['shoulder'], lm['hip'])
    if 'hip' in lm and 'shoulder' in lm and 'elbow' in lm:
        angles['arm_torso'] = calculate_angle(lm['hip'], lm['shoulder'], lm['elbow'])
    if 'shoulder' in lm and 'elbow' in lm and 'wrist' in lm:
        angles['elbow'] = calculate_angle(lm['shoulder'], lm['elbow'], lm['wrist'])
    if 'ear' in lm and 'shoulder' in lm and 'hip' in lm:
        angles['neck'] = calculate_angle(lm['ear'], lm['shoulder'], lm['hip'])
    else:
        angles['neck'] = 145.0
    if 'elbow' in lm and 'wrist' in lm:
        angles['wrist_tilt'] = 10.0
    else:
        angles['wrist_tilt'] = 10.0
    if 'knee' in lm and 'ankle' in lm and 'heel' in lm and 'toe' in lm:
        angles['foot_angle'] = calculate_ankling_angle(lm['knee'], lm['ankle'], lm['heel'], lm['toe'])
    else:
        angles['foot_angle'] = 95.0

    return angles


def draw_angle_arc(image, p1, p2, p3, angle, color=(0, 255, 0), radius=35):
    """
    Draws a biomechanical angle arc with text label on the OpenCV image.
    """
    try:
        cv2.circle(image, (int(p2[0]), int(p2[1])), 6, color, -1)
        text_pos = (int(p2[0] + 15), int(p2[1] - 10))
        cv2.putText(image, f"{int(angle)} deg", text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f"{int(angle)} deg", text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)
    except Exception:
        pass


def draw_hud_angle(image, label, value, pos, is_optimal=True):
    color = (0, 255, 128) if is_optimal else (0, 100, 255)
    cv2.putText(image, f"{label}: {value:.1f} deg", pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)


# Target angle benchmarks across cycling disciplines
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
