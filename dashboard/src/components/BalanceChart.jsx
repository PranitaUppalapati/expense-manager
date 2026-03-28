import React from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { fmtK, fmt } from "../utils.js";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "#111527",
      border: "1px solid rgba(255,255,255,0.12)",
      borderRadius: 10,
      padding: "10px 14px",
    }}>
      <div style={{ fontSize: 12, color: "#94A3B8", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#A78BFA" }}>
        {fmt(payload[0].value)}
      </div>
    </div>
  );
};

export default function BalanceChart({ data }) {
  const max = Math.max(...data.map((d) => d.balance));
  const min = Math.min(...data.map((d) => d.balance));
  const low = data.find((d) => d.balance === min);
  const high = data.find((d) => d.balance === max);

  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#7C3AED" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#7C3AED" stopOpacity={0.0}  />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="month"
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
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(124,58,237,0.3)", strokeWidth: 1 }} />
          <Area
            type="monotone"
            dataKey="balance"
            stroke="#7C3AED"
            strokeWidth={2}
            fill="url(#balGrad)"
            dot={false}
            activeDot={{ r: 5, fill: "#A78BFA", stroke: "#7C3AED", strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>

      <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
        <div className="insight-row" style={{ flex: 1 }}>
          <span className="insight-label">Peak Balance</span>
          <span className="insight-value" style={{ color: "var(--green)" }}>
            {fmtK(max)} <span style={{ fontSize: 11, color: "var(--text-2)" }}>({high?.month})</span>
          </span>
        </div>
        <div className="insight-row" style={{ flex: 1 }}>
          <span className="insight-label">Lowest Balance</span>
          <span className="insight-value" style={{ color: "var(--red)" }}>
            {fmtK(min)} <span style={{ fontSize: 11, color: "var(--text-2)" }}>({low?.month})</span>
          </span>
        </div>
      </div>
    </div>
  );
}
