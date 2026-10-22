// /embed: the portfolio's live picture of Plumes (workspace rule 27: animated and data-dense). The national map (the
// app's own InteractiveMap and data) tours the richest 12-month windows of the record, chosen from the data
// (states.ts): each shows thermal-detection density, detections near and far from a volcano, earthquakes by magnitude
// and depth and the volcanoes' activity, beside a panel with one fact per line (the volcano in focus, the window, its
// counts, SO₂ and VIIRS heat at the volcano, a sparkline). No Header, footer, controls or links (live embeds carry no
// link: the portfolio around the frame links to the app); the frame is inert and the map is non-interactive, so a
// touch on it scrolls the parent page.
// The tour matches Lights: DWELL_MS on each window, then a fade out, the next window drawn, a fade in (Akari's slow
// duration and its exit and standard easings). It opens on the densest window and stays there under reduced motion
// (the still view). It pauses while the parent says so (off-screen, or another embed is the one moving on a touch
// device), while the frame is out of sight, and while the tab is hidden. Phones get their own layout (layout.ts).

import { AkariProvider, useLang } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useRef, useState } from "react";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { parseUrl } from "@/app/url";
import { loadConfig, loadLayers, loadRoot, loadVolcano, loadVolcanoes, resolveUrl } from "@/data/load";
import { layerMonths } from "@/data/layers";
import { formatDate } from "@/lib/dates";
import { WINDOW_MONTHS, windowMonths } from "@/map/density";
import { loadAllQuakes } from "@/map/points";
import { loadWindow } from "@/map/windowData";

import { PADDING, useCompact } from "./layout";
import { fromPack, PACK_DIR, packState, withFocus, type PackIndex, type PackState, type ShownWindow } from "./pack";
import { COOKIE_DOMAIN, listenToParent, onPauseChange, pausedByParent, postReady } from "./parent-bridge";
import { chooseStates } from "./states";

const InteractiveMap = lazy(() => import("@/map/InteractiveMap"));

/** Time on each window between transitions: Lights' DWELL_MS. */
export const DWELL_MS = 2200;
/** Longest wait for the map to draw a window before fading back in anyway. */
const DRAW_CAP_MS = 1500;

const urlLang = parseUrl(location.pathname, location.search).lang;

/** `?pr=` from the parent (the frame is shown scaled down), clamped; default: the device's ratio, at most 2. */
function pixelRatio(): number {
  const pr = Number(new URLSearchParams(location.search).get("pr"));
  if (Number.isFinite(pr) && pr > 0) return Math.min(2, Math.max(0.5, pr));
  return Math.min(window.devicePixelRatio || 1, 2);
}

const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/** An Akari motion token's value (duration in ms, or an easing), read from the page's CSS. */
function motionToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** A CSS time ("360ms", or ".36s" once minified) in milliseconds; 0 when unreadable. */
function durationMs(v: string): number {
  const n = parseFloat(v);
  if (!Number.isFinite(n)) return 0;
  return v.endsWith("ms") ? n : v.endsWith("s") ? n * 1000 : n;
}

/** The windows in time order, loaded one after another with the densest-ranked first, so the first is ready soonest.
 *  From the build-time pack (pack.ts: a few hundred kB, a smaller file per window on phones); without a pack (an
 *  offline build), computed in the browser from the published layers. */
