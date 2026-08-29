"""
NintAi Biomechanical Consultation Engine.
Supports Anthropic Claude, Google Gemini, and 100% Offline Rule-Based Diagnostic Engine.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def generate_rule_based_breakdown(angles: dict, targets: dict) -> str:
    """
    Generates a deterministic clinical bike fit breakdown without requiring external AI APIs.
    Modeled after MyVeloFit and Bike Fast Fit diagnostic protocols.
    """
    knee_ext = angles.get('knee_ext_max', 145.0)
    knee_flex = angles.get('knee_flex_min', 71.0)
    hip_closed = angles.get('hip_closed_min', 49.0)
    back_angle = angles.get('back_avg', 43.5)
    arm_angle = angles.get('arm_avg', 88.0)
    ankling = angles.get('ankling_avg', angles.get('foot_angle_avg', 96.0))

    # Knee Extension Evaluation (Holmes Method: 25-35 deg flexion = 145-155 deg extension)
    target_k_low, target_k_high = targets.get('knee_ext_max', (140, 150))
    saddle_recs = []
    fit_score = 100

    if knee_ext < target_k_low:
        diff_deg = target_k_low - knee_ext
        mm_adj = int(diff_deg * 2.8)
        saddle_recs.append(f"**Raise Saddle Height:** +{mm_adj} mm (Knee extension is {knee_ext:.1f}°, below target {target_k_low}°–{target_k_high}°).")
        fit_score -= int(diff_deg * 4)
    elif knee_ext > target_k_high:
        diff_deg = knee_ext - target_k_high
        mm_adj = int(diff_deg * 2.8)
        saddle_recs.append(f"**Lower Saddle Height:** -{mm_adj} mm (Knee extension is {knee_ext:.1f}°, above target {target_k_low}°–{target_k_high}°).")
        fit_score -= int(diff_deg * 4)
    else:
        saddle_recs.append(f"**Saddle Height:** Optimal ({knee_ext:.1f}° within target {target_k_low}°–{target_k_high}°).")

    # Hip / Cockpit Evaluation
    target_h_low, target_h_high = targets.get('hip_closed_min', (45, 55))
    cockpit_recs = []
    if hip_closed < target_h_low:
        cockpit_recs.append(f"**Increase Cockpit Stack / Shorten Reach:** +5 to 10 mm spacers (Closed hip angle {hip_closed:.1f}° is tight, creating potential breathing compression).")
        fit_score -= 10
    else:
        cockpit_recs.append(f"**Hip Angle:** Optimal ({hip_closed:.1f}° clearance at TDC 12h).")

    # Ankling Evaluation
    target_a_low, target_a_high = targets.get('ankling_bdc', (90, 105))
    ankle_recs = []
    if ankling > target_a_high:
        ankle_recs.append(f"**Plantarflexion Warning:** Ankle angle is {ankling:.1f}° at BDC (toe-pointing observed; rider may be reaching for the pedals).")
        fit_score -= 8
    else:
        ankle_recs.append(f"**Dynamic Ankling:** Neutral ({ankling:.1f}° at BDC 6h).")

    fit_score = max(min(fit_score, 100), 40)

    report_md = f"""### Clinical Biomechanical Evaluation Report

**Overall Fit Alignment Score:** `{fit_score}% / 100%`

---

