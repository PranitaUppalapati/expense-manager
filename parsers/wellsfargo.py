"""Wells Fargo — CSV parser (checking / savings)."""

import csv
from datetime import datetime
from .base import AbstractBankParser, Transaction


class WellsFargoParser(AbstractBankParser):
    BANK     = "Wells Fargo"
    BANK_ID  = "wellsfargo"
    CURRENCY = "USD"

    def __init__(self, account_type="debit"):
        self.account_type = account_type

    def parse(self, filepath: str) -> list[Transaction]:
        """
        Wells Fargo CSV format (no header row):
          Date, Amount, *, *, Description
          "01/15/2024","-29.99","*","*","AMAZON.COM"
        """
        txns    = []
        account = "...XXXX"

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 5:
                    continue

                raw_date = row[0].strip().strip('"')
                raw_amt  = row[1].strip().strip('"').replace(",", "")
                desc     = row[4].strip().strip('"') if len(row) > 4 else ""

                # Skip header-like rows
                if raw_date.lower() in ("date", "") or not raw_amt:
                    continue

                try:
                    amount = float(raw_amt)
                except ValueError:
                    continue

                debit, credit = (abs(amount), 0.0) if amount < 0 else (0.0, amount)

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
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return raw
