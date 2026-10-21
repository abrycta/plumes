"""Item 14: load the M1 catalogue (real USGS/GVP + synthetic extrapolated series) into a throwaway DB; size and plans.
Usage: pg_size.py load|measure|drop   (env ADMIN_URL = a URL to an existing DB on the server; never touches other DBs)"""
import csv, io, json, os, sys, time, random, datetime as dt, psycopg
ADMIN = os.environ["ADMIN_URL"]; DB = "plumes_spike"
def url_for(db): 
    from urllib.parse import urlsplit, urlunsplit
    s = urlsplit(ADMIN); return urlunsplit(s._replace(path="/" + db))
OUT = os.path.join(os.path.dirname(__file__), "out")
cmd = sys.argv[1]
if cmd == "drop":
    with psycopg.connect(ADMIN, autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {DB} WITH (FORCE)")
        print("exists after drop:", c.execute("select count(*) from pg_database where datname=%s", (DB,)).fetchone()[0])
    sys.exit()
if cmd == "load":
    with psycopg.connect(ADMIN, autocommit=True) as c:
        assert c.execute("select count(*) from pg_database where datname=%s", (DB,)).fetchone()[0] == 0, "exists"
        c.execute(f"CREATE DATABASE {DB}")
    with psycopg.connect(url_for(DB), autocommit=True) as c:
        c.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        c.execute("""
        CREATE TABLE volcano (id int PRIMARY KEY, name text, lat double precision, lon double precision, geog geography(Point,4326));
        CREATE TABLE gvp_eruption (eruption_number int PRIMARY KEY, volcano_id int REFERENCES volcano, vei int, start_date date, end_date date, activity text);
        CREATE TABLE usgs_event (id text PRIMARY KEY, t timestamptz, lat double precision, lon double precision, depth real, mag real, mag_type text, geog geography(Point,4326));
        CREATE TABLE volcano_day (volcano_id int, day date, so2_15 real, so2_15_n smallint, so2_50 real, so2_50_n smallint, omi_15 real, omi_15_n smallint,
             frp_modis real, frp_viirs real, hot_n smallint, eq_n smallint, PRIMARY KEY (volcano_id, day));
        CREATE TABLE volcano_bins (volcano_id int, day date, ring smallint, band smallint, value real, n smallint, PRIMARY KEY (volcano_id, day, ring, band));
        CREATE TABLE thermal_detection (t date, lat real, lon real, frp real, conf smallint, sat char(1), volcano_id int, geog geography(Point,4326));
        """)
        vols = list(csv.DictReader(open(f"{OUT}/gvp_volcanoes.csv")))
        with c.cursor().copy("COPY volcano (id,name,lat,lon) FROM STDIN") as cp:
            for v in vols: cp.write_row((int(v["Volcano_Number"]), v["Volcano_Name"], float(v["Latitude"]), float(v["Longitude"])))
        c.execute("UPDATE volcano SET geog = ST_MakePoint(lon, lat)::geography")
        vid = {v["Volcano_Name"]: int(v["Volcano_Number"]) for v in vols}
        with c.cursor().copy("COPY gvp_eruption FROM STDIN") as cp:
            for e in csv.DictReader(open(f"{OUT}/gvp_eruptions.csv")):
                def d(p):
                    try: return dt.date(int(e[p + "Year"]), int(e[p + "Month"] or 1) or 1, int(e[p + "Day"] or 1) or 1)
                    except Exception: return None
                if int(e["Volcano_Number"]) in vid.values():
                    cp.write_row((int(e["Eruption_Number"]), int(e["Volcano_Number"]), int(e["ExplosivityIndexMax"]) if e["ExplosivityIndexMax"] else None,
                                  d("StartDate"), d("EndDate"), e["Activity_Type"]))
        with c.cursor().copy("COPY usgs_event (id,t,lat,lon,depth,mag,mag_type) FROM STDIN") as cp:
            for f in ("usgs_a.csv", "usgs_b.csv"):
                for r in csv.DictReader(open(f"{OUT}/{f}")):
                    cp.write_row((r["id"], r["time"], float(r["latitude"]), float(r["longitude"]), float(r["depth"] or 0), float(r["mag"]) if r["mag"] else None, r["magType"]))
        c.execute("UPDATE usgs_event SET geog = ST_MakePoint(lon, lat)::geography")
        # synthetic series at the full span (2000-01-01 .. 2026-10-31), 24 volcanoes, values shaped like Taal's January 2020
        random.seed(1); days = [dt.date(2000, 1, 1) + dt.timedelta(i) for i in range((dt.date(2026, 11, 1) - dt.date(2000, 1, 1)).days)]
        ids = list(vid.values()) + [999999]
        with c.cursor().copy("COPY volcano (id,name,lat,lon) FROM STDIN") as cp: cp.write_row((999999, "pad-24th", 13.0, 123.0))
        rnd = lambda: round(random.expovariate(20), 4)
        with c.cursor().copy("COPY volcano_day FROM STDIN") as cp:
            for v in ids:
                for d in days:
                    cp.write_row((v, d, rnd(), random.randint(0, 40), rnd(), random.randint(0, 900), rnd() if d.year >= 2004 else None,
                                  random.randint(0, 30), random.choice([None] * 20 + [round(random.uniform(5, 200), 1)]), None, 0, random.randint(0, 3)))
        with c.cursor().copy("COPY volcano_bins FROM STDIN") as cp:   # 4 rings x 1 band (S5P from 2018-05) + 4 rings x 1 band (fire)
            for v in ids:
                for d in days:
                    for ring in (5, 15, 30, 50):
                        cp.write_row((v, d, ring, 1, rnd(), random.randint(0, 500)))
        with c.cursor().copy("COPY thermal_detection (t,lat,lon,frp,conf,sat,volcano_id) FROM STDIN") as cp:   # 10 % sample of 400k
            for _ in range(40000):
                v = random.choice(vols); cp.write_row((random.choice(days), float(v["Latitude"]) + random.gauss(0, .05), float(v["Longitude"]) + random.gauss(0, .05),
                                                      round(random.uniform(1, 300), 1), random.randint(0, 100), random.choice("MV"), int(v["Volcano_Number"])))
        c.execute("UPDATE thermal_detection SET geog = ST_MakePoint(lon, lat)::geography")
        c.execute("""CREATE INDEX ON usgs_event USING gist (geog); CREATE INDEX ON usgs_event (t); CREATE INDEX ON volcano USING gist (geog);
                     CREATE INDEX ON thermal_detection USING gist (geog); CREATE INDEX ON thermal_detection (volcano_id, t); VACUUM ANALYZE;""")
        print("loaded")
if cmd in ("load", "measure"):
    with psycopg.connect(url_for(DB), autocommit=True) as c:
        res = {"db_bytes": c.execute("select pg_database_size(current_database())").fetchone()[0]}
        res["tables"] = [dict(zip(("table", "rows", "total", "index"), r)) for r in c.execute("""
            select relname, n_live_tup, pg_total_relation_size(relid), pg_indexes_size(relid) from pg_stat_user_tables order by 3 desc""")]
        Q = {"q1_events_30km_dates": "SELECT count(*), max(mag) FROM usgs_event e JOIN volcano v ON v.name='Taal' WHERE ST_DWithin(e.geog, v.geog, 30000) AND e.t >= '2019-12-01' AND e.t < '2020-02-15'",
             "q2_14d_before_vei3": "SELECT g.eruption_number, avg(d.so2_15), max(d.eq_n) FROM gvp_eruption g JOIN volcano_day d ON d.volcano_id=g.volcano_id AND d.day >= g.start_date - 14 AND d.day < g.start_date WHERE g.vei >= 3 GROUP BY 1",
             "q3_nearest": "SELECT name, ST_Distance(geog, ST_MakePoint(121.05,14.10)::geography) FROM volcano ORDER BY geog <-> ST_MakePoint(121.05,14.10)::geography LIMIT 1"}
        res["queries"] = {}
        for k, q in Q.items():
            c.execute(q).fetchall()                                     # warm
            ms = []
            for _ in range(5):
                t = time.perf_counter(); c.execute(q).fetchall(); ms.append((time.perf_counter() - t) * 1000)
            plan = c.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + q).fetchone()[0][0]
            res["queries"][k] = {"client_ms_median": round(sorted(ms)[2], 1), "server_exec_ms": plan["Execution Time"], "top_node": plan["Plan"]["Node Type"]}
        print(json.dumps(res, indent=1, default=str)); json.dump(res, open(f"{OUT}/pg_size.json", "w"), indent=1, default=str)
