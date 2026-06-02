# =============================================================================
# report_generator.py — Excel & PDF Report Builder
# v2 — WeasyPrint/Jinja2 PDF, location metadata, severity scoring, heatmap
# =============================================================================

import os
import warnings
import re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import CellIsRule
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

OUTPUT_DIR = "output"

COLORS = {
    "HIGH RISK":     "FF4444",
    "ELEVATED RISK": "FF8C00",
    "NEUTRAL":       "FFD700",
    "LOW RISK":      "90EE90",
    "header":        "1a1a2e",
    "subheader":     "16213e",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def sanitize_text(text):
    """Replace non-ASCII characters to prevent WeasyPrint encoding crashes."""
    if not isinstance(text, str):
        return str(text)
    return text.encode("ascii", "replace").decode("ascii").replace("?", " ").strip()


def style_header_cell(cell, text, font_size=11, bold=True, color="header"):
    cell.value = text
    cell.font  = Font(name="Calibri", size=font_size, bold=bold, color="FFFFFF")
    cell.fill  = PatternFill(start_color=COLORS[color], end_color=COLORS[color], fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_risk_cell(cell, sentiment_label):
    color = COLORS.get(sentiment_label, "FFFFFF")
    cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    cell.font = Font(name="Calibri", size=9, bold=True)
    cell.alignment = Alignment(horizontal="center", vertical="center")


def severity_color(score):
    """Returns an RGB hex string for a 0-100 severity score."""
    if score >= 70:
        return "FF4444"
    elif score >= 40:
        return "FF8C00"
    else:
        return "90EE90"


# ─── Excel Sheet 1 — Executive Summary ────────────────────────────────────────

def write_summary_sheet(ws, ticker, analysis, comparison, latest_date, previous_date):
    ws.title = "Executive Summary"
    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 25

    row = 1
    ws.merge_cells(f"A{row}:B{row}")
    style_header_cell(ws[f"A{row}"], f"RedFlag Risk Report - {ticker}", font_size=14)
    row += 1

    ws.merge_cells(f"A{row}:B{row}")
    style_header_cell(
        ws[f"A{row}"],
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        font_size=9, bold=False, color="subheader"
    )
    row += 2

    style_header_cell(ws[f"A{row}"], "Latest 10-K Filing Date", color="subheader")
    ws[f"B{row}"] = latest_date
    row += 1

    style_header_cell(ws[f"A{row}"], "Previous 10-K Filing Date", color="subheader")
    ws[f"B{row}"] = previous_date or "N/A"
    row += 2

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

    style_header_cell(
        ws[f"A{row}"],
        f"New Risk Keywords This Year ({len(comparison['new_keywords'])})",
        color="subheader"
    )
    ws[f"B{row}"] = ", ".join(comparison["new_keywords"]) if comparison["new_keywords"] else "None"
    row += 2

    ws.merge_cells(f"A{row}:B{row}")
    style_header_cell(ws[f"A{row}"], "Category Breakdown", font_size=11)
    row += 1

    for cat, data in comparison["by_category"].items():
        style_header_cell(ws[f"A{row}"], cat, color="subheader")
        traj = data["trajectory"].encode("ascii", "ignore").decode("ascii").strip()
        ws[f"B{row}"] = (
            f"{data['previous_count']} -> {data['current_count']} "
            f"({data['percent_change']:+.1f}%) {traj}"
        )
        row += 1


# ─── Excel Sheet 2 — All Findings (with new columns + formatting) ──────────────

def write_findings_sheet(ws, findings):
    ws.title = "All Findings"

    col_widths = [18, 15, 22, 70, 15, 18, 10, 12, 15, 12, 45, 45]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    headers = [
        "Section", "Category", "Keyword Triggered", "Flagged Sentence",
        "Sentiment Score", "Risk Level", "Para #", "Sentence #",
        "Severity Score", "Confidence Score", "Context Before", "Context After"
    ]
    for col, header in enumerate(headers, 1):
        style_header_cell(ws.cell(row=1, column=col), header)

    for row_num, finding in enumerate(findings, 2):
        ws.cell(row=row_num, column=1).value  = finding.get("section", "")
        ws.cell(row=row_num, column=2).value  = finding.get("category", "")
        ws.cell(row=row_num, column=3).value  = finding.get("keyword", "")
        ws.cell(row=row_num, column=4).value  = finding.get("sentence", "")
        ws.cell(row=row_num, column=5).value  = finding.get("sentiment_score", 0)
        risk_cell = ws.cell(row=row_num, column=6)
        risk_cell.value = finding.get("sentiment_label", "")
        style_risk_cell(risk_cell, finding.get("sentiment_label", ""))
        ws.cell(row=row_num, column=7).value  = finding.get("para_num", 0)
        ws.cell(row=row_num, column=8).value  = finding.get("sentence_num", 0)
        ws.cell(row=row_num, column=9).value  = finding.get("severity_score", 0)
        ws.cell(row=row_num, column=10).value = finding.get("confidence_score", 50)
        ws.cell(row=row_num, column=11).value = finding.get("context_before", "")
        ws.cell(row=row_num, column=12).value = finding.get("context_after", "")

        ws.cell(row=row_num, column=4).alignment  = Alignment(wrap_text=True)
        ws.cell(row=row_num, column=11).alignment = Alignment(wrap_text=True)
        ws.cell(row=row_num, column=12).alignment = Alignment(wrap_text=True)

        # Alternate row shading (skip col 6=Risk Level, 9=Severity, 10=Confidence)
        if row_num % 2 == 0:
            for col in [1, 2, 3, 4, 5, 7, 8, 11, 12]:
                ws.cell(row=row_num, column=col).fill = PatternFill(
                    start_color="F5F5F5", end_color="F5F5F5", fill_type="solid"
                )

    if len(findings) >= 1:
        last_row  = len(findings) + 1
        sev_range = f"I2:I{last_row}"
        con_range = f"J2:J{last_row}"

        # Conditional formatting — Severity Score (col I = 9)
        ws.conditional_formatting.add(
            sev_range,
            CellIsRule(operator="greaterThanOrEqual", formula=["70"],
                       fill=PatternFill(bgColor="FF4444"))
        )
        ws.conditional_formatting.add(
            sev_range,
            CellIsRule(operator="between", formula=["40", "69"],
                       fill=PatternFill(bgColor="FF8C00"))
        )
        ws.conditional_formatting.add(
            sev_range,
            CellIsRule(operator="lessThan", formula=["40"],
                       fill=PatternFill(bgColor="90EE90"))
        )

        # Conditional formatting — Confidence Score (col J = 10)
        ws.conditional_formatting.add(
            con_range,
            CellIsRule(operator="greaterThanOrEqual", formula=["70"],
                       fill=PatternFill(bgColor="90EE90"))
        )
        ws.conditional_formatting.add(
            con_range,
            CellIsRule(operator="between", formula=["40", "69"],
                       fill=PatternFill(bgColor="FF8C00"))
        )
        ws.conditional_formatting.add(
            con_range,
            CellIsRule(operator="lessThan", formula=["40"],
                       fill=PatternFill(bgColor="FF4444"))
        )

    # Freeze top row and enable auto-filter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:L{max(len(findings) + 1, 1)}"


# ─── Excel Sheet 3 — Year-Over-Year ───────────────────────────────────────────

def write_comparison_sheet(ws, comparison):
    ws.title = "Year-Over-Year"
    for col, w in zip("ABCDEF", [20, 18, 18, 15, 15, 25]):
        ws.column_dimensions[col].width = w

    headers = ["Category", "Last Year", "This Year", "Change", "% Change", "Trajectory"]
    for col, header in enumerate(headers, 1):
        style_header_cell(ws.cell(row=1, column=col), header)

    for row_num, (cat, data) in enumerate(comparison["by_category"].items(), 2):
        ws.cell(row=row_num, column=1).value = cat
        ws.cell(row=row_num, column=2).value = data["previous_count"]
        ws.cell(row=row_num, column=3).value = data["current_count"]
        ws.cell(row=row_num, column=4).value = f"{data['change']:+d}"
        ws.cell(row=row_num, column=5).value = f"{data['percent_change']:+.1f}%"
        traj = data["trajectory"].encode("ascii", "ignore").decode("ascii").strip()
        ws.cell(row=row_num, column=6).value = traj


# ─── Excel Sheet 4 — Risk Heatmap ─────────────────────────────────────────────

def write_heatmap_sheet(ws, findings):
    ws.title = "Risk Heatmap"

    categories = ["Financial", "Legal", "Operational", "Regulatory"]

    # Group findings by category
    by_cat = {cat: [] for cat in categories}
    for f in findings:
        cat = f.get("category", "")
        if cat in by_cat:
            by_cat[cat].append(f)

    max_findings = max((len(v) for v in by_cat.values()), default=0)

    # Header row: Finding numbers
    ws.cell(row=1, column=1).value = "Category"
    style_header_cell(ws.cell(row=1, column=1), "Category")
    for n in range(1, max_findings + 1):
        cell = ws.cell(row=1, column=n + 1)
        style_header_cell(cell, str(n), font_size=9)
        ws.column_dimensions[openpyxl.utils.get_column_letter(n + 1)].width = 16

    ws.column_dimensions["A"].width = 15

    for row_num, cat in enumerate(categories, 2):
        # Category name cell
        cat_cell = ws.cell(row=row_num, column=1)
        cat_cell.value = cat
        cat_cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        cat_cell.fill = PatternFill(start_color=COLORS["header"], end_color=COLORS["header"], fill_type="solid")
        cat_cell.alignment = Alignment(horizontal="center", vertical="center")

        for col_num, finding in enumerate(by_cat[cat], 2):
            cell = ws.cell(row=row_num, column=col_num)
            kw = finding.get("keyword", "")[:20]
            cell.value = kw
            sc = finding.get("severity_score", 50)
            color = severity_color(sc)
            cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            cell.font = Font(name="Calibri", size=8, bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.row_dimensions[1].height = 20
    for r in range(2, 6):
        ws.row_dimensions[r].height = 30

    ws.freeze_panes = "B2"


# ─── PDF helpers ──────────────────────────────────────────────────────────────

def _risk_class(sentiment_label):
    label = (sentiment_label or "").upper()
    if "HIGH" in label:
        return "high"
    elif "ELEVATED" in label:
        return "elevated"
    elif "NEUTRAL" in label:
        return "neutral"
    else:
        return "low"


def _trajectory_badge_class(trajectory):
    t = trajectory.upper()
    if "STABLE" in t or "IMPROVING" in t or "DECREASING" in t:
        return "badge-green"
    elif "DETERIORATING" in t:
        return "badge-red"
    else:
        return "badge-amber"


def _trend_arrow(trajectory):
    t = trajectory.upper()
    if "SIGNIFICANTLY IMPROVING" in t:
        return ("↓↓", "trend-down")
    elif "IMPROVING" in t:
        return ("↓", "trend-down")
    elif "STABLE" in t:
        return ("→", "trend-flat")
    elif "DETERIORATING" in t:
        return ("↑↑", "trend-up")
    elif "INCREASING" in t:
        return ("↑", "trend-up")
    return ("→", "trend-flat")


def _generate_verdict(analysis, comparison):
    summary = analysis.get("summary", {})
    findings = analysis.get("findings", [])

    top_cat = max(summary, key=summary.get) if summary else "Regulatory"
    top_count = summary.get(top_cat, 0)

    if findings:
        top_f = findings[0]  # already sorted by severity_score desc
        top_kw = sanitize_text(top_f.get("keyword", "N/A"))
        top_sev = top_f.get("severity_score", 0)
    else:
        top_kw = "N/A"
        top_sev = 0

    trend = sanitize_text(comparison["sentiment_trend"]["sentiment_trend"])

    s1 = (
        f"The {top_cat} category dominates this filing with {top_count} flagged instances, "
        "indicating elevated exposure in this area."
    )
    s2 = (
        f"The highest severity finding relates to '{top_kw}' "
        f"(severity score: {top_sev}), which warrants immediate management attention."
    )
    s3 = f"Overall language assessment: {trend}."
    return [s1, s2, s3]


def _build_category_grid(comparison, analysis):
    categories = ["Financial", "Legal", "Operational", "Regulatory"]
    grid = []
    by_cat = comparison.get("by_category", {})
    summary = analysis.get("summary", {})

    for cat in categories:
        data = by_cat.get(cat, {
            "current_count": summary.get(cat, 0),
            "previous_count": 0,
            "change": 0,
            "percent_change": 0.0,
            "trajectory": "STABLE",
        })
        arrow, tclass = _trend_arrow(data.get("trajectory", "STABLE"))
        grid.append({
            "name":          cat,
            "current_count": data.get("current_count", 0),
            "previous_count": data.get("previous_count", 0),
            "change":        data.get("change", 0),
            "trajectory":    sanitize_text(data.get("trajectory", "").encode("ascii", "ignore").decode()),
            "trend_arrow":   arrow,
            "trend_class":   tclass,
        })
    return grid


def _build_new_keywords_detail(new_keywords, findings):
    # Build a lookup: keyword → (category, severity_score)
    kw_lookup = {}
    for f in findings:
        kw = f.get("keyword", "")
        if kw not in kw_lookup:
            kw_lookup[kw] = (f.get("category", "Unknown"), f.get("severity_score", 50))

    result = []
    for kw in new_keywords:
        cat, sev = kw_lookup.get(kw, ("Unknown", 50))
        if sev >= 70:
            dot = "red"
        elif sev >= 40:
            dot = "amber"
        else:
            dot = "grey"
        result.append({
            "keyword":   sanitize_text(kw),
            "category":  cat,
            "severity":  sev,
            "dot_class": dot,
        })
    return result


def _sanitize_findings_for_html(findings):
    cleaned = []
    for f in findings:
        cleaned.append({
            "section":        sanitize_text(f.get("section", "")),
            "category":       sanitize_text(f.get("category", "")),
            "keyword":        sanitize_text(f.get("keyword", "")),
            "sentence":       sanitize_text(f.get("sentence", "")),
            "sentiment_score": f.get("sentiment_score", 0),
            "sentiment_label": sanitize_text(f.get("sentiment_label", "")),
            "severity_score": f.get("severity_score", 0),
            "para_num":       f.get("para_num", 0),
            "sentence_num":   f.get("sentence_num", 0),
            "context_before": sanitize_text(f.get("context_before", "")),
            "context_after":  sanitize_text(f.get("context_after", "")),
            "risk_class":     _risk_class(f.get("sentiment_label", "")),
        })
    return cleaned


# ─── PDF Render (WeasyPrint → xhtml2pdf fallback) ─────────────────────────────

def _render_pdf(html_content, filepath):
    """
    Renders HTML to PDF.
    Tries WeasyPrint first (best quality); falls back to xhtml2pdf if GTK is unavailable.
    """
    # Attempt WeasyPrint
    try:
        from weasyprint import HTML as WP_HTML
        WP_HTML(string=html_content).write_pdf(filepath)
        print("[RedFlag] PDF rendered via WeasyPrint.")
        return
    except Exception as wp_err:
        print(f"[RedFlag] WeasyPrint unavailable ({type(wp_err).__name__}). Falling back to xhtml2pdf...")

    # Fallback: xhtml2pdf (pure Python, no system dependencies)
    try:
        from xhtml2pdf import pisa
        with open(filepath, "wb") as f:
            status = pisa.CreatePDF(html_content, dest=f)
        if status.err:
            print(f"[RedFlag] WARNING: xhtml2pdf reported errors (check output).")
        else:
            print("[RedFlag] PDF rendered via xhtml2pdf.")
        return
    except Exception as xp_err:
        print(f"[RedFlag] ERROR: xhtml2pdf also failed: {xp_err}")
        print("[RedFlag] Install WeasyPrint GTK runtime or xhtml2pdf to enable PDF output.")
        # Write a placeholder text file instead of crashing the pipeline
        with open(filepath.replace(".pdf", "_PDF_UNAVAILABLE.txt"), "w") as f:
            f.write(
                "PDF generation failed.\n"
                "Install WeasyPrint (requires GTK on Windows) or xhtml2pdf:\n"
                "  pip install xhtml2pdf\n"
                "For WeasyPrint on Windows, see:\n"
                "  https://doc.courtbouillon.org/weasyprint/stable/first_steps.html\n"
            )


# ─── PDF Generator ────────────────────────────────────────────────────────────

def generate_pdf(ticker, analysis, comparison, latest_date, exchange="NYSE/NASDAQ",
                 previous_date=None):
    """Builds a 4-page CFO-ready PDF using Jinja2 + WeasyPrint (xhtml2pdf fallback)."""
    import jinja2

    ensure_output_dir()
    print("[RedFlag] Building PDF report (Jinja2 + HTML)...")

    findings = analysis.get("findings", [])
    has_previous = previous_date is not None and previous_date != "N/A"

    # Sanitize findings for HTML output
    clean_findings = _sanitize_findings_for_html(findings)

    # Build template context
    trajectory_raw = comparison["overall"].get("trajectory", "STABLE")
    trajectory_clean = sanitize_text(
        trajectory_raw.encode("ascii", "ignore").decode("ascii").strip()
    )
    avg_severity = (
        round(sum(f.get("severity_score", 50) for f in findings) / len(findings))
        if findings else 0
    )

    # Group findings by category
    categories = ["Financial", "Legal", "Operational", "Regulatory"]
    findings_by_category = {cat: [] for cat in categories}
    for f in clean_findings:
        cat = f.get("category", "")
        if cat in findings_by_category:
            findings_by_category[cat].append(f)

    context = {
        "ticker":               sanitize_text(ticker),
        "exchange":             sanitize_text(exchange),
        "filing_date":          sanitize_text(str(latest_date)),
        "generated_date":       datetime.now().strftime("%B %d, %Y"),
        "trajectory_clean":     trajectory_clean,
        "trajectory_badge_class": _trajectory_badge_class(trajectory_raw),
        "verdict":              _generate_verdict(analysis, comparison),
        "total_findings":       len(findings),
        "avg_severity":         avg_severity,
        "new_keywords":         _build_new_keywords_detail(
                                    comparison.get("new_keywords", []), findings),
        "category_grid":        _build_category_grid(comparison, analysis),
        "top5_findings":        clean_findings[:5],
        "findings_by_category": findings_by_category,
        "has_previous":         has_previous,
    }

    template_dir  = os.path.dirname(os.path.abspath(__file__))
    jinja_env     = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        autoescape=True
    )
    template      = jinja_env.get_template("pdf_template.html")
    html_content  = template.render(**context)

    filepath = os.path.join(OUTPUT_DIR, f"{ticker}_summary.pdf")
    _render_pdf(html_content, filepath)
    print(f"[RedFlag] PDF report saved: {filepath}")
    return filepath


# ─── Master Excel Builder ─────────────────────────────────────────────────────

def generate_excel(ticker, analysis, comparison, latest_date, previous_date):
    ensure_output_dir()
    print("[RedFlag] Building Excel report...")

    wb  = openpyxl.Workbook()
    ws1 = wb.active
    write_summary_sheet(ws1, ticker, analysis, comparison, latest_date, previous_date)

    ws2 = wb.create_sheet()
    write_findings_sheet(ws2, analysis["findings"])

    ws3 = wb.create_sheet()
    write_comparison_sheet(ws3, comparison)

    ws4 = wb.create_sheet()
    write_heatmap_sheet(ws4, analysis["findings"])

    filepath = os.path.join(OUTPUT_DIR, f"{ticker}_risk_report.xlsx")
    wb.save(filepath)
    print(f"[RedFlag] Excel report saved: {filepath}")
    return filepath


# ─── Peer Comparison — Excel ──────────────────────────────────────────────────

def generate_comparison_excel(tickers, results_list):
    ensure_output_dir()
    print("[RedFlag] Building peer comparison Excel...")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Peer Comparison"

    col_widths = [14, 18, 18, 20, 20, 15, 18, 28, 20]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    headers = [
        "Company", "Total Findings", "Financial Count", "Regulatory Count",
        "Operational Count", "Legal Count", "Avg Severity Score",
        "Trajectory", "New Keywords Count"
    ]
    for col, header in enumerate(headers, 1):
        style_header_cell(ws.cell(row=1, column=col), header)

    data_rows = []
    for r in results_list:
        analysis   = r["analysis"]
        comparison = r["comparison"]
        findings   = analysis.get("findings", [])
        summary    = analysis.get("summary", {})
        avg_sev = (
            round(sum(f.get("severity_score", 50) for f in findings) / len(findings))
            if findings else 0
        )
        traj = comparison["overall"].get("trajectory", "STABLE")
        traj_clean = traj.encode("ascii", "ignore").decode("ascii").strip()

        data_rows.append([
            r["ticker"],
            len(findings),
            summary.get("Financial", 0),
            summary.get("Regulatory", 0),
            summary.get("Operational", 0),
            summary.get("Legal", 0),
            avg_sev,
            traj_clean,
            len(comparison.get("new_keywords", [])),
        ])

    for row_num, row in enumerate(data_rows, 2):
        for col, val in enumerate(row, 1):
            ws.cell(row=row_num, column=col).value = val

    # Color worst→red, best→green for numeric columns
    numeric_col_indices = [2, 3, 4, 5, 6, 7, 9]  # higher = worse
    for col_idx in numeric_col_indices:
        values = [
            data_rows[i][col_idx - 1]
            for i in range(len(data_rows))
            if isinstance(data_rows[i][col_idx - 1], (int, float))
        ]
        if not values or len(set(values)) < 2:
            continue
        min_v = min(values)
        max_v = max(values)
        for row_num in range(2, len(data_rows) + 2):
            cell = ws.cell(row=row_num, column=col_idx)
            if isinstance(cell.value, (int, float)):
                ratio = (cell.value - min_v) / (max_v - min_v)
                r_val = min(255, int(255 * ratio))
                g_val = min(255, int(255 * (1 - ratio)))
                hex_color = f"{r_val:02X}{g_val:02X}00"
                cell.fill = PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:I{len(data_rows) + 1}"

    filename = f"COMPARISON_{'_'.join(tickers)}.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    wb.save(filepath)
    print(f"[RedFlag] Comparison Excel saved: {filepath}")
    return filepath


# ─── Peer Comparison — PDF ────────────────────────────────────────────────────

def generate_comparison_pdf(tickers, results_list):
    ensure_output_dir()
    print("[RedFlag] Building peer comparison PDF...")

    # Build ranked list by avg severity score
    ranked = []
    for r in results_list:
        findings = r["analysis"].get("findings", [])
        avg_sev = (
            round(sum(f.get("severity_score", 50) for f in findings) / len(findings))
            if findings else 0
        )
        traj = r["comparison"]["overall"].get("trajectory", "STABLE")
        traj_clean = traj.encode("ascii", "ignore").decode("ascii").strip()
        total = len(findings)
        new_kw = len(r["comparison"].get("new_keywords", []))

        # One-sentence note
        summary = r["analysis"].get("summary", {})
        top_cat = max(summary, key=summary.get) if summary else "Risk"
        note = (
            f"{r['ticker']} shows {total} total findings led by {top_cat} risks "
            f"with avg severity {avg_sev} and {new_kw} new keyword(s)."
        )
        ranked.append({
            "ticker":   sanitize_text(r["ticker"]),
            "avg_sev":  avg_sev,
            "total":    total,
            "traj":     sanitize_text(traj_clean),
            "new_kw":   new_kw,
            "note":     sanitize_text(note),
        })

    ranked.sort(key=lambda x: x["avg_sev"], reverse=True)

    rows_html = ""
    for rank, item in enumerate(ranked, 1):
        sev_color = "#e94560" if item["avg_sev"] >= 70 else "#e67e22" if item["avg_sev"] >= 40 else "#27ae60"
        rows_html += f"""
        <tr>
          <td style='font-weight:bold;'>{rank}</td>
          <td style='font-weight:bold;font-size:11pt;'>{item['ticker']}</td>
          <td>{item['total']}</td>
          <td style='font-weight:bold;color:{sev_color};'>{item['avg_sev']}</td>
          <td>{item['traj']}</td>
          <td>{item['new_kw']}</td>
          <td style='font-size:8pt;color:#555;'>{item['note']}</td>
        </tr>"""

    tickers_str = sanitize_text("_".join(tickers))
    html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'/>
    <style>
      @page {{ size: A4 landscape; margin: 15mm; }}
      body {{ font-family: Arial, sans-serif; font-size: 9pt; color: #1a1a2e; }}
      h1 {{ font-size: 18pt; color: #1a1a2e; margin-bottom: 3mm; }}
      .sub {{ font-size: 9pt; color: #888; margin-bottom: 6mm; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th {{ background: #1a1a2e; color: white; padding: 3mm 4mm; text-align: left; font-size: 9pt; }}
      td {{ padding: 2.5mm 4mm; border-bottom: 1px solid #eee; vertical-align: top; }}
      tr:nth-child(even) td {{ background: #f8f8fc; }}
      .footer {{ position: fixed; bottom: 5mm; width: 100%; text-align: center;
                 font-size: 7pt; color: #aaa; }}
    </style></head>
    <body>
      <h1>RedFlag — Peer Comparison</h1>
      <div class='sub'>
        Companies: {sanitize_text(', '.join(tickers))} &nbsp;&bull;&nbsp;
        Generated: {datetime.now().strftime('%B %d, %Y')} &nbsp;&bull;&nbsp;
        Ranked by Average Severity Score (highest = most risk)
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Company</th><th>Total Findings</th>
            <th>Avg Severity</th><th>Trajectory</th>
            <th>New Keywords</th><th>Summary Note</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
      <div class='footer'>
        RedFlag &nbsp;&bull;&nbsp; SEC EDGAR public data &nbsp;&bull;&nbsp;
        github.com/zshqv/RedFlag
      </div>
    </body></html>"""

    filename = f"COMPARISON_{tickers_str}_summary.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    _render_pdf(html, filepath)
    print(f"[RedFlag] Comparison PDF saved: {filepath}")
    return filepath


# ─── Master Report Generator ──────────────────────────────────────────────────

def generate_reports(ticker, analysis, comparison, latest_date, previous_date,
                     exchange="NYSE/NASDAQ"):
    excel_path = generate_excel(ticker, analysis, comparison, latest_date, previous_date)
    pdf_path   = generate_pdf(
        ticker, analysis, comparison, latest_date,
        exchange=exchange, previous_date=previous_date
    )
    return {"excel": excel_path, "pdf": pdf_path}


# ─── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from fetchers.edgar_fetcher import fetch_10k
    from text_parser import extract_sections
    from risk_analyzer import analyze_filings
    from comparator import compare_years

    print("[RedFlag] Running full pipeline test...\n")
    result = fetch_10k("AAPL")

    if result:
        latest_sections   = extract_sections(result["latest"]["text"])
        latest_analysis   = analyze_filings(latest_sections)

        if result["previous"]["text"]:
            previous_sections = extract_sections(result["previous"]["text"])
            previous_analysis = analyze_filings(previous_sections)
        else:
            previous_analysis = {"findings": [], "summary": {}}

        comparison = compare_years(latest_analysis, previous_analysis)

        paths = generate_reports(
            ticker        = result["ticker"],
            analysis      = latest_analysis,
            comparison    = comparison,
            latest_date   = result["latest"]["date"],
            previous_date = result["previous"]["date"],
            exchange      = result.get("exchange", "NYSE/NASDAQ")
        )
        print(f"\n  Excel: {paths['excel']}")
        print(f"  PDF:   {paths['pdf']}")
