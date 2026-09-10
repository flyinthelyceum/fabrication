"""Rear brain door: the drop-down shelf that closes the brain band.

WHAT THIS PART IS
=================

One 18mm Baltic birch door spanning the brain band's open rear face, INSET
between the two REAR STILES' inner edges (``parts/stiles.py``, RULED
2026-09-04: the flange band at each corner is a fixed stile and every door
sits between stile and divider, flush, no overlay), from the deck's top to
the cap's underside, hinged along its BOTTOM edge on a continuous (piano)
hinge so it swings down through 90 degrees and lies flat as a shelf. Between
the stiles it also drops between the two rear legs' flange TOES, which the
wall-to-wall door of C07 could not. Ruled in the brief (v7, "Rear:
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
as it divides the band: the IEC inlet and the two glands sit LEFT of it
(sealed power); the RJ45 and the clear reveal sit RIGHT of it (exposed
signal). The two rail indicator lamps and the two GX16 bulkheads that were
here were STRUCK 2026-09-09 (subtract pass, items 06 and 09): the lamps
reported a rail state nothing else on the station reads, and the bulkheads
served the pendant (now a USB-C coupler on the console) and the mast camera
(parked to 2026-11-02). The VFD's keep-out (``vfd_keepout_x``)
runs into the door's left end too: nothing is cut through the door there.

THE JOINTS. ALL FACES, ONE HOUSING
==================================

    rear-left stile   door's left end, END_REVEAL off the stile's inner edge
    rear-right stile  door's right end, the same
    brain_partition   partition's rear edge (end grain) lands on the door's
                      inside face; the two Torx catch screws go through the
                      door into that edge
    base_deck         no contact: the hinge knuckle lives in HINGE_GAP
    top_cap           no contact: TOP_REVEAL, which the swing arc needs
    rear_door_reveal  the ONE housing: the pane sits in a PT-deep rabbet in
                      the door's inside face, flush with it
    interlock_block   an 18mm birch offcut hung from the CAP's underside at
                      the door's sealed end, the seat the interlock switch
                      body screws to; the key on the door reaches into the
                      switch's head

The door's ends stand ``END_REVEAL`` off each stile's inner edge, the house
reveal, so the door reads as one more inset panel in the run of them.

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

RULED 2026-09-04 (Jared): a TONGUE interlock, positive mode, Omron D4NS
class. The operation key (D4DS-K1) is screwed to the door's inside face at
the sealed end, its tongue standing ``KEY_TONGUE[2]`` into the band along
-Y; the switch body sits on the carcass side, on an 18mm birch offcut block hung
from the cap's underside (the door's left end is now a stile's width in
from the wall, so a block on the wall no longer reaches the key), its
mounting face parallel to the door and ``SWITCH_STANDOFF`` inside it, head
up, key slot facing the door.
Closed, the tongue is in the head and the cam holds the direct-opening NC
contact closed; the moment the door turns the tongue withdraws and the NC
contact is forced open. That NC contact feeds the CONTACTOR COIL and nothing
else, by doctrine: opening the door drops the VFD, the motion controller and
the extractor, never compute. Positive mode: the guard's OPENING is what
breaks the loop, so a stuck mechanism cannot leave the coil fed. The
roller-plunger striker this file carried until 2026-09-04 is gone.

The switch and the key are reference solids drawn off the D4NS datasheet
(``SWITCH_SOURCE``): the body, the head's key slot, the K1 plate and tongue.
``check_rear_door`` reads the closed-door engagement (the standoff against
the datasheet's 44 to 46.5 band, the tongue's reach into the head) and the
open-door clearance (the key swung with the door against the switch and its
block, at several angles) off those solids. The block is a real birch part,
exported as a flat, and is NOT nested: it is a 40 x 120 offcut, and the
standing note says so.

THE INDICATORS
==============

STRUCK 2026-09-09. The two 22mm rail pilot lights (white ALWAYS-LIVE, amber
CONTACTOR, counterbored from the inside to a 6mm land, ruled 2026-09-04) are
gone with their cuts, envelopes and checks; git has the geometry.

THE REVEAL (I27)
================

A rounded-rectangle window over the signal zone, glazed with CLEAR 3mm
acrylic (2026-09-03 finish ruling: every reveal is clear) in a rabbet on the
INSIDE face. Inside rather than outside so that a hand pushing from behind
pushes the pane INTO its rabbet, and so gravity seats it when the door is a
shelf. Four screws through the pane's lip retain it. The pane is cut on the
Universal and fits a QUARTER blank; the door itself is a Shapeoko or
track-saw part and never goes to the Universal.

THE CALLOUTS (C17)
==================

Two words V-carved into the OUTSIDE face, through the black to raw birch:
``CALLOUT_VFD`` over the drive, starting ``VFD_CALLOUT_X0`` in from the
door's left end so the word sits over the drive's own keep-out and reads
right across the sealed side (a word centred on the sealed span would sit
over the glands and name nothing), and ``CALLOUT_MAINS`` centred over the
IEC inlet, where the cord goes in. Both stay left of the split, which
``check_rear_door`` measures.

The outside face is this drawing's Z = 0, its BACK, so the second fixture
sees the CUT drawing turned over. That fixture gets its OWN file,
``CARVE_NAME``.dxf: the door outline flipped about its vertical centreline
for reference, and ``VCARVE`` and ``REGISTER`` in that same flipped frame,
as the carved face is seen (``callouts.carve_drawing``). ``PART_NAME``.dxf
keeps the CUT frame only, so no file holds two frames. The register is the
two catch bores, through holes on the split's centreline, one low and one
high, so the pins are 333mm apart; in the carve drawing its circles sit on
the flipped bores. The model's word is mirrored in the door frame so it
reads from the room.

PANEL CONVENTION
================

Drawn flat: local origin at the door's lower-left corner AS SEEN FROM INSIDE
THE BAND (station +X to local +X), local +Y up, local +Z through the
thickness from the OUTSIDE (room) face at Z = 0 to the INSIDE (band) face at
Z = t. Placed with ``plane``, whose origin is (x_left(d), y_rear, deck_top +
HINGE_GAP) -- the rear-left stile's inner edge plus END_REVEAL -- and whose
z_dir is station -Y, the same convention the spine uses. In
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
    Location,
    Part,
    Plane,
    RectangleRounded,
    Unit,
    export_step,
    extrude,
)

from lib.house import GRID, LASER_BED_SMALL, QUARTER, SHEET_4X8, fits
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    GLAND_M25_D,
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
from stations.cnc_shapeoko.parts import callouts
from stations.cnc_shapeoko.parts.brain_partition import DOOR_LANDING
from stations.cnc_shapeoko.parts.spine_panel import signal_x

PART_NAME = "rear_door"
REVEAL_NAME = "rear_door_reveal"
CARVE_NAME = "rear_door_carve"
"""The second fixture's DXF, the outside-face carve in its own flipped frame
(C17). No STEP: the solid is PART_NAME's."""
SWITCH_ENV_NAME = "interlock_switch_env"
KEY_ENV_NAME = "interlock_key_env"
BLOCK_NAME = "interlock_block"
"""The switch's seat: a birch offcut, a real part with its own flat (DXF) and
placed STEP, in the ``offcut`` group so the nest does not look for it."""
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
HINGE = "continuous (piano) hinge, 1in open x 48in, stainless, surface mount"
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

