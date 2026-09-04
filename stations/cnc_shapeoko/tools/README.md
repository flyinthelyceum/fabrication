# CNC Station Tool List

Canonical, editable list lives in the Google Sheet "CNC Station – Tool List v1" — Drive folder IC / CNC Station 2026. Sheet URL: https://docs.google.com/spreadsheets/d/1AtX_waFmqeCopwA0GV06VFfvzlMztYqAFsnEd0OT-00
`tool_list.csv` and `tool_list_add.csv` here are point-in-time snapshots of the Sheet's TRAY and ADD tabs, committed for the build123d tray generator to read.
Regenerate by exporting the Sheet's TRAY tab (File > Download > CSV) over `tool_list.csv`, and the ADD tab over `tool_list_add.csv` — never hand-edit these snapshots, with one exception: `capture_ingest.py` upserts the row it just captured, and the same row lands in the Sheet through the CAPTURE tab, so the two stay in step. The ADD tab's subtotal rows (blank id) are dropped from the snapshot.

## Capture (spec v3, approved 2026-09-04)

Trays are milled from two-tone Kaizen foam on the Shapeoko, one piece per drawer. A pocket comes from one of three socket rules in `parts/trays.py` and nowhere else:

- `cutter` — a CATALOG row: `oal_mm` by its largest diameter
- `collet` — a CATALOG row: `oal_mm` by the DIN 6499 ER-16 body
- `captured` — a CAPTURED row: the pocket IS the tool's traced outline, from `captures/T0xx.dxf`, at a depth of `height_class` plus `FOAM_DEPTH_ALLOW`

Everything that is not a cutter or a collet gets traced. The bounding-box-plus-clearance rule and its three caliper numbers are gone (ruled 2026-09-03, replaced 2026-09-04): a wrench is not a box.

### The sheet family, and why it stops at A2

**A trace sheet never has to be bigger than the drawer.** Anything that will not lie in a drawer does not get a foam pocket, so it never gets traced. That is the whole sizing rule, and it is what sets the top of the family.

The drawers are `parts/drawers.py`. After the 2026-09-04 inset-front ruling every box is 259 wide outside; 18mm birch a side, 500mm slides, a front rabbet and a back set in one thickness with its own thickness behind it give the **clear interior 446 deep x 223 wide** (`drawers.interior`, same for all three boxes). A tool that fills that interior end to end does not draw a 446 x 223 line: the collar rides 7mm outside it, so the loop on the paper is **460 x 237**. The largest sheet's window has to hold that, not the tool.

| size | page mm | window mm | largest tool | tag ids | tag mm | what it is for |
|---|---|---|---|---|---|---|
| LETTER | 216 x 279 | 180 x 180 | 162 x 162 | 0–3 | 30 | the default. Most of the cutter and instrument drawers. |
| A4 | 210 x 297 | 174 x 198 | 180 x 156 | 4–7 | 30 | the default where the paper is metric. |
| TABLOID | 279 x 432 | 243 x 313 | 295 x 225 | 8–11 | 40 | the long-tool sheet: the jog pendant (228), a torque wrench, a long clamp. |
| A3 | 297 x 420 | 261 x 301 | 283 x 243 | 12–15 | 40 | TABLOID's metric twin: wider, shorter. |
| ARCH B | 305 x 457 | 269 x 338 | 320 x 251 | 20–23 | 40 | the plotter roll's size, where the shop has ARCH B and not TABLOID. |
| A2 | 420 x 594 | 384 x 475 | 457 x 366 | 16–19 | 40 | the ceiling: the window covers the whole drawer interior plus the collar's halo, 14.6mm to spare on the long axis. |

"Largest tool" is the window less one collar diameter and the crop's 2mm inset a side, so it is what will actually come back, not what will physically lie on the paper.

