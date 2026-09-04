"""Lungs door: the front of the extractor bay, hung on the left end wall's front edge.

WHAT THIS PART IS
=================

One 18mm Baltic birch door filling the lungs bay's front opening -- between
the FRONT-LEFT STILE's inner edge and the lungs/stock divider's left face,
deck top to cap underside -- on a continuous (piano) hinge along its LEFT
edge, so it swings OUTBOARD, to the operator's left, and the CT 15 on its
carriage (C06) is pulled forward through the opening it leaves. RULED
2026-09-03 (faces): lungs is the leftmost FRONT bay and this door closes its
front, not the left end wall. RULED 2026-09-04 (Kerf): the flange band at
the corner is a fixed stile (``parts/stiles.py``), the door is INSET between
that stile and the divider, and the hinge's fixed leaf lands on the stile's
inner edge, its 18mm of end grain at the carcass's front plane.

Closed, the door is INSET. Its outer face is flush with the carcass's front
plane at ``y_front``, the plane the end wall's and both dividers' front edges
stop on. Its inside face carries the bay's acoustic lay-up
(``Station.lungs_lining_t`` of MLV plus foam) as a reference slab,
``lungs_door_lining``, so the closed carriage is measured against the lining
and not against the door alone. A magnetic catch on the divider's lungs face
holds it shut against a strike plate on the door; a capsule finger pull near
the free edge opens it; there is no handle. The EXTRACTION callout is
V-carved on the outer face (C17) at ``callout_centre_local``, through the
paint to raw birch, on the DXF's ``VCARVE`` layer; the painted door goes
back on the machine on the pull's two end arcs, its ``REGISTER`` layer,
because the door has no screw hole on that face and the hinge's screws are
driven on the fit, not modelled.

    lungs_door            the birch, one capsule pull, one blind pilot, the
                          callout
    lungs_door_lining     the lay-up on the inside face, a reference slab,
                          relieved around the pull; its DXF is the knife
                          template for the MLV and the foam
    lungs_catch_env       the magnetic catch's body on the divider, reference
    lungs_catch_strike    the strike plate on the door's inside face, steel
    lungs_door_hinge      the knuckle, built for this module's own checks and
                          NOT placed in the assembly: it stands proud of the
                          carcass front by design (see THE HINGE), and the
                          assembly's envelope check would read that as the
                          carcass not fitting the leg opening. The rear door's
                          knuckle at the rear is treated the same way.


WHAT THE DOOR COST THE CARRIAGE
===============================

An inset door ``t`` thick with ``lungs_lining_t`` on its inside face occupies
the bay's first ``t + lungs_lining_t`` of depth, 30mm, and the lungs
carriage used to close at ``bay_walls.SLIDE_FRONT_INSET`` = 20, the drawers'
inset, leaving 2mm for a 12mm lay-up. C06 tagged its ``LUNGS_DOOR_LANDING``
as "assumption until C09 lands a door"; this is C09, and the landing is
``t + lining``. ``bay_walls.LUNGS_SLIDE_INSET`` (snap_up of that, 40) is
where the lungs bay's slide row now starts and where the tray's closed
front sits; what the snap added is the running gap between the lining and
the tray. The drawers' row did not move. The bay is 821 deep and the tray
500, so the 20mm came from behind the tray, where nothing stood.


THE HINGE, THE PROUD KNUCKLE, AND WHAT IT COSTS THE BLANK
==========================================================

Same class and the SAME BOM LINE as the rear door (C07): "Piano hinge, rear
door and lungs door, Amazon, 2". This is the second of the two, and it is
NOT the rear door's flat surface-mount construction. The leaves go into the
GAP: one on the stile's inner edge face, one on the door's hinge edge face,
and the knuckle stands in front of the carcass plane on a pin
``AXIS_OFF`` ahead of it -- a PROUD knuckle. RULED 2026-09-04: the door
"must open to 180 to lie against the leg face so the tray path is clear; if
180 needs a proud knuckle, model it." It does: the leg's flange stands
``leg_wall_t`` (3.52) in front of the carcass plane at the corner, a door
folded 180 on a flat hinge lies 1mm off the plane and lands on the steel
2.5mm short of flat. On a pin ``(leg_wall_t + lungs_door_lay_gap) / 2``
ahead of the plane the folded door's outer face lies ``lungs_door_lay_gap``
in front of the flange's face: against the leg, clear of it. The gap
between stile and door is the knuckle's diameter (``HINGE_GAP``); the free
edge gets ``SIDE_REVEAL`` to the divider, which the swing arc needs; the top
and bottom edges get ``REVEAL`` each. The knuckle is a reference solid; the
hinge's other numbers are the rear door's, so one representative hinge is
measured once when the pair arrives, and the proud barrel is what to buy
(an offset or raised-barrel continuous hinge; MEASURE THIS).

What the knuckle costs: it stands in the tray's path unless the tray's left
cheek passes outboard of it, which is what the left slide's spacer block
(``Station.lungs_spacer``, RULED the same day) is for. ``lungs_carriage``
sweeps the tray against it.


THE SWING, AND THE TRAY
=======================

The tray is pulled through the opening the open door leaves, so the open
door has to be out of the tray's way and not merely out of the bay. At 90
the door stands straight out the front, hinge side, its thickness and
lining reaching into the opening past the knuckle. ``carriage_clear_angle``
scans the swing and reports the first opening at which every solid of the
extended carriage clears the open door, lining and strike; the operator
opens the door past it before pulling. At 180 the door lies against the
leg, outboard of the stile's edge, entirely clear of the opening. Both
acceptance angles are reported by ``swing_report`` as gaps and shared
volumes against the front-left leg's envelope (``machine.
front_left_leg_envelope``, the X flange and the Y flange band), the two
front stiles and the extended carriage.


PANEL CONVENTION
================

Drawn flat like a drawer front: local origin at the door's lower-left
corner AS SEEN FROM THE FRONT (the hinge corner), local +X to station +X,
local +Y up, local +Z through the thickness from the INSIDE face at Z = 0
to the OUTSIDE (reading) face at Z = t, so the DXF's CUT layer is the face
the operator reads and the face the callout lands on. Placed with
``plane``, origin (lungs_opening_x[0] + HINGE_GAP, y_front + t, deck_top +
REVEAL), z_dir station -Y. The lining is drawn flat the same way and placed by
``lining_plane`` one lay-up thickness behind the door's inside face.

The pull is an APERTURE and is capsule-ended, per ``through_slot``; the
lining's relief around it is the same shape a half-grid larger. Nothing in
this door is joinery, so nothing in it is square.
"""

