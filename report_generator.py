# =============================================================================
# report_generator.py — HTML Report Generator (v3.0)
# =============================================================================

import os
import math
from datetime import datetime


OUTPUT_DIR = "output"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
#  Context builder (shared by template and fallback)
# ─────────────────────────────────────────────────────────────

def _build_pdf_context(ticker, analysis, comparison, latest_date, exchange, previous_date):
    findings     = analysis["findings"]
    summary      = analysis["summary"]
    high_count   = summary["by_severity"].get("HIGH", 0)
    medium_count = summary["by_severity"].get("MEDIUM", 0)
    low_count    = summary["by_severity"].get("LOW", 0)
    total        = summary["total"]
    by_category  = summary.get("by_category", {})

    if high_count > 0:
        verdict_label = "HIGH RISK"
        verdict_class = "verdict-red"
        verdict_line1 = f"{high_count} HIGH-severity flag(s) detected — immediate review required."
        verdict_line2 = "Do not proceed without resolving these items in due diligence."
    elif medium_count > 3:
        verdict_label = "MEDIUM RISK"
        verdict_class = "verdict-amber"
        verdict_line1 = f"{medium_count} MEDIUM-severity flags detected — detailed review recommended."
        verdict_line2 = "Each flag should be traced to source documents and management commentary."
    else:
        verdict_label = "LOW RISK"
        verdict_class = "verdict-green"
        verdict_line1 = f"Minimal findings ({total} total). Standard due diligence sufficient."
        verdict_line2 = "No high-priority items requiring escalation at this time."

    avg_sev = 0
    if total > 0:
        avg_sev = round(sum(f.get("severity_score", 50) for f in findings) / total)

    overall  = comparison.get("overall", {})
    cat_grid = comparison.get("by_category", {})
    new_kws  = comparison.get("new_keywords", [])

    max_cat_count = max((v.get("current_count", 0) for v in cat_grid.values()), default=1)
    if max_cat_count == 0:
        max_cat_count = 1

    medium_findings = [f for f in findings if f["severity"] == "MEDIUM"]
    medium_split    = math.ceil(len(medium_findings) / 2) if medium_findings else 0
    medium_first    = medium_findings[:medium_split]
    medium_second   = medium_findings[medium_split:]

    filing_year = str(latest_date)[:4] if latest_date else "N/A"

    dominant_category = max(by_category, key=by_category.get) if by_category else "Operational"
    traj_str   = overall.get("trajectory", "stable").lower()
    top_kw     = findings[0]["keyword"] if findings else "N/A"
    first_new_kw = new_kws[0] if new_kws else "none identified"
    bottom_line = (
        f"{dominant_category} exposure has {traj_str} year-over-year, "
        f"with \"{top_kw}\" representing the highest-severity flag. "
        f"{len(new_kws)} new keyword(s) — including \"{first_new_kw}\" "
        f"— suggest a changing disclosure posture not present in the prior filing."
    )

    kw_to_score = {f["keyword"]: f["severity_score"] for f in findings}

    if cat_grid:
        big_cat, big_cd = max(cat_grid.items(), key=lambda x: x[1].get("change", 0))
        raise_1 = {
            "text": f"{big_cat} risk increased by {big_cd.get('change', 0)} flags year-over-year",
            "tag":  "See risk heat map",
        }
    else:
        raise_1 = {"text": "No year-over-year category data available", "tag": ""}

    if findings:
        top    = findings[0]
        raise_2 = {
            "text": f"\"{top['keyword']}\" flagged in {top['section']} (severity score {top['severity_score']})",
            "tag":  f"Page {top['page_num']}, Para {top['para_num']}",
        }
    else:
        raise_2 = {"text": "No findings identified", "tag": ""}

    if new_kws:
        top_new = max(new_kws, key=lambda k: kw_to_score.get(k, 0))
        raise_3 = {
            "text": f"New keyword \"{top_new}\" (score {kw_to_score.get(top_new, 0)}) — absent in prior filing",
            "tag":  "Absent in prior filing",
        }
    else:
        raise_3 = {"text": "No new keywords identified in this filing", "tag": ""}

    return {
        "ticker":           ticker,
        "company_name":     ticker,
        "doc_type":         "10-K / Annual Report",
        "exchange":         exchange,
        "filing_date":      str(latest_date or "N/A"),
        "filing_year":      filing_year,
        "previous_date":    str(previous_date or "N/A"),
        "generated_date":   datetime.now().strftime("%Y-%m-%d"),
        "verdict_label":    verdict_label,
        "verdict_class":    verdict_class,
        "verdict_line1":    verdict_line1,
        "verdict_line2":    verdict_line2,
        "bottom_line":      bottom_line,
        "three_to_raise":   [raise_1, raise_2, raise_3],
        "total_findings":   total,
        "high_count":       high_count,
        "medium_count":     medium_count,
        "low_count":        low_count,
        "avg_severity":     avg_sev,
        "avg_sentiment":    summary.get("avg_sentiment", 0.0),
        "sections_scanned": summary.get("sections_with_flags", []),
        "high_findings":    [f for f in findings if f["severity"] == "HIGH"],
        "medium_findings":  medium_findings,
        "medium_first":     medium_first,
        "medium_second":    medium_second,
        "low_findings":     [f for f in findings if f["severity"] == "LOW"],
        "has_previous":     bool(previous_date),
        "category_grid":    cat_grid,
        "max_cat_count":    max_cat_count,
        "new_keywords":     new_kws,
        "sentiment_trend":  comparison.get("sentiment_trend", {}),
        "overall":          overall,
        "trajectory":       overall.get("trajectory", "STABLE"),
        "by_category":      by_category,
    }


