# =============================================================================
# main.py — RedFlag CLI Entry Point (v2.0)
# =============================================================================
# Usage:
#   python main.py AAPL
#   python main.py RELIANCE.NS
#   python main.py HSBC.L
#   python main.py RY.TO
#   python main.py --pdf /path/to/report.pdf
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
+========================================+
|  [RedFlag] Risk Intelligence Platform   |
|  Flags anomalies in financial filings    |
|  github.com/zshqv/RedFlag               |
+========================================+
    """)


def file_size_str(path):
    if not os.path.exists(path):
        return "N/A"
    size = os.path.getsize(path)
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB"
    elif size >= 1_000:
        return f"{size / 1_000:.1f} KB"
    return f"{size} B"


def run_redflag(ticker):
    """Run the full 7-step pipeline for a single ticker."""
    print(f"\n[RedFlag] ===== TICKER: {ticker} =====")

    start_time = time.time()

    print(f"[RedFlag] Step 1/7: Fetching filing...")
    result = fetch_filing(ticker)
    if not result:
        print(f"[RedFlag] ERROR: Could not fetch filing for {ticker}")
        return None

    ticker_clean = result.get("ticker", ticker)
    exchange = result.get("exchange", "Unknown")
    latest_date = result.get("latest", {}).get("date", "N/A")
    previous_date = result.get("previous", {}).get("date")
    latest_text = result.get("latest", {}).get("text", "")
    previous_text = result.get("previous", {}).get("text", "")

    print(f"[RedFlag] Step 2/7: Extracting sections...")
    latest_sections = extract_sections(latest_text)

    print(f"[RedFlag] Step 3/7: Analyzing latest filing...")
    latest_analysis = analyze_filings(latest_sections)

    print(f"[RedFlag] Step 4/7: Analyzing previous filing...")
    if previous_text:
        previous_sections = extract_sections(previous_text)
        previous_analysis = analyze_filings(previous_sections)
    else:
        previous_analysis = {"findings": [], "summary": {"total": 0, "by_category": {}, "by_severity": {}}}

    print(f"[RedFlag] Step 5/7: Year-over-year comparison...")
    comparison = compare_years(latest_analysis, previous_analysis)

    print(f"[RedFlag] Step 6/7: Generating reports (Excel, PDF, PPTX)...")
    report_paths = generate_reports(
        ticker_clean,
        latest_analysis,
        comparison,
        latest_date,
        previous_date,
        exchange
    )

    elapsed = time.time() - start_time

    print(f"\n[RedFlag] ===== RESULTS =====")
    print(f"Findings: {latest_analysis['summary']['total']} total")
    print(f"  — HIGH: {latest_analysis['summary']['by_severity'].get('HIGH', 0)}")
    print(f"  — MEDIUM: {latest_analysis['summary']['by_severity'].get('MEDIUM', 0)}")
    print(f"  — LOW: {latest_analysis['summary']['by_severity'].get('LOW', 0)}")
    print(f"Trajectory: {comparison['overall']['trajectory']}")
    print(f"New Keywords: {len(comparison.get('new_keywords', []))}")
    print(f"Exchange: {exchange}")
    print(f"Time: {elapsed:.1f}s")
    print(f"\nOutput files:")
    for key, path in report_paths.items():
        if path:
            size = file_size_str(path)
            print(f"  {key.upper()}: {path} ({size})")

    return {
        "ticker": ticker_clean,
        "analysis": latest_analysis,
        "comparison": comparison,
        "latest_date": latest_date,
        "exchange": exchange,
        "paths": report_paths,
    }


def run_compare(tickers):
    """Run comparison across multiple tickers."""
    print(f"\n[RedFlag] ===== COMPARISON MODE: {', '.join(tickers)} =====\n")

    results = []
    for ticker in tickers:
        result = run_redflag(ticker)
        if result:
            results.append(result)

    if len(results) < 2:
        print("[RedFlag] ERROR: Need at least 2 tickers for comparison")
        return

    print("\n[RedFlag] Generating comparison Excel and deck...")

    print(f"\n[RedFlag] All tickers processed. Open 'output/' folder for results.")
    try:
        if sys.platform == "win32":
            os.startfile("output")
        elif sys.platform == "darwin":
            subprocess.run(["open", "output"])
        else:
            subprocess.run(["xdg-open", "output"])
    except Exception:
        print("[RedFlag] Could not auto-open output folder.")


def main():
    print_banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py AAPL")
        print("  python main.py RELIANCE.NS")
        print("  python main.py HSBC.L")
        print("  python main.py RY.TO")
        print("  python main.py --pdf /path/to/report.pdf")
        print("  python main.py --compare JPM BAC GS")
        return

    if sys.argv[1] == "--compare":
        tickers = sys.argv[2:]
        if len(tickers) < 2:
            print("[RedFlag] ERROR: --compare requires at least 2 tickers")
            return
        run_compare(tickers)
    elif sys.argv[1] == "--pdf":
        if len(sys.argv) < 3:
            print("[RedFlag] ERROR: --pdf requires a file path")
            return
        pdf_path = sys.argv[2]
        result = run_redflag(pdf_path)
        if result:
            try:
                if sys.platform == "win32":
                    os.startfile("output")
                elif sys.platform == "darwin":
                    subprocess.run(["open", "output"])
                else:
                    subprocess.run(["xdg-open", "output"])
            except Exception:
                print("[RedFlag] Could not auto-open output folder.")
    else:
        ticker = sys.argv[1]
        result = run_redflag(ticker)
        if result:
            try:
                if sys.platform == "win32":
                    os.startfile("output")
                elif sys.platform == "darwin":
                    subprocess.run(["open", "output"])
                else:
                    subprocess.run(["xdg-open", "output"])
            except Exception:
                print("[RedFlag] Could not auto-open output folder.")


if __name__ == "__main__":
    main()
