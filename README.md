# RedFlag 🚩

**Flags the risk anomalies in SEC filings your human eye misses.**

A junior analyst spends 3–4 hours manually reading through a 200-page SEC 10-K filing, hunting for red flags buried in legal language. RedFlag does it in under 60 seconds — pulling the filing, scanning for risk language across four categories, scoring sentiment, comparing year-over-year, and exporting a clean Excel and PDF report.

Free. Open-source. Built for analysts who don't have Bloomberg.

---

## What It Does

| Step | What Happens |
|---|---|
| 1 | You provide a stock ticker — e.g. `AAPL` |
| 2 | RedFlag pulls the latest 10-K directly from SEC EDGAR |
| 3 | It isolates the high-risk sections — Risk Factors, MD&A, Financial Notes |
| 4 | It flags hundreds of risk keywords across Legal, Financial, Operational, and Regulatory categories |
| 5 | It scores the sentiment of the language surrounding each flag |
| 6 | It compares this year's filing to last year's — tracking if risk language is increasing |
| 7 | It exports a structured Excel report and a one-page PDF summary |

---

## Before vs. After

| | Before RedFlag | After RedFlag |
|---|---|---|
| Time per filing | 3–4 hours | Under 60 seconds |
| Process | Manual keyword search, Ctrl+F, highlighter | One command |
| Output | Hand-typed notes in Word | Structured Excel + PDF report |
| Year-on-year comparison | Done manually across two browser tabs | Automated |
| Coverage | One filing per analyst session | Any SEC-registered company, instantly |

---

## Output

Running RedFlag on any ticker produces two files:

- **`TICKER_risk_report.xlsx`** — Categorised keyword hits by section and risk type, sentiment scores, and year-over-year comparison
- **`TICKER_summary.pdf`** — One-page executive summary of the highest-priority flags

Sample output for Apple Inc. is included in the `/sample_output` folder.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/zshqv/redflag.git
cd redflag

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py AAPL
```

Replace `AAPL` with any valid stock ticker. RedFlag handles the rest.

---

## Project Structure

```
redflag/
│
├── main.py               # Entry point — run this
├── keywords.py           # Master risk keyword library across 4 categories
├── edgar_fetcher.py      # Pulls 10-K filings directly from SEC EDGAR API
├── text_parser.py        # Extracts and cleans high-risk sections
├── risk_analyzer.py      # Keyword flagging + sentiment scoring
├── comparator.py         # Year-over-year risk language comparison
├── report_generator.py   # Exports Excel + PDF reports
├── requirements.txt      # All dependencies
└── sample_output/        # Pre-generated sample reports for AAPL
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| `requests` | HTTP calls to SEC EDGAR free API |
| `beautifulsoup4` | Parses raw HTML filing documents |
| `nltk` / `textblob` | Sentiment scoring on flagged text |
| `pandas` | Structures and compares data |
| `openpyxl` | Builds the Excel report |
| `fpdf2` | Generates the PDF summary |

All tools are free and open-source. No API keys required.

---

## Why SEC EDGAR

Every paid financial data provider — Bloomberg, FactSet, Capital IQ — is reselling EDGAR data with a better interface. EDGAR is the primary source. It's free, public, and updated in real time. RedFlag goes directly to the source.

---

## Part of the Open-Source Finance Ecosystem

RedFlag is built alongside **[Trikosh](https://trikosh.io)** — an open-source financial research infrastructure platform covering 30 global companies across Financial Services, AI, and Healthcare.

> Trikosh gives you the data. RedFlag tells you what's wrong with it.

Both tools are built on the same philosophy: financial research infrastructure should not cost $24,000 a year.

---

## Contributing

Pull requests are welcome. If you're a finance student or analyst and want to add keywords, improve the sentiment model, or extend coverage — open an issue and let's talk.

---

## License

MIT License — free to use, modify, and distribute with attribution.

Built by [Ashutosh Tripathi](https://github.com/zshqv)
