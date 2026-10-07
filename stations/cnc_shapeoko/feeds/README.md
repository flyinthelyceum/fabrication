# Feeds library: Shapeoko 5 Pro, Innovation Commons

One place for every cutting setting the station uses, where each number came from, and what happened when we cut with it.

## The rule

**Conservative is the standard** (Jared, 2026-10-07): "let's always error on the side of running slower more conservative cuts as standard. we aren't a production shop." Students run this machine, so a slow cut that finishes is the goal. Our standard rows sit at the slow end of the range where maker charts and practitioner reports overlap, near Carbide Create's presets. A row only gets faster after it's been TESTED-here, and only when Jared asks for speed.

There is one floor, and it isn't speed. Below about 0.05 mm (0.002 in) per tooth, a cutter rubs instead of cutting, which burns wood and dulls the bit (`sources/limits.json`). So slow cuts lower the depth per pass first, and the feed second.

## Files

- `feeds_library.csv`: one row per (tool, material, operation). Column meanings are in `sources/library_design.md` section 1. `status` is `reference` (a source's numbers, kept for comparison), `candidate` (our pick, not yet cut) or `active` (cut here and logged clean).
- `test_log.csv`: one row per real cut. Every candidate that gets cut writes a row here; its `library_row_id` links back.
- `sources/`: the 2026-10-07 research behind the first rows. `manufacturer.json` covers Amana's 46170-K chart, read verbatim from Amana's PDF. `practitioner.json` covers Shapeoko-class reports with outcomes. `limits.json` covers spindle power, deflection and the minimum chip thickness. `library_design.md` has the schema, the chip-grading rubric, a feed-ladder coupon, and how a row becomes a Fusion tool preset.

## Trust tiers, weakest to strongest

`manufacturer` < `practitioner` < `derived` < `TESTED-here`. Charts assume rigid industrial routers. The Shapeoko's gantry stiffness is unpublished, so a TESTED-here row beats any chart.

## First standard rows (2026-10-07, derived, untested)

| cutter | op | rpm | feed | depth | per tooth |
|---|---|---|---|---|---|
| Amana 46170-K, 1/4 compression 2FL | outline, first pass | 16000 | 1905 mm/min (75 ipm) | 7.5 mm | 0.060 mm |
| same | outline, rest (2 passes) | 16000 | 1905 | 5.4 mm | 0.060 mm |
| same | dado/rabbet pockets | 16000 | 1905 | 3.0 mm | 0.060 mm |
| same | ramp in | | 953 mm/min | 3 deg | |
| Carbide #102, 1/8 square 2FL | hole spot 3 mm deep | 18000 | 914 | 1.0 mm | 0.025 mm |

How these compare with the sources: Amana's chart gives 110 ipm at 18k and a 1xD (6.35 mm) depth. Ours is 68% of that feed and 77% of its per-tooth load. Practitioner reports of clean cuts cluster at 100-150 ipm and 3-6 mm per pass.

A compression bit's first pass must go deeper than its 7 mm upcut section. Otherwise the downcut flutes never reach the top face and the top edge fuzzes. That's why the outline is 7.5 mm, then two passes of 5.4 mm. Compression bits always ramp in, never plunge.

The workbench prototype's fit coupon is the first cut to log against these rows.

## Tooling catalog (2026-10-07)

One row per cutter on hand, what it's for, and which library rows cover it. Material tags: `birch ply 18mm`, `birch ply 12mm`, `MDF`, `hardwood`, `aluminum`.

| cutter (tool_id) | what it's for | library rows |
|---|---|---|
| #101 (1/8in ball, 2FL) | fine 3D finish passes | STD-C3D101-*-FINISH (4 materials) |
| #102 (1/8in flat, 2FL) | pocketing, fine detail | STD-C3D102-*-POCKET (4 materials) plus the existing STD-C3D102-BIRCH18-SPOT |
| #201 (1/4in flat, 3FL upcut) | general profile cuts | STD-C3D201-*-PROFILE (4 materials) |
| #202 (1/4in ball, 2FL) | 3D finish passes | STD-C3D202-*-FINISH (4 materials) |
| #251 (1/4in downcut, 2FL) | clean-top-face profile in sheet goods | STD-C3D251-*-PROFILE (4 materials) |
| #301 (1/2in, 90 deg V) | V-carve, wide letters/chamfers | STD-C3D301-*-VCARVE (4 materials) |
| #302 (1/2in, 60 deg V) | V-carve, fine letters/inlay | STD-C3D302-*-VCARVE (4 materials) |
| McFly surfacer (1/4in shank, 25.4mm cut dia) | spoilboard and stock skim passes | STD-MCFLY-*-SURFACE (4 materials; unsourced, see note below) |
| T072, Amana 46170-K (1/4in compression, 2FL) | two-sided-clean profile/pocket in sheet goods | STD-AM46170K-BIRCH18-PROFILE-FIRST/REST, STD-AM46170K-BIRCH18-POCKET (birch 18mm only; see gap below) |
| T073, Amana 46202-K (1/4in downcut, 2FL) | clean-top-face profile | STD-AM46202K-*-PROFILE (4 materials) |
| T074, Amana 51502-Z (1/4in O-flute, 1FL, aluminum) | aluminum only | STD-AM51502Z-ALUM-PROFILE, flagged do not run without Jared's review |
| T075, Amana 46227 (1/8in downcut, 2FL) | profile in sheet goods and hardwood | STD-AM46227-*-PROFILE (4 materials) |
| T076, Amana 46340 (1/8in downcut, 2FL, solid-wood grind) | profile, best in hardwood | STD-AM46340-*-PROFILE (4 materials; sheet-goods rows are lower-confidence extrapolations, see outcome_notes) |
| T077, Amana 46375 (1/8in ball nose, 2FL upcut) | fine 3D finish passes | STD-AM46375-*-FINISH (4 materials) |

Gaps: no acrylic/HDPE O-flute cutter is on hand yet (A033/A015/A007 in `tool_list_add.csv` are the proposed buys), so there are no plastics rows in the library. The McFly surfacer has no sourced feed chart anywhere found this pass; its row is a conservative placeholder, flagged in `outcome_notes`, not a tested number. The 46170-K's birch ply 12mm variant isn't in the library yet; the 18mm rows above are what's tested-pending.

## How to log a cut

Every time a candidate row actually gets cut, add one row to `test_log.csv`: date, operator, the `library_row_id` it tests, the tool, the actual commanded settings, the chip grade/sound/finish you saw, and the outcome. Once a row has a clean test log entry, update that row's `confidence_tier` to `TESTED-here`, set `test_log_ref` to the test's `test_id`, and change `outcome` from `untested` to what actually happened. A row only earns `TESTED-here` by having a real test_log_ref; don't promote it by hand.
