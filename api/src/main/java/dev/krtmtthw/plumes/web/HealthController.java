package dev.krtmtthw.plumes.web;

import jakarta.servlet.http.HttpServletRequest;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import dev.krtmtthw.plumes.catalogue.CatalogueRepository;
import dev.krtmtthw.plumes.catalogue.Model.Dataset;

/**
 * {@code /healthz}: the process is up (no database; Render's health check uses it, so it never wakes Neon).
 * {@code /readyz}: the database answers and a data version is loaded.
 */
@RestController
public class HealthController {

    private final CatalogueRepository repo;

    public HealthController(CatalogueRepository repo) {
        this.repo = repo;
    }

    @GetMapping("/healthz")
    ResponseEntity<String> health() {
        return ResponseEntity.ok().header(HttpHeaders.CACHE_CONTROL, CachePolicy.NO_STORE)
                .contentType(MediaType.APPLICATION_JSON).body("{\"status\":\"ok\"}");
    }

    @GetMapping("/readyz")
    ResponseEntity<String> ready(HttpServletRequest request) {
        Dataset d = repo.dataset().orElseThrow(() -> new DatasetCache.NotReady("no data version is loaded"));
        return ResponseEntity.ok().header(HttpHeaders.CACHE_CONTROL, CachePolicy.NO_STORE)
                .contentType(MediaType.APPLICATION_JSON)
                .body("{\"status\":\"ready\",\"dataVersion\":\"" + d.dataVersion() + "\"}");
    }
}
