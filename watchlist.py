import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

WATCHLIST_FILE = "watchlist.json"
STATE_FILE     = os.path.join("output", "watchlist_state.json")


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    try:
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_watchlist(tickers):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(tickers, f, indent=2)


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    os.makedirs("output", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _has_worsened(old_traj, new_traj):
    """True if trajectory moved from stable/improving to deteriorating/increasing."""
    old_u    = old_traj.upper()
    new_u    = new_traj.upper()
    bad_sigs = ("DETERIORATING", "INCREASING", "WORSENING")
    old_bad  = any(s in old_u for s in bad_sigs)
    new_bad  = any(s in new_u for s in bad_sigs)
    return (not old_bad) and new_bad


def send_alert_email(ticker, old_trajectory, new_trajectory, findings_count):
    """Send Gmail alert when a ticker's trajectory worsens. Silently skips if env vars missing."""
    user     = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not password:
        print(f"[RedFlag] Watchlist: email alert skipped for {ticker} "
              f"(GMAIL_USER / GMAIL_APP_PASSWORD not set in environment)")
        return

    subject = f"RedFlag Alert: {ticker} Risk Trajectory Worsened"
    body = (
        f"RedFlag Risk Intelligence -- Watchlist Alert\n"
        f"{'=' * 50}\n\n"
        f"Ticker:           {ticker}\n"
        f"Previous Status:  {old_trajectory}\n"
        f"Current Status:   {new_trajectory}\n"
        f"Total Findings:   {findings_count}\n\n"
        f"The risk trajectory for {ticker} has worsened from '{old_trajectory}' "
        f"to '{new_trajectory}'. Please review the latest 10-K filing.\n\n"
        f"Source:  SEC EDGAR public filings\n"
        f"Tool:    github.com/zshqv/RedFlag\n"
    )

    try:
        msg = MIMEMultipart()
        msg["From"]    = user
        msg["To"]      = user
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user, password)
            server.send_message(msg)
        print(f"[RedFlag] Watchlist: alert email sent for {ticker}")
    except Exception as e:
        print(f"[RedFlag] Watchlist: failed to send email for {ticker}: {e}")


def run_watchlist_check():
    """Run the full analysis pipeline for every ticker in watchlist.json."""
    from fetchers.fetcher_router import fetch_filing
    from text_parser import extract_sections
    from risk_analyzer import analyze_filings
    from comparator import compare_years

    tickers = load_watchlist()
    if not tickers:
        print("[RedFlag] Watchlist is empty.")
        print('[RedFlag] Edit watchlist.json and add tickers, e.g.: ["AAPL", "JPM"]')
        return

    state     = _load_state()
    new_state = {}
    changed   = []
    unchanged = []

    print(f"[RedFlag] Checking {len(tickers)} watchlist ticker(s)...\n")

    for ticker in tickers:
        print(f"[RedFlag] Watchlist: processing {ticker}...")
        try:
            result = fetch_filing(ticker)
            if not result:
                print(f"[RedFlag] Watchlist: could not fetch {ticker} -- skipping")
                unchanged.append((ticker, "FETCH_FAILED"))
                continue

            latest_sections = extract_sections(result["latest"]["text"])
            latest_analysis = analyze_filings(latest_sections)

            if result["previous"]["text"]:
                prev_sections = extract_sections(result["previous"]["text"])
                prev_analysis = analyze_filings(prev_sections)
            else:
                prev_analysis = {"findings": [], "summary": {}}

            comparison = compare_years(latest_analysis, prev_analysis)
            trajectory = comparison["overall"].get("trajectory", "STABLE")
            n_findings = len(latest_analysis.get("findings", []))

            old_traj          = state.get(ticker, "STABLE")
            new_state[ticker] = trajectory

            if _has_worsened(old_traj, trajectory):
                print(f"[RedFlag] Watchlist: {ticker} WORSENED ({old_traj} -> {trajectory})")
                changed.append((ticker, old_traj, trajectory, n_findings))
                send_alert_email(ticker, old_traj, trajectory, n_findings)
            else:
                print(f"[RedFlag] Watchlist: {ticker} stable ({trajectory})")
                unchanged.append((ticker, trajectory))

        except Exception as e:
            print(f"[RedFlag] Watchlist: error processing {ticker}: {e}")
            unchanged.append((ticker, "ERROR"))

    _save_state(new_state)

    print(f"\n{'=' * 50}")
    print("[RedFlag] Watchlist Check Complete")
    print(f"  Tickers checked: {len(tickers)}")
    if changed:
        print(f"  ALERTS ({len(changed)}):")
        for t, old, new, n in changed:
            print(f"    {t}: {old} -> {new}  ({n} findings)")
    if unchanged:
        print(f"  Unchanged ({len(unchanged)}):")
        for item in unchanged:
            print(f"    {item[0]}: {item[1]}")
    print()


if __name__ == "__main__":
    print("watchlist imported successfully")
