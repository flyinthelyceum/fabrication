"""Console plate: the instrument panel inset in the right end wall, and the
chase behind it that the hands-bay drawers give up to make room for it.

Ruling 2026-09-03 (console_location): the console is an INSET PLATE in the
RIGHT END WALL, front region, at hand height. Not on the leg, not above the
drawers. Every run stays inside the carcass; the leg pattern stays free for the
arm; the E-stop sits on a fixed face at the operator's front-right corner.

Ruling 2026-09-03 (console_drawer_overlap): the device depth behind the plate
comes out of the OVERLAPPED DRAWERS' WIDTH. The plate does not move rearward;
every drawer whose Z band crosses the console band is narrowed, its right-hand
slide moves inboard with it. Ruling 2026-09-04 (fix set): ALL THREE drawers
are narrowed, "D3 narrowed to 259 on the console cheek extended to the deck",
so the cheek runs deck to cap, every right-hand slide is on it, and the three
inset fronts read as one column. ``CHEEK_TO_DECK`` carries it and
``narrowed_openings`` returns every opening.

Ruling 2026-09-04 (Kerf): the front-right STILE stands inside the chase's
front corner (``parts/stiles.py``), so the clear acrylic reveal over the
chase runs from the cheek's front edge to the stile's inner edge, and the
floor rib is notched around the stile's foot.

Ruling 2026-09-09 (console_material): the plate is NOT birch. It is 3mm 304
stainless, #4 brushed (``PLATE_T``, ``params.CONSOLE_PLATE``), waterjet cut in
the Innovation Commons, its legends Enduramark black on the Universal laser.
Jared: "The sheet shouldn't be birch. that makes no sense. We should spec a
metal plate that we can waterjet/lasercut and enduramark etch the markings
on." The 12mm plate was inherited from the carcass and fought every
panel-mount device on it: the XB4s take 1-6, the PL183 2-10, the HDMI D-type
that was tried on 09-09 takes 2. At 3mm every device is inside its range, the
instrument recesses and their acrylic panes vanish (everything flush-mounts,
the meter bezels stand proud), and the plate sits in a 3mm relief over the
wall's aperture instead of a rabbeted tongue-and-lip. Same day: a second
meter, SPEED beside LOAD, and the pendant port is USB-C, not GX16.

Ruling 2026-09-09 (console_subtract, Jared, calipers on the Carbide boxes):
the Carbide power pendant is NOT set into the plate as a box. Its E-stop and
feed-hold holes both read 0.865in (21.97mm), the 22mm standard, so the two
buttons come OUT of the box and go through this plate as two 22mm devices on
their own leads back to the Carbide controller; the box's ALLOCATED envelope
and its reference solid are gone. The VFD box's spindle button reads 0.743in
(18.87mm), a 19mm anti-vandal, so SPINDLE is that button, on hand, not a
Schneider 22. The state display is struck ("carbide motion logs all of it"),
the ToF sensor is struck, the two USB-C ports stay as thumb-drive ports to
the PC.

Ruling 2026-09-09 (console_composition, Jared): "the panel reads like a random
in-fill of buttons and plugs. we need to be better at nesting in symmetrical
and thoughtfully categorical ways." The plate is COMPOSED, not packed: five
groups, one axis, and the pitch rules only check what the composition placed
(``feedback_panel_layout_is_composition_not_packing``). Composition #3 of the
three drawn to scale that day, with the key moved into the lower half:

    group        devices                        zone
    READ         SPEED, LOAD                    top: a centred pair on the axis
    ARM          the key, alone                 lower half, on the axis
    MACHINE      E_STOP, FEED_HOLD, SPINDLE     working row, operator's corner
    EXTRACTION   EXTR_LAMP, DUST, BAG_LAMP      working row, far end; mirrors
                                                MACHINE across the axis
    PORTS        PENDANT, USB_1, USB_2          bottom edge, under MACHINE, the
                                                pendant under the E-stop

The plate grew to 400 x 200 for it (``CONSOLE_Z0`` GRID*24 -> GRID*20): two
real 3.5in dials want ~92mm of field on their own and could not share 120
with a switch row and a port row. Same day: the two lamps are JEWEL pilot
lights (Dialco class, 120 V neon), the bag lamp and a new EXTRACTOR lamp in
parallel with the CT 15's trigger load; the Schneider XB4BVB5 is superseded.


WHAT THIS PART OWNS
===================

  * CONSOLE_BAND: the region of the right end wall the console may occupy
  * the plate: 3mm stainless (``PLATE_T``), set FLUSH with the wall's outer
    face in a relief over a through-aperture; every device cutout and the
    two meters' stud holes
  * the cutter the right end wall subtracts to receive the plate
    (``wall_cutter``), so the aperture and the plate are one set of numbers
  * the CHASE behind the plate: the air the devices need (``CHASE``), the
    birch that walls it off from the drawers (a cheek, a floor rib) and the
    clear acrylic reveal that closes its front
  * the keep-out the drawers are checked against, as a reference solid
  * ``narrowed_openings`` / ``DRAWER_GIVE``: what the drawers lose
  * the E-stop's callout (C17), Enduramark-marked under the mushroom guard
    at ``estop_callout_anchor``, sized by ``estop_callout_band`` to the steel
    between the guard and the pendant port's flange; the one word on the red
    budget's device, itself black on brushed steel like every other. It goes
    out on the ``MARK`` layer, and the cut plate goes on the laser bed on its
    two short-edge screw holes (``REGISTER``).

It does NOT own the drawers (``drawers`` narrows itself by reading this file),
the wall (``bay_walls`` subtracts ``wall_cutter``) or the spine's crossings
(``spine_panel``; this file only checks that the chase meets them).


THE PLATE IS A FLUSH INSET, SCREWED FROM OUTSIDE
================================================

The wall gets a through-aperture ``LIP`` inside the plate's outline, for the
device bodies, and on its OUTER face a relief ``PLATE_T`` deep the size of the
plate's outline. The plate is a flat 3mm sheet: it lies in the relief, outer
faces flush, and the ``LIP`` margin of wall behind its edge is the land its
ten countersunk screws go into, from the outside, one head type, flush. The
plate comes off the station without touching a drawer, and the harness comes
out with it on its service loop. (Until 2026-09-09 the plate was 12mm birch
with a tongue in the aperture and a lip in a rabbet; the relief is what is
left of that.)

Both wall cuts are JOINERY -- a square member seats in them -- so both stay
square and get dogbone reliefs, per the rule in ``through_slot``'s docstring.
The aperture's four reliefs are through and sit under the plate, invisible.
The relief's four are blind, ``PLATE_T`` deep, and SHOW as a crescent at each
corner of the plate on the outer face. A matched ``ROUTER_R`` radius on the
plate's corners would hide them, and the waterjet cuts any radius for free;
that trades the rule for a look, and the rule stands until Jared says
otherwise. It is flagged in ``check_console_plate`` as a standing note so the
crescents are never a surprise on the day.


DEVICES, DEPTHS, AND WHERE THE CHASE'S WIDTH COMES FROM
=======================================================

Every device is a row in ``DEVICES`` with a model number, the cutout it wants,
what it occupies in front of and behind the plate, and where each number came
from. ``CHASE`` is the deepest datasheet depth behind the plate plus
``CHASE_MARGIN``. Today that is the key switch: Schneider quotes the XB4's
Depth as the whole product, head included, and the sheet does not split front
from back, so the whole figure is taken as behind-plate. Conservative by the
head's projection, and it drives the chase honestly rather than by a guess.

The three Carbide buttons (E-stop, feed hold, spindle) are ON HAND, pulled
from the Shapeoko 5 Pro power pendant and the VFD box. Their HOLES are
measured (2026-09-09, Jared, calipers); the buttons' bodies behind the plate,
their flanges and the panel range they clamp are not, so those rows carry
XB4-class figures marked assumption and the check reports MEASURE THIS. None
of them drives ``CHASE``: the key switch does.

Nothing is recessed (2026-09-09). The two dials mount the way a panel meter
does: body through a bore, bezel on the face, studs through the plate, and
the studs are drilled from the movement once the pair is in hand (the plate
cuts the two bores only). There are no pockets, no panes and no windows; a
3mm plate has no depth to pocket, and nothing reads through it since the
state display was struck.

22mm-standard devices get a 22.3mm bore, which is Schneider's own "Ø 22.3 mm
0/+0.4" figure and the lower edge of the band every 22mm maker quotes.


THE CHASE, AND WHAT THE DRAWERS GIVE UP
=======================================

Behind the plate, between the right end wall's inner face and the drawers, is
``CHASE`` of air. The drawers cannot see air, so a CHEEK -- an 18mm birch
panel standing at ``CHASE`` off the wall, the bay's full depth, from the lowest
narrowed opening's floor to the cap's underside -- walls it off and carries the
narrowed drawers' right-hand slides on its bay face. A floor RIB, 18mm birch
on edge across the chase at the cheek's bottom, ties the cheek to the wall:
screwed through the wall from outside on the band the console itself keeps
clear, and through the cheek into the rib's edge. The cheek's top edge is tied
down through the cap the way the spine's is; its rear edge butts the spine.
The chase's front is closed by a clear acrylic REVEAL (transpa.rent: the
console's back is the honest internals the design language wants shown).

So every narrowed drawer loses ``DRAWER_GIVE = CONSOLE_KEEPOUT + T``: the air
and the cheek that bounds it. The slide's own side clearance is unchanged; it moves
inboard with the box.

The console's runs reach the chase through the spine's crossings. Those that
emerge inside the chase's X band land in it directly; those that emerge in the
drawer zone come along the spine's front face and enter through ONE capsule
pass in the cheek at the crossings' row, near the spine. ``check_console_plate``
says which crossing does which.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from build123d import (
    Align,
    Box,
    Circle,
    ColorIndex,
    Face,
    Location,
    Part,
    Plane,
    Unit,
    export_step,
)

from lib import house
from lib.house import GRID, PANEL_T
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_FIT,
    DATUMS,
    EXPORT_DIR,
    ROUTER_D,
    SCREW_CLEAR_D,
    SCREW_D,
    SCREW_EDGE_OFF,
    SCREW_END_INSET,
    SCREW_PILOT_D,
    SCREW_PITCH,
    T,
    Datums,
    bore,
    export_part,
    flat_pattern,
    panel,
    relief,
    screw_positions,
    snap_dn,
    through_slot,
)
from stations.cnc_shapeoko import params
from stations.cnc_shapeoko.parts import callouts
from stations.cnc_shapeoko.parts.leg_joint import END_WALL_T

__all__ = [
    "PART_NAME",
    "CHEEK_NAME",
    "RIB_NAME",
    "REVEAL_NAME",
    "KEEPOUT_NAME",
    "CONSOLE_Y",
    "CHASE",
    "CHASE_MARGIN",
    "CONSOLE_KEEPOUT",
    "DRAWER_GIVE",
    "BAND_LAND",
    "gusset_land",
    "Device",
    "DEVICES",
    "console_z",
    "band_bound",
    "console_band",
    "plate_size",
    "narrowed_openings",
    "PLATE_T",
    "aperture_size",
    "build_plate",
    "wall_cutter",
    "build_cheek",
    "build_rib",
    "build_reveal",
    "build_keepout",
    "panes",
    "placed_all",
    "joint_table",
    "estop_callout_anchor",
    "CALLOUT_ESTOP",
    "estop_callout_band",
    "callouts_local",
    "register",
    "leg_bolt_clearance",
    "check_console_plate",
    "export",
]

PART_NAME = "console_plate"
CHEEK_NAME = "console_cheek"
RIB_NAME = "console_rib"
REVEAL_NAME = "console_reveal"
KEEPOUT_NAME = "console_keepout"
MARK_LAYER = "MARK"

D: Datums = DATUMS
PT = PANEL_T


# ====================================================================
# PARAMETERS. Every number below carries a SOURCE and a CONFIDENCE; nothing
# is a literal in the geometry. Datasheet values are read off the page the
# SOURCE names. "chosen" is a model number or a layout decision of this
# file's, under Jared's 2026-09-03 ruling that the 22mm set, the meter and
# the display are Claude-chosen with URLs. "allocation" is room reserved for
# a part whose envelope nobody publishes, and it never drives a dimension.
# ====================================================================

# -- the band ------------------------------------------------------------
CONSOLE_Y: tuple[float, float] = (GRID * 5, GRID * 25)
"""Station Y span of the console band on the right end wall: 100..500.
SOURCE: task C12 (Ruling console_location). CONFIDENCE: ruling. Starts clear
of the front leg's bolt columns (y 22.9 and 63.0) by more than ``LEG_LAND``."""

