import re
from typing import Any, List, Optional, Union
from backend.src.schemas.manifest import StatementType, DocumentMetadata, RawSheetPayload

# 1. Keyword mappings for sheet name / TOC title classification
NAME_KEYWORDS = {
    StatementType.BALANCE_SHEET: [
        "balance sheet", "statement of financial position", "sofp", "bs", 
        "position statement", "financial position", "consolidated balance sheet",
        "condensed balance sheet", "b_s", "b.s"
    ],
    StatementType.INCOME_STATEMENT: [
        "income statement", "statement of operations", "profit and loss", 
        "profit & loss", "p&l", "pnl", "statement of earnings", 
        "statement of comprehensive income", "income stmt", "operating statement",
        "statement of revenue and expenses", "is", "i_s", "i.s"
    ],
    StatementType.CASH_FLOW_STATEMENT: [
        "cash flow", "statement of cash flows", "cfs", "cash flows", 
        "cashflow", "flow of funds", "statement of cash flow", "cf_stmt", "c.f.s"
    ],
    StatementType.SOCE: [
        "stockholders equity", "shareholders equity", "soce", "statement of equity", 
        "changes in equity", "statement of changes in equity", "retained earnings", 
        "equity statement", "owners equity", "shareholder's fund", "shareholders funds"
    ],
    StatementType.TRIAL_BALANCE: [
        "trial balance", "tb", "general ledger", "gl trial balance", 
        "adjusted trial balance", "pre-closing tb", "post-closing tb", "working tb"
    ],
    StatementType.AR_AGING: [
        "ar aging", "aging schedule", "accounts receivable aging", "trade receivables aging", 
        "debtor aging", "receivables aging", "ar age analysis", "aged receivables"
    ],
    StatementType.PPE_SCHEDULE: [
        "ppe", "property plant", "fixed assets", "depreciation schedule", 
        "tangible assets", "asset rollforward", "fixed asset register", "fa schedule", "ppe rollforward"
    ],
    StatementType.DEBT_MATURITY: [
        "debt maturity", "debt schedule", "maturities of debt", "borrowings", 
        "borrowing schedule", "loan maturity", "debt amortization", "long-term debt schedule"
    ]
}

# 2. High-signal content keywords for page body scanning
CONTENT_SIGNATURES = {
    StatementType.BALANCE_SHEET: [
        "total assets", "total liabilities", "current assets", "non-current assets",
        "current liabilities", "non-current liabilities", "stockholders' equity", 
        "shareholders' equity", "total equity", "retained earnings", "accounts receivable", 
        "trade payables", "inventories", "property, plant and equipment", "intangible assets",
        "cash and cash equivalents", "share capital", "total liabilities and equity"
    ],
    StatementType.INCOME_STATEMENT: [
        "revenue", "revenues", "sales", "turnover", "cost of goods sold", "cogs", 
        "cost of sales", "cost of revenue", "gross profit", "operating income", 
        "operating expenses", "operating profit", "ebitda", "ebit", "selling, general",
        "sga", "sg&a", "research and development", "interest expense", "income tax expense", 
        "tax provision", "pretax income", "earnings before tax", "net income", "net profit", 
        "net earnings", "diluted earnings per share", "basic eps"
    ],
    StatementType.CASH_FLOW_STATEMENT: [
        "operating cash flow", "investing cash flow", "financing cash flow", 
        "operating activities", "investing activities", "financing activities", 
        "net cash provided by", "net cash used in", "cash from operations", 
        "depreciation & amortization", "working capital changes", "net cash change", 
        "beginning cash", "ending cash", "cash and cash equivalents at end of year",
        "capital expenditures", "capex", "dividends paid"
    ],
    StatementType.SOCE: [
        "common stock", "additional paid-in capital", "apic", "retained earnings", 
        "accumulated other comprehensive", "aoci", "treasury stock", "dividends declared", 
        "dividends paid", "share capital", "beginning balance", "ending balance", 
        "balance as of", "stock based compensation", "total stockholders' equity"
    ],
    StatementType.TRIAL_BALANCE: [
        "account number", "account title", "debit", "credit", "ending balance", 
        "net balance", "dr", "cr", "unadjusted balance", "adjusted balance"
    ],
    StatementType.AR_AGING: [
        "current", "0-30", "1-30", "31-60", "30-60", "61-90", "60-90", "91-120", 
        "90+", "120+", "past due", "allowance for credit losses", "allowance for doubtful",
        "total gross receivables", "provision for bad debt"
    ],
    StatementType.PPE_SCHEDULE: [
        "gross carrying amount", "accumulated depreciation", "additions", "disposals", 
        "depreciation expense", "net book value", "nbv", "closing gross carrying amount",
        "impairment", "transfers", "construction in progress", "useful lives"
    ],
    StatementType.DEBT_MATURITY: [
        "year 1", "year 2", "year 3", "year 4", "year 5", "thereafter", 
        "total debt maturities", "scheduled debt", "principal repayments", 
        "senior notes", "term loan", "credit facility", "carrying amount"
    ]
}

# Legal entity suffixes across US, UK, India, and global jurisdictions
CORP_SUFFIX_PATTERN = re.compile(
    r"\b(ltd\.?|limited|inc\.?|incorporated|corp\.?|corporation|llc|llp|plc|pvt\.?\s*ltd\.?|private\s+limited|gmbh|sa|nv|co\.?|company)\b",
    re.IGNORECASE
)

