"""Stock rack: one comb under the cap, nine grooves in the deck.

WHAT IT IS
==========

RULING 11, 2026-09-03, rewrote this part. The rack that indexes HALF blanks on
edge in the stock bay is two things, and only one of them is a part:

  * the TOP COMB, one birch bar ``RAIL_T`` thick and ``RAIL_H`` tall, spanning
    the stock bay's clear width between the two dividers, its top edge tongued
    ``TONGUE_D`` up into a housing ``top_cap`` cuts in the cap's underside.
    Its lower edge carries the comb: one slot per blank at
    ``Station.sheet_pitch``, open at the bottom, so a blank's top passes
    through it. Its front face is the STOCK header: the word is V-carved
    (C17) into the comb's spine, the birch between the slot tips and the
    cap, on the ``VCARVE`` layer, and the painted comb goes back on the
    machine on the first and last slot's capsule tips (``REGISTER``), the
    only voids it has. The spine is 14mm, so the word is ``callout_h``
    tall rather than the station's 12: ``callouts.fit_height`` sizes it to
    the band.
  * nine GROOVES, ``GROOVE_D`` deep, milled into ``base_deck``'s top face at
    the same pitch, open at the front, so a blank drops in at deck level and
    slides out FORWARD. There is no bottom rail. ``base_deck`` cuts them to
    this module's lines (``slot_x_station``, ``groove_y``), so the deck and
    the comb cannot drift apart.

This module emits the comb and owns every number of the rack. The deck and
the cap read from here rather than the other way round, which is why it
imports nothing from either.

WHY THE COMB HANGS FROM THE CAP AND NOT THE DIVIDERS
====================================================

The ruling left the housing to "top_cap or the dividers as the geometry
needs". The geometry decided. The cap's tie screw runs down each divider's
centreline with its first fastener ``SCREW_END_INSET`` from the open front,
and a divider housing on the comb's line would put a ``DADO_D`` pocket floor
inside a millimetre of that screw's clearance hole. So the comb's ENDS butt
the dividers' stock faces and its TOP edge is housed in the cap, the member
it hangs from anyway. Its length is therefore the bay's clear width exactly,
and the deck-level housings ``bay_walls`` used to cut are gone.

CUTS: APERTURE VERSUS JOINERY
=============================

The slots are apertures: a blank passes through one and nothing seats in its
closed end, so that end is a full capsule, ``corner_r = SLOT_R``, declared on
the call. The comb's two end faces and its top tongue are joinery: square,
uncut; the dogbones live in the cap's housing, where ``top_cap`` drops a
relief on each corner its trench makes with the dividers' housings. The deck
grooves are apertures in the same sense (a blank's edge rides in one, nothing
seats against the end) and get a capsule rear end; the front end runs off the
deck's edge.

THE HEIGHT CHECK, AS RULED
==========================

A 600 blank in a 5mm groove tops out ``sheet_slot[1] - GROOVE_D`` above
deck_top, against a cap underside ``bay_h`` above it. The comb, ``RAIL_H``
tall under the cap, holds the blank's top ``comb_engage`` deep, and its slot
runs ``slot_depth`` up from its bottom edge: the engagement, one clearance,
and the capsule's own radius, so the blank's flat top never rides up into the
round. ``check_stock_rails`` measures all of this off the solids, and the
assembly carries one blank as a reference solid so the deck groove and the
comb slot are checked as housings rather than trusted.

PANEL CONVENTION
================

Flat like a panel: origin at the comb's lower-left corner as the operator
sees it, +X along the bay, +Y up, +Z through the thickness. Local Z = T is the
operator-facing face, so the DXF's CUT layer is the face the callout is carved
into. ``plane`` stands it up with local +Z toward the open front.
"""

from __future__ import annotations

from math import sqrt

from build123d import Align, Axis, Box, Compound, Face, GeomType, Location, Part, Plane

from lib.house import GRID, on_grid
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    HOUSE_ENGAGE,
    ROUTER_D,
    T,
    Datums,
    export_part,
    flat_pattern,
    panel,
    through_slot,
)
from stations.cnc_shapeoko.parts import callouts

