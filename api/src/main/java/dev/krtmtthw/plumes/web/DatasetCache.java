package dev.krtmtthw.plumes.web;

import java.util.Optional;

import org.springframework.stereotype.Component;

import dev.krtmtthw.plumes.catalogue.CatalogueRepository;
import dev.krtmtthw.plumes.catalogue.Model.Dataset;

/**
 * The loaded data version, re-read at most every 30 s: the ETag check of a conditional request then needs no
 * database round trip, and a new load is visible within half a minute.
 */
@Component
public class DatasetCache {

    private static final long TTL_NANOS = 30_000_000_000L;
    private final CatalogueRepository repo;
    private volatile Dataset value;
    private volatile long readAt;

    public DatasetCache(CatalogueRepository repo) {
        this.repo = repo;
    }

    public Optional<Dataset> get() {
        Dataset v = value;
        if (v != null && System.nanoTime() - readAt < TTL_NANOS) return Optional.of(v);
        Optional<Dataset> fresh = repo.dataset();
        fresh.ifPresent(d -> { value = d; readAt = System.nanoTime(); });
        return fresh;
    }

    /** The data version, or a 503 not-ready problem when nothing is loaded yet. */
    public Dataset require() {
        return get().orElseThrow(() -> new NotReady("no data version is loaded"));
    }

    public static final class NotReady extends RuntimeException {
        public NotReady(String message) {
            super(message);
        }
    }
}
