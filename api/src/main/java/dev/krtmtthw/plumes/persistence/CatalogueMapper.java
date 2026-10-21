package dev.krtmtthw.plumes.persistence;

import java.time.LocalDate;
import java.util.List;

import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import dev.krtmtthw.plumes.catalogue.Model.Counts;
import dev.krtmtthw.plumes.catalogue.Model.Dataset;
import dev.krtmtthw.plumes.catalogue.Model.Document;
import dev.krtmtthw.plumes.catalogue.Model.Event;
import dev.krtmtthw.plumes.catalogue.Model.EventSummary;
import dev.krtmtthw.plumes.catalogue.Model.NearbyVolcano;
import dev.krtmtthw.plumes.catalogue.Model.Point;
import dev.krtmtthw.plumes.catalogue.Model.Precursor;

/**
 * MyBatis mapper over the PostGIS catalogue (api/db/migrations). Registered by {@link MyBatisConfig}, not by
 * classpath scanning, so the native image needs no scanning metadata. Distances are on the WGS 84 spheroid
 * (geography), in km.
 */
public interface CatalogueMapper {

    String POINT = "ST_SetSRID(ST_MakePoint(#{lon}, #{lat}), 4326)::geography";

    String EVENT_FILTER = """
            FROM event e
            WHERE e.day BETWEEN #{q.from} AND #{q.to}
              AND ((#{q.earthquakes} AND e.kind = 'earthquake') OR (#{q.thermal} AND e.kind = 'thermal'))
              AND ST_DWithin(e.geog, ST_SetSRID(ST_MakePoint(#{q.lon}, #{q.lat}), 4326)::geography, #{q.radiusKm} * 1000)
            """;

    @Select("SELECT data_version, data_as_of, generated_at, fixture, source, loaded_at, index_header::text AS index_header FROM dataset")
    Dataset dataset();

    @Select("""
            SELECT (SELECT count(*) FROM volcano) AS volcanoes,
                   (SELECT count(*) FROM volcano WHERE detail IS NOT NULL) AS volcano_files,
                   (SELECT count(*) FROM episode) AS episodes,
                   (SELECT count(*) FROM event WHERE kind = 'earthquake') AS earthquakes,
                   (SELECT count(*) FROM event WHERE kind = 'thermal') AS thermal,
                   (SELECT min(day) FROM event WHERE kind = 'earthquake') AS earthquake_from,
                   (SELECT max(day) FROM event WHERE kind = 'earthquake') AS earthquake_to,
                   (SELECT min(day) FROM event WHERE kind = 'thermal') AS thermal_from,
                   (SELECT max(day) FROM event WHERE kind = 'thermal') AS thermal_to""")
    Counts counts();

    @Select("SELECT id, feature::text AS json FROM volcano ORDER BY ord")
    List<Document> features();

    @Select("SELECT id, detail::text AS json FROM volcano WHERE id = #{id} AND detail IS NOT NULL")
    Document detail(@Param("id") String id);

    @Select("SELECT id, lat, lon FROM volcano WHERE id = #{id}")
    Point volcano(@Param("id") String id);

    @Select("SELECT id, name_en, name_ja, ST_Distance(geog, " + POINT + ") / 1000 AS distance_km "
            + "FROM volcano ORDER BY geog <-> " + POINT + ", id LIMIT #{limit}")
    List<NearbyVolcano> nearest(@Param("lat") double lat, @Param("lon") double lon, @Param("limit") int limit);

    @Select("SELECT e.kind, e.ext_id, e.t, e.lat, e.lon, "
            + "ST_Distance(e.geog, ST_SetSRID(ST_MakePoint(#{q.lon}, #{q.lat}), 4326)::geography) / 1000 AS distance_km, "
            + "e.mag, e.mag_type, e.depth_km, e.frp_mw, e.sensor, e.fire_type::int AS fire_type, e.source "
            + EVENT_FILTER + " ORDER BY e.t, e.kind, e.ext_id LIMIT #{limit}")
    List<Event> events(@Param("q") Object q, @Param("limit") int limit);

    @Select("SELECT e.kind, count(*) AS n, max(e.mag) AS max_mag, max(e.frp_mw) AS max_frp_mw, "
            + "min(e.day) AS first_day, max(e.day) AS last_day " + EVENT_FILTER + " GROUP BY e.kind ORDER BY e.kind")
    List<EventSummary> eventSummary(@Param("q") Object q);

    @Select("""
            SELECT p.volcano_id, p.id AS episode_id, p.start_day, p.end_text, p.vei,
                   count(e.kind) FILTER (WHERE e.kind = 'earthquake') AS earthquakes,
                   max(e.mag) FILTER (WHERE e.kind = 'earthquake') AS max_mag,
                   count(e.kind) FILTER (WHERE e.kind = 'thermal') AS thermal,
                   max(e.frp_mw) FILTER (WHERE e.kind = 'thermal') AS max_frp_mw
            FROM episode p
            JOIN volcano v ON v.id = p.volcano_id
            LEFT JOIN event e ON e.day >= p.start_day - #{days} AND e.day < p.start_day
                             AND ST_DWithin(e.geog, v.geog, #{radiusKm} * 1000)
            WHERE p.kind = 'gvp_eruption' AND p.start_day IS NOT NULL AND p.vei >= #{minVei} AND p.start_day >= #{since}
            GROUP BY p.volcano_id, p.id, p.start_day, p.end_text, p.vei
            ORDER BY p.start_day, p.volcano_id""")
    List<Precursor> precursors(@Param("minVei") int minVei, @Param("days") int days, @Param("radiusKm") double radiusKm,
                               @Param("since") LocalDate since);
}
