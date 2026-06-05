# =============================================================================
# edgar_fetcher.py — SEC EDGAR Filing Fetcher
# =============================================================================
# Fetches the two most recent 10-K annual reports for any US-listed ticker.
#
# SEC EDGAR requires a User-Agent header identifying the requester.
# Set the EDGAR_USER_AGENT environment variable before running:
#
#   Windows:  $env:EDGAR_USER_AGENT = "Your Name your@email.com"
#   Mac/Linux: export EDGAR_USER_AGENT="Your Name your@email.com"
#
# If the variable is not set, a generic placeholder is used.
# =============================================================================

import os
import requests
import json
import time


# SEC EDGAR requires a User-Agent string with your name and email.
# Read from environment so credentials are never stored in the repo.
HEADERS = {
    "User-Agent": os.environ.get("EDGAR_USER_AGENT", "RedFlag-Analyzer contact@example.com")
}

EDGAR_BASE_URL      = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


# -----------------------------------------------------------------------------
# STEP 1 — Convert ticker symbol to SEC CIK number
# -----------------------------------------------------------------------------
def get_cik_from_ticker(ticker):
    """
    Converts a stock ticker symbol to an SEC CIK number.

    Args:
        ticker (str): Stock ticker e.g. "AAPL", "TSLA", "JPM"

    Returns:
        str: Zero-padded CIK number e.g. "0000320193"
        None: If ticker not found
    """
    print(f"[RedFlag] Looking up CIK for ticker: {ticker.upper()}...")

    response = requests.get(COMPANY_TICKERS_URL, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not reach SEC EDGAR. Status: {response.status_code}")
        return None

    companies = response.json()

    for key, company in companies.items():
        if company["ticker"].upper() == ticker.upper():
            cik = str(company["cik_str"]).zfill(10)
            print(f"[RedFlag] Found CIK: {cik} for {company['title']}")
            return cik

    print(f"[RedFlag] ERROR: Ticker '{ticker}' not found in SEC EDGAR database.")
    return None


# -----------------------------------------------------------------------------
# STEP 2 — Fetch list of 10-K filings for a company
# -----------------------------------------------------------------------------
def get_10k_filings(cik):
    """
    Fetches the list of 10-K filings for a company using their CIK number.

    Args:
        cik (str): Zero-padded CIK number e.g. "0000320193"

    Returns:
        list: List of 10-K filing metadata dictionaries, newest first
        None: If no 10-K filings found
    """
    print(f"[RedFlag] Fetching filing history for CIK: {cik}...")

    url = f"{EDGAR_BASE_URL}/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not fetch filings. Status: {response.status_code}")
        return None

    data = response.json()
    filings = data.get("filings", {}).get("recent", {})

    forms         = filings.get("form", [])
    dates         = filings.get("filingDate", [])
    accession_nos = filings.get("accessionNumber", [])
    documents     = filings.get("primaryDocument", [])

    tenk_filings = []
    for i, form in enumerate(forms):
        if form == "10-K":
            tenk_filings.append({
                "form":         form,
                "date":         dates[i],
                "accession_no": accession_nos[i],
                "primary_doc":  documents[i],
                "cik":          cik
            })

    if not tenk_filings:
        print(f"[RedFlag] ERROR: No 10-K filings found for this company.")
        return None

    print(f"[RedFlag] Found {len(tenk_filings)} 10-K filings. Most recent: {tenk_filings[0]['date']}")
    return tenk_filings


# -----------------------------------------------------------------------------
# STEP 3 — Download the full text of a 10-K filing
# -----------------------------------------------------------------------------
def download_10k_text(filing):
    """
    Downloads the full text content of a 10-K filing.

    Args:
        filing (dict): Filing metadata from get_10k_filings()

    Returns:
        str: Raw text content of the 10-K filing
        None: If download fails
    """
    accession_clean = filing["accession_no"].replace("-", "")
    cik_clean       = filing["cik"].lstrip("0")

    filing_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_clean}/{accession_clean}/{filing['primary_doc']}"
    )

    print(f"[RedFlag] Downloading 10-K from SEC EDGAR...")

    time.sleep(0.5)  # be polite to SEC servers

    response = requests.get(filing_url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not download filing. Status: {response.status_code}")
        return None

    print(f"[RedFlag] Successfully downloaded 10-K ({len(response.text):,} characters)")
    return response.text


# -----------------------------------------------------------------------------
# MASTER FUNCTION — fetch latest + previous 10-K for year-over-year analysis
# -----------------------------------------------------------------------------
def fetch_10k(ticker):
    """
    Fetches the two most recent 10-K filings for a ticker.

    Args:
        ticker (str): Stock ticker e.g. "AAPL"

    Returns:
        dict: {
            "ticker": ticker,
            "latest":   {"date": ..., "text": ...},
            "previous": {"date": ..., "text": ...}
        }
        None: If anything fails
    """
    cik = get_cik_from_ticker(ticker)
    if not cik:
        return None

    filings = get_10k_filings(cik)
    if not filings:
        return None

    latest_text = download_10k_text(filings[0])
    if not latest_text:
        return None

    previous_text = None
    previous_date = None
    if len(filings) > 1:
        print(f"[RedFlag] Also fetching previous year's 10-K ({filings[1]['date']})...")
        time.sleep(0.5)
        previous_text = download_10k_text(filings[1])
        previous_date = filings[1]["date"]

    return {
        "ticker":   ticker.upper(),
        "latest":   {"date": filings[0]["date"], "text": latest_text},
        "previous": {"date": previous_date, "text": previous_text}
    }


# -----------------------------------------------------------------------------
# Quick test — python edgar_fetcher.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    result = fetch_10k("AAPL")
    if result:
        print(f"\n[RedFlag] Test Complete")
        print(f"  Ticker:        {result['ticker']}")
        print(f"  Latest 10-K:   {result['latest']['date']}")
        print(f"  Previous 10-K: {result['previous']['date']}")
        print(f"  Latest size:   {len(result['latest']['text']):,} characters")
