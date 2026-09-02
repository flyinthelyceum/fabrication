"""Leg tie bracket, x4. Machined black delrin.

This is the part that makes the brief's structural claim true. Four of these
bolt the finished carcass to the four Shapeoko legs and turn four independent
splayed legs into a braced frame. Everything else in the carcass is storage
until these are in.

WHY IT IS MACHINED AND NOT SHEET
================================

The leg leans. The carcass does not. A tie between them has to be a wedge on one
face and a flat pad on the other, and a wedge is not a thing you cut out of a
flat panel. So this part leaves the panel convention behind: it is a solid block
of delrin with an angled face, and its DXF is a machining layout rather than a
laser blank.

    leg face      inclined ``leg_splay`` from vertical, bears on the leg
    pad face      vertical, bears on the outer face of the birch end wall

The legs splay outward with height: the leg frame is 1524mm across at the table
and roughly 1100 across the inner faces at the floor. The datum origin sits on
the left inner leg face AT THE FLOOR, so the clear gap between a vertical
carcass wall and a leg face opens as ``z * tan(leg_splay)``. That single fact
sets everything below, including how high up the leg the tie has to sit before
there is enough gap to hold a machinable block of delrin.

WHERE THE 52mm SWING LANDS
==========================

``table_h`` matches neither published leg configuration and the levelling feet
swing the frame by 52mm. The carcass answers that by being built from the floor
up, so its height is fixed and the leftover becomes ``Datums.top_gap``. The tie
answers it by being slotted: ``LEG_SLOT_V`` = 60mm of vertical travel against
the leg, which is 60 > 52 with room either side.

The slot runs UP THE LEG FACE, not vertically through space. It has to. A
vertical slot in an inclined face binds the moment the carcass moves, because
moving 60mm in Z along a leaning leg is also moving 6.3mm in X. Running the slot
in the plane of the face makes the joint a slide instead of a jam. The residual
that is left over -- ``LEG_SLOT_V * tan(leg_splay)``, the standoff the wedge no
longer fills once the carcass has moved -- is taken by a shim pack on the LEG
side of the joint, inside the bolted clamp where a shim belongs, not under the
pad where it would put the carcass screws in bending.

THE FASTENERS
=============

Leg side: two M6 through the leg's own 7mm holes, from OUTSIDE the leg where a
wrench can reach, with a steel backing washer against the 3.4mm leg wall
(10-gauge steel dimples under a bolt head; delrin against it will creep). Each
bolt lands in a slot in the tie and pulls up on a nut sunk into a pocket in the
pad face, so the nut travels with the slot and never has to be reached.

Only the 40mm axis of ``leg_mount_pitch`` is usable. The other axis is 65mm, and
a 60mm slot in a 65mm-pitch pattern leaves a 2mm web -- the two slots would meet
and the tie would be a fork. So each tie takes ONE hole pair per leg, and the
four ties together, at four corners, fix the frame. Written down because it is a
real constraint, not an oversight.

Carcass side: four screws driven from INSIDE the bay, through the birch, into
blind tapped holes in the delrin. Nothing is fastened from the leg side, where
there is a steel leg 20mm away and no room for a driver.

WHAT PLACING THESE FOUND
========================

This part is last because it registers to the assembled carcass AND to the
machine, and putting it where the legs are turns up a hole in the carcass: the
four bay walls are cut to ``front_bay_d``, so they stop at the spine, and the
brain band's left and right ends are open air. The front ties land on the end
walls. The rear ties land on nothing. The tie goes where the leg is, so what is
missing is a part rather than a placement, and ``check_leg_tie`` names it with
its dimensions: a brain-band end cheek per side. It also closes the electrical
band, which the brief asks for on its own account.

ASSEMBLY ORDER
==============

The carcass screws are driven from inside, so the ties go on before the bays are
loaded: the front pair from inside the lungs and hands bays, the rear pair from
inside the brain band through the rear panel opening. Then the carcass is
levelled, then the leg bolts are pulled up from outside the legs and the shim
pack is set. Bolting the legs before levelling wastes the slot.

MATERIAL NON-ARTIFICE
=====================

Black delrin, a wear material, doing a wear material's job: a machined bearing
face between steel and plywood that can be shimmed, slid and re-tightened for
the life of the machine. Nothing here is decorative and nothing is hidden. No
red: the E-stop is the whole red budget. Nothing on this part senses, gates or
stops anything -- it is pure structure.
"""

