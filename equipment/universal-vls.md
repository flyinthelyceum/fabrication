# Universal VLS3.60 and VLS6.60 lasers

The Innovation Commons has two VLS3.60 (the Yellow lasers) and one VLS6.60 (the Blue laser). Each has its own print-station PC with CorelDRAW and the Universal driver. Laser wattage and the installed lens have not been read off the machines yet.

Researched 2026-11-23 from the maker's documents, for a job that scores fine ruler lines and then cuts 1/8 in acrylic. Every claim cites its document and page.

## Documents read


- **G2008** = "VersaLASER VLS3.60, VLS4.60 and VLS6.60 User Guide", copyright 2008, ULS. This is the exact-model guide. Copy read: a mirror at fau.utcluj.ro (file vls460_manual.pdf, 119 PDF pages). The PDF is an excerpt: its printed page numbers skip (for example PDF p.25 is printed p.36, PDF p.26 is printed p.39). I cite the printed page number from the page footer, with the PDF page in brackets. Its driver text describes Windows XP/Vista era software.
- **G2026** = "VLS Platform Laser Systems User Guide", Version 2026.02.0103, ulsinc.com/assets/pdf/VLS_Platform_User_Guide_2026.02.0103.pdf (102 pages, printed page = PDF page). Title page: "VLS3.75, VLS4.75, VLS6.75 (also for discontinued models VLS3.60, VLS4.60, VLS6.60)". This is the current maker guide for the driver and UCP. Where G2008 and G2026 differ, I say so.
- **MSG** = "Section 5 Material Settings Guide" (acrylic on pages 5-4 and 5-5), service.ulsinc.com, folder "Platform_M_V_X" (file MVX_Material Settings Guide.pdf, 26 pages). It is the maker's, but it is filed under a Platform M/V/X heading and does not say it is written for the VLS3.60 or VLS6.60. Treat it as a starting-point table for maker-labelled laser wattages 25 to 60 W.
- Also downloaded but used only for a work-area cross-check: VLS Desktop User Guide (ulsinc.com/assets/pdf/vls_desktop_user_guide.pdf), the 2020 VLS Platform guide, and the 2012 VLS Desktop manual.

The three machines may be floor-standing Platform units or desktop units. The G2008 spec table lists the VLS3.60/4.60/6.60 as "Floor Standing". Which the Innovation Commons owns has not been checked.

---

## A. Raster versus vector; hairline width; RGB values for the 8 pens

**How the driver decides.** The driver decides by the width of each line or curve. Only lines and curves of 0.001 in (0.0254 mm) or less are vector objects. Every other element is raster. (G2026 p.37). The driver "distinguishes between raster objects and vector objects by the types of elements contained in the graphic". All graphics other than outlines of very thin line widths are interpreted as raster. (G2026 p.67).

**The exact maximum width.**
- Current guide: 0.001 in (0.0254 mm) or less. (G2026 p.37, p.43, p.45, p.67).
- 2008 guide gives three numbers that do not match each other: the glossary says a hairline is "less than 0.003 inches or 0.076 mm" (G2008 p.20 [PDF 14]); the setup text says to set line thickness to "0.001 inches (0.025 mm) or the smallest possible line thickness available" (G2008 p.73 [PDF 55]); and it says "usually, any line thickness 0.008 inches (0.2 mm) or greater will engrave", with the exact cross-over depending on the software and found only by experiment (G2008 p.73 [PDF 55]).
- Working rule that fits both guides: set the Corel outline to Hairline, which is at or below 0.001 in. The 0.003 in figure is only the 2008 glossary and should not be used as a target.

**Thicker lines and filled shapes.** Anything thicker than the limit is raster. (G2026 p.37, p.43). In the 2008 guide, colour fills and bitmaps cause engraving, and an outline that is too thick is interpreted as a filled object and engraved instead of vector cut. (G2008 p.73 [PDF 55]). A white fill does not hide a vector outline; the outline still cuts. (G2026 p.67; G2008 p.73).

**Overlap rules.** Overlapping raster fills are filtered so each spot is engraved once. Overlapping vector outlines are not filtered: two outlines on top of each other are both cut. (G2026 p.67-68; G2008 p.73). So duplicate lines in Corel will fire twice.

**The eight pens and exact RGB values.** (G2026 p.67; identical table in G2008 p.72 [PDF 54]).

