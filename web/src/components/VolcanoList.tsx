import { Input, Label, Sparkline, T, useLang, useT } from "@abrycta/akari/react";
import { useId, useMemo, useState } from "react";

import type { VolcanoesIndex } from "@contracts/readmodels";

import { AppLink } from "@/app/Link";
import { filterVolcanoes, sortVolcanoes } from "@/data/volcanoes";
import { formatDate } from "@/lib/dates";

/** `links={false}`: names as plain text (the /embed carries no links); `first`: that volcano leads the list, outlined. */
export function VolcanoList({ index, compact, links = true, first, limit }: { index: VolcanoesIndex; compact?: boolean; links?: boolean; first?: string; limit?: number }) {
  const t = useT();
  const { lang } = useLang();
  const [q, setQ] = useState("");
  const id = useId();
  const rows = useMemo(() => {
    const r = filterVolcanoes(sortVolcanoes(index.features, lang), q);
    return first ? [...r.filter((f) => f.properties.id === first), ...r.filter((f) => f.properties.id !== first)] : r;
  }, [index, lang, q, first]);
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={id}>{t("Find a volcano", "火山を探す")}</Label>
        <Input id={id} type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("Taal, Mayon, Kanlaon…", "タール、マヨン、カンラオン…")} autoComplete="off" />
      </div>
      <p className="m-0 text-xs text-muted-foreground" aria-live="polite">
        {t(`${rows.length} of ${index.features.length} volcanoes · most recent eruption (GVP) first`, `${index.features.length}火山中${rows.length} · 最近の噴火(GVP)順`)}
      </p>
      <ul className={`m-0 grid list-none items-start gap-2 p-0 ${compact ? "" : "sm:grid-cols-2 lg:grid-cols-3"}`}>
        {rows.slice(0, limit).map((f) => {
          const p = f.properties;
          const monthly = p.monthly ? Object.entries(p.monthly)[0] : undefined;
          return (
            <li key={p.id} className={`grid gap-1 rounded-sm border bg-card p-3 ${p.id === first ? "border-foreground" : "border-border"}`} data-volcano={p.id}>
              <div className="flex items-baseline justify-between gap-2">
                {links ? (
                  <AppLink to="volcano" id={p.id} className="font-medium underline-offset-4 hover:underline">
                    {p.name[lang]}
                  </AppLink>
                ) : (
                  <span className="font-medium">{p.name[lang]}</span>
                )}
                <span className={`text-[11px] ${p.coverage === "deep" ? "text-seal-text" : "text-muted-foreground"}`}>{p.coverage === "deep" ? t("Bulletins + satellites", "火山情報+衛星") : t("Satellites + history", "衛星+噴火史")}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {p.lastEruption?.start ? (
                  <>
                    <T en="Last eruption" ja="最後の噴火" /> {formatDate(p.lastEruption.start, lang)}
                    {p.lastEruption.vei != null ? ` · VEI ${p.lastEruption.vei}` : ""} (GVP)
                  </>
                ) : (
                  <T en="No dated eruption in GVP" ja="GVPに日付のある噴火記録なし" />
                )}
                {p.eruptionsSince1900 != null ? (
                  <>
                    {" · "}
                    {t(`${p.eruptionsSince1900} ${p.eruptionsSince1900 === 1 ? "eruption" : "eruptions"} since 1900`, `1900年以降${p.eruptionsSince1900}回`)}
                  </>
                ) : null}
              </span>
              {monthly ? <Sparkline values={monthly[1].values} label={t(`${monthly[0]} monthly from ${monthly[1].start}`, `${monthly[0]}(${monthly[1].start}からの月別)`)} height={24} /> : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
