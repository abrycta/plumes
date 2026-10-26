package dev.krtmtthw.plumes.load;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.file.Path;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

/**
 * A load that dies mid-way (a duplicate key, found when event_next's primary key is built after every insert)
 * leaves the previous version serving, the same tables and no event_next, and the next load swaps in a compact event
 * with the migration's index names (docs/architecture/NEON-STORAGE.md). Ends with the fixtures loaded, as ContractIT
 * expects.
 */
@EnabledIfEnvironmentVariable(named = "TEST_DATABASE_URL", matches = ".+")
class LoaderCleanupIT {

    static final Path DATA = Path.of(System.getProperty("plumes.contracts", "../contracts")).resolve("fixtures/data");
    static final Path USGS = Path.of("src/test/resources/usgs-taal-2019-12-2020-02.csv");
    static final DatabaseUrl DB = DatabaseUrl.parse(System.getenv("TEST_DATABASE_URL"));

    @Test
    void failedLoadLeavesNoOrphansAndItsSpaceIsReused() throws Exception {
        assertThat(load()).isZero();
        List<String> tables = query("SELECT relname FROM pg_class WHERE relkind = 'r'"
                + " AND relnamespace = 'public'::regnamespace ORDER BY 1");
        List<String> served = query("SELECT data_version || ' ' || (SELECT count(*) FROM event) FROM dataset");

        Loader.Version v = new Loader(Loader.Source.of(DATA.toString()), List.of(USGS), List.of()).read();
        v.events.add(v.events.get(0)); // duplicate (kind, ext_id): building event_next's primary key fails
        assertThatThrownBy(() -> Loader.load(DB, v, DATA.toString())).isInstanceOf(SQLException.class);

        assertThat(query("SELECT relname FROM pg_class WHERE relkind = 'r'"
                + " AND relnamespace = 'public'::regnamespace ORDER BY 1")).isEqualTo(tables);
        assertThat(query("SELECT data_version || ' ' || (SELECT count(*) FROM event) FROM dataset")).isEqualTo(served);
        long afterFailure = size();
        assertThat(load()).isZero();
        long afterNext = size();
        System.out.printf("tables %s; event after the failed load %d kB, after the next load %d kB%n", tables,
                afterFailure >> 10, afterNext >> 10);
        assertThat(afterNext).as("the next load is no larger than the old table").isLessThanOrEqualTo(afterFailure + (64 << 10));
        assertThat(query("SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND tablename = 'event'"
                + " ORDER BY 1")).containsExactly("event_day_idx", "event_geog_idx", "event_pkey");
    }

    static int load() throws Exception {
        return Loader.runWith(System.getenv("TEST_DATABASE_URL"), new String[] {DATA.toString(), "--usgs", USGS.toString()});
    }

    static long size() throws SQLException {
        return Long.parseLong(query("SELECT pg_total_relation_size('event')").get(0));
    }

    static List<String> query(String sql) throws SQLException {
        List<String> out = new ArrayList<>();
        try (Connection c = Loader.connect(DB); Statement s = c.createStatement(); ResultSet rs = s.executeQuery(sql)) {
            while (rs.next()) out.add(rs.getString(1));
        }
        return out;
    }
}