HINGE_LEAF_W = (25.4 - HINGE_KNUCKLE_D) / 2
"""One leaf, knuckle to edge: (25.4 open less the knuckle) / 2 = 10.2. SOURCE:
derived from the representative listing. CONFIDENCE: representative. At 12mm
house stock (ruling 18) the 1-1/2in (38.1) open hinge's 16.5 leaf overhangs
the deck's rear edge and a stile's inner edge, both 12mm deep, so the hinge is
the 1in (25.4) open size: a 10.2 leaf lands on 12mm with margin. Has to fit
the panel edge it screws to, which is the check. MEASURE THIS when it arrives."""

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

END_REVEAL = TOP_REVEAL
"""Gap between each end of the door and the rear stile's inner edge it sits
beside (2026-09-04: the door is between the stiles). The house reveal, the
same figure the top edge and every drawer front get. CONFIDENCE: design."""

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

# ---- the callouts (C17, OUTSIDE face) ---------------------------------------
CALLOUT_VFD = "VARIABLE FREQUENCY DRIVE"
CALLOUT_MAINS = "MAINS"
"""The two words on the door's room face. SOURCE: task C17 ("VARIABLE
FREQUENCY DRIVE over the sealed side, MAINS at the IEC"). CONFIDENCE: spec.
Both at callouts.CALLOUT_H."""
VFD_CALLOUT_X0 = GRID
"""Door-local X of the drive word's LEFT edge: one module in from the left
end wall's face, so the word starts over the drive's own keep-out. SOURCE:
layout. CONFIDENCE: chosen, checked (left of the split)."""
VFD_CALLOUT_Y = GRID * 23
"""Door-local Y of the drive word's centre: the band above the glands' bores
(GLAND_Y + GLAND_D/2 = 312.5) and below the top edge (613), on the grid.
Nothing is cut through the outside face there. SOURCE: layout. CONFIDENCE:
chosen, checked."""
MAINS_CALLOUT_Y = GRID * 5
"""Door-local Y of MAINS' centre, over the IEC cutout (top edge at 74.75
with its clearance): the word's baseline clears it by better than a grid.
SOURCE: layout. CONFIDENCE: chosen, checked."""

