// Turns a volcano read model into tracks on one shared time axis. Pure functions (unit-tested).
// Safety (RESEARCH.md §9): every track carries its instrument and coverage wording; PHIVOLCS alert levels are
// dated, linked markers "as reported by PHIVOLCS on <date>" and the record ends at the read model's span; nothing
// here describes a present state.

import type { DailySeries, Episode, LocalText, SparseSeries, VolcanoReadModel } from "@contracts/readmodels";

import { addDays, formatDate, toDay } from "@/lib/dates";

export type GroupId = "alert" | "earthquakes" | "so2" | "thermal" | "eruptions" | "ash" | "people" | "other";
export type TrackKind = "line" | "bars" | "markers" | "spans";

export interface TrackPoint {
  date: string;
  /** null on a line: no valid observation that day (a gap, never zero). */
  value: number | null;
  /** Last day of a span (eruptions). */
  end?: string;
  coverage?: number | null;
  url?: string;
  /** Short mark drawn on markers/spans (e.g. "4", "VEI 4"). */
  mark?: string;
  extra?: { label: LocalText; value: string }[];
}

export interface Track {
  id: string;
  group: GroupId;
  kind: TrackKind;
  title: LocalText;
  /** Instrument, platform and its main limitation; shown under the title. */
  instrument: LocalText;
  unit: string;
  sources: string[];
  ringKm?: number;
  /** First day the instrument could report: before it, "not observed"; after it, an empty day means "nothing detected". */
  start?: string;
  /** Last day covered by a daily series (start + length - 1). */
  end?: string;
  points: TrackPoint[];
  coverage: "per-day" | "not-reported" | "not-applicable";
  /** Every point links to its source page (PHIVOLCS, VAAC, DROMIC: Q5 ii). */
  linked: boolean;
  note?: LocalText;
}

export const GROUPS: { id: GroupId; title: LocalText }[] = [
  { id: "alert", title: { en: "Alert levels", ja: "警戒レベル" } },
  { id: "earthquakes", title: { en: "Earthquakes", ja: "地震" } },
  { id: "so2", title: { en: "Sulfur dioxide (SO₂)", ja: "二酸化硫黄(SO₂)" } },
  { id: "thermal", title: { en: "Heat: thermal anomalies and radiative power", ja: "熱:熱異常と放射電力" } },
  { id: "eruptions", title: { en: "Eruptions", ja: "噴火" } },
  { id: "ash", title: { en: "Ash for aviation", ja: "航空向けの火山灰情報" } },
  { id: "people", title: { en: "People", ja: "人々" } },
  { id: "other", title: { en: "Other records", ja: "その他の記録" } },
];

