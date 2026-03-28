import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { fmtK, CATEGORY_COLORS } from "../utils.js";

// Categories we want to show stacked (exclude Transfers & Others to keep it readable)
const SHOW_CATS = [
  "Food & Dining",
  "Shopping",
  "Fashion & Apparel",
  "Beauty & Wellness",
  "Subscriptions",
  "Travel & Transport",
  "Entertainment",
  "Jewellery",
  "Electronics & Tech",
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const items = [...payload].reverse().filter((p) => p.value > 0);
  return (
    <div style={{
      background: "#111527",
      border: "1px solid rgba(255,255,255,0.12)",
      borderRadius: 10,
      padding: "12px 16px",
      minWidth: 180,
      maxHeight: 280,
      overflowY: "auto",
    }}>
      <div style={{ fontSize: 12, color: "#94A3B8", marginBottom: 8, fontWeight: 600 }}>{label}</div>
      {items.map((p) => (
        <div key={p.name} style={{ display: "flex", justifyContent: "space-between", gap: 16, marginBottom: 3 }}>
          <span style={{ fontSize: 11, color: p.fill || "#94A3B8" }}>{p.name}</span>
          <span style={{ fontSize: 11, fontWeight: 600, color: "#F1F5F9" }}>{fmtK(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

export default function CategoryTrendChart({ transactions, monthlyLabels }) {
  // Build per-month, per-category totals
  const dataMap = {};
  for (const t of transactions) {
    if (t.debit <= 0 || !SHOW_CATS.includes(t.category)) continue;
    const mo = t.date.slice(0, 7);
    if (!dataMap[mo]) dataMap[mo] = {};
    dataMap[mo][t.category] = (dataMap[mo][t.category] || 0) + t.debit;
  }

  const chartData = monthlyLabels.map((m) => ({
    label: m.label,
    ...Object.fromEntries(SHOW_CATS.map((c) => [c, dataMap[m.month]?.[c] || 0])),
  }));

  // Only show categories that have any spend in this period
  const activeCats = SHOW_CATS.filter((c) =>
    chartData.some((d) => d[c] > 0)
  );

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} barCategoryGap="28%">
        <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="label"
          tick={{ fill: "#64748B", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={fmtK}
          tick={{ fill: "#64748B", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Legend
          iconType="circle"
          iconSize={7}
          wrapperStyle={{ fontSize: 11, color: "#94A3B8", paddingTop: 10 }}
        />
        {activeCats.map((cat) => (
          <Bar
            key={cat}
            dataKey={cat}
            stackId="a"
            fill={CATEGORY_COLORS[cat] || "#6B7280"}
            radius={activeCats.indexOf(cat) === activeCats.length - 1 ? [3,3,0,0] : [0,0,0,0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