# ---- the reveal -------------------------------------------------------------
WINDOW_LAND_X = GRID * 3
"""Solid door on each side of the window: from the partition's right face and
from the door's right end (the rear-right stile's edge, 2026-09-04). SOURCE:
design. CONFIDENCE: design. Big enough that the right-hand stay's foot stays
off the rabbet."""
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
plus the Universal's kerf. CONFIDENCE: chosen."""
PANE_SCREW = "5 x 12 pan head, the house screw, exposed"
PANE_SCREW_LEN = 12.0
PANE_SCREW_D = SCREW_CLEAR_D
PANE_PILOT_D = SCREW_PILOT_D
PANE_PILOT_DEPTH = PANE_SCREW_LEN - PT
"""Four screws through the pane's lip into blind pilots in the rabbet floor.
SOURCE: console_plate's reveal fixing, shortened so the pilot leaves birch
under it. CONFIDENCE: chosen."""

# ---- the interlock: switch, key, block -------------------------------------
SWITCH = "Omron D4NS-4AF, safety-door switch, tongue operated, 1NC/1NO slow-action, direct-opening NC, 1 conduit M20"
"""RULED 2026-09-04 (Jared): tongue type, positive mode, D4NS class, body
on the carcass, actuator on the door. Model: the 1NC/1NO 1-conduit switch
with the house M20 boss (D4NS-4AF; D4NS-1AF is the same switch in Pg13.5).
The coil rides the NC contact, which the key holds closed and the key's
withdrawal opens by direct action. SOURCE: ruling; model table in
SWITCH_SOURCE p.2. CONFIDENCE: ruling (type), chosen (contact/conduit)."""
SWITCH_SOURCE = "https://files.omron.eu/downloads/latest/datasheet/en/c128_d4ns_safety-door_switch_datasheet_en.pdf"
"""Omron D4NS datasheet (C128, Safety-door Switch D4NS). Every switch and key
figure below is read off its dimension drawings, p.6 (switch), p.7 (keys, and
the key inserted) and p.8 (mounting holes). CONFIDENCE: datasheet."""
SWITCH_BODY = (31.0, 96.0, 30.6)
"""W across (the head is 30.2), L head top to bottom, D proud of the
mounting face (the body below the head is 30). SOURCE: SWITCH_SOURCE p.6,
1-conduit drawing: 31 across, 41 head-top-to-screw-row plus 55 screw-row-to-
bottom, 30.6 head depth. CONFIDENCE: datasheet, the length summed off two
stacked dimensions on the drawing."""
SWITCH_SCREW_ROW = 41.0
SWITCH_SCREW_PITCH = 20.0
SWITCH_SCREW_D = 4.0
"""Two M4 mounting screws, 20 +-0.1 apart across the body, 41 below the
head's top, in 2.15R slotted holes. SOURCE: SWITCH_SOURCE p.6 and p.8.
CONFIDENCE: datasheet. Into birch they become 4mm wood screws in
SCREW_PILOT_D pilots."""
SWITCH_STUD_ROW = 47.0
SWITCH_STUD_PITCH = 22.0
SWITCH_STUD_D = 4.0
SWITCH_STUD_H = 4.8
"""Two locating studs on the back of the body, 4 -0.05/-0.15 dia, 4.8 high,
22 +-0.1 apart, 47 +-0.1 below the screw row; they go into holes in the
mounting surface. SOURCE: SWITCH_SOURCE p.8 ("secured more by the studs").
CONFIDENCE: datasheet."""
SWITCH_SLOT_DROP = 7.5
"""Key slot centre below the head's top, on the head's front face. SOURCE:
SWITCH_SOURCE p.6, the 7.5 on the head-cap view, with the tongue drawn just
under the head's top on p.7. CONFIDENCE: datasheet, read off the raster."""
SWITCH_SLOT_DEPTH = 20.0
"""How deep the reference solid's slot is cut into the head from its front
face: deeper than the tongue ever reaches, so the solid never claims volume
the tongue occupies. Modelling clearance, not a datasheet figure. CONFIDENCE:
chosen."""
KEY_FACE_BAND = (44.0, 46.5)
"""Key insertion face to the switch's mounting face, the datasheet's window
for the K1 key with the head at front-side mounting. SOURCE: SWITCH_SOURCE
p.7, "44 to 46.5 Key insertion face". CONFIDENCE: datasheet."""
SWITCH_STANDOFF = 45.0
"""Where this build puts the switch's mounting face: inside the door's inside
face by this much, in the middle of KEY_FACE_BAND. CONFIDENCE: chosen inside
the datasheet's band, checked."""
KEY_ALIGN_TOL = 1.0
KEY_R_MIN = 200.0
"""Permissible centre-line difference between key and key hole, and the
minimum insertion radius for a hinged door. SOURCE: SWITCH_SOURCE p.7.
CONFIDENCE: datasheet. The door's radius at the key is checked against
KEY_R_MIN."""

