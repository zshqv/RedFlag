# RedFlag

![MIT License](https://img.shields.io/badge/license-MIT-green.svg)

**RedFlag — a due diligence co-pilot that flags risk anomalies in financial filings so analysts don't miss what matters.**

> **Before: 3 hours manually reading a 300-page 10-K. After: 60 seconds.**

RedFlag fetches the latest annual filing for any ticker, scans it against 220+ risk keywords across 6 categories, scores every finding by severity, and produces a ready-to-share HTML report and a keyword glossary PDF — no spreadsheet wrangling required.

> **Companion:** Trikosh tells you what a company looks like. RedFlag tells you what's wrong with it. [trikosh.io](https://trikosh.io)

---

## Case Study: Sony 20-F

Sony's 2024 20-F (annual report) processed end-to-end. Open the HTML report to see the full risk findings, severity scores, year-over-year trajectory, and keyword breakdown.

**[View Sony Report →](case-studies/SONY_McKinsey_report.html)**

---

## Supported Sources

| Source | Ticker Format | Data Provider |
|--------|--------------|---------------|
| US Public Companies | `AAPL`, `JPM` | SEC EDGAR |
| UK Listed Companies | `HSBC.L`, `BP.L` | Companies House API + IR page fallback |
| India BSE / NSE | `RELIANCE.NS`, `TCS.BO` | BSE / NSE investor relations |
| Canada TSX / TSXV | `RY.TO`, `SU.TO` | SEDAR+ public filing search |
| Manual PDF | `--pdf "/path/to/file.pdf"` | Local file (any country) |

---

## Outputs

Every run produces **2 files** in `output/`:

| File | Format | Contents |
|------|--------|----------|
| `TICKER_report.html` | HTML | Full risk report: verdict · HIGH / MEDIUM / LOW findings with location metadata · year-over-year trajectory · category heat map · methodology |
| `TICKER_glossary.pdf` | PDF | Every triggered keyword — deduplicated, with the section it first appeared in and a plain-English explanation of the risk it represents |

---

## Quick Start

```bash
pip install -r requirements.txt

# US company (SEC EDGAR)
python main.py AAPL

# UK company (Companies House)
python main.py HSBC.L

# India (BSE / NSE)
python main.py RELIANCE.NS

# Canada (SEDAR+)
python main.py RY.TO

# Manual PDF (any country)
python main.py --pdf "/path/to/annual_report.pdf"

# Peer comparison
python main.py --compare JPM BAC GS
```

Output files open automatically from the `output/` folder after each run.

---

## Optional: Claude-Powered Explanations

Set `ANTHROPIC_API_KEY` to enable AI-generated 2-sentence explanations per finding using `claude-haiku-4-5-20251001`. Without the key, deterministic rule-based fallback templates are used automatically — the tool works fully offline.

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## File Structure

```
redflag/
├── main.py                     # CLI entry point — routes all inputs, runs full pipeline
├── risk_analyzer.py            # 3-tier severity scoring, location metadata, co-occurrence
├── keywords.py                 # 220+ risk keywords across 6 categories + 6 industry packs
├── text_parser.py              # Extracts all 18 standard 10-K sections
├── comparator.py               # Year-over-year deltas, new keywords, sentiment trend
├── flag_explainer.py           # Claude API explanations per finding, rule-based fallback
├── report_generator.py         # Renders HTML report via Jinja2 template
├── glossary_generator.py       # Generates Glossary PDF from triggered keywords
├── pdf_template.html           # Jinja2 template for the HTML report
├── confidence_scorer.py        # Confidence scoring layer
├── trend_analyzer.py           # 5-year historical trend analysis
├── dashboard.py                # Optional Streamlit web UI
├── watchlist.py                # Persistent ticker watchlist
├── comparator.py               # YoY comparison engine
├── fetchers/
│   ├── fetcher_router.py       # Routes to correct fetcher by ticker suffix or file path
│   ├── edgar_fetcher.py        # SEC EDGAR — US 10-K / 20-F filings
│   ├── fca_fetcher.py          # Companies House API — UK annual reports
│   ├── bse_fetcher.py          # BSE / NSE investor relations — India
│   ├── sedar_fetcher.py        # SEDAR+ — Canada annual filings
│   └── pdf_fetcher.py          # Manual PDF ingestion via pdfplumber
├── case-studies/
│   └── SONY_McKinsey_report.html   # Sony 20-F full risk report (sample output)
├── requirements.txt
└── output/                     # Generated files (gitignored)
```

---

## Keyword Library — v2.0

220+ keywords across 6 risk categories, with 6 industry-specific packs:

| Category | Keywords | Examples |
|----------|---------|---------|
| Legal / Litigation | 45 | class action, indictment, consent decree, whistleblower |
| Regulatory / Compliance | 40 | OFAC, AML, material weakness, SOX 404, data breach |
| Financial / Liquidity | 40 | going concern, covenant breach, goodwill impairment, cash burn |
| Operational / Strategic | 40 | key person, customer concentration, force majeure, product recall |
| Governance / ESG | 30 | self-dealing, poison pill, dual class shares, ESG rating downgrade |
| Forward-Looking / Uncertainty | 25 | no assurance, headwinds, recessionary conditions |

Industry packs: **Banking · Technology · Healthcare · Energy · Real Estate · Consulting**

---

## Severity Scoring

Each finding is scored 0–100:

| Tier | Trigger | Score Modifier |
|------|---------|---------------|
| HIGH | Sentiment < −0.25 **or** keyword on always-high list | +20 |
| MEDIUM | Sentiment in (−0.25, −0.10) or mitigating language present | — |
| LOW | Sentiment ≥ −0.10 | — |

Additional modifiers: −15 (mitigating language in flagged sentence) · +15 (amplifying language) · +10 (same keyword appears in 2+ findings in the same section). Base score: 50. Clamped 0–100.

---

## License

MIT — see [LICENSE](LICENSE)
