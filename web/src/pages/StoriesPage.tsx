import { Page, useLang, useT } from "@abrycta/akari/react";
import { use, useEffect } from "react";

import { AppLink } from "@/app/Link";
import { loadStory, STORIES } from "@/data/load";
import { formatRange } from "@/lib/dates";

function StoryCard({ id }: { id: string }) {
  const { lang } = useLang();
  const story = use(loadStory(id));
  return (
    <li className="flex flex-col gap-1 rounded-sm border border-border bg-card p-4">
      <AppLink to="story" id={id} className="font-heading text-xl font-semibold underline-offset-4 hover:underline">
        {story.title[lang]}
      </AppLink>
      <span className="text-sm text-muted-foreground">{formatRange(story.span.start, story.span.end, lang)}</span>
      {story.summary ? <p className="m-0 text-sm">{story.summary[lang]}</p> : null}
    </li>
  );
}

export default function StoriesPage() {
  const t = useT();
  useEffect(() => {
    document.title = `${t("Stories", "ストーリー")} · Plumes`;
  }, [t]);
  return (
    <Page width="full" title={t("Stories", "ストーリー")} lede={t("Past eruptions told step by step, every number linked to its source and date.", "過去の噴火を一歩ずつ。すべての数値に出典と日付のリンク付き。")}>
      <ul className="m-0 grid list-none items-start gap-3 p-0 sm:grid-cols-2">
        {STORIES.map((s) => (
          <StoryCard key={s.id} id={s.id} />
        ))}
      </ul>
    </Page>
  );
}
