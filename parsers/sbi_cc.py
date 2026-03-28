"""
SBI Credit Card — PDF parser using pdfplumber.
Falls back gracefully if pdfplumber is not installed.
"""

import re
from datetime import datetime
from .base import AbstractBankParser, Transaction


class SBICreditCardParser(AbstractBankParser):
    BANK      = "SBI Credit Card"
    BANK_ID   = "sbi_cc"
    ACCT_TYPE = "credit_card"
    CURRENCY  = "INR"

    # Typical SBI CC row pattern:
    # 15 Jan 2024  AMAZON PAY  15 Jan 2024  500.00 Cr  1234.56
    ROW_RE = re.compile(
        r"(\d{2}\s+\w{3}\s+\d{4})\s+"   # transaction date
        r"(.+?)\s+"                        # description (non-greedy)
        r"(\d[\d,]*\.\d{2})\s*(Cr|Dr)",   # amount + type
        re.IGNORECASE,
    )

    def parse(self, filepath: str) -> list[Transaction]:
        try:
            import pdfplumber
        except ImportError:
            print(
                f"  [WARN] pdfplumber not installed — skipping SBI CC PDF: {filepath}\n"
                "         Run: pip3 install pdfplumber"
            )
            return []

        txns = []
        account = "XXXX XXXX"

        with pdfplumber.open(filepath) as pdf:
            full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        # Extract account number
        m = re.search(r"Card\s+No[.:]?\s*(\d{4}\s*\d{4}\s*\d{4}\s*\d{4}|\*{4}\s*\*{4}\s*\d{4})", full_text, re.I)
        if m:
            account = m.group(1).strip()

        for match in self.ROW_RE.finditer(full_text):
            raw_date, desc, amount_str, dr_cr = match.groups()
            amount = float(amount_str.replace(",", ""))
            is_credit = dr_cr.upper() == "CR"

            txns.append(Transaction(
                bank=self.BANK,
                bank_id=self.BANK_ID,
                account=account,
                account_type=self.ACCT_TYPE,
                currency=self.CURRENCY,
                date=self._parse_date(raw_date),
                description=desc.strip(),
                credit=amount if is_credit else 0.0,
                debit=0.0 if is_credit else amount,
                balance=0.0,  # CC PDFs rarely show running balance
            ))

        return txns

    @staticmethod
    def _parse_date(raw: str) -> str:
        for fmt in ("%d %b %Y", "%d-%b-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return raw.strip()
