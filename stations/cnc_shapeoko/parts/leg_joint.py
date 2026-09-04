"""Leg joint: the machine's own legs bolted straight into the carcass end walls.

Build order 5. This module owns no solid. It owns a JOINT: the fastener stack,
where every bolt lands, the cutter each insert needs in the birch, and the checks
that say whether the joint is buildable. ``bay_walls`` subtracts the cutters;
``assembly`` prints the axes; nothing else needs to know this exists.


WHAT THIS REPLACED, AND WHY
===========================

Until 2026-09-02 this joint was a machined delrin wedge -- ``parts/leg_tie.py``,
four of them -- that spanned an assumed 6-degree leg splay and bolted to the
OUTSIDE of the carcass. Jared killed it, verbatim: "The leg ties are egregious
design. Unacceptable. The legs themselves have bolt holes. We are not bolting
shit to the outside of the machine just so the carcass is fastened to the legs.
Bolts through the legs into threaded inserts is more than fine."

And the splay it existed to span was never real, ruled the same day: "There is no
way Shapeoko manufactured table legs with splay. It's square. We have no reason
to believe otherwise." ``leg_splay`` is 0.0 and nothing reads it.

The whole part fell out of two facts that were already true and were not being
used. The legs are square, so a vertical carcass wall and a leg's inner face are
PARALLEL. And the carcass footprint is flush to the leg inner faces -- the
2026-09-02 ruling in ``carcass.py`` -- so those two faces are not merely parallel,
they are TOUCHING. There is no gap to span, so there is nothing to span it with.


THE JOINT
=========

    outside the leg    a bolt head and a flat washer. Nothing else, ever.
    through the leg    the leg's OWN hole, ``leg_holes.hole_d``, already there
    the interface      leg inner face flat on end wall outer face, no spacer,
                       no boss, no shim, no standoff
    inside the birch   a threaded insert, driven below the bearing face so
                       nothing stands proud of it

The bolt size is not chosen. The calipered 6.604mm through hole is an M6 normal
clearance hole, so the leg picked M6 for us; ``BOLT_D`` derives from
``leg_holes.hole_d`` and follows it if a future leg's hole is something else.

The counterbore is the part that is easy to leave out and fatal to leave out.
The insert has a head, the head would stand proud of the birch, and the birch is
a BEARING FACE -- it is the only thing between the leg and the carcass. An insert
sitting proud turns a flat joint into a three-point one and puts the whole load
on three brass heads. So the wall gets a shallow counterbore at the insert's own
outside diameter, the insert is driven to the bottom of it, and the face stays
flat. See ``WALL_CBORE_D`` and ``check_leg_joint``.


WHERE THE 52mm LEVELLING SWING WENT
===================================

The old ties were SLOTTED for it: ``LEG_SLOT_V`` = 60mm of vertical travel, so
the carcass could be bolted first and levelled afterward. Inserts have no slot.
A bolt into an insert is a fixed point, and this joint does not pretend
otherwise. It is resolved by ORDER instead of by geometry:

    1. the carcass is built from the FLOOR UP. Its height is fixed and the
       leftover becomes ``Datums.top_gap``, which is why the swing could never
       break the carcass in the first place.
    2. the machine is LEVELLED FIRST, on its own feet, before anything is bolted.
    3. THEN the bolts go in, at whatever height the levelled legs put their holes.
    4. re-levelling later means LOOSENING THEM. Not adjusting them, not shimming
       them: eight M6 out, wind the feet, eight M6 back in. That is the whole
       cost, it is an hour, and it is the correct trade for a joint with no
       bracket, no wedge and no slot in it.

EIGHT BOLTS, NOT SIXTEEN (RULED 2026-09-04)
==========================================

The leg's pattern is a 2x2 cluster per leg and the carcass uses ONE column of
it: the outer one, 56.9 in from the inner face. The inner column, 16.78 in
(the heel reading of 2026-09-04), puts its pilot 5.98mm inside the end wall's
``EDGE_LAND`` and the land rule stands. Jared: "DROP the inner bolt column (8
bolts, outer column only; the plinth carries, bolts brace)". ``LegHoles.
cols_used`` carries it; the BOM buys 8 inserts, 8 M6 x 16 and 8 DIN 125.

WHAT CARRIES WHAT, which is the thing a slot used to blur:

    the machine's feet are its ONLY floor contact. The carcass never carries the
    Shapeoko, at any height, in any config.
    the plinth carries the carcass. It sits on the floor and it is the only
    thing under the birch.
    the bolts BRACE. They tie four independent legs into a frame and they stop
    the carcass racking. They do not carry the machine and they do not carry the
    carcass. Nothing hangs.

``floor_state`` computes, at the fitted ``table_h``, whether that is actually
what happens: whether every hole row lands in birch with the plinth on the
floor, or whether the carcass would have to be lifted off its plinth to reach a
row -- which would be hanging, and which would be wrong.


WHAT IS MEASURED, AND THE ONE THING LEFT
=======================================

``params.LegHoles`` is calipered as of 2026-09-03: pitch, row heights, edge
offset, hole diameter, and which faces carry holes. The leg is an ANGLE IRON in
profile and not a tube, which settles ``walls_in_path`` at 1 -- one wall under
the head, no cavity to span, and no crush sleeve to buy.

Left open: ``LegHoles.flange_w``, the width of the angle's bolt-bearing flange.
The holes prove it reaches far enough to contain them; what it does not prove is
whether it runs far enough past the outer column for the reach ``check_leg_joint``
asks for. That is the last number on the leg.


MATERIAL NON-ARTIFICE
=====================

There is no part here. That is the point: the joint is the machine's steel, the
carcass's birch, and a fastener, with nothing invented to sit between them. The
only manufactured thing this module adds to the station is a hole. No red: the
E-stop is the whole red budget, and nothing here senses, gates or stops anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Align, Cylinder, Location, Part, Plane

from lib.house import GRID, on_grid
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    T,
    Datums,
)

__all__ = [
    "NAME",
    "Bolt",
    "BOLT_D",
    "BOLT_THREAD",
    "INSERT_PART",
    "INSERT_LEN",
    "INSERT_OD",
    "INSERT_PILOT_D",
    "WALL_CBORE_D",
    "WALL_CBORE_DEPTH",
    "WALL_PILOT_DEPTH",
    "END_WALLS",
    "bolt_length",
    "bolts",
    "insert_cutter",
    "insert_cutters",
    "keepouts",
    "wall_band",
    "floor_state",
    "check_leg_joint",
]

NAME = "leg_joint"

S = DATUMS.s
D: Datums = DATUMS


# ============================================================ parameters
# One block. The pattern comes from ``params.LegHoles``, the panel from
# ``carcass.T``, and the insert from its vendor sheet. No dimension literal
# appears in the geometry underneath.

# -- which walls the joint lands on -----------------------------------------
END_WALLS = (0, 3)
"""Indices of the two walls that present birch to a leg.

