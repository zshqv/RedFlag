# =============================================================================
# report_generator.py — Excel, PDF, and PPTX Report Generator (v2.0)
# =============================================================================

import os
import warnings
import re
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from bs4 import XMLParsedAsHTMLWarning
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import jinja2

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

OUTPUT_DIR = "output"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    return text.encode("ascii", "replace").decode("ascii").replace("?", " ").strip()

def generate_excel(ticker, analysis, comparison, latest_date, previous_date):
    """Generate 3-sheet Excel workbook."""
    ensure_output_dir()
    wb = Workbook()
    ws = wb.active
    ws.title = "Quick Brief"

    findings = analysis["findings"]
    summary = analysis["summary"]

    header_fill = PatternFill(start_color="1a1a2e", end_color="1a1a2e", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    row = 1
    headers = ["Company", "Ticker", "Source", "Filing Date", "Verdict", "Total", "HIGH", "MEDIUM", "LOW"]
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    ws.freeze_panes = "A6"

    row = 2
    high_count = summary["by_severity"].get("HIGH", 0)
    medium_count = summary["by_severity"].get("MEDIUM", 0)
    low_count = summary["by_severity"].get("LOW", 0)

    ws.cell(row=row, column=1).value = ticker
    ws.cell(row=row, column=2).value = ticker
    ws.cell(row=row, column=3).value = comparison.get("exchange", "Unknown")
    ws.cell(row=row, column=4).value = latest_date
    ws.cell(row=row, column=5).value = "REVIEW REQUIRED" if high_count > 0 else "PASS"
    ws.cell(row=row, column=6).value = summary["total"]
    ws.cell(row=row, column=7).value = high_count
    ws.cell(row=row, column=8).value = medium_count
    ws.cell(row=row, column=9).value = low_count

    row = 5
    finding_headers = ["Section", "Page", "Para", "Sent", "Keyword", "Category", "Severity", "Flagged Sentence", "Explanation"]
    for col, header in enumerate(finding_headers, start=1):
        cell = ws.cell(row=row, column=col)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.border = thin_border

    ws.auto_filter.ref = f"A{row}:{get_column_letter(len(finding_headers))}{row}"

    sorted_findings = sorted(findings, key=lambda f: (
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(f["severity"], 3),
        -f["severity_score"]
    ))

    for finding in sorted_findings:
        row += 1
        severity = finding["severity"]
        if severity == "HIGH":
            fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        elif severity == "MEDIUM":
            fill = PatternFill(start_color="FFF3CC", end_color="FFF3CC", fill_type="solid")
        else:
            fill = PatternFill(start_color="E6FFE6", end_color="E6FFE6", fill_type="solid")

        ws.cell(row=row, column=1).value = finding["section"]
        ws.cell(row=row, column=2).value = finding["page_num"]
        ws.cell(row=row, column=3).value = finding["para_num"]
        ws.cell(row=row, column=4).value = finding["sentence_num"]
        ws.cell(row=row, column=5).value = finding["keyword"]
        ws.cell(row=row, column=6).value = finding["category"]
        ws.cell(row=row, column=7).value = finding["severity"]
        ws.cell(row=row, column=8).value = finding["flagged_sentence"][:100]
        ws.cell(row=row, column=9).value = finding["explanation"][:100]

        for col in range(1, len(finding_headers) + 1):
            ws.cell(row=row, column=col).fill = fill
            ws.cell(row=row, column=col).border = thin_border

    for col in range(1, 10):
        ws.column_dimensions[get_column_letter(col)].width = 15

    ws2 = wb.create_sheet("Risk Dashboard")
    ws2.cell(row=1, column=1).value = "Total Findings"
    ws2.cell(row=1, column=2).value = summary["total"]
    ws2.cell(row=2, column=1).value = "HIGH"
    ws2.cell(row=2, column=2).value = high_count
    ws2.cell(row=3, column=1).value = "MEDIUM"
    ws2.cell(row=3, column=2).value = medium_count
    ws2.cell(row=4, column=1).value = "LOW"
    ws2.cell(row=4, column=2).value = low_count

    row = 6
    ws2.cell(row=row, column=1).value = "Category"
    ws2.cell(row=row, column=2).value = "Count"
    for category, count in summary["by_category"].items():
        row += 1
        ws2.cell(row=row, column=1).value = category
        ws2.cell(row=row, column=2).value = count

    ws3 = wb.create_sheet("YoY Comparison")
    ws3.cell(row=1, column=1).value = "Year-over-Year Comparison"
    ws3.cell(row=2, column=1).value = "Category"
    ws3.cell(row=2, column=2).value = "Prior Year"
    ws3.cell(row=2, column=3).value = "This Year"
    ws3.cell(row=2, column=4).value = "Delta"

    if comparison.get("by_category"):
        row = 3
        for cat_name, cat_data in comparison["by_category"].items():
            ws3.cell(row=row, column=1).value = cat_name
            ws3.cell(row=row, column=2).value = cat_data.get("previous_count", 0)
            ws3.cell(row=row, column=3).value = cat_data.get("current_count", 0)
            ws3.cell(row=row, column=4).value = cat_data.get("change", 0)
            row += 1

    filepath = os.path.join(OUTPUT_DIR, f"{ticker}_redflag.xlsx")
    wb.save(filepath)
    return filepath

def generate_pdf(ticker, analysis, comparison, latest_date, exchange, previous_date):
    """Generate PDF report using simple FPDF2."""
    ensure_output_dir()

    findings = analysis["findings"]
    summary = analysis["summary"]

    high_count = summary["by_severity"].get("HIGH", 0)
    medium_count = summary["by_severity"].get("MEDIUM", 0)
    low_count = summary["by_severity"].get("LOW", 0)
    total = summary["total"]

    if total > 0:
        avg_severity = round(sum(f.get("severity_score", 50) for f in findings) / total)
    else:
        avg_severity = 0

    if high_count > 0:
        verdict_line = f"CRITICAL: {high_count} HIGH-severity flags require immediate review."
    elif medium_count > 3:
        verdict_line = f"ELEVATED RISK: {medium_count} MEDIUM flags detected. Detailed review recommended."
    else:
        verdict_line = f"LOW RISK: Minimal findings ({low_count} low-severity). Standard due diligence sufficient."

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 10, f"{ticker}: RedFlag Risk Report", ln=True)

        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Exchange: {exchange} | Filing Date: {latest_date}", ln=True)
        pdf.cell(0, 8, f"Report Generated: {datetime.now().strftime('%Y-%m-%d')}", ln=True)

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Verdict", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 5, verdict_line)

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Finding Counts", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Total: {total} | HIGH: {high_count} | MEDIUM: {medium_count} | LOW: {low_count}", ln=True)

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Top Findings", ln=True)
        pdf.set_font("Helvetica", "", 10)

        for idx, f in enumerate(findings[:10]):
            pdf.multi_cell(0, 4, f"{idx+1}. {f['keyword']} ({f['section']}, page {f['page_num']}) — {f['explanation'][:80]}")

        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Methodology", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 4, "This report analyzes all 18 10-K sections using a keyword library of 220+ terms across 6 risk categories. Severity is scored 0-100 based on sentiment, mitigating/amplifying language, and keyword co-occurrence.")

        pdf.ln(3)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 4, "github.com/zshqv/RedFlag — Not financial advice.", ln=True)

        filepath = os.path.join(OUTPUT_DIR, f"{ticker}_redflag.pdf")
        pdf.output(filepath)
        return filepath

    except ImportError:
        print("[RedFlag] FPDF2 not available, skipping PDF generation")
        return None

