export const CATEGORY_COLORS = {
  "Transfers":           "#6C5CE7",
  "Food & Dining":       "#FF6B6B",
  "Shopping":            "#4ECDC4",
  "Beauty & Wellness":   "#F472B6",
  "Fashion & Apparel":   "#FB923C",
  "Subscriptions":       "#A78BFA",
  "Jewellery":           "#FBBF24",
  "Travel & Transport":  "#38BDF8",
  "Entertainment":       "#34D399",
  "Electronics & Tech":  "#22D3EE",
  "Healthcare":          "#86EFAC",
  "Utilities & Bills":   "#FCD34D",
  "Education":           "#C084FC",
  "Groceries":           "#6EE7B7",
  "Others":              "#6B7280",
};

export const BANK_COLORS = {
  "sbi":         "#7C3AED",
  "sbi_cc":      "#A855F7",
  "chase":       "#1D4ED8",
  "bofa":        "#DC2626",
  "citi":        "#2563EB",
  "wellsfargo":  "#D97706",
  "amex":        "#059669",
  "capitalone":  "#EA580C",
};

export const BANK_DISPLAY = {
  "sbi":         "SBI",
  "sbi_cc":      "SBI Credit",
  "chase":       "Chase",
  "bofa":        "BofA",
  "citi":        "Citi",
  "wellsfargo":  "Wells Fargo",
  "amex":        "Amex",
  "capitalone":  "Capital One",
};

// Currency-aware formatters
const CURRENCY_SYMBOL = { INR: "₹", USD: "$", EUR: "€", GBP: "£" };

export const fmtAmount = (n, currency = "INR") => {
  const sym    = CURRENCY_SYMBOL[currency] || currency + " ";
  const locale = currency === "INR" ? "en-IN" : "en-US";
  return sym + Math.abs(Number(n)).toLocaleString(locale, { maximumFractionDigits: 0 });
};

export const fmtAmountK = (n, currency = "INR") => {
  const sym = CURRENCY_SYMBOL[currency] || currency + " ";
  const abs = Math.abs(n);
  if (currency === "INR") {
    if (abs >= 100000) return sym + (abs / 100000).toFixed(1) + "L";
  } else {
    if (abs >= 1000000) return sym + (abs / 1000000).toFixed(1) + "M";
  }
  if (abs >= 1000) return sym + (abs / 1000).toFixed(1) + "K";
  return sym + abs.toFixed(0);
};

// Keep original INR-specific helpers for backward compat
export const fmt = (n) =>
  "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });

export const fmtK = (n) => {
  if (n >= 100000) return "₹" + (n / 100000).toFixed(1) + "L";
  if (n >= 1000)   return "₹" + (n / 1000).toFixed(1)   + "K";
  return "₹" + n.toFixed(0);
};

export const fmtMonth = (ym) => {
  const [y, m] = ym.split("-");
  const d = new Date(Number(y), Number(m) - 1, 1);
  return d.toLocaleString("en-IN", { month: "short", year: "2-digit" });
};
