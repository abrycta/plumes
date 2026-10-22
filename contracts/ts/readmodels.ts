// Plumes read models: TypeScript mirror of contracts/schemas/*.schema.json (schemaVersion "1").
// The JSON Schemas are the source of truth; the pipeline validates every published file against them.
// A historical record only: no type here represents a "current" status (DECISIONS Q14).

export type ISODate = string; // YYYY-MM-DD
export type ISOMonth = string; // YYYY-MM
export type SourceId = string; // an id in pipeline/sources.yaml
export type DataVersion = `v${number}`;

export interface LocalText {
  en: string;
  ja: string;
}

export interface Header {
  schemaVersion: "1";
  dataVersion: DataVersion;
  /** Snapshot date: the record ends here. Label it "as reported on <date>", never "current". */
  dataAsOf: ISODate;
  generatedAt: string;
  fixture?: boolean;
}

/** One cited number. PHIVOLCS, VAAC and DROMIC figures always carry `url` (Q5 ii). */
export interface Figure {
  label: LocalText;
  value: number | string;
  unit?: string;
  source: SourceId;
  url?: string;
  asOf?: ISODate;
  note?: LocalText;
  /** Whose number a second-hand figure is (e.g. "PHIVOLCS" via a weekly report). */
  reportedBy?: string;
}

export interface Asset {
  kind: "image";
  /** Relative to the data version root. */
  url: string;
  date: ISODate;
  sensor?: string;
  source?: SourceId;
  caption?: LocalText;
  credit: string;
  width?: number;
  height?: number;
  /** Pairs a story's before and after images. */
  role?: "before" | "after";
}

export interface Provenance {
  sources: {
    id: SourceId;
    attribution: string;
    licence: string;
    link?: string;
    snapshotDate?: ISODate;
    /** true: show "data as of <snapshotDate>" */
    fromArchive?: boolean;
    url?: string;
  }[];
  earthEngine?: { assets?: string[]; eecuSeconds?: number };
  commit?: string;
}

// ---------- latest.json and <version>/manifest.json ----------

export interface Latest {
  schemaVersion: "1";
  kind: "latest";
  current: DataVersion;
  /** e.g. "v3/": every other file is fetched relative to this. */
  base: string;
  dataAsOf: ISODate;
  generatedAt: string;
  previous?: string | null;
  mirrors?: string[];
  fixture?: boolean;
}

export interface Manifest extends Header {
  kind: "manifest";
  files: { path: string; bytes: number; sha256: string }[];
  checks: { passed: boolean; results?: Record<string, unknown>[] };
  provenance?: Provenance;
  archivekit?: Record<string, unknown>;
}

// ---------- <version>/volcanoes.geojson ----------

export type Coverage = "deep" | "satellite";

export interface VolcanoFeatureProps {
  id: string;
  name: LocalText;
  gvpNumber?: number | null;
  elevationM?: number | null;
  observatory: boolean;
  coverage: Coverage;
  lastEruption?: { start: string; vei?: number | null } | null;
  eruptionsSince1900?: number;
  eruptionsSince2000?: number;
  /** Per-month summaries for the scrubber; values[i] is month start + i. */
  monthly?: Record<string, { start: ISOMonth; values: (number | null)[] }>;
  /** Per-volcano read model, relative to the version root. */
  file: string;
}

export interface VolcanoesIndex extends Header {
  type: "FeatureCollection";
  kind: "volcanoes";
  features: {
    type: "Feature";
    id?: string;
    geometry: { type: "Point"; coordinates: [number, number] | [number, number, number] };
    properties: VolcanoFeatureProps;
  }[];
}

// ---------- <version>/volcano/<id>.json ----------

export interface Volcano {
  id: string;
  gvpNumber?: number | null;
  gvpName?: string | null;
  name: LocalText;
  lat: number;
  lon: number;
  elevationM?: number | null;
  type?: string | null;
  observatory: boolean;
  coverage: Coverage;
  links: { phivolcs?: string; gvp?: string; comet?: string; hazardhunter?: string };
}

