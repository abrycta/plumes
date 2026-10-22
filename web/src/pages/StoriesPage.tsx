import { Alert, AlertDescription, AlertTitle, Page, useLang, useT } from "@abrycta/akari/react";
import { use, useEffect } from "react";

import { AppLink } from "@/app/Link";
import { DraftBadge } from "@/components/FigureList";
import { useUrlState } from "@/app/url";
import { loadStoriesIndex, loadStoryFile, type StoryRef, storyRefs } from "@/data/load";
import { formatRange } from "@/lib/dates";

function StoryCard({ entry }: { entry: StoryRef }) {
  const { lang } = useLang();
  const story = use(loadStoryFile(entry.file));
  if (!story) return null;
  return (
    <li className="flex flex-col gap-1 rounded-sm border border-border bg-card p-4" data-story-card={entry.status}>
      <AppLink to="story" id={entry.id} className="font-heading text-xl font-semibold underline-offset-4 hover:underline">
        {story.title[lang]}
      </AppLink>
      <span className="text-sm text-muted-foreground">{formatRange(story.span.start, story.span.end, lang)}</span>
      <DraftBadge status={entry.status} />
      {story.summary ? <p className="m-0 text-sm">{story.summary[lang]}</p> : null}
    </li>
  );
}

export default function StoriesPage() {
  const t = useT();
  const { preview } = useUrlState();
  const entries = storyRefs(use(loadStoriesIndex()), Boolean(preview));
  useEffect(() => {
    document.title = `${t("Stories", "ストーリー")} · Plumes`;
  }, [t]);
  return (
    <Page title={t("Stories", "ストーリー")} lede={t("Past eruptions told step by step, every number linked to its source and date.", "過去の噴火を一歩ずつ。すべての数値に出典と日付のリンク付き。")}>
      {preview ? (
        <Alert data-stories-preview>
          <AlertTitle>{t("Preview", "プレビュー")}</AlertTitle>
          <AlertDescription>
            {t(
              "This list includes drafts generated from the data. They are not reviewed yet and are hidden without the preview link.",
              "この一覧には、データから生成した下書きが含まれます。まだレビューされておらず、プレビュー用のリンクがなければ表示されません。",
            )}
          </AlertDescription>
        </Alert>
      ) : null}
      <ul className="m-0 grid list-none items-start gap-3 p-0 sm:grid-cols-2">
        {entries.map((s) => (
          <StoryCard key={s.id} entry={s} />
        ))}
      </ul>
    </Page>
  );
}
