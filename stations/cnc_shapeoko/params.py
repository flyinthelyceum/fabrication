"""Parameter block for the Shapeoko 5 Pro 4x4 station carcass.

Every number the model needs lives here and nowhere else. Most of them are
estimates scaled from photographs and published specs, tagged below with their
confidence. None of them gate the CAD: measuring the real machine is an edit to
this file, not a redesign.

Brief: https://notes.aaand.space/cnc-station-enclosure.html (v4, 2026-09-01)

Sourced pass 2026-09-01: manufacturer figures reconciled in from the URLs in
SOURCES. Where a sourced number disagrees with the brief the brief's value is
kept and the disagreement is written on the line, not silently resolved.

Measured pass 2026-09-02: Jared's tape and calipers on the machine itself, plus
two hand-dimensioned elevations of the gussets. The leg opening, the table
height, the four frame gussets, the VFD enclosure and its fans, and the CT 15
are measured now rather than scaled or published, and their CONFIDENCE says so.
The gussets are what replaced ``clear_h``: the ceiling under this machine is a
function of X and Y, not a number. See GUSSETS and ``Station.clear_z``.

Measured pass 2026-09-03: the leg bolt pattern and the leg itself. The whole
``LegHoles`` block is calipered rather than inferred, the legs are ANGLE IRON
and not tube -- which settles ``walls_in_path`` at 1 and kills the crush-sleeve
risk -- and ``z_beam`` is a direct tape reading instead of a derivation that had
implied an impossibly thin frame beam. Two BLOCKING conflicts fell out of that
pass and are Jared's to rule on, not the model's to paper over: see check() and
``parts.leg_joint.check_leg_joint``.
"""

from dataclasses import dataclass
from math import ceil

from lib.house import CARCASS_T, GRID, PANEL_T, QUARTER, STOCK_MODULE, on_grid

# Where each number came from. A reader who doubts a value chases it here.
SOURCES = {
    "footprint_x": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "footprint_y": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "footprint_z": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "travel_x": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "travel_y": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "t_slot_pitch": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "table_h_no_feet": "https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "table_h_with_feet": "https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "leg_wall_t": "MEASURED 2026-09-03, calipers, 0.1385 in. Was the leg kit "
                   "page's 10-gauge: https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "leg_holes": "MEASURED 2026-09-03, Jared's calipers on the machine: pitch "
                  "1.58in both ways, lower row 15-3/4in off the floor, edge offset "
                  "0.9in, hole 0.26in, holes on the left and right sides only, and "
                  "the leg is an ANGLE IRON in profile, not a tube. Supersedes "
                  "https://community.carbide3d.com/t/leg-kit-center-to-center-spacing-and-hole-diameter/105167"
                  " -- a Carbide staff forum reply, not a spec sheet, which had "
                  "covered the pitch and the hole diameter only. "
                  "THEN MEASURED 2026-09-04, Jared, calipers/observed, verbatim: "
                  "\"the legs all follow the inside of the worktable. so in this "
                  "case the front-left leg y-facing flange runs inboard toward "
                  "the machine. as does all flanges on the legs: always inboard. "
                  "also the inside corners on the legs are radiused. OUTSIDE "
                  "MEASUREMENTS-- SIDE_FLANGE: 84mm INSIDE MEASUREMENTS-- 76mm "
                  "(to beginning of radius). M2 17mm from outside face to edge of "
                  "bolt hole.\" So: every flange on all four legs runs INBOARD "
                  "(front_flange_inboard = True); flange_w = 84.0 OUTSIDE, heel "
                  "to toe; inner_fillet_r = 84.0 - 3.5179 - 76.0 = 4.48; "
                  "edge_off_heel = 17.0 + 6.604/2 = 20.302 to the hole CENTRE "
                  "from the HEEL, so edge_off (inner face to centre) derives to "
                  "16.784. SUPERSEDED: the morning reading of 2026-09-04 that "
                  "put the Y flange OUTBOARD (front_flange_inboard = False) was "
                  "a misread of an ambiguous question, not a measurement. "
                  "SUPERSEDED: edge_off 22.86 (0.90in, 2026-09-03) was read as "
                  "inner-edge-to-centre; the 09-04 reading is heel-to-hole-EDGE "
                  "and the two datums differ by the wall plus the hole radius, "
                  "which is the 6.08mm between them.",
    "leg_x_inner": "MEASURED 2026-09-02, tape. Was 1100 scaled off a photograph.",
    "leg_y_inner": "MEASURED 2026-09-02, tape. Was 1150 scaled off a photograph.",
    "leg_splay": "Jared, 2026-09-02: the legs are square. The 6 deg was an "
                 "eyeball off a render, never measured.",
    "clear_h_min": "MEASURED 2026-09-02, tape, floor to the lowest obstruction, "
                   "which is the bottom of an X gusset, not a Y gusset: "
                   "z_beam 839.9875 - gusset_x_h 180.975 = 659.01, 4.96mm from "
                   "the 654.05 tape reading, against 839.9875 - gusset_y_h "
                   "266.7 = 573.29, 80.76mm off.",
    "gusset_x": "MEASURED 2026-09-02, tape plus a hand-dimensioned elevation.",
    "gusset_y": "MEASURED 2026-09-02, tape plus a hand-dimensioned elevation.",
    "gusset_plate_t": "MEASURED 2026-09-02. Photographs and calipers: the "
                       "gussets are flat plates, not solids, no thicker than "
                       "1/4in (6.35mm).",
    "gusset_count": "RULED by Jared 2026-09-02, verbatim: \"Each side has two "
                     "gussets so eight total mirrored across the centerline "
                     "of each axis.\" Confirms the eight-plate model in "
                     "Station.gussets.",
    "z_beam": "MEASURED 2026-09-03, tape, floor to the underside of the frame "
              "beam directly. Was DERIVED from clear_h_min + gusset_y_h "
              "(920.75mm); see check().",
    "extractor_env": "See EXTRACTORS. Each entry carries its own festoolusa URL.",
    "hose_id": "https://carbide3d.com/hub/docs/sweepy-pro-s5-pro/",
    "hose_bend_mult": "UNSOURCED ASSUMPTION. No maker publishes a bend radius for D36/32.",
    "vfd_box": "MEASURED 2026-09-02, calipers. Carbide publishes nothing.",
    "vfd_model": "CONFIRMED 2026-09-09, Jared, reading the drive: CDI Electric "
                 "EM60G1R5S1 (EM60 series, 1.5 kW, SINGLE-PHASE 110 V in), P+ and "
                 "PB solderable posts visible (braking resistor). EM60 manual, "
                 "same day: ONE analog output FM1, P2.0.33 selects frequency OR "
                 "output current (not both); one relay T1, P2.0.29 default = "
                 "running. So SPEED reads FM1 as frequency and LOAD reads a "
                 "split-core current transducer on a spindle phase; T1 is the "
                 "AUTO contact for DUST_CONTROL.",
    "STATION_SUPPLY": "RULED 2026-09-09, Jared: the station is fed by ONE "
                      "dedicated 120 V / 20 A circuit. Drive, PC, extractor, "
                      "lamps and controls all hang off it.",
    "DUST_CONTROL": "RULED 2026-09-09, Jared: the CT 15 E does NOT re-energise "
                    "on mains restore, so switching its mains cannot drive AUTO; "
                    "it has a plug-in auto-start (current-sensing) socket. Every "
                    "selector position acts through a TRIGGER LOAD in that socket, "
                    "fed by the VFD's T1 relay (AUTO) and the selector's ON "
                    "contact wired in PARALLEL; OFF opens both. The CT stays "
                    "energised. Supersedes the brief's SSR-switched extractor "
                    "receptacle. Trigger wattage vs the CT's auto threshold: "
                    "UNVERIFIED.",
    "vfd_fan": "MEASURED 2026-09-02, calipers, two square fans on the left face.",
    "vfd_vent_clear": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "vfd_mount_pitch": "MEASURED 2026-09-09, Jared, calipers on the drive's back: "
                       "3.34in on centre, level pair of KEYHOLES (top 2.287in below "
                       "the case top, 0.614in tall, slot 0.15in, round 0.28in). "
                       "Carbide's doc (https://carbide3d.com/hub/docs/65mm-er16-spindle/) "
                       "said 85 and 'slotted'. Geometry in parts/vfd_mount.py.",
    "VFD_WIRING": "READ 2026-09-09 off the open drive (Jared's photos) and the EM60 "
                  "manual. Control strip order and the relay block are read off the "
                  "silkscreen; Carbide's four wire colours are read off ferrule "
                  "positions in the photo (Jared to confirm by label). J5 and J6 "
                  "both on V (Jared, same day).",
    "JEWEL_LAMP": "RULED 2026-09-09, Jared: 'indicator on jewels for sure'. Dialco / "
                  "Dialight faceted-jewel pilot light, amber, 120 V neon, from the "
                  "Analog Hunt List (Personal Bench BOM - Master, rows 17-23). "
                  "Footprint is the family's, not a part's, until the lamps land.",
    "mini_pc_env": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkStation/ThinkStation_P350_Tiny/ThinkStation_P350_Tiny_Spec.PDF"
                   " -- Lenovo ThinkStation P350 Tiny, 1L Tiny chassis, PSREF "
                   "dimensions 179mm W x 182.9mm D x 36.5mm H (read 2026-09-04). "
                   "MEASURED 2026-09-11, Jared, calipers on the unit with rubber feet: "
                   "7-1/16 x 7-3/16 x 1.425 in = 179.4 x 182.6 x 36.2; PSREF confirmed. "
                   "Replaces the Intel NUC 13 Pro (117x112x54, medium): the P350 "
                   "is the unit Jared is fitting, RT3.",
    "drawer_slide_side_clear": "https://www.accuride.com/hardware/3832 -- the 3832 "
                  "series sheet: \"clearance required .50in +0.031/-0.0 [12.7mm "
                  "+0.8/-0.0]\", and the slides may not function with less than "
                  "12.7mm of side space. Read 2026-09-02.",
    "drawer_slide_build_under": "https://www.accuride.com/hardware/3832 -- same "
                  "sheet, the build recommendation rather than the constraint: "
                  "\"the drawer should be constructed 1-1/16in [27.0mm] less than "
                  "the cabinet opening\". 13.5mm per side, which is the 12.7 "
                  "minimum plus most of its +0.8 band.",
    "er16_collet_od": "DIN 6499 / ISO 15488 ER collet series, ER-16 body: 17.0mm "
                  "OD x 27.5mm long. Chart: "
                  "https://carbideprocessors.com/content/collet-guide-chart.pdf "
                  "and https://www.cgtk.co.uk/metalwork/data/er . Corroborated "
                  "by tool_list.csv, which carries oal 27.5 on all three ER16 "
                  "collets. NOT calipered: Jared's calipers supersede this. "
                  "Read by parts/trays.py, which owns the socket that uses it.",
    # ---- catalog capture 2026-09-03 (C00): parts in hand, by SKU. Datasheet
    # first, Amazon listing second, calipers last (Jared's skus ruling). Every
    # value below is read off the maker's page or the listing it names; anything
    # the sources do not state is None and CONFIDENCE says MEASURE.
    "UPTJ14": "https://www.amazon.com/dp/B0FV7H7CP3 -- the UPERFECT listing "
              "whose item details read Model Number UPTJ14. Its text gives "
              "0.23in thin and 1.4lbs; its VESA image gives 75*75 mm, M4*4 mm, "
              "2 pcs; its port image and a review place the two USB-C and the "
              "mini HDMI on the RIGHT edge facing the screen, buttons and "
              "headphone jack on the LEFT. uperfect.com publishes no UPTJ14 page "
              "(its BE156PF, 355 x 223 x 11, 72% sRGB, is a different panel and "
              "was NOT used). Outline W x H and port offsets are not published.",
    "PL183": "https://www.amazon.com/dp/B09Z2FB8V4 -- PENGLIN listing, Model "
             "Number PL183, 5-pack. Text: panel thickness 2.0-10mm. Its PRODUCT "
             "SIZE drawing: 29.7 overall, flange 2.2 thick, 26 x 31 flange, "
             "round 24 cutout, two 3.5 holes on a 19 x 24 diagonal. thepenglin.com "
             "carries no drawings, only links back to Amazon.",
    "CONSOLE_PLATE": "Jared, 2026-09-09, this thread: 'The sheet shouldn't be "
                     "birch... We should spec a metal plate that we can "
                     "waterjet/lasercut and enduramark etch the markings on.' "
                     "Enduramark: https://www.enduramark.com/ (CO2-laser marking "
                     "spray; black on stainless is its best case).",
    "METER_MOVEMENT": "the pair is a HUNT, not a datasheet: Weston Model 301 "
                      "class, 3.5in round, 0-1 mA DC movement, on the analog "
                      "hunt list 2026-09-09. The 85C1 placeholder/fallback was "
                      "struck 2026-09-09 (subtract pass, item 12).",
    "MAST_BALANCER": "subtract pass 2026-09-09, item 05: the machined "
                     "counterweight, its slot and the delrin pulleys are struck "
                     "for a bought spring tool balancer at the mast tip, 1-3 kg "
                     "class (a retractable balancer, not a zero-gravity arm). "
                     "No SKU yet; envelope is the family's.",
    "45-682-292": "https://www.ergodirect.com/attachments/doc/e3df7e14535acb3b8540cb5b4845df8fa258d971/drawing-ergotron-lx-pro-desk-monitor-arm.pdf"
                  " -- Ergotron DIM-LXproArm dimensional illustrations rev "
                  "11/12/2024, plus the ErgoDirect spec table at "
                  "https://www.ergodirect.com/20192-ergotron-45-682-292-lx-pro-desk-mount-single-monitor-arm-black.html"
                  " (desk 0.4-2.4in, under-surface 2.8in clear, 8.3 lbs) and "
                  "Ergotron's LX Pro spec statement "
                  "https://media.ergotron.com/reserved/resources/specs-lx-pro-series-ea-orig.pdf"
                  " (VESA MIS-D 100/75, 4-22 lbs, lift 13in). ergotron.com "
                  "itself returns 403 to a fetch.",
    "motion_controller_env": "https://carbide3d.com/files/pdf/shapeoko51pro_assembly_3.pdf"
                  " -- the 5.1 Pro assembly guide, section 12.1: the controller "
                  "mounts to the BACK RIGHT table leg with the leg kit's Mounting "
                  "Hardware. It carries NO envelope and NO hole pattern, and "
                  "neither does https://shop.carbide3d.com/products/carbide-motion-pcb ."
                  " LEAD, not evidence: a community user measured 13.25 x 6.75 x "
                  "3.5in with the USB port standing 0.3125in proud, "
                  "https://community.carbide3d.com/t/5-pro-electronics-box-dimensions/59644"
                  " . Not a datasheet, so the value stays None until calipered.",
    "motion_controller_mount": "https://carbide3d.com/files/pdf/shapeoko51pro_assembly_3.pdf"
                  " -- same guide, same page: the photo shows two screws into "
                  "the leg's own holes and a slotted back on the enclosure. "
                  "Pattern not dimensioned anywhere Carbide publishes.",
    "ct15_exhaust": "https://www.festoolusa.com/-/media/tts/fcp/festool-usa/downloads/manuals/10696789_d_ct_15_25_e_us.pdf"
                  " -- CT 15 E / CT 25 E manual (festoolusa serves it empty to "
                  "a script; the Wayback copy at "
                  "http://web.archive.org/web/20240204235125/https://www.festoolusa.com/-/media/tts/fcp/festool-usa/downloads/manuals/10696789_d_ct_15_25_e_us.pdf"
                  " reads). Fig. 1 item [1-8] Exhaust opening: a grille on a "
                  "side face of the head, beside the locking clip [1-7] and "
                  "under the filter drawer [1-6], near the front corner; "
                  "section 9.3: open the grille and the D27/32 hose inserts. "
                  "No dimension or position is given. READ 2026-09-04 off the "
                  "figure itself (page 4 of the PDF, rendered): the drawing "
                  "shows the control panel's face and that side face together, "
                  "so the side is the one on the viewer's RIGHT when facing the "
                  "panel. The value is a DESIGN face-region under Jared's "
                  "ruling of 2026-09-04 (\"airflow is airflow\"): the head band "
                  "over the front half of that face, which covers the grille "
                  "wherever on the face it sits. Airflow is not read here: "
                  "see SOURCES[\"ct15_airflow\"].",
    "ct15_airflow": "https://www.festoolusa.com/-/media/tts/fcp/festool-usa/downloads/manuals/10696789_d_ct_15_25_e_us.pdf"
                  " -- same manual, section 5 Technical data, read 2026-09-04 "
                  "off the Wayback copy. The row reads \"Max. suction capacity "
                  "(air), extractor/turbine: 130 m3/h (4591 cu.ft./h) / 222 "
                  "m3/h (7840 cu.ft./h)\". Two figures, not one: 4591 cu.ft./h "
                  "is 76.5 CFM at the extractor, 7840 cu.ft./h is 130.7 CFM at "
                  "the bare turbine. The festoolusa product page's \"130 CFM "
                  "(3 700 l/min)\" is the TURBINE number -- 3 700 l/min is 222 "
                  "m3/h -- and the model, and the brief, had been reading it as "
                  "the extractor's. Corrected 2026-09-04: the extractor moves "
                  "130 m3/h, and 130 m3/h and 130 CFM are two different numbers "
                  "that happen to share a digit string. Both now sit on the "
                  "EXTRACTORS row under their own names.",
    "ct15_inlet": "https://www.festoolusa.com/-/media/tts/fcp/festool-usa/downloads/manuals/10696789_d_ct_15_25_e_us.pdf"
                  " -- same manual, fig. 3 'Connect the suction hose'. Not "
                  "dimensioned. Hose D 27/32 mm x 3.5 m per the data table. "
                  "OBSERVED 2026-09-04, Jared, no numbers, verbatim: \"The CT15 "
                  "hose comes out of the hole at the top front of the machine "
                  "just to the right of the FESTOOL label\" (viewed from the "
                  "control-panel front). Position and diameter still MEASURE; "
                  "nothing here is invented.",
    "ct15_plug_lead": "https://www.festoolusa.com/-/media/tts/fcp/festool-usa/downloads/manuals/10696789_d_ct_15_25_e_us.pdf"
                  " -- data table: mains power cable length 5.5 m (18 ft). The "
                  "product page says 5 m; the manual's figure is kept and the "
                  "disagreement written here. Cable holder is [1-2] on the head; "
                  "the exit point is not dimensioned.",
    "ct15_main_filter": "https://www.festoolusa.com/accessories/dust-extraction/filters-and-filter-bags/main-filter/204201---hepa-hf-ct-minimidi-2"
                  " -- Main Filter HEPA-HF-CT COMP, order no. 204201, listed for "
                  "CT MINI/MIDI (I) from 2019 and for CT 15 and CT 25. Manual "
                  "9.5 calls it the filter drawer [1-6].",
    # ---- the Kerf fix set, RULED by Jared 2026-09-04 (evening) ----------
    "leg_cols_used": "RULED 2026-09-04, Jared: \"DROP the inner bolt column (8 "
                     "bolts, outer column only; the plinth carries, bolts "
                     "brace)\". The column nearest the leg's inner corner "
                     "(c0, 16.78 in) fails the 18mm land rule by 6mm; the "
                     "outer column (c1, 56.9 in) clears it. The leg's pattern "
                     "is unchanged; the carcass uses one column of it.",
    "stile_toe_land": "RULED 2026-09-04, Jared: \"the flange band is a fixed "
                      "stile\". The stile's inner edge stands this far past "
                      "the steel toe so the door's hinge corner and the "
                      "knuckle never touch the flange on the swing; the "
                      "number is this repo's choice.",
    "lungs_spacer_plies": "RULED 2026-09-04, Jared: \"lungs bay +40 with the "
                          "left slide on a 40 spacer so the tray clears the "
                          "toe\". With the stile and its knuckle in the "
                          "opening the tray needs 45.8 of spacer, not 40; three "
                          "plies of the carcass birch (54) is the first "
                          "one-material block past it. Bay follows to 460.",
    "lungs_door_lay_gap": "RULED 2026-09-04, Jared: the lungs door \"must "
                          "open to 180 to lie against the leg face\". The "
                          "knuckle stands proud so the folded door clears the "
                          "flange's front face by this much; the gap is this "
                          "repo's choice.",
    "corner_chamfer": "RULED 2026-09-04, Jared: \"r4.5 chamfers on the four "
                      "end-wall/deck corners\". The leg's inside corner is a "
                      "4.48 fillet (MEASURED 2026-09-04); a 4.5 chamfer clears "
                      "the whole of it.",
    "tray_knuckle_clear": "Running clearance between the lungs tray's cheek "
                          "and the lungs door's knuckle on the pull. This "
                          "repo's choice.",
}

