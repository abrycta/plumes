package dev.krtmtthw.plumes.web;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.List;

import jakarta.servlet.http.HttpServletRequest;

import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.context.annotation.ImportRuntimeHints;
import org.springframework.core.io.ClassPathResource;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import dev.krtmtthw.plumes.catalogue.CatalogueService;
import dev.krtmtthw.plumes.catalogue.CatalogueService.Center;
import dev.krtmtthw.plumes.catalogue.CatalogueService.EventsResult;
import dev.krtmtthw.plumes.catalogue.CatalogueService.NotFound;
import dev.krtmtthw.plumes.catalogue.Model.Counts;
import dev.krtmtthw.plumes.catalogue.Model.Dataset;
import dev.krtmtthw.plumes.catalogue.Model.Document;
import dev.krtmtthw.plumes.catalogue.Model.Event;
import dev.krtmtthw.plumes.catalogue.Model.EventSummary;
import dev.krtmtthw.plumes.catalogue.Model.NearbyVolcano;
import dev.krtmtthw.plumes.catalogue.Model.Precursor;

/**
 * The driving adapter: {@code /v1} reads (contracts/openapi.yaml). The volcano list and detail are the published
 * read models (volcanoes.schema.json, volcano.schema.json) as loaded; the other reads are spatial-temporal queries.
 * JSON is written with Jackson trees, so the native image needs no reflection metadata for response types.
 */
@RestController
@RequestMapping("/v1")
@ImportRuntimeHints(CatalogueController.Hints.class)
public class CatalogueController {