CONSOLE_Z0 = GRID * 20
"""Bottom of the band, STATION Z (400 off the floor, 328 above the deck). The
top is derived: see ``console_z``, and it is the gusset that sets it (z ~600),
so the plate is 200 tall.
SOURCE: task C12 put it at GRID*24 (480, a 120 plate). RULED 2026-09-09
(console_composition): GRID*20, because two 3.5in dials plus a switch row plus
a port row do not compose in 120 and the top cannot rise (the gusset). Read as
station Z. The leg insert rows at z 400.05 / 440.18 sit at y 56.9, forward of
the band's front edge at ``CONSOLE_Y[0]`` = 100, so the band's bottom at 400 is
not near them: ``leg_bolt_clearance`` measures it. CONFIDENCE: ruling."""

CAP_TIE_SCREW_LEN = 50.0
"""Length of the top cap's tie screws into the walls' top edges. The cap's file
names the screw (SCREW_D, 5mm Confirmat / M5) and not its length; 5 x 50 is
the stock Confirmat length for 18mm into an edge. CONFIDENCE: chosen."""

CAP_TIE_REACH = CAP_TIE_SCREW_LEN - (T - DADO_D) - DADO_D
"""How far below the cap's underside a tie screw's tip reaches: the screw
less the cap above its housing floor, less the wall's tongue in the housing.
Derived; 32mm at the house numbers."""

TOP_SCREW_LINE = CAP_TIE_REACH + SCREW_EDGE_OFF
"""What the top of the band stays below the cap's underside by: the tie screw's
reach plus the fastener edge distance. Derived; 41mm."""

BAND_LAND = GRID
"""What the top of the band stays below the MACHINE's ceiling by, where the
machine is lower than the cap's tie line. The front-right Y gusset plate sits
``plate_t`` deep in the wall's outer face (the wall is relieved to it) and its
underside tapers down toward the leg: at the band's ruled front edge (y 100)
it is at z 620, under the cap-tie line's 657. The spec's formula for the band
top cannot be met there; the machine is not a choice. One grid module of wall
between the rabbet's top edge and the steel keeps the rabbet's wall whole and
its corner reliefs closed (``gusset_land`` measures what is actually left).
SOURCE: the machine (params.Station.clear_z); the land is this file's.
CONFIDENCE: chosen. RULING WANTED: T or GRID; the other reading of the spec
(start CONSOLE_Y later along the taper) moves a ruled number."""

LEG_LAND = T
"""Birch kept between any console cut or keep-out and a leg-bolt axis.
SOURCE: task C12 "18mm of land". CONFIDENCE: ruling."""

# -- the plate and its inset --------------------------------------------
PLATE_T: float = params.CONSOLE_PLATE["t"]
"""Thickness of the plate: 3mm 304 stainless, ``params.CONSOLE_PLATE``. RULED
2026-09-09. Deliberately not ``T``: the carcass is 12mm birch and the plate is
not the carcass. CONFIDENCE: ruling."""

PLATE_MATERIAL: str = params.CONSOLE_PLATE["material"]

LIP = T
"""Width of the plate's margin: the ring of wall behind the plate's edge that
the aperture stops short of and the screws land in. One carcass thickness, so
a screw on its centreline is ``SCREW_EDGE_OFF`` from the plate's edge. Derived."""

RELIEF_T = PLATE_T
"""Depth of the wall's outer-face relief the plate lies in: the plate's own
thickness, so the outer faces are flush. Derived."""

PLATE_SCREW_D = 4.0
PLATE_SCREW_LEN = 10.0
PLATE_SCREW = params.CONSOLE_PLATE["screw"]
"""4 x 10 flat head, countersunk into the 3mm plate, into the wall's ``LIP``
margin: 3 in the plate, 7 in a 12mm wall, 5mm short of the inner face. The
house 5mm Confirmat is a pan head and stands proud of a 3mm plate, so the
plate carries its own screw. CONFIDENCE: chosen."""

PLATE_SCREW_CLEAR_D = 4.5
PLATE_SCREW_PILOT_D = 2.5
PLATE_SCREW_PILOT = PLATE_SCREW_LEN - PLATE_T
"""Depth of the pilot in the wall's margin, under the relief. Derived; 7mm."""

# -- devices ------------------------------------------------------------
BORE_22 = 22.3
"""Bore for every 22mm-standard device. SOURCE: Schneider XB4 product data
sheets, mounting note (4): "Ø 22.5 mm recommended (Ø 22.3 mm 0/+0.4)". The
task asks for 22.3 and the sheet allows it. CONFIDENCE: datasheet."""

PITCH_22_MIN = 40.0
"""Minimum centre spacing between 22mm devices. SOURCE: the same sheets, note
(2): "40 mm min." CONFIDENCE: datasheet."""

DEVICE_CLEAR = 1.0
"""Air around an instrument's body in its bore, and around a display's active
area in its window, per side. CONFIDENCE: chosen."""

XB4_PANEL_T: tuple[float, float] = (1.0, 6.0)
"""Panel thickness a Harmony XB4 22mm device clamps. SOURCE: the XB4 product
data sheets, "panel thickness 1...6 mm". CONFIDENCE: datasheet."""

CHASE_MARGIN = GRID / 2
"""Air behind the deepest device before the cheek. SOURCE: task C12 "plus
10mm". CONFIDENCE: ruling."""

CHEEK_TO_DECK = True
"""The cheek stands on the deck and every drawer is narrowed onto it. RULED
2026-09-04 (Jared, fix set): "D3 narrowed to 259 on the console cheek
extended to the deck". False restores the C12 reading: the cheek from the
lowest opening that crosses the band. CONFIDENCE: ruling."""

# -- the composition ------------------------------------------------------
# RULED 2026-09-09 (Jared). The groups and the axis ARE the design; every
# pitch rule below only checks it. Plate-local frame: X from the plate's FRONT
# edge (the operator's corner is x = 0; station +Y), Y up from the bottom edge.
# Composition #3 of three drawn to scale, ARM moved to (200, 50) by Jared.

AXIS_X = 200.0
"""The plate's axis of symmetry, plate-local: half of the band's 400. The two
dials and the key sit on it; MACHINE and EXTRACTION mirror across it, triplet
centre to triplet centre. CONFIDENCE: ruling."""

ROW_Y = 78.0
"""Plate-local Y of the WORKING ROW: the MACHINE triplet at the operator's
corner and the EXTRACTION triplet at the far end. An XB4 body (47 tall,
centred) spans 54.5..101.5 behind the plate; the dials' bodies start at 108.
CONFIDENCE: ruling (composition #3), checked."""

MACHINE_X: tuple[float, float, float] = (44.0, 84.0, 124.0)
"""Plate-local X of E_STOP, FEED_HOLD, SPINDLE on the working row, at
``PITCH_22_MIN`` exactly. STOP is the corner you slap without looking, HOLD
the button used every job, then the spindle: the machine's three buttons as
one block. Centre 84 = ``AXIS_X`` - 116. CONFIDENCE: ruling, checked."""

EXTRACTION_X: tuple[float, float, float] = (284.0, 316.0, 348.0)
"""Plate-local X of EXTR_LAMP, DUST, BAG_LAMP on the working row: the selector
with a jewel each side at ``JEWEL_22_PITCH_MIN``. Centre 316 = ``AXIS_X`` + 116,
the mirror of MACHINE. CONFIDENCE: ruling, checked."""

METER_X: tuple[float, float] = (130.0, 270.0)
METER_Y = 146.0
"""Plate-local centres of the two dials, SPEED left and LOAD right, 70 either
side of the axis: the cause you set, then the effect you read. 89 bezels at 140
pitch leave 51 of steel between them. CONFIDENCE: ruling, checked."""

ARM_XY: tuple[float, float] = (200.0, 50.0)
"""Plate-local centre of the key switch, ALONE, on the axis, centred in the
lower half: the one keyed act (arming the station) is not on the row a hand
sweeps. Jared 2026-09-09: "move the ARM switch down to about (200, 50) so it
is centered in the lower half". Nothing within 40 of it. CONFIDENCE: ruling."""

PORTS_X: tuple[float, float, float] = (44.0, 75.0, 106.0)
PORTS_Y = 30.0
"""Plate-local centres of PENDANT, USB_1, USB_2: one row of three D-types on
the bottom edge under MACHINE, the pendant under the E-stop (same X), at 31
pitch (PL183 flange 26, 5 between). Composition #3 drew the row at y 34; it is
at 30 so the E-stop's word has 12.5 of steel between the port's flange and
the guard instead of 8.5 (``estop_callout_band``): 4mm lower buys a legible
word and costs nothing, the flange's foot sits 2.5 above the margin.
CONFIDENCE: ruling (the row), chosen (the 4mm)."""

CALLOUT_ESTOP = "EMERGENCY STOP"
"""The word under the mushroom guard, marked (C17). SOURCE: task C17, the
one callout on the E-stop; it names the device and is black on brushed steel
like every other word, never red. CONFIDENCE: spec. Its height is derived from
``estop_callout_band``, the steel between the guard and the pendant's
flange, by ``callouts.fit_height``; the station's CALLOUT_H does not fit."""

# -- composition rules: what the check holds between groups ---------------
JEWEL_22_PITCH_MIN = 32.0
"""Centre spacing between a jewel lamp and a 22mm device. No maker rule (a
jewel's bezel is ~20); the composition set 32, which leaves a 9mm web between
a 16 bore and a 22.3 bore. CONFIDENCE: chosen, this file's rule."""

FLANGE_TO_BEZEL_MIN = 8.0
"""Least steel on the face between any device's flange and a dial's bezel. The
composition has 8.5 twice (FEED_HOLD under SPEED, DUST under LOAD); the
composer's 10 was measured on the key, which has since moved down. Two proud
rings 8mm apart read as two rings. CONFIDENCE: chosen, this file's rule."""

# -- the dials --------------------------------------------------------------
METER_BEZEL_D = 89.0
METER_BORE = 76.0
METER_BEHIND: tuple[float, float, float] = (76.0, 76.0, 60.0)
METER_STUDS: tuple[tuple[float, float], ...] = ()
METER_STUD_D = 0.0
METER_FRONT: tuple[float, float] = (METER_BEZEL_D, METER_BEZEL_D)
"""The dial footprint the plate is composed around and cut for: a 3.5in
round movement, Weston 301 class (``params.METER_MOVEMENT``). Bezel 89 on the
face, body through a 76 bore, ~60 behind. NONE of it is a datasheet: the pair
is a hunt, and 3.5in meters vary by maker in bore and stud pattern. The bezel
and bore are the composition's target (a 3.5in case, a 3in body); the studs
are NOT cut until the pair is in hand (``METER_STUDS`` empty, MEASURE), so the
waterjet file carries two clean bores and the stud holes are a drill-press
step from the movement itself. CONFIDENCE: assumption, MEASURE the pair."""