# ---------------------------------------------------------------- extractors
#
# The station is built around ONE of these. Jared ordered the CT 15 HEPA. The
# CT 36 EI was the v2 unit until 2026-09-03, when the measured z_beam left it
# 39mm short on hose-bend headroom; its row is gone and the surrender is a
# standing note in check() that never clears.
#
# THIS TABLE IS WHY THE REGISTRY EXISTS. The brief carried an envelope tagged
# "CT48 E" that was in fact the CT 36's to within 4mm on height, and a real CT 48
# has never stood under this frame in any version of the design. Envelopes and
# bag part numbers are per size and do not interchange, so both live on the same
# row as the name and neither can drift away from it again.
#
#   CT 15      470 x 320 x 435    15 L    130 m3/h  fitted, DATASHEET (RT6)
#              (re-taken 2026-09-04 from the festoolusa published L x W x H; the
#               earlier caliper read 457 x 308 x 429 was ~6.4mm short on height
#               and undersized W and D. The airflow column is the EXTRACTOR
#               figure, not the turbine's, and it read 130 CFM here until
#               2026-09-04 -- see the row)
#   CT 26 EI   630 x 365 x 540    26 L              never fitted
#   CT 36 EI   630 x 365 x 596    36 L              WITHDRAWN 2026-09-03
#   CT 48 EI   740 x 406 x 1005   48 L              will not fit, ever
#
EXTRACTORS = {
    "CT15": {
        "name": "Festool CT 15 HEPA CLEANTEC",
        "env": (470.0, 320.0, 435.0),   # DATASHEET (RT6, 2026-09-04): festoolusa
                                        # published L x W x H. Supersedes the
                                        # 2026-09-02 caliper (457.2 x 307.975 x
                                        # 428.625), which read ~6.4mm short on
                                        # height. CONFIDENCE: datasheet.
        "capacity_l": 15,
        # AIRFLOW, CORRECTED 2026-09-04. The manual's data table row "Max.
        # suction capacity (air), extractor/turbine" carries TWO figures:
        #   extractor  130 m3/h (4591 cu.ft./h) =  76.5 CFM  through the
        #              machine, filter and hose in the path
        #   turbine    222 m3/h (7840 cu.ft./h) = 130.7 CFM  the fan alone
        # The festoolusa product page's "130 CFM (3 700 l/min)" is the TURBINE
        # figure: 3 700 l/min IS 222 m3/h. This row read airflow_cfm 130.0 and
        # called it the extractor's, which was 1.7x too high. Both figures now
        # live here under their own names and nothing derives from a bare 130.
        # See SOURCES["ct15_airflow"].
        "airflow_extractor_m3h": 130.0,
        "airflow_turbine_m3h": 222.0,
        "bag": "Festool SC-FIS-CT MINI/MIDI-2/5/CT15, part 204308",
        "main_filter": "Festool HEPA-HF-CT COMP (MINI/MIDI-2/CT15), part 204201",
                                        # festoolusa accessory page; see
                                        # SOURCES["ct15_main_filter"]
        "url": "https://www.festoolusa.com/products/dust-extractors/dust-extractors-for-cleaning/578441---ct-15-hepa-us",
    },
}

MAIN_FILTER = "Festool HEPA-HF-CT 26/36/48 PTFE, part 205412"
"""The 26/36/48 filter, kept for anything that still imports the name. It does
NOT cover the CT 15: that unit's filter is part 204201 and lives on its own
EXTRACTORS row as ``main_filter`` (read 2026-09-03 off the festoolusa accessory
page, SOURCES["ct15_main_filter"]). ``Station.consumables`` reads the row, never
this constant, so the fitted unit can no longer be quoted the wrong filter."""


# ---------------------------------------------------------------- catalog
#
# Parts IN HAND, captured by SKU on 2026-09-03 (C00). Jared's ruling: datasheet
# first, Amazon listing second, calipers last. Each block is one part; each
# value is either read off the page SOURCES names for that key or is None,
# and a None is a measurement handed to J02, never a guess. ``catalog_measure``
# lists the Nones and check() reports each one as MEASURE THIS.
#
# Units: mm, kg. Tuples are (W, H) or (W, D) as the comment says.

UPTJ14 = {
    "name": "UPERFECT UPTJ14 15.6in touchscreen",
    "env": None,                    # outside W x H. MEASURE: the listing
                                    # publishes no plan dimension, only thin.
    "thickness": 5.842,             # listing: "0.23in thin" (chassis, kickstand
                                    # folded)
    "weight_kg": 0.635,             # listing: "1.4lbs"
    "vesa": (75.0, 75.0),           # listing VESA image: "VESA Size 75*75 mm"
    "vesa_screw": "M4 x 4mm",       # same image: "Screw Size M4*4 mm/2 Pcs"
    "vesa_holes": 2,                # TWO holes on one horizontal 75mm line,
                                    # not four; the image shows the pair and a
                                    # review says the same. The arm's 4-hole
                                    # plate lands on two screws.
    "vesa_offset": None,            # MEASURE: where the pattern sits on the
                                    # back relative to the outline.
    "usb_c_count": 2,               # listing text and port image
    "usb_c_side": "RIGHT edge facing the screen; buttons and headphone jack "
                  "on the LEFT edge",      # listing port image, corroborated
                                    # by a review on the same listing
    "usb_c_offset": None,           # MEASURE: port centre from the bottom
                                    # edge and from the back face.
    "hdmi": "mini HDMI, same edge as the USB-C pair, outboard of them",
    "runs": "RULED 2026-09-09: TWO cables to the panel, HDMI -> mini HDMI "
            "(video) and USB-A -> USB-C (touch + power), 15ft each, in the "
            "Ergotron arm's cable channels, into the carcass through a gland "
            "at the arm mount (J04), NOT through the console plate. The P350 "
            "Tiny's USB-C carries no video (Lenovo PSREF, 2026-09-08).",
}

