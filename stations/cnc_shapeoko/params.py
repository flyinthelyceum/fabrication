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
    "leg_wall_t": "https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "leg_mount_pitch": "https://community.carbide3d.com/t/leg-kit-center-to-center-spacing-and-hole-diameter/105167",
    "leg_mount_hole_d": "https://community.carbide3d.com/t/leg-kit-center-to-center-spacing-and-hole-diameter/105167",
    "leg_x_inner": "MEASURED 2026-09-02, tape. Was 1100 scaled off a photograph.",
    "leg_y_inner": "MEASURED 2026-09-02, tape. Was 1150 scaled off a photograph.",
    "leg_splay": "UNSOURCED. Carbide publishes no leg geometry at all.",
    "clear_h_min": "MEASURED 2026-09-02, tape, floor to the lowest obstruction.",
    "gusset_x": "MEASURED 2026-09-02, tape plus a hand-dimensioned elevation.",
    "gusset_y": "MEASURED 2026-09-02, tape plus a hand-dimensioned elevation.",
    "gusset_plate_t": "MEASURED 2026-09-02. Photographs and calipers: the "
                       "gussets are flat plates, not solids, no thicker than "
                       "1/4in (6.35mm).",
    "z_beam": "DERIVED from clear_h_min + gusset_y_h. See check(); confirm it.",
    "extractor_env": "See EXTRACTORS. Each entry carries its own festoolusa URL.",
    "hose_id": "https://carbide3d.com/hub/docs/sweepy-pro-s5-pro/",
    "hose_bend_mult": "UNSOURCED ASSUMPTION. No maker publishes a bend radius for D36/32.",
    "vfd_box": "MEASURED 2026-09-02, calipers. Carbide publishes nothing.",
    "vfd_fan": "MEASURED 2026-09-02, calipers, two square fans on the left face.",
    "vfd_vent_clear": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "vfd_mount_pitch": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "mini_pc_env": "https://download.intel.com/newsroom/2023/client-computing/Intel-NUC-13-Pro-Tech-Product-Spec.pdf",
}

# ---------------------------------------------------------------- extractors
#
# The station is built around ONE of these and has to be able to grow into the
# other. Jared ordered the CT 15 HEPA; the CT 36 EI is the v2 growth path.
#
# THIS TABLE IS WHY THE REGISTRY EXISTS. The brief carried an envelope tagged
# "CT48 E" that was in fact the CT 36's to within 4mm on height, and a real CT 48
# has never stood under this frame in any version of the design. Envelopes and
# bag part numbers are per size and do not interchange, so both live on the same
# row as the name and neither can drift away from it again.
#
#   CT 15      457 x 308 x 429    15 L    130 CFM   fitted, CALIPERED
#              (the spec table's 470 x 320 x 435 also had W and D the wrong way
#               round, which is why the row below is now the caliper's)
#   CT 26 EI   630 x 365 x 540    26 L              would also fit
#   CT 36 EI   630 x 365 x 596    36 L              the growth path
#   CT 48 EI   740 x 406 x 1005   48 L              will not fit, ever
#
EXTRACTORS = {
    "CT15": {
        "name": "Festool CT 15 HEPA CLEANTEC",
        "env": (457.2, 307.975, 428.625),   # CALIPERED 2026-09-02. Supersedes the
                                        # festoolusa spec table's 470 x 320 x 435,
                                        # which was also transposed in W and D.
        "capacity_l": 15,
        "airflow_cfm": 130.0,           # festoolusa: "130 CFM (3 700 l/min)"
        "bag": "Festool SC-FIS-CT MINI/MIDI-2/5/CT15, part 204308",
        "url": "https://www.festoolusa.com/products/dust-extractors/dust-extractors-for-cleaning/578441---ct-15-hepa-us",
    },
    "CT36EI": {
        "name": "Festool CT 36 EI HEPA CLEANTEC",
        "env": (630.0, 365.0, 596.0),   # festoolusa spec table. Height is body
                                        # only; the carry handle is not in it.
        "capacity_l": 36,
        "airflow_cfm": None,            # not read off the spec table yet
        "bag": "Festool SC FIS-CT 36/5, part 496186",
        "url": "https://www.festoolusa.com/products/dust-extractors/workshop-dust-extractors/577872---ct-36-ei-hepa-us",
    },
}

MAIN_FILTER = "Festool HEPA-HF-CT 26/36/48 PTFE, part 205412"
"""One filter covers the 26, 36 and 48. It does NOT cover the CT 15, whose main
filter has not been read off a spec table yet. Tagged so the gap is visible when
the consumable line gets ordered."""

