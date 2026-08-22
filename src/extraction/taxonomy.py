import re
from typing import Dict, List, Optional

# Standard Chart of Accounts (COA) taxonomy synonym dictionary
TAXONOMY_MAP: Dict[str, List[str]] = {
    # ================= BALANCE SHEET =================
    # Current Assets
    "CashAndCashEquivalents": [
        "cash and cash equivalents", "cash & cash equivalents", "cash and bank balances",
        "cash", "cash at bank", "balances with banks"
    ],
    "MarketableSecurities": [
        "marketable securities", "short-term investments", "current investments",
        "temporary investments", "liquid funds"
    ],
    "AccountsReceivable": [
        "accounts receivable", "trade receivables", "trade debtors", "sundry debtors",
        "accounts receivable, net", "receivables", "notes receivable"
    ],
    "AllowanceForDoubtfulAccounts": [
        "allowance for doubtful accounts", "allowance for credit losses",
        "provision for bad debts", "provision for doubtful debts", "expected credit loss allowance"
    ],
    "Inventories": [
        "inventories", "inventory", "stock in trade", "finished goods",
        "work in progress", "raw materials", "inventories at cost"
    ],
    "PrepaidExpenses": [
        "prepaid expenses", "prepayments", "other current assets", "short-term advances",
        "advances to suppliers", "other receivables"
    ],
    "TotalCurrentAssets": [
        "total current assets", "total current assets subtotal", "current assets"
    ],

    # Non-Current Assets
    "PropertyPlantAndEquipmentNet": [
        "property, plant and equipment", "property, plant and equipment, net",
        "property plant and equipment (net)", "property plant and equipment", "fixed assets",
        "tangible assets", "property, plant and equipment (net of accumulated depreciation)",
        "ppe, net", "ppe"
    ],
    "AccumulatedDepreciation": [
        "accumulated depreciation", "accumulated depreciation and amortization",
        "less: accumulated depreciation"
    ],
    "Goodwill": [
        "goodwill", "goodwill on consolidation"
    ],
    "IntangibleAssets": [
        "intangible assets", "intangible assets, net", "other intangible assets",
        "patents and trademarks", "software capitalised"
    ],
    "LongTermInvestments": [
        "long-term investments", "non-current investments", "financial assets at amortized cost",
        "investments in subsidiaries", "investments in associates"
    ],
    "TotalNonCurrentAssets": [
        "total non-current assets", "total noncurrent assets", "non-current assets"
    ],
    "TotalAssets": [
        "total assets", "total asset"
    ],

    # Current Liabilities
    "AccountsPayable": [
        "accounts payable", "trade payables", "trade creditors", "sundry creditors",
        "bills payable", "trade and other payables"
    ],
    "ShortTermDebt": [
        "short-term debt", "short term borrowings", "current portion of long-term debt",
        "current maturities of long-term debt", "short term loans", "bank overdraft"
    ],
    "AccruedLiabilities": [
        "accrued liabilities", "accrued expenses", "other current liabilities",
        "provisions (current)", "current provisions", "statutory dues payable"
    ],
    "TotalCurrentLiabilities": [
        "total current liabilities", "current liabilities"
    ],

    # Non-Current Liabilities
    "LongTermDebt": [
        "long-term debt", "long term borrowings", "non-current borrowings",
        "senior notes", "term loans", "bonds payable", "debentures"
    ],
    "DeferredTaxLiabilities": [
        "deferred tax liabilities", "deferred tax liabilities (net)", "non-current tax liabilities"
    ],
    "TotalNonCurrentLiabilities": [
        "total non-current liabilities", "total noncurrent liabilities", "non-current liabilities",
        "long-term liabilities", "total long-term liabilities"
    ],
    "TotalLiabilities": [
        "total liabilities"
    ],

    # Stockholders' Equity
    "CommonStock": [
        "common stock", "share capital", "equity share capital", "issued capital",
        "common shares", "ordinary share capital"
    ],
    "AdditionalPaidInCapital": [
        "additional paid-in capital", "additional paid in capital", "capital reserve",
        "securities premium", "share premium", "apic"
    ],
    "RetainedEarnings": [
        "retained earnings", "accumulated earnings", "surplus in statement of profit and loss",
        "ending retained earnings", "retained profits"
    ],
    "AccumulatedOtherComprehensiveIncome": [
        "accumulated other comprehensive income", "aoci", "accumulated other comprehensive loss",
        "other reserves"
    ],
    "TotalStockholdersEquity": [
        "total stockholders' equity", "total stockholders equity", "total shareholders' equity",
        "total shareholders equity", "total equity", "shareholders' funds", "total members' equity"
    ],
    "TotalLiabilitiesAndEquity": [
        "total liabilities and equity", "total liabilities & equity",
        "total liabilities and stockholders' equity", "total liabilities & stockholders' equity",
        "total equity and liabilities", "total liabilities and shareholders' equity"
    ],

    # ================= INCOME STATEMENT =================
    "Revenue": [
        "revenue", "revenues", "revenue from operations", "sales", "net sales",
        "total revenue", "turnover", "operating revenue", "gross sales"
    ],
    "CostOfGoodsSold": [
        "cost of goods sold", "cost of goods sold (cogs)", "cogs", "cost of sales",
        "cost of revenue", "cost of materials consumed", "purchase of stock-in-trade"
    ],
    "GrossProfit": [
        "gross profit", "gross profit / (loss)", "gross margin"
    ],
    "SellingGeneralAndAdministrative": [
        "selling, general and administrative", "selling general and administrative",
        "sg&a", "sga", "selling and distribution expenses", "administrative expenses",
        "general and administrative expenses", "selling, general and administrative expenses"
    ],
    "ResearchAndDevelopment": [
        "research and development", "research and development (r&d)", "r&d", "research & development"
    ],
    "DepreciationAndAmortizationExpense": [
        "depreciation and amortization", "depreciation & amortization", "depreciation expense",
        "amortization expense", "depreciation and amortisation expense"
    ],
    "TotalOperatingExpenses": [
        "total operating expenses", "operating expenses", "total opex"
    ],
    "OperatingIncome": [
        "operating income", "operating profit", "operating income (ebit)", "ebit",
        "operating profit / (loss)", "profit from operations"
    ],
    "InterestExpense": [
        "interest expense", "finance costs", "interest cost", "finance cost",
        "borrowing costs"
    ],
    "InterestIncome": [
        "interest income", "finance income", "other income", "investment income"
    ],
    "EarningsBeforeTax": [
        "earnings before tax", "earnings before taxes (ebt)", "ebt", "profit before tax",
        "profit before taxation", "income before income taxes", "profit before income tax"
    ],
    "IncomeTaxExpense": [
        "income tax expense", "tax expense", "provision for income taxes", "income taxes",
        "current tax", "deferred tax charge / (credit)"
    ],
    "NetIncome": [
        "net income", "net profit", "net profit / (loss)", "net earnings",
        "profit for the year", "profit / (loss) for the period", "profit for the period",
        "net income (loss)"
    ],

    # ================= CASH FLOW STATEMENT =================
    "OperatingCashFlow": [
        "operating cash flow", "net cash provided by operating activities",
        "net cash from operating activities", "cash generated from operations",
        "net cash flow from operating activities", "operating activities"
    ],
    "DepreciationAmortizationAddback": [
        "depreciation & amortization add-back", "depreciation and amortization add-back",
        "depreciation and amortization", "depreciation & amortization"
    ],
    "WorkingCapitalChanges": [
        "working capital changes", "changes in working capital", "net change in working capital",
        "adjustments for working capital changes"
    ],
    "CapitalExpenditures": [
        "capital expenditures", "capex", "purchase of property, plant and equipment",
        "payments for property, plant and equipment", "additions to fixed assets"
    ],
    "InvestingCashFlow": [
        "investing cash flow", "net cash used in investing activities",
        "net cash provided by (used in) investing activities", "net cash from investing activities",
        "investing activities"
    ],
    "DebtBorrowingsRepayments": [
        "debt borrowings / (repayments)", "debt repayments", "proceeds from debt",
        "repayment of borrowings", "proceeds from borrowings", "net debt borrowings"
    ],
    "DividendsPaid": [
        "dividends paid", "payment of dividends", "dividends distributed"
    ],
    "FinancingCashFlow": [
        "financing cash flow", "net cash used in financing activities",
        "net cash provided by (used in) financing activities", "net cash from financing activities",
        "financing activities"
    ],
    "NetCashChange": [
        "net cash change", "net increase in cash and cash equivalents",
        "net decrease in cash and cash equivalents", "net change in cash",
        "net increase / (decrease) in cash and cash equivalents"
    ],
    "BeginningCash": [
        "beginning cash", "cash and cash equivalents at beginning of period",
        "cash and cash equivalents at start of year", "opening cash and cash equivalents",
        "opening cash"
    ],
    "EndingCash": [
        "ending cash", "cash and cash equivalents at end of period",
        "cash and cash equivalents at end of year", "closing cash and cash equivalents",
        "closing cash"
    ],

    # ================= SOCE =================
    "BeginningRetainedEarnings": [
        "beginning retained earnings", "retained earnings at beginning of period",
        "opening retained earnings", "balance at beginning of year"
    ],
    "DividendsDeclared": [
        "dividends declared", "dividends declared and paid", "dividends paid", "dividends"
    ],
    "EndingRetainedEarnings": [
        "ending retained earnings", "retained earnings at end of period",
        "closing retained earnings", "balance at end of year"
    ]
}


