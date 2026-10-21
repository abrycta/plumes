package dev.krtmtthw.plumes.web;

/**
 * Data-derived weak ETags in Replay's form, {@code W/"c{contract}-{impl}-{implVersion}-d{dataVersion}"}: a response
 * changes only with the contract, the build or the data version, so the tag never hashes response bytes.
 */
public final class Etags {

    private Etags() { }

    public static String of(String contract, String impl, String implVersion, String dataVersion) {
        String d = dataVersion.startsWith("v") ? dataVersion.substring(1) : dataVersion;
        return "W/\"c" + contract + "-" + impl + "-" + implVersion + "-d" + d + "\"";
    }

    /** Weak comparison (RFC 9110 §8.8.3.2) of an If-None-Match list against our tag. */
    public static boolean matches(String ifNoneMatch, String etag) {
        if (ifNoneMatch == null || ifNoneMatch.isBlank()) return false;
        String ours = opaque(etag);
        for (String candidate : ifNoneMatch.split(",")) {
            String c = candidate.trim();
            if (c.equals("*") || opaque(c).equals(ours)) return true;
        }
        return false;
    }

    private static String opaque(String tag) {
        return tag.startsWith("W/") ? tag.substring(2) : tag;
    }
}
