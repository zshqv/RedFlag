import sys
import os

# Ensure the parent RedFlag directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def fetch_filing(ticker):
    """
    Routes to the correct fetcher based on ticker suffix or file path.
    .NS / .BO  -> BSE India fetcher
    .TO        -> SEDAR+ Canada fetcher
    .L         -> FCA/LSE UK fetcher
    .pdf file or --pdf prefix -> Manual PDF fetcher
    no suffix  -> SEC EDGAR fetcher

    Returns unified dict:
        {ticker, exchange, latest: {date, text}, previous: {date, text}}
    Returns None on failure (errors logged, not raised).
    """
    ticker = ticker.strip()
    upper  = ticker.upper()

    try:
        if upper.endswith(".PDF") or ticker.startswith("--pdf"):
            from fetchers.pdf_fetcher import fetch_pdf
            print(f"[RedFlag] Source detected: Manual PDF")
            # For --pdf, strip the prefix to get the path
            file_path = ticker[6:] if ticker.startswith("--pdf") else ticker
            return fetch_pdf(file_path)

        elif upper.endswith(".NS") or upper.endswith(".BO"):
            from fetchers.bse_fetcher import fetch_filing as _fetch
            print(f"[RedFlag] Source detected: BSE/NSE (India)")
            return _fetch(ticker)

        elif upper.endswith(".TO") or upper.endswith(".TSX"):
            from fetchers.sedar_fetcher import fetch_filing as _fetch
            print(f"[RedFlag] Source detected: SEDAR+ (Canada)")
            return _fetch(ticker)

        elif upper.endswith(".L"):
            from fetchers.fca_fetcher import fetch_filing as _fetch
            print(f"[RedFlag] Source detected: Companies House (UK)")
            return _fetch(ticker)

        else:
            # US exchanges: NYSE, NASDAQ, or plain ticker
            from fetchers.edgar_fetcher import fetch_10k
            print(f"[RedFlag] Source detected: SEC EDGAR (US)")
            result = fetch_10k(ticker)
            if result and "exchange" not in result:
                result["exchange"] = "NYSE/NASDAQ"
            return result

    except Exception as e:
        print(f"[RedFlag] ERROR: Fetcher failed for '{ticker}': {e}")
        return None


route_fetcher = fetch_filing
