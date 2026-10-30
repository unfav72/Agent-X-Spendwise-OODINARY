"""
Spendwise AI - Ingestion Normalizer
Normalizes multi-format transaction statements and large UPI datasets into a unified canonical schema.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

# Standard Spendwise AI Categories
CATEGORIES = [
    "Food and groceries",
    "Food delivery",
    "Shopping",
    "Transport",
    "Fuel",
    "Education",
    "Entertainment",
    "Healthcare",
    "Bills and utilities",
    "Subscriptions",
    "Transfers",
    "Income",
    "Other"
]

MERCHANT_RULES = [
    # Food delivery
    (r"(swiggy|zomato|eats|ubereats|cloudkitchen|faasos|behrouz|box8|domino'?s|mcdonald'?s|burger king|pizza hut|kfc|subway|food)", "Food delivery"),
    # Food and groceries
    (r"(blinkit|zepto|instamart|bigbasket|bbdaily|dmart|nature'?s basket|supermarket|grocer|kirana|star bazaar|more retail|spencer|grocery)", "Food and groceries"),
    # Subscriptions
    (r"(netflix|spotify|hotstar|prime video|youtube premium|apple\.com\/bill|icloud|google one|openai|chatgpt|claude\.ai|github|notion|linkedin premium|canva)", "Subscriptions"),
    # Entertainment
    (r"(bookmyshow|pvr|inox|cinepolis|playstation|steam|xbox|gaming|entertainment)", "Entertainment"),
    # Shopping
    (r"(amazon|flipkart|myntra|ajio|zara|h&m|meesho|nykaa|tata cliq|reliance digital|croma|vijay sales|shoppers stop|lifestyle|shopping)", "Shopping"),
    # Transport
    (r"(uber|ola|rapido|irctc|redbus|makemytrip|goibibo|indigo|air india|vistara|spicejet|metro|chalo|yulu|transport)", "Transport"),
    # Fuel
    (r"(indian oil|ioc|hpcl|bpcl|bharat petro|hindustan petro|shell petrol|petrol pump|fuel|cng|auto gas)", "Fuel"),
    # Bills and utilities
    (r"(bescom|tata power|adani electricity|electricity|water supply|airtel|jio|vi prepaid|vodafone|broadband|act fibernet|tatasky|dish tv|gas bill|mahanagar gas|utilities|bill payment)", "Bills and utilities"),
    # Healthcare
    (r"(apollo|pharmeasy|1mg|tata 1mg|netmeds|medplus|dr\.? lal|pathlabs|max healthcare|fortis|hospital|clinic|pharmacy|diagnostic|health)", "Healthcare"),
    # Education
    (r"(coursera|udemy|edx|unacademy|upgrad|simplilearn|byju'?s|school|college|tuition|university|exam fee|education)", "Education"),
    # Income
    (r"(salary|payroll|stipend|interest credited|dividend|cashback|bonus|incentive)", "Income"),
    # Transfers
    (r"(transfer to|sent to|p2p|neft|rtgs|imps to|fund transfer)", "Transfers"),
]

DATE_PATTERNS = [
    (r"^\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    (r"^\d{2}/\d{2}/\d{4}", "%d/%m/%Y"),
    (r"^\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),
    (r"^\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
    (r"^\d{2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}", "%d %b %Y"),
    (r"^\d{2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}", "%d %B %Y"),
    (r"^\d{2}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}", "%d-%b-%Y"),
    (r"^\d{2}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}", "%d-%b-%y"),
]

def parse_date(date_val: Any) -> Optional[str]:
    """Parse various date/timestamp formats into standard YYYY-MM-DD string."""
    if not date_val:
        return None
    
    if isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")

    s = str(date_val).strip()
    if not s:
        return None

    # Strip time part if present (e.g. '2024-10-08 15:17:28' -> '2024-10-08')
    s_date = s.split("T")[0].split(" ")[0]

    for pattern, fmt in DATE_PATTERNS:
        if re.match(pattern, s_date, re.IGNORECASE):
            try:
                dt = datetime.strptime(s_date, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # Fallback with dateutil
    try:
        from dateutil import parser
        dt = parser.parse(s, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None

def extract_merchant(description: str) -> str:
    """Extract clean merchant name from raw transaction string."""
    clean = description.strip()

    upi_match = re.search(r"UPI[/-]([A-Za-z0-9\s\._&]+?)[/-]", clean, re.IGNORECASE)
    if upi_match:
        m = upi_match.group(1).strip()
        if len(m) > 2 and not m.isdigit():
            return m.title()

    pos_match = re.search(r"(?:POS|ECOM|INF)[/-]?\s*(?:\d+)?\s*([A-Za-z0-9\s\._&]+)", clean, re.IGNORECASE)
    if pos_match:
        m = pos_match.group(1).strip()
        tokens = m.split()
        if tokens:
            return " ".join(tokens[:3]).title()

    for pattern, _ in MERCHANT_RULES:
        m = re.search(pattern, clean, re.IGNORECASE)
        if m:
            return m.group(1).title()

    words = re.findall(r"[A-Za-z0-9]+", clean)
    if words:
        return " ".join(words[:3]).title()

    return "Unknown Merchant"

def categorize_transaction(description: str, merchant: str, debit: float, credit: float, user_corrections: Optional[Dict[str, str]] = None) -> str:
    """Classify transaction into standard categories using rules and user corrections."""
    if user_corrections:
        m_lower = merchant.strip().lower()
        if m_lower in user_corrections:
            return user_corrections[m_lower]
        for key, cat in user_corrections.items():
            if key in m_lower or key in description.lower():
                return cat

    text = f"{merchant} {description}".lower()

    if credit > 0 and debit == 0:
        if any(w in text for w in ["salary", "payroll", "dividend", "interest", "bonus", "stipend"]):
            return "Income"
        if "refund" in text or "reversal" in text or "cashback" in text:
            return "Income"

    for pattern, cat in MERCHANT_RULES:
        if re.search(pattern, text):
            return cat

    if credit > 0:
        return "Income"
    return "Other"

def normalize_row(row_dict: Dict[str, Any], source_file: str = "upload", row_index: int = 0, user_corrections: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    Normalizes a row dictionary from any financial CSV/Excel/PDF into canonical Spendwise schema.
    """
    keys_lower = {k.strip().lower(): v for k, v in row_dict.items() if k is not None}

    # 1. Date extraction (supports timestamp, transaction_date, date, etc.)
    date_val = None
    for k in ["transaction_date", "date", "txn_date", "tx_date", "value_date", "posting_date", "timestamp"]:
        if k in keys_lower and keys_lower[k]:
            date_val = keys_lower[k]
            break
    
    parsed_date = parse_date(date_val)
    if not parsed_date:
        return None

    # 2. Reference ID extraction
    reference_id = None
    for k in ["transaction id", "transaction_id", "reference_id", "ref_no", "reference", "utr", "txn_id", "cheque_no"]:
        if k in keys_lower and keys_lower[k]:
            reference_id = str(keys_lower[k]).strip()
            break

    # 3. Description extraction
    description = ""
    for k in ["description", "narration", "particulars", "remarks", "details", "transaction_details"]:
        if k in keys_lower and keys_lower[k]:
            description = str(keys_lower[k]).strip()
            break

    status_val = str(keys_lower.get("transaction_status", "")).strip().upper()
    type_val = str(keys_lower.get("transaction type", "") or keys_lower.get("type", "")).strip()

    if not description:
        sender_bank = keys_lower.get("sender_bank", "")
        receiver_bank = keys_lower.get("receiver_bank", "")
        m_cat = keys_lower.get("merchant_category", "")
        state = keys_lower.get("sender_state", "")
        
        parts = []
        if status_val == "FAILED":
            parts.append("[FAILED PAYMENT]")
        if type_val:
            parts.append(type_val)
        if m_cat:
            parts.append(f"to {m_cat}")
        if sender_bank and receiver_bank:
            parts.append(f"({sender_bank} -> {receiver_bank})")
        elif receiver_bank:
            parts.append(f"(via {receiver_bank})")
        if state:
            parts.append(f"[{state}]")

        description = " ".join(parts) if parts else "Transaction"

    # 4. Debit & Credit extraction
    debit = 0.0
    credit = 0.0
    has_separate = False

    debit_keys = ["debit", "withdrawal", "dr", "amount_debited", "spent"]
    credit_keys = ["credit", "deposit", "cr", "amount_credited", "received"]

    for k in debit_keys:
        if k in keys_lower and keys_lower[k] not in [None, ""]:
            try:
                debit = float(str(keys_lower[k]).replace(",", "").replace("₹", "").replace("$", "").strip())
                has_separate = True
                break
            except ValueError:
                pass

    for k in credit_keys:
        if k in keys_lower and keys_lower[k] not in [None, ""]:
            try:
                credit = float(str(keys_lower[k]).replace(",", "").replace("₹", "").replace("$", "").strip())
                has_separate = True
                break
            except ValueError:
                pass

    if not has_separate:
        amount_val = None
        # Look for any key containing "amount" (e.g. 'amount (inr)', 'amount', 'net_amount')
        for k, v in keys_lower.items():
            if "amount" in k and v not in [None, ""]:
                amount_val = v
                break

        if amount_val is not None:
            try:
                amt = float(str(amount_val).replace(",", "").replace("₹", "").replace("$", "").strip())
                if amt < 0:
                    debit = abs(amt)
                elif type_val.lower() in ["dr", "debit", "withdrawal", "w"]:
                    debit = amt
                elif type_val.lower() in ["cr", "credit", "deposit", "c"]:
                    credit = amt
                else:
                    # In default UPI/card transactions, default to debit (expense)
                    # unless credit indicators are detected
                    desc_lower = description.lower()
                    if any(w in desc_lower for w in ["salary", "credit", "refund", "reversal"]):
                        credit = amt
                    else:
                        debit = amt
            except ValueError:
                return None

    if debit == 0.0 and credit == 0.0:
        return None

    # 5. Merchant extraction
    merchant = ""
    for k in ["merchant", "payee", "beneficiary", "vendor"]:
        if k in keys_lower and keys_lower[k]:
            merchant = str(keys_lower[k]).strip()
            break

    if not merchant and "merchant_category" in keys_lower:
        m_cat = str(keys_lower["merchant_category"]).strip()
        r_bank = keys_lower.get("receiver_bank")
        merchant = f"{m_cat} ({r_bank})" if r_bank else f"{m_cat} Merchant"

    if not merchant or merchant.lower() in ["none", "unknown", "nan"]:
        merchant = extract_merchant(description)

    # 6. Category mapping
    category = ""
    for k in ["category", "expense_type", "tag", "merchant_category"]:
        if k in keys_lower and keys_lower[k]:
            raw_c = str(keys_lower[k]).strip().lower()
            if "groc" in raw_c:
                category = "Food and groceries"
            elif "food" in raw_c or "dining" in raw_c:
                category = "Food delivery"
            elif "shop" in raw_c or "retail" in raw_c:
                category = "Shopping"
            elif "util" in raw_c or "bill" in raw_c:
                category = "Bills and utilities"
            elif "trans" in raw_c or "travel" in raw_c:
                category = "Transport"
            elif "fuel" in raw_c:
                category = "Fuel"
            elif "entert" in raw_c:
                category = "Entertainment"
            elif "health" in raw_c or "medic" in raw_c:
                category = "Healthcare"
            elif "edu" in raw_c:
                category = "Education"
            elif "other" in raw_c:
                category = "Other"
            elif raw_c.title() in CATEGORIES:
                category = raw_c.title()
            break

    if not category or category not in CATEGORIES:
        category = categorize_transaction(description, merchant, debit, credit, user_corrections)

    # Unique record ID
    tx_id = reference_id if reference_id else f"tx_{parsed_date.replace('-', '')}_{row_index}_{abs(hash(description)) % 100000:05d}"

    return {
        "id": tx_id,
        "account_id": "acc_primary",
        "transaction_date": parsed_date,
        "description": description,
        "merchant": merchant,
        "debit": round(debit, 2),
        "credit": round(credit, 2),
        "currency": "INR",
        "category": category,
        "reference_id": reference_id,
        "source_file": source_file,
        "source_row": row_index,
        "extraction_confidence": 1.0
    }
