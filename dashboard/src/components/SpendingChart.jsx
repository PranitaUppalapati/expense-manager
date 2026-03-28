import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { fmtK } from "../utils.js";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#111527",
      border: "1px solid rgba(255,255,255,0.12)",
      borderRadius: 10,
      padding: "12px 16px",
      minWidth: 160,
    }}>
      <div style={{ fontSize: 12, color: "#94A3B8", marginBottom: 8 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ display: "flex", justifyContent: "space-between", gap: 20, marginBottom: 4 }}>
          <span style={{ fontSize: 12, color: p.color }}>{p.name}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: "#F1F5F9" }}>
            {fmtK(p.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function SpendingChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} barGap={3} barCategoryGap="30%">
        <defs>
          <linearGradient id="debitGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#EF4444" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#EF4444" stopOpacity={0.4} />
          </linearGradient>
          <linearGradient id="creditGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10B981" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#10B981" stopOpacity={0.4} />
          </linearGradient>
        </defs>
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
          iconSize={8}
          wrapperStyle={{ fontSize: 12, color: "#94A3B8", paddingTop: 12 }}
        />
        <Bar dataKey="debits" name="Spent" fill="url(#debitGrad)"  radius={[4,4,0,0]} />
        <Bar dataKey="credits" name="Income" fill="url(#creditGrad)" radius={[4,4,0,0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