Tag size is a documented constant per size, not a formula: 30mm on the two letter-class sheets, 40mm on the four big ones. It stops at 40 rather than growing to 50 on A2 because a bigger tag eats the window from both ends, and 50mm tags would leave A2's window at 454.6 against the 460 a full-interior tool draws. The window covering the drawer wins.

Every sheet keeps the same 14mm gutter, the same 1mm window border, the same TAG and HEIGHT boxes, the same 100mm scale bar and the same three rules. The only things that change are the page, the tag size and the quartet.

Generate them with `PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/trace_sheet.py`, or one at a time with `--size TABLOID`. `trace_sheet.pdf` stays the LETTER sheet under its old name so every existing link resolves; the family is `trace_sheet_<size>.pdf`.

### Self-identifying sheets

Nobody types the paper size into the Form. Each size carries a **different quartet of ArUco ids** out of DICT_4X4_50 (the table above), `capture_ingest.identify` reads the quartet out of the photo and looks that size's geometry up in `trace_sheet.SIZES`, and the rest of the pipeline follows. Two things fall out:

- a student who prints TABLOID and photographs it gets TABLOID's window and TABLOID's mm, with nothing to get wrong;
- the failure that would otherwise be silent, a sheet read against the wrong page size and every dimension out by the ratio of the two pages, is not reachable. It is a rejection, not a wrong number.

LETTER keeps ids 0–3 and keeps its exact v1 window (180 x 180 at 17.95, 48.0), so sheets photographed before the family existed still ingest to the same numbers. T025 and T026 were re-run against the family code and came back to within 4e-7 mm of their pre-family values.

A size counts as present at two detected markers, not one: a lone stray id out of a 50-marker dictionary is a detector false positive and should not reject an otherwise good capture. Two sizes at two markers each is `two different sheet sizes in frame` and rejects; no size at two markers is `no known sheet size found` and rejects.

### The two limits the collar imposes

- **14.0mm is the hard floor.** The collar's contact cylinder is `trace_sheet.COLLAR_OD` = 14.0 across, which is `2 x capture_ingest.PEN_R`. Nothing narrower than that exists as far as the trace is concerned, and every concave corner of the tool tighter than 7mm comes back as a 7mm fillet. That always makes the foam tongue smaller than the notch, never larger, so the tool still drops in.
- **About 20mm is the practical floor for a slot.** A 14mm collar cannot be walked into a slot, throat or gap much narrower than 20mm without the pencil losing contact, so the line bridges it and the pocket comes out solid there. If the tool has one, caliper that one dimension and write it on the sheet. That is a rule on the sheet and on the card, not a note in this file.

### The procedure (this is the laminated card, `capture_card.pdf`)

1. **SHEET.** Take a trace sheet: the smallest size the tool lies in with a finger's width to spare. The size and its window are printed under the window. Write the tool's TAG (T0__, from the drawer label) in the TAG box.
2. **HEIGHT.** Slide the tool edge-on into the gauge. The smallest slot it enters is its height: 10, 20, 30, 40 or 50. Write it in the HEIGHT box.
3. **LAY.** Lay the tool inside the window, as it sits in the drawer. Clear of the border line and of the four corner squares.
4. **TRACE.** Pencil in the TRACE collar. Straight up like a candle, collar riding the tool. Trace the OUTSIDE only, all the way round, until the line meets itself.
5. **PHOTO.** Lift the tool off. Photograph the whole sheet from above: all four corner squares in frame, sheet flat, no shadow across the line.
6. **FORM.** Open the form "CNC tray capture": tag, height, photo. Done. The software reads the corner squares to know which paper you used. The tray regenerates; a rejected sheet comes back with one line saying why.

Two cases where the answer is not to trace, both on the sheet and on the card:

- **It does not fit the window.** Take a bigger sheet, remembering the pencil rides 7mm outside the tool, so leave 10mm of clear paper all round. If the tool is a plain rectangular slab, do not trace it at all: write L, W and thickness in the boxes and photograph the sheet.
- **It has a slot, throat or gap under 20mm.** The collar cannot enter one. Caliper that one dimension and write it on the sheet beside the boxes.

