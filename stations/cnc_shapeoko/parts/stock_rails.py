"""Stock rack rails: the two comb rails that index HALF blanks on edge.

WHAT THEY ARE
=============

Two birch bars, ``T`` thick and ``RACK_RAIL_H`` tall, spanning the stock bay
between the lungs/stock divider and the stock/hands divider. Each seats in
the housings ``bay_walls._stock_face`` already cuts: a blind pocket
``DADO_W`` wide, ``DADO_D`` deep and ``RACK_RAIL_H`` tall in each divider's
bay face, standing on ``deck_top`` at each of ``bay_walls.rack_rail_y``.
The rail is the member those pockets were cut for, so its section is the
pocket's section and its length is the clear bay plus a tongue each end.

Along the top edge each rail carries the comb: one slot per HALF blank at
``Station.sheet_pitch``, sized for a blank of the carcass sheet plus a
clearance each side. ``Datums.stock_capacity`` is the slot count, which is
the same arithmetic ``check.py`` prints in its header, and this module
asserts the two agree rather than deriving a second number.

WHERE THEY SIT, AND WHY THAT IS NOT "TOP AND BOTTOM"
====================================================

The housings bay_walls cuts are BOTH at deck level: one at a quarter of the
blank's depth in from the open front, one at three quarters, so a 600 blank
is carried inboard of both its ends. They are a FRONT rail and a REAR rail.
There is no housing under the top cap, so there is no top rail in this model
and the C02 brief's "top rail front face is the STOCK header" has no face to
land on. ``callout_face`` returns the front rail's operator-facing face,
which is the nearest thing that exists; it sits on the deck, 141mm behind
the deck's front edge, and it is not a header. Adding a top pair means a
housing pair in ``bay_walls._stock_face``, which this part does not own.

CUTS: APERTURE VERSUS JOINERY
=============================

The slots are apertures. A blank stands in one; nothing seats against its
floor corners, so the floor is a full capsule, ``corner_r = SLOT_W / 2``,
declared on the call. The rail's two ends are joinery: a square tongue that
seats in a square-cornered pocket, so the end outline stays square and the
dogbones live in the divider, where bay_walls already drops a ``relief`` on
each of the pocket's four inside corners. Nothing here rounds a tongue.

WHAT THE CHECK KNOWS THAT THE BRIEF DID NOT
===========================================

Every number below is read from params, house, carcass or bay_walls. Drawn
from those numbers the comb has no teeth and the blank does not stand under
the cap, and ``check_stock_rails`` says so instead of rounding either away.
See its docstring. Those are rulings, not measurements, and they are Jared's.

PANEL CONVENTION
================

Flat like a panel: origin at the rail's lower-left corner as the operator
sees it, +X along the bay, +Y up, +Z through the thickness. Local Z = T is
the operator-facing face, so the DXF's CUT layer is the face the callout is
carved into. ``plane`` stands it up with local +Z toward the open front.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from build123d import Axis, Compound, Face, Part, Plane

from lib.house import GRID, on_grid
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    HOUSE_ENGAGE,
    STOCK_HEADROOM,
    T,
    Datums,
    export_part,
    panel,
    through_slot,
)
from stations.cnc_shapeoko.parts.bay_walls import RACK_RAIL_H, rack_rail_y

__all__ = [
    "RailSpec",
    "RAILS",
    "SLOT_W",
    "SLOT_D",
    "pitch",
    "slot_count",
    "slot_centres",
    "rail_length",
    "plane",
    "build",
    "place",
    "placed_all",
    "joint_table",
    "callout_face",
    "check_stock_rails",
]

D: Datums = DATUMS


# ================================================================ parameters
# Everything specific to the two rails. No dimension literal appears below
# this block; each value names where it came from.

RAIL_H = RACK_RAIL_H
"""Rail height. SOURCE: bay_walls.RACK_RAIL_H, the housing's height. The rail
is the member that housing was cut for, so it is the same number."""

RAIL_T = T
"""Rail thickness. SOURCE: carcass.T. The housing is DADO_W = T + DADO_FIT wide,
which is the house fit for a T member."""

TONGUE_D = DADO_D
"""How far each end enters its divider. SOURCE: carcass.DADO_D, the depth
bay_walls cuts the housing with (``groove(depth=DADO_D)``)."""

BLANK_T = T
"""The blank the comb is sized for. SOURCE: house.CARCASS_T via carcass.T;
C02 brief 2026-09-03 sizes the slots for 18mm blanks. CONFIDENCE: spec."""

SLOT_CLEAR = 1.0
"""Clearance each side of a blank in its slot. SOURCE: C02 brief 2026-09-03,
"plus 1mm clearance each side". CONFIDENCE: spec."""

SLOT_W = BLANK_T + 2 * SLOT_CLEAR
"""Slot width across the bay."""

SLOT_R = SLOT_W / 2
"""Capsule radius of the slot floor: the aperture rule, roundest available.
SOURCE: carcass.through_slot's own docstring."""