/** Instrument wording per source id (RESEARCH.md §9 rule 3). */
export const INSTRUMENTS: Record<string, LocalText> = {
  "s5p-offl-so2": {
    en: "Sentinel-5P TROPOMI (satellite, early-afternoon overpass, clear days only); a column amount, not a flux",
    ja: "Sentinel-5P TROPOMI(衛星、午後の通過時、晴天日のみ)。放出量ではなくカラム量",
  },
  "omi-omso2e": {
    en: "OMI on Aura (satellite, from Oct 2004, 0.25° cells, clear cells only, partial rows since 2008); a column amount, not a flux",
    ja: "Aura衛星OMI(2004年10月から、0.25°格子、晴天の格子のみ、2008年以降は一部の列が欠測)。放出量ではなくカラム量",
  },
  "modis-mod14a1": { en: "MODIS on Terra (satellite, 1 km daily); may include vegetation fires", ja: "Terra衛星MODIS(1 km、日別)。植生火災を含む場合あり" },
  "viirs-vnp14a1": { en: "VIIRS on S-NPP (satellite, 1 km daily); may include vegetation fires", ja: "S-NPP衛星VIIRS(1 km、日別)。植生火災を含む場合あり" },
  "firms-modis": { en: "NASA FIRMS active-fire detections (satellite); may include vegetation fires", ja: "NASA FIRMS 熱異常検知(衛星)。植生火災を含む場合あり" },
  "firms-viirs-noaa20": {
    en: "VIIRS on NOAA-20 via NASA FIRMS (satellite, 375 m, from Apr 2018; its own series, not joined to S-NPP); may include vegetation fires",
    ja: "NOAA-20衛星VIIRS(NASA FIRMS経由、375 m、2018年4月から。S-NPPとは接続しない独立系列)。植生火災を含む場合あり",
  },
  "usgs-comcat-ph-2010": { en: "USGS ComCat (global network; small local earthquakes are missed)", ja: "USGS ComCat(全球観測網。小さな地元の地震は捉えられない)" },
  "usgs-comcat-ph-1900-2009": { en: "USGS ComCat (global network; small local earthquakes are missed)", ja: "USGS ComCat(全球観測網。小さな地元の地震は捉えられない)" },
  "landsat-surface-temperature": { en: "Landsat thermal band (satellite, every 8–16 days, clear scenes only)", ja: "Landsat熱赤外バンド(衛星、8〜16日ごと、晴天時のみ)" },
  "phivolcs-bulletins": { en: "DOST-PHIVOLCS bulletins, each linked; ground observations", ja: "DOST-PHIVOLCSの火山情報(各リンク付き)。地上観測" },
  "phivolcs-lava-bulletins": { en: "DOST-PHIVOLCS LAVA bulletins, each linked; ground observations", ja: "DOST-PHIVOLCS LAVA火山情報(各リンク付き)。地上観測" },
  "vaac-tokyo-advisories": { en: "Tokyo VAAC advisories for aviation (JMA), each linked; satellite and pilot reports", ja: "東京VAAC航空路火山灰情報(気象庁、各リンク付き)。衛星とパイロット報告" },
  "dswd-dromic-reports": { en: "DSWD DROMIC reports, each linked; counts as reported on each date", ja: "DSWD DROMIC報告(各リンク付き)。各日付時点の報告値" },
  "gvp-eruptions-ph": { en: "Smithsonian Global Volcanism Program; dates can be uncertain", ja: "スミソニアン博物館GVP。日付に不確かさあり" },
  "nasa-msvolso2l4": { en: "NASA MEaSUREs multi-satellite SO₂ mass per eruption", ja: "NASA MEaSUREs 多衛星による噴火ごとのSO₂量" },
  "gpm-imerg-v07": { en: "NASA GPM IMERG Final (satellites merged with gauges, 0.1° grid, UTC days); an area estimate, not a rain gauge", ja: "NASA GPM IMERG Final(複数衛星と雨量計の統合、0.1°格子、UTC日)。雨量計ではなく面的な推定" },
};

function instrumentOf(sources: string[]): LocalText {
  const known = sources.map((s) => INSTRUMENTS[s]).filter((x): x is LocalText => !!x);
  if (known.length) return { en: known.map((k) => k.en).join("; "), ja: known.map((k) => k.ja).join("。") };
  return { en: `Source: ${sources.join(", ")}`, ja: `出典:${sources.join("、")}` };
}

/** The family of a series id: the id without its ring ("so2_s5p_15km" -> "so2_s5p"). */
export function familyOf(id: string): string {
  return id.replace(/_\d+km$/, "").replace(/_box$/, "");
}

function groupOf(id: string): GroupId {
  if (id.startsWith("so2")) return "so2";
  if (id.startsWith("eq")) return "earthquakes";
  if (id.startsWith("frp") || id.startsWith("fire")) return "thermal";
  return "other";
}

/** Ring radii (km) offered by this read model's series. */
export function ringOptions(model: VolcanoReadModel): number[] {
  const rings = new Set<number>();
  for (const s of [...Object.values(model.daily), ...Object.values(model.events)]) if (s.ringKm) rings.add(s.ringKm);
  return [...rings].sort((a, b) => a - b);
}

/** Pick one series per family: the one at `ring`, else the nearest ring. */
export function pickByRing<T extends { ringKm?: number }>(entries: [string, T][], ring: number | null): [string, T][] {
  const byFamily = new Map<string, [string, T][]>();
  for (const e of entries) {
    const f = familyOf(e[0]);
    byFamily.set(f, [...(byFamily.get(f) ?? []), e]);
  }
  const out: [string, T][] = [];
  for (const list of byFamily.values()) {
    if (list.length === 1 || ring == null) {
      out.push(list[0]!);
      continue;
    }
    const best = [...list].sort((a, b) => Math.abs((a[1].ringKm ?? 0) - ring) - Math.abs((b[1].ringKm ?? 0) - ring) || (a[1].ringKm ?? 0) - (b[1].ringKm ?? 0))[0]!;
    out.push(best);
  }
  return out;
}