| Pen | R | G | B |
|---|---|---|---|
| Black | 0 | 0 | 0 |
| Red | 255 | 0 | 0 |
| Green | 0 | 255 | 0 |
| Yellow | 255 | 255 | 0 |
| Blue | 0 | 0 | 255 |
| Magenta | 255 | 0 | 255 |
| Cyan | 0 | 255 | 255 |
| Orange | 255 | 102 | 0 |

Colours that are not exact matches are mapped to the nearest driver colour and halftoned. (G2008 p.73 [PDF 55]; G2026 p.43 "matched to the nearest color"). G2008 says the driver colours "MUST exactly match" (p.72).

**Materials Database tab uses only three colours.** Black = raster, red = vector cut, blue = vector mark. Vector objects of any other colour are converted to grayscale and printed as raster. (G2026 p.38, p.67). The manual tab has an eight-colour table. (G2026 p.43).

**Inconsistency in G2026:** the sentence on p.67 lists the manual tab colours as "BLACK, BLUE, RED, GREEN, CYAN, MAGENTA and ORANGE" (no yellow), but its own RGB table lists eight including yellow, and p.43 says eight.

---

## B. Run order; can pen order change; vector optimizer

**Raster before vector.** Always. In G2008: all engraving first, then vector cutting. (G2008 p.73 [PDF 55]). In G2026 manual tab: color table is processed top to bottom, "with all raster objects being completed first, then vector objects follow." (G2026 p.43).

**Vector pen order, Materials Database tab.** Raster first, then vector marking (blue), then vector cutting (red). (G2026 p.38). That is the order a score-then-cut job needs (blue score, then red cut) and needs no change if you use this tab.

**Vector pen order, Manual Control tab.** Vectors are grouped by pen colour and run in the colour order listed in the colour table. (G2026 p.55; G2008 p.59 [PDF 41]).

**Can the user change pen order?** Yes in the current guide. "You can change the order of the colors in the color table by dragging the color up or down the list in the table. This will change the order of execution of objects in those colors. You can only change color order when first printing a job. After printing the job to the UCP the color order becomes fixed for that job." (G2026 p.44). So reorder in the driver dialog at print time; it cannot be fixed afterwards in the UCP Settings view. G2008 does not mention reordering colours (not found).

**Default table order is not stated in text.** G2008 lists the colours in the order "black, red, green, yellow, blue, magenta, cyan and orange" (p.72 [PDF 54]). INFERENCE, not a maker statement: if the table opens in that order, red is above blue, so a blue-before-red job in the manual tab needs blue dragged above red. Check on the machine's driver before the job.

**Vector Optimizer ("Sort"/"Enhance").** Location: Manual Control tab, Vector sub-tab. (G2026 p.55; G2008 p.59 [PDF 41]). Four choices: None, Enhance Only, Sort Only, Enhance and Sort. Pen colour grouping and colour order always hold, whichever you pick; the optimizer works inside one colour. (G2026 p.55; G2008 p.59).
- None: original order from the graphics program, "usually a random order". (G2026 p.55).
- Enhance Only: joins connected vectors into a continuous path. (G2026 p.55). G2008 words this as removing start/stop points inside curves so they run smoother with less jitter, no effect on straight horizontal or vertical lines. (G2008 p.59).
- Sort Only: open paths first, each starting from the end nearest the focus carriage ("nearest neighbor"); then closed paths in nested order, innermost first, outermost last. (G2026 p.55; G2008 p.59, which adds this is "useful in an elevated cutting application to prevent the outer piece from falling first").
- Enhance and Sort: both.
- Effect: with Sort on, open-path ruler tick lines in one pen run before closed shapes of that same pen. Inside-out ordering applies within a colour only.

**Vector Scaling** (same sub-tab) calibrates vector size; it does not scale raster. Method: draw a known square, measure, enter desired/measured as X and Y factors. (G2026 p.55-56; G2008 p.59 uses a 5 in square example). Relevant to gauge accuracy.

---

## C. Materials Database tab versus Manual Control tab

