import os
import sys

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _avg_sev(findings):
    if not findings:
        return 0
    return round(sum(f.get("severity_score", 50) for f in findings) / len(findings))


def _read_bytes(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return b""


def _run_pipeline(ticker):
    from fetchers.fetcher_router import fetch_filing
    from text_parser import extract_sections
    from risk_analyzer import analyze_filings
    from comparator import compare_years

    result = fetch_filing(ticker)
    if not result:
        return None, None, None, None

    latest_sections = extract_sections(result["latest"]["text"])
    latest_analysis = analyze_filings(latest_sections)

    if result["previous"]["text"]:
        prev_sections = extract_sections(result["previous"]["text"])
        prev_analysis = analyze_filings(prev_sections)
    else:
        prev_analysis = {"findings": [], "summary": {}}

    comparison = compare_years(latest_analysis, prev_analysis)
    return result, latest_analysis, prev_analysis, comparison


# ─── Streamlit app ────────────────────────────────────────────────────────────

def run_app():
    from report_generator import (generate_reports, generate_comparison_excel,
                                   generate_comparison_pdf)
    from deck_generator import generate_deck, generate_comparison_deck
    from trend_analyzer import analyze_trend
    from watchlist import load_watchlist, save_watchlist

    st.set_page_config(
        page_title="RedFlag — SEC Risk Intelligence",
        page_icon=":triangular_flag_on_post:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
        .redflag-logo { font-size:1.9rem; font-weight:900; color:#1a1a2e; letter-spacing:-1px; }
        .redflag-logo span { color:#E24B4A; }
    </style>
    """, unsafe_allow_html=True)

    # Session state
    for key, default in [("results", None), ("cmp_results", None), ("mode", "idle")]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ─── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="redflag-logo">Red<span>Flag</span></div>',
                    unsafe_allow_html=True)
        st.caption("SEC EDGAR Risk Intelligence  |  github.com/zshqv/RedFlag")
        st.divider()

        ticker_input = st.text_input(
            "Enter Ticker Symbol",
            placeholder="e.g. AAPL, JPM, RELIANCE.NS",
        )

        st.selectbox(
            "Sector Override",
            ["Auto-Detect", "Banking", "Technology", "Healthcare", "Energy"],
        )

        compare_mode  = st.checkbox("Compare Mode")
        compare_input = None
        if compare_mode:
            compare_input = st.text_input(
                "Enter tickers separated by commas",
                placeholder="e.g. JPM, BAC, GS",
            )

        analyse_btn = st.button("Analyse", type="primary", use_container_width=True)

        st.divider()
        st.subheader("Watchlist")

        wl_tickers   = load_watchlist()
        add_input    = st.text_input("Add ticker", placeholder="e.g. AAPL")
        add_btn      = st.button("Add to Watchlist")

        if add_btn and add_input.strip():
            t = add_input.strip().upper()
            if t not in wl_tickers:
                wl_tickers.append(t)
                save_watchlist(wl_tickers)
                st.success(f"Added {t}")
            else:
                st.info(f"{t} already in watchlist")

        if wl_tickers:
            st.write("Watching: " + "  ·  ".join(wl_tickers))
        else:
            st.caption("No tickers saved")

    # ─── Trigger analysis ─────────────────────────────────────────────────────
    if analyse_btn:
        if compare_mode and compare_input and compare_input.strip():
            tickers = [t.strip().upper() for t in compare_input.split(",") if t.strip()]
            if len(tickers) < 2:
                st.error("Compare mode requires at least 2 tickers.")
            else:
                results_list = []
                for t in tickers:
                    with st.spinner(f"Fetching and analysing {t}..."):
                        result, analysis, _, comparison = _run_pipeline(t)
                    if result is None:
                        st.error(f"Could not fetch filings for {t}. Check the ticker symbol.")
                        continue
                    if not analysis.get("findings"):
                        st.warning(f"No risk findings identified for {t}.")
                    results_list.append({
                        "ticker":      result["ticker"],
                        "analysis":    analysis,
                        "comparison":  comparison,
                        "latest_date": result["latest"]["date"],
                        "exchange":    result.get("exchange", "NYSE/NASDAQ"),
                    })
                if results_list:
                    st.session_state.cmp_results = ([r["ticker"] for r in results_list],
                                                    results_list)
                    st.session_state.mode = "compare"

        elif ticker_input.strip():
            ticker = ticker_input.strip().upper()
            with st.spinner(f"Fetching and analysing {ticker}..."):
                result, analysis, _, comparison = _run_pipeline(ticker)

            if result is None:
                st.error(f"Could not fetch filings for {ticker}. Check the ticker symbol.")
            else:
                if not analysis.get("findings"):
                    st.warning("No risk findings identified. "
                               "The filing may not have been parsed correctly.")

                rpt_paths = generate_reports(
                    ticker        = result["ticker"],
                    analysis      = analysis,
                    comparison    = comparison,
                    latest_date   = result["latest"]["date"],
                    previous_date = result["previous"]["date"],
                    exchange      = result.get("exchange", "NYSE/NASDAQ"),
                )
                pptx_path = generate_deck(
                    ticker      = result["ticker"],
                    analysis    = analysis,
                    comparison  = comparison,
                    latest_date = result["latest"]["date"],
                    exchange    = result.get("exchange", "NYSE/NASDAQ"),
                )
                st.session_state.results = {
                    "ticker":      result["ticker"],
                    "analysis":    analysis,
                    "comparison":  comparison,
                    "latest_date": result["latest"]["date"],
                    "exchange":    result.get("exchange", "NYSE/NASDAQ"),
                    "excel_path":  rpt_paths.get("excel"),
                    "pdf_path":    rpt_paths.get("pdf"),
                    "pptx_path":   pptx_path,
                }
                st.session_state.mode = "single"
        else:
            st.warning("Please enter a ticker symbol.")

    # ─── Single ticker results ─────────────────────────────────────────────────
    if st.session_state.mode == "single" and st.session_state.results:
        r          = st.session_state.results
        findings   = r["analysis"].get("findings", [])
        comparison = r["comparison"]
        traj       = comparison["overall"].get("trajectory", "STABLE")

        st.subheader(f"{r['ticker']} — Risk Analysis Report")
        st.caption(f"Filing: {r['latest_date']}  |  Exchange: {r['exchange']}")

        t_upper = traj.upper()
        if any(x in t_upper for x in ("IMPROVING", "DECREASING", "STABLE")):
            st.success(f"Trajectory: {traj}")
        elif any(x in t_upper for x in ("DETERIORATING", "INCREASING")):
            st.error(f"Trajectory: {traj}")
        else:
            st.warning(f"Trajectory: {traj}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Findings", len(findings))
        c2.metric("Avg Severity",   _avg_sev(findings))
        c3.metric("New Keywords",   len(comparison.get("new_keywords", [])))
        c4.metric("Trajectory",     traj)

        st.divider()
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Summary", "All Findings", "Year-over-Year", "Trend"]
        )

        with tab1:
            summary = r["analysis"].get("summary", {})
            st.markdown("#### Executive Verdict")
            if summary:
                top_cat = max(summary, key=summary.get)
                sent_trend = (comparison.get("sentiment_trend", {})
                              .get("sentiment_trend", "N/A"))
                st.write(
                    f"The **{top_cat}** category dominates this filing with "
                    f"**{summary[top_cat]}** flagged instances."
                )
                st.write(
                    f"Overall risk trajectory: **{traj}**. "
                    f"Language sentiment is **{sent_trend}**."
                )

            st.markdown("#### Category Overview")
            cats = ["Financial", "Legal", "Operational", "Regulatory"]
            cols = st.columns(4)
            for i, cat in enumerate(cats):
                cols[i].metric(cat, summary.get(cat, 0))

        with tab2:
            if findings:
                df = pd.DataFrame([
                    {
                        "Category":         f.get("category", ""),
                        "Keyword":          f.get("keyword", ""),
                        "Severity Score":   f.get("severity_score", 0),
                        "Confidence Score": f.get("confidence_score", 50),
                        "Section":          f.get("section", ""),
                        "Flagged Sentence": (f.get("sentence", "") or "")[:150],
                    }
                    for f in findings
                ])
                st.dataframe(df, use_container_width=True, height=450)
            else:
                st.info("No findings to display.")

        with tab3:
            by_cat = comparison.get("by_category", {})
            if by_cat:
                df_yoy = pd.DataFrame([
                    {
                        "Category":   cat,
                        "Last Year":  d.get("previous_count", 0),
                        "This Year":  d.get("current_count",  0),
                        "Change":     d.get("change", 0),
                        "% Change":   f"{d.get('percent_change', 0):+.1f}%",
                        "Trajectory": d.get("trajectory", "STABLE"),
                    }
                    for cat, d in by_cat.items()
                ])
                st.dataframe(df_yoy, use_container_width=True)
            else:
                st.info("No year-over-year data available.")

        with tab4:
            with st.spinner(f"Fetching 5-year trend for {r['ticker']}..."):
                trend = analyze_trend(r["ticker"])
            if "error" in trend:
                st.warning(f"Trend data unavailable: {trend['error']}")
            else:
                df_trend = pd.DataFrame({
                    "Year":        trend["years"],
                    "Financial":   trend.get("Financial",   []),
                    "Regulatory":  trend.get("Regulatory",  []),
                    "Operational": trend.get("Operational", []),
                    "Legal":       trend.get("Legal",       []),
                })
                st.dataframe(df_trend, use_container_width=True)

        st.divider()
        st.markdown("#### Download Reports")
        dc1, dc2, dc3 = st.columns(3)
        if r.get("excel_path") and os.path.exists(r["excel_path"]):
            dc1.download_button(
                "Download Excel",
                data=_read_bytes(r["excel_path"]),
                file_name=os.path.basename(r["excel_path"]),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        if r.get("pdf_path") and os.path.exists(r["pdf_path"]):
            dc2.download_button(
                "Download PDF",
                data=_read_bytes(r["pdf_path"]),
                file_name=os.path.basename(r["pdf_path"]),
                mime="application/pdf",
            )
        if r.get("pptx_path") and os.path.exists(r["pptx_path"]):
            dc3.download_button(
                "Download PPTX",
                data=_read_bytes(r["pptx_path"]),
                file_name=os.path.basename(r["pptx_path"]),
                mime=("application/vnd.openxmlformats-officedocument"
                      ".presentationml.presentation"),
            )

    # ─── Comparison results ────────────────────────────────────────────────────
    elif st.session_state.mode == "compare" and st.session_state.cmp_results:
        out_tickers, cmp_results = st.session_state.cmp_results

        with st.spinner("Building comparison reports..."):
            excel_path = generate_comparison_excel(
                tickers=out_tickers, results_list=cmp_results)
            pdf_path   = generate_comparison_pdf(
                tickers=out_tickers, results_list=cmp_results)
            pptx_path  = generate_comparison_deck(
                tickers=out_tickers, results_list=cmp_results)

        st.subheader("Peer Comparison — Risk Analysis")
        st.caption(f"Companies: {', '.join(out_tickers)}")

        rows = []
        for r in cmp_results:
            findings = r["analysis"].get("findings", [])
            summary  = r["analysis"].get("summary", {})
            rows.append({
                "Company":        r["ticker"],
                "Total Findings": len(findings),
                "Financial":      summary.get("Financial",   0),
                "Regulatory":     summary.get("Regulatory",  0),
                "Operational":    summary.get("Operational", 0),
                "Legal":          summary.get("Legal",       0),
                "Avg Severity":   _avg_sev(findings),
                "Trajectory":     r["comparison"]["overall"].get("trajectory", "STABLE"),
                "New Keywords":   len(r["comparison"].get("new_keywords", [])),
            })
        df_cmp = (pd.DataFrame(rows)
                  .sort_values("Avg Severity", ascending=False)
                  .reset_index(drop=True))
        st.dataframe(df_cmp, use_container_width=True)

        st.divider()
        st.markdown("#### Download Comparison Reports")
        dc1, dc2, dc3 = st.columns(3)
        if os.path.exists(excel_path):
            dc1.download_button(
                "Download Excel",
                data=_read_bytes(excel_path),
                file_name=os.path.basename(excel_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        if os.path.exists(pdf_path):
            dc2.download_button(
                "Download PDF",
                data=_read_bytes(pdf_path),
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
            )
        if os.path.exists(pptx_path):
            dc3.download_button(
                "Download PPTX",
                data=_read_bytes(pptx_path),
                file_name=os.path.basename(pptx_path),
                mime=("application/vnd.openxmlformats-officedocument"
                      ".presentationml.presentation"),
            )

    # ─── Welcome screen ────────────────────────────────────────────────────────
    else:
        st.markdown("""
        ## Welcome to RedFlag
        Enter a ticker in the sidebar and click **Analyse** to scan the latest 10-K for risk signals.

        **Supported exchanges:**
        - US: NYSE / NASDAQ — `AAPL`, `JPM`, `TSLA`
        - India: NSE/BSE — `RELIANCE.NS`, `TCS.BO`
        - Canada: TSX — `SHOP.TO`
        - UK: LSE — `HSBC.L`

        **Features:**
        - Risk scoring across Financial, Legal, Operational, Regulatory categories
        - Year-over-year trajectory analysis
        - Confidence scoring on every finding
        - 5-year trend analysis
        - Export to Excel, PDF, and PowerPoint
        """)


if __name__ == "__main__":
    run_app()
