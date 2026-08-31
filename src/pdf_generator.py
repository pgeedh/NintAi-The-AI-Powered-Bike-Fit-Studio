"""
Open-BikeFit - High-Resolution PDF Fit Report Generator.
Generates structured biomechanical posture reports for riders and fitters.
"""

import os
from fpdf import FPDF

class OpenVeloFitPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(24, 24, 27)
        self.cell(0, 6, 'OPEN-BIKEFIT BIOMECHANICAL REPORT', 0, 1, 'L')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(113, 113, 122)
        self.cell(0, 4, 'Kinematic Posture Baseline & Hardware Adjustment Guide', 0, 1, 'L')
        self.line(10, 21, 200, 21)
        self.ln(5)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', '', 7.5)
        self.set_text_color(161, 161, 170)
        self.cell(0, 8, f'Open-BikeFit (Open-Source Biomechanical Studio) | Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(24, 24, 27)
        self.cell(0, 6, label.upper(), 0, 1, 'L')
        self.ln(1)


def build_clinical_pdf(
    snap_tdc: str, 
    snap_bdc: str, 
    snap_power: str, 
    snap_overall: str, 
    stats: dict, 
    targets: dict, 
    consultation_text: str, 
    output_path: str = "outputs/reports/clinical_fit_report.pdf",
    rider_profile: dict = None
):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    pdf = OpenVeloFitPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    if rider_profile is None:
        rider_profile = {}

    r_name = rider_profile.get('name', 'Rider')
    r_disc = rider_profile.get('discipline', 'Road Endurance')
    r_goal = rider_profile.get('goal', 'Balanced Performance')

    # Rider Header Card
    pdf.set_fill_color(244, 244, 245)
    pdf.rect(10, 24, 190, 10, 'F')
    pdf.set_xy(12, 26)
    pdf.set_font('Helvetica', 'B', 8.5)
    pdf.set_text_color(24, 24, 27)
    pdf.cell(60, 5, f"Rider: {r_name}", 0, 0, 'L')
    pdf.cell(65, 5, f"Discipline: {r_disc}", 0, 0, 'L')
    pdf.cell(65, 5, f"Target: {r_goal}", 0, 1, 'L')
    pdf.ln(3)

    # 1. 4-Phase Stills
    pdf.chapter_title("1. Pedal Stroke Decomposition (4-Phase Kinematics)")
    img_w, img_h = 88, 50
    pos = [
        (12, 42, snap_tdc, "Phase 1: Top Dead Center (12h Flexion)"),
        (106, 42, snap_power, "Phase 2: Power Phase (3h Drive)"),
        (12, 98, snap_bdc, "Phase 3: Bottom Dead Center (6h Extension)"),
        (106, 98, snap_overall, "Phase 4: Full Kinetic Chain Profile")
    ]
    for x, y, path, lbl in pos:
        if path and os.path.exists(path):
            try:
                pdf.image(path, x, y, img_w, img_h)
            except Exception:
                pass
        pdf.set_xy(x, y + img_h + 1)
        pdf.set_font("Helvetica", 'I', 7.5)
        pdf.set_text_color(82, 82, 91)
        pdf.cell(img_w, 4, lbl, 0, 0, 'C')

    # 2. Angle Table
    pdf.set_y(158)
    pdf.chapter_title("2. Observed Kinematic Angles vs Target Envelopes")
    pdf.set_fill_color(244, 244, 245)
    pdf.set_draw_color(228, 228, 231)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_text_color(24, 24, 27)

    cols = [70, 35, 45, 40]
    pdf.cell(cols[0], 6, "Kinematic Metric", 1, 0, 'L', True)
    pdf.cell(cols[1], 6, "Observed Value", 1, 0, 'C', True)
    pdf.cell(cols[2], 6, "Reference Target", 1, 0, 'C', True)
    pdf.cell(cols[3], 6, "Status", 1, 1, 'C', True)

    def add_row(name, val, target_bounds, unit="deg"):
        t_low, t_high = target_bounds
        pdf.set_font("Helvetica", '', 8)
        pdf.set_text_color(39, 39, 42)
        pdf.cell(cols[0], 5.5, name, 1)
        pdf.cell(cols[1], 5.5, f"{val:.1f} {unit}", 1, 0, 'C')
        pdf.cell(cols[2], 5.5, f"{t_low} - {t_high} {unit}", 1, 0, 'C')

        is_opt = (t_low <= val <= t_high)
        if is_opt:
            pdf.set_text_color(22, 163, 74)
            status = "Optimal"
        elif val < t_low:
            pdf.set_text_color(220, 38, 38)
            status = "Low / Closed"
        else:
            pdf.set_text_color(220, 38, 38)
            status = "High / Extended"

        pdf.cell(cols[3], 5.5, status, 1, 1, 'C')
        pdf.set_text_color(39, 39, 42)

    add_row("Knee Extension (BDC 6h)", stats.get('knee_ext_max', 145.0), targets.get('knee_ext_max', (140, 150)))
    add_row("Knee Flexion (TDC 12h)", stats.get('knee_flex_min', 71.0), targets.get('knee_flex_min', (68, 75)))
    add_row("Closed Hip Angle (TDC 12h)", stats.get('hip_closed_min', 49.0), targets.get('hip_closed_min', (45, 55)))
    add_row("Torso Angle (to horizontal)", stats.get('back_avg', 43.5), targets.get('back_avg', (40, 50)))
    add_row("Shoulder / Reach Angle", stats.get('arm_avg', 88.0), targets.get('arm_avg', (85, 95)))
    add_row("Ankle Plantarflexion at BDC", stats.get('ankling_avg', stats.get('foot_angle_avg', 96.0)), targets.get('ankling_bdc', (90, 105)))

    # 3. Report Section
    if consultation_text:
        pdf.add_page()
        pdf.chapter_title("3. Studio Fit Summary & Hardware Adjustments")
        pdf.set_font("Helvetica", size=8.5)
        pdf.set_text_color(39, 39, 42)
        clean_text = consultation_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 4.8, clean_text)

    pdf.output(output_path)
    print(f"[Open-BikeFit] PDF Report compiled: {output_path}")
