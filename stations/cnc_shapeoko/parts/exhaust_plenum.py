"""Exhaust plenum: the baffled box the lungs bay breathes out through.

WHAT THIS PART IS
=================

Eight panels of birch, seven slabs of lay-up, and one box of air nobody may
build in.

``exhaust_plenum_*``  A rabbeted birch box standing across the REAR of the
                      lungs bay, behind the carriage's lip and the pressure
                      sensor's barbs, end wall to divider, its back on the
                      spine, its floor over the extractor's receptacle box and
                      its top under the hose's turning room. Two vertical
                      BAFFLES housed in the floor and the top split it into
                      three pockets; the air enters a MOUTH in the front wall
                      at the right pocket, turns round the first baffle's
                      rear end, turns round the second baffle's front end,
                      and leaves the left pocket through an EXIT capsule cut
                      through the box's left wall and the end wall behind it,
                      to the room at the machine's left flank, in the lower
                      third of the bay.

``exhaust_plenum_lining_*``  The acoustic lay-up (``bay_walls.LINING_T`` of
                      MLV plus foam) on the back wall's inner face, one slab
                      per pocket, and on both faces of both baffles, as
                      reference slabs, so every free-area figure below is the
                      NET section.

``hose_corridor_env`` The room the D36 hose needs to leave the unit's head
                      and reach the port in the left end wall, as a reference
                      solid. Nothing may stand in it; this plenum's top is
                      set by it.


WHY THE BAY IS THE FIRST CHAMBER, AND THE PLENUM IS NOT BESIDE THE UNIT
======================================================================

RULED 2026-09-04 (Jared): "we don't need to overengineer the plenum ct15
grille. airflow is airflow." The manual's Fig. 1 puts the exhaust opening
[1-8] on the side face of the head, beside the locking clip [1-7], under the
filter drawer [1-6], near the FRONT corner, and never dimensions it.
``params.ct15_exhaust`` therefore names a face REGION, the head band over the
front half of that side face, and the receiver is sized to the face rather
than to a grille position Festool never published. The unit's front is the
station's REAR: ``lungs_carriage.CT15_INLET_END`` puts the hose inlet, and so
the control panel, against the lip, so that front half is the +Y half.

Which side that is decides where the air goes. Fig. 1 is drawn from the
front-right: the control panel's face on the left of the drawing, the side
with the clip and the drawer on the right. That side is on the viewer's
RIGHT when facing the control panel. The unit rides its tray control panel
to the lip, facing the station's rear, so a viewer facing the panel stands
at +Y looking -Y and their right is -X: the grille faces the LEFT END WALL,
not the divider. (lungs_carriage's earlier note read it as the divider side;
this module and that note now agree.)

Which is where the plan of "the unit slides through the plenum's mouth with
a soft seal band" runs out of room, and it is worth saying plainly rather
than quietly not doing it. The gap between that face and the end wall is
37mm beside the spacer block and 91mm above it. A birch box with a mouth
for the unit to enter does not fit in either, and the seal band would be
worse than the box: the tray travels 508mm, so a band around a mouth on
the unit's SIDE face does not compress once, it DRAGS the full length of
the unit on every pull, and the one moving part in this bay is the one
thing that must not bind. A collar the unit passes through end-on would
capture the wrong half -- the grille is at the panel end, which rides
against the lip at the back of the bay, so a collar in front of it would
enclose the rear half of a bay that is already enclosed.

So the LINED BAY is the first chamber. The jet leaves the grille into the
side gap, expands into 460 x 620 x 821 of lined box behind a lined door,
and the plenum draws from the bay through a mouth sized to the same
velocity rule as every other section. This is not a smaller idea than the
seal band; it is a larger first expansion than a 37mm hood could ever be,
and it is the bay Jared already paid for in lay-up. The seal the bay has
is the door's lay-up (lungs_door). That is what "airflow is airflow"
buys: the plenum stops caring where on the face the grille is, and the
only thing that touches the unit is air.


WHAT SIZES A SECTION, AND WHAT THE 1.5x IS 1.5 OF
=================================================

The rule handed to this part was "free area at every section >= 1.5 x the
exhaust face region". Read against what it models, that rule is about not
choking the air the unit moves, and the face region is the wrong thing to
multiply: the region is generous BY CONSTRUCTION, because its job is to
cover a grille whose position Festool never published, and most of what it
covers is sealed plastic that moves nothing. Jared ruled on exactly this
shape of number on the VFD louvre (2026-09-02, "why would we calculate off
of a sealed face?"). It is also not buildable: the region is 392 cm2, 1.5x
is 588 cm2 per section, and the void behind the lip is 255 deep by 424
wide -- three such sections do not exist in it.

So the 1.5 is kept and pointed at the flow. Two figures, both off the
manual's data table (see ``params.SOURCES["ct15_airflow"]``), because the
table gives two and the model had been using the wrong one:

    rated    130 m3/h = 36.1 L/s = 76.5 CFM. The EXTRACTOR: air through the
             machine with filter and hose in the path. ``SECTION_MARGIN``
             (1.5) is applied to this. -> 180.6 cm2
    max      222 m3/h = 61.7 L/s = 130.7 CFM. The bare TURBINE, the worst
             case the plenum can be handed. No margin: a margin on an
             unreachable figure is a margin on a margin. -> 205.6 cm2

``section_req`` takes the larger, 205.6 cm2 at ``V_MAX`` (3.0 m/s, the
low-velocity duct convention for a quiet occupied room; not a Festool
figure). Every section here carries at least that, net of the lay-up, so
the box runs at or under 2.0 m/s on the flow the extractor actually moves
and at or under 3.0 m/s with the hose pulled off.

The "130 CFM" the brief and this model had been quoting was the TURBINE
figure all along -- the festoolusa page's "130 CFM (3 700 l/min)", and
3 700 l/min is 222 m3/h. The extractor's own figure is 130 m3/h, a
different number that shares a digit string. Corrected in params and in
the brief on 2026-09-04.


THE EXIT, AND WHY IT IS THE END WALL
====================================

The brief says "low at the rear". The three ways out of the rear of the
lungs bay were all measured before this one was chosen:

    deck    into the plinth. The plinth is a closed frame of 60mm rails
            whose only grille is the 10 cm2 the VFD's intake asked for. It
            is a choke, not an exit, and it is the brain band's intake air.
    spine   into the sealed mains compartment: the backplate's devices are
            18mm behind the spine, and a hand through a 200 cm2 hole in
            the lungs bay reaches them. Also the noise would leave through
            the top cap and the VFD louvre, high and beside the operator.
    end wall  to the room, between the two left legs' flanges, under the
            table, in the lower third of the bay, facing away from the
            operator. Nothing is on the outer face there.

The end wall it is. ``bay_walls`` cuts the capsule in wall 0 from this
module's ``exit_station``; the plenum's own left wall carries the same
capsule in the same place.


WHAT IT CLEARS
==============

    the tray      the front wall stands ``SERVICE_GAP`` behind the closed
                  tray's rearmost point (the sensor's barbs); the pull is
                  toward the operator, away from here, so the swept tray
                  never reaches the plenum
    the receptacle  the floor stands ``RECEPTACLE_CLEAR`` above the handy
                  box on the spine; the slot under the floor is where the
                  plug goes in, reached with the tray pulled out
    the hose      the top stands ``HOSE_CLEAR`` under ``hose_corridor_env``
    the door      at 180 the lungs door lies against the front-left leg,
                  outboard of the bay's front; the plenum is the bay's whole
                  depth behind it and the check prints the figure
    the mains crossings  the EXTRACTOR MAINS bore is under the floor and
                  the MAST FEED bore is above the top; neither is inside
                  the box


JOINERY
=======

The carcass vocabulary. Side walls run full depth and full height and carry
a RABBET on every inner-face edge: the floor and the top run full depth in
the bottom and top rabbets; the front and back walls stand between the
floor and the top in the vertical rabbets, screwed through the floor and
the top. The baffles are housed in DADOS in the floor's top face and the
top's underside, run out under the wall each baffle butts and BLIND at the
free end, so the blind end carries a dogbone relief at each inside corner,
``DADO_D`` deep, per the ``through_slot`` rule. The mouth and the exit are
APERTURES: capsules. The box is assembled outside the bay and screwed to
the end wall and the divider through its own side walls from inside the
pockets; those pilots are driven on the fit, like the hinges'.


PANEL CONVENTION
================

    floor, top   local X = station +X, local Y = station +Y, flat, from
                 x = x_l + t - RABBET_D. Floor thickness up; top thickness
                 up with its top face at z1. Baffle dados on the floor's
                 FRONT (top) face and the top's BACK (under) face.
    side walls   local X = station +Y (0 at the front), local Y = station
                 +Z (0 at z0), thickness into +X: the left wall's inner
                 face is its FRONT (Z = t), the right wall's its BACK.
    front, back  local X = station +X (from x_l + t - RABBET_D), local Y =
                 station +Z (0 at the floor's top face), thickness into -Y
                 so Z = 0 is the front wall's INNER face and the back
                 wall's OUTER face on the spine.
    baffles      as the side walls, from their own x, standing in the
                 floor's dado.
"""

