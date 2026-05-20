# =============================================================================
# comparator.py — Year-Over-Year Risk Comparison Engine
# =============================================================================
# A single year's risk findings mean little without context.
# This module compares this year's 10-K analysis against last year's to show:
#
#   1. Did total risk flags increase or decrease?
#   2. Which categories got worse? Which improved?
#   3. Are new risk keywords appearing for the first time?
#   4. What is the overall risk trajectory?
#
# Input:  Two analysis results from risk_analyzer.py (latest + previous year)
# Output: A comparison dictionary ready for the report generator
# =============================================================================


# -----------------------------------------------------------------------------
# RISK TRAJECTORY INTERPRETER
# Converts a percentage change into a human-readable trajectory label
# -----------------------------------------------------------------------------
def interpret_trajectory(percent_change):
    """
    Converts a percentage change in risk findings into a trajectory label.

    Args:
        percent_change (float): Percentage change from previous to current year

    Returns:
        str: Human-readable trajectory label
    """
    if percent_change >= 25:
        return "⚠️  DETERIORATING"
    elif percent_change >= 10:
        return "📈  INCREASING"
    elif percent_change <= -25:
        return "✅  SIGNIFICANTLY IMPROVING"
    elif percent_change <= -10:
        return "📉  IMPROVING"
    else:
        return "➡️  STABLE"


# -----------------------------------------------------------------------------
# STEP 1 — COMPARE CATEGORY COUNTS
# How many findings per category this year vs last year?
# -----------------------------------------------------------------------------
def compare_category_counts(current_summary, previous_summary):
    """
    Compares risk finding counts per category between two years.

    Args:
        current_summary  (dict): Category counts from this year's analysis
        previous_summary (dict): Category counts from last year's analysis

    Returns:
        dict: Category-level comparison with change and trajectory
    """

    # Get all categories from both years combined
    all_categories = set(list(current_summary.keys()) + list(previous_summary.keys()))

    category_comparison = {}

    for category in all_categories:
        current_count  = current_summary.get(category, 0)
        previous_count = previous_summary.get(category, 0)

        # Calculate the change
        change = current_count - previous_count

        # Calculate percentage change (avoid division by zero)
        if previous_count > 0:
            percent_change = round((change / previous_count) * 100, 1)
        elif current_count > 0:
            # Category is brand new this year
            percent_change = 100.0
        else:
            percent_change = 0.0

        trajectory = interpret_trajectory(percent_change)

        category_comparison[category] = {
            "current_count":  current_count,
            "previous_count": previous_count,
            "change":         change,
            "percent_change": percent_change,
            "trajectory":     trajectory,
        }

    return category_comparison


# -----------------------------------------------------------------------------
# STEP 2 — FIND NEW KEYWORDS
# Which risk keywords appear this year that did NOT appear last year?
# These are the most important signals — something new is being disclosed
# -----------------------------------------------------------------------------
def find_new_keywords(current_findings, previous_findings):
    """
    Identifies risk keywords that appear in the current year but not last year.
    New keywords represent emerging risks the company just started disclosing.

    Args:
        current_findings  (list): Findings from this year's analysis
        previous_findings (list): Findings from last year's analysis

    Returns:
        list: Keywords that are new this year
    """

    # Extract the set of keywords from each year
    current_keywords  = set(f["keyword"] for f in current_findings)
    previous_keywords = set(f["keyword"] for f in previous_findings)

    # New keywords = appear this year but NOT last year
    new_keywords = current_keywords - previous_keywords

    return sorted(list(new_keywords))


# -----------------------------------------------------------------------------
# STEP 3 — COMPARE SENTIMENT TRENDS
# Is the language getting more alarming or more reassuring over time?
# -----------------------------------------------------------------------------
def compare_sentiment_trends(current_findings, previous_findings):
    """
    Compares the average sentiment score between this year and last year.
    More negative average = language is becoming more alarming.

    Args:
        current_findings  (list): Findings from this year's analysis
        previous_findings (list): Findings from last year's analysis

    Returns:
        dict: Sentiment trend comparison
    """

    # Calculate average sentiment for each year
    if current_findings:
        current_avg = round(
            sum(f["sentiment_score"] for f in current_findings) / len(current_findings), 3
        )
    else:
        current_avg = 0.0

    if previous_findings:
        previous_avg = round(
            sum(f["sentiment_score"] for f in previous_findings) / len(previous_findings), 3
        )
    else:
        previous_avg = 0.0

    sentiment_change = round(current_avg - previous_avg, 3)

    # More negative change = language is getting more alarming
    if sentiment_change < -0.05:
        sentiment_trend = "Language becoming MORE alarming"
    elif sentiment_change > 0.05:
        sentiment_trend = "Language becoming LESS alarming"
    else:
        sentiment_trend = "Language tone is STABLE"

    return {
        "current_avg_sentiment":  current_avg,
        "previous_avg_sentiment": previous_avg,
        "sentiment_change":       sentiment_change,
        "sentiment_trend":        sentiment_trend,
    }