**Materials Database tab ("beginner").** Calculates power and speed from the selected material and the maximum output power of the installed laser. (G2026 p.37). Settings inside it: Intensity Adjustments of +/-50% for raster, vector mark and vector cut (G2026 p.39; G2008 p.39 [PDF 26]); Print Special Effects (Normal, 3D, Rubber Stamp, Reduction) (G2026 p.39-40); Material Thickness, which "must" be entered and is used to compute vector-cut settings and to set Z in auto-Z mode (G2026 p.40; G2008 p.41 [PDF 28]); Merge Pages, Print Direction, Vector Performance, Units, Fixture Type (G2026 p.40-41); "Define Job" saves fixture type, thickness, print direction, vector sliders and intensity as a sub-record (G2026 p.39).
- Standard materials are read-only; Clone or New Material creates an editable record. The cut record needs at least two thicknesses; the database interpolates. (G2026 p.41-42; G2008 p.40 [PDF 27], which uses "a 1/8 inch piece of acrylic and a 1/2 inch" as its example of two thicknesses).
- Selecting a material and then switching to the Manual tab transfers its power and speed to black (raster), red (vector cut) and blue (vector mark). (G2026 p.44).

**Manual Control tab ("advanced").** Settings are applied per colour; each colour can hold raster and vector data. (G2026 p.43). Controls, per colour (G2026 p.44-45; G2008 p.48-49 [PDF 30-31]):
- % Power 0 to 100. % Speed 0 to 100, the maximum travel speed; "100% raster speed is different than 100% vector speed"; vector speeds are one-third to one-half of maximum raster speed. PPI 1 to 1000 (pulses per inch, vector only). Under 150 PPI risks a perforated effect; 300 to 500 is called a good nominal value; higher PPI risks melting or charring on edges, lower PPI a serrated edge. (G2026 p.45).
- Z-Axis field: sets the table height before that colour's objects run; works only with Auto Z on in the UCP; "can be used as a method of focusing by entering the thickness of the material". (G2026 p.45).
- SET button must be pressed to register colour-table edits; changes are not kept until OK or Apply. (G2026 p.45).

**Mode per pen.** (G2026 p.45; G2008 p.49 [PDF 31]).
- Rast/Vect (default): elements of that colour are raster or vector depending on line width.
- Rast: forces everything in that colour to raster, including thin lines.
- Vect: prints only vector objects of that colour; raster elements are ignored. (G2008: skips all fills and all outlines thicker than a hairline.)
- Skip: everything in that colour is ignored.

**Save and load settings.** Save writes a snapshot to a ".LAS" file; Load replaces on-screen settings from a .LAS file. Press SET before saving so the colour table is registered. (G2026 p.43 and p.45-46; G2008 p.50 [PDF 32]). The Materials tab has the same Load/Save pair. (G2026 p.43). Apply saves driver changes; Default resets to factory values. (G2026 p.42, p.45).

**Z-axis / thickness field.** Materials tab: Material Thickness field. Manual tab: enter thickness in the Z-axis field for every colour used. Requires Auto Z enabled in the UCP System tab and correct lens size selected. (G2026 p.40, p.45, p.61, p.65).

---

## D. Kerf, spot size, vector line spacing, acrylic

**Kerf.** No kerf width figure appears in any maker document I read. Not found.

**Spot size.**
- Standard 2.0 inch lens: no numeric spot size stated in G2008, G2026 or MSG. The 2.0 is called the "standard" lens (G2008 p.103 [PDF 67]; G2026 p.78). Not found as a number.
- 1.5 inch lens: spot size 0.003 in (0.076 mm), effective focal range +/-0.075 in (1.91 mm); "can engrave very fine detail but can only be used on very flat materials". (G2026 p.79; G2008 p.103 [PDF 67]).
- 4.0 inch lens: spot size 0.013 in (0.330 mm), focal range +/-0.2 in (5.08 mm). (same pages).
- HPDFO: effective spot "as small as 1/4th the size of a standard 2.0 focusing lens", depending on material; enables thinner marked and cut lines at the same power. (G2026 p.78; G2008 p.103).
- Lens kits: G2026 lists 2.0, 1.5, 4.0 and HPDFO (p.79); G2008 lists the standard 2.0 plus optional 1.5, 2.5, 4.0 and HPDFO (p.103). The lens must also be selected in the UCP System tab and calibrated if changed. (G2026 p.61; G2008 p.29 [PDF 23]).
- The installed lens and laser wattage in these machines are unknown to me.

**What limits fine vector spacing.** The maker does not give a minimum line spacing for vectors. What the documents do say: (1) spot size by lens, above; (2) Image Density affects vector quality and speed for curves and small segments, higher density gives finer vector detail but slower processing (G2026 p.50; G2008 p.55 [PDF 37]); (3) Vector Performance Quality improves "curve and small line segment quality" at the cost of time (G2026 p.56); (4) the motion system rarely reaches the set speed on curves and small segments (G2026 p.56); (5) focus is very sensitive, and the shorter lens has the smaller focal range (G2026 p.65, p.79). The only maker example with 0.010 in spacing is a raster tuning test pattern of about 20 thin vertical lines "0.010 in apart" at 0.001 in line thickness (G2026 p.51, p.54), which is not a statement of minimum resolvable spacing.

