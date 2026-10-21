import type { Lang } from "./dates";

export function formatNumber(v: number, lang: Lang, digits?: number): string {
  const max = digits ?? (Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 10 ? 1 : 2);
  return new Intl.NumberFormat(lang === "ja" ? "ja-JP" : "en-GB", { maximumFractionDigits: max }).format(v);
}

/** Flight level (hundreds of feet) to kilometres, one decimal. */
export function flToKm(fl: number): number {
  return Math.round(fl * 100 * 0.3048) / 1000;
}

export function formatPercent(f: number, lang: Lang): string {
  return `${formatNumber(Math.round(f * 100), lang, 0)}${lang === "ja" ? "%" : " %"}`;
}