export function dailyTrack(id: string, s: DailySeries): Track {
  const points: TrackPoint[] = s.values.map((v, i) => ({ date: addDays(s.start, i), value: v, coverage: s.coverage?.[i] ?? undefined }));
  return {
    id,
    group: groupOf(id),
    kind: "line",
    title: s.label,
    instrument: instrumentOf(s.source),
    unit: s.unit,
    sources: s.source,
    ringKm: s.ringKm,
    start: s.start,
    end: addDays(s.start, s.values.length - 1),
    points,
    coverage: s.coverage ? "per-day" : "not-reported",
    linked: false,
    note: s.note,
  };
}

/** Readout labels of the extra columns of event series. */
const COLUMN_LABELS: Record<string, LocalText> = {
  n: { en: "count", ja: "件数" },
  maxMag: { en: "largest magnitude", ja: "最大マグニチュード" },
  maxFrpMw: { en: "max radiative power", ja: "最大放射電力" },
  nVolcano: { en: "flagged volcanic by FIRMS", ja: "FIRMSの火山フラグ" },
};

export function eventsTrack(id: string, s: SparseSeries): Track {
  // The first numeric column is drawn; the others go into the readout.
  const valueCol = s.cols.find((_, i) => i > 0 && s.rows.some((r) => typeof r[i] === "number")) ?? s.cols[1] ?? "value";
  const vi = s.cols.indexOf(valueCol);
  const points: TrackPoint[] = s.rows.map((r) => ({
    date: r[0],
    value: typeof r[vi] === "number" ? (r[vi] as number) : null,
    extra: s.cols
      .map((c, i) => [c, i] as const)
      .filter(([c, i]) => i > 0 && c !== valueCol && r[i] != null)
      .map(([c, i]) => ({ label: COLUMN_LABELS[c] ?? { en: c, ja: c }, value: `${r[i]}${s.units[c] ? ` ${s.units[c]}` : ""}` })),
  }));
  return {
    id,
    group: groupOf(id),
    kind: "bars",
    title: s.label,
    instrument: instrumentOf(s.source),
    unit: s.units[valueCol] ?? "",
    sources: s.source,
    ringKm: s.ringKm,
    start: s.start,
    points,
    coverage: "not-applicable",
    linked: false,
    note: s.note,
  };
}

/** Partial GVP dates to a day: "1911" -> "1911-01-01", "2020-01" -> "2020-01-01". */
export function dayOf(partial: string): string {
  if (/^-?\d{1,5}$/.test(partial)) return `${partial.padStart(4, "0")}-01-01`;
  if (/^\d{4}-\d{2}$/.test(partial)) return `${partial}-01`;
  return partial.slice(0, 10);
}

