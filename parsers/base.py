"""
Base classes for all bank parsers.
Every parser returns a list of Transaction dataclass instances.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal


AccountType = Literal["debit", "savings", "credit_card"]
Currency    = Literal["INR", "USD", "EUR", "GBP"]


@dataclass
class Transaction:
    bank:         str          # Human-readable bank name  e.g. "SBI", "Chase"
    bank_id:      str          # Machine ID  e.g. "sbi", "chase", "amex"
    account:      str          # Masked account number
    account_type: AccountType  # "debit" | "savings" | "credit_card"
    currency:     Currency     # "INR" | "USD" | …
    date:         str          # ISO "YYYY-MM-DD"
    description:  str          # Raw description from statement
    credit:       float        # Money IN  (always ≥ 0)
    debit:        float        # Money OUT (always ≥ 0)
    balance:      float        # Running balance after this transaction
    category:     str = "Others"
    # Assigned later by the orchestrator:
    id:           str = ""     # e.g. "sbi-0", "chase-12"
    dedup_key:    str = ""     # sha256 fingerprint for deduplication


class AbstractBankParser(ABC):
    """
    Implement `parse(filepath)` to return a list of Transaction objects.
    All amounts should be positive floats; set `credit` XOR `debit` > 0.
    """

    @abstractmethod
    def parse(self, filepath: str) -> list[Transaction]:
        ...