__all__ = [
    "LABEL",
    "BLANK_LABEL",
    "CALLOUT",
    "callout_h",
    "callout_centre",
    "callouts_local",
    "register",
    "export",
    "RAIL_H",
    "RAIL_T",
    "TONGUE_D",
    "SLOT_W",
    "SLOT_R",
    "GROOVE_D",
    "pitch",
    "slot_count",
    "rail_length",
    "blank_h",
    "tooth_w",
    "end_land",
    "slot_centres",
    "slot_x_station",
    "comb_y",
    "comb_z",
    "blank_top_z",
    "comb_engage",
    "slot_depth",
    "spine_w",
    "groove_y",
    "plane",
    "build",
    "place",
    "blank_ref",
    "placed_all",
    "joint_table",
    "callout_face",
    "check_stock_rails",
]

D: Datums = DATUMS


# ================================================================ parameters
# Everything specific to the rack. No dimension literal appears below this
# block; each value names where it came from.

LABEL = "stock_rail_top"
"""The comb's name in the assembly and on its exports."""

BLANK_LABEL = "stock_blank_ref"
"""The reference blank the assembly carries in slot 0."""

CALLOUT = "STOCK"
"""V-carved into ``callout_face``'s spine (C17). SOURCE: brief v8, the STOCK
header. CONFIDENCE: spec. Its height is ``callout_h``, derived."""

RAIL_H = GRID * 2
"""Visible height of the comb under the cap: the header. Two grid modules.
SOURCE: bay_walls.RACK_RAIL_H before ruling 11 (2026-09-03); the ruling moved
the comb to the cap and kept the section. CONFIDENCE: spec."""

RAIL_T = T
"""Comb thickness. SOURCE: carcass.T. The cap's housing is DADO_W = T + DADO_FIT
wide, the house fit for a T member."""

TONGUE_D = HOUSE_ENGAGE
"""How far the comb's top edge enters the cap's underside housing. SOURCE:
carcass.HOUSE_ENGAGE, the house third-of-thickness every housed edge uses."""

BLANK_T = T
"""The blank the comb is sized for. SOURCE: house.CARCASS_T via carcass.T;
ruling 11 sizes the slots for an 18mm blank. CONFIDENCE: spec."""

SLOT_CLEAR = 1.0
"""Clearance each side of a blank in its slot, and over its top. SOURCE: ruling
11, 2026-09-03, "18 blank + 1/side". CONFIDENCE: spec."""

SLOT_W = BLANK_T + 2 * SLOT_CLEAR
"""Slot width across the bay, and the deck groove's width."""

SLOT_R = SLOT_W / 2
"""Capsule radius of a slot's closed end and a groove's rear end: the aperture
rule, roundest available. SOURCE: carcass.through_slot's own docstring."""

GROOVE_D = 5.0
"""Depth of the grooves base_deck mills for a blank's lower edge. SOURCE: ruling
11, 2026-09-03, "5mm-deep grooves". CONFIDENCE: spec."""

GROOVE_REAR_LAND = GRID
"""Birch between a groove's rear end and the spine housing's line. One module,
so the housing floor is never undercut by a groove. SOURCE: house grid.
CONFIDENCE: choice."""

COMB_INSET = GRID
"""Comb front face set back from the open front. One module: the cap's housing
keeps a front wall, so a blank dragged out forward cannot drag the header with
it, and the header sits in the cap's shadow line rather than proud of the
dividers' raw edges. SOURCE: house grid; the ruling names no inset.
CONFIDENCE: choice."""

RULED_PITCH = GRID * 2
RULED_COUNT = 9
"""What ruling 11 says the rack holds: 40mm pitch, 9 blanks. Held here so the
derived count is checked against the ruling rather than trusted."""

SPINE_MIN = ROUTER_D
"""Least birch between a slot's capsule tip and the tongue: one cutter diameter,
the same floor bay_walls.LOUVRE_RIB_MIN uses. CONFIDENCE: choice."""

OVERSHOOT = SLOT_W
"""How far the slot cutter runs past the comb's bottom edge so its own rounded
open end is fully out of the material. One slot width, which exceeds the
capsule radius. SOURCE: geometry of through_slot's capsule."""

EPS = 1e-6
"""Comparison tolerance, the same figure assembly.BAND_EPS uses."""


# ================================================================ derivations


def pitch(d: Datums = D) -> float:
    """Slot pitch. SOURCE: params.Station.sheet_pitch."""
    return d.s.sheet_pitch


def slot_count(d: Datums = D) -> int:
    """Slots in the comb, grooves in the deck: the bay's HALF-blank capacity,
    from Datums, the same arithmetic check.py prints in its header."""
    return d.stock_capacity


def rail_length(d: Datums = D) -> float:
    """The comb's length: the clear bay, divider face to divider face."""
    return d.stock_clear_w