export function buildTracks(model: VolcanoReadModel, ring: number | null): Track[] {
  const tracks: Track[] = [];
  const b = model.bulletins;
  if (b && b.rows.length) {
    const alert = b.rows.filter((r) => r[1] != null);
    if (alert.length)
      tracks.push({
        id: "alert",
        group: "alert",
        kind: "markers",
        title: { en: "Alert level, as reported by PHIVOLCS on each date", ja: "警戒レベル(各日付にPHIVOLCSが発表したもの)" },
        instrument: instrumentOf(b.source),
        unit: "",
        sources: b.source,
        points: alert.map((r) => ({ date: r[0], value: r[1], url: r[8], mark: String(r[1]) })),
        coverage: "not-applicable",
        linked: true,
      });
    const eq = b.rows.filter((r) => r[2] != null);
    if (eq.length)
      tracks.push({
        id: "bulletin_eq",
        group: "earthquakes",
        kind: "markers",
        title: { en: "Volcanic earthquakes per bulletin (PHIVOLCS)", ja: "火山性地震の回数(PHIVOLCS発表ごと)" },
        instrument: instrumentOf(b.source),
        unit: "events",
        sources: b.source,
        points: eq.map((r) => ({ date: r[0], value: r[2], url: r[8], mark: String(r[2]) })),
        coverage: "not-applicable",
        linked: true,
      });
    const flux = b.rows.filter((r) => r[4] != null);
    if (flux.length)
      tracks.push({
        id: "bulletin_so2",
        group: "so2",
        kind: "markers",
        title: { en: "SO₂ flux, PHIVOLCS (ground, t/day)", ja: "SO₂放出量(PHIVOLCS、地上観測、t/日)" },
        instrument: instrumentOf(b.source),
        unit: "t/day",
        sources: b.source,
        points: flux.map((r) => ({ date: r[5] ?? r[0], value: r[4], url: r[8], mark: String(r[4]) })),
        coverage: "not-applicable",
        linked: true,
      });
  }
  for (const [id, s] of pickByRing(Object.entries(model.events).filter(([id]) => id.startsWith("eq")), ring)) tracks.push(eventsTrack(id, s));
  for (const [id, s] of pickByRing(Object.entries(model.daily), ring)) tracks.push(dailyTrack(id, s));
  for (const [id, s] of pickByRing(Object.entries(model.events).filter(([id]) => !id.startsWith("eq")), ring)) tracks.push(eventsTrack(id, s));

  const eruptions = model.episodes.filter((e) => e.kind === "gvp_eruption");
  if (eruptions.length)
    tracks.push({
      id: "eruptions",
      group: "eruptions",
      kind: "spans",
      title: { en: "Eruptions (GVP), with VEI", ja: "噴火(GVP)と火山爆発指数VEI" },
      instrument: instrumentOf([...new Set(eruptions.flatMap((e) => e.source))]),
      unit: "",
      sources: [...new Set(eruptions.flatMap((e) => e.source))],
      points: eruptions.map((e) => episodePoint(e)),
      coverage: "not-applicable",
      linked: true,
    });

  const adv = model.advisories;
  if (adv && adv.rows.length) {
    const byDay = new Map<string, TrackPoint>();
    for (const r of adv.rows) {
      const day = r[0].slice(0, 10);
      const cur = byDay.get(day);
      const n = (Number(cur?.extra?.[0]?.value) || 0) + 1;
      const top = r[2];
      const higher = top != null && (cur?.value == null || top > cur.value);
      byDay.set(day, {
        date: day,
        value: higher ? top : (cur?.value ?? null),
        url: higher || !cur ? r[4] : cur.url,
        mark: higher ? `FL${top}` : cur?.mark,
        extra: [{ label: { en: "advisories", ja: "情報数" }, value: String(n) }],
      });
    }
    tracks.push({
      id: "advisories",
      group: "ash",
      kind: "markers",
      title: { en: "Highest ash top in VAAC advisories (flight level)", ja: "VAAC情報の火山灰最高高度(フライトレベル)" },
      instrument: instrumentOf(adv.source),
      unit: "FL",
      sources: adv.source,
      points: [...byDay.values()],
      coverage: "not-applicable",
      linked: true,
    });
  }

  const dis = model.displacement;
  if (dis && dis.rows.length)
    tracks.push({
      id: "displacement",
      group: "people",
      kind: "markers",
      title: { en: "People affected, as reported by DSWD", ja: "被災者数(DSWD報告)" },
      instrument: instrumentOf(dis.source),
      unit: "persons",
      sources: dis.source,
      points: dis.rows.map((r) => ({
        date: r[0].slice(0, 10),
        value: r[2],
        url: r[7],
        mark: r[2] != null ? compact(r[2]) : undefined,
        extra: [
          { label: { en: "report", ja: "報告" }, value: `#${r[1]}` },
          ...(r[3] != null ? [{ label: { en: "inside evacuation centres", ja: "避難所内" }, value: String(r[3]) }] : []),
          ...(r[5] != null ? [{ label: { en: "outside evacuation centres", ja: "避難所外" }, value: String(r[5]) }] : []),
        ],
      })),
      coverage: "not-applicable",
      linked: true,
    });

  const order = GROUPS.map((g) => g.id);
  return tracks.sort((a, b) => order.indexOf(a.group) - order.indexOf(b.group));
}

