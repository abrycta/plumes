package dev.krtmtthw.plumes;

import java.util.Arrays;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import dev.krtmtthw.plumes.load.DatabaseUrl;
import dev.krtmtthw.plumes.load.Loader;

/**
 * Plumes' read-only catalogue API. One binary, two commands:
 * <ul>
 *   <li>no arguments: serve HTTP on {@code PORT};</li>
 *   <li>{@code load <data-dir-or-base-url> [--usgs file.csv]...}: load one published data version into PostGIS and
 *       exit (no Spring context; see {@link Loader}).</li>
 * </ul>
 * Configuration comes from the environment: {@code DATABASE_URL} (a postgres:// URL, as Neon prints it),
 * {@code PORT}, {@code PLUMES_EDGE_SECRET}.
 */
@SpringBootApplication
public class PlumesApplication {

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("load")) {
            System.exit(Loader.run(Arrays.copyOfRange(args, 1, args.length)));
        }
        DatabaseUrl.fromEnvironment().ifPresent(db -> {
            System.setProperty("spring.datasource.url", db.jdbcUrl());
            if (db.user() != null) System.setProperty("spring.datasource.username", db.user());
            if (db.password() != null) System.setProperty("spring.datasource.password", db.password());
        });
        SpringApplication.run(PlumesApplication.class, args);
    }
}
