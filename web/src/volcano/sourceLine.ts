import type { LocalText } from "@contracts/readmodels";

/** Short source names for a track's one-line caption (rule 28b). The full instrument wording, coverage and notes
 *  stay one tap away in the caption's disclosure (data/tracks.ts INSTRUMENTS), never removed. */
const SHORT: Record<string, LocalText> = {
  "s5p-offl-so2": { en: "Sentinel-5P TROPOMI", ja: "Sentinel-5P TROPOMI" },
  "modis-mod14a1": { en: "MODIS on Terra", ja: "Terra衛星MODIS" },
  "viirs-vnp14a1": { en: "VIIRS on S-NPP", ja: "S-NPP衛星VIIRS" },
  "firms-modis": { en: "NASA FIRMS", ja: "NASA FIRMS" },
  "firms-viirs-noaa20": { en: "VIIRS on NOAA-20 (NASA FIRMS)", ja: "NOAA-20衛星VIIRS(NASA FIRMS)" },
  "usgs-comcat-ph-2010": { en: "USGS ComCat", ja: "USGS ComCat" },
  "usgs-comcat-ph-1900-2009": { en: "USGS ComCat", ja: "USGS ComCat" },
  "landsat-surface-temperature": { en: "Landsat thermal band", ja: "Landsat熱赤外バンド" },
  "phivolcs-bulletins": { en: "DOST-PHIVOLCS bulletins", ja: "DOST-PHIVOLCSの火山情報" },
  "phivolcs-lava-bulletins": { en: "DOST-PHIVOLCS LAVA bulletins", ja: "DOST-PHIVOLCS LAVA火山情報" },
  "vaac-tokyo-advisories": { en: "Tokyo VAAC (JMA)", ja: "東京VAAC(気象庁)" },
  "dswd-dromic-reports": { en: "DSWD DROMIC reports", ja: "DSWD DROMIC報告" },
  "gvp-eruptions-ph": { en: "Smithsonian GVP", ja: "スミソニアン博物館GVP" },
  "comet-licsbas": { en: "Sentinel-1 radar (COMET LiCSBAS)", ja: "Sentinel-1レーダー(COMET LiCSBAS)" },
  "nasa-msvolso2l4": { en: "NASA MEaSUREs SO₂", ja: "NASA MEaSUREs SO₂" },
  "gpm-imerg-v07": { en: "NASA GPM IMERG", ja: "NASA GPM IMERG" },
};

/** "Sentinel-5P TROPOMI · USGS ComCat": each source once, in the track's order; unknown ids by their id. */
export function sourceLine(sources: readonly string[], lang: "en" | "ja"): string {
  return [...new Set(sources.map((s) => SHORT[s]?.[lang] ?? s))].join(lang === "ja" ? "、" : " · ");
}
