# =============================================================================
# report_generator.py — HTML Report Generator (v2.0 Sony-style layout)
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
    traj_str     = overall.get("trajectory", "stable").lower()
    top_kw       = findings[0]["keyword"] if findings else "N/A"
    first_new_kw = new_kws[0] if new_kws else "none identified"
    bottom_line  = (
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
        top     = findings[0]
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
#  Static CSS — v2 Sony-style
# ─────────────────────────────────────────────────────────────

_V2_CSS = """\
<style>
    @page { size: A4; margin: 18mm 15mm; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt; color: #222; background: white; line-height: 1.5; }

    .page { page-break-before: always; padding-bottom: 20px; }
    .page-first { page-break-before: avoid; }

    /* Cover header */
    .cover-header {
        background: #1a1a2e;
        margin-top: -18mm;
        margin-left: -15mm;
        margin-right: -15mm;
        padding: calc(18mm + 16px) calc(15mm + 12px) 20px;
    }
    .cover-header-inner { position: relative; }
    .cover-topright { position: absolute; top: 0; right: 0; text-align: right; font-size: 9pt; color: #9999bb; line-height: 1.6; }
    .cover-company { font-size: 28pt; font-weight: 500; color: #ffffff; margin-bottom: 5px; }
    .cover-meta { font-size: 11pt; color: #9999bb; margin-bottom: 12px; }

    /* Verdict pill */
    .verdict-pill { display: inline-block; padding: 5px 16px; border-radius: 3px; font-weight: bold; font-size: 13pt; color: #ffffff; }
    .verdict-red   { background: #E24B4A; }
    .verdict-amber { background: #EF9F27; }
    .verdict-green { background: #3B6D11; }

    /* 6-cell stat grid */
    .stat-grid { width: 100%; border-collapse: collapse; margin: 14px 0; }
    .stat-grid td { border: 1px solid #ddd; padding: 10px 8px; text-align: center; vertical-align: top; width: 16.6%; }
    .stat-num { font-size: 22pt; font-weight: bold; color: #1a1a2e; line-height: 1.2; }
    .stat-num.red   { color: #E24B4A; }
    .stat-num.amber { color: #EF9F27; }
    .stat-num.green { color: #3B6D11; }
    .stat-label { font-size: 8pt; color: #666; margin-top: 3px; }
    .stat-delta { font-size: 9pt; color: #888; }

    /* Bottom line box */
    .bottom-line-box {
        border-left: 3px solid #1a1a2e;
        background: #f5f5f5;
        padding: 12px 16px;
        margin-top: 14px;
        font-size: 13pt;
        line-height: 1.6;
        color: #333;
    }

    /* Page footer */
    .page-footer { text-align: right; font-size: 9pt; color: #999; margin-top: 18px; }

    /* Section title */
    .section-title {
        font-size: 14pt;
        font-weight: 500;
        color: #1a1a2e;
        border-bottom: 2px solid #1a1a2e;
        padding-bottom: 5px;
        margin-bottom: 14px;
    }
    .section-subtitle { font-size: 10pt; color: #666; margin-bottom: 12px; margin-top: -10px; }

    /* Heat map bars */
    .heatmap-table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
    .heatmap-table td { padding: 3px 6px; vertical-align: middle; }
    .hm-label { font-size: 10pt; color: #333; width: 28%; }
    .hm-bar-cell { width: 48%; }
    .hm-bar-bg { background: #eeeeee; height: 16px; width: 100%; }
    .hm-bar { height: 16px; }
    .hm-count { font-size: 10pt; font-weight: bold; text-align: center; width: 8%; }
    .hm-delta { font-size: 11pt; text-align: center; width: 8%; font-weight: bold; }

    /* Tier chips */
    .tier-chip { display: inline-block; padding: 4px 12px; font-weight: bold; font-size: 10pt; color: #ffffff; margin-right: 6px; }
    .chip-red   { background: #E24B4A; }
    .chip-amber { background: #EF9F27; }
    .chip-green { background: #3B6D11; }

    /* Section divider */
    .divider { padding: 6px 12px; margin: 14px 0 8px; font-weight: bold; font-size: 12pt; color: white; }
    .div-navy  { background: #1a1a2e; }
    .div-red   { background: #E24B4A; border-left: 4px solid #a83331; }
    .div-amber { background: #EF9F27; border-left: 4px solid #a36e1b; }
    .div-green { background: #3B6D11; border-left: 4px solid #254809; }

    /* Finding cards */
    .card { margin: 8px 0; page-break-inside: avoid; }
    .card-header { padding: 5px 10px; font-size: 9pt; font-weight: bold; color: #ffffff; }
    .card-header.high   { background: #E24B4A; }
    .card-header.medium { background: #EF9F27; }
    .card-header.low    { background: #3B6D11; }
    .kw-pill { display: inline-block; background: rgba(255,255,255,0.25); padding: 1px 7px; border-radius: 2px; margin-left: 8px; font-size: 8pt; }

    .ctx-block { border-left: 3px solid #cccccc; padding: 4px 8px; margin: 3px 0; font-style: italic; color: #888888; font-size: 9pt; }

    .flagged-high   { background: #fff5f5; border-left: 3px solid #E24B4A; padding: 6px 10px; margin: 3px 0; font-size: 11pt; }
    .flagged-medium { background: #fffbf0; border-left: 3px solid #EF9F27; padding: 6px 10px; margin: 3px 0; font-size: 11pt; }
    .flagged-low    { background: #f4faf4; border-left: 3px solid #3B6D11; padding: 6px 10px; margin: 3px 0; font-size: 11pt; }

    .why-box { background: #f5f5f5; padding: 8px 12px; margin: 3px 0; font-size: 11pt; line-height: 1.6; color: #333333; }

    /* New keyword cards */
    .kw-card { border-left: 3px solid #1a1a2e; padding: 8px 12px; margin: 6px 0; background: #fafafa; page-break-inside: avoid; }
    .kw-card-name { font-size: 12pt; font-weight: bold; color: #1a1a2e; }
    .sev-score { display: inline-block; font-size: 9pt; color: #666; margin-left: 8px; }
    .kw-desc { font-size: 10pt; color: #555; margin-top: 4px; line-height: 1.5; }
    .dot-legend { font-size: 9pt; color: #666; margin-top: 12px; }
    .dot-high { color: #E24B4A; }
    .dot-mid  { color: #EF9F27; }
    .dot-low  { color: #3B6D11; }

    /* Dashboard */
    .dash-title { font-size: 16pt; font-weight: bold; color: #1a1a2e; text-align: center; margin-bottom: 14px; }
    .dash-rule  { border: none; border-top: 1px solid #cccccc; margin: 14px 0; }
    .three-raise-item { margin: 10px 0; page-break-inside: avoid; }
    .raise-num  { font-size: 14pt; font-weight: bold; color: #1a1a2e; margin-right: 6px; }
    .raise-text { font-size: 13pt; color: #222; line-height: 1.5; }
    .raise-tag  { display: inline-block; font-size: 9pt; color: #888; background: #f0f0f0; padding: 2px 8px; margin-top: 3px; }

    /* Source table */
    .source-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10pt; }
    .source-table td { padding: 6px 10px; border-bottom: 1px solid #eeeeee; vertical-align: top; }
    .source-table td.lbl { font-size: 10pt; color: #999999; width: 38%; background: #fafafa; }
    .source-table td.val { font-size: 12pt; color: #222; }

    .full-disclaimer { font-size: 9pt; color: #888888; margin-top: 16px; line-height: 1.6; background: #f5f5f5; padding: 10px 12px; }
    .low-note { font-size: 9pt; color: #888; font-style: italic; margin: 6px 0 10px; }

    .yoy-table { width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 10pt; }
    .yoy-table th { background: #1a1a2e; color: white; padding: 5px 8px; text-align: left; }
    .yoy-table td { padding: 5px 8px; border-bottom: 1px solid #eeeeee; }
</style>"""


# ─────────────────────────────────────────────────────────────
#  Fallback HTML — v2 Sony-style layout
# ─────────────────────────────────────────────────────────────

def _build_fallback_html(ctx):
    all_findings = ctx["high_findings"] + ctx["medium_findings"] + ctx["low_findings"]
    kw_to_score  = {f["keyword"]: f.get("severity_score", 50) for f in all_findings}
    max_bc       = max(ctx["by_category"].values()) if ctx["by_category"] else 1

    # ── helpers ──────────────────────────────────────────────

    def _card(f):
        sev     = f.get("severity", "LOW").lower()
        kw      = f.get("keyword", "")
        section = f.get("section", "")
        pg      = f.get("page_num", "")
        para    = f.get("para_num", "")
        sent    = f.get("sent_num", f.get("sentence_num", ""))
        cb      = str(f.get("context_before", "") or "")
        ca      = str(f.get("context_after",  "") or "")
        flag    = str(f.get("flagged_sentence", "") or "")
        why     = str(f.get("explanation", "") or f.get("why", "") or "")
        h = []
        h.append('<div class="card">')
        h.append(
            f'<div class="card-header {sev}">'
            f'{section} &nbsp;&middot;&nbsp; Page {pg} &nbsp;&middot;&nbsp; Para {para} &nbsp;&middot;&nbsp; Sent {sent}'
            f'<span class="kw-pill">{kw}</span></div>'
        )
        if cb:
            snippet = cb[:250] + ("..." if len(cb) > 250 else "")
            h.append(f'<div class="ctx-block">{snippet}</div>')
        h.append(f'<div class="flagged-{sev}">{flag}</div>')
        if ca:
            snippet2 = ca[:250] + ("..." if len(ca) > 250 else "")
            h.append(f'<div class="ctx-block">{snippet2}</div>')
        if why:
            h.append(f'<div class="why-box"><strong>Why this matters:</strong> {why}</div>')
        h.append('</div>')
        return "\n".join(h)

    def _hm_row(cat, count):
        cd  = ctx["category_grid"].get(cat, {})
        chg = cd.get("change", 0)
        pct = round(count / max_bc * 100) if max_bc else 0
        if chg > 0:
            col, arr = "#E24B4A", "&#8593;"
        elif chg < 0:
            col, arr = "#3B6D11", "&#8595;"
        else:
            col, arr = "#EF9F27", "&#8594;"
        return (
            f'<table class="heatmap-table"><tr>'
            f'<td class="hm-label">{cat}</td>'
            f'<td class="hm-bar-cell"><div class="hm-bar-bg">'
            f'<div class="hm-bar" style="background:{col};width:{pct}%;"></div>'
            f'</div></td>'
            f'<td class="hm-count">{count}</td>'
            f'<td class="hm-delta" style="color:{col};">{arr}</td>'
            f'</tr></table>'
        )

    def _kw_card(kw):
        score = kw_to_score.get(kw, 50)
        if score >= 70:
            dot_col, dot_lbl = "#E24B4A", "high severity"
        elif score >= 40:
            dot_col, dot_lbl = "#EF9F27", "elevated"
        else:
            dot_col, dot_lbl = "#3B6D11", "lower"
        return (
            f'<div class="kw-card"><div>'
            f'<span class="kw-card-name">{kw}</span>'
            f'<span class="sev-score">score {score}</span>'
            f'<span style="color:{dot_col};font-size:9pt;">&#9679; {dot_lbl}</span>'
            f'</div><div class="kw-desc">First appearance in this filing &#8212; absent from prior year &#8212; '
            f'signals a new or escalating risk disclosure area worth monitoring.</div></div>'
        )

    # ── computed blocks ───────────────────────────────────────

    reg_count   = ctx["by_category"].get("Regulatory", "&#8212;")
    legal_count = ctx["by_category"].get("Legal", "&#8212;")

    stat_cover = (
        '<table class="stat-grid"><tr>'
        f'<td><div class="stat-num">{ctx["total_findings"]}</div><div class="stat-label">Total flags</div></td>'
        f'<td><div class="stat-num red">{ctx["high_count"]}</div><div class="stat-label">High severity</div></td>'
        f'<td><div class="stat-num">{len(ctx["new_keywords"])}</div><div class="stat-label">New keywords</div></td>'
        f'<td><div class="stat-num amber">{reg_count}</div><div class="stat-label">Regulatory flags</div></td>'
        f'<td><div class="stat-num amber">{legal_count}</div><div class="stat-label">Legal flags</div></td>'
        f'<td><div class="stat-num green">{ctx["avg_sentiment"]:.3f}</div><div class="stat-label">Avg sentiment</div></td>'
        '</tr></table>'
    )

    stat_dash = (
        '<table class="stat-grid"><tr>'
        f'<td><div class="stat-num">{ctx["total_findings"]}</div><div class="stat-label">Total flags</div></td>'
        f'<td><div class="stat-num red">{ctx["high_count"]}</div><div class="stat-label">High severity</div></td>'
        f'<td><div class="stat-num amber">{ctx["medium_count"]}</div><div class="stat-label">Medium severity</div></td>'
        f'<td><div class="stat-num green">{ctx["low_count"]}</div><div class="stat-label">Low severity</div></td>'
        f'<td><div class="stat-num">{len(ctx["new_keywords"])}</div><div class="stat-label">New keywords</div></td>'
        f'<td><div class="stat-num">{ctx["avg_sentiment"]:.3f}</div><div class="stat-label">Avg sentiment</div></td>'
        '</tr></table>'
    )

    hm_rows = "\n".join(_hm_row(cat, cnt) for cat, cnt in ctx["by_category"].items())

    tier_chips = (
        f'<span class="tier-chip chip-red">HIGH &nbsp;&middot;&nbsp; {ctx["high_count"]} flags</span>'
        f'<span class="tier-chip chip-amber">MEDIUM &nbsp;&middot;&nbsp; {ctx["medium_count"]} flags</span>'
        f'<span class="tier-chip chip-green">LOW &nbsp;&middot;&nbsp; {ctx["low_count"]}</span>'
    )

    high_cards    = "\n".join(_card(f) for f in ctx["high_findings"])
    medium1_cards = "\n".join(_card(f) for f in ctx["medium_first"])
    medium2_cards = "\n".join(_card(f) for f in ctx["medium_second"])
    low_cards     = "\n".join(_card(f) for f in ctx["low_findings"])

    if ctx["new_keywords"]:
        nkw_html = "\n".join(_kw_card(kw) for kw in ctx["new_keywords"])
        nkw_html += (
            '\n<div class="dot-legend">'
            '<span class="dot-high">&#9679;</span> high severity (score 70+) &nbsp;&nbsp;'
            '<span class="dot-mid">&#9679;</span> elevated (40&#8211;69) &nbsp;&nbsp;'
            '<span class="dot-low">&#9679;</span> lower (&lt;40)'
            '</div>'
        )
    else:
        nkw_html = '<p style="color:#888;font-style:italic;">No new keywords identified in this filing.</p>'

    ttr_parts = []
    for i, item in enumerate(ctx["three_to_raise"], 1):
        tag_html = f'\n<br><span class="raise-tag">{item["tag"]}</span>' if item["tag"] else ""
        ttr_parts.append(
            f'<div class="three-raise-item">'
            f'<span class="raise-num">{i}.</span> '
            f'<span class="raise-text">{item["text"]}</span>'
            f'{tag_html}</div>'
        )
    ttr_html = "\n".join(ttr_parts)

    high_div_p2 = (
        f'<div class="divider div-red">High severity findings &nbsp;({ctx["high_count"]})</div>\n{high_cards}'
        if ctx["high_findings"] else ""
    )
    high_div_p3 = (
        f'<div class="divider div-red">High severity findings &nbsp;({ctx["high_count"]})</div>\n{high_cards}'
        if ctx["high_findings"] else ""
    )
    med1_div = (
        f'<div class="divider div-amber">Medium severity findings &nbsp;({ctx["medium_count"]})</div>\n{medium1_cards}'
        if ctx["medium_first"] else ""
    )
    med2_section = (
        f'<div class="divider div-amber">Medium severity findings (continued)</div>\n{medium2_cards}'
        if ctx["medium_second"] else ""
    )
    low_section = (
        f'<div class="divider div-green">Low severity findings &nbsp;({ctx["low_count"]})</div>\n'
        f'<p class="low-note">Low severity flags are included for completeness. '
        f'Standard boilerplate language &#8212; no immediate action required.</p>\n'
        f'{low_cards}'
        if ctx["low_findings"] else ""
    )

    sections_str = ", ".join(ctx["sections_scanned"]) if ctx["sections_scanned"] else "N/A"

    # ── assemble ──────────────────────────────────────────────

    parts = []
    parts.append('<!DOCTYPE html>')
    parts.append('<html lang="en">')
    parts.append('<head>')
    parts.append('<meta charset="utf-8">')
    parts.append(f'<title>RedFlag &#8212; {ctx["ticker"]}</title>')
    parts.append(_V2_CSS)
    parts.append('</head>')
    parts.append('<body>')

    # PAGE 1 — COVER
    parts.append('<div class="page-first">')
    parts.append('  <div class="cover-header">')
    parts.append('    <div class="cover-header-inner">')
    parts.append(f'      <div class="cover-topright">RedFlag v2.0<br>{ctx["generated_date"]}</div>')
    parts.append(f'      <div class="cover-company">{ctx["company_name"]}</div>')
    parts.append(
        f'      <div class="cover-meta">{ctx["ticker"]} &nbsp;&middot;&nbsp; '
        f'{ctx["doc_type"]} &nbsp;&middot;&nbsp; {ctx["filing_date"]} &nbsp;&middot;&nbsp; {ctx["exchange"]}</div>'
    )
    parts.append(f'      <div class="verdict-pill {ctx["verdict_class"]}">{ctx["verdict_label"]}</div>')
    parts.append('    </div>')
    parts.append('  </div>')
    parts.append(stat_cover)
    parts.append(f'  <div class="bottom-line-box">{ctx["bottom_line"]}</div>')
    parts.append(
        '  <div class="page-footer">Not financial advice &nbsp;&middot;&nbsp; '
        'For due diligence purposes only &nbsp;&middot;&nbsp; RedFlag &nbsp;&middot;&nbsp; '
        'github.com/zshqv/RedFlag</div>'
    )
    parts.append('</div>')

    # PAGE 2 — RISK HEAT MAP
    parts.append('<div class="page">')
    parts.append('  <div class="section-title">Risk exposure &#8212; category breakdown</div>')
    parts.append(hm_rows)
    parts.append(f'  <div style="margin:14px 0 16px;">{tier_chips}</div>')
    parts.append(high_div_p2)
    parts.append('</div>')

    # PAGE 3 — ALL HIGH + FIRST HALF MEDIUM
    parts.append('<div class="page">')
    parts.append(high_div_p3)
    parts.append(med1_div)
    parts.append('</div>')

    # PAGE 4 — REMAINING MEDIUM + LOW
    parts.append('<div class="page">')
    parts.append(med2_section)
    parts.append(low_section)
    parts.append('</div>')

    # PAGE 5 — NEW KEYWORDS
    parts.append('<div class="page">')
    parts.append('  <div class="section-title">New risk keywords &#8212; absent in prior year filing</div>')
    parts.append('  <p class="section-subtitle">New keyword appearances often signal emerging risks or changing disclosures.</p>')
    parts.append(nkw_html)
    parts.append('</div>')

    # PAGE 6 — DASHBOARD
    parts.append('<div class="page">')
    parts.append(
        f'  <div class="dash-title">Key findings &#8212; {ctx["company_name"]} {ctx["ticker"]} {ctx["filing_year"]}</div>'
    )
    parts.append(stat_dash)
    parts.append('  <hr class="dash-rule">')
    parts.append('  <div class="divider div-navy" style="margin-bottom:12px;">Three things to raise in this meeting</div>')
    parts.append(ttr_html)
    parts.append(
        '  <div class="page-footer">Not financial advice &nbsp;&middot;&nbsp; '
        'For due diligence purposes only &nbsp;&middot;&nbsp; RedFlag &nbsp;&middot;&nbsp; '
        'github.com/zshqv/RedFlag</div>'
    )
    parts.append('</div>')

    # PAGE 7 — SOURCE & REPRODUCIBILITY
    parts.append('<div class="page">')
    parts.append('  <div class="section-title">Source &amp; reproducibility</div>')
    parts.append('  <table class="source-table">')
    parts.append(f'    <tr><td class="lbl">Source type</td><td class="val">{ctx["exchange"]}</td></tr>')
    parts.append(f'    <tr><td class="lbl">Filing date</td><td class="val">{ctx["filing_date"]}</td></tr>')
    parts.append(f'    <tr><td class="lbl">Prior filing date</td><td class="val">{ctx["previous_date"]}</td></tr>')
    parts.append(f'    <tr><td class="lbl">Analyzed on</td><td class="val">{ctx["generated_date"]}</td></tr>')
    parts.append(f'    <tr><td class="lbl">Sections scanned</td><td class="val">{sections_str}</td></tr>')
    parts.append('    <tr><td class="lbl">Keyword library version</td><td class="val">v2.0 &#8212; 220+ keywords, 6 categories</td></tr>')
    parts.append('    <tr><td class="lbl">Explanation engine</td><td class="val">Claude API (claude-haiku-4-5-20251001) + rule-based fallback</td></tr>')
    parts.append('    <tr><td class="lbl">GitHub</td><td class="val">github.com/zshqv/RedFlag</td></tr>')
    parts.append('  </table>')
    parts.append(
        '  <div class="full-disclaimer">'
        '<strong>DISCLAIMER:</strong> This report is not financial advice and must not be relied upon as the sole basis '
        'for investment decisions. RedFlag is a due diligence co-pilot that highlights linguistic risk anomalies in '
        'financial filings. All findings are keyword-based and must be validated by qualified human analysts familiar '
        'with the company and its industry context. Severity scoring is rule-based and does not constitute a professional '
        'risk assessment. Not financial advice. For due diligence purposes only.'
        '</div>'
    )
    parts.append('</div>')

    parts.append('</body>')
    parts.append('</html>')
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────
#  HTML report
# ─────────────────────────────────────────────────────────────

def generate_html_report(ticker, analysis, comparison, latest_date, exchange, previous_date):
    ensure_output_dir()
    html_path = os.path.join(OUTPUT_DIR, f"{ticker}_report.html")
    ctx       = _build_pdf_context(ticker, analysis, comparison, latest_date, exchange, previous_date)
    html_str  = _build_fallback_html(ctx)
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