# ─────────────────────────────────────────────────────────────
#  Fallback HTML (when pdf_template.html is unavailable)
# ─────────────────────────────────────────────────────────────

def _build_fallback_html(ctx):
    sev_bg = {
        "HIGH RISK":   "#E24B4A",
        "MEDIUM RISK": "#EF9F27",
        "LOW RISK":    "#3B6D11",
    }.get(ctx["verdict_label"], "#1a1a2e")

    rows = []
    for f in ctx["high_findings"] + ctx["medium_findings"] + ctx["low_findings"]:
        row_bg = {"HIGH": "#FFCCCC", "MEDIUM": "#FFF3CC", "LOW": "#E6FFE6"}.get(f["severity"], "#fff")
        sent   = str(f.get("flagged_sentence", ""))[:200]
        rows.append(
            f"<tr style='background:{row_bg}'>"
            f"<td>{f.get('section','')}</td>"
            f"<td><strong>{f.get('keyword','')}</strong></td>"
            f"<td>{f.get('severity','')}</td>"
            f"<td>{f.get('severity_score',0)}</td>"
            f"<td>{sent}</td>"
            f"</tr>"
        )

    cat_rows = "".join(
        f"<tr><td>{cat}</td><td>{count}</td></tr>"
        for cat, count in ctx["by_category"].items()
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RedFlag — {ctx['ticker']}</title>
<style>
  body{{font-family:Helvetica,Arial,sans-serif;margin:0;color:#222;}}
  header{{background:#1a1a2e;color:#fff;padding:20px 32px;}}
  header h1{{margin:0;font-size:22px;}}
  header p{{margin:4px 0 0;opacity:.7;font-size:12px;}}
  .verdict{{background:{sev_bg};color:#fff;padding:10px 32px;font-weight:bold;font-size:15px;}}
  .metrics{{display:flex;gap:12px;padding:18px 32px;background:#f5f5f5;flex-wrap:wrap;}}
  .metric{{background:#fff;border-radius:4px;padding:10px 18px;text-align:center;min-width:90px;}}
  .metric .val{{font-size:26px;font-weight:bold;color:#1a1a2e;}}
  .metric .lbl{{font-size:10px;color:#666;margin-top:2px;}}
  main{{padding:22px 32px;}}
  h2{{color:#1a1a2e;border-bottom:2px solid #1a1a2e;padding-bottom:5px;font-size:16px;}}
  table{{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px;}}
  th{{background:#1a1a2e;color:#fff;padding:7px 8px;text-align:left;}}
  td{{padding:6px 8px;border-bottom:1px solid #ddd;vertical-align:top;}}
  footer{{background:#1a1a2e;color:#888;padding:10px 32px;font-size:10px;margin-top:28px;}}
</style>
</head>
<body>
<header>
  <h1>RedFlag Risk Report — {ctx['ticker']}</h1>
  <p>{ctx['exchange']} &nbsp;|&nbsp; Filing: {ctx['filing_date']} &nbsp;|&nbsp; Generated: {ctx['generated_date']}</p>
</header>
<div class="verdict">{ctx['verdict_label']} — {ctx['verdict_line1']}</div>
<div class="metrics">
  <div class="metric"><div class="val">{ctx['total_findings']}</div><div class="lbl">Total</div></div>
  <div class="metric"><div class="val" style="color:#E24B4A">{ctx['high_count']}</div><div class="lbl">HIGH</div></div>
  <div class="metric"><div class="val" style="color:#EF9F27">{ctx['medium_count']}</div><div class="lbl">MEDIUM</div></div>
  <div class="metric"><div class="val" style="color:#3B6D11">{ctx['low_count']}</div><div class="lbl">LOW</div></div>
  <div class="metric"><div class="val">{len(ctx['new_keywords'])}</div><div class="lbl">New Keywords</div></div>
  <div class="metric"><div class="val">{ctx['avg_sentiment']:.3f}</div><div class="lbl">Avg Sentiment</div></div>
</div>
<main>
  <h2>All Findings</h2>
  <table>
    <thead><tr><th>Section</th><th>Keyword</th><th>Severity</th><th>Score</th><th>Flagged Sentence</th></tr></thead>
    <tbody>{''.join(rows) if rows else '<tr><td colspan="5" style="text-align:center;color:#999">No findings identified.</td></tr>'}</tbody>
  </table>
  <h2 style="margin-top:28px">Risk by Category</h2>
  <table style="max-width:320px">
    <thead><tr><th>Category</th><th>Count</th></tr></thead>
    <tbody>{cat_rows if cat_rows else '<tr><td colspan="2">No data</td></tr>'}</tbody>
  </table>
</main>
<footer>RedFlag · github.com/zshqv/RedFlag · Not financial advice.</footer>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
#  HTML report
# ─────────────────────────────────────────────────────────────

def generate_html_report(ticker, analysis, comparison, latest_date, exchange, previous_date):
    ensure_output_dir()
    html_path    = os.path.join(OUTPUT_DIR, f"{ticker}_report.html")
    ctx          = _build_pdf_context(ticker, analysis, comparison, latest_date, exchange, previous_date)
    html_str = _build_fallback_html(ctx)

    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html_str)
    print(f"[RedFlag] HTML report saved: {html_path}")
    return html_path


# ─────────────────────────────────────────────────────────────
#  Master
# ─────────────────────────────────────────────────────────────

def generate_reports(ticker, analysis, comparison, latest_date, previous_date, exchange):
    """Generates the HTML report. Returns {"html": path}."""
    html_path = generate_html_report(
        ticker, analysis, comparison, latest_date, exchange, previous_date
    )
    return {"html": html_path}
