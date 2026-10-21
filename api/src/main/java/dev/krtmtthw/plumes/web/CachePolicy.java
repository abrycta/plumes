package dev.krtmtthw.plumes.web;

/**
 * Cache-Control by resource class (DATA-PLAN §8). Data only changes when a new version is loaded (weekly), so the
 * edge keeps reads for a day and serves them stale for a week while it revalidates with the dataset ETag.
 */
public final class CachePolicy {

    public static final String DATA = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800, stale-if-error=604800";
    public static final String META = "public, max-age=60, s-maxage=600, stale-while-revalidate=86400";
    public static final String NOT_FOUND = "public, max-age=60, s-maxage=3600";
    public static final String NO_STORE = "no-store";

    private CachePolicy() { }
}
