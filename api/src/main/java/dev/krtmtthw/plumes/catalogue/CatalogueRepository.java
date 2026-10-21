package dev.krtmtthw.plumes.catalogue;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import dev.krtmtthw.plumes.catalogue.Model.Counts;
import dev.krtmtthw.plumes.catalogue.Model.Dataset;
import dev.krtmtthw.plumes.catalogue.Model.Document;
import dev.krtmtthw.plumes.catalogue.Model.Event;
import dev.krtmtthw.plumes.catalogue.Model.EventSummary;
import dev.krtmtthw.plumes.catalogue.Model.NearbyVolcano;
import dev.krtmtthw.plumes.catalogue.Model.Point;
import dev.krtmtthw.plumes.catalogue.Model.Precursor;

/** The driven port: read-only queries over the PostGIS catalogue. */
public interface CatalogueRepository {

    Optional<Dataset> dataset();

    Counts counts();

    /** Features of volcanoes.geojson in published order. */
    List<Document> features();

    /** volcano/&lt;id&gt;.json, verbatim; empty when the volcano is unknown or has no published file. */
    Optional<Document> detail(String id);

    Optional<Point> volcano(String id);

    List<NearbyVolcano> nearest(double lat, double lon, int limit);

    List<Event> events(EventQuery q, int limit);

    List<EventSummary> eventSummary(EventQuery q);

    List<Precursor> precursors(int minVei, int days, double radiusKm, LocalDate since);

    record EventQuery(double lat, double lon, double radiusKm, LocalDate from, LocalDate to, boolean earthquakes,
                      boolean thermal) { }
}
