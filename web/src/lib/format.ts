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

const UNITS_JA: Record<string, string> = { events: "回", pixels: "画素", persons: "人", "t/day": "t/日" };

/** A unit in the page's language (symbols such as MW, FL or µmol/m² stay as they are). */
export function unitLabel(unit: string, lang: Lang): string {
  return lang === "ja" ? (UNITS_JA[unit] ?? unit) : unit;
}

const GVP_TYPES_JA: Record<string, string> = {
  Caldera: "カルデラ",
  Complex: "複合火山",
  Compound: "複成火山",
  "Lava dome": "溶岩ドーム",
  Stratovolcano: "成層火山",
  "Stratovolcano(es)": "成層火山(群)",
};

/** GVP's primary volcano type in the page's language; unknown types are shown as GVP writes them. */
export function volcanoType(type: string, lang: Lang): string {
  return lang === "ja" ? (GVP_TYPES_JA[type] ?? type) : type;
}
