import { useLang, useT } from "@abrycta/akari/react";

import type { Figure } from "@contracts/readmodels";

import { ExtLink } from "@/app/Link";
import { useUrlState } from "@/app/url";
import { formatDate } from "@/lib/dates";
import { formatNumber } from "@/lib/format";

/** Cited numbers: value, unit, date and source; PHIVOLCS, VAAC and DROMIC figures link to their page. */
export function FigureList({ figures }: { figures: Figure[] }) {
  const t = useT();
  const { lang } = useLang();
  if (!figures.length) return null;
  return (
    <dl className="m-0 grid gap-x-6 gap-y-2 sm:grid-cols-2">
      {figures.map((f, i) => (
        <div key={i} className="flex flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">{f.label[lang]}</dt>
          <dd className="m-0">
            <span className="font-heading text-xl font-semibold tabular">{typeof f.value === "number" ? formatNumber(f.value, lang) : f.value}</span>
            {f.unit ? <span className="text-sm"> {f.unit}</span> : null}
            <span className="block text-xs text-muted-foreground">
              {f.asOf ? `${f.source === "phivolcs-bulletins" || f.source === "phivolcs-lava-bulletins" ? t("as reported by PHIVOLCS on", "PHIVOLCS発表") : t("as of", "時点")} ${formatDate(f.asOf, lang)} · ` : ""}
              {f.url ? <ExtLink href={f.url}>{f.source}</ExtLink> : f.source}
            </span>
            {f.note ? <span className="block text-xs text-muted-foreground">{f.note[lang]}</span> : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** "Draft" until Kurt has reviewed both languages (contracts README). */
export function DraftBadge({ status }: { status?: "draft" | "reviewed" }) {
  const t = useT();
  const { preview } = useUrlState();
  if (status !== "draft" || !preview) return null;
  return <span className="self-start rounded-sm border border-dashed border-border px-1.5 text-[11px] text-muted-foreground">{t("Draft text, not yet reviewed", "下書き(未レビュー)")}</span>;
}
