# =============================================================================
# keywords.py — RedFlag Risk Keyword Library
# =============================================================================
# This file is the foundation of RedFlag. It contains a curated dictionary of
# risk-signal words and phrases organized into 4 categories. Every other module
# in RedFlag references this file when scanning SEC filings.
#
# Categories:
#   1. LEGAL      — litigation, investigations, regulatory actions
#   2. FINANCIAL  — debt, liquidity, going concern warnings
#   3. OPERATIONAL — supply chain, key person, technology risks
#   4. REGULATORY  — compliance, government scrutiny, policy risk
#
# v2 — Expanded from 100 to 160 keywords across all 4 categories
# =============================================================================


# -----------------------------------------------------------------------------
# LEGAL RISK KEYWORDS
# Phrases that signal the company is facing or anticipating legal trouble
# -----------------------------------------------------------------------------
LEGAL_KEYWORDS = [
    "litigation",
    "lawsuit",
    "legal proceedings",
    "class action",
    "regulatory investigation",
    "subpoena",
    "indictment",
    "criminal investigation",
    "securities fraud",
    "whistleblower",
    "settlement",
    "injunction",
    "cease and desist",
    "enforcement action",
    "government inquiry",
    "alleged violation",
    "pending litigation",
    "legal liability",
    "judicial proceedings",
    "arbitration",
    "legal challenge",
    "regulatory sanction",
    "fine and penalty",
    "legal dispute",
    "court order",
    # v2 additions
    "derivative action",
    "qui tam",
    "patent infringement",
    "trade secret misappropriation",
    "breach of fiduciary duty",
    "shareholder lawsuit",
    "DOJ investigation",
    "FTC action",
    "consent decree",
    "plea agreement",
    "contempt of court",
    "unfair competition",
    "defamation claim",
    "product liability",
    "contractual dispute",
]


# -----------------------------------------------------------------------------
# FINANCIAL RISK KEYWORDS
# Phrases that signal stress in the company's financial health
# -----------------------------------------------------------------------------
FINANCIAL_KEYWORDS = [
    "going concern",
    "substantial doubt",
    "liquidity risk",
    "default",
    "debt covenant",
    "covenant breach",
    "insolvency",
    "bankruptcy",
    "chapter 11",
    "impairment",
    "goodwill impairment",
    "asset write-down",
    "write-off",
    "material weakness",
    "restatement",
    "negative cash flow",
    "working capital deficit",
    "accumulated deficit",
    "net loss",
    "revenue decline",
    "margin compression",
    "credit facility",
    "debt maturity",
    "refinancing risk",
    "capital raise",
    "dilution",
    "going-concern opinion",
    "auditor doubt",
    "financial restatement",
    "earnings miss",
    # v2 additions
    "covenant violation",
    "debt acceleration",
    "cash burn",
    "runway concern",
    "deferred revenue risk",
    "pension obligation",
    "underfunded liability",
    "contingent liability",
    "off-balance sheet",
    "credit downgrade",
    "interest coverage ratio",
    "leverage ratio",
    "accounts receivable risk",
    "inventory write-down",
    "foreign exchange risk",
]


# -----------------------------------------------------------------------------
# OPERATIONAL RISK KEYWORDS
# Phrases that signal problems in how the company runs its business
# -----------------------------------------------------------------------------
OPERATIONAL_KEYWORDS = [
    "supply chain disruption",
    "key personnel",
    "loss of key personnel",
    "dependence on single customer",
    "single supplier",
    "concentration risk",
    "cybersecurity breach",
    "data breach",
    "system failure",
    "operational disruption",
    "business continuity",
    "natural disaster",
    "force majeure",
    "product recall",
    "manufacturing defect",
    "quality control failure",
    "talent retention",
    "labor shortage",
    "union dispute",
    "strike",
    "intellectual property theft",
    "technology obsolescence",
    "platform dependency",
    "customer concentration",
    "geographic concentration",
    # v2 additions
    "key man risk",
    "founder dependency",
    "vendor lock-in",
    "third party dependency",
    "outsourcing risk",
    "cloud dependency",
    "algorithm change",
    "platform risk",
    "channel concentration",
    "distribution disruption",
    "raw material shortage",
    "energy cost exposure",
    "logistics failure",
    "reputational damage",
    "employee misconduct",
]


# -----------------------------------------------------------------------------
# REGULATORY RISK KEYWORDS
# Phrases that signal exposure to government rules, policy, or compliance issues
# -----------------------------------------------------------------------------
REGULATORY_KEYWORDS = [
    "regulatory change",
    "compliance failure",
    "non-compliance",
    "regulatory scrutiny",
    "government regulation",
    "new legislation",
    "policy uncertainty",
    "export control",
    "sanctions",
    "antitrust",
    "environmental regulation",
    "data privacy",
    "GDPR",
    "SEC investigation",
    "FDA approval",
    "regulatory approval",
    "license revocation",
    "permit denial",
    "trade restriction",
    "tariff",
    "import restriction",
    "foreign corrupt practices",
    "FCPA violation",
    "tax reform",
    "regulatory burden",
    # v2 additions
    "regulatory overhang",
    "pending rulemaking",
    "Basel III",
    "Dodd-Frank",
    "SOX compliance",
    "AML violation",
    "KYC failure",
    "money laundering",
    "tax authority investigation",
    "customs violation",
    "healthcare regulation",
    "price control",
    "rate regulation",
    "spectrum license",
    "carbon regulation",
]


# -----------------------------------------------------------------------------
# MASTER KEYWORD DICTIONARY
# Combines all 4 categories into one unified object that other modules import
# -----------------------------------------------------------------------------
REDFLAG_KEYWORDS = {
    "Legal":       LEGAL_KEYWORDS,
    "Financial":   FINANCIAL_KEYWORDS,
    "Operational": OPERATIONAL_KEYWORDS,
    "Regulatory":  REGULATORY_KEYWORDS,
}


# -----------------------------------------------------------------------------
# KEYWORD METADATA
# Useful for reporting — tells us how many keywords exist per category
# -----------------------------------------------------------------------------
def get_keyword_summary():
    """
    Returns a simple summary of how many keywords exist in each category.
    Useful for debugging and for the report header.
    """
    summary = {}
    for category, keywords in REDFLAG_KEYWORDS.items():
        summary[category] = len(keywords)
    return summary


# -----------------------------------------------------------------------------
# QUICK TEST — run this file directly to verify everything loaded correctly
# python keywords.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("RedFlag Keyword Library — Loaded Successfully\n")
    summary = get_keyword_summary()
    for category, count in summary.items():
        print(f"  {category}: {count} keywords")
    print(f"\n  Total: {sum(summary.values())} keywords across 4 categories")