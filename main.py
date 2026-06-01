# =============================================================================
# main.py — RedFlag Entry Point
# =============================================================================
# Usage:
#   python main.py AAPL
#   python main.py RELIANCE.NS
#   python main.py HSBC.L
#   python main.py --compare JPM BAC GS WFC
# =============================================================================

import sys
import os
import time

from fetchers.fetcher_router import fetch_filing
from text_parser             import extract_sections
from risk_analyzer           import analyze_filings
from comparator              import compare_years
from report_generator        import generate_reports, generate_comparison_excel, generate_comparison_pdf


def print_banner():
    print("""
+======================================================+
|                                                      |
|   [RedFlag] SEC Filing Risk Analyzer                 |
|   Flags the risk anomalies your human eye misses     |
|   github.com/zshqv/RedFlag                           |
|                                                      |
+======================================================+
    """)


def run_redflag(ticker):
    """Runs the complete RedFlag analysis pipeline for a single ticker."""

    start_time = time.time()
    print_banner()
    print(f"[RedFlag] Starting analysis for: {ticker.upper()}\n")
    print("=" * 60)

    # STEP 1 — Fetch filing
    print("\n[+] STEP 1 -- Fetching filing...\n")
    result = fetch_filing(ticker)

    if not result:
        print(f"\n[RedFlag] ERROR: Could not fetch filings for '{ticker}'.")
        print("[RedFlag] Please check the ticker symbol and try again.")
        return None

    has_previous = result["previous"]["text"] is not None
    exchange     = result.get("exchange", "NYSE/NASDAQ")

    # STEP 2 — Extract sections
    print("\n[+] STEP 2 -- Extracting high-risk sections...\n")
    latest_sections = extract_sections(result["latest"]["text"])

    # STEP 3 — Risk analysis (latest)
    print("\n[+] STEP 3 -- Running risk analysis on latest filing...\n")
    latest_analysis = analyze_filings(latest_sections)

    # STEP 4 — Analyze previous year
    if has_previous:
        print("\n[+] STEP 4 -- Analyzing previous year's filing...\n")
        previous_sections = extract_sections(result["previous"]["text"])
        previous_analysis = analyze_filings(previous_sections)
    else:
        print("\n[RedFlag] No previous filing found -- skipping year-over-year comparison.")
        previous_analysis = {"findings": [], "summary": {}}

    # STEP 5 — Compare years
    print("\n[+] STEP 5 -- Running year-over-year comparison...\n")
    comparison = compare_years(latest_analysis, previous_analysis)

    # STEP 6 — Generate reports
    print("\n[+] STEP 6 -- Generating Excel + PDF reports...\n")
    paths = generate_reports(
        ticker        = result["ticker"],
        analysis      = latest_analysis,
        comparison    = comparison,
        latest_date   = result["latest"]["date"],
        previous_date = result["previous"]["date"] if has_previous else None,
        exchange      = exchange,
    )

    elapsed = round(time.time() - start_time, 1)

    print("\n" + "=" * 60)
    print(f"""
[+] RedFlag Analysis Complete -- {ticker.upper()}
-------------------------------------------
  Total Risk Findings:  {len(latest_analysis['findings'])}
  Overall Trajectory:   {comparison['overall']['trajectory']}
  New Keywords:         {len(comparison['new_keywords'])}
  Exchange:             {exchange}
  Time Taken:           {elapsed} seconds

  Reports saved to:
  [Excel]  {paths['excel']}
  [PDF]    {paths['pdf']}
-------------------------------------------
  A task that takes analysts 3-4 hours
  completed in {elapsed} seconds.
    """)

    # Open the output folder
    output_dir = os.path.abspath("output")
    try:
        os.startfile(output_dir)
    except Exception:
        pass

    return {
        "ticker":     result["ticker"],
        "analysis":   latest_analysis,
        "comparison": comparison,
        "latest_date": result["latest"]["date"],
        "exchange":   exchange,
    }


def run_compare(tickers):
    """Runs the full pipeline for each ticker and generates peer comparison files."""

    print_banner()
    print(f"[RedFlag] Peer Comparison Mode: {', '.join(tickers)}\n")
    print("=" * 60)

    results_list = []

    for ticker in tickers:
        print(f"\n{'=' * 60}")
        print(f"[RedFlag] Processing: {ticker.upper()}")
        print(f"{'=' * 60}")
        result = run_redflag(ticker)
        if result:
            results_list.append(result)
        else:
            print(f"[RedFlag] WARNING: Skipping {ticker} -- fetch failed.")

    if not results_list:
        print("[RedFlag] ERROR: No tickers could be processed.")
        return

    print(f"\n[RedFlag] Generating peer comparison files for {len(results_list)} companies...")

    excel_path = generate_comparison_excel(
        tickers=[r["ticker"] for r in results_list],
        results_list=results_list
    )
    pdf_path = generate_comparison_pdf(
        tickers=[r["ticker"] for r in results_list],
        results_list=results_list
    )

    print(f"\n[RedFlag] Comparison Reports:")
    print(f"  [Excel]  {excel_path}")
    print(f"  [PDF]    {pdf_path}")

    output_dir = os.path.abspath("output")
    try:
        os.startfile(output_dir)
    except Exception:
        pass


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("\n[RedFlag] ERROR: No ticker provided.")
        print("[RedFlag] Usage:")
        print("  python main.py AAPL")
        print("  python main.py RELIANCE.NS")
        print("  python main.py --compare JPM BAC GS WFC\n")
        sys.exit(1)

    if sys.argv[1].strip().lower() == "--compare":
        # Peer comparison mode
        tickers = [t.strip().upper() for t in sys.argv[2:] if t.strip()]
        if len(tickers) < 2:
            print("[RedFlag] ERROR: --compare requires at least 2 tickers.")
            print("[RedFlag] Usage: python main.py --compare JPM BAC GS")
            sys.exit(1)
        run_compare(tickers)
    else:
        # Single ticker mode
        ticker = sys.argv[1].strip().upper()
        run_redflag(ticker)