PL183 = {
    "name": "PENGLIN PL183 USB-C 3.1 female-female panel-mount coupler, D-type",
    "cutout": "round",              # listing PRODUCT SIZE drawing
    "cutout_d": 24.0,               # same drawing: 24 circle
    "mount_hole_d": 3.5,            # same drawing: 2 x 3.5
    "mount_hole_pitch": (19.0, 24.0),   # holes diagonally opposed, 19 across
                                    # by 24 up, the Neutrik D-shape footprint
    "flange": (26.0, 31.0),         # W x H, same drawing
    "flange_t": 2.2,                # same drawing
    "overall_l": 29.7,              # same drawing, flange face to rear of body
    "body_behind_flange": 27.5,     # 29.7 - 2.2; subtract the panel to get
                                    # depth behind the panel
    "panel_t_range": (2.0, 10.0),   # listing text: "Panel thickness 2.0-10mm"
    "cable_behind": None,           # MEASURE: the mating USB-C plug's straight
                                    # length behind the body is not on the sheet
}

LX_PRO_ARM = {                      # Ergotron 45-682-292, the SOURCES key
    "name": "Ergotron LX Pro desk arm, matte black, 45-682-292",
    "vesa": ((75.0, 75.0), (100.0, 100.0)),     # MIS-D 100/75, spec statement
    "load_kg": (1.8, 10.0),         # 4-22 lbs, spec statement
    "reach": 656.0,                 # drawing: 25.8in pole axis to plate, fully
                                    # extended. Spec rounds it to "<= 25in".
    "lift": 330.0,                  # 13in, spec statement
    "desk_t_range": (10.0, 60.0),   # ErgoDirect: 0.4-2.4in. Drawing: the
                                    # 2-piece clamp has three positions, <=10,
                                    # 12-35 and 37-60.
    "under_clear_d": 71.0,          # drawing: 2.8in the clamp reaches under
                                    # the edge; ErgoDirect: "<= 2.8in (70mm)
                                    # deep to be clear of obstacles"
    "clamp_base_footprint": (115.0, 87.0),   # W x D on the surface, drawing
                                    # top view 4.5 x 3.4in
    "clamp_drop_below": 137.0,      # drawing: 5.4in below the surface
    "pole_above": 135.0,            # drawing: 5.3in base to top of the 5in pole
    "pole_d": 30.0,                 # drawing: 1.2in
    "weight_kg": 3.76,              # ErgoDirect: 8.3 lbs
    "clamp_plate_holes": None,      # MEASURE: the vertical clamp plate carries
                                    # a hole field (drawing shows it, no
                                    # numbers). J04's leg-pattern fit-check
                                    # needs it.
    "grommet": "not included; 98-728-292 is the grommet base",
    "cable_route": "the arm's channels carry the screen's two cables to a "
                   "gland at the mount; see UPTJ14['runs'] (ruling 2026-09-09)",
}

motion_controller_env = None        # W x H x D. MEASURE. Carbide publishes no
                                    # envelope; the forum lead in SOURCES is not
                                    # a datasheet and does not drive design.
motion_controller_mount = None      # foot / slot pattern. MEASURE. The guide
                                    # says BACK RIGHT leg, leg kit hardware,
                                    # and stops there.

ct15_exhaust = {
    # A design FACE-REGION, not a grille position. RULED 2026-09-04 (Jared):
    # "we don't need to overengineer the plenum ct15 grille. airflow is
    # airflow." The plenum (parts/exhaust_plenum.py) covers the whole region
    # and sizes its sections to the unit's airflow, so where inside this
    # face the grille [1-8] actually sits stops mattering. See SOURCES.
    "side": "right, facing the control panel",   # manual Fig. 1: the side
                                    # with the locking clip [1-7] and the
                                    # filter drawer [1-6]. On the tray, the
                                    # panel faces the lip (+Y), so this is
                                    # the -X face, toward the LEFT end wall.
    "along_frac": (0.5, 1.0),       # the half of the unit's length nearest
                                    # the control panel (the grille is by the
                                    # front corner, beside the clip)
    "up_frac": (0.6, 1.0),          # the head band: the top 40% of the
                                    # unit's height. Fig. 1 puts the grille
                                    # in the head's lower band, just over the
                                    # container seam; this covers it.
}
ct15_inlet = None                   # hose inlet position on the container.
                                    # MEASURE.
ct15_plug_lead = {
    "length": 5500.0,               # manual data table: 5.5 m (18 ft)
    "exit": None,                   # MEASURE: where the lead leaves the head
}

CONSOLE_PLATE = {
    "name": "Console plate: 3mm 304 stainless, #4 brushed, waterjet cut, "
            "Enduramark legends",
    "t": 3.0,                       # RULED 2026-09-09 (Jared). The plate is NOT
                                    # birch: 12mm carcass stock was inherited
                                    # from the carcass and fought every
                                    # panel-mount device on it (XB4 1-6, PL183
                                    # 2-10, NAHDMI-W <=2). 3mm sits inside every
                                    # range the plate carries.
    "material": "304 stainless sheet, #4 brushed, 3.0 (11 ga nominal)",
    "process": "waterjet in the IC, through cuts only (bores, D-types, "
               "screw clearances); countersinks on the drill "
               "press after; legends Enduramark black on the Universal laser, "
               "the plate located on its two short-edge screw holes (REGISTER)",
    "screw": "4 x 10 flat head countersunk wood screw, 12 off",
    "size": (400.0, 200.0),         # RULED 2026-09-09: composition #3 needs 200
                                    # tall (two 3.5in dials + a switch row + a
                                    # port row); CONSOLE_Z0 GRID*24 -> GRID*20.
    "composition": "five groups on one axis (READ / ARM / MACHINE / EXTRACTION "
                   "/ PORTS), console_plate.py docstring; composed, not packed",
    "panel_t_range_note": "3mm is inside XB4 (1-6), PL183 (2-10) and the "
                          "meters' stud reach; console_plate checks each row",
}

DUST_CONTROL = {                    # the DUST selector's wiring (2026-09-09)
    "extractor": "CT15",
    "ct_mode": "AUTO, left there; the CT's own face switch is never touched",
    "actuator": "a TRIGGER LOAD plugged into the CT 15's auto-start socket; "
                "the CT sees current and runs. Not a contactor on its mains: "
                "the CT 15 stays off after a mains cut, so mains switching "
                "cannot give AUTO.",
    "AUTO": "trigger load fed through the VFD's T1 relay (EM60 P2.0.29, "
            "default = running)",
    "ON": "trigger load fed through the selector's own contact, wired in "
          "PARALLEL with T1",
    "OFF": "both paths open; the trigger load is dead, the CT idles in AUTO",
    "supersedes": "the SSR-switched extractor receptacle (parts/mains_backplate "
                  "RECEPTACLE_NAME and its SSR): the CT stays energised and is "
                  "never switched at its mains. SSR struck from the model "
                  "2026-09-09 (subtract pass, item 10); the receptacle rides "
                  "ALWAYS-LIVE and a 24 V interposing relay on that rail "
                  "(mains_backplate.TRIGGER_RELAY_ENV) switches the load.",
    "trigger_relay": "MY2NJ-class 24 V DC ice-cube relay in an 8-pin DIN socket; "
                     "coil from the VFD's +24V through T1 (AUTO) and the DUST "
                     "selector's ON contact in parallel; flyback diode across "
                     "the coil; contact rated 10 A switches the 0.6 A load",
    "trigger_load": "two 100 ohm 100 W aluminium-housed wirewound resistors in "
                    "series (200 ohm, 72 W at 120 V) bolted to the steel mains "
                    "backplate as their heatsink; fused at 1 A",
    "trigger_load_w": 60.0,         # MEASURED 2026-09-09: a 60 W resistive
                                    # load in the auto socket fired the CT 15
                                    # at once. Smaller not tested. Build the
                                    # load at 60 W (240 ohm, 100 W wirewound
                                    # on a heatsink, brain band). T1 (3 A)
                                    # switches 0.5 A directly, no relay.
}

VFD_WIRING = {                      # the EM60's control strip as built (2026-09-09)
    "control_strip": ("+10V", "VF1", "FM1", "GND", "COM", "DI1", "DI2", "DI3",
                      "DI4", "OP", "+24V"),      # top to bottom on the silkscreen
    "relay_block": ("TA", "TB", "TC"),           # T1: TA-TC normally open per
                                                 # the EM60 family; CONFIRM on
                                                 # manual p.18 before mains
    "jumpers": "J5 (VF1) on V, J6 (FM1) on V: analog in and out both 0-10 V "
               "(Jared 2026-09-09)",
    "carbide": {"red": "VF1", "black": "GND", "green": "COM", "blue": "DI1"},
                                    # read off ferrule positions in the photo:
                                    # 0-10 V speed, analog ground, digital
                                    # common, run. Jared to CONFIRM by label.
    "carbide_confirmed": None,      # MEASURE: read the label beside each ferrule
    "station_adds": {"SPEED": "FM1 + GND, one series resistor at the meter",
                     "DUST_AUTO": "trigger load across TA + TC (T1 NO), 120 V, "
                                  "routed out of the box on its own path",
                     "LOAD": "nothing in the box: split-core CT on U, V or W"},
    "expansion": "JP1 2-row header = the EM60 expansion slot (a fact of the "
                 "board). The EM60-IO card that would give a second analog out "
                 "has no purchase path (searched 2026-09-09) and was struck; "
                 "LOAD reads the phase clamp",
    "untouched": "P+ / PB (braking resistor), +10V, OP, DI2-DI4, +24V",
}

STATION_SUPPLY = {                  # RULED 2026-09-09
    "circuit": "one dedicated 120 V / 20 A branch circuit",
    "loads": "VFD (EM60G1R5S1, single-phase 110 V), console PC, CT 15, "
             "console lamps and controls",
}

JEWEL_LAMP = {                      # the two console indicators (2026-09-09)
    "name": None,                   # MEASURE (a hunt): Dialco / Dialight faceted
                                    # jewel pilot light, amber, 120 V neon;
                                    # Analog Hunt List rows 17-23
    "supersedes": "Schneider XB4BVB5 (the 24 V LED pilot that stood as BAG_LAMP)",
    "mount": "5/8in (16) hole, ~20 bezel, ~40 behind with leads, thin panel: "
             "the family's numbers (console_plate.JEWEL_*), assumption",
    "drive": {"BAG_LAMP": "station controller, filter differential pressure "
                          "(nothing behind it until the controller exists)",
              "EXTR_LAMP": "120 V neon in PARALLEL with the CT 15 trigger load "
                           "(DUST_CONTROL): lit whenever the extractor is asked to run"},
}

METER_MOVEMENT = {                  # the two dials, SPEED and LOAD (2026-09-09)
    "name": None,                   # MEASURE (a hunt): a MATCHED PAIR of vintage
                                    # 3.5in moving-coil movements, Weston 301
                                    # class, 0-1 mA DC, custom scale cards
                                    # (SPEED 0-24k RPM, LOAD 0-100 %). Model TBD.
    "target": "3.5in round case, Weston 301 class: bezel ~89 on the face, body "
              "through a ~76 bore, ~60 behind. The console is COMPOSED around "
              "this footprint and cuts the two bores (console_plate.METER_*); "
              "stud holes are drilled from the movement when the pair lands. "
              "Assumption until then.",
    "drive": "SPEED: 0-10V from the EM60's single analog output FM1 set to "
             "frequency (P2.0.33), one series resistor. LOAD: a split-core "
             "current transducer on one spindle phase, 0-10V out, one series "
             "resistor; FM1 cannot carry both (SOURCES['vfd_model'], 2026-09-09)",
    "panel_t_range": (1.0, 6.0),    # assumption: stud-mounted bezel, M3 studs;
                                    # read the pair when it lands.
}

MAST_BALANCER = {                   # subtract pass 2026-09-09, item 05
    "name": None,                   # MEASURE: a 1-3 kg retractable spring tool
                                    # balancer, hung at the mast tip, hose on
                                    # its hook. Replaces the machined
                                    # counterweight, slot and delrin pulleys.
    "envelope": None,               # MEASURE: body dia x height, hook drop,
                                    # cable travel; the family runs ~60-80 dia
                                    # x 100-130 tall, 1.5 m travel
    "capacity_kg": (1.0, 3.0),      # the hose over the bed, estimate
}

