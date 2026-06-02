# =============================================================================
# risk_analyzer.py — RedFlag Core Analysis Engine
# v2 — Added location metadata, weighted severity scoring
# =============================================================================

import re
from textblob import TextBlob
from keywords import REDFLAG_KEYWORDS
from confidence_scorer import score_confidence


# Category weights for severity scoring
CATEGORY_WEIGHTS = {
    "Regulatory": 1.2,
    "Legal":      1.1,
    "Financial":  1.0,
    "Operational": 0.9,
}


def calculate_severity_score(polarity, category):
    """
    Maps TextBlob polarity [-1, +1] to severity score [0, 100].
    polarity=-1 (most negative/risky) → base=100
    polarity=0  (neutral)             → base=50
    polarity=+1 (positive)            → base=0
    Then multiplied by category weight and capped at 100.
    """
    base = (1.0 - polarity) / 2.0 * 100.0
    weight = CATEGORY_WEIGHTS.get(category, 1.0)
    return min(100, int(round(base * weight)))


def interpret_severity(score):
    """Derives risk label from severity score (0-100)."""
    if score >= 70:
        return "HIGH RISK"
    elif score >= 40:
        return "ELEVATED RISK"
    elif score >= 20:
        return "NEUTRAL"
    else:
        return "LOW RISK"


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def scan_section(section_name, section_text):
    """
    Scans a section for risk keywords.
    Splits by paragraph first (\\n\\n), then by sentence within each paragraph.
    Records para_num, sentence_num, context_before, context_after per finding.
    """
    findings = []

    # Split into paragraphs first for location tracking
    paragraphs = section_text.split('\n\n')

    for para_num, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue

        sentences = split_into_sentences(paragraph)
        if not sentences:
            continue

        for sentence_num, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            for category, keywords in REDFLAG_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in sentence_lower:
                        blob = TextBlob(sentence)
                        sentiment_score = round(blob.sentiment.polarity, 3)
                        severity_score  = calculate_severity_score(sentiment_score, category)
                        sentiment_label = interpret_severity(severity_score)

                        context_before = sentences[sentence_num - 1][:300] if sentence_num > 0 else ""
                        context_after  = sentences[sentence_num + 1][:300] if sentence_num < len(sentences) - 1 else ""

                        findings.append({
                            "section":         section_name,
                            "category":        category,
                            "keyword":         keyword,
                            "sentence":        sentence[:500],
                            "sentiment_score": sentiment_score,
                            "sentiment_label": sentiment_label,
                            "severity_score":  severity_score,
                            "para_num":        para_num,
                            "sentence_num":    sentence_num,
                            "context_before":  context_before,
                            "context_after":   context_after,
                        })
                        break  # one keyword match per sentence per category
                else:
                    continue
                break  # one category match per sentence

    return findings


def analyze_filings(sections):
    all_findings = []

    for section_name, section_text in sections.items():
        if not section_text:
            print(f"[RedFlag] Skipping empty section: {section_name}")
            continue

        print(f"[RedFlag] Scanning section: {section_name}...")
        findings = scan_section(section_name, section_text)
        all_findings.extend(findings)
        print(f"[RedFlag] Found {len(findings)} red flags in '{section_name}'")

    summary = {}
    for finding in all_findings:
        category = finding["category"]
        summary[category] = summary.get(category, 0) + 1

    # Sort by severity score descending (highest severity first)
    all_findings.sort(key=lambda x: x["severity_score"], reverse=True)

    # Add confidence score to every finding (uses full list for co-occurrence)
    for finding in all_findings:
        finding["confidence_score"] = score_confidence(finding, all_findings)

    print(f"\n[RedFlag] Total red flags found: {len(all_findings)}")

    return {
        "findings": all_findings,
        "summary":  summary
    }


if __name__ == "__main__":
    from fetchers.edgar_fetcher import fetch_10k
    from text_parser import extract_sections

    print("[RedFlag] Fetching Apple 10-K...\n")
    result = fetch_10k("AAPL")

    if result:
        print("\n[RedFlag] Extracting sections...\n")
        sections = extract_sections(result["latest"]["text"])

        print("\n[RedFlag] Running risk analysis...\n")
        analysis = analyze_filings(sections)

        print("\n[RedFlag] Risk Analysis Summary:")
        print("-" * 50)
        for category, count in analysis["summary"].items():
            print(f"  {category}: {count} findings")

        print(f"\n[RedFlag] Top 5 Highest Severity Findings:")
        print("-" * 50)
        for finding in analysis["findings"][:5]:
            print(f"\n  Category:      {finding['category']}")
            print(f"  Keyword:       {finding['keyword']}")
            print(f"  Severity:      {finding['severity_score']}")
            print(f"  Risk:          {finding['sentiment_label']}")
            print(f"  Location:      Para {finding['para_num']}, Sentence {finding['sentence_num']}")
            print(f"  Context Before: {finding['context_before'][:80]}...")
