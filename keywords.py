# =============================================================================
# keywords.py — RedFlag Risk Keyword Library v2.0
# =============================================================================
# 6 Core Categories + 6 Industry Packs = 220+ keywords
#
# Categories:
#   1. Legal / Litigation        (45 keywords)
#   2. Regulatory / Compliance   (40 keywords)
#   3. Financial / Liquidity     (40 keywords)
#   4. Operational / Strategic   (40 keywords)
#   5. Governance / ESG          (30 keywords)
#   6. Forward-Looking / Uncertainty (25 keywords)
# =============================================================================


LEGAL_KEYWORDS = [
    # Core litigation & legal proceedings
    "litigation",
    "lawsuit",
    "legal proceedings",
    "class action",
    "securities fraud",
    "injunction",
    "contempt",
    "indictment",
    "grand jury",
    "subpoena",
    "consent decree",
    "cease and desist",
    "breach of fiduciary duty",
    "misrepresentation",
    "disgorgement",
    "restatement",
    "whistleblower",
    "qui tam",
    "false claims act",
    "arbitration",
    "settlement agreement",
    "preliminary injunction",
    "permanent injunction",
    "criminal charges",
    "deferred prosecution",
    "regulatory investigation",
    "government inquiry",
    "alleged violation",
    "pending litigation",
    "legal liability",
    "judicial proceedings",
    "legal challenge",
    "regulatory sanction",
    "fine and penalty",
    "legal dispute",
    "court order",
    "derivative action",
    "patent infringement",
    "trade secret misappropriation",
    "shareholder lawsuit",
    "DOJ investigation",
    "FTC action",
    "plea agreement",
    "unfair competition",
    "defamation claim",
]


REGULATORY_KEYWORDS = [
    # Compliance & regulatory actions
    "sanctions",
    "OFAC",
    "AML",
    "anti-money laundering",
    "KYC",
    "know your customer",
    "GDPR",
    "data breach",
    "cybersecurity incident",
    "regulatory capital",
    "stress test",
    "living will",
    "resolution plan",
    "market manipulation",
    "insider trading",
    "Sarbanes-Oxley",
    "SOX 404",
    "material weakness",
    "significant deficiency",
    "control failure",
    "enforcement action",
    "consent order",
    "memorandum of understanding",
    "corrective action plan",
    "regulatory scrutiny",
    "regulatory change",
    "compliance failure",
    "non-compliance",
    "government regulation",
    "new legislation",
    "policy uncertainty",
    "export control",
    "antitrust",
    "environmental regulation",
    "data privacy",
    "SEC investigation",
    "FDA approval",
    "regulatory approval",
    "license revocation",
    "permit denial",
]


FINANCIAL_KEYWORDS = [
    # Liquidity & financial stress
    "going concern",
    "covenant breach",
    "covenant violation",
    "debt covenant",
    "borrowing base",
    "credit facility terminated",
    "acceleration of debt",
    "cross-default",
    "leverage ratio breach",
    "interest coverage",
    "negative working capital",
    "cash burn",
    "runway",
    "liquidity crisis",
    "capital raise required",
    "dilution",
    "goodwill impairment",
    "asset impairment",
    "write-down",
    "write-off",
    "contingent liability",
    "off-balance sheet",
    "variable interest entity",
    "related party loan",
    "pledge of assets",
    "substantial doubt",
    "liquidity risk",
    "default",
    "insolvency",
    "bankruptcy",
    "chapter 11",
    "material weakness",
    "restatement",
    "negative cash flow",
    "working capital deficit",
    "accumulated deficit",
    "net loss",
    "revenue decline",
    "margin compression",
    "credit facility",
]


OPERATIONAL_KEYWORDS = [
    # Operational & strategic risks
    "key person",
    "key employee departure",
    "succession plan",
    "single customer",
    "customer concentration",
    "revenue concentration",
    "geographic concentration",
    "single supplier",
    "supply disruption",
    "force majeure",
    "business continuity",
    "disaster recovery",
    "system outage",
    "data loss",
    "product recall",
    "safety incident",
    "environmental violation",
    "ESG controversy",
    "greenwashing",
    "carbon liability",
    "stranded assets",
    "technology obsolescence",
    "competitive displacement",
    "market share loss",
    "pricing pressure",
    "dependence on single customer",
    "supply chain disruption",
    "talent retention",
    "labor shortage",
    "union dispute",
    "strike",
    "intellectual property theft",
    "platform dependency",
    "vendor lock-in",
    "third party dependency",
    "outsourcing risk",
    "cloud dependency",
    "algorithm change",
    "platform risk",
    "reputational damage",
]