SLOT_D = STOCK_HEADROOM
"""Slot depth from the rail's top edge, DERIVED not chosen: carcass.STOCK_HEADROOM
is the lift the bay pays for so a blank clears its slot, and a slot deeper
than the lift cannot be exited. SOURCE: carcass.STOCK_HEADROOM. What is left
under the slot floor, RAIL_H - SLOT_D, is the rail's spine."""

SLOT_OVERSHOOT = SLOT_W
"""How far the slot cutter runs past the rail's top edge so its own rounded
top end is fully out of the material. One slot width, which exceeds the
capsule radius. SOURCE: geometry of through_slot's capsule."""

EPS = 1e-6
"""Comparison tolerance, the same figure assembly.BAND_EPS uses."""

CALLOUT_RAIL = "front"
"""Which rail's operator-facing face carries the STOCK callout (C17 V-carves
it). SOURCE: C02 brief 2026-09-03 names the front face of a rail. See the
module docstring: this face is on the deck, not at the bay's head."""


# ================================================================ rail table


@dataclass(frozen=True)
class RailSpec:
    """One of the two rails: its name and which of ``rack_rail_y``'s entries
    it seats at."""

    name: str
    index: int

    @property
    def label(self) -> str:
        return f"stock_rail_{self.name}"


RAILS: tuple[RailSpec, ...] = (
    RailSpec("front", 0),
    RailSpec("rear", 1),
)


# ================================================================ derivations


def pitch(d: Datums = D) -> float:
    """Slot pitch. SOURCE: params.Station.sheet_pitch."""
    return d.s.sheet_pitch


def slot_count(d: Datums = D) -> int:
    """Slots per rail: the bay's HALF-blank capacity, from Datums."""
    return d.stock_capacity


def rail_length(d: Datums = D) -> float:
    """Blank length: the clear bay plus a tongue into each divider."""
    return d.stock_clear_w + 2 * TONGUE_D


def tooth_w(d: Datums = D) -> float:
    """Birch left between two slots."""
    return pitch(d) - SLOT_W


def end_land(d: Datums = D) -> float:
    """Birch between the outermost slot and the divider's face, on each end,
    with the comb centred in the clear span."""
    n = slot_count(d)
    return (d.stock_clear_w - (n - 1) * pitch(d) - SLOT_W) / 2


def slot_centres(d: Datums = D) -> list[float]:
    """Rail-local X of each slot centre, comb centred in the clear span."""
    n = slot_count(d)
    x0 = TONGUE_D + end_land(d) + SLOT_R
    return [x0 + i * pitch(d) for i in range(n)]


def slot_floor(d: Datums = D) -> float:
    """Rail-local Y of the slot floor's lowest point."""
    return RAIL_H - SLOT_D


def blank_rise() -> float:
    """How far above the capsule's lowest point a blank's bottom corners
    bear: a flat edge on a round floor touches at +/- BLANK_T / 2."""
    return SLOT_R - sqrt(SLOT_R**2 - (BLANK_T / 2) ** 2)


