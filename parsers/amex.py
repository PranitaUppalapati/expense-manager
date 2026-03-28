"""American Express — CSV parser (credit cards only)."""

import csv
from datetime import datetime
from .base import AbstractBankParser, Transaction


class AmexParser(AbstractBankParser):
    BANK      = "Amex"
    BANK_ID   = "amex"
    ACCT_TYPE = "credit_card"
    CURRENCY  = "USD"

    def parse(self, filepath: str) -> list[Transaction]:
        """
        Amex CSV format:
          Date, Description, Card Member, Account #, Amount
          01/15/2024, AMAZON.COM, CARD MEMBER, -41004, 29.99

        Amount: positive = charge (debit), negative = payment/credit
        """
        txns    = []
        account = "...XXXXX"

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows   = list(reader)

        # Extract account from first row if present
        if rows:
            raw_acct = rows[0].get("Account #", "").strip()
            if raw_acct:
                account = "..." + str(raw_acct)[-5:]

        for row in rows:
            row = {k.strip(): v.strip() for k, v in row.items() if k}

            raw_date = row.get("Date", "").strip()
            desc     = row.get("Description", "").strip()
            raw_amt  = row.get("Amount", "0").strip().replace(",", "")

            if not raw_date or not desc:
                continue

            try:
                amount = float(raw_amt)
            except ValueError:
                continue

            # Amex: positive = charge (money OUT), negative = payment (money IN)
            if amount >= 0:
                debit, credit = amount, 0.0
            else:
                debit, credit = 0.0, abs(amount)

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
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return raw
