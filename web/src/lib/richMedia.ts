// Workspace rule 6b: heavy or interactive embeds (the MapLibre map) load only when the screen is at least 768px
// wide, the primary pointer hovers and is fine, and Save-Data is off. Otherwise the static picture stays. Never by
// user-agent or width alone; re-checked on rotation, resize and input changes (matchMedia listeners).

import { useSyncExternalStore } from "react";

export const RICH_QUERIES = ["(min-width: 768px)", "(hover: hover) and (pointer: fine)"] as const;

interface Env {
  matches: (q: string) => boolean;
  saveData: boolean;
}

/** Pure decision, unit-tested. */
export function richMediaAllowed(env: Env): boolean {
  return RICH_QUERIES.every((q) => env.matches(q)) && !env.saveData;
}

function saveData(): boolean {
  const c = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
  return !!c?.saveData;
}

function snapshot(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return richMediaAllowed({ matches: (q) => window.matchMedia(q).matches, saveData: saveData() });
}

function subscribe(fn: () => void) {
  const mqls = RICH_QUERIES.map((q) => window.matchMedia(q));
  for (const m of mqls) m.addEventListener("change", fn);
  const c = (navigator as Navigator & { connection?: EventTarget }).connection;
  c?.addEventListener?.("change", fn);
  window.addEventListener("orientationchange", fn);
  return () => {
    for (const m of mqls) m.removeEventListener("change", fn);
    c?.removeEventListener?.("change", fn);
    window.removeEventListener("orientationchange", fn);
  };
}

/** Static picture first (server snapshot false), upgraded in the browser when rule 6b allows. */
export function useRichMedia(): boolean {
  return useSyncExternalStore(subscribe, snapshot, () => false);
}
