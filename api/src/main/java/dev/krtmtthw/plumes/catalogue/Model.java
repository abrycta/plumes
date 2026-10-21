package dev.krtmtthw.plumes.catalogue;

import java.time.LocalDate;
import java.time.OffsetDateTime;

/**
 * The read model of the catalogue: plain records, filled by the persistence adapter (MyBatis constructor
 * auto-mapping by argument name) and turned into JSON by the web adapter.
 */
public final class Model {

    private Model() { }

    /** The loaded data version (one row). {@code indexHeader} is volcanoes.geojson without its features. */
    public record Dataset(String dataVersion, LocalDate dataAsOf, OffsetDateTime generatedAt, Boolean fixture,
                          String source, OffsetDateTime loadedAt, String indexHeader) { }

    public record Counts(Long volcanoes, Long volcanoFiles, Long episodes, Long earthquakes, Long thermal,
                         LocalDate earthquakeFrom, LocalDate earthquakeTo, LocalDate thermalFrom, LocalDate thermalTo) { }

    /** A published JSON document, verbatim. */
    public record Document(String id, String json) { }

    public record Point(String id, Double lat, Double lon) { }

    public record NearbyVolcano(String id, String nameEn, String nameJa, Double distanceKm) { }

    public record Event(String kind, String extId, OffsetDateTime t, Double lat, Double lon, Double distanceKm,
                        Float mag, String magType, Float depthKm, Float frpMw, String sensor, Integer fireType,
                        String source) { }

    public record EventSummary(String kind, Long n, Float maxMag, Float maxFrpMw, LocalDate firstDay, LocalDate lastDay) { }

    public record Precursor(String volcanoId, String episodeId, LocalDate startDay, String endText, Integer vei,
                            Long earthquakes, Float maxMag, Long thermal, Float maxFrpMw) { }
}