The left end wall's OUTER face is at ``x_left`` and the right end wall's at
``x_right``, which are the leg inner faces themselves. The dividers touch no leg
and the front is open, so these two panels are the entire joint."""

# -- the bolt, which the leg chose ------------------------------------------
BOLT_CLEAR = 1.0
"""Clearance a through hole carries over its bolt. 7mm thru is M6, 9mm is M8."""

BOLT_D = float(round(S.leg_holes.hole_d - BOLT_CLEAR))
"""Nominal bolt diameter the leg's hole implies, SNAPPED to the nearest whole
millimetre because a bolt is bought in nominal sizes and a hole is measured in
whatever the calipers say. The 2026-09-03 hole is 6.604mm: minus the clearance
that is 5.604, and a 5.6mm bolt does not exist. It rounds to the M6 it always
was. Without the snap this quantity silently becomes 5.604 and drags ENGAGE_MIN
down with it, understating the thread the insert needs by most of a millimetre."""
BOLT_THREAD = f"M{BOLT_D:.0f}-1.0"
BOLT_HEAD = "socket cap, hex drive"
"""A socket head, not a hex head. The head sits against a leg face with the
machine's own steel around it and a socket reaches where a spanner does not."""

WASHER = "DIN 125 flat, steel"
WASHER_T = 1.6
WASHER_D = 12.0
"""The flat washer is the whole of what is outside the leg besides the head, and
it is not optional: ``leg_wall_t`` is 3.52mm of calipered 10-gauge steel and a
bare M6 head dimples it. It spreads the head and it is the last part of this
joint."""

