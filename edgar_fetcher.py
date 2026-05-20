# =============================================================================
# edgar_fetcher.py — SEC EDGAR Filing Fetcher
# =============================================================================
# This module connects to the SEC EDGAR free public API and retrieves the
# most recent 10-K annual report for any publicly traded US company.
#
# No API key required. No paid subscription. SEC EDGAR is free and public.
#
# Workflow:
#   1. Accept a stock ticker (e.g. "AAPL")
#   2. Convert ticker to SEC CIK number (unique company identifier)
#   3. Fetch the list of filings for that company
#   4. Find the most recent 10-K filing
#   5. Download the full text of that filing
# =============================================================================

import requests  # For making HTTP requests to SEC EDGAR
import json      # For parsing the JSON responses from EDGAR
import time      # For adding small delays so we don't overwhelm SEC servers


# -----------------------------------------------------------------------------
# CONSTANTS
# SEC EDGAR requires a User-Agent header identifying who is making the request
# This is a legal requirement from the SEC — always include it
# -----------------------------------------------------------------------------
HEADERS = {
    "User-Agent": "RedFlag-Analyzer redflag@github.com"
}

# Base URLs for the SEC EDGAR API
EDGAR_BASE_URL   = "https://data.sec.gov"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2020-01-01&forms=10-K"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


# -----------------------------------------------------------------------------
# STEP 1 — GET CIK NUMBER FROM TICKER
# Every company on SEC EDGAR has a unique CIK (Central Index Key) number
# We need this to look up their filings
# -----------------------------------------------------------------------------
def get_cik_from_ticker(ticker):
    """
    Converts a stock ticker symbol to an SEC CIK number.

    Args:
        ticker (str): Stock ticker e.g. "AAPL", "TSLA", "JPM"

    Returns:
        str: Zero-padded CIK number e.g. "0000320193"
        None: If ticker not found
    """# =============================================================================
# edgar_fetcher.py — SEC EDGAR Filing Fetcher
# =============================================================================
# This module connects to the SEC EDGAR free public API and retrieves the
# most recent 10-K annual report for any publicly traded US company.
#
# No API key required. No paid subscription. SEC EDGAR is free and public.
#
# Workflow:
#   1. Accept a stock ticker (e.g. "AAPL")
#   2. Convert ticker to SEC CIK number (unique company identifier)
#   3. Fetch the list of filings for that company
#   4. Find the most recent 10-K filing
#   5. Download the full text of that filing
# =============================================================================

import requests  # For making HTTP requests to SEC EDGAR
import json      # For parsing the JSON responses from EDGAR
import time      # For adding small delays so we don't overwhelm SEC servers


# -----------------------------------------------------------------------------
# CONSTANTS
# SEC EDGAR requires a User-Agent header identifying who is making the request
# This is a legal requirement from the SEC — always include it
# -----------------------------------------------------------------------------
HEADERS = {
    "User-Agent": "RedFlag-Analyzer redflag@github.com"
}

# Base URLs for the SEC EDGAR API
EDGAR_BASE_URL   = "https://data.sec.gov"
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2020-01-01&forms=10-K"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


# -----------------------------------------------------------------------------
# STEP 1 — GET CIK NUMBER FROM TICKER
# Every company on SEC EDGAR has a unique CIK (Central Index Key) number
# We need this to look up their filings
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

    # SEC provides a master JSON file mapping all tickers to CIK numbers
    response = requests.get(COMPANY_TICKERS_URL, headers=HEADERS)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not reach SEC EDGAR. Status: {response.status_code}")
        return None

    # Parse the JSON response
    companies = response.json()

    # Search through all companies for our ticker
    for key, company in companies.items():
        if company["ticker"].upper() == ticker.upper():
            # CIK must be padded to 10 digits — SEC requirement
            cik = str(company["cik_str"]).zfill(10)
            print(f"[RedFlag] Found CIK: {cik} for {company['title']}")
            return cik

    # If we get here, the ticker wasn't found
    print(f"[RedFlag] ERROR: Ticker '{ticker}' not found in SEC EDGAR database.")
    return None


