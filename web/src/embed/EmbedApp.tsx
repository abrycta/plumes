// /embed: the portfolio's live picture of Plumes. The national map (the app's own InteractiveMap and data) with
// thermal detections and earthquakes, stepping month by month through the year up to the most recent eruption GVP
// records (the month the map page opens on), over a two-line caption. No Header, footer, controls or links (live
// embeds carry no link: the portfolio around the frame links to the app); the frame is inert and the map is
// non-interactive, so a touch on it scrolls the parent page.
// It starts on the eruption month and stays there under reduced motion (the still view). The steps pause while the
// parent says so (off-screen, or another embed is the one moving on a touch device), while the frame is out of
// sight, and while the tab is hidden.

import { AkariProvider, useLang, useT } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useRef, useState } from "react";

import type { Layer, VolcanoesIndex } from "@contracts/readmodels";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { parseUrl } from "@/app/url";
import { loadConfig, loadLayers, loadRoot, loadVolcanoes, resolveUrl } from "@/data/load";
import { filtersByMonth, layerMonths, layerPath } from "@/data/layers";
import type { Overlay } from "@/map/InteractiveMap";

import { PADDING, useCompact } from "./layout";
import { COOKIE_DOMAIN, listenToParent, onPauseChange, pausedByParent, postReady } from "./parent-bridge";

const InteractiveMap = lazy(() => import("@/map/InteractiveMap"));

/** Time on each month. */
const DWELL_MS = 1800;
/** Months shown, ending on the eruption month. */
const SPAN = 12;

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
  return lang === "ja" ? `${y}年${mo}月` : `${["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][mo - 1]} ${y}`;
}

/** The months to step through and the eruption that ends them (the map page's opening month). */
function tourOf(index: VolcanoesIndex, layers: Layer[]): { months: string[]; eruption: { month: string; id: string } | null } {
  const all = [...new Set(layers.flatMap((l) => layerMonths(l)))].sort();
  const eruptions = index.features
    .map((f) => ({ id: f.properties.id, month: (f.properties.lastEruption?.start ?? "").slice(0, 7) }))
    .filter((e) => /^\d{4}-\d{2}$/.test(e.month))
    .sort((a, b) => a.month.localeCompare(b.month));
  const last = eruptions.at(-1);
  const end = last && all.includes(last.month) ? all.indexOf(last.month) : all.length - 1;
  return { months: all.slice(Math.max(0, end - SPAN + 1), end + 1), eruption: last && all.includes(last.month) ? last : null };
}

/** The month shown: the last of `months` (the still view), then a step every DWELL_MS while allowed. */
function useStep(count: number, frame: React.RefObject<HTMLDivElement | null>): number {
  const [step, setStep] = useState(count - 1);
  useEffect(() => {
    const el = frame.current;
    if (!el || count < 2) return;
    let timer: number | undefined;
    let inView = true;
    const running = () => inView && document.visibilityState === "visible" && !pausedByParent() && !reducedMotion() && "embedReady" in document.documentElement.dataset;
    const schedule = () => {
      clearTimeout(timer);
      timer = undefined;
      if (running())
        timer = window.setTimeout(() => {
          setStep((s) => (s + 1) % count);
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
      // Reduced motion: back to the eruption month, statically.
      if (motion.matches) setStep(count - 1);
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
  }, [count, frame]);
  return step;
}

function Swatch({ color }: { color: string }) {
  return <span aria-hidden="true" className="inline-block size-[0.75em] shrink-0 rounded-full" style={{ background: color }} />;
}

function EmbedMap({ frame }: { frame: React.RefObject<HTMLDivElement | null> }) {
  const t = useT();
  const { lang } = useLang();
  const compact = useCompact();
  const index = use(loadVolcanoes());
  const layers = use(loadLayers());
  const config = use(loadConfig());
  const root = use(loadRoot());
  const thermal = layers.layers.find((l) => l.id === "thermal-detections");
  const quakes = layers.layers.find((l) => l.id === "earthquakes-usgs");
  const { months, eruption } = useMemo(() => tourOf(index, [thermal, quakes].filter((l): l is Layer => !!l)), [index, thermal, quakes]);
  const step = useStep(months.length, frame);
  const month = months[step] ?? null;

  const overlays: Overlay[] = [];
  for (const [layer, id] of [[quakes, "earthquakes"], [thermal, "thermal"]] as const)
    if (layer && month && layerMonths(layer).includes(month))
      overlays.push({ id, url: resolveUrl(root.versionBase, layerPath(layer, month)), sourceLayer: layer.sourceLayer, month: filtersByMonth(layer) ? month : undefined, attribution: id === "thermal" ? "NASA FIRMS" : "USGS" });

  // Fixed for the map's life: a mode change resizes the same map (it refits), it never recreates it.
  const embed = useMemo(
    () => ({
      pixelRatio: pixelRatio(),
      padding: matchMedia("(max-width: 1100px)").matches ? PADDING.compact : PADDING.desktop,
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

  const volcano = eruption ? index.features.find((f) => f.properties.id === eruption.id) : undefined;
  const headline = month
    ? `${formatMonth(month, lang)}${volcano && month === eruption?.month ? t(` · ${volcano.properties.name.en} erupts`, ` · ${volcano.properties.name.ja}が噴火`) : ""}`
    : t("Philippine volcanoes", "フィリピンの火山");

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <div className="relative min-h-0 flex-1">
        <InteractiveMap
          index={index}
          styleUrl={config.basemap?.style ?? "https://tiles.openfreemap.org/styles/positron"}
          coastUrl={resolveUrl("/", config.basemap?.fallback ?? "/basemap/coast.geojson")}
          overlays={overlays}
          embed={embed}
        />
      </div>
      <div
        className={
          compact
            ? "flex shrink-0 flex-col gap-0.5 border-t border-border px-2 py-1.5 leading-tight"
            : "flex shrink-0 flex-col gap-2 border-t border-border px-8 py-5 leading-tight"
        }
        data-testid="embed-caption"
      >
        <p className={`m-0 truncate font-heading font-semibold ${compact ? "text-[14px]" : "text-[30px]"}`} data-month={month ?? ""}>
          {headline}
        </p>
        <p className={`m-0 flex items-center gap-[0.5em] truncate text-muted-foreground ${compact ? "text-[12px]" : "text-[22px]"}`}>
          <Swatch color="var(--chart-4)" />
          <span className="shrink-0">{t("Thermal (NASA FIRMS)", "熱異常(NASA FIRMS)")}</span>
          <Swatch color="var(--chart-2)" />
          <span className="shrink-0">{t("Earthquakes (USGS)", "地震(USGS)")}</span>
          <span className="truncate">· © OpenMapTiles © OpenStreetMap</span>
        </p>
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