def generate_pptx(ticker, analysis, comparison, latest_date, exchange):
    """Generate 8-slide PPTX presentation."""
    ensure_output_dir()

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    findings = analysis["findings"]
    summary = analysis["summary"]

    high_count = summary["by_severity"].get("HIGH", 0)
    medium_count = summary["by_severity"].get("MEDIUM", 0)
    low_count = summary["by_severity"].get("LOW", 0)
    total = summary["total"]

    print("[RedFlag] Building slide 1: Cover")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(26, 26, 46)

    left = Inches(1)
    top = Inches(2)
    width = Inches(11.333)
    height = Inches(2)

    title_box = slide.shapes.add_textbox(left, top, width, height)
    title_frame = title_box.text_frame
    title_frame.text = sanitize_text(f"{ticker}: RedFlag Risk Report")
    title_frame.paragraphs[0].font.size = Pt(54)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

    subtitle_box = slide.shapes.add_textbox(left, top + Inches(2.2), width, Inches(1))
    subtitle_frame = subtitle_box.text_frame
    subtitle_frame.text = sanitize_text(f"{exchange} | {latest_date}")
    subtitle_frame.paragraphs[0].font.size = Pt(24)
    subtitle_frame.paragraphs[0].font.color.rgb = RGBColor(200, 200, 200)

    footer_box = slide.shapes.add_textbox(left, top + Inches(4.5), width, Inches(1))
    footer_frame = footer_box.text_frame
    footer_frame.text = f"Total: {total} | HIGH: {high_count} | MEDIUM: {medium_count} | LOW: {low_count}"
    footer_frame.paragraphs[0].font.size = Pt(18)
    footer_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

    print("[RedFlag] Building slide 2: Risk Scorecard")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(245, 245, 245)

    metrics = [
        ("Total", str(total), RGBColor(100, 100, 100)),
        ("HIGH", str(high_count), RGBColor(231, 76, 60)),
        ("MEDIUM", str(medium_count), RGBColor(243, 156, 18)),
        ("LOW", str(low_count), RGBColor(39, 174, 96)),
    ]

    for idx, (label, value, color) in enumerate(metrics):
        left_pos = Inches(1 + idx * 2.8)
        box = slide.shapes.add_shape(1, left_pos, Inches(2), Inches(2), Inches(2.5))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(255, 255, 255)
        box.line.color.rgb = color

        text_frame = box.text_frame
        text_frame.word_wrap = True
        p = text_frame.paragraphs[0]
        p.text = sanitize_text(value)
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = color
        p.alignment = PP_ALIGN.CENTER

        label_box = slide.shapes.add_textbox(left_pos, Inches(4.8), Inches(2), Inches(0.8))
        label_frame = label_box.text_frame
        label_frame.text = sanitize_text(label)
        label_frame.paragraphs[0].font.size = Pt(14)
        label_frame.paragraphs[0].font.bold = True
        label_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    print("[RedFlag] Building slide 3: Category Breakdown (bar chart)")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(255, 255, 255)

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = "Risk Findings by Category"
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = RGBColor(26, 26, 46)

    categories = list(summary["by_category"].items())
    for idx, (cat_name, cat_count) in enumerate(categories[:6]):
        left_pos = Inches(0.8 + idx * 1.8)
        bar_height = min(4.5, cat_count * 0.3)
        bar = slide.shapes.add_shape(1, left_pos, Inches(5.5 - bar_height), Inches(1.4), Inches(bar_height))
        bar.fill.solid()
        bar.fill.fore_color.rgb = RGBColor(26, 26, 46)
        bar.line.width = 0

        label_box = slide.shapes.add_textbox(left_pos, Inches(6), Inches(1.4), Inches(0.4))
        label_frame = label_box.text_frame
        label_frame.text = sanitize_text(cat_name)
        label_frame.paragraphs[0].font.size = Pt(10)
        label_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        value_box = slide.shapes.add_textbox(left_pos, Inches(5.2 - bar_height), Inches(1.4), Inches(0.3))
        value_frame = value_box.text_frame
        value_frame.text = str(cat_count)
        value_frame.paragraphs[0].font.size = Pt(11)
        value_frame.paragraphs[0].font.bold = True
        value_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        value_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    print("[RedFlag] Building slide 4: All Flags by Tier")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(255, 255, 255)

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = "All Findings by Severity Tier"
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True

    high_findings = [f for f in findings if f["severity"] == "HIGH"]
    medium_findings = [f for f in findings if f["severity"] == "MEDIUM"]
    low_findings = [f for f in findings if f["severity"] == "LOW"]

    columns = [
        ("HIGH", high_findings, RGBColor(231, 76, 60)),
        ("MEDIUM", medium_findings, RGBColor(243, 156, 18)),
        ("LOW", low_findings, RGBColor(39, 174, 96)),
    ]

    for col_idx, (tier_name, tier_findings, color) in enumerate(columns):
        left_pos = Inches(0.5 + col_idx * 4)
        top_pos = Inches(1.2)

        header_box = slide.shapes.add_shape(1, left_pos, top_pos, Inches(3.8), Inches(0.4))
        header_box.fill.solid()
        header_box.fill.fore_color.rgb = color
        header_frame = header_box.text_frame
        header_frame.text = sanitize_text(f"{tier_name} ({len(tier_findings)})")
        header_frame.paragraphs[0].font.size = Pt(12)
        header_frame.paragraphs[0].font.bold = True
        header_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        header_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        text_box = slide.shapes.add_textbox(left_pos, top_pos + Inches(0.5), Inches(3.8), Inches(5.5))
        text_frame = text_box.text_frame
        text_frame.word_wrap = True

        for finding in tier_findings[:8]:
            p = text_frame.add_paragraph()
            p.text = sanitize_text(f"• Pg{finding['page_num']} — {finding['keyword']} ({finding['section']})")
            p.font.size = Pt(9)
            p.level = 0

    print("[RedFlag] Building slide 5: Top 3 Flags")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(255, 255, 255)

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = "Top 3 Critical Findings to Present"
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True

    for idx, finding in enumerate(findings[:3]):
        top_pos = Inches(1.2 + idx * 2)
        card = slide.shapes.add_shape(1, Inches(0.5), top_pos, Inches(12.333), Inches(1.8))
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(240, 240, 240)
        card.line.color.rgb = RGBColor(26, 26, 46)

        text_box = slide.shapes.add_textbox(Inches(0.7), top_pos + Inches(0.1), Inches(12), Inches(1.6))
        text_frame = text_box.text_frame
        text_frame.word_wrap = True

        p = text_frame.paragraphs[0]
        p.text = sanitize_text(f"{idx+1}. {finding['keyword']} — {finding['section']} (Pg {finding['page_num']})")
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = RGBColor(26, 26, 46)

        p2 = text_frame.add_paragraph()
        p2.text = sanitize_text(finding["explanation"][:100])
        p2.font.size = Pt(10)
        p2.level = 0

    print("[RedFlag] Building slide 6: New Keywords")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(255, 255, 255)

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = "New Keywords This Year (Absent in Prior Year)"
    title_frame.paragraphs[0].font.size = Pt(24)
    title_frame.paragraphs[0].font.bold = True

    new_kws = comparison.get("new_keywords", [])
    for idx, kw in enumerate(new_kws[:20]):
        col = idx % 4
        row_num = idx // 4
        left_pos = Inches(0.5 + col * 3)
        top_pos = Inches(1.3 + row_num * 1.2)

        kw_box = slide.shapes.add_shape(1, left_pos, top_pos, Inches(2.8), Inches(0.8))
        kw_box.fill.solid()
        kw_box.fill.fore_color.rgb = RGBColor(230, 230, 230)
        kw_frame = kw_box.text_frame
        kw_frame.text = sanitize_text(kw)
        kw_frame.paragraphs[0].font.size = Pt(11)
        kw_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        kw_frame.vertical_anchor = 1

    print("[RedFlag] Building slide 7: YoY Trajectory")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(255, 255, 255)

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6))
    title_frame = title_box.text_frame
    title_frame.text = "Year-Over-Year Risk Trajectory"
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True

    traj = comparison.get("overall", {}).get("trajectory", "STABLE")
    traj_color = {"DETERIORATING": RGBColor(231, 76, 60), "STABLE": RGBColor(100, 100, 100)}.get(traj, RGBColor(39, 174, 96))

    traj_box = slide.shapes.add_shape(1, Inches(2), Inches(2.5), Inches(9.333), Inches(2))
    traj_box.fill.solid()
    traj_box.fill.fore_color.rgb = traj_color
    traj_frame = traj_box.text_frame
    traj_frame.text = sanitize_text(traj)
    traj_frame.paragraphs[0].font.size = Pt(48)
    traj_frame.paragraphs[0].font.bold = True
    traj_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
    traj_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    traj_frame.vertical_anchor = 1

    print("[RedFlag] Building slide 8: Methodology")
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(26, 26, 46)

    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.8))
    title_frame = title_box.text_frame
    title_frame.text = "Source & Methodology"
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

    info_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.3), Inches(12.333), Inches(5.8))
    info_frame = info_box.text_frame
    info_frame.word_wrap = True

    lines = [
        f"Filing: {ticker} | {exchange} | {latest_date}",
        "Keywords Scanned: 220+ across 6 risk categories",
        "Sections Analyzed: All 18 standard 10-K items",
        "Severity Scoring: Rule-based (0–100 scale)",
        "Explanation Engine: Claude API (Haiku 4.5) with fallback",
        "",
        "⚠ DISCLAIMER: Not financial advice. For due diligence use only.",
        "RedFlag is a co-pilot tool — validate all findings with human analysis.",
        "github.com/zshqv/RedFlag",
    ]

    for line in lines:
        p = info_frame.add_paragraph()
        p.text = sanitize_text(line)
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.space_before = Pt(6)

    filepath = os.path.join(OUTPUT_DIR, f"{ticker}_dashboard.pptx")
    prs.save(filepath)
    return filepath

def generate_reports(ticker, analysis, comparison, latest_date, previous_date, exchange):
    """Master function — generates Excel, PDF, and PPTX."""
    excel_path = generate_excel(ticker, analysis, comparison, latest_date, previous_date)
    pdf_path = generate_pdf(ticker, analysis, comparison, latest_date, exchange, previous_date)
    pptx_path = generate_pptx(ticker, analysis, comparison, latest_date, exchange)

    return {
        "excel": excel_path,
        "pdf": pdf_path,
        "pptx": pptx_path
    }
