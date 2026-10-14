"""
Riding-style reference ranges and plain-language fit recommendations.

Ranges are commonly cited dynamic bike-fit guidelines (side-view, 2D). They are
starting points, not medical advice — comfort and injury history always win.
"""

# Degrees of knee angle change per mm of saddle height is roughly 0.35-0.45
# for most riders, i.e. ~2.5 mm of saddle per degree of knee extension.
MM_PER_KNEE_DEGREE = 2.5
MAX_SINGLE_SADDLE_CHANGE_MM = 15

METRICS = {
    "knee_ext": {
        "label": "Knee extension (bottom of stroke)",
        "short": "Knee @ bottom",
        "explain": "How straight your leg gets at the bottom of the pedal stroke. "
                   "Mostly controlled by saddle height.",
    },
    "knee_flex": {
        "label": "Knee bend (top of stroke)",
        "short": "Knee @ top",
        "explain": "How bent your knee is at the top of the stroke. Too small = knee "
                   "is cramped (saddle low/forward or cranks too long).",
    },
    "hip_closed": {
        "label": "Hip angle (most closed)",
        "short": "Hip closed",
        "explain": "Angle between torso and thigh at the top of the stroke. Too closed "
                   "chokes breathing and power; too open is less aero.",
    },
    "torso": {
        "label": "Torso angle (vs. horizontal)",
        "short": "Torso",
        "explain": "How low your back is. Lower = more aero, higher = more comfortable. "
                   "Mostly controlled by handlebar height and reach.",
    },
    "shoulder": {
        "label": "Shoulder angle (arm vs. torso)",
        "short": "Shoulder",
        "explain": "Angle between upper arm and torso. Tells you if the bars are too "
                   "close (small) or too far (large).",
    },
    "elbow": {
        "label": "Elbow bend",
        "short": "Elbow",
        "explain": "A slight bend absorbs road buzz. Locked-out elbows usually mean "
                   "the reach is too long.",
    },
}

PROFILES = {
    "road_endurance": {
        "name": "Road — endurance / comfort",
        "emoji": "🚲",
        "blurb": "Sportives, long rides, commuting. Comfort first.",
        "ranges": {
            "knee_ext": (140, 150),
            "knee_flex": (65, 80),
            "hip_closed": (50, 65),
            "torso": (45, 55),
            "shoulder": (80, 95),
            "elbow": (150, 165),
        },
    },
    "road_race": {
        "name": "Road — race / aggressive",
        "emoji": "🏁",
        "blurb": "Racing, crits, fast group rides. Lower and longer.",
        "ranges": {
            "knee_ext": (140, 150),
            "knee_flex": (65, 80),
            "hip_closed": (45, 55),
            "torso": (35, 45),
            "shoulder": (85, 100),
            "elbow": (150, 165),
        },
    },
    "tri_tt": {
        "name": "Triathlon / Time trial",
        "emoji": "⏱️",
        "blurb": "Aero bars, long steady efforts. Aero but sustainable.",
        "ranges": {
            "knee_ext": (140, 150),
            "knee_flex": (65, 80),
            "hip_closed": (40, 55),
            "torso": (10, 28),
            "shoulder": (80, 100),
            "elbow": (85, 115),
        },
    },
    "mtb_gravel": {
        "name": "MTB / Gravel",
        "emoji": "⛰️",
        "blurb": "Off-road control, more upright, wider bars.",
        "ranges": {
            "knee_ext": (138, 148),
            "knee_flex": (65, 80),
            "hip_closed": (55, 70),
            "torso": (45, 60),
            "shoulder": (75, 90),
            "elbow": (140, 160),
        },
    },
}

DEFAULT_PROFILE = "road_endurance"


def status_for(value, rng, tolerance=3.0):
    """Return 'ok', 'watch' (just outside) or 'fix' (clearly outside)."""
    if value is None or value <= 0:
        return "na"
    lo, hi = rng
    if lo <= value <= hi:
        return "ok"
    dist = lo - value if value < lo else value - hi
    return "watch" if dist <= tolerance else "fix"


def _mid(rng):
    return (rng[0] + rng[1]) / 2.0


