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
    Fetches UK company annual report.
    Ticker format: HSBC.L, BP.L
    """
    company_name = re.sub(r'\.L$', '', ticker.upper())
    print(f"[RedFlag] FCA/LSE: Looking up annual report for {company_name}...")

    try:
        result = _fetch_annual_report(company_name)
        if result:
            return {
                "ticker":   ticker.upper(),
                "exchange": "LSE",
                "latest":   {"date": result.get("date", "N/A"), "text": result["text"]},
                "previous": {"date": None, "text": None}
            }
    except Exception as e:
        print(f"[RedFlag] FCA/LSE fetch failed: {e}")

    return None


def _fetch_annual_report(company_name):
    import pdfplumber

    # Search for the annual report PDF
    search_url = (
        "https://www.google.com/search"
        f"?q={requests.utils.quote(company_name)}+annual+report+2024+PDF+filetype:pdf"
    )
    resp = requests.get(
        search_url,
        headers={**HEADERS, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        timeout=15
    )
    if resp.status_code != 200:
        raise Exception(f"Search returned status {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")

    pdf_urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]
        if href.startswith("http") and ".pdf" in href.lower():
            if "annual" in href.lower() or "report" in href.lower():
                pdf_urls.append(href)

    if not pdf_urls:
        raise Exception("No annual report PDF found in search results")

    time.sleep(0.5)
    for pdf_url in pdf_urls[:3]:
        try:
            pdf_resp = requests.get(pdf_url, headers=HEADERS, timeout=30)
            if pdf_resp.status_code == 200 and len(pdf_resp.content) > 10000:
                with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages[:100]]
                text = "\n\n".join(pages)
                if len(text) > 1000:
                    return {"text": text, "date": "N/A"}
        except Exception:
            continue

    raise Exception("Could not extract text from any found PDF")


fetch_fca = fetch_filing