    /** The OpenAPI document is a classpath resource: native images include only declared resources. */
    static final class Hints implements RuntimeHintsRegistrar {
        @Override
        public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
            hints.resources().registerPattern("contract/openapi.yaml");
        }
    }

    static final MediaType GEO_JSON = MediaType.parseMediaType("application/geo+json");

    private final CatalogueService service;
    private final DatasetCache dataset;
    private final ApiInfo info;
    private final ObjectMapper json;

    public CatalogueController(CatalogueService service, DatasetCache dataset, ApiInfo info, ObjectMapper json) {
        this.service = service;
        this.dataset = dataset;
        this.info = info;
        this.json = json;
    }

    @GetMapping("/meta")
    ResponseEntity<String> meta(HttpServletRequest request) {
        Dataset d = dataset.require();
        return cached(request, d, CachePolicy.META, MediaType.APPLICATION_JSON, () -> {
            Counts c = service.repository().counts();
            ObjectNode n = json.createObjectNode();
            n.put("impl", ApiInfo.IMPL).put("implVersion", info.implVersion()).put("contract", ApiInfo.CONTRACT)
                    .put("schemaVersion", "1").put("commit", info.commit());
            header(n, d);
            n.put("source", d.source()).put("loadedAt", d.loadedAt().toInstant().toString());
            ObjectNode counts = n.putObject("counts");
            counts.put("volcanoes", c.volcanoes()).put("volcanoFiles", c.volcanoFiles()).put("episodes", c.episodes())
                    .put("earthquakes", c.earthquakes()).put("thermalDetections", c.thermal());
            ObjectNode cov = n.putObject("coverage");
            cov.putObject("earthquake").put("from", str(c.earthquakeFrom())).put("to", str(c.earthquakeTo()));
            cov.putObject("thermal").put("from", str(c.thermalFrom())).put("to", str(c.thermalTo()));
            return write(n);
        });
    }

    /** volcanoes.geojson, equal to the published file. */
    @GetMapping("/volcanoes")
    ResponseEntity<String> volcanoes(HttpServletRequest request) {
        Dataset d = dataset.require();
        return cached(request, d, CachePolicy.DATA, GEO_JSON, () -> {
            List<Document> features = service.repository().features();
            StringWriter out = new StringWriter();
            try (JsonGenerator g = json.getFactory().createGenerator(out)) {
                ObjectNode header = (ObjectNode) json.readTree(d.indexHeader());
                g.writeStartObject();
                var it = header.fields();
                while (it.hasNext()) {
                    var f = it.next();
                    g.writeFieldName(f.getKey());
                    g.writeTree(f.getValue());
                }
                g.writeArrayFieldStart("features");
                for (Document f : features) g.writeRawValue(f.json());
                g.writeEndArray();
                g.writeEndObject();
            }
            return out.toString();
        });
    }

    @GetMapping("/volcanoes/nearest")
    ResponseEntity<String> nearest(HttpServletRequest request, @RequestParam(required = false) Double lat,
                                   @RequestParam(required = false) Double lon, @RequestParam(required = false) Integer limit) {
        Dataset d = dataset.require();
        return cached(request, d, CachePolicy.DATA, MediaType.APPLICATION_JSON, () -> {
            List<NearbyVolcano> rows = service.nearest(lat, lon, limit);
            ObjectNode n = json.createObjectNode();
            header(n, d);
            n.put("kind", "nearest");
            n.putObject("query").put("lat", lat).put("lon", lon);
            ArrayNode items = n.putArray("volcanoes");
            for (NearbyVolcano v : rows) {
                ObjectNode o = items.addObject();
                o.put("id", v.id());
                o.putObject("name").put("en", v.nameEn()).put("ja", v.nameJa());
                o.put("distanceKm", round(v.distanceKm(), 2));
            }
            return write(n);
        });
    }

    /** volcano/&lt;id&gt;.json, equal to the published file. */
    @GetMapping("/volcanoes/{id}")
    ResponseEntity<String> volcano(HttpServletRequest request, @PathVariable String id) {
        Dataset d = dataset.require();
        return cached(request, d, CachePolicy.DATA, MediaType.APPLICATION_JSON, () -> service.detail(id)
                .map(Document::json)
                .orElseThrow(() -> new NotFound(service.repository().volcano(id).isPresent()
                        ? "volcano \"" + id + "\" has no published file in data version " + d.dataVersion()
                        : "no volcano with id \"" + (id.length() > 40 ? id.substring(0, 40) : id) + "\"")));
    }

    /** Earthquakes and thermal detections within a radius of a volcano or a point, between two days (inclusive). */
    @GetMapping("/events")
    ResponseEntity<String> events(HttpServletRequest request,
                                  @RequestParam(required = false) String volcano,
                                  @RequestParam(required = false) Double lat,
                                  @RequestParam(required = false) Double lon,
                                  @RequestParam(required = false) Double radiusKm,
                                  @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
                                  @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to,
                                  @RequestParam(required = false) String kind,
                                  @RequestParam(required = false) Integer limit) {
        Dataset d = dataset.require();
        return cached(request, d, CachePolicy.DATA, MediaType.APPLICATION_JSON, () -> {
            Center center = service.center(volcano, lat, lon);
            EventsResult r = service.events(center, radiusKm, from, to, kind, limit);
            ObjectNode n = json.createObjectNode();
            header(n, d);
            n.put("kind", "events");
            ObjectNode q = n.putObject("query");
            if (center.volcanoId() != null) q.put("volcano", center.volcanoId());
            q.put("lat", center.lat()).put("lon", center.lon()).put("radiusKm", r.query().radiusKm())
                    .put("from", r.query().from().toString()).put("to", r.query().to().toString());
            ArrayNode kinds = q.putArray("kinds");
            if (r.query().earthquakes()) kinds.add("earthquake");
            if (r.query().thermal()) kinds.add("thermal");
            ObjectNode summary = n.putObject("summary");
            for (String k : List.of("earthquake", "thermal")) {
                if (k.equals("earthquake") ? !r.query().earthquakes() : !r.query().thermal()) continue;
                EventSummary s = r.summary().stream().filter(x -> x.kind().equals(k)).findFirst().orElse(null);
                ObjectNode o = summary.putObject(k);
                o.put("n", s == null ? 0 : s.n());
                if (k.equals("earthquake")) o.put("maxMag", s == null ? null : s.maxMag());
                else o.put("maxFrpMw", s == null ? null : s.maxFrpMw());
                o.put("firstDay", s == null ? null : str(s.firstDay())).put("lastDay", s == null ? null : str(s.lastDay()));
            }
            n.put("returned", r.events().size()).put("truncated", r.truncated());
            ArrayNode items = n.putArray("events");
            for (Event e : r.events()) {
                ObjectNode o = items.addObject();
                o.put("kind", e.kind()).put("id", e.extId());
                if (e.kind().equals("earthquake")) o.put("time", e.t().toInstant().toString());
                else o.put("date", e.t().toInstant().toString().substring(0, 10));
                o.put("lat", e.lat()).put("lon", e.lon()).put("distanceKm", round(e.distanceKm(), 2));
                if (e.kind().equals("earthquake")) {
                    o.put("mag", e.mag()).put("magType", e.magType()).put("depthKm", e.depthKm());
                } else {
                    o.put("frpMw", e.frpMw()).put("sensor", e.sensor()).put("type", e.fireType());
                }
                o.putArray("source").add(e.source());
            }
            return write(n);
        });
    }

    /** What the instruments recorded in the days before each GVP eruption of at least a given VEI. */
    @GetMapping("/eruptions/precursors")
    ResponseEntity<String> precursors(HttpServletRequest request,
                                      @RequestParam(required = false) Integer minVei,
                                      @RequestParam(required = false) Integer days,
                                      @RequestParam(required = false) Double radiusKm,
                                      @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate since) {
        Dataset d = dataset.require();
        return cached(request, d, CachePolicy.DATA, MediaType.APPLICATION_JSON, () -> {
            List<Precursor> rows = service.precursors(minVei, days, radiusKm, since);
            ObjectNode n = json.createObjectNode();
            header(n, d);
            n.put("kind", "precursors");
            n.putObject("query").put("minVei", minVei == null ? 3 : minVei).put("days", days == null ? 14 : days)
                    .put("radiusKm", radiusKm == null ? CatalogueService.DEFAULT_RADIUS_KM : radiusKm)
                    .put("since", since == null ? "2000-01-01" : since.toString());
            n.putObject("note").put("en", "Counts cover the earthquakes and thermal detections loaded in this data version (see /v1/meta coverage); an empty window outside that coverage means not observed, not quiet.")
                    .put("ja", "件数はこのデータ版に読み込まれた地震と熱異常の範囲内のものです(/v1/meta の coverage 参照)。範囲外の空の期間は「静穏」ではなく「未観測」を意味します。");
            ArrayNode items = n.putArray("eruptions");
            for (Precursor p : rows) {
                ObjectNode o = items.addObject();
                o.put("volcano", p.volcanoId()).put("episodeId", p.episodeId()).put("start", p.startDay().toString())
                        .put("end", p.endText()).put("vei", p.vei());
                o.putObject("earthquakes").put("n", p.earthquakes()).put("maxMag", p.maxMag());
                o.putObject("thermal").put("n", p.thermal()).put("maxFrpMw", p.maxFrpMw());
            }
            return write(n);
        });
    }

    @GetMapping("/openapi.yaml")
    ResponseEntity<String> openapi() throws IOException {
        try (InputStream in = new ClassPathResource("contract/openapi.yaml").getInputStream()) {
            return ResponseEntity.ok().header(HttpHeaders.CACHE_CONTROL, CachePolicy.META)
                    .contentType(MediaType.parseMediaType("application/yaml"))
                    .body(new String(in.readAllBytes(), StandardCharsets.UTF_8));
        }
    }

    // ---------------------------------------------------------------------------------------------------------

    interface Body {
        String get() throws IOException;
    }

    /** ETag first: a conditional request that matches costs no query. */
    private ResponseEntity<String> cached(HttpServletRequest request, Dataset d, String cacheControl, MediaType type, Body body) {
        String etag = info.etag(d.dataVersion());
        if (Etags.matches(request.getHeader(HttpHeaders.IF_NONE_MATCH), etag)) {
            return ResponseEntity.status(HttpStatus.NOT_MODIFIED).eTag(etag).header(HttpHeaders.CACHE_CONTROL, cacheControl).build();
        }
        String text;
        try {
            text = body.get();
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
        return ResponseEntity.ok().eTag(etag).header(HttpHeaders.CACHE_CONTROL, cacheControl)
                .header("X-Data-Version", d.dataVersion()).contentType(type).body(text);
    }

    private static void header(ObjectNode n, Dataset d) {
        n.put("dataVersion", d.dataVersion()).put("dataAsOf", d.dataAsOf().toString());
        if (Boolean.TRUE.equals(d.fixture())) n.put("fixture", true);
    }

    private String write(ObjectNode n) throws IOException {
        return json.writeValueAsString(n);
    }

    private static String str(Object o) {
        return o == null ? null : o.toString();
    }

    private static Double round(Double v, int places) {
        if (v == null) return null;
        double f = Math.pow(10, places);
        return Math.round(v * f) / f;
    }
}