# -----------------------------------------------------------------------------
# STEP 2 — GET LIST OF 10-K FILINGS FOR THIS COMPANY
# Using the CIK, we fetch their complete filing history and find 10-Ks
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

    # EDGAR submissions endpoint — returns all filings for a company
    url = f"{EDGAR_BASE_URL}/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not fetch filings. Status: {response.status_code}")
        return None

    data = response.json()

    # Extract the recent filings section
    filings = data.get("filings", {}).get("recent", {})

    # Get the parallel arrays from EDGAR response
    forms        = filings.get("form", [])
    dates        = filings.get("filingDate", [])
    accession_nos = filings.get("accessionNumber", [])
    documents    = filings.get("primaryDocument", [])

    # Filter for only 10-K filings (annual reports)
    tenk_filings = []
    for i, form in enumerate(forms):
        if form == "10-K":
            tenk_filings.append({
                "form":           form,
                "date":           dates[i],
                "accession_no":   accession_nos[i],
                "primary_doc":    documents[i],
                "cik":            cik
            })

    if not tenk_filings:
        print(f"[RedFlag] ERROR: No 10-K filings found for this company.")
        return None

    print(f"[RedFlag] Found {len(tenk_filings)} 10-K filings. Most recent: {tenk_filings[0]['date']}")
    return tenk_filings


# -----------------------------------------------------------------------------
# STEP 3 — DOWNLOAD THE ACTUAL 10-K DOCUMENT
# Using the accession number, we download the full text of the filing
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

    # Build the URL to the filing document
    # EDGAR stores files at a specific URL pattern using the accession number
    accession_clean = filing["accession_no"].replace("-", "")
    cik_clean       = filing["cik"].lstrip("0")  # Remove leading zeros for URL

    # Construct the filing index URL
    filing_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_clean}/{accession_clean}/{filing['primary_doc']}"
    )

    print(f"[RedFlag] Downloading 10-K from: {filing_url}")

    # Be polite to SEC servers — small delay before downloading
    time.sleep(0.5)

    response = requests.get(filing_url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not download filing. Status: {response.status_code}")
        return None

    print(f"[RedFlag] Successfully downloaded 10-K ({len(response.text):,} characters)")
    return response.text


# -----------------------------------------------------------------------------
# MAIN FUNCTION — Ties all 3 steps together
# Call this from other modules with just a ticker symbol
# -----------------------------------------------------------------------------
def fetch_10k(ticker):
    """
    Master function — fetches the two most recent 10-K filings for a ticker.
    Returns both so the comparator module can do year-over-year analysis.

    Args:
        ticker (str): Stock ticker e.g. "AAPL"

    Returns:
        dict: {
            "ticker": ticker,
            "latest": { "date": ..., "text": ... },
            "previous": { "date": ..., "text": ... }
        }
        None: If anything fails
    """

    # Step 1 — Get CIK
    cik = get_cik_from_ticker(ticker)
    if not cik:
        return None

    # Step 2 — Get list of 10-K filings
    filings = get_10k_filings(cik)
    if not filings:
        return None

    # Step 3 — Download the latest 10-K
    latest_text = download_10k_text(filings[0])
    if not latest_text:
        return None

    # Step 4 — Download the previous year's 10-K (for comparison)
    previous_text = None
    if len(filings) > 1:
        print(f"[RedFlag] Also fetching previous year's 10-K ({filings[1]['date']})...")
        time.sleep(0.5)
        previous_text = download_10k_text(filings[1])

    return {
        "ticker":   ticker.upper(),
        "latest":   {"date": filings[0]["date"], "text": latest_text},
        "previous": {"date": filings[1]["date"] if len(filings) > 1 else None,
                     "text": previous_text}
    }


# -----------------------------------------------------------------------------
# QUICK TEST — run this file directly to verify it works
# python edgar_fetcher.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    result = fetch_10k("AAPL")
    if result:
        print(f"\n[RedFlag] Test Complete")
        print(f"  Ticker:        {result['ticker']}")
        print(f"  Latest 10-K:   {result['latest']['date']}")
        print(f"  Previous 10-K: {result['previous']['date']}")
        print(f"  Latest size:   {len(result['latest']['text']):,} characters")# =============================================================================
# edgar_fetcher.py — SEC EDGAR Filing Fetcher
# =============================================================================
# This module connects to the SEC EDGAR free public API and retrieves the
# most recent 10-K annual report for any publicly traded US company.
#
# No API key required. No paid subscription. SEC EDGAR is free and public.
#
# Workflow:
#   1. Accept a stock ticker (e.g. "AAPL")
#   2. Convert ticker to SEC CIK number (unique company identifier)
#   3. Fetch the list of filings for that company
#   4. Find the most recent 10-K filing
#   5. Download the full text of that filing
# =============================================================================

import requests  # For making HTTP requests to SEC EDGAR
import json      # For parsing the JSON responses from EDGAR
import time      # For adding small delays so we don't overwhelm SEC servers


# -----------------------------------------------------------------------------
# CONSTANTS
# SEC EDGAR legally requires a real name and email in the User-Agent header
# This identifies who is making the request to their servers
# -----------------------------------------------------------------------------
HEADERS = {
    "User-Agent": "Ashutosh Tripathi tashu10cfc@gmail.com"
}

# Base URLs for the SEC EDGAR API
EDGAR_BASE_URL      = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


# -----------------------------------------------------------------------------
# STEP 1 — GET CIK NUMBER FROM TICKER
# Every company on SEC EDGAR has a unique CIK (Central Index Key) number
# We need this to look up their filings
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

    # SEC provides a master JSON file mapping all tickers to CIK numbers
    response = requests.get(COMPANY_TICKERS_URL, headers=HEADERS)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not reach SEC EDGAR. Status: {response.status_code}")
        return None

    # Parse the JSON response
    companies = response.json()

    # Search through all companies for our ticker
    for key, company in companies.items():
        if company["ticker"].upper() == ticker.upper():
            # CIK must be padded to 10 digits — SEC requirement
            cik = str(company["cik_str"]).zfill(10)
            print(f"[RedFlag] Found CIK: {cik} for {company['title']}")
            return cik

    # If we get here, the ticker wasn't found
    print(f"[RedFlag] ERROR: Ticker '{ticker}' not found in SEC EDGAR database.")
    return None


# -----------------------------------------------------------------------------
# STEP 2 — GET LIST OF 10-K FILINGS FOR THIS COMPANY
# Using the CIK, we fetch their complete filing history and find 10-Ks
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

    # EDGAR submissions endpoint — returns all filings for a company
    url = f"{EDGAR_BASE_URL}/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not fetch filings. Status: {response.status_code}")
        return None

    data = response.json()

    # Extract the recent filings section
    filings = data.get("filings", {}).get("recent", {})

    # Get the parallel arrays from EDGAR response
    forms         = filings.get("form", [])
    dates         = filings.get("filingDate", [])
    accession_nos = filings.get("accessionNumber", [])
    documents     = filings.get("primaryDocument", [])

    # Filter for only 10-K filings (annual reports)
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
# STEP 3 — DOWNLOAD THE ACTUAL 10-K DOCUMENT
# Using the accession number, we download the full text of the filing
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

    # Build the URL to the filing document
    accession_clean = filing["accession_no"].replace("-", "")
    cik_clean       = filing["cik"].lstrip("0")  # Remove leading zeros for URL

    # Construct the filing document URL
    filing_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_clean}/{accession_clean}/{filing['primary_doc']}"
    )

    print(f"[RedFlag] Downloading 10-K from SEC EDGAR...")

    # Be polite to SEC servers — small delay before downloading
    time.sleep(0.5)

    response = requests.get(filing_url, headers=HEADERS)

    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not download filing. Status: {response.status_code}")
        return None

    print(f"[RedFlag] Successfully downloaded 10-K ({len(response.text):,} characters)")
    return response.text