#### 1. Primary Kinematic Envelopes
- **Knee Extension at BDC (6 o'clock):** `{knee_ext:.1f}°` *(Reference: {target_k_low}°–{target_k_high}°)*
- **Knee Flexion at TDC (12 o'clock):** `{knee_flex:.1f}°` *(Reference: {targets.get('knee_flex_min', (68,75))[0]}°–{targets.get('knee_flex_min', (68,75))[1]}°)*
- **Closed Hip Angle at TDC:** `{hip_closed:.1f}°` *(Reference: {target_h_low}°–{target_h_high}°)*
- **Torso Incline to Horizontal:** `{back_angle:.1f}°` *(Reference: {targets.get('back_avg', (40,50))[0]}°–{targets.get('back_avg', (40,50))[1]}°)*
- **Shoulder / Cockpit Angle:** `{arm_angle:.1f}°` *(Reference: {targets.get('arm_avg', (85,95))[0]}°–{targets.get('arm_avg', (85,95))[1]}°)*
- **Dynamic Ankling at BDC:** `{ankling:.1f}°` *(Reference: {target_a_low}°–{target_a_high}°)*

---

#### 2. Prioritized Action Plan (Step-by-Step)
1. **Primary Saddle Adjustment:**
   - {saddle_recs[0]}
2. **Cockpit & Reach Geometry:**
   - {cockpit_recs[0]}
3. **Foot & Cleat Interface:**
   - {ankle_recs[0]}

---

#### 3. Overuse Injury Risk Assessment
- **Patellofemoral Tendon Load:** {'Low risk' if knee_ext >= target_k_low else 'Elevated (Saddle too low increases patellar shear force)'}
- **Hamstring / Biceps Femoris Strain:** {'Low risk' if knee_ext <= target_k_high else 'Elevated (Hyperextension at BDC increases posterior knee strain)'}
- **Lumbar Spine Fatigue:** {'Within normal bounds' if hip_closed >= target_h_low else 'Elevated (Aggressive hip closure forces lower back compensation)'}

*Note: Make adjustments in small increments (3–5mm) and perform a dynamic test ride between each change.*
"""
    return report_md


def generate_consultation(
    angles: dict, 
    targets: dict, 
    provider: str = "OFFLINE", 
    api_key: str = None
) -> str:
    """
    Dispatches biomechanical evaluation to Claude, Gemini, or Offline Rule Engine.
    """
    if provider == "OFFLINE" or not api_key:
        return generate_rule_based_breakdown(angles, targets)

    prompt = f"""
    You are an elite clinical biomechanist and professional cycling fit specialist (equivalent to certified master fitters using MyVeloFit, Retül, and Bike Fast Fit).
    Analyze the following dynamic kinematic motion capture data:

    OBSERVED METRIC ENVELOPE:
    - Knee Extension at BDC (6 o'clock): {angles.get('knee_ext_max', 145.0):.1f} deg (Reference Target: {targets.get('knee_ext_max', (140,150))[0]}-{targets.get('knee_ext_max', (140,150))[1]} deg)
    - Knee Flexion at TDC (12 o'clock): {angles.get('knee_flex_min', 71.0):.1f} deg (Reference Target: {targets.get('knee_flex_min', (68,75))[0]}-{targets.get('knee_flex_min', (68,75))[1]} deg)
    - Closed Hip Angle at TDC: {angles.get('hip_closed_min', 49.0):.1f} deg (Reference Target: {targets.get('hip_closed_min', (45,55))[0]}-{targets.get('hip_closed_min', (45,55))[1]} deg)
    - Torso Incline to Horizontal: {angles.get('back_avg', 43.5):.1f} deg (Reference Target: {targets.get('back_avg', (40,50))[0]}-{targets.get('back_avg', (40,50))[1]} deg)
    - Shoulder / Arm Angle: {angles.get('arm_avg', 88.0):.1f} deg (Reference Target: {targets.get('arm_avg', (85,95))[0]}-{targets.get('arm_avg', (85,95))[1]} deg)
    - Dynamic Ankling at BDC: {angles.get('ankling_avg', angles.get('foot_angle_avg', 96.0)):.1f} deg (Reference Target: {targets.get('ankling_bdc', (90,105))[0]}-{targets.get('ankling_bdc', (90,105))[1]} deg)

    REQUIRED OUTPUT FORMAT:
    1. Overall Fit Alignment Score (0 to 100%).
    2. Primary Kinematic Envelopes evaluation explaining what the angles indicate physiologically.
    3. Step-by-Step Prioritized Action Plan with exact millimeter adjustments for Saddle Height (+/- mm), Saddle Fore-Aft, and Cockpit Spacers/Stem.
    4. Overuse Injury Risk Assessment (Patellofemoral load, hamstring strain, lumbar fatigue).
    
    TONE & STYLE:
    - Formal, clinical, structured markdown.
    - Zero emojis.
    - Exact and concise (under 300 words).
    """

    if provider == "CLAUDE":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            # Fallback to Claude 3.5 Sonnet if 3.7 identifier varies
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=800,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text.strip()
            except Exception as e2:
                return f"Anthropic Claude API Error: {str(e2)}\n\n" + generate_rule_based_breakdown(angles, targets)

    elif provider == "GEMINI":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Google Gemini API Error: {str(e)}\n\n" + generate_rule_based_breakdown(angles, targets)

    return generate_rule_based_breakdown(angles, targets)