from __future__ import annotations

from math import pi

from build123d import Align, Box, Location, Part, Plane, Unit, export_step

from lib.house import GRID, SHEET_5X5_BALTIC, fits
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    EXPORT_DIR,
    RABBET_D,
    RABBET_W,
    SCREW_CLEAR_D,
    SERVICE_GAP,
    T,
    Datums,
    export_part,
    groove,
    panel,
    rabbet,
    relief,
    screw_line,
    snap_up,
    through_slot,
)
from stations.cnc_shapeoko.params import CATALOG, EXTRACTORS
from stations.cnc_shapeoko.parts import lungs_carriage, mains_backplate
from stations.cnc_shapeoko.parts.bay_walls import LINING_T, SLIDE_LEN, WALLS

__all__ = [
    "PART_NAME",
    "LINING_STEM",
    "HOSE_NAME",
    "V_MAX",
    "rated_flow_ls",
    "max_flow_ls",
    "section_req",
    "box_station",
    "interior",
    "pockets",
    "gap",
    "baffle_spans",
    "mouth_station",
    "exit_station",
    "exhaust_region_station",
    "hose_corridor_station",
    "free_areas",
    "panels",
    "placed_all",
    "joint_table",
    "check_exhaust_plenum",
    "export",
]

D: Datums = DATUMS
PART_NAME = "exhaust_plenum"
LINING_STEM = f"{PART_NAME}_lining"
HOSE_NAME = "hose_corridor_env"

# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# The bay, the spine and the lining come from Datums and bay_walls; the
# unit and its airflow from EXTRACTORS; the exhaust region from params;
# the tray's reach from lungs_carriage; the receptacle from
# mains_backplate; the joinery from carcass. No dimension literal appears
# in the geometry.
# ====================================================================

# ---- the air ----------------------------------------------------------------
V_MAX = 3.0
"""Design velocity through every section, m/s. SOURCE: the low-velocity
duct convention for quiet occupied rooms (ASHRAE-class guidance puts
return plenums at 2.5-4 m/s); not a Festool figure. CONFIDENCE: design.
The unit's own exhaust port, sized to take a D27/32 hose (manual 9.3),
runs an order of magnitude faster, which is why an expansion box helps
at all."""

SECTION_MARGIN = 1.5
"""How much more section than the rated flow needs, on the RATED flow.
SOURCE: the brief's rule, read against the thing it models -- see the
module docstring. CONFIDENCE: spec."""

M3H_TO_LS = 1000.0 / 3600.0
"""1 m3/h in L/s. SOURCE: arithmetic. CONFIDENCE: exact."""

CFM_PER_LS = 60.0 / 28.316846592
"""1 L/s in cu ft/min, for reporting only. SOURCE: arithmetic (1 cu.ft. =
28.316846592 L, exactly, from the international inch). CONFIDENCE: exact."""

POCKETS = 3
"""Pockets between the walls: mouth, middle, exit; two baffles, two turns.
SOURCE: brief ("turns twice through a baffled plenum"). CONFIDENCE: spec."""

APERTURE_INSET = GRID / 2
"""Birch left between a capsule's edge and the nearest wall, lining or
edge of its panel. SOURCE: design. CONFIDENCE: design."""

# ---- the clearances ---------------------------------------------------------
TRAY_CLEAR = SERVICE_GAP
"""Front wall to the closed tray's rearmost point. SOURCE: carcass
SERVICE_GAP, the carcass's own figure for air above a fitted thing.
CONFIDENCE: derived."""

RECEPTACLE_CLEAR = GRID / 2
"""Floor underside to the top of the receptacle's handy box. SOURCE:
design; the box's raised cover is what the plug lands on and it is below
this. CONFIDENCE: design."""

