import os
import anthropic


FALLBACK_TEMPLATES = {
    "Legal": (
        "This language signals unresolved legal exposure that management has not quantified. "
        "Explicit disclaimers about litigation outcomes indicate the risk is real and active."
    ),
    "Regulatory": (
        "Management is disclosing uncertainty about regulatory compliance, which may signal an active "
        "investigation or enforcement action. This warrants direct follow-up before any transaction."
    ),
    "Financial": (
        "This language indicates potential stress on the company's financial position or ability to meet obligations. "
        "Cross-check against liquidity ratios and debt maturity schedules."
    ),
    "Operational": (
        "An operational concentration or dependency has been disclosed that could disrupt business continuity. "
        "This is a structural vulnerability unlikely to be resolved quickly."
    ),
    "Governance": (
        "A governance concern has been flagged that may affect board oversight or management integrity. "
        "These risks are often underweighted but material in M&A contexts."
    ),
    "Forward-Looking": (
        "Management is explicitly qualifying their own forward guidance with uncertainty language. "
        "Paired with other high-severity flags, this signals deteriorating confidence in the business outlook."
    ),
}


def explain_finding(finding: dict) -> str:
    """
    Generate a 2-sentence explanation of why a finding is a red flag.

    Args:
        finding (dict): Must contain keys:
            - category: str (e.g. "Legal", "Regulatory")
            - keyword: str (e.g. "going concern")
            - flagged_sentence: str (the sentence containing the keyword)
            - context_before: str (context before the sentence)
            - context_after: str (context after the sentence)
            - severity: str (e.g. "HIGH", "MEDIUM", "LOW")

    Returns:
        str: 2-sentence explanation
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)

            system_prompt = (
                "You are a financial due diligence analyst. Explain in exactly 2 sentences "
                "why a specific piece of language in a financial filing is a red flag. "
                "Write for a consultant or analyst who may not be a finance expert. "
                "Be direct and specific. No jargon, no hedging. Never start with 'This is a red flag because'."
            )

            user_message = (
                f"Category: {finding.get('category', 'Unknown')}. "
                f"Keyword: {finding.get('keyword', 'N/A')}. "
                f"Flagged sentence: {finding.get('flagged_sentence', 'N/A')}. "
                f"Context before: {finding.get('context_before', '')}. "
                f"Context after: {finding.get('context_after', '')}. "
                f"Severity: {finding.get('severity', 'MEDIUM')}."
            )

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=120,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            return response.content[0].text if response.content else _get_fallback(finding)

        except Exception as e:
            print(f"[RedFlag] Claude API call failed: {e}. Using fallback template.")
            return _get_fallback(finding)
    else:
        return _get_fallback(finding)


def _get_fallback(finding: dict) -> str:
    """Get the rule-based fallback explanation based on category."""
    category = finding.get("category", "Forward-Looking")
    return FALLBACK_TEMPLATES.get(category, FALLBACK_TEMPLATES["Forward-Looking"])


if __name__ == "__main__":
    test_finding = {
        "category": "Financial",
        "keyword": "going concern",
        "flagged_sentence": "The company has substantial doubt about its ability to continue as a going concern.",
        "context_before": "The audit report notes significant operational challenges.",
        "context_after": "Management has implemented a restructuring plan.",
        "severity": "HIGH",
    }

    print("Testing flag_explainer with fallback (no API key):")
    explanation = explain_finding(test_finding)
    print(f"\n{explanation}")