BOLT_STOCK_LEN = (12.0, 16.0, 20.0, 25.0, 30.0, 35.0, 40.0)
"""Stock lengths under the head, so the BOM buys a length that exists."""

ENGAGE_MIN = BOLT_D * 1.5
"""Thread engagement floor. One and a half diameters is the convention for a
steel bolt in a brass insert; below it the insert strips before the bolt does."""

ENGAGE_CLEAR = 1.0
"""How far the bolt tip must stop short of the insert's blind end. A bolt that
bottoms out reads as tight and clamps nothing."""

# -- the insert -------------------------------------------------------------
INSERT_PART = "E-Z LOK 400-M6, E-Z Knife brass insert for hard wood"
INSERT_ALT = "Rampa type SK/B M6, the interchangeable European knife-thread"
"""Named so the BOM buys a knife-thread insert and not a hex-drive one.

E-Z LOK sells both families for wood: E-Z Knife (400 series, brass, slotted, coarse
external knife thread) for HARD wood, and E-Z Hex (900 series, flanged, hex drive)
for SOFT wood. Baltic birch ply is the hard-wood case, so this is the 400. The
Rampa is the same joint from a different vendor and is listed so a lead time does
not stop the build.

CONFIDENCE: medium, and the disagreement is written down rather than resolved.
E-Z LOK's own dimensional chart reads 0.500in OD and 0.453in (11.51mm) length on
a 3/8in (9.525mm) pilot; a distributor listing for the stainless variant of the
same part reads 12.70mm installed length on a 25/64in (9.92mm) pilot. The LONGER
length and the SMALLER pilot are taken below, because both errors are in the
direction that still yields a working joint: a pilot bore deep enough either way,
and a hole the insert can bite. Confirm against the packet before drilling 8 of
them."""

INSERT_THREAD = BOLT_THREAD
INSERT_OD = 12.7        # 0.500in, the external knife thread's major diameter
INSERT_LEN = 12.7       # the longer of the two published readings, see above
INSERT_PILOT_D = 9.525  # 3/8in, E-Z LOK's own drill chart for the 400-M6
INSERT_DRIVER = "E-Z LOK DT-M6 drive tool, or an M6 bolt and two nuts locked"

# -- what the wall gets ------------------------------------------------------
CBORE_CLEAR = 1.3
"""Diametral clearance on the counterbore. The insert is driven, not dropped, so
it wants room to start square without wanting room to wander."""

WALL_CBORE_D = INSERT_OD + CBORE_CLEAR
WALL_CBORE_DEPTH = 1.5
"""Depth of the seat the insert's head finishes in. Shallow on purpose: enough to
take the head below the bearing face and no more, because every millimetre here
is a millimetre of birch not holding the insert."""

WALL_PILOT_DEPTH = INSERT_LEN + GRID / 20
"""Pilot bore below the counterbore floor, one millimetre deeper than the insert
so it is never the bore that stops the drive."""

WALL_BACK_MIN = 2.0
"""Birch that must be left behind a blind insert. Below this the far face of the
wall bulges when the insert is driven, and the bay side of an end wall is a
finished face."""

# -- where the joint may sit on the panel -----------------------------------
EDGE_LAND = T
"""Solid birch around the PILOT BORE, between it and any edge of the panel, its
tongues included. One panel thickness, the same land the louvre field keeps.

This is the STRUCTURAL land. The pilot runs nearly the whole thickness and it is
what the knife thread expands into, so the material around it is what takes the
driving force and the pull-out load."""

