# =============================================================================
# report_generator.py -- Excel & PDF Report Builder
# =============================================================================
# This module takes all RedFlag findings and exports them into two files:
#
#   1. EXCEL REPORT -- Full structured data with all findings, category
#      breakdown, year-over-year comparison, and sentiment scores
#
#   2. PDF SUMMARY -- One-page executive summary with the highest priority
#      flags and overall risk trajectory
#
# Input:  Analysis results + comparison data from previous modules
# Output: TICKER_risk_report.xlsx and TICKER_summary.pdf
# =============================================================================

import os                                    # For creating output directories
import warnings                              # For suppressing XML parser warning
from datetime import datetime                # For timestamps in reports
import openpyxl                              # For building Excel reports
from openpyxl.styles import (               # For Excel formatting
    Font, PatternFill, Alignment
)
from fpdf import FPDF                        # For building PDF reports
from bs4 import XMLParsedAsHTMLWarning       # For suppressing BeautifulSoup warning

# Suppress the XML parsed as HTML warning -- harmless for our use case
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
OUTPUT_DIR = "output"   # All reports saved here

# Color scheme for Excel -- risk levels mapped to background colors
COLORS = {
    "HIGH RISK":        "FF4444",   # Red
    "ELEVATED RISK":    "FF8C00",   # Orange
    "NEUTRAL":          "FFD700",   # Yellow
    "LOW RISK":         "90EE90",   # Light green
    "POSITIVE":         "228B22",   # Dark green
    "header":           "1a1a2e",   # Dark navy
    "subheader":        "16213e",   # Slightly lighter navy
}


# -----------------------------------------------------------------------------
# HELPER -- Create output directory if it doesn't exist
# -----------------------------------------------------------------------------
def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[RedFlag] Created output directory: {OUTPUT_DIR}/")


# -----------------------------------------------------------------------------
# HELPER -- Apply header style to an Excel cell
# -----------------------------------------------------------------------------
def style_header_cell(cell, text, font_size=11, bold=True, color="header"):
    cell.value = text
    cell.font  = Font(
        name="Calibri", size=font_size, bold=bold, color="FFFFFF"
    )
    cell.fill  = PatternFill(
        start_color=COLORS[color], end_color=COLORS[color], fill_type="solid"
    )
    cell.alignment = Alignment(
        horizontal="center", vertical="center", wrap_text=True
    )


