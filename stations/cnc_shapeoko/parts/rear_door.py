"""Rear brain door: the drop-down shelf that closes the brain band.

WHAT THIS PART IS
=================

One 18mm Baltic birch door spanning the brain band's open rear face, between
the two end walls' inner faces, from the deck's top to the cap's underside,
hinged along its BOTTOM edge on a continuous (piano) hinge so it swings down
through 90 degrees and lies flat as a shelf. Ruled in the brief (v7, "Rear:
Brain"): "a full-width door that swings down on a piano hinge and becomes a
shelf, so a hand holding a multimeter has somewhere to put it. The door
carries the interlock switch, the IEC inlet, the RJ45, the external GX16s,
the glands for the spindle cable and the machine harness, and one indicator
per circuit on its inside face."

Closed, the door occupies the last ``t`` of the band in Y: its inside face at
``y_rear - t`` is the plane ``brain_partition`` stops at and the plane the
left end wall's louvre keeps a ``LOUVRE_LAND`` of solid birch behind. Its ends
land on the end walls' inner faces, its top edge runs ``TOP_REVEAL`` under
the cap, and its bottom edge sits ``HINGE_GAP`` above the deck, which is the
gap the hinge's knuckle lies in.

Everything on it obeys the split. ``Datums.brain_split_x`` divides the door
as it divides the band: the IEC inlet, the two glands and the two lamps sit
LEFT of it (sealed power); the RJ45, the two GX16 bulkheads and the clear
reveal sit RIGHT of it (exposed signal). The VFD's keep-out (``vfd_keepout_x``)
runs into the door's left end too: nothing is cut through the door there.

THE JOINTS. ALL FACES, ONE HOUSING
==================================

    left end wall     door's left end butts the wall's inner face
    right end wall    door's right end butts the wall's inner face
    brain_partition   partition's rear edge (end grain) lands on the door's
                      inside face; the two Torx catch screws go through the
                      door into that edge
    base_deck         no contact: the hinge knuckle lives in HINGE_GAP
    top_cap           no contact: TOP_REVEAL, which the swing arc needs
    rear_door_reveal  the ONE housing: the pane sits in a PT-deep rabbet in
                      the door's inside face, flush with it

The door's ends are cut to the end walls' faces with no side reveal: the
acceptance for this part reads the door's X extent against
``leg_x_inner - 2 * carcass_t`` to 0.1mm. The shop eases the ends on the
first fit; the model does not pre-spend that.

THE HINGE, AND WHY THE DOOR IS SHORTER THAN THE BAND
====================================================

A continuous hinge mounted with both leaves on the OUTER faces -- one on the
door's rear face, one on the deck's rear edge -- puts its knuckle on the
outside at the joint line, half in the gap between the door's bottom edge and
the deck's top face. So the gap has to be the knuckle's diameter, and the
door is the bay height less that gap and less a top reveal that the swing
arc needs: the door's top-inside corner rises ``hypot(H, t + off) - H`` as it
starts to turn. ``check_rear_door`` states both.

The axis is ``hinge_axis``. Every open-door question in this module is asked
by rotating the placed solid ``OPEN_ANGLE`` about it and reading the result,
so the arc and the shelf are the same geometry as the closed door.

THE INTERLOCK
=============

A roller-plunger safety limit switch on the door's inside face at the sealed
end, plunger axis along -X, riding a delrin STRIKER pad on the left end
wall's inner face. Closed, the door presses the roller; the moment the door
turns, the roller runs off the pad's rear edge (it moves rearward ~40mm in
the first 5 degrees) and the plunger extends. It feeds the CONTACTOR COIL
and nothing else, by doctrine: opening the door drops the VFD, the motion
controller and the extractor, never compute.

The contact mode is an open item and the check says so: a plunger pressed by
a CLOSED guard is negative-mode actuation, so the coil loop rides the switch's
NO contact and the direct-opening NC contact is not what opens it. A tongue
interlock would be positive-mode. The BOM line is a $10 panel interlock
switch, which is a limit switch, and the spec asks for plunger/roller. RULING
WANTED, not decided here.

THE INDICATORS
==============

Two 22mm pilot lights on the INSIDE face, sealed side, high, so a person who
has just opened the door reads which rails are live before reaching in.
White is ALWAYS-LIVE, amber is CONTACTOR. No red: the E-stop is the red
budget.

They are NOT cut through the door. A 22mm device clamps at most a 6mm panel
and its body is 46mm long, so a lamp through 18mm birch stands 28mm proud of
the door's rear face with its terminals in the service space, outside the
sealed compartment and outside the leg opening the gate measures the
carcass against. Instead the two lamps sit in the top leg of a 2mm aluminium
angle screwed to the door's inside face: bezels UP when the door is closed,
bodies hanging inside the sealed band. Drop the door and that top leg turns
to face the person standing behind the machine, which is what "facing the
operator when the door is down" asks for, more directly than a lamp in the
door's face would. The angle is the bracket; the lamps are reference solids
on it.

THE REVEAL (I27)
================

A rounded-rectangle window over the signal zone, glazed with CLEAR 3mm
acrylic (2026-09-03 finish ruling: every reveal is clear) in a rabbet on the
INSIDE face. Inside rather than outside so that a hand pushing from behind
pushes the pane INTO its rabbet, and so gravity seats it when the door is a
shelf. Four screws through the pane's lip retain it. The pane is a laser part
on the Universal and fits a QUARTER blank; the door itself is a Shapeoko or
track-saw part and never goes to the laser.

PANEL CONVENTION
================

Drawn flat: local origin at the door's lower-left corner AS SEEN FROM INSIDE
THE BAND (station +X to local +X), local +Y up, local +Z through the
thickness from the OUTSIDE (room) face at Z = 0 to the INSIDE (band) face at
Z = t. Placed with ``plane``, whose origin is (t, y_rear, deck_top + HINGE_GAP)
and whose z_dir is station -Y, the same convention the spine uses. In
``flat_pattern`` terms the inside face is the CUT face, an inside-face pocket
is POCKET_FRONT and an outside-face pocket is POCKET_BACK.

Every aperture in this door is an APERTURE in the carcass.py sense: nothing
square seats in one, so every corner is rounded inward. Round bores are their
own capsule; the slots and pockets carry an explicit ``corner_r``; the IEC
cutout is oversized by ``DEVICE_CLEAR`` so the inlet body's square corners
clear the cutter's radius.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, sqrt

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Location,
    Part,
    Plane,
    RectangleRounded,
    Unit,
    export_step,
    extrude,
)

from lib.house import GRID, LASER_BED_SMALL, QUARTER, SHEET_5X5_BALTIC, fits
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    GLAND_M25_D,
    GX16_PANEL_D,
    ROUTER_R,
    SCREW_CLEAR_D,
    SCREW_PILOT_D,
    Datums,
    PT,
    T,
    bore,
    export_part,
    flat_pattern,
    panel,
    through_slot,
)
from stations.cnc_shapeoko.parts.brain_partition import DOOR_LANDING
from stations.cnc_shapeoko.parts.spine_panel import signal_x

PART_NAME = "rear_door"
REVEAL_NAME = "rear_door_reveal"
SWITCH_ENV_NAME = "interlock_switch_env"
STRIKER_NAME = "interlock_striker"
BRACKET_NAME = "indicator_bracket"
LAMP_ENV_STEM = "indicator_env"
STAY_STEM = "rear_door_stay"

D: Datums = DATUMS

MATERIAL_REVEAL = "clear acrylic 3mm"
"""The reveal's material. RULED 2026-09-03 (finish): clear, never smoked.
``lib.house.MATERIALS['reveal']`` still reads smoked and is not this part's
to edit; the ruling is what the pane is ordered against."""


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# Boundaries come from Datums, joinery from carcass.py, material from
# house.py. Every value carries its SOURCE and CONFIDENCE.
# ====================================================================

# ---- the hinge --------------------------------------------------------------
HINGE = "continuous (piano) hinge, 1-1/2in open x 48in, stainless, surface mount"
"""SOURCE: brief BOM line "Piano hinge, rear door and lungs door, Amazon, 2".
No SKU on the line; the class of part every listing sells. CONFIDENCE:
representative. MEASURE THIS when it arrives: leaf thickness, knuckle
diameter, leaf width."""

HINGE_LEAF_T = 1.0
"""Leaf thickness. SOURCE: representative 0.040in listing. CONFIDENCE:
representative. Sets where the pin axis sits off the rear face."""

HINGE_KNUCKLE_D = 5.0
"""Knuckle outside diameter. SOURCE: representative listing (~0.19in over a
0.09in pin). CONFIDENCE: representative. Sets HINGE_GAP: the knuckle lies in
the gap between the door's bottom edge and the deck's top face."""

HINGE_LEAF_W = 16.5
"""One leaf, knuckle to edge: (38.1 open less the knuckle) / 2. SOURCE:
derived from the representative listing. CONFIDENCE: representative. Has to
fit the deck's 18mm rear edge, which is the check."""