CATALOG = {
    "UPTJ14": UPTJ14,
    "PL183": PL183,
    "CONSOLE_PLATE": CONSOLE_PLATE,
    "STATION_SUPPLY": STATION_SUPPLY,
    "DUST_CONTROL": DUST_CONTROL,
    "METER_MOVEMENT": METER_MOVEMENT,
    "MAST_BALANCER": MAST_BALANCER,
    "VFD_WIRING": VFD_WIRING,
    "JEWEL_LAMP": JEWEL_LAMP,
    "45-682-292": LX_PRO_ARM,
    "motion_controller_env": motion_controller_env,
    "motion_controller_mount": motion_controller_mount,
    "ct15_exhaust": ct15_exhaust,
    "ct15_inlet": ct15_inlet,
    "ct15_plug_lead": ct15_plug_lead,
}


def catalog_measure() -> list[str]:
    """Dotted names of every catalog value that is still None.

    One name per measurement J02 owes. check() turns each into a MEASURE note,
    so the gate lists exactly these and nothing sourced hides among them."""
    out: list[str] = []
    for key, val in CATALOG.items():
        if val is None:
            out.append(key)
        elif isinstance(val, dict):
            out.extend(f"{key}.{k}" for k, v in val.items() if v is None)
    return out


# What each open catalog value is FOR, so the tape is pointed at the right
# thing. Keyed like catalog_measure() names them.
CATALOG_MEASURE_HINTS = {
    "MAST_BALANCER.name": "Which spring balancer hangs the hose at the mast "
                  "tip; sets the tip fitting and the hook drop.",
    "MAST_BALANCER.envelope": "Body dia x height, hook drop and cable travel "
                  "of the balancer: the mast's tip envelope and the hose's "
                  "reach over the bed.",
    "DUST_CONTROL.trigger_load_w": "The CT 15's auto-start current threshold "
                  "(manual) and a resistive load that clears it: what the "
                  "DUST selector actually switches.",
    "UPTJ14.env": "Outside W x H of the chassis, kickstand folded: sizes the "
                  "console aperture and the drawer keep-out.",
    "UPTJ14.vesa_offset": "Centre of the two-hole 75mm pattern from the "
                  "outline: where the arm plate puts the screen.",
    "UPTJ14.usb_c_offset": "USB-C centres from the bottom edge and the back "
                  "face on the RIGHT edge: the cable exit and its bend room.",
    "PL183.cable_behind": "Straight length of the mating USB-C plug behind "
                  "the body: depth the console plate needs behind the panel.",
    "METER_MOVEMENT.name": "Which matched pair of movements: confirms the two "
                  "76 bores on the console, sets the stud pattern (drilled from "
                  "the part), bezel, depth behind and the scale cards.",
    "JEWEL_LAMP.name": "Which jewel lamps: sets the two 16 bores on the console "
                  "and what is behind them.",
    "VFD_WIRING.carbide_confirmed": "Read the label beside each of Carbide's four "
                  "ferrules (red/black/green/blue) on the EM60 strip; the photo "
                  "reading is VF1/GND/COM/DI1.",
    "45-682-292.clamp_plate_holes": "Hole field on the 2-piece clamp's "
                  "vertical plate: what J04 lands on the leg's 40x40 pattern "
                  "or the Carbide bracket.",
    "motion_controller_env": "Controller enclosure W x H x D and the USB "
                  "stand-proud: the brain band's keep-out. Forum lead 336.6 x "
                  "171.5 x 88.9 is not a datasheet.",
    "motion_controller_mount": "Slot/foot pattern on the enclosure back: "
                  "matches or does not match the leg's 40x40.",
    "ct15_inlet": "Hose inlet centre on the head: where the D36 hose "
                  "leaves the bay toward the hose port. Sets the floor of "
                  "exhaust_plenum's hose corridor and so the plenum's top.",
    "ct15_plug_lead.exit": "Where the mains lead leaves the head: the "
                  "station socket's side.",
}

# Confidence tags carried from the brief's parameter table, so a reader of the
# model knows which numbers are load-bearing guesses.
CONFIDENCE = {
    "table_h": "measured",   # 2026-09-02: levelling feet ARE on the machine, so
                             # it is Carbide's 945 config and not the 893 one.
    "clear_h_min": "measured",   # floor to the LOWEST obstruction, which is the
                             # bottom of an X gusset (839.9875 - 180.975 = 659.01,
                             # 4.96mm off the tape), not a Y gusset. The floor of
                             # the envelope.
    "z_beam": "measured",    # 2026-09-03 tape, floor to the underside of the
                             # frame beam directly. Was derived from
                             # clear_h_min + gusset_y_h; see SOURCES.
    "gusset_x": "measured",  # both X gussets, height, top band and clear span
    "gusset_y": "measured",  # both Y gussets, plus the inner block
    "gusset_plate_t": "measured",   # 2026-09-02 photographs and calipers:
                             # flat plate, <= 1/4in.
    "gusset_count": "measured",   # RULED by Jared 2026-09-02: two plates per
                             # leg, eight total. See check() and SOURCES.
    "leg_x_inner": "measured",   # 2026-09-02 tape, was 1100 off a photograph
    "leg_y_inner": "measured",   # same tape
    "leg_splay": "ruling",   # RULED by Jared 2026-09-02: the legs are square.
                             # The field survives so a measured non-zero can drop
                             # in, but nothing in the model reads it any more.
    "vfd_box": "measured",   # 2026-09-02 calipers
    "vfd_fan": "measured",   # 2026-09-02 calipers, two square fans, left face
    "extractor_env": "calipered",   # the fitted CT 15 row is calipered
                                 # (2026-09-02); the CT 36 EI row was deleted
                                 # with the withdrawn v2 path, 2026-09-03
    "vfd_panel_standoff": "assumption",     # see the field. A traded clearance.
    "vfd_louvre_free_ratio": "assumption",  # nobody publishes one
    "lungs_lining_t": "medium",  # MLV plus open-cell foam, lay-up not yet bought
    "lungs_slide_t": "high",     # Accuride 3832 class member section
    "lungs_side_clear": "medium",   # a hand's clearance, chosen not sourced
    "drawer_slide_side_clear": "high",      # Accuride 3832 sheet, the constraint
    "drawer_slide_build_under": "high",     # same sheet, the recommendation
    "er16_collet_od": "high",       # DIN 6499 standard size, not calipered
    "footprint_x": "high",       # carbide3d spec table
    "footprint_y": "high",       # carbide3d spec table
    "footprint_z": "medium",     # live spec 23.25in, older forum quotes of the same field 21in
    "travel_x": "high",          # carbide3d spec table
    "travel_y": "high",          # carbide3d spec table
    "t_slot_pitch": "high",      # carbide3d spec table
    "table_h_no_feet": "high",   # carbide leg kit page
    "table_h_with_feet": "high", # carbide leg kit page
    "leg_wall_t": "measured",    # 2026-09-03 calipers, 0.1385in, against the leg
                                 # kit page's 10-gauge nominal
    # ONE tag for the whole LegHoles block, because the block is one measurement
    # session and not seven independent numbers. check() reports it as unmeasured
    # until this reads "measured".
    "leg_holes": "measured",     # 2026-09-03 calipers, the whole block: pitch,
                                 # rows, edge offset, hole diameter, which faces
                                 # carry holes, and the angle-iron profile that
                                 # settles walls_in_path at 1. The flange WIDTH
                                 # is not a LegHoles number the geometry reads;
                                 # it gates check_leg_joint's reach note instead.
    "hose_id": "high",           # carbide sweepy pro doc, 35/36mm
    "hose_bend_mult": "assumption",  # nobody publishes one. Flagged, not sourced.
    "vfd_vent_clear": "high",    # carbide 65mm spindle doc, 30cm
    "vfd_mount_pitch": "measured",   # 2026-09-09, calipers, 3.34in
    "mini_pc_env": "datasheet",  # Lenovo P350 Tiny, PSREF W x D x H
    # ---- catalog capture 2026-09-03 (C00). "datasheet" = read off the maker's
    # page or the listing SOURCES names. A dotted key is one value inside that
    # block that the sources do not state; it is None and reads MEASURE.
    "UPTJ14": "datasheet",
    "UPTJ14.env": "MEASURE",
    "UPTJ14.vesa_offset": "MEASURE",
    "UPTJ14.usb_c_offset": "MEASURE",
    "PL183": "datasheet",
    "PL183.cable_behind": "MEASURE",
    "CONSOLE_PLATE": "ruling",      # 2026-09-09, Jared: stainless, waterjet,
                                    # Enduramark
    "STATION_SUPPLY": "ruling",     # 2026-09-09, Jared: one 120 V / 20 A circuit
    "DUST_CONTROL": "ruling",       # 2026-09-09, Jared: through the auto socket
    "MAST_BALANCER.name": "MEASURE",
    "MAST_BALANCER.envelope": "MEASURE",
    "DUST_CONTROL.trigger_load_w": "measured",   # 2026-09-09, 60 W fires
    "vfd_model": "confirmed",       # 2026-09-09, Jared read it off the drive
    "METER_MOVEMENT": "assumption",     # 3.5in target footprint, composed around
    "METER_MOVEMENT.name": "MEASURE",
    "JEWEL_LAMP": "ruling",             # 2026-09-09, Jared: jewels
    "JEWEL_LAMP.name": "MEASURE",
    "VFD_WIRING": "read",               # 2026-09-09, silkscreen + photos + manual
    "VFD_WIRING.carbide_confirmed": "MEASURE",
    "45-682-292": "datasheet",
    "45-682-292.clamp_plate_holes": "MEASURE",
    "motion_controller_env": "MEASURE",     # forum lead only, not a datasheet
    "motion_controller_mount": "MEASURE",
    "ct15_exhaust": "design",       # RULED 2026-09-04, Jared: "airflow is
                                    # airflow". A face region, not a grille.
    "ct15_airflow": "datasheet",    # the manual's own data table, both figures
    "ct15_inlet": "MEASURE",
    "ct15_plug_lead": "datasheet",
    "ct15_plug_lead.exit": "MEASURE",
    "ct15_main_filter": "datasheet",
    # ---- the Kerf fix set, 2026-09-04 (evening) ----
    "leg_cols_used": "ruling",
    "stile_toe_land": "choice",
    "lungs_spacer_plies": "choice",      # under a ruling that said 40; see SOURCES
    "lungs_door_lay_gap": "choice",
    "corner_chamfer": "ruling",
    "tray_knuckle_clear": "choice",
}


# ---------------------------------------------------------------- gussets
#
# THE CEILING UNDER THIS MACHINE IS A SURFACE, NOT A NUMBER.
#
# ``clear_h`` used to be one scalar, 780mm, and every check compared against it.
# Ruled by Jared 2026-09-02, after measuring: "clear_h as a global constraint
# gives up a ton of space between the gussets on x and still over a foot of
# usable full height on y. Model the gussets in their entirety and let's develop
# around them."
#
# Each one hangs from the underside of a frame beam, runs at FULL intrusion
# for a top band, then tapers back to the leg's inner face -- along the axis
# it braces. Below a gusset entirely, the full leg opening is clear.
# ``Station.clear_z(x, y)`` is the resulting ceiling and ``Station.clear_h_min``
# is only its lowest value.
#
# MEASURED 2026-09-02, second pass: Jared's photographs and calipers. The
# gussets are flat plates, ``gusset_plate_t`` thick (6.35mm, 1/4in), bolted
# between a leg and the frame beam -- not the wall-to-wall solids the first
# pass modelled for want of that measurement. Along the axis a gusset braces,
# nothing changes: the heights, the top bands, the tapers and the inboard
# intrusions are the same numbers already committed. Along the axis it does
# NOT brace, each gusset is now the plate thickness, positioned at the leg it
# sits against, not a solid run to the far wall.
#
# How many plates there are was open until Jared ruled it 2026-09-02,
# verbatim: "Each side has two gussets so eight total mirrored across the
# centerline of each axis." The hand elevations are one gusset per side per
# axis -- four drawings -- but they are elevations, not plans; the ruling is
# what settles it. ``Station.gussets`` places each measured profile twice,
# once per leg on the axis it does not brace: EIGHT plates, not four. See
# CONFIDENCE["gusset_count"] and the docstring on ``Station.gussets``.
#
# One constraint rides on top of all of it, ruled the same day: "We should be
# building the carcass to fit between the legs flush to the edges of the CNC
# bed. Workholding often mounts pieces vertically against the outside face of
# the bed so we can't build outside of the footprint of the legs." Flush to the
# leg inner faces is allowed. Outside them is not, ever.


