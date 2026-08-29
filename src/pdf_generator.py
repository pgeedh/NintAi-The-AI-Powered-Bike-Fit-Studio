"""
NintAi Clinical Dossier PDF Generator.
"""

import os
from fpdf import FPDF

class FitDossierPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, 'NINTAI BIOMECHANICAL MOTION DOSSIER', 0, 1, 'L')
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(100, 116, 139)
        self.cell(0, 4, 'Dynamic Motion Capture Kinematics & Fit Evaluation', 0, 1, 'L')
        self.line(10, 22, 200, 22)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 8, f'NintAi Suite | Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Helvetica', 'B', 10.5)
        self.set_text_color(30, 41, 59)
        self.cell(0, 6, label.upper(), 0, 1, 'L')
        self.ln(1.5)


def build_clinical_pdf(
    snap_tdc: str, 
    snap_bdc: str, 
    snap_power: str, 
    snap_overall: str, 
    stats: dict, 
    targets: dict, 
    consultation_text: str, 
    output_path: str = "outputs/reports/clinical_fit_report.pdf"
):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    pdf = FitDossierPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    # 1. 4-Phase Stills
    pdf.chapter_title("1. Dynamic Stroke Decomposition (4-Phase Kinematics)")
    img_w, img_h = 88, 52
    pos = [
        (12, 34, snap_tdc, "Phase 1: Top Dead Center (12h)"),
        (106, 34, snap_power, "Phase 2: Power Delivery (3h)"),
        (12, 92, snap_bdc, "Phase 3: Bottom Dead Center (6h)"),
        (106, 92, snap_overall, "Phase 4: Full Kinetic Chain Profile")
    ]
    for x, y, path, lbl in pos:
        if path and os.path.exists(path):
            try:
                pdf.image(path, x, y, img_w, img_h)
            except Exception:
                pass
        pdf.set_xy(x, y + img_h + 1)
        pdf.set_font("Helvetica", 'I', 7.5)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(img_w, 4, lbl, 0, 0, 'C')

    # 2. Angle Table
    pdf.set_y(154)
    pdf.chapter_title("2. Observed Biomechanical Envelopes")
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font("Helvetica", 'B', 8.5)
    pdf.set_text_color(15, 23, 42)

    cols = [70, 35, 45, 40]
    pdf.cell(cols[0], 6.5, "Kinematic Metric", 1, 0, 'L', True)
    pdf.cell(cols[1], 6.5, "Observed Value", 1, 0, 'C', True)
    pdf.cell(cols[2], 6.5, "Reference Range", 1, 0, 'C', True)
    pdf.cell(cols[3], 6.5, "Status", 1, 1, 'C', True)

    def add_row(name, val, target_bounds, unit="deg"):
        t_low, t_high = target_bounds
        pdf.set_font("Helvetica", '', 8.5)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(cols[0], 6, name, 1)
        pdf.cell(cols[1], 6, f"{val:.1f} {unit}", 1, 0, 'C')
        pdf.cell(cols[2], 6, f"{t_low} - {t_high} {unit}", 1, 0, 'C')

        is_opt = (t_low <= val <= t_high)
        if is_opt:
            pdf.set_text_color(16, 185, 129)
            status = "Optimal"
        elif val < t_low:
            pdf.set_text_color(225, 29, 72)
            status = "Low / Closed"
        else:
            pdf.set_text_color(225, 29, 72)
            status = "High / Extended"

        pdf.cell(cols[3], 6, status, 1, 1, 'C')
        pdf.set_text_color(30, 41, 59)

    add_row("Knee Extension (BDC 6h)", stats.get('knee_ext_max', 145.0), targets.get('knee_ext_max', (140, 150)))
    add_row("Knee Flexion (TDC 12h)", stats.get('knee_flex_min', 71.0), targets.get('knee_flex_min', (68, 75)))
    add_row("Closed Hip Angle (TDC 12h)", stats.get('hip_closed_min', 49.0), targets.get('hip_closed_min', (45, 55)))
    add_row("Torso Incline to Horizontal", stats.get('back_avg', 43.5), targets.get('back_avg', (40, 50)))
    add_row("Shoulder / Cockpit Angle", stats.get('arm_avg', 88.0), targets.get('arm_avg', (85, 95)))
    add_row("Dynamic Ankling at BDC", stats.get('ankling_avg', stats.get('foot_angle_avg', 96.0)), targets.get('ankling_bdc', (90, 105)))

    # 3. Consultation Section
    if consultation_text:
        pdf.add_page()
        pdf.chapter_title("3. Diagnostic Consultation & Prescription")
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(30, 41, 59)
        clean_text = consultation_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, clean_text)

    pdf.output(output_path)
    print(f"[NintAi] PDF Dossier compiled: {output_path}")