CBORE_EDGE_LAND = T / 2
"""Solid birch around the COUNTERBORE, a weaker requirement than EDGE_LAND.

Patched 2026-09-03. Jared's calipers put the leg's hole 22.86mm off the inner
corner and the old single land rejected all eight inner-column bolts by 2.14mm.
That rule applied the counterbore's full 14mm diameter as though the whole hole
were 14mm wide. It is not. WALL_CBORE_DEPTH is 1.5mm, a seat for the insert's
head, and below it the hole is the 9.525mm pilot. A 1.5mm-deep clearance seat
takes no hoop load; it needs enough birch not to break out at the surface and no
more. Half a panel thickness is that, and the real joint has 15.86mm.

The bolts were never too close to the edge. The check was measuring the wrong
bore."""


def edge_margin() -> float:
    """Least distance from a panel edge to an insert's CENTRE.

    Both bores are asked and the worse one wins, so changing either the insert or
    the counterbore moves this on its own. Today the pilot binds: 18.0 + 4.76 =
    22.76 against the counterbore's 9.0 + 7.0 = 16.0."""
    return max(EDGE_LAND + INSERT_PILOT_D / 2,
               CBORE_EDGE_LAND + WALL_CBORE_D / 2)


# ============================================================ derived


def bolt_length() -> float | None:
    """Shortest stock bolt that engages enough thread without bottoming out.

    Under the head, in order: the washer, the leg wall or walls the bolt crosses,
    the counterbore void between the leg face and the insert's head, and then the
    thread. ``None`` when no stock length satisfies both ends, which is a real
    answer and ``check_leg_joint`` reports it.
    """
    stack = WASHER_T + S.leg_holes.walls_in_path * S.leg_wall_t + WALL_CBORE_DEPTH
    for length in BOLT_STOCK_LEN:
        engage = length - stack
        if ENGAGE_MIN <= engage <= INSERT_LEN - ENGAGE_CLEAR:
            return length
    return None


def bolt_engagement(length: float) -> float:
    """Thread actually taken up inside the insert, for a given bolt length."""
    return length - (
        WASHER_T + S.leg_holes.walls_in_path * S.leg_wall_t + WALL_CBORE_DEPTH
    )


def wall_band(d: Datums = D) -> tuple[float, float]:
    """Station Z range an insert centre may occupy in an end wall.

    The blank runs a tongue below ``deck_top`` and another above ``top_z[0]``,
    but a tongue is buried in a housing and is not somewhere to put a bolt. So
    the band is the wall's CLEAR height, less a land and the counterbore's own
    radius at each end.
    """
    margin = edge_margin()
    return (d.deck_top + margin, d.top_z[0] - margin)


# ============================================================ the bolts


@dataclass(frozen=True)
class Bolt:
    """One bolt through one leg into one insert, in station coordinates.

    ``x``/``y``/``z`` is the insert's MOUTH: the point where the bolt axis meets
    the end wall's outer face, which is also the leg's inner face, because the
    2026-09-02 flush ruling put those two planes in the same place.

    ``inward`` is +1 when the insert runs into +X and -1 when into -X, so one
    field carries which side of the station this is and every downstream length
    is a multiplication rather than a branch.
    """

    label: str
    wall: int
    leg: str
    x: float
    y: float
    z: float
    inward: float

    @property
    def axis(self) -> tuple[float, float, float]:
        return (self.inward, 0.0, 0.0)

    def head_face(self) -> tuple[float, float, float]:
        """Where the washer bears: the leg's outer surface, one wall out."""
        out = S.leg_holes.walls_in_path * S.leg_wall_t
        return (self.x - self.inward * out, self.y, self.z)

    def tip(self, length: float | None = None) -> tuple[float, float, float]:
        """Where the bolt's last thread finishes inside the insert."""
        length = bolt_length() if length is None else length
        reach = WALL_CBORE_DEPTH + (
            bolt_engagement(length) if length is not None else INSERT_LEN
        )
        return (self.x + self.inward * reach, self.y, self.z)

    def plane(self) -> Plane:
        """Local frame at the insert mouth, local +Z running INTO the birch."""
        return Plane(
            origin=(self.x, self.y, self.z),
            x_dir=(0.0, 1.0, 0.0),
            z_dir=self.axis,
        )


