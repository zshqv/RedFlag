# RedFlag

![MIT License](https://img.shields.io/badge/license-MIT-green.svg)

**RedFlag — a due diligence co-pilot that flags risk anomalies in financial filings so analysts and consultants don't miss what matters.**

> **Companion:** Trikosh tells you what a company looks like. RedFlag tells you what's wrong with it. [trikosh.io](https://trikosh.io)

---

## Supported Sources

| Source | Ticker Format | Data Provider |
|--------|--------------|---------------|
| US Public Companies | `AAPL`, `JPM` | SEC EDGAR (EDGAR full-text search) |
| UK Listed Companies | `HSBC.L`, `BP.L` | Companies House API + IR page fallback |
| India BSE / NSE | `RELIANCE.NS`, `TCS.BO` | BSE / NSE investor relations |
| Canada TSX / TSXV | `RY.TO`, `SU.TO` | SEDAR+ public filing search |
| Manual PDF | `--pdf "/path/to/file.pdf"` | Local file (any country) |

---

## Outputs

Every run produces **3 output files** in `output/`:

| File | Format | Contents |
|------|--------|----------|
| `TICKER_redflag.xlsx` | Excel | 3 sheets: Quick Brief · Risk Dashboard · YoY Comparison |
| `TICKER_redflag.pdf` | PDF | 7 pages: Cover · Methodology · HIGH/MEDIUM/LOW findings · YoY · Source |
| `TICKER_dashboard.pptx` | PowerPoint | 8 slides: Cover · Scorecard · Heat Map · All Flags · Top 3 · New Keywords · YoY · Methodology |

---

## Quick Start

```bash
pip install -r requirements.txt

# US company (SEC EDGAR)
python main.py AAPL

# UK company (Companies House)
python main.py HSBC.L

# India (BSE/NSE)
python main.py RELIANCE.NS

# Canada (SEDAR+)
python main.py RY.TO

# Manual PDF
python main.py --pdf "/path/to/annual_report.pdf"

# Peer comparison (generates individual + comparison output)
python main.py --compare JPM BAC GS
```

---

## Optional: Claude-Powered Explanations

Set `ANTHROPIC_API_KEY` in your environment to enable AI-generated 2-sentence explanations per finding using `claude-haiku-4-5-20251001`. Without the key, deterministic rule-based fallback templates are used automatically.

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## File Structure

| File | Description |
|------|-------------|
| `main.py` | CLI entry point — routes all inputs, runs full pipeline |
| `keywords.py` | 220+ risk keywords across 6 categories + 6 industry packs |
| `text_parser.py` | Extracts all 18 standard 10-K sections with page estimation |
| `risk_analyzer.py` | 3-tier severity scoring, full location metadata, co-occurrence |
| `comparator.py` | Year-over-year comparison: category deltas, new keywords, sentiment trend |
| `flag_explainer.py` | Claude API explanations per finding, rule-based fallback |
| `report_generator.py` | Generates Excel (3 sheets), PDF (7 pages), PPTX (8 slides) |
| `pdf_template.html` | Jinja2 / WeasyPrint HTML template for the PDF output |
| `fetchers/fetcher_router.py` | Routes to correct fetcher by ticker suffix or file path |
| `fetchers/edgar_fetcher.py` | SEC EDGAR — US 10-K filings |
| `fetchers/fca_fetcher.py` | Companies House API — UK annual reports |
| `fetchers/bse_fetcher.py` | BSE / NSE investor relations — India |
| `fetchers/sedar_fetcher.py` | SEDAR+ — Canada annual filings |
| `fetchers/pdf_fetcher.py` | Manual PDF ingestion via pdfplumber (any country) |
| `requirements.txt` | Full Python dependency list |

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

| Tier | Trigger | Score Modifier |
|------|---------|---------------|
| HIGH | Sentiment < -0.25 **or** keyword in always-high list | +20 |
| MEDIUM | Sentiment in (-0.25, -0.10) or mitigating language | — |
| LOW | Sentiment >= -0.10 | — |

Score modifiers: -15 (mitigating language in sentence), +15 (amplifying language), +10 (same keyword in 2+ findings in section). Base score: 50. Clamped 0-100.

---

## License

MIT — see [LICENSE](LICENSE)