One tool per sheet. Never a hand in the window, never a tool on its edge, never a tool that moved. Sheets, collar, pencil and gauge live in Drawer 1. Print sheets at 100%: the bar at the bottom must measure 100mm.

### The pen rule

The tracing tool is a standard wooden hex pencil (7mm across flats) in the printed TRACE collar (`tracing_collar.stl`): a 14.0mm OD contact cylinder with a hex bore, the lead exiting flush at the bottom face. The collar, not the pencil, rides the tool, so the drawn line's centreline is always the tool's outline offset outward by exactly the collar's radius, whatever the tool's height and however sharp the pencil. `capture_ingest.PEN_R = 7.0` is that radius (CONFIDENCE: design; verify with calipers on the printed collar once and correct it if the printer ran fat or thin). No other pen, no other collar: a bare pencil traces a line whose offset depends on the taper and the tool's height, and the pocket comes out wrong by an unknowable amount.

### What the ingest does

`capture_ingest.py <image> <tag> <height>` (or `ingest(image_path, tag, height_slot, source="trace")`): finds the ArUco tags, reads the quartet to know which paper this is, rectifies the photo into that size's mm frame (three tags is the floor), crops the field, thresholds the pencil line, takes the largest closed contour, measures the line's own width from its hole, insets by half of that plus `PEN_R`, offsets by `FOAM_CLEAR` (1.0, settled by the fit test), and writes:

- `captures/T0xx.dxf` — the pocket, one closed loop, mm, laid with its long side along X and its box's corner at the origin
- `captures/preview/T0xx.png` — the rectified sheet, the detected line in orange, the pocket in cyan, L / W / H in the corner. Look at this before trusting a capture.
- the tag's row in `tool_list.csv`: `dims_status=CAPTURED`, `silhouette`, `height_class`, `bbox_l_mm` / `bbox_w_mm` (the tool's L and W, for the record; trays pack by the loop's own box)

It rejects, with one line and nothing written, when: two different sheet sizes are in the frame; no known quartet is in the frame; fewer than three tags of the identified size are found; the trace is not a closed loop; the trace touches the window edge (the message names the size and says to take a bigger sheet); a second trace in the window is more than a quarter of the largest's area.

`test_capture.py` runs the whole family end to end (every size rendered, warped about 20 degrees, identified from its own quartet, and a 50 x 100 stadium recovered within 0.3mm), the LETTER stadium case, a 94%-print case proving the same tool comes back correct with `--print-scale 0.94` and about 7% too big without it, and the five reject paths: `PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/test_capture.py`.

