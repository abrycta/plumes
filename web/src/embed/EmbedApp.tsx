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

import { AkariProvider, Sparkline, useLang, useT } from "@abrycta/akari/react";
import { lazy, Suspense, use, useEffect, useMemo, useRef, useState } from "react";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { parseUrl } from "@/app/url";
import { loadConfig, loadLayers, loadRoot, loadVolcano, loadVolcanoes, resolveUrl } from "@/data/load";
import { layerMonths } from "@/data/layers";
import { formatDate } from "@/lib/dates";
import { formatNumber } from "@/lib/format";
import { WINDOW_MONTHS, windowMonths } from "@/map/density";
import { LAYER_BG, LAYER_TEXT } from "@/map/layerColors";
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

/** One fact per line: a layer swatch (a dot in the layer's colour, sized by the text) or its blank place, then the text. */
function Fact({ swatch, children }: { swatch?: string; children: React.ReactNode }) {
  return (
    <li className="flex min-w-0 items-baseline gap-ak-0-5">
      <span aria-hidden="true" className={swatch ?? "invisible"}>
        ●
      </span>
      <span className="truncate">{children}</span>
    </li>
  );
}

function EmbedMap({ frame }: { frame: React.RefObject<HTMLDivElement | null> }) {
  const t = useT();
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
  const nameOf = (id: string) => index.features.find((f) => f.properties.id === id)?.properties.name[lang] ?? id;
  const names = (s?.eruptions ?? []).map((e) => nameOf(e.id));
  const months = s ? windowMonths(s.end, WINDOW_MONTHS) : [];
  const d = cur;
  const focus = d?.focus;
  const fname = focus ? nameOf(focus.id) : "";
  const headline = s ? (names.length ? t(`${names.join(" and ")} ${names.length > 1 ? "erupt" : "erupts"}`, `${names.join("・")}の噴火`) : t("The latest 12 months", "直近12か月")) : "";
  const range = s ? `${formatDate(months[0]!, lang)} – ${formatDate(s.end, lang)}` : "";
  const n = (v: number) => formatNumber(v, lang);
  const notObserved = t("Not observed: outside this instrument's record", "観測なし(この観測機器の記録の範囲外)");
  const gaps = !!d?.counts.some((c) => c.thermalObserved === false || c.quakesObserved === false);
  const cMax = d ? Math.max(1, ...d.counts.map((c) => Math.max(c.thermalNear + c.thermalFar, c.quakes))) : 1;

  return (
    <div ref={content} className="flex h-full bg-background text-foreground" data-embed-content>
      <div className="relative min-h-0 min-w-0 flex-1">
        <InteractiveMap
          index={index}
          styleUrl={config.basemap?.style ?? "https://tiles.openfreemap.org/styles/positron"}
          coastUrl={resolveUrl("/", config.basemap?.fallback ?? "/basemap/coast.geojson")}
          data={cur?.geojson ?? null}
          activity={d?.activity}
          eruptions={eruptionMap}
          formatMonth={(m) => formatDate(m, lang)}
          embed={embed}
        />
      </div>
      <aside className={`flex w-1/2 shrink-0 flex-col justify-center border-l border-border leading-tight tabular sm:w-2/5 lg:w-1/3 ${compact ? "gap-ak-0-5 px-ak-1 py-ak-1" : "gap-ak-2 px-ak-4 py-ak-4"}`} data-testid="embed-caption">
        {d && s ? (
          <>
            <h1 className={`m-0 line-clamp-2 font-heading font-semibold ${compact ? "text-ak-sm" : "text-ak-3xl"}`} data-window-end={s.end}>
              {headline}
            </h1>
            <p className={`m-0 truncate text-muted-foreground ${compact ? "text-ak-xs" : "text-ak-xl"}`}>{range}</p>
            <ul className={`m-0 flex list-none flex-col p-0 ${compact ? "gap-0 text-ak-xs" : "gap-ak-0-5 text-ak-xl"}`} data-embed-facts>
              <Fact swatch={LAYER_TEXT.thermal}>{t(`${n(d.totals.thermal)} thermal detections`, `熱異常 ${n(d.totals.thermal)}件`)}</Fact>
              <Fact>{compact ? t(`${n(d.totals.near)} near volcanoes`, `火山付近 ${n(d.totals.near)}件`) : t(`${n(d.totals.near)} within 15 km of a volcano`, `うち火山15 km以内 ${n(d.totals.near)}件`)}</Fact>
              <Fact swatch={LAYER_TEXT.quakes}>{t(`${n(d.totals.quakes)} earthquakes`, `地震 ${n(d.totals.quakes)}件`)}</Fact>
              {d.totals.maxMag ? <Fact>{t(`Largest M${d.totals.maxMag.toFixed(1)}`, `最大 M${d.totals.maxMag.toFixed(1)}`)}</Fact> : null}
              {focus?.viirs ? (
                <Fact>{compact ? t(`${fname} VIIRS: ${n(focus.viirs.days)} days`, `${fname} VIIRS ${n(focus.viirs.days)}日`) : t(`${fname}: VIIRS heat on ${n(focus.viirs.days)} days`, `${fname}:VIIRS熱異常 ${n(focus.viirs.days)}日`)}</Fact>
              ) : null}
              {focus?.so2 ? (
                <Fact>
                  {compact
                    ? t(`${fname} SO₂: max ${n(focus.so2.peak)} t`, `${fname} SO₂最大 ${n(focus.so2.peak)} t`)
                    : t(`${fname}: SO₂ peak ${n(focus.so2.peak)} t, ${formatDate(focus.so2.peakDate, lang)}`, `${fname}:SO₂最大 ${n(focus.so2.peak)} t(${formatDate(focus.so2.peakDate, lang)})`)}
                </Fact>
              ) : null}
            </ul>
            {focus?.so2 ? (
              <div className="min-w-0" data-embed-sparkline>
                <Sparkline
                  values={focus.so2.weeks}
                  height={compact ? 24 : 48}
                  zero
                  marker="none"
                  className={compact ? "h-ak-3" : "h-ak-8"}
                  markers={focus.eruptionWeeks.map((w) => ({
                    at: w,
                    label: t("Eruption", "噴火"),
                  }))}
                  markerLabels={false}
                  label={t(`SO₂ near ${fname}, weekly peak (TROPOMI, ${focus.so2.ringKm} km)`, `${fname}付近のSO₂(週最大、TROPOMI、${focus.so2.ringKm} km)`)}
                />
                {!compact ? <p className="m-0 truncate text-ak-base text-muted-foreground">{t(`SO₂ near ${fname}, weekly peak`, `${fname}付近のSO₂(週最大)`)}</p> : null}
              </div>
            ) : null}
            {!compact ? (
              <div className="min-w-0">
                <div className="flex h-ak-8 items-end gap-ak-0-5" aria-hidden="true" data-embed-months>
                  {d.counts.map((c) => (
                    <div key={c.month} className="flex h-full flex-1 items-end gap-px" data-not-observed={[c.thermalObserved === false && "thermal", c.quakesObserved === false && "quakes"].filter(Boolean).join(" ") || undefined}>
                      {c.thermalObserved === false ? (
                        <div className="h-full flex-1 bg-muted opacity-70" title={notObserved} />
                      ) : (
                        <div className="flex h-full flex-1 flex-col justify-end">
                          <div className={`${LAYER_BG.thermal} opacity-30`} style={{ height: `${(100 * c.thermalFar) / cMax}%` }} />
                          <div className={LAYER_BG.thermal} style={{ height: `${(100 * c.thermalNear) / cMax}%` }} />
                        </div>
                      )}
                      {c.quakesObserved === false ? <div className="h-full flex-1 bg-muted opacity-70" title={notObserved} /> : <div className={`flex-1 ${LAYER_BG.quakes}`} style={{ height: `${(100 * c.quakes) / cMax}%` }} />}
                    </div>
                  ))}
                </div>
                <p className="m-0 flex items-baseline gap-ak-0-5 truncate text-ak-base text-muted-foreground">
                  {t("Per month:", "月別:")}
                  <span aria-hidden="true" className={LAYER_TEXT.thermal}>
                    ●
                  </span>
                  {t("thermal", "熱異常")}
                  <span aria-hidden="true" className={LAYER_TEXT.quakes}>
                    ●
                  </span>
                  {t("earthquakes", "地震")}
                </p>
                {gaps ? (
                  <p className="m-0 flex items-baseline gap-ak-0-5 truncate text-ak-base text-muted-foreground" data-embed-not-observed>
                    <span aria-hidden="true" className="text-muted opacity-70">
                      ■
                    </span>
                    {notObserved}
                  </p>
                ) : null}
              </div>
            ) : null}
            <p className={`m-0 text-muted-foreground ${compact ? "truncate text-ak-2xs" : "text-ak-base"}`}>© OpenMapTiles © OpenStreetMap · NASA FIRMS · USGS · Copernicus Sentinel-5P</p>
          </>
        ) : null}
      </aside>
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
