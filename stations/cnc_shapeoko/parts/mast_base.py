"""Mast backing plate: the steel under the mast pad. Hardware, modelled.

WHAT IT IS
==========

One square of 6mm mild steel under the top cap at the mast pad, four M8
clearance holes on the pad's own 40mm square, nuts and washers on its
underside. It is a large washer with an argument: the mast is a cantilevered
column carrying a hose under tension, a camera and a counterweight, and four
M8 washers on 18mm of birch would crush and loosen inside a term. The plate
turns four point loads into one bearing area the ply can carry.

RULED 2026-09-03: the mast rises from the LEFT REAR corner, so there is ONE
plate, under the left pad. The right pad stays cut in the cap as a spare and
gets no plate until a mast is bolted to it. ``top_cap.MAST_SIDE`` carries the
ruling and this module reads it; nothing here decides handedness.

WHY IT IS IN THE ASSEMBLY
=========================

It is not a birch part and it is not cut on the Shapeoko, so by the carcass's
own rules it would be a BOM line and nothing more. It is modelled anyway,
as a reference solid, because of where it lives: the brain band's rear-left
corner, hard against the end wall's inner face on one side and the spine's
rear face on another, with the VFD's air corridor under it. That is exactly
the neighbourhood the interference check exists for, and the first cut of
this part (C15) found that a 120mm plate centred on the pad as the cap first
drew it overlapped BOTH housed panels by a panel thickness. The pad moved;
the plate is what moved it. ``top_cap.mast_pads`` now places each pad so its
plate registers into that corner, and this module checks that it did.

Placement follows the cap: the plate's top face is the cap's underside,
``Datums.top_z[0]``, and its outline is the pad's ``span_x`` x ``span_y``,
which the cap already keeps every other cut out of.

WHAT IT EXPORTS
===============

STEP only. There is no DXF nest entry because it is not a sheet part: it goes
to the metal supplier as a size, or to the water jet from shop plate, and the
STEP carries the hole pattern either way.

PANEL CONVENTION
================

Drawn flat like a panel: origin at the plate's lower-left corner, +X and +Y
across, +Z through the thickness, top face at Z = ``PLATE_T``. Placed with
``plane()`` so the top face lands on the cap's underside.
"""

from __future__ import annotations

from build123d import Part, Plane

from stations.cnc_shapeoko.carcass import DATUMS, Datums, bore, export_part, panel
from stations.cnc_shapeoko.parts.top_cap import (
    MAST_BOLT_CLEAR_D,
    MAST_BOLT_D,
    MAST_PADS,
    MAST_PLATE,
    MAST_SIDE,
    _Pad,
    mast_pad,
)

NAME = "mast_backing_plate"


# ---------------------------------------------------------------- parameters
# Everything specific to THIS part. The pad, the bolt and the plate's square
# belong to the top cap, because the cap is what the plate has to match.

PLATE = MAST_PLATE
"""120mm square. SOURCE: C15 ruling 2026-09-03 via top_cap.MAST_PLATE.
CONFIDENCE: ruling."""

PLATE_T = 6.0
"""Thickness. SOURCE: C15 ruling 2026-09-03, mild steel, 6mm. CONFIDENCE:
ruling. Thick enough that the plate is the stiff thing and the ply is the
bearing, not the other way round."""

MATERIAL = "mild steel"
"""SOURCE: C15 ruling 2026-09-03. Not aluminium: this is a washer and it does
not care about weight. Not stainless: it lives inside a closed carcass and
gets painted with the rest."""

BOLT_CLEAR_D = MAST_BOLT_CLEAR_D
"""Same clearance as the holes in the cap above it, so the two patterns are one
pattern. 8.4mm on M8 is the ISO 273 fine series."""

BOLT_EDGE_MIN = MAST_BOLT_D * 1.5
"""Minimum bolt-centre to plate-edge distance in steel. SOURCE: structural
steel detailing convention, 1.5d for a sheared or cut edge. CONFIDENCE: high
as a rule of thumb; the plate clears it by a factor of three."""


# ---------------------------------------------------------------- derivations


def pad(d: Datums = DATUMS) -> _Pad:
    """The pad this plate backs: the mast's own."""
    return mast_pad(MAST_SIDE, d)


def origin(d: Datums = DATUMS) -> tuple[float, float]:
    """Station (x, y) of the plate's lower-left corner: the pad's footprint,
    which the cap sized to this plate."""
    p = pad(d)
    return (p.span_x[0], p.span_y[0])


def plane(d: Datums = DATUMS) -> Plane:
    """The plate's frame in station space: flat, top face on the cap's
    underside."""
    ox, oy = origin(d)
    return Plane(origin=(ox, oy, d.top_z[0] - PLATE_T), x_dir=(1, 0, 0), z_dir=(0, 0, 1))