# -----------------------------------------------------------------------------
# HELPER -- Apply risk color to a sentiment cell
# -----------------------------------------------------------------------------
def style_risk_cell(cell, sentiment_label):
    color = COLORS.get(sentiment_label, "FFFFFF")
    cell.fill = PatternFill(
        start_color=color, end_color=color, fill_type="solid"
    )
    cell.font = Font(name="Calibri", size=9, bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")


# -----------------------------------------------------------------------------
# EXCEL SHEET 1 -- Executive Summary
# -----------------------------------------------------------------------------
def write_summary_sheet(ws, ticker, analysis, comparison, latest_date, previous_date):
    """Writes the executive summary sheet to the Excel workbook."""

    ws.title = "Executive Summary"
    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 25

    row = 1

    # Title
    ws.merge_cells(f"A{row}:B{row}")
    style_header_cell(
        ws[f"A{row}"],
        f"RedFlag Risk Report - {ticker}",
        font_size=14
    )
    row += 1

    ws.merge_cells(f"A{row}:B{row}")
    style_header_cell(
        ws[f"A{row}"],
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        font_size=9, bold=False, color="subheader"
    )
    row += 2

    # Filing dates
    style_header_cell(ws[f"A{row}"], "Latest 10-K Filing Date", color="subheader")
    ws[f"B{row}"] = latest_date
    row += 1

    style_header_cell(ws[f"A{row}"], "Previous 10-K Filing Date", color="subheader")
    ws[f"B{row}"] = previous_date or "N/A"
    row += 2

    # Overall trajectory
    overall = comparison["overall"]
    style_header_cell(ws[f"A{row}"], "Overall Risk Trajectory", color="subheader")
    ws[f"B{row}"] = overall["trajectory"]
    row += 1

    style_header_cell(ws[f"A{row}"], "Total Findings This Year", color="subheader")
    ws[f"B{row}"] = overall["current_total"]
    row += 1

    style_header_cell(ws[f"A{row}"], "Total Findings Last Year", color="subheader")
    ws[f"B{row}"] = overall["previous_total"]
    row += 1

    style_header_cell(ws[f"A{row}"], "Year-Over-Year Change", color="subheader")
    ws[f"B{row}"] = f"{overall['total_change']:+d} ({overall['percent_change']:+.1f}%)"
    row += 2

    # Sentiment trend
    sentiment = comparison["sentiment_trend"]
    style_header_cell(ws[f"A{row}"], "Sentiment Trend", color="subheader")
    ws[f"B{row}"] = sentiment["sentiment_trend"]
    row += 1

    style_header_cell(ws[f"A{row}"], "Avg Sentiment This Year", color="subheader")
    ws[f"B{row}"] = sentiment["current_avg_sentiment"]
    row += 1

    style_header_cell(ws[f"A{row}"], "Avg Sentiment Last Year", color="subheader")
    ws[f"B{row}"] = sentiment["previous_avg_sentiment"]
    row += 2

    # New keywords
    style_header_cell(
        ws[f"A{row}"],
        f"New Risk Keywords This Year ({len(comparison['new_keywords'])})",
        color="subheader"
    )
    ws[f"B{row}"] = (
        ", ".join(comparison["new_keywords"])
        if comparison["new_keywords"] else "None"
    )
    row += 2

    # Category breakdown header
    ws.merge_cells(f"A{row}:B{row}")
    style_header_cell(ws[f"A{row}"], "Category Breakdown", font_size=11)
    row += 1

    for cat, data in comparison["by_category"].items():
        style_header_cell(ws[f"A{row}"], cat, color="subheader")
        ws[f"B{row}"] = (
            f"{data['previous_count']} -> {data['current_count']} "
            f"({data['percent_change']:+.1f}%) {data['trajectory']}"
        )
        row += 1


# -----------------------------------------------------------------------------
# EXCEL SHEET 2 -- All Findings
# -----------------------------------------------------------------------------
def write_findings_sheet(ws, findings):
    """Writes all individual findings to a detailed sheet."""

    ws.title = "All Findings"

    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 80
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 18

    # Header row
    headers = [
        "Section", "Category", "Keyword Triggered",
        "Flagged Sentence", "Sentiment Score", "Risk Level"
    ]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        style_header_cell(cell, header)

    # Data rows
    for row_num, finding in enumerate(findings, 2):
        ws.cell(row=row_num, column=1).value = finding["section"]
        ws.cell(row=row_num, column=2).value = finding["category"]
        ws.cell(row=row_num, column=3).value = finding["keyword"]
        ws.cell(row=row_num, column=4).value = finding["sentence"]
        ws.cell(row=row_num, column=5).value = finding["sentiment_score"]

        risk_cell = ws.cell(row=row_num, column=6)
        risk_cell.value = finding["sentiment_label"]
        style_risk_cell(risk_cell, finding["sentiment_label"])

        ws.cell(row=row_num, column=4).alignment = Alignment(wrap_text=True)

        # Alternate row shading
        if row_num % 2 == 0:
            for col in range(1, 6):
                ws.cell(row=row_num, column=col).fill = PatternFill(
                    start_color="F5F5F5", end_color="F5F5F5", fill_type="solid"
                )


# -----------------------------------------------------------------------------
# EXCEL SHEET 3 -- Year-Over-Year Comparison
# -----------------------------------------------------------------------------
def write_comparison_sheet(ws, comparison):
    """Writes the year-over-year comparison to its own sheet."""

    ws.title = "Year-Over-Year"
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 25

    headers = ["Category", "Last Year", "This Year", "Change", "% Change", "Trajectory"]
    for col, header in enumerate(headers, 1):
        style_header_cell(ws.cell(row=1, column=col), header)

    for row_num, (cat, data) in enumerate(comparison["by_category"].items(), 2):
        ws.cell(row=row_num, column=1).value = cat
        ws.cell(row=row_num, column=2).value = data["previous_count"]
        ws.cell(row=row_num, column=3).value = data["current_count"]
        ws.cell(row=row_num, column=4).value = f"{data['change']:+d}"
        ws.cell(row=row_num, column=5).value = f"{data['percent_change']:+.1f}%"
        ws.cell(row=row_num, column=6).value = data["trajectory"]


# -----------------------------------------------------------------------------
# MASTER EXCEL BUILDER
# -----------------------------------------------------------------------------
def generate_excel(ticker, analysis, comparison, latest_date, previous_date):
    """Builds the complete Excel report with 3 sheets."""

    ensure_output_dir()
    print("[RedFlag] Building Excel report...")

    wb = openpyxl.Workbook()

    ws1 = wb.active
    write_summary_sheet(ws1, ticker, analysis, comparison, latest_date, previous_date)

    ws2 = wb.create_sheet()
    write_findings_sheet(ws2, analysis["findings"])

    ws3 = wb.create_sheet()
    write_comparison_sheet(ws3, comparison)

    filepath = os.path.join(OUTPUT_DIR, f"{ticker}_risk_report.xlsx")
    wb.save(filepath)
    print(f"[RedFlag] Excel report saved: {filepath}")
    return filepath


# -----------------------------------------------------------------------------
# PDF REPORT BUILDER
# One-page executive summary
# NOTE: We use only ASCII characters throughout to avoid font encoding errors
# -----------------------------------------------------------------------------
def generate_pdf(ticker, analysis, comparison, latest_date):
    """Builds a one-page PDF executive summary."""

    ensure_output_dir()
    print("[RedFlag] Building PDF summary...")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # ---- Title ----
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(
        0, 12,
        f"RedFlag Risk Report - {ticker}",
        new_x="LMARGIN", new_y="NEXT", align="C"
    )

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 6,
        f"10-K Filing Date: {latest_date}  |  "
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        new_x="LMARGIN", new_y="NEXT", align="C"
    )
    pdf.ln(5)

    # ---- Overall Trajectory ----
    overall = comparison["overall"]

    # Strip emoji from trajectory for PDF compatibility
    trajectory_clean = (
        overall["trajectory"]
        .replace("WARNING SIGN", "!")
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
    )

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 8, "Overall Risk Trajectory", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(220, 50, 50)
    pdf.cell(0, 10, trajectory_clean, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ---- Key Metrics ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 7, "Key Metrics", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)

    metrics = [
        ("Total Risk Findings This Year", str(overall["current_total"])),
        ("Total Risk Findings Last Year", str(overall["previous_total"])),
        ("Year-Over-Year Change",
         f"{overall['total_change']:+d} ({overall['percent_change']:+.1f}%)"),
        ("Sentiment Trend",
         comparison["sentiment_trend"]["sentiment_trend"]),
        ("New Risk Keywords", str(len(comparison["new_keywords"]))),
    ]

    for label, value in metrics:
        pdf.cell(110, 7, label + ":", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    pdf.ln(4)

    # ---- Category Breakdown ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 7, "Category Breakdown", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)

    for cat, data in comparison["by_category"].items():
        # Strip emoji for PDF
        traj = data["trajectory"].encode("ascii", "ignore").decode("ascii").strip()
        line = (
            f"{cat}: {data['previous_count']} -> {data['current_count']} "
            f"({data['percent_change']:+.1f}%)  {traj}"
        )
        pdf.cell(0, 7, line, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # ---- New Keywords ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(
        0, 7,
        f"New Risk Keywords This Year ({len(comparison['new_keywords'])})",
        new_x="LMARGIN", new_y="NEXT"
    )

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)

    if comparison["new_keywords"]:
        pdf.multi_cell(0, 7, ", ".join(comparison["new_keywords"]))
    else:
        pdf.cell(0, 7, "None", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # ---- Top 5 Highest Risk Sentences ----
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(26, 26, 46)
    pdf.cell(0, 7, "Top 5 Highest Risk Findings", new_x="LMARGIN", new_y="NEXT")

    top_findings = analysis["findings"][:5]
    for i, finding in enumerate(top_findings, 1):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(220, 50, 50)

        header_line = (
            f"{i}. [{finding['category']}] {finding['keyword']} "
            f"- {finding['sentiment_label']} ({finding['sentiment_score']})"
        )
        pdf.cell(0, 6, header_line, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(80, 80, 80)

        # Clean sentence -- remove non-ASCII characters for PDF safety
        sentence = finding["sentence"][:200]
        sentence = sentence.encode("ascii", "ignore").decode("ascii")
        if len(finding["sentence"]) > 200:
            sentence += "..."

        pdf.multi_cell(0, 5, sentence)
        pdf.ln(2)

    # ---- Footer ----
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(
        0, 5,
        "Generated by RedFlag - github.com/zshqv/RedFlag | "
        "Data sourced from SEC EDGAR (free public API)",
        align="C"
    )

    filepath = os.path.join(OUTPUT_DIR, f"{ticker}_summary.pdf")
    pdf.output(filepath)
    print(f"[RedFlag] PDF summary saved: {filepath}")
    return filepath


# -----------------------------------------------------------------------------
# MASTER REPORT GENERATOR
# -----------------------------------------------------------------------------
def generate_reports(ticker, analysis, comparison, latest_date, previous_date):
    """Generates both the Excel and PDF reports."""

    excel_path = generate_excel(
        ticker, analysis, comparison, latest_date, previous_date
    )
    pdf_path = generate_pdf(ticker, analysis, comparison, latest_date)

    return {"excel": excel_path, "pdf": pdf_path}


# -----------------------------------------------------------------------------
# QUICK TEST
# python report_generator.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    from edgar_fetcher import fetch_10k
    from text_parser import extract_sections
    from risk_analyzer import analyze_filings
    from comparator import compare_years

    print("[RedFlag] Running full pipeline test...\n")
    result = fetch_10k("AAPL")

    if result and result["previous"]["text"]:

        latest_sections   = extract_sections(result["latest"]["text"])
        latest_analysis   = analyze_filings(latest_sections)

        previous_sections = extract_sections(result["previous"]["text"])
        previous_analysis = analyze_filings(previous_sections)

        comparison = compare_years(latest_analysis, previous_analysis)

        paths = generate_reports(
            ticker        = result["ticker"],
            analysis      = latest_analysis,
            comparison    = comparison,
            latest_date   = result["latest"]["date"],
            previous_date = result["previous"]["date"]
        )

        print(f"\n[RedFlag] Reports generated successfully:")
        print(f"  Excel: {paths['excel']}")
        print(f"  PDF:   {paths['pdf']}")