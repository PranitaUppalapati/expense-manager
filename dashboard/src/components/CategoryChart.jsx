import React, { useState } from "react";
import { PieChart, Pie, Cell, Tooltip } from "recharts";
import { fmt, fmtK, CATEGORY_COLORS } from "../utils.js";

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div style={{
      background: "#111527",
      border: "1px solid rgba(255,255,255,0.12)",
      borderRadius: 10,
      padding: "10px 14px",
    }}>
      <div style={{ fontSize: 12, color: d.payload.fill, fontWeight: 600 }}>{d.name}</div>
      <div style={{ fontSize: 13, color: "#F1F5F9", marginTop: 4 }}>{fmt(d.value)}</div>
      <div style={{ fontSize: 11, color: "#94A3B8" }}>{d.payload.pct}% of total</div>
      <div style={{ fontSize: 10, color: "#475569", marginTop: 5 }}>↗ click to view transactions</div>
    </div>
  );
};

export default function CategoryChart({ data, onCategoryClick }) {
  const [active, setActive] = useState(null);
  const total = data.reduce((s, d) => s + d.amount, 0);

  const chartData = data.map((d) => ({
    name: d.category,
    value: d.amount,
    fill: CATEGORY_COLORS[d.category] || "#6B7280",
    pct: ((d.amount / total) * 100).toFixed(1),
  }));

  const handleSegmentClick = (_, index) => {
    onCategoryClick?.(chartData[index]?.name);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <PieChart width={200} height={200}>
          <Pie
            data={chartData}
            cx={100}
            cy={100}
            innerRadius={62}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
            style={{ cursor: "pointer" }}
            onMouseEnter={(_, i) => setActive(i)}
            onMouseLeave={() => setActive(null)}
            onClick={handleSegmentClick}
          >
            {chartData.map((d, i) => (
              <Cell
                key={d.name}
                fill={d.fill}
                opacity={active === null || active === i ? 1 : 0.35}
                stroke={active === i ? d.fill : "none"}
                strokeWidth={active === i ? 2 : 0}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </div>

      {/* Donut centre label */}
      <div style={{ textAlign: "center", marginTop: -12, marginBottom: 8 }}>
        <div style={{ fontSize: 11, color: "#64748B" }}>Total spent</div>
        <div style={{ fontSize: 17, fontWeight: 700, color: "#F1F5F9" }}>{fmtK(total)}</div>
      </div>

      {/* Legend */}
      <div className="cat-legend">
        {chartData.map((d, i) => (
          <div
            key={d.name}
            className="cat-row"
            style={{
              opacity: active === null || active === i ? 1 : 0.5,
              cursor: "pointer",
            }}
            onMouseEnter={() => setActive(i)}
            onMouseLeave={() => setActive(null)}
            onClick={() => onCategoryClick?.(d.name)}
          >
            <span className="cat-dot" style={{ background: d.fill }} />
            <span className="cat-name">{d.name}</span>
            <span className="cat-pct">{d.pct}%</span>
            <div className="cat-bar-outer">
              <div
                className="cat-bar-inner"
                style={{ width: d.pct + "%", background: d.fill }}
              />
            </div>
            <span className="cat-amt">{fmtK(d.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