# -----------------------------------------------------------------------------
# MASTER FUNCTION — Runs the full year-over-year comparison
# -----------------------------------------------------------------------------
def compare_years(current_analysis, previous_analysis):
    """
    Master function — compares this year's analysis against last year's.

    Args:
        current_analysis  (dict): Output from risk_analyzer.analyze_filings()
                                  for the latest 10-K
        previous_analysis (dict): Output from risk_analyzer.analyze_filings()
                                  for the previous year's 10-K

    Returns:
        dict: Full comparison report ready for report_generator.py
    """

    print("[RedFlag] Running year-over-year comparison...")

    current_findings  = current_analysis["findings"]
    previous_findings = previous_analysis["findings"]
    current_summary   = current_analysis["summary"]
    previous_summary  = previous_analysis["summary"]

    # Total findings comparison
    current_total  = len(current_findings)
    previous_total = len(previous_findings)
    total_change   = current_total - previous_total

    if previous_total > 0:
        total_percent_change = round((total_change / previous_total) * 100, 1)
    else:
        total_percent_change = 0.0

    overall_trajectory = interpret_trajectory(total_percent_change)

    # Run all three comparisons
    category_comparison = compare_category_counts(current_summary, previous_summary)
    new_keywords        = find_new_keywords(current_findings, previous_findings)
    sentiment_trend     = compare_sentiment_trends(current_findings, previous_findings)

    print(f"[RedFlag] Overall trajectory: {overall_trajectory}")
    print(f"[RedFlag] New keywords this year: {len(new_keywords)}")

    return {
        "overall": {
            "current_total":      current_total,
            "previous_total":     previous_total,
            "total_change":       total_change,
            "percent_change":     total_percent_change,
            "trajectory":         overall_trajectory,
        },
        "by_category":    category_comparison,
        "new_keywords":   new_keywords,
        "sentiment_trend": sentiment_trend,
    }


# -----------------------------------------------------------------------------
# QUICK TEST — run this file directly to verify it works
# python comparator.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    from edgar_fetcher import fetch_10k
    from text_parser import extract_sections
    from risk_analyzer import analyze_filings

    print("[RedFlag] Fetching Apple 10-K (latest + previous)...\n")
    result = fetch_10k("AAPL")

    if result and result["previous"]["text"]:

        print("\n[RedFlag] Analyzing latest 10-K...")
        latest_sections  = extract_sections(result["latest"]["text"])
        latest_analysis  = analyze_filings(latest_sections)

        print("\n[RedFlag] Analyzing previous 10-K...")
        previous_sections = extract_sections(result["previous"]["text"])
        previous_analysis = analyze_filings(previous_sections)

        print("\n[RedFlag] Comparing years...\n")
        comparison = compare_years(latest_analysis, previous_analysis)

        print("\n[RedFlag] Year-Over-Year Comparison:")
        print("-" * 50)
        overall = comparison["overall"]
        print(f"  This Year:    {overall['current_total']} findings")
        print(f"  Last Year:    {overall['previous_total']} findings")
        print(f"  Change:       {overall['total_change']:+d} ({overall['percent_change']:+.1f}%)")
        print(f"  Trajectory:   {overall['trajectory']}")

        print(f"\n  Sentiment Trend: {comparison['sentiment_trend']['sentiment_trend']}")

        print(f"\n  New Keywords This Year ({len(comparison['new_keywords'])}):")
        for kw in comparison["new_keywords"][:10]:
            print(f"    — {kw}")

        print(f"\n  Category Breakdown:")
        for cat, data in comparison["by_category"].items():
            print(f"    {cat}: {data['previous_count']} → {data['current_count']} {data['trajectory']}")