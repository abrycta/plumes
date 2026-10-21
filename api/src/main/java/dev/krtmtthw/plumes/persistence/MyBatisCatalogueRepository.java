package dev.krtmtthw.plumes.persistence;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.springframework.stereotype.Repository;

import dev.krtmtthw.plumes.catalogue.CatalogueRepository;
import dev.krtmtthw.plumes.catalogue.Model.Counts;
import dev.krtmtthw.plumes.catalogue.Model.Dataset;
import dev.krtmtthw.plumes.catalogue.Model.Document;
import dev.krtmtthw.plumes.catalogue.Model.Event;
import dev.krtmtthw.plumes.catalogue.Model.EventSummary;
import dev.krtmtthw.plumes.catalogue.Model.NearbyVolcano;
import dev.krtmtthw.plumes.catalogue.Model.Point;
import dev.krtmtthw.plumes.catalogue.Model.Precursor;

/** The driven adapter: the catalogue port over MyBatis and PostGIS. */
@Repository
public class MyBatisCatalogueRepository implements CatalogueRepository {

    private final CatalogueMapper mapper;

    public MyBatisCatalogueRepository(CatalogueMapper mapper) {
        this.mapper = mapper;
    }

    @Override public Optional<Dataset> dataset() { return Optional.ofNullable(mapper.dataset()); }
    @Override public Counts counts() { return mapper.counts(); }
    @Override public List<Document> features() { return mapper.features(); }
    @Override public Optional<Document> detail(String id) { return Optional.ofNullable(mapper.detail(id)); }
    @Override public Optional<Point> volcano(String id) { return Optional.ofNullable(mapper.volcano(id)); }
    @Override public List<NearbyVolcano> nearest(double lat, double lon, int limit) { return mapper.nearest(lat, lon, limit); }
    @Override public List<Event> events(EventQuery q, int limit) { return mapper.events(q, limit); }
    @Override public List<EventSummary> eventSummary(EventQuery q) { return mapper.eventSummary(q); }

    @Override
    public List<Precursor> precursors(int minVei, int days, double radiusKm, LocalDate since) {
        return mapper.precursors(minVei, days, radiusKm, since);
    }
}