function useStates(): ShownWindow[] {
  const index = use(loadVolcanoes());
  const layers = use(loadLayers());
  const root = use(loadRoot());
  const [loaded, setLoaded] = useState<ShownWindow[]>([]);
  useEffect(() => {
    let live = true;
    const add = (w: ShownWindow) => live && setLoaded((l) => [...l, w].sort((a, b) => a.state.end.localeCompare(b.state.end)));
    const phone = matchMedia("(max-width: 600px)").matches;
    void (async () => {
      const pack = await fetch(`/${PACK_DIR}/index.json`)
        .then((r) => (r.ok && (r.headers.get("content-type") ?? "").includes("json") ? (r.json() as Promise<PackIndex>) : null))
        .catch(() => null);
      if (pack?.states.length) {
        for (const s of [...pack.states].sort((a, b) => b.points - a.points)) {
          const p = await fetch(`/${PACK_DIR}/${phone ? s.compact : s.file}`)
            .then((r) => (r.ok ? (r.json() as Promise<PackState>) : null))
            .catch(() => null);
          if (!live) return;
          if (p) add(fromPack(p));
        }
        return;
      }
      const thermal = layers.layers.find((l) => l.id === "thermal-detections");
      const quakes = layers.layers.find((l) => l.id === "earthquakes-usgs");
      const record = [...new Set([...layerMonths(thermal), ...layerMonths(quakes)])].filter((m) => m <= root.latest.dataAsOf.slice(0, 7)).sort();
      const all = quakes ? await loadAllQuakes(quakes, root.versionBase, record).catch(() => []) : [];
      for (const s of chooseStates(index, record, all).sort((a, b) => b.quakes - a.quakes)) {
        const data = await loadWindow(layers, root.versionBase, index, windowMonths(s.end, WINDOW_MONTHS));
        const p = await withFocus(packState(s, data, phone), index, loadVolcano);
        if (!live) return;
        add(fromPack(p));
      }
    })();
    return () => {
      live = false;
    };
  }, [index, layers, root]);
  return loaded;
}

/**
 * The tour (Lights' timing): while the frame is in sight, the tab visible, the parent has not paused it and motion is
 * allowed, every DWELL_MS the content fades out, the next window (time order, wrapping) is selected and drawn, and
 * the content fades back in. Returns the shown window's end month: null = the densest (the start and the still view).
 */
function useTour(ends: readonly string[], frame: React.RefObject<HTMLDivElement | null>, content: React.RefObject<HTMLDivElement | null>, drawn: React.RefObject<(() => void) | null>): string | null {
  const [shown, setShown] = useState<string | null>(null);
  const latest = useRef({ ends, shown });
  useEffect(() => {
    latest.current = { ends, shown };
  }, [ends, shown]);
  useEffect(() => {
    const el = frame.current;
    if (!el) return;
    let timer: number | undefined;
    let inView = true;
    let busy = false;
    const ready = () => "embedReady" in document.documentElement.dataset;
    const running = () => inView && document.visibilityState === "visible" && !pausedByParent() && !reducedMotion();
    const fade = (to: number) => {
      const node = content.current;
      if (!node) return Promise.resolve();
      return node
        .animate(
          { opacity: to },
          {
            duration: durationMs(motionToken("--ak-duration-slow")),
            easing: motionToken(to === 0 ? "--ak-ease-exit" : "--ak-ease-standard") || "ease",
            fill: "forwards",
          },
        )
        .finished.then(() => undefined)
        .catch(() => undefined);
    };
    const schedule = () => {
      clearTimeout(timer);
      timer = undefined;
      if (!busy && running() && latest.current.ends.length > 1) timer = window.setTimeout(advance, DWELL_MS);
    };
    async function advance() {
      if (!running()) return;
      if (!ready()) return schedule(); // the first window is still drawing
      const { ends: all, shown: cur } = latest.current;
      if (all.length < 2) return schedule();
      busy = true;
      document.documentElement.dataset.tourPhase = "out";
      await fade(0);
      // The next window, drawn while hidden: wait for the map's idle after the new data (capped), then fade in.
      const next = all[(all.indexOf(cur ?? densestEnd()) + 1) % all.length]!;
      await new Promise<void>((resolve) => {
        const cap = window.setTimeout(resolve, DRAW_CAP_MS);
        drawn.current = () => {
          clearTimeout(cap);
          resolve();
        };
        setShown(next);
      });
      drawn.current = null;
      document.documentElement.dataset.tourPhase = "in";
      await fade(1);
      document.documentElement.dataset.tourPhase = "dwell";
      busy = false;
      schedule();
    }
    const densestEnd = () => document.documentElement.dataset.embedDensest ?? latest.current.ends[0]!;
    const io = new IntersectionObserver(([e]) => {
      inView = !!e?.isIntersecting;
      schedule();
    });
    io.observe(el);
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const onMotion = () => {
      // Reduced motion: back to the densest window, statically.
      if (motion.matches) {
        setShown(null);
        content.current?.getAnimations().forEach((a) => a.cancel());
      }
      schedule();
    };
    motion.addEventListener("change", onMotion);
    document.addEventListener("visibilitychange", schedule);
    window.addEventListener("plumes:embed-ready", schedule);
    const offPause = onPauseChange(schedule);
    schedule();
    return () => {
      clearTimeout(timer);
      io.disconnect();
      motion.removeEventListener("change", onMotion);
      document.removeEventListener("visibilitychange", schedule);
      window.removeEventListener("plumes:embed-ready", schedule);
      offPause();
    };
  }, [frame, content, drawn]);
  return shown;
}