# -----------------------------------------------------------------------------
# MAIN FUNCTION — Ties all 3 steps together
# Call this from other modules with just a ticker symbol
# -----------------------------------------------------------------------------
def fetch_10k(ticker):
    """
    Master function — fetches the two most recent 10-K filings for a ticker.
    Returns both so the comparator module can do year-over-year analysis.

    Args:
        ticker (str): Stock ticker e.g. "AAPL"

    Returns:
        dict: {
            "ticker": ticker,
            "latest": { "date": ..., "text": ... },
            "previous": { "date": ..., "text": ... }
        }
        None: If anything fails
    """

    # Step 1 — Get CIK
    cik = get_cik_from_ticker(ticker)
    if not cik:
        return None

    # Step 2 — Get list of 10-K filings
    filings = get_10k_filings(cik)
    if not filings:
        return None

    # Step 3 — Download the latest 10-K
    latest_text = download_10k_text(filings[0])
    if not latest_text:
        return None

    # Step 4 — Download the previous year's 10-K (for comparison)
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
# QUICK TEST — run this file directly to verify it works
# python edgar_fetcher.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    result = fetch_10k("AAPL")
    if result:
        print(f"\n[RedFlag] Test Complete")
        print(f"  Ticker:        {result['ticker']}")
        print(f"  Latest 10-K:   {result['latest']['date']}")
        print(f"  Previous 10-K: {result['previous']['date']}")
        print(f"  Latest size:   {len(result['latest']['text']):,} characters")