@dataclass(frozen=True)
class Gusset:
    """One frame gusset plate, expressed as the ceiling it imposes.

    ``axis`` is the axis the gusset eats into and ``side`` is which end of that
    axis it hangs off. The profile is read in ``u``, the distance in from the
    leg inner face on that side, so the two gussets braced against the same
    axis share one set of measurements and differ only in which way ``u`` runs.

    Along the axis it does NOT brace, a gusset is a flat plate: ``plate_t``
    thick (MEASURED, see SOURCES), sitting at one end of that axis --
    ``cross_side`` says which -- rather than running the full ``span`` between
    the legs. ``cross_lo``/``cross_hi`` are that plate's extent, in station
    coordinates on the cross axis.
    """

    label: str
    axis: str           # "x" | "y"
    side: str           # "near" (the u = 0 end) | "far"
    z_beam: float       # underside of the frame beam it hangs from
    height: float       # total, down from z_beam
    top_h: float        # the band at full intrusion, down from z_beam
    intrude: float      # how far in from the leg face, at full intrusion
    length: float       # full clear span of the constrained axis
    span: float         # full clear span of the axis this gusset does NOT
                        # constrain, i.e. the leg opening the plate sits in
    plate_t: float      # MEASURED. The plate's own thickness, on the cross axis
    cross_side: str     # "near" (cross = 0 end) | "far", which leg the plate
                        # sits against on the axis it does not constrain

    @property
    def z_bot(self) -> float:
        """Lowest point of the gusset. Below this the whole opening is clear."""
        return self.z_beam - self.height

    @property
    def taper_h(self) -> float:
        """Height of the tapering part, between z_bot and the top band."""
        return self.height - self.top_h

    def u_at(self, coord: float) -> float:
        """Distance in from this gusset's leg face, given a station coordinate."""
        return coord if self.side == "near" else self.length - coord

    def coord_at(self, u: float) -> float:
        """The inverse: station coordinate, given a distance in from the face."""
        return u if self.side == "near" else self.length - u

    def intrusion_at(self, z: float) -> float:
        """How far in from the leg face the gusset reaches at height ``z``.

        Also the depth a part standing at the leg face has to be relieved by to
        reach that height.
        """
        if z <= self.z_bot:
            return 0.0
        if z >= self.z_bot + self.taper_h:
            return self.intrude
        return self.intrude * (z - self.z_bot) / self.taper_h

    def ceiling_at(self, u: float) -> float:
        """Highest z anything may reach at ``u`` in from the leg face."""
        if u >= self.intrude:
            return self.z_beam
        if u <= 0.0:
            return self.z_bot
        return self.z_bot + self.taper_h * (u / self.intrude)

    @property
    def cross_lo(self) -> float:
        """Low-coordinate edge of the plate on the axis it does not brace."""
        return 0.0 if self.cross_side == "near" else self.span - self.plate_t

    @property
    def cross_hi(self) -> float:
        """High-coordinate edge of the plate on the axis it does not brace."""
        return self.cross_lo + self.plate_t

    def applies_at(self, cross: float) -> bool:
        """Whether this plate is present at ``cross``, the coordinate on the
        axis it does not brace. Off the plate, this gusset imposes nothing."""
        return self.cross_lo <= cross <= self.cross_hi


# ---------------------------------------------------------------- leg bolt pattern
#
# THE LEGS ARE SQUARE. Ruled by Jared 2026-09-02, verbatim: "There is no way
# Shapeoko manufactured table legs with splay. It's square. We have no reason to
# believe otherwise." ``leg_splay`` is 0.0 below and nothing in the model reads
# it any more.
#
# What replaced the leg-tie bracket is the leg's OWN bolt pattern. The carcass
# footprint is flush to the leg inner faces, so an end wall's outer face is
# already against a leg's inner face: a bolt through the leg's existing hole
# lands in a threaded insert in the birch with nothing in between and nothing
# outside the leg but a head and a washer.
#
# THIS WHOLE BLOCK IS UNMEASURED. Carbide staff gave the pitch and the hole
# diameter on forum thread 105167 and nothing else; every other field here is a
# plausible placeholder this repo invented so the geometry could be drawn.
# Jared calipers the legs 2026-09-03. It is ONE block with ONE confidence tag
# because it is one measurement session, and ``check()`` reports it as unmeasured
# until CONFIDENCE["leg_holes"] says otherwise. Tomorrow's numbers are an edit to
# the defaults below and to nothing else in the repo.
#
# THE DATUM IS THE HEEL (2026-09-04). The leg is an angle whose two flanges both
# run INBOARD, so its outer corner -- the HEEL, the outside face of either
# flange -- is the only sharp edge the leg has; the inside corner between the
# flanges is a fillet (``inner_fillet_r``). The station origin stays on the
# intersection of the two INNER faces, one ``LEG_WALL_T`` in from the heel on
# each axis, because that is the plane the carcass is flush to; but every
# in-face number Jared reads with calipers is read from the heel, so the
# measured field is the heel reading and the inner-face figure derives.

LEG_WALL_T = 3.5179
"""MEASURED 2026-09-03, calipers, 0.1385in. The leg's wall, one constant so
``Station.leg_wall_t`` and ``LegHoles.edge_off`` cannot disagree about it."""


@dataclass(frozen=True)
class LegHoles:
    """The Shapeoko leg's own bolt pattern, as the carcass uses it.

    IN-FACE COORDINATES. The pattern is read on the leg face it is cut in, not
    in station coordinates, so it survives whichever face turns out to carry it:

        h   horizontal, in the plane of the face, measured from the leg's INNER
            edge INTO the leg opening -- +Y on a front leg, -Y on a rear leg
        v   vertical, measured from the FLOOR

    ``rows_z`` is the subset of rows the carcass actually bolts to, not every
    hole the leg has. ``pitch_v`` records the pattern's own vertical spacing so
    tomorrow's calipers can be checked against the rows rather than replacing
    them silently.
    """

    pitch_h: float = 40.132
    """Horizontal centre-to-centre, in the face. MEASURED 2026-09-03, calipers,
    1.58in. Confirms the 40mm FORUM figure (Carbide staff, 105167) almost
    exactly."""

    pitch_v: float = 40.132
    """Vertical centre-to-centre, in the face. MEASURED 2026-09-03, calipers,
    1.58in -- the same reading as ``pitch_h``: the pattern is a square 2x2
    cluster, not the tall two-row brace the 65mm placeholder assumed. Replaces
    that placeholder; back ON the 20mm bench grid is still not true (40.132mm),
    which is why nothing bolted to a leg can be grid-indexed on both axes."""

    hole_d: float = 6.604
    """MEASURED 2026-09-03, calipers, 0.26in. The leg's own through hole.
    Supersedes the 7mm FORUM figure. 6.604mm is an M6 NORMAL clearance hole
    (DIN 66 medium is 6.6), where 7mm would have been a loose one, so the bolt
    the leg chose is M6 either way and no hardware moves.

    ONE LABEL TO CONFIRM: Jared reported this as the diameter "on y bolt holes".
    Read here as the holes this joint uses -- the pattern on the x_inner faces,
    whose in-face horizontal coordinate IS y in station coordinates, which is how
    ``bolts()`` names them. The alternative reading, a second pattern on the
    Y-FACING flange, would contradict the same session's "nothing on front and
    rear" and nothing in the carcass could use it anyway."""

    rows_z: tuple[float, ...] = (400.05, 440.182)
    """MEASURED 2026-09-03, calipers. Height above the FLOOR of each hole row
    the carcass uses: the lower row at 15-3/4in (400.05mm), the upper row one
    ``pitch_v`` above it. Replaces the (150, 650)mm placeholder, which assumed
    two widely-spaced rows -- one low, one near the top cap -- rather than the
    single tight cluster the calipers found."""

    cols_per_leg: int = 2
    """Hole columns per leg, at ``pitch_h``, starting ``edge_off`` in from the
    leg's inner edge. Confirmed by the 2026-09-03 calipers, unchanged from the
    placeholder."""

    edge_off_heel: float = 20.302
    """MEASURED 2026-09-04, Jared, calipers. First column's CENTRE from the
    HEEL (the flange's outside face). SOURCE "Jared, calipers/observed
    2026-09-04"; CONFIDENCE measured. The reading was 17.0mm from the outside
    face to the EDGE of the lower-front bolt hole; plus half of ``hole_d``
    (6.604 / 2 = 3.302) puts the centre at 20.302.

    Supersedes 22.86 (0.90in, 2026-09-03), which this repo had read as
    inner-edge-to-centre. The two readings are different datums, not a
    disagreement: heel-to-edge 17.0 plus the hole radius is 20.302 to the
    centre from the heel, and less the wall it is 16.784 from the inner face
    (``edge_off``). The 09-03 figure sat 6.08mm further in than the leg's hole
    actually does, which is why every inner-column bolt now lands closer to the
    end wall's front edge than the 09-03 model said."""

    @property
    def edge_off(self) -> float:
        """DERIVED: first column's centre from the leg's INNER face INTO the
        opening, ``edge_off_heel`` less one wall. 16.784mm.

        Kept under this name because it is the in-face coordinate the joint
        works in: the inner face is the station datum, the plane the carcass is
        flush to, and the edge the two materials share -- the end wall's birch
        runs from it inward and the leg's steel from it outward. A bolt needs
        both, so it lives where the leg's flange reaches back across that face
        into the opening (``flange_reach``)."""
        return self.edge_off_heel - LEG_WALL_T

    faces: tuple[str, ...] = ("x_inner",)
    """CONFIRMED 2026-09-03: "Bolt holes are only on left and right sides of
    machine. Nothing on front and rear." Which leg faces carry the pattern.

    ``x_inner`` is the face whose normal runs in X: the one a left leg presents
    to the left end wall and a right leg to the right end wall. Those are the
    only faces the carcass has birch against, because the front of the station
    is open and the rear is a door. Left/right on the machine IS the X-facing
    pair, so the placeholder guess was right; the Y-facing (front/rear) faces
    carry nothing, confirmed."""

    walls_in_path: int = 1
    """CONFIRMED 2026-09-03: "Each leg is an angle iron in profile, not tube."

    How many thicknesses of leg wall a bolt crosses on its way to the insert. An
    angle is an OPEN section, so the answer is 1: the head bears on the single
    wall the hole is in, there is no cavity to span, and THE CRUSH SLEEVE RISK IS
    DEAD. A closed tube would have made this 2, grown the bolt by the tube's
    depth and needed a sleeve or an internal spacer nobody had bought. The
    placeholder guessed 1 and the calipers agreed, which is luck rather than
    method, and it is written down because the next station's legs get measured
    and not assumed."""

    flange_w: float | None = 84.0
    """MEASURED 2026-09-04, Jared, calipers, OUTSIDE: heel (the flange's outer
    face) to toe, the same for both flanges of the angle. SOURCE "Jared,
    calipers/observed 2026-09-04"; CONFIDENCE measured.

    Read from the HEEL, not from the inner face: the in-opening reach past the
    inner face is ``flange_reach`` (84.0 - 3.5179 = 80.48). The bolt pattern had
    proven 66.29mm of that reach by its own existence; the tape found 14.2mm
    more. It is ONE width for both flanges because Jared read one number
    ("SIDE_FLANGE: 84mm") for a symmetric angle."""

    inner_fillet_r: float = 4.48
    """MEASURED 2026-09-04 by difference, Jared, calipers. The leg's inside
    corner, between its two flanges, is a fillet and not a sharp edge: the
    INSIDE reading was 76.0mm from a flange's inner face to the start of the
    radius, so 84.0 (outside) - 3.5179 (wall) - 76.0 (inside, to the radius) =
    4.48. SOURCE "Jared, calipers/observed 2026-09-04"; CONFIDENCE measured.

    Modelled wherever a leg envelope is built (``machine.leg_envelopes``): the
    fillet is steel filling the corner the carcass's own square corner would
    otherwise occupy, so an end wall flush to both inner faces meets it unless
    that corner is chamfered or the carcass steps in. The old "inner corner"
    datum was a sharp edge that does not exist; the datum is the heel and the
    inner faces derive from it, one ``LEG_WALL_T`` in."""

    front_flange_inboard: bool | None = True
    """INBOARD, all four legs, both flanges, full leg height. Jared, 2026-09-04,
    verbatim: "the legs all follow the inside of the worktable. so in this case
    the front-left leg y-facing flange runs inboard toward the machine. as does
    all flanges on the legs: always inboard." SOURCE "Jared, calipers/observed
    2026-09-04"; CONFIDENCE measured.

    True: the Y-facing flange runs INTO the leg opening from the corner,
    across the bay's open front (the angle's vertex, the heel, at the leg's
    OUTER corner). The morning reading of the same day (False, outboard) was a
    misread of an ambiguous question and is superseded; see SOURCES.
    Added 2026-09-03 (C06), because the lungs carriage and the three drawers
    all pull out through the front, and a flange running inboard stands
    squarely in their path. ``machine.front_leg_flanges`` builds that band
    (``flange_reach`` wide, ``LEG_WALL_T`` thick, floor to table) and the
    carriage, the lungs door, the rear door and the drawers check against it.
    The field's name is historical: it is one reading for every leg."""

    @property
    def flange_reach(self) -> float | None:
        """DERIVED: how far a flange reaches INTO the opening past the leg's
        inner face, ``flange_w`` less one wall. 80.48mm. None while unmeasured.

        This is the number every in-opening check wants: the toe of the
        Y flange in X across a bay's front, and the toe of the X flange in Y
        along an end wall, both measured from the station datum."""
        return None if self.flange_w is None else self.flange_w - LEG_WALL_T

    cols_used: tuple[int, ...] = (1,)
    """Which of the leg's columns the carcass bolts to, by index into
    ``columns_h``. RULED 2026-09-04 (Jared): the OUTER column only. Column 0,
    16.78 in from the inner face, lands 5.98mm short of the end wall's 18mm
    land (``leg_joint.EDGE_LAND``, never relaxed); column 1 at 56.9 clears it
    by 34. Eight bolts brace the frame, the plinth carries the carcass. SOURCE
    "leg_cols_used"; CONFIDENCE ruling. The leg's own pattern (``cols_per_leg``)
    is still the measured 2x2; this is what the carcass uses of it."""

    def columns_h(self) -> tuple[float, ...]:
        """Column offsets in from the leg's inner edge, at ``pitch_h``: the
        leg's whole pattern."""
        return tuple(self.edge_off + i * self.pitch_h for i in range(self.cols_per_leg))

    def columns_used_h(self) -> tuple[float, ...]:
        """The columns the carcass bolts to, as offsets in from the inner
        edge. What ``leg_joint.bolts`` iterates."""
        cols = self.columns_h()
        return tuple(cols[i] for i in self.cols_used)

    @property
    def count_per_leg(self) -> int:
        return len(self.rows_z) * len(self.cols_used)

    @property
    def span_h(self) -> float:
        """How far into the opening the last USED column reaches."""
        cols = self.columns_used_h()
        return cols[-1] if cols else 0.0


