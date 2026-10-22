// /embed: the portfolio's live picture of Plumes (workspace rule 27: animated and data-dense). The national map (the
// app's own InteractiveMap and data) steps through the richest 12-month windows of the record, chosen from the data
// (states.ts): each shows thermal-detection density, detections near and far from a volcano, earthquakes by magnitude
// and depth and the volcanoes' activity, over a caption that names the window and its counts. No Header, footer,
// controls or links (live embeds carry no link: the portfolio around the frame links to the app); the frame is inert
// and the map is non-interactive, so a touch on it scrolls the parent page.
// It opens on the densest window and stays there under reduced motion (the still view). The steps pause while the
// parent says so (off-screen, or another embed is the one moving on a touch device), while the frame is out of
// sight, and while the tab is hidden. Phones get their own layout: Luzon to the Visayas (decision P1).

import { AkariProvider, useLang, useT } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useRef, useState } from "react";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { parseUrl } from "@/app/url";
import { loadConfig, loadLayers, loadRoot, loadVolcanoes, resolveUrl } from "@/data/load";
import { layerMonths } from "@/data/layers";
import { formatNumber } from "@/lib/format";
import { WINDOW_MONTHS, windowMonths } from "@/map/density";
import { loadAllQuakes } from "@/map/points";
import { loadWindow, toGeojson, type MapGeojson, type WindowData } from "@/map/windowData";

import { PADDING, useCompact } from "./layout";
import { COOKIE_DOMAIN, listenToParent, onPauseChange, pausedByParent, postReady } from "./parent-bridge";
import { chooseStates, type EmbedState } from "./states";

const InteractiveMap = lazy(() => import("@/map/InteractiveMap"));

/** Time on each window: long enough to read the caption. */
const DWELL_MS = 7000;

const urlLang = parseUrl(location.pathname, location.search).lang;

/** `?pr=` from the parent (the frame is shown scaled down), clamped; default: the device's ratio, at most 2. */
function pixelRatio(): number {
  const pr = Number(new URLSearchParams(location.search).get("pr"));
  if (Number.isFinite(pr) && pr > 0) return Math.min(2, Math.max(0.5, pr));
  return Math.min(window.devicePixelRatio || 1, 2);
}

const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

function formatMonth(m: string, lang: "en" | "ja"): string {
  const [y, mo] = m.split("-").map(Number) as [number, number];
  return lang === "ja" ? `${y}年${mo}月` : `${["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][mo - 1]} ${y}`;
}

interface Loaded {
  state: EmbedState;
  data: WindowData;
  geojson: MapGeojson;
  /** Points drawn: thermal detections and earthquakes (the densest window is the still view). */
  points: number;
}

/** Loads the chosen windows one after another, densest-ranked first, so the first state is ready soonest. */
function useStates(): { loaded: Loaded[]; total: number } {
  const index = use(loadVolcanoes());
  const layers = use(loadLayers());
  const root = use(loadRoot());
  const [states, setStates] = useState<EmbedState[] | null>(null);
  const [loaded, setLoaded] = useState<Loaded[]>([]);
  useEffect(() => {
    let live = true;
    const thermal = layers.layers.find((l) => l.id === "thermal-detections");
    const quakes = layers.layers.find((l) => l.id === "earthquakes-usgs");
    const record = [...new Set([...layerMonths(thermal), ...layerMonths(quakes)])].filter((m) => m <= root.latest.dataAsOf.slice(0, 7)).sort();
    void (async () => {
      const all = quakes ? await loadAllQuakes(quakes, root.versionBase, record).catch(() => []) : [];
      const chosen = chooseStates(index, record, all);
      if (!live) return;
      setStates(chosen);
      // Ranked order (chooseStates returns time order): the busiest window loads first.
      for (const s of [...chosen].sort((a, b) => b.quakes - a.quakes)) {
        const data = await loadWindow(layers, root.versionBase, index, windowMonths(s.end, WINDOW_MONTHS));
        if (!live) return;
        const item = { state: s, data, geojson: toGeojson(data), points: data.thermal.length + data.quakes.length };
        setLoaded((l) => [...l, item].sort((a, b) => a.state.end.localeCompare(b.state.end)));
      }
    })();
    return () => {
      live = false;
    };
  }, [index, layers, root]);
  return { loaded, total: states?.length ?? 0 };
}

