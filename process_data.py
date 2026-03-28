"""
Multi-bank statement processor — main entry point.

Usage:
  python3 process_data.py                        # scan statements/ for all files
  python3 process_data.py --file path/to/file    # single file (used by n8n)
  python3 process_data.py --folder path/to/dir   # scan a specific folder
  python3 process_data.py --force                # re-process even known files

Output: dashboard/src/data/transactions.json
"""

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
from collections import defaultdict
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT           = pathlib.Path(__file__).parent
STATEMENTS_DIR = ROOT / "statements"
OUTPUT_PATH    = ROOT / "dashboard" / "src" / "data" / "transactions.json"
REGISTRY_PATH  = ROOT / "processed_files.json"   # dedup: file-level fingerprints

# ── Imports ───────────────────────────────────────────────────────────────────
sys.path.insert(0, str(ROOT))
from parsers import detect_parser, Transaction
from categorizer import classify


# ─────────────────────────────────────────────────────────────────────────────
# Deduplication helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _txn_dedup_key(t: Transaction) -> str:
    """Content-based fingerprint to catch overlapping date-range exports."""
    amount = round(t.debit if t.debit else t.credit, 2)
    return _sha256(f"{t.bank_id}|{t.date}|{amount}|{t.description[:40]}")


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {}


def save_registry(registry: dict):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# File discovery
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf"}


def discover_files(folder: pathlib.Path) -> list:
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(folder.rglob(f"*{ext}"))
    return [f for f in files if not f.name.startswith("~$")]


# ─────────────────────────────────────────────────────────────────────────────
# Core processing
# ─────────────────────────────────────────────────────────────────────────────

def process_files(files: list, force: bool) -> list:
    registry = load_registry()
    all_txns = []
    updated  = False

    for filepath in sorted(files):
        fp_str = str(filepath)
        fhash  = _file_hash(fp_str)

        if not force and fhash in registry:
            print(f"  ↩  Skipped (already processed): {filepath.name}")
            continue

        parser = detect_parser(fp_str)
        if parser is None:
            print(f"  ✗  No parser found for: {filepath.name}  — skipping")
            continue

        try:
            txns = parser.parse(fp_str)
        except Exception as e:
            print(f"  ✗  Error parsing {filepath.name}: {e}")
            continue

        for t in txns:
            t.category = classify(t.description)

        print(f"  ✓  {parser.__class__.__name__:25s}  {len(txns):4d} txns  ← {filepath.name}")
        all_txns.extend(txns)

        registry[fhash] = {
            "path":         fp_str,
            "processed_at": datetime.utcnow().isoformat(),
        }
        updated = True

    if updated:
        save_registry(registry)

    return all_txns


def deduplicate(txns: list) -> list:
    seen   = set()
    unique = []
    dupes  = 0
    for t in txns:
        key = _txn_dedup_key(t)
        t.dedup_key = key
        if key not in seen:
            seen.add(key)
            unique.append(t)
        else:
            dupes += 1
    if dupes:
        print(f"  ⚡  Removed {dupes} duplicate transaction(s)")
    return unique


# ─────────────────────────────────────────────────────────────────────────────
# JSON output builders
# ─────────────────────────────────────────────────────────────────────────────

def _merchant_name(desc: str) -> str:
    if "UPI/DR" in desc or "UPI/CR" in desc:
        parts = desc.split("/")
        return (parts[3] if len(parts) > 3 else desc).strip()[:30]
    cleaned = re.sub(r"^(SBIPOS\d*|OTHPOS\d*|OTHPG\s*\d+)\s*", "", desc, flags=re.I)
    cleaned = re.sub(r"\b\d{6,}\b", "", cleaned).strip()
    return cleaned[:30]


