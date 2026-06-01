# =============================================================================
# keywords.py — RedFlag Risk Keyword Library
# =============================================================================
# Categories:
#   1. LEGAL      — litigation, investigations, regulatory actions
#   2. FINANCIAL  — debt, liquidity, going concern warnings
#   3. OPERATIONAL — supply chain, key person, technology risks
#   4. REGULATORY  — compliance, government scrutiny, policy risk
#
# v3 — Added INDUSTRY_PACKS + sector detection helpers
# =============================================================================


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


REDFLAG_KEYWORDS = {
    "Legal":       LEGAL_KEYWORDS,
    "Financial":   FINANCIAL_KEYWORDS,
    "Operational": OPERATIONAL_KEYWORDS,
    "Regulatory":  REGULATORY_KEYWORDS,
}


# =============================================================================
# INDUSTRY PACKS — sector-specific keyword additions
# =============================================================================
INDUSTRY_PACKS = {
    "Banking": [
        "net interest margin",
        "tier 1 capital",
        "tier 2 capital",
        "basel",
        "deposit outflow",
        "credit loss provision",
        "loan impairment",
        "non-performing loan",
        "allowance for credit losses",
        "bank run",
        "capital adequacy",
        "stress test",
        "interest rate sensitivity",
        "mortgage default",
        "liquidity coverage ratio",
    ],
    "Technology": [
        "supply chain",
        "semiconductor",
        "data privacy",
        "cloud outage",
        "ip theft",
        "export control",
        "chip shortage",
        "hardware dependency",
        "open source risk",
        "software vulnerability",
        "API deprecation",
        "platform ban",
        "data localization",
        "AI regulation",
        "model bias",
    ],
    "Healthcare": [
        "clinical trial",
        "FDA approval",
        "patent expiry",
        "drug recall",
        "liability",
        "reimbursement",
        "biosimilar competition",
        "off-label use",
        "adverse event",
        "post-market surveillance",
        "Medicare reimbursement",
        "formulary exclusion",
        "pricing pressure",
        "generic competition",
        "regulatory hold",
    ],
    "Energy": [
        "oil spill",
        "carbon tax",
        "stranded asset",
        "pipeline",
        "refinery",
        "commodity price",
        "reserve depletion",
        "decommissioning liability",
        "flaring violation",
        "methane regulation",
        "energy transition risk",
        "renewable mandate",
        "drilling moratorium",
        "LNG market",
        "crude price volatility",
    ],
}


def get_keywords_for_sector(sector):
    """
    Returns REDFLAG_KEYWORDS merged with the relevant sector pack.
    The sector pack keywords are added under a key matching the sector name.
    """
    merged = {k: list(v) for k, v in REDFLAG_KEYWORDS.items()}
    pack = INDUSTRY_PACKS.get(sector, [])
    if pack:
        merged[sector] = pack
    return merged


def detect_sector(company_name):
    """
    Uses simple keyword matching on the company name to guess the sector.
    Returns one of: 'Banking', 'Technology', 'Healthcare', 'Energy', or None.
    """
    name_lower = company_name.lower()

    banking_signals = [
        "bank", "bancorp", "financial", "trust", "credit union",
        "savings", "capital", "securities", "investment", "asset management",
        "jpmorgan", "citigroup", "wells fargo", "goldman", "morgan stanley",
    ]
    tech_signals = [
        "tech", "software", "systems", "data", "digital", "semiconductor",
        "micro", "intel", "google", "apple", "microsoft", "meta", "amazon",
        "cloud", "cyber", "ai", "computing", "networks", "information",
    ]
    healthcare_signals = [
        "health", "pharma", "pharmaceutical", "medical", "bio", "therapeutics",
        "hospital", "clinic", "life sciences", "genomics", "oncology", "surgery",
    ]
    energy_signals = [
        "energy", "oil", "gas", "petroleum", "power", "electric", "nuclear",
        "solar", "wind", "coal", "mining", "refining", "pipeline", "utilities",
    ]

    for signal in banking_signals:
        if signal in name_lower:
            return "Banking"
    for signal in tech_signals:
        if signal in name_lower:
            return "Technology"
    for signal in healthcare_signals:
        if signal in name_lower:
            return "Healthcare"
    for signal in energy_signals:
        if signal in name_lower:
            return "Energy"

    return None


def get_keyword_summary():
    summary = {}
    for category, keywords in REDFLAG_KEYWORDS.items():
        summary[category] = len(keywords)
    return summary


if __name__ == "__main__":
    print("RedFlag Keyword Library — Loaded Successfully\n")
    summary = get_keyword_summary()
    for category, count in summary.items():
        print(f"  {category}: {count} keywords")
    print(f"\n  Total: {sum(summary.values())} keywords across 4 categories")
    print(f"\n  Industry Packs: {', '.join(INDUSTRY_PACKS.keys())}")
    detected = detect_sector("JPMorgan Chase Bank")
    print(f"\n  Sector detection 'JPMorgan Chase Bank' → {detected}")
