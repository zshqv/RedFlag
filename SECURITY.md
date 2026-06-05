# Security Policy

## Is RedFlag safe to run locally?

Yes. RedFlag is a read-only tool. It fetches public filings from SEC EDGAR,
analyzes them locally on your machine, and writes output files to a local folder.
It does not send your data anywhere, does not require login or authentication,
and does not modify any system files.

---

## What steps were taken to ensure security?

The following checks were completed as part of a full sanity and security audit:

- **No hardcoded credentials** — The SEC EDGAR User-Agent header is read from the
  `EDGAR_USER_AGENT` environment variable. No real name or email is stored in the
  repository. If the variable is not set, a generic placeholder is used.

- **No eval or exec calls** — No file in the codebase uses `eval()` or `exec()` on
  any data fetched from SEC EDGAR or provided by the user.

- **All output is written locally and gitignored** — Generated files are saved to an
  `output/` folder that is listed in `.gitignore`. Output files are never committed
  to version control.

- **No third-party network calls** — The only external domain RedFlag contacts is
  `sec.gov` (SEC EDGAR public API). No data is sent to any other service or server.

- **No dangerous import libraries** — No file imports `openpyxl`, `python-pptx`, or
  any library that writes to formats outside the stated outputs (HTML, PDF).

- **Dependency surface is minimal** — `requirements.txt` contains exactly five
  libraries: requests, beautifulsoup4, textblob, fpdf2, pandas.

- **Output folder and sensitive files are gitignored** — `.gitignore` explicitly
  covers `output/`, `__pycache__/`, `*.pyc`, `.env`, and `.venv`.

---

## Network activity

The only domain RedFlag contacts is `sec.gov` (SEC EDGAR public API).
Specific endpoints used:

- `https://www.sec.gov/files/company_tickers.json` — ticker-to-CIK lookup
- `https://data.sec.gov/submissions/CIK{cik}.json` — filing history
- `https://www.sec.gov/Archives/edgar/data/...` — filing document download

No data is sent outbound. All processing and output generation happens locally.

---

## Reporting a vulnerability

If you discover a security issue, open a GitHub Issue marked `[SECURITY]`
or contact the maintainer directly via GitHub.
