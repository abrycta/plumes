// Dated event markers on the timeline's value rows (LAYERS-PLAN §6), drawn with Akari's event markers.
// Pure: derived from the tracks already on the page, so a marker appears only where its data is shown.

import type { EventMarker } from "@abrycta/akari/react";

import { familyOf, type Track } from "@/data/tracks";

type Lang = "en" | "ja";

/** S-NPP VIIRS deliveries stop on this day; NOAA-20 VIIRS continues as its own series (L5), never spliced in. */
export const SNPP_END = "2026-11-02";

const VIIRS = /^(fire|frp)_viirs/;
const ERUPTION_ROWS = /^(los_|rain_)/; // deformation and rain charts carry GVP eruption dates
const LAKE = /^lake_/;
const SO2 = { omi: /^so2_omi/, s5p: /^so2_s5p/ };

const lastDay = (t: Track) => t.end ?? [...t.points].reverse().find((p) => p.value != null)?.date;

/** Markers for one value track, from the other tracks on the page. Span ends are inclusive (the last day). */
export function markersFor(track: Track, tracks: readonly Track[], lang: Lang): EventMarker[] {
  if (track.kind !== "line" && track.kind !== "bars") return [];
  const fam = familyOf(track.id);
  const out: EventMarker[] = [];

  if (VIIRS.test(fam))
    out.push({
      at: SNPP_END,
      label: "NOAA-20",
      kind: "sensor-change",
      description: lang === "ja" ? "S-NPP VIIRSの配信終了。以後はNOAA-20 VIIRSを別系列で表示" : "S-NPP VIIRS deliveries end; NOAA-20 VIIRS continues as its own series",
    });

  if (ERUPTION_ROWS.test(fam))
    for (const t of tracks.filter((x) => x.kind === "spans" && x.group === "eruptions"))
      for (const p of t.points)
        out.push({
          at: p.date,
          ...(p.end && p.end > p.date ? { end: p.end } : {}),
          label: lang === "ja" ? "噴火" : "Eruption",
          description: `${lang === "ja" ? "噴火(GVP)" : "Eruption (GVP)"}${p.mark ? `, ${p.mark}` : ""}`,
        });

  if (LAKE.test(fam)) {
    const area = tracks.find((x) => familyOf(x.id) === "lake_area" && x.kind === "line");
    let start: string | null = null;
    let last = "";
    for (const p of area?.points ?? []) {
      if (p.value === 0) {
        start ??= p.date;
        last = p.date;
      } else if (p.value != null && start) {
        out.push(lakeGone(start, last, lang));
        start = null;
      }
    }
    if (start) out.push(lakeGone(start, last, lang));
  }

  if (SO2.omi.test(fam) || SO2.s5p.test(fam)) {
    const omi = tracks.find((x) => SO2.omi.test(familyOf(x.id)) && x.start);
    const s5p = tracks.find((x) => SO2.s5p.test(familyOf(x.id)) && x.start);
    const [a, b] = [omi && lastDay(omi), s5p && lastDay(s5p)];
    if (omi?.start && s5p?.start && a && b) {
      const from = omi.start > s5p.start ? omi.start : s5p.start;
      const to = a < b ? a : b;
      if (from <= to)
        out.push({
          at: from,
          end: to,
          label: "OMI + TROPOMI",
          description: lang === "ja" ? "OMIとTROPOMIの観測が重なる期間(別々に表示)" : "OMI and TROPOMI overlap (shown separately, not merged)",
        });
    }
  }
  return out;
}

function lakeGone(at: string, end: string, lang: Lang): EventMarker {
  return { at, end, kind: "gap", label: lang === "ja" ? "湖なし" : "Lake gone", description: lang === "ja" ? "火口湖が消失していた期間" : "Crater lake gone" };
}
