import React from "react";
import { fmtK } from "../utils.js";

const BAR_COLORS = [
  "#7C3AED","#06B6D4","#EC4899","#F59E0B","#10B981",
  "#EF4444","#A78BFA","#38BDF8","#F472B6","#FBBF24",
  "#34D399","#6C5CE7",
];

export default function MerchantChart({ data }) {
  const max = data[0]?.amount || 1;

  return (
    <div className="merchant-list">
      {data.map((m, i) => (
        <div key={m.name} className="merchant-row">
          <div className="merchant-meta">
            <span className="merchant-name" title={m.name}>{m.name}</span>
            <span className="merchant-amt">{fmtK(m.amount)}</span>
          </div>
          <div className="merchant-bar-outer">
            <div
              className="merchant-bar-inner"
              style={{
                width: `${(m.amount / max) * 100}%`,
                background: BAR_COLORS[i % BAR_COLORS.length],
                opacity: 0.8,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