METER_85C1 = {
    "front": (64.0, 56.0), "bore": 48.5 + 2 * DEVICE_CLEAR,
    "behind": (48.5, 48.5, 50.0), "studs": ((-26.25, -15.0), (26.25, -15.0)),
    "stud_d": 3.4,
}
"""The 85C1 footprint (Delixi drawing, ``params.METER_MOVEMENT['fallback']``)
the plate was cut for until 2026-09-09: documented FALLBACK, not the default.
If the hunt fails, the two ``METER_*`` above take these five numbers."""

# -- the jewels -------------------------------------------------------------
JEWEL_BORE = 16.0
JEWEL_FLANGE = 20.0
JEWEL_BEHIND: tuple[float, float, float] = (20.0, 20.0, 40.0)
JEWEL_PANEL_T: tuple[float, float] = (1.0, 6.0)
"""A faceted-jewel pilot light, Dialco/Dialight class, 120 V neon
(``params.JEWEL_LAMP``): 5/8in mounting hole (16), ~20 bezel, ~40 behind with
its leads, clamps a thin panel. A HUNT, so every number is the family's, not a
part's. CONFIDENCE: assumption, MEASURE the lamps when they land."""

CARBIDE_HOLE_22 = 21.97
CARBIDE_HOLE_19 = 18.87
"""What the Carbide boxes' button holes read. MEASURED 2026-09-09 (Jared,
calipers): E-stop and feed hold 0.865in, the VFD box's spindle button 0.743in.
The plate cuts the STANDARD cutouts those sizes name (``BORE_22``,
``BORE_19``), not the readings; the readings are why the buttons are 22 and
19 and nothing else. CONFIDENCE: measured."""

BORE_19 = 19.0
"""19mm anti-vandal cutout, nominal. The makers quote 19.0-19.2; the button
on hand has not been read for its thread OD, so the nominal stands.
MEASURE THIS with the button. CONFIDENCE: assumption."""

ESTOP_BEHIND = 60.0
FEED_HOLD_BEHIND = 57.0
SPINDLE_BEHIND = 39.37
"""Depth behind the plate of the three Carbide buttons. The spindle button is
MEASURED 2026-09-09 (Jared, calipers): 1.55in behind its flange. The other
two are NOT: the E-stop carries the brief's "~60mm behind panel", the feed
hold an XB4 momentary's 57; MEASURE THIS with those two in hand. All under
the key switch's 86, so none drives the chase. CONFIDENCE: measured (spindle),
assumption (E-stop, feed hold)."""

AV19_FLANGE = 21.82
AV19_BODY: tuple[float, float] = (AV19_FLANGE, AV19_FLANGE)
AV19_PANEL_T: tuple[float, float] = (1.0, 10.0)
"""The spindle button's flange is MEASURED 2026-09-09 (Jared, calipers):
0.859in over the flange. Its body behind the plate is taken as no wider than
the flange (a 19mm anti-vandal's body is its thread, under the flange), and
the panel range is the makers' 1-10mm; both assumption. CONFIDENCE: measured
(flange), assumption (body, panel_t)."""

XB4_BODY: tuple[float, float] = (30.0, 47.0)
"""(W, H) of a Harmony XB4 complete unit behind the plate, taken as centred on
its bore. SOURCE: every XB4 product data sheet below, Width 30 mm, Height 47
mm. Which way the 47 hangs off the head is not on the sheet; centred is the
reading, and the clash check has a millimetre in hand on it. CONFIDENCE: datasheet
for the figures, assumption for the centring."""

GX16_BEHIND = 15.6
"""GX16 panel socket, overall length. SOURCE: Handson Technology GX16 datasheet
https://www.handsontec.com/dataspecs/connector/GX16.pdf mechanical drawing:
socket 15.6 overall, M16x1 thread 8.6 long, flange Ø19, S19 nut. The mating
plug goes in from OUTSIDE, so behind-plate is the socket plus solder tails.
CONFIDENCE: datasheet."""

@dataclass(frozen=True)
class Device:
    """One console element and everything the plate has to cut for it.

    ``cx``/``cy`` are plate-local, X along station +Y from the plate's front
    edge, Y up from its bottom edge. Every size is mm.

    kind      bore      a round through hole, ``bore_d``
              d_type    a round hole plus two diagonal screw holes (Neutrik D)
    studs     (dx, dy) of through holes ``stud_d`` for a stud-mounted bezel
    front     (W, H) the device occupies ON the outer face: bezel or flange
    behind    (W, H, depth) the device occupies behind the plate's inner face,
              centred on (cx, cy); depth measured from the inner face
    panel_t   (min, max) panel thickness the device clamps; the plate has to
              be inside it (``check_console_plate``)
    red       True for the one device that spends the red budget
    family    "22" (22mm standard), "19" (anti-vandal), "jewel", "meter",
              "d_type": which pitch rule applies between two devices
    group     READ / ARM / MACHINE / EXTRACTION / PORTS: the composition
    """

    label: str
    model: str
    kind: str
    cx: float
    cy: float
    source: str
    confidence: str
    bore_d: float = 0.0
    studs: tuple[tuple[float, float], ...] = ()      # (dx, dy) + stud bore d
    stud_d: float = 0.0
    d_holes: tuple[tuple[float, float], ...] = ()    # D-type screw holes (dx, dy)
    d_hole_d: float = 0.0
    front: tuple[float, float] = (0.0, 0.0)
    behind: tuple[float, float, float] = (0.0, 0.0, 0.0)
    panel_t: tuple[float, float] = (0.0, 99.0)
    red: bool = False
    family: str = ""
    group: str = ""


_SE = "https://www.se.com/us/en/product/{}/ -- product data sheet PDF: "

DEVICES: tuple[Device, ...] = (
    # READ: the pair, on the axis
    Device(
        "SPEED", "moving-coil panel meter, spindle RPM, 0-24k scale card, VFD "
        "FM1 frequency out (params.METER_MOVEMENT; Weston 301 class target)",
        "bore", METER_X[0], METER_Y,
        "RULED 2026-09-09 (Jared): a second dial so SPEED and LOAD read as a "
        "pair, the feeds-and-speeds teaching object. Footprint: METER_* (3.5in "
        "target); studs not cut until the pair is measured.",
        "ruling (the dial); target footprint, MEASURE the pair",
        bore_d=METER_BORE, studs=METER_STUDS, stud_d=METER_STUD_D,
        front=METER_FRONT, behind=METER_BEHIND, panel_t=params.METER_MOVEMENT["panel_t_range"],
        family="meter", group="READ",
    ),
    Device(
        "LOAD", "moving-coil panel meter, spindle load, 0-100 scale card, "
        "split-core current transducer on a spindle phase (params.METER_MOVEMENT)",
        "bore", METER_X[1], METER_Y,
        "as SPEED. The 85C1 (Adafruit 4404 drawing) is the documented fallback, "
        "METER_85C1.",
        "ruling (the dial); target footprint, MEASURE the pair",
        bore_d=METER_BORE, studs=METER_STUDS, stud_d=METER_STUD_D,
        front=METER_FRONT, behind=METER_BEHIND, panel_t=params.METER_MOVEMENT["panel_t_range"],
        family="meter", group="READ",
    ),
    # ARM: alone, on the axis, lower half
    Device(
        "ARM", "Schneider Harmony XB4BG21, key switch selector, metal, black, "
        "22mm, key 455, 2 positions stay put, 1 NO",
        "bore", ARM_XY[0], ARM_XY[1],
        _SE.format("XB4BG21") + "Mounting diameter 22.5 mm, Height 47 mm, "
        "Width 30 mm, Depth 86 mm (whole product, head included)",
        "chosen; dimensions datasheet; place ruled 2026-09-09",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], 86.0),
        panel_t=XB4_PANEL_T, family="22", group="ARM",
    ),
    # MACHINE: the operator's corner, working row
    Device(
        "E_STOP", "22mm mushroom E-stop, ON HAND, pulled from the Carbide 3D "
        "Shapeoko 5 Pro power pendant; its own leads back to the Carbide controller",
        "bore", MACHINE_X[0], ROW_Y,
        "MEASURED 2026-09-09 (Jared, calipers): the pendant's E-stop hole reads "
        "0.865in (CARBIDE_HOLE_22), the 22mm standard; cut BORE_22. The box "
        "itself is not on the plate (ruling console_subtract).",
        "bore: measured (22mm standard); guard 40, body XB4-class, depth "
        "ESTOP_BEHIND, panel_t: assumption, MEASURE with the button",
        bore_d=BORE_22, front=(40.0, 40.0), behind=(XB4_BODY[0], XB4_BODY[1], ESTOP_BEHIND),
        panel_t=XB4_PANEL_T, red=True, family="22", group="MACHINE",
    ),
    Device(
        "FEED_HOLD", "22mm push button, ON HAND, pulled from the Carbide power "
        "pendant (feed hold); its own leads back to the Carbide controller",
        "bore", MACHINE_X[1], ROW_Y,
        "MEASURED 2026-09-09 (Jared, calipers): the pendant's feed-hold hole reads "
        "0.865in (CARBIDE_HOLE_22), the 22mm standard; cut BORE_22.",
        "bore: measured (22mm standard); body XB4-class, depth FEED_HOLD_BEHIND, "
        "panel_t: assumption, MEASURE with the button",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], FEED_HOLD_BEHIND),
        panel_t=XB4_PANEL_T, family="22", group="MACHINE",
    ),
    Device(
        "SPINDLE", "19mm anti-vandal push button, ON HAND, pulled from the Carbide "
        "VFD box (spindle enable); the Schneider ZB4BH033 that stood here is superseded",
        "bore", MACHINE_X[2], ROW_Y,
        "MEASURED 2026-09-09 (Jared, calipers): the VFD box's spindle-button hole "
        "reads 0.743in (CARBIDE_HOLE_19), a 19mm anti-vandal; cut BORE_19. Flange "
        "0.859in (AV19_FLANGE), 1.55in behind the flange (SPINDLE_BEHIND). Third "
        "button of the MACHINE block (Jared: 'move the spindle button with the "
        "estop and feed hold'), on the 22 row's 40 pitch.",
        "bore, flange, depth: measured; body width and panel_t: assumption",
        bore_d=BORE_19, front=AV19_BODY, behind=(AV19_BODY[0], AV19_BODY[1], SPINDLE_BEHIND),
        panel_t=AV19_PANEL_T, family="19", group="MACHINE",
    ),
    # EXTRACTION: the far end, working row, mirrors MACHINE
    Device(
        "EXTR_LAMP", "jewel pilot light, amber, 120 V neon, Dialco class "
        "(params.JEWEL_LAMP): EXTRACTOR CALLED, in parallel with the CT 15's "
        "trigger load, so it lights whenever the extractor is being asked to run",
        "bore", EXTRACTION_X[0], ROW_Y,
        "RULED 2026-09-09 (Jared: 'indicator on jewels for sure'). The trigger load "
        "is a resistor (params.DUST_CONTROL); the lamp is its face. A HUNT; "
        "JEWEL_* are the family's numbers.",
        "ruling (the lamp); footprint assumption, MEASURE the lamps",
        bore_d=JEWEL_BORE, front=(JEWEL_FLANGE, JEWEL_FLANGE), behind=JEWEL_BEHIND,
        panel_t=JEWEL_PANEL_T, family="jewel", group="EXTRACTION",
    ),
    Device(
        "DUST", "Schneider Harmony XB4BD33, 3-position selector switch, black, "
        "maintained, 2 NO: AUTO / ON / OFF, acting on a trigger load in the CT 15's "
        "auto-start socket (params.DUST_CONTROL), never on the extractor's mains",
        "bore", EXTRACTION_X[1], ROW_Y,
        _SE.format("XB4BD33") + "Mounting diameter 22.5 mm, Height 47 mm, "
        "Width 30 mm, Depth 68 mm. Wiring: params.SOURCES['DUST_CONTROL']",
        "chosen; dimensions datasheet; wiring ruling 2026-09-09",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], 68.0),
        panel_t=XB4_PANEL_T, family="22", group="EXTRACTION",
    ),
    Device(
        "BAG_LAMP", "jewel pilot light, amber, Dialco class (params.JEWEL_LAMP): "
        "the bag/filter service lamp, differential pressure across the filter; "
        "the Schneider XB4BVB5 that stood here is superseded",
        "bore", EXTRACTION_X[2], ROW_Y,
        "RULED 2026-09-09 (Jared: 'indicator on jewels for sure'). Driven by the "
        "station controller when it exists; until then a lamp with nothing behind "
        "it, cut anyway because the plate is composed once. A HUNT.",
        "ruling (the lamp); footprint assumption, MEASURE the lamps",
        bore_d=JEWEL_BORE, front=(JEWEL_FLANGE, JEWEL_FLANGE), behind=JEWEL_BEHIND,
        panel_t=JEWEL_PANEL_T, family="jewel", group="EXTRACTION",
    ),
    # PORTS: the bottom edge under MACHINE
    Device(
        "PENDANT", "PENGLIN PL183 USB-C panel-mount coupler, D-type (params.PL183): "
        "the jog pendant's port, under the E-stop",
        "d_type", PORTS_X[0], PORTS_Y,
        "RULED 2026-09-09 (Jared: 'Jog Remote USB-C'; 'group the pendant with the "
        "two usb plugs'). The Carbide pendant is a USB device on a removable USB-C "
        "to USB-A lead; the GX16 that stood here as the house connector meant "
        "re-terminating USB into aircraft pins on both sides. Cutout as USB_1.",
        "ruling; dimensions datasheet (C00 capture)",
        bore_d=24.0, d_holes=((-9.5, 12.0), (9.5, -12.0)), d_hole_d=3.5,
        front=(26.0, 31.0), behind=(24.0, 24.0, 27.5), panel_t=params.PL183["panel_t_range"],
        family="d_type", group="PORTS",
    ),
    Device(
        "USB_1", "PENGLIN PL183 USB-C panel-mount coupler, D-type (params.PL183): "
        "thumb-drive port to the PC (RULED 2026-09-09: keep, two hosts on a passive "
        "cable do nothing, so never a laptop)",
        "d_type", PORTS_X[1], PORTS_Y,
        "params.SOURCES['PL183']: round 24 cutout, 2 x 3.5 on a 19 x 24 "
        "diagonal, flange 26 x 31 x 2.2, body 27.5 behind the flange",
        "datasheet (C00 capture)",
        bore_d=24.0, d_holes=((-9.5, 12.0), (9.5, -12.0)), d_hole_d=3.5,
        front=(26.0, 31.0), behind=(24.0, 24.0, 27.5), panel_t=params.PL183["panel_t_range"],
        family="d_type", group="PORTS",
    ),
    Device(
        "USB_2", "PENGLIN PL183 USB-C panel-mount coupler, D-type (params.PL183): "
        "second thumb-drive port to the PC",
        "d_type", PORTS_X[2], PORTS_Y,
        "as USB_1", "datasheet (C00 capture)",
        bore_d=24.0, d_holes=((-9.5, 12.0), (9.5, -12.0)), d_hole_d=3.5,
        front=(26.0, 31.0), behind=(24.0, 24.0, 27.5), panel_t=params.PL183["panel_t_range"],
        family="d_type", group="PORTS",
    ),
)