def build_output(txns: list) -> dict:
    # Assign stable IDs (sorted by date)
    per_bank_counter = defaultdict(int)
    for t in sorted(txns, key=lambda x: x.date):
        n    = per_bank_counter[t.bank_id]
        t.id = f"{t.bank_id}-{n}"
        per_bank_counter[t.bank_id] += 1

    # Banks index
    banks_seen = {}
    for t in sorted(txns, key=lambda x: x.date):
        if t.bank_id not in banks_seen:
            banks_seen[t.bank_id] = {
                "id":           t.bank_id,
                "name":         t.bank,
                "account_type": t.account_type,
                "currency":     t.currency,
                "account":      t.account,
                "last_balance": 0.0,
            }
        if t.balance:
            banks_seen[t.bank_id]["last_balance"] = t.balance

    # Monthly summary per bank
    monthly_map = {}
    for t in txns:
        mo  = t.date[:7]
        key = (mo, t.bank_id)
        if key not in monthly_map:
            monthly_map[key] = {
                "month":    mo,
                "bank_id":  t.bank_id,
                "bank":     t.bank,
                "currency": t.currency,
                "credits":  0.0,
                "debits":   0.0,
                "count":    0,
            }
        monthly_map[key]["credits"] += t.credit
        monthly_map[key]["debits"]  += t.debit
        monthly_map[key]["count"]   += 1

    # Category totals
    cat_map = defaultdict(float)
    for t in txns:
        if t.debit > 0:
            cat_map[(t.category, t.bank_id, t.currency)] += t.debit

    cat_totals = [
        {"category": cat, "bank_id": bid, "currency": cur, "amount": round(amt, 2)}
        for (cat, bid, cur), amt in sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
    ]

    # Top merchants
    merch_map = defaultdict(float)
    for t in txns:
        if t.debit > 0:
            merch_map[(_merchant_name(t.description), t.bank_id, t.currency)] += t.debit

    top_merchants = sorted(
        [{"name": n, "bank_id": bid, "currency": cur, "amount": round(a, 2)}
         for (n, bid, cur), a in merch_map.items()],
        key=lambda x: x["amount"], reverse=True
    )[:30]

    all_dates = [t.date for t in txns if t.date]
    period    = f"{min(all_dates)[:7]} – {max(all_dates)[:7]}" if all_dates else "—"

    return {
        "generated_at":    datetime.utcnow().isoformat(),
        "period":          period,
        "banks":           list(banks_seen.values()),
        "transactions":    [_txn_to_dict(t) for t in txns],
        "monthly_summary": sorted(monthly_map.values(), key=lambda x: (x["month"], x["bank_id"])),
        "category_totals": cat_totals,
        "top_merchants":   top_merchants,
    }


def _txn_to_dict(t: Transaction) -> dict:
    return {
        "id":           t.id,
        "bank":         t.bank,
        "bank_id":      t.bank_id,
        "account":      t.account,
        "account_type": t.account_type,
        "currency":     t.currency,
        "date":         t.date,
        "description":  t.description,
        "credit":       round(t.credit,  2),
        "debit":        round(t.debit,   2),
        "balance":      round(t.balance, 2),
        "category":     t.category,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Multi-bank statement processor")
    ap.add_argument("--file",   help="Process a single file (used by n8n)")
    ap.add_argument("--folder", help="Scan a specific folder")
    ap.add_argument("--force",  action="store_true",
                    help="Re-process files even if already in registry")
    args = ap.parse_args()

    print("\n🏦  Multi-Bank Statement Processor")
    print("─" * 50)

    if args.file:
        files = [pathlib.Path(args.file)]
        if not files[0].exists():
            print(f"✗ File not found: {args.file}")
            sys.exit(1)
    elif args.folder:
        files = discover_files(pathlib.Path(args.folder))
    else:
        if not STATEMENTS_DIR.exists():
            print(f"✗ statements/ folder not found at {STATEMENTS_DIR}")
            sys.exit(1)
        files = discover_files(STATEMENTS_DIR)

    if not files:
        print("  No statement files found.")
        sys.exit(0)

    print(f"  Found {len(files)} file(s)\n")

    all_txns = process_files(files, force=args.force)

    if not all_txns:
        print("\n  No new transactions to add.")
        sys.exit(0)

    all_txns = deduplicate(all_txns)

    # Merge with existing JSON (so single-file runs don't erase other banks)
    if OUTPUT_PATH.exists() and not args.force:
        with open(OUTPUT_PATH) as f:
            existing = json.load(f)

        existing_keys = set()
        existing_objs = []
        for td in existing.get("transactions", []):
            t = Transaction(
                bank=td["bank"], bank_id=td["bank_id"], account=td["account"],
                account_type=td["account_type"], currency=td["currency"],
                date=td["date"], description=td["description"],
                credit=td["credit"], debit=td["debit"], balance=td["balance"],
                category=td["category"], id=td["id"],
            )
            key = _txn_dedup_key(t)
            t.dedup_key = key
            if key not in existing_keys:
                existing_keys.add(key)
                existing_objs.append(t)

        new_unique = [t for t in all_txns if t.dedup_key not in existing_keys]
        print(f"\n  ➕  {len(new_unique)} new  +  {len(existing_objs)} existing transactions")
        all_txns = existing_objs + new_unique

    output = build_output(all_txns)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅  {len(all_txns)} transactions → {OUTPUT_PATH}")
    print(f"   Banks:  {', '.join(b['name'] for b in output['banks'])}")
    print(f"   Period: {output['period']}")


if __name__ == "__main__":
    main()
