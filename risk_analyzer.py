# =============================================================================
# risk_analyzer.py — Risk Finding Extraction & Severity Scoring (v2.0)
# =============================================================================

import re
from textblob import TextBlob
from keywords import KEYWORDS
from flag_explainer import explain_finding

HIGH_SEVERITY_KEYWORDS = [
    "going concern", "material weakness", "restatement",
    "criminal charges", "under investigation", "indictment",
    "class action", "securities fraud", "data breach",
    "cybersecurity incident", "cannot guarantee", "no assurance",
    "whistleblower",
]

HIGH_SEVERITY_KEYWORDS_SET = {k.lower() for k in HIGH_SEVERITY_KEYWORDS}

MITIGATING_PHRASES = [
    "we believe", "we expect", "we intend", "we are confident",
    "mitigated", "resolved", "we have taken steps", "management intends",
]

AMPLIFYING_PHRASES = [
    "material adverse", "significant risk", "cannot guarantee",
    "no assurance", "under investigation", "subject to litigation",
]


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def interpret_severity(polarity, keyword, sentence=""):
    """
    HIGH if polarity < -0.25 or keyword is in the always-high list.
    MEDIUM if polarity in (-0.25, -0.10) or mitigating language present.
    LOW otherwise.
    """
    if polarity < -0.25 or keyword.lower() in HIGH_SEVERITY_KEYWORDS_SET:
        return "HIGH"
    has_mitigating = any(p in sentence.lower() for p in MITIGATING_PHRASES)
    if polarity < -0.10 or has_mitigating:
        return "MEDIUM"
    return "LOW"


def calculate_severity_score(finding, section_findings=None):
    """
    Start 50.
    +20 if HIGH; -15 if mitigating in flagged_sentence; -10 if mitigating in
    context_after; +15 if amplifying phrase present; +10 if same keyword
    appears in 2+ other findings in same section. Clamped 0-100.
    """
    score = 50

    if finding.get("severity") == "HIGH":
        score += 20

    flagged_sentence = (finding.get("flagged_sentence", "") or "").lower()
    context_after = (finding.get("context_after", "") or "").lower()

    if any(phrase in flagged_sentence for phrase in MITIGATING_PHRASES):
        score -= 15
    if any(phrase in context_after for phrase in MITIGATING_PHRASES):
        score -= 10
    if any(phrase in flagged_sentence for phrase in AMPLIFYING_PHRASES):
        score += 15

    if section_findings:
        keyword = finding.get("keyword", "")
        same_keyword_count = sum(
            1 for f in section_findings
            if f.get("keyword") == keyword and f is not finding
        )
        if same_keyword_count >= 2:
            score += 10

    return max(0, min(100, score))


def scan_section(section_name, section_data, all_findings):
    """
    Scan one section for keyword matches. Returns list of finding dicts,
    each with all required fields including severity_score and explanation.
    Co-occurrence +10 rule applied as a post-processing pass over the section.
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
                if keyword.lower() not in sentence_lower:
                    continue

                sentiment = TextBlob(sentence).sentiment.polarity
                severity = interpret_severity(sentiment, keyword, sentence)

                para_num = (
                    len([s for s in sentences[:sentence_num] if s.endswith((".", ":"))]) + 1
                )

                context_start = max(0, sentence_num - 2)
                context_end = min(len(sentences), sentence_num + 3)

                context_before = " ".join(sentences[context_start:sentence_num]).strip()
                context_after = " ".join(sentences[sentence_num + 1:context_end]).strip()

                context_before = (context_before[:300] + "...") if len(context_before) > 300 else context_before
                context_after = (context_after[:300] + "...") if len(context_after) > 300 else context_after
                flagged_capped = (sentence[:500] + "...") if len(sentence) > 500 else sentence

                finding = {
                    "section": section_name,
                    "page_num": page_num,
                    "para_num": para_num,
                    "sentence_num": sentence_num,
                    "context_before": context_before,
                    "flagged_sentence": flagged_capped,
                    "context_after": context_after,
                    "keyword": keyword,
                    "category": category,
                    "sentiment_score": sentiment,
                    "severity": severity,
                    "severity_score": 0,
                    "explanation": "",
                }

                finding["explanation"] = explain_finding(finding)
                findings.append(finding)
                break  # one keyword per category per sentence

    # Post-process: apply co-occurrence +10 within this section
    for finding in findings:
        finding["severity_score"] = calculate_severity_score(finding, findings)

    return findings


def analyze_filings(sections):
    """
    Master analyzer — extract all findings from all sections.

    Returns:
        {
            "findings": [...],
            "summary": {
                "total": int,
                "by_category": {...},
                "by_severity": {"HIGH": int, "MEDIUM": int, "LOW": int},
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

    for finding in all_findings:
        cat = finding["category"]
        sev = finding["severity"]
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1

    avg_sentiment = 0.0
    if all_findings:
        avg_sentiment = sum(f["sentiment_score"] for f in all_findings) / len(all_findings)

    sections_with_flags = sorted(set(f["section"] for f in all_findings))

    return {
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "by_category": by_category,
            "by_severity": by_severity,
            "avg_sentiment": round(avg_sentiment, 3),
            "sections_with_flags": sections_with_flags,
        },
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
            top = analysis["findings"][0]
            print(f"\nTop finding: {top['keyword']} in {top['section']} (score {top['severity_score']})")