def blank_h() -> float:
    """The comb's flat blank height: the header plus its tongue into the cap."""
    return RAIL_H + TONGUE_D


def tooth_w(d: Datums = D) -> float:
    """Birch left between two slots."""
    return pitch(d) - SLOT_W


def end_land(d: Datums = D) -> float:
    """Birch between the outermost slot and the divider's face, on each end,
    with the comb centred in the clear span."""
    n = slot_count(d)
    return (d.stock_clear_w - (n - 1) * pitch(d) - SLOT_W) / 2


def slot_centres(d: Datums = D) -> list[float]:
    """Comb-local X of each slot centre, comb centred in the clear span."""
    n = slot_count(d)
    x0 = end_land(d) + SLOT_R
    return [x0 + i * pitch(d) for i in range(n)]


def slot_x_station(d: Datums = D) -> list[float]:
    """Station X of each slot centre: the rack's pitch line, which the deck
    grooves are cut to."""
    return [d.stock_x[0] + x for x in slot_centres(d)]


def comb_y(d: Datums = D) -> tuple[float, float]:
    """Station Y span of the comb: front face to rear face."""
    return (d.y_front + COMB_INSET, d.y_front + COMB_INSET + RAIL_T)


def comb_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span of the comb's visible height: bottom edge to the cap's
    underside. The tongue continues TONGUE_D above."""
    return (d.top_z[0] - RAIL_H, d.top_z[0])


def blank_top_z(d: Datums = D) -> float:
    """Station Z of a blank's top edge when it stands in its deck groove."""
    return d.deck_top - GROOVE_D + d.s.sheet_slot[1]


def comb_engage(d: Datums = D) -> float:
    """How far a standing blank's top reaches up into the comb."""
    return blank_top_z(d) - comb_z(d)[0]


def slot_depth(d: Datums = D) -> float:
    """Slot depth from the comb's bottom edge, DERIVED not chosen: the blank's
    engagement, one clearance over it, and the capsule's own radius, so the
    straight run of the slot ends a clearance above the blank's flat top and
    the round never bears on it."""
    return comb_engage(d) + SLOT_CLEAR + SLOT_R


def spine_w(d: Datums = D) -> float:
    """Birch between a slot's capsule tip and the top of the header, below the
    tongue: the comb's spine."""
    return RAIL_H - slot_depth(d)


def blank_lift(d: Datums = D) -> float:
    """How far a blank can rise inside its slot before its top corners meet the
    capsule: the clearance plus the rise a flat 18 edge gets on a round of
    SLOT_R. Reported, not judged: the blank leaves forward by ruling."""
    return SLOT_CLEAR + (SLOT_R - sqrt(SLOT_R**2 - (BLANK_T / 2) ** 2))


def groove_y(d: Datums = D) -> tuple[float, float]:
    """Station Y span of a deck groove: open at the front edge, capsule tip one
    land ahead of the spine's line."""
    return (d.y_front, d.y_spine - GROOVE_REAR_LAND)


def callout_h(d: Datums = D) -> float:
    """Cap height of the header word: the station's CALLOUT_H if the spine
    has room for it with a clearance above and below, else what the spine
    leaves."""
    return callouts.fit_height(spine_w(d))


def callout_centre(d: Datums = D) -> tuple[float, float]:
    """Comb-local centre of the word: the middle of the span, the middle of
    the spine between the slot tips and the cap's underside."""
    return (rail_length(d) / 2, slot_depth(d) + spine_w(d) / 2)


def callouts_local(d: Datums = D) -> list[callouts.Callout]:
    """The comb's one word, on the Z = T face the operator sees."""
    return [callouts.Callout(CALLOUT, callout_centre(d), height=callout_h(d))]


def register(d: Datums = D) -> callouts.Register:
    """The second fixture's datums: the first and last slot's capsule tips,
    which a SLOT_W pin seats in. The comb has no holes; its slots are open
    at the bottom, so the pin bears on the tip's half circle."""
    xs = slot_centres(d)
    y = slot_depth(d) - SLOT_R
    return callouts.Register(
        (xs[0], y, SLOT_W), (xs[-1], y, SLOT_W), "the first and last slot's capsule tips"
    )


