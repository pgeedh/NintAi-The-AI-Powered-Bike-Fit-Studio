"""
NintAi biomechanics — offline signal processing for dynamic bike fit.

Pipeline (video):
 1. Landmark tracks  -> gap-fill (linear, <=0.25 s) -> zero-phase Savitzky-Golay smoothing.
 2. Joint angles per frame (2D sagittal plane, side-on camera).
 3. Pedal-stroke segmentation from the knee-angle signal (peak = bottom dead centre).
    Every metric is computed *per stroke* and summarised by the median and IQR,
    which is robust to occasional tracking glitches (cf. MyVeloFit / Retul style).
 4. Crank circle fit (Kasa algebraic least squares) on the ball-of-foot path ->
    crank centre, radius in px, clock position per frame and a px->mm scale
    from the known crank length.
 5. Derived fit quantities: KOPS at 3 o'clock, hip rock, ankling range,
    cadence and a geometric (law-of-cosines) saddle-height correction.

Angle definitions (all in degrees, inner angles unless stated):
  knee      = angle(hip, knee, ankle)            180 = straight leg
  hip       = angle(shoulder, hip, knee)         smaller = more closed
  torso     = acute angle of hip->shoulder vs horizontal
  shoulder  = angle(hip, shoulder, elbow)
  elbow     = angle(shoulder, elbow, wrist)
  ankle     = angle(knee, ankle, toe)            ankling range = max-min per stroke
  foot      = signed heel->toe vs horizontal     + = toe pointing down
"""
import numpy as np

try:
    from scipy.signal import find_peaks, savgol_filter
except Exception:  # scipy optional; fall back to simpler maths
    find_peaks = savgol_filter = None

JOINTS = ['ear', 'shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle', 'heel', 'toe']

# Winter (2009) anthropometrics: thigh 0.245 H, shank 0.246 H.
THIGH_SHANK_FRACTION_OF_HEIGHT = 0.491
BALL_OF_FOOT = 0.72   # fraction along heel->toe where the pedal spindle sits


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #
def angle3(a, b, c):
    """Inner angle ABC in degrees. Vectorised over leading dims (…,2)."""
    a, b, c = np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)
    v1, v2 = a - b, c - b
    dot = np.sum(v1 * v2, axis=-1)
    n = np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1)
    with np.errstate(invalid='ignore', divide='ignore'):
        cos = np.clip(dot / n, -1.0, 1.0)
    return np.degrees(np.arccos(cos))


def acute_to_horizontal(a, b):
    v = np.asarray(b, float) - np.asarray(a, float)
    ang = np.degrees(np.arctan2(np.abs(v[..., 1]), np.abs(v[..., 0])))
    return ang


