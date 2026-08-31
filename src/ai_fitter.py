"""
Open-BikeFit - Biomechanical Fit Report Engine.
Deterministic kinematic rules + LLM narrative reporting with strict studio guardrails.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def generate_rule_based_breakdown(
    angles: dict, 
    targets: dict, 
    rider_profile: dict = None
) -> str:
    """
    Generates a deterministic bike fit breakdown without requiring external AI APIs.
    Follows standard studio fitting protocols (Holmes knee angle, KOPS, cockpit reach).
    """
    if rider_profile is None:
        rider_profile = {}

    rider_name = rider_profile.get('name', 'Rider')
    discipline = rider_profile.get('discipline', 'Road Endurance')
    fit_goal = rider_profile.get('goal', 'Balanced Performance')
    pain_points = rider_profile.get('pain_points', [])
    
    knee_ext = float(angles.get('knee_ext_max', 145.0))
    knee_flex = float(angles.get('knee_flex_min', 71.0))
    hip_closed = float(angles.get('hip_closed_min', 49.0))
    back_angle = float(angles.get('back_avg', 43.5))
    arm_angle = float(angles.get('arm_avg', 88.0))
    ankling = float(angles.get('ankling_avg', angles.get('foot_angle_avg', 96.0)))

    # Knee Extension Evaluation
    target_k_low, target_k_high = targets.get('knee_ext_max', (140, 150))
    saddle_height_recs = []
    fit_score = 100

    if knee_ext < target_k_low:
        diff_deg = target_k_low - knee_ext
        mm_adj = int(diff_deg * 2.8)
        saddle_height_recs.append(
            f"**Raise Saddle Height by {mm_adj} mm**: Knee extension is {knee_ext:.1f}°, which is below the target range ({target_k_low}°–{target_k_high}°). Raising the saddle will open the knee angle, decrease patellar tendon strain, and improve pedal stroke clearance at TDC."
        )
        fit_score -= int(diff_deg * 3.5)
    elif knee_ext > target_k_high:
        diff_deg = knee_ext - target_k_high
        mm_adj = int(diff_deg * 2.8)
        saddle_height_recs.append(
            f"**Lower Saddle Height by {mm_adj} mm**: Knee extension is {knee_ext:.1f}°, exceeding the recommended envelope ({target_k_low}°–{target_k_high}°). Lowering the saddle will eliminate hyperextension at the 6 o'clock position, prevent rocking hips, and reduce posterior hamstring strain."
        )
        fit_score -= int(diff_deg * 3.5)
    else:
        saddle_height_recs.append(
            f"**Saddle Height**: Optimal ({knee_ext:.1f}° within {target_k_low}°–{target_k_high}° window). Stable leg extension at BDC."
        )

    # Hip / Cockpit Stack Evaluation
    target_h_low, target_h_high = targets.get('hip_closed_min', (45, 55))
    cockpit_recs = []
    if hip_closed < target_h_low:
        diff_h = target_h_low - hip_closed
        cockpit_recs.append(
            f"**Increase Handlebar Stack by +5 to 10 mm (add spacers)**: Closed hip angle is {hip_closed:.1f}° at Top Dead Center (TDC), which is overly acute (target: {target_h_low}°–{target_h_high}°). Adding spacers under the stem will relieve diaphragm compression and improve pelvic posture."
        )
        fit_score -= 8
    elif hip_closed > target_h_high:
        cockpit_recs.append(
            f"**Cockpit Drop**: Posture is relatively upright (Closed hip {hip_closed:.1f}°). If seeking a more aerodynamic profile, consider lowering the stem by 5 mm."
        )
    else:
        cockpit_recs.append(
            f"**Closed Hip Clearance**: Optimal ({hip_closed:.1f}° at 12 o'clock TDC)."
        )

    # Shoulder / Reach Evaluation
    target_arm_low, target_arm_high = targets.get('arm_avg', (85, 95))
    reach_recs = []
    if arm_angle < target_arm_low:
        reach_recs.append(
            f"**Cockpit Reach is Compact (Arm angle {arm_angle:.1f}°)**: Consider swapping to a +10mm longer stem to open shoulder space and distribute upper body weight evenly."
        )
        fit_score -= 6
    elif arm_angle > target_arm_high:
        reach_recs.append(
            f"**Cockpit Reach is Stretched (Arm angle {arm_angle:.1f}°)**: Consider a -10mm shorter stem or adjusting hood angle upward to relieve pressure on the palms and triceps."
        )
        fit_score -= 6
    else:
        reach_recs.append(
            f"**Cockpit Reach**: Balanced ({arm_angle:.1f}° arm-to-torso angle). Weight is neutrally supported."
        )

    # Ankling Evaluation
    target_a_low, target_a_high = targets.get('ankling_bdc', (90, 105))
    ankle_recs = []
    if ankling > target_a_high:
        ankle_recs.append(
            f"**Ankling / Plantarflexion Warning**: Ankle angle is {ankling:.1f}° at BDC (noticeable toe-down pedaling). Often indicates the rider is compensating for a high saddle or cleat positioned too far forward."
        )
        fit_score -= 7
    else:
        ankle_recs.append(
            f"**Ankling Mechanics**: Stable ({ankling:.1f}° at BDC)."
        )

    fit_score = max(min(fit_score, 100), 45)

    # Pain points cross-referencing
    pain_analysis = []
    if pain_points:
        for p in pain_points:
            p_lower = p.lower()
            if "anterior" in p_lower or "front of knee" in p_lower:
                pain_analysis.append(f"- **Front of Knee (Patellar Discomfort)**: Frequently caused by a saddle that is slightly too low or positioned too far forward, increasing knee flexion loads at the 3 o'clock power phase. Follow the saddle height adjustment above.")
            elif "posterior" in p_lower or "back of knee" in p_lower:
                pain_analysis.append(f"- **Back of Knee (Hamstring Discomfort)**: Typically caused by hyperextension at the 6 o'clock BDC position or excessive saddle setback. Ensure the saddle is lowered to keep knee extension under {target_k_high}°.")
            elif "back" in p_lower or "lumbar" in p_lower:
                pain_analysis.append(f"- **Lower Back Fatigue**: Common with excessive reach or tight closed hip angles. Increasing stem stack height by 5–10mm will reduce pelvis rotation torque.")
            elif "numb" in p_lower or "hand" in p_lower or "wrist" in p_lower:
                pain_analysis.append(f"- **Hand & Wrist Numbness**: Indicates excessive forward weight distribution. Shortening reach or slightly tilting saddle nose up to level will shift load back to the sit bones.")
            elif "neck" in p_lower:
                pain_analysis.append(f"- **Neck & Trapezius Strain**: Often caused by craned neck angle from excessive drop. Increasing handlebar height will provide immediate relief.")
    else:
        pain_analysis.append("- No specific pain points flagged in rider intake profile.")

    pain_section = "\n".join(pain_analysis)

    report_md = f"""### Open-BikeFit Biomechanical Posture Report