def plane(d: Datums = D) -> Plane:
    """The comb's frame in station space: local +X along the bay, local +Y up
    from the comb's bottom edge, local +Z toward the open front. Local Z = 0 is
    the rear face."""
    return Plane(
        origin=(d.stock_x[0], comb_y(d)[1], comb_z(d)[0]),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


# ================================================================ build


def build(d: Datums = D, *, carve: bool = True) -> Part:
    """The comb, flat in its own frame, the header word carved into its spine
    unless ``carve`` is off (the DXF's CUT layers are read off the un-carved
    blank)."""
    p = panel(rail_length(d), blank_h(), RAIL_T)
    depth = slot_depth(d)
    length = depth + OVERSHOOT
    cy = depth - length / 2          # runs from -OVERSHOOT up to the slot's tip
    cutters = None
    for cx in slot_centres(d):
        # APERTURE: a blank passes through it, nothing seats in its closed end,
        # so the end is a full capsule. Declared here, on the call.
        c = through_slot(
            (cx, cy), length, SLOT_W, thickness=RAIL_T, angle=90.0, corner_r=SLOT_R
        )
        cutters = c if cutters is None else cutters + c
    if cutters is not None:
        p -= cutters
    if carve:
        p = callouts.carve(p, callouts_local(d), thickness=RAIL_T)
    return p


def place(flat: Part | None = None, d: Datums = D) -> Part:
    """The comb in station coordinates, hanging from the cap."""
    flat = build(d) if flat is None else flat
    return plane(d) * flat


def blank_ref(d: Datums = D, index: int = 0) -> Part:
    """The HALF blank the rack is for, standing in slot ``index`` flush with the
    open front, as a reference solid: lower edge in its deck groove, top edge
    through the comb's slot. Station coordinates."""
    depth, height = d.s.sheet_slot
    cx = slot_x_station(d)[index]
    return Box(
        BLANK_T, depth, height, align=(Align.CENTER, Align.MIN, Align.MIN)
    ).moved(Location((cx, d.y_front, d.deck_top - GROOVE_D)))


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, part): the comb, and one blank as a reference solid."""
    return [
        (LABEL, "carcass", place(d=d)),
        (BLANK_LABEL, "reference", blank_ref(d)),
    ]


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples.

    Tuples rather than ``assembly.Joint`` so this module never imports the
    assembly that imports it; the same shape ``drawers.joint_table`` uses.
    The comb is housed in the cap along Z and butts both dividers; the
    reference blank is housed in the deck's groove and in the comb's slot, so
    a missing or short cut on either shows up as a housing fault."""
    z_cap = d.top_z[0]
    z_comb = comb_z(d)[0]
    return [
        ("top_cap", LABEL, "housing", "z", z_cap, z_cap + TONGUE_D,
         "comb's top tongue up into the cap's underside housing"),
        ("lungs_stock", LABEL, "butt", None, 0.0, 0.0,
         "comb's left end butts the divider's stock face; the cap locates it"),
        ("stock_hands", LABEL, "butt", None, 0.0, 0.0,
         "comb's right end butts the divider's stock face; the cap locates it"),
        ("base_deck", BLANK_LABEL, "housing", "z", d.deck_top - GROOVE_D, d.deck_top,
         "a blank's lower edge in its deck groove"),
        (LABEL, BLANK_LABEL, "housing", "z", z_comb, z_comb + slot_depth(d),
         "a blank's top edge through the comb's slot"),
    ]


def callout_face(d: Datums = D) -> Face:
    """The comb's operator-facing face, in station coordinates: the header C17
    V-carves STOCK into. Its outward normal is -Y."""
    return place(d=d).faces().filter_by(Axis.Y).sort_by(Axis.Y)[0]


# ================================================================ checks


