"""VFD mount: the standoff plate the drive hangs on, and the drive as a keep-out.

WHAT THIS PART IS
=================

Two solids, one of birch and one of air.

``vfd_mount``     One 18mm Baltic birch plate screwed flat to the spine's REAR
                  face at the left end of the brain band, standing on the deck,
                  the drive's own footprint wide. The drive hangs on it by the
                  two slotted holes on its back, at ``vfd_mount_pitch``. It is
                  a STANDOFF plate: it holds the drive one carcass thickness off
                  the spine, so the drive's back is never against the panel the
                  front bays' pass-throughs come out of, and it is the thing
                  that comes off if the drive is ever changed, rather than the
                  spine.

``vfd_keepout``   The drive itself, ``vfd_box`` in Carbide's stock vertical
                  orientation, as a reference solid. Not birch, not cut, not on
                  the BOM: it is in the assembly so that every later layout in
                  the brain band collides with the drive honestly instead of
                  with a note in a docstring. The mast plate, the mains
                  backplate and the signal mounts all get their first fit-check
                  against this box.

WHERE IT STANDS, AND WHY THE AIR IS WHERE IT IS
==============================================

Ruling 2026-09-02: the drive vents THROUGH THE PANEL. Its vented LEFT face,
carrying both fans, looks at the louvre field in the left end wall from
``vfd_panel_standoff`` away, and Carbide's 300mm is paid for on the far side of
that louvre. ``Datums.vfd_x`` already places the body from that ruling; this
module reads it and adds nothing in X.

So the keep-out's left face is EXACTLY ``vfd_panel_standoff`` off the end
wall's inner face, and the 40mm slab between them is the only clearance the
vented face gets inside the box. That slab is AIR, and ``assembly`` checks it
stays air: no part may share volume with ``standoff_slab``. The keep-out does
not grow by ``vfd_vent_clear`` on the vented side because the ruling has
already said the 300mm is not inside the carcass; a keep-out that pretended
otherwise would sit inside the end wall and report a collision with the very
louvre that pays for it.

Vertically the drive is lifted ``LIFT`` off the deck. The deck's intake field
is directly under it (``base_deck.INTAKE_X/Y`` sit inside ``vfd_keepout_x``),
and the fans are on the drive's side, so the air that comes up through the
deck has to get out from under the drive and round to its left face before it
can do anything. The lift is that path.

THE JOINTS
==========

    front face   flat on the spine's rear face, screwed through. The spine cuts
                 nothing for it: pilots are drilled at assembly through the
                 plate's own holes, blind, inside ``Datums.vfd_keepout_x`` where
                 ``spine_panel`` keeps every crossing out. A blind screw is not
                 a pass-through; it does not bleed the chimney into a bay.
    bottom edge  butts the deck's top face. The deck cuts no housing for it.
                 Standing on the deck is what registers the plate's height, so
                 the drive lands at ``LIFT`` without anyone measuring.
    left edge    on the plane of the drive's vented face, ``Datums.vfd_x[0]``.
                 The plate reaches no further left, so no birch enters the
                 standoff slab.
    rear face    the drive hangs on it: two E-Z LOK inserts, the leg joint's
                 SKU, at ``vfd_mount_pitch``.

Screw heads sit in counterbores on the DRIVE face, under the drive, so the
drive's back lands flat and the plate cannot come off while the drive is on
it. The drive comes off first, by design.

WHAT IS MEASURED, WHAT IS NOT
=============================

The drive was calipered 2026-09-02 (``params.vfd_box``, ``vfd_fan``) and its
mount pitch is Carbide's own figure. Carbide's page says the two slotted holes
are "on the back of the VFD enclosure, spaced 85mm apart" and are used "to
hang the unit", and says nothing else: not which way the pair runs, not how
far below the top it sits, not how wide the slot is. Those three drive only
where the two insert bores land on the plate and what bolt goes through them.
They are tagged below and ``check_vfd_mount`` carries them as MEASURE until
they are read off the drive's back. The plate's outline, its place in the
band and the keep-out do not depend on any of them.

PANEL CONVENTION
================

Drawn flat: local origin at the plate's lower-left corner as seen from the
REAR of the station, local +X to station +X, local +Y up, local +Z through
the thickness from the DRIVE face (Z = 0) to the spine face (Z = t). Placed
with ``plane()``, whose origin is the datum corner: the vented-face plane,
the spine's rear face plus one thickness, the deck's top.
"""

from __future__ import annotations

