package dev.krtmtthw.plumes.catalogue;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import org.springframework.stereotype.Service;

import dev.krtmtthw.plumes.catalogue.CatalogueRepository.EventQuery;
import dev.krtmtthw.plumes.catalogue.Model.Event;
import dev.krtmtthw.plumes.catalogue.Model.EventSummary;
import dev.krtmtthw.plumes.catalogue.Model.Point;
import dev.krtmtthw.plumes.catalogue.Model.Precursor;

/**
 * The application core: query rules and limits. The limits keep every response small (Render's 5 GB of egress a
 * month is shared, DATA-PLAN §8) and every query cheap on Neon's smallest compute.
 */
@Service
public class CatalogueService {

    public static final double MAX_RADIUS_KM = 100;
    public static final double DEFAULT_RADIUS_KM = 30;
    public static final long MAX_WINDOW_DAYS = 3660;
    public static final int MAX_EVENTS = 1000;
    public static final int MAX_NEAREST = 24;
    public static final int MAX_PRECURSOR_DAYS = 365;
    public static final Set<String> KINDS = Set.of("earthquake", "thermal");

    private final CatalogueRepository repo;

    public CatalogueService(CatalogueRepository repo) {
        this.repo = repo;
    }

    public CatalogueRepository repository() {
        return repo;
    }

    /** Where an event search is centred: a volcano by id, or a point. */
    public record Center(String volcanoId, double lat, double lon) { }

    public record EventsResult(Center center, EventQuery query, List<EventSummary> summary, List<Event> events,
                               boolean truncated) { }

    public Center center(String volcanoId, Double lat, Double lon) {
        if (volcanoId != null) {
            if (lat != null || lon != null) throw new InvalidQuery("volcano", "give either volcano or lat/lon, not both");
            Point p = repo.volcano(volcanoId).orElseThrow(() -> new NotFound("no volcano with id \"" + clip(volcanoId) + "\""));
            return new Center(p.id(), p.lat(), p.lon());
        }
        if (lat == null || lon == null) throw new InvalidQuery("volcano", "give a volcano id or both lat and lon");
        checkLatLon(lat, lon);
        return new Center(null, lat, lon);
    }

    public EventsResult events(Center center, Double radiusKm, LocalDate from, LocalDate to, String kinds, Integer limit) {
        double radius = radiusKm == null ? DEFAULT_RADIUS_KM : radiusKm;
        if (!(radius > 0 && radius <= MAX_RADIUS_KM)) throw new InvalidQuery("radiusKm", "must be in (0, " + (int) MAX_RADIUS_KM + "]");
        if (from == null) throw new InvalidQuery("from", "required (YYYY-MM-DD)");
        if (to == null) throw new InvalidQuery("to", "required (YYYY-MM-DD)");
        if (to.isBefore(from)) throw new InvalidQuery("to", "must not be before from");
        if (ChronoUnit.DAYS.between(from, to) >= MAX_WINDOW_DAYS) throw new InvalidQuery("to", "the window is limited to " + MAX_WINDOW_DAYS + " days");
        int max = limit == null ? MAX_EVENTS : limit;
        if (max < 0 || max > MAX_EVENTS) throw new InvalidQuery("limit", "must be in [0, " + MAX_EVENTS + "]");
        boolean eq = true;
        boolean th = true;
        if (kinds != null && !kinds.isBlank()) {
            Set<String> ks = Set.of(kinds.split(","));
            if (!KINDS.containsAll(ks)) throw new InvalidQuery("kind", "comma-separated list of earthquake, thermal");
            eq = ks.contains("earthquake");
            th = ks.contains("thermal");
        }
        EventQuery q = new EventQuery(center.lat(), center.lon(), radius, from, to, eq, th);
        List<EventSummary> summary = repo.eventSummary(q);
        List<Event> events = max == 0 ? List.of() : repo.events(q, max);
        long total = summary.stream().mapToLong(EventSummary::n).sum();
        return new EventsResult(center, q, summary, events, total > events.size());
    }

    public List<Precursor> precursors(Integer minVei, Integer days, Double radiusKm, LocalDate since) {
        int vei = minVei == null ? 3 : minVei;
        if (vei < 0 || vei > 8) throw new InvalidQuery("minVei", "must be in [0, 8]");
        int d = days == null ? 14 : days;
        if (d < 1 || d > MAX_PRECURSOR_DAYS) throw new InvalidQuery("days", "must be in [1, " + MAX_PRECURSOR_DAYS + "]");
        double r = radiusKm == null ? DEFAULT_RADIUS_KM : radiusKm;
        if (!(r > 0 && r <= MAX_RADIUS_KM)) throw new InvalidQuery("radiusKm", "must be in (0, " + (int) MAX_RADIUS_KM + "]");
        return repo.precursors(vei, d, r, since == null ? LocalDate.of(2000, 1, 1) : since);
    }

    public List<Model.NearbyVolcano> nearest(Double lat, Double lon, Integer limit) {
        if (lat == null || lon == null) throw new InvalidQuery("lat", "lat and lon are required");
        checkLatLon(lat, lon);
        int n = limit == null ? 1 : limit;
        if (n < 1 || n > MAX_NEAREST) throw new InvalidQuery("limit", "must be in [1, " + MAX_NEAREST + "]");
        return repo.nearest(lat, lon, n);
    }

    public Optional<Model.Document> detail(String id) {
        return repo.detail(id);
    }

    private static void checkLatLon(double lat, double lon) {
        if (!(lat >= -90 && lat <= 90)) throw new InvalidQuery("lat", "must be in [-90, 90]");
        if (!(lon >= -180 && lon <= 180)) throw new InvalidQuery("lon", "must be in [-180, 180]");
    }

    static String clip(String s) {
        return s.length() > 40 ? s.substring(0, 40) + "…" : s;
    }

    /** A query parameter the API rejects (400). */
    public static final class InvalidQuery extends RuntimeException {
        private final String parameter;

        public InvalidQuery(String parameter, String message) {
            super(parameter + ": " + message);
            this.parameter = parameter;
        }

        public String parameter() {
            return parameter;
        }
    }

    /** A resource that does not exist in the loaded data version (404). */
    public static final class NotFound extends RuntimeException {
        public NotFound(String message) {
            super(message);
        }
    }
}