from __future__ import annotations

from math import hypot

from build123d import Align, Axis, Box, Cylinder, Location, Part, Plane, Unit, export_step

from lib.house import FULL, GRID, SHEET_5X5_BALTIC, fits
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    ROUTER_R,
    SCREW_PILOT_D,
    T,
    Datums,
    bore,
    export_part,
    flat_pattern,
    panel,
    through_slot,
)
from stations.cnc_shapeoko.parts import callouts, lungs_carriage
from stations.cnc_shapeoko.parts.bay_walls import LUNGS_SLIDE_INSET, WALLS
from stations.cnc_shapeoko.parts.bay_walls import placed_all as walls_placed
from stations.cnc_shapeoko.parts.drawers import PULL_DROP, PULL_H, PULL_L
from stations.cnc_shapeoko.parts.rear_door import (
    HINGE,
    HINGE_KNUCKLE_D,
    HINGE_LEAF_T,
    HINGE_LEAF_W,
    HINGE_LEN,
    TOP_REVEAL,
)

__all__ = [
    "PART_NAME",
    "AXIS_OFF",
    "STOP_FAMILIES",
    "LINING_NAME",
    "CATCH_NAME",
    "STRIKE_NAME",
    "HINGE_NAME",
    "CALLOUT",
    "door_size",
    "plane",
    "hinge_axis",
    "pull_local",
    "callout_centre_local",
    "callouts_local",
    "register",
    "build",
    "build_lining",
    "build_strike",
    "build_catch",
    "build_hinge",
    "place",
    "place_lining",
    "placed_all",
    "moving",
    "swung",
    "door_open",
    "swing_report",
    "carriage_clear_angle",
    "leg_stop_angle",
    "joint_table",
    "check_lungs_door",
    "export",
]

D: Datums = DATUMS

PART_NAME = "lungs_door"
LINING_NAME = "lungs_door_lining"
CATCH_NAME = "lungs_catch_env"
STRIKE_NAME = "lungs_catch_strike"
HINGE_NAME = "lungs_door_hinge"

CALLOUT = "EXTRACTION"
"""The door's callout, V-carved on the outer face (C17) at callouts.CALLOUT_H.
SOURCE: brief v8, "EXTRACTION on the lungs door". CONFIDENCE: spec."""


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# Boundaries come from Datums, joinery from carcass.py, the hinge from
# rear_door (one hinge, one BOM line, measured once), the pull from drawers
# (one pull family), the lay-up thickness from params. Every value carries
# its SOURCE and CONFIDENCE.
# ====================================================================

# ---- the hinge --------------------------------------------------------------
HINGE_GAP = HINGE_KNUCKLE_D
"""Gap between the front-left stile's inner edge and the door's hinge edge:
the knuckle lies in it, its leaves down the two edge faces. SOURCE: derived,
the rear door's knuckle. CONFIDENCE: derived from a representative hinge;
MEASURE THIS with the hinge (the note is the rear door's, shared)."""

AXIS_OFF = (D.s.leg_wall_t + D.s.lungs_door_lay_gap) / 2
"""The pin's stand-off in front of the carcass plane: the PROUD knuckle.
Half the leg's wall plus half the lay gap, so the door folded to 180 lies
``lungs_door_lay_gap`` clear of the flange's front face. SOURCE: derived
from params (leg_wall_t MEASURED, lungs_door_lay_gap choice) under the
2026-09-04 ruling. CONFIDENCE: derived. Replaces the rear door's flat
HINGE_AXIS_OFF (0.5) for this door only."""

STOP_FAMILIES = ("measured", "inboard", "stile")
"""What the swing is stopped by: the front-left leg's bolted X flange, its
Y flange band across the bay's front, and the two front stiles."""

SIDE_REVEAL = TOP_REVEAL
"""Gap between the door's free edge and the divider's face. SOURCE: the rear
door's TOP_REVEAL, the same figure for the same reason: the free edge's
inside corner rises ``hypot(L, t + off) - L`` as the door starts to turn,
under a millimetre here, and the rest is a finish reveal. CONFIDENCE:
design, checked against the arc (door and strike plate both)."""

REVEAL = TOP_REVEAL
"""Gap above and below the door. A side-hung door has no knuckle at its top
or bottom edge, so both are finish reveals. SOURCE: the rear door's figure.
CONFIDENCE: design."""

OPEN_SIGN = -1.0
"""Sign of the rotation about +Z that swings the free edge OUTBOARD (toward
the operator, -Y on this datum, then round to the left). SOURCE: task C09
("swings outboard"). CONFIDENCE: spec; the check confirms the sign by
reading the open door's position."""

SWING_ANGLES = (90.0, 180.0)
"""The two openings the acceptance asks to be reported. SOURCE: task C09.
CONFIDENCE: spec."""

SWING_STEP = 5.0
"""Degrees between samples when the swing is scanned for the first clear
angle and the last free one. SOURCE: chosen; the scan is a report, not a
cut. CONFIDENCE: chosen."""

# ---- the lay-up -------------------------------------------------------------
LINING_INSET = GRID
"""Solid door left bare around the lay-up, all four edges: keeps the MLV off
the hinge leaf's line, off the strike plate and off the free edge's swing
corner, and gives the fingers through the pull a bare strip of door above it
to curl behind. SOURCE: design, one grid module. CONFIDENCE: design."""