function EmbedMap({ frame }: { frame: React.RefObject<HTMLDivElement | null> }) {
  const { lang } = useLang();
  const compact = useCompact();
  const index = use(loadVolcanoes());
  const config = use(loadConfig());
  const loaded = useStates();
  const content = useRef<HTMLDivElement>(null);
  const drawn = useRef<(() => void) | null>(null);
  const densest = loaded.reduce<ShownWindow | null>((best, l) => (l.points > (best?.points ?? -1) ? l : best), null);
  useEffect(() => {
    if (densest) document.documentElement.dataset.embedDensest = densest.state.end;
  }, [densest]);
  const ends = useMemo(() => loaded.map((l) => l.state.end), [loaded]);
  const shownEnd = useTour(ends, frame, content, drawn);
  const cur = loaded.find((l) => l.state.end === shownEnd) ?? densest;

  // Fixed for the map's life: a mode change resizes the same map (it refits), it never recreates it.
  const embed = useMemo(
    () => ({
      pixelRatio: pixelRatio(),
      padding: matchMedia("(max-width: 1100px)").matches ? PADDING.compact : PADDING.desktop,
      scale: matchMedia("(max-width: 600px)").matches ? 0.6 : matchMedia("(max-width: 1100px)").matches ? 1 : 2,
      onReady: () => {
        if ("embedReady" in document.documentElement.dataset) return;
        document.documentElement.dataset.embedReady = "";
        window.dispatchEvent(new Event("plumes:embed-ready"));
        postReady();
      },
      onDrawn: () => drawn.current?.(),
    }),
    [],
  );
  useEffect(() => {
    document.documentElement.dataset.embedLayout = compact ? "compact" : "desktop";
  }, [compact]);

  const s = cur?.state;
  const eruptionMap = useMemo(() => new Map((s?.eruptions ?? []).map((e) => [e.id, e.month])), [s]);
  return (
    <div ref={content} className="h-full bg-background text-foreground" data-embed-content>
      <div className="relative h-full" data-window-end={cur?.state.end ?? ""}>
        <InteractiveMap
          index={index}
          styleUrl={config.basemap?.style ?? "https://tiles.openfreemap.org/styles/positron"}
          coastUrl={resolveUrl("/", config.basemap?.fallback ?? "/basemap/coast.geojson")}
          data={cur?.geojson ?? null}
          activity={cur?.activity}
          eruptions={eruptionMap}
          formatMonth={(m) => formatDate(m, lang)}
          embed={embed}
        />
      </div>
    </div>
  );
}

function LangFromUrl() {
  const { lang, setLang } = useLang();
  useEffect(() => {
    if (urlLang && urlLang !== lang) setLang(urlLang);
    // Only once: ?lang= wins over a stored choice.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

export function EmbedApp() {
  useEffect(() => listenToParent(), []);
  const frame = useRef<HTMLDivElement>(null);
  return (
    <AkariProvider defaultLang={urlLang ?? "en"} toaster={false} sharedCookieDomain={COOKIE_DOMAIN} inlineScript={false}>
      <LangFromUrl />
      <div ref={frame} inert className="h-dvh overflow-hidden bg-background" data-testid="embed-frame">
        <ErrorBoundary>
          <Suspense fallback={null}>
            <EmbedMap frame={frame} />
          </Suspense>
        </ErrorBoundary>
      </div>
    </AkariProvider>
  );
}