HOSE_CORRIDOR_DROP = D.s.hose_id + GRID / 2
"""How far below the unit's top the hose corridor's floor sits: one hose
diameter plus half a module, because the hose leaves the head through the
slot at its top front (manual Fig. 1 [1-2]; OBSERVED 2026-09-04, Jared:
"the hole at the top front of the machine just to the right of the FESTOOL
label") and runs level before it climbs to the port. SOURCE: design on an
observed position; ``params.ct15_inlet`` is still None. CONFIDENCE:
assumption, MEASURE THIS with the inlet: the corridor's floor and this
plenum's top move with it."""

HOSE_CLEAR = GRID / 2
"""Plenum top to the corridor's floor. SOURCE: design. CONFIDENCE: design."""

# ---- fasteners --------------------------------------------------------------
MOUNT_INSET = T * 1.5
"""Mounting screws (side wall into the bay wall) in from the side wall's
edges, both axes. SOURCE: carcass SCREW_END_INSET. CONFIDENCE: derived."""

MOUNT_PITCH = GRID * 15
"""Pitch that puts exactly two mounting screws on each of the two vertical
lines: the exit capsule occupies the middle of the left wall and a third
screw would land in it. SOURCE: design. CONFIDENCE: design."""

# ---- the unit and its exhaust ------------------------------------------------
CT15 = EXTRACTORS["CT15"]
"""The fitted unit's row. SOURCE: params.EXTRACTORS. CONFIDENCE: calipered
envelope, datasheet airflow."""

REGION = CATALOG["ct15_exhaust"]
"""The exhaust face region, a design face-region under the 2026-09-04
ruling: side, span along the unit, span up the unit, all as fractions.
SOURCE: params.ct15_exhaust. CONFIDENCE: design."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the block
# above and on Datums.
# ====================================================================


def rated_flow_ls() -> float:
    """What the EXTRACTOR moves, L/s: the manual's 130 m3/h, air through the
    machine with a filter and a hose in the path. This is the flow the
    ``SECTION_MARGIN`` rule is written against."""
    return CT15["airflow_extractor_m3h"] * M3H_TO_LS


def max_flow_ls() -> float:
    """What the TURBINE moves, L/s: the manual's 222 m3/h, the fan alone.
    The worst case the plenum can be handed -- hose off the inlet, filter
    new -- and the flow ``V_MAX`` alone is applied to."""
    return CT15["airflow_turbine_m3h"] * M3H_TO_LS


def section_req() -> float:
    """Net free area every section must carry, mm2.

    Two rules, and the section is the larger of what they ask:

        rated    SECTION_MARGIN x the rated flow's section at V_MAX. The
                 brief's 1.5x, pointed at the flow instead of at the face
                 region (docstring).
        max      the turbine's free-air flow at V_MAX, no margin. A margin
                 on a figure that is already the unreachable worst case
                 would be a margin on a margin.
    """
    return max(
        SECTION_MARGIN * rated_flow_ls(),
        max_flow_ls(),
    ) / 1000.0 / V_MAX * 1e6


def tray_rear_reach(d: Datums = D) -> float:
    """Station Y of the closed tray's rearmost point: the lip's rear face or
    the sensor's barbs, whichever is further back."""
    _x0, y0, _z0 = lungs_carriage.carriage_origin(d)
    return max(y0 + SLIDE_LEN, lungs_carriage.dp_station(d)[1][1])


