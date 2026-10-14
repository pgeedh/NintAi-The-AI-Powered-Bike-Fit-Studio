import numpy as np
import cv2
import math

class OneEuroFilter:
    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.t_prev = t0
        self.x_prev = np.array(x0, dtype=float)
        self.dx_prev = np.zeros_like(x0, dtype=float)
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.alpha = self._alpha(min_cutoff)

    def _alpha(self, cutoff):
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau * 30.0)

    def __call__(self, t, x):
        t_e = t - self.t_prev
        a_d = self._alpha(self.d_cutoff)
        dx = (x - self.x_prev) / t_e if t_e > 0 else np.zeros_like(x)
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        a = self._alpha(cutoff)
        x_hat = a * x + (1 - a) * self.x_prev
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle

def calculate_angle_horizontal(a, b):
    """Acute angle (0-90 deg) between segment a->b and the horizontal.

    Folding into 0-90 makes the metric independent of which way the rider faces
    (a left-facing rider would otherwise report ~140 deg instead of ~40 deg).
    """
    v = np.array(b, dtype=float) - np.array(a, dtype=float)
    ang = np.abs(np.degrees(np.arctan2(v[1], v[0])))
    return float(min(ang, 180.0 - ang))


class LazyOneEuroFilter:
    """OneEuroFilter that initialises on the first sample instead of (0, 0).

    The original filter started from the origin, which dragged the first
    ~second of landmarks towards the top-left corner of the frame.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.f = None

    def __call__(self, t, x):
        x = np.asarray(x, dtype=float)
        if self.f is None:
            self.f = OneEuroFilter(t0=t, x0=x, **self.kwargs)
            return x
        return self.f(t, x)

def draw_angle_arc(image, p1, p2, p3, angle, color=(0, 255, 255), radius=30):
    if p1 == (0,0) or p2 == (0,0) or p3 == (0,0): return
    v1 = np.array(p1) - np.array(p2)
    v2 = np.array(p3) - np.array(p2)
    ang1 = np.degrees(np.arctan2(v1[1], v1[0]))
    ang2 = np.degrees(np.arctan2(v2[1], v2[0]))
    if ang1 < 0: ang1 += 360
    if ang2 < 0: ang2 += 360
    diff = ang2 - ang1
    if diff < 0: diff += 360
    if diff > 180:
        start, end = ang2, ang1
    else:
        start, end = ang1, ang2
    cv2.ellipse(image, p2, (radius, radius), 0, start, end, color, 2, cv2.LINE_AA)
    text_x = int(p2[0] + radius * 1.5 * np.cos(np.radians((start+end)/2)))
    text_y = int(p2[1] + radius * 1.5 * np.sin(np.radians((start+end)/2)))
    cv2.putText(image, f"{int(angle)}", (text_x-10, text_y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

def detect_side(lm_dict):
    nose = lm_dict.get('nose')
    l_ear = lm_dict.get('left_ear')
    r_ear = lm_dict.get('right_ear')
    
    if nose is not None and l_ear is not None:
        if nose[0] < l_ear[0]: return 'left'
        else: return 'right'
    if nose is not None and r_ear is not None:
        if nose[0] < r_ear[0]: return 'left'
        else: return 'right'
        
    l_hip = lm_dict.get('left_hip')
    l_knee = lm_dict.get('left_knee')
    if l_hip is not None and l_knee is not None:
        if l_knee[0] < l_hip[0]: return 'left'
        else: return 'right'
        
    return 'left'

def get_primary_landmarks(lm_dict, facing_side):
    left_keys = ['left_shoulder', 'left_hip', 'left_knee', 'left_ankle', 'left_heel', 'left_toe']
    right_keys = ['right_shoulder', 'right_hip', 'right_knee', 'right_ankle', 'right_heel', 'right_toe']
    
    l_count = sum(1 for k in left_keys if k in lm_dict)
    r_count = sum(1 for k in right_keys if k in lm_dict)
    
    # A rider facing image-left shows their LEFT side to the camera (and vice
    # versa), so prefer the facing side whenever enough of it is visible.
    if facing_side == 'left' and l_count >= 4:
        prefix = 'left_'
    elif facing_side == 'right' and r_count >= 4:
        prefix = 'right_'
    else:
        prefix = 'left_' if l_count >= r_count else 'right_'
    
    unified = {}
    for k, v in lm_dict.items():
        if k.startswith(prefix):
            unified[k.replace(prefix, '')] = v
        unified[k] = v 
    unified['side'] = prefix.replace('_', '')
    return unified

def analyze_posture(lm):
    angles = {}
    def valid(pt): return pt is not None and not (pt[0] == 0 and pt[1] == 0)

    if valid(lm.get('hip')) and valid(lm.get('knee')) and valid(lm.get('ankle')):
        angles['knee'] = calculate_angle(lm['hip'], lm['knee'], lm['ankle'])
    else: angles['knee'] = 0

    if valid(lm.get('shoulder')) and valid(lm.get('hip')) and valid(lm.get('knee')):
        angles['hip'] = calculate_angle(lm['shoulder'], lm['hip'], lm['knee'])
    else: angles['hip'] = 0
    
    if valid(lm.get('shoulder')) and valid(lm.get('hip')):
        angles['back'] = calculate_angle_horizontal(lm['hip'], lm['shoulder'])
    else: angles['back'] = 0
    
    if valid(lm.get('elbow')) and valid(lm.get('shoulder')) and valid(lm.get('hip')):
        angles['arm_torso'] = calculate_angle(lm['elbow'], lm['shoulder'], lm['hip'])
    else: angles['arm_torso'] = 0

    if valid(lm.get('shoulder')) and valid(lm.get('elbow')) and valid(lm.get('wrist')):
        angles['elbow'] = calculate_angle(lm['shoulder'], lm['elbow'], lm['wrist'])
    else: angles['elbow'] = 0
    
    ear_pt = None
    if 'ear' in lm: ear_pt = lm['ear']
    elif 'side' in lm:
        ear_pt = lm.get(f"{lm['side']}_ear")
        
    if valid(ear_pt) and valid(lm.get('shoulder')) and valid(lm.get('hip')):
        angles['neck'] = calculate_angle(lm['hip'], lm['shoulder'], ear_pt)
    else: angles['neck'] = 0
    
    if valid(lm.get('elbow')) and valid(lm.get('wrist')):
        angles['wrist_tilt'] = calculate_angle_horizontal(lm['elbow'], lm['wrist'])
    else: angles['wrist_tilt'] = 0
    
    # Real Foot Angle (Heel-Toe vs Horizontal)
    # 0 deg = flat. + deg = toe up?
    if valid(lm.get('heel')) and valid(lm.get('toe')):
        angles['foot_angle'] = calculate_angle_horizontal(lm['heel'], lm['toe'])
    else: angles['foot_angle'] = 0

    return angles

def get_feedback(knee_angle, arm_avg):
    feedback_lines = []
    if knee_angle > 0:
        if knee_angle < 140: feedback_lines.append(f"Knee Extension low ({knee_angle:.0f}°). Raise Saddle.")
        elif knee_angle > 150: feedback_lines.append(f"Knee Extension high ({knee_angle:.0f}°). Lower Saddle.")
    return feedback_lines, {}, {}