@dataclass(frozen=True)
class Station:
    # ---- machine envelope -------------------------------------------------
    table_h: float = 945.0          # MEASURED 2026-09-02. Levelling feet ARE on the
                                    # machine, so this is Carbide's 945 config. The
                                    # brief's 889 was an exact 35in conversion of a
                                    # number that was never the right config.
    clear_h_min: float = 654.05     # MEASURED 2026-09-02, 25-3/4 in, floor to the
                                    # LOWEST obstruction under the frame, which is
                                    # the bottom of an X gusset (839.9875 - 180.975
                                    # = 659.01, 4.96mm off the tape), not a Y
                                    # gusset. This is the FLOOR of the clearance
                                    # envelope and not the envelope: anything whose
                                    # footprint is smaller than the leg opening
                                    # asks clear_z(x, y) instead.
    z_beam: float = 839.9875        # MEASURED 2026-09-03, 33-1/16 in, floor to the
                                    # UNDERSIDE OF THE FRAME BEAM directly, per the
                                    # standing request in check(). Supersedes the
                                    # clear_h_min + gusset_y_h derivation (920.75mm),
                                    # which implied a 24.25mm beam and was flagged as
                                    # too thin to be real. This measurement implies
                                    # 105.0mm instead, which is plausible for a
                                    # member carrying the gantry.
    leg_x_inner: float = 1254.125   # MEASURED 2026-09-02, 49-3/8 in, inside faces of
                                    # the legs, left to right. Was 1100 scaled off the
                                    # leg-kit photo, so the model gained 154mm here.
    leg_y_inner: float = 1089.025   # MEASURED 2026-09-02, 42-7/8 in, inside faces,
                                    # front to back. Was 1150, so it lost 61mm.
    leg_splay: float = 0.0          # degrees
    """RULED by Jared 2026-09-02: the legs are square.

    The 6.0 that stood here was an eyeball off a leg-kit render by an earlier
    session, tagged UNSOURCED / low, and it was wrong. The field is kept so a
    measured non-zero can drop in without a schema change; nothing in the model
    reads it any more."""

    # ---- the four gussets, measured -------------------------------------
    # Heights are down from the beam underside. Clear spans are between the two
    # gussets on that axis; the per-side intrusion is derived from them so it
    # follows the tape rather than being written down twice.
    gusset_x_h: float = 180.975     # 7-1/8 in, total height of an X gusset
    gusset_x_top_h: float = 53.975  # 2-1/8 in, the band at full intrusion
    gusset_x_clear: float = 1144.5875   # 45-1/16 in, clear X in the top band
    gusset_y_h: float = 266.7       # 10-1/2 in, total height of a Y gusset
    gusset_y_top_h: float = 85.725  # 3-3/8 in, the band at full intrusion
    gusset_y_clear: float = 315.9125    # 12-7/16 in, clear Y in the top band
    gusset_y_block: tuple[float, float] = (95.25, 85.725)
    """The innermost part of a Y gusset: a roughly square block, 3-3/4 x 3-3/8
    in, measured in Y and Z off the hand-dimensioned elevation.

    The envelope does NOT use it. It treats the whole intrusion as solid from
    the leg face inward, which is conservative: if the gusset is only this block
    at its inner end, the envelope opens by whatever is behind the block. Kept
    because it is a real measurement and the day someone models the gusset as a
    part rather than as a keep-out, this is the shape."""
    gusset_plate_t: float = 6.35    # MEASURED 2026-09-02, photographs and
                                    # calipers, 1/4in. Each gusset is a flat
                                    # plate this thick along the axis it does
                                    # NOT brace, sitting at the leg it braces --
                                    # not a solid run to the far wall. See the
                                    # gusset docstring block above and check().

    # ---- machine, as published --------------------------------------------
    # The station has to live inside these. None of them were in the brief.
    footprint_x: float = 1524.0     # 60 in, carbide3d spec table
    footprint_y: float = 1498.6     # 59 in, carbide3d spec table
    footprint_z: float = 590.55     # 23.25 in, carbide3d spec table. CONTRADICTION:
                                    # older forum quotes of this same field say 21 in
                                    # (533.4). The published spec appears to have moved.
    travel_x: float = 1237.0        # carbide3d spec table
    travel_y: float = 1237.0        # carbide3d spec table
    t_slot_pitch: float = 102.6     # centre to centre, carbide3d spec table
    table_h_no_feet: float = 893.0  # carbide leg kit page, its own mm for 35 in
    table_h_with_feet: float = 945.0    # carbide leg kit page, 36 in
    leg_wall_t: float = LEG_WALL_T  # MEASURED 2026-09-03, calipers, 0.1385 in.
                                    # Carbide's leg kit page says 10-gauge (3.4mm);
                                    # the extra 0.12mm is powder coat on both faces,
                                    # which is the direction that does not matter.
                                    # Anything bolted to a leg gets a backing washer.
    leg_holes: LegHoles = LegHoles()
    """The leg's own bolt pattern, in one block. See LegHoles and check()."""

    # ---- extractor selection ----------------------------------------------
    extractor: str = "CT15"
    """The unit that was ORDERED and that v1 is built around. It is also the
    only unit the station will ever take.

    RULED by Jared 2026-09-03: "maximize the space we have and we'll live with
    what we must." The v2 promise to accept a CT 36 EI without a redesign is
    WITHDRAWN. It was not given up to a choice in the carcass, it was taken by
    the tape: floor to the underside of the frame beam is 33-1/16in, not the
    920.75mm the old derivation implied, and a CT 36 EI wants its 596mm body
    plus a 144mm hose bend under a ceiling 39mm short of carrying both. No
    divider move recovers a ceiling. The surrender is a standing note in
    check() that never clears."""

    # ---- bays -------------------------------------------------------------
    bay_brain_d: float = 250.0      # rear band, full width
    bay_hands_w: float = 412.0      # drawer opening + the right end-wall
                                    # doubler ply (12mm): the blind M6 leg-joint
                                    # insert needs 24mm of end wall at 12mm
                                    # stock, so the end walls are doubled and the
                                    # hands bay grows one ply to keep 400 clear.

    # ---- drawer slides, as the maker specifies them ------------------------
    # The BOM buys 500mm full-extension side-mount slides, Accuride 3832 class,
    # which is the same family the lungs carriage rides. Two numbers come off
    # the maker's own sheet and they are not the same number:
    drawer_slide_side_clear: float = 12.7   # the CONSTRAINT: .50in +.031/-0.0
                                    # of side space per side. Below this the
                                    # slide does not run. See SOURCES.
    drawer_slide_build_under: float = 27.0  # the RECOMMENDATION: build the box
                                    # 1-1/16in narrower than the opening, which
                                    # is 13.5 per side and lands inside the
                                    # tolerance band rather than on its floor.
                                    # parts/drawers.py sizes the box from this
                                    # and checks the result against the
                                    # constraint above.

    # ---- lungs bay allowance ----------------------------------------------
    # bay_lungs_w is DERIVED from these and the fitted extractor. It used to be a
    # 480 literal sized around a CT 48 that was really a CT 36, which left 66mm
    # of slack nothing had named. Naming the three allowances means the bay
    # resizes correctly when the extractor changes instead of keeping a cushion
    # whose size nobody could account for.
    lungs_lining_t: float = 12.0    # MLV plus open-cell foam, bonded, per side
    lungs_slide_t: float = 12.7     # slide member plus its clearance, per side
    lungs_side_clear: float = 20.0  # hand clearance, carriage to lining, per side
    lungs_spacer_plies: int = 5
    """Plies of the carcass birch laminated into the block the LEFT slide's
    cabinet member screws to, standing off the left end wall's inner face.
    RULED 2026-09-04 (Jared): "lungs bay +40 with the left slide on a 40
    spacer so the tray clears the toe". The stile that replaced the flange
    band carries the lungs door's knuckle at its inner edge, and the tray has
    to pass the knuckle, not only the toe. At 12mm house stock the tray needs
    about 52.8 of spacer to clear the stile's inner edge, the knuckle and a
    running clearance, so the block is five plies of the carcass birch (60);
    at the old 18mm three plies gave 54. The bay derives from it. SOURCE
    "lungs_spacer_plies"; CONFIDENCE choice."""

    # ---- the Kerf fix set, RULED 2026-09-04 (evening) ---------------------
    # Every door and drawer front is INSET between a fixed stile and a
    # divider, flush in the carcass plane, no overlay anywhere; the flange
    # band at each corner is a birch stile standing inside the steel.
    stile_toe_land: float = 2.0
    """How far a stile's inner edge stands past the leg flange's toe, into the
    opening. The knuckle and the door's hinge corner live at that edge, so
    this is what keeps both off the steel on the swing. SOURCE
    "stile_toe_land"; CONFIDENCE choice."""

    lungs_door_lay_gap: float = 1.0
    """Air between the lungs door's outer face, folded to 180, and the
    flange's front face it lies against. Sets the proud knuckle's axis:
    (leg_wall_t + this) / 2 in front of the carcass plane. SOURCE
    "lungs_door_lay_gap"; CONFIDENCE choice."""

    corner_chamfer: float = 4.5
    """Chamfer on the four vertical outer corners of the carcass (end walls
    and deck) where the leg's 4.48 inside fillet stands. RULED 2026-09-04
    ("r4.5 chamfers"). SOURCE "corner_chamfer"; CONFIDENCE ruling; check()
    holds it against ``LegHoles.inner_fillet_r``."""

    tray_knuckle_clear: float = 2.0
    """Running clearance between the lungs tray's left cheek and the lungs
    door's knuckle, on the pull. SOURCE "tray_knuckle_clear"; CONFIDENCE
    choice."""

    # ---- components -------------------------------------------------------
    vfd_model: str = "CDI Electric EM60G1R5S1"   # CONFIRMED 2026-09-09, Jared:
                                    # EM60 1.5 kW, single-phase 110 V; P+ / PB
                                    # posts seen. FM1 analog out (freq OR
                                    # current), T1 relay = running. SOURCES.
    vfd_box: tuple[float, float, float] = (142.875, 184.15, 320.675)   # vertical.
                                    # CALIPERED 2026-09-02, w x d x h. Supersedes the
                                    # brief's 200 x 130 x 300 guess and the forum's
                                    # 152 x 178 x 260. Narrower and deeper than both.
    vfd_fan: float = 84.1375        # CALIPERED 2026-09-02. Square fan aperture.
    vfd_fan_count: int = 2          # both on the vented LEFT face
    vfd_vent_clear: float = 300.0   # carbide 65mm spindle doc, 30cm from the vented
                                    # (left) face to any obstruction
    vfd_mount_pitch: float = 84.84  # MEASURED 2026-09-09 (Jared, calipers):
                                    # 3.34in between the two keyholes on the
                                    # back, level pair. Carbide's doc says 85.

    # ---- VFD ventilation: a knowing deviation -----------------------------
    # Ruling 2026-09-02, Jared: the drive vents THROUGH THE PANEL.
    #
    # Carbide asks for 300mm of clear air off the drive's vented LEFT face. This
    # station does not give it 300mm of clear air. The drive stands vertically in
    # Carbide's own stock orientation at the LEFT end of the brain band, its
    # vented face looking at a louvred opening in the left brain-band cheek
    # vfd_panel_standoff away, and the 300mm is satisfied by the open room on the
    # other side of that louvre rather than by span inside the box.
    #
    # THIS IS A TRADE, NOT A SOLUTION, and it is written here so nobody later
    # reads a passing check as Carbide's clearance having been met. What was
    # bought for it: the brain band stops reserving a 430mm internal corridor,
    # which was the previous model's answer and which turned the drive 90 degrees
    # out of the orientation its stock mount sets.
    #
    # What pays for it, all three required together:
    #   1. louvre free area >= vfd_louvre_free_ratio x the FAN APERTURE area
    #   2. intake low, through the plinth and the deck
    #   3. exhaust high, through the top cap's louvre field over the band
    #
    # Ruled by Jared 2026-09-02, once the drive had been calipered: "Fan aperture
    # for sure. Why would we calculate off of a sealed face?" The requirement had
    # been 1.5x the whole 130 x 300mm left face, which was a guess at an enclosure
    # nobody had measured AND was mostly sealed steel that moves no air. It is now
    # 1.5x the two 84.1mm square fans, and it fell from 585cm2 to 212cm2.
    vfd_vent_mode: str = "panel"
    vfd_panel_standoff: float = 40.0        # 2 grid modules, vented face to the
                                            # cheek's inner face. ASSUMPTION.
    vfd_louvre_free_ratio: float = 1.5      # ASSUMPTION, not sourced. Nobody
                                            # publishes a free-area figure for a
                                            # louvre standing in for a clearance.
                                            # 1.5 pays for the air having to turn
                                            # through 90 degrees to leave.

    mini_pc_env: tuple[float, float, float] = (179.0, 36.5, 182.9)   # Lenovo P350 Tiny,
                                    # stood UPRIGHT on its 37mm-flat profile: big
                                    # face (179 W) to the reveal, only 36.5 deep
                                    # into the brain band, 182.9 tall (RT3, PSREF)

    # ---- sheet goods ------------------------------------------------------
    carcass_t: float = CARCASS_T
    panel_t: float = PANEL_T
    stock_module: float = STOCK_MODULE
    sheet_slot: tuple[float, float] = (600.0, 600.0)   # HALF blank on edge
    sheet_pitch: float = GRID       # slot spacing in the rack. RULING 19,
                                    # 2026-09-04 REVERSES ruling 11: one grid
                                    # module, 20mm pitch. At 12mm house stock a
                                    # blank plus clearance is a ~14mm slot in a
                                    # 20mm pitch, so the comb keeps a 6mm tooth
                                    # and the bay holds 18 blanks, not 9.
    laser_blank: tuple[float, float] = QUARTER

    # ---- extraction -------------------------------------------------------
    hose_id: float = 36.0           # antistatic, the run to the boot.
                                    # Confirmed: carbide sweepy pro takes 35/36mm.
    hose_bend_mult: float = 4.0     # ASSUMPTION, not a spec. No manufacturer publishes
                                    # a bend radius for the D36/32 hose family, so the
                                    # model uses a multiple of hose diameter.
    overrun_s: int = 12             # hose clear time after the spindle drops
    cyclone: bool = False           # struck 2026-09-01. All internal, no external port.

    # ---- earthing and bonding ---------------------------------------------
    # Ruled by Jared 2026-09-02: antistatic hose, and the grounding has to be
    # real rather than a word on a BOM line. Sourced research disagreed about
    # WHERE the charge goes, and the disagreement is the interesting part.
    #
    # Festool's own path: the AS hose is conductive along its length and earths
    # through the CT's chassis to the CT's mains plug. That works and needs
    # nothing from us EXCEPT that the socket the CT sits in is genuinely earthed.
    # The Carbide 3D community's warning runs the other way: do NOT drive a
    # separate earth rod for the dust system, because a second earth reference is
    # a ground loop and code wants one ground per system.
    #
    # Both are right, and they reconcile as a STAR POINT. Everything metal bonds
    # to one PE bar. Nothing bonds to earth by a second route. The thing that
    # must stay OFF the bar is the motion controller's logic 0V, because that is
    # the path that turns a hose discharge into a false limit switch.
    hose_antistatic: bool = True    # not optional. The 36mm run is the AS/CTR hose.
    bond_star_point: str = "PE bar, sealed mains compartment"
    bond_lead_mm2: float = 4.0      # green/yellow. Sized for a boot in a shop, not
                                    # for fault current: it gets stood on.
    bond_clip_pitch: float = 300.0  # clip the lead to the OUTSIDE of the hose.
                                    # Inside, it collects chips and blocks the line.
    bond_max_ohm: float = 1.0       # convention for a bonding conductor, not a
                                    # Festool figure. Record the real reading.

    # Everything that lands on the bar. If this list grows a controller, stop.
    bond_targets: tuple[str, ...] = (
        "CT 15 chassis, via its own earthed plug on a station socket",
        "hose cuff at the dust boot, by a lead run outside the hose",
        "machine frame and spindle body, via the VFD's PE",
        "mast extrusion, which carries the hose over the centroid",
        "carcass hardware that touches any of the above",
    )

    # Named so that adding one is a deliberate act rather than a slip.
    bond_excluded: tuple[str, ...] = (
        "the motion controller's logic 0V",
        "any second earth rod or building steel tap",
    )

    def front_bay_d(self) -> float:
        """Usable depth of a front bay: the leg opening less the rear brain band
        and the panel that divides them."""
        return self.leg_y_inner - self.bay_brain_d - self.carcass_t

    def hose_bend_r(self) -> float:
        """Working bend radius for the extraction hose. An assumption, derived so
        that it moves when hose_id moves."""
        return self.hose_id * self.hose_bend_mult

    # ---- the fitted extractor ---------------------------------------------

    @property
    def spec(self) -> dict:
        """The EXTRACTORS row for the unit that is actually going in."""
        return EXTRACTORS[self.extractor]

    @property
    def extractor_env(self) -> tuple[float, float, float]:
        """(long axis in Y, width in X, height in Z) of the fitted unit.

        Derived from the selector, never written down twice. The unit's long axis
        runs front to back so it pulls toward the operator; see the carcass
        module's note on why all three front bays load from the front."""
        return self.spec["env"]

    @property
    def consumables(self) -> dict:
        """Bag and filter for whatever is fitted. Bags are per size."""
        return {"filter_bag": self.spec["bag"], "main_filter": self.spec["main_filter"]}

    # ---- lungs bay width, derived rather than estimated -------------------

    @property
    def lungs_spacer(self) -> float:
        """Thickness of the left slide's spacer block: plies of the carcass
        birch. 60mm at five plies of 12mm stock. DERIVED."""
        return self.lungs_spacer_plies * self.carcass_t

    def lungs_allowance(self) -> float:
        """Total width the bay spends on everything that is not the extractor:
        acoustic lining, slide member and hand clearance, both sides, plus the
        left slide's spacer (2026-09-04)."""
        return (
            2 * (self.lungs_lining_t + self.lungs_slide_t + self.lungs_side_clear)
            + self.lungs_spacer
        )

    @property
    def bay_lungs_w(self) -> float:
        """Clear width of the lungs bay, set by the fitted extractor, on the grid.

        Snapped UP: the bay is allowed to be generous, never short. This is the
        one bay dimension the fitted unit sets. 460 with the 54 spacer
        (2026-09-04); was 400."""
        need = self.spec["env"][1] + self.lungs_allowance()
        return _snap_up(need)

    # ---- the clearance envelope, which replaced clear_h --------------------

    @property
    def gusset_x_intrude(self) -> float:
        """How far an X gusset reaches in from a leg face, per side. Derived
        from the measured clear span so it follows the tape."""
        return (self.leg_x_inner - self.gusset_x_clear) / 2

    @property
    def gusset_y_intrude(self) -> float:
        """The same for a Y gusset, which is seven times the bite."""
        return (self.leg_y_inner - self.gusset_y_clear) / 2

    @property
    def gussets(self) -> tuple[Gusset, ...]:
        """Eight of them, in station coordinates: one per leg per axis.

        Each of the four measured profiles (X left, X right, Y front, Y rear)
        is now a plate, ``gusset_plate_t`` thick, at ONE end of the axis it does
        not brace -- not a solid run to the far wall. RULED by Jared
        2026-09-02: "Each side has two gussets so eight total mirrored across
        the centerline of each axis." So every measured profile is placed
        twice, once per leg on the axis it does not constrain -- eight plates,
        not four. See CONFIDENCE["gusset_count"].
        """
        z = self.z_beam
        profiles = (
            ("X gusset left", "x", "near", self.gusset_x_h, self.gusset_x_top_h,
             self.gusset_x_intrude, self.leg_x_inner, self.leg_y_inner,
             ("front", "rear")),
            ("X gusset right", "x", "far", self.gusset_x_h, self.gusset_x_top_h,
             self.gusset_x_intrude, self.leg_x_inner, self.leg_y_inner,
             ("front", "rear")),
            ("Y gusset front", "y", "near", self.gusset_y_h, self.gusset_y_top_h,
             self.gusset_y_intrude, self.leg_y_inner, self.leg_x_inner,
             ("left", "right")),
            ("Y gusset rear", "y", "far", self.gusset_y_h, self.gusset_y_top_h,
             self.gusset_y_intrude, self.leg_y_inner, self.leg_x_inner,
             ("left", "right")),
        )
        out: list[Gusset] = []
        for label, axis, side, height, top_h, intrude, length, span, corners in profiles:
            for cross_side, corner in (("near", corners[0]), ("far", corners[1])):
                out.append(Gusset(
                    f"{label} @ {corner}", axis, side, z, height, top_h,
                    intrude, length, span, self.gusset_plate_t, cross_side,
                ))
        return tuple(out)

    def clear_z(self, x: float, y: float) -> float:
        """Highest z anything may reach at (x, y). THE envelope.

        This is what replaced the scalar clear_h. Every gusset whose plate
        covers this point votes and the lowest ceiling wins; a gusset whose
        plate sits elsewhere on the cross axis imposes nothing here."""
        z = self.z_beam
        for g in self.gussets:
            coord, cross = (x, y) if g.axis == "x" else (y, x)
            if g.applies_at(cross):
                z = min(z, g.ceiling_at(g.u_at(coord)))
        return z

    def clear_z_over(
        self, xs: tuple[float, float], ys: tuple[float, float]
    ) -> float:
        """Lowest ceiling anywhere over a rectangular footprint.

        The four corners are enough for the one caller of this, which always
        asks about the full leg opening: every gusset plate meets a leg face
        exactly at a corner, at u = 0 on its constrained axis, which is its
        worst point regardless of the plate's cross-axis position. A footprint
        that does NOT sit on the leg faces could miss a plate's cross-axis band
        at its corners and still catch it in the middle of an edge; this method
        does not search for that, because nothing calls it with such a
        footprint yet."""
        return min(self.clear_z(x, y) for x in xs for y in ys)

    # ---- VFD panel venting ------------------------------------------------

    @property
    def vfd_vent_aperture_area(self) -> float:
        """Open area of the drive's fans on its vented LEFT face.

        The face itself is 184 x 321mm and almost all of it is sealed steel.
        What moves air is the two square fans, and Jared ruled on 2026-09-02
        that the louvre answers the aperture, not the face."""
        return self.vfd_fan_count * self.vfd_fan ** 2

    @property
    def louvre_free_area_req(self) -> float:
        """Free area the brain-band louvre has to present for the traded
        clearance to be paid for. See the vfd_vent_mode comment block."""
        return self.vfd_vent_aperture_area * self.vfd_louvre_free_ratio