def fit_circle(pts):
    """Kasa least-squares circle fit. Returns (cx, cy, r, rms_residual) or None."""
    pts = np.asarray(pts, float)
    pts = pts[np.all(np.isfinite(pts), axis=1)]
    if len(pts) < 8:
        return None
    x, y = pts[:, 0], pts[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    b = x ** 2 + y ** 2
    try:
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    cx, cy = sol[0] / 2, sol[1] / 2
    r = np.sqrt(max(sol[2] + cx ** 2 + cy ** 2, 0))
    res = np.sqrt(np.mean((np.hypot(x - cx, y - cy) - r) ** 2))
    return float(cx), float(cy), float(r), float(res)


def knee_for_reach(L1, L2, d):
    """Knee angle (deg) for hip-ankle distance d given thigh L1 and shank L2."""
    cos = (L1 ** 2 + L2 ** 2 - d ** 2) / (2 * L1 * L2)
    return float(np.degrees(np.arccos(np.clip(cos, -1, 1))))


def reach_for_knee(L1, L2, theta_deg):
    """Hip-ankle distance for a knee angle (law of cosines)."""
    return float(np.sqrt(L1 ** 2 + L2 ** 2 - 2 * L1 * L2 * np.cos(np.radians(theta_deg))))


# --------------------------------------------------------------------------- #
# Signal processing
# --------------------------------------------------------------------------- #
def _fill_gaps(arr, max_gap):
    """Linear interpolation over NaN runs up to max_gap samples. arr: (N,) or (N,2)."""
    arr = np.array(arr, float)
    one_d = arr.ndim == 1
    if one_d:
        arr = arr[:, None]
    n = len(arr)
    idx = np.arange(n)
    for d in range(arr.shape[1]):
        col = arr[:, d]
        good = np.isfinite(col)
        if good.sum() < 2:
            continue
        filled = np.interp(idx, idx[good], col[good])
        # only accept fills inside short gaps
        bad = ~good
        run_start = None
        for i in range(n + 1):
            if i < n and bad[i]:
                if run_start is None:
                    run_start = i
            elif run_start is not None:
                L = i - run_start
                inner = run_start > 0 and i < n
                if L <= max_gap and inner:
                    col[run_start:i] = filled[run_start:i]
                run_start = None
        arr[:, d] = col
    return arr[:, 0] if one_d else arr


def smooth(arr, fps, window_s=0.2, poly=2):
    """Zero-phase Savitzky-Golay smoothing over finite stretches."""
    arr = np.array(arr, float)
    win = int(round(window_s * fps)) | 1
    if savgol_filter is None or win < poly + 2:
        return arr
    out = arr.copy()
    finite = np.all(np.isfinite(arr), axis=-1) if arr.ndim > 1 else np.isfinite(arr)
    # process contiguous finite segments
    i, n = 0, len(arr)
    while i < n:
        if not finite[i]:
            i += 1
            continue
        j = i
        while j < n and finite[j]:
            j += 1
        seg = arr[i:j]
        if len(seg) >= win:
            out[i:j] = savgol_filter(seg, win, poly, axis=0)
        i = j
    return out


def _peaks(sig, fps, prominence):
    """Indices of local maxima at least 0.33 s apart (<=180 rpm)."""
    sig = np.nan_to_num(sig, nan=np.nanmedian(sig) if np.isfinite(sig).any() else 0)
    dist = max(1, int(0.33 * fps))
    if find_peaks is not None:
        p, _ = find_peaks(sig, distance=dist, prominence=prominence)
        return p
    # simple fallback
    p = [i for i in range(1, len(sig) - 1) if sig[i] >= sig[i - 1] and sig[i] > sig[i + 1]]
    keep = []
    for i in p:
        if not keep or i - keep[-1] >= dist:
            keep.append(i)
    return np.array(keep, int)


def _summ(vals):
    vals = np.asarray([v for v in vals if np.isfinite(v)], float)
    if len(vals) == 0:
        return None
    q1, q3 = np.percentile(vals, [25, 75])
    return {'median': float(np.median(vals)), 'iqr': float(q3 - q1),
            'min': float(vals.min()), 'max': float(vals.max()), 'n': int(len(vals))}


# --------------------------------------------------------------------------- #
# Main analysis
# --------------------------------------------------------------------------- #
def build_tracks(frames, side, conf_thr=0.5):
    """frames: list of {name: (x,y,c)}. Returns {joint: (N,2) array with NaNs}."""
    n = len(frames)
    tracks = {}
    for j in JOINTS:
        arr = np.full((n, 2), np.nan)
        key = f"{side}_{j}"
        for i, f in enumerate(frames):
            v = f.get(key)
            if v is not None and v[2] >= conf_thr:
                arr[i] = v[:2]
        tracks[j] = arr
    # derived: ball of foot (pedal spindle proxy)
    tracks['ball'] = tracks['heel'] + BALL_OF_FOOT * (tracks['toe'] - tracks['heel'])
    return tracks


def angle_series(t):
    s = {
        'knee': angle3(t['hip'], t['knee'], t['ankle']),
        'hip': angle3(t['shoulder'], t['hip'], t['knee']),
        'torso': acute_to_horizontal(t['hip'], t['shoulder']),
        'shoulder': angle3(t['hip'], t['shoulder'], t['elbow']),
        'elbow': angle3(t['shoulder'], t['elbow'], t['wrist']),
        'ankle': angle3(t['knee'], t['ankle'], t['toe']),
        'neck': angle3(t['hip'], t['shoulder'], t['ear']),
    }
    v = t['toe'] - t['heel']
    s['foot'] = np.degrees(np.arctan2(v[:, 1], np.abs(v[:, 0])))  # + = toe down (image y down)
    return s


def analyze_sequence(frames, times, side, facing_right, crank_mm=172.5, rider_height_cm=None):
    """
    frames: list of raw per-frame landmark dicts; times: seconds.
    Returns dict with smoothed tracks, angle series, per-stroke stats and derived metrics.
    """
    times = np.asarray(times, float)
    n = len(frames)
    fps = (n - 1) / (times[-1] - times[0]) if n > 1 and times[-1] > times[0] else 30.0

    raw = build_tracks(frames, side)
    tracks = {}
    for j, arr in raw.items():
        filled = _fill_gaps(arr, max_gap=int(0.25 * fps))
        tracks[j] = smooth(filled, fps, window_s=0.15)
    ang = angle_series(tracks)
    ang = {k: smooth(v, fps, window_s=0.15) for k, v in ang.items()}

    knee = ang['knee']
    finite_knee = knee[np.isfinite(knee)]
    out = {'fps': fps, 'tracks': tracks, 'angles': ang, 'times': times,
           'cycles': [], 'per_stroke': {}, 'derived': {}, 'method': 'percentile'}
    if len(finite_knee) < 5:
        return out

    k_range = np.percentile(finite_knee, 98) - np.percentile(finite_knee, 2)
    peaks = _peaks(knee, fps, prominence=max(8.0, 0.35 * k_range))
    cycles = [(int(a), int(b)) for a, b in zip(peaks[:-1], peaks[1:])
              if 0.33 <= times[b] - times[a] <= 2.5]
    out['cycles'] = cycles
    out['bdc_idx'] = [int(p) for p in peaks]

    per = {k: [] for k in ('knee_ext', 'knee_flex', 'hip_closed', 'hip_open', 'ankle_range',
                           'torso', 'shoulder', 'elbow', 'tdc_idx')}
    for a, b in cycles:
        seg = slice(a, b + 1)
        kseg = knee[seg]
        if not np.isfinite(kseg).any():
            continue
        per['knee_ext'].append(knee[a])
        per['knee_flex'].append(np.nanmin(kseg))
        per['tdc_idx'].append(a + int(np.nanargmin(kseg)))
        per['hip_closed'].append(np.nanmin(ang['hip'][seg]))
        per['hip_open'].append(np.nanmax(ang['hip'][seg]))
        per['ankle_range'].append(np.nanmax(ang['ankle'][seg]) - np.nanmin(ang['ankle'][seg]))
        per['torso'].append(np.nanmedian(ang['torso'][seg]))
        per['shoulder'].append(np.nanmedian(ang['shoulder'][seg]))
        per['elbow'].append(np.nanmedian(ang['elbow'][seg]))

    if len(per['knee_ext']) >= 2:
        out['method'] = 'per-stroke'
        out['per_stroke'] = {k: _summ(v) for k, v in per.items() if k != 'tdc_idx'}
        out['tdc_idx'] = per['tdc_idx']
        periods = [times[b] - times[a] for a, b in cycles]
        out['derived']['cadence_rpm'] = float(60.0 / np.median(periods))
    else:
        # Fallback: robust percentiles across the whole clip
        def pct(sig, q):
            s = sig[np.isfinite(sig)]
            return float(np.percentile(s, q)) if len(s) else None
        out['per_stroke'] = {
            'knee_ext': {'median': pct(knee, 97), 'iqr': None, 'n': 0},
            'knee_flex': {'median': pct(knee, 3), 'iqr': None, 'n': 0},
            'hip_closed': {'median': pct(ang['hip'], 3), 'iqr': None, 'n': 0},
            'ankle_range': {'median': (pct(ang['ankle'], 95) or 0) - (pct(ang['ankle'], 5) or 0), 'iqr': None, 'n': 0},
            'torso': {'median': pct(ang['torso'], 50), 'iqr': None, 'n': 0},
            'shoulder': {'median': pct(ang['shoulder'], 50), 'iqr': None, 'n': 0},
            'elbow': {'median': pct(ang['elbow'], 50), 'iqr': None, 'n': 0},
        }
        out['bdc_idx'] = [int(np.nanargmax(knee))]
        out['tdc_idx'] = [int(np.nanargmin(knee))]

    # ---------------- Scale & crank geometry ---------------- #
    L1 = np.nanmedian(np.linalg.norm(tracks['hip'] - tracks['knee'], axis=1))
    L2 = np.nanmedian(np.linalg.norm(tracks['knee'] - tracks['ankle'], axis=1))
    d = out['derived']
    d['thigh_px'], d['shank_px'] = float(L1), float(L2)

    circ = fit_circle(tracks['ball'])
    mm_per_px = None
    scale_source = None
    if circ:
        cx, cy, r, res = circ
        plausible = 0.25 * L2 < r < 0.65 * L2 and res < 0.2 * r
        d['crank_fit'] = {'cx': cx, 'cy': cy, 'r_px': r, 'rms_px': res, 'ok': bool(plausible)}
        if plausible:
            mm_per_px = crank_mm / r
            scale_source = f'crank circle ({crank_mm:g} mm)'
    if mm_per_px is None and rider_height_cm:
        mm_per_px = (rider_height_cm * 10 * THIGH_SHANK_FRACTION_OF_HEIGHT) / (L1 + L2)
        scale_source = f'rider height ({rider_height_cm:g} cm)'
    d['mm_per_px'] = mm_per_px
    d['scale_source'] = scale_source

    # Clock angle & KOPS (knee vs pedal spindle at 3 o'clock)
    if circ and d['crank_fit']['ok']:
        cx, cy = circ[0], circ[1]
        bx, by = tracks['ball'][:, 0] - cx, tracks['ball'][:, 1] - cy
        fwd = 1.0 if facing_right else -1.0
        clock = np.degrees(np.arctan2(-by, bx * fwd))  # 0 = forward (3 o'clock), 90 = up
        d['clock_deg'] = clock
        at3 = np.where(np.abs(clock) < 12)[0]
        if len(at3) >= 2:
            offs = (tracks['knee'][at3, 0] - tracks['ball'][at3, 0]) * fwd
            offs = offs[np.isfinite(offs)]
            if len(offs):
                d['kops_px'] = float(np.median(offs))
                if mm_per_px:
                    d['kops_mm'] = d['kops_px'] * mm_per_px

    # Hip rock: vertical hip excursion within strokes
    if cycles:
        rocks = []
        for a, b in cycles:
            hy = tracks['hip'][a:b + 1, 1]
            if np.isfinite(hy).sum() > 3:
                rocks.append(np.nanmax(hy) - np.nanmin(hy))
        if rocks:
            d['hip_rock_px'] = float(np.median(rocks))
            if mm_per_px:
                d['hip_rock_mm'] = d['hip_rock_px'] * mm_per_px

    return out


def saddle_change_mm(knee_now, knee_target, thigh_px, shank_px, mm_per_px):
    """Geometric saddle height change (mm, + = raise) to move BDC knee angle to target."""
    if not (knee_now and thigh_px and shank_px and mm_per_px):
        return None
    d_now = reach_for_knee(thigh_px, shank_px, knee_now)
    d_tgt = reach_for_knee(thigh_px, shank_px, knee_target)
    return (d_tgt - d_now) * mm_per_px