HAND_RELIEF = GRID / 2
"""How far past the pull's ends and below its bottom edge the lay-up's notch
runs, and the notch's corner radius, so the slot's edges are clean birch and
not foam. Above the pull the notch runs out through the lay-up's top edge:
the fingers through the slot curl up behind bare door. SOURCE: design.
CONFIDENCE: design."""

# ---- the pull ---------------------------------------------------------------
PULL_EDGE = GRID * 2
"""Free edge to the near end of the pull. The pull sits by the free edge on
a hinged door, where the hand has leverage, at the drawers' drop below the
top edge so the family reads as one. PULL_H, PULL_L and PULL_DROP are the
drawers' own. SOURCE: design. CONFIDENCE: design."""

# ---- the catch --------------------------------------------------------------
CATCH = "surface-mount magnetic catch, adjustable, with strike plate"
CATCH_BODY = (46.0, 16.0, 16.0)
"""Body L (along Z, the long way) x W (magnet face to back, along Y) x D
(proud of the divider's face, along X). SOURCE: representative 46mm
adjustable magnetic catch, the class every listing sells; the BOM line
"Magnetic catches, adjustable feet, levelers, Amazon, set" carries no SKU.
CONFIDENCE: representative. MEASURE THIS when it arrives."""

STRIKE = (45.0, 14.0, 1.5)
"""Strike plate L (along Z) x W (along X) x T, one countersunk screw.
SOURCE: same representative listing. CONFIDENCE: representative."""

STRIKE_EDGE = SIDE_REVEAL
"""Strike plate's outer edge in from the door's free edge. SOURCE: design.
CONFIDENCE: design; the body has to overlap it, which the check measures."""

STRIKE_PILOT_DEPTH = T / 2
"""Blind pilot in the door for the strike's screw, from the inside face.
SOURCE: the rear door's pilots. CONFIDENCE: chosen."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the block
# above and on Datums.
# ====================================================================


def door_size(d: Datums = D) -> tuple[float, float]:
    """(width, height) of the cut blank: the lungs OPENING (stile's inner
    edge to the divider) less the knuckle gap and the side reveal, the bay
    height less two reveals."""
    x0, x1 = d.lungs_opening_x
    return (x1 - x0 - HINGE_GAP - SIDE_REVEAL, d.bay_h - 2 * REVEAL)


def x_hinge_edge(d: Datums = D) -> float:
    """Station X of the door's hinge edge: the stile's edge plus the gap."""
    return d.lungs_opening_x[0] + HINGE_GAP


def z_bottom(d: Datums = D) -> float:
    """Station Z of the door's bottom edge."""
    return d.deck_top + REVEAL


