# COMET licence email (not sent — decided 2026-10-22)

Status: **not sent — decided 2026-10-22.** Kurt decided the same day not to email COMET (DECISIONS L1a): the portal's CC BY-NC 4.0 notice is treated as covering the LiCSBAS data, which Plumes publishes with attribution and the CC BY-NC notice. The draft below is kept as history only.

Where to send it: the COMET Volcano Portal's "Contact/Give Feedback" page, https://comet.nerc.ac.uk/comet-volcano-portal/contact (the copyright page lists no email address; checked 2026-10-22).

Why ask: the portal's copyright page (https://comet.nerc.ac.uk/comet-volcano-portal/copyright, read 2026-10-22) says "Images used throughout the website are licensed under the Creative Commons Attribution-NonCommercial 4.0 International". It says nothing about the LiCSBAS JSON files under `comet-volcanodb.org/data/disp_data_gacos/`, and the underlying LiCSAR products are Copernicus-derived (OGL v3 on CEDA). Plumes would publish derived series and a velocity grid, not images, so the images licence does not settle it.

---

**Subject:** Permission to show derived LiCSBAS time series from the COMET Volcano Portal on a non-commercial site

Dear COMET Volcano Portal team,

I am building Plumes, a non-commercial portfolio site that records the past activity of the 24 active Philippine volcanoes from public satellite and bulletin data. It is a retrospective record only, not a monitoring or warning service, and every view points readers to PHIVOLCS.

Your portal's LiCSBAS time series cover 18 of these volcanoes. I would like to:

1. reduce each volcano's GACOS-corrected series (the `disp_data_gacos` JSON files) to one line-of-sight time series near the summit, relative to your reference area, and show it as a chart;
2. show one mean line-of-sight velocity grid per frame as a map layer;
3. publish these derived files (a few kilobytes per volcano) with the site under CC BY-NC 4.0, with an acknowledgement of COMET and "LiCSAR contains modified Copernicus Sentinel data [year]" on every chart and in the site's sources page, and a link back to the portal. The original files would be kept in a private archive only, not redistributed.

Is this use fine with you? If so, which citation or acknowledgement would you prefer (for example a paper for LiCSBAS and the portal)? I am also glad to follow any other conditions, or to leave the data as links only if you would rather.

Thank you for making this work available.

Kind regards,
Kurt
https://krtmtthw.dev

---

When the reply arrives: record it as a new row in DECISIONS.md (date, the permission and conditions quoted, the citation), copy the citation into LICENCES.md (Sentinel-1 InSAR entry) and the registry entry, then unblock M2 item 9 in [../LAYERS-PLAN.md](../LAYERS-PLAN.md) §7. If COMET declines or does not answer, deformation stays as links (Q8's M1 form).
