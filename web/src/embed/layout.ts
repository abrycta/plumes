// The /embed's two layouts, chosen by the frame's own width:
// - desktop: krtmtthw.dev shows a fixed 1280×800 frame scaled to its picture slot (mouse and trackpad devices), so
//   type and markers are drawn large enough to read once scaled down;
// - compact: phones and tablets get the frame at the slot's real size (at most about 960 px wide) and it lays out
//   for that size: the map beside a fact panel at 14/12 px. Never the desktop view scaled down.
import { useSyncExternalStore } from "react";

export const COMPACT_QUERY = "(max-width: 1100px)";
/** Padding around the Philippines when the map fits it, per layout. */
export const PADDING = { compact: 8, desktop: 32 } as const;

export function useCompact(): boolean {
  return useSyncExternalStore(
    (on) => {
      const m = matchMedia(COMPACT_QUERY);
      m.addEventListener("change", on);
      return () => m.removeEventListener("change", on);
    },
    () => matchMedia(COMPACT_QUERY).matches,
  );
}

export const PHONE_QUERY = "(max-width: 600px)";

/** Phone-sized frames (the krtmtthw.dev slot on a phone): the tour keeps to the screens legible there. */
export function usePhone(): boolean {
  return useSyncExternalStore(
    (on) => {
      const m = matchMedia(PHONE_QUERY);
      m.addEventListener("change", on);
      return () => m.removeEventListener("change", on);
    },
    () => matchMedia(PHONE_QUERY).matches,
  );
}