from __future__ import annotations

from math import cos, radians, sin, tan

from build123d import (
    Align,
    Box,
    Cylinder,
    Location,
    Part,
    Plane,
    Pos,
    Rot,
    SlotOverall,
    extrude,
)

from lib.house import GRID, MATERIALS
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    LEG_SLOT_V,
    SCREW_D,
    SCREW_END_INSET,
    SCREW_PILOT_D,
    T,
    export_part,
    screw_positions,
    snap_up,
)
from stations.cnc_shapeoko.params import STATION

__all__ = ["build", "placements", "placed", "check_leg_tie", "NAME", "MATERIAL"]

NAME = "leg_tie"
MATERIAL = MATERIALS["wear"]
QTY = 4


# ============================================================ parameters
# One block. Everything below derives from params.py, house.py or carcass.py.
# No dimension literal appears in the geometry underneath.

S = STATION
D = DATUMS

# -- the splay, which is the whole reason this part exists ------------------
SPLAY = S.leg_splay                 # degrees. LOW confidence, and it drives
                                    # thickness, mounting height and slot angle.
TAN_SPLAY = tan(radians(SPLAY))
COS_SPLAY = cos(radians(SPLAY))

# -- delrin the tapped holes need ------------------------------------------
TAP_DEPTH = SCREW_D * 2             # thread engagement for the carcass screws
TAP_WALL = SCREW_D                  # delrin left behind a blind tap
T_FLOOR = TAP_DEPTH + TAP_WALL      # thinnest slice of tie that is still a part

# -- where on the leg the tie can live -------------------------------------
# The gap is z * tan(splay). Below T_FLOOR / tan(splay) there is not enough gap
# to hold a tie at all, so the tie climbs until there is. Snapped to the bench
# grid, and never below the deck, whose top face is the carcass's Z datum.
Z_CLEAR = GRID                      # tie never starts right on the deck line
Z0 = snap_up(max(D.deck_top + Z_CLEAR, T_FLOOR / TAN_SPLAY)) if TAN_SPLAY else 0.0

T_MIN = Z0 * TAN_SPLAY              # gap at the bottom of the tie == its thickness

# -- leg-side fasteners ----------------------------------------------------
BOLT_D = S.leg_mount_hole_d         # 7mm thru for M6, the leg's own hole
BOLT_PITCH = S.leg_mount_pitch[0]   # the usable axis. See the docstring on 65.
SLOT_L = LEG_SLOT_V / COS_SPLAY + BOLT_D    # slot length IN THE LEG FACE, so the
                                            # bolt centre travels LEG_SLOT_V in Z
NUT_D = BOLT_D * 2                  # M6 nut across corners plus a washer
NUT_DEEP = BOLT_D                   # nut sunk clear of the pad's bearing face
POCKET_L = SLOT_L + BOLT_D          # the nut travels the length of the slot

# -- blank ------------------------------------------------------------------
EDGE = SCREW_D                      # minimum web between two features
# Width is set by getting the carcass screw columns OUTBOARD of the nut pockets:
# inset + web + half a pocket + half the bolt pitch, doubled.
W = snap_up(2 * (SCREW_END_INSET + EDGE + NUT_D / 2 + BOLT_PITCH / 2))
# Height is the nut pocket's vertical run plus a screw row above and below it.
H = snap_up(POCKET_L * COS_SPLAY + 2 * SCREW_END_INSET)
T_MAX = T_MIN + H * TAN_SPLAY       # thickness at the top of the wedge

# -- carcass-side fasteners -------------------------------------------------
# Straight off the spine's fastener rule, so a 15mm carcass re-spaces them.
SCREW_XS = screw_positions(W)
SCREW_YS = screw_positions(H)
SCREW_LEN_MIN = T + TAP_DEPTH       # birch plus engagement. Spec the next size up.

# -- commissioning ----------------------------------------------------------
SHIM_SWING = LEG_SLOT_V * TAN_SPLAY  # standoff the wedge stops filling once the
                                     # carcass has used its full travel. Delrin
                                     # shim pack, leg side, inside the clamp.

