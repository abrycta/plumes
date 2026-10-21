package dev.krtmtthw.plumes;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.Test;

import dev.krtmtthw.plumes.catalogue.CatalogueRepository;
import dev.krtmtthw.plumes.catalogue.CatalogueService;
import dev.krtmtthw.plumes.catalogue.CatalogueService.InvalidQuery;
import dev.krtmtthw.plumes.catalogue.Model;
import dev.krtmtthw.plumes.load.DatabaseUrl;
import dev.krtmtthw.plumes.web.ApiInfo;
import dev.krtmtthw.plumes.web.Etags;

/** Fast checks without a database. */
class UnitTest {

    @Test
    void neonUrlBecomesJdbc() {
        DatabaseUrl d = DatabaseUrl.parse("postgresql://u%40x:p%2Fw@ep-x-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require");
        assertThat(d.jdbcUrl()).isEqualTo("jdbc:postgresql://ep-x-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channelBinding=require");
        assertThat(d.user()).isEqualTo("u@x");
        assertThat(d.password()).isEqualTo("p/w");
        assertThat(d.toString()).doesNotContain("p/w");
        assertThat(DatabaseUrl.parse("postgres://a:b@localhost:5433/plumes?sslmode=disable").jdbcUrl())
                .isEqualTo("jdbc:postgresql://localhost:5433/plumes?sslmode=disable");
    }

    @Test
    void etagsFollowReplaysFormAndCompareWeakly() {
        String tag = Etags.of("1.0.0", "java", "0.1.0", "v3");
        assertThat(tag).isEqualTo("W/\"c1.0.0-java-0.1.0-d3\"");
        assertThat(Etags.matches("\"c1.0.0-java-0.1.0-d3\"", tag)).isTrue();
        assertThat(Etags.matches("W/\"x\", W/\"c1.0.0-java-0.1.0-d3\"", tag)).isTrue();
        assertThat(Etags.matches("*", tag)).isTrue();
        assertThat(Etags.matches("W/\"c1.0.0-java-0.1.0-d2\"", tag)).isFalse();
        assertThat(Etags.matches(null, tag)).isFalse();
    }

    @Test
    void contractVersionMatchesOpenApi() throws Exception {
        String yaml = Files.readString(Path.of(System.getProperty("plumes.contracts", "../contracts"), "openapi.yaml"));
        assertThat(yaml).contains("\n  version: " + ApiInfo.CONTRACT + "\n");
    }

    @Test
    void queryLimitsAreEnforced() {
        CatalogueService s = new CatalogueService(new EmptyRepository());
        var c = new CatalogueService.Center(null, 14, 121);
        LocalDate d = LocalDate.of(2020, 1, 1);
        assertThatThrownBy(() -> s.events(c, 500.0, d, d, null, null)).isInstanceOf(InvalidQuery.class).hasMessageStartingWith("radiusKm");
        assertThatThrownBy(() -> s.events(c, null, null, d, null, null)).hasMessageStartingWith("from");
        assertThatThrownBy(() -> s.events(c, null, d, d.minusDays(1), null, null)).hasMessageStartingWith("to");
        assertThatThrownBy(() -> s.events(c, null, d, d.plusYears(11), null, null)).hasMessageStartingWith("to");
        assertThatThrownBy(() -> s.events(c, null, d, d, "quake", null)).hasMessageStartingWith("kind");
        assertThatThrownBy(() -> s.events(c, null, d, d, null, 5000)).hasMessageStartingWith("limit");
        assertThatThrownBy(() -> s.center(null, 95.0, 0.0)).hasMessageStartingWith("lat");
        assertThatThrownBy(() -> s.center("taal", 1.0, 1.0)).hasMessageStartingWith("volcano");
        assertThatThrownBy(() -> s.nearest(14.0, 121.0, 99)).hasMessageStartingWith("limit");
        assertThatThrownBy(() -> s.precursors(9, null, null, null)).hasMessageStartingWith("minVei");
        assertThat(s.events(c, null, d, d, "thermal", 0).query().earthquakes()).isFalse();
    }

    static class EmptyRepository implements CatalogueRepository {
        public Optional<Model.Dataset> dataset() { return Optional.empty(); }
        public Model.Counts counts() { return null; }
        public List<Model.Document> features() { return List.of(); }
        public Optional<Model.Document> detail(String id) { return Optional.empty(); }
        public Optional<Model.Point> volcano(String id) { return Optional.empty(); }
        public List<Model.NearbyVolcano> nearest(double lat, double lon, int limit) { return List.of(); }
        public List<Model.Event> events(EventQuery q, int limit) { return List.of(); }
        public List<Model.EventSummary> eventSummary(EventQuery q) { return List.of(); }
        public List<Model.Precursor> precursors(int minVei, int days, double radiusKm, LocalDate since) { return List.of(); }
    }
}
