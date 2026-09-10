"""Brain-band partition: the sealed/signal wall, with its one transit.

WHAT THIS PART IS
=================

One 18mm Baltic birch panel standing in the brain band on the plane
``Datums.brain_split_x``, running from the spine's rear face to the rear
door's landing and the full band height from the deck to the top cap's
underside. Its left face looks at sealed power (contactor, fused inlet, WAGO
rails); its right face looks at exposed signal (mini PC, motion controller,
station microcontroller's parked seat, ethernet bulkhead) at the operator's corner.

It is a BARRIER, not a brace. The carcass is stiff without it; what it does is
turn "mains behind a driver, signal behind clear acrylic" from a wiring habit
into a panel. A student opening the rear door sees the signal side and cannot
reach the mains side without a driver, which is the brief's sentence made of
plywood.

THE JOINT, AND THE ONE OPENING
==============================

    front edge   tongue into the spine's REAR-face housing, which
                 ``spine_panel`` already cuts at ``PARTITION_HOUSE_D`` deep
                 and interrupts once, at the split transit
    rear edge    butts the rear door's landing: the door is one carcass
                 thickness and occupies the last ``t`` of the band, so the
                 panel stops at ``y_rear - t``
    bottom edge  butts the deck's top face. The deck cuts no housing for it.
    top edge     butts the cap's underside. The cap cuts no housing for it.

The tongue is ``PARTITION_HOUSE_D`` deep, not ``HOUSE_ENGAGE``: the spine
chose a half-depth housing so its rear-face cut and the wall-2 housing on its
front face leave half the panel between them, and the tongue is exactly what
that housing receives. It is JOINERY, so it stays square; the dogbones are the
spine's, at the four stopped corners of its housing.

The transit is the ONE opening. Every low-voltage lead that crosses from
sealed to signal -- the current transformer on the spindle leg, the feed for
the stock wash -- passes here and nowhere else. It is a notch in the front
edge, ``SPLIT_TRANSIT_H`` tall at ``SPLIT_TRANSIT_Z`` above the deck, the same
two numbers the spine used to interrupt its housing, so the notch and the gap
are one feature drawn from one place. The notch reaches ``TRANSIT_D`` past the
spine's rear face so the leads have a window and not a slit. It is an
APERTURE: nothing seats in it, so its inner end is a capsule.

NO HOLES FOR HARDWARE
=====================

Nothing is drilled through this panel. A bulkhead, a gland or a fastener in
the partition is a second way across the split, and the split is worth having
only while there is one. The mains side is reached with a driver from the
door; the panel itself is held by its tongue and by the door landing on its
rear edge.

INTERFACE, for the parts cut alongside this one:

    spine_panel   housing at ``brain_split_x + t/2``, ``DADO_W`` wide,
                  ``PARTITION_HOUSE_D`` deep in the REAR face, interrupted
                  over ``SPLIT_TRANSIT_Z +- SPLIT_TRANSIT_H/2``; this panel's
                  tongue and notch are read off those constants
    rear_door     lands on this panel's rear edge at ``y_rear - t``
    top_cap       the exhaust field stops at ``brain_split_x``, this panel's
                  LEFT face, so no slot opens over the signal side

PANEL CONVENTION
================

Drawn flat: local origin at the blank's lower-left corner, local +X runs from
the spine toward the rear door, local +Y runs up, local +Z through the
thickness from the sealed face (Z = 0) to the signal face (Z = t). Placed with
``plane()``, whose origin is the panel's DATUM corner: the spine's rear face,
the deck's top, the split plane. The blank reaches ahead of that corner by the
tongue, which ``blank_offset`` carries, the way the spine's does.
"""

from __future__ import annotations

from build123d import Location, Part, Plane

from lib.house import GRID, SHEET_4X8, fits
from stations.cnc_shapeoko.carcass import (
    DADO_W,
    DATUMS,
    Datums,
    export_part,
    panel,
    through_slot,
)
from stations.cnc_shapeoko.parts.spine_panel import (
    PARTITION_HOUSE_D,
    SPLIT_TRANSIT_H,
    SPLIT_TRANSIT_Z,
    signal_x,
)

PART_NAME = "brain_partition"


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# Shared boundaries come from Datums, the housing and the transit from
# spine_panel, material from house.py.
# ====================================================================

TONGUE = PARTITION_HOUSE_D
"""How far the front edge enters the spine. SOURCE: spine_panel.PARTITION_HOUSE_D,
the depth of the housing it seats in. CONFIDENCE: derived. Not HOUSE_ENGAGE:
the spine's housing is half-depth on purpose, and a tongue longer than its
housing is a panel that does not seat."""

