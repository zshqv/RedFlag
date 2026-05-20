# =============================================================================
# text_parser.py — SEC Filing Section Extractor
# =============================================================================
# A raw 10-K filing is 150-300 pages of HTML. Most of it is boilerplate.
# This module extracts only the 3 high-risk sections that analysts care about:
#
#   1. Item 1A — Risk Factors
#   2. Item 7  — Management Discussion & Analysis (MD&A)
#   3. Item 8  — Financial Statements & Notes
#
# Input:  Raw HTML text of a 10-K filing (from edgar_fetcher.py)
# Output: Dictionary of clean, readable text per section
#
# KEY FIX: SEC filings mention section names twice — once in the table of
# contents, and once at the actual section. We skip the first occurrence
# and extract from the second (real) occurrence.
# =============================================================================

import re
from bs4 import BeautifulSoup


# -----------------------------------------------------------------------------
# SECTION MARKERS
# These are the exact phrases SEC filings use to mark each section
# -----------------------------------------------------------------------------
SECTION_MARKERS = {
    "Risk Factors": [
        "item 1a",
        "item\xa01a",
        "risk factors",
    ],
    "MD&A": [
        "item 7",
        "item\xa07",
        "management's discussion and analysis",
        "management discussion and analysis",
    ],
    "Financial Notes": [
        "item 8",
        "item\xa08",
        "financial statements and supplementary data",
        "notes to consolidated financial statements",
    ]
}

# How many characters to extract per section (roughly 15-20 pages worth)
SECTION_CHAR_LIMIT = 50000


# -----------------------------------------------------------------------------
# STEP 1 — CLEAN THE RAW HTML
# -----------------------------------------------------------------------------
def clean_html_to_text(raw_html):
    """
    Converts raw HTML from SEC EDGAR into clean plain text.

    Args:
        raw_html (str): Raw HTML content of the 10-K filing

    Returns:
        tuple: (original_case_text, lowercase_text)
    """

    print("[RedFlag] Cleaning raw HTML filing...")

    soup = BeautifulSoup(raw_html, "lxml")

    # Remove script and style tags
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    text_lower = text.lower()

    print(f"[RedFlag] Cleaned text length: {len(text):,} characters")
    return text, text_lower


# -----------------------------------------------------------------------------
# STEP 2 — FIND THE SECOND OCCURRENCE OF A SECTION
# The first occurrence is always in the table of contents — we skip it
# The second occurrence is the real section content
# -----------------------------------------------------------------------------
def find_second_occurrence(text_lower, markers):
    """
    Finds the SECOND occurrence of a section marker in the document.
    The first occurrence is always the table of contents — we skip it.

    Args:
        text_lower (str): Lowercase full filing text
        markers (list):   List of marker phrases to search for

    Returns:
        int: Character position of the second occurrence
        -1:  If not found
    """

    for marker in markers:
        first_pos = text_lower.find(marker)

        if first_pos == -1:
            continue

        # Search for the second occurrence starting after the first
        second_pos = text_lower.find(marker, first_pos + len(marker) + 1)

        if second_pos != -1:
            return second_pos

    return -1


# -----------------------------------------------------------------------------
# STEP 3 — EXTRACT ALL 3 SECTIONS
# -----------------------------------------------------------------------------
def extract_sections(raw_html):
    """
    Master function — extracts the 3 high-risk sections from a 10-K filing.

    Args:
        raw_html (str): Raw HTML content of the 10-K filing

    Returns:
        dict: {
            "Risk Factors":    "extracted text...",
            "MD&A":            "extracted text...",
            "Financial Notes": "extracted text..."
        }
    """

    # Step 1 — Clean the HTML
    text, text_lower = clean_html_to_text(raw_html)

    sections = {}
    section_names = list(SECTION_MARKERS.keys())

    for i, section_name in enumerate(section_names):
        print(f"[RedFlag] Extracting section: {section_name}...")

        markers = SECTION_MARKERS[section_name]

        # Find the SECOND occurrence — skipping the table of contents
        start_pos = find_second_occurrence(text_lower, markers)

        if start_pos == -1:
            print(f"[RedFlag] WARNING: Could not find '{section_name}' section.")
            sections[section_name] = ""
            continue

        # Find where the next section starts
        if i + 1 < len(section_names):
            next_markers = SECTION_MARKERS[section_names[i + 1]]
            end_pos = find_second_occurrence(text_lower[start_pos + 100:], next_markers)

            if end_pos != -1:
                end_pos = start_pos + 100 + end_pos
            else:
                end_pos = start_pos + SECTION_CHAR_LIMIT
        else:
            end_pos = start_pos + SECTION_CHAR_LIMIT

        # Extract and cap the section text
        section_text = text[start_pos:end_pos][:SECTION_CHAR_LIMIT]
        section_text = section_text.strip()

        sections[section_name] = section_text
        print(f"[RedFlag] Extracted {len(section_text):,} characters from '{section_name}'")

    return sections


# -----------------------------------------------------------------------------
# QUICK TEST
# python text_parser.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    from edgar_fetcher import fetch_10k

    print("[RedFlag] Fetching Apple 10-K for parsing test...\n")
    result = fetch_10k("AAPL")

    if result:
        print("\n[RedFlag] Running section extractor...\n")
        sections = extract_sections(result["latest"]["text"])

        print("\n[RedFlag] Extraction Complete — Summary:")
        print("-" * 50)
        for section_name, text in sections.items():
            if text:
                preview = text[:200].replace('\n', ' ')
                print(f"\n  {section_name} ({len(text):,} chars)")
                print(f"  Preview: {preview}...")
            else:
                print(f"\n  {section_name}: NOT FOUND")