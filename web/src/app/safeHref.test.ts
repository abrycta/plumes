import { describe, expect, it } from "vitest";

import { safeHref } from "./safeHref";

describe("safeHref", () => {
  it("keeps https links and drops every other scheme", () => {
    expect(safeHref("https://volcano.si.edu/volcano.cfm?vn=273070")).toBe(
      "https://volcano.si.edu/volcano.cfm?vn=273070",
    );
    for (const bad of [
      "http://example.com",
      "javascript:alert(1)",
      "data:text/html,x",
      "//evil.example",
      "",
      null,
      undefined,
    ]) {
      expect(safeHref(bad)).toBeUndefined();
    }
  });
});
