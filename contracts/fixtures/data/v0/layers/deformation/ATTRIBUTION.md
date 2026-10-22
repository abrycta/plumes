# Attribution: deformation fixture

`taal-032D_07536_111313.tif`, the `deformation-velocity` entry in `../../layers.json` and the `los_comet_032D_07536_111313` series in `../../volcano/taal.json` are derived from the COMET Volcano Portal LiCSBAS series for Taal, Sentinel-1 frame 032D_07536_111313 (downloaded 2026-10-22).

COMET LiCSBAS (COMET Volcano Portal, https://comet.nerc.ac.uk/comet-volcano-portal/), processed by COMET, not by Plumes; LiCSAR contains modified Copernicus Sentinel data 2014–2026. Changes made: reduced to a summit series and a mean velocity per frame. Licensed under CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/). Non-commercial use only.

See `docs/LICENCES.md` (`comet-licsbas`) and DECISIONS L1a, L11. Rebuild: `cd pipeline && PYTHONPATH=. uv run --group comet python scripts/build_fixture_deformation.py`.