def blank_stand_z(d: Datums = D) -> float:
    """Station Z of a blank's bottom edge when it stands in a slot."""
    return d.deck_top + slot_floor(d) + blank_rise()


def y_centre(spec: RailSpec, d: Datums = D) -> float:
    """Station Y of the rail's centreline: the housing's, from bay_walls."""
    return rack_rail_y(d)[spec.index]


def x_start(d: Datums = D) -> float:
    """Station X of the rail's left end, inside the lungs/stock divider."""
    return d.stock_x[0] - TONGUE_D


def plane(spec: RailSpec, d: Datums = D) -> Plane:
    """The rail's frame in station space: local +X along the bay, local +Y
    up from deck_top, local +Z toward the open front. Local Z = 0 is the rail's
    rear face, at the housing's rear wall."""
    return Plane(
        origin=(x_start(d), y_centre(spec, d) + RAIL_T / 2, d.deck_top),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


# ================================================================ build


def build(d: Datums = D) -> Part:
    """One rail, flat in its own frame. Both rails are the same part."""
    p = panel(rail_length(d), RAIL_H, RAIL_T)
    length = SLOT_D + SLOT_OVERSHOOT
    cy = slot_floor(d) + length / 2
    cutters = None
    for cx in slot_centres(d):
        # APERTURE: a blank stands in it, nothing seats in its corners, so the
        # floor is a full capsule. Declared here, on the call.
        c = through_slot(
            (cx, cy), length, SLOT_W, thickness=RAIL_T, angle=90.0, corner_r=SLOT_R
        )
        cutters = c if cutters is None else cutters + c
    if cutters is not None:
        p -= cutters
    return p


def place(spec: RailSpec, flat: Part | None = None, d: Datums = D) -> Part:
    """A rail in station coordinates, seated in its housings."""
    flat = build(d) if flat is None else flat
    return plane(spec, d) * flat


def placed_all(d: Datums = D) -> list[tuple[str, Part]]:
    """Both rails, labelled, stood up."""
    flat = build(d)
    return [(spec.label, place(spec, flat, d)) for spec in RAILS]


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples.

    Tuples rather than ``assembly.Joint`` so this module never imports the
    assembly that imports it; the same shape ``drawers.joint_table`` uses.
    Each rail is housed in both dividers along X and bears on the deck."""
    out: list[tuple] = []
    left_face = d.wall_x[1] + d.t        # lungs/stock divider, its stock face
    right_face = d.wall_x[2]             # stock/hands divider, its stock face
    for spec in RAILS:
        out.append(
            ("lungs_stock", spec.label, "housing", "x",
             left_face - HOUSE_ENGAGE, left_face,
             "rail's left tongue in the divider's blind housing")
        )
        out.append(
            ("stock_hands", spec.label, "housing", "x",
             right_face, right_face + HOUSE_ENGAGE,
             "rail's right tongue in the divider's blind housing")
        )
        out.append(
            ("base_deck", spec.label, "bearing", None, 0.0, 0.0,
             "rail stands on the deck between the dividers")
        )
    return out


def callout_face(d: Datums = D) -> Face:
    """The operator-facing face of the callout rail, in station coordinates:
    the face C17 V-carves STOCK into. Its outward normal is -Y."""
    spec = next(s for s in RAILS if s.name == CALLOUT_RAIL)
    return place(spec, d=d).faces().sort_by(Axis.Y)[0]


# ================================================================ checks


def check_stock_rails(d: Datums = D) -> list[str]:
    """What the rails have to be true for.

    Two of these fail on the numbers as they stand, and both are rulings for
    Jared rather than anything this module can decide:

    1. TEETH. A slot for an 18mm blank with 1mm a side is 20mm wide, and the
       pitch is 20mm, so the comb has 0mm of birch between slots. Either the
       pitch is two grid modules (a 20 tooth, 9 blanks) or the slot is for
       thinner stock than the carcass sheet.

    2. HEADROOM. bay_h budgets the blank plus STOCK_HEADROOM to lift it clear
       of the slot, and the rail keeps RAIL_H - SLOT_D of spine under the slot
       floor. Standing on that spine a 600 blank's top is already above the
       cap's underside. Either the rail is shorter, the spine is thinner, or
       the blank leaves forward along its slot and never lifts.
    """
    notes: list[str] = []
    n = slot_count(d)
    p = pitch(d)

    # -- the brief's own assertion: 19 at 20 -------------------------------
    if n != d.stock_capacity:
        notes.append(f"slot count {n} has drifted off Datums.stock_capacity {d.stock_capacity}")
    if not on_grid(p) or abs(p - GRID) > EPS:
        notes.append(f"slot pitch {p:.1f}mm is not the {GRID:.0f}mm bench grid")
    if n * p > d.stock_clear_w + EPS:
        notes.append(
            f"{n} slots at {p:.1f}mm need {n * p:.1f}mm and the bay is "
            f"{d.stock_clear_w:.1f}mm clear"
        )

    # -- the comb has to have teeth ----------------------------------------
    if tooth_w(d) <= EPS:
        notes.append(
            f"the comb has no teeth: a {SLOT_W:.1f}mm slot ({BLANK_T:.0f}mm blank "
            f"plus {SLOT_CLEAR:.1f}mm a side) at {p:.1f}mm pitch leaves "
            f"{tooth_w(d):.1f}mm of birch between slots and {end_land(d):.2f}mm at "
            f"each end. {n} blanks at this pitch was arithmetic, never geometry. "
            "RULING WANTED: pitch of two grid modules (a 20mm tooth, "
            f"{int(d.stock_clear_w // (2 * GRID))} blanks) or a slot for thinner "
            "stock than the carcass sheet."
        )

    # -- the rail seats in the housing bay_walls cut -----------------------
    if abs(RAIL_H - RACK_RAIL_H) > EPS:
        notes.append(f"rail height {RAIL_H:.1f} is not the housing's {RACK_RAIL_H:.1f}")
    if RAIL_T > DADO_W:
        notes.append(f"rail {RAIL_T:.1f} thick will not enter a {DADO_W:.1f} housing")
    if SLOT_D >= RAIL_H:
        notes.append(f"slot depth {SLOT_D:.1f} leaves no spine under a {RAIL_H:.1f} rail")
    if slot_floor(d) < TONGUE_D:
        notes.append("slot floor is lower than the tongue; the comb undercuts its own joint")

    # -- a blank has to stand under the cap, and leave -----------------------
    blank_h = d.s.sheet_slot[1]
    ceiling = d.top_z[0]
    top = blank_stand_z(d) + blank_h
    if top > ceiling + EPS:
        notes.append(
            f"a {blank_h:.0f}mm blank standing in the slot reaches z {top:.1f}, "
            f"{top - ceiling:.1f}mm above the cap's underside at {ceiling:.1f}: "
            f"the rail keeps {slot_floor(d):.0f}mm of spine under the slot floor and "
            f"the capsule floor lifts the blank another {blank_rise():.1f}mm, while "
            f"bay_h budgets the blank plus {STOCK_HEADROOM:.0f}mm of headroom and "
            f"nothing for a {RAIL_H:.0f}mm rail. RULING WANTED: shorter rail, "
            "thinner spine, or the blank slides out forward and never lifts."
        )
    elif ceiling - top < SLOT_D - EPS:
        notes.append(
            f"a blank stands with {ceiling - top:.1f}mm over it and needs "
            f"{SLOT_D:.0f}mm to lift clear of its slot: it comes out forward along "
            "the slot, not up"
        )

    # -- geometry as built ---------------------------------------------------
    flat = build(d)
    bb = flat.bounding_box()
    if abs(bb.size.X - rail_length(d)) > EPS or abs(bb.size.Y - RAIL_H) > EPS:
        notes.append(
            f"flat rail is {bb.size.X:.2f} x {bb.size.Y:.2f}, not "
            f"{rail_length(d):.2f} x {RAIL_H:.2f}"
        )
    # the two ends are joinery: square, uncut, the full section
    for x in (bb.min.X, bb.max.X):
        ends = [f for f in flat.faces() if abs(f.center().X - x) < EPS]
        if len(ends) != 1 or abs(ends[0].area - RAIL_H * RAIL_T) > EPS:
            notes.append(f"the tongue at x {x:.1f} is not one square {RAIL_H:.0f} x {RAIL_T:.0f} face")

    for spec in RAILS:
        pb = place(spec, flat, d).bounding_box()
        x0, x1 = d.stock_x
        if abs(pb.min.X - (x0 - TONGUE_D)) > EPS or abs(pb.max.X - (x1 + TONGUE_D)) > EPS:
            notes.append(
                f"{spec.label} spans x {pb.min.X:.2f}..{pb.max.X:.2f}, not the housings' "
                f"{x0 - TONGUE_D:.2f}..{x1 + TONGUE_D:.2f}"
            )
        yc = y_centre(spec, d)
        if abs(pb.min.Y - (yc - RAIL_T / 2)) > EPS or abs(pb.max.Y - (yc + RAIL_T / 2)) > EPS:
            notes.append(f"{spec.label} is not centred on its housing at y {yc:.1f}")
        if abs(pb.min.Z - d.deck_top) > EPS or abs(pb.max.Z - (d.deck_top + RAIL_H)) > EPS:
            notes.append(f"{spec.label} does not stand on deck_top inside its housing's height")

    return notes


# ================================================================ main

if __name__ == "__main__":
    d = D
    flat = build(d)
    n = slot_count(d)

    print("STOCK RAILS: two comb rails, one part")
    print(
        f"  blank {rail_length(d):.1f} x {RAIL_H:.0f} x {RAIL_T:.0f}, "
        f"{TONGUE_D:.0f}mm tongue each end into the dividers' housings"
    )
    print(
        f"  comb: {n} slots {SLOT_W:.1f} wide, {SLOT_D:.0f} deep, capsule floor r {SLOT_R:.1f}, "
        f"at {pitch(d):.1f} pitch; tooth {tooth_w(d):.1f}, end land {end_land(d):.2f}"
    )
    print(
        f"  a {d.s.sheet_slot[1]:.0f} blank stands at z {blank_stand_z(d):.1f}, "
        f"top at {blank_stand_z(d) + d.s.sheet_slot[1]:.1f} under a cap at {d.top_z[0]:.1f}"
    )

    written: list[str] = []
    placed = []
    for spec in RAILS:
        up = place(spec, flat, d)
        placed.append(up)
        pb = up.bounding_box()
        print(
            f"\n  {spec.label}"
            f"\n    placed  x {pb.min.X:.1f}..{pb.max.X:.1f}   y {pb.min.Y:.1f}..{pb.max.Y:.1f}"
            f"   z {pb.min.Z:.1f}..{pb.max.Z:.1f}   volume {up.volume / 1000:.0f} cm3"
        )
        for p_ in export_part(flat, spec.label):
            written.append(str(p_))

    cf = callout_face(d)
    print(
        f"\n  callout face ({CALLOUT_RAIL} rail, -Y): centre "
        f"({cf.center().X:.1f}, {cf.center().Y:.1f}, {cf.center().Z:.1f}), "
        f"{cf.area / 100:.0f}cm2"
    )

    ab = Compound(children=placed).bounding_box()
    print(
        f"\n  both rails placed: x {ab.min.X:.1f}..{ab.max.X:.1f}  "
        f"y {ab.min.Y:.1f}..{ab.max.Y:.1f}  z {ab.min.Z:.1f}..{ab.max.Z:.1f}"
    )

    print("\n  wrote:")
    for p_ in written:
        print(f"    {p_}")

    found = check_stock_rails(d)
    if found:
        print(f"\n{len(found)} stock rail note(s):")
        for n_ in found:
            print(f"  - {n_}")
    else:
        print("\nno stock rail constraint violations")
