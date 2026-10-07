# Living Feeds-and-Speeds Reference Library — Design Proposal
Shapeoko 5 Pro, Innovation Commons. Angle: how to build and maintain the library, not the numbers themselves.

## 0. The core method, synthesized from the field

Every serious source converges on the same loop: **start conservative → cut a short test → read the chip/sound/finish → adjust one variable → log it → repeat until the setting earns a TESTED status.** None of the sources (Carbide 3D, Sienci, CNCCookbook/G-Wizard, Popular Woodworking) publish a formal "feed ladder coupon" as a named artifact — that structure (stepped slots on one offcut) is a synthesis of the chipload-test-cut method onto a single test piece, built below in Section 3.

- Carbide 3D's own tuning heuristic: "test cuts on your CNC router should make chips (not dust), not bog down your machine, and produce an edge that is of good quality… if the test cut produces more dust than chips, try decreasing RPM, increasing feed, or fewer flutes; if the cut is rough/aggressive, increase RPM, decrease feed, or more flutes." Goal is the largest clean chip — reduces heat, extends tool life. (Carbide 3D feeds/speeds guidance, summarized via [Popular Woodworking, "Feeds & Speeds for CNC Routers"](https://www.popularwoodworking.com/techniques/feeds-speeds-for-cnc-routers/))
- Carbide 3D's blog is explicit that it does **not** give a step-by-step empirical procedure beyond one diagnostic: after a job, the tool should be lukewarm, touchable — if it's hot, feeds/speeds are wrong. Otherwise they punt to manufacturer catalogs, Carbide 3D's own tested charts, or G-Wizard. ([carbide3d.com/blog/feed-and-speeds-part-1](https://carbide3d.com/blog/feed-and-speeds-part-1/))
- Sienci's resource frames the same test-and-read loop with slightly different fault signatures: "Aim for consistent, clean chip formation — not dust, not chunks." Burning → speed problem. Rubbing/overheating → feed too slow. Bit breakage → feed too fast. Their tables are "a jumping-off point," explicitly expected to be corrected by experience. ([resources.sienci.com/view/cnc-feeds-speeds](https://resources.sienci.com/view/cnc-feeds-speeds/))
- G-Wizard's own description of its method: it is a two-step calculator, not a test protocol — it picks a surface-speed/chipload starting point from tool-and-material data, then adjusts for the actual cutting conditions (deflection limits, rigidity, finish target vs. max material-removal-rate target). It explicitly offers a "most conservative" setting = the slowest feed before rubbing, useful as a calibration anchor. ([cnccookbook.com/g-wizard-cnc-feed-speed-calculator](https://www.cnccookbook.com/g-wizard-cnc-feed-speed-calculator/), [cnc-chip-load-calculator](https://www.cnccookbook.com/cnc-chip-load-calculator/))
- Chipload arithmetic everyone agrees on: `Feed = Chipload x Flutes x RPM`, i.e. chipload = feed / (RPM x flutes). Wood chipload ranges by diameter (reference starting points, not our tested numbers): 1/4" bit 0.003–0.006 ipt, 3/8" 0.005–0.010 ipt, 1/2" 0.007–0.015 ipt, 3/4" 0.010–0.020 ipt. For full-width slotting, both flute edges are loaded, so cut chipload roughly in half vs. a side-milling pass regardless of material. ([CNC-Dad feeds/speeds beginners guide](https://www.cnc-dad.com/blog/feeds-and-speeds-for-beginners/); slotting rule corroborated across router-feeds guides)

**Conclusion for our protocol:** there is no single authoritative "feed ladder" standard to adopt wholesale. We build our own coupon (Section 3) directly from this shared diagnostic vocabulary — chip-vs-dust, sound, heat, finish — because that vocabulary is what every source actually tests against.

## 1. CSV schema: `~/projects/fabrication/stations/cnc_shapeoko/feeds/feeds_library.csv`

One row = one (tool, material, operation) setting. Design goals: Fusion-preset-ready (Section 4 maps columns straight to JSON fields), and every row's trust level is explicit rather than implied.

| Column | Type | Notes |
|---|---|---|
| `row_id` | string | stable id, e.g. `EM-6MM-2FL_BIRCHPLY18_SLOT` |
| `tool_id` | string | matches our tool crib ID / Fusion tool GUID if known |
| `tool_description` | string | e.g. "6mm 2-flute carbide upcut, 22mm LOC" |
| `tool_diameter_mm` | number | |
| `flutes` | integer | |
| `material` | string | e.g. "Birch plywood 18mm" — match Fusion/Carbide material taxonomy where possible |
| `operation` | enum | `slot` \| `profile_side` \| `profile_adaptive` \| `pocket` \| `drill` \| `surface` |
| `stepover_pct` | number | % of diameter, for profile/pocket ops; blank for slot/drill |
| `doc_mm` | number | depth of cut per pass |
| `woc_mm` | number | width of cut per pass (= diameter for full slot) |
| `rpm` | integer | `n` |
| `feed_mm_min` | number | `v_f` |
| `plunge_feed_mm_min` | number | `v_f_plunge` |
| `chipload_mm` | number | derived = feed / (rpm × flutes); store it, don't recompute silently in the sheet elsewhere |
| `coolant` | enum | `air` \| `dust_collection_only` \| `none` |
| `source` | string | citation: URL, manufacturer catalog name+page, or `in-house` |
| `confidence_tier` | enum | `manufacturer` \| `practitioner` \| `derived` \| `TESTED-here` — see tier definitions below |
| `test_log_ref` | string | FK into the test-cut log (Section 2) `test_id`, required when tier = `TESTED-here` |
| `outcome` | enum | `clean` \| `dusty_slow_feed` \| `rough_too_fast` \| `burned` \| `deflected` \| `broke_tool` \| `untested` |
| `outcome_notes` | string | free text: chip size/color, sound, finish, heat |
| `last_verified` | date | |
| `status` | enum | `candidate` \| `active` \| `deprecated` |

**Confidence tiers** (ordered weakest → strongest evidence for *our* machine/material/tool combo):
1. `manufacturer` — vendor catalog or Fusion/Carbide default preset, unverified here.
2. `practitioner` — forum/maker-sourced number (Sienci, CNCCookbook forum, community posts), unverified here.
3. `derived` — computed from chipload formula/G-Wizard-style scaling off a tier-1/2 number for a different tool size, unverified here.
4. `TESTED-here` — ran a coupon or real job on this Shapeoko 5 Pro, logged the outcome, row reflects the cut that actually worked (or the failure that defines a ceiling/floor).

A row only earns `TESTED-here` by having a `test_log_ref`. This keeps the "we calculated it" and "we proved it" numbers from blurring together, which is the whole point of the tiering.

## 2. Test-cut log schema

Separate file (or sheet) so one test session can validate/refute several library rows. `~/projects/fabrication/stations/cnc_shapeoko/feeds/test_cut_log.csv`:

| Column | Notes |
|---|---|
| `test_id` | e.g. `2026-10-07-A3` |
| `date` | |
| `operator` | |
| `coupon_id` | which physical test piece / which slot letter on it (ties to Section 3) |
| `tool_id` | |
| `material` | include sheet batch/supplier if it matters (moisture, glue line count) |
| `rpm`, `feed_mm_min`, `doc_mm`, `woc_mm` | the actual commanded values |
| `chip_grade` | `dust` \| `fine_chips` \| `good_chips` \| `chunks_tearout` — see grading rubric below |
| `sound` | free text, but anchor to: `quiet_cutting` \| `chatter` \| `screaming_rpm` \| `bogging_labored` |
| `finish` | `clean` \| `fuzzy` \| `burn_marks` \| `tearout` \| `melted_edge` |
| `heat_check` | touch test post-cut: `cool` \| `warm` \| `hot_cant_touch` (Carbide 3D's lukewarm-is-correct heuristic) |
| `tool_wear_observed` | `none` \| `dulling` \| `chipped_flute` \| `broken` — free text detail |
| `tool_runtime_min_cumulative` | running total minutes on this specific physical tool, for wear-vs-life correlation |
| `verdict` | `increase_feed` \| `decrease_feed` \| `increase_rpm` \| `decrease_rpm` \| `keep_as_candidate` \| `promote_to_tested` \| `reject` |
| `photo_ref` | path/filename of a chip/finish close-up — cheap, and settles disputes about what "good chips" looked like |
| `notes` | |

**Chip grading rubric** (synthesized from Carbide 3D + Sienci language, since neither gives a strict 4-point scale — this is the derived scale to apply consistently):
- `dust` — fine powder, little to no particle structure. Feed too slow / rpm too high / too many flutes for the chipload. Reject or increase feed.
- `fine_chips` — small but discrete chips, slightly powdery mixed in. Borderline; usually acceptable for finish passes, not ideal for roughing.
- `good_chips` — comma-shaped or curled chips with visible thickness, consistent size. Target state across all sources.
- `chunks_tearout` — oversized fractured chips, splintering, visible tearout on the wall. Feed too fast / doc too deep / rpm too low. Reduce feed or doc.

**Tool wear logging**: the practitioner sources (DATRON, W.C. Chapman & Sons, CNCArena forum) converge on tracking *cumulative cutting time or parts-count per physical tool*, with periodic visual/loupe inspection of flank wear, and tying wear observations back to the job parameters that produced them — not just tracking tool identity in isolation. Our `tool_runtime_min_cumulative` + `tool_wear_observed` columns are the minimum viable version of that; if a tool shows wear at a logged runtime, that runtime becomes a de facto tool-life ceiling for future rows using that tool_id.

## 3. Feed-ladder test coupon: 18mm birch plywood, fits 300×150mm offcut

Design: a single rectangular offcut, grain direction marked, with a row of short slots cut at stepped parameters. Keep each slot short (full engagement reached fast, short runtime, minimal material) — this is a synthesis of the chipload-test-cut idea, not a published template.

**Layout** — 300mm (X) × 150mm (Y), 18mm birch ply:
- 20mm margin all around.
- One row of 6 slots along X, each slot 30mm long × (tool diameter) wide, spaced 20mm apart (center-to-center ~50mm), running in the Y-minor direction so each slot is a straight full-width plunge-and-cut, not a contour.
- Slot depth: either hold depth constant and step the feed rate (preferred first pass — isolates one variable), or hold feed constant and step DOC per slot in a second row if the first axis is inconclusive. Don't vary both in the same slot.
- Label each slot's parameters directly on the wood next to it with pencil/marker before cutting, or engrave a tiny V-carve number — paper/post-it labels get blown off by dust collection.

**Example single-axis ladder (feed rate), for a 6mm 2-flute bit, 18mm material, single full-depth slotting pass at DOC = 6mm:**

| Slot | Feed (mm/min) | RPM | Chipload (mm) |
|---|---|---|---|
| 1 | 800 | 18000 | 0.022 |
| 2 | 1200 | 18000 | 0.033 |
| 3 | 1600 | 18000 | 0.044 |
| 4 | 2000 | 18000 | 0.056 |
| 5 | 2400 | 18000 | 0.067 |
| 6 | 2800 | 18000 | 0.078 |

(Numbers are a scaffold to adapt to the actual tool/spindle on hand — not a tested recommendation; populate with manufacturer or G-Wizard starting values before cutting, per the chipload formula `feed = chipload x flutes x rpm`.)

**For each slot, observe and record (feeds directly into the test-cut log):**
1. Chip grade (dust / fine_chips / good_chips / chunks_tearout) — collect a pinch of chips from each slot in a labeled bag or photograph immediately, dust collection mixes samples fast.
2. Sound through the cut — steady tone vs. chatter vs. bogging.
3. Wall finish — run a fingernail/thumb across the slot wall; note fuzz, burn streaks, melted-looking glue line, or clean crisp edge.
4. Heat — touch the bit immediately after (careful) per Carbide 3D's lukewarm heuristic.
5. Any deflection — check slot width with calipers against commanded tool diameter; oversized slot = deflection or runout.
6. Visible edge of the cut slot wall under raking light for tearout, especially on the exit/climb side if using conventional milling.

**Verdict rule of thumb** (from the synthesized sources): the slot that produces consistent `good_chips`, a steady cutting sound, no burning, a cool-to-warm tool, and a clean wall — at the *highest* feed that still does all of that — is the one to promote to `TESTED-here` in the library. Slots on either side define the dust/rubbing floor and the tearout/chatter ceiling, both worth logging even though neither gets promoted.

Two ladders (depth-of-cut and stepover) can be run on the same 300×150 blank by adding a second and third row of slots below the first, each row holding feed constant and stepping its own variable — the blank has room for roughly 3 rows of 6 slots at the spacing above.

## 4. From a library row to a Fusion tool preset

Fusion's tool library is JSON (`.json`, or a zipped bundle as `.tools` — renaming to `.zip` exposes the underlying JSON). Per Autodesk's own Fusion CAM API documentation:

- Tool library structure overview: [Types of tool libraries](https://help.autodesk.com/cloudhelp/ENU/Fusion-CAM/files/MFG-TOOL-LIB-TYPES.htm), [Tool Library overview](https://help.autodesk.com/cloudhelp/ENU/Fusion-CAM/files/MFG-TOOL-LIBRARY-OVERVIEW.htm), [Import and export tools and tool libraries](https://help.autodesk.com/cloudhelp/ENU/Fusion-CAM/files/MFG-REF-LIBRARY-EXP-IMP.htm).
- The programmatic entry point is `Tool.createFromJson()` in the Fusion CAM API — i.e. Autodesk's own API treats "build a tool from a JSON blob" as a first-class, documented operation ([CAM API: CAMLibraries_UM.htm](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CAMLibraries_UM.htm), `Tool_createFromJson.htm` reference — the direct page 404'd on this pass but is indexed under the Fusion-360-API CAM Libraries section; re-fetch by searching Fusion's API docs for `createFromJson` if the exact page is needed again).

**Per-material presets live under each tool's `start-values` (older schema) or `presets` array (newer schema).** Field names documented/corroborated across Autodesk's API reference and tool-vendor libraries built against it (RobbJack's Fusion 360 library, 12,310 presets, built on "tools.json version 36" — [robbjack.com/downloads/fusion-360](https://robbjack.com/downloads/fusion-360)):

| JSON field | Meaning | Maps from our CSV column |
|---|---|---|
| `guid` | stable unique ID for the preset | `row_id` (generate a GUID keyed to it) |
| `name` / `description` | human label, typically "<Material> — <tested/recommended> — SFM/chipload summary" | `material` + `operation` + `confidence_tier` |
| `n` | spindle speed, RPM | `rpm` |
| `v_c` | cutting (surface) speed | derived from `tool_diameter_mm` + `rpm` if needed |
| `f_z` | feed per tooth (chipload) | `chipload_mm` |
| `f_n` | feed per revolution (older/alternate field alongside `f_z`) | derivable from `chipload_mm` × `flutes` |
| `v_f` | cutting feedrate | `feed_mm_min` |
| `v_f_plunge` | plunge feedrate | `plunge_feed_mm_min` |
| `v_f_ramp` | ramp feedrate | not currently in our schema — add if we start using ramp entry regularly |
| `v_f_leadIn` / `v_f_leadOut` | lead-in/out feedrates | not currently in our schema |
| `n_ramp` | ramp spindle speed override | not currently in our schema |
| `use-stepdown` / `use-stepover` | whether this preset also carries stepdown/stepover recommendations | `doc_mm` / `stepover_pct` when present |
| `tool-coolant` | coolant flag | `coolant` |

**Practical path to "feed the library into Fusion directly":** write a small script that reads `feeds_library.csv`, filters to rows with `status = active` (optionally restrict to `confidence_tier = TESTED-here` for a conservative library), and for each `tool_id` emits/updates a `presets` entry in that tool's JSON block with `guid`, `name` (include the confidence tier in the name string so it's visible inside Fusion's UI — e.g. "Birch Ply 18mm — TESTED 2026-10 — slot"), `n`, `f_z`, `v_f`, `v_f_plunge`. That keeps the CSV as the single source of truth and the Fusion `.json` tool library as a generated artifact, consistent with how Jared's other canon-routing rule treats generated outputs (regenerate from source, don't hand-edit the derived file).

## Sources
- [Popular Woodworking — Feeds & Speeds for CNC Routers](https://www.popularwoodworking.com/techniques/feeds-speeds-for-cnc-routers/)
- [Carbide 3D — Feed and Speeds Part 1](https://carbide3d.com/blog/feed-and-speeds-part-1/)
- [Sienci Resources — CNC Feeds & Speeds Fundamentals](https://resources.sienci.com/view/cnc-feeds-speeds/)
- [CNCCookbook — G-Wizard Feed & Speed Calculator Guide](https://www.cnccookbook.com/g-wizard-cnc-feed-speed-calculator/)
- [CNCCookbook — CNC Chip Load Calculator](https://www.cnccookbook.com/cnc-chip-load-calculator/)
- [CNC-Dad — CNC Feeds and Speeds for Beginners](https://www.cnc-dad.com/blog/feeds-and-speeds-for-beginners/)
- [Carbide 3D Community — Looking for tool database documentation](https://community.carbide3d.com/t/looking-for-tool-database-documentation/21555)
- [RobbJack — Fusion 360 Tool Library Download, tested presets](https://robbjack.com/downloads/fusion-360)
- [Autodesk Forums — Is there a published JSON or CSV Fusion 360 tool library format?](https://forums.autodesk.com/t5/fusion-manufacture-forum/is-there-a-published-json-or-csv-fusion-360-tool-library-format/td-p/12397105) (fetch blocked 403 this pass; cited for the question thread, field names corroborated via RobbJack + Autodesk API docs instead)
- [Autodesk — Types of tool libraries](https://help.autodesk.com/cloudhelp/ENU/Fusion-CAM/files/MFG-TOOL-LIB-TYPES.htm)
- [Autodesk — Tool Library overview](https://help.autodesk.com/cloudhelp/ENU/Fusion-CAM/files/MFG-TOOL-LIBRARY-OVERVIEW.htm)
- [Autodesk — Import and export tools and tool libraries](https://help.autodesk.com/cloudhelp/ENU/Fusion-CAM/files/MFG-REF-LIBRARY-EXP-IMP.htm)
- [Autodesk Fusion CAM API — CAM Libraries](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CAMLibraries_UM.htm)
- [DATRON USA — Tool Life Monitoring](https://www.datron.com/resources/blog/tool-life-monitoring/)
- [W.C. Chapman & Sons — How to Diagnose Costly End Mill Wear Before It Scraps Parts](https://wcchapman.com/how-to-diagnose-end-mill-wear/)
- [CNCArena Forum — tool life spread sheet for operator](https://en.cncarena.com/forum/thread/136303-tool-life-spread-sheet-for-operator/)

## Known gaps / not verified this pass
- Could not independently confirm the Autodesk `Tool_createFromJson.htm` page content directly (404 on fetch); field list is corroborated through the RobbJack vendor library (built against Autodesk's schema) and search-result excerpts of Autodesk's own docs, not a direct primary-source read of that exact page.
- No source gave a named, published "feed ladder test coupon" artifact — Section 3's coupon design is this researcher's synthesis of the universally-agreed diagnostic variables (chip grade, sound, finish, heat) onto a single physical test piece, not a transcription of an existing standard. Flag before treating it as industry-standard rather than in-house.
