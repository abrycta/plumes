package dev.krtmtthw.plumes;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.JsonSchema;
import com.networknt.schema.JsonSchemaFactory;
import com.networknt.schema.SchemaValidatorsConfig;
import com.networknt.schema.SpecVersion;
import com.networknt.schema.ValidationMessage;

import dev.krtmtthw.plumes.load.DatabaseUrl;
import dev.krtmtthw.plumes.load.Loader;

/**
 * The contract test (ARCHITECTURE-OPTIONS §3.1: API JSON equals static JSON). Loads contracts/fixtures/data with
 * the real loader into a migrated PostGIS (CI: a service container; TEST_DATABASE_URL), then checks that
 * <ul>
 *   <li>/v1/volcanoes and /v1/volcanoes/taal equal the fixture files and validate against their schemas;</li>
 *   <li>the spatial queries reproduce the fixture's own per-day series from the raw points (USGS within 30 km,
 *       VIIRS within 15 km);</li>
 *   <li>ETags, 304s and problem documents behave.</li>
 * </ul>
 */
@SpringBootTest
@AutoConfigureMockMvc
@EnabledIfEnvironmentVariable(named = "TEST_DATABASE_URL", matches = ".+")
class ContractIT {

    static final Path CONTRACTS = Path.of(System.getProperty("plumes.contracts", "../contracts"));
    static final Path DATA = CONTRACTS.resolve("fixtures/data");
    static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);

    @Autowired MockMvc mvc;

    @DynamicPropertySource
    static void database(DynamicPropertyRegistry r) {
        DatabaseUrl db = DatabaseUrl.parse(System.getenv("TEST_DATABASE_URL"));
        r.add("spring.datasource.url", db::jdbcUrl);
        r.add("spring.datasource.username", db::user);
        r.add("spring.datasource.password", db::password);
    }

    @BeforeAll
    static void load() throws Exception {
        Path usgs = Path.of("src/test/resources/usgs-taal-2019-12-2020-02.csv");
        assertThat(LoaderAccess.load(DATA, usgs)).isZero();
    }

    @Test
    void volcanoDetailEqualsTheStaticReadModel() throws Exception {
        JsonNode api = body("/v1/volcanoes/taal", "application/json");
        JsonNode file = JSON.readTree(DATA.resolve("v0/volcano/taal.json").toFile());
        assertThat(canonical(api)).isEqualTo(canonical(file));
        assertThat(validate("volcano.schema.json", api)).isEmpty();
    }

    @Test
    void volcanoListEqualsTheStaticIndex() throws Exception {
        JsonNode api = body("/v1/volcanoes", "application/geo+json");
        JsonNode file = JSON.readTree(DATA.resolve("v0/volcanoes.geojson").toFile());
        assertThat(canonical(api)).isEqualTo(canonical(file));
        assertThat(validate("volcanoes.schema.json", api)).isEmpty();
    }

    @Test
    void earthquakesWithin30kmReproduceTheFixtureSeries() throws Exception {
        JsonNode r = body("/v1/events?volcano=taal&radiusKm=30&from=2019-12-01&to=2020-02-15&kind=earthquake", "application/json");
        JsonNode series = JSON.readTree(DATA.resolve("v0/volcano/taal.json").toFile()).path("events").path("eq_usgs_30km");
        Map<String, Integer> perDay = new HashMap<>();
        Map<String, BigDecimal> maxMag = new HashMap<>();
        for (JsonNode e : r.path("events")) {
            String day = e.path("time").asText().substring(0, 10);
            perDay.merge(day, 1, Integer::sum);
            maxMag.merge(day, e.path("mag").decimalValue(), BigDecimal::max);
        }
        assertThat(r.path("summary").path("earthquake").path("n").asInt()).isEqualTo(56);
        assertThat(perDay).hasSize(series.path("rows").size());
        for (JsonNode row : series.path("rows")) {
            assertThat(perDay.get(row.get(0).asText())).as(row.get(0).asText()).isEqualTo(row.get(1).asInt());
            assertThat(maxMag.get(row.get(0).asText()).compareTo(row.get(2).decimalValue())).isZero();
        }
    }

    @Test
    void viirsDetectionsWithin15kmReproduceTheFixtureSeries() throws Exception {
        JsonNode r = body("/v1/events?volcano=taal&radiusKm=15&from=2020-01-01&to=2020-01-31&kind=thermal", "application/json");
        JsonNode series = JSON.readTree(DATA.resolve("v0/volcano/taal.json").toFile()).path("events").path("fire_viirs_15km");
        Map<String, Integer> perDay = new HashMap<>();
        for (JsonNode e : r.path("events")) {
            if (e.path("sensor").asText().startsWith("VIIRS")) perDay.merge(e.path("date").asText(), 1, Integer::sum);
        }
        Map<String, Integer> expected = new HashMap<>();
        for (JsonNode row : series.path("rows")) expected.put(row.get(0).asText(), row.get(1).asInt());
        assertThat(perDay).isEqualTo(expected);
    }

    @Test
    void nearestAndPrecursors() throws Exception {
        JsonNode n = body("/v1/volcanoes/nearest?lat=14.1&lon=121.0&limit=2", "application/json");
        assertThat(n.path("volcanoes").get(0).path("id").asText()).isEqualTo("taal");
        assertThat(n.path("volcanoes").size()).isEqualTo(2);

        JsonNode p = body("/v1/eruptions/precursors?minVei=4&since=2020-01-01&days=14", "application/json");
        JsonNode taal2020 = p.path("eruptions").get(0);
        assertThat(taal2020.path("episodeId").asText()).isEqualTo("gvp-22344");
        assertThat(taal2020.path("vei").asInt()).isEqualTo(4);

        JsonNode meta = body("/v1/meta", "application/json");
        assertThat(meta.path("dataVersion").asText()).isEqualTo("v0");
        assertThat(meta.path("counts").path("volcanoes").asInt()).isEqualTo(24);
        assertThat(meta.path("counts").path("earthquakes").asInt()).isEqualTo(56);
    }

    @Test
    void etagsAndProblems() throws Exception {
        MvcResult ok = mvc.perform(get("/v1/volcanoes/taal")).andReturn();
        String etag = ok.getResponse().getHeader("ETag");
        assertThat(etag).isEqualTo("W/\"c1.0.0-java-0.1.0-d0\"");
        assertThat(ok.getResponse().getHeader("Cache-Control")).contains("s-maxage=86400").contains("stale-while-revalidate");
        assertThat(mvc.perform(get("/v1/volcanoes/taal").header("If-None-Match", etag)).andReturn().getResponse().getStatus()).isEqualTo(304);

        problem("/v1/volcanoes/nowhere", 404, "not-found");
        problem("/v1/volcanoes/mayon", 404, "not-found"); // known volcano, no file in the fixture
        problem("/v1/events?volcano=taal&radiusKm=500&from=2020-01-01&to=2020-01-02", 400, "invalid-parameter");
        problem("/v1/events?volcano=taal&from=2020-13-01&to=2020-01-02", 400, "invalid-parameter");
        problem("/v1/nothing-here", 404, "not-found");
        assertThat(mvc.perform(get("/readyz")).andReturn().getResponse().getContentAsString()).contains("\"dataVersion\":\"v0\"");
    }

    // ---------------------------------------------------------------------------------------------------------

    private JsonNode body(String url, String type) throws Exception {
        MvcResult r = mvc.perform(get(url)).andReturn();
        assertThat(r.getResponse().getStatus()).as(url + " " + r.getResponse().getContentAsString()).isEqualTo(200);
        assertThat(r.getResponse().getContentType()).startsWith(type);
        return JSON.readTree(r.getResponse().getContentAsByteArray());
    }

    private void problem(String url, int status, String code) throws Exception {
        MvcResult r = mvc.perform(get(url)).andReturn();
        assertThat(r.getResponse().getStatus()).as(url).isEqualTo(status);
        assertThat(r.getResponse().getContentType()).startsWith("application/problem+json");
        JsonNode p = JSON.readTree(r.getResponse().getContentAsByteArray());
        assertThat(p.path("code").asText()).isEqualTo(code);
        assertThat(p.path("type").asText()).isEqualTo("https://plumes.krtmtthw.dev/problems/" + code);
    }

    /** JSON value equality: key order ignored, numbers compared by value (311 equals 311.0). */
    static Object canonical(JsonNode n) {
        if (n.isObject()) {
            Map<String, Object> m = new java.util.TreeMap<>();
            for (Iterator<Map.Entry<String, JsonNode>> it = n.fields(); it.hasNext(); ) {
                var e = it.next();
                m.put(e.getKey(), canonical(e.getValue()));
            }
            return m;
        }
        if (n.isArray()) {
            java.util.List<Object> l = new java.util.ArrayList<>();
            n.forEach(x -> l.add(canonical(x)));
            return l;
        }
        if (n.isNumber()) return n.decimalValue().stripTrailingZeros().toPlainString();
        if (n.isNull()) return "\u0000null";
        return n.asText() + (n.isTextual() ? "" : "\u0000" + n.getNodeType());
    }

    static Set<ValidationMessage> validate(String schema, JsonNode doc) throws Exception {
        String base = "https://plumes.krtmtthw.dev/schemas/";
        JsonSchemaFactory f = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V202012,
                b -> b.schemaMappers(m -> m.mapPrefix(base, CONTRACTS.resolve("schemas").toAbsolutePath().toUri().toString())));
        SchemaValidatorsConfig config = SchemaValidatorsConfig.builder().formatAssertionsEnabled(true).build();
        JsonSchema s = f.getSchema(com.networknt.schema.SchemaLocation.of(base + schema), config);
        return s.validate(doc);
    }

    /** Runs the same loader as `plumes-api load`, against TEST_DATABASE_URL. */
    static final class LoaderAccess {
        static int load(Path data, Path usgs) throws Exception {
            assertThat(Files.isDirectory(data)).as(data.toString()).isTrue();
            return Loader.runWith(System.getenv("TEST_DATABASE_URL"),
                    new String[] {data.toString(), "--usgs", usgs.toString()});
        }
    }
}
