# =============================================================================
# main.py — RedFlag Entry Point
# =============================================================================
# This is the single command that runs the entire RedFlag pipeline.
#
# Usage:
#   python main.py AAPL
#   python main.py TSLA
#   python main.py JPM
#
# What happens when you run it:
#   1. Fetches the latest and previous 10-K from SEC EDGAR
#   2. Extracts the high-risk sections (Risk Factors, MD&A, Financial Notes)
#   3. Flags risk keywords across 4 categories
#   4. Scores sentiment on every flagged sentence
#   5. Compares this year vs last year
#   6. Exports a full Excel report + one-page PDF summary
#   7. Opens the output folder automatically
# =============================================================================

import sys          # For reading the ticker argument from the command line
import os           # For opening the output folder after generation
import time         # For tracking total runtime

# Import all RedFlag modules
from edgar_fetcher    import fetch_10k
from text_parser      import extract_sections
from risk_analyzer    import analyze_filings
from comparator       import compare_years
from report_generator import generate_reports


# -----------------------------------------------------------------------------
# BANNER — Prints when RedFlag starts
# -----------------------------------------------------------------------------
def print_banner():
    print("""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   🚩  RedFlag — SEC Filing Risk Analyzer             ║
║   Flags the risk anomalies your human eye misses     ║
║   github.com/zshqv/RedFlag                           ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
    """)


# -----------------------------------------------------------------------------
# MAIN PIPELINE
# Orchestrates all 6 modules in sequence
# -----------------------------------------------------------------------------
def run_redflag(ticker):
    """
    Runs the complete RedFlag analysis pipeline for a given ticker.

    Args:
        ticker (str): Stock ticker e.g. "AAPL"
    """

    start_time = time.time()
    print_banner()
    print(f"[RedFlag] Starting analysis for: {ticker.upper()}\n")
    print("=" * 60)

    # ------------------------------------------------------------------
    # STEP 1 — Fetch 10-K filings from SEC EDGAR
    # ------------------------------------------------------------------
    print("\n📥  STEP 1 — Fetching SEC EDGAR filings...\n")
    result = fetch_10k(ticker)

    if not result:
        print(f"\n[RedFlag] ERROR: Could not fetch filings for '{ticker}'.")
        print("[RedFlag] Please check the ticker symbol and try again.")
        return

    has_previous = result["previous"]["text"] is not None

    # ------------------------------------------------------------------
    # STEP 2 — Extract high-risk sections from latest filing
    # ------------------------------------------------------------------
    print("\n📄  STEP 2 — Extracting high-risk sections...\n")
    latest_sections = extract_sections(result["latest"]["text"])

    # ------------------------------------------------------------------
    # STEP 3 — Run risk analysis on latest filing
    # ------------------------------------------------------------------
    print("\n🔍  STEP 3 — Running risk analysis on latest filing...\n")
    latest_analysis = analyze_filings(latest_sections)

    # ------------------------------------------------------------------
    # STEP 4 — Analyze previous year (for comparison)
    # ------------------------------------------------------------------
    if has_previous:
        print("\n📅  STEP 4 — Analyzing previous year's filing...\n")
        previous_sections = extract_sections(result["previous"]["text"])
        previous_analysis = analyze_filings(previous_sections)
    else:
        print("\n[RedFlag] No previous filing found — skipping year-over-year comparison.")
        previous_analysis = {"findings": [], "summary": {}}

    # ------------------------------------------------------------------
    # STEP 5 — Compare years
    # ------------------------------------------------------------------
    print("\n📊  STEP 5 — Running year-over-year comparison...\n")
    comparison = compare_years(latest_analysis, previous_analysis)

    # ------------------------------------------------------------------
    # STEP 6 — Generate reports
    # ------------------------------------------------------------------
    print("\n📋  STEP 6 — Generating Excel + PDF reports...\n")
    paths = generate_reports(
        ticker        = result["ticker"],
        analysis      = latest_analysis,
        comparison    = comparison,
        latest_date   = result["latest"]["date"],
        previous_date = result["previous"]["date"] if has_previous else "N/A"
    )

    # ------------------------------------------------------------------
    # DONE — Print summary
    # ------------------------------------------------------------------
    elapsed = round(time.time() - start_time, 1)

    print("\n" + "=" * 60)
    print(f"""
✅  RedFlag Analysis Complete — {ticker.upper()}
─────────────────────────────────────────
  Total Risk Findings:  {len(latest_analysis['findings'])}
  Overall Trajectory:   {comparison['overall']['trajectory']}
  New Keywords:         {len(comparison['new_keywords'])}
  Time Taken:           {elapsed} seconds

  Reports saved to:
  📊  {paths['excel']}
  📄  {paths['pdf']}
─────────────────────────────────────────
  A task that takes analysts 3-4 hours
  completed in {elapsed} seconds.
    """)

    # Open the output folder automatically
    output_dir = os.path.abspath("output")
    os.startfile(output_dir)


# -----------------------------------------------------------------------------
# ENTRY POINT
# Reads the ticker from the command line and runs the pipeline
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # Check that a ticker was provided
    if len(sys.argv) < 2:
        print("\n[RedFlag] ERROR: No ticker provided.")
        print("[RedFlag] Usage: python main.py AAPL")
        print("[RedFlag] Example tickers: AAPL, TSLA, JPM, MSFT, GOOGL\n")
        sys.exit(1)

    # Get the ticker from command line
    ticker = sys.argv[1].strip().upper()

    # Run the full pipeline
    run_redflag(ticker)