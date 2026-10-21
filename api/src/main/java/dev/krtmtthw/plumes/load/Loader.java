package dev.krtmtthw.plumes.load;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.sql.Types;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * Loads one published data version (contracts/README.md) into PostGIS, atomically: everything is replaced in one
 * transaction, so the API serves either the old version or the new one, never a mix.
 *
 * <pre>
 * plumes-api load &lt;data-dir | base URL&gt; [--usgs comcat.csv]... [--firms firms.csv]... [--dry-run]
 * </pre>
 *
 * The argument is the folder or URL that holds {@code latest.json} (for example {@code contracts/fixtures/data} or
 * the GitHub Pages data root). Earthquakes are not part of the read models at M1, so they come from USGS ComCat CSV
 * files ({@code --usgs}, the FDSN {@code format=csv} columns). Thermal detections come from the published
 * {@code thermal-detections} layer when it is GeoJSON, and from FIRMS area-API CSV files ({@code --firms}).
 */
public final class Loader {

    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS); // keep published numbers as written

    private final Source source;
    private final List<Path> usgs;
    private final List<Path> firms;

    Loader(Source source, List<Path> usgs, List<Path> firms) {
        this.source = source;
        this.usgs = usgs;
        this.firms = firms;
    }

    public static int run(String[] args) throws Exception {
        return runWith(System.getenv("DATABASE_URL"), args);
    }

    /** {@code databaseUrl}: a postgres:// or jdbc: URL. */
    public static int runWith(String databaseUrl, String[] args) throws Exception {
        String where = null;
        List<Path> usgs = new ArrayList<>();
        List<Path> firms = new ArrayList<>();
        boolean dryRun = false;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--usgs" -> usgs.add(Path.of(args[++i]));
                case "--firms" -> firms.add(Path.of(args[++i]));
                case "--dry-run" -> dryRun = true;
                default -> where = args[i];
            }
        }
        if (where == null) {
            System.err.println("usage: plumes-api load <data-dir|base-url> [--usgs file.csv]... [--firms file.csv]... [--dry-run]");
            return 2;
        }
        Loader loader = new Loader(Source.of(where), usgs, firms);
        Version v = loader.read();
        System.out.printf("read %s: %d volcanoes (%d with a file), %d episodes, %d events%n", v.dataVersion,
                v.volcanoes.size(), v.volcanoes.stream().filter(x -> x.detail != null).count(), v.episodes.size(), v.events.size());
        if (dryRun) {
            return 0;
        }
        if (databaseUrl == null || databaseUrl.isBlank()) throw new IllegalStateException("DATABASE_URL is not set");
        DatabaseUrl db = DatabaseUrl.parse(databaseUrl);
        try (Connection c = connect(db)) {
            write(c, v, where);
        }
        System.out.println("loaded " + v.dataVersion);
        return 0;
    }

    static Connection connect(DatabaseUrl db) throws SQLException {
        Properties p = new Properties();
        if (db.user() != null) p.setProperty("user", db.user());
        if (db.password() != null) p.setProperty("password", db.password());
        p.setProperty("reWriteBatchedInserts", "true");
        p.setProperty("connectTimeout", "30");
        return DriverManager.getConnection(db.jdbcUrl(), p);
    }

    // ---------------------------------------------------------------------------------------------------------
    // Reading

    record VolcanoRow(String id, int ord, Integer gvpNumber, String nameEn, String nameJa, double lat, double lon,
                      Double elevationM, boolean observatory, String coverage, String feature, String detail) { }

    record EpisodeRow(String volcanoId, String id, String kind, String startText, LocalDate startDay, String endText,
                      Integer vei, Double so2MassKt, Double plumeAltKm, Integer maxAlert) { }

    record EventRow(String kind, String extId, Instant t, LocalDate day, double lat, double lon, Float mag,
                    String magType, Float depthKm, Float frpMw, String sensor, Integer fireType, String source) { }

    static final class Version {
        String dataVersion;
        LocalDate dataAsOf;
        OffsetDateTime generatedAt;
        boolean fixture;
        String indexHeader;
        final List<VolcanoRow> volcanoes = new ArrayList<>();
        final List<EpisodeRow> episodes = new ArrayList<>();
        final List<EventRow> events = new ArrayList<>();
    }

    Version read() throws IOException, InterruptedException {
        JsonNode latest = JSON.readTree(source.text("latest.json"));
        String base = latest.path("base").asText();
        Version v = new Version();
        v.dataVersion = latest.path("current").asText();
        require(base.equals(v.dataVersion + "/"), "latest.json base must be <current>/");

        JsonNode index = JSON.readTree(source.text(base + "volcanoes.geojson"));
        checkHeader(index, "volcanoes", v.dataVersion);
        v.dataAsOf = LocalDate.parse(index.path("dataAsOf").asText());
        v.generatedAt = OffsetDateTime.parse(index.path("generatedAt").asText());
        v.fixture = index.path("fixture").asBoolean(false);
        ObjectNode header = ((ObjectNode) index).deepCopy();
        header.remove("features");
        v.indexHeader = JSON.writeValueAsString(header);

        int ord = 0;
        for (JsonNode f : index.path("features")) {
            JsonNode p = f.path("properties");
            String id = p.path("id").asText();
            String file = p.path("file").asText(null);
            String detail = file == null ? null : source.textIfPresent(base + file);
            if (detail != null) {
                JsonNode doc = JSON.readTree(detail);
                checkHeader(doc, "volcano", v.dataVersion);
                require(id.equals(doc.path("volcano").path("id").asText()), "volcano id mismatch in " + file);
                for (JsonNode e : doc.path("episodes")) {
                    String start = e.path("start").asText();
                    v.episodes.add(new EpisodeRow(id, e.path("id").asText(), e.path("kind").asText(), start,
                            start.matches("\\d{4}-\\d{2}-\\d{2}") ? LocalDate.parse(start) : null,
                            text(e, "end"), integer(e, "vei"), number(e, "so2MassKt"), number(e, "plumeAltKm"),
                            integer(e, "maxAlert")));
                }
            }
            JsonNode coords = f.path("geometry").path("coordinates");
            v.volcanoes.add(new VolcanoRow(id, ord++, integer(p, "gvpNumber"), p.path("name").path("en").asText(),
                    p.path("name").path("ja").asText(), coords.get(1).asDouble(), coords.get(0).asDouble(),
                    number(p, "elevationM"), p.path("observatory").asBoolean(), p.path("coverage").asText(),
                    JSON.writeValueAsString(f), detail));
        }
        require(!v.volcanoes.isEmpty(), "no volcanoes in volcanoes.geojson");

        readThermalLayer(base, v);
        for (Path p : firms) readFirmsCsv(p, v);
        for (Path p : usgs) readUsgsCsv(p, v);
        dedupe(v.events);
        return v;
    }

    private void readThermalLayer(String base, Version v) throws IOException, InterruptedException {
        String layersText = source.textIfPresent(base + "layers.json");
        if (layersText == null) return;
        for (JsonNode layer : JSON.readTree(layersText).path("layers")) {
            if (!layer.path("id").asText().equals("thermal-detections") || !layer.path("format").asText().equals("geojson")) {
                continue;
            }
            String source = layer.path("sources").path(0).asText("firms-modis");
            for (JsonNode month : layer.path("time").path("available")) {
                String path = base + layer.path("url").asText().replace("{month}", month.asText());
                for (JsonNode f : JSON.readTree(this.source.text(path)).path("features")) {
                    JsonNode p = f.path("properties");
                    JsonNode c = f.path("geometry").path("coordinates");
                    addThermal(v, LocalDate.parse(p.path("date").asText()), c.get(1).asDouble(), c.get(0).asDouble(),
                            (float) p.path("frp").asDouble(), p.path("sensor").asText(null), integer(p, "type"), source);
                }
            }
        }
    }

    private static void addThermal(Version v, LocalDate day, double lat, double lon, Float frp, String sensor,
                                   Integer type, String source) {
        String id = sensor + "/" + day + "/" + lat + "/" + lon;
        v.events.add(new EventRow("thermal", id, day.atStartOfDay().toInstant(ZoneOffset.UTC), day, lat, lon,
                null, null, null, frp, sensor, type, source));
    }

    /** FIRMS area-API CSV (latitude, longitude, acq_date, instrument/satellite, frp, type). */
    private static void readFirmsCsv(Path p, Version v) throws IOException {
        // The area API ends each response without a newline, so concatenated responses glue the next header onto
        // the last row (DECISIONS B5): split on the header and drop its repeats.
        String text = Files.readString(p);
        String header = text.lines().findFirst().orElse("");
        String body = text.substring(header.length()).replace(header, "\n");
        List<Map<String, String>> rows = Csv.read(header + body);
        String sensorHint = p.getFileName().toString().replaceFirst("^firms_", "").replaceFirst("\\.csv$", "");
        for (Map<String, String> r : rows) {
            String type = r.get("type");
            addThermal(v, LocalDate.parse(r.get("acq_date")), Double.parseDouble(r.get("latitude")),
                    Double.parseDouble(r.get("longitude")), Float.parseFloat(r.get("frp")), sensorHint,
                    type == null || type.isBlank() ? null : Integer.valueOf(type), "firms-modis");
        }
    }

    /** USGS ComCat FDSN CSV. Events before 2010 come from usgs-comcat-ph-1900-2009, the rest from -2010. */
    private static void readUsgsCsv(Path p, Version v) throws IOException {
        for (Map<String, String> r : Csv.read(Files.readString(p))) {
            if (!"earthquake".equals(r.getOrDefault("type", "earthquake"))) continue;
            Instant t = Instant.parse(r.get("time"));
            LocalDate day = t.atOffset(ZoneOffset.UTC).toLocalDate();
            v.events.add(new EventRow("earthquake", r.get("id"), t, day, Double.parseDouble(r.get("latitude")),
                    Double.parseDouble(r.get("longitude")), floatOrNull(r.get("mag")), blankToNull(r.get("magType")),
                    floatOrNull(r.get("depth")), null, null, null,
                    day.getYear() < 2010 ? "usgs-comcat-ph-1900-2009" : "usgs-comcat-ph-2010"));
        }
    }

    private static void dedupe(List<EventRow> events) {
        Set<String> seen = new HashSet<>();
        events.removeIf(e -> !seen.add(e.kind + "\u0000" + e.extId));
    }

    private static void checkHeader(JsonNode doc, String kind, String version) {
        require("1".equals(doc.path("schemaVersion").asText()), kind + ": schemaVersion must be \"1\"");
        require(kind.equals(doc.path("kind").asText()), "expected kind " + kind);
        require(version.equals(doc.path("dataVersion").asText()), kind + ": dataVersion differs from latest.json");
    }

    // ---------------------------------------------------------------------------------------------------------
    // Writing: one transaction

    static void write(Connection c, Version v, String where) throws SQLException {
        c.setAutoCommit(false);
        try (Statement s = c.createStatement()) {
            s.execute("SET LOCAL statement_timeout = '300s'");
            // DELETE, not TRUNCATE: readers keep seeing the previous version (MVCC) until the commit.
            s.execute("DELETE FROM event");
            s.execute("DELETE FROM episode");
            s.execute("DELETE FROM volcano");
            s.execute("DELETE FROM dataset");
        }
        try (PreparedStatement ps = c.prepareStatement("""
                INSERT INTO dataset (data_version, data_as_of, generated_at, fixture, source, index_header)
                VALUES (?, ?, ?, ?, ?, ?::json)""")) {
            ps.setString(1, v.dataVersion);
            ps.setObject(2, v.dataAsOf);
            ps.setObject(3, v.generatedAt);
            ps.setBoolean(4, v.fixture);
            ps.setString(5, where.startsWith("http") ? where : "local:" + Path.of(where).getFileName());
            ps.setString(6, v.indexHeader);
            ps.executeUpdate();
        }
        try (PreparedStatement ps = c.prepareStatement("""
                INSERT INTO volcano (id, ord, gvp_number, name_en, name_ja, lat, lon, geog, elevation_m, observatory,
                                     coverage, feature, detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ST_SetSRID(ST_MakePoint(?, ?), 4326)::geography, ?, ?, ?, ?::json, ?::json)""")) {
            for (VolcanoRow r : v.volcanoes) {
                ps.setString(1, r.id);
                ps.setInt(2, r.ord);
                ps.setObject(3, r.gvpNumber, Types.INTEGER);
                ps.setString(4, r.nameEn);
                ps.setString(5, r.nameJa);
                ps.setDouble(6, r.lat);
                ps.setDouble(7, r.lon);
                ps.setDouble(8, r.lon);
                ps.setDouble(9, r.lat);
                ps.setObject(10, r.elevationM, Types.DOUBLE);
                ps.setBoolean(11, r.observatory);
                ps.setString(12, r.coverage);
                ps.setString(13, r.feature);
                ps.setString(14, r.detail);
                ps.addBatch();
            }
            ps.executeBatch();
        }
        try (PreparedStatement ps = c.prepareStatement("""
                INSERT INTO episode (volcano_id, id, kind, start_text, start_day, end_text, vei, so2_mass_kt,
                                     plume_alt_km, max_alert) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""")) {
            for (EpisodeRow r : v.episodes) {
                ps.setString(1, r.volcanoId);
                ps.setString(2, r.id);
                ps.setString(3, r.kind);
                ps.setString(4, r.startText);
                ps.setObject(5, r.startDay, Types.DATE);
                ps.setString(6, r.endText);
                ps.setObject(7, r.vei, Types.INTEGER);
                ps.setObject(8, r.so2MassKt, Types.DOUBLE);
                ps.setObject(9, r.plumeAltKm, Types.DOUBLE);
                ps.setObject(10, r.maxAlert, Types.INTEGER);
                ps.addBatch();
            }
            ps.executeBatch();
        }
        try (PreparedStatement ps = c.prepareStatement("""
                INSERT INTO event (kind, ext_id, t, day, lat, lon, geog, mag, mag_type, depth_km, frp_mw, sensor,
                                   fire_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ST_SetSRID(ST_MakePoint(?, ?), 4326)::geography, ?, ?, ?, ?, ?, ?, ?)""")) {
            int n = 0;
            for (EventRow r : v.events) {
                ps.setString(1, r.kind);
                ps.setString(2, r.extId);
                ps.setTimestamp(3, Timestamp.from(r.t));
                ps.setObject(4, r.day);
                ps.setDouble(5, r.lat);
                ps.setDouble(6, r.lon);
                ps.setDouble(7, r.lon);
                ps.setDouble(8, r.lat);
                ps.setObject(9, r.mag, Types.REAL);
                ps.setString(10, r.magType);
                ps.setObject(11, r.depthKm, Types.REAL);
                ps.setObject(12, r.frpMw, Types.REAL);
                ps.setString(13, r.sensor);
                ps.setObject(14, r.fireType, Types.SMALLINT);
                ps.setString(15, r.source);
                ps.addBatch();
                if (++n % 5000 == 0) ps.executeBatch();
            }
            ps.executeBatch();
        }
        c.commit();
        c.setAutoCommit(true);
        try (Statement s = c.createStatement()) {
            s.execute("ANALYZE volcano; ANALYZE episode; ANALYZE event");
        }
    }

    // ---------------------------------------------------------------------------------------------------------

    private static String text(JsonNode n, String field) {
        JsonNode x = n.get(field);
        return x == null || x.isNull() ? null : x.asText();
    }

    private static Integer integer(JsonNode n, String field) {
        JsonNode x = n.get(field);
        return x == null || x.isNull() ? null : x.asInt();
    }

    private static Double number(JsonNode n, String field) {
        JsonNode x = n.get(field);
        return x == null || x.isNull() ? null : x.asDouble();
    }

    private static Float floatOrNull(String s) {
        return s == null || s.isBlank() ? null : Float.valueOf(s);
    }

    private static String blankToNull(String s) {
        return s == null || s.isBlank() ? null : s;
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new IllegalStateException(message);
    }

    /** A data root on disk or over HTTPS. */
    interface Source {
        String textIfPresent(String path) throws IOException, InterruptedException;

        default String text(String path) throws IOException, InterruptedException {
            String t = textIfPresent(path);
            if (t == null) throw new IOException("missing " + path);
            return t;
        }

        static Source of(String where) {
            if (where.startsWith("https://") || where.startsWith("http://")) {
                String root = where.endsWith("/") ? where : where + "/";
                HttpClient http = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL)
                        .connectTimeout(Duration.ofSeconds(20)).build();
                return path -> {
                    HttpResponse<String> r = http.send(HttpRequest.newBuilder(URI.create(root + path))
                            .timeout(Duration.ofSeconds(60)).header("User-Agent", "plumes-api-loader").build(),
                            HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
                    if (r.statusCode() == 404) return null;
                    if (r.statusCode() != 200) throw new IOException(path + ": HTTP " + r.statusCode());
                    return r.body();
                };
            }
            Path root = Path.of(where);
            return path -> {
                Path p = root.resolve(path).normalize();
                if (!p.startsWith(root.normalize())) throw new IOException("path escapes the data root: " + path);
                return Files.exists(p) ? Files.readString(p, StandardCharsets.UTF_8) : null;
            };
        }
    }
}
