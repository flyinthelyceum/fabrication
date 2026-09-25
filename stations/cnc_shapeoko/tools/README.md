# CNC Station Tool List

Canonical, editable list lives in the Google Sheet "CNC Station – Tool List v1" — Drive folder IC / CNC Station 2026. Sheet URL: https://docs.google.com/spreadsheets/d/1AtX_waFmqeCopwA0GV06VFfvzlMztYqAFsnEd0OT-00
`tool_list.csv` and `tool_list_add.csv` here are point-in-time snapshots of the Sheet's TRAY and ADD tabs, committed for the build123d tray generator to read.
Regenerate by exporting the Sheet's TRAY tab (File > Download > CSV) over `tool_list.csv`, and the ADD tab over `tool_list_add.csv` — never hand-edit these snapshots, with one exception: `capture_ingest.py` upserts the row it just captured, and the same row lands in the Sheet through the CAPTURE tab, so the two stay in step. The ADD tab's subtotal rows (blank id) are dropped from the snapshot.

## Drawer inserts and capture (capture spec v3, 2026-09-04; inserts 2026-09-25)

**Drawer inserts (ruled 2026-09-25; the foam trays and `parts/trays.py` are retired).** Jared, when the foam trays overflowed D2 and D3: "all the cutters need to be oriented by kind and oriented standing up. and we need to learn from the way that carbide 3d has built their holders ... we have too much goofy shit going on." The research, both red teams and the design are at notes.aaand.space/cnc-drawer-inserts.html.