/** Index of the shown state: the densest one first (the still view), then a step every DWELL_MS while allowed. */
function useStep(count: number, densest: number, frame: React.RefObject<HTMLDivElement | null>): number {
  const [step, setStep] = useState<number | null>(null);
  const shown = step ?? densest;
  const latest = useRef({ count, densest });
  useEffect(() => {
    latest.current = { count, densest };
  }, [count, densest]);
  const many = count > 1;
  useEffect(() => {
    const el = frame.current;
    if (!el) return;
    let timer: number | undefined;
    let inView = true;
    const running = () => inView && document.visibilityState === "visible" && !pausedByParent() && !reducedMotion() && "embedReady" in document.documentElement.dataset;
    const schedule = () => {
      clearTimeout(timer);
      timer = undefined;
      if (running() && latest.current.count > 1)
        timer = window.setTimeout(() => {
          setStep((s) => ((s ?? latest.current.densest) + 1) % latest.current.count);
          schedule();
        }, DWELL_MS);
    };
    const io = new IntersectionObserver(([e]) => {
      inView = !!e?.isIntersecting;
      schedule();
    });
    io.observe(el);
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const onMotion = () => {
      // Reduced motion: back to the densest window, statically.
      if (motion.matches) setStep(null);
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
  }, [frame, many]);
  return Math.min(shown, Math.max(0, count - 1));
}

function Swatch({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <span aria-hidden="true" className={`inline-block size-[0.75em] shrink-0 rounded-full ${className ?? ""}`} style={style} />;
}

function EmbedMap({ frame }: { frame: React.RefObject<HTMLDivElement | null> }) {
  const t = useT();
  const { lang } = useLang();
  const compact = useCompact();
  const index = use(loadVolcanoes());
  const config = use(loadConfig());
  const { loaded } = useStates();
  const densest = loaded.reduce((best, l, i) => (l.points > (loaded[best]?.points ?? -1) ? i : best), 0);
  const step = useStep(loaded.length, densest, frame);
  const cur = loaded[step] ?? null;

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
    }),
    [],
  );
  useEffect(() => {
    document.documentElement.dataset.embedLayout = compact ? "compact" : "desktop";
  }, [compact]);

  const s = cur?.state;
  const eruptionMap = useMemo(() => new Map((s?.eruptions ?? []).map((e) => [e.id, e.month])), [s]);
  const names = (s?.eruptions ?? []).map((e) => index.features.find((f) => f.properties.id === e.id)?.properties.name[lang] ?? e.id);
  const months = s ? windowMonths(s.end, WINDOW_MONTHS) : [];
  const range = s ? `${formatMonth(months[0]!, lang)} – ${formatMonth(s.end, lang)}` : "";
  const headline = s
    ? names.length
      ? t(`${names.join(" and ")} ${names.length > 1 ? "erupt" : "erupts"} · ${range}`, `${names.join("・")}の噴火 · ${range}`)
      : t(`The latest 12 months · ${range}`, `直近12か月 · ${range}`)
    : "";
  const d = cur?.data;
  const near = d ? d.thermal.filter((p) => p.near).length : 0;
  const maxMag = d ? d.quakes.reduce((m, q) => Math.max(m, q.mag ?? 0), 0) : 0;
  const cMax = d ? Math.max(1, ...d.counts.map((c) => Math.max(c.thermalNear + c.thermalFar, c.quakes))) : 1;

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <div className="relative min-h-0 flex-1">
        <InteractiveMap
          index={index}
          styleUrl={config.basemap?.style ?? "https://tiles.openfreemap.org/styles/positron"}
          coastUrl={resolveUrl("/", config.basemap?.fallback ?? "/basemap/coast.geojson")}
          data={cur?.geojson ?? null}
          activity={d?.activity}
          eruptions={eruptionMap}
          formatMonth={(m) => formatMonth(m, lang)}
          embed={embed}
        />
      </div>
      <div className={compact ? "flex shrink-0 flex-col gap-0.5 border-t border-border px-2 py-1.5 leading-tight" : "flex shrink-0 items-end gap-8 border-t border-border px-8 py-5 leading-tight"} data-testid="embed-caption">
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <p className={`m-0 truncate font-heading font-semibold ${compact ? "text-ak-sm" : "text-ak-2xl"}`} data-window-end={s?.end ?? ""}>
            {headline}
          </p>
          <p className={`m-0 flex items-center gap-[0.5em] truncate text-muted-foreground tabular ${compact ? "text-ak-xs" : "text-ak-xl"}`}>
            {d ? (
              <>
                <Swatch className="bg-chart-4" />
                <span className="shrink-0">{t(`${formatNumber(d.thermal.length, lang)} thermal (${formatNumber(near, lang)} near volcanoes)`, `熱異常${formatNumber(d.thermal.length, lang)}件(火山付近${formatNumber(near, lang)}件)`)}</span>
                <Swatch style={{ background: "var(--ak-div-7)" }} />
                <span className="shrink-0">{t(`${formatNumber(d.quakes.length, lang)} earthquakes${maxMag ? `, max M${maxMag.toFixed(1)}` : ""}`, `地震${formatNumber(d.quakes.length, lang)}件${maxMag ? `(最大M${maxMag.toFixed(1)})` : ""}`)}</span>
                <span className="truncate">· NASA FIRMS · USGS · © OpenMapTiles © OpenStreetMap</span>
              </>
            ) : null}
          </p>
        </div>
        {!compact && d ? (
          <div className="flex h-16 w-80 shrink-0 items-end gap-1" aria-hidden="true" data-embed-months>
            {d.counts.map((c) => (
              <div key={c.month} className="flex h-full flex-1 items-end gap-px">
                <div className="flex h-full flex-1 flex-col justify-end">
                  <div className="bg-chart-4 opacity-30" style={{ height: `${(100 * c.thermalFar) / cMax}%` }} />
                  <div className="bg-chart-4" style={{ height: `${(100 * c.thermalNear) / cMax}%` }} />
                </div>
                <div className="flex-1" style={{ height: `${(100 * c.quakes) / cMax}%`, background: "var(--ak-div-7)" }} />
              </div>
            ))}
          </div>
        ) : null}
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
      <div ref={frame} inert className="h-dvh overflow-hidden" data-testid="embed-frame">
        <ErrorBoundary>
          <Suspense fallback={null}>
            <EmbedMap frame={frame} />
          </Suspense>
        </ErrorBoundary>
      </div>
    </AkariProvider>
  );
}