# Reject words to avoid mistaking statement titles or units for entity names
TITLE_EXCLUSIONS = [
    "balance sheet", "income statement", "cash flow", "statement of", "profit and loss",
    "p&l", "equity", "soce", "trial balance", "amounts in", "for the year", "as of",
    "fy20", "fy19", "period ended", "line item", "schedule", "table of contents", "index"
]


def classify_sheet(sheet_payload: RawSheetPayload) -> StatementType:
    """Classifies a worksheet or PDF page into a StatementType."""
    # Retain type if already discovered via PDF TOC
    if sheet_payload.detected_type != StatementType.UNKNOWN:
        return sheet_payload.detected_type

    sheet_name_clean = sheet_payload.sheet_name.lower().strip()

    # 1. Match by sheet tab name
    for stmt_type, keywords in NAME_KEYWORDS.items():
        for kw in keywords:
            if kw in sheet_name_clean:
                return stmt_type

    # 2. Match by combined text (page text + grid text)
    combined_text = (sheet_payload.raw_text or "").lower()
    for row in sheet_payload.raw_grid[:30]:
        row_str = " ".join(str(cell).lower() for cell in row if cell is not None)
        combined_text += " " + row_str

    for stmt_type, signatures in CONTENT_SIGNATURES.items():
        match_count = sum(1 for sig in signatures if sig in combined_text)
        if match_count >= 2:
            return stmt_type

    return StatementType.UNKNOWN


def extract_metadata(source: Union[RawSheetPayload, List[List[Any]]]) -> DocumentMetadata:
    """
    Scans raw_text (PDF) or top grid rows (Excel) for client name, currency, scale, and dates.
    Accepts either a RawSheetPayload or a raw 2D grid.
    """
    metadata = DocumentMetadata()

    if isinstance(source, RawSheetPayload):
        raw_text = source.raw_text or ""
        raw_grid = source.raw_grid
    else:
        raw_text = ""
        raw_grid = source

    # Build header text block and clean header lines
    if raw_text:
        header_text = raw_text[:1200]
        header_lines = [line.strip() for line in raw_text.split("\n")[:10] if line.strip()]
    else:
        header_text = ""
        header_lines = []
        for row in raw_grid[:10]:
            non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
            if non_empty:
                header_lines.append(non_empty[0])
                header_text += "\n" + " ".join(non_empty)

    # 1. Detect Client / Entity Name
    for line in header_lines[:5]:
        if any(ex in line.lower() for ex in TITLE_EXCLUSIONS):
            continue
        if CORP_SUFFIX_PATTERN.search(line):
            metadata.client_name = line
            break

    if not metadata.client_name and header_lines:
        for line in header_lines[:3]:
            if not any(ex in line.lower() for ex in TITLE_EXCLUSIONS) and len(line) > 2:
                metadata.client_name = line
                break

    # 2. Detect Currency (Anywhere in header text)
    if "₹" in header_text or re.search(r"(inr|rupees?|rs\.?)", header_text, re.IGNORECASE):
        metadata.currency = "INR"
    elif "$" in header_text or re.search(r"(usd|dollars?)", header_text, re.IGNORECASE):
        metadata.currency = "USD"
    elif "€" in header_text or re.search(r"(eur|euros?)", header_text, re.IGNORECASE):
        metadata.currency = "EUR"
    elif "£" in header_text or re.search(r"(gbp|pounds?)", header_text, re.IGNORECASE):
        metadata.currency = "GBP"

    # 3. Detect Scale Unit
    if re.search(r"(billions?|in billions?|\bbn\b)", header_text, re.IGNORECASE):
        metadata.scale = "BILLIONS"
    elif re.search(r"(millions?|in millions?|\bmn\b)", header_text, re.IGNORECASE):
        metadata.scale = "MILLIONS"
    elif re.search(r"(thousands?|in thousands?|\bk\b)", header_text, re.IGNORECASE):
        metadata.scale = "THOUSANDS"
    elif re.search(r"(crores?|in crores?|\bcr\b)", header_text, re.IGNORECASE):
        metadata.scale = "CRORES"
    elif re.search(r"(lakhs?|in lakhs?|\blac\b)", header_text, re.IGNORECASE):
        metadata.scale = "LAKHS"

    # 4. Detect Period / Date (Matches anywhere in any format)
    date_patterns = [
        r"(?:(?:\d{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2})",
        r"(?:20\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])|(?:0[1-9]|[12]\d|3[01])[-/](?:0[1-9]|1[0-2])[-/]20\d{2})",
        r"(?:(?:FY\s*)?20\d{2}\s*[-/]\s*(?:20\d{2}|\d{2})|FY\s*\d{2}(?:[-/]\d{2})?)",
        r"(?:20\d{2})"
    ]
    combined_date_regex = re.compile("|".join(f"({p})" for p in date_patterns), re.IGNORECASE)
    match = combined_date_regex.search(header_text)
    if match:
        metadata.period_ended = match.group(0).strip()

    return metadata


# Backward compatibility alias
extract_metadata_from_grid = extract_metadata