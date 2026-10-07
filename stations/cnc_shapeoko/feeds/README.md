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