function episodePoint(e: Episode): TrackPoint {
  const extra: TrackPoint["extra"] = [];
  if (e.so2MassKt != null) extra.push({ label: { en: "SO₂ mass (MSVOLSO2L4)", ja: "SO₂量(MSVOLSO2L4)" }, value: `${e.so2MassKt} kt` });
  if (e.plumeAltKm != null) extra.push({ label: { en: "plume altitude", ja: "噴煙高度" }, value: `${e.plumeAltKm} km` });
  return { date: dayOf(e.start), end: e.end ? dayOf(e.end) : undefined, value: e.vei ?? null, url: e.url, mark: e.vei != null ? `VEI ${e.vei}` : "VEI ?", extra };
}

export type Reading =
  | { status: "value"; point: TrackPoint; reportedOn?: string }
  | { status: "no-observation" }
  | { status: "nothing-detected" }
  | { status: "not-observed" }
  | { status: "no-report" }
  | { status: "outside" };

/** What a track says about one day. */
export function readAt(track: Track, date: string): Reading {
  const d = toDay(date);
  if (track.kind === "line") {
    if (!track.start || d < toDay(track.start) || (track.end && d > toDay(track.end))) return { status: "outside" };
    const p = track.points[d - toDay(track.start)];
    return p && p.value != null ? { status: "value", point: p } : { status: "no-observation" };
  }
  if (track.kind === "spans") {
    const p = track.points.find((x) => toDay(x.date) <= d && d <= toDay(x.end ?? x.date));
    return p ? { status: "value", point: p } : { status: "no-report" };
  }
  if (track.id === "alert") {
    // The level in force is not inferred: show the last level PHIVOLCS reported on or before this day, with its date.
    const prior = track.points.filter((p) => toDay(p.date) <= d).at(-1);
    return prior ? { status: "value", point: prior, reportedOn: prior.date } : { status: "no-report" };
  }
  const p = track.points.find((x) => x.date === date);
  if (p) return { status: "value", point: p };
  if (track.kind === "bars") {
    if (track.start && d < toDay(track.start)) return { status: "not-observed" };
    return { status: "nothing-detected" };
  }
  return { status: "no-report" };
}

/** Non-null values of a track inside [from, to]. */
export function valuesIn(track: Track, from: string, to: string): number[] {
  const a = toDay(from);
  const b = toDay(to);
  return track.points.filter((p) => p.value != null && toDay(p.date) <= b && toDay(p.end ?? p.date) >= a).map((p) => p.value as number);
}

/** Valid-observation share of a line track inside [from, to] (days with a value / days covered by the series). */
export function observedShare(track: Track, from: string, to: string): number | null {
  if (track.kind !== "line" || !track.start || !track.end) return null;
  const a = Math.max(toDay(from), toDay(track.start));
  const b = Math.min(toDay(to), toDay(track.end));
  if (b < a) return null;
  let n = 0;
  for (let d = a; d <= b; d++) if (track.points[d - toDay(track.start)]?.value != null) n++;
  return n / (b - a + 1);
}

/** Track ids a story step's `series` names ("bulletins" covers every bulletin-derived track). */
export function tracksForStep(step: { series: string[] }, tracks: Track[]): Track[] {
  const want = new Set(step.series);
  return tracks.filter((t) => want.has(t.id) || (want.has("bulletins") && (t.id === "alert" || t.id.startsWith("bulletin_"))));
}


export interface AbsentRecord {
  id: string;
  title: LocalText;
  /** Why this volcano has nothing in the series: the specific reason, never a generic "no record". */
  reason: LocalText;
}