/** values[i] is the value for start + i days; null = no valid observation. */
export interface DailySeries {
  source: SourceId[];
  unit: string;
  label: LocalText;
  start: ISODate;
  ringKm?: number;
  values: (number | null)[];
  /** Valid-pixel fraction 0..1 per day, same length as values. */
  coverage?: (number | null)[];
  note?: LocalText;
}

/** rows[k][0] is an ISO date; the rest follow cols. */
export interface SparseSeries {
  source: SourceId[];
  label: LocalText;
  cols: ["date", ...string[]];
  units: Record<string, string>;
  ringKm?: number;
  /** First day the instrument could report. */
  start?: ISODate;
  /** Last day the source covers: later days are not observed, never "nothing detected". */
  end?: ISODate;
  rows: [ISODate, ...(number | string | null)[]][];
  note?: LocalText;
}

export type BulletinRow = [
  date: ISODate,
  alertLevel: number | null,
  volcanicEq: number | null,
  tremor: number | null,
  so2FluxTpd: number | null,
  so2FluxDate: ISODate | null,
  plumeM: number | null,
  deformation: string | null,
  url: string,
];

export interface Bulletins {
  source: SourceId[];
  authority: "DOST-PHIVOLCS";
  cols: ["date", "alertLevel", "volcanicEq", "tremor", "so2FluxTpd", "so2FluxDate", "plumeM", "deformation", "url"];
  rows: BulletinRow[];
  gaps?: { start: string; end: string; reason: LocalText }[];
}

export type AdvisoryRow = [
  dtg: string,
  advisoryNo: string,
  topFl: number | null,
  heightBasis: "observed" | "reported" | "none",
  url: string,
];

export interface Advisories {
  source: SourceId[];
  cols: ["dtg", "advisoryNo", "topFl", "heightBasis", "url"];
  rows: AdvisoryRow[];
}

export type DisplacementRow = [
  asOf: string,
  report: string,
  affectedPersons: number | null,
  insidePersonsNow: number | null,
  insidePersonsCum: number | null,
  outsidePersonsNow: number | null,
  outsidePersonsCum: number | null,
  url: string,
];

export interface Displacement {
  source: SourceId[];
  cols: ["asOf", "report", "affectedPersons", "insidePersonsNow", "insidePersonsCum", "outsidePersonsNow", "outsidePersonsCum", "url"];
  rows: DisplacementRow[];
}

export interface Episode {
  id: string;
  kind: "gvp_eruption" | "alert_window" | "strong_degassing";
  /** YYYY, YYYY-MM or YYYY-MM-DD (GVP dates can be partial). */
  start: string;
  end?: string | null;
  startUncertaintyDays?: number | null;
  vei?: number | null;
  so2MassKt?: number | null;
  plumeAltKm?: number | null;
  maxAlert?: number | null;
  source: SourceId[];
  url?: string;
}

export interface Reading {
  id: string;
  episodeId?: string;
  start: ISODate;
  end: ISODate;
  status: "draft" | "reviewed";
  text: LocalText;
  limits?: LocalText;
  figures: Figure[];
}

export interface Exposure {
  rings: { radiusKm: number; population: number; year: number; source: SourceId }[];
  comparisons?: Figure[];
  lgus?: { pcode: string; name: string; province?: string; distanceKm: number }[];
}

export interface VolcanoReadModel extends Header {
  kind: "volcano";
  volcano: Volcano;
  span: { start: ISODate; end: ISODate };
  daily: Record<string, DailySeries>;
  events: Record<string, SparseSeries>;
  bulletins?: Bulletins | null;
  advisories?: Advisories | null;
  displacement?: Displacement | null;
  episodes: Episode[];
  readings: Reading[];
  exposure: Exposure;
  provenance: Provenance;
}

// ---------- <version>/layers.json ----------