def normalize_line_item_key(raw_description: str) -> str:
    """
    Cleans raw line item text and matches it against standard taxonomy synonyms.
    Returns canonical key (e.g. 'Revenue') or sanitized raw description if unmapped.
    """
    desc_clean = str(raw_description).lower().strip()
    
    # Strip leading line numbers: '1. Net Sales' -> 'Net Sales', 'A. Revenue' -> 'Revenue'
    desc_clean = re.sub(r"^[0-9a-zA-Z]{1,3}[\.\)\-]\s*", "", desc_clean).strip()
    # Strip footnote references: 'Inventories [1]' -> 'Inventories'
    desc_clean = re.sub(r"\[.*?\]|\(.*?\)", "", desc_clean).strip()

    for canonical_key, synonyms in TAXONOMY_MAP.items():
        for syn in synonyms:
            if syn == desc_clean or desc_clean.startswith(syn):
                return canonical_key

    # Secondary fuzzy pass: Substring search for high-confidence terms
    for canonical_key, synonyms in TAXONOMY_MAP.items():
        for syn in synonyms:
            if len(syn) > 5 and syn in desc_clean:
                return canonical_key

    # Fallback to sanitized PascalCase string of original description
    fallback_key = re.sub(r"[^a-zA-Z0-9]", "", raw_description.title())
    return fallback_key if fallback_key else "UnmappedLineItem"