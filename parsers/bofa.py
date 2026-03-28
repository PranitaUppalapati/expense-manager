"""Bank of America — CSV parser (checking, savings, and credit cards)."""

import csv
from datetime import datetime
from .base import AbstractBankParser, Transaction


class BofAParser(AbstractBankParser):
    BANK     = "Bank of America"
    BANK_ID  = "bofa"
    CURRENCY = "USD"

    def __init__(self, account_type="debit"):
        self.account_type = account_type

    def parse(self, filepath: str) -> list[Transaction]:
        txns   = []
        account = "...XXXX"

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            # BofA puts account info in header lines before the CSV data
            raw = f.read()

        import io, re
        # Extract account number if present in header
        m = re.search(r"Account #[:\s]*(\S+)", raw, re.I)
        if m:
            account = "..." + m.group(1)[-4:]

        # Find where the CSV data starts (first line with "Date" header)
        lines = raw.splitlines()
        start = 0
        for i, line in enumerate(lines):
            if line.lower().startswith("date,") or "posted date" in line.lower():
                start = i
                break

        reader = csv.DictReader(lines[start:])
        headers_lower = {h.lower().strip() for h in (reader.fieldnames or [])}

        # Detect format variant
        has_running_bal  = "running bal." in headers_lower or "running balance" in headers_lower
        has_debit_credit = "debit amount" in headers_lower and "credit amount" in headers_lower

        for row in reader:
            # Normalise keys
            row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            raw_date = (row.get("date") or row.get("posted date") or "").strip()
            desc     = (row.get("payee") or row.get("description") or "").strip()
            if not raw_date or not desc:
                continue

            if has_debit_credit:
                debit  = float((row.get("debit amount")  or "0").replace(",", ""))
                credit = float((row.get("credit amount") or "0").replace(",", ""))
            else:
                raw_amt = (row.get("amount") or "0").replace(",", "")
                try:
                    amount = float(raw_amt)
                except ValueError:
                    continue
                debit, credit = (abs(amount), 0.0) if amount < 0 else (0.0, amount)

            raw_bal = row.get("running bal.") or row.get("running balance") or "0"
            try:
                balance = float(raw_bal.replace(",", ""))
            except ValueError:
                balance = 0.0

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
                balance=balance,
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
