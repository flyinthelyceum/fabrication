# CNC Station Tool List

Canonical, editable list lives in the Google Sheet "CNC Station – Tool List v1" — Drive folder IC / CNC Station 2026. Sheet URL: https://docs.google.com/spreadsheets/d/1AtX_waFmqeCopwA0GV06VFfvzlMztYqAFsnEd0OT-00
`tool_list.csv` and `tool_list_add.csv` here are point-in-time snapshots of the Sheet's TRAY and ADD tabs, committed for the build123d tray generator to read.
Regenerate by exporting the Sheet's TRAY tab (File > Download > CSV) over `tool_list.csv`, and the ADD tab over `tool_list_add.csv` — never hand-edit these snapshots. The ADD tab's subtotal rows (blank id) are dropped from the snapshot.

## Capture (ruled 2026-09-03)

Trays are milled from two-tone Kaizen foam on the Shapeoko, one piece per drawer. Every pocket is the tool's bounding box plus clearance, whatever its kind, so the capture for a MEASURE row is three caliper numbers: `bbox_l_mm`, `bbox_w_mm`, `bbox_h_mm`. No photos, no scans, no outlines. Catalog parts take the datasheet. The `socket_note` column is retired as a rule (there are no per-kind socket rules any more); it stays in the schema until the tray rewrite (C16) drops it from the reader.

The Sheet's LOG tab (date, reading, who) is the human half of the station log; the first row is reserved for the commissioning continuity reading. It is not snapshotted here.

## DXF layers the tray export writes (C16)

The foam tray goes out as one DXF per drawer, `tray_<drawer>.dxf`, with the pocket geometry on named layers so the CAM reader takes depth from the layer and never from a guess:

- `CUT` — the tray outline, through
- `POCKET_<depth>` — one layer per pocket depth in mm, e.g. `POCKET_20`; closed loops, pocket to that depth from the top face
- `LABEL` — text beside each pocket, engrave 0.8mm
- `FINGER` — finger reliefs, same depth as the pocket they serve

Until C16 lands, `tray_d1.dxf` carries only `CUT` and the engrave artwork from the printed-tray era.
