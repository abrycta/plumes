import type { AnchorHTMLAttributes, MouseEvent } from "react";

import { safeHref } from "./safeHref";
import { formatUrl, navigateHref, type Page, type UrlState, useUrlState } from "./url";

/** In-app link: a real href (open in a new tab works), client-side navigation on plain clicks. */
export function AppLink({ to, id, query, onClick, ...rest }: AnchorHTMLAttributes<HTMLAnchorElement> & { to: Exclude<Page, "notfound">; id?: string | null; query?: Partial<UrlState> }) {
  const url = useUrlState();
  const href = formatUrl({ page: to, id: id ?? null, lang: url.lang, date: null, from: null, to: null, ring: null, preview: url.preview, ...query });
  const click = (e: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    navigateHref(href);
    window.scrollTo(0, 0);
  };
  return <a {...rest} href={href} onClick={click} />;
}

/** External link: new tab, with the ↗ mark announced as part of the name. A non-https href renders as plain text. */
export function ExtLink({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
  if (!safeHref(href)) return <span className={className}>{children}</span>;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className ?? "underline underline-offset-4 hover:text-foreground"}>
      {children}
      <span aria-hidden="true"> ↗</span>
    </a>
  );
}