def bolts(d: Datums = D) -> list[Bolt]:
    """Every bolt in the joint, in station coordinates.

    Four legs, the columns ``LegHoles.cols_used`` names (RULED 2026-09-04:
    the OUTER column only, eight bolts) and one bolt per row in ``rows_z``.
    The columns march from the leg's INNER edge into the opening, which on a
    front leg is +Y and on a rear leg is -Y, because that edge is the datum
    the station origin sits on and because a column the other way has no
    carcass behind it. The inner column, 16.78 in, fails ``EDGE_LAND`` by 6
    and is left empty; the land rule is not relaxed.
    """
    h = d.s.leg_holes
    out: list[Bolt] = []
    sides = (
        ("left", END_WALLS[0], d.x_left, 1.0),
        ("right", END_WALLS[1], d.x_right, -1.0),
    )
    ends = (
        ("front", d.y_front, 1.0),
        ("rear", d.y_rear, -1.0),
    )
    for side, wall, x, inward in sides:
        for end, y0, along in ends:
            for c, col in zip(h.cols_used, h.columns_used_h()):
                y = y0 + along * col
                for r, z in enumerate(h.rows_z):
                    out.append(
                        Bolt(
                            f"{side}_{end}_c{c}_r{r}",
                            wall,
                            f"{side}_{end}",
                            x,
                            y,
                            z,
                            inward,
                        )
                    )
    return out


def keepouts(
    d: Datums = D,
) -> list[tuple[str, int, tuple[float, float], tuple[float, float]]]:
    """(label, wall index, station Y span, station Z span) of each insert.

    The footprint of the widest feature at the bearing face, which is the
    counterbore. Published because ``bay_walls`` has to keep the brain-band
    louvre off it, the same way it keeps the field off the panel's own edges: a
    slot through a structural bolt is not a louvre, it is a missing bolt.
    """
    r = WALL_CBORE_D / 2
    return [
        (b.label, b.wall, (b.y - r, b.y + r), (b.z - r, b.z + r))
        for b in bolts(d)
    ]


# ============================================================ geometry


def insert_cutter(b: Bolt) -> Part:
    """The hole one insert needs, as a solid to SUBTRACT, in STATION coordinates.

    Two coaxial cylinders on the bolt axis, cut from the wall's OUTER face
    inward: the counterbore that swallows the insert's head so the bearing face
    stays flat, and the pilot the knife thread bites into.

    Station coordinates rather than panel-local, and for the same reason
    ``gusset_prism`` is: the panel that receives this brings it into its own
    frame with ``to_local``, so the cut and the check that verifies the cut are
    built from one solid and cannot drift apart.
    """
    over = WALL_CBORE_DEPTH      # overshoot the face so the boolean is clean
    cbore = Cylinder(
        WALL_CBORE_D / 2,
        WALL_CBORE_DEPTH + over,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, -over)))
    pilot = Cylinder(
        INSERT_PILOT_D / 2,
        WALL_CBORE_DEPTH + WALL_PILOT_DEPTH + over,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, -over)))
    return b.plane() * (cbore + pilot)


def insert_cutters(wall: int, d: Datums = D) -> Part | None:
    """Every insert hole in one wall, unioned, in station coordinates.

    ``None`` when this wall takes no bolts, so a caller subtracts nothing rather
    than subtracting an empty solid.
    """
    cut = None
    for b in bolts(d):
        if b.wall != wall:
            continue
        c = insert_cutter(b)
        cut = c if cut is None else cut + c
    return cut


# ============================================================ floor or hang


@dataclass(frozen=True)
class FloorState:
    """Whether the carcass stands on its plinth once the bolts are in."""

    on_floor: bool
    lift: float             # how far the carcass would have to rise, mm
    band: tuple[float, float]
    lowest: float
    highest: float

    @property
    def room_down(self) -> float:
        """How far the machine may be wound DOWN before the lowest row leaves
        the wall's usable band."""
        return self.lowest - self.band[0]

    @property
    def room_up(self) -> float:
        """The same, wound UP, against the highest row."""
        return self.band[1] - self.highest


