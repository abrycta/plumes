"""Item 16: EECU-seconds of the Run 1 Taal month (S5P SO2 two rings + MOD14A1) via EE profiles (retrying until ready)."""
import io, contextlib, json, os, runpy, sys, time, ee
k = os.environ["EE_KEY_FILE"]; i = json.load(open(k)); ee.Initialize(ee.ServiceAccountCredentials(i["client_email"], k), project=i["project_id"])
ids = []; t = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    with ee.data.profiling(ids.append):
        runpy.run_path(sys.argv[1], run_name="__main__")
wall = time.time() - t
for attempt in range(8):
    try:
        txt = ee.ApiFunction.call_("Profile.getProfiles", ids=ids, format="text").getInfo(); break
    except ee.EEException as e:
        time.sleep(5); txt = f"not ready: {e}"
print("wall_s", round(wall, 1), "profiles", len(ids)); print(txt[:1500])
