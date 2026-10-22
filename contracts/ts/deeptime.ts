// Deep-time strip: TypeScript mirror of contracts/schemas/deeptime.schema.json (<version>/deeptime.json).
// GVP Holocene eruptions with GVP's date uncertainty, and NOAA NCEI HazEL impacts (compiled estimates, each linked).
// Partial dates: YYYY, YYYY-MM or YYYY-MM-DD; BCE years are negative without a year 0 (-3580 is 3580 BCE).

import type { Header, ISODate, LocalText, Provenance } from "./readmodels";

export type PartialDate = string;
/** NCEI amount-order code: 0 none, 1 few/limited … 4 very many/extreme (see glossary.orders). */
export type AmountOrder = 0 | 1 | 2 | 3 | 4;

export interface DeepTimeImpact {
  id: `hazel-${number}`;
  date: PartialDate;
  vei?: number;
  deaths?: number;
  deathsOrder?: AmountOrder;
  /** Includes secondary effects (tsunami, earthquake). */
  deathsTotal?: number;
  deathsTotalOrder?: AmountOrder;
  injuries?: number;
  injuriesOrder?: AmountOrder;
  injuriesTotal?: number;
  injuriesTotalOrder?: AmountOrder;
  missing?: number;
  missingOrder?: AmountOrder;
  missingTotal?: number;
  missingTotalOrder?: AmountOrder;
  /** Million US$ (NCEI). */
  damageMusd?: number;
  damageOrder?: AmountOrder;
  damageMusdTotal?: number;
  damageTotalOrder?: AmountOrder;
  housesDestroyed?: number;
  housesDestroyedOrder?: AmountOrder;
  housesDestroyedTotal?: number;
  housesDestroyedTotalOrder?: AmountOrder;
  /** NCEI killing-agent codes (glossary.agents). */
  agents?: string[];
  tsunami?: true;
  earthquake?: true;
  /** NCEI event page. */
  url: string;
}

export interface DeepTimeEruption {
  id: `gvp-${number}`;
  start: PartialDate;
  end: PartialDate | null;
  certainty: "confirmed" | "uncertain";
  vei: number | null;
  veiModifier?: string;
  /** ± years (radiocarbon dates). */
  startYearUncertainty?: number;
  /** ± days. */
  startDayUncertainty?: number;
  /** "?" uncertain year, "<" before. */
  startYearModifier?: string;
  evidence?: string;
  url: string;
  impacts?: DeepTimeImpact[];
}

export interface DeepTimeVolcano {
  id: string;
  gvpNumber: number | null;
  eruptions: DeepTimeEruption[];
  /** HazEL events outside every GVP eruption window (mostly later lahars). */
  otherImpacts: DeepTimeImpact[];
}

export interface DeepTime extends Header {
  kind: "deeptime";
  span: { startYear: number; satelliteEraStart: ISODate };
  glossary: {
    agents: Record<string, LocalText>;
    orders: { people: Record<string, LocalText>; damage: Record<string, LocalText> };
  };
  notes: { impacts: LocalText; dates: LocalText };
  volcanoes: DeepTimeVolcano[];
  provenance: Provenance;
}
