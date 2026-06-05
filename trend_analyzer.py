import time

CATEGORIES = ["Financial", "Regulatory", "Operational", "Legal"]


def analyze_trend(ticker):
    """Fetch up to 5 years of 10-K filings and return per-year category risk counts."""
    try:
        from fetchers.edgar_fetcher import get_cik_from_ticker, get_10k_filings, download_10k_text
    except ImportError:
        from edgar_fetcher import get_cik_from_ticker, get_10k_filings, download_10k_text

    from text_parser import extract_sections
    from risk_analyzer import analyze_filings

    print(f"[RedFlag] Trend: fetching up to 5 years of 10-K filings for {ticker}...")

    cik = get_cik_from_ticker(ticker)
    if not cik:
        return {"error": f"Could not find CIK for ticker '{ticker}'"}

    filings = get_10k_filings(cik)
    if not filings:
        return {"error": f"No 10-K filings found for '{ticker}'"}

    # One filing per calendar year, up to 5
    seen_years = set()
    target_filings = []
    for f in filings:
        year = f["date"][:4]
        if year not in seen_years:
            seen_years.add(year)
            target_filings.append(f)
        if len(target_filings) >= 5:
            break

    results = {}  # int(year) -> summary dict

    for filing in target_filings:
        year = int(filing["date"][:4])
        try:
            print(f"[RedFlag] Trend: downloading {year} filing...")
            time.sleep(0.3)
            text = download_10k_text(filing)
            if not text:
                print(f"[RedFlag] Trend: skipping {year} -- download returned None")
                continue
            sections = extract_sections(text)
            analysis = analyze_filings(sections)
            results[year] = analysis.get("summary", {})
            print(f"[RedFlag] Trend: {year} done ({len(analysis.get('findings', []))} findings)")
        except Exception as e:
            print(f"[RedFlag] Trend: skipping {year} -- {e}")
            continue

    if len(results) < 2:
        return {"error": "Insufficient historical data (fewer than 2 years fetched successfully)"}

    years_sorted = sorted(results.keys())
    trend = {"years": years_sorted}
    for cat in CATEGORIES:
        trend[cat] = [results[y].get(cat, 0) for y in years_sorted]

    return trend


if __name__ == "__main__":
    print("trend_analyzer imported successfully")
