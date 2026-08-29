import numpy as np
import cv2
import math

class OneEuroFilter:
    """
    Adaptive 1€ Filter for smooth, low-latency tracking of 2D/3D biomechanical keypoints.
    """
    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.t_prev = t0
        self.x_prev = np.array(x0, dtype=float)
        self.dx_prev = np.zeros_like(x0, dtype=float)
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

    def _alpha(self, cutoff, dt):
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def filter(self, t, x):
        dt = t - self.t_prev
        if dt <= 1e-5:
            return self.x_prev

        x = np.array(x, dtype=float)
        dx = (x - self.x_prev) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        cutoff = self.min_cutoff + self.beta * np.linalg.norm(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1.0 - a) * self.x_prev

        self.t_prev = t
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat


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
            self.bone_lengths['femur'] = np.median(self.samples['femur'])
            self.bone_lengths['tibia'] = np.median(self.samples['tibia'])
            self.bone_lengths['torso'] = np.median(self.samples['torso'])
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

    return angle


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
    return abs(math.degrees(math.atan2(dy, abs(dx))))


def calculate_ankling_angle(knee, ankle, heel, toe):
    """
    Calculates true dynamic ankling angle: angle between the tibia (knee->ankle)
    and the foot line (heel->toe).
    Optimal at BDC is ~90-100 deg (neutral to slight plantarflexion).
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
    """
    Knee Over Pedal Spindle (KOPS) offset at 3 o'clock power phase.
    Positive: Knee forward of spindle (anterior)
    Negative: Knee behind spindle (posterior)
    Target: 0 +/- 1.0 cm
    """
    horizontal_offset_px = knee[0] - ankle_at_3oclock[0]
    return horizontal_offset_px * pixel_to_cm_scale


# Target angle benchmarks across cycling disciplines
FIT_TARGETS = {
    "ROAD": {
        "knee_ext_max": (140, 150),   # BDC Extension
        "knee_flex_min": (68, 75),    # TDC Flexion
        "hip_closed_min": (45, 55),   # Closed Hip Angle
        "back_avg": (40, 50),         # Torso Incline
        "arm_avg": (85, 95),          # Shoulder/Arm angle
        "ankling_bdc": (90, 105),     # Ankle angle at BDC
    },
    "TRIATHLON_TT": {
        "knee_ext_max": (145, 153),   # Slightly more open for aero power
        "knee_flex_min": (65, 72),
        "hip_closed_min": (40, 48),   # Aggressive hip angle
        "back_avg": (15, 25),         # Aero horizontal torso
        "arm_avg": (80, 90),          # 90 deg aero bar support
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
