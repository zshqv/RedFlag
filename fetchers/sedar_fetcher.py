import requests
import re
import time
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "RedFlag-Analyzer tashu10cfc@gmail.com"
}


def fetch_filing(ticker):
    """
    Fetches Canadian annual report from SEDAR+ or IR page fallback.
    Ticker format: TD.TO, RY.TO
    """
    company_name = re.sub(r'\.(TO|TSX)$', '', ticker.upper())
    print(f"[RedFlag] SEDAR: Looking up annual report for {company_name}...")

    try:
        text, filing_date = _fetch_from_sedar(company_name)
        if text:
            return _build_result(ticker, "TSX", filing_date, text)
    except Exception as e:
        print(f"[RedFlag] SEDAR direct fetch failed: {e}. Trying IR fallback...")

    try:
        text, filing_date = _fetch_from_ir_search(company_name)
        if text:
            return _build_result(ticker, "TSX", filing_date, text)
    except Exception as e:
        print(f"[RedFlag] IR fallback also failed: {e}")

    return None


def _build_result(ticker, exchange, filing_date, text):
    return {
        "ticker":   ticker.upper(),
        "exchange": exchange,
        "latest":   {"date": filing_date or "N/A", "text": text},
        "previous": {"date": None, "text": None}
    }


def _fetch_from_sedar(company_name):
    url = (
        "https://www.sedarplus.ca/csa-party/records/search.html"
        f"?searchText={requests.utils.quote(company_name)}&category=Annual+Report"
    )
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        raise Exception(f"SEDAR+ returned status {resp.status_code}")
    soup = BeautifulSoup(resp.text, "lxml")
    links = soup.find_all("a", href=re.compile(r'annual.report', re.I))
    if not links:
        raise Exception("No annual report links found on SEDAR+")
    doc_url = links[0]["href"]
    if not doc_url.startswith("http"):
        doc_url = "https://www.sedarplus.ca" + doc_url
    time.sleep(0.5)
    doc_resp = requests.get(doc_url, headers=HEADERS, timeout=15)
    if doc_resp.status_code != 200:
        raise Exception(f"Document fetch failed: {doc_resp.status_code}")
    return doc_resp.text, "N/A"


def _fetch_from_ir_search(company_name):
    search_url = (
        "https://www.google.com/search"
        f"?q={requests.utils.quote(company_name)}+annual+report+filetype:pdf+investor+relations"
    )
    resp = requests.get(
        search_url,
        headers={**HEADERS, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        timeout=15
    )
    if resp.status_code != 200:
        raise Exception(f"Google search returned status {resp.status_code}")
    soup = BeautifulSoup(resp.text, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]
        if href.startswith("http") and ".pdf" in href.lower():
            try:
                import pdfplumber, io
                pdf_resp = requests.get(href, headers=HEADERS, timeout=30)
                if pdf_resp.status_code == 200:
                    with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
                        pages = [p.extract_text() or "" for p in pdf.pages[:100]]
                    return "\n\n".join(pages), "N/A"
            except Exception:
                continue
    raise Exception("No usable PDF found via Google search")


fetch_sedar = fetch_filing