KEY = "Omron D4DS-K1, operation key, horizontal mounting"
KEY_PLATE = (30.0, 13.0, 2.0)
KEY_HOLE_PITCH = 15.0
KEY_TONGUE = (13.0, 4.3, 28.0)
"""The K1 key: an L. Plate 30 along by 13 across by 2 thick, two 2.15R
slotted holes 15 +-0.1 apart along it, screwed flat to the door's inside
face; tongue 13 wide by 4.3 thick standing 28 off the key insertion face,
perpendicular to the plate. On this door the plate's 30 runs along X and
the tongue's 4.3 is its Z thickness, which is the way the slot on the head's
front face lies with the body vertical. SOURCE: SWITCH_SOURCE p.7 (K1) and
p.8 (key mounting holes). CONFIDENCE: datasheet, read off the drawing."""
KEY_Y = GRID * 28.5
"""Door-local height of the tongue's centreline, 570: high on the sealed
side, under the door's top edge by more than the switch's head, above the
VFD standoff slab's top (z 458.7 station) by more than the switch body's
length, so nothing of the switch stands in the drive's air. SOURCE: layout
against vfd_mount.standoff_slab. CONFIDENCE: chosen, checked."""

BLOCK = "18mm birch offcut, 40 x 140, hung from the cap's underside"
BLOCK_W = GRID * 2
BLOCK_H = GRID * 7
"""The switch's seat: one thickness of birch hanging from the cap's
underside, its top edge on the cap, its rear face SWITCH_STANDOFF inside the
door, 40 wide so the 31 body sits on it with a pilot's worth of birch each
side, 140 tall so the screw row and the stud row both land on it under the
cap (head top 31.5 under the cap, studs 88 below that, half a module of birch
under them; the check holds it). Hung from
the cap rather than stood on the wall because the door's left end is a
stile's width in from the wall (2026-09-04) and the key with it. SOURCE:
design. CONFIDENCE: design, checked. NOT nested: an offcut, cut from the
sheet's waste."""
BLOCK_SCREW = "5 x 50 pan head, two, down through the cap into the block's top edge, drilled at the fit"
"""The block's own fixing runs along Z, through the cap's 18 and 32 into the
block's top edge: RULED 2026-09-04 (fix set, "interlock block screws 5x50").
An edge-drilled hole the flat pattern cannot carry. Standing note.
CONFIDENCE: ruling (length), chosen (route)."""
KEY_X = GRID * 3
"""Door-local X of the tongue's centreline: three modules in from the door's
left end, so the block hangs clear of the stile and the drive's keep-out
below it stays sealed. CONFIDENCE: chosen, checked."""

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


def x_left(d: Datums = D) -> float:
    """Station X of the door's left end: the rear-left stile's inner edge
    plus the end reveal. Every door-local X is measured from here."""
    return d.rear_opening_x[0] + END_REVEAL


def door_size(d: Datums = D) -> tuple[float, float]:
    """(width, height) of the cut blank: the rear opening between the two
    stiles' inner edges less an end reveal each side, bay height less the
    hinge clearance."""
    x0, x1 = d.rear_opening_x
    return (x1 - x0 - 2 * END_REVEAL, d.bay_h - HINGE_CLEAR)


def z_bottom(d: Datums = D) -> float:
    """Station Z of the door's bottom edge."""
    return d.deck_top + HINGE_GAP