DOOR_LANDING = DATUMS.t
"""What the rear edge gives up to the rear door. SOURCE: task C03 ruling
2026-09-03, "bay_brain_d less the door's carcass_t landing"; the door is one
carcass thickness and sits inside the leg opening, in the last t of the band.
CONFIDENCE: ruling."""

TRANSIT_H = SPLIT_TRANSIT_H
"""Height of the transit notch. SOURCE: spine_panel.SPLIT_TRANSIT_H, the
interruption in the housing. CONFIDENCE: derived. The notch and the gap are
one feature; this file does not restate the number."""

TRANSIT_Z = SPLIT_TRANSIT_Z
"""Centre height of the transit above deck_top. SOURCE:
spine_panel.SPLIT_TRANSIT_Z. CONFIDENCE: derived."""

TRANSIT_D = GRID * 2
"""How far the transit reaches into the panel past the spine's rear face.
SOURCE: design, on the bench grid; the one number here that no ruling or
datasheet supplies. CONFIDENCE: design. Two modules, the same as the height,
so the window the leads pass through is a square with a capsule end rather
than a slit. A CT lead and a stock-wash feed are small; this leaves room for
a third run without a second opening."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the
# block above and on Datums.
# ====================================================================


def clear_span(d: Datums = DATUMS) -> float:
    """Datum-face to datum-face along Y: the spine's rear face to the rear
    door's landing. ``bay_brain_d`` less one thickness, by construction of
    ``Datums.y_spine``."""
    return d.brain_d - DOOR_LANDING


def blank_size(d: Datums = DATUMS) -> tuple[float, float]:
    """Cut size of the blank: the clear span plus the tongue at the housed
    front edge, and the full bay height, because top and bottom butt."""
    return (clear_span(d) + TONGUE, d.bay_h)


def blank_offset(d: Datums = DATUMS) -> tuple[float, float]:
    """Where the blank's lower-left corner sits in ``plane()``'s local frame.
    The blank reaches ahead of the datum corner by the tongue."""
    return (-TONGUE, 0.0)


def plane(d: Datums = DATUMS) -> Plane:
    """The partition's frame in station space: local +X to station +Y, local
    +Y up, thickness into +X, origin at the datum corner (split plane, spine
    rear face, deck top). The same orientation as ``Datums.wall_plane``."""
    return Plane(
        origin=(d.brain_split_x, d.y_spine + d.t, d.deck_top),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )


def transit_local(d: Datums = DATUMS) -> tuple[tuple[float, float], float, float]:
    """The transit cutter, in blank-local terms: (centre, length, width).

    Centred on the blank's front edge and running ``TONGUE + TRANSIT_D`` into
    it, so half the slot hangs off the edge and the notch is open at the
    mouth. Width is the transit height. The capsule end is the inner one.
    """
    reach = TONGUE + TRANSIT_D
    return ((0.0, TRANSIT_Z), 2 * reach, TRANSIT_H)


def transit_z(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Z span of the transit opening."""
    return (d.deck_top + TRANSIT_Z - TRANSIT_H / 2, d.deck_top + TRANSIT_Z + TRANSIT_H / 2)


def build(d: Datums = DATUMS) -> Part:
    """The partition, flat in panel-local coordinates."""
    w, h = blank_size(d)
    part = panel(w, h, d.t)

    # The front tongue IS the blank's first TONGUE of width: nothing is cut for
    # it. Joinery, so it stays square; the spine relieves its own corners.

    # The transit: an aperture, so a capsule at its inner end. The slot's
    # front half lies off the blank, which makes the notch open at the edge.
    centre, length, width = transit_local(d)
    part -= through_slot(
        centre, length, width, thickness=d.t, corner_r=width / 2
    )

    # No holes for hardware. See the module docstring.

    return part


def place(part: Part | None = None, d: Datums = DATUMS) -> Part:
    """The flat panel stood up in station coordinates."""
    part = build(d) if part is None else part
    dx, dy = blank_offset(d)
    return plane(d) * part.moved(Location((dx, dy, 0)))


# ---------------------------------------------------------------- checks


