import os

from dotenv import load_dotenv

load_dotenv()

SIGNATURE = "Created with love for the passion of Triathlon by Pruthvi"
DEFAULT_MODEL = os.getenv("NINTAI_GEMINI_MODEL", "gemini-2.5-flash")


def _fmt(v):
    try:
        return f"{float(v):.1f}" if v and float(v) > 0 else "N/A"
    except (TypeError, ValueError):
        return "N/A"


def build_prompt(metrics, recommendations, profile_name="Road", rider_notes=""):
    rec_lines = "\n".join(f"- {r['title']}: {r['detail']}" for r in recommendations) or "- None"
    return f"""
You are an expert professional bike fitter and biomechanist (like those at MyVeloFit or Retul).

Riding style: {profile_name}
Rider notes (pain, goals, history): {rider_notes or 'none given'}

**Observed dynamic angles (2D, side view):**
- Knee extension at bottom of stroke: {_fmt(metrics.get('knee_ext'))} deg
- Knee angle at top of stroke: {_fmt(metrics.get('knee_flex'))} deg
- Most closed hip angle: {_fmt(metrics.get('hip_closed'))} deg
- Torso angle vs horizontal: {_fmt(metrics.get('torso'))} deg
- Shoulder angle (upper arm vs torso): {_fmt(metrics.get('shoulder'))} deg
- Elbow angle: {_fmt(metrics.get('elbow'))} deg

**Rule-based suggestions already shown to the rider:**
{rec_lines}

**Your task:**
1. In 2-3 sentences, summarise the overall position for this riding style.
2. Explain the 1-3 most important changes, in order, and *why* (power, aero, comfort, injury).
3. Tie advice to the rider notes if any (e.g. knee pain -> saddle height / cleats).
4. Remind them to change one thing at a time in small steps and re-test.
Use short paragraphs and plain language. Max 250 words. No markdown tables.
""".strip()


def offline_summary(metrics, recommendations, profile_name="Road"):
    """Readable coach notes without any API key."""
    lines = [f"Position summary for {profile_name}."]
    if not recommendations:
        lines.append("All measured angles are within the typical range for this riding style. "
                     "If you're comfortable and pain-free, leave it alone — great fit!")
    else:
        lines.append("Here is what to work on, in order of importance:")
        for i, r in enumerate(recommendations, 1):
            lines.append(f"{i}. {r['title']}. {r['detail']}")
    lines.append("Golden rule: change one thing at a time, in small steps, ride for a few days, "
                 "then re-test. Comfort and pain-free riding always beat textbook numbers.")
    return "\n\n".join(lines)


def generate_ai_analysis(angles, recommendations, api_key=None, profile_name="Road",
                         rider_notes="", model=None):
    """
    Returns (text, source) where source is 'gemini' or 'offline'.

    Backwards compatible: `angles` may be the old stats dict (knee_ext_max, ...)
    or the new metrics dict (knee_ext, ...). `recommendations` may be a list of
    strings (legacy) or dicts from fit_profiles.build_recommendations.
    """
    metrics = dict(angles or {})
    legacy = {'knee_ext_max': 'knee_ext', 'knee_flex_min': 'knee_flex', 'hip_closed_min': 'hip_closed',
              'back_avg': 'torso', 'arm_avg': 'shoulder'}
    for old, new in legacy.items():
        if old in metrics and new not in metrics:
            metrics[new] = metrics[old]
    recs = [r if isinstance(r, dict) else {'title': str(r), 'detail': ''} for r in (recommendations or [])]

    key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        return offline_summary(metrics, recs, profile_name), 'offline'

    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=model or DEFAULT_MODEL,
            contents=build_prompt(metrics, recs, profile_name, rider_notes),
        )
        text = (resp.text or "").strip()
        if not text:
            raise RuntimeError("Empty response")
        return f"{text}\n\n{SIGNATURE}", 'gemini'
    except Exception as e:  # network, quota, bad key...
        msg = str(e).split('\n')[0][:200]
        return (offline_summary(metrics, recs, profile_name)
                + f"\n\n(AI coach unavailable: {msg}. Showing built-in guidance instead.)"), 'offline'
