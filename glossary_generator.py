# =============================================================================
# glossary_generator.py — RedFlag Triggered Keyword Glossary (v1.0)
# =============================================================================

import os
from datetime import datetime
from fpdf import FPDF

OUTPUT_DIR = "output"

_CAT_COLORS = {
    "Legal":           (226,  75,  74),
    "Regulatory":      (239, 159,  39),
    "Financial":       ( 26,  26,  46),
    "Operational":     ( 59, 109,  17),
    "Governance":      ( 90,  90, 180),
    "Forward-Looking": (100, 100, 100),
    "Banking":         ( 15,  76, 129),
    "Technology":      ( 41, 128, 185),
    "Healthcare":      ( 22, 160, 133),
    "Energy":          (211,  84,   0),
    "Real Estate":     (142,  68, 173),
    "Consulting":      ( 52,  73,  94),
}
_DEFAULT_COLOR = (80, 80, 80)

_CATEGORY_ORDER = [
    "Legal", "Regulatory", "Financial", "Operational", "Governance",
    "Forward-Looking", "Banking", "Technology", "Healthcare",
    "Energy", "Real Estate", "Consulting",
]

# Pre-written explanations keyed by keyword.lower()
GLOSSARY_EXPLANATIONS = {
    # ── Legal ─────────────────────────────────────────────────────────────────
    "litigation": (
        "The company is party to one or more active lawsuits. Litigation creates "
        "financial uncertainty through potential judgments, settlement payments, and "
        "legal costs, and can distract management from core operations."
    ),
    "lawsuit": (
        "A formal legal action has been brought against the company. Even when the "
        "company ultimately prevails, defending suits consumes management time and "
        "legal spend, and an adverse verdict can be material."
    ),
    "legal proceedings": (
        "Ongoing court or administrative proceedings name the company as a party. "
        "Investors should assess the probability of adverse judgments and the dollar "
        "exposure disclosed in the notes."
    ),
    "class action": (
        "A lawsuit filed on behalf of a group of plaintiffs with similar claims — "
        "typically shareholders or consumers. Class actions can yield large aggregate "
        "damages and signal widespread alleged harm or misconduct."
    ),
    "securities fraud": (
        "Allegations that the company or its officers misled investors through false "
        "statements or material omissions. Securities fraud claims carry severe "
        "financial and reputational consequences and often precede SEC enforcement."
    ),
    "injunction": (
        "A court order requiring the company to stop or perform specific actions. "
        "An injunction can immediately halt revenue-generating activities and signals "
        "a court found merit in a plaintiff's claims."
    ),
    "contempt": (
        "A finding that the company violated a court order. Contempt signals "
        "non-compliance with legal obligations and can result in escalating fines "
        "or operating restrictions."
    ),
    "indictment": (
        "A formal criminal charge has been brought against the company or its "
        "executives. Indictments represent severe legal jeopardy and typically "
        "trigger contract terminations, lender defaults, and regulatory action."
    ),
    "grand jury": (
        "A grand jury investigation signals federal prosecutors are examining "
        "potential criminal conduct. This is a significant escalation beyond civil "
        "proceedings and may result in indictments."
    ),
    "subpoena": (
        "The company has received a legal demand to produce documents or testify. "
        "Subpoenas are often the first visible sign of a government investigation "
        "and can precede enforcement actions or criminal charges."
    ),
    "consent decree": (
        "A formal agreement — typically with a regulator — imposing specific "
        "operating conditions or remediation requirements. Consent decrees restrict "
        "business flexibility and require ongoing compliance monitoring."
    ),
    "cease and desist": (
        "A legal order demanding the company stop a specific activity immediately. "
        "These orders can disrupt operations or product offerings until the "
        "underlying issue is resolved to the issuing authority's satisfaction."
    ),
    "breach of fiduciary duty": (
        "A claim that directors or officers failed to act in shareholders' best "
        "interests. Such claims can result in personal executive liability and "
        "signal governance failures at the board level."
    ),
    "misrepresentation": (
        "Allegations that the company made false or misleading statements. "
        "Misrepresentation claims expose the company to rescission of contracts, "
        "compensatory damages, and potential securities law liability."
    ),
    "disgorgement": (
        "A regulatory or court remedy requiring the company to return ill-gotten "
        "gains. Disgorgement penalties can be substantial and often accompany SEC "
        "enforcement actions for fraud or insider trading."
    ),
    "restatement": (
        "The company has corrected previously issued financial statements. "
        "Restatements indicate prior reporting errors, undermine investor trust, "
        "and frequently precede SEC investigations or securities class actions."
    ),
    "whistleblower": (
        "An employee or insider has reported alleged wrongdoing internally or to "
        "regulators. Whistleblower disclosures often precede enforcement actions "
        "and suggest internal compliance failures went unaddressed."
    ),
    "qui tam": (
        "A lawsuit filed by a private party on behalf of the government, typically "
        "under the False Claims Act. Qui tam suits allege the company defrauded "
        "the government and can result in treble damages plus attorney fees."
    ),
    "false claims act": (
        "Exposure under the U.S. False Claims Act means the company may have "
        "submitted fraudulent invoices or claims to the federal government. "
        "Penalties include treble damages and exclusion from government contracts."
    ),
    "arbitration": (
        "Disputes are being resolved through private arbitration rather than courts. "
        "Outcomes and settlement amounts are rarely disclosed publicly, obscuring "
        "the company's true legal exposure from outside investors."
    ),
    "settlement agreement": (
        "The company has agreed to pay or perform in exchange for dismissing a "
        "claim. Repeated settlements may signal systemic legal or compliance "
        "problems rather than isolated incidents."
    ),
    "preliminary injunction": (
        "A court has temporarily halted a company activity while a case proceeds. "
        "A preliminary injunction signals the court found a reasonable likelihood "
        "of plaintiff success, increasing overall litigation risk."
    ),
    "permanent injunction": (
        "A final court order permanently prohibiting a specific business practice. "
        "Unlike temporary orders, permanent injunctions represent final adverse "
        "rulings that require lasting operational changes."
    ),
    "criminal charges": (
        "The company or its executives face formal criminal prosecution. Criminal "
        "charges carry the most severe consequences — fines, debarment from "
        "government contracts, and possible imprisonment for individuals."
    ),
    "deferred prosecution": (
        "A criminal charge is suspended pending the company's compliance with "
        "agreed conditions. Deferred prosecution agreements acknowledge wrongdoing "
        "and impose ongoing obligations under government monitoring."
    ),
    "regulatory investigation": (
        "A government agency is examining the company's conduct. Investigations "
        "are lengthy, expensive, and uncertain — outcomes range from no-action "
        "letters to large fines, consent orders, or criminal referrals."
    ),
    "government inquiry": (
        "A government body has formally requested information. Inquiries are early "
        "indicators of broader investigations and can escalate into enforcement "
        "actions if substantive issues are uncovered."
    ),
    "alleged violation": (
        "A regulator, plaintiff, or third party claims the company broke a law or "
        "rule. Even unproven allegations create headline risk, legal costs, and "
        "potential liability if the claim is later validated."
    ),
    "pending litigation": (
        "Lawsuits that have not yet been resolved represent contingent liabilities "
        "that may crystallize into cash outflows or operational restrictions as "
        "proceedings advance."
    ),
    "legal liability": (
        "The company faces potential financial obligations from legal claims. "
        "Understated or undisclosed legal liabilities can distort the true "
        "financial picture and lead to unexpected cash outflows."
    ),
    "judicial proceedings": (
        "Formal court proceedings involve the company. Adverse rulings can have "
        "material financial or operational consequences that are difficult to "
        "predict until proceedings conclude."
    ),
    "legal challenge": (
        "Business practices, products, or intellectual property are being "
        "challenged in court. Sustained legal challenges delay strategy, impose "
        "costs, or force changes to core operations."
    ),
    "regulatory sanction": (
        "A formal penalty imposed by a regulator for non-compliance. Sanctions "
        "signal prior violations, impose direct financial costs, and typically "
        "require remediation programs under government oversight."
    ),
    "fine and penalty": (
        "The company has been assessed financial penalties by a court or regulator. "
        "Fines reduce cash and earnings and may signal broader compliance failures "
        "that require systemic remediation."
    ),
    "legal dispute": (
        "An unresolved disagreement with a third party that may lead to or is "
        "already in litigation. Legal disputes divert management attention and "
        "create contingent financial liabilities."
    ),
    "court order": (
        "A binding instruction from a court requiring the company to act or refrain "
        "from acting in a specific way. Violating a court order constitutes contempt "
        "and can accelerate legal consequences."
    ),
    "derivative action": (
        "A lawsuit brought by shareholders on behalf of the company against its "
        "own directors or officers. Derivative suits signal board-level governance "
        "failures and can result in damages or forced leadership changes."
    ),
    "patent infringement": (
        "A claim that the company's products or processes use intellectual property "
        "without authorization. Infringement findings can result in injunctions "
        "halting product sales and substantial royalty or damages payments."
    ),
    "trade secret misappropriation": (
        "An allegation that the company unlawfully acquired or used another party's "
        "confidential information. Such claims can result in injunctions, damages, "
        "and damage to client and employee relationships."
    ),
    "shareholder lawsuit": (
        "Shareholders are suing the company over alleged harm to their interests. "
        "These suits often accompany stock price declines and can result in "
        "settlements that further reduce shareholder value."
    ),
    "doj investigation": (
        "The U.S. Department of Justice is investigating the company. DOJ "
        "investigations carry the risk of criminal prosecution, debarment, and "
        "very large financial penalties."
    ),
    "ftc action": (
        "The Federal Trade Commission has initiated action against the company, "
        "typically for antitrust or consumer protection violations. FTC actions "
        "can force divestitures, consent orders, and significant fines."
    ),
    "plea agreement": (
        "The company or an executive has entered a guilty plea to criminal charges. "
        "Plea agreements confirm wrongdoing, impose penalties, and often require "
        "the company to submit to ongoing government monitoring."
    ),
    "unfair competition": (
        "Claims that the company engaged in deceptive or anti-competitive business "
        "practices. Findings can result in injunctions, damages, and reputational "
        "harm with customers and business partners."
    ),
    "defamation claim": (
        "A claim that the company made false statements harming another party's "
        "reputation. Defamation liability creates financial exposure and can damage "
        "business relationships if the company is found liable."
    ),

    # ── Regulatory ─────────────────────────────────────────────────────────────
    "sanctions": (
        "The company operates with sanctioned countries, entities, or individuals. "
        "Violations of economic sanctions can result in massive fines, reputational "
        "damage, and criminal liability for executives."
    ),
    "ofac": (
        "Involvement with entities on the OFAC Specially Designated Nationals list "
        "signals potential sanctions violations. OFAC enforcement actions have "
        "resulted in multi-billion-dollar penalties."
    ),
    "aml": (
        "Anti-money laundering compliance issues suggest financial controls may have "
        "been exploited for illicit transactions. AML failures attract heavy "
        "regulatory penalties and reputational damage."
    ),
    "anti-money laundering": (
        "Deficiencies in the anti-money laundering program indicate systemic "
        "compliance weaknesses. Regulators take AML failures seriously and have "
        "imposed billion-dollar fines on major financial institutions."
    ),
    "kyc": (
        "Failures in Know Your Customer procedures mean the company may not "
        "adequately verify client identities, opening the door to financial crime "
        "exposure and regulatory sanctions."
    ),
    "know your customer": (
        "Inadequate verification of customer identities increases the company's "
        "exposure to financial crime and regulatory penalties. Regulators require "
        "robust KYC programs, especially in financial services."
    ),
    "gdpr": (
        "Exposure under the EU General Data Protection Regulation signals potential "
        "personal data handling failures. GDPR fines can reach 4% of global annual "
        "revenue and also trigger class action lawsuits."
    ),
    "data breach": (
        "Unauthorized parties accessed sensitive company or customer data. Data "
        "breaches create regulatory liability, litigation risk, remediation costs, "
        "and lasting reputational harm."
    ),
    "cybersecurity incident": (
        "A cyberattack, intrusion, or security failure has occurred or is a material "
        "risk. Incidents disrupt operations, trigger mandatory regulatory notifications, "
        "and frequently result in class action suits."
    ),
    "regulatory capital": (
        "The company may not maintain required minimum capital levels set by "
        "regulators. Falling below thresholds can trigger supervisory intervention, "
        "restrict dividends, and limit business activity."
    ),
    "stress test": (
        "Regulatory stress testing requirements signal the company operates in a "
        "heavily supervised environment. Failing a stress test can restrict capital "
        "returns and require remediation plans filed with regulators."
    ),
    "living will": (
        "A resolution plan is required by regulators for systemically important "
        "firms. Deficiencies signal the company may not be orderly resolvable "
        "without government intervention."
    ),
    "resolution plan": (
        "Regulators require a plan for winding down in an orderly fashion. An "
        "inadequate plan imposes operational constraints and signals the company "
        "is considered systemically significant."
    ),
    "market manipulation": (
        "Allegations that the company manipulated prices or trading volumes. "
        "Market manipulation is a serious securities law violation carrying "
        "criminal liability, large fines, and reputational damage."
    ),
    "insider trading": (
        "Allegations or disclosures of trading on material non-public information. "
        "Violations expose executives to criminal prosecution and the company to "
        "SEC enforcement and shareholder lawsuits."
    ),
    "sarbanes-oxley": (
        "Sarbanes-Oxley compliance issues signal weaknesses in financial reporting "
        "controls. Violations can lead to SEC enforcement, personal liability for "
        "executives, and damaged auditor relationships."
    ),
    "sox 404": (
        "A material weakness or deficiency in internal controls under SOX Section "
        "404 indicates financial statements may be unreliable. Findings require "
        "remediation and increase audit costs."
    ),
    "material weakness": (
        "A material weakness in internal controls means there is a reasonable "
        "possibility of material misstatement in the financial statements. This is "
        "the most severe internal control deficiency and may require restatement."
    ),
    "significant deficiency": (
        "A notable internal control gap that, while less severe than a material "
        "weakness, still indicates financial reporting processes are not functioning "
        "optimally and warrant remediation."
    ),
    "control failure": (
        "A failure in internal controls has been identified. Control failures allow "
        "errors or fraud to go undetected and may escalate to material weaknesses "
        "if not promptly corrected."
    ),
    "enforcement action": (
        "A regulator has formally initiated disciplinary proceedings. Enforcement "
        "actions typically result in fines, consent orders, and operational "
        "constraints, with outcomes publicly disclosed to all stakeholders."
    ),
    "consent order": (
        "The company has entered a binding agreement with a regulator to undertake "
        "specific remediation steps. Consent orders impose operational restrictions "
        "and monitoring requirements."
    ),
    "memorandum of understanding": (
        "A regulatory MOU signals informal supervisory pressure that has not yet "
        "escalated to a formal enforcement action, typically requiring the company "
        "to address identified weaknesses within defined timeframes."
    ),
    "corrective action plan": (
        "A regulator has required a formal plan to fix identified deficiencies. "
        "Corrective action plans impose operational constraints and deadlines; "
        "failure to meet them typically escalates to formal enforcement."
    ),
    "regulatory scrutiny": (
        "Regulators are actively examining the company's practices. Heightened "
        "scrutiny limits strategic flexibility, increases compliance costs, and "
        "frequently precedes formal enforcement actions."
    ),
    "regulatory change": (
        "New or proposed regulations may materially alter the company's operating "
        "environment. Changes can raise compliance costs, restrict profitable "
        "activities, or require business model adjustments."
    ),
    "compliance failure": (
        "The company failed to adhere to applicable laws, regulations, or internal "
        "policies. Failures attract penalties, operational restrictions, and damage "
        "to relationships with regulators and customers."
    ),
    "non-compliance": (
        "The company is not meeting regulatory or legal requirements. Non-compliance "
        "findings trigger fines, license revocations, and reputational harm, and "
        "often require costly remediation programs."
    ),
    "government regulation": (
        "The company's business is subject to significant government oversight. "
        "Increased regulation raises compliance costs and can restrict profitable "
        "activities, particularly when regulatory direction is uncertain."
    ),
    "new legislation": (
        "Pending or recently enacted laws could materially affect the company. "
        "New legislation can impose compliance costs, restrict business practices, "
        "or create new liability exposures not contemplated in existing plans."
    ),
    "policy uncertainty": (
        "Uncertainty around government policy creates planning and forecasting risk, "
        "particularly disruptive for businesses dependent on stable regulatory "
        "frameworks or government contracts."
    ),
    "export control": (
        "The company's products or technology are subject to export restrictions. "
        "Violations can result in large fines, debarment from government contracts, "
        "and reputational harm."
    ),
    "antitrust": (
        "Antitrust scrutiny signals regulators believe the company may have "
        "anti-competitive market power. Actions can force divestitures, restrict "
        "acquisitions, and result in significant financial penalties."
    ),
    "environmental regulation": (
        "The company faces legal obligations under environmental laws. Evolving "
        "environmental regulations can impose costly compliance requirements, "
        "cleanup liabilities, and operational restrictions."
    ),
    "data privacy": (
        "The company handles personal data subject to privacy regulations. Failures "
        "attract regulatory fines and class action suits and can erode consumer "
        "trust in the company's products and services."
    ),
    "sec investigation": (
        "The U.S. Securities and Exchange Commission is investigating the company. "
        "SEC investigations carry serious risk of enforcement actions, fines, trading "
        "restrictions, and reputational damage."
    ),
    "fda approval": (
        "Key products require FDA approval to reach market. Delays or denials can "
        "significantly defer revenue and require costly product reformulations or "
        "additional clinical studies."
    ),
    "regulatory approval": (
        "Key business activities depend on obtaining regulatory approval. Delays, "
        "conditions, or denials can halt product launches, acquisitions, or market "
        "entries, creating material financial risk."
    ),
    "license revocation": (
        "A key operating license may be or has been revoked. Revocations can "
        "immediately halt operations in the affected area and signal severe "
        "non-compliance with regulatory requirements."
    ),
    "permit denial": (
        "A permit required for operations or expansion has been denied. Denials "
        "can delay or permanently block projects, requiring costly re-engineering "
        "or abandonment of planned activities."
    ),

    # ── Financial ─────────────────────────────────────────────────────────────
    "going concern": (
        "The company's auditors have expressed doubt about its ability to continue "
        "operating for the next 12 months. A going concern opinion is one of the "
        "most severe financial red flags and often precedes bankruptcy filings."
    ),
    "covenant breach": (
        "The company violated a condition in its loan or bond agreements. Covenant "
        "breaches can trigger immediate debt acceleration, restrict new borrowing, "
        "and require lender waivers under unfavorable terms."
    ),
    "covenant violation": (
        "A breach of financial covenants embedded in debt agreements gives lenders "
        "the right to demand immediate repayment, which can precipitate a "
        "liquidity crisis."
    ),
    "debt covenant": (
        "Loan agreements include financial maintenance requirements. Approaching or "
        "breaching these thresholds signals financial stress and can trigger "
        "acceleration of all outstanding debt."
    ),
    "borrowing base": (
        "The maximum borrowable amount under a revolving credit facility is "
        "constrained by an asset formula. A declining borrowing base reduces "
        "available liquidity and may signal deteriorating asset quality."
    ),
    "credit facility terminated": (
        "A lender cancelled the company's revolving credit line. Termination "
        "removes a key liquidity buffer and indicates lenders have lost confidence "
        "in the company's creditworthiness."
    ),
    "acceleration of debt": (
        "Lenders have demanded immediate repayment of outstanding debt. Acceleration "
        "occurs after a covenant breach and may force emergency asset sales or "
        "a bankruptcy filing."
    ),
    "cross-default": (
        "A default on one debt obligation triggers defaults under other agreements. "
        "Cross-default clauses cause a cascade of simultaneous debt accelerations "
        "that can rapidly exhaust the company's liquidity."
    ),
    "leverage ratio breach": (
        "The company's debt-to-earnings or debt-to-assets ratio exceeded permitted "
        "limits. Breaches restrict borrowing and may trigger mandatory repayment or "
        "lender-imposed operating restrictions."
    ),
    "interest coverage": (
        "A low or declining ratio signals the company generates insufficient "
        "operating profit to comfortably service its debt. Falling below 1.5x "
        "coverage is a common early warning sign of financial stress."
    ),
    "negative working capital": (
        "Current liabilities exceed current assets, creating near-term cash flow "
        "pressure. Persistent negative working capital signals difficulty meeting "
        "short-term obligations as they fall due."
    ),
    "cash burn": (
        "The company is consuming cash faster than it generates it. A high burn "
        "rate limits operational runway and may require dilutive equity raises or "
        "additional borrowing to sustain operations."
    ),
    "runway": (
        "The company has a finite time before it runs out of cash. A short runway "
        "creates existential pressure to secure financing on potentially "
        "unfavorable terms."
    ),
    "liquidity crisis": (
        "The company cannot meet its short-term financial obligations. A liquidity "
        "crisis can quickly lead to bankruptcy or forced asset sales at "
        "distressed prices."
    ),
    "capital raise required": (
        "The company must raise new equity or debt to fund operations or growth. "
        "Required raises signal insufficient internal cash generation and are "
        "frequently dilutive to existing shareholders."
    ),
    "dilution": (
        "Existing shareholders' ownership percentage is being reduced through new "
        "share issuances. Dilution reduces per-share earnings and value and is "
        "particularly concerning when driven by financial distress."
    ),
    "goodwill impairment": (
        "The company wrote down goodwill from a prior acquisition, signaling the "
        "acquired business is underperforming. Impairments reduce book value and "
        "may signal poor prior investment decisions."
    ),
    "asset impairment": (
        "The carrying value of assets exceeds their recoverable amount. Asset "
        "impairments reduce reported earnings and book value and can signal "
        "deteriorating business fundamentals."
    ),
    "write-down": (
        "The company reduced the book value of an asset to reflect its true "
        "economic value. Write-downs reduce net income and equity and often "
        "indicate overoptimistic prior valuations."
    ),
    "write-off": (
        "An asset has been removed from the balance sheet as unrecoverable. "
        "Write-offs are a direct charge against earnings and may reflect "
        "failed business ventures or uncollectable receivables."
    ),
    "contingent liability": (
        "The company has a potential financial obligation that depends on a future "
        "event. Understated contingent liabilities can materially misrepresent "
        "the company's true financial position."
    ),
    "off-balance sheet": (
        "The company has financial arrangements not fully reflected on its balance "
        "sheet. Off-balance sheet structures can obscure the true level of "
        "the company's debt and financial risk."
    ),
    "variable interest entity": (
        "The company consolidates or has exposure to entities where control is "
        "based on economic interest rather than voting shares. VIE structures "
        "can obscure leverage and create unexpected consolidation requirements."
    ),
    "related party loan": (
        "Loans exist with insiders, directors, or affiliated entities. Related "
        "party loans create conflict-of-interest risks and may indicate poor "
        "governance or self-dealing."
    ),
    "pledge of assets": (
        "Company assets have been pledged as collateral. Pledged assets restrict "
        "operational flexibility, and in a default scenario creditors can seize "
        "them, potentially impairing ongoing operations."
    ),
    "substantial doubt": (
        "Management or auditors have raised substantial doubt about the ability "
        "to continue as a going concern. This is an explicit signal of severe "
        "financial stress that warrants immediate scrutiny."
    ),
    "liquidity risk": (
        "The company may have difficulty meeting financial obligations as they fall "
        "due. Liquidity risk can escalate rapidly during market stress or when "
        "credit lines are reduced or withdrawn."
    ),
    "default": (
        "The company has failed to meet a financial obligation as required. A "
        "default triggers cross-default clauses, accelerates debt, and can "
        "precipitate a bankruptcy filing if not cured promptly."
    ),
    "insolvency": (
        "The company's liabilities exceed its assets or it cannot pay debts as they "
        "fall due. Insolvency is a direct precursor to bankruptcy and often results "
        "in total loss for equity holders."
    ),
    "bankruptcy": (
        "The company has filed for or is approaching formal bankruptcy protection. "
        "Bankruptcy typically results in significant or total loss for equity "
        "holders and substantial disruption to operations."
    ),
    "chapter 11": (
        "The company filed for Chapter 11 bankruptcy protection in the U.S. While "
        "Chapter 11 allows continued operations, it indicates severe financial "
        "distress and often results in equity dilution or elimination."
    ),
    "negative cash flow": (
        "The company is spending more cash than it generates from operations. "
        "Sustained negative cash flow depletes reserves, increases debt dependency, "
        "and limits investment in growth."
    ),
    "working capital deficit": (
        "Current liabilities exceed current assets, creating a near-term funding "
        "gap. This signals potential difficulty meeting upcoming obligations "
        "without additional financing."
    ),
    "accumulated deficit": (
        "The company has incurred more total losses than profits since inception. "
        "A large accumulated deficit signals the company has not achieved sustained "
        "profitability and raises long-term funding concerns."
    ),
    "net loss": (
        "The company's expenses exceeded revenues in the reporting period. Recurring "
        "net losses erode cash, require external financing, and signal the business "
        "has not yet achieved a sustainable operating model."
    ),
    "revenue decline": (
        "The company's revenues are falling year-over-year, signaling potential "
        "market share loss, pricing pressure, or customer attrition. Declining "
        "revenues reduce the company's ability to fund operations and growth."
    ),
    "margin compression": (
        "The gap between revenues and costs is narrowing. Margin compression signals "
        "pricing power erosion, rising input costs, or operational inefficiency "
        "that threatens long-term profitability."
    ),
    "credit facility": (
        "The company relies on a bank credit facility for liquidity. Dependence "
        "creates risk if lenders reduce, restrict, or withdraw access, particularly "
        "in adverse market conditions."
    ),

    # ── Operational ───────────────────────────────────────────────────────────
    "key person": (
        "The company's performance depends heavily on one or a few specific "
        "individuals. Unexpected departure of a key person can disrupt operations, "
        "strategy, and customer relationships with little warning."
    ),
    "key employee departure": (
        "Critical employees have left or may leave. Executive or technical departures "
        "signal internal problems, reduce capabilities, and lead to knowledge loss "
        "that can take years to rebuild."
    ),
    "succession plan": (
        "The company lacks a clear plan for leadership transitions. Weak succession "
        "planning creates organizational risk when key leaders depart, retire, or "
        "become unavailable unexpectedly."
    ),
    "single customer": (
        "The company depends on one customer for a disproportionate share of "
        "revenue. Loss of that customer can cause a sudden, severe revenue shortfall "
        "with limited short-term ability to compensate."
    ),
    "customer concentration": (
        "A small number of customers account for a large portion of revenue. "
        "Concentration risk means losing even one major customer can materially "
        "impair financial performance."
    ),
    "revenue concentration": (
        "Revenue is heavily concentrated in a specific product, geography, or "
        "customer segment. A single adverse event can therefore disproportionately "
        "impact total company revenue."
    ),
    "geographic concentration": (
        "Operations or revenues are concentrated in a single region or country. "
        "This amplifies exposure to local regulatory changes, economic downturns, "
        "or geopolitical instability."
    ),
    "single supplier": (
        "The company depends on one supplier for a critical input. A single-source "
        "relationship creates vulnerability to supply disruptions, price increases, "
        "or supplier financial failure."
    ),
    "supply disruption": (
        "Interruptions in the supply chain have occurred or are a material risk. "
        "Disruptions can halt production, delay deliveries, damage customer "
        "relationships, and cascade into financial impacts."
    ),
    "force majeure": (
        "Events beyond the company's control — natural disasters, wars, pandemics — "
        "may prevent contractual performance. Force majeure events can disrupt "
        "revenues, trigger contract disputes, and increase costs."
    ),
    "business continuity": (
        "The company's ability to maintain operations during disruptive events is "
        "at risk. Inadequate business continuity planning can result in prolonged "
        "outages with severe financial and reputational consequences."
    ),
    "disaster recovery": (
        "The company may not restore systems and operations quickly after a major "
        "incident. Weak disaster recovery capabilities can extend outages and cause "
        "significant customer and revenue loss."
    ),
    "system outage": (
        "Technology system failures have occurred or represent a material risk. "
        "Outages can halt revenue-generating activities, expose the company to "
        "contractual penalties, and damage customer trust."
    ),
    "data loss": (
        "Critical data has been lost or is at risk. Data loss results in regulatory "
        "penalties, legal claims, operational disruptions, and significant costs "
        "to recover or reconstruct."
    ),
    "product recall": (
        "The company recalled or may recall a product due to defects or safety "
        "concerns. Recalls generate direct costs, potential litigation, and lasting "
        "damage to brand reputation."
    ),
    "safety incident": (
        "A workplace or product safety incident has occurred. Safety incidents "
        "create regulatory liability, potential litigation, and can impair the "
        "company's ability to attract and retain employees."
    ),
    "environmental violation": (
        "The company violated environmental laws or regulations. Violations result "
        "in fines, cleanup obligations, operating permit revocations, and "
        "reputational harm with ESG-focused investors."
    ),
    "esg controversy": (
        "The company is involved in a controversy related to environmental, social, "
        "or governance practices. ESG controversies can trigger investor divestment, "
        "media scrutiny, and customer boycotts."
    ),
    "greenwashing": (
        "Allegations that the company overstated or fabricated its environmental "
        "credentials. Greenwashing exposes the company to regulatory action, "
        "investor lawsuits, and reputational damage."
    ),
    "carbon liability": (
        "The company faces financial exposure related to carbon emissions through "
        "taxes, trading schemes, or legal claims. Carbon liability is growing as "
        "regulators and investors demand decarbonization."
    ),
    "stranded assets": (
        "The company holds assets that may lose value prematurely due to regulatory, "
        "market, or technological change. Stranded assets require impairments and "
        "signal business model risk in the energy transition."
    ),
    "technology obsolescence": (
        "The company's products or infrastructure face the risk of becoming "
        "technologically outdated. Obsolescence erodes competitive position and "
        "requires ongoing R&D investment to remain relevant."
    ),
    "competitive displacement": (
        "Competitors are taking market share from the company. Displacement reduces "
        "revenue growth and compresses margins as the company responds with "
        "pricing cuts or increased spending."
    ),
    "market share loss": (
        "The company's share of its addressable market is declining. This typically "
        "signals a weakening competitive position and may presage further revenue "
        "deterioration."
    ),
    "pricing pressure": (
        "The company faces difficulty maintaining prices due to competition or "
        "customer bargaining power. Pricing pressure compresses margins even when "
        "volumes remain stable."
    ),
    "dependence on single customer": (
        "A single customer represents a disproportionate share of revenue, creating "
        "severe vulnerability to that customer's decisions, financial health, and "
        "renegotiation leverage."
    ),
    "supply chain disruption": (
        "The company's supply chain has been or may be interrupted. Disruptions "
        "increase costs, delay production, and can result in contract penalties "
        "and customer attrition if deliveries are not met."
    ),
    "talent retention": (
        "The company struggles to retain key employees. High turnover increases "
        "recruitment costs, reduces organizational knowledge, and can impair "
        "product quality and customer relationships."
    ),
    "labor shortage": (
        "Difficulty hiring qualified workers is impairing operations. Labor "
        "shortages increase wages, reduce output capacity, and can delay "
        "expansion plans or service delivery."
    ),
    "union dispute": (
        "The company is in conflict with employee unions. Disputes can result in "
        "strikes, work slowdowns, and renegotiated labor contracts that increase "
        "costs or restrict operational flexibility."
    ),
    "strike": (
        "Employees have gone on strike or threatened to do so. Strikes halt "
        "production, damage customer relationships, and impose significant "
        "financial costs, particularly in manufacturing or logistics."
    ),
    "intellectual property theft": (
        "Proprietary technology or trade secrets have been or may be stolen. IP "
        "theft eliminates competitive advantages built over years of R&D investment "
        "and is difficult to fully remediate."
    ),
    "platform dependency": (
        "The company's business relies on a third-party platform it does not "
        "control. Policy changes, fee increases, or de-platforming decisions by "
        "the operator create material concentration risk."
    ),
    "vendor lock-in": (
        "The company cannot easily switch away from a critical vendor, reducing "
        "negotiating leverage, creating single-point-of-failure risk, and may "
        "result in escalating costs over time."
    ),
    "third party dependency": (
        "Critical functions depend on third parties. Failures, pricing changes, or "
        "relationship terminations by those parties can directly impact the "
        "company's own service delivery."
    ),
    "outsourcing risk": (
        "Critical functions performed by outside vendors may not be adequately "
        "controlled. Outsourcing risk includes quality failures, data exposure, "
        "and vendor instability that can disrupt operations."
    ),
    "cloud dependency": (
        "Operations depend on cloud infrastructure from a limited set of providers. "
        "Cloud outages or provider failures can halt operations and create "
        "compliance issues if service level agreements are not met."
    ),
    "algorithm change": (
        "Changes to platform algorithms affect the company's ability to reach "
        "customers or generate revenue. Algorithm changes by third parties can "
        "rapidly and unpredictably alter business fundamentals."
    ),
    "platform risk": (
        "The company's business model is exposed to disruption from platform policy "
        "changes or shutdowns. This risk is acute for businesses built on a single "
        "distribution channel or marketplace."
    ),
    "reputational damage": (
        "The company has suffered or risks significant damage to its brand or public "
        "standing. Reputational damage reduces customer acquisition, increases "
        "employee turnover, and impairs access to capital."
    ),

    # ── Governance ────────────────────────────────────────────────────────────
    "board independence": (
        "The company's board lacks sufficient independent directors to provide "
        "effective oversight of management. Poor independence reduces accountability "
        "and increases the risk of decisions that favor insiders."
    ),
    "related party transaction": (
        "The company transacts with entities or individuals connected to its insiders. "
        "These transactions create conflict-of-interest risks and may not be "
        "conducted on arm's length terms."
    ),
    "self-dealing": (
        "Company insiders are directing business to entities they personally "
        "benefit from. Self-dealing is a serious governance failure that harms "
        "shareholder interests and may constitute fraud."
    ),
    "executive misconduct": (
        "Allegations or findings of improper conduct by senior management undermine "
        "investor confidence, attract regulatory scrutiny, and can trigger "
        "leadership departures."
    ),
    "clawback": (
        "The company has obligations to recover previously paid executive "
        "compensation. Clawback disclosures often accompany restatements or "
        "findings of executive misconduct."
    ),
    "say on pay": (
        "Shareholders have expressed concerns about executive compensation through "
        "advisory votes. A failed say-on-pay vote signals investor dissatisfaction "
        "with pay-for-performance alignment."
    ),
    "poison pill": (
        "The company adopted a shareholder rights plan that dilutes hostile "
        "acquirers. Poison pills entrench management and can destroy value by "
        "deterring potentially beneficial acquisition offers."
    ),
    "staggered board": (
        "Only a portion of the board stands for election each year, making it "
        "difficult for shareholders to quickly replace directors. Staggered boards "
        "reduce management accountability."
    ),
    "dual class shares": (
        "The company has share classes with different voting rights. Dual class "
        "structures concentrate control with founders or insiders, limiting other "
        "shareholders' ability to influence company direction."
    ),
    "activist investor": (
        "A significant shareholder is publicly pressuring management for changes. "
        "Activist campaigns signal investor dissatisfaction and can lead to board "
        "changes, spin-offs, or strategic pivots."
    ),
    "proxy contest": (
        "Shareholders are attempting to elect their own director nominees. Proxy "
        "contests signal serious disagreement with management strategy and can "
        "result in board turnover and strategic changes."
    ),
    "hostile takeover": (
        "An unsolicited acquisition attempt has been made or is at risk. Hostile "
        "situations create uncertainty for employees and counterparties and may "
        "result in significant management and strategy changes."
    ),
    "change of control": (
        "A transaction or event may trigger change-of-control provisions in "
        "contracts, debt agreements, or employee plans. These can trigger "
        "significant costs, debt acceleration, or talent departures."
    ),
    "golden parachute": (
        "Executives are entitled to large payments upon a change of control. "
        "Golden parachutes create misaligned incentives and can reduce the "
        "attractiveness of the company to potential acquirers."
    ),
    "excessive compensation": (
        "Executive pay appears disconnected from company performance. Excessive "
        "compensation diverts resources from shareholders and signals weak "
        "board oversight of management."
    ),
    "audit committee": (
        "Issues with the audit committee's composition or function have been "
        "identified. An ineffective audit committee is a serious governance "
        "red flag that weakens financial reporting integrity."
    ),
    "independence concern": (
        "Questions have been raised about the independence of directors, auditors, "
        "or committee members. Lack of independence undermines objective oversight "
        "and increases the risk of conflicts of interest."
    ),
    "conflicts of interest": (
        "Directors, officers, or key employees have interests that may conflict "
        "with those of the company or its shareholders, compromising decision-making "
        "and potentially harming shareholder value."
    ),
    "nepotism": (
        "Family members or personal connections of insiders are being hired or "
        "advantaged. Nepotism signals governance weakness and can lead to regulatory "
        "scrutiny and shareholder dissatisfaction."
    ),
    "diversity disclosure": (
        "The company flagged concerns or risks related to workforce or board "
        "diversity. Inadequate diversity disclosure attracts regulatory attention "
        "and can signal reputational and governance gaps."
    ),
    "esg rating downgrade": (
        "An independent ESG rating agency has lowered the company's score. "
        "Downgrades trigger divestment by ESG-mandated investors and signal "
        "unresolved environmental, social, or governance concerns."
    ),
    "founder dependency": (
        "Strategy, culture, or operations are heavily dependent on the company's "
        "founder. Founder dependency creates key person risk and may signal "
        "insufficient organizational depth."
    ),
    "key man risk": (
        "The company's ability to operate depends on the continued involvement "
        "of one or a few specific individuals. This risk is especially acute in "
        "smaller companies or those with concentrated leadership."
    ),
    "quality control failure": (
        "Quality assurance processes have failed to prevent defective products or "
        "services. Failures trigger recalls, liability claims, and reputational "
        "damage."
    ),
    "manufacturing defect": (
        "Products were produced with physical or functional defects. Manufacturing "
        "defects create product liability exposure, recall costs, and reputational "
        "harm."
    ),
    "employee misconduct": (
        "Employees engaged in dishonest, illegal, or policy-violating behavior. "
        "Misconduct creates legal liability, regulatory scrutiny, and reputational "
        "risk."
    ),
    "product liability": (
        "The company faces legal claims arising from harm caused by its products. "
        "Product liability suits can result in large damages awards and force "
        "costly product design changes."
    ),
    "contractual dispute": (
        "The company and a counterparty disagree over contract terms or performance. "
        "Disputes create litigation risk, financial liabilities, and may damage "
        "important business relationships."
    ),
    "channel concentration": (
        "The company sells predominantly through a limited number of distribution "
        "channels. This creates vulnerability if the channel partner changes terms, "
        "reduces allocation, or fails."
    ),

    # ── Forward-Looking ────────────────────────────────────────────────────────
    "no assurance": (
        "Management explicitly cannot guarantee a stated outcome. This language "
        "signals genuine uncertainty about the company's ability to execute its "
        "stated strategy or meet disclosed targets."
    ),
    "cannot guarantee": (
        "The company explicitly acknowledges it cannot promise a positive outcome. "
        "This hedging in a formal filing is a deliberate signal that management "
        "considers a negative scenario to be a real possibility."
    ),
    "may not be able": (
        "The company admits it may fail to achieve a key objective. This hedge "
        "signals that management is uncertain about its ability to execute a "
        "material part of its business plan."
    ),
    "significant uncertainty": (
        "The company faces material unknowns in its operating environment. "
        "Significant uncertainty signals that financial forecasts may be unreliable "
        "and outcomes could vary widely from expectations."
    ),
    "highly uncertain": (
        "The company's future outcomes are described as highly unpredictable. "
        "This signals that management cannot provide meaningful guidance and "
        "that financial projections carry low confidence."
    ),
    "unpredictable": (
        "Key variables in the operating environment cannot be forecast. "
        "Unpredictability in core business drivers increases the range of possible "
        "outcomes and complicates financial modeling."
    ),
    "adverse conditions": (
        "The company faces or expects conditions harmful to its business. "
        "Adverse conditions disclosures signal the operating environment is actively "
        "working against the company's financial objectives."
    ),
    "unfavorable conditions": (
        "Market or economic conditions are working against the company's interests. "
        "This disclosure indicates that external headwinds are material enough for "
        "management to specifically flag them in the filing."
    ),
    "deteriorating": (
        "Key business metrics or external conditions are worsening. Deteriorating "
        "trends warn that financial performance may worsen beyond current "
        "reported results."
    ),
    "challenging environment": (
        "Management acknowledges the operating environment is difficult. This is "
        "a qualitative warning that conditions making it harder to achieve targets "
        "are present and not yet resolved."
    ),
    "headwinds": (
        "The company faces forces impeding its financial performance. Explicit "
        "headwind disclosures signal that management expects ongoing pressure on "
        "revenues, margins, or growth."
    ),
    "macro uncertainty": (
        "Broad economic or market conditions are volatile and unpredictable. "
        "Macro uncertainty can affect demand, credit availability, and cost "
        "structures in ways management cannot fully mitigate."
    ),
    "geopolitical risk": (
        "International political tensions or conflicts threaten the company's "
        "operations or revenues. This is particularly relevant for companies with "
        "international supply chains or significant non-domestic sales."
    ),
    "currency risk": (
        "Exchange rate movements could materially affect the company's financials. "
        "Currency risk is most acute for companies with significant non-domestic "
        "revenues or costs that are not hedged."
    ),
    "interest rate sensitivity": (
        "Changes in interest rates could significantly affect borrowing costs or "
        "asset values. High sensitivity is a material risk in rising or volatile "
        "rate environments."
    ),
    "inflation impact": (
        "Rising prices are increasing the company's costs or reducing consumer "
        "purchasing power. Inflation erodes margins when costs rise faster than "
        "the company can pass price increases to customers."
    ),
    "recessionary conditions": (
        "The economy is contracting or at risk of contraction, reducing demand "
        "for the company's products or services. Recessions amplify credit risk, "
        "reduce revenues, and can trigger covenant breaches."
    ),
    "demand weakness": (
        "Customer demand for the company's offerings is soft or declining. "
        "Demand weakness drives revenue shortfalls and can force price cuts "
        "that further compress already-thin margins."
    ),
    "pending rulemaking": (
        "New regulations under development could alter the company's operating "
        "environment. Pending rulemaking creates planning uncertainty and may "
        "require costly compliance investments once finalized."
    ),
    "tariff": (
        "Import or export tariffs are affecting the company's cost structure "
        "or competitive position. Tariffs can render products uncompetitive "
        "or significantly increase input costs with limited ability to offset."
    ),
    "import restriction": (
        "Restrictions on the importation of goods or materials affect the supply "
        "chain or sales. Import restrictions can disrupt production and force "
        "expensive alternative sourcing."
    ),
    "trade restriction": (
        "Government-imposed limits on trade affect the company's ability to sell "
        "into or source from key markets. Trade restrictions can materially reduce "
        "addressable markets or increase costs."
    ),
    "uncertain outcome": (
        "The resolution of a key matter cannot be predicted. Uncertain outcomes on "
        "material issues — litigation, regulatory decisions, or contract negotiations "
        "— create unquantifiable financial risk."
    ),

    # ── Banking pack ──────────────────────────────────────────────────────────
    "net interest margin": (
        "The spread between interest earned and interest paid is compressing. "
        "Falling net interest margins reduce bank profitability and signal "
        "pricing pressure or an unfavorable rate environment."
    ),
    "tier 1 capital": (
        "The bank's highest-quality capital buffer may be under pressure. A "
        "declining Tier 1 ratio limits growth, dividends, and buybacks and may "
        "attract regulatory intervention."
    ),
    "tier 2 capital": (
        "The bank's supplementary capital may not be sufficient to absorb losses. "
        "Pressure on Tier 2 ratios signals balance sheet stress and can affect "
        "the bank's regulatory standing."
    ),
    "basel": (
        "The bank faces compliance obligations under the Basel regulatory framework. "
        "New Basel rules can require additional capital, restrict activities, or "
        "change the risk-weighting of assets."
    ),
    "deposit outflow": (
        "The bank is experiencing withdrawal of customer deposits. Deposit outflows "
        "reduce the funding base and, if severe, can precipitate a liquidity crisis "
        "or bank run."
    ),
    "credit loss provision": (
        "The bank is setting aside significant reserves for potential loan defaults. "
        "Rising provisions signal deteriorating loan quality and directly reduce "
        "reported earnings."
    ),
    "loan impairment": (
        "Loans on the bank's books have deteriorated in credit quality. Loan "
        "impairments reduce asset values and require additional provisioning "
        "that directly hits reported earnings."
    ),
    "non-performing loan": (
        "A significant portion of the loan portfolio is not generating interest "
        "income due to borrower default. High NPL ratios signal credit quality "
        "problems and potential capital adequacy concerns."
    ),
    "allowance for credit losses": (
        "The reserve set aside to absorb expected loan defaults is increasing. "
        "A rising allowance signals management expects deterioration in loan "
        "quality and reduces reported net income."
    ),
    "bank run": (
        "Large-scale depositor withdrawals are occurring or at risk. A bank run "
        "can quickly exhaust liquidity and precipitate failure even for institutions "
        "that are solvent under normal conditions."
    ),
    "capital adequacy": (
        "The bank may not maintain sufficient capital relative to risk-weighted "
        "assets. Failing capital adequacy tests triggers regulatory intervention "
        "and can restrict dividends and growth."
    ),
    "mortgage default": (
        "Mortgage borrowers are failing to make payments, increasing credit loss "
        "exposure. Rising mortgage defaults signal housing market stress and result "
        "in significant loss provisions."
    ),
    "liquidity coverage ratio": (
        "The ratio of high-quality liquid assets to net cash outflows may be under "
        "pressure. A low LCR signals vulnerability to short-term funding stress and "
        "may attract supervisory attention."
    ),

    # ── Technology pack ───────────────────────────────────────────────────────
    "supply chain": (
        "The company's supply chain is exposed to disruption risk. Technology "
        "supply chains — especially for semiconductors and components — are "
        "vulnerable to geopolitical tensions and single-source dependencies."
    ),
    "semiconductor": (
        "Products rely on semiconductors that may be in short supply or subject "
        "to export controls. Semiconductor shortages can halt production and cause "
        "significant revenue delays."
    ),
    "cloud outage": (
        "Outages at cloud infrastructure providers can halt operations. Cloud "
        "outages are increasingly material as companies depend on third-party "
        "infrastructure for core services."
    ),
    "ip theft": (
        "Intellectual property has been or risks being stolen. IP theft — especially "
        "by foreign state actors — can permanently eliminate competitive advantages "
        "built over years of R&D investment."
    ),
    "chip shortage": (
        "A shortage of semiconductor chips is constraining production. Chip shortages "
        "extend lead times, increase costs, and prevent the company from meeting "
        "customer demand."
    ),
    "hardware dependency": (
        "Software or services depend on specific hardware configurations. Hardware "
        "dependency limits flexibility, increases supply chain risk, and can be "
        "exploited by component vendors."
    ),
    "open source risk": (
        "The company uses open source software that may contain vulnerabilities or "
        "have unfavorable licensing terms. Risks include security exposure and "
        "unexpected intellectual property obligations."
    ),
    "software vulnerability": (
        "Known or potential security vulnerabilities exist in the company's software "
        "or infrastructure. Vulnerabilities can be exploited by attackers, resulting "
        "in data breaches and regulatory penalties."
    ),
    "api deprecation": (
        "A key API the company depends on or provides is being deprecated. "
        "Deprecations can break integrations, require costly re-engineering, and "
        "damage customer relationships."
    ),
    "platform ban": (
        "The company faces the risk of being banned from a key operating platform. "
        "Platform bans can immediately eliminate a significant revenue channel with "
        "no short-term alternative."
    ),
    "data localization": (
        "Regulations requiring data to be stored in specific countries increase "
        "infrastructure costs and limit operational flexibility. Data localization "
        "can fragment global architectures significantly."
    ),
    "ai regulation": (
        "Emerging regulations governing artificial intelligence may restrict or "
        "require changes to the company's AI-powered products. AI regulation is "
        "rapidly evolving and creates significant compliance uncertainty."
    ),
    "model bias": (
        "The company's AI or algorithmic models may produce biased outputs. Model "
        "bias creates regulatory, legal, and reputational risks, particularly in "
        "high-stakes applications such as credit or hiring."
    ),

    # ── Healthcare pack ───────────────────────────────────────────────────────
    "clinical trial": (
        "The company's pipeline depends on clinical trial outcomes. Trial failures "
        "can immediately eliminate a product's commercial potential and erase "
        "significant R&D investment."
    ),
    "patent expiry": (
        "Key patents protecting the company's products are expiring. Expiry opens "
        "the door to generic or biosimilar competition, which can rapidly erode "
        "revenue and margins."
    ),
    "drug recall": (
        "The company recalled a drug due to safety or quality concerns. Drug recalls "
        "generate direct costs, FDA scrutiny, product liability claims, and lasting "
        "reputational damage."
    ),
    "liability": (
        "The company faces potential legal or financial obligations arising from its "
        "products or services. Healthcare liability exposure is particularly severe "
        "given patient harm risks and regulatory requirements."
    ),
    "reimbursement": (
        "Revenue depends on third-party reimbursement decisions by insurers or "
        "government programs. Reimbursement cuts or denials can materially reduce "
        "product revenues."
    ),
    "biosimilar competition": (
        "Lower-cost biosimilar versions of the company's biologics are entering "
        "the market. Biosimilar competition can rapidly erode pricing power and "
        "market share for biologic drugs."
    ),
    "off-label use": (
        "The company's products are being used for indications not approved by the "
        "FDA. Off-label promotion is illegal and can result in large Department of "
        "Justice settlements."
    ),
    "adverse event": (
        "Negative health outcomes associated with the company's products have been "
        "reported. Accumulation of adverse events can trigger regulatory review, "
        "label changes, or product withdrawal."
    ),
    "post-market surveillance": (
        "The company is subject to ongoing post-approval safety monitoring. "
        "Post-market surveillance can uncover new safety signals that trigger "
        "label changes, restrictions, or recalls."
    ),
    "medicare reimbursement": (
        "Changes to Medicare reimbursement rates can materially affect revenues. "
        "Government program reimbursement is subject to annual review and can be "
        "cut without significant notice."
    ),
    "formulary exclusion": (
        "The company's products were removed from key payer formularies. Exclusions "
        "can rapidly reduce prescription volumes and require costly rebating to "
        "regain preferred status."
    ),
    "generic competition": (
        "Generic drug competition has entered or will soon enter key markets. "
        "Generic entry typically causes rapid and severe revenue erosion in the "
        "affected product lines."
    ),
    "regulatory hold": (
        "A regulator has placed a hold on a clinical trial or product approval. "
        "Clinical holds delay product launches, increase development costs, and "
        "signal potential safety concerns with the company's pipeline."
    ),

    # ── Energy pack ───────────────────────────────────────────────────────────
    "oil spill": (
        "The company experienced or risks an oil spill. Oil spills create enormous "
        "environmental cleanup costs, regulatory fines, and lasting reputational "
        "damage with investors and communities."
    ),
    "carbon tax": (
        "The company faces financial exposure from carbon pricing mechanisms. "
        "Carbon taxes increase operating costs for high-emission businesses and "
        "may accelerate stranded asset risk."
    ),
    "stranded asset": (
        "Assets the company holds may lose value prematurely due to the energy "
        "transition. Stranded assets require large impairments and signal potential "
        "business model obsolescence."
    ),
    "pipeline": (
        "Pipeline infrastructure faces regulatory, safety, or operational risk. "
        "Incidents create environmental liability, regulatory scrutiny, and "
        "significant remediation costs."
    ),
    "refinery": (
        "Refinery operations face environmental, regulatory, or safety risks. "
        "Outages or violations create operational disruptions, fines, and "
        "potential shutdown risk."
    ),
    "commodity price": (
        "Revenues or costs are significantly exposed to commodity price fluctuations. "
        "Volatile commodity prices can produce large swings in profitability with "
        "limited short-term mitigation."
    ),
    "reserve depletion": (
        "Natural resource reserves are declining. Depletion reduces long-term "
        "revenue potential and may require costly exploration or acquisition "
        "activities to replenish reserves."
    ),
    "decommissioning liability": (
        "The company faces legally required decommissioning costs for assets at "
        "end of life. These liabilities are often large, uncertain in timing, and "
        "difficult to fully fund in advance."
    ),
    "flaring violation": (
        "The company violated rules governing the burning of associated gas. "
        "Flaring violations attract regulatory fines and environmental scrutiny "
        "and signal operational compliance process weaknesses."
    ),
    "methane regulation": (
        "Tightening regulations on methane emissions affect operating costs and "
        "processes. Compliance can require significant capital investment and "
        "operational changes."
    ),
    "energy transition risk": (
        "The shift toward renewable energy threatens the company's core business. "
        "Energy transition risk encompasses stranded assets, regulatory changes, "
        "and declining demand for fossil fuel products."
    ),
    "renewable mandate": (
        "Government mandates requiring renewable energy sourcing or production "
        "affect the company's cost structure or competitive position. Mandates "
        "can accelerate or reshape investment priorities."
    ),
    "drilling moratorium": (
        "A government restriction on drilling activities limits the company's "
        "ability to develop new reserves. Moratoriums directly reduce future "
        "production capacity and long-term revenue potential."
    ),
    "lng market": (
        "Volatility or structural shifts in the global LNG market affect the "
        "company's revenues and project economics. LNG markets are subject to "
        "geopolitical, regulatory, and demand-side disruption."
    ),
    "crude price volatility": (
        "Unpredictable fluctuations in crude oil prices create revenue and earnings "
        "uncertainty. Crude price volatility makes financial planning difficult "
        "and can rapidly shift project economics."
    ),

    # ── Real Estate pack ──────────────────────────────────────────────────────
    "cap rate": (
        "Movements in capitalization rates can materially affect property "
        "valuations. Rising cap rates compress asset values and reduce the equity "
        "cushion available to support debt."
    ),
    "vacancy rate": (
        "A high or rising vacancy rate reduces rental income and signals weakening "
        "demand. High vacancies can trigger loan covenant breaches and impair the "
        "company's ability to service debt."
    ),
    "noi": (
        "Declining net operating income from properties reduces debt service "
        "coverage and property valuations. NOI pressure can trigger lender concerns "
        "and restrict the company's refinancing options."
    ),
    "ffo": (
        "Funds from operations — the primary REIT profitability measure — is under "
        "pressure. Declining FFO reduces the ability to pay dividends and signals "
        "weakening property-level performance."
    ),
    "reit": (
        "The company's REIT status carries specific regulatory requirements around "
        "income, assets, and distributions. Failure to maintain REIT status would "
        "create significant and immediate tax consequences."
    ),
    "lease expiration": (
        "A significant portion of leases expire in the near term, creating "
        "re-leasing risk. Lease expirations can result in vacancy, lower rents "
        "on renewal, or loss of key tenants."
    ),
    "tenant concentration": (
        "A small number of tenants account for a large share of rental income. "
        "The departure or default of one key tenant can materially impair the "
        "company's revenue."
    ),
    "refinancing risk": (
        "The company has near-term debt maturities that require refinancing in "
        "potentially adverse market conditions. Refinancing risk is highest when "
        "properties are underperforming or markets are stressed."
    ),

    # ── Consulting pack ───────────────────────────────────────────────────────
    "utilization rate": (
        "A declining percentage of billable consultant hours signals revenue "
        "pressure. Low utilization rates directly reduce revenue per headcount "
        "and compress consulting firm profitability."
    ),
    "billable hours": (
        "Declining billable hours signal weakening client demand or engagement "
        "volume. For consulting firms, billable hours are the primary revenue "
        "driver and a leading indicator of financial performance."
    ),
    "client concentration": (
        "Revenue is heavily dependent on a small number of clients. The loss of "
        "a single key engagement can materially impair the firm's revenue and "
        "profitability."
    ),
    "contract renewal": (
        "Key client contracts are at risk of non-renewal. Failure to renew "
        "significant engagements creates sudden revenue gaps that are difficult "
        "to replace quickly with new business."
    ),
    "engagement termination": (
        "A client terminated or may terminate a consulting engagement before "
        "scheduled completion. Early terminations reduce revenue, create stranded "
        "staffing costs, and may signal client dissatisfaction."
    ),
    "key partner departure": (
        "Senior partners or key rainmakers have left or may leave the firm. "
        "Partner departures can take client relationships with them, creating "
        "immediate and hard-to-replace revenue losses."
    ),
}


