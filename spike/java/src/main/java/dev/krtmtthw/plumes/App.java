package dev.krtmtthw.plumes;

import java.lang.management.ManagementFactory;
import java.nio.file.*;
import java.util.*;
import org.apache.ibatis.annotations.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
public class App {
  public static void main(String[] args) { SpringApplication.run(App.class, args); }

  @Mapper
  public interface VolcanoMapper {
    @Select("SELECT 1") int ping();
    /** M1 query 3: nearest volcano to a point, with distance in km (PostGIS KNN on geography). */
    @Select("""
        SELECT v.id, v.name, round((ST_Distance(v.geog, ST_MakePoint(#{lon}, #{lat})::geography) / 1000)::numeric, 1) AS km
        FROM volcano v ORDER BY v.geog <-> ST_MakePoint(#{lon}, #{lat})::geography LIMIT 1""")
    Map<String, Object> nearest(@Param("lat") double lat, @Param("lon") double lon);
    /** M1 query 1: events within a radius between dates. */
    @Select("""
        SELECT count(*) AS n, max(mag) AS max_mag FROM usgs_event e JOIN volcano v ON v.id = #{id}
        WHERE ST_DWithin(e.geog, v.geog, #{km} * 1000) AND e.t >= #{from}::date AND e.t < #{to}::date""")
    Map<String, Object> eventsNear(@Param("id") int id, @Param("km") double km, @Param("from") String from, @Param("to") String to);
  }

  @RestController
  public static class Api {
    private final VolcanoMapper m;
    Api(VolcanoMapper m) { this.m = m; }
    @GetMapping("/readyz") public ResponseEntity<String> ready() { m.ping(); return ResponseEntity.ok("ok"); }
    @GetMapping("/api/nearest") public ResponseEntity<Map<String, Object>> nearest(@RequestParam double lat, @RequestParam double lon) {
      return cached(m.nearest(lat, lon)); }
    @GetMapping("/api/volcanoes/{id}/events") public ResponseEntity<Map<String, Object>> events(@PathVariable int id,
        @RequestParam(defaultValue = "30") double km, @RequestParam String from, @RequestParam String to) {
      return cached(m.eventsNear(id, km, from, to)); }
    @GetMapping("/stats") public Map<String, Object> stats() throws Exception {
      String rss = Files.readAllLines(Path.of("/proc/self/status")).stream().filter(l -> l.startsWith("VmRSS")).findFirst().orElse("?");
      var rt = ManagementFactory.getRuntimeMXBean(); var mem = Runtime.getRuntime();
      return Map.of("vmrss", rss, "uptime_ms", rt.getUptime(), "heap_used_mb", (mem.totalMemory() - mem.freeMemory()) >> 20,
          "heap_max_mb", mem.maxMemory() >> 20, "cpus", mem.availableProcessors(), "jvm", System.getProperty("java.version"));
    }
    private static <T> ResponseEntity<T> cached(T body) {
      return ResponseEntity.ok().header("Cache-Control", "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800").body(body); }
  }
}
