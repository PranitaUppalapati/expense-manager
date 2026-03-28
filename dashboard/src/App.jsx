import React, { useState, useMemo } from "react";
import rawData from "./data/transactions.json";
import {
  fmt, fmtK, fmtAmount, fmtAmountK, fmtMonth,
  CATEGORY_COLORS, BANK_COLORS, BANK_DISPLAY,
} from "./utils.js";
import SpendingChart     from "./components/SpendingChart.jsx";
import CategoryChart     from "./components/CategoryChart.jsx";
import BalanceChart      from "./components/BalanceChart.jsx";
import MerchantChart     from "./components/MerchantChart.jsx";
import TransactionList, { cleanDesc } from "./components/TransactionList.jsx";
import CategoryTrendChart from "./components/CategoryTrendChart.jsx";

const NAV = [
  { icon: "◈", label: "Overview",     view: "Overview"      },
  { icon: "↗", label: "Trends",       view: "Trends"        },
  { icon: "≡", label: "Transactions", view: "Transactions"  },
];

const PERIODS = [
  { label: "3M",  months: 3   },
  { label: "6M",  months: 6   },
  { label: "1Y",  months: 12  },
  { label: "All", months: 999 },
];

export default function App() {
  const [view,           setView]          = useState("Overview");
  const [period,         setPeriod]        = useState(12);
  const [bankFilter,     setBankFilter]    = useState("all");
  const [activeCategory, setActiveCategory] = useState(null);

  // Category click in donut chart → jump to Transactions filtered by that category
  const handleCategoryClick = (category) => {
    setActiveCategory(category);
    setView("Transactions");
  };

  const banks = rawData.banks || [];

  // ── Aggregate monthly_summary by month (handles multiple banks per month)
  const aggregatedMonthly = useMemo(() => {
    const src = bankFilter === "all"
      ? rawData.monthly_summary
      : rawData.monthly_summary.filter((m) => m.bank_id === bankFilter);
    const agg = {};
    for (const m of src) {
      if (!agg[m.month]) agg[m.month] = { month: m.month, credits: 0, debits: 0, count: 0 };
      agg[m.month].credits += m.credits;
      agg[m.month].debits  += m.debits;
      agg[m.month].count   += m.count;
    }
    return Object.values(agg).sort((a, b) => a.month.localeCompare(b.month));
  }, [bankFilter]);

  const allMonths = useMemo(
    () => aggregatedMonthly.map((m) => m.month),
    [aggregatedMonthly],
  );

  const filteredMonths = useMemo(() => {
    if (period >= 999) return allMonths;
    return allMonths.slice(-period);
  }, [allMonths, period]);

  const startMonth = filteredMonths[0]  || "";
  const endMonth   = filteredMonths[filteredMonths.length - 1] || "";

  // ── Filtered transactions (bank + period)
  const transactions = useMemo(
    () =>
      rawData.transactions.filter((t) => {
        if (bankFilter !== "all" && t.bank_id !== bankFilter) return false;
        const mo = t.date.slice(0, 7);
        return mo >= startMonth && mo <= endMonth;
      }),
    [startMonth, endMonth, bankFilter],
  );

  // ── Chart data
  const monthlyData = useMemo(
    () =>
      aggregatedMonthly
        .filter((m) => m.month >= startMonth && m.month <= endMonth)
        .map((m) => ({ ...m, label: fmtMonth(m.month) })),
    [aggregatedMonthly, startMonth, endMonth],
  );

  // Running balance — debit accounts only (credit cards don't have running balance)
  const balanceData = useMemo(() => {
    const byMonth = {};
    for (const t of transactions) {
      if (t.account_type !== "credit_card" && t.balance) {
        byMonth[t.date.slice(0, 7)] = t.balance;
      }
    }
    return filteredMonths
      .filter((m) => byMonth[m] !== undefined)
      .map((m) => ({ month: fmtMonth(m), balance: byMonth[m] }));
  }, [filteredMonths, transactions]);

  const categoryData = useMemo(() => {
    const totals = {};
    for (const t of transactions) {
      if (t.debit > 0) totals[t.category] = (totals[t.category] || 0) + t.debit;
    }
    return Object.entries(totals)
      .map(([category, amount]) => ({ category, amount }))
      .sort((a, b) => b.amount - a.amount);
  }, [transactions]);

  const merchantData = useMemo(() => {
    const map = {};
    for (const t of transactions) {
      if (t.debit > 0) {
        const name = cleanDesc(t.description).slice(0, 30);
        map[name] = (map[name] || 0) + t.debit;
      }
    }
    return Object.entries(map)
      .map(([name, amount]) => ({ name, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 12);
  }, [transactions]);

  // ── Summary stats
  const totalDebit  = transactions.reduce((s, t) => s + t.debit,  0);
  const totalCredit = transactions.reduce((s, t) => s + t.credit, 0);
  const netFlow     = totalCredit - totalDebit;
  const txnCount    = transactions.filter((t) => t.debit > 0 || t.credit > 0).length;

  // Month-over-month spend change
  const currMonth     = endMonth;
  const prevMonth     = allMonths[allMonths.indexOf(currMonth) - 1];
  const currMonthData = aggregatedMonthly.find((m) => m.month === currMonth);
  const prevMonthData = aggregatedMonthly.find((m) => m.month === prevMonth);
  const spendChange   =
    currMonthData && prevMonthData && prevMonthData.debits > 0
      ? ((currMonthData.debits - prevMonthData.debits) / prevMonthData.debits) * 100
      : null;

  // Trend insights
  const trendInsights = useMemo(() => {
    if (!monthlyData.length) return {};
    const debitOnly = monthlyData.filter((m) => m.debits > 0);
    if (!debitOnly.length) return {};
    const worstMonth = debitOnly.reduce((a, b) => (b.debits > a.debits ? b : a), debitOnly[0]);
    const bestMonth  = debitOnly.reduce((a, b) => (b.debits < a.debits ? b : a), debitOnly[0]);
    const avg        = debitOnly.reduce((s, m) => s + m.debits, 0) / debitOnly.length;
    const totalC     = monthlyData.reduce((s, m) => s + m.credits, 0);
    const totalD     = monthlyData.reduce((s, m) => s + m.debits,  0);
    const savings    = totalC > 0 ? ((totalC - totalD) / totalC) * 100 : 0;
    return { worstMonth, bestMonth, avg, savings };
  }, [monthlyData]);

  // Currency for selected bank (INR default when "all")
  const selectedBank = banks.find((b) => b.id === bankFilter);
  const currency     = selectedBank?.currency || "INR";
  const fmtV = (n) => fmtAmountK(n, currency);
  const fmtF = (n) => fmtAmount(n, currency);

  return (
    <div className="app">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">💳</div>
          <div>
            <div className="logo-text">Spendly</div>
            <div className="logo-sub">MULTI-BANK</div>
          </div>
        </div>

        <nav className="nav-section">
          <div className="nav-label">Menu</div>
          {NAV.map((n) => (
            <div
              key={n.view}
              className={`nav-item ${view === n.view ? "active" : ""}`}
              onClick={() => {
                setView(n.view);
                if (n.view !== "Transactions") setActiveCategory(null);
              }}
            >
              <span className="icon">{n.icon}</span>
              {n.label}
            </div>
          ))}
        </nav>

        {/* ── Accounts section ── */}
        {banks.length > 0 && (
          <div className="accounts-section">
            <div className="nav-label">Accounts</div>
            {banks.map((b) => {
              const color    = BANK_COLORS[b.id] || "#6B7280";
              const isCC     = b.account_type === "credit_card";
              const isActive = bankFilter === b.id;
              return (
                <div
                  key={b.id}
                  className="account-bank-card"
                  onClick={() => setBankFilter(isActive ? "all" : b.id)}
                  style={isActive ? { borderColor: color, background: color + "18" } : {}}
                >
                  <div className="account-bank-header">
                    <span className="account-bank-dot" style={{ background: color }} />
                    <span className="account-bank-name">{BANK_DISPLAY[b.id] || b.name}</span>
                    {isCC && <span className="account-type-badge cc">CC</span>}
                  </div>
                  <div className={`account-bank-balance ${isCC ? "cc" : "debit"}`}>
                    {fmtAmountK(b.last_balance, b.currency)}
                  </div>
                  <div className="account-bank-sub">
                    {isCC ? "outstanding" : "last balance"}
                    {b.account ? ` · ···${b.account.slice(-4)}` : ""}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="sidebar-footer">
          <div className="account-chip">
            <div className="label">DATA PERIOD</div>
            <div className="value">{rawData.period || "—"}</div>
            <div className="label" style={{ marginTop: 6 }}>TOTAL TXN</div>
            <div className="value">{(rawData.transactions?.length || 0).toLocaleString()}</div>
          </div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="main">
        {/* Header */}
        <div className="page-header">
          <div>
            <div className="page-title">
              {view === "Overview"     && "Financial Overview"}
              {view === "Trends"       && "Spending Trends"}
              {view === "Transactions" && "All Transactions"}
            </div>
            <div className="page-subtitle">
              {filteredMonths.length > 1
                ? `${fmtMonth(startMonth)} – ${fmtMonth(endMonth)}`
                : startMonth ? fmtMonth(startMonth) : "—"}
              &nbsp;·&nbsp;
              {selectedBank ? (BANK_DISPLAY[selectedBank.id] || selectedBank.name) : "All Banks"}
            </div>
          </div>

          <div className="header-controls-wrapper">
            {/* Period pills */}
            <div className="header-controls">
              {PERIODS.map((p) => (
                <button
                  key={p.label}
                  className={`period-pill ${period === p.months ? "active" : ""}`}
                  onClick={() => setPeriod(p.months)}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Bank filter pills — only shown when multiple banks exist */}
            {banks.length > 1 && (
              <div className="header-controls">
                <button
                  className={`period-pill ${bankFilter === "all" ? "active" : ""}`}
                  onClick={() => setBankFilter("all")}
                >
                  All
                </button>
                {banks.map((b) => {
                  const color    = BANK_COLORS[b.id] || "#6B7280";
                  const isActive = bankFilter === b.id;
                  return (
                    <button
                      key={b.id}
                      className="period-pill"
                      onClick={() => setBankFilter(isActive ? "all" : b.id)}
                      style={isActive ? {
                        background:  color + "33",
                        borderColor: color + "80",
                        color,
                      } : {}}
                    >
                      {BANK_DISPLAY[b.id] || b.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* ══ OVERVIEW ══ */}
        {view === "Overview" && (
          <>
            <div className="stats-grid">
              <StatCard icon="📤" iconBg="rgba(239,68,68,0.12)"
                label="Total Spent"  value={fmtV(totalDebit)}  full={fmtF(totalDebit)}
                change={spendChange} changeLabel="vs prev month" invert />
              <StatCard icon="📥" iconBg="rgba(16,185,129,0.12)"
                label="Total Income" value={fmtV(totalCredit)} full={fmtF(totalCredit)} />
              <StatCard icon="⚡" iconBg="rgba(124,58,237,0.12)"
                label="Net Flow"
                value={(netFlow >= 0 ? "+" : "") + fmtV(Math.abs(netFlow))}
                full={fmtF(netFlow)} positive={netFlow >= 0} />
              <StatCard icon="🔢" iconBg="rgba(6,182,212,0.12)"
                label="Transactions" value={txnCount} full={`${txnCount} total`} />
            </div>

            <div className="charts-row two-col">
              <div className="card">
                <div className="card-title">Monthly Spending</div>
                <div className="card-sub">Debits vs Credits per month</div>
                <SpendingChart data={monthlyData} />
              </div>
              <div className="card">
                <div className="card-title">Spending by Category</div>
                <div className="card-sub">Click a segment or row to drill into transactions</div>
                <CategoryChart data={categoryData} onCategoryClick={handleCategoryClick} />
              </div>
            </div>

            <div className="charts-row two-col">
              <div className="card">
                <div className="card-title">Balance Trend</div>
                <div className="card-sub">Account balance over time</div>
                <BalanceChart data={balanceData} />
              </div>
              <div className="card">
                <div className="card-title">Top Merchants</div>
                <div className="card-sub">Highest spend recipients</div>
                <MerchantChart data={merchantData} />
              </div>
            </div>
          </>
        )}

        {/* ══ TRENDS ══ */}
        {view === "Trends" && (
          <>
            <div className="stats-grid">
              <StatCard icon="🔥" iconBg="rgba(239,68,68,0.12)"
                label="Highest Spend Month"
                value={trendInsights.worstMonth?.label || "—"}
                full={fmtF(trendInsights.worstMonth?.debits || 0)}
                changeLabel={fmtV(trendInsights.worstMonth?.debits || 0) + " spent"} />
              <StatCard icon="✨" iconBg="rgba(16,185,129,0.12)"
                label="Lowest Spend Month"
                value={trendInsights.bestMonth?.label || "—"}
                full={fmtF(trendInsights.bestMonth?.debits || 0)}
                changeLabel={fmtV(trendInsights.bestMonth?.debits || 0) + " spent"} />
              <StatCard icon="📊" iconBg="rgba(124,58,237,0.12)"
                label="Avg Monthly Spend"
                value={fmtV(trendInsights.avg || 0)}
                full={fmtF(trendInsights.avg || 0)}
                changeLabel="per month" />
              <StatCard icon="💰" iconBg="rgba(16,185,129,0.12)"
                label="Savings Rate"
                value={`${(trendInsights.savings || 0).toFixed(1)}%`}
                full={`${(trendInsights.savings || 0).toFixed(2)}%`}
                positive={(trendInsights.savings || 0) >= 0}
                changeLabel="income retained" />
            </div>

            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-title">Spending by Category Over Time</div>
              <div className="card-sub">Monthly breakdown across lifestyle categories (excludes transfers)</div>
              <CategoryTrendChart transactions={transactions} monthlyLabels={monthlyData} />
            </div>

            <div className="charts-row two-col">
              <div className="card">
                <div className="card-title">Monthly Spend vs Income</div>
                <div className="card-sub">Net cash flow per month</div>
                <SpendingChart data={monthlyData} />
              </div>
              <div className="card">
                <div className="card-title">Top Merchants</div>
                <div className="card-sub">Highest spend recipients this period</div>
                <MerchantChart data={merchantData} />
              </div>
            </div>
          </>
        )}

        {/* ══ TRANSACTIONS ══ */}
        {view === "Transactions" && (
          <div className="card">
            <TransactionList
              transactions={transactions}
              activeCategory={activeCategory}
              onClearActiveCategory={() => setActiveCategory(null)}
            />
          </div>
        )}
      </main>
    </div>
  );
}

// ── Stat Card ────────────────────────────────────────────────
function StatCard({ icon, iconBg, label, value, full, change, changeLabel, invert, positive }) {
  const hasChange  = change !== null && change !== undefined;
  const isUp       = change > 0;
  const changeClass = hasChange
    ? (invert ? (isUp ? "down" : "up") : (isUp ? "up" : "down"))
    : "neutral";

  return (
    <div className="stat-card" title={full}>
      <div className="stat-icon" style={{ background: iconBg }}>{icon}</div>
      <div className="stat-label">{label}</div>
      <div
        className="stat-value"
        style={
          positive === false ? { color: "var(--red)"   } :
          positive === true  ? { color: "var(--green)" } : {}
        }
      >
        {value}
      </div>
      {hasChange && (
        <div className={`stat-change ${changeClass}`}>
          <span>{isUp ? "▲" : "▼"}</span>
          <span>{Math.abs(change).toFixed(1)}% {changeLabel}</span>
        </div>
      )}
      {!hasChange && (
        <div className="stat-change neutral">
          <span style={{ color: "var(--text-3)" }}>{changeLabel || "—"}</span>
        </div>
      )}
    </div>
  );
}
