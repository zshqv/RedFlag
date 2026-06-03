# =============================================================================
# risk_analyzer.py — Risk Finding Extraction & Severity Scoring (v2.0)
# =============================================================================

import re
from textblob import TextBlob
from keywords import KEYWORDS
from flag_explainer import explain_finding

# 3-Tier Severity Thresholds
HIGH_SEVERITY_KEYWORDS = [
    "going concern", "material weakness", "restatement",
    "criminal charges", "under investigation", "indictment",
    "class action", "securities fraud", "data breach",
    "cybersecurity incident", "cannot guarantee", "no assurance",
    "whistleblower",
]

MITIGATING_PHRASES = [
    "we believe", "we expect", "we intend", "we are confident",
    "mitigated", "resolved", "we have taken steps", "management intends",
]

AMPLIFYING_PHRASES = [
    "material adverse", "significant risk", "cannot guarantee",
    "no assurance", "under investigation", "subject to litigation",
]

CATEGORY_MAPPING = {
    "Legal": "Legal",
    "Regulatory": "Regulatory",
    "Financial": "Financial",
    "Operational": "Operational",
    "Governance": "Governance",
    "Forward-Looking": "Forward-Looking",
}


def split_into_sentences(text):
    """Split text into sentences, handling common edge cases."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def calculate_severity_score(finding):
    """
    Calculate severity score (0-100) based on multiple factors.

    Base: 50
    +20 if severity == HIGH
    -15 if mitigating language in flagged_sentence
    -10 if mitigating language in context_after
    +15 if amplifying language present
    +10 if same keyword appears in 2+ other findings in same section
    Clamped to 0-100
    """
    score = 50

    severity = finding.get("severity", "MEDIUM")
    if severity == "HIGH":
        score += 20
    elif severity == "MEDIUM":
        score += 5

    flagged_sentence = (finding.get("flagged_sentence", "") or "").lower()
    context_after = (finding.get("context_after", "") or "").lower()

    if any(phrase in flagged_sentence for phrase in MITIGATING_PHRASES):
        score -= 15

    if any(phrase in context_after for phrase in MITIGATING_PHRASES):
        score -= 10

    if any(phrase in flagged_sentence for phrase in AMPLIFYING_PHRASES):
        score += 15

    return max(0, min(100, score))


def interpret_severity(polarity):
    """Convert TextBlob polarity (-1 to +1) to severity tier."""
    if polarity < -0.25:
        return "HIGH"
    elif polarity < -0.10:
        return "MEDIUM"
    else:
        return "LOW"


def scan_section(section_name, section_data, all_findings):
    """
    Scan a section for keywords and extract findings.

    Args:
        section_name: str (e.g. "Item 1A")
        section_data: dict with "text" and "page_num"
        all_findings: list (accumulated findings for co-occurrence checking)

    Returns:
        list of finding dicts
    """
    section_text = section_data.get("text", "")
    page_num = section_data.get("page_num", 0)

    if not section_text:
        return []

    findings = []
    sentences = split_into_sentences(section_text)

    for sentence_num, sentence in enumerate(sentences):
        sentence_lower = sentence.lower()

        for category, keywords in KEYWORDS.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()

                if keyword_lower not in sentence_lower:
                    continue

                sentiment = TextBlob(sentence).sentiment.polarity
                severity = interpret_severity(sentiment)

                para_num = len([s for s in sentences[:sentence_num] if s.endswith(('.',':'))]) + 1

                context_start = max(0, sentence_num - 2)
                context_end = min(len(sentences), sentence_num + 3)

                context_before = " ".join(sentences[context_start:sentence_num]).strip()
                context_after = " ".join(sentences[sentence_num + 1:context_end]).strip()

                context_before = (context_before[:300] + "...") if len(context_before) > 300 else context_before
                context_after = (context_after[:300] + "...") if len(context_after) > 300 else context_after

                flagged_sentence_capped = (sentence[:500] + "...") if len(sentence) > 500 else sentence

                finding = {
                    "section": section_name,
                    "page_num": page_num,
                    "para_num": para_num,
                    "sentence_num": sentence_num,
                    "context_before": context_before,
                    "flagged_sentence": flagged_sentence_capped,
                    "context_after": context_after,
                    "keyword": keyword,
                    "category": category,
                    "sentiment_score": sentiment,
                    "severity": severity,
                }

                finding["severity_score"] = calculate_severity_score(finding)
                finding["explanation"] = explain_finding(finding)

                findings.append(finding)
                break

        else:
            continue
        break

    return findings


def analyze_filings(sections):
    """
    Master analyzer function — extract all findings from all sections.

    Args:
        sections (dict): {section_name: {text: str, page_num: int}, ...}

    Returns:
        dict: {
            "findings": [...],
            "summary": {
                "total": int,
                "by_category": {...},
                "by_severity": {...},
                "avg_sentiment": float,
                "sections_with_flags": [...]
            }
        }
    """
    all_findings = []

    for section_name, section_data in sections.items():
        section_findings = scan_section(section_name, section_data, all_findings)
        all_findings.extend(section_findings)

    all_findings.sort(key=lambda f: f["severity_score"], reverse=True)

    by_category = {}
    by_severity = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    avg_sentiment = 0

    if all_findings:
        sentiment_scores = [f["sentiment_score"] for f in all_findings]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    for finding in all_findings:
        category = finding["category"]
        severity = finding["severity"]

        by_category[category] = by_category.get(category, 0) + 1
        by_severity[severity] += 1

    sections_with_flags = list(set(f["section"] for f in all_findings))

    return {
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "by_category": by_category,
            "by_severity": by_severity,
            "avg_sentiment": round(avg_sentiment, 3),
            "sections_with_flags": sections_with_flags,
        }
    }


if __name__ == "__main__":
    try:
        from fetchers.edgar_fetcher import fetch_10k
    except ImportError:
        from edgar_fetcher import fetch_10k

    print("[RedFlag] Fetching Apple 10-K for analysis test...\n")
    result = fetch_10k("AAPL")

    if result:
        from text_parser import extract_sections

        print("\n[RedFlag] Extracting sections...\n")
        sections = extract_sections(result["latest"]["text"])

        print("\n[RedFlag] Analyzing for risk findings...\n")
        analysis = analyze_filings(sections)

        print("\n[RedFlag] Analysis Complete — Summary:")
        print("-" * 50)
        print(f"Total findings: {analysis['summary']['total']}")
        print(f"By category: {analysis['summary']['by_category']}")
        print(f"By severity: {analysis['summary']['by_severity']}")
        print(f"Avg sentiment: {analysis['summary']['avg_sentiment']}")
        if analysis["findings"]:
            print(f"\nTop finding: {analysis['findings'][0]['keyword']} in {analysis['findings'][0]['section']}")