GROUPS: dict[str, tuple[str, ...]] = {
    g: tuple(dv.label for dv in DEVICES if dv.group == g)
    for g in ("READ", "ARM", "MACHINE", "EXTRACTION", "PORTS")
}
"""The composition's five groups, read off the table."""

# -- what the chase is, derived from the table ----------------------------
CHASE_DRIVER: Device = max(DEVICES, key=lambda dv: dv.behind[2])
"""The device that sets the chase. Today the key switch."""

CHASE = CHASE_DRIVER.behind[2] + CHASE_MARGIN
"""Air between the wall's inner face and the cheek: 96mm at today's table."""

CONSOLE_KEEPOUT = CHASE
"""The keep-out the spec defines: the deepest device plus ``CHASE_MARGIN``,
96mm at today's table. The chase air, and the reference solid the drawers are
checked against. SOURCE: task C12. CONFIDENCE: ruling (the formula), datasheet
(the number)."""

DRAWER_GIVE = CONSOLE_KEEPOUT + T
"""What each overlapped drawer actually gives up in width: the keep-out AND
the cheek that bounds it, because a drawer slide needs a face to screw to and
the wall is now ``CONSOLE_KEEPOUT`` away. The spec narrows a drawer by
``CONSOLE_KEEPOUT`` and says its slide shifts inboard with it; the cheek is
what the slide shifts onto, and it is a sheet thickness the spec did not
carry. Its slide moves inboard by this same amount. CONFIDENCE: derived.
RULING WANTED: the spec's number is the keep-out; the drawer's loss is the
keep-out plus one sheet, or the slides mount to something thinner."""

# -- the chase's birch and acrylic --------------------------------------
RIB_W = CHASE
"""The floor rib spans the chase exactly: 18mm birch on edge, ``CHASE`` wide."""

CHEEK_PASS: tuple[float, float] = (GRID * 2, 24.0)
"""(length along the bay, height) of the one capsule pass in the cheek for the
runs that emerge from the spine in the drawer zone. 24 clears a GX16 plug's
Ø18.3 knurl (Handson drawing) with room; two leads side by side in 40.
CONFIDENCE: chosen."""

CHEEK_PASS_SETBACK = GRID * 2
"""Pass centre forward of the spine's front face. CONFIDENCE: chosen."""

REVEAL_SCREW_D = SCREW_CLEAR_D
"""Clearance holes in the acrylic reveal for the house screw into birch edges."""


# ====================================================================
# GEOMETRY. Arithmetic on the block above and on Datums.
# ====================================================================


def console_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span of the band: GRID*24 up to whichever is lower of the
    cap's underside less the tie screws' reach and a land, and the machine's
    own ceiling over the band's front end on the wall's outer face -- the
    front-right Y gusset plate tapers down toward the leg and is lowest at the
    band's front edge. The wall is relieved to that plate; the plate flush in
    it cannot be, so it stays ``BAND_LAND`` under it."""
    cap = d.top_z[0] - TOP_SCREW_LINE
    steel = d.s.clear_z(d.x_right, CONSOLE_Y[0]) - BAND_LAND
    return (CONSOLE_Z0, min(cap, steel))


def band_bound(d: Datums = D) -> str:
    """Which limit sets the band's top: 'cap ties' or 'gusset'."""
    cap = d.top_z[0] - TOP_SCREW_LINE
    steel = d.s.clear_z(d.x_right, CONSOLE_Y[0]) - BAND_LAND
    return "gusset" if steel < cap else "cap ties"


def console_band(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """((y0, y1), (z0, z1)) of CONSOLE_BAND in station coordinates."""
    return (CONSOLE_Y, console_z(d))


def plate_size(d: Datums = D) -> tuple[float, float]:
    """(W, H) of the plate: the band's Y span, and the band's Z span snapped
    DOWN to the grid so the plate stays inside it."""
    (y0, y1), (z0, z1) = console_band(d)
    return (y1 - y0, snap_dn(z1 - z0))


def plate_z(d: Datums = D) -> tuple[float, float]:
    z0 = console_z(d)[0]
    return (z0, z0 + plate_size(d)[1])


def aperture_size(d: Datums = D) -> tuple[float, float]:
    """(W, H) of the wall's through-aperture behind the plate: the plate less
    its ``LIP`` margin all round."""
    w, h = plate_size(d)
    return (w - 2 * LIP, h - 2 * LIP)


def wall_inner_x(d: Datums = D) -> float:
    """Station X of the right end wall's inner face."""
    return d.wall_x[3]


def chase_x(d: Datums = D) -> tuple[float, float]:
    """Station X span of the chase air: cheek face to the wall's inner face."""
    return (wall_inner_x(d) - CHASE, wall_inner_x(d))


def cheek_x(d: Datums = D) -> tuple[float, float]:
    """Station X span of the cheek panel, inboard of the chase."""
    x1 = chase_x(d)[0]
    return (x1 - T, x1)


def narrowed_openings(d: Datums = D) -> tuple[int, ...]:
    """Indices into ``bay_walls.drawer_openings`` (bottom first) of every
    opening the cheek carries: all of them with ``CHEEK_TO_DECK`` (RULED
    2026-09-04), else those whose Z band crosses CONSOLE_BAND. What
    ``drawers`` narrows."""
    from stations.cnc_shapeoko.parts.bay_walls import drawer_openings

    z0, z1 = console_z(d)
    out: list[int] = []
    for k, (floor, height) in enumerate(drawer_openings(d)):
        lo = d.deck_top + floor
        hi = lo + height
        if CHEEK_TO_DECK or (lo < z1 and hi > z0):
            out.append(k)
    return tuple(out)


def cheek_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span of the cheek: the lowest narrowed opening's floor (the
    deck, under the 2026-09-04 ruling) to the cap's underside, which it
    butts."""
    from stations.cnc_shapeoko.parts.bay_walls import drawer_openings

    ks = narrowed_openings(d)
    if not ks:
        return (d.top_z[0], d.top_z[0])
    floors = [d.deck_top + drawer_openings(d)[k][0] for k in ks]
    return (min(floors), d.top_z[0])


def rib_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span of the floor rib: on the cheek's bottom edge."""
    z0 = cheek_z(d)[0]
    return (z0, z0 + T)


def chase_y(d: Datums = D) -> tuple[float, float]:
    """Station Y span of the cheek, the rib and the chase: one pane thickness
    behind the bay's open front, where the reveal sits flush with the
    carcass, to the spine's front face."""
    return (d.y_front + PT, d.y_spine)


def stile_x(d: Datums = D) -> tuple[float, float]:
    """Station X span of the front-right stile, which stands inside the
    chase's front corner (2026-09-04)."""
    return next(xs for label, xs, _ys in d.stiles if label == "stile_front_right")


