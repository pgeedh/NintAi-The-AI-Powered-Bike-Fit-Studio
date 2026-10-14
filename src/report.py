"""PDF report generation (fpdf2)."""
import os
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from src import fit_profiles as fp

STATUS_TXT = {'ok': 'In range', 'watch': 'Borderline', 'fix': 'Adjust', 'na': 'n/a'}
STATUS_RGB = {'ok': (22, 163, 74), 'watch': (217, 119, 6), 'fix': (220, 38, 38), 'na': (120, 120, 120)}
ACCENT = (14, 116, 144)


def _latin(text):
    """Core PDF fonts are latin-1 only; map common unicode to safe equivalents."""
    repl = {'°': ' deg', '—': '-', '–': '-', '’': "'", '‘': "'", '“': '"', '”': '"',
            '…': '...', '•': '-', '≈': '~', '×': 'x'}
    for a, b in repl.items():
        text = text.replace(a, b)
    return text.encode('latin-1', 'replace').decode('latin-1')


class BikeFitPDF(FPDF):
    def header(self):
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, 210, 18, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 14)
        self.set_xy(10, 4)
        self.cell(0, 10, 'NintAi  |  Bike Fit Report', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, 'Nintai (Japanese for Perseverance) - Created with love for the passion of Triathlon by Pruthvi',
                  align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 4, f'Page {self.page_no()}  -  2D video estimate, not medical advice.', align='C')
        self.set_text_color(0, 0, 0)

    def section(self, title):
        self.ln(2)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*ACCENT)
        self.cell(0, 8, _latin(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_text_color(0, 0, 0)
        self.ln(2)


def generate_fit_report(result, snapshot_paths, output_path=None, coach_text=None, rider_name=""):
    """
    Build the PDF. Returns the PDF as bytes (and writes it to output_path if given).
    result: dict from engine.analyze_video / analyze_image.
    """
    prof = fp.PROFILES[result['profile']]
    pdf = BikeFitPDF()
    pdf.set_auto_page_break(True, margin=18)
    pdf.add_page()

    # Summary line
    pdf.set_font('Helvetica', '', 10)
    who = f"Rider: {rider_name}   |   " if rider_name else ""
    pdf.cell(0, 6, _latin(f"{who}Style: {prof['name']}   |   {datetime.now():%d %b %Y %H:%M}   |   "
                          f"Source: {result['mode']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if result.get('score') is not None:
        pdf.set_font('Helvetica', 'B', 22)
        sc = result['score']
        col = STATUS_RGB['ok'] if sc >= 80 else STATUS_RGB['watch'] if sc >= 55 else STATUS_RGB['fix']
        pdf.set_text_color(*col)
        pdf.cell(0, 12, f"Fit score: {sc}/100", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    # Images
    pdf.section('Visual assessment')
    order = [k for k in ('bdc', 'tdc', 'front', 'photo') if k in snapshot_paths]
    if len(order) == 1:
        pdf.image(snapshot_paths[order[0]], x=10, w=190)
    else:
        y = pdf.get_y()
        x_positions = [10, 105]
        row_h = 0
        for i, k in enumerate(order):
            col = i % 2
            if col == 0 and i > 0:
                y += row_h + 4
            info = pdf.image(snapshot_paths[k], x=x_positions[col], y=y, w=93)
            row_h = max(row_h if col else 0, info.rendered_height)
        pdf.set_y(y + row_h + 4)

    # Metrics table
    pdf.section('Measured angles')
    widths = [70, 28, 40, 30]
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(236, 244, 247)
    for w, h in zip(widths, ['Metric', 'Value', 'Target range', 'Status']):
        pdf.cell(w, 8, h, border=1, align='C', fill=True)
    pdf.ln()
    pdf.set_font('Helvetica', '', 10)
    for k, meta in fp.METRICS.items():
        v = result['metrics'].get(k, 0)
        st = result['statuses'].get(k, 'na')
        lo, hi = prof['ranges'][k]
        pdf.cell(widths[0], 8, _latin(meta['label']), border=1)
        pdf.cell(widths[1], 8, f"{v:.0f} deg" if v else "-", border=1, align='C')
        pdf.cell(widths[2], 8, f"{lo}-{hi} deg", border=1, align='C')
        pdf.set_text_color(*STATUS_RGB[st])
        pdf.cell(widths[3], 8, STATUS_TXT[st], border=1, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    # Recommendations
    pdf.section('What to adjust (in this order)')
    pdf.set_font('Helvetica', '', 10)
    if not result['recommendations']:
        pdf.multi_cell(0, 6, "Everything measured is within range for this style. If you're comfortable, keep it!")
    for i, r in enumerate(result['recommendations'], 1):
        pdf.set_font('Helvetica', 'B', 10)
        pdf.multi_cell(0, 6, _latin(f"{i}. {r['title']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 5, _latin(r['detail']), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    if result.get('warnings'):
        pdf.section('Capture quality notes')
        pdf.set_font('Helvetica', 'I', 9)
        for w in result['warnings']:
            pdf.multi_cell(0, 5, _latin(f"- {w}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if coach_text:
        pdf.add_page()
        pdf.section('Coach notes')
        pdf.set_font('Helvetica', '', 10)
        clean = coach_text.replace('**', '').replace('### ', '').replace('## ', '').replace('# ', '')
        pdf.multi_cell(0, 5.5, _latin(clean))

    data = bytes(pdf.output())
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'wb') as fh:
            fh.write(data)
    return data
