package dev.krtmtthw.plumes.load;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Turns a libpq URL ({@code postgres[ql]://user:pass@host[:port]/db?sslmode=require&channel_binding=require}, the form
 * Neon and dbmate use) into a JDBC URL plus credentials. libpq-only parameters are renamed or dropped.
 */
public record DatabaseUrl(String jdbcUrl, String user, String password) {

    public static Optional<DatabaseUrl> fromEnvironment() {
        String url = System.getenv("DATABASE_URL");
        return url == null || url.isBlank() ? Optional.empty() : Optional.of(parse(url));
    }

    public static DatabaseUrl parse(String url) {
        if (url.startsWith("jdbc:")) {
            return new DatabaseUrl(url, null, null);
        }
        URI uri = URI.create(url);
        if (!"postgres".equals(uri.getScheme()) && !"postgresql".equals(uri.getScheme())) {
            throw new IllegalArgumentException("DATABASE_URL must be a postgres:// URL");
        }
        String user = null;
        String password = null;
        if (uri.getRawUserInfo() != null) {
            String[] parts = uri.getRawUserInfo().split(":", 2);
            user = decode(parts[0]);
            password = parts.length > 1 ? decode(parts[1]) : null;
        }
        List<String> params = new ArrayList<>();
        if (uri.getRawQuery() != null) {
            for (String p : uri.getRawQuery().split("&")) {
                String[] kv = p.split("=", 2);
                switch (kv[0]) {
                    case "sslmode" -> params.add(p);
                    case "channel_binding" -> params.add("channelBinding=" + (kv.length > 1 ? kv[1] : "prefer"));
                    case "options", "application_name", "connect_timeout" -> { } // libpq only; set in config
                    default -> params.add(p);
                }
            }
        }
        String port = uri.getPort() > 0 ? ":" + uri.getPort() : "";
        String jdbc = "jdbc:postgresql://" + uri.getHost() + port + uri.getRawPath()
                + (params.isEmpty() ? "" : "?" + String.join("&", params));
        return new DatabaseUrl(jdbc, user, password);
    }

    private static String decode(String s) {
        return URLDecoder.decode(s, StandardCharsets.UTF_8);
    }

    @Override
    public String toString() {
        return "DatabaseUrl[" + jdbcUrl + ", user=" + user + "]"; // never the password
    }
}