# Confidence tags carried from the brief's parameter table, so a reader of the
# model knows which numbers are load-bearing guesses.
CONFIDENCE = {
    "table_h": "measured",   # 2026-09-02: levelling feet ARE on the machine, so
                             # it is Carbide's 945 config and not the 893 one.
    "clear_h_min": "measured",   # floor to the LOWEST obstruction, which is the
                             # bottom of a Y gusset. The floor of the envelope.
    "z_beam": "derived",     # clear_h_min + gusset_y_h, NOT a tape reading.
                             # params.check() carries the note that says so.
    "gusset_x": "measured",  # both X gussets, height, top band and clear span
    "gusset_y": "measured",  # both Y gussets, plus the inner block
    "gusset_plate_t": "measured",   # 2026-09-02 photographs and calipers:
                             # flat plate, <= 1/4in. Which LEG each plate sits
                             # at is still an assumption; see check().
    "leg_x_inner": "measured",   # 2026-09-02 tape, was 1100 off a photograph
    "leg_y_inner": "measured",   # same tape
    "leg_splay": "low",      # visible in the leg-kit render
    "vfd_box": "measured",   # 2026-09-02 calipers
    "vfd_fan": "measured",   # 2026-09-02 calipers, two square fans, left face
    "extractor_env": "high",     # festoolusa spec table for whichever row is
                                 # selected; the CT 15 row is calipered instead
    "vfd_panel_standoff": "assumption",     # see the field. A traded clearance.
    "vfd_louvre_free_ratio": "assumption",  # nobody publishes one
    "lungs_lining_t": "medium",  # MLV plus open-cell foam, lay-up not yet bought
    "lungs_slide_t": "high",     # Accuride 3832 class member section
    "lungs_side_clear": "medium",   # a hand's clearance, chosen not sourced
    "footprint_x": "high",       # carbide3d spec table
    "footprint_y": "high",       # carbide3d spec table
    "footprint_z": "medium",     # live spec 23.25in, older forum quotes of the same field 21in
    "travel_x": "high",          # carbide3d spec table
    "travel_y": "high",          # carbide3d spec table
    "t_slot_pitch": "high",      # carbide3d spec table
    "table_h_no_feet": "high",   # carbide leg kit page
    "table_h_with_feet": "high", # carbide leg kit page
    "leg_wall_t": "high",        # 10-gauge powder-coated steel, carbide leg kit page
    "leg_mount_pitch": "medium", # Carbide staff reply on the forum, not a spec sheet
    "leg_mount_hole_d": "medium",# same reply
    "hose_id": "high",           # carbide sweepy pro doc, 35/36mm
    "hose_bend_mult": "assumption",  # nobody publishes one. Flagged, not sourced.
    "vfd_vent_clear": "high",    # carbide 65mm spindle doc, 30cm
    "vfd_mount_pitch": "high",   # carbide 65mm spindle doc
    "mini_pc_env": "medium",     # NUC 13 Pro tall chassis, as the class of thing
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
# What is still NOT measured: how many plates there are. The hand elevations
# are one gusset per side per axis -- four drawings. The table has four legs.
# ``Station.gussets`` ASSUMES each leg carries two plates, one bracing X and
# one bracing Y, which is EIGHT plates, not four. ``check()`` carries the note
# asking Jared to confirm it on the machine; see the docstring on
# ``Station.gussets`` for the arrangement this model commits to in the
# meantime.
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


@dataclass(frozen=True)
class Station:
    # ---- machine envelope -------------------------------------------------
    table_h: float = 945.0          # MEASURED 2026-09-02. Levelling feet ARE on the
                                    # machine, so this is Carbide's 945 config. The
                                    # brief's 889 was an exact 35in conversion of a
                                    # number that was never the right config.
    clear_h_min: float = 654.05     # MEASURED 2026-09-02, 25-3/4 in, floor to the
                                    # LOWEST obstruction under the frame, which is
                                    # the bottom of a Y gusset. This is the FLOOR of
                                    # the clearance envelope and not the envelope:
                                    # anything whose footprint is smaller than the
                                    # leg opening asks clear_z(x, y) instead.
    leg_x_inner: float = 1254.125   # MEASURED 2026-09-02, 49-3/8 in, inside faces of
                                    # the legs, left to right. Was 1100 scaled off the
                                    # leg-kit photo, so the model gained 154mm here.
    leg_y_inner: float = 1089.025   # MEASURED 2026-09-02, 42-7/8 in, inside faces,
                                    # front to back. Was 1150, so it lost 61mm.
    leg_splay: float = 6.0          # degrees

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
    leg_wall_t: float = 3.4         # 10-gauge steel, carbide leg kit page.
                                    # Anything bolted to a leg gets a backing washer.
    leg_mount_pitch: tuple[float, float] = (40.0, 65.0)   # carbide staff, forum 105167.
                                    # 65 is off the 20mm grid: a bolt-through plate
                                    # cannot be grid-indexed on both axes.
    leg_mount_hole_d: float = 7.0   # thru for M6, same source

    # ---- extractor selection ----------------------------------------------
    extractor: str = "CT15"
    """The unit that was ORDERED and that v1 is built around."""

    extractor_growth: str = "CT36EI"
    """The unit v2 has to accept without a redesign. Everything expensive to
    change is sized for this one; only the lungs/stock divider, the stock rack
    and the slide member are sized for the fitted unit. See check_growth_path."""

    # ---- bays -------------------------------------------------------------
    bay_brain_d: float = 250.0      # rear band, full width
    bay_stock_w: float = 220.0      # DEAD ESTIMATE. Stock is the remainder and
                                    # Datums.stock_clear_w is the real number;
                                    # this is kept only so check() can report
                                    # how far the brief's arithmetic was out.
    bay_hands_w: float = 400.0      # drawer width

    # ---- lungs bay allowance ----------------------------------------------
    # bay_lungs_w is DERIVED from these and the fitted extractor. It used to be a
    # 480 literal sized around a CT 48 that was really a CT 36, which left 66mm
    # of slack nothing had named. Naming the three allowances means the bay
    # resizes correctly when the extractor changes instead of keeping a cushion
    # whose size nobody could account for.
    lungs_lining_t: float = 12.0    # MLV plus open-cell foam, bonded, per side
    lungs_slide_t: float = 12.7     # slide member plus its clearance, per side
    lungs_side_clear: float = 20.0  # hand clearance, carriage to lining, per side

    # ---- components -------------------------------------------------------
    vfd_box: tuple[float, float, float] = (142.875, 184.15, 320.675)   # vertical.
                                    # CALIPERED 2026-09-02, w x d x h. Supersedes the
                                    # brief's 200 x 130 x 300 guess and the forum's
                                    # 152 x 178 x 260. Narrower and deeper than both.
    vfd_fan: float = 84.1375        # CALIPERED 2026-09-02. Square fan aperture.
    vfd_fan_count: int = 2          # both on the vented LEFT face
    vfd_vent_clear: float = 300.0   # carbide 65mm spindle doc, 30cm from the vented
                                    # (left) face to any obstruction
    vfd_mount_pitch: float = 85.0   # two slotted wall-mount holes, carbide spindle doc

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

    mini_pc_env: tuple[float, float, float] = (117.0, 112.0, 54.0)   # NUC 13 Pro tall

    # ---- sheet goods ------------------------------------------------------
    carcass_t: float = CARCASS_T
    panel_t: float = PANEL_T
    stock_module: float = STOCK_MODULE
    sheet_slot: tuple[float, float] = (600.0, 600.0)   # HALF blank on edge
    sheet_pitch: float = 20.0                          # slot spacing in the rack
    laser_blank: tuple[float, float] = QUARTER

    # ---- extraction -------------------------------------------------------
    hose_id: float = 36.0           # antistatic, the run to the boot.
                                    # Confirmed: carbide sweepy pro takes 35/36mm.
    hose_bend_mult: float = 4.0     # ASSUMPTION, not a spec. No manufacturer publishes
                                    # a bend radius for the D36/32 hose family, so the
                                    # model uses a multiple of hose diameter.
    overrun_s: int = 12             # hose clear time after the spindle drops
    cyclone: bool = False           # struck 2026-09-01. All internal, no external port.

    def front_bays(self) -> float:
        """Sum of the three front bay widths."""
        return self.bay_lungs_w + self.bay_stock_w + self.bay_hands_w

    def slack(self) -> float:
        """Millimetres left over across the front. The brief's warning is that
        this is currently zero against an estimated leg_x_inner."""
        return self.leg_x_inner - self.front_bays()

    def front_bay_d(self) -> float:
        """Usable depth of a front bay: the leg opening less the rear brain band
        and the panel that divides them."""
        return self.leg_y_inner - self.bay_brain_d - self.carcass_t

    def hose_bend_r(self) -> float:
        """Working bend radius for the extraction hose. An assumption, derived so
        that it moves when hose_id moves."""
        return self.hose_id * self.hose_bend_mult

    def stock_capacity(self) -> int:
        """HALF blanks the station rack holds on edge."""
        return int(self.bay_stock_w // self.sheet_pitch)

    # ---- the fitted extractor, and the one v2 has to accept ---------------

    @property
    def spec(self) -> dict:
        """The EXTRACTORS row for the unit that is actually going in."""
        return EXTRACTORS[self.extractor]

    @property
    def growth_spec(self) -> dict:
        """The EXTRACTORS row v2 has to accept without a redesign."""
        return EXTRACTORS[self.extractor_growth]

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
        return {"filter_bag": self.spec["bag"], "main_filter": MAIN_FILTER}

    # ---- lungs bay width, derived rather than estimated -------------------

    def lungs_allowance(self) -> float:
        """Total width the bay spends on everything that is not the extractor:
        acoustic lining, slide member and hand clearance, both sides."""
        return 2 * (self.lungs_lining_t + self.lungs_slide_t + self.lungs_side_clear)

    def lungs_w_for(self, key: str) -> float:
        """Clear lungs width that housing EXTRACTORS[key] needs, on the grid.

        Snapped UP: the bay is allowed to be generous, never short. This is the
        one bay dimension the fitted unit sets, which is what makes the growth
        path a divider move rather than a rebuild."""
        need = EXTRACTORS[key]["env"][1] + self.lungs_allowance()
        return _snap_up(need)

    @property
    def bay_lungs_w(self) -> float:
        """Clear width of the lungs bay, set by the FITTED extractor."""
        return self.lungs_w_for(self.extractor)

    @property
    def bay_lungs_w_growth(self) -> float:
        """What the lungs bay becomes under the growth extractor. The difference
        between this and bay_lungs_w is the whole cost of the conversion, and it
        comes out of stock."""
        return self.lungs_w_for(self.extractor_growth)

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
    def z_beam(self) -> float:
        """Underside of the machine's frame beam, the absolute ceiling.

        DERIVED, NOT MEASURED. The tape read the floor to the LOWEST obstruction,
        which is the bottom of a Y gusset, so the beam is that plus the Y
        gusset's own height. ``check()`` carries the note, and the note stays up
        because the implied beam thickness is thin enough to be worth a second
        tape reading."""
        return self.clear_h_min + self.gusset_y_h

    @property
    def gussets(self) -> tuple[Gusset, ...]:
        """Eight of them, in station coordinates: one per leg per axis.

        Each of the four measured profiles (X left, X right, Y front, Y rear)
        is now a plate, ``gusset_plate_t`` thick, at ONE end of the axis it does
        not brace -- not a solid run to the far wall. Which leg was not
        measured directly: Jared's elevations are one gusset per side per axis,
        four drawings, and the table has four legs. This ASSUMES each leg
        carries two plates, one bracing X and one bracing Y, so every measured
        profile is placed twice, once per leg on the axis it does not
        constrain -- eight plates, not four. ``check()`` carries the note
        asking Jared to confirm it on the machine.
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

    if s.slack() < 0:
        problems.append(
            f"front bays overflow the leg opening by {-s.slack():.0f}mm "
            f"({s.front_bays():.0f} into {s.leg_x_inner:.0f}). "
            "Stock is the bay that gives; the room's wall rack absorbs it."
        )
    elif s.slack() == 0:
        problems.append(
            "front bays sum to leg_x_inner with zero slack. This is the brief's "
            "open item: one tape measurement between the inside faces of the legs."
        )

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

    problems.append(
        f"z_beam {s.z_beam:.2f}mm is DERIVED and not measured. The tape read "
        f"{s.clear_h_min:.2f}mm from the floor to the LOWEST obstruction, which "
        f"is the bottom of a Y gusset, and the gusset's own {s.gusset_y_h:.1f}mm "
        f"was added to it. That implies a frame beam {s.table_h - s.z_beam:.2f}mm "
        "thick, which is thin for a member carrying a gantry. Measure floor to "
        "the UNDERSIDE OF THE FRAME BEAM directly and write the answer into "
        "z_beam. Everything above the gussets moves with it."
    )

    problems.append(
        "each gusset's extent along the axis it does NOT constrain is now "
        f"measured: it is a flat plate, {s.gusset_plate_t:.2f}mm thick "
        "(photographs and calipers, 2026-09-02), at the leg it braces, not the "
        "wall-to-wall solid the first pass modelled for want of that "
        "measurement. Which leg was not measured directly: the hand elevations "
        "are one gusset per side per axis, four drawings, and the table has "
        "four legs, so this model ASSUMES each leg carries two plates, one "
        "bracing X and one bracing Y -- eight plates, not four. Confirm on the "
        "machine whether every leg really carries its own pair before this "
        "clears. Unrelated and still open: the intrusion depth stays solid "
        f"from the leg face rather than only the {s.gusset_y_block[0]:.1f} x "
        f"{s.gusset_y_block[1]:.1f}mm block at a Y gusset's inner end, which if "
        "true opens the envelope further than this model says."
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

    return problems


def check_growth_path(s: Station = STATION) -> list[str]:
    """Can the station still take the growth extractor without a redesign.

    The promise made on 2026-09-02 is that swapping a CT 15 for a CT 36 costs a
    divider move and a slide member, not a new carcass. That promise is only
    worth anything if it is tested, so this asserts every dimension that would
    be EXPENSIVE to revisit against the growth unit, not the fitted one.

    Anything this reports is a dimension where the growth path has quietly been
    lost and the model is still claiming it.
    """
    g = s.growth_spec
    env = g["env"]
    problems: list[str] = []

    if env[0] > s.front_bay_d():
        problems.append(
            f"GROWTH LOST: {g['name']} is {env[0]:.0f}mm long into a "
            f"{s.front_bay_d():.0f}mm front bay. Bay depth is expensive to change, "
            "so this has to be sized for the growth unit from the start."
        )

    if env[2] > s.clear_h_min:
        problems.append(
            f"GROWTH LOST: {g['name']} is {env[2]:.0f}mm tall into "
            f"{s.clear_h_min:.0f}mm of clearance under the frame. No divider move "
            "recovers this."
        )

    if s.clear_h_min - env[2] < s.hose_bend_r():
        problems.append(
            f"GROWTH LOST: {s.clear_h_min - env[2]:.0f}mm of headroom over "
            f"{g['name']} against a {s.hose_bend_r():.0f}mm hose bend radius"
        )

    grow_w = s.bay_lungs_w_growth
    if grow_w + s.bay_hands_w >= s.leg_x_inner:
        problems.append(
            f"GROWTH LOST: lungs {grow_w:.0f}mm plus hands {s.bay_hands_w:.0f}mm "
            f"leaves nothing for stock inside {s.leg_x_inner:.0f}mm"
        )

    return problems


def conversion_steps(s: Station = STATION) -> list[str]:
    """The named cost of going from the fitted extractor to the growth one.

    If this list ever grows past a divider, a rack and a slide member, the
    growth path has stopped being cheap and the claim in the brief is stale.
    """
    delta = s.bay_lungs_w_growth - s.bay_lungs_w
    return [
        f"set extractor = {s.extractor_growth!r} in params. One line.",
        f"move the lungs/stock divider {delta:.0f}mm right, into the second dado "
        "station already cut in the deck and the top cap. Lift the birch spline "
        "out of it and drop it into the vacated one.",
        f"recut the stock rack: it loses {delta:.0f}mm of width and the blanks "
        "it holds drop accordingly.",
        f"swap the lungs slide member for one no taller than the growth stack "
        "allows, and change the bag to " + s.growth_spec["bag"] + ".",
    ]


if __name__ == "__main__":
    s = STATION
    print(f"fitted:  {s.spec['name']}  {s.extractor_env[0]:.0f} x "
          f"{s.extractor_env[1]:.0f} x {s.extractor_env[2]:.0f}")
    print(f"growth:  {s.growth_spec['name']}  lungs bay would go "
          f"{s.bay_lungs_w:.0f} -> {s.bay_lungs_w_growth:.0f}mm")
    print(f"front bays {s.front_bays():.0f}mm into {s.leg_x_inner:.0f}mm, "
          f"slack {s.slack():.0f}mm")
    print(f"station rack holds {s.stock_capacity()} HALF blanks on edge")
    print(
        f"ceiling {s.clear_h_min:.1f} at the leg faces, {s.z_beam:.1f} at the beam; "
        f"full height only over x {s.gusset_x_intrude:.1f}.."
        f"{s.leg_x_inner - s.gusset_x_intrude:.1f}  y {s.gusset_y_intrude:.1f}.."
        f"{s.leg_y_inner - s.gusset_y_intrude:.1f}"
    )

    grown = check_growth_path(s)
    if grown:
        print(f"\n{len(grown)} GROWTH PATH failure(s):")
        for p in grown:
            print(f"  - {p}")
    else:
        print("\ngrowth path intact. Conversion to the CT 36:")
        for i, step in enumerate(conversion_steps(s), 1):
            print(f"  {i}. {step}")

    found = check(s)
    if found:
        print(f"\n{len(found)} constraint note(s):")
        for p in found:
            print(f"  - {p}")
    else:
        print("\nno constraint violations")
