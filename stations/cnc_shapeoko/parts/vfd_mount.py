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
    rear face    the drive hangs on it: two E-Z LOK 400-M3 inserts (the leg
                 joint's family at the drive's slot size) at ``vfd_mount_pitch``.

Screw heads sit in counterbores on the DRIVE face, under the drive, so the
drive's back lands flat and the plate cannot come off while the drive is on
it. The drive comes off first, by design.

WHAT IS MEASURED, WHAT IS NOT
=============================

The drive was calipered 2026-09-02 (``params.vfd_box``, ``vfd_fan``) and its
back was read 2026-09-09 (Jared, calipers, drive open on the bench): the two
hanging holes are KEYHOLES, the pair runs ACROSS the back, 3.34in on centre
(84.84, not Carbide's round 85), the top of each keyhole 2.287in (58.09)
below the top of the case, each 0.614in (15.60) tall, the upper narrow slot
0.15in (3.81) wide and the lower round 0.28in (7.11). So the drive hangs on a
screw whose SHANK passes 3.81 and whose HEAD passes 7.11: an M3 pan head
(DIN 7985: head 6.0, shank 3.0), not the M6 the leg joint uses, in an M3
knife-thread insert of the same family (E-Z LOK 400-M3). Everything on the
drive's back is measured; what is NOT is the case's sheet thickness, which
sets how far the head stands off the plate (``HANG_STANDOFF``, an assumption
carried as a build note).

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

from lib.house import GRID, SHEET_4X8, fits
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
from math import ceil

from stations.cnc_shapeoko.parts.leg_joint import INSERT_PART  # noqa: F401  (the M6 family this part's M3 belongs to)

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
"""Centre distance of the drive's two keyholes. SOURCE: params.vfd_mount_pitch,
MEASURED 2026-09-09 (3.34in = 84.84; Carbide's doc says 85). CONFIDENCE:
measured."""

MOUNT_PAIR_HORIZONTAL = True
"""The pair runs ACROSS the drive, level, centred on its width. MEASURED
2026-09-09 (Jared, calipers): a level pair 3.34in on centre. CONFIDENCE:
measured."""

KEYHOLE_TOP_DROP = 58.09
KEYHOLE_H = 15.60
KEYHOLE_SLOT_W = 3.81
KEYHOLE_ROUND_D = 7.11
"""The drive's hanging keyholes. MEASURED 2026-09-09 (Jared, calipers): top of
the keyhole 2.287in below the top of the case; keyhole 0.614in tall; upper
(narrow) slot 0.15in wide; lower (round) 0.28in. The head goes in at the round
end and the drive drops until the screw's shank sits at the slot's top.
CONFIDENCE: measured."""

HANG_SCREW = "M3 x 10 pan head, DIN 7985, stainless"
HANG_SCREW_D = 3.0
HANG_HEAD_D = 6.0
HANG_HEAD_H = 2.4
"""What hangs the drive. The shank must pass the 3.81 slot and the head the
7.11 round: M3 (3.0 shank, 6.0 head) does both with 0.4 and 0.55 a side. M4
(4.0) does not pass the slot; a #6 pan (6.9 head) passes the round by 0.1,
too little for a caliper reading. Head figures: DIN 7985 M3 (dk 6.0, k 2.4).
CONFIDENCE: measured (the slot), datasheet (the screw)."""

HANG_STANDOFF = 2.0
"""How far the head's underside stands off the plate when the drive hangs:
the case's back sheet plus play. The sheet is NOT measured (~1.2 assumed); 2.0
leaves the head bearing on the sheet with room and is a build note (drive the
screw to a 2mm feeler under the head), not geometry. CONFIDENCE: assumption,
MEASURE the sheet."""

MOUNT_DROP = KEYHOLE_TOP_DROP + HANG_SCREW_D / 2
"""Screw centres below the drive's TOP face when it hangs: the shank rests at
the slot's top end, so the centre is the keyhole's top plus the shank's
radius. DERIVED from measured numbers: 59.6."""

MOUNT_DROP_MEASURED = True
"""The keyholes were read 2026-09-09; every MEASURE note on them is retired."""

MOUNT_SLOT_W: float = KEYHOLE_SLOT_W
"""Width of the drive's slot: the keyhole's upper leg. MEASURED 2026-09-09."""

INSERT = "E-Z LOK 400-M3, E-Z Knife brass insert for hard wood"
INSERT_DRIVER = "E-Z LOK 500-006 drive tool (the chart's tool for the 400-M3)"
INSERT_PILOT_D = 6.747
INSERT_LEN = 9.53
INSERT_OD = 7.94
"""The hanging screws' insert: the leg joint's FAMILY (E-Z Knife 400, brass,
hard wood) at M3, not its SKU: the drive's slot takes a 3mm shank and nothing
larger. Pilot 17/64in from E-Z LOK's own drill chart for wood (400-M3, drive
tool 500-006). Installed length 9.53 from a retail listing of the same part;
the OD is NOT published on the page or the chart and 5/16in is taken from the
17/64 pilot family (400-004/006/008 share it). Confirm both on the packet
before drilling. CONFIDENCE: datasheet (pilot, tool), medium (length),
inference (OD)."""

BOLT = HANG_SCREW
"""Kept under the old name for the report. The M6 pan head and DIN 125 washer
of 2026-09-03 are gone: no washer, the head alone passes the round and bears
on the sheet around the slot (1.1 a side)."""

CBORE_CLEAR = 1.3
WALL_CBORE_D = INSERT_OD + CBORE_CLEAR
WALL_CBORE_DEPTH = 1.5
WALL_PILOT_DEPTH = INSERT_LEN + GRID / 20
WALL_BACK_MIN = 2.0
"""The insert's seat in the plate, the leg joint's rules (a 1.5 seat so the
head finishes below the bearing face, the pilot one millimetre deeper than
the insert, 2mm of birch behind a blind bore) applied to the M3 insert's own
numbers. Named as leg_joint names them so the arithmetic below reads the
same. CONFIDENCE: derived."""

INSERT_PLIES = max(1, ceil((WALL_CBORE_DEPTH + WALL_PILOT_DEPTH + WALL_BACK_MIN) / PLATE_T))
INSERT_SUBSTRATE_T = INSERT_PLIES * PLATE_T
"""Birch behind each hanging-screw insert, and how many plies of house stock
make it. DERIVED, the same rule as the leg joint's end wall: seat plus pilot
plus 2mm behind. With the M3 insert (2026-09-09) that is 1.5 + 10.5 + 2 =
14.0, still over one 12mm ply by 2, so each insert still seats in a local
DOUBLER PAD -- a second ply laminated to the plate behind the two boss holes
before the inserts are driven. Dropping the 1.5 seat would bring it to 12.5,
still over; the pad stays. A build step the flat-panel model carries as a
note, not a second solid."""


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
    if WALL_CBORE_DEPTH + WALL_PILOT_DEPTH >= INSERT_SUBSTRATE_T:
        notes.append(
            f"the insert pilot is {WALL_CBORE_DEPTH + WALL_PILOT_DEPTH:.1f} deep "
            f"in a {INSERT_SUBSTRATE_T:.0f} plate: it is a through hole"
        )
    if INSERT_PLIES > 1:
        notes.append(
            f"INSERT DOUBLER PADS, standing note. Each of the two hanging-bolt "
            f"inserts seats in {INSERT_PLIES} plies of {PLATE_T:.0f}mm birch "
            f"({INSERT_SUBSTRATE_T:.0f}mm): a doubler pad laminated to the plate "
            f"behind the boss hole, because a blind {INSERT} bores "
            f"{WALL_CBORE_DEPTH + WALL_PILOT_DEPTH:.1f}mm and one {PLATE_T:.0f}mm "
            "ply cannot hold it at 12mm house stock. Laminate the pads, then "
            "drill. Expected, and worth knowing before the plate is cut."
        )

    # -- the keyholes, measured: the screw passes the slot and the round
    if not MOUNT_DROP_MEASURED:
        notes.append("the drive's keyholes are not measured; the insert bores are provisional")
    if HANG_SCREW_D > KEYHOLE_SLOT_W - 0.5:
        notes.append(
            f"the hanging screw's {HANG_SCREW_D:.1f} shank does not pass the drive's "
            f"{KEYHOLE_SLOT_W:.2f} slot with 0.25 a side"
        )
    if HANG_HEAD_D > KEYHOLE_ROUND_D - 0.5:
        notes.append(
            f"the hanging screw's {HANG_HEAD_D:.1f} head does not pass the drive's "
            f"{KEYHOLE_ROUND_D:.2f} round with 0.25 a side"
        )
    if HANG_HEAD_D <= KEYHOLE_SLOT_W + 1.0:
        notes.append(
            f"the {HANG_HEAD_D:.1f} head bears less than 0.5 a side on the sheet "
            f"around a {KEYHOLE_SLOT_W:.2f} slot"
        )
    notes.append(
        f"VFD HANG, standing note. Keyholes MEASURED 2026-09-09: pair across, "
        f"{MOUNT_PITCH:.2f} on centre, top {KEYHOLE_TOP_DROP:.2f} below the case top, "
        f"{KEYHOLE_H:.2f} tall, slot {KEYHOLE_SLOT_W:.2f} / round {KEYHOLE_ROUND_D:.2f}. "
        f"Screw centres {MOUNT_DROP:.1f} below the top (shank at the slot's end). "
        f"{HANG_SCREW} in {INSERT}; drive it to a {HANG_STANDOFF:.0f}mm feeler under "
        "the head (the case sheet is not measured: MEASURE it, then set the "
        "standoff to sheet + 0.5). No washer: nothing wider than the head passes "
        "the round. Expected, and worth knowing before the inserts are driven."
    )

    if not fits((w, h), SHEET_4X8):
        notes.append(f"plate blank {w:.0f} x {h:.0f} does not come out of a 4x8 sheet")

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