If the sheet did not print at 100% (a printer's own margins forced a smaller scale), pass `--print-scale` — measured scale-bar length / 100, read off the line under the bar on the printed sheet — and the ingest corrects for it; every capture from an uncorrected scaled sheet is wrong by that same ratio.

### The columns

`tool_list.csv` and the Sheet's TRAY tab carry, beyond the catalog columns:

| column | values | who writes it |
|---|---|---|
| `dims_status` | `CATALOG` (datasheet numbers: cutters, collets), `CAPTURED` (traced, silhouette on disk), `MEASURE` (nothing yet) | CATALOG by hand; CAPTURED by the ingest; MEASURE is the default |
| `height_class` | 10, 20, 30, 40, 50: the gauge slot the tool passed | the ingest, from the Form |
| `silhouette` | `captures/T0xx.dxf`, relative to this directory | the ingest |

`bbox_l_mm`, `bbox_w_mm`, `bbox_h_mm` stay in the schema as the ingest's record of L and W (and the old photo estimates); `trays.py` reads none of them. `socket_note` stays as a free note.

### The Form and the CAPTURE tab

The Sheet's CAPTURE tab (columns `timestamp, tag, height_slot, photo_url, status, reason`) is the landing tab. `~/labnode-scripts/cnc-capture-ingest.py` reads rows whose `status` is blank, downloads the photo from Drive, runs the ingest, writes `status` (`captured` / `rejected` / `error`) and `reason` back, uploads the preview to `IC / CNC Station 2026 / 05 Capture / preview`, and puts one line in the 07:05 digest.

The Form itself is a five-minute manual task (the Drive token on the Mini has no Forms scope, and this is not worth a second credential). In Google Forms:

1. New form, title **CNC tray capture**. Settings > Responses: collect email off; Presentation: confirmation message "Captured. Check the tray preview tomorrow morning."
2. Question 1, **Tag**, Dropdown, required. Options: every `id` in the TRAY tab (T013..T058 today; copy the column). Keep the list in the TRAY tab's order.
3. Question 2, **Height slot**, Multiple choice, required. Options: `10`, `20`, `30`, `40`, `50`.
4. Question 3, **Photo of the sheet**, File upload, required, images only, one file, 10 MB. Google will ask to create an upload folder: put it in **IC / CNC Station 2026 / 05 Capture** (the folder exists; choose it or move the auto-created one inside it).
5. Responses > Link to Sheets > Select existing spreadsheet > "CNC Station – Tool List v1". The Form creates a new tab; rename it **CAPTURE** and delete the empty CAPTURE tab that is there now, OR leave the empty one and re-point `CAPTURE_TAB` in the script at the Form's tab name. The Form writes `Timestamp, Tag, Height slot, Photo of the sheet` as columns A..D; the script fills `status` and `reason` in E and F.
6. Print the Form's link as a QR on the card's back, or put the short link on the drawer label.

### The physical kit (Drawer 1)

- a stack of `trace_sheet.pdf` (LETTER), printed at 100% (the scale bar is the check), and a few of each larger size behind them: `trace_sheet_tabloid.pdf` is the one the pendant needs
- the TRACE collar (`tracing_collar.stl`, PLA, 0.2 layer, no supports, bore up) with a hex pencil in it
- the height gauge (`height_gauge.stl`, 180 x 60 x 60, prints flat on its back; five through-slots 10..50, labels embossed on the front)
- `capture_card.pdf`, laminated

All of them are in Drive under IC / CNC Station 2026 / 06 Tool Capture, generated by `trace_sheet.py`: the six sheet PDFs, the card, the gauge and the collar.

### v2: the machine captures its own tools

The ingest's image source is a plug: `ingest(..., source="camera")` is reserved for a camera on the Z plate looking down at a tool on a fiducial mat on the bed, one gSender macro to the capture pose, a frame grab on the console. Same ingest, same tags, same output. It raises `NotImplementedError` today. Nothing in v1 is built in a way that v2 would have to undo: the sheet frame becomes the mat frame and the tag positions become the mat's.

The Sheet's LOG tab (date, reading, who) is the human half of the station log; the first row is reserved for the commissioning continuity reading. It is not snapshotted here.

## DXF layers the tray export writes (C16)

The foam tray goes out as one DXF per drawer, `tray_<drawer>.dxf`, with the geometry on named layers so the CAM reader (Carbide Create) takes depth from the layer and never from a guess:

- `OUTLINE` — the tray blank, through; the drawer's inside floor
- `POCKET_D<depth>` — one layer per pocket depth in mm, e.g. `POCKET_D8.35`; closed loops (pocket plus its finger scoop), pocket to that depth from the top face with the 1/8in flat endmill (`lib.house.POCKET_TOOL_D`)
- `TEXT_D<depth>` — label glyphs, milled through the black top layer with a text cutter; the depth is the top layer plus a bite

Text depth and pocket depths are both read off the layer name. The 30mm two-tone blank is black over white; every pocket floor is at least `FOAM_REVEAL` into the white.

## DXF layers the birch callouts write (C17)

Five birch parts carry a V-carved word (finish ruling 2026-09-03: carved through matte black to raw birch, no fill, on the Shapeoko; the Universal cuts clear acrylic only and no acrylic part carries text). The carve is a SECOND fixture, after paint, so each of those parts' DXFs carries two layers on top of the CUT/BACK/POCKET set, written by `parts/callouts.py`:

- `VCARVE` — the letter outlines, closed loops. V-carve with the 60-degree bit (tool list T023) to `callouts.VCARVE_D` at the centreline; the STEP shows a 1mm flat stand-in.
- `REGISTER` — exactly two circles, each coincident with a void the part already has (no new holes). Pin the spoilboard at the two centres with pins of the circles' diameter and drop the painted part over them. Per part: drawer fronts and the lungs door use the pull's two end arcs; the stock comb its first and last slot tips; the rear door its two catch bores; the console plate its two short-edge lip screws.

Both layers are drawn as the carved face is SEEN on the second fixture. For every part but the rear door that is the CUT frame, and the two layers ride the part's own DXF. The rear door's word is on its outside face, the BACK of its drawing, so its second fixture is a SEPARATE file, `rear_door_carve.dxf`: the door outline flipped about its vertical centreline on `OUTLINE_FLIPPED` (reference, not a toolpath; the door is already cut), and `VCARVE` + `REGISTER` in that same flipped frame, the register circles on the flipped catch bores. `rear_door.dxf` holds the CUT frame only. No file mixes the two frames.

Three registers (drawer fronts, lungs door, stock comb) are capsule ends, not round holes; the gate carries a standing RULING WANTED line for each until Jared accepts them or names holes.

## The nest and the sheet count (C18)

`nest.py` is the first-cut gate: every sheet part the assembly places, laid onto the stock it is cut from, and the count that comes out. Run it with `PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/nest.py`; `check.py` asserts the same count as a STANDING line (`nest: N sheets of 5x5`) so the order and the model cannot drift apart.

Three nests, three stocks, one output folder `export/cnc_shapeoko/nest/`:

- `sheet_NN.dxf` — 18mm 5x5 Baltic birch, every solid in `assembly.birch_components` (groups carcass, plinth, drawer, carriage). The deck and the top cap are track-saw parts by the 2026-09-02 ruling and take a sheet each, flagged TRACK SAW. Everything else is Shapeoko, and because the travel (1237) is shorter than the sheet (1525) on both axes, every Shapeoko sheet is ripped first: full-width rips between shelves, crosscuts between segments, every blank's parts within the travel less one cutter diameter. The rips are drawn.
- `laser_NN.dxf` — 3mm clear acrylic on the Universal's large bed (`LASER_BED_LARGE`): the rear door's reveal, the console's reveal and three panes, the cradle's lip.
- `foam_NN.dxf` — two-tone Kaizen foam, one tray per drawer from `trays.plan`.
- `manifest.csv` — one row per placement: file, part, x, y, size as placed, grain rule, shelf, segment.

Rectangles only, greedy, biggest first, 10mm kerf/margin between rectangles and to every blank edge. The count is a ceiling the shop can only beat. Grain is along the sheet's X; standing seen panels keep theirs vertical, rails and drawer panels along their length, the rest may turn — shop convention, carried as a RULING WANTED line in the gate until Jared confirms or names exceptions in `nest.GRAIN_OVERRIDES`.

The blanks are read off the placed solids in `assembly.components`, never off the export folder (which is gitignored and only as current as its last run). The drawings on a sheet are the parts' own layers, rebuilt through each module's builders and moved with the part, plus:

- `SHEET` — the stock outline
- `RIP` — the track-saw lines (Shapeoko sheets only)
- `PART_<label>` — the placed blank's rectangle, one layer per part, so a part's name is in the layer table exactly once per placement
- `LABEL` — the part's name as glyph outlines inside its rectangle; reference, not a toolpath

The rear door contributes its CUT frame only; its outside-face carve stays in `rear_door_carve.dxf`. The console plate's `ACRYLIC` layer is dropped from the birch sheet because the panes ride the laser nest as their own parts.