def reveal_span(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """(x span, z span) of the acrylic reveal: over the chase AND the cheek's
    front edge, from the cheek's outer face to the front-right stile's inner
    edge (INSET between cheek and stile, 2026-09-04), from the rib's bottom to
    the cap, so its screws land in the cheek's edge and the rib's end."""
    return ((cheek_x(d)[0], stile_x(d)[0]), (rib_z(d)[0], d.top_z[0]))


def rib_notch_local(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """((x0, x1), (y0, y1)) of the notch the stile's foot takes out of the
    rib, rib-local: from the rib's front end back to the stile's rear face,
    and from the wall's inner face across to the stile's inner edge."""
    y0, _y1 = chase_y(d)
    sx0, _sx1 = stile_x(d)
    stile_rear = next(ys[1] for label, _xs, ys in d.stiles if label == "stile_front_right")
    return ((0.0, stile_rear - y0), (0.0, wall_inner_x(d) - sx0))


def rib_front_x(d: Datums = D) -> tuple[float, float]:
    """Station X of the rib's front end that survives the notch: what the
    reveal's third screw lands in."""
    return (cheek_x(d)[1], stile_x(d)[0])


# -- local frames --------------------------------------------------------
# The plate and the cheek are drawn like a wall: local X = station +Y, local
# Y = up, thickness into station +X, back face (Z = 0) inboard. The rib is
# drawn flat like the deck but its local +Y runs into station -X so its origin
# sits on the wall's inner face. The reveal is drawn like a drawer front.
# check_console_plate asserts every placed bounding box, because a rotation is
# where signs go wrong.


def plate_plane(d: Datums = D) -> Plane:
    return Plane(
        origin=(wall_inner_x(d), CONSOLE_Y[0], plate_z(d)[0]),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )


def cheek_plane(d: Datums = D) -> Plane:
    return Plane(
        origin=(cheek_x(d)[0], chase_y(d)[0], cheek_z(d)[0]),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )


def rib_plane(d: Datums = D) -> Plane:
    return Plane(
        origin=(wall_inner_x(d), chase_y(d)[0], rib_z(d)[0]),
        x_dir=(0, 1, 0),
        z_dir=(0, 0, 1),
    )


def reveal_plane(d: Datums = D) -> Plane:
    (x0, _x1), (z0, _z1) = reveal_span(d)
    return Plane(origin=(x0, d.y_front + PT, z0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))


# -- the plate -----------------------------------------------------------


def lip_screws(d: Datums = D) -> list[tuple[float, float]]:
    """Plate-local centres of the margin screws: the carcass rhythm along the
    two long edges, one at the middle of each short edge."""
    w, h = plate_size(d)
    e = LIP / 2
    out: list[tuple[float, float]] = []
    for p in screw_positions(w, pitch=SCREW_PITCH, inset=SCREW_END_INSET):
        out.append((p, e))
        out.append((p, h - e))
    out.append((e, h / 2))
    out.append((w - e, h / 2))
    return out


def build_plate(d: Datums = D) -> Part:
    """The plate, flat, plate-local: Z = 0 its inner face, Z = ``PLATE_T`` the
    outer face the operator reads. Through cuts only, which is all a waterjet
    makes; the ten countersinks are a drill-press step and the legends are a
    laser layer (``MARK``), and neither is in the solid."""
    w, h = plate_size(d)
    p = panel(w, h, PLATE_T)

    # the margin screws, through, countersunk after cutting
    for x, y in lip_screws(d):
        p -= bore(x, y, PLATE_SCREW_CLEAR_D, thickness=PLATE_T)

    # the devices
    for dv in DEVICES:
        p -= bore(dv.cx, dv.cy, dv.bore_d, thickness=PLATE_T)
        for dx, dy in dv.d_holes:
            p -= bore(dv.cx + dx, dv.cy + dy, dv.d_hole_d, thickness=PLATE_T)
        for dx, dy in dv.studs:
            p -= bore(dv.cx + dx, dv.cy + dy, dv.stud_d, thickness=PLATE_T)
    return p


def wall_cutter(d: Datums = D) -> Part:
    """What the right end wall loses to the console, in STATION coordinates,
    for ``bay_walls`` to bring into its own frame and subtract.

    JOINERY, both cuts, so square with dogbones: the through-aperture behind
    the plate for the device bodies, and the outer-face relief the plate lies
    in. Both ``DADO_FIT`` oversize, the way every housing in the carcass is.
    Plus the ten pilots for the margin screws, blind from the outer face.
    """
    w, h = plate_size(d)
    tw, th = aperture_size(d)
    cx, cy = w / 2, h / 2
    cut: Part | None = None

    def add(c: Part) -> None:
        nonlocal cut
        cut = c if cut is None else cut + c

    # through aperture, + fit, square, four through reliefs
    aw, ah = tw + DADO_FIT, th + DADO_FIT
    add(through_slot((cx, cy), aw, ah))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(relief(cx + sx * aw / 2, cy + sy * ah / 2))

    # outer-face relief, outline + fit, RELIEF_T (the plate) deep
    rw, rh = w + DADO_FIT, h + DADO_FIT
    over = T
    rab = Box(rw, rh, RELIEF_T + over, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((cx, cy, T - RELIEF_T))
    )
    add(rab)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(relief(cx + sx * rw / 2, cy + sy * rh / 2, depth=RELIEF_T, side="front"))

    # margin screw pilots, blind from the outer face into the land
    for x, y in lip_screws(d):
        add(bore(x, y, PLATE_SCREW_PILOT_D, depth=RELIEF_T + PLATE_SCREW_PILOT, side="front"))

    # the rib's screws, through the wall from outside into the rib's edge,
    # below the band on the same face
    z_rib = (rib_z(d)[0] + rib_z(d)[1]) / 2 - plate_z(d)[0]
    for y in rib_wall_screws_y(d):
        add(bore(y - CONSOLE_Y[0], z_rib, SCREW_CLEAR_D))

    assert cut is not None
    return plate_plane(d) * cut


# -- the chase -----------------------------------------------------------


def cheek_size(d: Datums = D) -> tuple[float, float]:
    y0, y1 = chase_y(d)
    z0, z1 = cheek_z(d)
    return (y1 - y0, z1 - z0)


def cheek_pass_local(d: Datums = D) -> tuple[float, float]:
    """Cheek-local centre of the pass: near the spine, at the spine's high
    crossing row, which is where the console runs cross."""
    from stations.cnc_shapeoko.parts.spine_panel import ROW_Z

    w, _h = cheek_size(d)
    return (w - CHEEK_PASS_SETBACK, d.deck_top + ROW_Z["high"] - cheek_z(d)[0])


def cheek_rib_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Cheek-local centres of the screws through the cheek into the rib's edge:
    the rib's mid-thickness, on the carcass rhythm."""
    w, _h = cheek_size(d)
    y = T / 2
    return [(p, y) for p in screw_positions(w, pitch=SCREW_PITCH, inset=SCREW_END_INSET)]


def build_cheek(d: Datums = D) -> Part:
    """The cheek, flat, cheek-local: Z = 0 is the BAY face that carries the
    narrowed drawers' slides, Z = T looks into the chase."""
    from stations.cnc_shapeoko.parts.bay_walls import (
        SLIDE_MEMBER_H,
        _slide_row,
        drawer_openings,
    )

    w, h = cheek_size(d)
    p = panel(w, h)
    z0 = cheek_z(d)[0]

    # the slide rows the right end wall gave up, on the bay face, at the same
    # heights bay_walls drills them: one row per narrowed opening. bay_walls
    # measures a row from the bay's open front and this blank starts a pane
    # thickness behind it, so the row shifts forward by that much.
    shift = Location((d.y_front - chase_y(d)[0], 0, 0))
    for k in narrowed_openings(d):
        floor, _height = drawer_openings(d)[k]
        y_local = d.deck_top + floor + SLIDE_MEMBER_H / 2 - z0
        p -= _slide_row(y_local, "back", d).moved(shift)

    # screws into the rib's edge
    for x, y in cheek_rib_screws_local(d):
        p -= bore(x, y, SCREW_CLEAR_D)

    # the one pass: an APERTURE, capsule-ended
    px, py = cheek_pass_local(d)
    pl, ph = CHEEK_PASS
    p -= through_slot((px, py), pl, ph, corner_r=ph / 2)
    return p


def rib_wall_screws_y(d: Datums = D) -> list[float]:
    """Station Y of the screws through the wall into the rib's edge: on the
    band the console keeps clear of the front leg's flange, back to the
    spine. Starts at the console band, not the bay front, because the leg's
    angle covers the wall's outer face at the front corner."""
    y0, y1 = CONSOLE_Y[0], chase_y(d)[1]
    return [y0 + p for p in screw_positions(y1 - y0, pitch=SCREW_PITCH, inset=SCREW_END_INSET)]


def build_rib(d: Datums = D) -> Part:
    """The floor rib, flat, rib-local: local X along the bay, local Y across
    the chase from the wall's inner face, thickness up. No holes: both sets of
    screws enter its EDGES, which the shop drills to the holes in the wall and
    the cheek. One NOTCH at its front-outer corner for the front-right stile's
    foot (2026-09-04): JOINERY, square, one dogbone at its inside corner."""
    y0, y1 = chase_y(d)
    p = panel(y1 - y0, RIB_W)
    (nx0, nx1), (ny0, ny1) = rib_notch_local(d)
    over = T
    p -= through_slot(
        ((nx0 - over + nx1 + DADO_FIT / 2) / 2, (ny0 - over + ny1 + DADO_FIT / 2) / 2),
        (nx1 + DADO_FIT / 2) - (nx0 - over),
        (ny1 + DADO_FIT / 2) - (ny0 - over),
    )
    p -= relief(nx1 + DADO_FIT / 2, ny1 + DADO_FIT / 2)
    return p


def build_reveal(d: Datums = D) -> Part:
    """The clear acrylic reveal over the chase's front, flat, reveal-local:
    local X = station X from the cheek's outer face, local Y up. Three
    clearance holes: two into the cheek's front edge, one into what is left
    of the rib's front end beside the stile."""
    (x0, x1), (z0, z1) = reveal_span(d)
    w, h = x1 - x0, z1 - z0
    p = panel(w, h, PT)
    cx = T / 2                                   # the cheek's centreline
    for y in (h * 0.3, h * 0.8):
        p -= bore(cx, y, REVEAL_SCREW_D, thickness=PT)
    rx0, rx1 = rib_front_x(d)
    p -= bore((rx0 + rx1) / 2 - x0, T / 2, REVEAL_SCREW_D, thickness=PT)   # the rib's end
    return p


def build_keepout(d: Datums = D) -> Part:
    """The chase air the drawers are checked against, in STATION coordinates.
    Since 2026-09-09 nothing is subtracted from it: the E-stop is a 22mm
    device like its neighbours, not a box on a bracket."""
    x0, x1 = chase_x(d)
    (y0, y1), (z0, z1) = console_band(d)
    return Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3).moved(
        Location((x0, y0, z0))
    )


def panes(d: Datums = D) -> list[tuple[str, Device, Part]]:
    """(label, device, flat pane) for each recessed instrument. Empty since
    2026-09-09: a 3mm plate has no pockets and nothing reads through acrylic.
    Kept so the nest and the assembly keep one call."""
    return []


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, placed solid) for everything this module puts in the
    assembly: the steel plate, birch, acrylic, and the keep-out reference solid.
    The plate lies in the wall's relief, its outer face at the wall's."""
    out: list[tuple[str, str, Part]] = [
        (PART_NAME, "steel", plate_plane(d) * build_plate(d).moved(Location((0.0, 0.0, T - PLATE_T)))),
        (CHEEK_NAME, "carcass", cheek_plane(d) * build_cheek(d)),
        (RIB_NAME, "carcass", rib_plane(d) * build_rib(d)),
        (REVEAL_NAME, "acrylic", reveal_plane(d) * build_reveal(d)),
        (KEEPOUT_NAME, "reference", build_keepout(d)),
    ]
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples for
    ``assembly.joints``. The plate is housed in the wall's relief; everything
    else in the chase meets on faces."""
    from stations.cnc_shapeoko.parts.bay_walls import WALLS

    wall = WALLS[3].name
    x0 = wall_inner_x(d)
    out: list[tuple] = [
        (wall, PART_NAME, "housing", "x", x0 + T - PLATE_T, x0 + T,
         "plate flush in the wall's outer-face relief, over the aperture"),
        (PART_NAME, KEEPOUT_NAME, "bearing", None, 0.0, 0.0,
         "the chase air starts at the plate's inner face"),
        (wall, KEEPOUT_NAME, "bearing", None, 0.0, 0.0, "air against the wall's inner face"),
        (CHEEK_NAME, KEEPOUT_NAME, "bearing", None, 0.0, 0.0, "air against the cheek"),
        (RIB_NAME, KEEPOUT_NAME, "bearing", None, 0.0, 0.0, "air above the rib"),
        (REVEAL_NAME, KEEPOUT_NAME, "bearing", None, 0.0, 0.0, "air behind the reveal"),
        (CHEEK_NAME, RIB_NAME, "butt", None, 0.0, 0.0,
         "rib's end on the cheek's chase face, screwed through the cheek"),
        (wall, RIB_NAME, "butt", None, 0.0, 0.0,
         "rib's end on the wall's inner face, screwed through the wall from outside"),
        ("top_cap", CHEEK_NAME, "butt", None, 0.0, 0.0,
         "cheek's top edge on the cap's underside, tied down through the cap"),
        ("base_deck", CHEEK_NAME, "butt", None, 0.0, 0.0,
         "cheek's bottom edge on the deck (2026-09-04: the cheek runs to the deck)"),
        ("base_deck", RIB_NAME, "bearing", None, 0.0, 0.0,
         "rib flat on the deck's top face"),
        ("stile_front_right", RIB_NAME, "butt", None, 0.0, 0.0,
         "the stile's foot in the rib's notch, DADO_FIT clear"),
        ("stile_front_right", REVEAL_NAME, "butt", None, 0.0, 0.0,
         "reveal's right edge beside the stile's inner edge"),
        ("spine_panel", CHEEK_NAME, "butt", None, 0.0, 0.0,
         "cheek's rear edge on the spine's front face; the spine cuts nothing"),
        ("spine_panel", RIB_NAME, "butt", None, 0.0, 0.0, "rib's rear end on the spine"),
        (CHEEK_NAME, REVEAL_NAME, "butt", None, 0.0, 0.0,
         "reveal on the cheek's front edge, screwed into it"),
        (RIB_NAME, REVEAL_NAME, "butt", None, 0.0, 0.0, "reveal on the rib's front end"),
        (wall, REVEAL_NAME, "butt", None, 0.0, 0.0, "reveal beside the wall's front edge"),
    ]
    return out