**Marking or scoring acrylic with low-power vector lines.** The maker's acrylic table (MSG p.5-4) lists a "VECTOR ENGRAVING" row, quoted exactly:

| Laser wattage | Power | Speed | PPI | Pass | Depth |
|---|---|---|---|---|---|
| 25 | 6 | 4.0 | 1000 | 1 | .005" |
| 30 | 5 | 4.0 | 1000 | 1 | .005" |
| 35 | 4 | 4.0 | 1000 | 1 | .005" |
| 40 | 3 | 4.0 | 1000 | 1 | .005" |
| 45 | 3 | 4.0 | 1000 | 1 | .005" |
| 50 | 3 | 4.0 | 1000 | 1 | .005" |
| 55 | 2 | 4.0 | 1000 | 1 | .005" |
| 60 | 2 | 4.0 | 1000 | 1 | .005" |

(MSG p.5-4; headed "ACRYLIC - CAST AND EXTRUDED"; not stated whether that depth is an unmasked or masked result.) The same page gives "VECTOR CUTTING": 25 W = power 100, speed 0.1; 30 W = 100, 0.4; 35 W = 100, 0.6; 40 W = 100, 0.9; 45 W = 100, 1.2; 50 W = 100, 1.5; 55 W = 100, 1.7; 60 W = 100, 2.0; all at PPI 1000, 1 pass, depth .25". Light raster: 25 W = 53/100/500 through 60 W = 22/100/500, depth .002". Deep raster: 25 W = 100/60/500 through 60 W = 100/90/500, depth .010". I give no value for these machines because wattage is unknown; do not interpolate a number here without knowing it. The guide says to treat these as "a guideline or starting point" and says power doubling roughly doubles depth and halving speed roughly doubles depth (MSG p.5-2).

Vector cut at power 100 is the table's cut recipe, so 1/8 in thickness is within the .25 in depth listed. No thickness-specific 1/8 in row exists.

**Cast versus extruded (MSG p.5-5, quoted in substance).**
- Cast turns white or frosted when engraved; extruded stays clear. Use extruded for paint-filled engraving and cast for regular engraving.
- "Cast engraves better without masking." Light engraving without masking is called "the better all around alternative"; deep engraving needs transfer-tape masking against smoke damage, but deep engraving also leaves a white crusty deposit at the edges that cannot be removed without damage.
- For cutting only, extruded "works better and is less expensive"; extruded cut edges look more polished and clearer than cast.
- The maker's order for engraving plus cutting on one piece: "first engrave lightly and unmasked. Then mask with transfer tape, dampen, elevate, re-focus, and cut as a second step."
- Black cast acrylic is not discussed separately in anything I read.

---

## E. Image Density, Print Direction, Image Enhancement/Tuning, Vector Performance

**Image Density.** Location: Raster sub-tab of the Manual Control tab (G2026 p.49). It sets the lines of pixels per vertical inch for raster: seven choices from 83 LPI (density 1) to 2000 LPI (density 7). (G2026 p.49). It also affects vector quality and speed on curves and many small segments: higher density gives finer vector detail but slower. (G2026 p.50; G2008 p.55). Image densities 5 and below fix pulses at 500 PPI, densities 6 and 7 at 1000 PPI for rasters. (G2026 p.44-45). G2008 says six density choices (p.54 [PDF 36]); a high-density SolidWorks note says black sketch entities are not printed as vectors at densities 6 and 7 (G2026 p.69, SolidWorks only). Image Density cannot be changed after printing to the UCP. (G2026 p.58-59).

**Print Direction.** Location: Raster sub-tab (Manual tab) and the Materials tab. Down (default) starts at the top of the field; Up starts at the bottom, used because smoke can mar already-engraved areas. Raster only. (G2026 p.40, p.50; G2008 p.55 [PDF 37]).

