import { AkariProvider } from "@abrycta/akari/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { PlumesHeader } from "./Shell";
import { parseUrl } from "./url";

// Drift guard (Akari README): Plumes renders Akari's one menu bar, once, with at most one current item.
function render(path: string, search = "") {
  return renderToStaticMarkup(
    <AkariProvider toaster={false} inlineScript={false}>
      <PlumesHeader url={parseUrl(path, search)} />
    </AkariProvider>,
  );
}
const count = (html: string, re: RegExp) => html.match(re)?.length ?? 0;

describe("PlumesHeader", () => {
  it.each([
    ["/", "", "Map", "page"],
    ["/volcanoes", "", "Volcanoes", "page"],
    ["/volcano/taal", "?date=2020-01-12", "Volcanoes", "true"],
    ["/stories", "", "Stories", "page"],
    ["/story/taal-2020", "?lang=ja", "Stories", "true"],
    ["/about", "", "About &amp; sources", "page"],
    ["/nope", "", null, null],
  ] as const)("%s%s → %s", (path, search, label, aria) => {
    const html = render(path, search);
    expect(count(html, /<header[^>]*data-akari-header=""/g)).toBe(1);
    expect(html).toContain("噴");
    expect(count(html, /data-current=""/g)).toBe(label ? 1 : 0);
    if (label) {
      const cur = /<a [^>]*aria-current="([^"]+)"[^>]*data-current=""[^>]*>([^<]*)<\/a>/.exec(html);
      expect([cur?.[2], cur?.[1]]).toEqual([label, aria]);
    }
    expect(html).toContain('href="https://krtmtthw.dev"');
  });
});