def estop_callout_anchor(d: Datums = D) -> tuple[float, float]:
    """Plate-local centre for C17's EMERGENCY STOP callout: under the mushroom
    guard, above the pendant port's flange. Enduramark black on brushed steel
    like every other word; the red budget is the mushroom, not a letter (the
    brief reads two ways on this, and ``check_console_plate`` asks)."""
    dv = next(v for v in DEVICES if v.red)
    below = next(v for v in DEVICES if v.label == "PENDANT")
    top = below.cy + below.front[1] / 2
    bottom = dv.cy - dv.front[1] / 2
    return (dv.cx, (top + bottom) / 2)


def estop_callout_band(d: Datums = D) -> tuple[float, float]:
    """Plate-local Y span of the steel the E-stop's word sits in: from the
    pendant port's flange top to the mushroom guard's bottom."""
    dv = next(v for v in DEVICES if v.red)
    below = next(v for v in DEVICES if v.label == "PENDANT")
    return (below.cy + below.front[1] / 2, dv.cy - dv.front[1] / 2)


def callouts_local(d: Datums = D) -> list[callouts.Callout]:
    """The plate's one word, on the outer face the operator reads, as tall as
    its band allows AND as wide as the steel between the front screw margin
    and the guard's centreline allows (the E-stop is at the plate's front
    corner since 2026-09-09; the word is centred on it and must not run onto
    the margin). Marked, not carved: the solid is untouched and the word goes
    out on ``MARK``."""
    y0, y1 = estop_callout_band(d)
    cx, cy = estop_callout_anchor(d)
    h = callouts.fit_height(y1 - y0)
    w_avail = 2 * (cx - LIP)
    w = callouts.text_width(CALLOUT_ESTOP, h)
    if w > w_avail:
        h = h * w_avail / w
    return [callouts.Callout(CALLOUT_ESTOP, (cx, cy), height=h)]


def register(d: Datums = D) -> callouts.Register:
    """The laser bed's datums: the two short-edge margin screws, through holes
    the plate already has, one at each end of the plate."""
    (ax, ay), (bx, by) = lip_screws(d)[-2:]
    return callouts.Register(
        (ax, ay, PLATE_SCREW_CLEAR_D), (bx, by, PLATE_SCREW_CLEAR_D), "the two short-edge margin screws"
    )


# ====================================================================
# CHECKS
# ====================================================================


def _outline_dist(pt: tuple[float, float], lo: tuple[float, float], hi: tuple[float, float]) -> float:
    """Distance from a point to a rectangle (0 inside)."""
    dx = max(lo[0] - pt[0], 0.0, pt[0] - hi[0])
    dy = max(lo[1] - pt[1], 0.0, pt[1] - hi[1])
    return hypot(dx, dy)


def leg_bolt_clearance(d: Datums = D) -> list[tuple[str, float]]:
    """(bolt label, mm) from each right-end-wall bolt axis to the nearest
    point of the console's cuts in the wall (the rabbet, DADO_FIT oversize)
    and of the keep-out's footprint on the wall, whichever is nearer. Both are
    the same rectangle in Y-Z today; measured separately so they stay honest
    if one moves."""
    from stations.cnc_shapeoko.parts import leg_joint

    w, h = plate_size(d)
    y0, z0 = CONSOLE_Y[0], plate_z(d)[0]
    rab_lo = (y0 - DADO_FIT / 2, z0 - DADO_FIT / 2)
    rab_hi = (y0 + w + DADO_FIT / 2, z0 + h + DADO_FIT / 2)
    (ky0, ky1), (kz0, kz1) = console_band(d)
    out: list[tuple[str, float]] = []
    for b in leg_joint.bolts(d):
        if b.wall != 3:
            continue
        pt = (b.y, b.z)
        out.append(
            (b.label, min(_outline_dist(pt, rab_lo, rab_hi), _outline_dist(pt, (ky0, kz0), (ky1, kz1))))
        )
    return out


def gusset_land(d: Datums = D) -> tuple[float, float]:
    """(mm, station y) of the least wall left between the console's cuts on
    the wall's outer face and the gusset relief above them: the rabbet's top
    edge (``DADO_FIT`` oversize) and its two blind corner reliefs, against the
    gusset's underside where it crosses the wall's outer face (the machine's
    own ceiling, sampled along the band). The relief is ``RELIEF_T`` deep and the
    relief ``plate_t`` deep, so any overlap of the two outlines is a real
    intersection; this is the web between them, and it is held to the same
    ``ROUTER_D`` every other pair of cuts is."""
    w, h = plate_size(d)
    y0, z0 = CONSOLE_Y[0], plate_z(d)[0]
    top = z0 + h + DADO_FIT / 2
    r = ROUTER_D / 2
    ya, yb = y0 - DADO_FIT / 2, y0 + w + DADO_FIT / 2
    dy = 0.5
    n = int((yb - ya) / dy)
    ceiling = [(ya + i * dy, d.s.clear_z(d.x_right, ya + i * dy)) for i in range(n + 1)]
    # the top edge is horizontal: the nearest ceiling point over it is straight up
    best = min(((zc - top, y) for y, zc in ceiling), key=lambda t: t[0])
    # the corner reliefs are circles on the edge's ends: nearest ceiling point, less r
    for yc in (ya, yb):
        for y, zc in ceiling:
            land = hypot(y - yc, zc - top) - r
            if land < best[0]:
                best = (land, yc)
    return best


def _front_rect(dv: Device) -> tuple[tuple[float, float], tuple[float, float]]:
    """What the device occupies on the outer face: its bezel/flange."""
    w, h = max(dv.front[0], dv.bore_d), max(dv.front[1], dv.bore_d)
    return ((dv.cx - w / 2, dv.cy - h / 2), (dv.cx + w / 2, dv.cy + h / 2))


def _cut_rect(dv: Device) -> tuple[tuple[float, float], tuple[float, float]]:
    """What the plate actually loses to the device on its outer face: the
    bore and its screw and stud holes. The web rule is about the steel
    between CUTS; a flange lying on the face is not a cut."""
    x0 = x1 = dv.cx
    y0 = y1 = dv.cy
    r = dv.bore_d / 2
    x0, x1, y0, y1 = x0 - r, x1 + r, y0 - r, y1 + r
    for (dx, dy), hd in [(h_, dv.d_hole_d) for h_ in dv.d_holes] + [(s_, dv.stud_d) for s_ in dv.studs]:
        hr = hd / 2
        x0, x1 = min(x0, dv.cx + dx - hr), max(x1, dv.cx + dx + hr)
        y0, y1 = min(y0, dv.cy + dy - hr), max(y1, dv.cy + dy + hr)
    return ((x0, y0), (x1, y1))


def _behind_rect(dv: Device) -> tuple[tuple[float, float], tuple[float, float]]:
    w, h, _dep = dv.behind
    return ((dv.cx - w / 2, dv.cy - h / 2), (dv.cx + w / 2, dv.cy + h / 2))


def _rect_gap(a, b) -> float:
    """Clear distance between two axis-aligned rectangles. Negative when they
    overlap: the smaller of the two axis overlaps, negated."""
    gx = max(b[0][0] - a[1][0], a[0][0] - b[1][0])   # separation in x, <0 if overlapping
    gy = max(b[0][1] - a[1][1], a[0][1] - b[1][1])
    if gx >= 0 and gy >= 0:
        return hypot(gx, gy)
    if gx >= 0 or gy >= 0:
        return max(gx, gy)
    return max(gx, gy)


def _behind_clashes() -> list[tuple[Device, Device, float]]:
    out = []
    for i, a in enumerate(DEVICES):
        for b in DEVICES[i + 1:]:
            gap = _rect_gap(_behind_rect(a), _behind_rect(b))
            if gap < 0:
                out.append((a, b, gap))
    return out