def check_brain_partition(d: Datums = DATUMS) -> list[str]:
    """What this part has to be true for. The assembly's interference check
    owns whether it seats in the spine; these are the things that are wrong
    before the solids are compared."""
    notes: list[str] = []
    w, h = blank_size(d)
    centre, length, width = transit_local(d)
    reach = length / 2
    r = width / 2

    if clear_span(d) <= 0:
        notes.append(
            f"the brain band is {d.brain_d:.0f}mm deep and the door landing is "
            f"{DOOR_LANDING:.0f}mm: there is no span left for the partition"
        )
        return notes

    # the tongue is what the spine's housing receives, and only that
    if abs(TONGUE - PARTITION_HOUSE_D) > 1e-6:
        notes.append(
            f"the tongue is {TONGUE:.1f}mm and the spine's housing is "
            f"{PARTITION_HOUSE_D:.1f}mm deep: the panel either bottoms out short "
            "or stands proud of the spine"
        )
    if DADO_W < d.t:
        notes.append(
            f"the spine's housing is {DADO_W:.1f}mm wide and this panel is "
            f"{d.t:.1f}mm thick: it does not enter"
        )

    # the transit stays inside the panel and clear of the door landing
    if TRANSIT_Z - TRANSIT_H / 2 <= 0 or TRANSIT_Z + TRANSIT_H / 2 >= d.bay_h:
        notes.append(
            f"the transit ({TRANSIT_Z:.0f} +- {TRANSIT_H / 2:.0f} above the deck) "
            f"runs off the {d.bay_h:.0f}mm panel"
        )
    if reach - TONGUE >= clear_span(d):
        notes.append(
            f"the transit reaches {reach - TONGUE:.0f}mm past the spine into a "
            f"{clear_span(d):.0f}mm span: it opens onto the rear door"
        )

    # the straight part of the capsule has to cover the whole tongue, or the
    # tongue's notch edge is a curve and the housing's stopped end is a line
    if reach - r < TONGUE:
        notes.append(
            f"the transit's capsule starts {reach - r:.1f}mm into the blank and "
            f"the tongue is {TONGUE:.1f}mm: the notch does not clear the housing "
            "gap squarely. TRANSIT_D has to be at least the transit's half-height."
        )

    # the partition is the boundary the zones are stated against
    if abs(d.brain_split_x + d.t - signal_x(d)[0]) > 1e-6:
        notes.append(
            f"the signal zone starts at x={signal_x(d)[0]:.1f} and this panel's "
            f"right face is at x={d.brain_split_x + d.t:.1f}: the zone map and "
            "the partition disagree about where the split is"
        )

    travel = min(d.s.travel_x, d.s.travel_y)
    if max(w, h) > travel:
        notes.append(
            f"partition blank {w:.0f} x {h:.0f} exceeds the machine's own "
            f"{travel:.0f}mm travel: it cannot be cut on the Shapeoko itself. "
            "Cut on the track saw or Shaper Origin instead, by ruling, "
            "2026-09-02. Expected, and worth knowing before it goes to either tool."
        )
    if not fits((w, h), SHEET_4X8):
        notes.append(
            f"partition blank {w:.0f} x {h:.0f} does not come out of a 4x8 Baltic sheet"
        )

    return notes


if __name__ == "__main__":
    d = DATUMS
    flat = build(d)
    bb = flat.bounding_box()
    placed = place(flat, d)
    pbb = placed.bounding_box()
    w, h = blank_size(d)
    z0, z1 = transit_z(d)

    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {d.t:.1f}")
    print(
        f"  flat bbox   {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}"
        f"   volume {flat.volume / 1000:.1f} cm3"
        f"  ({100 * flat.volume / (w * h * d.t):.1f}% of the blank)"
    )
    print(
        f"  placed      x {pbb.min.X:.1f}..{pbb.max.X:.1f}  "
        f"y {pbb.min.Y:.1f}..{pbb.max.Y:.1f}  z {pbb.min.Z:.1f}..{pbb.max.Z:.1f}"
    )
    print(
        f"  clear span  y {d.y_spine + d.t:.1f}..{d.y_rear - DOOR_LANDING:.1f} "
        f"({clear_span(d):.1f} = brain {d.brain_d:.0f} less door {DOOR_LANDING:.0f})"
        f"   tongue {TONGUE:.1f} into the spine, top and bottom butt"
    )
    print(
        f"  split at x={d.brain_split_x:.1f}   sealed side is Z=0, signal side is Z=t"
    )
    print(
        f"  transit     z {z0:.1f}..{z1:.1f} ({TRANSIT_H:.0f} tall), "
        f"{TRANSIT_D:.0f} past the spine's rear face, capsule r {TRANSIT_H / 2:.0f}; "
        "the only opening, no hardware holes"
    )

    found = check_brain_partition(d)
    if found:
        print(f"\n{len(found)} partition note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno partition constraint violations")

    for p in export_part(flat, PART_NAME):
        print(f"wrote {p}")
