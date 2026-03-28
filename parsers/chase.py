"""
Chase Bank — CSV parser.
Covers both Chase Checking/Savings and Chase Credit Cards
(both use the same CSV export format).
"""

import csv
from datetime import datetime
from .base import AbstractBankParser, Transaction


class ChaseParser(AbstractBankParser):
    BANK      = "Chase"
    BANK_ID   = "chase"
    CURRENCY  = "USD"

    # Chase credit card CSV has "Type" column with values like "Sale", "Payment"
    # Chase checking CSV has "Type" with "DEBIT", "CREDIT", "ATM", etc.
    HEADERS = {"Transaction Date", "Post Date", "Description", "Amount"}

    def __init__(self, account_type="debit"):
        self.account_type = account_type

    def parse(self, filepath: str) -> list[Transaction]:
        txns = []
        account = "...XXXX"

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

            # Auto-detect credit vs debit from "Type" values in first few rows
            rows = list(reader)

        # Guess account type from Type column values
        types = {r.get("Type", "").strip().lower() for r in rows[:20]}
        if types & {"sale", "payment", "return", "adjustment"}:
            acct_type = "credit_card"
        else:
            acct_type = self.account_type

        for row in rows:
            raw_date = row.get("Transaction Date", "").strip()
            desc     = row.get("Description", "").strip()
            raw_amt  = row.get("Amount", "0").strip().replace(",", "")

            if not raw_date or not raw_amt:
                continue

            try:
                amount = float(raw_amt)
            except ValueError:
                continue

            # Chase: negative amount = charge/debit, positive = payment/credit
            if amount < 0:
                debit, credit = abs(amount), 0.0
            else:
                debit, credit = 0.0, amount

            txns.append(Transaction(
                bank=self.BANK,
                bank_id=self.BANK_ID,
                account=account,
                account_type=acct_type,
                currency=self.CURRENCY,
                date=self._parse_date(raw_date),
                description=desc,
                credit=credit,
                debit=debit,
                balance=0.0,  # Chase CSV doesn't include running balance
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
