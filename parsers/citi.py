"""Citibank — CSV parser (checking and credit cards use same export format)."""

import csv
from datetime import datetime
from .base import AbstractBankParser, Transaction


class CitiParser(AbstractBankParser):
    BANK     = "Citi"
    BANK_ID  = "citi"
    CURRENCY = "USD"

    def __init__(self, account_type="debit"):
        self.account_type = account_type

    def parse(self, filepath: str) -> list[Transaction]:
        txns    = []
        account = "...XXXX"

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows   = list(reader)
            headers_lower = {h.lower().strip() for h in (reader.fieldnames or [])}

        # Citi format: Status, Date, Description, Debit, Credit
        # or:          Date, Description, Debit, Credit
        has_status = "status" in headers_lower

        for row in rows:
            row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            status = row.get("status", "").lower()
            if status and status not in ("", "cleared", "posted", "pending"):
                continue

            raw_date = row.get("date", "").strip()
            desc     = row.get("description", "").strip()
            if not raw_date or not desc:
                continue

            raw_debit  = (row.get("debit")  or "").replace(",", "")
            raw_credit = (row.get("credit") or "").replace(",", "")

            try:
                debit  = abs(float(raw_debit))  if raw_debit  else 0.0
                credit = abs(float(raw_credit)) if raw_credit else 0.0
            except ValueError:
                continue

            txns.append(Transaction(
                bank=self.BANK,
                bank_id=self.BANK_ID,
                account=account,
                account_type=self.account_type,
                currency=self.CURRENCY,
                date=self._parse_date(raw_date),
                description=desc,
                credit=credit,
                debit=debit,
                balance=0.0,
            ))

        return txns

    @staticmethod
    def _parse_date(raw: str) -> str:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return raw
