import { T, useLang } from "@abrycta/akari/react";

import { formatDate } from "@/lib/dates";

/** "Data through <date>" (RESEARCH.md §9 rule 2): on every chart and map. The record ends here; nothing is live. */
export function DataThrough({ date, className }: { date: string; className?: string }) {
  const { lang } = useLang();
  return (
    <span data-data-through className={className ?? "font-mono text-[11px] tracking-wide text-muted-foreground uppercase"}>
      <T en="Data through" ja="データの最終日" /> <time dateTime={date}>{formatDate(date, lang)}</time>
    </span>
  );
}
