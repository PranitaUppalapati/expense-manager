"""Capital One — CSV parser (credit cards)."""

import csv
from datetime import datetime
from .base import AbstractBankParser, Transaction


class CapitalOneParser(AbstractBankParser):
    BANK      = "Capital One"
    BANK_ID   = "capitalone"
    ACCT_TYPE = "credit_card"
    CURRENCY  = "USD"

    def parse(self, filepath: str) -> list[Transaction]:
        """
        Capital One CSV:
          Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit
          2024-01-15, 2024-01-16, 1234, AMAZON.COM, Shopping, 29.99,
          2024-01-20, 2024-01-21, 1234, PAYMENT THANK YOU, , , 500.00
        """
        txns    = []
        account = "...XXXX"

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows   = list(reader)

        # Extract card number from first data row
        if rows:
            card_no = rows[0].get("Card No.", "").strip()
            if card_no:
                account = "..." + str(card_no)[-4:]

        for row in rows:
            row = {k.strip(): v.strip() for k, v in row.items() if k}

            raw_date = row.get("Transaction Date", "").strip()
            desc     = row.get("Description", "").strip()

            if not raw_date or not desc:
                continue

            raw_debit  = (row.get("Debit",  "") or "").replace(",", "")
            raw_credit = (row.get("Credit", "") or "").replace(",", "")

            try:
                debit  = float(raw_debit)  if raw_debit  else 0.0
                credit = float(raw_credit) if raw_credit else 0.0
            except ValueError:
                continue

            txns.append(Transaction(
                bank=self.BANK,
                bank_id=self.BANK_ID,
                account=account,
                account_type=self.ACCT_TYPE,
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
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return raw
