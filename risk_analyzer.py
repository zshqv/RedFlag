# =============================================================================
# risk_analyzer.py — RedFlag Core Analysis Engine
# =============================================================================
# This is the heart of RedFlag. It takes cleaned section text and does two
# things:
#
#   1. KEYWORD FLAGGING — scans every sentence for risk keywords from our
#      keywords.py library, recording every hit with its category and context
#
#   2. SENTIMENT SCORING — scores the tone of each flagged sentence using
#      TextBlob. Negative scores indicate alarming language.
#
# Input:  Dictionary of section texts (from text_parser.py)
# Output: List of flagged findings, each with category, keyword, sentence,
#         and sentiment score
# =============================================================================

import re                              # For splitting text into sentences
from textblob import TextBlob          # For sentiment scoring
from keywords import REDFLAG_KEYWORDS  # Our master keyword library


# -----------------------------------------------------------------------------
# SENTIMENT SCORE INTERPRETER
# TextBlob returns a polarity score between -1.0 and +1.0
# We convert this into a human-readable risk label
# -----------------------------------------------------------------------------
def interpret_sentiment(score):
    """
    Converts a TextBlob polarity score into a human-readable risk label.

    TextBlob polarity scale:
        -1.0 to -0.3  → Highly Negative (alarm language)
        -0.3 to -0.1  → Negative (cautionary language)
        -0.1 to +0.1  → Neutral (factual language)
        +0.1 to +0.3  → Positive (reassuring language)
        +0.3 to +1.0  → Highly Positive (optimistic language)

    Args:
        score (float): TextBlob polarity score

    Returns:
        str: Human-readable label
    """
    if score <= -0.3:
        return "HIGH RISK"
    elif score <= -0.1:
        return "ELEVATED RISK"
    elif score <= 0.1:
        return "NEUTRAL"
    elif score <= 0.3:
        return "LOW RISK"
    else:
        return "POSITIVE"


# -----------------------------------------------------------------------------
# STEP 1 — SPLIT TEXT INTO SENTENCES
# We analyze sentence by sentence so we can pinpoint exactly where each
# red flag appears in the filing
# -----------------------------------------------------------------------------
def split_into_sentences(text):
    """
    Splits a block of text into individual sentences.

    Args:
        text (str): Block of text from a 10-K section

    Returns:
        list: List of individual sentence strings
    """

    # Split on period, exclamation, or question mark followed by a space
    # This is a simple but effective sentence splitter for financial text
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter out very short fragments (less than 20 characters)
    # These are usually noise — page numbers, headers, etc.
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    return sentences


# -----------------------------------------------------------------------------
# STEP 2 — SCAN A SINGLE SECTION FOR KEYWORDS
# Goes sentence by sentence through one section and flags keyword matches
# -----------------------------------------------------------------------------
def scan_section(section_name, section_text):
    """
    Scans a single filing section for risk keywords and scores sentiment.

    Args:
        section_name (str): Name of the section e.g. "Risk Factors"
        section_text (str): Cleaned text content of the section

    Returns:
        list: List of finding dictionaries, one per keyword match
    """

    findings = []

    # Split the section into individual sentences
    sentences = split_into_sentences(section_text)

    # Go through every sentence
    for sentence in sentences:
        sentence_lower = sentence.lower()

        # Check this sentence against every category and keyword
        for category, keywords in REDFLAG_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in sentence_lower:

                    # Keyword found — score the sentiment of this sentence
                    blob = TextBlob(sentence)
                    sentiment_score = round(blob.sentiment.polarity, 3)
                    sentiment_label = interpret_sentiment(sentiment_score)

                    # Record this finding
                    findings.append({
                        "section":         section_name,
                        "category":        category,
                        "keyword":         keyword,
                        "sentence":        sentence[:500],  # Cap at 500 chars
                        "sentiment_score": sentiment_score,
                        "sentiment_label": sentiment_label,
                    })

                    # Once we find one keyword match in a sentence,
                    # move to the next sentence to avoid duplicate entries
                    break

            else:
                # Inner loop didn't break — continue to next category
                continue
            # Inner loop broke — break outer loop too (move to next sentence)
            break

    return findings


# -----------------------------------------------------------------------------
# STEP 3 — ANALYZE ALL SECTIONS
# Runs the scanner across all 3 sections and compiles a master findings list
# -----------------------------------------------------------------------------
def analyze_filings(sections):
    """
    Master function — runs keyword flagging and sentiment scoring across
    all extracted sections.

    Args:
        sections (dict): Output from text_parser.extract_sections()
                         {"Risk Factors": "...", "MD&A": "...", ...}

    Returns:
        dict: {
            "findings": [...],       # All flagged sentences with scores
            "summary":  {...}        # Count of findings per category
        }
    """

    all_findings = []

    for section_name, section_text in sections.items():
        if not section_text:
            print(f"[RedFlag] Skipping empty section: {section_name}")
            continue

        print(f"[RedFlag] Scanning section: {section_name}...")
        findings = scan_section(section_name, section_text)
        all_findings.extend(findings)
        print(f"[RedFlag] Found {len(findings)} red flags in '{section_name}'")

    # Build a summary — count findings per category
    summary = {}
    for finding in all_findings:
        category = finding["category"]
        summary[category] = summary.get(category, 0) + 1

    # Sort findings by sentiment score (most negative first)
    all_findings.sort(key=lambda x: x["sentiment_score"])

    print(f"\n[RedFlag] Total red flags found: {len(all_findings)}")

    return {
        "findings": all_findings,
        "summary":  summary
    }


# -----------------------------------------------------------------------------
# QUICK TEST — run this file directly to verify it works
# python risk_analyzer.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    from edgar_fetcher import fetch_10k
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

        print(f"\n[RedFlag] Top 5 Highest Risk Sentences:")
        print("-" * 50)
        for finding in analysis["findings"][:5]:
            print(f"\n  Category:  {finding['category']}")
            print(f"  Keyword:   {finding['keyword']}")
            print(f"  Risk:      {finding['sentiment_label']} ({finding['sentiment_score']})")
            print(f"  Sentence:  {finding['sentence'][:150]}...")