from build123d import Align, Box, Location, Part, Plane

from lib.house import GRID, SHEET_5X5_BALTIC, fits
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    SCREW_CBORE_D,
    SCREW_CLEAR_D,
    SCREW_EDGE_OFF,
    Datums,
    bore,
    export_part,
    panel,
    screw_positions,
    snap_up,
)
from stations.cnc_shapeoko.parts.leg_joint import (
    INSERT_PART,
    INSERT_PILOT_D,
    WALL_CBORE_D,
    WALL_CBORE_DEPTH,
    WALL_PILOT_DEPTH,
)

PART_NAME = "vfd_mount"
KEEPOUT_NAME = "vfd_keepout"


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# The drive's body, fans, pitch and standoff come from params; where it
# stands in X from Datums; the insert from leg_joint; material from house.
# ====================================================================

PLATE_T = DATUMS.t
"""Plate thickness. SOURCE: task C04 ruling 2026-09-03, "use carcass_t birch",
not the 3mm acrylic. CONFIDENCE: ruling. It carries a hung drive and takes
knife-thread inserts; 3mm of anything would do neither."""

LIFT = GRID * 3
"""Drive bottom above deck_top. SOURCE: design, on the bench grid; no ruling
or datasheet supplies it. CONFIDENCE: design. Three modules, the plinth's own
height: the deck's intake field is under the drive and the fans are on its
side, so the air has to leave from under the body before it can reach the
vented face. A hand fits under the drive at this figure, which is also what
lifting it back onto its inserts wants."""

TOP_LAND_MIN = SCREW_EDGE_OFF
"""Least birch above the drive's top edge. SOURCE: carcass fastener edge
distance, T/2. CONFIDENCE: derived. The plate's height is then snapped UP to
the grid, so the real land is whatever the snap leaves, never less."""

MOUNT_PITCH = DATUMS.s.vfd_mount_pitch
"""Centre distance of the drive's two slotted hanging holes. SOURCE:
params.vfd_mount_pitch, Carbide 65mm ER-16 spindle doc, 85mm. CONFIDENCE:
high."""

MOUNT_PAIR_HORIZONTAL = True
"""The pair runs ACROSS the drive, level, centred on its width. SOURCE:
inference from Carbide's wording, "two slotted holes ... used to hang the
unit": a hung box hangs level from a level pair, and 85 fits across a 143mm
back with 29mm each side. CONFIDENCE: inference, NOT measured. If the pair
turns out to run up the back, this flips and the bores follow."""

MOUNT_DROP = GRID * 2
"""Slot centres below the drive's TOP face. SOURCE: none. CONFIDENCE: MEASURE,
provisional. Carbide publishes nothing and the drive has not been turned over
with calipers. The value here places the bores near the top of the back where
a hanging pair lives; it is where the bores land on the plate and nothing
else. ``check_vfd_mount`` carries it as MEASURE THIS until
``MOUNT_DROP_MEASURED`` is set."""

MOUNT_DROP_MEASURED = False
"""Flip to True when MOUNT_DROP and the slot width have been read off the
drive's back and written into the two parameters above and below."""

MOUNT_SLOT_W: float | None = None
"""Width of the drive's slotted hole. SOURCE: none, Carbide does not publish
it. CONFIDENCE: MEASURE. Decides whether the M6 bolt below passes; None until
read."""

INSERT = INSERT_PART
"""The hanging bolts' insert. SOURCE: leg_joint's SKU, E-Z LOK 400-M6, so the
station carries one insert and one driver. CONFIDENCE: ruling by reuse. The
bore is that insert's own pilot and counterbore, read from leg_joint."""

BOLT = "M6 pan head, DIN 125 washer under the head"
"""What hangs the drive. SOURCE: the insert's thread. CONFIDENCE: pending
MOUNT_SLOT_W: a pan head and washer bridge a slot, but only if M6 passes it."""

# ---- plate to spine ----------------------------------------------------
SPINE_SCREW_D = SCREW_CLEAR_D
"""Clearance through the plate for the screw into the spine. SOURCE: carcass
standard. CONFIDENCE: derived."""

SPINE_SCREW_CBORE_D = SCREW_CBORE_D
SPINE_SCREW_CBORE_DEPTH = PLATE_T / 2
"""Counterbore on the DRIVE face so the head sits below the plate and the
drive's back lands flat. SOURCE: carcass standard, half the thickness.
CONFIDENCE: derived."""

