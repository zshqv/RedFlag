import sys
import os

# Ensure the parent RedFlag directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def fetch_filing(ticker):
    """
    Routes to the correct fetcher based on ticker suffix.
    .NS / .BO  -> BSE India fetcher
    .TO        -> SEDAR+ Canada fetcher
    .L         -> FCA/LSE UK fetcher
    no suffix  -> SEC EDGAR fetcher

    Returns unified dict:
        {ticker, exchange, latest: {date, text}, previous: {date, text}}
    Returns None on failure (errors logged, not raised).
    """
    ticker = ticker.strip()
    upper  = ticker.upper()

    try:
        if upper.endswith(".NS") or upper.endswith(".BO"):
            from fetchers.bse_fetcher import fetch_filing as _fetch
            print(f"[RedFlag] Routing {ticker} -> BSE India fetcher")
            return _fetch(ticker)

        elif upper.endswith(".TO") or upper.endswith(".TSX"):
            from fetchers.sedar_fetcher import fetch_filing as _fetch
            print(f"[RedFlag] Routing {ticker} -> SEDAR+ Canada fetcher")
            return _fetch(ticker)

        elif upper.endswith(".L"):
            from fetchers.fca_fetcher import fetch_filing as _fetch
            print(f"[RedFlag] Routing {ticker} -> FCA/LSE UK fetcher")
            return _fetch(ticker)

        else:
            # US exchanges: NYSE, NASDAQ, or plain ticker
            from fetchers.edgar_fetcher import fetch_10k
            print(f"[RedFlag] Routing {ticker} -> SEC EDGAR fetcher")
            result = fetch_10k(ticker)
            if result and "exchange" not in result:
                result["exchange"] = "NYSE/NASDAQ"
            return result

    except Exception as e:
        print(f"[RedFlag] ERROR: Fetcher failed for '{ticker}': {e}")
        return None