def _snap_up(mm: float) -> float:
    """Round up to the bench grid.

    carcass.py has the same helper, but params sits underneath carcass and
    cannot import from it without a cycle. Both derive from house.GRID, so
    there is one grid, not two."""
    return ceil(mm / GRID - 1e-9) * GRID


STATION = Station()


def check(s: Station = STATION) -> list[str]:
    """Report every constraint the current numbers violate.

    Run this after editing a parameter. It is cheaper than discovering the
    conflict in geometry.
    """
    problems: list[str] = []

    if CONFIDENCE.get("leg_x_inner") == "low":
        problems.append(
            f"leg_x_inner is still {s.leg_x_inner:.0f}mm scaled off a photograph, "
            "not measured. It is the one unsourced number the whole model stands "
            "on, and stock is the bay that absorbs whatever the tape says. This "
            "note does not clear until CONFIDENCE says it was measured."
        )

    if s.leg_x_inner >= s.footprint_x:
        problems.append(
            f"leg_x_inner {s.leg_x_inner:.0f}mm is not inside the machine's own "
            f"{s.footprint_x:.0f}mm footprint. One of the two is wrong."
        )

    if s.table_h not in (s.table_h_no_feet, s.table_h_with_feet):
        problems.append(
            f"table_h {s.table_h:.0f}mm matches neither published leg config "
            f"({s.table_h_no_feet:.0f} without leveling feet, "
            f"{s.table_h_with_feet:.0f} with). Which feet are on the machine "
            f"moves the clearance by {s.table_h_with_feet - s.table_h_no_feet:.0f}mm."
        )

    if CONFIDENCE.get("leg_holes") != "measured":
        h = s.leg_holes
        problems.append(
            f"the leg bolt pattern is PARTLY measured. 2026-09-03 calipers gave "
            f"the {h.pitch_h:.2f} x {h.pitch_v:.2f}mm pitch (a square 2x2 "
            f"cluster, not the tall two-row placeholder), rows_z at "
            f"{', '.join(f'{z:.2f}' for z in h.rows_z)}mm off the floor, the "
            f"{h.edge_off:.2f}mm edge offset and confirmed the {h.faces} face "
            "list. STILL UNMEASURED: hole_d "
            f"({h.hole_d:.0f}mm, forum) and walls_in_path={h.walls_in_path} -- "
            "the leg cross-section, open channel vs. closed tube, which is "
            "the crush-sleeve question and the one field that can change the "
            "hardware order. The block clears when CONFIDENCE[\"leg_holes\"] "
            "says measured, because it is one measurement session and this "
            "is not the whole session yet."
        )

    # clear_h_min was tape-read to the bottom of an X gusset, not a Y gusset
    # (SOURCES, CONFIDENCE). Both z_beam and clear_h_min are independently
    # measured now, so this always runs rather than only while z_beam was
    # derived: it is a cross-check between two tape readings, not a gate on
    # either one's confidence.
    CLEAR_H_MIN_TOL = 10.0  # mm, tape
    clear_h_min_expected = s.z_beam - s.gusset_x_h
    clear_h_min_diff = s.clear_h_min - clear_h_min_expected
    if abs(clear_h_min_diff) > CLEAR_H_MIN_TOL:
        problems.append(
            f"clear_h_min {s.clear_h_min:.2f}mm disagrees with z_beam - gusset_x_h "
            f"({s.z_beam:.2f} - {s.gusset_x_h:.1f} = {clear_h_min_expected:.2f}mm) "
            f"by {clear_h_min_diff:.2f}mm, outside the {CLEAR_H_MIN_TOL:.0f}mm tape "
            "tolerance. clear_h_min is supposed to be the bottom of an X gusset; "
            "re-tape both numbers."
        )

    problems.append(
        "EXTRACTOR GROWTH SURRENDERED, standing note. The station is sized "
        f"for the {EXTRACTORS[s.extractor]['name']} and for nothing "
        "larger. The "
        "CT 36 EI growth path was withdrawn by Jared 2026-09-03 after the "
        "measured z_beam left it 39mm short on hose-bend headroom, which no "
        "divider move recovers. This note never clears; it is here so a "
        "passing gate is never read as the CT 36 EI still fitting. "
        "Swapping up later is a new carcass, not a conversion."
    )

    if CONFIDENCE.get("gusset_count") == "low":
        problems.append(
            "each gusset's extent along the axis it does NOT constrain is now "
            f"measured: it is a flat plate, {s.gusset_plate_t:.2f}mm thick "
            "(photographs and calipers, 2026-09-02), at the leg it braces, not "
            "the wall-to-wall solid the first pass modelled for want of that "
            "measurement. Which leg was not measured directly: the hand "
            "elevations are one gusset per side per axis, four drawings, and "
            "the table has four legs, so this model ASSUMES each leg carries "
            "two plates, one bracing X and one bracing Y -- eight plates, not "
            "four. Confirm on the machine whether every leg really carries "
            "its own pair before this clears. This note does not clear until "
            "CONFIDENCE says the count was settled."
        )

    problems.append(
        "a gusset's intrusion depth is still modelled solid the whole way "
        "from the leg face to the top band, rather than only the measured "
        f"{s.gusset_y_block[0]:.1f} x {s.gusset_y_block[1]:.1f}mm block at a Y "
        "gusset's inner end. The block's own footprint was measured off the "
        "hand-dimensioned elevation; whether the gusset is really solid there "
        "or is only that block was not measured. If it is only the block, the "
        "envelope opens further than this model says. That is still the "
        "conservative direction, same as before fdeaee5, and it stays open."
    )

    if s.corner_chamfer < s.leg_holes.inner_fillet_r:
        problems.append(
            f"corner_chamfer {s.corner_chamfer:.2f} is under the leg's "
            f"{s.leg_holes.inner_fillet_r:.2f} inside fillet: the carcass corner "
            "stands in the steel"
        )

    if any(i >= s.leg_holes.cols_per_leg for i in s.leg_holes.cols_used):
        problems.append(
            f"LegHoles.cols_used {s.leg_holes.cols_used} names a column the "
            f"{s.leg_holes.cols_per_leg}-column leg does not have"
        )

    if s.extractor_env[2] > s.clear_h_min:
        problems.append(
            f"{s.spec['name']} is taller than the clearance under the frame "
            f"({s.extractor_env[2]:.0f} into {s.clear_h_min:.0f}, over by "
            f"{s.extractor_env[2] - s.clear_h_min:.0f}mm). It does not stand under "
            "this machine in any orientation the bay allows."
        )

    if s.extractor_env[0] > s.front_bay_d():
        problems.append(
            f"extractor is deeper than a front bay ({s.extractor_env[0]:.0f} into "
            f"{s.front_bay_d():.0f}mm), so it cannot lie down in the lungs bay either"
        )

    if s.clear_h_min - s.extractor_env[2] < s.hose_bend_r():
        problems.append(
            f"no room above the extractor for the hose to turn: "
            f"{s.clear_h_min - s.extractor_env[2]:.0f}mm of headroom against a "
            f"{s.hose_bend_r():.0f}mm working bend radius (assumed, not published)"
        )

    if s.vfd_box[2] > s.clear_h_min:
        problems.append("VFD box is taller than the clearance under the frame")

    if s.vfd_vent_mode == "panel":
        # The old question was whether the bay is deep enough to hold Carbide's
        # 300mm inside it. Under the 2026-09-02 ruling that is the wrong question:
        # the clearance is deliberately taken outside the box. What has to hold
        # instead is that the trade was actually paid for.
        problems.append(
            f"TRADED CLEARANCE, standing note. Carbide asks {s.vfd_vent_clear:.0f}mm "
            f"of clear air off the drive's vented face. It gets "
            f"{s.vfd_panel_standoff:.0f}mm and then a louvre to room air. Ruled by "
            "Jared 2026-09-02. This note never clears; it is here so a passing check "
            "is never read as Carbide's clearance having been met. Paid for by a "
            f"louvre of at least {s.louvre_free_area_req / 100.0:.0f}cm2 free area "
            f"({s.vfd_louvre_free_ratio:.1f}x the FAN APERTURE, which is "
            f"{s.vfd_fan_count} squares of {s.vfd_fan:.1f}mm. Ruled by Jared "
            "2026-09-02: the fans move the air, not the sealed steel around "
            "them), intake low through the plinth, exhaust high through the top cap."
        )
        if s.bay_brain_d < s.vfd_box[1] + s.vfd_panel_standoff:
            problems.append(
                f"brain bay {s.bay_brain_d:.0f}mm deep cannot hold the VFD's "
                f"{s.vfd_box[1]:.0f}mm depth plus the {s.vfd_panel_standoff:.0f}mm "
                "standoff its vented face needs to the louvre. Panel venting does "
                "not remove the standoff, only Carbide's 300mm."
            )
    elif s.bay_brain_d < s.vfd_box[1] + s.vfd_vent_clear:
        problems.append(
            f"brain bay {s.bay_brain_d:.0f}mm deep cannot hold the VFD's "
            f"{s.vfd_box[1]:.0f}mm depth plus Carbide's {s.vfd_vent_clear:.0f}mm "
            "ventilation clearance. Either the bay grows, the VFD vents to open air "
            "through the panel, or the clearance is knowingly traded down."
        )

    if s.bay_brain_d < s.mini_pc_env[1]:
        problems.append(
            f"brain bay {s.bay_brain_d:.0f}mm is shallower than the mini PC's "
            f"{s.mini_pc_env[1]:.0f}mm"
        )

    if s.bay_lungs_w < s.extractor_env[1]:
        problems.append(
            f"lungs bay {s.bay_lungs_w:.0f}mm is narrower than the extractor's "
            f"{s.extractor_env[1]:.0f}mm, before lining and slides"
        )

    if not on_grid(s.stock_module):
        problems.append(f"stock module {s.stock_module}mm is off the {GRID}mm grid")

    if not on_grid(s.t_slot_pitch):
        problems.append(
            f"machine T-slot pitch {s.t_slot_pitch}mm is off the {GRID}mm bench grid. "
            "Not fixable: it is the machine. Jigs that cross from bench to bed carry "
            "the conversion, and the station rack stays on the bench grid."
        )

    if max(s.sheet_slot) > min(s.travel_x, s.travel_y):
        problems.append(
            f"a HALF blank {max(s.sheet_slot):.0f}mm does not fit the machine's "
            f"{min(s.travel_x, s.travel_y):.0f}mm travel"
        )

    if s.sheet_slot[1] > s.clear_h_min:
        problems.append(
            "a HALF blank will not stand on edge under the table. "
            "The station rack holds ready-use stock only."
        )

    # Catalog capture (C00): one MEASURE note per value the datasheets and
    # listings do not state. Each clears when its None becomes a number.
    for name in catalog_measure():
        hint = CATALOG_MEASURE_HINTS.get(name, "")
        problems.append(
            f"catalog {name} is None, MEASURE THIS. {hint} CONFIDENCE reads "
            f"{CONFIDENCE.get(name, CONFIDENCE.get(name.split('.')[0]))}; "
            "see SOURCES."
        )

    return problems