SPINE_SCREW_LEN_MAX = PLATE_T + DATUMS.t / 2
"""Longest screw that may be driven: through the plate and half into the spine.
SOURCE: derived, the spine's front face carries the dividers' housings and a
screw reaching them is a screw through a joint. CONFIDENCE: derived."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the
# block above and on Datums.
# ====================================================================


def drive_size(d: Datums = DATUMS) -> tuple[float, float, float]:
    """(w, depth, h) of the drive, stock orientation: params.vfd_box."""
    return d.s.vfd_box


def plate_size(d: Datums = DATUMS) -> tuple[float, float]:
    """Cut size of the plate: the drive's width exactly, and the lift plus
    the drive's height plus the top land, snapped up to the grid."""
    w, _dep, h = drive_size(d)
    return (w, snap_up(LIFT + h + TOP_LAND_MIN))


def top_land(d: Datums = DATUMS) -> float:
    """Birch above the drive's top edge once the snap has been taken."""
    return plate_size(d)[1] - LIFT - drive_size(d)[2]


def plate_x(d: Datums = DATUMS) -> tuple[float, float]:
    """Station X span of the plate: the drive's own, from Datums."""
    return d.vfd_x


def plate_y(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Y span of the plate: flat on the spine's rear face."""
    y0 = d.y_spine + d.t
    return (y0, y0 + PLATE_T)


def plate_z(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Z span of the plate: standing on the deck."""
    return (d.deck_top, d.deck_top + plate_size(d)[1])


def drive_y(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Y span of the drive body: off the plate's rear face."""
    y0 = plate_y(d)[1]
    return (y0, y0 + drive_size(d)[1])


def drive_z(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Z span of the drive body: LIFT above the deck."""
    z0 = d.deck_top + LIFT
    return (z0, z0 + drive_size(d)[2])


def standoff(d: Datums = DATUMS) -> float:
    """What the vented face actually gets to the end wall's inner face, as
    built. Equals vfd_panel_standoff by construction of Datums.vfd_x; the
    check says so rather than assuming it."""
    return d.vfd_x[0] - (d.wall_x[0] + d.t)


def mount_local(d: Datums = DATUMS) -> list[tuple[float, float]]:
    """The two insert centres in plate-local XY, from the drive's outline."""
    w, _dep, h = drive_size(d)
    z_top = LIFT + h
    if MOUNT_PAIR_HORIZONTAL:
        y = z_top - MOUNT_DROP
        return [(w / 2 - MOUNT_PITCH / 2, y), (w / 2 + MOUNT_PITCH / 2, y)]
    x = w / 2
    return [(x, z_top - MOUNT_DROP), (x, z_top - MOUNT_DROP - MOUNT_PITCH)]


def spine_screws_local(d: Datums = DATUMS) -> list[tuple[float, float]]:
    """Plate-to-spine screw centres in plate-local XY: two columns, each at
    the carcass edge distance, on the carcass fastener rhythm."""
    w, h = plate_size(d)
    out: list[tuple[float, float]] = []
    for x in (SCREW_EDGE_OFF, w - SCREW_EDGE_OFF):
        for p in screw_positions(h):
            out.append((x, p))
    return out


def plane(d: Datums = DATUMS) -> Plane:
    """The plate's frame in station space: local +X to station +X, local +Y
    up, thickness into -Y so the plate lands on the spine's rear face with
    its Z = 0 face looking at the drive. Origin at the datum corner: the
    vented-face plane, the plate's rear face, the deck's top."""
    return Plane(
        origin=(plate_x(d)[0], plate_y(d)[1], plate_z(d)[0]),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def build(d: Datums = DATUMS) -> Part:
    """The plate, flat in panel-local coordinates."""
    w, h = plate_size(d)
    part = panel(w, h, PLATE_T)

    # The drive's hanging bolts: insert pilot and its seat, blind from the
    # drive face. Round holes, so no corner question arises.
    for x, y in mount_local(d):
        part -= bore(x, y, INSERT_PILOT_D, thickness=PLATE_T,
                     depth=WALL_CBORE_DEPTH + WALL_PILOT_DEPTH, side="back")
        part -= bore(x, y, WALL_CBORE_D, thickness=PLATE_T,
                     depth=WALL_CBORE_DEPTH, side="back")

    # Plate to spine: through clearance, counterbored on the drive face.
    for x, y in spine_screws_local(d):
        part -= bore(x, y, SPINE_SCREW_D, thickness=PLATE_T)
        part -= bore(x, y, SPINE_SCREW_CBORE_D, thickness=PLATE_T,
                     depth=SPINE_SCREW_CBORE_DEPTH, side="back")

    # No apertures. Nothing passes through this plate but fasteners.
    return part


def place(part: Part | None = None, d: Datums = DATUMS) -> Part:
    """The flat plate stood up in station coordinates."""
    part = build(d) if part is None else part
    return plane(d) * part


def build_keepout(d: Datums = DATUMS) -> Part:
    """The drive body as a reference solid, in STATION coordinates."""
    w, dep, h = drive_size(d)
    x0 = plate_x(d)[0]
    y0 = drive_y(d)[0]
    z0 = drive_z(d)[0]
    return Box(w, dep, h, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x0, y0, z0))
    )


def standoff_slab(d: Datums = DATUMS) -> Part:
    """The air the vented face breathes through, in STATION coordinates: from
    the end wall's inner face to the drive's vented face, over the drive's own
    depth and height. ``assembly`` checks nothing occupies it."""
    x0 = d.wall_x[0] + d.t
    x1 = plate_x(d)[0]
    y0, y1 = drive_y(d)
    z0, z1 = drive_z(d)
    return Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x0, y0, z0))
    )


