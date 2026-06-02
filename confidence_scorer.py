MITIGATING_PHRASES = [
    "we believe", "we expect", "we intend", "we are confident",
    "we have taken steps", "mitigated", "resolved", "no longer",
]

AMPLIFYING_PHRASES = [
    "material adverse", "significant risk", "may result in", "could result in",
    "subject to litigation", "under investigation", "cannot guarantee", "no assurance",
]


def score_confidence(finding, all_findings):
    """Return confidence score 0-100 for a risk finding. Higher = more confident."""
    score     = 50
    keyword   = finding.get("keyword", "")
    para_num  = finding.get("para_num", -1)
    sentence  = (finding.get("sentence",      "") or "").lower()
    ctx_after = (finding.get("context_after", "") or "").lower()

    # Co-occurrence: same keyword appears more than once in the same paragraph
    co_count = sum(
        1 for f in all_findings
        if f.get("keyword", "") == keyword and f.get("para_num", -2) == para_num
    )
    if co_count > 1:
        score += min(20, (co_count - 1) * 10)

    # Mitigating language in the flagged sentence (-15, one-time)
    for phrase in MITIGATING_PHRASES:
        if phrase in sentence:
            score -= 15
            break

    # Mitigating language in context_after (-10, one-time)
    for phrase in MITIGATING_PHRASES:
        if phrase in ctx_after:
            score -= 10
            break

    # Amplifying language in the flagged sentence (+15, one-time)
    for phrase in AMPLIFYING_PHRASES:
        if phrase in sentence:
            score += 15
            break

    return max(0, min(100, score))


if __name__ == "__main__":
    print("confidence_scorer imported successfully")