def bolts_local(d: Datums = DATUMS) -> list[tuple[float, float]]:
    """The four bolt centres in plate-local XY."""
    ox, oy = origin(d)
    return [(bx - ox, by - oy) for bx, by in pad(d).bolts]


# ---------------------------------------------------------------- build


def build(d: Datums = DATUMS) -> Part:
    """The plate, flat in its own frame."""
    p = panel(PLATE, PLATE, PLATE_T)
    for bx, by in bolts_local(d):
        p -= bore(bx, by, BOLT_CLEAR_D, thickness=PLATE_T)
    return p


def place(flat: Part | None = None, d: Datums = DATUMS) -> Part:
    """The plate in station coordinates, under the cap."""
    flat = build(d) if flat is None else flat
    return plane(d) * flat


# ---------------------------------------------------------------- checks


def check_mast_base(d: Datums = DATUMS) -> list[str]:
    """What this plate has to be true. The assembly's interference check owns
    the question of whether it hits the spine or the end wall; these are the
    things that are wrong before the solids are even compared."""
    notes: list[str] = []

    if MAST_SIDE not in MAST_PADS:
        notes.append(
            f"the plate backs the {MAST_SIDE!r} pad and the cap cuts {MAST_PADS}"
        )
        return notes

    p = pad(d)
    ox, oy = origin(d)
    x1, y1 = ox + PLATE, oy + PLATE

    # inside the brain band: behind the spine, between the end walls' faces
    if ox < d.wall_x[0] + d.t - 1e-6 or x1 > d.wall_x[3] + 1e-6:
        notes.append(
            f"plate spans x {ox:.1f}..{x1:.1f}, outside the band's clear width "
            f"{d.wall_x[0] + d.t:.1f}..{d.wall_x[3]:.1f}: it is inside an end wall"
        )
    if oy < d.y_spine + d.t - 1e-6:
        notes.append(
            f"plate front edge at y {oy:.1f} is ahead of the spine's rear face "
            f"{d.y_spine + d.t:.1f}: it is sitting in the spine"
        )
    if y1 > d.y_rear + 1e-6:
        notes.append(f"plate rear edge at y {y1:.1f} is past y_rear {d.y_rear:.1f}")

    # the cap's footprint for this pad IS the plate; if the two disagree, the
    # louvre field and the feed slot are keeping clear of the wrong square
    if abs((p.span_x[1] - p.span_x[0]) - PLATE) > 1e-6 or abs(
        (p.span_y[1] - p.span_y[0]) - PLATE
    ) > 1e-6:
        notes.append(
            f"the cap claims {p.span_x[1] - p.span_x[0]:.0f} x "
            f"{p.span_y[1] - p.span_y[0]:.0f} for this pad and the plate is "
            f"{PLATE:.0f} square"
        )

    # bolts inside the plate with steel edge distance
    for bx, by in bolts_local(d):
        edge = min(bx, PLATE - bx, by, PLATE - by)
        if edge < BOLT_EDGE_MIN:
            notes.append(
                f"a bolt sits {edge:.1f}mm from the plate edge, under the "
                f"{BOLT_EDGE_MIN:.0f}mm (1.5d) a cut steel edge wants"
            )

    if PLATE_T >= d.bay_h:
        notes.append("the plate is taller than the bay, which is absurd")

    return notes


# ---------------------------------------------------------------- main

if __name__ == "__main__":
    d = DATUMS
    flat = build(d)
    placed = place(flat, d)
    bb = placed.bounding_box()
    mx, my, mz = d.mast_base

    print(f"{NAME}: {MATERIAL} {PLATE:.0f} x {PLATE:.0f} x {PLATE_T:.0f}, under the {MAST_SIDE} pad")
    print(
        f"  placed  x {bb.min.X:.1f}..{bb.max.X:.1f}  y {bb.min.Y:.1f}..{bb.max.Y:.1f}  "
        f"z {bb.min.Z:.1f}..{bb.max.Z:.1f}   ({bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f})"
    )
    print(f"  pad centre ({mx:.1f}, {my:.1f}) on the cap's top face z {mz:.1f}")
    for bx, by in pad(d).bolts:
        print(f"  M{MAST_BOLT_D:.0f} clearance {BOLT_CLEAR_D:.1f} at station ({bx:.1f}, {by:.1f})")
    print(
        f"  clear of the end wall face by {bb.min.X - (d.wall_x[0] + d.t):.1f}mm, "
        f"of the spine's rear face by {bb.min.Y - (d.y_spine + d.t):.1f}mm"
    )

    for w_ in export_part(flat, NAME, dxf=False):
        print(f"  wrote {w_}  {w_.stat().st_size} bytes   (STEP only: hardware, no nest entry)")

    found = check_mast_base(d)
    if found:
        print(f"\n{len(found)} mast base note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno mast base constraint violations")