# ---------------------------------------------------------------- checks


def check_vfd_mount(d: Datums = DATUMS) -> list[str]:
    """What this part has to be true for. The assembly's interference check
    owns whether the plate or the drive hits a neighbour; these are the
    things that are wrong before the solids are compared."""
    notes: list[str] = []
    s = d.s
    w, h = plate_size(d)
    dw, ddep, dh = drive_size(d)
    x0, x1 = plate_x(d)
    dy0, dy1 = drive_y(d)
    dz0, dz1 = drive_z(d)

    # -- the standoff is the ruling's number, as built
    if abs(standoff(d) - s.vfd_panel_standoff) > 1e-6:
        notes.append(
            f"the vented face stands {standoff(d):.1f}mm off the end wall and "
            f"the ruling is {s.vfd_panel_standoff:.1f}mm"
        )

    # -- the drive and its plate stay in the drive's own keep-out, left of
    #    the sealed zone's electrical and of the partition
    k0, k1 = d.vfd_keepout_x
    if x0 < k0 - 1e-6 or x1 > k1 + 1e-6:
        notes.append(
            f"plate spans x {x0:.1f}..{x1:.1f}, outside the drive's keep-out "
            f"{k0:.1f}..{k1:.1f}"
        )
    if x1 > d.brain_split_x - 1e-6:
        notes.append(
            f"the drive reaches x {x1:.1f}, past the partition at {d.brain_split_x:.1f}"
        )

    # -- the drive stays inside the band: under the cap, ahead of the door
    if dz1 > d.top_z[0] - 1e-6:
        notes.append(
            f"the drive's top at z {dz1:.1f} is above the cap's underside {d.top_z[0]:.1f}"
        )
    if dy1 > d.y_rear - d.t + 1e-6:
        notes.append(
            f"the drive's back reaches y {dy1:.1f}, into the rear door's landing "
            f"at {d.y_rear - d.t:.1f}"
        )
    if h > d.bay_h:
        notes.append(f"plate is {h:.0f} tall in a {d.bay_h:.0f} bay")

    # -- the plate holds the whole drive with its land
    if top_land(d) < TOP_LAND_MIN:
        notes.append(
            f"top land is {top_land(d):.1f}mm against {TOP_LAND_MIN:.0f} minimum"
        )

    # -- the hanging bores: inside the plate with edge distance, inside the
    #    drive's outline, and clear of the spine screws
    mounts = mount_local(d)
    if abs(abs(mounts[0][0] - mounts[1][0]) + abs(mounts[0][1] - mounts[1][1]) - MOUNT_PITCH) > 1e-6:
        notes.append("the two insert bores are not vfd_mount_pitch apart")
    edge_min = INSERT_PILOT_D / 2 + SCREW_EDGE_OFF
    for mx, my in mounts:
        edge = min(mx, w - mx, my, h - my)
        if edge < edge_min:
            notes.append(
                f"an insert bore sits {edge:.1f}mm from the plate edge, under "
                f"{edge_min:.1f}"
            )
        if not (0 < mx < dw and LIFT < my < LIFT + dh):
            notes.append(
                f"an insert bore at local ({mx:.1f}, {my:.1f}) is outside the "
                "drive's back"
            )
        for sx, sy in spine_screws_local(d):
            gap = ((mx - sx) ** 2 + (my - sy) ** 2) ** 0.5
            if gap < (WALL_CBORE_D + SPINE_SCREW_CBORE_D) / 2 + SCREW_EDGE_OFF:
                notes.append(
                    f"an insert bore at local ({mx:.1f}, {my:.1f}) is {gap:.1f}mm "
                    f"from a spine screw at ({sx:.1f}, {sy:.1f})"
                )
    if WALL_CBORE_DEPTH + WALL_PILOT_DEPTH >= PLATE_T:
        notes.append(
            f"the insert pilot is {WALL_CBORE_DEPTH + WALL_PILOT_DEPTH:.1f} deep "
            f"in a {PLATE_T:.0f} plate: it is a through hole"
        )

    # -- what the drive's back has not told us yet
    if not MOUNT_DROP_MEASURED:
        notes.append(
            f"the drive's hanging slots are placed {MOUNT_DROP:.0f}mm below its "
            f"top, {'level' if MOUNT_PAIR_HORIZONTAL else 'vertical'} and centred, "
            "from Carbide's wording alone (\"two slotted holes spaced 85mm apart "
            "that can be used to hang the unit\"). MEASURE THIS on the drive's "
            "back: drop from the top, which way the pair runs, slot width. The "
            "plate's outline does not move; only the two insert bores do."
        )
    if MOUNT_SLOT_W is None:
        notes.append(
            "the drive's slot width is not measured, so whether an M6 pan head "
            "passes it is not known. MEASURE THIS; if it is under 6.5mm the "
            "insert steps down to the M5 of the same family."
        )
    elif MOUNT_SLOT_W < 6.5:
        notes.append(
            f"the drive's slot is {MOUNT_SLOT_W:.1f}mm and the bolt is M6: it "
            "does not pass. Step the insert down to M5."
        )

    if not fits((w, h), SHEET_5X5_BALTIC):
        notes.append(f"plate blank {w:.0f} x {h:.0f} does not come out of a 5x5 sheet")

    return notes