def check_earthing(s: Station = STATION) -> list[str]:
    """Whether the static path is specified well enough to wire.

    None of this is geometry, so none of it can be caught by an interference
    check. It is here because the failure it prevents does not look electrical
    when it arrives: it looks like a false limit switch, a lost step, or a job
    that dies two hours in for no reason anybody can reproduce.
    """
    problems: list[str] = []

    if not s.hose_antistatic:
        problems.append(
            "the extraction hose is not antistatic. Dry MDF dust through smooth "
            "plastic at the velocities this station runs is the biggest charge "
            "generator in the room, and the discharge lands beside the motion "
            "controller. There is no version of this build where that is a "
            "saving."
        )

    if s.bond_clip_pitch <= 0 or s.bond_clip_pitch > 500:
        problems.append(
            f"bond lead clip pitch {s.bond_clip_pitch:.0f}mm. A lead that is only "
            "held at its ends is a lead that gets caught by the gantry."
        )

    # The build instructions the geometry cannot enforce. STANDING by design:
    # they never clear, they just have to stay visible until commissioning.
    problems.append(
        "EARTH BONDING, standing note. One star point: "
        f"{s.bond_star_point}. Everything metal lands there and nowhere else. "
        "On the bar: " + "; ".join(s.bond_targets) + ". Never on the bar: "
        + "; ".join(s.bond_excluded) + ". A second earth reference is a ground "
        "loop, and the loop's return path is the thing that upsets the "
        "controller. This note never clears."
    )

    problems.append(
        "PE IS NEVER SWITCHED, standing note. The contactor drops line and "
        "neutral on the VFD, the extractor and the mast. It must not break "
        "protective earth on any of them, or opening the rear panel removes the "
        "static path at the same moment it exposes the machine. Earth continuity "
        "survives the interlock by construction."
    )

    problems.append(
        "ANODIZE IS AN INSULATOR, standing note. The mast extrusion and the "
        "machine's own frame are anodized aluminium, so a bonding screw driven "
        "into a clean-looking face may read open. Use a serrated star washer "
        "under every bonding lug and bite through the coating; the backing "
        "washer is not optional. Verify with a meter, not by looking at it."
    )

    problems.append(
        f"BOND CONTINUITY, MEASURE THIS at commissioning. Hose cuff at the dust "
        f"boot to {s.bond_star_point}, target under {s.bond_max_ohm:.1f} ohm, and "
        "write the reading down rather than recording a pass. That figure is a "
        "bonding convention, not a Festool specification. Re-check it after any "
        "hose or boot change, because a swapped hose is the commonest way a "
        "working station quietly stops being earthed."
    )

    return problems


if __name__ == "__main__":
    s = STATION
    print(f"fitted:  {s.spec['name']}  {s.extractor_env[0]:.0f} x "
          f"{s.extractor_env[1]:.0f} x {s.extractor_env[2]:.0f}")
    print(f"lungs bay {s.bay_lungs_w:.0f}mm clear")
    print(
        f"ceiling {s.clear_h_min:.1f} at the leg faces, {s.z_beam:.1f} at the beam; "
        f"full height only over x {s.gusset_x_intrude:.1f}.."
        f"{s.leg_x_inner - s.gusset_x_intrude:.1f}  y {s.gusset_y_intrude:.1f}.."
        f"{s.leg_y_inner - s.gusset_y_intrude:.1f}"
    )

    found = check(s)
    if found:
        print(f"\n{len(found)} constraint note(s):")
        for p in found:
            print(f"  - {p}")
    else:
        print("\nno constraint violations")