def floor_state(d: Datums = D) -> FloorState:
    """Does the plinth sit on the floor at the fitted ``table_h``, or would the
    carcass hang off its bolts.

    The carcass is built floor-up, so its birch band is fixed in Z. The hole
    rows are fixed in Z by the levelled machine. If every row falls inside the
    band, the two agree and the plinth carries the carcass with the bolts doing
    nothing but bracing. If a row falls outside it, the only way to reach that
    row is to lift the carcass off its plinth, which is hanging, and which is
    the failure this function exists to catch before somebody drills a leg.
    """
    band = wall_band(d)
    rows = d.s.leg_holes.rows_z
    lowest, highest = min(rows), max(rows)
    lift = max(band[0] - lowest, highest - band[1], 0.0)
    return FloorState(lift <= 0.0, lift, band, lowest, highest)


# ============================================================ checks


def check_leg_joint(d: Datums = D) -> list[str]:
    """Constraints this joint owns.

    What it does NOT own: whether an insert lands on top of a dado, a slide
    mount or the louvre. Those features belong to ``bay_walls`` and it checks
    them against ``keepouts`` there, where the feature geometry actually lives.
    """
    s = d.s
    h = s.leg_holes
    notes: list[str] = []

    # -- the pattern is unmeasured, and every hole below moves with it -------
    from stations.cnc_shapeoko.params import CONFIDENCE

    if CONFIDENCE.get("leg_holes") != "measured":
        notes.append(
            f"every one of the {len(bolts(d))} inserts below is placed off a leg "
            "pattern that is not measured. Every insert in the end walls moves "
            "when it is."
        )

    # -- the bolt itself ----------------------------------------------------
    length = bolt_length()
    if length is None:
        notes.append(
            f"no stock bolt length works: the stack under the head is "
            f"{WASHER_T + h.walls_in_path * s.leg_wall_t + WALL_CBORE_DEPTH:.1f}mm "
            f"and the thread has to land between {ENGAGE_MIN:.1f}mm of engagement "
            f"and {INSERT_LEN - ENGAGE_CLEAR:.1f}mm before it bottoms out in the "
            f"insert. Stock lengths tried: {BOLT_STOCK_LEN}."
        )

    if s.leg_wall_t < BOLT_D / 2:
        notes.append(
            f"the leg wall is {s.leg_wall_t:.1f}mm under an {BOLT_THREAD} bolt "
            "head. The flat washer is not optional: 10-gauge steel dimples under "
            "a bare head and the joint goes slack the first time the machine is "
            "run."
        )

    if h.walls_in_path > 1:
        notes.append(
            f"the bolt is modelled crossing {h.walls_in_path} leg walls, so the "
            "leg is a CLOSED section and the bolt spans its cavity. A closed tube "
            "pulled up on an M6 dents before it clamps: it needs a crush sleeve "
            "or an internal spacer through the cavity, which is hardware nobody "
            "has bought. Confirm the leg section with the calipers before "
            "ordering bolts."
        )

    # -- the insert in an 18mm panel ----------------------------------------
    depth = WALL_CBORE_DEPTH + WALL_PILOT_DEPTH
    if depth > T - WALL_BACK_MIN:
        notes.append(
            f"the insert bore is {depth:.1f}mm into {T:.0f}mm of birch, leaving "
            f"{T - depth:.1f}mm behind it against a {WALL_BACK_MIN:.1f}mm floor. "
            "The bay face of an end wall is a finished face and it will bulge."
        )

    if INSERT_PILOT_D >= INSERT_OD:
        notes.append(
            f"the pilot bore is {INSERT_PILOT_D:.2f}mm against a "
            f"{INSERT_OD:.2f}mm insert. There is nothing for the knife thread to "
            "bite."
        )

    # -- every bolt has to land in birch ------------------------------------
    band = wall_band(d)
    y_lo, y_hi = d.end_wall_y
    y_land = edge_margin()
    for b in bolts(d):
        if not (band[0] <= b.z <= band[1]):
            where = (
                "the toe-kick void, where the plinth is set back from the leg "
                "face and there is no birch at all"
                if b.z < d.deck_z[0]
                else "the deck's edge lamination"
                if b.z < d.deck_top
                else "above the top cap"
            )
            notes.append(
                f"bolt {b.label} lands at z={b.z:.0f} and the end wall's usable "
                f"band is {band[0]:.0f}..{band[1]:.0f}. It is in {where}. An "
                "insert there is not a joint: either that row goes unused, or the "
                "carcass grows to meet it. It must NOT be answered by driving an "
                "insert into the deck's edge, which is end grain across the "
                "laminations and the weakest hole in the station."
            )
        if not (y_lo + y_land <= b.y <= y_hi - y_land):
            short = max(y_lo + y_land - b.y, b.y - (y_hi - y_land))
            notes.append(
                f"bolt {b.label} lands at y={b.y:.2f} and the end wall runs "
                f"{y_lo:.0f}..{y_hi:.0f} with a {y_land:.2f}mm land "
                f"({EDGE_LAND:.1f} of birch plus the pilot's radius): short by "
                f"{short:.2f}mm. The column reaches past the birch."
            )

    # -- what the columns assume about the leg itself ------------------------
    # The datum sits on the leg's inner corner: birch runs inward from it, steel
    # runs outward. A bolt needs both, so every column has to sit in the band
    # where the leg's own flange reaches BACK across that corner into the opening.
    # The leg is an angle (2026-09-03), so there IS such a flange; how wide it is
    # is the last unmeasured thing on this joint.
    reach = h.span_h + WALL_CBORE_D / 2
    proven = max(h.columns_h()) + h.hole_d / 2
    if h.flange_w is None:
        notes.append(
            f"the angle's flange width is not measured, so the columns still "
            f"ASSUME the leg's bolt face reaches {reach:.1f}mm into the opening "
            f"past its inner corner ({h.cols_per_leg} columns from "
            f"{h.edge_off:.1f}mm at {h.pitch_h:.1f}mm pitch, plus the "
            "counterbore's radius). Inboard of that corner is birch and outboard "
            "of it is steel, so that band is the only place a bolt has both. The "
            f"pattern's own existence proves {proven:.1f}mm of it: the outer hole "
            "is drilled in that flange and its own edge has to be. What is open "
            f"is the remaining {reach - proven:.1f}mm. Measure the angle's flange "
            "and write it into params.LegHoles.flange_w."
        )
    elif h.flange_reach < reach:
        notes.append(
            f"the angle's flange is {h.flange_w:.1f}mm wide from the heel, "
            f"{h.flange_reach:.1f}mm past the inner face, and the columns need "
            f"{reach:.1f}mm of it (columns {h.cols_used} of {h.cols_per_leg} from "
            f"{h.edge_off:.1f}mm at {h.pitch_h:.1f}mm pitch, plus the counterbore's radius). The "
            f"outer column overhangs the steel by {reach - h.flange_reach:.1f}mm, so "
            "its bolt has birch behind it and nothing in front. Either that column "
            "goes unused and the joint runs one column per leg, or the counterbore "
            "comes down to fit inside the flange."
        )

    # -- the levelling swing, resolved by order rather than by a slot -------
    swing = s.table_h_with_feet - s.table_h_no_feet
    st = floor_state(d)
    if not st.on_floor:
        notes.append(
            f"the carcass would HANG: the hole rows run {st.lowest:.0f}.."
            f"{st.highest:.0f} and the end wall's usable band is "
            f"{st.band[0]:.0f}..{st.band[1]:.0f}, so reaching a row means lifting "
            f"the carcass {st.lift:.0f}mm off its plinth. The plinth carries the "
            "carcass and the machine's feet are its only floor contact; a bolt "
            "that has to take the carcass's weight is the wrong joint."
        )
    else:
        notes.append(
            f"LEVEL FIRST, THEN BOLT, standing note. The inserts are fixed, "
            f"where the old leg ties were slotted for the {swing:.0f}mm levelling "
            "swing. The carcass is built floor-up and its plinth sits on the "
            "floor; the machine is levelled on its own feet; only then do the "
            f"{len(bolts(d))} bolts go in. Re-levelling later means loosening "
            f"them all, not adjusting them. Winding the feet leaves "
            f"{st.room_down:.0f}mm of room down and {st.room_up:.0f}mm up before "
            f"a row leaves the wall's {st.band[0]:.0f}..{st.band[1]:.0f} band, "
            f"against the {swing:.0f}mm the feet can travel end to end. Expected, "
            "and worth knowing before the feet are wound to an extreme."
        )

    # -- the pattern is off the bench grid, and that is the machine's fault -
    if not on_grid(h.pitch_v) or not on_grid(h.pitch_h):
        notes.append(
            f"the leg pattern is {h.pitch_h:.0f} x {h.pitch_v:.0f}mm and the "
            f"bench grid is {GRID:.0f}mm. Not fixable: it is the machine. Nothing "
            "bolted to a leg can be grid-indexed on both axes, which is why the "
            "insert positions are read off the leg and never snapped."
        )

    return notes