def check_stock_rails(d: Datums = D) -> list[str]:
    """What the rack has to be true for, measured off the numbers and the
    solid. The deck groove and the cap housing are checked in the assembly,
    against the reference blank and the comb; see ``joint_table``."""
    s = d.s
    notes: list[str] = []
    n = slot_count(d)
    p = pitch(d)

    # -- the ruling, held against the derivation ------------------------------
    if abs(p - RULED_PITCH) > EPS or not on_grid(p):
        notes.append(
            f"sheet_pitch is {p:.1f}, not the {RULED_PITCH:.0f} ruling 11 set "
            "(two grid modules)"
        )
    if n != RULED_COUNT:
        notes.append(
            f"the bay holds {n} blanks at {p:.0f} pitch in {d.stock_clear_w:.1f} "
            f"clear; ruling 11 said {RULED_COUNT}. The ruling was written for "
            "the bay as it stood; re-rule before cutting."
        )

    # -- the comb has teeth, and lands ----------------------------------------
    tw = tooth_w(d)
    if tw < ROUTER_D:
        notes.append(
            f"the comb has no teeth: a {SLOT_W:.1f}mm slot at {p:.1f}mm pitch "
            f"leaves {tw:.1f}mm of birch between slots, under one cutter"
        )
    if end_land(d) < ROUTER_D:
        notes.append(
            f"the outermost slot leaves {end_land(d):.2f}mm to the divider face, "
            "under one cutter"
        )
    if spine_w(d) < SPINE_MIN:
        notes.append(
            f"a {slot_depth(d):.1f}mm slot in a {RAIL_H:.0f}mm comb leaves a "
            f"{spine_w(d):.1f}mm spine, under the {SPINE_MIN:.2f}mm floor"
        )

    # -- a blank stands in the groove, reaches the comb, and clears the cap --
    top = blank_top_z(d)
    ceiling = d.top_z[0]
    if top > ceiling - EPS:
        notes.append(
            f"a {s.sheet_slot[1]:.0f}mm blank in a {GROOVE_D:.0f}mm groove reaches "
            f"z {top:.1f}, at or above the cap's underside at {ceiling:.1f}"
        )
    if comb_engage(d) <= 0:
        notes.append(
            f"the comb's bottom edge at z {comb_z(d)[0]:.1f} hangs above a blank's "
            f"top at {top:.1f}: it indexes nothing"
        )
    if GROOVE_D >= d.t:
        notes.append(f"a {GROOVE_D:.0f}mm groove goes through a {d.t:.0f}mm deck")
    gy0, gy1 = groove_y(d)
    if gy1 <= gy0 or gy1 > d.y_spine - EPS:
        notes.append(
            f"deck groove y {gy0:.1f}..{gy1:.1f} runs into the spine's line at "
            f"{d.y_spine:.1f}"
        )

    # -- geometry as built ----------------------------------------------------
    flat = build(d)
    bb = flat.bounding_box()
    if (
        abs(bb.size.X - rail_length(d)) > EPS
        or abs(bb.size.Y - blank_h()) > EPS
        or abs(bb.size.Z - RAIL_T) > EPS
    ):
        notes.append(
            f"flat comb is {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}, not "
            f"{rail_length(d):.2f} x {blank_h():.2f} x {RAIL_T:.2f}"
        )
    # the two ends are joinery: square, uncut, the full section
    for x in (bb.min.X, bb.max.X):
        ends = [f for f in flat.faces() if abs(f.center().X - x) < EPS]
        if len(ends) != 1 or abs(ends[0].area - blank_h() * RAIL_T) > EPS:
            notes.append(
                f"the end at x {x:.1f} is not one square {blank_h():.0f} x "
                f"{RAIL_T:.0f} face"
            )
    # the top edge is joinery too: one flat face, the tongue
    tops = [f for f in flat.faces() if abs(f.center().Y - bb.max.Y) < EPS]
    if len(tops) != 1 or abs(tops[0].area - rail_length(d) * RAIL_T) > EPS:
        notes.append("the comb's top edge is not one uncut tongue face")
    # every slot ends in a capsule: one cylindrical face per slot, SLOT_R
    rounds = flat.faces().filter_by(GeomType.CYLINDER)
    if len(rounds) < n:
        notes.append(
            f"{len(rounds)} cylindrical faces for {n} slots: a slot end is not a "
            "capsule"
        )
    # the slot's straight run ends a clearance above the blank's top
    tip = comb_z(d)[0] + slot_depth(d)
    if tip - SLOT_R < top + SLOT_CLEAR - EPS:
        notes.append(
            f"the slot's straight run ends at z {tip - SLOT_R:.1f}, under a blank's "
            f"top at {top:.1f} plus {SLOT_CLEAR:.0f} clearance"
        )

    up = place(flat, d)
    pb = up.bounding_box()
    x0, x1 = d.stock_x
    if abs(pb.min.X - x0) > EPS or abs(pb.max.X - x1) > EPS:
        notes.append(
            f"comb spans x {pb.min.X:.2f}..{pb.max.X:.2f}, not the clear bay's "
            f"{x0:.2f}..{x1:.2f}"
        )
    cy0, cy1 = comb_y(d)
    if abs(pb.min.Y - cy0) > EPS or abs(pb.max.Y - cy1) > EPS:
        notes.append(f"comb sits at y {pb.min.Y:.1f}..{pb.max.Y:.1f}, not {cy0:.1f}..{cy1:.1f}")
    if abs(pb.min.Z - comb_z(d)[0]) > EPS or abs(pb.max.Z - (ceiling + TONGUE_D)) > EPS:
        notes.append(
            f"comb spans z {pb.min.Z:.1f}..{pb.max.Z:.1f}, not the cap's underside "
            f"less {RAIL_H:.0f} up to its housing at {ceiling + TONGUE_D:.1f}"
        )
    cf = callout_face(d)
    if abs(cf.center().Y - cy0) > EPS:
        notes.append("the callout face is not the comb's front face")

    # -- the header word sits in the spine, below the cap, and the comb goes
    # back on its two slot tips. The tongue is not a cut, so it is declared.
    notes += callouts.check_callouts(
        build(d),
        callouts_local(d),
        register(d),
        size=(rail_length(d), blank_h()),
        thickness=RAIL_T,
        keep_clear=[((0.0, RAIL_H), (rail_length(d), blank_h()))],
        label=LABEL,
    )

    return notes