GOVERNANCE_KEYWORDS = [
    # Governance & ESG concerns
    "board independence",
    "related party transaction",
    "self-dealing",
    "executive misconduct",
    "clawback",
    "say on pay",
    "poison pill",
    "staggered board",
    "dual class shares",
    "activist investor",
    "proxy contest",
    "hostile takeover",
    "change of control",
    "golden parachute",
    "excessive compensation",
    "audit committee",
    "independence concern",
    "conflicts of interest",
    "nepotism",
    "diversity disclosure",
    "ESG rating downgrade",
    "founder dependency",
    "key man risk",
    "quality control failure",
    "manufacturing defect",
    "employee misconduct",
    "product liability",
    "contractual dispute",
    "customer concentration",
    "channel concentration",
]


FORWARD_LOOKING_KEYWORDS = [
    # Uncertainty & forward-looking warnings
    "no assurance",
    "cannot guarantee",
    "may not be able",
    "significant uncertainty",
    "highly uncertain",
    "unpredictable",
    "adverse conditions",
    "unfavorable conditions",
    "deteriorating",
    "challenging environment",
    "headwinds",
    "macro uncertainty",
    "geopolitical risk",
    "currency risk",
    "interest rate sensitivity",
    "inflation impact",
    "recessionary conditions",
    "demand weakness",
    "substantial doubt",
    "pending rulemaking",
    "policy uncertainty",
    "tariff",
    "import restriction",
    "trade restriction",
    "uncertain outcome",
]


KEYWORDS = {
    "Legal": LEGAL_KEYWORDS,
    "Regulatory": REGULATORY_KEYWORDS,
    "Financial": FINANCIAL_KEYWORDS,
    "Operational": OPERATIONAL_KEYWORDS,
    "Governance": GOVERNANCE_KEYWORDS,
    "Forward-Looking": FORWARD_LOOKING_KEYWORDS,
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
    "Real Estate": [
        "cap rate",
        "vacancy rate",
        "NOI",
        "FFO",
        "REIT",
        "lease expiration",
        "tenant concentration",
        "refinancing risk",
    ],
    "Consulting": [
        "utilization rate",
        "billable hours",
        "client concentration",
        "contract renewal",
        "engagement termination",
        "key partner departure",
    ],
}


def get_keywords_for_sector(sector):
    """
    Returns KEYWORDS merged with the relevant sector pack.
    The sector pack keywords are added under a key matching the sector name.
    """
    merged = {k: list(v) for k, v in KEYWORDS.items()}
    pack = INDUSTRY_PACKS.get(sector, [])
    if pack:
        merged[sector] = pack
    return merged


def detect_sector(company_name):
    """
    Uses simple keyword matching on the company name to guess the sector.
    Returns one of: 'Banking', 'Technology', 'Healthcare', 'Energy',
    'Real Estate', 'Consulting', or None.
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
    real_estate_signals = [
        "real estate", "reit", "property", "realty", "estate", "land",
        "commercial", "residential", "development", "construction",
    ]
    consulting_signals = [
        "consulting", "advisory", "management consulting", "professional services",
        "accenture", "deloitte", "mckinsey", "bain", "bcg",
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
    for signal in real_estate_signals:
        if signal in name_lower:
            return "Real Estate"
    for signal in consulting_signals:
        if signal in name_lower:
            return "Consulting"

    return None


def get_keyword_summary():
    summary = {}
    for category, keywords in KEYWORDS.items():
        summary[category] = len(keywords)
    return summary


if __name__ == "__main__":
    print("RedFlag Keyword Library v2.0 — Loaded Successfully\n")
    summary = get_keyword_summary()
    for category, count in summary.items():
        print(f"  {category}: {count} keywords")
    print(f"\n  Total: {sum(summary.values())} keywords across {len(KEYWORDS)} categories")
    print(f"\n  Industry Packs: {', '.join(INDUSTRY_PACKS.keys())}")
    detected = detect_sector("JPMorgan Chase Bank")
    print(f"\n  Sector detection test: 'JPMorgan Chase Bank' → {detected}")