**Rider:** `{rider_name}` | **Discipline:** `{discipline}` | **Target Profile:** `{fit_goal}`  
**Overall Fit Alignment Score:** `{fit_score}% / 100%`

---

#### 1. Kinematic Joint Angle Summary
- **Knee Extension at BDC (6 o'clock):** `{knee_ext:.1f}°` *(Target: {target_k_low}°–{target_k_high}°)*
- **Knee Flexion at TDC (12 o'clock):** `{knee_flex:.1f}°` *(Target: {targets.get('knee_flex_min', (68,75))[0]}°–{targets.get('knee_flex_min', (68,75))[1]}°)*
- **Closed Hip Angle at TDC:** `{hip_closed:.1f}°` *(Target: {target_h_low}°–{target_h_high}°)*
- **Torso Angle (to horizontal):** `{back_angle:.1f}°` *(Target: {targets.get('back_avg', (40,50))[0]}°–{targets.get('back_avg', (40,50))[1]}°)*
- **Shoulder / Reach Angle:** `{arm_angle:.1f}°` *(Target: {target_arm_low}°–{target_arm_high}°)*
- **Ankle Angle at BDC:** `{ankling:.1f}°` *(Target: {target_a_low}°–{target_a_high}°)*

---

#### 2. Prioritized Wrench Adjustments (Step-by-Step)
1. **Saddle Position:**
   - {saddle_height_recs[0]}
2. **Cockpit Stack & Reach:**
   - {cockpit_recs[0]}
   - {reach_recs[0]}
3. **Pedal & Shoe Interface:**
   - {ankle_recs[0]}

---

#### 3. Intake Symptom & Pain Point Diagnostics
{pain_section}

---

#### 4. Iteration & Adaptation Protocol
- Perform physical adjustments in single increments (e.g., 3–5 mm at a time).
- Test ride for 20–30 km under normal riding cadence before re-recording a progress video.
- *Notice: Open-BikeFit provides geometric kinematic baseline estimation to assist riders and bike fitters. It is not a medical diagnostic tool.*
"""
    return report_md


def generate_consultation(
    angles: dict, 
    targets: dict, 
    provider: str = "OFFLINE", 
    api_key: str = None,
    rider_profile: dict = None
) -> str:
    """
    Generates a professional bike fit summary. 
    The LLM API key is used strictly for formatting and writing the narrative report based on CV kinematics.
    """
    if provider == "OFFLINE" or not api_key:
        return generate_rule_based_breakdown(angles, targets, rider_profile)

    if rider_profile is None:
        rider_profile = {}

    rider_name = rider_profile.get('name', 'Rider')
    discipline = rider_profile.get('discipline', 'Road Endurance')
    fit_goal = rider_profile.get('goal', 'Balanced Performance')
    pain_points = ", ".join(rider_profile.get('pain_points', [])) or "None reported"

    prompt = f"""
    You are an expert bicycle fitting specialist generating an automated fit report for Open-BikeFit.
    Format your response exactly like an authentic, high-end bike fit studio summary (similar to MyVeloFit or Retül reports).

    RIDER PROFILE:
    - Name: {rider_name}
    - Discipline: {discipline}
    - Fit Target: {fit_goal}
    - Reported Discomfort / Symptoms: {pain_points}

    OBSERVED KINEMATIC ANGLES (Calculated from Computer Vision):
    - Knee Extension at BDC (6 o'clock): {angles.get('knee_ext_max', 145.0):.1f} deg (Reference Target: {targets.get('knee_ext_max', (140,150))[0]}-{targets.get('knee_ext_max', (140,150))[1]} deg)
    - Knee Flexion at TDC (12 o'clock): {angles.get('knee_flex_min', 71.0):.1f} deg (Reference Target: {targets.get('knee_flex_min', (68,75))[0]}-{targets.get('knee_flex_min', (68,75))[1]} deg)
    - Closed Hip Angle at TDC: {angles.get('hip_closed_min', 49.0):.1f} deg (Reference Target: {targets.get('hip_closed_min', (45,55))[0]}-{targets.get('hip_closed_min', (45,55))[1]} deg)
    - Torso Incline: {angles.get('back_avg', 43.5):.1f} deg (Reference Target: {targets.get('back_avg', (40,50))[0]}-{targets.get('back_avg', (40,50))[1]} deg)
    - Shoulder / Arm Angle: {angles.get('arm_avg', 88.0):.1f} deg (Reference Target: {targets.get('arm_avg', (85,95))[0]}-{targets.get('arm_avg', (85,95))[1]} deg)
    - Dynamic Ankling at BDC: {angles.get('ankling_avg', angles.get('foot_angle_avg', 96.0)):.1f} deg (Reference Target: {targets.get('ankling_bdc', (90,105))[0]}-{targets.get('ankling_bdc', (90,105))[1]} deg)

    STRICT GUARDRAILS & STRUCTURE:
    1. Overall Fit Alignment Score (e.g. 84% / 100%).
    2. Kinematic Joint Angle Summary comparing observed values vs reference targets.
    3. Step-by-Step Prioritized Wrench Adjustments with explicit millimeter changes for Saddle Height (+/- mm), Saddle Fore/Aft (+/- mm), Handlebar Stack Spacers (+/- mm), and Stem Length.
    4. Intake Symptom & Discomfort Diagnostics addressing rider's reported symptoms ({pain_points}) and how the physical adjustments resolve them.
    5. 2-Week Adaptation & Re-Testing Protocol.
    
    TONE & STYLE:
    - Clean, professional, technical Markdown.
    - Zero emojis.
    - Non-clinical posture guidance (no medical diagnostic claims).
    - Under 350 words.
    """

    if provider == "CLAUDE":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=900,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=900,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text.strip()
            except Exception as e2:
                return f"Anthropic Claude API Notice: {str(e2)}\n\n" + generate_rule_based_breakdown(angles, targets, rider_profile)

    elif provider == "GEMINI":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Google Gemini API Notice: {str(e)}\n\n" + generate_rule_based_breakdown(angles, targets, rider_profile)

    return generate_rule_based_breakdown(angles, targets, rider_profile)