def plane(d: Datums = D) -> Plane:
    """Door frame: local +X to station +X, local +Y up, thickness into -Y
    from the rear face at y_rear. Origin at the door's lower-left corner on
    its OUTSIDE face."""
    return Plane(
        origin=(x_left(d), d.y_rear, z_bottom(d)),
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
    return d.brain_split_x - x_left(d)


def keepout_local(d: Datums = D) -> float:
    """Door-local X where the VFD keep-out ends; nothing is cut left of it."""
    return d.vfd_keepout_x[1] - x_left(d)


def catch_positions(d: Datums = D) -> list[tuple[float, float]]:
    """Door-local centres of the two catch screws: on the partition's
    centreline, one low, one high."""
    _w, h = door_size(d)
    cx = split_local(d) + d.t / 2
    return [(cx, CATCH_Y[0]), (cx, h - CATCH_Y[0])]


def callouts_local(d: Datums = D) -> list[callouts.Callout]:
    """The two words, door-local, on the OUTSIDE (Z = 0, back) face."""
    vfd_w = callouts.text_width(CALLOUT_VFD)
    return [
        callouts.Callout(CALLOUT_VFD, (VFD_CALLOUT_X0 + vfd_w / 2, VFD_CALLOUT_Y), face="back"),
        callouts.Callout(CALLOUT_MAINS, (IEC_POS[0], MAINS_CALLOUT_Y), face="back"),
    ]


def register(d: Datums = D) -> callouts.Register:
    """The second fixture's datums: the two catch bores, through holes on the
    split's centreline, low and high."""
    (ax, ay), (bx, by) = catch_positions(d)
    return callouts.Register(
        (ax, ay, CATCH_CLEAR_D), (bx, by, CATCH_CLEAR_D), "the two catch bores"
    )


def window_local(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """((x0, x1), (y0, y1)) of the window aperture, door-local."""
    w, h = door_size(d)
    sx0, _sx1 = signal_x(d)
    # the signal zone runs to the right end wall; the door now stops at the
    # rear-right stile, so the right land is measured from the door's end
    x0 = sx0 - x_left(d) + WINDOW_LAND_X
    x1 = w - WINDOW_LAND_X
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


def key_axis(d: Datums = D) -> tuple[float, float]:
    """(station x, station z) of the tongue's centreline, which runs along
    Y from the door's inside face into the switch's head."""
    return (x_left(d) + KEY_X, z_bottom(d) + KEY_Y)


def switch_mount_y(d: Datums = D) -> float:
    """Station Y of the switch's mounting face: the block's rear face."""
    return d.y_rear - d.t - SWITCH_STANDOFF


def head_top_z(d: Datums = D) -> float:
    """Station Z of the head's top: the slot's drop above the tongue."""
    return key_axis(d)[1] + SWITCH_SLOT_DROP


def switch_axis(d: Datums = D) -> tuple[float, float]:
    """(station y of the head's front face, station z of the tongue): where
    the key enters the switch. Kept under this name for the assembly's
    report."""
    return (switch_mount_y(d) + SWITCH_BODY[2], key_axis(d)[1])


def block_extent(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """((x0, x1), (y0, y1), (z0, z1)) of the block, station coordinates:
    hanging from the cap's underside, centred on the key, one thickness
    ending at the mounting face."""
    y1 = switch_mount_y(d)
    x, _z = key_axis(d)
    z1 = d.top_z[0]
    return ((x - BLOCK_W / 2, x + BLOCK_W / 2), (y1 - d.t, y1), (z1 - BLOCK_H, z1))


def block_plane(d: Datums = D) -> Plane:
    """Block frame: local +X to station -X from the block's right edge, local
    +Y up (station +Z), local +Z into +Y so the mounting face is local Z = t,
    the CUT face in ``flat_pattern`` terms."""
    (x0, x1), (y0, _y1), (z0, _z1) = block_extent(d)
    return Plane(origin=(x1, y0, z0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))


def switch_holes_local(d: Datums = D) -> list[tuple[str, float, float, float, float]]:
    """(label, local x, local y, diameter, depth) of the four holes in the
    block's mounting face: two screw pilots on the screw row, two stud holes
    on the stud row, all blind from the mounting face."""
    (_x0, _x1), (_y0, _y1), (z0, _z1) = block_extent(d)
    cx = BLOCK_W / 2
    y_screw = head_top_z(d) - SWITCH_SCREW_ROW - z0
    y_stud = y_screw - SWITCH_STUD_ROW
    # the block's own two 5 x 50s come down from the cap into this top edge:
    # an edge hole, not a face feature, so nothing is cut here for them
    return [
        ("switch_screw_l", cx - SWITCH_SCREW_PITCH / 2, y_screw, SCREW_PILOT_D, T / 2),
        ("switch_screw_r", cx + SWITCH_SCREW_PITCH / 2, y_screw, SCREW_PILOT_D, T / 2),
        ("switch_stud_l", cx - SWITCH_STUD_PITCH / 2, y_stud, SWITCH_STUD_D, SWITCH_STUD_H + 0.2),
        ("switch_stud_r", cx + SWITCH_STUD_PITCH / 2, y_stud, SWITCH_STUD_D, SWITCH_STUD_H + 0.2),
    ]


def build_block(d: Datums = D) -> Part:
    """The block, flat in its own frame: a birch blank with the switch's four
    holes blind from the mounting face."""
    part = panel(BLOCK_W, BLOCK_H, d.t)
    for _label, x, y, dia, depth in switch_holes_local(d):
        part -= bore(x, y, dia, depth=depth, side="front")
    return part


def place_block(block: Part | None = None, d: Datums = D) -> Part:
    block = build_block(d) if block is None else block
    return block_plane(d) * block


def build_switch_env(d: Datums = D) -> Part:
    """The switch on its block, station coordinates: the body from the
    mounting face toward the door, head up, the key slot cut into the head's
    front face so the tongue sits in air the solid does not claim."""
    x, z = key_axis(d)
    y0 = switch_mount_y(d)
    z_top = head_top_z(d)
    body = Box(
        SWITCH_BODY[0], SWITCH_BODY[2], SWITCH_BODY[1],
        align=(Align.CENTER, Align.MIN, Align.MAX),
    ).moved(Location((x, y0, z_top)))
    slot = Box(
        KEY_TONGUE[0] + 2 * KEY_ALIGN_TOL, SWITCH_SLOT_DEPTH, KEY_TONGUE[1] + 2 * KEY_ALIGN_TOL,
        align=(Align.CENTER, Align.MAX, Align.CENTER),
    ).moved(Location((x, y0 + SWITCH_BODY[2], z)))
    return body - slot


def build_key_env(d: Datums = D) -> Part:
    """The K1 key on the door's inside face, station coordinates: the plate
    flat on the face, the tongue standing into the band to KEY_TONGUE[2]
    off the face."""
    x, z = key_axis(d)
    y_in = d.y_rear - d.t
    plate = Box(
        KEY_PLATE[0], KEY_PLATE[2], KEY_PLATE[1],
        align=(Align.CENTER, Align.MAX, Align.CENTER),
    ).moved(Location((x, y_in, z)))
    tongue = Box(
        KEY_TONGUE[0], KEY_TONGUE[2], KEY_TONGUE[1],
        align=(Align.CENTER, Align.MAX, Align.CENTER),
    ).moved(Location((x, y_in, z)))
    return plate + tongue


def key_pilots_local(d: Datums = D) -> list[tuple[float, float]]:
    """Door-local pilots for the key's two M4 screws, on the tongue's line."""
    return [(KEY_X - KEY_HOLE_PITCH / 2, KEY_Y), (KEY_X + KEY_HOLE_PITCH / 2, KEY_Y)]


def key_open(angle: float, d: Datums = D) -> Part:
    """The key swung with the door: rotated ``angle`` about the pin."""
    return build_key_env(d).rotate(hinge_axis(d), angle)


def key_radius(d: Datums = D) -> float:
    """The tongue's insertion radius: the pin to the tongue's centre at the
    door's inside face."""
    ax = hinge_axis(d)
    _x, z = key_axis(d)
    return hypot(d.y_rear - d.t - ax.position.Y, z - ax.position.Z)


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
    ).moved(Location((x_left(d) + lx, d.y_rear - d.t, z_bottom(d) + ly)))


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

    # -- pilots: the key (sealed, in the keep-out's X but blind) and stays
    for x, y in key_pilots_local(d):
        out.append(Cut("key_pilot", "sealed", "pilot", x, y, (SCREW_PILOT_D, SCREW_PILOT_D),
                       corner_r=SCREW_PILOT_D / 2, depth=T / 2,
                       note="blind from the inside face, M4 wood screw, the K1 key"))
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


def build(d: Datums = D, *, carve: bool = True) -> Part:
    """The door, flat in panel-local coordinates, its two words carved into
    the outside face unless ``carve`` is off (the DXF's CUT layers are read
    off the un-carved blank)."""
    w, h = door_size(d)
    part = panel(w, h, d.t)
    for c in cuts(d):
        part -= _cutter(c)
    if carve:
        part = callouts.carve(part, callouts_local(d), thickness=d.t)
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
    assembly: the door, the pane, the interlock block on the wall with the
    switch on it and the key on the door, the two folded stays."""
    out: list[tuple[str, str, Part]] = [
        (PART_NAME, "carcass", place(d=d)),
        (REVEAL_NAME, "acrylic", place_reveal(d=d)),
        (BLOCK_NAME, "offcut", place_block(d=d)),
        (SWITCH_ENV_NAME, "reference", build_switch_env(d)),
        (KEY_ENV_NAME, "reference", build_key_env(d)),
    ]
    for end in ("l", "r"):
        out.append((f"{STAY_STEM}_{end}", "reference", build_stay(end, d)))
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints for ``assembly.joints``. One housing (the pane in its
    rabbet); everything else meets on a face."""
    from stations.cnc_shapeoko.parts.brain_partition import PART_NAME as PARTITION

    y_in = d.y_rear - d.t
    out: list[tuple] = [
        (PARTITION, PART_NAME, "butt", None, 0.0, 0.0,
         "partition's rear edge lands on the door's inside face; two Torx screws through the door into it"),
        (PART_NAME, REVEAL_NAME, "housing", "y", y_in, y_in + REVEAL_DEPTH,
         "pane flush in the inside-face rabbet"),
        ("top_cap", BLOCK_NAME, "butt", None, 0.0, 0.0,
         "block's top edge on the cap's underside, two 5 x 50 down through the cap"),
        (BLOCK_NAME, SWITCH_ENV_NAME, "bearing", None, 0.0, 0.0,
         "switch body on the block's rear face, two M4 and two studs"),
        (PART_NAME, KEY_ENV_NAME, "bearing", None, 0.0, 0.0,
         "key plate flat on the door's inside face, two M4"),
        (SWITCH_ENV_NAME, KEY_ENV_NAME, "housing", "y",
         switch_axis(d)[0] - SWITCH_SLOT_DEPTH, switch_axis(d)[0],
         "the tongue in the head's slot"),
    ]
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
    # from the HEEL, one wall outside the inner face, so the toe stands
    # flange_reach into the opening (MEASURED 2026-09-04: 84.0 outside)
    w = h.flange_reach if h.flange_reach is not None else h.span_h + h.hole_d / 2
    t = s.leg_wall_t
    out: list[tuple[str, Part]] = []
    for label, x0 in (("rear left leg, Y flange", d.x_left - t), ("rear right leg, Y flange", d.x_right - w)):
        plate = Box(w + t, t, s.table_h, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
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
    ox0, ox1 = d.rear_opening_x
    if abs(w - (ox1 - ox0 - 2 * END_REVEAL)) > 0.1:
        notes.append(
            f"the door is {w:.2f} wide and the rear stiles' inner edges are "
            f"{ox1 - ox0:.2f} apart: it is not the opening less two reveals"
        )
    pb = place(d=d).bounding_box()
    if pb.min.X < ox0 + END_REVEAL - 1e-6 or pb.max.X > ox1 - END_REVEAL + 1e-6:
        notes.append(
            f"the door spans x {pb.min.X:.1f}..{pb.max.X:.1f} against the stiles' "
            f"{ox0:.1f}..{ox1:.1f}: an end reveal is wrong"
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
    if not fits((w, h), SHEET_4X8):
        notes.append(f"door blank {w:.0f} x {h:.0f} does not come out of a 4x8 Baltic sheet")

    # -- the hinge -----------------------------------------------------------
    rise = swing_rise(d)
    if rise >= TOP_REVEAL:
        notes.append(
            f"the door's top corner rises {rise:.2f}mm on the swing and the top reveal "
            f"is {TOP_REVEAL:.1f}: the door hits the cap before it opens"
        )
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
    xl = x_left(d)
    if wx0 + xl < sx0 or wx1 + xl > sx1:
        notes.append(
            f"the window runs x {wx0 + xl:.1f}..{wx1 + xl:.1f} station and the signal "
            f"zone is {sx0:.1f}..{sx1:.1f}: the reveal is not wholly over the signal side"
        )
    rw, rh = rabbet_size(d)
    if wy0 - REVEAL_LIP <= RJ45_POS[1] + RJ45_FLANGE[1] / 2:
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
    # closed: the switch's mounting face inside the datasheet's band off the
    # key face, the tongue inside the head, the key and the slot on one line
    y_front, z_axis = switch_axis(d)
    y_in = d.y_rear - d.t
    reach = KEY_TONGUE[2] - (y_in - y_front)
    if not (KEY_FACE_BAND[0] - 1e-6 <= SWITCH_STANDOFF <= KEY_FACE_BAND[1] + 1e-6):
        notes.append(
            f"the switch's mounting face is {SWITCH_STANDOFF:.1f} off the key face; the "
            f"datasheet wants {KEY_FACE_BAND[0]:.1f} to {KEY_FACE_BAND[1]:.1f}"
        )
    if reach <= 0:
        notes.append(f"the tongue stops {-reach:.1f}mm short of the head: the key never enters the switch")
    if reach >= SWITCH_SLOT_DEPTH:
        notes.append("the tongue reaches deeper than the reference solid's slot: the model claims it as overlap")
    if key_radius(d) < KEY_R_MIN:
        notes.append(
            f"the key swings on a {key_radius(d):.0f}mm radius; the datasheet wants "
            f"{KEY_R_MIN:.0f} or more for a hinged door"
        )
    # the block's top edge has to land on solid cap, not on the exhaust field
    # or the mast pad, and the block has to stay clear of the stile
    from stations.cnc_shapeoko.parts.top_cap import build as build_cap
    cap = d.top_plane * build_cap(d)
    (bx0, bx1), (by0, by1), (bz0, bz1) = block_extent(d)
    probe = Box(bx1 - bx0, by1 - by0, 1.0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((bx0, by0, bz1))
    )
    try:
        solid = (cap & probe).volume
    except Exception:
        solid = 0.0
    footprint = (bx1 - bx0) * (by1 - by0)
    if solid < footprint - 1.0:
        notes.append(
            f"the interlock block hangs on {solid / footprint:.0%} cap at x {bx0:.0f}..{bx1:.0f} "
            f"y {by0:.0f}..{by1:.0f}: a cut in the cap is over it"
        )
    if abs(bz1 - d.top_z[0]) > 1e-6:
        notes.append(f"the interlock block's top at z {bz1:.1f} is not on the cap's underside")
    for lab, (sx0, sx1), (sy0, sy1) in d.stiles:
        if bx0 < sx1 and bx1 > sx0 and by0 < sy1 and by1 > sy0:
            notes.append(f"the interlock block stands in {lab}")
    for label, x, y, dia, depth in switch_holes_local(d):
        if x - dia / 2 < 0 or x + dia / 2 > BLOCK_W or y - dia / 2 < 0 or y + dia / 2 > BLOCK_H:
            notes.append(f"{label} runs off the {BLOCK_W:.0f} x {BLOCK_H:.0f} block")
        if depth > T - POCKET_FLOOR_MIN:
            notes.append(f"{label} is {depth:.1f} deep in the block's {T:.0f}")
    # open: the key swung with the door clears the switch and its block once
    # the tongue is out, and the door itself clears them at every angle
    switch_env = build_switch_env(d)
    block = place_block(d=d)
    for angle in (-5.0, -10.0, -30.0, -60.0, OPEN_ANGLE):
        key = key_open(angle, d)
        door_at = place(d=d).rotate(hinge_axis(d), angle)
        for what, moving in (("key", key), ("door", door_at)):
            for name, fixed in ((SWITCH_ENV_NAME, switch_env), (BLOCK_NAME, block)):
                try:
                    shared = (moving & fixed).volume
                except Exception:
                    shared = 0.0
                if shared > 1.0:
                    notes.append(
                        f"the {what} at {-angle:.0f} degrees open shares {shared / 1000:.1f} cm3 "
                        f"with {name}: the door does not open past the interlock"
                    )
    notes.append(
        f"INTERLOCK, standing note. RULED 2026-09-04: tongue type, positive mode. {SWITCH} "
        f"on a {BLOCK} whose rear face is {SWITCH_STANDOFF:.1f} inside the door (datasheet "
        f"{KEY_FACE_BAND[0]:.1f} to {KEY_FACE_BAND[1]:.1f}); {KEY} on the door at door "
        f"({KEY_X:.0f}, {KEY_Y:.0f}), tongue {reach:.1f} into the head closed, insertion radius "
        f"{key_radius(d):.0f}. The coil rides the direct-opening NC contact, closed while the "
        "key is in. The key stands 28 proud of the door's inside face at its left end, and "
        "of the open shelf. The block is NOT nested: a 40 x 140 offcut hung from the cap, "
        f"fixed with two {BLOCK_SCREW}. The M20 conduit exits the body's bottom, downward. Expected, and "
        "worth knowing before the key is fitted: its slotted holes are the +-1 alignment."
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
    if ob.min.X < d.rear_opening_x[0] - 1e-6 or ob.max.X > d.rear_opening_x[1] + 1e-6:
        notes.append("the open door reaches past a rear stile's inner edge")
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
        f"GLANDS, standing note. Both glands are M{GLAND_D:.0f} by the C07 spec (I91, D01) "
        "where the BOM line reads 20mm; the spec wins and the BOM line follows. The "
        "harness gland sits on the SEALED side by the same spec while the motion "
        "controller is on the signal side, so the harness crosses the partition at "
        "the transit with the CT lead. Expected, and worth knowing before the "
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

    # -- the callouts: on birch, on the sealed side, and the door goes back on
    # its two catch bores
    notes += callouts.check_callouts(
        build(d),
        callouts_local(d),
        register(d),
        size=(w, h),
        thickness=d.t,
        label=PART_NAME,
    )
    for c in callouts_local(d):
        bb = callouts.sketch(c).bounding_box()
        if bb.max.X > sp:
            notes.append(
                f"{c.text} reaches door x {bb.max.X:.1f} and the split is at {sp:.1f}: "
                "it is not over the sealed side"
            )
    return notes


# ====================================================================
# EXPORT
# ====================================================================


def export(d: Datums = D) -> list:
    """STEP + DXF for the door (birch: CUT and the pocket layers off the
    un-carved blank, first fixture), a second DXF for the outside-face carve
    (the flipped outline, VCARVE and REGISTER, one frame), the pane on an
    ACRYLIC layer for the Universal, and STEP alone for the reference and
    wear solids."""
    written = []
    door_layers = flat_pattern(build(d, carve=False))
    written += export_part(build(d), PART_NAME, layers=door_layers)
    written += export_part(
        build(d),
        CARVE_NAME,
        step=False,
        layers=callouts.carve_drawing(
            callouts_local(d), register(d), width=door_size(d)[0], cut=door_layers["CUT"]
        ),
    )
    pane = build_reveal(d)
    written += export_part(pane, REVEAL_NAME, layers={"ACRYLIC": flat_pattern(pane)["CUT"]})
    # the block's flat: DXF only here, its placed STEP comes with the rest
    written += export_part(build_block(d), BLOCK_NAME, step=False)
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
    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {d.t:.0f} (between the rear stiles less "
          f"2 x END_REVEAL {END_REVEAL:.0f}; bay {d.bay_h:.0f} less "
          f"HINGE_CLEAR {HINGE_CLEAR:.0f} = gap {HINGE_GAP:.0f} + reveal {TOP_REVEAL:.0f})")
    print(f"  closed   x {pb.min.X:.1f}..{pb.max.X:.1f}  y {pb.min.Y:.1f}..{pb.max.Y:.1f}  "
          f"z {pb.min.Z:.1f}..{pb.max.Z:.1f}   volume {flat.volume / 1000:.1f} cm3")
    print(f"  hinge    axis y {ax.position.Y:.2f} z {ax.position.Z:.2f}, swing rise {swing_rise(d):.2f}")
    print(f"  open     x {ob.min.X:.1f}..{ob.max.X:.1f}  y {ob.min.Y:.1f}..{ob.max.Y:.1f}  "
          f"z {ob.min.Z:.1f}..{ob.max.Z:.1f}")
    print(f"  split at door x {split_local(d):.1f}; keep-out ends at {keepout_local(d):.1f}")
    for line in callouts.describe(callouts_local(d), register(d)):
        print(f"  {line}")
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
