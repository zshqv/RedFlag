import requests
import re
import time
import io
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "RedFlag-Analyzer tashu10cfc@gmail.com"
}


def fetch_filing(ticker):
    """
    Fetches Indian company annual report from BSE India.
    Ticker format: RELIANCE.NS or TCS.BO
    """
    company_name = re.sub(r'\.(NS|BO)$', '', ticker.upper())
    print(f"[RedFlag] BSE: Looking up annual report for {company_name}...")

    try:
        result = _fetch_from_bse(company_name)
        if result:
            return {
                "ticker":   ticker.upper(),
                "exchange": "BSE/NSE",
                "latest":   {"date": result.get("date", "N/A"), "text": result["text"]},
                "previous": {"date": None, "text": None}
            }
    except Exception as e:
        print(f"[RedFlag] BSE fetch failed: {e}")

    return None


def _fetch_from_bse(company_name):
    import pdfplumber

    # BSE corporate announcements search
    search_url = (
        "https://www.bseindia.com/corporates/ann.html"
        f"?scripcode=&companyname={requests.utils.quote(company_name)}&anntype=Annual+Report"
    )
    resp = requests.get(search_url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"BSE returned status {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")

    pdf_links = []
    for a in soup.find_all("a", href=re.compile(r'\.pdf$', re.I)):
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.bseindia.com" + href
        pdf_links.append(href)

    if not pdf_links:
        # Try fallback: search for PDF via Google
        return _fallback_google_search(company_name)

    time.sleep(0.5)
    pdf_resp = requests.get(pdf_links[0], headers=HEADERS, timeout=30)
    if pdf_resp.status_code != 200:
        raise Exception(f"PDF download failed: {pdf_resp.status_code}")

    with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages[:100]]
    return {"text": "\n\n".join(pages), "date": "N/A"}


def _fallback_google_search(company_name):
    import pdfplumber

    search_url = (
        "https://www.google.com/search"
        f"?q={requests.utils.quote(company_name)}+BSE+annual+report+PDF+2024"
    )
    resp = requests.get(
        search_url,
        headers={**HEADERS, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        timeout=15
    )
    if resp.status_code != 200:
        raise Exception("Google fallback search failed")

    soup = BeautifulSoup(resp.text, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]
        if href.startswith("http") and ".pdf" in href.lower():
            try:
                pdf_resp = requests.get(href, headers=HEADERS, timeout=30)
                if pdf_resp.status_code == 200:
                    with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
                        pages = [p.extract_text() or "" for p in pdf.pages[:100]]
                    return {"text": "\n\n".join(pages), "date": "N/A"}
            except Exception:
                continue

    raise Exception("No PDF found via BSE or Google fallback")


fetch_bse = fetch_filing
