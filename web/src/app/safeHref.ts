/** A URL from the data, only when it is https: (the schemas require it; this guards the page as well). */
export function safeHref(url: string | null | undefined): string | undefined {
  return typeof url === "string" && url.startsWith("https://")
    ? url
    : undefined;
}
