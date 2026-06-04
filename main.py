# =============================================================================
# main.py — RedFlag CLI Entry Point (v2.0)
# =============================================================================
# Usage:
#   python main.py AAPL
#   python main.py RELIANCE.NS
#   python main.py HSBC.L
#   python main.py RY.TO
#   python main.py --pdf "/path/to/report.pdf"
#   python main.py --compare JPM BAC GS
# =============================================================================

import sys
import os
import time
import subprocess

from fetchers.fetcher_router import fetch_filing
from text_parser import extract_sections
from risk_analyzer import analyze_filings
from comparator import compare_years
from report_generator import generate_reports


def print_banner():
    print("""
+==========================================+
|   RedFlag — Risk Intelligence Platform   |
|   Flags anomalies in financial filings   |
|   github.com/zshqv/RedFlag               |
+==========================================+
    """)


def file_size_str(path):
    if not path or not os.path.exists(path):
        return "N/A"
    size = os.path.getsize(path)
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB"
    if size >= 1_000:
        return f"{size / 1_000:.1f} KB"
    return f"{size} B"


def _empty_analysis():
    return {
        "findings": [],
        "summary": {
            "total": 0,
            "by_category": {},
            "by_severity": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "avg_sentiment": 0.0,
            "sections_with_flags": [],
        },
    }


def _open_output():
    try:
        folder = os.path.abspath("output")
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", folder])
        else:
            subprocess.run(["xdg-open", folder])
    except Exception:
        pass


def run_redflag(ticker):
    """Run the full pipeline for a single ticker or PDF path."""
    print(f"\n[RedFlag] ===== {ticker} =====")
    start = time.time()

    print("[RedFlag] Step 1/7: Fetching filing...")
    result = fetch_filing(ticker)
    if not result:
        print(f"[RedFlag] ERROR: Could not fetch filing for '{ticker}'")
        return None

    ticker_clean  = result.get("ticker", ticker)
    exchange      = result.get("exchange", "Unknown")
    latest_date   = result.get("latest", {}).get("date", "N/A")
    previous_date = result.get("previous", {}).get("date")
    latest_text   = result.get("latest", {}).get("text", "")
    previous_text = result.get("previous", {}).get("text", "")

    print("[RedFlag] Step 2/7: Extracting sections from latest filing...")
    latest_sections = extract_sections(latest_text)

    print("[RedFlag] Step 3/7: Analyzing latest filing...")
    latest_analysis = analyze_filings(latest_sections)

    print("[RedFlag] Step 4/7: Analyzing previous filing...")
    if previous_text:
        prev_sections  = extract_sections(previous_text)
        prev_analysis  = analyze_filings(prev_sections)
    else:
        print("[RedFlag]   No previous filing — skipping YoY analysis.")
        prev_analysis = _empty_analysis()

    print("[RedFlag] Step 5/7: Year-over-year comparison...")
    comparison = compare_years(latest_analysis, prev_analysis)
    comparison["exchange"] = exchange

    print("[RedFlag] Step 6/7: Generating reports (Excel, PDF, PPTX)...")
    paths = generate_reports(
        ticker_clean, latest_analysis, comparison,
        latest_date, previous_date, exchange
    )

    elapsed = time.time() - start
    summ    = latest_analysis["summary"]

    print(f"\n[RedFlag] ===== RESULTS: {ticker_clean} =====")
    print(f"  Total findings : {summ['total']}")
    print(f"  HIGH           : {summ['by_severity'].get('HIGH', 0)}")
    print(f"  MEDIUM         : {summ['by_severity'].get('MEDIUM', 0)}")
    print(f"  LOW            : {summ['by_severity'].get('LOW', 0)}")
    print(f"  Trajectory     : {comparison['overall']['trajectory']}")
    print(f"  New keywords   : {len(comparison.get('new_keywords', []))}")
    print(f"  Exchange       : {exchange}")
    print(f"  Elapsed        : {elapsed:.1f}s")
    print()
    for key, path in paths.items():
        size = file_size_str(path)
        print(f"  {key.upper():<6}: {path}  ({size})")

    return {
        "ticker":    ticker_clean,
        "analysis":  latest_analysis,
        "comparison": comparison,
        "latest_date": latest_date,
        "exchange":  exchange,
        "paths":     paths,
    }


def run_compare(tickers):
    """Run the pipeline across multiple tickers and report side-by-side."""
    print(f"\n[RedFlag] ===== COMPARISON MODE: {', '.join(tickers)} =====\n")

    results = []
    for ticker in tickers:
        r = run_redflag(ticker)
        if r:
            results.append(r)

    if len(results) < 2:
        print("[RedFlag] ERROR: Need at least 2 successful tickers for comparison.")
        return

    print("\n[RedFlag] ===== PEER COMPARISON SUMMARY =====")
    print(f"  {'Ticker':<10} {'Total':>6} {'HIGH':>6} {'MEDIUM':>8} {'LOW':>5}  Trajectory")
    print("  " + "-" * 55)
    for r in results:
        s = r["analysis"]["summary"]
        traj = r["comparison"]["overall"]["trajectory"]
        print(f"  {r['ticker']:<10} {s['total']:>6} "
              f"{s['by_severity'].get('HIGH',0):>6} "
              f"{s['by_severity'].get('MEDIUM',0):>8} "
              f"{s['by_severity'].get('LOW',0):>5}  {traj}")

    print(f"\n[RedFlag] All output files are in: output/")
    _open_output()


def main():
    print_banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py AAPL")
        print("  python main.py RELIANCE.NS")
        print("  python main.py HSBC.L")
        print("  python main.py RY.TO")
        print('  python main.py --pdf "/path/to/report.pdf"')
        print("  python main.py --compare JPM BAC GS")
        return

    if sys.argv[1] == "--compare":
        tickers = sys.argv[2:]
        if len(tickers) < 2:
            print("[RedFlag] ERROR: --compare requires at least 2 tickers.")
            return
        run_compare(tickers)

    elif sys.argv[1] == "--pdf":
        if len(sys.argv) < 3:
            print("[RedFlag] ERROR: --pdf requires a file path argument.")
            return
        run_redflag(sys.argv[2])
        _open_output()

    else:
        run_redflag(sys.argv[1])
        _open_output()


if __name__ == "__main__":
    main()