def plane(d: Datums = D) -> Plane:
    """Door frame: local +X to station +X, local +Y up, thickness into -Y
    from the inside face at y_front + t, so local Z = t is the outer face."""
    return Plane(
        origin=(x_hinge_edge(d), d.y_front + d.t, z_bottom(d)),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def hinge_axis(d: Datums = D) -> Axis:
    """The pin: vertical, in the middle of the knuckle gap, AXIS_OFF in
    front of the carcass's front plane (the proud knuckle)."""
    return Axis(
        (d.lungs_opening_x[0] + HINGE_GAP / 2, d.y_front - AXIS_OFF, 0.0),
        (0, 0, 1),
    )


def pull_local(d: Datums = D) -> tuple[float, float]:
    """Door-local centre of the pull: PULL_EDGE in from the free edge,
    PULL_DROP below the top."""
    w, h = door_size(d)
    return (w - PULL_EDGE - PULL_L / 2, h - PULL_DROP)


def callout_centre_local(d: Datums = D) -> tuple[float, float]:
    """Door-local centre of the EXTRACTION callout, for C17: centred on the
    door in the band below the pull, where the drawers put theirs."""
    w, h = door_size(d)
    return (w / 2, (h - PULL_DROP - PULL_H / 2) / 2)


def callouts_local(d: Datums = D) -> list[callouts.Callout]:
    """The door's one word, on the Z = t face the operator reads."""
    return [callouts.Callout(CALLOUT, callout_centre_local(d))]


def register(d: Datums = D) -> callouts.Register:
    """The second fixture's datums: the pull's two end arcs, which a PULL_H
    pin seats in. The same pins the drawer fronts use."""
    cx, cy = pull_local(d)
    dx = (PULL_L - PULL_H) / 2
    return callouts.Register(
        (cx - dx, cy, PULL_H), (cx + dx, cy, PULL_H), "the pull's two end arcs"
    )


def lining_size(d: Datums = D) -> tuple[float, float]:
    w, h = door_size(d)
    return (w - 2 * LINING_INSET, h - 2 * LINING_INSET)


def lining_t(d: Datums = D) -> float:
    return d.s.lungs_lining_t


def lining_plane(d: Datums = D) -> Plane:
    """The lay-up's frame: the door's, shifted in by the inset and back by
    one lay-up thickness, so its local Z = 0 face lands on the door's inside
    face."""
    return Plane(
        origin=(
            x_hinge_edge(d) + LINING_INSET,
            d.y_front + d.t + lining_t(d),
            z_bottom(d) + LINING_INSET,
        ),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def relief_local(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """(centre, (width, height)) of the lay-up's notch over the pull,
    lining-local: HAND_RELIEF past the pull's ends and below its bottom edge,
    open at the top. Its upper end lies a full width outside the lay-up so
    the notch leaves the top edge at full width; only its two bottom corners
    are rounded."""
    cx, cy = pull_local(d)
    _lw, lh = lining_size(d)
    width = PULL_L + 2 * HAND_RELIEF
    y0 = cy - LINING_INSET - PULL_H / 2 - HAND_RELIEF
    y1 = lh + width
    return ((cx - LINING_INSET, (y0 + y1) / 2), (width, y1 - y0))


def strike_local(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """((x0, x1), (y0, y1)) of the strike plate on the door's inside face,
    door-local: against the free edge, centred on the pull's height."""
    w, _h = door_size(d)
    _cx, cy = pull_local(d)
    sl, sw, _st = STRIKE
    x1 = w - STRIKE_EDGE
    return ((x1 - sw, x1), (cy - sl / 2, cy + sl / 2))


def strike_pilot_local(d: Datums = D) -> tuple[float, float]:
    (x0, x1), (y0, y1) = strike_local(d)
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def catch_station(
    d: Datums = D,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The catch body on the divider's lungs face: proud of it toward the
    door, its magnet face on the strike, its length vertical and centred on
    the strike."""
    cl, cw, cd = CATCH_BODY
    _sl, _sw, st = STRIKE
    x1 = d.lungs_x[1]
    y0 = d.y_front + d.t + st
    _xs, (ly0, ly1) = strike_local(d)
    zc = z_bottom(d) + (ly0 + ly1) / 2
    return ((x1 - cd, x1), (y0, y0 + cw), (zc - cl / 2, zc + cl / 2))


def swing_rise(d: Datums = D) -> float:
    """How far the free edge's inside corner reaches past its closed X as the
    door starts to turn: the arc's radius less the corner's closed distance
    from the pin, in X. The strike plate's outer corner is further out in Y
    and is the one the check uses."""
    w, _h = door_size(d)
    L = HINGE_GAP / 2 + w
    _st = STRIKE[2]
    return hypot(L, d.t + _st + AXIS_OFF) - L


# ---------------------------------------------------------------- solids


def build(d: Datums = D, *, carve: bool = True) -> Part:
    """The door, flat: the blank, the capsule pull, the strike's pilot, and
    the callout carved into the outer face unless ``carve`` is off (the DXF's
    CUT layers are read off the un-carved blank)."""
    w, h = door_size(d)
    part = panel(w, h, d.t)
    part -= through_slot(pull_local(d), PULL_L, PULL_H, corner_r=PULL_H / 2)
    px, py = strike_pilot_local(d)
    part -= bore(px, py, SCREW_PILOT_D, depth=STRIKE_PILOT_DEPTH, side="back")
    if carve:
        part = callouts.carve(part, callouts_local(d), thickness=d.t)
    return part


def build_lining(d: Datums = D) -> Part:
    """The lay-up, flat, one lay-up thick, relieved around the pull."""
    lw, lh = lining_size(d)
    lt = lining_t(d)
    part = panel(lw, lh, lt)
    centre, (rl, rw) = relief_local(d)
    part -= through_slot(centre, rl, rw, thickness=lt, corner_r=HAND_RELIEF)
    return part


def build_strike(d: Datums = D) -> Part:
    """The strike plate, station coordinates, flat on the door's inside
    face."""
    (x0, x1), (y0, y1) = strike_local(d)
    _sl, _sw, st = STRIKE
    return Box(x1 - x0, st, y1 - y0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x_hinge_edge(d) + x0, d.y_front + d.t, z_bottom(d) + y0))
    )


def build_catch(d: Datums = D) -> Part:
    """The catch body, station coordinates."""
    (x0, x1), (y0, y1), (z0, z1) = catch_station(d)
    return Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x0, y0, z0))
    )


def build_hinge(d: Datums = D) -> Part:
    """The knuckle, station coordinates: a barrel on the pin the door's
    height. For this module's checks only; see the docstring."""
    _w, h = door_size(d)
    ax = hinge_axis(d)
    return Cylinder(
        HINGE_KNUCKLE_D / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((ax.position.X, ax.position.Y, z_bottom(d))))


def place(part: Part | None = None, d: Datums = D) -> Part:
    part = build(d) if part is None else part
    return plane(d) * part


def place_lining(part: Part | None = None, d: Datums = D) -> Part:
    part = build_lining(d) if part is None else part
    return lining_plane(d) * part


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, placed solid) for everything this module puts in the
    assembly, CLOSED: the door, its lay-up, the strike, the catch body."""
    return [
        (PART_NAME, "carcass", place(d=d)),
        (LINING_NAME, "reference", place_lining(d=d)),
        (STRIKE_NAME, "steel", build_strike(d)),
        (CATCH_NAME, "reference", build_catch(d)),
    ]


def moving(d: Datums = D) -> list[tuple[str, Part]]:
    """What swings with the door: the door, its lay-up, the strike."""
    return [(label, part) for label, _group, part in placed_all(d) if label != CATCH_NAME]


def swung(part: Part, angle: float, d: Datums = D) -> Part:
    """A placed solid rotated ``angle`` degrees open about the pin."""
    return part.rotate(hinge_axis(d), OPEN_SIGN * angle)


def door_open(angle: float = SWING_ANGLES[0], d: Datums = D) -> Part:
    """The placed door alone, ``angle`` degrees open."""
    return swung(place(d=d), angle, d)


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints for ``assembly.joints``. Everything meets on a face;
    the door's edges meet nothing (the knuckle gap and the reveals)."""
    return [
        (PART_NAME, LINING_NAME, "bearing", None, 0.0, 0.0,
         "lay-up bonded flat on the door's inside face"),
        (PART_NAME, STRIKE_NAME, "bearing", None, 0.0, 0.0,
         "strike plate flat on the door's inside face, one screw"),
        (WALLS[1].name, CATCH_NAME, "bearing", None, 0.0, 0.0,
         "catch body on the divider's lungs face, two screws"),
        (CATCH_NAME, STRIKE_NAME, "bearing", None, 0.0, 0.0,
         "the magnet face on the strike plate, door closed"),
    ]


# ====================================================================
# OPEN-DOOR QUESTIONS
# ====================================================================


def _obstacles(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, family, solid): the front-left leg's envelope pieces (family
    is their case, "measured" / "inboard" / "outboard"), the two front
    stiles (family "stile", 2026-09-04) and every solid of the carriage at
    full extension (family "carriage").

    ``machine`` and ``stiles`` are imported here rather than at the top
    because the machine imports the assembly that imports this part; the
    same deferral the carriage makes."""
    from stations.cnc_shapeoko.machine import front_left_leg_envelope
    from stations.cnc_shapeoko.parts import stiles

    out: list[tuple[str, str, Part]] = [
        (label, case, solid) for label, case, solid in front_left_leg_envelope(d)
    ]
    for label, _group, part in stiles.placed_all(d):
        if "_front_" in label:
            out.append((label, "stile", part))
    for label, _group, part in lungs_carriage.placed_all(d):
        out.append((label, "carriage", lungs_carriage.extended(part)))
    return out


def _bb_touch(a, b) -> bool:
    return not (
        a.max.X < b.min.X or b.max.X < a.min.X
        or a.max.Y < b.min.Y or b.max.Y < a.min.Y
        or a.max.Z < b.min.Z or b.max.Z < a.min.Z
    )


def _shared(a: Part, b: Part) -> float:
    if not _bb_touch(a.bounding_box(), b.bounding_box()):
        return 0.0
    try:
        s = a & b
    except Exception:
        return 0.0
    return 0.0 if s is None else s.volume


def swing_report(
    angle: float, d: Datums = D, obstacles: list[tuple[str, str, Part]] | None = None
) -> list[tuple[str, str, str, float, float]]:
    """(moving part, obstacle, family, gap mm, shared mm3) for every moving
    solid at ``angle`` open against every obstacle. Gap is the closest
    approach, 0 when they touch or share volume."""
    obstacles = _obstacles(d) if obstacles is None else obstacles
    out: list[tuple[str, str, str, float, float]] = []
    for mlabel, part in moving(d):
        m = swung(part, angle, d)
        for olabel, family, solid in obstacles:
            gap = m.distance_to(solid)
            out.append((mlabel, olabel, family, gap, _shared(m, solid) if gap <= 1e-6 else 0.0))
    return out


def _clear_of(angle: float, family_ok, d: Datums, obstacles) -> bool:
    """True when nothing that swings shares volume with any obstacle whose
    family ``family_ok`` accepts, at ``angle`` open."""
    for mlabel, part in moving(d):
        m = swung(part, angle, d)
        mb = m.bounding_box()
        for _olabel, family, solid in obstacles:
            if not family_ok(family):
                continue
            if not _bb_touch(mb, solid.bounding_box()):
                continue
            if _shared(m, solid) > 1.0:
                return False
    return True


def carriage_clear_angle(
    d: Datums = D, obstacles: list[tuple[str, str, Part]] | None = None
) -> float | None:
    """The first opening angle, in SWING_STEP steps, at which the extended
    carriage clears the open door, lay-up and strike. None if none does."""
    obstacles = _obstacles(d) if obstacles is None else obstacles
    a = SWING_STEP
    while a <= 180.0 + 1e-9:
        if _clear_of(a, lambda f: f == "carriage", d, obstacles):
            return a
        a += SWING_STEP
    return None


def leg_stop_angle(
    case: str, d: Datums = D, obstacles: list[tuple[str, str, Part]] | None = None
) -> float:
    """The largest opening angle, in SWING_STEP steps from closed, before the
    door, lay-up or strike first touches the front-left leg in the given
    flange ``case`` ("inboard" / "outboard") or a front stile; the leg's
    measured X flange counts in both. 0 when the closed door's first step
    already does."""
    obstacles = _obstacles(d) if obstacles is None else obstacles
    ok = lambda f: f in ("measured", "stile", case)  # noqa: E731
    last = 0.0
    a = SWING_STEP
    while a <= 180.0 + 1e-9:
        if not _clear_of(a, ok, d, obstacles):
            return last
        last = a
        a += SWING_STEP
    return last


# ====================================================================
# CHECKS
# ====================================================================


def _probe_fraction(solid: Part, probe: Part) -> float:
    try:
        return (solid & probe).volume / probe.volume
    except Exception:
        return 0.0


def check_lungs_door(d: Datums = D) -> list[str]:
    """What this part has to be true for. The assembly's interference check
    owns whether it meets its neighbours closed; these are the things that
    are wrong before the solids are compared, plus the open-door questions
    only this module can ask."""
    notes: list[str] = []
    s = d.s
    w, h = door_size(d)
    lt = lining_t(d)
    walls = walls_placed(d)

    # -- the blank -----------------------------------------------------------
    if abs(w - (d.lungs_opening_x[1] - d.lungs_opening_x[0] - HINGE_GAP - SIDE_REVEAL)) > 1e-6:
        notes.append(f"the door is {w:.2f} wide, not the opening less HINGE_GAP and SIDE_REVEAL")
    if abs(h - (d.bay_h - 2 * REVEAL)) > 1e-6:
        notes.append(f"the door is {h:.2f} tall, not bay_h less two reveals")
    travel = min(s.travel_x, s.travel_y)
    if max(w, h) > travel:
        notes.append(
            f"door blank {w:.0f} x {h:.0f} exceeds the machine's own {travel:.0f}mm "
            "travel: cut on the track saw or Shaper Origin, by ruling, 2026-09-02. "
            "Expected, and worth knowing before it goes to either tool."
        )
    if not fits((w, h), SHEET_5X5_BALTIC):
        notes.append(f"door blank {w:.0f} x {h:.0f} does not come out of a 5x5 Baltic sheet")
    if not fits((w, h), FULL):
        notes.append(f"door blank {w:.0f} x {h:.0f} does not come out of a FULL 600 x 1200 blank")

    # -- closed: flush, inside the opening, the lay-up behind it ------------
    door = place(d=d)
    db = door.bounding_box()
    divider_front = walls[1].bounding_box().min.Y
    if abs(db.min.Y - divider_front) > 0.5:
        notes.append(
            f"the door's outer face is at y {db.min.Y:.2f} and the divider's front "
            f"edge at {divider_front:.2f}: not flush"
        )
    ox0, ox1 = d.lungs_opening_x
    if db.min.X < ox0 + HINGE_GAP - 1e-6 or db.max.X > ox1 - SIDE_REVEAL + 1e-6:
        notes.append(
            f"the door spans x {db.min.X:.1f}..{db.max.X:.1f} against an opening "
            f"{ox0:.1f}..{ox1:.1f}: the gap or the reveal is wrong"
        )
    if db.min.Z < d.deck_top + REVEAL - 1e-6 or db.max.Z > d.top_z[0] - REVEAL + 1e-6:
        notes.append(f"the door spans z {db.min.Z:.1f}..{db.max.Z:.1f} and is not inside the bay's reveals")
    lb = place_lining(d=d).bounding_box()
    if abs(lb.size.Y - lt) > 1e-6 or abs(lb.min.Y - (d.y_front + d.t)) > 1e-6:
        notes.append(
            f"the lay-up slab is {lb.size.Y:.1f} thick at y {lb.min.Y:.1f}: not "
            f"lungs_lining_t {lt:.1f} on the door's inside face"
        )
    tray_front = lungs_carriage.carriage_origin(d)[1]
    room = tray_front - lb.max.Y
    if room < 0:
        notes.append(
            f"the closed tray's front at y {tray_front:.1f} sits {-room:.1f}mm inside "
            f"the door's lay-up, which reaches y {lb.max.Y:.1f}"
        )
    if abs(LUNGS_SLIDE_INSET - lungs_carriage.carriage_origin(d)[1]) > 1e-6:
        notes.append("the carriage does not close at bay_walls.LUNGS_SLIDE_INSET")

    # -- the swing arc against the divider ----------------------------------
    rise = swing_rise(d)
    if rise >= SIDE_REVEAL:
        notes.append(
            f"the free edge's strike corner rises {rise:.2f}mm on the swing and the "
            f"side reveal is {SIDE_REVEAL:.1f}: the door hits the divider before it opens"
        )

    # -- the pull, the lay-up's relief, the strike --------------------------
    (cx, cy) = pull_local(d)
    if not (PULL_L / 2 < cx < w - PULL_L / 2 and PULL_H / 2 < cy < h - PULL_H / 2):
        notes.append("the pull runs off the door")
    if PULL_H / 2 < ROUTER_R:
        notes.append("the pull's end radius is under the cutter's")
    (rcx, rcy), (rl, rw) = relief_local(d)
    lw, lh = lining_size(d)
    if not (rl / 2 < rcx < lw - rl / 2 and rcy - rw / 2 > 0):
        notes.append("the lay-up's notch over the pull runs off the lay-up's side or bottom")
    if rcy + rw / 2 < lh + rl / 2:
        notes.append("the lay-up's notch does not leave the top edge at full width")
    (sx0, sx1), (sy0, sy1) = strike_local(d)
    if sx0 < lw + LINING_INSET:
        notes.append(f"the strike plate at door x {sx0:.1f} lies on the lay-up, which reaches {lw + LINING_INSET:.1f}")
    if sx1 > w or sy1 > h or sy0 < 0:
        notes.append("the strike plate runs off the door")

    # -- the catch: on birch, clear of the slide, over the strike -----------
    (kx0, kx1), (ky0, ky1), (kz0, kz1) = catch_station(d)
    probe = Box(1.0, ky1 - ky0, kz1 - kz0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((kx1, ky0, kz0))
    )
    on_birch = _probe_fraction(walls[1], probe)
    if on_birch < 0.99:
        notes.append(
            f"the catch body lands on {on_birch:.0%} birch on the divider's lungs face "
            f"at y {ky0:.0f}..{ky1:.0f} z {kz0:.0f}..{kz1:.0f}"
        )
    if ky1 > LUNGS_SLIDE_INSET + 1e-6:
        notes.append(
            f"the catch body reaches y {ky1:.1f} and the slide's cabinet member "
            f"starts at {LUNGS_SLIDE_INSET:.0f}: the catch is under the slide"
        )
    strike = build_strike(d).bounding_box()
    ox = min(kx1, strike.max.X) - max(kx0, strike.min.X)
    oz = min(kz1, strike.max.Z) - max(kz0, strike.min.Z)
    if ox < STRIKE[1] / 2 or oz < STRIKE[0] / 2:
        notes.append(
            f"the magnet face overlaps the strike plate by {ox:.1f} x {oz:.1f}: less "
            "than half the plate"
        )
    if kz1 > d.top_z[0] - 1e-6:
        notes.append("the catch body runs into the cap")

    # -- the hinge: its fixed leaf on the stile's inner edge face, in the gap
    from stations.cnc_shapeoko.parts import stiles as _stiles

    stile = _stiles.place("stile_front_left", d=d)
    if HINGE_LEAF_W > d.t:
        notes.append(
            f"the hinge leaf is {HINGE_LEAF_W:.1f} wide and the stile's inner edge is "
            f"{d.t:.0f} deep: the stile-side leaf hangs off the edge"
        )
    leaf = Box(1.0, HINGE_LEAF_W, h, align=(Align.MAX, Align.MIN, Align.MIN)).moved(
        Location((ox0, d.y_front, z_bottom(d)))
    )
    leaf_frac = _probe_fraction(stile, leaf)
    line = Box(1.0, SCREW_PILOT_D, h, align=(Align.MAX, Align.CENTER, Align.MIN)).moved(
        Location((ox0, d.y_front + HINGE_LEAF_W / 2, z_bottom(d)))
    )
    line_frac = _probe_fraction(stile, line)
    if line_frac < 1.0 - 1e-3 or leaf_frac < 1.0 - 1e-3:
        notes.append(
            f"the hinge leaf on the stile's inner edge (x {ox0:.1f}, y {d.y_front:.0f}.."
            f"{d.y_front + HINGE_LEAF_W:.1f}) lands on {leaf_frac:.0%} birch and its screw "
            f"line on {line_frac:.0%}"
        )
    notes.append(
        f"the hinge is the rear door's representative {HINGE}: leaf {HINGE_LEAF_T:.1f}, "
        f"knuckle o{HINGE_KNUCKLE_D:.1f} (which is HINGE_GAP), leaf {HINGE_LEAF_W:.1f} wide, "
        f"{HINGE_LEN:.1f} long against a {h:.1f} door, so the second of the BOM's two "
        "is cut to length. MEASURE THIS when it arrives; the gap and the axis follow "
        "the knuckle."
    )
    notes.append(
        f"the catch is a representative {CATCH}, body {CATCH_BODY[0]:.0f} x {CATCH_BODY[1]:.0f} "
        f"x {CATCH_BODY[2]:.0f} proud of the divider, strike {STRIKE[0]:.0f} x {STRIKE[1]:.0f} x "
        f"{STRIKE[2]:.1f}; the BOM's set carries no SKU. MEASURE THIS when it arrives; "
        "only the pilot and the body's reach move."
    )

    # -- the open door -------------------------------------------------------
    ob = door_open(SWING_ANGLES[0], d).bounding_box()
    if ob.max.Y > d.t or ob.min.Y > -w / 2:
        notes.append("the open door did not swing outboard: OPEN_SIGN is wrong")
    if ob.size.X > d.t + STRIKE[2] + 2 * HINGE_KNUCKLE_D:
        notes.append("the door at 90 is not edge-on to the front: the pin is not vertical")

    obstacles = _obstacles(d)
    hh = s.leg_holes
    reports = {a: swing_report(a, d, obstacles) for a in SWING_ANGLES}

    def worst(rows, family):
        hits = [r for r in rows if r[2] == family and r[4] > 1.0]
        gap = min((r[3] for r in rows if r[2] == family), default=None)
        return hits, gap

    clear_a = carriage_clear_angle(d, obstacles)
    stop_out = leg_stop_angle("outboard", d, obstacles)
    stop_in = leg_stop_angle("inboard", d, obstacles)

    # the one thing the swing has to do: open far enough for the tray to pass
    # before the door meets the leg or a stile. In the outboard case that is
    # decided here; the inboard (measured) case is decided below.
    if clear_a is not None and stop_out < clear_a:
        notes.append(
            f"in the outboard-flange case the door stops on the front-left leg at "
            f"{stop_out:.0f} degrees, before the {clear_a:.0f} the extended carriage "
            "needs: the tray does not pass the open door"
        )

    # the knuckle against the steel and the stiles: it stands in the gap and
    # must share nothing with either
    knuckle = build_hinge(d)
    knuckle_hit = sum(_shared(knuckle, sol) for _l, c, sol in obstacles if c == "inboard")
    for lab, c, sol in obstacles:
        if c in ("measured", "stile"):
            v = _shared(knuckle, sol)
            if v > 1.0:
                notes.append(f"the knuckle stands {v / 1000:.1f} cm3 inside {lab}")
    for lab, c, sol in obstacles:
        if c == "stile":
            for m, o, _f, _g, v in [r for r in reports[SWING_ANGLES[1]] if r[1] == lab and r[4] > 1.0]:
                notes.append(f"{m} at 180 open runs into {o} ({v / 1000:.1f} cm3)")
    inboard_90, _ = worst(reports[SWING_ANGLES[0]], "inboard")
    if hh.front_flange_inboard is None:
        if knuckle_hit > 1.0 or inboard_90:
            notes.append(
                "the leg's Y-facing flange is not measured: neither its width nor "
                "which way it runs. IF it runs into the opening across the bay's front "
                "(vertex at the leg's outer corner), the knuckle at x "
                f"{d.lungs_x[0]:.0f}..{d.lungs_x[0] + HINGE_GAP:.0f} stands in it "
                f"({knuckle_hit / 1000:.1f} cm3) at the width the bolt pattern proves "
                f"({hh.span_h + hh.hole_d / 2:.1f}mm), and the door's swing stops at "
                f"{stop_in:.0f} degrees against the {clear_a if clear_a is not None else 180:.0f} "
                "the tray needs: the door does not open. MEASURE THIS: on a front leg, does the flange "
                "without holes run along the machine's front INTO the leg opening, or "
                "away from it; and how wide. Write LegHoles.front_flange_inboard and "
                "LegHoles.flange_w. The same reading answers the lungs carriage and "
                "the rear door."
            )
    elif hh.front_flange_inboard:
        if knuckle_hit > 1.0:
            notes.append(
                f"the knuckle stands {knuckle_hit / 1000:.1f} cm3 inside the front-left "
                "leg's inboard Y flange. The door does not open."
            )
        for m, o, _f, _g, v in inboard_90:
            notes.append(f"{m} at 90 open runs into the {o} ({v / 1000:.1f} cm3). The door does not open.")
        inboard_180, _ = worst(reports[SWING_ANGLES[1]], "inboard")
        for m, o, _f, _g, v in inboard_180:
            notes.append(f"{m} at 180 open runs into the {o} ({v / 1000:.1f} cm3). The door does not lie against the leg.")
        if stop_in < SWING_ANGLES[1]:
            notes.append(
                f"the door stops at {stop_in:.0f} degrees against the leg or a stile; the "
                f"ruling wants {SWING_ANGLES[1]:.0f}, flat against the leg"
            )

    # the tray through the open door
    hits_90, gap_90 = worst(reports[SWING_ANGLES[0]], "carriage")
    hits_180, gap_180 = worst(reports[SWING_ANGLES[1]], "carriage")
    if hits_180:
        notes.append(
            f"at 180 open the extended carriage still runs into the door: "
            f"{', '.join(f'{m} / {o} {v / 1000:.1f} cm3' for m, o, _f, _g, v in hits_180)}"
        )
    if clear_a is None:
        notes.append("no opening angle lets the extended carriage clear the open door")
    else:
        how = (
            f"at 90 it does not: {', '.join(f'{m} / {o} {v / 1000:.1f} cm3' for m, o, _f, _g, v in hits_90)}"
            if hits_90
            else f"at 90 it already does, by {gap_90:.1f}mm"
        )
        notes.append(
            f"TRAY THROUGH THE OPEN DOOR, standing note. The extended carriage clears "
            f"the open door, lay-up and strike from {clear_a:.0f} degrees; {how}; at 180 "
            f"it clears by {gap_180:.1f}mm. The door is {d.t:.0f} of birch and "
            f"{lt:.0f} of lay-up standing {AXIS_OFF:.2f} off a pin in the knuckle gap, "
            f"and the cheek passes {lungs_carriage.carriage_origin(d)[0] - d.lungs_opening_x[0]:.1f} "
            "past the stile's edge. "
            "Open the door past that angle before pulling the tray. Expected, and worth "
            "knowing."
        )

    # flat against the leg: the proud knuckle puts the folded door clear of
    # the flange's front face by the lay gap
    o180 = door_open(SWING_ANGLES[1], d).bounding_box()
    gaps = {
        fam: worst(reports[SWING_ANGLES[1]], fam)[1] for fam in ("measured", "inboard", "stile")
    }
    lay = o180.max.Y - (d.y_front - s.leg_wall_t)
    notes.append(
        f"AGAINST THE LEG AT 180, standing note. The knuckle is PROUD: pin {AXIS_OFF:.2f} "
        f"in front of the carcass plane (half the leg's {s.leg_wall_t:.2f} wall plus half "
        f"a {s.lungs_door_lay_gap:.1f} lay gap). At 180 the door lies y "
        f"{o180.max.Y:.2f}..{o180.min.Y:.2f}, its outer face {-lay:.2f} in front of the "
        f"flange's front face at y {d.y_front - s.leg_wall_t:.2f}; closest approach to the "
        f"X flange {gaps['measured']:.2f}, the Y flange band {gaps['inboard']:.2f}, a stile "
        f"{gaps['stile']:.2f}. The swing runs to {stop_in:.0f} degrees; the extended tray "
        f"passes from {clear_a if clear_a is not None else float('nan'):.0f}. "
        "The barrel to buy is an offset/raised-barrel continuous hinge; MEASURE THIS "
        "when it arrives. Expected, and worth knowing before a hold-open is chosen."
    )

    # -- what the geometry cannot enforce ------------------------------------
    notes.append(
        f"LAY-UPS ON THE WALLS, standing note. The bay's side lay-ups ({lt:.0f}mm on the "
        "left end wall's and the divider's lungs faces, not modelled, bay_walls.LINING_T) "
        f"start behind the door's inside face at y {d.t:.0f} and are cut around the "
        f"catch body at x {kx0:.0f}..{kx1:.0f} y {ky0:.0f}..{ky1:.0f} z {kz0:.0f}..{kz1:.0f}, "
        "which screws to birch; the shop pilots the divider through the body's slots "
        "on the first fit. Expected, and worth knowing before the lay-up is bonded."
    )
    # -- the callout lands on birch, and the door goes back on its pins -------
    notes += callouts.check_callouts(
        build(d),
        callouts_local(d),
        register(d),
        size=door_size(d),
        thickness=d.t,
        label=PART_NAME,
    )
    return notes


# ====================================================================
# EXPORT
# ====================================================================


def export(d: Datums = D) -> list:
    """STEP + DXF for the door (CUT and the pilot's pocket layer off the
    un-carved blank, VCARVE and REGISTER for the second fixture) and for the
    lay-up on a LINING layer, the knife template; STEP alone for the strike,
    the catch body and the knuckle."""
    written = []
    door_layers = flat_pattern(build(d, carve=False))
    door_layers.update(callouts.layers(callouts_local(d), register(d), width=door_size(d)[0]))
    written += export_part(build(d), PART_NAME, layers=door_layers)
    lining = build_lining(d)
    written += export_part(lining, LINING_NAME, layers={"LINING": flat_pattern(lining)["CUT"]})
    out_dir = EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for label, solid in (
        (STRIKE_NAME, build_strike(d)),
        (CATCH_NAME, build_catch(d)),
        (HINGE_NAME, build_hinge(d)),
    ):
        p = out_dir / f"{label}.step"
        export_step(solid, p, unit=Unit.MM)
        written.append(p)
    return written


# ====================================================================
# REPORT
# ====================================================================

if __name__ == "__main__":
    d = D
    w, h = door_size(d)
    flat = build(d)
    pb = place(flat, d).bounding_box()
    ax = hinge_axis(d)
    (kx0, kx1), (ky0, ky1), (kz0, kz1) = catch_station(d)
    print(
        f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {d.t:.0f} (opening "
        f"{d.lungs_opening_x[1] - d.lungs_opening_x[0]:.2f} less "
        f"HINGE_GAP {HINGE_GAP:.0f} and SIDE_REVEAL {SIDE_REVEAL:.0f}; {d.bay_h:.0f} less "
        f"2 x REVEAL {REVEAL:.0f}); pin {AXIS_OFF:.2f} proud"
    )
    print(
        f"  closed   x {pb.min.X:.1f}..{pb.max.X:.1f}  y {pb.min.Y:.1f}..{pb.max.Y:.1f}  "
        f"z {pb.min.Z:.1f}..{pb.max.Z:.1f}   volume {flat.volume / 1000:.1f} cm3"
    )
    print(f"  hinge    axis x {ax.position.X:.2f} y {ax.position.Y:.2f}, vertical; swing rise {swing_rise(d):.2f}")
    for a in SWING_ANGLES:
        ob = door_open(a, d).bounding_box()
        print(f"  open {a:3.0f} x {ob.min.X:.1f}..{ob.max.X:.1f}  y {ob.min.Y:.1f}..{ob.max.Y:.1f}")
    lw, lh = lining_size(d)
    print(f"  lay-up   {lw:.1f} x {lh:.1f} x {lining_t(d):.0f} on the inside face, inset {LINING_INSET:.0f}")
    cx, cy = pull_local(d)
    print(f"  pull     capsule {PULL_L:.0f} x {PULL_H:.0f} at door ({cx:.1f}, {cy:.1f})")
    for line in callouts.describe(callouts_local(d), register(d)):
        print(f"  {line}")
    print(
        f"  catch    body x {kx0:.1f}..{kx1:.1f} y {ky0:.1f}..{ky1:.1f} z {kz0:.1f}..{kz1:.1f} "
        f"on the divider; strike at door x {strike_local(d)[0][0]:.1f}..{strike_local(d)[0][1]:.1f}"
    )
    for n in check_lungs_door(d):
        print(f"  - {n}")
    for p in export(d):
        print(f"wrote {p}")