/** Series this volcano's record has nothing in, each with the reason (shown under the time axis). */
export function absentRecords(model: VolcanoReadModel, tracks: Track[]): AbsentRecord[] {
  const out: AbsentRecord[] = [];
  const asOf = model.dataAsOf;
  const b = model.bulletins;
  if (!b || !b.rows.length)
    out.push({
      id: "bulletins",
      title: { en: "PHIVOLCS bulletins (alert levels, volcanic earthquakes, SO₂ flux)", ja: "PHIVOLCSの火山情報(警戒レベル、火山性地震、SO₂放出量)" },
      reason: {
        en: "None issued for this volcano in the record: PHIVOLCS publishes daily bulletins for its observatory volcanoes and during unrest. Plumes reads the English bulletins from September 2017 and the LAVA bulletins from July 2022.",
        ja: "記録の期間にこの火山の火山情報は発表されていない。PHIVOLCSの日々の火山情報は観測所のある火山と活動時のみ。Plumesは2017年9月からの英語版と2022年7月からのLAVA版を読んでいる。",
      },
    });
  else {
    if (!b.rows.some((r) => r[2] != null))
      out.push({ id: "bulletin_eq", title: { en: "Volcanic earthquakes per bulletin (PHIVOLCS)", ja: "火山性地震の回数(PHIVOLCS)" }, reason: { en: "No bulletin in the record reports a volcanic-earthquake count.", ja: "記録中の火山情報に火山性地震の回数の記載がない。" } });
    if (!b.rows.some((r) => r[4] != null))
      out.push({ id: "bulletin_so2", title: { en: "SO₂ flux, PHIVOLCS (ground)", ja: "SO₂放出量(PHIVOLCS、地上観測)" }, reason: { en: "No bulletin in the record reports an SO₂ flux.", ja: "記録中の火山情報にSO₂放出量の記載がない。" } });
  }
  if (!model.advisories || !model.advisories.rows.length)
    out.push({
      id: "advisories",
      title: { en: "Volcanic ash advisories (Tokyo VAAC)", ja: "航空路火山灰情報(東京VAAC)" },
      reason:
        model.volcano.gvpNumber == null
          ? { en: "Advisories name volcanoes by their GVP number, and this volcano has none, so none can be matched to it.", ja: "火山灰情報はGVP番号で火山を示すが、この火山には番号がないため対応する情報はない。" }
          : { en: "Tokyo VAAC issued no advisory for this volcano from 2010 (the start of the archive Plumes reads) to the data date.", ja: "東京VAACは2010年(Plumesが読む記録の開始)からデータの最終日まで、この火山の情報を発表していない。" },
    });
  if (!model.episodes.some((e) => e.kind === "gvp_eruption"))
    out.push({
      id: "eruptions",
      title: { en: "Eruptions (GVP)", ja: "噴火(GVP)" },
      reason:
        model.volcano.gvpNumber == null
          ? { en: "Not in the Smithsonian GVP list of Holocene volcanoes, so there is no GVP eruption history for it.", ja: "スミソニアン博物館GVPの完新世火山の一覧にないため、GVPの噴火史はない。" }
          : { en: "The Smithsonian GVP lists this volcano but records no dated eruption for it.", ja: "スミソニアン博物館GVPはこの火山を掲載しているが、年代のある噴火の記録はない。" },
    });
  if (!model.displacement || !model.displacement.rows.length)
    out.push({
      id: "displacement",
      title: { en: "People affected (DSWD DROMIC)", ja: "被災者数(DSWD DROMIC)" },
      reason: { en: "This data version carries DSWD DROMIC figures for the Taal eruption of January 2020 only.", ja: "このデータ版のDSWD DROMICの数値は2020年1月のタール火山噴火のみ。" },
    });
  for (const t of tracks)
    if (t.kind === "bars" && !t.points.length)
      out.push({
        id: t.id,
        title: t.title,
        reason: {
          en: `Nothing detected${t.ringKm ? ` within ${t.ringKm} km` : ""} from ${formatDate(t.start ?? model.span.start, "en")}, when the instrument record starts, to ${formatDate(asOf, "en")}.`,
          ja: `観測記録の始まる${formatDate(t.start ?? model.span.start, "ja")}から${formatDate(asOf, "ja")}まで、${t.ringKm ? `${t.ringKm} km圏で` : ""}検知なし。`,
        },
      });
  return out;
}

/** 504265 -> "504k", 38203 -> "38k", 950 -> "950". */
export function compact(n: number): string {
  if (Math.abs(n) >= 1e6) return `${Math.round(n / 1e5) / 10}M`;
  if (Math.abs(n) >= 1e4) return `${Math.round(n / 1e3)}k`;
  if (Math.abs(n) >= 1e3) return `${Math.round(n / 100) / 10}k`;
  return String(n);
}