HINGE_LEN = 1219.2
"""48in. SOURCE: the listing's length. CONFIDENCE: representative. Longer than
the door by about a millimetre: it is cut to the door, and the check says so."""

HINGE_GAP = HINGE_KNUCKLE_D
"""Gap between the door's bottom edge and deck_top. SOURCE: derived, the
knuckle's diameter. CONFIDENCE: derived."""

TOP_REVEAL = 2.0
"""Gap between the door's top edge and the cap's underside. SOURCE: design;
the swing arc's rise is under 0.5mm and the rest is a finish reveal.
CONFIDENCE: design, checked against the arc."""

HINGE_CLEAR = HINGE_GAP + TOP_REVEAL
"""What the door gives up against the bay height: the acceptance's "hinge
clearance constant". SOURCE: derived. CONFIDENCE: derived."""

HINGE_AXIS_OFF = HINGE_LEAF_T / 2
"""Pin axis behind the rear face: an unswaged continuous hinge carries its
barrel on the leaf plane, and the leaf plane is half a leaf off the face it
is screwed to. SOURCE: derived. CONFIDENCE: derived."""

OPEN_ANGLE = -90.0
"""Degrees about +X that drop the door to horizontal. SOURCE: task C07
acceptance ("rotated -90 deg about its hinge axis"). CONFIDENCE: spec. The
check confirms the sign by reading the result."""

# ---- cutting rules ----------------------------------------------------------
DEVICE_CLEAR = 1.0
"""Per-side oversize on a rectangular cutout whose device has square corners.
SOURCE: geometry -- a corner rounded at ROUTER_R needs r * (1 - 1/sqrt 2) =
0.93mm of oversize for a square corner to clear it. CONFIDENCE: derived,
rounded up."""

POCKET_FLOOR_MIN = T / 4
"""Thinnest birch left under any pocket. SOURCE: console_plate's rule, the
same 4.5mm. CONFIDENCE: chosen."""

# ---- the IEC inlet (sealed side, low) ---------------------------------------
IEC = "IEC C14 fused inlet module, screw mount, from the BOM's 4-pack"
IEC_CUTOUT = (47.5, 27.5)
"""Panel cutout, W x H, long axis horizontal. SOURCE: task C07 spec ("standard
27.5x47.5 panel cutout"), the figure every fused-inlet listing quotes.
CONFIDENCE: spec. MEASURE THIS against the 4-pack: the flange has to cover
the cutout plus DEVICE_CLEAR on every side."""
IEC_HOLE_PITCH = 40.0
IEC_HOLE_D = 3.2
"""The two mounting screws, on the long axis. SOURCE: representative fused
inlet module (the AC-01 class). CONFIDENCE: representative. MEASURE THIS."""
IEC_POS = (GRID * 15, GRID * 3)
"""Door-local centre. Low, so the cord drops along the door; above the hinge
leaf; inside the sealed zone and clear of the VFD keep-out. SOURCE: layout.
CONFIDENCE: chosen, checked."""

# ---- the two lamps (sealed side, high, INSIDE face) -------------------------
LAMP_BORE = 22.3
"""SOURCE: Schneider XB4 mounting diameter 22.5, cut 22.3 as console_plate
does. CONFIDENCE: datasheet."""
LAMP_BODY = (30.0, 47.0)
"""Body W x H behind the panel. SOURCE: se.com XB4BVB1 / XB4BVB5 product
sheets, "Width 30 mm, Height 47 mm", the figures console_plate captured for
the same family. CONFIDENCE: datasheet."""
LAMP_DEPTH = 54.0
"""Whole-product depth. SOURCE: se.com XB4BVB5, "Depth 54 mm". CONFIDENCE:
datasheet."""
LAMP_HEAD_PROUD = 8.0
"""How much of LAMP_DEPTH is the head in front of the panel. SOURCE: not on
the product sheet; assumption from the XB4 pilot-light outline. CONFIDENCE:
assumption. Moves only the envelope's reach."""
LAMP_PANEL_MAX = 6.0
"""Thickest panel the XB4 fixing collar clamps. SOURCE: Harmony XB4 mounting
data, panel thickness 1 to 6 mm. CONFIDENCE: datasheet. This is why the lamps
are not through the door: see BRACKET."""
BRACKET = "aluminium angle 40 x 40 x 2, black anodized, 160 long, on the door's inside face"
BRACKET_LEG = 40.0
BRACKET_T = 2.0
BRACKET_L = GRID * 8
"""The lamp bracket. One leg screwed flat to the door's inside face, the
other standing out into the band, top face up, carrying both lamps. 2mm sits
inside the XB4 clamp range with room to spare; 160 long puts its two screws
outboard of the hanging lamp bodies. SOURCE: design; stock angle.
CONFIDENCE: design. Not on the BOM, which the check says."""
BRACKET_X = GRID * 16.5
BRACKET_TOP = GRID * 1.5
"""Door-local centre X of the bracket and the drop of its top face below the
door's top edge. High on the sealed side, clear of the VFD keep-out and the
mast plate. SOURCE: layout. CONFIDENCE: chosen, checked."""
LAMP_PITCH = GRID * 3
"""Centre to centre along the bracket: two 47mm bodies side by side with
room between. SOURCE: LAMP_BODY. CONFIDENCE: derived."""
LAMPS = (
    ("always_live", "Schneider Harmony XB4BVB1, pilot light, white, 22mm, LED 24V", +1),
    ("contactor", "Schneider Harmony XB4BVB5, pilot light, orange, 22mm, LED 24V", -1),
)
"""(rail, model, side of the bracket's centre). The reading order for a
person standing behind the machine is +X to -X, so white ALWAYS-LIVE takes
the +X seat. Amber for CONTACTOR: no red on this door. SOURCE: brief "each
rail gets its own indicator lamp on the inside of the rear door"; BOM
"Indicator lamps, panel mount, per rail on the rear door, 2". CONFIDENCE:
chosen (models), the same family as the console."""

# ---- the two GX16 bulkheads (signal side, low) ------------------------------
GX16_FLANGE_D = 19.0
GX16_THREAD_L = 8.6
"""SOURCE: handsontec GX16 sheet, as captured by console_plate (flange O19,
M16x1 thread 8.6 long, S19 nut). CONFIDENCE: datasheet."""
GX16_PANEL_MAX = 5.0
"""Thickest panel an 8.6mm thread clamps with its nut on. SOURCE: derived,
thread less a nut. CONFIDENCE: chosen. console_plate cuts the same socket
through 18mm with no pocket; that plate's nut will not reach and is not this
part's to fix."""
GX16_POCKET_D = 26.0
"""Inside-face pocket for the S19 nut: 22 across corners plus room for a
spanner's jaw. CONFIDENCE: chosen."""
GX16_Y = GRID * 3
GX16S = (
    ("pendant", "GX16 panel socket, the house connector: the pendant run", GRID * 47),
    ("mast_camera", "GX16 panel socket, the house connector: the mast camera run", GRID * 50),
)
"""(run, model, door-local x). SOURCE: task C07 ("2x external GX16 bulkheads
for the pendant and mast-camera runs"). CONFIDENCE: spec."""

