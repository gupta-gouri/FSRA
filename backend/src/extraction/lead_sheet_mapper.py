import re
from typing import Tuple

# Standard Audit Lead Sheet Taxonomy (Big 4 / GAAP Standard)
LEAD_SHEET_TAXONOMY = {
    # ================= BALANCE SHEET ASSETS (1000-1999) =================
    "A": {"name": "Cash and Cash Equivalents", "fs": "BALANCE_SHEET", "keywords": ["cash", "bank", "checking", "savings", "petty cash", "money market"]},
    "B": {"name": "Marketable Securities & Investments", "fs": "BALANCE_SHEET", "keywords": ["marketable securities", "short-term investment", "treasury bill", "liquid fund"]},
    "C": {"name": "Accounts Receivable", "fs": "BALANCE_SHEET", "keywords": ["accounts receivable", "trade receivable", "trade debtor", "customer receivable", "unbilled revenue"]},
    "C-1": {"name": "Allowance for Doubtful Accounts", "fs": "BALANCE_SHEET", "keywords": ["allowance for doubtful", "allowance for credit", "bad debt provision"]},
    "D": {"name": "Inventories", "fs": "BALANCE_SHEET", "keywords": ["inventory", "raw material", "work in progress", "finished goods", "stock in trade"]},
    "E": {"name": "Prepaid Expenses & Other Current Assets", "fs": "BALANCE_SHEET", "keywords": ["prepaid", "advance to supplier", "security deposit", "other current asset"]},
    "F": {"name": "Property, Plant & Equipment", "fs": "BALANCE_SHEET", "keywords": ["ppe", "fixed asset", "building", "machinery", "equipment", "vehicle", "furniture", "land"]},
    "F-1": {"name": "Accumulated Depreciation", "fs": "BALANCE_SHEET", "keywords": ["accumulated depreciation", "accum depr", "allowance for depreciation"]},
    "G": {"name": "Intangible Assets & Goodwill", "fs": "BALANCE_SHEET", "keywords": ["goodwill", "patent", "trademark", "software", "license", "intangible"]},
    
    # ================= BALANCE SHEET LIABILITIES (2000-2999) =================
    "AA": {"name": "Accounts Payable", "fs": "BALANCE_SHEET", "keywords": ["accounts payable", "trade payable", "trade creditor", "vendor payable", "bills payable"]},
    "BB": {"name": "Short-Term Debt & Current Borrowings", "fs": "BALANCE_SHEET", "keywords": ["short-term debt", "line of credit", "current portion of lt debt", "bank overdraft", "short term loan"]},
    "CC": {"name": "Accrued Expenses & Other Current Liabilities", "fs": "BALANCE_SHEET", "keywords": ["accrued", "payroll payable", "taxes payable", "statutory liability", "accrued interest"]},
    "DD": {"name": "Long-Term Debt", "fs": "BALANCE_SHEET", "keywords": ["long-term debt", "senior note", "term loan", "bond payable", "debenture", "mortgage"]},
    "EE": {"name": "Deferred Taxes & Non-Current Liabilities", "fs": "BALANCE_SHEET", "keywords": ["deferred tax liability", "deferred revenue non-current", "other long-term liability"]},

    # ================= EQUITY (3000-3999) =================
    "KK": {"name": "Common Stock & Contributed Capital", "fs": "BALANCE_SHEET", "keywords": ["common stock", "share capital", "equity capital", "apic", "additional paid-in", "securities premium"]},
    "LL": {"name": "Retained Earnings & Reserves", "fs": "BALANCE_SHEET", "keywords": ["retained earnings", "accumulated surplus", "general reserve", "opening balance", "dividends declared"]},

    # ================= INCOME STATEMENT REVENUE (4000-4999) =================
    "10": {"name": "Revenue from Operations", "fs": "INCOME_STATEMENT", "keywords": ["revenue", "sales", "turnover", "fee income", "service income", "gross receipts"]},
    "15": {"name": "Other Income", "fs": "INCOME_STATEMENT", "keywords": ["interest income", "dividend income", "gain on disposal", "miscellaneous income", "foreign exchange gain"]},

    # ================= INCOME STATEMENT EXPENSES (5000-6999) =================
    "20": {"name": "Cost of Goods Sold", "fs": "INCOME_STATEMENT", "keywords": ["cogs", "cost of goods sold", "cost of sales", "direct material", "direct labor", "freight in"]},
    "30": {"name": "Selling, General & Administrative", "fs": "INCOME_STATEMENT", "keywords": ["salary", "wage", "rent", "utilities", "marketing", "advertising", "travel", "legal", "audit fee", "sga", "sg&a"]},
    "40": {"name": "Research & Development", "fs": "INCOME_STATEMENT", "keywords": ["r&d", "research", "development cost", "testing"]},
    "50": {"name": "Depreciation & Amortization", "fs": "INCOME_STATEMENT", "keywords": ["depreciation expense", "amortization expense", "depr & amort"]},
    "60": {"name": "Interest Expense & Finance Costs", "fs": "INCOME_STATEMENT", "keywords": ["interest expense", "bank charges", "finance charge", "loan fees"]},
    "70": {"name": "Income Tax Expense", "fs": "INCOME_STATEMENT", "keywords": ["income tax provision", "tax expense", "current tax", "deferred tax expense"]}
}

