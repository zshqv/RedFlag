# =============================================================================
# text_parser.py — SEC Filing Section Extractor (All 18 Items)
# =============================================================================
# Extracts all 18 standard 10-K items with page number estimation.
# Returns section name, text content, and estimated page number for each.
# =============================================================================

import re
from bs4 import BeautifulSoup

SECTION_MARKERS = {
    "Item 1": [
        "item 1 business",
        "item 1.",
        "business of the registrant",
    ],
    "Item 1A": [
        "item 1a risk factors",
        "item 1a",
        "item\xa01a",
        "risk factors",
    ],
    "Item 1B": [
        "item 1b unresolved staff comments",
        "item 1b",
        "unresolved staff comments",
    ],
    "Item 2": [
        "item 2 properties",
        "item 2",
        "properties of the registrant",
    ],
    "Item 3": [
        "item 3 legal proceedings",
        "item 3",
        "legal proceedings",
    ],
    "Item 4": [
        "item 4 mine safety disclosures",
        "item 4",
        "mine safety",
    ],
    "Item 5": [
        "item 5 market for registrant",
        "item 5",
        "market for registrant common",
    ],
    "Item 6": [
        "item 6 selected financial data",
        "item 6",
        "selected financial data",
    ],
    "Item 7": [
        "item 7 management's discussion",
        "item 7",
        "item\xa07",
        "management's discussion and analysis",
        "management discussion and analysis",
        "md&a",
    ],
    "Item 7A": [
        "item 7a quantitative and qualitative",
        "item 7a",
        "quantitative and qualitative disclosures",
    ],
    "Item 8": [
        "item 8 financial statements",
        "item 8",
        "item\xa08",
        "financial statements and supplementary",
    ],
    "Item 9": [
        "item 9 changes in disagreements",
        "item 9",
        "changes in disagreements with accountants",
    ],
    "Item 9A": [
        "item 9a controls and procedures",
        "item 9a",
        "controls and procedures",
    ],
    "Item 9B": [
        "item 9b other information",
        "item 9b",
        "other information",
    ],
    "Item 10": [
        "item 10 directors executive officers",
        "item 10",
        "directors executive officers",
    ],
    "Item 11": [
        "item 11 executive compensation",
        "item 11",
        "executive compensation",
    ],
    "Item 12": [
        "item 12 security ownership",
        "item 12",
        "security ownership",
    ],
    "Item 13": [
        "item 13 certain relationships",
        "item 13",
        "certain relationships and related transactions",
    ],
    "Item 14": [
        "item 14 principal accountant",
        "item 14",
        "principal accountant fees and services",
    ],
}

SECTION_CHAR_LIMIT = 50000
CHARS_PER_PAGE = 3000


def clean_html_to_text(raw_html):
    print("[RedFlag] Cleaning raw HTML filing...")
    soup = BeautifulSoup(raw_html, "lxml")

    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text)
    text_lower = text.lower()

    print(f"[RedFlag] Cleaned text length: {len(text):,} characters")
    return text, text_lower


def find_second_occurrence(text_lower, markers):
    for marker in markers:
        first_pos = text_lower.find(marker)

        if first_pos == -1:
            continue

        second_pos = text_lower.find(marker, first_pos + len(marker) + 1)

        if second_pos != -1:
            return second_pos

    return -1


def estimate_page_num(section_start_pos, full_text):
    return max(1, section_start_pos // CHARS_PER_PAGE)


def extract_sections(raw_html):
    """
    Master function — extracts all 18 10-K items with page number estimation.

    Returns:
        dict: {
            "Item 1": {"text": "...", "page_num": 5},
            "Item 1A": {"text": "...", "page_num": 8},
            ...
        }
    """
    text, text_lower = clean_html_to_text(raw_html)

    sections = {}
    section_names = list(SECTION_MARKERS.keys())

    for i, section_name in enumerate(section_names):
        print(f"[RedFlag] Extracting section: {section_name}...")

        markers = SECTION_MARKERS[section_name]
        start_pos = find_second_occurrence(text_lower, markers)

        if start_pos == -1:
            print(f"[RedFlag] WARNING: Could not find '{section_name}' section.")
            sections[section_name] = {"text": "", "page_num": 0}
            continue

        if i + 1 < len(section_names):
            next_markers = SECTION_MARKERS[section_names[i + 1]]
            end_pos = find_second_occurrence(text_lower[start_pos + 100:], next_markers)

            if end_pos != -1:
                end_pos = start_pos + 100 + end_pos
            else:
                end_pos = start_pos + SECTION_CHAR_LIMIT
        else:
            end_pos = start_pos + SECTION_CHAR_LIMIT

        section_text = text[start_pos:end_pos][:SECTION_CHAR_LIMIT].strip()
        page_num = estimate_page_num(start_pos, text)

        sections[section_name] = {"text": section_text, "page_num": page_num}
        print(f"[RedFlag] Extracted {len(section_text):,} chars from '{section_name}' (page {page_num})")

    return sections


if __name__ == "__main__":
    from fetchers.edgar_fetcher import fetch_10k

    print("[RedFlag] Fetching Apple 10-K for parsing test...\n")
    result = fetch_10k("AAPL")

    if result:
        print("\n[RedFlag] Running section extractor...\n")
        sections = extract_sections(result["latest"]["text"])

        print("\n[RedFlag] Extraction Complete — Summary:")
        print("-" * 50)
        for section_name, data in sections.items():
            text = data["text"]
            page = data["page_num"]
            if text:
                preview = text[:200].replace('\n', ' ')
                print(f"\n  {section_name} (page {page}, {len(text):,} chars)")
                print(f"  Preview: {preview}...")
            else:
                print(f"\n  {section_name}: NOT FOUND")
