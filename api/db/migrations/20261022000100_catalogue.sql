-- migrate:up
-- The Plumes read catalogue (ARCHITECTURE-OPTIONS §3, DATA-PLAN §4). Loaded only by `plumes-api load`, one data
-- version per transaction; the API never writes. Every row that comes from a published read model keeps that JSON
-- verbatim (type json keeps the text byte for byte), so the API's documents equal the static ones; the relational
-- columns beside it exist for the spatial and temporal queries.
CREATE EXTENSION IF NOT EXISTS postgis;

-- The loaded data version: exactly one row.
CREATE TABLE dataset (
    singleton     boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    data_version  text        NOT NULL CHECK (data_version ~ '^v[0-9]+$'),
    data_as_of    date        NOT NULL,
    generated_at  timestamptz NOT NULL,
    fixture       boolean     NOT NULL DEFAULT false,
    source        text        NOT NULL,           -- where the loader read the version (a base URL or "fixtures")
    loaded_at     timestamptz NOT NULL DEFAULT now(),
    index_header  json        NOT NULL            -- volcanoes.geojson without its features
);

CREATE TABLE volcano (
    id           text PRIMARY KEY CHECK (id ~ '^[a-z0-9-]+$'),
    ord          integer          NOT NULL,       -- position in volcanoes.geojson
    gvp_number   integer,
    name_en      text             NOT NULL,
    name_ja      text             NOT NULL,
    lat          double precision NOT NULL,
    lon          double precision NOT NULL,
    geog         geography(Point, 4326) NOT NULL,
    elevation_m  double precision,
    observatory  boolean          NOT NULL,
    coverage     text             NOT NULL,
    feature      json             NOT NULL,       -- the feature of volcanoes.geojson, verbatim
    detail       json                             -- volcano/<id>.json, verbatim (null while unpublished)
);
CREATE INDEX volcano_geog_idx ON volcano USING gist (geog);

-- Episodes from the per-volcano files (GVP eruptions, alert windows, strong degassing).
CREATE TABLE episode (
    volcano_id   text    NOT NULL REFERENCES volcano (id) ON DELETE CASCADE,
    id           text    NOT NULL,
    kind         text    NOT NULL,
    start_text   text    NOT NULL,                -- YYYY, YYYY-MM or YYYY-MM-DD as published (GVP dates can be partial)
    start_day    date,                            -- only when start_text is a full date
    end_text     text,
    vei          integer,
    so2_mass_kt  double precision,
    plume_alt_km double precision,
    max_alert    integer,
    PRIMARY KEY (volcano_id, id)
);
CREATE INDEX episode_start_idx ON episode (start_day) WHERE start_day IS NOT NULL;

-- Point events: USGS earthquakes and FIRMS thermal detections.
CREATE TABLE event (
    kind        text             NOT NULL CHECK (kind IN ('earthquake', 'thermal')),
    ext_id      text             NOT NULL,        -- USGS id; FIRMS: sensor/date/lat/lon
    t           timestamptz      NOT NULL,        -- thermal detections: the acquisition date at 00:00 UTC
    day         date             NOT NULL,        -- the published (UTC) day
    lat         double precision NOT NULL,
    lon         double precision NOT NULL,
    geog        geography(Point, 4326) NOT NULL,
    mag         real,
    mag_type    text,
    depth_km    real,
    frp_mw      real,
    sensor      text,
    fire_type   smallint,
    source      text             NOT NULL,        -- registry id (pipeline/sources.yaml)
    PRIMARY KEY (kind, ext_id)
);
CREATE INDEX event_geog_idx ON event USING gist (geog);
CREATE INDEX event_day_idx ON event (kind, day);

-- migrate:down
DROP TABLE event;
DROP TABLE episode;
DROP TABLE volcano;
DROP TABLE dataset;