export type LayerId = "thermal-detections" | "earthquakes-usgs" | "so2-monthly" | "hillshade" | "rings" | "deformation-velocity";

/** One InSAR frame cropped around one volcano (deformation-velocity): the file is url with {frame} = id. */
export interface DeformationFrame {
  id: string;
  volcanoId: string;
  track: number;
  pass: "ascending" | "descending";
  /** [w, s, e, n] of the pixel edges. */
  bounds: [number, number, number, number];
  /** [lon, lat] of the reference area the values are relative to. */
  reference: [number, number];
  start: ISODate;
  end: ISODate;
  /** Number of acquisitions. */
  dates: number;
}

export interface Layer {
  id: LayerId;
  title: LocalText;
  format: "geojson" | "pmtiles" | "raster-xyz" | "cog";
  /** Relative to the version root; may contain {month}, {year}, {z}/{x}/{y}, {frame}. */
  url: string;
  sourceLayer?: string;
  time?: { step: "month" | "year" | "none"; start: string; end: string; available?: string[] };
  minzoom?: number;
  maxzoom?: number;
  bounds?: [number, number, number, number];
  properties?: Record<string, string>;
  legend?: { unit?: string; stops?: [number, string][] };
  sources: SourceId[];
  attribution: string;
  note?: LocalText;
  frames?: DeformationFrame[];
}

export interface Layers extends Header {
  kind: "layers";
  layers: Layer[];
}

// ---------- <version>/story/<id>.json (and story/drafts/<id>.json) ----------

export type StoryStepKind = "before" | "onset" | "course" | "after";

/** One rendered template sentence (STORIES-PLAN §B3): text plus the figures and sources behind it. */
export interface StorySentence {
  template: string;
  text: LocalText;
  /** Indexes into the step's figures. */
  figures: number[];
  sources: SourceId[];
}

export interface StoryScore {
  families: number;
  steps: number;
  tier: "story" | "reading" | "none";
}

export interface StoryStep {
  id: string;
  kind?: StoryStepKind;
  sentences?: StorySentence[];
  /** Fixed reasons shown when the step has no fact sentence. */
  absent?: { why: string; text: LocalText }[];
  start: ISODate;
  end: ISODate;
  title: LocalText;
  text: LocalText;
  status?: "draft" | "reviewed";
  /** Keys of VolcanoReadModel.daily / .events, or "bulletins" | "advisories" | "displacement". */
  series: string[];
  figures: Figure[];
  assets?: Asset[];
  map?: { center?: [number, number]; zoom?: number; layers?: LayerId[]; month?: ISOMonth };
}

export interface Story extends Header {
  kind: "story";
  id: string;
  volcanoId: string;
  volcanoFile?: string;
  title: LocalText;
  summary?: LocalText;
  span: { start: ISODate; end: ISODate };
  /** Derived: reviewed only when every step is. Drafts are hidden unless the preview parameter is set (ST1). */
  status?: "draft" | "reviewed";
  generator?: { name: string; version: string; catalogueVersion: number };
  episodeIds?: string[];
  score?: StoryScore;
  steps: StoryStep[];
  winds?: {
    source: SourceId[];
    point: [number, number];
    cols: ["time", "hPa", "u", "v", "speedMs", "dirToDeg"];
    rows: [string, number, number, number, number, number][];
  };
  provenance: Provenance;
}

// ---------- <version>/stories.json ----------

export interface StoryIndexEntry {
  id: string;
  volcanoId: string;
  title: LocalText;
  span: { start: ISODate; end: ISODate };
  episodeIds?: string[];
  score?: StoryScore;
  status: "draft" | "reviewed";
  rank?: number;
  /** Relative to the version root; absent for readings. */
  file?: string;
  sentences?: number;
}

export interface StoriesIndex extends Header {
  kind: "stories";
  stories: StoryIndexEntry[];
  excluded?: { id: string; reason: string }[];
}
