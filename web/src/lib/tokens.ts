import { flat } from "@abrycta/akari/tokens";

export type ThemeKey = "light" | "dark" | "light-hc" | "dark-hc";

const TOKENS = flat as unknown as Record<string, Record<string, string>>;

/** An Akari colour token's value for the theme (MapLibre paint needs resolved colours, not CSS variables).
 *  An unknown id falls back to Akari's muted text colour, never to an app-local value. */
export function tokenColour(id: string, key: ThemeKey): string {
  const t = TOKENS[id] ?? TOKENS["color.text-muted"]!;
  return t[key] ?? t.light!;
}