def build_recommendations(metrics, profile_key, extra=None):
    """
    metrics: dict with keys from METRICS (degrees). Missing / 0 values are skipped.
    extra:   optional dict e.g. {'torso_range': deg, 'mode': 'video'|'image'}
    Returns an ordered list of dicts: {priority, title, detail, metric}
      priority 1 = do this first (saddle height), 3 = nice to have.
    """
    extra = extra or {}
    ranges = PROFILES[profile_key]["ranges"]
    recs = []

    def get(k):
        v = metrics.get(k)
        return v if v is not None and v > 0 else None

    # 1. Saddle height — always the first thing to get right.
    ke = get("knee_ext")
    if ke is not None:
        lo, hi = ranges["knee_ext"]
        if ke < lo:
            mm = min((_mid(ranges["knee_ext"]) - ke) * MM_PER_KNEE_DEGREE, MAX_SINGLE_SADDLE_CHANGE_MM)
            recs.append({
                "priority": 1, "metric": "knee_ext",
                "title": f"Raise your saddle ~{mm:.0f} mm",
                "detail": f"Your knee only opens to {ke:.0f}° at the bottom (target {lo}–{hi}°). "
                          "A low saddle overloads the front of the knee and wastes power. "
                          "Raise it in 3–5 mm steps and re-test.",
            })
        elif ke > hi:
            mm = min((ke - _mid(ranges["knee_ext"])) * MM_PER_KNEE_DEGREE, MAX_SINGLE_SADDLE_CHANGE_MM)
            recs.append({
                "priority": 1, "metric": "knee_ext",
                "title": f"Lower your saddle ~{mm:.0f} mm",
                "detail": f"Your knee opens to {ke:.0f}° at the bottom (target {lo}–{hi}°). "
                          "Over-extension often causes hip rocking and pain behind the knee. "
                          "Lower it in 3–5 mm steps and re-test.",
            })

    # 2. Knee at top of stroke (only meaningful once saddle height is sane).
    kf = get("knee_flex")
    if kf is not None and (ke is None or ranges["knee_ext"][0] - 3 <= ke <= ranges["knee_ext"][1] + 3):
        lo, hi = ranges["knee_flex"]
        if kf < lo - 3:
            recs.append({
                "priority": 2, "metric": "knee_flex",
                "title": "Knee is cramped at the top of the stroke",
                "detail": f"Knee closes to {kf:.0f}° (target {lo}–{hi}°). Consider sliding the saddle "
                          "back a few mm or trying shorter cranks (e.g. 165–170 mm).",
            })

    # 3. Hip angle.
    hc = get("hip_closed")
    if hc is not None:
        lo, hi = ranges["hip_closed"]
        if hc < lo - 2:
            recs.append({
                "priority": 2, "metric": "hip_closed",
                "title": "Open up your hip angle",
                "detail": f"Your hip closes to {hc:.0f}° (target {lo}–{hi}°). Try raising the bars "
                          "(spacers / stem flip), shorter cranks, or — on a tri bike — moving the "
                          "saddle slightly forward.",
            })
        elif hc > hi + 5:
            recs.append({
                "priority": 3, "metric": "hip_closed",
                "title": "You have room to get lower",
                "detail": f"Hip angle of {hc:.0f}° is more open than needed for this style "
                          f"(target {lo}–{hi}°). If you want more speed, drop the bars gradually.",
            })

    # 4. Torso / bar height.
    to = get("torso")
    if to is not None:
        lo, hi = ranges["torso"]
        if to > hi + 3:
            recs.append({
                "priority": 3, "metric": "torso",
                "title": "Position is more upright than typical for this style",
                "detail": f"Torso at {to:.0f}° (typical {lo}–{hi}°). Fine if comfort is the goal — "
                          "otherwise lower the bars 5–10 mm at a time.",
            })
        elif to < lo - 3:
            recs.append({
                "priority": 2, "metric": "torso",
                "title": "Position is very low — check it's sustainable",
                "detail": f"Torso at {to:.0f}° (typical {lo}–{hi}°). If you feel neck/back strain or "
                          "can't hold it for long, raise the bars slightly.",
            })

    # 5. Reach (shoulder angle).
    sh = get("shoulder")
    if sh is not None:
        lo, hi = ranges["shoulder"]
        if sh < lo - 3:
            recs.append({
                "priority": 2, "metric": "shoulder",
                "title": "Reach looks short",
                "detail": f"Shoulder angle {sh:.0f}° (target {lo}–{hi}°). You may feel cramped. "
                          "A 10 mm longer stem (or extending aerobar pads forward) is a common fix.",
            })
        elif sh > hi + 3:
            recs.append({
                "priority": 2, "metric": "shoulder",
                "title": "Reach looks long",
                "detail": f"Shoulder angle {sh:.0f}° (target {lo}–{hi}°). Stretching for the bars loads "
                          "the neck and shoulders. Try a 10 mm shorter stem or move pads back.",
            })

    # 6. Elbows.
    el = get("elbow")
    if el is not None:
        lo, hi = ranges["elbow"]
        if el > hi + 5:
            recs.append({
                "priority": 3, "metric": "elbow",
                "title": "Soften your elbows",
                "detail": f"Elbows are nearly locked ({el:.0f}°). Keep a slight bend to absorb bumps; "
                          "if you can't, reach is probably too long.",
            })

    # 7. Stability (video only).
    tr = extra.get("torso_range")
    if tr is not None and tr > 10:
        recs.append({
            "priority": 2, "metric": "torso",
            "title": "Upper body is moving a lot",
            "detail": f"Your torso angle varies by {tr:.0f}° while pedalling. Rocking usually means the "
                      "saddle is too high, or you're filming during a very hard effort.",
        })

    recs.sort(key=lambda r: r["priority"])
    return recs


def fit_score(metrics, profile_key):
    """0-100 score: share of metrics in range, with partial credit for 'watch'."""
    ranges = PROFILES[profile_key]["ranges"]
    weights = {"knee_ext": 3, "knee_flex": 1, "hip_closed": 2, "torso": 1, "shoulder": 1.5, "elbow": 0.5}
    total = got = 0.0
    for k, w in weights.items():
        s = status_for(metrics.get(k), ranges[k])
        if s == "na":
            continue
        total += w
        got += w * {"ok": 1.0, "watch": 0.6, "fix": 0.15}[s]
    if total == 0:
        return None
    return int(round(100 * got / total))
