# RedFlag

![MIT License](https://img.shields.io/badge/license-MIT-green.svg)

**Flags the risk anomalies in SEC filings your human eye misses.**

---

## What It Is

RedFlag is an automated Python tool that fetches 10-K filings from SEC EDGAR and scans them for risk language across four categories: Legal, Financial, Operational, and Regulatory.

---

## Outputs

RedFlag produces exactly two files per run:

1. **HTML Report** — full risk analysis by section, keyword category, sentiment score, and year-over-year comparison
2. **Glossary PDF** — one entry per unique risk keyword, with the section it appeared in and a plain-English explanation of why it is a red flag

---

## Before vs After

| | Before | After |
|---|---|---|
| Time | 3–4 hours manually reading a 300-page 10-K, Ctrl+F, hand-typed notes | Under 60 seconds |
| Output | Notes scattered across tabs | HTML report + Glossary PDF ready instantly |

---

## Usage

```bash
python main.py AAPL
```

---

## File Structure

```
RedFlag/
├── main.py
├── edgar_fetcher.py
├── keywords.py
├── text_parser.py
├── risk_analyzer.py
├── comparator.py
├── report_generator.py
├── glossary_generator.py
├── case-studies/
│   ├── Sony_RedFlag_CaseStudy.html
│   └── Sony_RedFlag_Glossary.pdf
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| `requests` | SEC EDGAR API calls |
| `beautifulsoup4` | Parses raw HTML filings |
| `textblob` | Sentiment scoring |
| `fpdf2` | Generates the Glossary PDF |
| `pandas` | Structures and compares data |

---

## Philosophy

Every paid financial data provider — Bloomberg, FactSet, Capital IQ — is reselling EDGAR data with a better interface. EDGAR is the primary source. It's free, public, and updated in real time. RedFlag goes directly to the source.

---

## Ecosystem

RedFlag is built alongside [Trikosh](https://trikosh.io) — an open-source financial research platform covering 120 global companies across Financial Services, AI, and Healthcare. Trikosh tells you what a company looks like. RedFlag tells you what's wrong with it.

---

## Roadmap

- [ ] EU filings support — integrate ESMA and Companies House (UK) filing APIs
- [ ] India filings support — integrate BSE India disclosure portal
- [ ] Multi-company watchlist — run RedFlag across a portfolio of tickers in one command

---

## License

MIT