if __name__ == "__main__":
    d = DATUMS
    flat = build(d)
    placed = place(flat, d)
    bb = placed.bounding_box()
    ko = build_keepout(d)
    kb = ko.bounding_box()
    w, h = plate_size(d)
    dw, ddep, dh = drive_size(d)

    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {PLATE_T:.0f}, on the spine's rear face")
    print(
        f"  placed  x {bb.min.X:.1f}..{bb.max.X:.1f}  y {bb.min.Y:.1f}..{bb.max.Y:.1f}  "
        f"z {bb.min.Z:.1f}..{bb.max.Z:.1f}   volume {flat.volume / 1000:.1f} cm3"
    )
    print(
        f"  {KEEPOUT_NAME}: {dw:.1f} x {ddep:.1f} x {dh:.1f}  "
        f"x {kb.min.X:.1f}..{kb.max.X:.1f}  y {kb.min.Y:.1f}..{kb.max.Y:.1f}  "
        f"z {kb.min.Z:.1f}..{kb.max.Z:.1f}"
    )
    print(
        f"  vented face {standoff(d):.1f}mm off the end wall's inner face "
        f"(ruling {d.s.vfd_panel_standoff:.0f}); lifted {LIFT:.0f} off the deck; "
        f"top land {top_land(d):.1f}"
    )
    for mx, my in mount_local(d):
        print(
            f"  insert {INSERT_PILOT_D:.3f} pilot at local ({mx:.1f}, {my:.1f}) "
            f"= station ({bb.min.X + mx:.1f}, {d.deck_top + my:.1f}); pitch {MOUNT_PITCH:.0f}"
        )
    print(
        f"  {len(spine_screws_local(d))} screws into the spine, {SPINE_SCREW_D:.1f} "
        f"clear, {SPINE_SCREW_CBORE_D:.0f} x {SPINE_SCREW_CBORE_DEPTH:.0f} cbore on the "
        f"drive face; screw no longer than {SPINE_SCREW_LEN_MAX:.0f}"
    )

    found = check_vfd_mount(d)
    if found:
        print(f"\n{len(found)} vfd mount note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno vfd mount constraint violations")

    for p in export_part(flat, PART_NAME):
        print(f"wrote {p}")
    for p in export_part(ko, KEEPOUT_NAME, dxf=False):
        print(f"wrote {p}   (STEP only: reference solid, not a sheet part)")
