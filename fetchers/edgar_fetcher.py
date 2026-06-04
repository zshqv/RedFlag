import requests
import time

HEADERS = {
    "User-Agent": "Ashutosh Tripathi tashu10cfc@gmail.com"
}

EDGAR_BASE_URL      = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def get_cik_from_ticker(ticker):
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


def get_10k_filings(cik):
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

    # Accept both 10-K (domestic) and 20-F (foreign private issuer)
    target_forms = {"10-K", "20-F"}
    tenk_filings = []
    for i, form in enumerate(forms):
        if form in target_forms:
            tenk_filings.append({
                "form":         form,
                "date":         dates[i],
                "accession_no": accession_nos[i],
                "primary_doc":  documents[i],
                "cik":          cik
            })
    if not tenk_filings:
        print(f"[RedFlag] ERROR: No 10-K or 20-F filings found for this company.")
        return None
    form_type = tenk_filings[0]["form"]
    print(f"[RedFlag] Found {len(tenk_filings)} {form_type} filings. Most recent: {tenk_filings[0]['date']}")
    return tenk_filings


def download_10k_text(filing):
    accession_clean = filing["accession_no"].replace("-", "")
    cik_clean       = filing["cik"].lstrip("0")
    filing_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_clean}/{accession_clean}/{filing['primary_doc']}"
    )
    form_label = filing.get("form", "10-K")
    print(f"[RedFlag] Downloading {form_label} from SEC EDGAR...")
    time.sleep(0.5)
    response = requests.get(filing_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"[RedFlag] ERROR: Could not download filing. Status: {response.status_code}")
        return None
    print(f"[RedFlag] Successfully downloaded {form_label} ({len(response.text):,} characters)")
    return response.text


def fetch_10k(ticker):
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
        prev_form = filings[1]["form"]
        print(f"[RedFlag] Also fetching previous year's {prev_form} ({filings[1]['date']})...")
        time.sleep(0.5)
        previous_text = download_10k_text(filings[1])
        previous_date = filings[1]["date"]
    form_type = filings[0]["form"]
    exchange_label = "SEC EDGAR (20-F / Foreign Private Issuer)" if form_type == "20-F" else "NYSE/NASDAQ"
    return {
        "ticker":   ticker.upper(),
        "exchange": exchange_label,
        "latest":   {"date": filings[0]["date"], "text": latest_text},
        "previous": {"date": previous_date, "text": previous_text}
    }