def map_account_to_lead_sheet(account_name: str, account_number: str="") -> Tuple[str, str, str]:
    """
    Classifies a GL account into an Audit Lead Sheet code, name and FS target.
    Returns: (lead_code, lead_name, fs_target)
    """
    clean_name = str(account_name).lower().strip()
    clean_num = str(account_number).strip()

    # Pass 1: Account number prefix heuristic (if 4-digit GL coding is present)
    if clean_num and clean_num[:1].isdigit():
        prefix = clean_num[0]
        if prefix == "1" and any(k in clean_name for k in ["cash", "bank"]):
            return "A", LEAD_SHEET_TAXONOMY["A"]["name"], "BALANCE_SHEET"
        elif prefix == "1" and any(k in clean_name for k in ["receivable", "debtor"]):
            return "C", LEAD_SHEET_TAXONOMY["C"]["name"], "BALANCE_SHEET"
        elif prefix == "1" and any(k in clean_name for k in ["inventory", "stock"]):
            return "D", LEAD_SHEET_TAXONOMY["D"]["name"], "BALANCE_SHEET"
        elif prefix == "1" and any(k in clean_name for k in ["fixed", "equipment", "asset", "building"]):
            return "F", LEAD_SHEET_TAXONOMY["F"]["name"], "BALANCE_SHEET"
        elif prefix == "2" and any(k in clean_name for k in ["payable", "vendor", "creditor"]):
            return "AA", LEAD_SHEET_TAXONOMY["AA"]["name"], "BALANCE_SHEET"
        elif prefix == "2" and any(k in clean_name for k in ["debt", "loan", "borrowing", "note"]):
            return "DD", LEAD_SHEET_TAXONOMY["DD"]["name"], "BALANCE_SHEET"
        elif prefix == "3":
            return "KK", LEAD_SHEET_TAXONOMY["KK"]["name"], "BALANCE_SHEET"
        elif prefix == "4":
            return "10", LEAD_SHEET_TAXONOMY["10"]["name"], "INCOME_STATEMENT"
        elif prefix == "5":
            return "20", LEAD_SHEET_TAXONOMY["20"]["name"], "INCOME_STATEMENT"
        elif prefix == "6":
            return "30", LEAD_SHEET_TAXONOMY["30"]["name"], "INCOME_STATEMENT"

    # Pass 2: Keyword Taxonomy Mapping
    for code, info in LEAD_SHEET_TAXONOMY.items():
        if any(kw in clean_name for kw in info["keywords"]):
            return code, info["name"], info["fs"]

    # Fallback for unclassified accounts
    return "OTH", "Other Miscellaneous Accounts", "BALANCE_SHEET"