def check_console_plate(d: Datums = D) -> list[str]:
    """What the console has to be true for."""
    from stations.cnc_shapeoko.parts import drawers, leg_joint
    from stations.cnc_shapeoko.parts.bay_walls import SLIDE_LEN
    from stations.cnc_shapeoko.parts.spine_panel import (
        BORE_CLEAR_MIN,
        BORE_D,
        CROSSINGS,
        ROW_Z,
        crossing_x,
    )

    notes: list[str] = []
    w, h = plate_size(d)
    tw, th = aperture_size(d)
    (by0, by1), (bz0, bz1) = console_band(d)
    z0 = plate_z(d)[0]

    # -- the band has to exist and the plate has to fit it
    if bz1 <= bz0 + GRID:
        notes.append(
            f"CONSOLE_BAND is {bz1 - bz0:.0f}mm tall between z {bz0:.0f} and "
            f"{bz1:.0f}: the cap's tie screws leave no band"
        )
    if z0 + h > bz1 + 1e-9:
        notes.append(f"the plate runs {z0 + h - bz1:.1f}mm above the band's top")

    # -- the wall's outer face above the rabbet is not the gusset's relief
    land, land_y = gusset_land(d)
    if land < ROUTER_D:
        notes.append(
            f"the rabbet's top edge or a corner relief comes {land:.1f}mm from the "
            f"gusset relief at y {land_y:.0f}, under a {ROUTER_D:.2f}mm web: the "
            "band's top is in the steel"
        )
    cap_line = d.top_z[0] - TOP_SCREW_LINE
    if bz1 < cap_line - 1e-9:
        notes.append(
            "CONSOLE BAND TOP, standing note. The spec puts the band's top at the "
            f"cap's underside less the tie line, z {cap_line:.0f}; the front-right Y "
            f"gusset's underside crosses the wall's outer face at z "
            f"{d.s.clear_z(d.x_right, CONSOLE_Y[0]):.1f} over the band's ruled front "
            f"edge (y {CONSOLE_Y[0]:.0f}), so the band stops BAND_LAND {BAND_LAND:.0f} "
            f"under the steel at z {bz1:.1f} and the plate is {h:.0f} tall, not "
            f"{snap_dn(cap_line - bz0):.0f}. The least wall between the rabbet and the "
            f"relief is {land:.1f}mm at y {land_y:.0f}. The machine set this, not a "
            "choice; the land is chosen. Expected, and worth knowing before the "
            "band is read against the brief."
        )

    # -- 18mm of land to every leg bolt on this wall
    worst = min(leg_bolt_clearance(d), key=lambda t: t[1])
    if worst[1] < LEG_LAND:
        notes.append(
            f"the console's cut or keep-out comes {worst[1]:.1f}mm from leg "
            f"bolt {worst[0]}'s axis, under the {LEG_LAND:.0f}mm land"
        )

    # -- the plate is inside every device's panel-thickness range, and its
    # screws stop short of the wall's inner face
    for dv in DEVICES:
        lo, hi = dv.panel_t
        if not lo - 1e-9 <= PLATE_T <= hi + 1e-9:
            notes.append(
                f"{dv.label} clamps a {lo:.0f}-{hi:.0f}mm panel and the plate is "
                f"{PLATE_T:.0f}mm ({PLATE_MATERIAL})"
            )
    if PLATE_SCREW_PILOT > T - RELIEF_T - 2.0:
        notes.append(
            f"the plate screw's {PLATE_SCREW_PILOT:.0f}mm pilot runs within 2mm of "
            f"the wall's inner face ({T - RELIEF_T:.0f} of wall under the relief)"
        )
    notes.append(
        f"CONSOLE PLATE, standing note. {PLATE_MATERIAL}, RULED 2026-09-09: "
        f"{params.CONSOLE_PLATE['process']}. The two meter bezels stand 10mm "
        "proud of the flush plate (no recess, no panes). The DXF's CUT layer is "
        "the waterjet's; MARK is the laser's; the countersinks are on neither."
    )

    # -- 22mm bores are 22.3, one red
    reds = [dv for dv in DEVICES if dv.red]
    if len(reds) != 1:
        notes.append(f"{len(reds)} devices are tagged red; the E-stop is the budget")
    for dv in DEVICES:
        if dv.family == "22" and abs(dv.bore_d - BORE_22) > 0.05:
            notes.append(f"{dv.label} is a 22mm device bored {dv.bore_d:.2f}")
        if not dv.family or not dv.group:
            notes.append(f"{dv.label} has no family or group: it is not in the composition")

    # -- devices on the face: at least a cutter web between neighbours, 22mm
    # and 19mm buttons at the maker's pitch, jewels at the composition's pitch
    # to a button, every flange FLANGE_TO_BEZEL_MIN off a dial's bezel
    buttons = {"22", "19"}
    for i, a in enumerate(DEVICES):
        for b in DEVICES[i + 1:]:
            gap = _rect_gap(_cut_rect(a), _cut_rect(b))
            if gap < ROUTER_D:
                notes.append(
                    f"{a.label} and {b.label} are cut {gap:.1f}mm apart on the plate's "
                    f"face, under a {ROUTER_D:.2f}mm web"
                )
            face = _rect_gap(_front_rect(a), _front_rect(b))
            if face < 0:
                notes.append(f"{a.label} and {b.label} overlap on the plate's outer face")
            pitch = hypot(a.cx - b.cx, a.cy - b.cy)
            if a.family in buttons and b.family in buttons and pitch < PITCH_22_MIN:
                notes.append(
                    f"{a.label} and {b.label} are {pitch:.0f}mm apart, under the "
                    f"{PITCH_22_MIN:.0f}mm the XB4 sheet asks for"
                )
            if {a.family, b.family} == {"jewel", "22"} and pitch < JEWEL_22_PITCH_MIN:
                notes.append(
                    f"{a.label} and {b.label} are {pitch:.0f}mm apart, under the "
                    f"composition's {JEWEL_22_PITCH_MIN:.0f} between a jewel and a 22"
                )
            if "meter" in (a.family, b.family) and a.family != b.family and face < FLANGE_TO_BEZEL_MIN:
                notes.append(
                    f"{a.label}'s flange is {face:.1f}mm from {b.label}'s bezel on the "
                    f"face, under FLANGE_TO_BEZEL_MIN {FLANGE_TO_BEZEL_MIN:.0f}"
                )
    for dv in DEVICES:
        (fx0, fy0), (fx1, fy1) = _front_rect(dv)
        if dv.family == "meter":
            # a proud bezel may overhang the margin strip; it may not cover a
            # screw. What is CUT (the bore) stays inside the field.
            (cx0, cy0), (cx1, cy1) = _cut_rect(dv)
            if cx0 < LIP or cy0 < LIP or cx1 > w - LIP or cy1 > h - LIP:
                notes.append(f"{dv.label}'s bore reaches into the plate's screw margin")
            r = dv.front[0] / 2
            for sx, sy in lip_screws(d):
                if hypot(sx - dv.cx, sy - dv.cy) < r + PLATE_SCREW_CLEAR_D / 2:
                    notes.append(
                        f"{dv.label}'s bezel covers the margin screw at ({sx:.0f}, {sy:.0f})"
                    )
        elif fx0 < LIP or fy0 < LIP or fx1 > w - LIP or fy1 > h - LIP:
            notes.append(f"{dv.label} reaches onto the plate's screw margin on the outer face")

    # -- the composition: groups where the ruling put them, mirrored on the axis
    by = {dv.label: dv for dv in DEVICES}
    def _cx(labels: tuple[str, ...]) -> float:
        return sum(by[l].cx for l in labels) / len(labels)
    if abs(_cx(GROUPS["MACHINE"]) + _cx(GROUPS["EXTRACTION"]) - 2 * AXIS_X) > 1e-6:
        notes.append(
            f"MACHINE (centre {_cx(GROUPS['MACHINE']):.1f}) and EXTRACTION (centre "
            f"{_cx(GROUPS['EXTRACTION']):.1f}) do not mirror about the axis at {AXIS_X:.0f}"
        )
    if abs(by["SPEED"].cx + by["LOAD"].cx - 2 * AXIS_X) > 1e-6 or by["SPEED"].cy != by["LOAD"].cy:
        notes.append("the two dials are not a pair centred on the axis")
    if abs(by["ARM"].cx - AXIS_X) > 1e-6:
        notes.append(f"ARM is at x {by['ARM'].cx:.1f}, off the axis at {AXIS_X:.0f}")
    for other in DEVICES:
        if other.label != "ARM" and hypot(other.cx - by["ARM"].cx, other.cy - by["ARM"].cy) < PITCH_22_MIN:
            notes.append(f"{other.label} is within {PITCH_22_MIN:.0f} of ARM, which stands alone")
    if len({by[l].cy for l in GROUPS["MACHINE"] + GROUPS["EXTRACTION"]}) != 1:
        notes.append("MACHINE and EXTRACTION are not on one row")
    if len({by[l].cy for l in GROUPS["PORTS"]}) != 1 or by["PENDANT"].cx != by["E_STOP"].cx:
        notes.append("PORTS are not one row with the pendant under the E-stop")
    notes.append(
        "CONSOLE COMPOSITION, standing note. RULED 2026-09-09: composed, not packed. "
        + "; ".join(f"{g}: {', '.join(ls)}" for g, ls in GROUPS.items())
        + f". Axis x {AXIS_X:.0f}; MACHINE and EXTRACTION centres {AXIS_X - _cx(GROUPS['MACHINE']):.0f} "
        "either side; dials 70 either side; the key alone on the axis at y "
        f"{by['ARM'].cy:.0f}. The pitch rules check this; they did not place it."
    )
    notes.append(
        "DIALS, standing note. SPEED and LOAD are cut as two 76 bores for a 3.5in "
        f"movement with an {METER_BEZEL_D:.0f} bezel (Weston 301 class, a hunt). No "
        "stud holes are cut: the pattern is the movement's, MEASURE it and drill "
        "from the part. The 85C1 footprint (METER_85C1) is the documented fallback."
    )
    for dv in DEVICES:
        (bx0, by0_), (bx1, by1_) = _behind_rect(dv)
        if bx0 < LIP or by0_ < LIP or bx1 > w - LIP or by1_ > h - LIP:
            notes.append(
                f"{dv.label}'s body behind the plate ({dv.behind[0]:.0f} x "
                f"{dv.behind[1]:.0f}) reaches behind the wall's land"
            )
    for a, b, gap in _behind_clashes():
        notes.append(
            f"{a.label} and {b.label} share {-gap:.1f}mm behind the plate"
        )

    # -- the chase holds every device with the margin
    for dv in DEVICES:
        if dv.behind[2] + CHASE_MARGIN > CHASE + 1e-9:
            notes.append(f"{dv.label} is {dv.behind[2]:.0f} deep behind the plate; the chase is {CHASE:.0f}")
    notes.append(
        "the three Carbide buttons are cut to their MEASURED holes (E-stop and feed "
        f"hold {CARBIDE_HOLE_22:.2f} -> {BORE_22:.1f}, spindle {CARBIDE_HOLE_19:.2f} -> "
        f"{BORE_19:.1f}); the spindle button is measured behind too ({AV19_FLANGE:.2f} "
        f"flange, {SPINDLE_BEHIND:.2f} deep). The E-stop and feed hold are not: depths "
        f"{ESTOP_BEHIND:.0f} / {FEED_HOLD_BEHIND:.0f} behind the plate are assumptions "
        f"under a chase the {CHASE_DRIVER.label} sets at {CHASE:.0f}. MEASURE THIS: "
        "calipers on those two out of the pendant: flange dia, body W x H x D, panel "
        f"range. Deeper than {CHASE - CHASE_MARGIN:.0f}mm and the chase grows."
    )
    notes.append(
        "PL183.cable_behind is None (params): the mating USB-C plug's straight length "
        f"behind the {27.5:.1f}mm body is not on the sheet. The chase gives it "
        f"{CHASE - 27.5:.0f}mm. MEASURE THIS with the cable that will live there."
    )
    notes.append(
        "all three USB-C cutouts (PENDANT, USB_1, USB_2) are cut as PL183, from the listing's 5-pack. "
        "MEASURE THIS: read the number off the bulkheads; if they are not "
        "PL183 the cutouts are not cut."
    )
    notes.append(
        "UNMODELLED: the screen cable gland. RULED 2026-09-09: the touchscreen's two "
        "cables (HDMI to mini HDMI, USB-A to USB-C, 15ft each) run in the Ergotron "
        "arm's channels and enter the carcass through a gland at the arm mount (J04, "
        "the Carbide monitor-mount location), not through this plate. The SCREEN "
        "coupler that stood at x=254 is gone (branch console-hdmi-bulkhead keeps "
        "the HDMI D-type dead end: the NAHDMI-W takes a 2mm panel)."
    )

    # -- the drawers: exactly those crossing the band, each by exactly K
    ks = narrowed_openings(d)
    narrowed = [s for s in drawers.DRAWERS if s.opening in ks]
    for s in drawers.DRAWERS:
        want = DRAWER_GIVE if s.opening in ks else 0.0
        base = d.s.bay_hands_w - d.s.drawer_slide_build_under
        got = base - drawers.box_size(s, d)[0]
        if abs(got - want) > 1e-6:
            notes.append(f"{s.name} is narrowed by {got:.1f}, not {want:.1f}")
    if len(narrowed) != len(ks):
        notes.append("the narrowed drawer count does not match the openings the cheek carries")
    if CHEEK_TO_DECK and abs(cheek_z(d)[0] - d.deck_top) > 1e-6:
        notes.append(f"the cheek is ruled to the deck and starts at z {cheek_z(d)[0]:.1f}")
    (nx0, nx1), (ny0, ny1) = rib_notch_local(d)
    if nx1 + DADO_FIT / 2 >= (chase_y(d)[1] - chase_y(d)[0]) or ny1 + DADO_FIT / 2 >= RIB_W - ROUTER_D:
        notes.append(
            f"the rib's stile notch ({nx1:.1f} x {ny1:.1f}) leaves under a cutter of rib "
            "beside the stile"
        )
    notes.append(
        f"CONSOLE KEEP-OUT, standing note. The keep-out is the spec's {CONSOLE_KEEPOUT:.0f} "
        f"({CHASE_DRIVER.label} {CHASE_DRIVER.behind[2]:.0f} + {CHASE_MARGIN:.0f}); each "
        f"narrowed drawer gives up DRAWER_GIVE {DRAWER_GIVE:.0f}, the keep-out plus the "
        f"{T:.0f}mm cheek its right slide screws to. The spec narrows by the keep-out "
        "and shifts the slide inboard with it; the cheek is what the slide shifts "
        "onto. Expected, and worth knowing before the drawers are read against the brief."
    )

    # -- the keep-out against the drawers closed and at full extension, the
    # slide members, and the cheek: bbox arithmetic on the plan the parts share
    kx0, kx1 = chase_x(d)
    for s in drawers.DRAWERS:
        x0, y0, bz = drawers.box_origin(s, d)
        bw, bdep, bh = drawers.box_size(s, d)
        clear = drawers.side_clearance(s, d)
        right = x0 + bw + clear          # the slide member's outer face
        zs = (bz, bz + bh)
        z_hit = zs[0] < bz1 and zs[1] > bz0
        for ext, ys in (("closed", (y0, y0 + bdep)), (f"{SLIDE_LEN:.0f}mm out", (y0 - SLIDE_LEN, y0 + bdep))):
            y_hit = ys[0] < by1 and ys[1] > by0
            if z_hit and y_hit and right > kx0 + 1e-9:
                notes.append(
                    f"{s.name} {ext}: its slide reaches x {right:.1f}, into the "
                    f"keep-out that starts at {kx0:.1f}"
                )
        if s.opening in ks:
            cx0 = cheek_x(d)[0]
            if abs(right - cx0) > 1e-6:
                notes.append(
                    f"{s.name}'s right slide member ends at x {right:.1f} and the cheek's "
                    f"bay face is at {cx0:.1f}; the slide has nothing to mount to"
                )

    # -- the crossings: which land in the chase, which come through the pass;
    # none under the cheek's rear edge
    cx0, cx1 = cheek_x(d)
    xs = crossing_x(d)
    in_chase, via_pass = [], []
    for c in CROSSINGS:
        if c.bay != "hands":
            continue
        x = xs[c.label]
        r = BORE_D[c.kind] / 2
        if x - r - BORE_CLEAR_MIN < cx1 and x + r + BORE_CLEAR_MIN > cx0:
            notes.append(
                f"spine crossing {c.label} at x {x:.1f} lands under the cheek's rear "
                f"edge (x {cx0:.1f}..{cx1:.1f}) with less than {BORE_CLEAR_MIN:.0f}mm"
            )
        elif x > cx1:
            in_chase.append(c.label)
        else:
            via_pass.append(c.label)
    px, py = cheek_pass_local(d)
    pass_z = cheek_z(d)[0] + py
    if abs(pass_z - (d.deck_top + ROW_Z["high"])) > 1e-6:
        notes.append("the cheek's pass is not on the spine's high crossing row")
    notes.append(
        "CONSOLE RUNS, standing note. Into the chase directly: "
        + (", ".join(in_chase) or "none")
        + ". Along the spine's front face and through the cheek's pass at "
        f"z {pass_z:.0f}: " + (", ".join(via_pass) or "none")
        + ". Expected, and worth knowing before the harness is cut to length."
    )

    # -- the rib's wall screws stay clear of the cap ties' reach and the leg
    for y in rib_wall_screws_y(d):
        for b in leg_joint.bolts(d):
            if b.wall == 3 and hypot(b.y - y, b.z - (rib_z(d)[0] + T / 2)) < LEG_LAND:
                notes.append(f"a rib screw at y {y:.0f} is inside the land of leg bolt {b.label}")

    # -- the placement is a rotation; assert every bbox
    x_w = wall_inner_x(d)
    want = {
        PART_NAME: ((x_w + T - PLATE_T, x_w + T), (CONSOLE_Y[0], CONSOLE_Y[1]), (z0, z0 + h)),
        CHEEK_NAME: (cheek_x(d), chase_y(d), cheek_z(d)),
        RIB_NAME: (chase_x(d), chase_y(d), rib_z(d)),
        REVEAL_NAME: (reveal_span(d)[0], (d.y_front, d.y_front + PT), reveal_span(d)[1]),
        KEEPOUT_NAME: (chase_x(d), CONSOLE_Y, console_z(d)),
    }
    for label, _group, part in placed_all(d):
        if label not in want:
            continue
        bb = part.bounding_box()
        got = ((bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z))
        for axis, g, e in zip("xyz", got, want[label]):
            if abs(g[0] - e[0]) > 0.05 or abs(g[1] - e[1]) > 0.05:
                notes.append(
                    f"{label} landed at {axis} {g[0]:.1f}..{g[1]:.1f} and belongs at "
                    f"{e[0]:.1f}..{e[1]:.1f}. Its plane is wrong."
                )

    # -- the wall's relief corners show
    notes.append(
        "CONSOLE CORNERS, standing note. The plate's inset is joinery, so the wall's "
        f"relief keeps square corners with four blind {ROUTER_D:.2f}mm reliefs, and "
        "each shows as a crescent at a corner of the plate on the outer face. A "
        "matched-radius corner would hide them (the waterjet cuts it for free); the "
        "rule stands until ruled on. Expected, and worth knowing before the first cut."
    )

    # -- the E-stop's word lands on steel, clear of every flange, and the plate
    # locates on its two end screws on the laser bed. The word is MARKED, not
    # carved; the carve check runs on a stand-in carve VCARVE_D deep so its
    # footprint rules (clear of cuts, inside the plate) still apply.
    notes += callouts.check_callouts(
        callouts.carve(build_plate(d), callouts_local(d), thickness=PLATE_T),
        callouts_local(d),
        register(d),
        size=plate_size(d),
        thickness=PLATE_T,
        keep_clear=[_front_rect(dv) for dv in DEVICES],
        label=PART_NAME,
    )
    notes.append(
        f"{CALLOUT_ESTOP} COLOUR, standing note. The brief v7 reads two ways: one line "
        "makes it 'the only red text on the station', two others say no red labels and no "
        "fill. Built as every legend on this plate is since 2026-09-09: Enduramark black "
        "on brushed stainless, never red; the red budget stays the mushroom and the "
        "mast's Fault state. RULING WANTED: black as built, or red in this one word. "
        "Neither the mark nor the register moves either way."
    )
    return notes