# ---- the RJ45 bulkhead (signal side, low) -----------------------------------
RJ45 = "Neutrik NE8FDP, RJ45 feedthrough, D-shape chassis"
RJ45_BORE = 24.0
RJ45_HOLES = ((-9.5, 12.0), (9.5, -12.0))
RJ45_HOLE_D = 3.5
RJ45_FLANGE = (26.0, 31.0)
"""The D-shape drilling: round 24 cutout, two screw holes on a 19 x 24
diagonal, 26 x 31 flange. SOURCE: the D-shape pattern as captured for the
PENGLIN PL183 in params (C00), which is the same universal D cutout.
CONFIDENCE: chosen (model), drilling by family. MEASURE THIS against the
bulkhead the BOM's "Panel-mount RJ45 bulkhead" line buys."""
RJ45_POS = (GRID * 44, GRID * 3)
"""Door-local centre, first in the signal row. SOURCE: layout. CONFIDENCE:
chosen, checked."""

# ---- the two glands (sealed side, mid) --------------------------------------
GLAND = "M25 cable gland, nylon, 13-18mm cable, with locknut"
GLAND_D = GLAND_M25_D
"""Panel bore. SOURCE: carcass.GLAND_M25_D, the house M25; task C07 (I91,
amended in D01): runs that cannot pass a GX16-6 get a gland, and these two
are M25. The BOM line still reads "Cable glands, 20mm: spindle cable, machine
harness, MAST FEED"; the spec's M25 wins here and the check says so.
CONFIDENCE: spec."""
GLAND_PANEL_MAX = 6.0
"""Thickest panel the gland's thread reaches through with the locknut on.
SOURCE: representative nylon M25 (10-12mm thread less a 5mm locknut).
CONFIDENCE: representative. MEASURE THIS."""
GLAND_POCKET_D = 40.0
"""Inside-face pocket for the locknut, across corners plus a spanner.
CONFIDENCE: representative."""
GLAND_Y = GRID * 15
GLANDS = (
    ("spindle", "VFD-to-spindle shielded cable", GRID * 15),
    ("harness", "motion-controller-to-machine harness", GRID * 19),
)
"""(run, what, door-local x). SOURCE: task C07. CONFIDENCE: spec. The harness
gland sits on the SEALED side by that spec while the controller lives on the
signal side, so the harness crosses the partition at the transit; the check
carries that as a standing note."""

# ---- the catch --------------------------------------------------------------
CATCH_SCREW = "5 x 40 pan head, Torx T25"
CATCH_CLEAR_D = SCREW_CLEAR_D
CATCH_Y = (GRID * 7, None)
"""Two screws through the door into the partition's rear edge (end grain),
at GRID*7 up from the bottom edge and GRID*7 down from the top; the second
is derived from the door height. SOURCE: task C07 ("tool-access catch, two
Torx screws, no hand latch"). CONFIDENCE: spec. The partition drills nothing
in its own model; the shop pilots its edge through these holes on the fit."""

# ---- the reveal -------------------------------------------------------------
WINDOW_LAND_X = GRID * 3
"""Solid door on each side of the window: from the partition's right face and
from the right end wall's inner face. SOURCE: design. CONFIDENCE: design. Big
enough that the right-hand stay's foot stays off the rabbet."""
WINDOW_Y = (GRID * 5, GRID * 2)
"""(bottom edge up from the door's bottom, top land down from the door's top).
The bottom clears the signal row's flanges and the rabbet's lip. SOURCE:
design. CONFIDENCE: design, checked."""
WINDOW_R = GRID
"""Window corner radius. An aperture, so rounded INWARD; a full capsule on a
300mm opening would be a stadium, so the radius is the grid. SOURCE: design.
CONFIDENCE: design."""
REVEAL_LIP = GRID * 0.6
"""Rabbet lip under the pane, 12mm: enough for a 5.4 clearance hole with
3mm of acrylic either side. SOURCE: design. CONFIDENCE: design."""
REVEAL_DEPTH = PT
"""Rabbet depth: the pane sits flush with the inside face. CONFIDENCE:
derived."""
PANE_FIT = 0.5
"""Per-side clearance of the pane in its rabbet, acrylic's thermal movement
plus the laser's kerf. CONFIDENCE: chosen."""
PANE_SCREW = "5 x 12 pan head, the house screw, exposed"
PANE_SCREW_LEN = 12.0
PANE_SCREW_D = SCREW_CLEAR_D
PANE_PILOT_D = SCREW_PILOT_D
PANE_PILOT_DEPTH = PANE_SCREW_LEN - PT
"""Four screws through the pane's lip into blind pilots in the rabbet floor.
SOURCE: console_plate's reveal fixing, shortened so the pilot leaves birch
under it. CONFIDENCE: chosen."""

# ---- the interlock switch ---------------------------------------------------
SWITCH = "Omron D4N-4132, safety limit switch, roller plunger, 1NC/1NO snap-action, 1 conduit M20"
"""SOURCE: task C07 ("plunger/roller safety switch, type per BOM, model
chosen"); BOM "Panel interlock switch, Amazon, 2". CONFIDENCE: chosen. The
BOM line's price buys a limit switch, not this; the ruling on contact mode
(see the docstring) decides which."""
SWITCH_BODY = (31.0, 55.0, 21.5)
"""W across the door, L along the plunger axis, D proud of the mounting face.
SOURCE: Omron D4N datasheet C68I-E-02, p.10, 1-conduit roller plunger
drawing: 31 max, 55, 21.5. CONFIDENCE: datasheet."""
SWITCH_HEAD = 20.5
"""Head section, square. SOURCE: same drawing, 20.5 x 20.5. CONFIDENCE:
datasheet."""
SWITCH_HEAD_REACH = 2.5 + 9.0 + 25.2
"""Body top to the roller's tip, plunger free. SOURCE: same drawing, the
2.5, 9 and 25.2 stacked along the axis. CONFIDENCE: datasheet, read off a
drawing rather than tabulated."""
SWITCH_PT = 2.0
SWITCH_OT = 4.0
"""Pretravel max and overtravel min. SOURCE: same datasheet p.11, D4N-[]132.
CONFIDENCE: datasheet."""
SWITCH_PRESS = SWITCH_PT + 1.0
"""How far the closed door presses the roller: the pretravel and a
millimetre of the overtravel. CONFIDENCE: chosen, inside the datasheet's
band."""
SWITCH_MOUNT_PITCH = 40.0
SWITCH_MOUNT_D = 4.0
"""Two M4 on 40 +-0.1, on the mounting face. SOURCE: same drawing.
CONFIDENCE: datasheet. Into birch they become 4mm wood screws in
SCREW_PILOT_D pilots."""
SWITCH_Y = GRID * 22.75
"""Door-local height of the plunger axis, 455: above the VFD standoff slab's
top (z 458.7 station) so the body never stands in the drive's air, and below
the lamps. SOURCE: layout against vfd_mount.standoff_slab. CONFIDENCE:
chosen, checked by the assembly."""

STRIKER = "black delrin pad, screwed to the left end wall's inner face"
STRIKER_T = GRID / 2
STRIKER_FACE = GRID
"""The pad the roller rides: 10 proud of the wall, 20 x 20 in Y-Z, the
'actuator on the end wall'. Delrin because it is the house wear material and
a roller runs off its rear edge every time the door opens. SOURCE: design.
CONFIDENCE: design. Its rear edge stops short of the door's inside face so
the pad and the door never touch."""
STRIKER_DOOR_CLEAR = 1.0

# ---- the stays --------------------------------------------------------------
STAY = "folding lid stay, two-arm, 200mm class, one each end"
STAY_FOLDED = (14.0, 160.0, 6.0)
"""W across the door, L up the door, proud of the inside face, FOLDED. SOURCE:
representative two-arm lid stay; not on the BOM, which the check says.
CONFIDENCE: representative. MEASURE THIS when a pair is chosen."""
STAY_END_INSET = GRID
STAY_Y0 = GRID * 4
"""Door-local position of each stay's foot: a grid in from the door's end,
four up from the bottom. SOURCE: layout. CONFIDENCE: chosen, checked."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the block
# above and on Datums.
# ====================================================================


def door_size(d: Datums = D) -> tuple[float, float]:
    """(width, height) of the cut blank: wall face to wall face, bay height
    less the hinge clearance."""
    return (d.x_right - 2 * d.t, d.bay_h - HINGE_CLEAR)


def z_bottom(d: Datums = D) -> float:
    """Station Z of the door's bottom edge."""
    return d.deck_top + HINGE_GAP