# -- placement --------------------------------------------------------------
# Four outboard corners of the carcass, from the shared datums. The tie goes
# where the LEG is; the legs are at y_front and y_rear.
CORNER_X = (D.wall_x[0], D.wall_x[3] + T)       # outer faces of the two end walls
CORNER_Y = (D.y_front, D.y_rear)

# How much vertical birch the carcass currently presents on those outer faces.
# The end walls are cut to front_bay_d, so they stop at the spine and the brain
# band's ends are open. Derived, not assumed: if the end walls ever run full
# depth this span follows them and the check below goes quiet.
CARCASS_FACE_Y = (D.y_front, D.front_bay_d)

OVER = 4 * max(W, H, T_MAX)         # cutter overshoot, so no boolean grazes a face


# ============================================================ geometry


def _leg_face_point(y: float) -> tuple[float, float]:
    """(local Y, local Z) of a point on the inclined leg face."""
    return (y, T_MIN + y * TAN_SPLAY)


def build() -> Part:
    """The tie, in its own machining frame.

        local origin   lower-left corner of the PAD face, which is the setup
                       face: pad down on the mill bed, wedge up
        local +X       0 .. W, pad width. Runs along station Y when placed.
        local +Y       0 .. H, tie height. Runs UP when placed.
        local +Z       0 .. t(y), thickness. Runs OUTBOARD when placed, so the
                       pad face at Z=0 is the face that bears on birch.

    Thickness grows with local +Y because the gap to the leg grows with height.
    """
    if TAN_SPLAY <= 0:
        raise ValueError(
            "leg_splay is zero or negative, so there is no wedge to machine and "
            "no gap between a vertical carcass wall and the leg. If the legs "
            "measure vertical the tie becomes a flat spacer and its thickness "
            "has to be measured rather than derived. See check_leg_tie()."
        )

    # -- the wedge blank ----------------------------------------------------
    part = Box(W, H, T_MAX, align=(Align.MIN, Align.MIN, Align.MIN))

    # Cut back to the leg face: the plane through (y=0, z=T_MIN) rising at SPLAY.
    part -= (
        Pos(W / 2, 0, T_MIN)
        * Rot(SPLAY, 0, 0)
        * Box(OVER, OVER, OVER, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )

    # -- leg-side slots, running UP THE FACE --------------------------------
    for cx in (W / 2 - BOLT_PITCH / 2, W / 2 + BOLT_PITCH / 2):
        cy, cz = _leg_face_point(H / 2)

        # Through slot on the leg-face normal. SlotOverall rotated 90 puts its
        # long axis on local +Y; Rot(SPLAY) lays that axis into the leg face and
        # the extrusion axis onto the face normal.
        part -= (
            Pos(cx, cy, cz)
            * Rot(SPLAY, 0, 0)
            * extrude(SlotOverall(SLOT_L, BOLT_D, rotation=90), amount=OVER, both=True)
        )

        # Nut pocket, coaxial with the slot so the nut seats square on the bolt
        # rather than cocked by the splay. Opens on the pad face and stops
        # NUT_DEEP in, leaving the pad bearing on birch all around it.
        y0 = cy + cz * TAN_SPLAY        # where the slot axis crosses the pad plane
        part -= (
            Pos(cx, y0 + OVER * sin(radians(SPLAY)), -OVER * cos(radians(SPLAY)))
            * Rot(SPLAY, 0, 0)
            * extrude(SlotOverall(POCKET_L, NUT_D, rotation=90), amount=OVER + NUT_DEEP)
        )

    # -- carcass-side blind taps -------------------------------------------
    # Driven from inside the bay, through the birch, into the delrin.
    for x in SCREW_XS:
        for y in SCREW_YS:
            part -= Cylinder(
                SCREW_PILOT_D / 2,
                TAP_DEPTH + OVER,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            ).moved(Location((x, y, -OVER)))

    return part


# ============================================================ placement


def placements(d=D) -> list[tuple[str, Plane]]:
    """The four ties in station coordinates, named by the corner they hold.

    Local +Z runs outboard on both sides, local +Y runs up on both sides, so one
    part serves all four positions: the block is symmetric about its own width
    centreline and the wedge always thickens upward.
    """
    x_l, x_r = CORNER_X
    y_f, y_r = CORNER_Y
    return [
        # left side: pad on x_l, thickness into -X, width running -Y
        ("left_front", Plane(origin=(x_l, y_f + W, Z0), x_dir=(0, -1, 0), z_dir=(-1, 0, 0))),
        ("left_rear", Plane(origin=(x_l, y_r, Z0), x_dir=(0, -1, 0), z_dir=(-1, 0, 0))),
        # right side: pad on x_r, thickness into +X, width running +Y
        ("right_front", Plane(origin=(x_r, y_f, Z0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))),
        ("right_rear", Plane(origin=(x_r, y_r - W, Z0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))),
    ]


def placed(part: Part | None = None) -> list[tuple[str, Part]]:
    """The same solid stood up at all four corners, for assembly checking."""
    p = part if part is not None else build()
    return [(name, plane * p) for name, plane in placements()]


# ============================================================ export layers


def dxf_layers(part: Part, tol: float = 1e-6) -> dict[str, list]:
    """Machining layout, in the spine's layer vocabulary.

    ``flat_pattern`` reads setup side and depth off faces parallel to Plane.XY,
    which is right for a sheet part and wrong for a wedge: the leg face is not
    parallel to anything, so an automatic read would call the tap floors the
    outline. This part names its own layers instead.

        CUT             the pad face: blank outline, tap holes, nut pockets
        POCKET_BACK_<d> the blind tap floors, cut <d> deep from the pad face
    """
    flat = part.faces().filter_by(Plane.XY)
    pad = [f for f in flat if abs(f.center().Z) < tol]
    taps = [f for f in flat if abs(f.center().Z - TAP_DEPTH) < tol]
    layers: dict[str, list] = {"CUT": pad}
    if taps:
        layers[f"POCKET_BACK_{TAP_DEPTH:g}"] = [
            f.moved(Location((0, 0, -TAP_DEPTH))) for f in taps
        ]
    return layers


# ============================================================ checks


def check_leg_tie(d=D) -> list[str]:
    """Constraints this part owns."""
    notes: list[str] = []
    s = d.s

    if SPLAY <= 0:
        notes.append(
            "leg_splay is zero, so there is no wedge and no gap between a "
            "vertical carcass wall and the leg. The tie becomes a flat spacer "
            "and its mounting height stops being derivable."
        )
        return notes

    if T_MIN < T_FLOOR - 1e-9:
        notes.append(
            f"tie is only {T_MIN:.1f}mm thick at its bottom edge against a "
            f"{T_FLOOR:.1f}mm floor ({TAP_DEPTH:.0f}mm of thread plus "
            f"{TAP_WALL:.0f}mm behind it). Z_CLEAR is holding the tie below the "
            "height where the splay has opened enough gap."
        )

    if Z0 + H > d.carcass_h:
        notes.append(
            f"tie runs to z={Z0 + H:.0f} against a {d.carcass_h:.0f}mm carcass. "
            "It would stand proud of the top cap."
        )

    if Z0 < d.deck_top:
        notes.append(
            f"tie starts at z={Z0:.0f}, below the deck top at {d.deck_top:.0f}. "
            "It has nothing to bolt to."
        )

    if LEG_SLOT_V <= s.table_h_with_feet - s.table_h_no_feet:
        notes.append(
            f"slot travel {LEG_SLOT_V:.0f}mm does not cover the "
            f"{s.table_h_with_feet - s.table_h_no_feet:.0f}mm levelling-feet swing"
        )

    if SLOT_L * COS_SPLAY + 2 * EDGE > H:
        notes.append(
            f"slot needs {SLOT_L * COS_SPLAY:.0f}mm of the tie's {H:.0f}mm "
            "height and there is no web left at the ends"
        )

    if s.leg_mount_pitch[1] < SLOT_L:
        notes.append(
            f"the leg's second hole axis is {s.leg_mount_pitch[1]:.0f}mm and a "
            f"slot is {SLOT_L:.0f}mm long, so two slots on that axis would meet. "
            "Each tie deliberately uses ONE hole pair; the four ties together "
            "fix the frame. Expected, and worth knowing before drilling."
        )

    for name, plane in placements(d):
        y0 = min(plane.origin.Y, plane.origin.Y + W * plane.x_dir.Y)
        y1 = y0 + W
        if y0 < CARCASS_FACE_Y[0] - 1e-6 or y1 > CARCASS_FACE_Y[1] + 1e-6:
            notes.append(
                f"the {name} tie needs a birch face at y {y0:.0f}..{y1:.0f} and "
                f"the carcass only presents one from {CARCASS_FACE_Y[0]:.0f} to "
                f"{CARCASS_FACE_Y[1]:.0f}: the bay walls are cut to front_bay_d, "
                "so the brain band's ends are open air. The tie goes where the "
                "leg is, so what is missing is a part, not a placement. Brain-"
                f"band end cheek, {d.t:.0f}mm birch, x at both end walls, y "
                f"{d.y_spine:.0f}..{d.y_rear:.0f}, z {d.deck_top:.0f}.."
                f"{d.top_z[0]:.0f}. It closes the electrical band as well, which "
                "the brief wants anyway, and it is the same later group as the "
                "louvred rear panel."
            )

    if s.leg_wall_t < BOLT_D / 2:
        notes.append(
            f"the leg wall is {s.leg_wall_t:.1f}mm under an M{BOLT_D - 1:.0f} "
            "bolt. The steel backing washer is not optional."
        )

    return notes


# ============================================================ main

if __name__ == "__main__":
    part = build()
    bb = part.bounding_box()

    print(f"{NAME} x{QTY}   {MATERIAL}")
    print(
        f"  splay {SPLAY:.1f} deg -> gap opens {TAN_SPLAY * 1000:.1f}mm per metre "
        f"of height"
    )
    print(
        f"  mounts at z {Z0:.0f}..{Z0 + H:.0f}, the lowest grid height where the "
        f"gap clears {T_FLOOR:.0f}mm of delrin"
    )
    print(f"  blank {W:.0f} x {H:.0f} x {T_MAX:.2f} (wedge {T_MIN:.2f} -> {T_MAX:.2f})")
    print(
        f"  leg side: 2 x M6 at {BOLT_PITCH:.0f} pitch, {SLOT_L:.1f}mm slot up the "
        f"face = {LEG_SLOT_V:.0f}mm of vertical travel"
    )
    print(
        f"  nut pocket {POCKET_L:.1f} x {NUT_D:.0f} x {NUT_DEEP:.0f} deep, on the "
        "pad face, coaxial with the slot"
    )
    print(
        f"  carcass side: {len(SCREW_XS)}x{len(SCREW_YS)} blind taps "
        f"{TAP_DEPTH:.0f} deep at x={[f'{v:.0f}' for v in SCREW_XS]} "
        f"y={[f'{v:.0f}' for v in SCREW_YS]}, screws >= {SCREW_LEN_MIN:.0f}mm"
    )
    print(
        f"  shim pack: {SHIM_SWING:.2f}mm of standoff over full travel, leg side, "
        "inside the bolted clamp"
    )
    print(f"  backing washer: steel, against the {S.leg_wall_t:.1f}mm leg wall")

    print(
        f"\n  bbox {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f}   "
        f"min ({bb.min.X:.2f}, {bb.min.Y:.2f}, {bb.min.Z:.2f})"
    )
    solid_v = W * H * (T_MIN + T_MAX) / 2
    print(
        f"  volume {part.volume / 1000:.1f} cm3 of a {solid_v / 1000:.1f} cm3 "
        f"wedge ({100 * part.volume / solid_v:.1f}% left after features)"
    )

    print(
        f"\n  placed (carcass presents birch on its end faces from y "
        f"{CARCASS_FACE_Y[0]:.0f} to {CARCASS_FACE_Y[1]:.0f}):"
    )
    for name, solid in placed(part):
        b = solid.bounding_box()
        on_birch = (
            b.min.Y >= CARCASS_FACE_Y[0] - 1e-6 and b.max.Y <= CARCASS_FACE_Y[1] + 1e-6
        )
        print(
            f"    {name:<12} x {b.min.X:8.2f}..{b.max.X:8.2f}   "
            f"y {b.min.Y:7.1f}..{b.max.Y:7.1f}   z {b.min.Z:6.1f}..{b.max.Z:6.1f}   "
            f"{'on the end wall' if on_birch else 'NO BIRCH BEHIND IT'}"
        )

    found = check_leg_tie()
    if found:
        print(f"\n  {len(found)} note(s):")
        for n in found:
            print(f"    - {n}")
    else:
        print("\n  no constraint violations")

    written = export_part(part, NAME, layers=dxf_layers(part), out_dir=EXPORT_DIR)
    print()
    for p in written:
        print(f"  wrote {p}  ({p.stat().st_size} bytes)")
