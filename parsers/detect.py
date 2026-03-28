"""
Auto-detect which bank parser to use for a given file.

Detection priority:
1. Parent folder name  (statements/Chase/ → Chase)
2. File extension
3. CSV header sniffing
4. PDF content keywords (for SBI CC)
"""

import os
import csv
import pathlib
from typing import Optional
from .base import AbstractBankParser


# Folder name → (parser_class_path, account_type)
FOLDER_MAP = {
    "sbi":         ("sbi",         "debit"),
    "sbi_cc":      ("sbi_cc",      "credit_card"),
    "chase":       ("chase",       "debit"),       # Chase auto-detects cc vs debit internally
    "bofa":        ("bofa",        "debit"),
    "bankofamerica": ("bofa",      "debit"),
    "citi":        ("citi",        "debit"),
    "citibank":    ("citi",        "debit"),
    "wellsfargo":  ("wellsfargo",  "debit"),
    "wells_fargo": ("wellsfargo",  "debit"),
    "amex":        ("amex",        "credit_card"),
    "americanexpress": ("amex",    "credit_card"),
    "capitalone":  ("capitalone",  "credit_card"),
    "capital_one": ("capitalone",  "credit_card"),
}

# CSV header patterns → (parser_key, account_type)
HEADER_MAP = [
    ({"transaction date", "post date", "description", "amount"},
     "chase", "debit"),
    ({"date", "description", "card member", "account #", "amount"},
     "amex", "credit_card"),
    ({"transaction date", "posted date", "card no.", "description", "debit"},
     "capitalone", "credit_card"),
    ({"status", "date", "description", "debit", "credit"},
     "citi", "debit"),
    ({"date", "description", "debit", "credit"},
     "citi", "debit"),
    ({"posted date", "payee", "address", "amount"},
     "bofa", "debit"),
    ({"date", "description", "amount", "running bal."},
     "bofa", "debit"),
]


def _load_parser(key: str, account_type: str) -> AbstractBankParser:
    if key == "sbi":
        from .sbi import SBIParser
        return SBIParser()
    if key == "sbi_cc":
        from .sbi_cc import SBICreditCardParser
        return SBICreditCardParser()
    if key == "chase":
        from .chase import ChaseParser
        return ChaseParser(account_type)
    if key == "bofa":
        from .bofa import BofAParser
        return BofAParser(account_type)
    if key == "citi":
        from .citi import CitiParser
        return CitiParser(account_type)
    if key == "wellsfargo":
        from .wellsfargo import WellsFargoParser
        return WellsFargoParser(account_type)
    if key == "amex":
        from .amex import AmexParser
        return AmexParser()
    if key == "capitalone":
        from .capitalone import CapitalOneParser
        return CapitalOneParser()
    raise ValueError(f"Unknown parser key: {key}")


def detect_parser(filepath: str) -> Optional[AbstractBankParser]:
    """Return the appropriate parser instance, or None if unrecognised."""
    path = pathlib.Path(filepath)
    ext  = path.suffix.lower()

    # ── 1. Folder name ────────────────────────────────────────────
    folder = path.parent.name.lower().replace(" ", "").replace("-", "_")
    if folder in FOLDER_MAP:
        key, acct_type = FOLDER_MAP[folder]
        return _load_parser(key, acct_type)

    # ── 2. Extension → obvious XLSX is SBI ───────────────────────
    if ext in (".xlsx", ".xls"):
        return _load_parser("sbi", "debit")

    # ── 3. CSV header sniffing ────────────────────────────────────
    if ext == ".csv":
        try:
            with open(filepath, newline="", encoding="utf-8-sig") as f:
                sample = f.read(4096)
            # Skip non-header preamble lines
            lines = [l for l in sample.splitlines() if "," in l]
            if lines:
                reader = csv.DictReader(lines)
                headers = {h.strip().lower() for h in (reader.fieldnames or [])}
                for pattern, key, acct_type in HEADER_MAP:
                    if pattern.issubset(headers):
                        return _load_parser(key, acct_type)
        except Exception:
            pass

    # ── 4. PDF → try SBI CC keywords ─────────────────────────────
    if ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                text = (pdf.pages[0].extract_text() or "").upper()
            if any(k in text for k in ("CREDIT CARD", "STATEMENT OF ACCOUNT", "CARD NUMBER")):
                return _load_parser("sbi_cc", "credit_card")
        except Exception:
            pass

    return None
