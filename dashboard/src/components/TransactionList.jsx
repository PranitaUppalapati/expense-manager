import React, { useState, useMemo, useEffect } from "react";
import { fmtAmount, CATEGORY_COLORS, BANK_COLORS, BANK_DISPLAY } from "../utils.js";

const PAGE_SIZE = 40;

export default function TransactionList({
  transactions,
  activeCategory,        // set by clicking a chart segment in Overview
  onClearActiveCategory, // call this to release the external filter
}) {
  const [search,     setSearch] = useState("");
  const [catFilter,  setCat]    = useState("All");
  const [typeFilter, setType]   = useState("All");
  const [page,       setPage]   = useState(1);

  // When the chart sets an external category, reset page so user sees results
  useEffect(() => {
    if (activeCategory) setPage(1);
  }, [activeCategory]);

  // The effective category: external (chart click) takes priority over dropdown
  const effectiveCat = activeCategory || catFilter;

  const categories = useMemo(() => {
    const cats = new Set(transactions.map((t) => t.category));
    return ["All", ...Array.from(cats).sort()];
  }, [transactions]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return transactions
      .filter((t) => {
        if (effectiveCat  !== "All" && t.category !== effectiveCat)  return false;
        if (typeFilter    === "Debit"  && t.debit   === 0)            return false;
        if (typeFilter    === "Credit" && t.credit  === 0)            return false;
        if (q && !t.description.toLowerCase().includes(q))           return false;
        return true;
      })
      .sort((a, b) => (b.date > a.date ? 1 : -1));
  }, [transactions, search, effectiveCat, typeFilter]);

  const visible = filtered.slice(0, page * PAGE_SIZE);
  const hasMore = visible.length < filtered.length;

  const handleSearch = (e) => { setSearch(e.target.value); setPage(1); };
  const handleType   = (e) => { setType(e.target.value);   setPage(1); };

  // When user manually changes the dropdown, hand control back to local state
  const handleCat = (e) => {
    setCat(e.target.value);
    setPage(1);
    if (activeCategory) onClearActiveCategory?.();
  };

  const clearAll = () => {
    setCat("All");
    setPage(1);
    onClearActiveCategory?.();
  };

  const catColor = activeCategory ? (CATEGORY_COLORS[activeCategory] || "#6B7280") : null;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div className="card-title">Transaction History</div>
          <div className="card-sub">
            {filtered.length} transaction{filtered.length !== 1 ? "s" : ""}
            {typeFilter !== "All" ? ` · ${typeFilter}s only` : ""}
          </div>
        </div>
      </div>

      {/* ── Active category banner (from chart drill-down) ── */}
      {activeCategory && (
        <div className="active-filter-banner">
          <span className="active-filter-label">
            Filtered by &nbsp;
            <span style={{ color: catColor, fontWeight: 700 }}>
              ● {activeCategory}
            </span>
          </span>
          <button className="active-filter-clear" onClick={clearAll}>
            ✕ Clear filter
          </button>
        </div>
      )}

      <div className="txn-controls">
        <input
          className="search-box"
          placeholder="Search transactions…"
          value={search}
          onChange={handleSearch}
        />
        {/* Dropdown mirrors the effective category; changing it releases the chart filter */}
        <select
          className="filter-select"
          value={effectiveCat}
          onChange={handleCat}
        >
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select className="filter-select" value={typeFilter} onChange={handleType}>
          {["All", "Debit", "Credit"].map((t) => <option key={t}>{t}</option>)}
        </select>
      </div>

      <div className="txn-table">
        <div className="txn-head">
          <span>Date</span>
          <span>Bank</span>
          <span>Description</span>
          <span>Category</span>
          <span style={{ textAlign: "right" }}>Amount</span>
          <span style={{ textAlign: "right" }}>Balance</span>
        </div>

        {visible.map((t) => {
          const catClr  = CATEGORY_COLORS[t.category] || "#6B7280";
          const bankClr = BANK_COLORS[t.bank_id]      || "#6B7280";
          return (
            <div key={t.id} className="txn-row">
              <span className="txn-date">{formatDate(t.date)}</span>

              <span>
                <span
                  className="txn-bank-pill"
                  style={{ background: bankClr + "22", color: bankClr }}
                >
                  {BANK_DISPLAY[t.bank_id] || t.bank || "—"}
                </span>
              </span>

              <span className="txn-desc" title={t.description}>
                {cleanDesc(t.description)}
              </span>

              <span>
                <span
                  className="txn-cat-pill"
                  style={{ background: catClr + "22", color: catClr }}
                >
                  <span style={{
                    width: 5, height: 5, borderRadius: "50%",
                    background: catClr, display: "inline-block",
                  }} />
                  {t.category}
                </span>
              </span>

              <span className={t.debit > 0 ? "txn-debit" : t.credit > 0 ? "txn-credit" : "txn-zero"}>
                {t.debit  > 0 && `−${fmtAmount(t.debit,  t.currency)}`}
                {t.credit > 0 && `+${fmtAmount(t.credit, t.currency)}`}
                {t.debit === 0 && t.credit === 0 && "—"}
              </span>

              <span className="txn-balance">
                {t.balance ? fmtAmount(t.balance, t.currency) : "—"}
              </span>
            </div>
          );
        })}
      </div>

      {hasMore && (
        <button className="load-more" onClick={() => setPage((p) => p + 1)}>
          Load more ({filtered.length - visible.length} remaining)
        </button>
      )}

      {filtered.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-3)" }}>
          No transactions match your filters.
        </div>
      )}
    </>
  );
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "2-digit" });
}

export function cleanDesc(desc = "") {
  if (desc.includes("UPI/DR") || desc.includes("UPI/CR")) {
    const parts = desc.split("/");
    const name  = (parts[3] || "").trim();
    const note  = (parts[6] || "").trim();
    if (name) return note ? `${name} · ${note}` : name;
  }
  return desc
    .replace(/^(SBIPOS\d*|OTHPOS\d*|OTHPG\s*\d+)\s*/i, "")
    .replace(/\b\d{6,}\b/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}