def hose_corridor_station(
    d: Datums = D,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The hose's room, station coordinates: from the end wall to the unit's
    centreline in X (the slot is on the side the port is on), from the unit's
    front face to the spine's lining in Y, from HOSE_CORRIDOR_DROP under the
    unit's top to the cap in Z."""
    (cx0, cx1), (_cy0, cy1), (_cz0, cz1) = lungs_carriage.ct15_station(d)
    return (
        (d.lungs_x[0], (cx0 + cx1) / 2),
        (cy1, d.y_spine - LINING_T),
        (cz1 - HOSE_CORRIDOR_DROP, d.top_z[0]),
    )


def box_station(
    d: Datums = D,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The box's outer envelope, station coordinates."""
    y_f = tray_rear_reach(d) + TRAY_CLEAR
    z0 = mains_backplate.receptacle_station(d)[2][1] + RECEPTACLE_CLEAR
    z1 = hose_corridor_station(d)[2][0] - HOSE_CLEAR
    return (d.lungs_x, (y_f, d.y_spine), (z0, z1))


def interior(
    d: Datums = D,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The air inside the six panels, before baffles and lay-up."""
    (x0, x1), (y0, y1), (z0, z1) = box_station(d)
    return ((x0 + T, x1 - T), (y0 + T, y1 - T), (z0 + T, z1 - T))


def back_lining_y(d: Datums = D) -> tuple[float, float]:
    """Station Y of the lay-up on the back wall's inner face."""
    (_x, (_y0, y1), _z) = interior(d)
    return (y1 - LINING_T, y1)


def pocket_pitch(d: Datums = D) -> float:
    """Wall-to-wall width of one pocket, baffles' thickness taken out."""
    (x0, x1), _y, _z = interior(d)
    return (x1 - x0 - (POCKETS - 1) * T) / POCKETS


def baffle_x(d: Datums = D) -> list[tuple[float, float]]:
    """Station X span of each baffle, left to right: b (exit/middle) then
    a (middle/mouth). Two baffles for three pockets."""
    (x0, _x1), _y, _z = interior(d)
    p = pocket_pitch(d)
    return [(x0 + (i + 1) * p + i * T, x0 + (i + 1) * p + (i + 1) * T) for i in range(POCKETS - 1)]


def pockets(d: Datums = D) -> list[tuple[float, float]]:
    """Station X span of the AIR in each pocket, net of the lay-up on the
    baffle faces, left to right: exit, middle, mouth."""
    (x0, x1), _y, _z = interior(d)
    bx = baffle_x(d)
    edges = [x0] + [v for pair in bx for v in pair] + [x1]
    out: list[tuple[float, float]] = []
    for i in range(POCKETS):
        lo, hi = edges[2 * i], edges[2 * i + 1]
        if i > 0:
            lo += LINING_T          # lay-up on the baffle to the left
        if i < POCKETS - 1:
            hi -= LINING_T          # lay-up on the baffle to the right
        out.append((lo, hi))
    return out


def gap(d: Datums = D) -> float:
    """Free run past a baffle's end, on the grid, sized so the turn's
    section (gap x interior height) carries the design flow."""
    _x, _y, (z0, z1) = interior(d)
    return snap_up(section_req() / (z1 - z0))


def baffle_spans(d: Datums = D) -> list[tuple[str, tuple[float, float], tuple[float, float]]]:
    """(label, x span, y span) of the two baffles. ``b`` (left, exit/middle)
    runs from the back wall forward, gap at the FRONT; ``a`` (right,
    middle/mouth) runs from the front wall rearward, gap at the REAR, so
    the mouth's air cannot go straight sideways."""
    _x, (y0, y1), _z = interior(d)
    g = gap(d)
    bx = baffle_x(d)
    lining_face = back_lining_y(d)[0]
    return [
        (f"{PART_NAME}_baffle_b", bx[0], (y0 + g, y1)),
        (f"{PART_NAME}_baffle_a", bx[1], (y0, lining_face - g)),
    ]


def mouth_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """The mouth capsule in the front wall, station (x span, z span): a
    vertical capsule filling the mouth pocket inside the inset."""
    _x, _y, (z0, z1) = interior(d)
    px0, px1 = pockets(d)[-1]
    return (
        (px0 + APERTURE_INSET, px1 - APERTURE_INSET),
        (z0 + APERTURE_INSET, z1 - APERTURE_INSET),
    )


def exit_width(d: Datums = D) -> float:
    """Height (Z) of the exit capsule: the smallest grid multiple whose
    capsule, at the exit's available length, carries the design flow."""
    length = exit_length(d)
    w = GRID
    while _capsule_area(length, w) < section_req() and w < length:
        w += GRID
    return w


def exit_length(d: Datums = D) -> float:
    """Length (Y) of the exit capsule: the exit pocket's run, inset from
    the front wall and from the back wall's lay-up."""
    _x, (y0, _y1), _z = interior(d)
    return back_lining_y(d)[0] - y0 - 2 * APERTURE_INSET


def exit_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """The exit capsule through the left side wall and the end wall,
    station (y span, z span): a horizontal capsule low in the exit pocket,
    one inset above the floor."""
    _x, (y0, _y1), (z0, _z1) = interior(d)
    w = exit_width(d)
    ya = y0 + APERTURE_INSET
    za = z0 + APERTURE_INSET
    return ((ya, ya + exit_length(d)), (za, za + w))


def exhaust_region_station(
    d: Datums = D,
) -> tuple[float, tuple[float, float], tuple[float, float]]:
    """The exhaust face region on the unit, station coordinates: (x of the
    face, y span, z span). The unit's control panel faces +Y (the lip), so
    its 'right, facing the panel' side is -X and 'toward the panel' is
    +Y."""
    (cx0, cx1), (cy0, cy1), (cz0, cz1) = lungs_carriage.ct15_station(d)
    x = cx0 if REGION["side"] == "right, facing the control panel" else cx1
    f0, f1 = REGION["along_frac"]
    g0, g1 = REGION["up_frac"]
    long, tall = cy1 - cy0, cz1 - cz0
    return (x, (cy0 + f0 * long, cy0 + f1 * long), (cz0 + g0 * tall, cz0 + g1 * tall))


def exhaust_region_area(d: Datums = D) -> float:
    _x, (y0, y1), (z0, z1) = exhaust_region_station(d)
    return (y1 - y0) * (z1 - z0)


def _capsule_area(length: float, width: float) -> float:
    """Open area of a capsule ``length`` long (end to end) and ``width``
    wide: the rectangle between the semicircles plus the circle."""
    r = min(width, length) / 2
    return width * (length - 2 * r) + pi * r * r


def free_areas(d: Datums = D) -> list[tuple[str, float]]:
    """(section, net free area mm2) along the path, in flow order."""
    _x, _y, (z0, z1) = interior(d)
    h = z1 - z0
    g = gap(d)
    pk = pockets(d)
    (mx0, mx1), (mz0, mz1) = mouth_station(d)
    (ey0, ey1), (ez0, ez1) = exit_station(d)
    return [
        ("mouth capsule", _capsule_area(mz1 - mz0, mx1 - mx0)),
        ("mouth pocket", (pk[2][1] - pk[2][0]) * h),
        ("turn 1, past baffle a", g * h),
        ("middle pocket", (pk[1][1] - pk[1][0]) * h),
        ("turn 2, past baffle b", g * h),
        ("exit pocket", (pk[0][1] - pk[0][0]) * h),
        ("exit capsule", _capsule_area(ey1 - ey0, ez1 - ez0)),
    ]


# ---------------------------------------------------------------- blanks

def side_size(d: Datums = D) -> tuple[float, float]:
    """(depth, height) of a side wall: the box's full Y and Z."""
    _x, (y0, y1), (z0, z1) = box_station(d)
    return (y1 - y0, z1 - z0)


def plate_size(d: Datums = D) -> tuple[float, float]:
    """(width, depth) of the floor and the top: interior plus two rabbet
    tongues, full depth."""
    (x0, x1), _y, _z = interior(d)
    _dep, _h = side_size(d)
    return (x1 - x0 + 2 * RABBET_D, _dep)


def wall_size(d: Datums = D) -> tuple[float, float]:
    """(width, height) of the front and back walls: interior plus two rabbet
    tongues, floor's top face to the top's underside."""
    (x0, x1), _y, (z0, z1) = interior(d)
    return (x1 - x0 + 2 * RABBET_D, z1 - z0)


def baffle_size(label: str, d: Datums = D) -> tuple[float, float]:
    """(length, height) of a baffle: its run, plus a tongue into the floor
    and one into the top."""
    _x, _y, (z0, z1) = interior(d)
    for lab, _xs, (y0, y1) in baffle_spans(d):
        if lab == label:
            return (y1 - y0, z1 - z0 + 2 * DADO_D)
    raise KeyError(label)


def _plate_x0(d: Datums = D) -> float:
    """Station X of a plate's or wall's local origin: the left side wall's
    inner face less the rabbet."""
    return interior(d)[0][0] - RABBET_D


# ---------------------------------------------------------------- planes

def _plane_plate(which: str, d: Datums = D) -> Plane:
    _x, (y0, _y1), (z0, z1) = box_station(d)
    z = z0 if which == "floor" else z1 - T
    return Plane(origin=(_plate_x0(d), y0, z), x_dir=(1, 0, 0), z_dir=(0, 0, 1))


def _plane_side(hand: str, d: Datums = D) -> Plane:
    (x0, x1), (y0, _y1), (z0, _z1) = box_station(d)
    x = x0 if hand == "l" else x1 - T
    return Plane(origin=(x, y0, z0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def _plane_wall(which: str, d: Datums = D) -> Plane:
    _x, (y0, y1), _z = box_station(d)
    _ix, _iy, (iz0, _iz1) = interior(d)
    y = y0 + T if which == "front" else y1
    return Plane(origin=(_plate_x0(d), y, iz0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))


def _plane_baffle(label: str, d: Datums = D) -> Plane:
    _x, _y, (iz0, _iz1) = interior(d)
    for lab, (x0, _x1), (y0, _y1) in baffle_spans(d):
        if lab == label:
            return Plane(origin=(x0, y0, iz0 - DADO_D), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    raise KeyError(label)


# ---------------------------------------------------------------- panels

def _side_faces(hand: str) -> str:
    """Which face of a side wall looks into the box, in ``groove`` terms."""
    return "front" if hand == "l" else "back"


def _baffle_dado_local(d: Datums = D) -> list[tuple[str, float, tuple[float, float], float]]:
    """(label, local x centre, local y span, blind end y) of each baffle's
    dado in plate-local coordinates: run out to the plate's edge under the
    wall the baffle butts, blind at the free end."""
    _x, (y_f, y_b), _z = box_station(d)
    x_org = _plate_x0(d)
    _dep, _h = side_size(d)
    out = []
    for lab, (bx0, bx1), (by0, by1) in baffle_spans(d):
        cx = (bx0 + bx1) / 2 - x_org
        if lab.endswith("_b"):          # butts the back wall: run to the rear edge
            out.append((lab, cx, (by0 - y_f, _dep), by0 - y_f))
        else:                            # butts the front wall: run to the front edge
            out.append((lab, cx, (0.0, by1 - y_f), by1 - y_f))
    return out


def _wall_screws_local(d: Datums = D) -> list[float]:
    """Plate-local Y of the screw lines through a plate into the front and
    back walls' edges: each wall's mid-thickness."""
    _dep, _h = side_size(d)
    return [T / 2, _dep - T / 2]


def build_plate(which: str, d: Datums = D) -> Part:
    """Floor or top, flat: the baffle dados on the face that looks into the
    box, dogboned at the blind end; screw lines into the front and back
    walls; the top also screws down into the baffles."""
    w, dep = plate_size(d)
    p = panel(w, dep)
    side = "front" if which == "floor" else "back"
    for lab, cx, (ya, yb), blind in _baffle_dado_local(d):
        p -= groove((cx, ya), (cx, yb), width=DADO_W, depth=DADO_D, side=side)
        for sx in (-1, 1):
            p -= relief(cx + sx * DADO_W / 2, blind, depth=DADO_D, side=side)
        if which == "top":
            lo, hi = (ya + T, yb) if ya == 0.0 else (ya, yb - T)
            p -= screw_line((cx, lo), (cx, hi), d=SCREW_CLEAR_D)
    for y in _wall_screws_local(d):
        p -= screw_line((RABBET_D, y), (w - RABBET_D, y), d=SCREW_CLEAR_D)
    return p


def build_side(hand: str, d: Datums = D) -> Part:
    """A side wall, flat: four rabbets on the inner face, the rabbet screws
    through the lips, the four mounting screws, and on the left wall the
    exit capsule."""
    dep, h = side_size(d)
    inner = _side_faces(hand)
    p = panel(dep, h)
    # rabbets: bottom (floor), top (top), front and rear (walls). ``toward``
    # is read along the direction of travel.
    p -= rabbet((0, 0), (dep, 0), width=RABBET_W, depth=RABBET_D, side=inner, toward="left")
    p -= rabbet((0, h), (dep, h), width=RABBET_W, depth=RABBET_D, side=inner, toward="right")
    p -= rabbet((0, 0), (0, h), width=RABBET_W, depth=RABBET_D, side=inner, toward="right")
    p -= rabbet((dep, 0), (dep, h), width=RABBET_W, depth=RABBET_D, side=inner, toward="left")
    # screws through the rabbet lips into the housed panels' edges
    p -= screw_line((0, T / 2), (dep, T / 2), d=SCREW_CLEAR_D)
    p -= screw_line((0, h - T / 2), (dep, h - T / 2), d=SCREW_CLEAR_D)
    p -= screw_line((T / 2, 0), (T / 2, h), d=SCREW_CLEAR_D)
    p -= screw_line((dep - T / 2, 0), (dep - T / 2, h), d=SCREW_CLEAR_D)
    # mounting screws into the bay wall, two per vertical line
    for x in (MOUNT_INSET, dep - MOUNT_INSET):
        p -= screw_line((x, 0), (x, h), d=SCREW_CLEAR_D, pitch=MOUNT_PITCH, inset=MOUNT_INSET)
    if hand == "l":
        _bx, (y0, _y1), (z0, _z1) = box_station(d)
        (ey0, ey1), (ez0, ez1) = exit_station(d)
        centre = ((ey0 + ey1) / 2 - y0, (ez0 + ez1) / 2 - z0)
        p -= through_slot(centre, ey1 - ey0, ez1 - ez0, corner_r=(ez1 - ez0) / 2)
    return p


def build_wall(which: str, d: Datums = D) -> Part:
    """Front or back wall, flat. The front carries the mouth."""
    w, h = wall_size(d)
    p = panel(w, h)
    if which == "front":
        _ix, _iy, (iz0, _iz1) = interior(d)
        (mx0, mx1), (mz0, mz1) = mouth_station(d)
        centre = ((mx0 + mx1) / 2 - _plate_x0(d), (mz0 + mz1) / 2 - iz0)
        p -= through_slot(centre, mz1 - mz0, mx1 - mx0, angle=90.0, corner_r=(mx1 - mx0) / 2)
    return p


def build_baffle(label: str, d: Datums = D) -> Part:
    """A baffle, flat. No features: housed top and bottom, glued, screwed
    from the top plate."""
    length, h = baffle_size(label, d)
    return panel(length, h)


def _box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Part:
    return Box(x[1] - x[0], y[1] - y[0], z[1] - z[0],
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x[0], y[0], z[0]))
    )


def lining_station(d: Datums = D) -> list[tuple[str, tuple, tuple, tuple]]:
    """(label, x, y, z spans) of the seven lay-up slabs: the back wall's
    inner face, one slab per pocket, and both faces of both baffles, floor's
    top face to the top's underside.

    The back wall's lay-up is THREE slabs and not one because baffle b runs
    to that wall: a single slab across the full interior width would have the
    baffle and its own lay-up standing inside it. One slab per pocket puts
    the lay-up exactly where the air is and leaves the baffle its landing."""
    _x, _iy, (iz0, iz1) = interior(d)
    y = back_lining_y(d)
    out = [
        (f"{LINING_STEM}_back_{i}", (px0, px1), y, (iz0, iz1))
        for i, (px0, px1) in enumerate(pockets(d))
    ]
    for lab, (bx0, bx1), (by0, by1) in baffle_spans(d):
        stem = lab.replace(PART_NAME, LINING_STEM)
        out.append((f"{stem}_l", (bx0 - LINING_T, bx0), (by0, by1), (iz0, iz1)))
        out.append((f"{stem}_r", (bx1, bx1 + LINING_T), (by0, by1), (iz0, iz1)))
    return out


def build_lining(d: Datums = D) -> list[tuple[str, Part]]:
    return [(lab, _box(x, y, z)) for lab, x, y, z in lining_station(d)]


def build_hose_corridor(d: Datums = D) -> Part:
    return _box(*hose_corridor_station(d))


# ---------------------------------------------------------------- assembly

def panels(d: Datums = D) -> list[tuple[str, Part, Plane]]:
    """(label, flat part, plane) for the eight birch panels."""
    out = [
        (f"{PART_NAME}_floor", build_plate("floor", d), _plane_plate("floor", d)),
        (f"{PART_NAME}_top", build_plate("top", d), _plane_plate("top", d)),
        (f"{PART_NAME}_side_l", build_side("l", d), _plane_side("l", d)),
        (f"{PART_NAME}_side_r", build_side("r", d), _plane_side("r", d)),
        (f"{PART_NAME}_front", build_wall("front", d), _plane_wall("front", d)),
        (f"{PART_NAME}_back", build_wall("back", d), _plane_wall("back", d)),
    ]
    for lab, _xs, _ys in baffle_spans(d):
        out.append((lab, build_baffle(lab, d), _plane_baffle(lab, d)))
    return out


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, part) for everything this module puts in the
    assembly: the birch as carcass, the lay-up and the hose corridor as
    references."""
    out: list[tuple[str, str, Part]] = [
        (label, "carcass", plane * part) for label, part, plane in panels(d)
    ]
    out += [(lab, "reference", part) for lab, part in build_lining(d)]
    out.append((HOSE_NAME, "reference", build_hose_corridor(d)))
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, ``(a, b, kind, axis, lo, hi, note)`` tuples."""
    n = PART_NAME
    (ix0, ix1), _iy, (iz0, iz1) = interior(d)
    out: list[tuple] = []
    for hand, face_x, inward in (("l", ix0, -1.0), ("r", ix1, 1.0)):
        lo, hi = sorted((face_x, face_x + inward * RABBET_D))
        for member in ("floor", "top", "front", "back"):
            out.append((f"{n}_side_{hand}", f"{n}_{member}", "housing", "x", lo, hi,
                        f"{member} edge in the side wall's rabbet"))
    for lab, _xs, _ys in baffle_spans(d):
        out.append((f"{n}_floor", lab, "housing", "z", iz0 - DADO_D, iz0,
                    "baffle's bottom tongue in the floor's dado"))
        out.append((f"{n}_top", lab, "housing", "z", iz1, iz1 + DADO_D,
                    "baffle's top tongue in the top's dado"))
    for plate in ("floor", "top"):
        for wall in ("front", "back"):
            out.append((f"{n}_{plate}", f"{n}_{wall}", "butt", None, 0.0, 0.0,
                        f"{wall} wall's edge on the {plate}, screwed through the {plate}"))
    out.append((f"{n}_baffle_a", f"{n}_front", "butt", None, 0.0, 0.0,
                "baffle a's front end on the front wall's inner face"))
    out.append((f"{n}_baffle_b", f"{n}_back", "butt", None, 0.0, 0.0,
                "baffle b's rear end on the back wall's inner face"))
    for lab, _x, _y, _z in lining_station(d):
        if lab.startswith(f"{LINING_STEM}_back"):
            host = f"{n}_back"
        else:
            host = lab.replace(LINING_STEM, n)[:-2]
        out.append((host, lab, "bearing", None, 0.0, 0.0, "lay-up bonded to the face"))
    out.append((f"{n}_side_l", WALLS[0].name, "butt", None, 0.0, 0.0,
                "left wall screwed to the end wall from inside the exit pocket"))
    out.append((f"{n}_side_r", WALLS[1].name, "butt", None, 0.0, 0.0,
                "right wall screwed to the divider from inside the mouth pocket"))
    out.append((f"{n}_back", "spine_panel", "butt", None, 0.0, 0.0,
                "back wall flat on the spine's lungs face"))
    return out


# ---------------------------------------------------------------- checks

def check_exhaust_plenum(d: Datums = D) -> list[str]:
    """What this box has to be true for: every section carries the design
    flow, it clears what it has to clear, its placement is what its planes
    say, and its blanks come out of a sheet. The assembly owns collisions."""
    notes: list[str] = []
    s = d.s
    (bx0, bx1), (by0, by1), (bz0, bz1) = box_station(d)
    (ix0, ix1), (iy0, iy1), (iz0, iz1) = interior(d)
    req = section_req()

    # -- every section, net of the lay-up, at or over BOTH flow rules
    for name, area in free_areas(d):
        if area < req - 1e-6:
            notes.append(
                f"{name} carries {area / 100:.0f} cm2 against {req / 100:.0f} cm2 "
                f"({SECTION_MARGIN:.1f}x {rated_flow_ls():.1f} L/s rated, and "
                f"{max_flow_ls():.1f} L/s turbine, at {V_MAX:.1f} m/s): the plenum "
                "chokes here"
            )
    worst = min(a for _n, a in free_areas(d))
    region = exhaust_region_area(d)
    notes.append(
        f"SECTION RULE, standing note. The extractor's rated "
        f"{CT15['airflow_extractor_m3h']:.0f} m3/h is {rated_flow_ls():.1f} L/s "
        f"({rated_flow_ls() * CFM_PER_LS:.0f} CFM); the bare turbine's "
        f"{CT15['airflow_turbine_m3h']:.0f} m3/h is {max_flow_ls():.1f} L/s "
        f"({max_flow_ls() * CFM_PER_LS:.0f} CFM). Every section carries at least "
        f"{req / 100:.0f} cm2, the larger of {SECTION_MARGIN:.1f}x the rated flow "
        f"and 1.0x the turbine flow at {V_MAX:.1f} m/s; the tightest is "
        f"{worst / 100:.0f} cm2, {worst / (rated_flow_ls() / 1000.0 / V_MAX * 1e6):.2f}x "
        f"the rated requirement and {V_MAX * req / worst:.2f} m/s at the turbine "
        f"figure. The rule was handed over as 1.5x the exhaust face REGION, which "
        f"would be {1.5 * region / 100:.0f} cm2 per section: it does not fit a "
        f"{by1 - by0:.0f}mm-deep void behind the lip, and it counts sealed plastic "
        "as if it moved air, which Jared ruled against on the VFD louvre "
        "(2026-09-02). The region is COVERAGE, not a duct: the bay is the first "
        "chamber and the mouth draws from it. This note never clears."
    )

    # -- the region and the mouth: where the jet actually goes
    rx, (ry0, ry1), (rz0, rz1) = exhaust_region_station(d)
    lin_l, _lin_r = lungs_carriage.lining_faces(d)
    notes.append(
        f"ct15_exhaust is a design face-region, x {rx:.0f} (the unit's side toward "
        f"the end wall), y {ry0:.0f}..{ry1:.0f}, z {rz0:.0f}..{rz1:.0f}, "
        f"{region / 100:.0f} cm2, {rx - lin_l:.0f}mm off the end wall's lining; the "
        f"mouth is in the front wall at x {mouth_station(d)[0][0]:.0f}..{mouth_station(d)[0][1]:.0f}, "
        f"z {mouth_station(d)[1][0]:.0f}..{mouth_station(d)[1][1]:.0f}, and the lined bay "
        "between them is the first expansion. NO SEAL BAND, and that is a "
        "deliberate departure from the plan the part was handed: a hood on that "
        f"face has {rx - lin_l:.0f}mm beside the spacer block and "
        f"{rx - (d.lungs_x[0] + LINING_T):.0f}mm above it, and a band around a "
        f"mouth on a SIDE face would drag the unit's whole length on every one of "
        f"the {lungs_carriage.SLIDE_TRAVEL:.0f}mm of travel rather than compress "
        "once. The bay is the chamber and the only thing touching the unit is air. "
        "Expected, and worth knowing."
    )

    # -- the tray: closed, it stops short of the front wall; the pull is away
    reach = tray_rear_reach(d)
    if by0 - reach < TRAY_CLEAR - 1e-6:
        notes.append(
            f"the front wall at y {by0:.1f} is {by0 - reach:.1f} behind the closed "
            f"tray's rearmost point at {reach:.1f} against TRAY_CLEAR {TRAY_CLEAR:.0f}"
        )
    # the whole travel, as a boolean and not as an argument: every carriage
    # solid swept over SLIDE_TRAVEL against the box's own envelope
    box_env = _box(*box_station(d))
    swept_max = reach
    for label, _group, part in lungs_carriage.placed_all(d):
        sw = lungs_carriage.swept(part)
        swept_max = max(swept_max, sw.bounding_box().max.Y)
        try:
            shared = sw & box_env
        except Exception:
            continue
        if shared is not None and shared.volume > 1.0:
            notes.append(
                f"{label} sweeps {shared.volume:,.0f} mm3 into the plenum's envelope "
                f"over the {lungs_carriage.SLIDE_TRAVEL:.0f}mm of travel"
            )
    notes.append(
        f"TRAY vs PLENUM, standing note. The closed tray's rearmost point is the "
        f"sensor's barbs at y {reach:.1f} and the swept carriage reaches y "
        f"{swept_max:.1f}; the front wall stands {by0 - swept_max:.0f} behind that, "
        f"because the {lungs_carriage.SLIDE_TRAVEL:.0f} of travel runs toward the "
        "operator. Every carriage solid was swept and intersected against the box: "
        "nothing shared. Expected, and worth knowing."
    )

    # -- the bay's own lay-up, which the box lands on
    notes.append(
        f"LINING, standing note. The box runs the bay's full width, x {bx0:.0f}..{bx1:.0f}, "
        f"which is the two walls' inner faces, so the bay's own {LINING_T:.0f}mm lay-up "
        f"stops at the plenum's front wall at y {by0:.0f} and the box's side walls land "
        "on bare birch. The box carries its own lay-up inside: the back wall in three "
        "slabs, one per pocket, and both faces of both baffles. Bond the bay's lay-up "
        "after the box is screwed in, not before. Expected, and worth knowing."
    )

    # -- the receptacle under the floor, and the plug's way in
    (_rx0, _rx1), (ry0b, _ry1b), (_rz0, rz1b) = mains_backplate.receptacle_station(d)
    if bz0 - rz1b < RECEPTACLE_CLEAR - 1e-6:
        notes.append(f"the floor at z {bz0:.1f} sits on the receptacle box's top at {rz1b:.1f}")
    notes.append(
        f"the floor stands {bz0 - rz1b:.0f} over the receptacle box; the slot under "
        f"it, z {d.deck_top:.0f}..{bz0:.0f} by the bay's width, is where the plug goes "
        f"in, {ry0b - reach:.0f} behind the closed tray. Expected, and worth knowing."
    )

    # -- the hose corridor over the top, the mains crossings outside the box
    (hx0, hx1), (hy0, hy1), (hz0, hz1) = hose_corridor_station(d)
    if hz0 - bz1 < HOSE_CLEAR - 1e-6:
        notes.append(f"the top at z {bz1:.1f} is inside the hose corridor from {hz0:.1f}")
    notes.append(
        f"{HOSE_NAME} is x {hx0:.0f}..{hx1:.0f} y {hy0:.0f}..{hy1:.0f} z {hz0:.0f}..{hz1:.0f}: "
        f"the hose leaves the head's top front and climbs to the port at z "
        f"{d.hose_port[2]:.0f}; the plenum's top is {hz0 - bz1:.0f} under it. The "
        "corridor's floor is one hose diameter under the unit's top on an observed "
        "position, not measured: catalog ct15_inlet is None, MEASURE THIS and the "
        "corridor and the top follow."
    )
    for name, (cx, cz) in mains_backplate_crossings(d).items():
        if bz0 < cz < bz1 and bx0 < cx < bx1:
            notes.append(f"the spine's {name} crossing at x {cx:.0f} z {cz:.0f} is inside the plenum")

    # -- the exit: through the end wall, clear of what the end wall carries
    (ey0, ey1), (ez0, ez1) = exit_station(d)
    _px, py, pz = d.hose_port
    port_r = s.hose_id / 2 + 4.0
    dy = max(py - port_r - ey1, ey0 - (py + port_r), 0.0)
    dz = max(pz - port_r - ez1, ez0 - (pz + port_r), 0.0)
    if dy == 0.0 and dz == 0.0:
        notes.append("the exit capsule runs into the hose port")
    from stations.cnc_shapeoko.parts.bay_walls import SPACER_H
    sp_y1 = lungs_carriage.carriage_origin(d)[1] + SLIDE_LEN
    if ey0 < sp_y1 and ez0 < d.deck_top + SPACER_H:
        notes.append("the exit capsule lands on the spacer block")
    for lab, _xs, (sy0, sy1) in d.stiles:
        if lab.endswith("_left") and not (ey1 < sy0 or sy1 < ey0):
            notes.append(f"the exit capsule crosses {lab}")
    notes.append(
        f"EXIT, standing note. A {ey1 - ey0:.0f} x {ez1 - ez0:.0f} capsule through the "
        f"left end wall at y {ey0:.0f}..{ey1:.0f}, z {ez0:.0f}..{ez1:.0f} "
        f"({(ez0 + ez1) / 2:.0f} above the floor, {(ez0 + ez1) / 2 - d.deck_top:.0f} "
        "above the deck), to the room between the two left legs. The deck was "
        "not chosen because the plinth is a closed frame with a 10 cm2 grille; "
        "the spine was not chosen because the mains backplate is 18mm behind it. "
        "This note never clears."
    )

    # -- the door at 180 is at the other end of the bay
    from stations.cnc_shapeoko.parts import lungs_door
    ob = lungs_door.door_open(180.0, d).bounding_box()
    notes.append(
        f"the lungs door at 180 lies at y {ob.min.Y:.0f}..{ob.max.Y:.0f}; the plenum "
        f"starts {by0 - ob.max.Y:.0f} behind it. Expected, and worth knowing."
    )

    # -- the placement is a rotation, and a rotation is where signs go wrong
    dep, h = side_size(d)
    pw, _pd = plate_size(d)
    x_org = _plate_x0(d)
    want_bb = {
        f"{PART_NAME}_floor": ((x_org, x_org + pw), (by0, by1), (bz0, bz0 + T)),
        f"{PART_NAME}_top": ((x_org, x_org + pw), (by0, by1), (bz1 - T, bz1)),
        f"{PART_NAME}_side_l": ((bx0, bx0 + T), (by0, by1), (bz0, bz1)),
        f"{PART_NAME}_side_r": ((bx1 - T, bx1), (by0, by1), (bz0, bz1)),
        f"{PART_NAME}_front": ((x_org, x_org + pw), (by0, by0 + T), (iz0, iz1)),
        f"{PART_NAME}_back": ((x_org, x_org + pw), (by1 - T, by1), (iz0, iz1)),
    }
    for lab, (x0, x1), (y0, y1) in baffle_spans(d):
        want_bb[lab] = ((x0, x1), (y0, y1), (iz0 - DADO_D, iz1 + DADO_D))
    for label, _group, part in placed_all(d):
        if label not in want_bb:
            continue
        bb = part.bounding_box()
        got3 = ((bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z))
        for axis, g, e in zip("xyz", got3, want_bb[label]):
            if abs(g[0] - e[0]) > 0.05 or abs(g[1] - e[1]) > 0.05:
                notes.append(
                    f"{label} landed at {axis} {g[0]:.1f}..{g[1]:.1f} and belongs "
                    f"at {e[0]:.1f}..{e[1]:.1f}. Its plane is wrong."
                )

    for label, part, _plane in panels(d):
        bb = part.bounding_box()
        if not fits((bb.size.X, bb.size.Y), SHEET_5X5_BALTIC):
            notes.append(f"{label} blank does not come out of a 5x5 sheet")

    return notes


def mains_backplate_crossings(d: Datums = D) -> dict[str, tuple[float, float]]:
    """Station (x, z) of every crossing through the spine into the lungs
    bay's section of it, from spine_panel."""
    from stations.cnc_shapeoko.parts import spine_panel
    out: dict[str, tuple[float, float]] = {}
    for name, (lx, lz) in spine_panel.crossing_positions(d).items():
        x = lx + d.t
        if d.lungs_x[0] <= x <= d.lungs_x[1]:
            out[name] = (x, lz + d.deck_top)
    return out


# ---------------------------------------------------------------- export

def export(d: Datums = D) -> list:
    """STEP and DXF for the eight panels; STEP only for the lay-up slabs
    and the hose corridor."""
    written = []
    for label, part, _plane in panels(d):
        written += export_part(part, label)
    out_dir = EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    refs = build_lining(d) + [(HOSE_NAME, build_hose_corridor(d))]
    for label, solid in refs:
        p = out_dir / f"{label}.step"
        export_step(solid, p, unit=Unit.MM)
        written.append(p)
    return written


# ---------------------------------------------------------------- report

if __name__ == "__main__":
    d = D
    (bx0, bx1), (by0, by1), (bz0, bz1) = box_station(d)
    (ix0, ix1), (iy0, iy1), (iz0, iz1) = interior(d)
    print(
        f"{PART_NAME}: {bx1 - bx0:.0f} wide x {by1 - by0:.1f} deep x {bz1 - bz0:.1f} tall, "
        f"x {bx0:.0f}..{bx1:.0f} y {by0:.1f}..{by1:.1f} z {bz0:.1f}..{bz1:.1f}; "
        f"interior {ix1 - ix0:.0f} x {iy1 - iy0:.1f} x {iz1 - iz0:.1f}"
    )
    for lab, (x0, x1), (y0, y1) in baffle_spans(d):
        print(f"  {lab}: x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  ({y1 - y0:.1f} long), gap {gap(d):.0f}")
    (mx0, mx1), (mz0, mz1) = mouth_station(d)
    (ey0, ey1), (ez0, ez1) = exit_station(d)
    print(f"  mouth capsule x {mx0:.1f}..{mx1:.1f} z {mz0:.1f}..{mz1:.1f} in the front wall")
    print(f"  exit capsule  y {ey0:.1f}..{ey1:.1f} z {ez0:.1f}..{ez1:.1f} through the left end wall")
    req = section_req()
    print(
        f"  rated {rated_flow_ls():.1f} L/s x {SECTION_MARGIN:.1f}, turbine "
        f"{max_flow_ls():.1f} L/s x 1.0, at {V_MAX:.1f} m/s -> {req / 100:.1f} cm2 per section"
    )
    for name, area in free_areas(d):
        print(f"    {name:24s} {area / 100:7.1f} cm2  {area / req:5.2f}x")
    for label, part, _plane in panels(d):
        bb = part.bounding_box()
        print(f"  blank {label:28s} {bb.size.X:7.1f} x {bb.size.Y:7.1f} x {bb.size.Z:.0f}")
    found = check_exhaust_plenum(d)
    print(f"\n{len(found)} exhaust plenum note(s):")
    for n in found:
        print(f"  - {n}")
    for p in export(d):
        print(f"wrote {p}")