# ================================================================ export


def export(d: Datums = D) -> list:
    """STEP + DXF for the comb: CUT off the un-carved blank, VCARVE and
    REGISTER for the second fixture; the STEP carries the carve."""
    layers = flat_pattern(build(d, carve=False))
    layers.update(callouts.layers(callouts_local(d), register(d), width=rail_length(d)))
    return export_part(build(d), LABEL, layers=layers)


# ================================================================ main

if __name__ == "__main__":
    d = D
    flat = build(d)
    n = slot_count(d)

    print("STOCK RACK: one comb under the cap, grooves in the deck")
    print(
        f"  comb blank {rail_length(d):.1f} x {blank_h():.0f} x {RAIL_T:.0f}, "
        f"{RAIL_H:.0f} showing under the cap, {TONGUE_D:.0f}mm tongue into it"
    )
    print(
        f"  comb: {n} slots {SLOT_W:.1f} wide, {slot_depth(d):.1f} deep, capsule tip "
        f"r {SLOT_R:.1f}, at {pitch(d):.1f} pitch; tooth {tooth_w(d):.1f}, end land "
        f"{end_land(d):.2f}, spine {spine_w(d):.1f}"
    )
    gy0, gy1 = groove_y(d)
    print(
        f"  deck: {n} grooves {SLOT_W:.1f} wide, {GROOVE_D:.0f} deep, "
        f"y {gy0:.0f}..{gy1:.1f}, at station x "
        f"{', '.join(f'{x:.2f}' for x in slot_x_station(d))}"
    )
    print(
        f"  a {d.s.sheet_slot[1]:.0f} blank stands at z {d.deck_top - GROOVE_D:.1f}, "
        f"top at {blank_top_z(d):.1f}, {comb_engage(d):.1f} into the comb, "
        f"{d.top_z[0] - blank_top_z(d):.1f} under the cap; it can lift "
        f"{blank_lift(d):.1f} before the capsule stops it"
    )

    placed = []
    for label, group, part in placed_all(d):
        placed.append(part)
        pb = part.bounding_box()
        print(
            f"\n  {label} ({group})"
            f"\n    placed  x {pb.min.X:.1f}..{pb.max.X:.1f}   y {pb.min.Y:.1f}..{pb.max.Y:.1f}"
            f"   z {pb.min.Z:.1f}..{pb.max.Z:.1f}   volume {part.volume / 1000:.0f} cm3"
        )

    cf = callout_face(d)
    print(
        f"\n  callout face ({CALLOUT}, -Y): centre "
        f"({cf.center().X:.1f}, {cf.center().Y:.1f}, {cf.center().Z:.1f}), "
        f"{cf.area / 100:.0f}cm2"
    )
    for line in callouts.describe(callouts_local(d), register(d)):
        print(f"  {line}")

    ab = Compound(children=placed).bounding_box()
    print(
        f"\n  comb and blank placed: x {ab.min.X:.1f}..{ab.max.X:.1f}  "
        f"y {ab.min.Y:.1f}..{ab.max.Y:.1f}  z {ab.min.Z:.1f}..{ab.max.Z:.1f}"
    )

    print("\n  wrote:")
    for p_ in export(d):
        print(f"    {p_}")

    found = check_stock_rails(d)
    if found:
        print(f"\n{len(found)} stock rack note(s):")
        for n_ in found:
            print(f"  - {n_}")
    else:
        print("\nno stock rack constraint violations")