# ====================================================================
# EXPORT
# ====================================================================


def _plate_layers(d: Datums = D) -> dict[str, list[Face]]:
    """``flat_pattern`` off the plate (CUT: the waterjet's), plus the layers
    it cannot infer: E_STOP, the one red bore; MARK, the word the Universal
    lays down in Enduramark; REGISTER, the two holes the plate is located by
    on the laser bed."""
    layers = flat_pattern(build_plate(d))
    est = next(v for v in DEVICES if v.red)
    layers["E_STOP"] = [Circle(est.bore_d / 2).faces()[0].moved(Location((est.cx, est.cy, 0)))]
    marked = callouts.layers(callouts_local(d), register(d), width=plate_size(d)[0])
    layers[MARK_LAYER] = marked.pop(callouts.VCARVE_LAYER)
    layers.update(marked)
    return layers


LAYER_COLOUR = {"E_STOP": ColorIndex.RED}
"""The DXF's E_STOP layer is drawn in the red house.RED reserves for consequence
(the only place this module names it): the shop reads one red circle on the
drawing and knows which bore it is."""
_RED_SWATCH = house.RED


def export(d: Datums = D) -> list:
    """STEP + DXF for the plate (stainless: CUT for the waterjet, MARK for the
    laser, the E-stop bore on E_STOP), the cheek and rib (birch), the reveal
    (acrylic), and STEP alone for the two reference solids."""
    from build123d import ExportDXF

    written = []
    out_dir = EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # the plate, with its colour-tagged layer written by hand so the layer
    # colour survives; export_part's writer takes no colours
    flat = build_plate(d)
    p = out_dir / f"{PART_NAME}.step"
    export_step(flat, p, unit=Unit.MM)
    written.append(p)
    p = out_dir / f"{PART_NAME}.dxf"
    ex = ExportDXF(unit=Unit.MM)
    for layer, faces in _plate_layers(d).items():
        ex.add_layer(layer, color=LAYER_COLOUR.get(layer))
        for f in faces:
            ex.add_shape(f.wires(), layer=layer)
    ex.write(p)
    written.append(p)

    written += export_part(build_cheek(d), CHEEK_NAME)
    written += export_part(build_rib(d), RIB_NAME)
    reveal = build_reveal(d)
    written += export_part(reveal, REVEAL_NAME, layers={"ACRYLIC": flat_pattern(reveal)["CUT"]})
    p = out_dir / f"{KEEPOUT_NAME}.step"
    export_step(build_keepout(d), p, unit=Unit.MM)
    written.append(p)
    return written


# ====================================================================
# REPORT
# ====================================================================

if __name__ == "__main__":
    d = DATUMS
    (y0, y1), (z0, z1) = console_band(d)
    w, h = plate_size(d)
    print(
        f"{PART_NAME}: band y {y0:.0f}..{y1:.0f}, z {z0:.0f}..{z1:.0f} station "
        f"(top set by the {band_bound(d)}); "
        f"plate {w:.0f} x {h:.0f} x {PLATE_T:.0f} ({PLATE_MATERIAL}) flush in the right "
        f"end wall, aperture {aperture_size(d)[0]:.0f} x {aperture_size(d)[1]:.0f}"
    )
    print(
        f"  chase {CHASE:.0f} (driver {CHASE_DRIVER.label} at {CHASE_DRIVER.behind[2]:.0f} + "
        f"{CHASE_MARGIN:.0f}); keep-out {CONSOLE_KEEPOUT:.0f}, drawers give up DRAWER_GIVE {DRAWER_GIVE:.0f}; "
        f"openings narrowed: {narrowed_openings(d)}"
    )
    for dv in DEVICES:
        print(f"  {dv.label:<9} {dv.kind:<7} at ({dv.cx:5.1f}, {dv.cy:5.1f})  {dv.model}")
    for label, mm in leg_bolt_clearance(d):
        print(f"  leg bolt {label}: {mm:.1f}mm of land")
    for line in callouts.describe(callouts_local(d), register(d)):
        print(f"  {line}")
    for n in check_console_plate(d):
        print(f"  - {n}")
    for p in export(d):
        print(f"wrote {p}")