def _deduplicate_keywords(risk_results):
    """Return list of dicts (keyword, section, category) — one entry per unique keyword."""
    seen = {}
    for finding in risk_results.get("findings", []):
        kw_lower = finding["keyword"].lower()
        if kw_lower not in seen:
            seen[kw_lower] = {
                "keyword": finding["keyword"],
                "section": finding["section"],
                "category": finding["category"],
            }
    return list(seen.values())


def generate_glossary_pdf(risk_results, ticker, output_dir=OUTPUT_DIR):
    """
    Build <ticker>_glossary.pdf from triggered keywords in risk_results.
    Returns output path, or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{ticker}_glossary.pdf")

    entries = _deduplicate_keywords(risk_results)
    if not entries:
        print("[RedFlag] Glossary: no triggered keywords — skipping.")
        return None

    # Group by category
    grouped = {}
    for e in entries:
        grouped.setdefault(e["category"], []).append(e)

    NAVY = (26, 26, 46)
    LIGHT = 245

    def _s(text):
        return str(text).encode("latin-1", "replace").decode("latin-1")

    try:
        pdf = FPDF()
        pdf.set_margins(14, 14, 14)
        pdf.set_auto_page_break(auto=True, margin=16)

        # ── Cover ──────────────────────────────────────────────────────────
        pdf.add_page()
        pdf.set_fill_color(*NAVY)
        pdf.rect(0, 0, 210, 52, "F")

        pdf.set_xy(14, 10)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, _s(f"RedFlag Glossary  —  {ticker}"), ln=True)

        pdf.set_xy(14, 24)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(0, 7, "Triggered Risk Keywords  |  Plain-English Explanations", ln=True)

        pdf.set_xy(14, 34)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(160, 160, 160)
        n_cats = len(grouped)
        pdf.cell(
            0, 7,
            _s(f"Generated: {datetime.now().strftime('%Y-%m-%d')}   |   "
               f"{len(entries)} unique keyword(s)   |   "
               f"{n_cats} categor{'y' if n_cats == 1 else 'ies'}"),
            ln=True,
        )

        pdf.set_text_color(30, 30, 30)
        pdf.set_xy(14, 60)

        # Summary table
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(LIGHT, LIGHT, LIGHT)
        pdf.cell(182, 8, "  Summary — Keywords Triggered by Category", ln=True, fill=True)

        pdf.set_font("Helvetica", "", 9)
        for cat in _CATEGORY_ORDER:
            if cat not in grouped:
                continue
            r, g, b = _CAT_COLORS.get(cat, _DEFAULT_COLOR)
            pdf.set_x(14)
            pdf.set_text_color(r, g, b)
            pdf.cell(65, 6, _s(f"  {cat}"), ln=False)
            pdf.set_text_color(30, 30, 30)
            n = len(grouped[cat])
            pdf.cell(0, 6, _s(f"{n} keyword{'s' if n != 1 else ''} triggered"), ln=True)

        pdf.set_text_color(30, 30, 30)
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(
            182, 5,
            "Each entry shows the keyword as it appeared in the filing, the section "
            "where it first triggered, and a plain-English explanation of the risk it "
            "represents. Explanations are pre-written and are not tailored to this "
            "specific company.",
        )
        pdf.set_text_color(30, 30, 30)

        # ── One page per category ──────────────────────────────────────────
        for cat in _CATEGORY_ORDER:
            if cat not in grouped:
                continue

            r, g, b = _CAT_COLORS.get(cat, _DEFAULT_COLOR)
            cat_entries = sorted(grouped[cat], key=lambda e: e["keyword"].lower())

            pdf.add_page()

            # Category header band
            pdf.set_fill_color(r, g, b)
            pdf.rect(0, 0, 210, 14, "F")
            pdf.set_xy(14, 2)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 10, _s(f"{cat} Risk Keywords"), ln=True)
            pdf.set_text_color(30, 30, 30)
            pdf.ln(5)

            for entry in cat_entries:
                kw = entry["keyword"]
                section = entry["section"]
                explanation = GLOSSARY_EXPLANATIONS.get(
                    kw.lower(),
                    (
                        "This keyword indicates a potential risk area identified in the "
                        "filing that warrants further review in due diligence."
                    ),
                )

                # Keyword header row
                pdf.set_x(14)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_fill_color(r, g, b)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(182, 7, _s(f"  {kw}"), ln=True, fill=True)

                # First-seen section row
                pdf.set_x(14)
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(90, 90, 90)
                pdf.set_fill_color(LIGHT, LIGHT, LIGHT)
                pdf.cell(182, 5, _s(f"  First seen in: {section}"), ln=True, fill=True)

                # Explanation body
                pdf.set_x(14)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(30, 30, 30)
                pdf.set_fill_color(255, 255, 255)
                pdf.multi_cell(182, 5, _s(explanation))
                pdf.ln(3)

        # ── Methodology page ───────────────────────────────────────────────
        pdf.add_page()
        pdf.set_fill_color(*NAVY)
        pdf.rect(0, 0, 210, 14, "F")
        pdf.set_xy(14, 2)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "Methodology & Disclaimer", ln=True)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(6)

        sections_text = [
            (
                "How keywords are selected",
                "RedFlag scans filings against a library of 220+ risk keywords across "
                "6 core categories (Legal, Regulatory, Financial, Operational, Governance, "
                "Forward-Looking) plus sector-specific packs. Only keywords that appear "
                "in the filing text are included in this glossary."
            ),
            (
                "How the first section is determined",
                "The 'first seen' section reflects the earliest section of the filing "
                "in which the keyword was detected. The same keyword may appear multiple "
                "times across sections; only the first occurrence is shown."
            ),
            (
                "About the explanations",
                "All explanations are pre-written for educational purposes. They describe "
                "the general risk associated with each keyword and are not tailored to "
                "this specific company's circumstances. A keyword triggering does not mean "
                "the company is in distress — context and severity scoring should guide "
                "further due diligence."
            ),
            (
                "Disclaimer",
                "This glossary is produced by the RedFlag automated analysis platform for "
                "informational and due diligence purposes only. It does not constitute "
                "financial, legal, or investment advice.  |  github.com/zshqv/RedFlag"
            ),
        ]
        for heading, body in sections_text:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 7, heading, ln=True)
            pdf.set_font("Helvetica", "" if heading != "Disclaimer" else "I", 9)
            pdf.set_text_color(30, 30, 30 if heading != "Disclaimer" else 100)
            pdf.multi_cell(182, 5, _s(body))
            pdf.ln(3)

        pdf.output(filepath)
        print(f"[RedFlag] Glossary PDF saved: {filepath}")
        return filepath

    except Exception as e:
        print(f"[RedFlag] Glossary PDF generation failed: {e}")
        return None
