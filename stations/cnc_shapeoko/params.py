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
                  "covered the pitch and the hole diameter only. Still open: the "
                  "angle's flange width, LegHoles.flange_w.",
    "leg_x_inner": "MEASURED 2026-09-02, tape. Was 1100 scaled off a photograph.",
    "leg_y_inner": "MEASURED 2026-09-02, tape. Was 1150 scaled off a photograph.",
    "leg_splay": "Jared, 2026-09-02: the legs are square. The 6 deg was an "
                 "eyeball off a render, never measured.",
    "clear_h_min": "MEASURED 2026-09-02, tape, floor to the lowest obstruction.",
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
    "vfd_fan": "MEASURED 2026-09-02, calipers, two square fans on the left face.",
    "vfd_vent_clear": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "vfd_mount_pitch": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "mini_pc_env": "https://download.intel.com/newsroom/2023/client-computing/Intel-NUC-13-Pro-Tech-Product-Spec.pdf",
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
    "extractor_env": "high",     # festoolusa spec table for whichever row is
                                 # selected; the CT 15 row is calipered instead
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

    edge_off: float = 22.86
    """MEASURED 2026-09-03, calipers, 0.9in. First column, measured from the
    leg's INNER edge INTO the opening.

    From that edge and not from the leg's outer face, for two reasons. The inner
    edge is the datum: the station origin sits on the intersection of the left
    and front leg inner faces. And it is the edge the two materials share -- the
    end wall's birch runs from it inward and the leg's steel runs from it
    outward, so the only place a bolt can have steel in front of it AND birch
    behind it is where the leg's face reaches back across that edge into the
    opening. 22.86mm (0.9in) asserts the leg reaches at least ``span_h`` in.
    ``leg_joint.check_leg_joint`` states that assumption against the measured
    value; it is no longer a placeholder but the leg's own reach past its inner
    corner is still what determines whether this overlap is real -- see
    ``walls_in_path``, still unmeasured."""

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

    flange_w: float | None = None
    """UNMEASURED. Width of the angle's bolt-bearing flange, from the leg's inner
    corner outward, in the same in-face direction ``edge_off`` runs.

    This is the ONE number still open on the leg. The holes prove the flange
    reaches at least far enough to contain them -- the outer column sits 62.99mm
    off the corner and its own hole wants 3.30mm more, so 66.29mm is proven by
    the pattern's own existence. What is NOT proven is whether the flange runs
    far enough past the outer hole for the joint check's full reach. ``None``
    keeps ``check_leg_joint`` reporting the gap; a number closes it or fails it
    outright."""

    def columns_h(self) -> tuple[float, ...]:
        """Column offsets in from the leg's inner edge, at ``pitch_h``."""
        return tuple(self.edge_off + i * self.pitch_h for i in range(self.cols_per_leg))

    @property
    def count_per_leg(self) -> int:
        return len(self.rows_z) * self.cols_per_leg

    @property
    def span_h(self) -> float:
        """How far into the opening the last column reaches."""
        cols = self.columns_h()
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
                                    # the bottom of a Y gusset. This is the FLOOR of
                                    # the clearance envelope and not the envelope:
                                    # anything whose footprint is smaller than the
                                    # leg opening asks clear_z(x, y) instead.
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
    leg_wall_t: float = 3.5179      # MEASURED 2026-09-03, calipers, 0.1385 in.
                                    # Carbide's leg kit page says 10-gauge (3.4mm);
                                    # the extra 0.12mm is powder coat on both faces,
                                    # which is the direction that does not matter.
                                    # Anything bolted to a leg gets a backing washer.
    leg_holes: LegHoles = LegHoles()
    """The leg's own bolt pattern, in one block. See LegHoles and check()."""

    # ---- extractor selection ----------------------------------------------
    extractor: str = "CT15"
    """The unit that was ORDERED and that v1 is built around."""

    extractor_growth: str = "CT15"
    """The unit v2 has to accept without a redesign.

    RULED by Jared 2026-09-03: "maximize the space we have and we'll live with
    what we must." This read CT36EI and that promise is WITHDRAWN. It was not
    given up to a choice in the carcass, it was taken by the tape: floor to the
    underside of the frame beam is 33-1/16in, not the 920.75mm the old derivation
    implied, and a CT 36 EI wants its 596mm body plus a 144mm hose bend under a
    ceiling 39mm short of carrying both. No divider move recovers a ceiling.

    Growth now equals fitted, so check_growth_path tests the CT 15 against its own
    bay and passes. The surrender is recorded as a standing note in check() so a
    passing gate is never read as the CT 36 still fitting."""

    # ---- bays -------------------------------------------------------------
    bay_brain_d: float = 250.0      # rear band, full width
    bay_stock_w: float = 220.0      # DEAD ESTIMATE. Stock is the remainder and
                                    # Datums.stock_clear_w is the real number;
                                    # this is kept only so check() can report
                                    # how far the brief's arithmetic was out.
    bay_hands_w: float = 400.0      # drawer width

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
    def growth_station_wanted(self) -> bool:
        """Whether a SECOND divider dado is a real station or a duplicate.

        False once growth equals fitted, which is where Jared's 2026-09-03 ruling
        left it. The deck and the top cap still subtract the growth groove, and
        that stays sound because the two positions coincide exactly and a boolean
        subtract of the same volume twice is one dado, not two. What is NOT sound
        is telling a reader there are two stations."""
        return self.extractor_growth != self.extractor

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

    if CONFIDENCE.get("z_beam") != "measured":
        problems.append(
            f"z_beam {s.z_beam:.2f}mm is DERIVED and not measured. The tape read "
            f"{s.clear_h_min:.2f}mm from the floor to the LOWEST obstruction, which "
            f"is the bottom of a Y gusset, and the gusset's own {s.gusset_y_h:.1f}mm "
            f"was added to it. That implies a frame beam {s.table_h - s.z_beam:.2f}mm "
            "thick, which is thin for a member carrying a gantry. Measure floor to "
            "the UNDERSIDE OF THE FRAME BEAM directly and write the answer into "
            "z_beam. Everything above the gussets moves with it."
        )

    if s.extractor_growth == s.extractor:
        problems.append(
            "EXTRACTOR GROWTH SURRENDERED, standing note. The station is sized "
            f"for the {EXTRACTORS[s.extractor]['name']} and for nothing "
            "larger. The "
            "CT 36 EI growth path was withdrawn by Jared 2026-09-03 after the "
            "measured z_beam left it 39mm short on hose-bend headroom, which no "
            "divider move recovers. This note never clears; it is here so a "
            "passing growth check is never read as the CT 36 EI still fitting. "
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


def check_growth_path(
    s: Station = STATION,
    bay_x: tuple[float, float] | None = None,
    bay_y: tuple[float, float] | None = None,
) -> list[str]:
    """Can the station still take the growth extractor without a redesign.

    The promise made on 2026-09-02 is that swapping a CT 15 for a CT 36 costs a
    divider move and a slide member, not a new carcass. That promise is only
    worth anything if it is tested, so this asserts every dimension that would
    be EXPENSIVE to revisit against the growth unit, not the fitted one.

    Anything this reports is a dimension where the growth path has quietly been
    lost and the model is still claiming it.

    ``bay_x``/``bay_y`` are the growth lungs bay's own footprint, in station
    coordinates -- carcass.py owns that geometry, not this module, so a caller
    with a ``Datums`` passes it in. Without it this falls back to
    ``clear_h_min``, the worst ceiling anywhere, which is what this function
    used before the gussets became an envelope rather than a scalar and is
    still correct, just pessimistic off-corner.
    """
    g = s.growth_spec
    env = g["env"]
    problems: list[str] = []
    ceiling = s.clear_z_over(bay_x, bay_y) if bay_x and bay_y else s.clear_h_min

    if env[0] > s.front_bay_d():
        problems.append(
            f"GROWTH LOST: {g['name']} is {env[0]:.0f}mm long into a "
            f"{s.front_bay_d():.0f}mm front bay. Bay depth is expensive to change, "
            "so this has to be sized for the growth unit from the start."
        )

    if env[2] > ceiling:
        problems.append(
            f"GROWTH LOST: {g['name']} is {env[2]:.0f}mm tall into "
            f"{ceiling:.0f}mm of clearance over its own bay. No divider move "
            "recovers this."
        )

    if ceiling - env[2] < s.hose_bend_r():
        problems.append(
            f"GROWTH LOST: {ceiling - env[2]:.0f}mm of headroom over "
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