**Image Enhancements and Tuning.** Location: Raster sub-tab, "Image Enhancements" section. (G2026 p.51-54). These apply to raster engraving only and are not available in 3D or rubber stamp modes (G2026 p.52). Tuning shifts alternate left-to-right and right-to-left raster strokes so they line up; typical value -8 to 0 (G2026 p.51). Enhancement modes: Disabled, Manual (Contrast, Definition, Density), Automatic with margins, Automatic without margins. (G2026 p.52). Texturize adds random power variation and is for engraving large acrylic areas (G2026 p.51). The UCP System tab also holds a Tuning value that is additive (G2026 p.61). None of this changes vector scoring.

**Vector Performance.** Location: Materials tab (G2026 p.40) and Manual tab, Vector sub-tab (G2026 p.56). Standard, Quality or Throughput. Quality takes longer and improves curve and small-segment quality; Throughput shortens time at some cost to quality. For long straight vectors (over 1 in) change speed instead. (G2026 p.40, p.56). Not changeable after printing for some settings. (G2026 p.58-59).

---

## F. Focusing; masking

**Four focus methods.** (G2026 p.64-66).
1. Focus tool supplied with the lens kit, placed on the material top with the notch against the carriage; "results are very sensitive to focus" (p.64-65). Use the tool that came with the installed lens.
2. Measure thickness with a caliper, move Z manually until the Z position equals that thickness (p.65). Needs correct lens size selected and Z homed and calibrated.
3. Enter thickness in the driver (Materials tab thickness field, or the Z field for every colour in the manual tab); with Auto Z on, the table moves when START is pressed (p.65, p.61).
4. Auto-focus on systems with it: a light-beam sensor crosses the field at about 3 in on Y with a notch in the Y ruler between 2 in and 4 in; part of the material must block it (p.65-66).

Verification: with Z at zero, the focus tool should show the table surface at the focus plane; re-home Z or recalibrate the lens in the UCP System tab if not. (p.65-66). Focus is on the top surface of the material. (G2026 p.64; flow-through table: Z should read 0 in +/-0.020 in, p.78). G2008 mirrors this: AUTO Z uses material thickness from the driver; if disabled use the Focus Tool (G2008 p.29 [PDF 23]). The 2008 guide also has a Z-Axis driver field for "Material Thickness focusing" (p.49 [PDF 31]).

**Masking.** Neither user guide discusses masking for engraving or scoring. The Material Settings Guide (MSG p.5-5) says: cast engraves better without masking; for cutting it "might be necessary to remove both sides of the original masking and re-mask with transfer tape if cutting through the original masking produces flaming" because the original masking is wax coated and will not absorb water; for thick acrylic, dampen the tape and elevate at least 1/2 in then re-focus; "engrave lightly and unmasked" first, then mask and cut. For paint filling the maker says to engrave through masking. Nothing in the maker documents says what masking does to fine score lines.

---

## G. Work area, origin, rulers

**Work area (G2008 p.10 [PDF 8]).** VLS3.60: 24 x 12 in (609.6 x 304.8 mm). VLS6.60: 32 x 18 in (812.8 x 457.2 mm). (VLS4.60 is 24 x 18 in.) Table: 29 x 17 in (VLS3.60) and 37 x 23 in (VLS6.60). Footnote on the same page: "Work area various by speeds and thruput." G2026 p.6 gives the same work areas for the .75 models (24 x 12, 24 x 18, 32 x 18 in); the Desktop guide (p.6) lists 24 x 12 in for the VLS3.60DT.

**Origin.** Software origin is the upper left corner of the engraving area; set the page to landscape and the page size equal to the engraving area, so the page's upper left corner is the laser's zero-zero. (G2008 p.72 [PDF 54]; G2026 p.66-67). The machine homes to the upper right corner (G2008 p.19 [PDF 13]; G2026 p.58, p.63). Pressing Pause also moves the carriage to the upper right home. (G2026 p.63).

**Physical rulers.** Rulers on the table edge match rulers in the UCP preview; "push the material up against the rulers and position your graphics accordingly". (G2026 p.64). Three alignment methods: rulers, the UCP Relocate view (nine anchor points, X-Y entry, or TO POINTER using the red pointer), or fixturing. (G2026 p.59, p.64; G2008 p.27 [PDF 21]). The Duplicate view arranges grids of a job. (G2026 p.59).

---

## H. CorelDRAW and file import

**Page and rulers (G2026 p.66-67; G2008 p.72 [PDF 54], p.68 [PDF 50]).** Landscape; page size matches the engraving area (VLS3.60 24 x 12 in, VLS6.60 32 x 18 in); the printer driver's Engraving Field width and height must match the page size exactly (G2008 p.60 [PDF 42]; G2026 p.56). Mismatch "may cause no graphics, partial graphics, erroneous graphics or a misaligned graphics output". Set the Corel vertical ruler origin to the page height (example in G2008: "12 inches (305 mm) for a VLS3.60"), (G2008 p.68 [PDF 50]).

