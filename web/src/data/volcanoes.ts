import type { VolcanoesIndex } from "@contracts/readmodels";

import { dayOf } from "./tracks";

type Feature = VolcanoesIndex["features"][number];

/** Most recent GVP eruption first; volcanoes without a dated eruption last, by name. */
export function sortVolcanoes(features: Feature[], lang: "en" | "ja"): Feature[] {
  return [...features].sort((a, b) => {
    const ea = a.properties.lastEruption?.start ? dayOf(a.properties.lastEruption.start) : "";
    const eb = b.properties.lastEruption?.start ? dayOf(b.properties.lastEruption.start) : "";
    if (ea !== eb) return ea < eb ? 1 : -1;
    return a.properties.name[lang].localeCompare(b.properties.name[lang]);
  });
}

export function filterVolcanoes(features: Feature[], q: string): Feature[] {
  const s = q.trim().toLowerCase();
  if (!s) return features;
  return features.filter((f) => f.properties.name.en.toLowerCase().includes(s) || f.properties.name.ja.includes(q.trim()) || f.properties.id.includes(s));
}

