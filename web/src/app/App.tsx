import { AkariProvider } from "@abrycta/akari/react";
import { lazy, Suspense } from "react";

import { ErrorBoundary } from "./ErrorBoundary";
import { PageGlyph } from "./PageGlyph";
import { Shell } from "./Shell";
import { parseUrl, useUrlState } from "./url";

/** Theme and contrast are shared with every *.krtmtthw.dev app (index.html loads the matching theme-init.js). */
export const THEME_COOKIE_DOMAIN = "krtmtthw.dev";

const MapPage = lazy(() => import("@/pages/MapPage"));
const VolcanoesPage = lazy(() => import("@/pages/VolcanoesPage"));
const VolcanoPage = lazy(() => import("@/pages/VolcanoPage"));
const StoriesPage = lazy(() => import("@/pages/StoriesPage"));
const StoryPage = lazy(() => import("@/pages/StoryPage"));
const AboutPage = lazy(() => import("@/pages/AboutPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function initialLang(): "en" | "ja" {
  const fromUrl = parseUrl(location.pathname, location.search).lang;
  if (fromUrl) return fromUrl;
  return navigator.language?.toLowerCase().startsWith("ja") ? "ja" : "en";
}

function Pages() {
  const { page, id } = useUrlState();
  let el;
  switch (page) {
    case "map":
      el = <MapPage />;
      break;
    case "volcanoes":
      el = <VolcanoesPage />;
      break;
    case "volcano":
      el = <VolcanoPage id={id!} />;
      break;
    case "stories":
      el = <StoriesPage />;
      break;
    case "story":
      el = <StoryPage id={id!} />;
      break;
    case "about":
      el = <AboutPage />;
      break;
    default:
      el = <NotFoundPage />;
  }
  return (
    <ErrorBoundary key={`${page}/${id ?? ""}`}>
      <Suspense fallback={<PageGlyph />}>{el}</Suspense>
    </ErrorBoundary>
  );
}

export function App() {
  return (
    <AkariProvider defaultLang={initialLang()} toaster={false} sharedCookieDomain={THEME_COOKIE_DOMAIN} inlineScript={false}>
      <Shell>
        <Pages />
      </Shell>
    </AkariProvider>
  );
}