Every drawer holds a stack of loose strips of 1/2in two-colour HDPE (ColorCore: black cap, white core), full inside width, front to back, each a whole number of 25mm modules deep (Carbide's rack module) and each holding one KIND of thing, with its kind word V-carved at its left end. The last strip is the keystone BIN: a frame cut to whatever depth is left, so the stack fills the drawer. Every place is 11 deep, into the white, so an empty place shows white; there are no free places, so white always means something is out. Buying a cutter re-mills one strip. `parts/inserts.py` builds all of it from the TRAY tab's `strip`, `store` and `hold_mm` columns:

- `bore` — a cutter or driver standing shank down: shank (or `hold_mm`'s first number) + 0.25, at a pitch of max(25, body + 10), where body is the cut diameter or `hold_mm`'s second number (a T-handle's thickness).
- `collet` — an ER16 standing nut off in a stepped bore, 17.6 x 5 over 13 x 11 (Carbide's collet caddies).
- `socket` — a part standing on end in a snug rectangle, `hold_mm` + 0.8 (0.4 a side, Carbide's essential-clamp caddy), with an 11mm finger gap on its thin side.
- `slot` — a flat part standing on edge, the same way.
- `recess` — a part lying in a drop-in rectangle, its box (L x W) + 2.
- `cup` — a round part standing in a round drop-in, `hold_mm` + 2.
- `case` — lives in another row's case. `loose` — lives in its drawer's BIN. `dock` — lives at the machine (wrenches, pendant, BitZero), not in a drawer; the dock is not modelled yet and the gate carries it as a TODO.

The capture pipeline below stays: a captured row's L x W and height are what a `recess` or `socket` is sized from. Its silhouette no longer cuts anything.

### The procedure (this is the laminated card, `capture_card.pdf`)

1. **LAY.** Take a capture sheet: the smallest size the tool lies in with a finger's width of magenta all round. Lay the tool FLAT inside the magenta window, on its widest face, as it sits in the drawer, clear of the border. Note its TAG (T0__, from the drawer label).
2. **MEASURE.** Measure the tool's tallest point above the sheet with the ruler, in mm, as it lies. A bottle on its side is its diameter.
3. **SHOOT.** Stand over the sheet. Phone flat, high enough that the whole sheet is about a third of the screen, all four corner squares showing. The bigger and rounder the tool, the higher the phone. No flash, no lamp shadow. Do not move the tool.
4. **SUBMIT.** Open the form "CNC tray capture": tag, height in mm, the photo. Done. The software reads the corner squares to know which paper you used and takes the tool's own outline out of the magenta. The tray regenerates; a rejected sheet comes back with one line saying why.

Two cases where the answer is not to photograph, both on the card:

- **It does not fit the window.** Take a bigger sheet: LETTER, then TABLOID. Nothing that will not lie in a drawer gets a pocket, so nothing bigger than TABLOID needs a sheet.
- **It will not lie flat, or it shines.** A tool that rocks throws its outline: prop it level with a scrap of card. Chrome reflects the magenta and can lose an edge: turn the sheet under the light and shoot again. Look at the preview the software posts back.

One tool per sheet. Never a hand in the window, never a tool on its edge, never a lamp or a flash throwing a hard shadow. Sheets and the ruler live in Drawer 1. Print sheets in colour at 100%: the bar at the bottom must measure 100mm.

### The magenta window (2026-09-11, about 11:00)

The window is filled with a flat, saturated magenta (`trace_sheet.WINDOW_FILL`, RGB 236, 0, 140: process magenta, C0 M100 Y40 on any colour printer). Jared's call after the white-capped Vactra bottle: a white or light-grey tool on white paper is white on white, and no threshold or colour model separates it reliably; on magenta it is a hole in the colour. Tags, quiet zones, the scale bar and the four rules stay on white (the markers want their contrast, the type wants reading). The TAG and HEIGHT boxes are gone: the Form carries both and nothing reads them off the paper. File names and the LETTER/TABLOID tag geometry are unchanged, so every link resolves and every white sheet already printed still ingests (see the fallback below).

**The mat idea.** A magenta sheet is a mat, not a consumable: laminate one matte per size and keep it in the drawer. Matte, because a gloss laminate throws a specular patch of the ceiling light that the chroma key reads as tool. The tool lies on the mat, the phone shoots, the mat goes back. Print the paper ones for the classroom; the laminated pair is the station's.

### Why the collar and the tracing are gone

From 2026-09-04 to 2026-09-11 the procedure was SHEET / HEIGHT / LAY / TRACE / PHOTO / FORM: a pencil in a printed 14mm collar rode the tool and drew a line 7mm outside it, the tool was lifted off, the sheet photographed, and the ingest inset the line by half its width plus the collar's radius. Jared red-teamed it on 2026-09-11 as too clunky for a student to get right, and the first two student sheets that day proved it: both traced with a bare pencil against the tool, no collar, so the offset was unknowable and both were rejected. The photo capture removes the whole failure class. There is no offset to get wrong, no collar to lose, no slot the collar cannot enter, no gauge: the tool's own edge is the outline, and the height is a number off a ruler. The trace source stays in `capture_ingest.py` as `source="trace"`, unchanged, so T025 and T026 (captured that way) can be re-run; nothing new uses it. The collar's STL is still generated for the same reason.

### The sheet family, and why it stops at A2

**A capture sheet never has to be bigger than the drawer.** Anything that will not lie in a drawer does not get a place in one, so it never gets captured. That is the whole sizing rule, and it is what sets the top of the family.

The drawers are `parts/drawers.py`. `drawers.interior` is canonical: D1's clear interior is **271 wide x 464 deep x 82 high** (the 446 x 223 this paragraph carried until 2026-09-11 was a stale brief figure; the scan's C-03 caught it). The family was sized when the collar added 7mm a side to every tool; without it every window has 14mm more to give.

| size | page mm | window mm | largest tool | tag ids | tag mm | what it is for |
|---|---|---|---|---|---|---|
| LETTER | 216 x 279 | 180 x 180 | 170 x 170 | 0–3 | 30 | the default. Most of the cutter and instrument drawers. |
| TABLOID | 279 x 432 | 243 x 313 | 303 x 233 | 8–11 | 40 | the long-tool sheet: the jog pendant (228), a torque wrench, a long clamp. |

"Largest tool" is the window less the crop's 2mm inset and 3mm of clear paper a side (`trace_sheet.CLEAR_PAPER`), so it is what will actually come back, not what will physically lie on the paper. RT4 (2026-09-04) trimmed A4, A3, ARCH B and A2 from the family; the shop prints on these two. The A2 argument (the window covers the whole drawer interior) is in `trace_sheet.py`'s docstring for when a tool longer than 303 turns up.

Tag size is a documented constant per size, not a formula: 30mm on LETTER, 40mm on TABLOID, big enough to detect with the sheet a third of the screen and small enough to keep out of the window.

Every sheet keeps the same 14mm gutter, the same 1mm window border, the same TAG and HEIGHT boxes, the same 100mm scale bar and the same four rules. The only things that change are the page, the tag size and the quartet.

Generate them with `PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/trace_sheet.py`, or one at a time with `--size TABLOID`. `trace_sheet.pdf` stays the LETTER sheet under its old name so every existing link resolves; the family is `trace_sheet_<size>.pdf`. The file names keep the word "trace" for the same reason.

### Self-identifying sheets

Nobody types the paper size into the Form. Each size carries a **different quartet of ArUco ids** out of DICT_4X4_50 (the table above), `capture_ingest.identify` reads the quartet out of the photo and looks that size's geometry up in `trace_sheet.SIZES`, and the rest of the pipeline follows. Two things fall out:

- a student who prints TABLOID and photographs it gets TABLOID's window and TABLOID's mm, with nothing to get wrong;
- the failure that would otherwise be silent, a sheet read against the wrong page size and every dimension out by the ratio of the two pages, is not reachable. It is a rejection, not a wrong number.

LETTER keeps ids 0–3 and keeps its exact v1 window (180 x 180 at 17.95, 48.0), so sheets photographed before the family existed still ingest to the same numbers. T025 and T026 were re-run against the family code and came back to within 4e-7 mm of their pre-family values.

A size counts as present at two detected markers, not one: a lone stray id out of a 50-marker dictionary is a detector false positive and should not reject an otherwise good capture. Two sizes at two markers each is `two different sheet sizes in frame` and rejects; no size at two markers is `no known sheet size found` and rejects.

### What the ingest does

`capture_ingest.py <image> <tag> <height_mm>` (or `ingest(image_path, tag, height, source="photo")`): finds the ArUco tags, reads the quartet to know which paper this is, rectifies the photo into that size's mm frame (three tags is the floor), crops the window, and then:

- **reads which window it is** off a band just inside the crop (`field_kind`): magenta when at least 60% of the band's pixels have an OpenCV hue in `MAGENTA_HUE` = 150 to 175 (300° to 350°; process magenta prints near 325°, a phone's white balance and a warm light move it 10° either way; CONFIDENCE: estimate, verified on the synthetic sheet at 324°, to be checked on the first colour print) and saturation over 90. Then, on **magenta**, the tool is a **chroma key**: every pixel whose hue is more than 12 units (24°) from the band's median, or whose saturation is under 90, is tool; a shadow is darker magenta at the same hue and stays field; a white tool, a grey tool, a chrome highlight and a pencil line are all "not field". On **white** (every sheet before 2026-09-11 11:00) it falls through to grabCut, unchanged.
- **segments the tool on a white window** with `cv2.grabCut`. One threshold is not enough: metal reflects (highlights as bright as the paper) and casts a soft shadow (darker than the paper). The threshold is only the seed: pixels more than 30% darker than a quadratic model of the paper's brightness fitted to the window's border band, or saturated, opened at twice a pencil line's width so a line already on the sheet cannot seed, eroded 1mm as probable foreground and 6mm as sure foreground; the border band is probable background, the paper outside the window sure background. grabCut refines the edge from colour. Then a 1mm open (pencil lines off, a line hugging the tool detached), a 1mm close (highlight gaps bridged), components that are thin everywhere at 2mm dropped whole (a retraced loop is thick but thin everywhere; a tool with a thin tip keeps its tip), holes filled (highlights), and any component within 3mm of the largest merged back (a piece of tool a highlight band cut off).
- **corrects the perspective, which is to say does not.** The four tags rectify the sheet plane exactly; a tool's edge above it would be inflated away from the camera's nadir by `p' = c + (p - c) · D / (D - h)`, and the correction `p = c + (p' - c) · (D - h_eff) / D` is in the code with `h_eff = 0 x` the measured height: the widest outline of a drawer tool (a clamp bar, a wrench, a block, a bottle on its side) lies ON the paper, so no shrink. The datum is Jared's calipers on the T056 Essential Clamp bar, 70.23 x 19.77: with `h_eff = h/2` the photo path read 68.9 x 20.0 (1.3mm short along L; W within 0.23, the uncorrected read). Foam must err large, never small (CONFIDENCE: measured, that datum). D, the camera height, still comes from the photo's EXIF: `D = f35 · S · image_diag_px / (43.27 · s_px)`, where f35 is FocalLengthIn35mmFilm, S and s_px the widest span between two detected tag corners in sheet mm and in the unwarped photo, and 43.27 the 35mm frame's diagonal (the form that is right for a 4:3 phone frame; on 3:2 it reduces to the long side over 36). No EXIF: D = 650 and the Result's reason says `camera height assumed 650`, which the digest shows. The oversize bound is a warning, not a gate: a round tool's widest edge at mid-height projects outward by up to `L · (h/2) / D` (the nadir at one end of the tool, the worst case), and over `OVERSIZE_MAX` (2.0mm, twice `FOAM_CLEAR`; CONFIDENCE: choice) the capture still goes through, with `if this tool is round its pocket may read up to X mm long; hold the phone higher for round tools` first in its reason and on the preview. A slab's widest edge is on the paper and the bound does not apply to it (as a rejection it would have wanted the pendant shot from 2300mm); a round tool's pocket errs large, which the foam takes. A 50 x 30 tool 16 tall at D 262 captures clean (bound 1.5mm); the 100 x 50 stadium 40 tall at the same D captures with the warning (7.6mm). Only D under 150 rejects (the model breaks); that is the only distance rejection. The first 2026-09-11 photos were shot at 212 to 308mm; with a 24mm-equivalent phone lens a LETTER sheet filling the frame means the phone is 20cm away, which is why the card says a third of the screen and the bigger and rounder the tool, the higher the phone.

Calibration datum 2026-09-11: T056 calipers 70.23 x 19.77, capture 70.3 x 20.5; width reads about 0.7 large from edge blur; tune EDGE_BLUR only after a second calipered tool agrees.
- Douglas-Peucker at 0.3mm, `print_scale` if the sheet did not print at 100%, the pocket as the corrected outline offset by `FOAM_CLEAR` (1.0, settled by the fit test; build123d's arc offset, with a raster offset behind it for the concavity the kernel folds over), the height class as `ceil(height_mm / 10) x 10`, and writes:

- `captures/T0xx.dxf` — the pocket, one closed loop, mm, laid with its long side along X and its box's corner at the origin
- `captures/preview/T0xx.png` — the rectified sheet, the detected silhouette in orange, the pocket in cyan, L / W / H, the height class and the D used in the corner. **Look at this before trusting a capture.**
- the tag's row in `tool_list.csv`: `dims_status=CAPTURED`, `silhouette`, `height_class`, `bbox_l_mm` / `bbox_w_mm` (the tool's L and W), `bbox_h_mm` (the measured height in mm)

It rejects, with one line and nothing written, when: two different sheet sizes are in the frame; no known quartet is in the frame; fewer than three tags of the identified size are found; no component over 100mm² is in the window (`no tool found in the window`); the tool touches the window edge (the message names the size and says to take a bigger sheet); a second component in the window is more than a quarter of the largest's area (`two tools`); the camera was under 150mm; the height is over 50 (`taller than any drawer`: measure it as the tool lies, a bottle on its side is its diameter) or not a number.

On magenta the one thing to watch is chrome: a polished tool reflects the field and can read as magenta along an edge; the merge and close rules cover a narrow band, a wide one loses that edge, and the card says to turn the sheet under the light. Both the white-window limits below still apply to white sheets.

Two things the white-window path cannot see, both visible in the preview: a specular band running the FULL length of an edge with a strip of tool beyond it wider than 3mm cuts that strip off (turn the sheet under the light, shoot again); a hard shadow from one lamp or a flash is read as tool along that side (about 1.5mm on the synthetic stadium; hence no flash, no lamp). Light-coloured tools (bare aluminium) have not been through it on a real photo yet: the seed wants 30% darker than paper or saturated, and a real trial is the check.

`test_capture.py` runs the photo source (a magenta sheet with a white stadium and a light-grey shiny one keyed on chroma, both within 0.5mm; the white sheet through grabCut: a modelled phone at D 600 with EXIF, the tool's edge rendered at h_eff about an off-centre nadir, with and without a pencil ring 3mm outside it, recovered within 0.5mm on both sheet sizes; a PNG without EXIF falling back to 650 and saying so; and six reject paths) and then the whole trace source as before (every size, the LETTER stadium, the 94% print, five reject paths, the tray): `PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/test_capture.py`.

If the sheet did not print at 100% (a printer's own margins forced a smaller scale), pass `--print-scale` — measured scale-bar length / 100, read off the line under the bar on the printed sheet — and the ingest corrects for it; every capture from an uncorrected scaled sheet is wrong by that same ratio.

### The columns

`tool_list.csv` and the Sheet's TRAY tab carry, beyond the catalog columns:

| column | values | who writes it |
|---|---|---|
| `dims_status` | `CATALOG` (datasheet numbers: cutters, collets), `CAPTURED` (photographed, silhouette on disk), `MEASURE` (nothing yet) | CATALOG by hand; CAPTURED by the ingest; MEASURE is the default |
| `height_class` | 10, 20, 30, 40, 50: the measured height rounded up to the next ten | the ingest, from the Form's height |
| `bbox_h_mm` | the measured height, mm | the ingest, from the Form's height |
| `silhouette` | `captures/T0xx.dxf`, relative to this directory | the ingest |
| `strip` | the kind word of the strip it lives on (`FLAT`, `SHEET`, `BALL`, `V`, `COLLETS`; `INSTRUMENTS`, `BOOTS`; `CLAMPS`, `CRUSH-IT`, `HEX`, `FIXTURES`), blank for case, loose and dock rows | by hand, 2026-09-25 |
| `store` | how it is held: `bore`, `collet`, `socket`, `slot`, `recess`, `cup`, `case`, `loose`, `dock` | by hand, 2026-09-25 |
| `hold_mm` | what it is held by when that is not its box: `20x12` for a clamp's body, `5.8x23` for a T-handle's hex across corners and handle thickness | by hand |
| `status` | `active`, `ordered` (bought, not in hand: it gets its place now), or `struck` (merged or does not exist; the row is skipped) | by hand; `status_note` says why |

`bbox_l_mm`, `bbox_w_mm`, `bbox_h_mm` are the ingest's record of L, W and height, and `inserts.py` sizes recesses, sockets and slots from them. `socket_note` stays as a free note. The `tile` and `label` columns went with the foam trays on 2026-09-25.

### The Form and the CAPTURE tab

The Sheet's CAPTURE tab (columns `timestamp, tag, height, photo_url, status, reason`) is the landing tab; `height` is the tool's measured mm as typed (the ingest strips anything that is not a digit, so "20mm" is 20). `~/labnode-scripts/cnc-capture-ingest.py` reads rows whose `status` is blank, downloads the photo from Drive, runs the ingest, writes `status` (`captured` / `rejected` / `error`) and `reason` back (an accepted capture's reason carries L, W, H and the class, plus `camera height assumed 650` when the photo had no EXIF), uploads the preview to `IC / CNC Station 2026 / 05 Capture / preview`, and puts one line in the 07:05 digest.

The Form exists (built through the Forms API on 2026-09-11 from the Brophy Drive token, which authorizes `forms:batchUpdate`; the one thing the API refuses is creating a file-upload question, so that question was added by hand). Form id `1CLmlEu2w75Go0GjtxteJvdp2GKIq3jxkxWVq3KZ8eIU`, in IC / CNC Station 2026. Questions: Tag (dropdown, one entry per capturable row), Height (mm, free text), Photo of the sheet (file upload, images, one file). Respondent email is collected, so a capture is attributed. It has no Google-linked response tab: `cnc-capture-ingest.py` reads the Forms API and copies each new response into the CAPTURE tab itself (columns G email, H response id, the dedup key), then runs the rows as before.

The Sheet's BOARD tab is the student-facing checkoff: one row per capturable tool, a checkbox that ticks itself when CAPTURE's last row for that tag says `captured`, the status, who, and the ingest's one line. Formulas only; nothing writes to it. The Sheet is shared read-only to the brophyprep.org domain for that tab.

### The physical kit (Drawer 1)

- a stack of `trace_sheet.pdf` (LETTER), printed in colour at 100% (the scale bar is the check), and a few TABLOID behind them: `trace_sheet_tabloid.pdf` is the one the pendant needs; one of each laminated matte as the station's mats
- a steel rule, for the height
- `capture_card.pdf`, laminated

The collar and the height gauge are retired (2026-09-11) and can leave the drawer. The sheets and the card are in Drive under IC / CNC Station 2026 / 06 Tool Capture, generated by `trace_sheet.py`, updated in place so every link still resolves.

### v2: the machine captures its own tools

The ingest's image source is a plug: `ingest(..., source="camera")` is reserved for a camera on the Z plate looking down at a tool on a fiducial mat on the bed, one gSender macro to the capture pose, a frame grab on the console. Same ingest, same tags, same segmentation, same output, and a known camera height instead of one read from EXIF. It raises `NotImplementedError` today. Nothing in v1 is built in a way that v2 would have to undo: the sheet frame becomes the mat frame and the tag positions become the mat's.

The Sheet's LOG tab (date, reading, who) is the human half of the station log; the first row is reserved for the commissioning continuity reading. It is not snapshotted here.

### Carbide 3D's print library: reference models only (2026-09-25)

https://carbide3d.com/3d-print/ publishes 32 STLs, most of them Carbide's own clamps, stops and caddies. RULED, Jared 2026-09-25: they are reference, never a print queue and never an object in a drawer ("I don't want any printed objects in the drawer. the 3d models are only provided as reference"). A caddy is not a way to fit a drawer; every tool keeps its own pocket. What the library is for is checking a tool's size against the maker's own model. The one check so far: `essentialsclampstandard.stl` is 70.0 x 20.0 x 18.0 against T056's calipers 70.23 x 19.77 and its capture 70.3 x 20.5 x 18.

The licence allows personal use and printing, and forbids redistributing the file. This repo is public, so no STL is committed; cite the page URL.

Library pages that name a part the station owns, dimensions off the STL's bounding box:

| page | STL box, mm | station row | status |
|---|---|---|---|
| essential-clamp | 70.0 x 20.0 x 18.0 | T056 | agrees with the calipers; the capture stands |
| essential-hard-stop | 32.0 x 30.9 x 14.0 | T045? | the capture reads 31.6 x 29.8 x 16: same footprint, 2 taller. UNVERIFIED which part T045 is |
| crush-it-hard-stop | 25.0 x 25.0 x 15.5 | none | does not match T045's capture |

T071 (the Crush-It Essentials Caddy) was added and struck the same day under this ruling.

## DXF layers the insert export writes (2026-09-25)

`inserts.export()` writes a STEP and a DXF per strip, `export/cnc_shapeoko/inserts/insert_<drawer>_<strip>.{step,dxf}`, plus `insert_coupon_fit` (below). The layers:

- `OUTLINE` — the strip blank, profile through
- `POCKET_D<depth>` — closed loops, pocketed to that depth from the top face with the #102 1/8in flat. Every place is `POCKET_D11`; a collet's stepped bore adds a `POCKET_D5` ring.
- `THROUGH` — the lift hole, and the keystone's window
- `VCARVE` — the kind word as outlines, V-carved with the #302 60-degree bit to 1.9 (Fusion's Engrave): through the 1.27 cap, the groove shows 0.7 of white

Cut the **fit coupon** first, from an offcut of the same sheet: 1/8 bores at 3.3 / 3.4 / 3.5, 1/4 bores at 6.5 / 6.6 / 6.7, one collet step and one clamp socket. Push a real shank, a collet and a clamp into each, then set `BORE_CLEAR` and `SNUG` from what fits before a strip is cut. Run `PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/parts/inserts.py` for the place table of every drawer.

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
- `hdpe_NN.dxf` — 1/2in two-colour HDPE, one blank per insert strip (fourteen, on one 24 x 48 sheet) from `inserts.plan_all`.
- `manifest.csv` — one row per placement: file, part, x, y, size as placed, grain rule, shelf, segment.

Rectangles only, greedy, biggest first, 10mm kerf/margin between rectangles and to every blank edge. The count is a ceiling the shop can only beat. Grain is along the sheet's X; standing seen panels keep theirs vertical, rails and drawer panels along their length, the rest may turn — shop convention, carried as a RULING WANTED line in the gate until Jared confirms or names exceptions in `nest.GRAIN_OVERRIDES`.

The blanks are read off the placed solids in `assembly.components`, never off the export folder (which is gitignored and only as current as its last run). The drawings on a sheet are the parts' own layers, rebuilt through each module's builders and moved with the part, plus:

- `SHEET` — the stock outline
- `RIP` — the track-saw lines (Shapeoko sheets only)
- `PART_<label>` — the placed blank's rectangle, one layer per part, so a part's name is in the layer table exactly once per placement
- `LABEL` — the part's name as glyph outlines inside its rectangle; reference, not a toolpath

The rear door contributes its CUT frame only; its outside-face carve stays in `rear_door_carve.dxf`. The console plate's `ACRYLIC` layer is dropped from the birch sheet because the panes ride the laser nest as their own parts.