# ============================================================ main

if __name__ == "__main__":
    d = D
    h = d.s.leg_holes
    bs = bolts(d)
    length = bolt_length()

    print(f"{NAME}: {len(bs)} bolts, {len(bs)} inserts, no manufactured part")
    print(
        f"  bolt      {BOLT_THREAD} x {length:.0f} {BOLT_HEAD}, "
        f"{bolt_engagement(length):.1f}mm of thread in the insert"
        if length
        else "  bolt      NO STOCK LENGTH WORKS, see check"
    )
    print(f"  washer    {WASHER} {WASHER_D:.0f} OD x {WASHER_T:.1f}, under the head")
    print(f"  insert    {INSERT_PART}")
    print(f"            {INSERT_THREAD} internal, {INSERT_OD:.2f} OD x {INSERT_LEN:.2f} long")
    print(f"            pilot {INSERT_PILOT_D:.3f}mm, driven with {INSERT_DRIVER}")
    print(f"            alternate: {INSERT_ALT}")
    print(
        f"  wall hole counterbore {WALL_CBORE_D:.1f} x {WALL_CBORE_DEPTH:.1f} deep, "
        f"then pilot {INSERT_PILOT_D:.3f} x {WALL_PILOT_DEPTH:.1f} deep. "
        f"BLIND: {T - WALL_CBORE_DEPTH - WALL_PILOT_DEPTH:.1f}mm of birch behind it, "
        "nothing through the panel."
    )
    print(
        f"  leg       {h.hole_d:.0f}mm thru, {h.pitch_h:.0f} x {h.pitch_v:.0f} pitch, "
        f"{h.cols_per_leg} columns from {h.edge_off:.0f}mm in, rows at "
        f"{[f'{z:.0f}' for z in h.rows_z]}, faces {h.faces}, "
        f"{h.walls_in_path} wall in the bolt's path"
    )

    st = floor_state(d)
    print(
        f"\nfloor or hang: plinth {'ON THE FLOOR' if st.on_floor else 'OFF THE FLOOR'}"
        f", rows {st.lowest:.0f}..{st.highest:.0f} inside the wall band "
        f"{st.band[0]:.0f}..{st.band[1]:.0f}"
        f"   ({st.room_down:.0f}mm of wind-down, {st.room_up:.0f}mm of wind-up)"
    )

    print("\nbolt axes, station coordinates, +X to the right")
    for b in bs:
        hx, hy, hz = b.head_face()
        tx, ty, tz = b.tip(length)
        print(
            f"  {b.label:<20} wall {b.wall}  "
            f"({hx:8.2f}, {hy:7.1f}, {hz:6.1f}) -> "
            f"({tx:8.2f}, {ty:7.1f}, {tz:6.1f})   "
            f"axis {'+X' if b.inward > 0 else '-X'}"
        )

    found = check_leg_joint(d)
    if found:
        print(f"\n{len(found)} leg-joint note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno leg-joint constraint violations")
