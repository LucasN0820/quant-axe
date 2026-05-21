export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function formatChange(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "--";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function changeColorClass(value: number | null | undefined) {
  return (value ?? 0) >= 0 ? "text-market-up" : "text-market-down";
}

export function formatNumber(value: number | string | null | undefined, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  if (typeof value === "string") {
    return value;
  }

  return value.toLocaleString("zh-CN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

export function formatAmount(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  if (typeof value === "string") {
    return value;
  }

  if (value >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(2)}亿`;
  }

  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(2)}万`;
  }

  return value.toLocaleString("zh-CN");
}

export function formatMetric(value: number | string | null | undefined, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  if (typeof value === "string") {
    return value;
  }

  return `${formatNumber(value)}${suffix}`;
}
