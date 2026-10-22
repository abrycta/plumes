// /embed: the portfolio's live picture of Plumes, as Lights' and Replay's embeds show their apps: the real map page
// (pages/MapPage: controls, window summary, map, timeline, legend, volcano list) without the Header or footer, fed
// from the build-time pack (pack.ts) and wholly inert, with no links (the portfolio around the frame links to the app).
// It tours the densest 12-month windows of the record (states.ts), densest first: DWELL_MS on each, then the map
// fades out, the next window is drawn and the map fades back in (Akari's slow duration, exit and standard easings).
// Reduced motion keeps the densest window still. It pauses while the parent says so (off-screen, or another embed is
// the one moving on a touch device), while the frame is out of sight, and while the tab is hidden. Phones get the
// map over the window summary (layout.ts), never the page scaled down.

import { AkariProvider, useLang } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useRef, useState } from "react";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { parseUrl } from "@/app/url";
import { loadLayers, loadRoot, loadVolcano, loadVolcanoes } from "@/data/load";
import { layerMonths } from "@/data/layers";
import { WINDOW_MONTHS, windowMonths } from "@/map/density";
import { loadAllQuakes } from "@/map/points";
import { loadWindow } from "@/map/windowData";

import { FitScreen } from "./FitScreen";
import { PADDING, useCompact, usePhone } from "./layout";
import { fromPack, PACK_DIR, packState, withFocus, type PackIndex, type PackState, type ShownWindow } from "./pack";
import { COOKIE_DOMAIN, listenToParent, onPauseChange, pausedByParent, postReady } from "./parent-bridge";
import { chooseStates } from "./states";

const MapPage = lazy(() => import("@/pages/MapPage"));
const VolcanoPage = lazy(() => import("@/pages/VolcanoPage"));
const VolcanoesPage = lazy(() => import("@/pages/VolcanoesPage"));

/** Time on each window between transitions: Lights' DWELL_MS. */
export const DWELL_MS = 2200;
/** Longest wait for the map to draw a window before fading back in anyway. */

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
function useTour(ends: readonly string[], frame: React.RefObject<HTMLDivElement | null>, content: React.RefObject<HTMLDivElement | null>): string | null {
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
      const nodes = content.current ? [content.current] : [];
      if (!nodes.length) return Promise.resolve();
      return Promise.all(
        nodes.map(
          (node) =>
            node.animate(
              { opacity: to },
              {
                duration: durationMs(motionToken("--ak-duration-slow")),
                easing: motionToken(to === 0 ? "--ak-ease-exit" : "--ak-ease-standard") || "ease",
                fill: "forwards",
              },
            ).finished,
        ),
      )
        .then(() => undefined)
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
      // Every screen stays mounted (drawn and measured while hidden): two frames for React to swap them.
      setShown(next);
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      document.documentElement.dataset.tourPhase = "in";
      await fade(1);
      document.documentElement.dataset.tourPhase = "dwell";
      busy = false;
      schedule();
    }
    const densestEnd = () => latest.current.ends[0]!;
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
  }, [frame, content]);
  return shown;
}

/** The tour's screens, in order: the map page first (the still view under reduced motion). */
const SCREENS = ["map", "volcano", "record", "volcanoes"] as const;
/** Phones (the slot is about 358×224): the screens that stay legible at that size. */
const PHONE_SCREENS = ["map", "deeptime"] as const;
type Screen = (typeof SCREENS)[number] | (typeof PHONE_SCREENS)[number];

function EmbedScreens({ frame }: { frame: React.RefObject<HTMLDivElement | null> }) {
  const compact = useCompact();
  const phone = usePhone();
  const index = use(loadVolcanoes());
  const loaded = useStates();
  const content = useRef<HTMLDivElement>(null);
  const shown = (useTour(phone ? PHONE_SCREENS : SCREENS, frame, content) ?? "map") as Screen;
  // The map screen: the densest window, zoomed to its volcano.
  const densest = loaded.reduce<ShownWindow | null>((best, l) => (l.points > (best?.points ?? -1) ? l : best), null);
  // The volcano screens: the two deep-record volcanoes with the latest eruptions (Mayon, Kanlaon in v2).
  const [top, record] = useMemo(
    () =>
      index.features
        .filter((f) => f.properties.coverage === "deep" && f.properties.lastEruption?.start)
        .sort((a, b) => (b.properties.lastEruption?.start ?? "").localeCompare(a.properties.lastEruption?.start ?? ""))
        .map((f) => f.properties.id),
    [index],
  );

  // Fixed for the map's life: a mode change resizes the same map (it refits), it never recreates it.
  const embed = useMemo(
    () => ({
      pixelRatio: pixelRatio(),
      padding: matchMedia("(max-width: 1100px)").matches ? PADDING.compact : PADDING.desktop,
      scale: matchMedia("(max-width: 600px)").matches ? 0.6 : 1,
      onReady: () => {
        if ("embedReady" in document.documentElement.dataset) return;
        document.documentElement.dataset.embedReady = "";
        window.dispatchEvent(new Event("plumes:embed-ready"));
        postReady();
      },
    }),
    [],
  );
  useEffect(() => {
    document.documentElement.dataset.embedLayout = compact ? "compact" : "desktop";
  }, [compact]);
  // No links in the frame (rule 6c): the app's links keep their look, without an href.
  useEffect(() => {
    const el = content.current;
    if (!el) return;
    const strip = () => el.querySelectorAll("a[href]").forEach((a) => a.removeAttribute("href"));
    strip();
    const mo = new MutationObserver(strip);
    mo.observe(el, { subtree: true, childList: true, attributes: true, attributeFilter: ["href"] });
    return () => mo.disconnect();
  }, []);

  const screen = (id: Screen, el: React.ReactNode) => (
    <div key={id} className={`absolute inset-0 ${shown === id ? "" : "invisible"}`} data-embed-screen={id} aria-hidden={shown !== id}>
      <ErrorBoundary>
        <Suspense fallback={null}>{el}</Suspense>
      </ErrorBoundary>
    </div>
  );
  return (
    <div ref={content} className="relative h-full overflow-hidden bg-background text-foreground" data-embed-content data-screen={shown} data-window-end={densest?.state.end ?? ""}>
      {screen(
        "map",
        <MapPage embed={{ end: densest?.state.end ?? "", window: densest ? { geojson: densest.geojson, counts: densest.counts, activity: densest.activity, totals: densest.totals } : null, map: embed, compact, focus: densest?.focus?.id ?? null }} />,
      )}
      {top && phone
        ? screen(
            "deeptime",
            <FitScreen align="bottom">
              <VolcanoPage id={top} part="deeptime" />
            </FitScreen>,
          )
        : null}
      {top && !phone
        ? screen(
            "volcano",
            <FitScreen>
              <VolcanoPage id={top} />
            </FitScreen>,
          )
        : null}
      {record && !phone
        ? screen(
            "record",
            <FitScreen at='[aria-labelledby="record-title"]'>
              <VolcanoPage id={record} />
            </FitScreen>,
          )
        : null}
      {phone
        ? null
        : screen(
            "volcanoes",
            <FitScreen>
              <VolcanoesPage />
            </FitScreen>,
          )}
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
            <EmbedScreens frame={frame} />
          </Suspense>
        </ErrorBoundary>
      </div>
    </AkariProvider>
  );
}