**Colour management.** G2026 p.69: "CorelDRAW products have a color matching feature that interferes with the proper mapping of colors... Make sure to turn color matching feature off." G2008 p.69 [PDF 51] for X3/X4: Tools, Color Management, "Color Management Off"; in Options > Global > Printing > Driver Compatibility, make sure the laser system is the printer and all check boxes are unchecked.

**Palette.** G2008 p.68 [PDF 50]: ULS supplied custom Corel palettes on the install CD ("MD COLOR PALETTE.CPL" for VLS2.30, 3.50, 3.60, 4.60, 6.60; "ADVANCED COLOR PALETTE.CPL" for PLS/ILS) to copy into Corel's Palettes folder and open via Window > Color Palettes > Open Palette. Use RGB values per section A if the palette is missing. (G2026 p.67).

**Outlines.** Set the outline colour red (or the intended pen) and width "Hairline". (G2008 p.69 [PDF 51]). G2026 p.67-68 also requires 0.001 in or less. Use "Hairline", then verify score and cut lines print as vector in the UCP preview. ULS gives no CorelDRAW 2020+ walkthrough in these documents; the Corel text is X3/X4.

**Do not use PostScript fonts or fills; use TrueType only.** (G2026 p.66, p.68).

**Direct File Import (PDF and DXF) is an optional paid add-on, with a 30-day free evaluation (G2026 p.92).** Activated from the UCP System tab. Behaviour (G2026 p.93):
- DXF: vector only; all line width and type data ignored; all vectors imported as solid hairline vectors; Units option converts DXF units to inches or cm; the choice "None (WYSIWYG)" "may produce unpredictable results"; "Center image" and "Sort vectors" options. In Materials mode, red = cut, blue = scribe, other colours use cut settings. In Manual mode, colours map to the colour table.
- PDF: "All strokes as vectors" option turns every stroke into a vector regardless of colour or width; otherwise only red and blue are vectors under the Materials tab. Vector data is kept at highest resolution regardless of Image Density.
- No statement on scale for PDF beyond these units notes. For AutoCAD the guide says print at 1:1 with zero margins and offsets (G2026 p.69).

---

## Not found in the maker's documents

- Kerf width for any lens, and any numeric spot size for the standard 2.0 inch lens.
- Minimum vector line spacing or minimum feature size.
- A maker statement specifically about scoring or marking acrylic with low-power vector lines beyond the one "VECTOR ENGRAVING" row of the Material Settings Guide.
- Any maker setting for 1/8 in (3 mm) black cast acrylic specifically, any setting by VLS3.60 or VLS6.60 model, or any setting for a wattage other than 25 to 60 W. The Material Settings Guide is not labelled for the VLS3.60/6.60 specifically.
- The default order of the colour table in the driver (only an order of listing in G2008).
- A ulsinc.com web page on cast versus extruded acrylic (ulsinc.com/materials and several guessed material URLs returned 404; the Materials Library page ulsinc.com/materials-library.html was not opened). The cast/extruded text above comes from the Material Settings Guide PDF on service.ulsinc.com.
- Reordering of pen colours in G2008 (the 2008 guide does not say it is possible).
- Whether masking changes fine vector score lines.
- How a current CorelDRAW version (2020 and later) should be set up; the maker text covers X3/X4 only.
- Wattage, lens and model variant (desktop or floor) of the school's machines; not guessed.
- G2008 pages missing from the excerpt copy (its printed numbers skip, e.g. pp.31-35, 43-47, 77-94); a full copy might add detail.

## THIRD-PARTY (not the maker; kept separate)

- A Delvies Plastics page "Universal Laser Systems Acrylic Cutting Settings" (delviesplastics.com) was surfaced in a search; a search summary quoted for 1/8 in acrylic "cut speed 7% power 100%" optimized for cast sheets. I did not open the page or confirm the machine, wattage or lens, so do not use it.
- A University of Houston architecture list and a Penn MEAM page were surfaced (power 100, speed 4.5 or 10, PPI 100 for 1/16 in acrylic). Not opened; machine models unknown.
- General web claims that cast is preferred for engraving and extruded for cutting agree with the maker's guide but come from vendors (xometry, trotec, others) and were not used for any fact above.