def plane(d: Datums = D) -> Plane:
    """Door frame: local +X to station +X, local +Y up, thickness into -Y
    from the rear face at y_rear. Origin at the door's lower-left corner on
    its OUTSIDE face."""
    return Plane(
        origin=(d.t, d.y_rear, z_bottom(d)),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def hinge_axis(d: Datums = D) -> Axis:
    """The pin, in station coordinates: along X, on the leaf plane behind
    the rear face, at the middle of the knuckle gap."""
    return Axis(
        (0.0, d.y_rear + HINGE_AXIS_OFF, d.deck_top + HINGE_GAP / 2),
        (1, 0, 0),
    )


def split_local(d: Datums = D) -> float:
    """Door-local X of the partition's LEFT face, the sealed/signal split."""
    return d.brain_split_x - d.t


def keepout_local(d: Datums = D) -> float:
    """Door-local X where the VFD keep-out ends; nothing is cut left of it."""
    return d.vfd_keepout_x[1] - d.t


def catch_positions(d: Datums = D) -> list[tuple[float, float]]:
    """Door-local centres of the two catch screws: on the partition's
    centreline, one low, one high."""
    _w, h = door_size(d)
    cx = split_local(d) + d.t / 2
    return [(cx, CATCH_Y[0]), (cx, h - CATCH_Y[0])]


def window_local(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """((x0, x1), (y0, y1)) of the window aperture, door-local."""
    _w, h = door_size(d)
    sx0, sx1 = signal_x(d)
    x0 = sx0 - d.t + WINDOW_LAND_X
    x1 = sx1 - d.t - WINDOW_LAND_X
    return ((x0, x1), (WINDOW_Y[0], h - WINDOW_Y[1]))


def window_centre(d: Datums = D) -> tuple[float, float]:
    (x0, x1), (y0, y1) = window_local(d)
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def window_size(d: Datums = D) -> tuple[float, float]:
    (x0, x1), (y0, y1) = window_local(d)
    return (x1 - x0, y1 - y0)


def rabbet_size(d: Datums = D) -> tuple[float, float]:
    w, h = window_size(d)
    return (w + 2 * REVEAL_LIP, h + 2 * REVEAL_LIP)


def rabbet_r() -> float:
    return WINDOW_R + REVEAL_LIP


def pane_size(d: Datums = D) -> tuple[float, float]:
    w, h = rabbet_size(d)
    return (w - 2 * PANE_FIT, h - 2 * PANE_FIT)


def pane_r() -> float:
    return rabbet_r() - PANE_FIT


def pane_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Pane-local (centred) positions of the four retaining screws: on the
    lip's centreline down each long side, at quarter and three-quarter
    height."""
    pw, ph = pane_size(d)
    lip_c = pw / 2 - (REVEAL_LIP - PANE_FIT) / 2
    return [(sx * lip_c, sy * ph / 4) for sx in (-1, 1) for sy in (-1, 1)]


def swing_rise(d: Datums = D) -> float:
    """How far the door's top-inside corner rises above its closed height
    as the door starts to turn: the arc's radius less its closed height."""
    _w, h = door_size(d)
    dy = d.t + HINGE_AXIS_OFF
    dz = HINGE_GAP / 2 + h
    return hypot(dy, dz) - dz


# -- the switch and its striker, station coordinates ----------------------


def switch_axis(d: Datums = D) -> tuple[float, float]:
    """(station y, station z) of the plunger axis. The axis runs along X and
    meets the left end wall's inner face at x = t through the striker."""
    return (d.y_rear - d.t - SWITCH_BODY[2] / 2, z_bottom(d) + SWITCH_Y)


def switch_body_x(d: Datums = D) -> tuple[float, float]:
    """Station X span of the switch body: the head end sits where the
    pressed roller puts it, the conduit end further right."""
    x0 = d.t + STRIKER_T + (SWITCH_HEAD_REACH - SWITCH_PRESS)
    return (x0, x0 + SWITCH_BODY[1])


def switch_mount_local(d: Datums = D) -> list[tuple[float, float]]:
    """Door-local pilot centres for the switch's two mounting screws: on the
    plunger axis, 40 apart, centred on the body."""
    x0, x1 = switch_body_x(d)
    cx = (x0 + x1) / 2 - d.t
    return [(cx - SWITCH_MOUNT_PITCH / 2, SWITCH_Y), (cx + SWITCH_MOUNT_PITCH / 2, SWITCH_Y)]


def build_switch_env(d: Datums = D) -> Part:
    """The switch as it sits on the door's inside face: body plus head, the
    head reaching to the striker's face with the roller pressed."""
    y, z = switch_axis(d)
    x0, x1 = switch_body_x(d)
    body = Box(
        SWITCH_BODY[1], SWITCH_BODY[2], SWITCH_BODY[0],
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    ).moved(Location((x0, y, z)))
    head_x0 = d.t + STRIKER_T
    head = Box(
        x0 - head_x0, SWITCH_HEAD, SWITCH_HEAD,
        align=(Align.MIN, Align.CENTER, Align.CENTER),
    ).moved(Location((head_x0, y, z)))
    return body + head


def build_striker(d: Datums = D) -> Part:
    """The delrin pad on the left end wall's inner face, centred on the
    plunger axis, its rear edge a millimetre off the door."""
    y, z = switch_axis(d)
    y1 = d.y_rear - d.t - STRIKER_DOOR_CLEAR
    return Box(
        STRIKER_T, STRIKER_FACE, STRIKER_FACE,
        align=(Align.MIN, Align.MAX, Align.CENTER),
    ).moved(Location((d.t, y1, z)))


# -- the lamps and their bracket -------------------------------------------


def bracket_top_z(d: Datums = D) -> float:
    """Station Z of the bracket's top face, the lamps' panel."""
    _w, h = door_size(d)
    return z_bottom(d) + h - BRACKET_TOP


def bracket_pilots_local(d: Datums = D) -> list[tuple[float, float]]:
    """Door-local pilots for the bracket's vertical leg: two, on the leg's
    centreline, a grid in from each end."""
    _w, h = door_size(d)
    y = h - BRACKET_TOP - BRACKET_LEG / 2
    return [(BRACKET_X - BRACKET_L / 2 + GRID, y), (BRACKET_X + BRACKET_L / 2 - GRID, y)]


def lamp_centre(side: int, d: Datums = D) -> tuple[float, float]:
    """(station x, station y) of one lamp's axis in the bracket's top leg:
    centred on what the leg has left past the vertical leg's thickness."""
    x = d.t + BRACKET_X + side * LAMP_PITCH / 2
    y = d.y_rear - d.t - BRACKET_T - (BRACKET_LEG - BRACKET_T) / 2
    return (x, y)


def build_bracket(d: Datums = D) -> Part:
    """The angle, station coordinates: vertical leg flat on the door's inside
    face, top leg standing into the band with the two lamp bores through it."""
    x0 = d.t + BRACKET_X - BRACKET_L / 2
    y_in = d.y_rear - d.t
    z_top = bracket_top_z(d)
    vert = Box(BRACKET_L, BRACKET_T, BRACKET_LEG, align=(Align.MIN, Align.MAX, Align.MAX)).moved(
        Location((x0, y_in, z_top))
    )
    top = Box(BRACKET_L, BRACKET_LEG, BRACKET_T, align=(Align.MIN, Align.MAX, Align.MAX)).moved(
        Location((x0, y_in, z_top))
    )
    angle = vert + top
    for _rail, _model, side in LAMPS:
        x, y = lamp_centre(side, d)
        angle -= Cylinder(LAMP_BORE / 2, BRACKET_T * 3, align=(Align.CENTER, Align.CENTER, Align.CENTER)).moved(
            Location((x, y, z_top - BRACKET_T / 2))
        )
    return angle


def build_lamp_env(side: int, d: Datums = D) -> Part:
    """One lamp on the bracket: its body hanging under the top leg and its
    head standing above it, station coordinates. The collar through the leg's
    bore is inside the bore and is not drawn. The 47 runs along the door."""
    x, y = lamp_centre(side, d)
    z_top = bracket_top_z(d)
    body_l = LAMP_DEPTH - LAMP_HEAD_PROUD - BRACKET_T
    body = Box(
        LAMP_BODY[1], LAMP_BODY[0], body_l, align=(Align.CENTER, Align.CENTER, Align.MAX)
    ).moved(Location((x, y, z_top - BRACKET_T)))
    head = Cylinder(
        LAMP_BODY[0] / 2, LAMP_HEAD_PROUD, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((x, y, z_top)))
    return body + head


# -- the stays ----------------------------------------------------------


def stay_local(end: str, d: Datums = D) -> tuple[float, float]:
    """Door-local lower-left corner of a folded stay's footprint."""
    w, _h = door_size(d)
    if end == "l":
        return (STAY_END_INSET, STAY_Y0)
    return (w - STAY_END_INSET - STAY_FOLDED[0], STAY_Y0)


def build_stay(end: str, d: Datums = D) -> Part:
    """One folded stay lying on the door's inside face, station coordinates."""
    lx, ly = stay_local(end, d)
    return Box(
        STAY_FOLDED[0], STAY_FOLDED[2], STAY_FOLDED[1],
        align=(Align.MIN, Align.MAX, Align.MIN),
    ).moved(Location((d.t + lx, d.y_rear - d.t, z_bottom(d) + ly)))


def stay_pilots_local(end: str, d: Datums = D) -> list[tuple[float, float]]:
    lx, ly = stay_local(end, d)
    cx = lx + STAY_FOLDED[0] / 2
    return [(cx, ly + GRID), (cx, ly + STAY_FOLDED[1] - GRID)]


# ====================================================================
# THE CUT LIST. One table so the check and the builder read the same thing.
# ====================================================================


@dataclass(frozen=True)
class Cut:
    """One feature cut in the door, door-local."""

    label: str
    side: str           # sealed | signal | split | keepout-free
    kind: str           # bore | slot | pocket_front | pocket_back | pilot
    cx: float
    cy: float
    size: tuple[float, float]       # (d, d) for round, (L, H) otherwise
    corner_r: float = 0.0
    depth: float | None = None      # None = through
    note: str = ""

    @property
    def is_through(self) -> bool:
        return self.depth is None

    @property
    def is_round(self) -> bool:
        return self.kind in ("bore", "pilot")

    @property
    def extent(self) -> tuple[tuple[float, float], tuple[float, float]]:
        l, h = self.size
        return ((self.cx - l / 2, self.cx + l / 2), (self.cy - h / 2, self.cy + h / 2))


def cuts(d: Datums = D) -> list[Cut]:
    """Every feature, in cutting order: pockets first, then through cuts."""
    out: list[Cut] = []
    _w, h = door_size(d)

    # -- sealed side: the lamp bracket's two pilots; the lamps cut nothing
    for x, y in bracket_pilots_local(d):
        out.append(Cut("bracket_pilot", "sealed", "pilot", x, y, (SCREW_PILOT_D, SCREW_PILOT_D),
                       corner_r=SCREW_PILOT_D / 2, depth=T / 2,
                       note="blind from the inside face, 4mm wood screw"))

    # -- sealed side: IEC inlet, oversized so the body's square corners clear
    iw, ih = IEC_CUTOUT
    iw += 2 * DEVICE_CLEAR
    ih += 2 * DEVICE_CLEAR
    out.append(Cut("iec_c14", "sealed", "slot", *IEC_POS, (iw, ih), corner_r=ROUTER_R,
                   note="fused inlet cutout, long axis horizontal"))
    for sx in (-1, 1):
        out.append(Cut(f"iec_screw_{'l' if sx < 0 else 'r'}", "sealed", "bore",
                       IEC_POS[0] + sx * IEC_HOLE_PITCH / 2, IEC_POS[1],
                       (IEC_HOLE_D, IEC_HOLE_D), corner_r=IEC_HOLE_D / 2))

    # -- sealed side: glands (pocket from the INSIDE for the locknut)
    for run, _what, x in GLANDS:
        out.append(Cut(f"gland_{run}_pocket", "sealed", "pocket_front", x, GLAND_Y,
                       (GLAND_POCKET_D, GLAND_POCKET_D), corner_r=GLAND_POCKET_D / 2,
                       depth=T - GLAND_PANEL_MAX, note="locknut pocket, inside face"))
        out.append(Cut(f"gland_{run}", "sealed", "bore", x, GLAND_Y, (GLAND_D, GLAND_D),
                       corner_r=GLAND_D / 2))

    # -- signal side: RJ45 D-shape
    out.append(Cut("rj45", "signal", "bore", *RJ45_POS, (RJ45_BORE, RJ45_BORE),
                   corner_r=RJ45_BORE / 2, note="D-shape body"))
    for i, (dx, dy) in enumerate(RJ45_HOLES):
        out.append(Cut(f"rj45_screw_{i}", "signal", "bore", RJ45_POS[0] + dx, RJ45_POS[1] + dy,
                       (RJ45_HOLE_D, RJ45_HOLE_D), corner_r=RJ45_HOLE_D / 2))

    # -- signal side: GX16s (pocket from the INSIDE for the nut)
    for run, _model, x in GX16S:
        out.append(Cut(f"gx16_{run}_pocket", "signal", "pocket_front", x, GX16_Y,
                       (GX16_POCKET_D, GX16_POCKET_D), corner_r=GX16_POCKET_D / 2,
                       depth=T - GX16_PANEL_MAX, note="S19 nut pocket, inside face"))
        out.append(Cut(f"gx16_{run}", "signal", "bore", x, GX16_Y, (GX16_PANEL_D, GX16_PANEL_D),
                       corner_r=GX16_PANEL_D / 2))

    # -- signal side: the reveal rabbet, then the window through it
    cx, cy = window_centre(d)
    out.append(Cut("reveal_rabbet", "signal", "pocket_front", cx, cy, rabbet_size(d),
                   corner_r=rabbet_r(), depth=REVEAL_DEPTH,
                   note="the pane's rabbet, inside face, flush"))
    out.append(Cut("reveal_window", "signal", "slot", cx, cy, window_size(d),
                   corner_r=WINDOW_R, note="the window, an aperture"))
    for sx, sy in pane_screws_local(d):
        out.append(Cut("pane_pilot", "signal", "pilot", cx + sx, cy + sy,
                       (PANE_PILOT_D, PANE_PILOT_D), corner_r=PANE_PILOT_D / 2,
                       depth=REVEAL_DEPTH + PANE_PILOT_DEPTH,
                       note="blind from the inside face, through the rabbet floor"))

    # -- on the split: the catch
    for i, (x, y) in enumerate(catch_positions(d)):
        out.append(Cut(f"catch_{i}", "split", "bore", x, y, (CATCH_CLEAR_D, CATCH_CLEAR_D),
                       corner_r=CATCH_CLEAR_D / 2, note="Torx screw into the partition's edge"))

    # -- pilots: the switch (sealed, in the keep-out's X but blind) and stays
    for x, y in switch_mount_local(d):
        out.append(Cut("switch_pilot", "sealed", "pilot", x, y, (SCREW_PILOT_D, SCREW_PILOT_D),
                       corner_r=SCREW_PILOT_D / 2, depth=T / 2,
                       note="blind from the inside face, 4mm wood screw"))
    for end in ("l", "r"):
        for x, y in stay_pilots_local(end, d):
            out.append(Cut(f"stay_{end}_pilot", "sealed" if end == "l" else "signal",
                           "pilot", x, y, (SCREW_PILOT_D, SCREW_PILOT_D),
                           corner_r=SCREW_PILOT_D / 2, depth=T / 2,
                           note="blind from the inside face"))
    return out


def _cutter(c: Cut) -> Part:
    """A Cut as a solid to subtract from the flat blank."""
    if c.kind == "bore":
        return bore(c.cx, c.cy, c.size[0])
    if c.kind == "pilot":
        return bore(c.cx, c.cy, c.size[0], depth=c.depth, side="front")
    if c.kind == "slot":
        return through_slot((c.cx, c.cy), c.size[0], c.size[1], corner_r=c.corner_r)
    if c.kind == "pocket_front":
        # through_slot built ``depth`` thick spans z -depth..2*depth; lifted by
        # T its floor lands at T - depth and it runs out the inside face
        s = through_slot((0.0, 0.0), c.size[0], c.size[1], thickness=c.depth, corner_r=c.corner_r)
        return s.moved(Location((c.cx, c.cy, T)))
    if c.kind == "pocket_back":
        # built ``depth/2`` thick it spans z -depth/2..depth: a pocket from the
        # outside face (Z = 0) to a floor at ``depth``
        s = through_slot((0.0, 0.0), c.size[0], c.size[1], thickness=c.depth / 2, corner_r=c.corner_r)
        return s.moved(Location((c.cx, c.cy, 0.0)))
    raise ValueError(f"unknown cut kind {c.kind!r}")


def build(d: Datums = D) -> Part:
    """The door, flat in panel-local coordinates."""
    w, h = door_size(d)
    part = panel(w, h, d.t)
    for c in cuts(d):
        part -= _cutter(c)
    return part


def build_reveal(d: Datums = D) -> Part:
    """The pane, flat, centred on the origin, PT thick, four screw holes."""
    pw, ph = pane_size(d)
    face = RectangleRounded(pw, ph, pane_r()).faces()[0]
    pane = extrude(face, amount=PT)
    for sx, sy in pane_screws_local(d):
        pane -= bore(sx, sy, PANE_SCREW_D, thickness=PT)
    return pane


def place(part: Part | None = None, d: Datums = D) -> Part:
    part = build(d) if part is None else part
    return plane(d) * part


def place_reveal(pane: Part | None = None, d: Datums = D) -> Part:
    pane = build_reveal(d) if pane is None else pane
    cx, cy = window_centre(d)
    return plane(d) * pane.moved(Location((cx, cy, T - REVEAL_DEPTH)))


def door_open(d: Datums = D) -> Part:
    """The placed door dropped to a shelf: rotated OPEN_ANGLE about the pin."""
    return place(d=d).rotate(hinge_axis(d), OPEN_ANGLE)


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, placed solid) for everything this module puts in the
    assembly: the door, the pane, the switch and its striker, the two lamp
    bodies, the two folded stays."""
    out: list[tuple[str, str, Part]] = [
        (PART_NAME, "carcass", place(d=d)),
        (REVEAL_NAME, "acrylic", place_reveal(d=d)),
        (SWITCH_ENV_NAME, "reference", build_switch_env(d)),
        (STRIKER_NAME, "wear", build_striker(d)),
    ]
    out.append((BRACKET_NAME, "steel", build_bracket(d)))
    for rail, _model, side in LAMPS:
        out.append((f"{LAMP_ENV_STEM}_{rail}", "reference", build_lamp_env(side, d)))
    for end in ("l", "r"):
        out.append((f"{STAY_STEM}_{end}", "reference", build_stay(end, d)))
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints for ``assembly.joints``. One housing (the pane in its
    rabbet); everything else meets on a face."""
    from stations.cnc_shapeoko.parts.bay_walls import WALLS
    from stations.cnc_shapeoko.parts.brain_partition import PART_NAME as PARTITION

    y_in = d.y_rear - d.t
    out: list[tuple] = [
        (WALLS[0].name, PART_NAME, "butt", None, 0.0, 0.0,
         "door's left end on the wall's inner face"),
        (WALLS[3].name, PART_NAME, "butt", None, 0.0, 0.0,
         "door's right end on the wall's inner face"),
        (PARTITION, PART_NAME, "butt", None, 0.0, 0.0,
         "partition's rear edge lands on the door's inside face; two Torx screws through the door into it"),
        (PART_NAME, REVEAL_NAME, "housing", "y", y_in, y_in + REVEAL_DEPTH,
         "pane flush in the inside-face rabbet"),
        (PART_NAME, SWITCH_ENV_NAME, "bearing", None, 0.0, 0.0,
         "switch body on the door's inside face, two screws"),
        (WALLS[0].name, STRIKER_NAME, "bearing", None, 0.0, 0.0,
         "striker pad on the wall's inner face"),
        (SWITCH_ENV_NAME, STRIKER_NAME, "bearing", None, 0.0, 0.0,
         "the roller on the pad's face, pressed"),
    ]
    out.append((PART_NAME, BRACKET_NAME, "butt", None, 0.0, 0.0,
                "bracket's vertical leg flat on the door's inside face, two screws"))
    for rail, _model, _side in LAMPS:
        out.append((BRACKET_NAME, f"{LAMP_ENV_STEM}_{rail}", "bearing", None, 0.0, 0.0,
                    "lamp clamped through the bracket's top leg"))
    for end in ("l", "r"):
        out.append((PART_NAME, f"{STAY_STEM}_{end}", "bearing", None, 0.0, 0.0,
                    "folded stay flat on the door's inside face"))
    return out


# ====================================================================
# OPEN-DOOR QUESTIONS
# ====================================================================


def rear_leg_flanges(d: Datums = D) -> list[tuple[str, Part]]:
    """The two rear legs' Y-facing flanges in the INBOARD case, the same
    construction ``machine.front_leg_flanges`` uses for the front pair: the
    plate just outside the opening's rear face, ``leg_wall_t`` thick, running
    into the opening by the width the bolt pattern proves, floor to table.
    Nothing when the flange is known to run outboard."""
    s = d.s
    h = s.leg_holes
    if h.front_flange_inboard is False:
        return []
    w = h.flange_w if h.flange_w is not None else h.span_h + h.hole_d / 2
    t = s.leg_wall_t
    out: list[tuple[str, Part]] = []
    for label, x0 in (("rear left leg, Y flange", d.x_left), ("rear right leg, Y flange", d.x_right - w)):
        plate = Box(w, t, s.table_h, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
            Location((x0, d.y_rear, 0.0))
        )
        out.append((label, plate))
    return out


def open_clash(d: Datums = D) -> list[tuple[str, float, float]]:
    """(flange, shared mm3, X overlap) for the open door against each rear
    leg's inboard-case Y flange."""
    door = door_open(d)
    db = door.bounding_box()
    out: list[tuple[str, float, float]] = []
    for label, plate in rear_leg_flanges(d):
        pb = plate.bounding_box()
        if db.max.X < pb.min.X or pb.max.X < db.min.X:
            continue
        try:
            shared = door & plate
        except Exception:
            continue
        if shared is None or shared.volume <= 1.0:
            continue
        sb = shared.bounding_box()
        out.append((label, shared.volume, sb.max.X - sb.min.X))
    return out


# ====================================================================
# CHECKS
# ====================================================================


def _on_side(c: Cut, d: Datums) -> bool:
    (x0, x1), _ = c.extent
    sp = split_local(d)
    if c.side == "sealed":
        return x1 <= sp
    if c.side == "signal":
        return x0 >= sp + d.t
    if c.side == "split":
        return x0 >= sp and x1 <= sp + d.t
    return True


def check_rear_door(d: Datums = D) -> list[str]:
    """What this part has to be true for. The assembly's interference check
    owns whether it meets its neighbours closed; these are the things that
    are wrong before the solids are compared, plus the open-door questions
    only this module can ask."""
    notes: list[str] = []
    w, h = door_size(d)
    s = d.s
    all_cuts = cuts(d)

    # -- the blank -----------------------------------------------------------
    if abs(w - (s.leg_x_inner - 2 * s.carcass_t)) > 0.1:
        notes.append(
            f"the door is {w:.2f} wide and the end walls' inner faces are "
            f"{s.leg_x_inner - 2 * s.carcass_t:.2f} apart: it does not span them"
        )
    if abs(h - (d.bay_h - HINGE_CLEAR)) > 1e-6:
        notes.append(f"the door is {h:.2f} tall, not bay_h less HINGE_CLEAR")
    if abs(DOOR_LANDING - d.t) > 1e-6:
        notes.append(
            f"the partition stops {DOOR_LANDING:.1f} short of y_rear and the door is "
            f"{d.t:.1f} thick: the partition's rear edge does not land on the door"
        )
    travel = min(s.travel_x, s.travel_y)
    if max(w, h) > travel:
        notes.append(
            f"door blank {w:.0f} x {h:.0f} exceeds the machine's own {travel:.0f}mm "
            "travel: cut on the track saw or Shaper Origin, by ruling, 2026-09-02. "
            "Expected, and worth knowing before it goes to either tool."
        )
    if not fits((w, h), SHEET_5X5_BALTIC):
        notes.append(f"door blank {w:.0f} x {h:.0f} does not come out of a 5x5 Baltic sheet")

    # -- the hinge -----------------------------------------------------------
    rise = swing_rise(d)
    if rise >= TOP_REVEAL:
        notes.append(
            f"the door's top corner rises {rise:.2f}mm on the swing and the top reveal "
            f"is {TOP_REVEAL:.1f}: the door hits the cap before it opens"
        )
    # the lamp heads on the bracket are the highest thing that swings; their
    # arc has to clear the cap's underside too
    z_head = bracket_top_z(d) + LAMP_HEAD_PROUD
    dy = d.t + HINGE_AXIS_OFF + BRACKET_LEG
    dz = z_head - hinge_axis(d).position.Z
    head_rise = hypot(dy, dz) - dz
    if z_head + head_rise >= d.top_z[0]:
        notes.append(
            f"a lamp head tops out at z {z_head:.1f} and rises {head_rise:.1f} on the "
            f"swing against the cap's underside at {d.top_z[0]:.1f}: the bracket is too high"
        )
    if BRACKET_T > LAMP_PANEL_MAX:
        notes.append(f"the bracket's {BRACKET_T:.0f}mm leg is thicker than the lamps clamp")
    if LAMP_PITCH < LAMP_BODY[1] + 2.0:
        notes.append("the two lamp bodies overlap on the bracket")
    if BRACKET_L / 2 - GRID < LAMP_PITCH / 2 + LAMP_BODY[1] / 2 + SCREW_CLEAR_D:
        notes.append("the bracket's screws sit behind the hanging lamp bodies: it is too short")
    if HINGE_LEAF_W > d.t:
        notes.append(
            f"the hinge leaf is {HINGE_LEAF_W:.1f} wide and the deck's rear edge is "
            f"{d.t:.0f}: the deck-side leaf hangs off the edge"
        )
    notes.append(
        f"the hinge is a representative {HINGE}: leaf {HINGE_LEAF_T:.1f}, knuckle "
        f"o{HINGE_KNUCKLE_D:.1f} (which is HINGE_GAP), leaf {HINGE_LEAF_W:.1f} wide, "
        f"{HINGE_LEN:.1f} long against a {w:.1f} door, so it is cut to length. The BOM "
        "line carries no SKU. MEASURE THIS when it arrives; the gap and the axis follow "
        "the knuckle."
    )

    # -- every cut on its side, rounded, inside the blank, off the keep-out --
    sp = split_local(d)
    ko = keepout_local(d)
    for c in all_cuts:
        (x0, x1), (y0, y1) = c.extent
        if not _on_side(c, d):
            notes.append(
                f"{c.label} lies at door x {x0:.1f}..{x1:.1f} and is declared {c.side}; "
                f"the split is at {sp:.1f}..{sp + d.t:.1f}. It is on the wrong side."
            )
        if c.corner_r <= 0.0 and not c.is_round:
            notes.append(f"{c.label} has square corners: not millable, and not an aperture")
        if x0 < 0 or x1 > w or y0 < 0 or y1 > h:
            notes.append(f"{c.label} runs off the {w:.0f} x {h:.0f} blank")
        if c.is_through and x0 < ko:
            notes.append(
                f"{c.label} is cut through the door at x {x0:.1f}, inside the VFD "
                f"keep-out (door x < {ko:.1f}): nothing passes through the door there"
            )
        if c.depth is not None and c.kind.startswith("pocket") and T - c.depth < POCKET_FLOOR_MIN - 1e-9:
            notes.append(
                f"{c.label} is {c.depth:.1f} deep in {T:.0f}, leaving {T - c.depth:.1f} "
                f"under the {POCKET_FLOOR_MIN:.1f} floor"
            )
    if IEC_POS[1] - (IEC_CUTOUT[1] / 2 + DEVICE_CLEAR) <= HINGE_LEAF_W:
        notes.append(
            f"the IEC cutout's bottom edge is {IEC_POS[1] - IEC_CUTOUT[1] / 2 - DEVICE_CLEAR:.1f} "
            f"up the door and the hinge leaf reaches {HINGE_LEAF_W:.1f}: the inlet sits on the leaf"
        )

    # -- the window and the pane --------------------------------------------
    (wx0, wx1), (wy0, wy1) = window_local(d)
    sx0, sx1 = signal_x(d)
    if wx0 + d.t < sx0 or wx1 + d.t > sx1:
        notes.append(
            f"the window runs x {wx0 + d.t:.1f}..{wx1 + d.t:.1f} station and the signal "
            f"zone is {sx0:.1f}..{sx1:.1f}: the reveal is not wholly over the signal side"
        )
    rw, rh = rabbet_size(d)
    if wy0 - REVEAL_LIP <= GX16_Y + GX16_POCKET_D / 2 or wy0 - REVEAL_LIP <= RJ45_POS[1] + RJ45_FLANGE[1] / 2:
        notes.append("the reveal's rabbet runs into the signal row's flanges")
    (lx, _ly) = stay_local("r", d)
    if wx1 + REVEAL_LIP + PANE_FIT > lx:
        notes.append(
            f"the rabbet reaches door x {wx1 + REVEAL_LIP:.1f} and the right stay's foot "
            f"starts at {lx:.1f}: the stay screws into the rabbet floor"
        )
    pw, ph = pane_size(d)
    if not fits((pw, ph), QUARTER):
        notes.append(f"the pane is {pw:.1f} x {ph:.1f} and does not come out of a QUARTER blank")
    if not fits((pw, ph), LASER_BED_SMALL):
        notes.append(f"the pane is {pw:.1f} x {ph:.1f} and does not fit the small Universal bed")
    if pane_r() <= 0 or WINDOW_R < ROUTER_R:
        notes.append("the window's corner radius is under the cutter's")
    lip_left = (REVEAL_LIP - PANE_FIT - PANE_SCREW_D) / 2
    if lip_left < 2.0:
        notes.append(
            f"a {PANE_SCREW_D:.1f} hole in a {REVEAL_LIP - PANE_FIT:.1f} lip leaves "
            f"{lip_left:.1f} of acrylic either side"
        )

    # -- the interlock -------------------------------------------------------
    y_axis, z_axis = switch_axis(d)
    x0, _x1 = switch_body_x(d)
    if x0 - (d.t + STRIKER_T) != SWITCH_HEAD_REACH - SWITCH_PRESS:
        notes.append("the switch head does not reach the striker")
    if SWITCH_PRESS < SWITCH_PT or SWITCH_PRESS > SWITCH_PT + SWITCH_OT:
        notes.append(
            f"the door presses the roller {SWITCH_PRESS:.1f}: outside the switch's "
            f"pretravel {SWITCH_PT:.0f} plus overtravel {SWITCH_OT:.0f}"
        )
    if y_axis + SWITCH_BODY[2] / 2 > d.y_rear - d.t + 1e-6:
        notes.append("the switch body reaches through the door")
    # the striker has to land on solid birch, not on a louvre slot
    from stations.cnc_shapeoko.parts.bay_walls import placed_all as walls_placed
    wall = walls_placed(d)[0]
    probe = Box(1.0, STRIKER_FACE, STRIKER_FACE, align=(Align.MAX, Align.MAX, Align.CENTER)).moved(
        Location((d.t, d.y_rear - d.t - STRIKER_DOOR_CLEAR, z_axis))
    )
    try:
        solid = (wall & probe).volume
    except Exception:
        solid = 0.0
    if solid < STRIKER_FACE * STRIKER_FACE * 1.0 - 1.0:
        notes.append(
            f"the striker pad lands on {solid / (STRIKER_FACE * STRIKER_FACE):.0%} birch at "
            f"y {y_axis:.0f} z {z_axis:.0f}: the louvre field is under it"
        )
    notes.append(
        f"INTERLOCK CONTACT MODE, standing note. {SWITCH} on the door's inside face, "
        f"axis at y {y_axis:.1f} z {z_axis:.1f} station meeting the left end wall's inner "
        f"face through a {STRIKER_T:.0f}mm delrin striker; the coil rides the NO contact, "
        "closed while the door presses the roller. A plunger pressed by a CLOSED guard is "
        "negative-mode actuation: the direct-opening NC is not what opens the loop, and a "
        "stuck plunger leaves the coil fed. A tongue interlock (D4NS class) would be "
        "positive-mode. RULING WANTED; the BOM's $10 line buys a limit switch."
    )

    # -- the open door -------------------------------------------------------
    door = door_open(d)
    ob = door.bounding_box()
    if ob.min.Z <= 0.0:
        notes.append(f"the open door reaches z {ob.min.Z:.1f}: it lies on the floor")
    if ob.max.Z > ob.min.Z + d.t + HINGE_GAP + 1.0:
        notes.append(
            f"the open door spans z {ob.min.Z:.1f}..{ob.max.Z:.1f}: OPEN_ANGLE did not "
            "lay it flat; the sign is wrong"
        )
    if ob.max.Y <= d.y_rear:
        notes.append("the open door did not swing rearward: OPEN_ANGLE's sign is wrong")
    if ob.min.X < d.t - 1e-6 or ob.max.X > d.x_right - d.t + 1e-6:
        notes.append("the open door reaches into a rear leg's bolt flange")
    hh = s.leg_holes
    clashes = open_clash(d)
    if hh.front_flange_inboard is None and clashes:
        hit = ", ".join(f"{lbl} by {ov:.1f}" for lbl, _v, ov in clashes)
        notes.append(
            "the rear leg's Y-facing flange is not measured: neither its width nor "
            "which way it runs. IF it runs into the opening across the band's rear "
            "(vertex at the leg's outer corner), the OPEN door lies through it at the "
            f"width the bolt pattern proves ({hh.span_h + hh.hole_d / 2:.1f}mm): {hit}mm, "
            f"over the door's {d.t:.0f}mm thickness at z {ob.min.Z:.0f}..{ob.max.Z:.0f}. "
            "The door does not drop to a shelf. MEASURE THIS: on a rear leg, does the "
            "flange without holes run along the machine's rear INTO the leg opening, or "
            "away from it; and how wide. Write LegHoles.front_flange_inboard and "
            "LegHoles.flange_w. The same reading answers the lungs carriage."
        )
    elif hh.front_flange_inboard and clashes:
        for lbl, vol, ov in clashes:
            notes.append(
                f"the open door runs {ov:.1f}mm into the {lbl} ({vol / 1000:.1f} cm3). "
                "It does not drop to a shelf."
            )

    # -- standing notes: what the geometry cannot enforce --------------------
    notes.append(
        f"LAMP BRACKET, standing note. The two rail lamps are not cut through the door: "
        f"a 22mm lamp clamps {LAMP_PANEL_MAX:.0f}mm and is {LAMP_DEPTH:.0f} deep, so in "
        f"{T:.0f}mm birch its body would stand {LAMP_DEPTH - LAMP_HEAD_PROUD - LAMP_PANEL_MAX - (T - LAMP_PANEL_MAX):.0f}mm "
        "out the rear face into the service space and outside the leg opening. They sit "
        f"in a {BRACKET} instead, bezels up, top face at z {bracket_top_z(d):.0f}, bodies "
        "inside the sealed band; dropped, the leg faces the person behind the machine. "
        "The angle is NOT on the BOM. Expected, and worth knowing before the lamps are "
        "ordered as door-mount."
    )
    notes.append(
        f"GLANDS, standing note. Both glands are M{GLAND_D:.0f} by the C07 spec (I91, D01) "
        "where the BOM line reads 20mm; the spec wins and the BOM line follows. The "
        "harness gland sits on the SEALED side by the same spec while the motion "
        "controller is on the signal side, so the harness crosses the partition at "
        "the transit with the CT leads. Expected, and worth knowing before the "
        "harness is pulled."
    )
    notes.append(
        f"CATCH, standing note. Two {CATCH_SCREW} through the door into the partition's "
        "rear edge at door x "
        + ", ".join(f"({x:.1f}, {y:.1f})" for x, y in catch_positions(d))
        + "; the partition drills nothing in its own model and the shop pilots its "
        "end grain through these holes on the first fit. Expected, and worth knowing."
    )
    notes.append(
        f"STAYS, standing note. Two {STAY}, folded {STAY_FOLDED[0]:.0f} x "
        f"{STAY_FOLDED[1]:.0f} x {STAY_FOLDED[2]:.0f} on the inside face, are reference "
        "solids from a representative listing and are NOT on the BOM. MEASURE THIS "
        "when a pair is chosen; the open shelf's load rating is theirs."
    )
    return notes


# ====================================================================
# EXPORT
# ====================================================================


def export(d: Datums = D) -> list:
    """STEP + DXF for the door (birch, CUT and the pocket layers), the pane on
    an ACRYLIC layer for the Universal, and STEP alone for the reference and
    wear solids."""
    written = []
    written += export_part(build(d), PART_NAME)
    pane = build_reveal(d)
    written += export_part(pane, REVEAL_NAME, layers={"ACRYLIC": flat_pattern(pane)["CUT"]})
    out_dir = EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for label, group, solid in placed_all(d):
        if group in ("carcass", "acrylic"):
            continue
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
    placed = place(flat, d)
    pb = placed.bounding_box()
    ob = door_open(d).bounding_box()
    ax = hinge_axis(d)
    (wx0, wx1), (wy0, wy1) = window_local(d)
    pw, ph = pane_size(d)
    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {d.t:.0f} (bay {d.bay_h:.0f} less "
          f"HINGE_CLEAR {HINGE_CLEAR:.0f} = gap {HINGE_GAP:.0f} + reveal {TOP_REVEAL:.0f})")
    print(f"  closed   x {pb.min.X:.1f}..{pb.max.X:.1f}  y {pb.min.Y:.1f}..{pb.max.Y:.1f}  "
          f"z {pb.min.Z:.1f}..{pb.max.Z:.1f}   volume {flat.volume / 1000:.1f} cm3")
    print(f"  hinge    axis y {ax.position.Y:.2f} z {ax.position.Z:.2f}, swing rise {swing_rise(d):.2f}")
    print(f"  open     x {ob.min.X:.1f}..{ob.max.X:.1f}  y {ob.min.Y:.1f}..{ob.max.Y:.1f}  "
          f"z {ob.min.Z:.1f}..{ob.max.Z:.1f}")
    print(f"  split at door x {split_local(d):.1f}; keep-out ends at {keepout_local(d):.1f}")
    print(f"  window   door x {wx0:.1f}..{wx1:.1f}  y {wy0:.1f}..{wy1:.1f}, r {WINDOW_R:.0f}; "
          f"pane {pw:.1f} x {ph:.1f} x {PT:.0f} {MATERIAL_REVEAL}, r {pane_r():.1f}")
    for c in cuts(d):
        print(f"  {c.label:<24} {c.side:<7} {c.kind:<12} ({c.cx:7.1f}, {c.cy:6.1f}) "
              f"{c.size[0]:5.1f} x {c.size[1]:5.1f}"
              + (f"  {c.depth:.1f} deep" if c.depth is not None else "  through"))
    for n in check_rear_door(d):
        print(f"  - {n}")
    for p in export(d):
        print(f"wrote {p}")
