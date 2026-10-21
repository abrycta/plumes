import { describe, expect, it } from "vitest";

import { formatUrl, parseUrl } from "./url";

describe("url", () => {
  it.each([
    ["/", "map", null],
    ["/volcanoes", "volcanoes", null],
    ["/volcano/taal", "volcano", "taal"],
    ["/story/taal-2020", "story", "taal-2020"],
    ["/about", "about", null],
    ["/volcano/../x", "notfound", null],
    ["/volcano/Taal!", "notfound", null],
    ["/nope", "notfound", null],
  ])("%s", (path, page, id) => {
    expect(parseUrl(path, "")).toMatchObject({ page, id });
  });
  it("round-trips view state and drops junk", () => {
    const s = parseUrl("/volcano/taal", "?from=2020-01-05&to=2020-02-02&date=2020-01-12&ring=15&lang=ja&x=1");
    expect(formatUrl(s)).toBe("/volcano/taal?from=2020-01-05&to=2020-02-02&date=2020-01-12&ring=15&lang=ja");
    expect(parseUrl("/", "?date=12-01-2020&ring=-3&lang=fr")).toMatchObject({ date: null, ring: null, lang: null });
  });
});
