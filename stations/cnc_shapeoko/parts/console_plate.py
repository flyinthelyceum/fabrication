"""Console plate: the instrument panel inset in the right end wall, and the
chase behind it that the hands-bay drawers give up to make room for it.

Ruling 2026-09-03 (console_location): the console is an INSET PLATE in the
RIGHT END WALL, front region, at hand height. Not on the leg, not above the
drawers. Every run stays inside the carcass; the leg pattern stays free for the
arm; the E-stop sits on a fixed face at the operator's front-right corner.

Ruling 2026-09-03 (console_drawer_overlap): the device depth behind the plate
comes out of the OVERLAPPED DRAWERS' WIDTH. The plate does not move rearward;
every drawer whose Z band crosses the console band is narrowed, its right-hand
slide moves inboard with it, and drawer 1 (CUTTERS, the shallow one) takes the
hit best. The count is computed, not chosen: ``narrowed_openings`` reports
which openings cross the band and ``drawers`` reads it.


WHAT THIS PART OWNS
===================

  * CONSOLE_BAND: the region of the right end wall the console may occupy
  * the plate: 18mm birch, the same sheet as the carcass, set FLUSH with the
    wall's outer face in a rabbeted through-aperture; every device cutout,
    every instrument pocket, the three clear-acrylic panes over the pockets
  * the cutter the right end wall subtracts to receive the plate
    (``wall_cutter``), so the aperture and the plate are one set of numbers
  * the CHASE behind the plate: the air the devices need (``CHASE``), the
    birch that walls it off from the drawers (a cheek, a floor rib) and the
    clear acrylic reveal that closes its front
  * the keep-out the drawers are checked against, as a reference solid, and
    the E-stop module's ALLOCATED envelope inside it
  * ``narrowed_openings`` / ``DRAWER_GIVE``: what the drawers lose

It does NOT own the drawers (``drawers`` narrows itself by reading this file),
the wall (``bay_walls`` subtracts ``wall_cutter``), the spine's crossings
(``spine_panel``; this file only checks that the chase meets them) or the
EMERGENCY STOP callout (C17; ``estop_callout_anchor`` says where it goes).


THE PLATE IS A FLUSH INSET, SCREWED FROM OUTSIDE
================================================

The wall gets a through-aperture the size of the plate's TONGUE and, on its
OUTER face, a rabbet ``DADO_D`` deep the size of the plate's outline. The plate
is 18mm thick: its outer ``DADO_D`` is full outline (the LIP), its inner
``T - DADO_D`` is the tongue that fills the aperture. Outer faces flush, inner
faces flush. Ten screws through the lip into the wall's land, from the outside,
one head type, exposed: the plate comes off the station without touching a
drawer, and the harness comes out with it on its service loop.

Both wall cuts are JOINERY -- a square member seats in them -- so both stay
square and get dogbone reliefs, per the rule in ``through_slot``'s docstring.
The aperture's four reliefs are through and sit under the lip, invisible. The
rabbet's four reliefs are blind, ``DADO_D`` deep, and SHOW as a crescent at
each corner of the plate on the outer face. A matched ``ROUTER_R`` radius on
the plate's corners would hide them; that trades the rule for a look, and the
rule stands until Jared says otherwise. It is flagged in ``check_console_plate``
as a standing note so the crescents are never a surprise on the day.


DEVICES, DEPTHS, AND WHERE THE CHASE'S WIDTH COMES FROM
=======================================================

Every device is a row in ``DEVICES`` with a model number, the cutout it wants,
what it occupies in front of and behind the plate, and where each number came
from. ``CHASE`` is the deepest datasheet depth behind the plate plus
``CHASE_MARGIN``. Today that is the key switch: Schneider quotes the XB4's
Depth as the whole product, head included, and the sheet does not split front
from back, so the whole figure is taken as behind-plate. Conservative by the
head's projection, and it drives the chase honestly rather than by a guess.

The Carbide E-stop module (the Shapeoko 5 Pro power pendant, in hand, GX16
leads) has NO published envelope: Carbide publishes none, the community asked
(thread 58934) and got nothing, and the printable home base is an STL rather
than a drawing. Its row is an ALLOCATION -- the room reserved for it on its
bracket behind the plate -- not a measurement, and ``CONFIDENCE`` says so. It
does not drive ``CHASE``; the check confirms the allocation fits inside the
chase with the margin and reports MEASURE THIS until the pendant is calipered.

The three instruments that read through clear acrylic (meter, state display,
bag bar) are RECESSED: a capsule pocket in the plate's outer face, the
instrument's face under a flush clear pane the size of the pocket, the body
through a bore in the pocket floor. Pocket depth is instrument height plus
``PT``. Capsule, not rectangle, because these are apertures nothing seats in
and a round cutter leaves them that way: the radius is half the pocket's short
side, and the pocket's length is whatever it takes for the instrument's
rectangle to fit inside the capsule (``capsule_for``).

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
from math import hypot, sqrt

from build123d import (
    Align,
    Box,
    Circle,
    ColorIndex,
    Face,
    Location,
    Part,
    Plane,
    Rectangle,
    Unit,
    export_step,
    extrude,
)

from lib import house
from lib.house import GRID, PANEL_T
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_FIT,
    DATUMS,
    EXPORT_DIR,
    GX16_PANEL_D,
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
    rabbet,
    relief,
    screw_positions,
    snap_dn,
    through_slot,
)

__all__ = [
    "PART_NAME",
    "CHEEK_NAME",
    "RIB_NAME",
    "REVEAL_NAME",
    "KEEPOUT_NAME",
    "ESTOP_ENV_NAME",
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
    "capsule_for",
    "build_plate",
    "wall_cutter",
    "build_cheek",
    "build_rib",
    "build_reveal",
    "build_keepout",
    "build_estop_env",
    "panes",
    "placed_all",
    "joint_table",
    "estop_callout_anchor",
    "leg_bolt_clearance",
    "check_console_plate",
    "export",
]

PART_NAME = "console_plate"
CHEEK_NAME = "console_cheek"
RIB_NAME = "console_rib"
REVEAL_NAME = "console_reveal"
KEEPOUT_NAME = "console_keepout"
ESTOP_ENV_NAME = "estop_module_env"
PANE_STEM = "console_pane"

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

CONSOLE_Z0 = GRID * 24
"""Bottom of the band, STATION Z (480 off the floor, 402 above the deck). The
top is derived: see ``console_z``.
SOURCE: task C12 "z from GRID*24". CONFIDENCE: ruling, read as station Z: the
band has to clear the leg insert rows at z 400.05 / 440.18 by a land, which is
the check the task asks for and which is trivial under the other reading; and
read above the deck the band would be 99mm tall, which does not hold two rows
of 22mm bezels at the 40mm pitch Schneider's sheet asks for."""

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
LIP = T
"""Width of the plate's lip, the part that sits in the wall's rabbet and
carries the screws. One thickness, so a screw on the lip's centreline is
``SCREW_EDGE_OFF`` from the plate's edge. Derived."""

LIP_T = DADO_D
"""Thickness of the lip, which is the depth of the wall's outer-face rabbet.
The standard third-of-thickness housing. Derived."""

TONGUE_T = T - LIP_T
"""Thickness of the plate's tongue, the part inside the wall's aperture, and
the wall's land under the rabbet. Derived; 12mm."""

PLATE_SCREW = f"{SCREW_D:.0f} x 16 pan head, the house screw, exposed"
PLATE_SCREW_LEN = 16.0
"""Through a ``LIP_T`` lip into a ``TONGUE_T`` land: 6 + 10 into 12, 2mm short
of the wall's inner face. CONFIDENCE: chosen."""

PLATE_SCREW_PILOT = PLATE_SCREW_LEN - LIP_T
"""Depth of the pilot in the wall's land. Derived; 10mm."""

# -- devices ------------------------------------------------------------
BORE_22 = 22.3
"""Bore for every 22mm-standard device. SOURCE: Schneider XB4 product data
sheets, mounting note (4): "Ø 22.5 mm recommended (Ø 22.3 mm 0/+0.4)". The
task asks for 22.3 and the sheet allows it. CONFIDENCE: datasheet."""

PITCH_22_MIN = 40.0
"""Minimum centre spacing between 22mm devices. SOURCE: the same sheets, note
(2): "40 mm min." CONFIDENCE: datasheet."""

DEVICE_CLEAR = 1.0
"""Air around an instrument inside its pocket, per side. CONFIDENCE: chosen."""

POCKET_FLOOR_MIN = T / 4
"""Least birch left under an instrument pocket: three plies of the 18mm sheet.
The floor is a ledge the instrument's bezel sits on and its studs clamp
through, not a span, and the heaviest thing on any ledge here is a 200g
meter. The meter's own pocket leaves 5mm. CONFIDENCE: chosen."""

CHASE_MARGIN = GRID / 2
"""Air behind the deepest device before the cheek. SOURCE: task C12 "plus
10mm". CONFIDENCE: ruling."""

UPPER_ROW_Y = 78.0
LOWER_ROW_Y = 37.0
"""Plate-local Y of the two 22mm/USB rows (0 at the plate's bottom edge), in a
plate 120 tall whose usable field is LIP..h-LIP = 18..102. The upper row puts
a 47mm XB4 body at 54.5..101.5, half a millimetre inside the land; the lower
row puts the OLED's 33mm body at 20.5..53.5, a millimetre under the XB4s.
CONFIDENCE: chosen, checked by ``check_console_plate``."""

ESTOP_Y = 70.0
PENDANT_Y = 29.0
BAG_BAR_Y = 30.0
"""The E-stop's 60mm allocation is taller than an XB4 body, so its bore sits
lower (allocation 40..100) and the pendant socket and the bag bar under it
sit lower again (19.5..38.5 and 24.9..35.1) to stay out of the allocation.
CONFIDENCE: chosen, checked."""

METER_Y = 50.0
"""Plate-local Y of the meter: its 58mm pocket at 21..79 owns its own X band
at the plate's right, nothing shares that band, and the ToF sits over it.
CONFIDENCE: chosen, checked."""

TOF_Y = 93.0
"""Plate-local Y of the ToF bore, at the plate's top edge: the board's 17.5mm
reaches 101.75, inside the tongue's outline, under the lip's screw line.
CONFIDENCE: chosen."""

ESTOP_ALLOC: tuple[float, float, float] = (GRID * 3.5, GRID * 3, GRID * 3)
"""(W along the plate, H, depth behind the plate) RESERVED for the Carbide
E-stop module on its bracket. NOT a measurement: see the module docstring.
The depth is the brief's own "~60mm behind panel". CONFIDENCE: allocation.
Never drives CHASE; ``check_console_plate`` reports MEASURE THIS."""

XB4_BODY: tuple[float, float] = (30.0, 47.0)
"""(W, H) of a Harmony XB4 complete unit behind the plate, taken as centred on
its bore. SOURCE: every XB4 product data sheet below, Width 30 mm, Height 47
mm. Which way the 47 hangs off the head is not on the sheet; centred is the
reading, and the clash check has a millimetre in hand on it. CONFIDENCE: datasheet
for the figures, assumption for the centring."""

BAR_H = 8.0
"""Height of the LED bargraph package above its pins. Its 25.4 x 10.16 face is
sourced; the height is not on the listings fetched. Drives its pocket depth
and nothing else. CONFIDENCE: assumption."""

GX16_BEHIND = 15.6
"""GX16 panel socket, overall length. SOURCE: Handson Technology GX16 datasheet
https://www.handsontec.com/dataspecs/connector/GX16.pdf mechanical drawing:
socket 15.6 overall, M16x1 thread 8.6 long, flange Ø19, S19 nut. The mating
plug goes in from OUTSIDE, so behind-plate is the socket plus solder tails.
CONFIDENCE: datasheet."""

OLED_BEHIND = 10.0
TOF_BEHIND = 15.0
BAR_BEHIND = 10.0
"""Cable and pin room behind the three PCB-mounted instruments. None of them
approaches the chase driver. CONFIDENCE: assumption."""

PANE_T = PT
"""The panes are the house acrylic, CLEAR by the 2026-09-03 finish ruling."""


@dataclass(frozen=True)
class Device:
    """One console element and everything the plate has to cut for it.

    ``cx``/``cy`` are plate-local, X along station +Y from the plate's front
    edge, Y up from its bottom edge. Every size is mm.

    kind      bore      a round through hole, ``bore_d``
              d_type    a round hole plus two diagonal screw holes (Neutrik D)
              pocket    a capsule pocket ``pocket_depth`` deep from the outer
                        face holding a ``face`` W x H instrument under a clear
                        pane, with ``floor_bore`` (round) or ``floor_slot``
                        (capsule W x H) through the floor
    front     (W, H) the device occupies ON the outer face: bezel or flange
    behind    (W, H, depth) the device occupies behind the plate's inner face,
              centred on (cx, cy); depth measured from the inner face
    red       True for the one device that spends the red budget
    """

    label: str
    model: str
    kind: str
    cx: float
    cy: float
    source: str
    confidence: str
    bore_d: float = 0.0
    face: tuple[float, float] = (0.0, 0.0)
    pocket_depth: float = 0.0
    floor_bore: float = 0.0
    floor_slot: tuple[float, float] = (0.0, 0.0)
    studs: tuple[tuple[float, float], ...] = ()      # (dx, dy) + stud bore d
    stud_d: float = 0.0
    d_holes: tuple[tuple[float, float], ...] = ()    # D-type screw holes (dx, dy)
    d_hole_d: float = 0.0
    front: tuple[float, float] = (0.0, 0.0)
    behind: tuple[float, float, float] = (0.0, 0.0, 0.0)
    red: bool = False

    @property
    def pocket(self) -> tuple[float, float]:
        """(L, H) of the capsule pocket that holds ``face`` with clearance."""
        return capsule_for(self.face[0], self.face[1], DEVICE_CLEAR)


def capsule_for(w: float, h: float, clear: float) -> tuple[float, float]:
    """(length, height) of the smallest capsule whose corner radius is half its
    height and which contains a ``w`` x ``h`` rectangle with ``clear`` around
    it. The rectangle's corner has to lie inside the end semicircle, which is
    what pushes the length past ``w + 2 * clear``."""
    hh = h + 2 * clear
    r = hh / 2
    half_h = h / 2
    if r <= half_h:
        raise ValueError("capsule needs positive clearance")
    return (w + 2 * r - 2 * sqrt(r * r - half_h * half_h), hh)


_SE = "https://www.se.com/us/en/product/{}/ -- product data sheet PDF: "

DEVICES: tuple[Device, ...] = (
    Device(
        "E_STOP", "Carbide 3D Shapeoko 5 Pro power pendant, in hand, GX16 leads; "
        "mounted as a unit on a bracket behind the plate, mushroom through the bore",
        "bore", 60.0, ESTOP_Y,
        "https://community.carbide3d.com/t/need-dimensions-of-so5-power-pendant-and-control-box/58934"
        " (asked, never answered); https://carbide3d.com/3d-print/power-pendant-home-base/"
        " (an STL, no drawing). Carbide publishes no envelope.",
        "bore: datasheet (22mm standard); envelope: allocation, MEASURE THIS",
        bore_d=BORE_22, front=(40.0, 40.0), behind=ESTOP_ALLOC, red=True,
    ),
    Device(
        "ARM", "Schneider Harmony XB4BG21, key switch selector, metal, black, "
        "22mm, key 455, 2 positions stay put, 1 NO",
        "bore", 115.0, UPPER_ROW_Y,
        _SE.format("XB4BG21") + "Mounting diameter 22.5 mm, Height 47 mm, "
        "Width 30 mm, Depth 86 mm (whole product, head included)",
        "chosen; dimensions datasheet",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], 86.0),
    ),
    Device(
        "SPINDLE", "Schneider Harmony ZB4BH033 head (green flush, illuminated, "
        "push-push) on the XB4BW33B5 body (universal LED 24V, 1NO+1NC)",
        "bore", 160.0, UPPER_ROW_Y,
        _SE.format("ZB4BH033") + "'Head for illuminated push button, Harmony XB4, "
        "metal, green flush, 22mm, universal LED, push push'; body figures from "
        + _SE.format("XB4BW33B5") + "Mounting diameter 22.5 mm, Height 47 mm, "
        "Width 30 mm, Depth 57 mm",
        "chosen; dimensions datasheet (body), head swap is in front of the plate",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], 57.0),
    ),
    Device(
        "DUST", "Schneider Harmony XB4BD33, 3-position selector switch, black, "
        "maintained, 2 NO: AUTO / ON / OFF",
        "bore", 205.0, UPPER_ROW_Y,
        _SE.format("XB4BD33") + "Mounting diameter 22.5 mm, Height 47 mm, "
        "Width 30 mm, Depth 68 mm",
        "chosen; dimensions datasheet",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], 68.0),
    ),
    Device(
        "BAG_LAMP", "Schneider Harmony XB4BVB5, pilot light, metal, orange, 22mm, "
        "universal LED, 24V AC/DC (the amber service lamp)",
        "bore", 250.0, UPPER_ROW_Y,
        _SE.format("XB4BVB5") + "Mounting diameter 22.5 mm, Height 47 mm, "
        "Width 30 mm, Depth 54 mm",
        "chosen; dimensions datasheet",
        bore_d=BORE_22, front=(30.0, 30.0), behind=(XB4_BODY[0], XB4_BODY[1], 54.0),
    ),
    Device(
        "LOAD", "85C1 moving-coil panel meter, 0-100 scale (Delixi drawing, the "
        "Adafruit 4404 class of part), recessed under a clear pane",
        "pocket", 327.0, METER_Y,
        "https://cdn-shop.adafruit.com/product-files/4404/C12723-001_datasheet_translate.pdf"
        " -- 85C1-A/V outline: face 64 x 56, bezel 10 thick, body Ø48.5 x 50 "
        "behind the bezel, 2 x M3 studs 52.5 apart 15 below centre",
        "chosen; dimensions datasheet drawing",
        face=(64.0, 56.0), pocket_depth=10.0 + PANE_T, floor_bore=48.5 + 2 * DEVICE_CLEAR,
        studs=((-26.25, -15.0), (26.25, -15.0)), stud_d=3.4,
        front=(0.0, 0.0), behind=(48.5, 48.5, 50.0 - (T - (10.0 + PANE_T))),
    ),
    Device(
        "STATE", "Adafruit 938, Monochrome 1.3in 128x64 OLED, STEMMA QT, "
        "recessed under a clear pane",
        "pocket", 144.0, LOWER_ROW_Y,
        "https://www.adafruit.com/product/938 -- PCB 35.6 x 33 x 6.2 mm, "
        "active area 29.42 x 14.70 mm",
        "chosen; dimensions datasheet",
        face=(35.6, 33.0), pocket_depth=6.2 + PANE_T, floor_slot=(20.0, 8.0),
        behind=(35.6, 33.0, OLED_BEHIND),
    ),
    Device(
        "BAG_BAR", "Kingbright DC-10YWA, 10-segment yellow LED bargraph, "
        "recessed under a clear pane (the bag bar; yellow, never red)",
        "pocket", 92.0, BAG_BAR_Y,
        "https://uk.farnell.com/kingbright/dc-10ywa/array-10-led-yellow-25-4x10-16mm/dp/2290326"
        " -- 25.4 x 10.16 mm package; height see BAR_H",
        "chosen; face datasheet, height assumption",
        face=(25.4, 10.16), pocket_depth=BAR_H + PANE_T, floor_slot=(26.0, 9.6),
        behind=(25.4, 10.16, BAR_BEHIND),
    ),
    Device(
        "PENDANT", "GX16 panel socket, the house connector, pendant port",
        "bore", 60.0, PENDANT_Y,
        "carcass.GX16_PANEL_D; https://www.handsontec.com/dataspecs/connector/GX16.pdf",
        "house standard; depth datasheet",
        bore_d=GX16_PANEL_D, front=(19.0, 19.0), behind=(19.0, 19.0, GX16_BEHIND),
    ),
    Device(
        "USB_1", "PENGLIN PL183 USB-C panel-mount coupler, D-type (params.PL183)",
        "d_type", 192.0, LOWER_ROW_Y,
        "params.SOURCES['PL183']: round 24 cutout, 2 x 3.5 on a 19 x 24 "
        "diagonal, flange 26 x 31 x 2.2, body 27.5 behind the flange",
        "datasheet (C00 capture)",
        bore_d=24.0, d_holes=((-9.5, 12.0), (9.5, -12.0)), d_hole_d=3.5,
        front=(26.0, 31.0), behind=(24.0, 24.0, 27.5),
    ),
    Device(
        "USB_2", "PENGLIN PL183 USB-C panel-mount coupler, D-type (params.PL183)",
        "d_type", 223.0, LOWER_ROW_Y,
        "as USB_1", "datasheet (C00 capture)",
        bore_d=24.0, d_holes=((-9.5, 12.0), (9.5, -12.0)), d_hole_d=3.5,
        front=(26.0, 31.0), behind=(24.0, 24.0, 27.5),
    ),
    Device(
        "SCREEN", "PENGLIN PL183 USB-C panel-mount coupler, D-type: the "
        "touchscreen's video run out to the Ergotron arm (I91)",
        "d_type", 254.0, LOWER_ROW_Y,
        "as USB_1. The third coupler comes from the same 5-pack the listing "
        "sells; PL229 is unresolved (params.PL229) and is not cut for.",
        "datasheet (C00 capture)",
        bore_d=24.0, d_holes=((-9.5, 12.0), (9.5, -12.0)), d_hole_d=3.5,
        front=(26.0, 31.0), behind=(24.0, 24.0, 27.5),
    ),
    Device(
        "TOF", "Adafruit 3967, VL53L1X time-of-flight breakout, behind a 6mm "
        "bore at the plate's top edge",
        "bore", 327.0, TOF_Y,
        "https://www.adafruit.com/product/3967 -- 25.5 x 17.5 x 4.6 mm, FoV 27 deg",
        "chosen; dimensions datasheet",
        bore_d=6.0, front=(6.0, 6.0), behind=(25.5, 17.5, TOF_BEHIND),
    ),
)

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


def tongue_size(d: Datums = D) -> tuple[float, float]:
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
    opening whose Z band crosses CONSOLE_BAND. What ``drawers`` narrows."""
    from stations.cnc_shapeoko.parts.bay_walls import drawer_openings

    z0, z1 = console_z(d)
    out: list[int] = []
    for k, (floor, height) in enumerate(drawer_openings(d)):
        lo = d.deck_top + floor
        hi = lo + height
        if lo < z1 and hi > z0:
            out.append(k)
    return tuple(out)


def cheek_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span of the cheek: the lowest narrowed opening's floor to the
    cap's underside, which it butts."""
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


def reveal_span(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """(x span, z span) of the acrylic reveal: over the chase AND the cheek's
    front edge, from the rib's bottom to the cap, so its screws land in the
    cheek's edge and the rib's end."""
    return ((cheek_x(d)[0], wall_inner_x(d)), (rib_z(d)[0], d.top_z[0]))


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


def _capsule_face(cx: float, cy: float, length: float, height: float) -> Face:
    """A capsule outline as a flat face at Z = 0, for the DXF layers."""
    r = height / 2
    sk = Rectangle(max(length - 2 * r, 1e-6), height)
    sk = sk + Circle(r).moved(Location((length / 2 - r, 0, 0))) + Circle(r).moved(
        Location((-(length / 2 - r), 0, 0))
    )
    return sk.faces()[0].moved(Location((cx, cy, 0)))


def lip_screws(d: Datums = D) -> list[tuple[float, float]]:
    """Plate-local centres of the lip screws: the carcass rhythm along the two
    long edges, one at the middle of each short edge."""
    w, h = plate_size(d)
    e = LIP / 2
    out: list[tuple[float, float]] = []
    for p in screw_positions(w, pitch=SCREW_PITCH, inset=SCREW_END_INSET):
        out.append((p, e))
        out.append((p, h - e))
    out.append((e, h / 2))
    out.append((w - e, h / 2))
    return out


def _pocket_cutter(dv: Device) -> Part:
    """The capsule pocket alone, floor at ``T - pocket_depth``, running out
    through the outer face."""
    length, height = dv.pocket
    depth = dv.pocket_depth
    # through_slot built for a ``depth`` thick panel spans z -depth..2*depth;
    # lifted by T its bottom face is the pocket floor at T - depth and its top
    # runs out the outer face
    c = through_slot((0.0, 0.0), length, height, thickness=depth, corner_r=height / 2)
    return c.moved(Location((dv.cx, dv.cy, T)))


def build_plate(d: Datums = D) -> Part:
    """The plate, flat, plate-local. Z = 0 is the inner face, Z = T the outer
    face the operator reads."""
    w, h = plate_size(d)
    p = panel(w, h)

    # the lip: take the ring off the BACK face, TONGUE_T deep, LIP wide,
    # counter-clockwise so "left" of each run is the inside of the outline
    for a, b in (((0.0, 0.0), (w, 0.0)), ((w, 0.0), (w, h)), ((w, h), (0.0, h)), ((0.0, h), (0.0, 0.0))):
        p -= rabbet(a, b, width=LIP, depth=TONGUE_T, side="back", toward="left")

    # the lip screws, through
    for x, y in lip_screws(d):
        p -= bore(x, y, SCREW_CLEAR_D)

    # the devices
    for dv in DEVICES:
        if dv.kind == "pocket":
            p -= _pocket_cutter(dv)
            if dv.floor_bore:
                p -= bore(dv.cx, dv.cy, dv.floor_bore)
            if dv.floor_slot != (0.0, 0.0):
                sl, sh = dv.floor_slot
                p -= through_slot((dv.cx, dv.cy), sl, sh, corner_r=sh / 2)
            for dx, dy in dv.studs:
                p -= bore(dv.cx + dx, dv.cy + dy, dv.stud_d)
        else:
            p -= bore(dv.cx, dv.cy, dv.bore_d)
            for dx, dy in dv.d_holes:
                p -= bore(dv.cx + dx, dv.cy + dy, dv.d_hole_d)
    return p


def wall_cutter(d: Datums = D) -> Part:
    """What the right end wall loses to the console, in STATION coordinates,
    for ``bay_walls`` to bring into its own frame and subtract.

    JOINERY, both cuts, so square with dogbones: the through-aperture the
    tongue fills, and the outer-face rabbet the lip sits in. Both ``DADO_FIT``
    oversize, the way every housing in the carcass is. Plus the ten pilots for
    the lip screws, blind from the outer face.
    """
    w, h = plate_size(d)
    tw, th = tongue_size(d)
    cx, cy = w / 2, h / 2
    cut: Part | None = None

    def add(c: Part) -> None:
        nonlocal cut
        cut = c if cut is None else cut + c

    # through aperture, tongue + fit, square, four through reliefs
    aw, ah = tw + DADO_FIT, th + DADO_FIT
    add(through_slot((cx, cy), aw, ah))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(relief(cx + sx * aw / 2, cy + sy * ah / 2))

    # outer-face rabbet, outline + fit, LIP_T deep from the outer face
    rw, rh = w + DADO_FIT, h + DADO_FIT
    over = T
    rab = Box(rw, rh, LIP_T + over, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((cx, cy, T - LIP_T))
    )
    add(rab)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(relief(cx + sx * rw / 2, cy + sy * rh / 2, depth=LIP_T, side="front"))

    # lip screw pilots, blind from the outer face into the land
    for x, y in lip_screws(d):
        add(bore(x, y, SCREW_PILOT_D, depth=LIP_T + PLATE_SCREW_PILOT, side="front"))

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
    the cheek."""
    y0, y1 = chase_y(d)
    return panel(y1 - y0, RIB_W)


def build_reveal(d: Datums = D) -> Part:
    """The clear acrylic reveal over the chase's front, flat, reveal-local:
    local X = station X from the cheek's outer face, local Y up. Three
    clearance holes: two into the cheek's front edge, one into the rib's end."""
    (x0, x1), (z0, z1) = reveal_span(d)
    w, h = x1 - x0, z1 - z0
    p = panel(w, h, PT)
    cx = T / 2                                   # the cheek's centreline
    for y in (h * 0.3, h * 0.8):
        p -= bore(cx, y, REVEAL_SCREW_D, thickness=PT)
    p -= bore(T + RIB_W / 2, T / 2, REVEAL_SCREW_D, thickness=PT)   # the rib's end
    return p


def build_keepout(d: Datums = D) -> Part:
    """The chase air the drawers are checked against, in STATION coordinates,
    less the E-stop module's allocation so the two reference solids do not
    share volume."""
    x0, x1 = chase_x(d)
    (y0, y1), (z0, z1) = console_band(d)
    box = Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3).moved(
        Location((x0, y0, z0))
    )
    return box - build_estop_env(d)


def build_estop_env(d: Datums = D) -> Part:
    """The E-stop module's ALLOCATED envelope behind its bore, station
    coordinates. An allocation, never a measurement; see the docstring."""
    dv = next(v for v in DEVICES if v.red)
    w, h, dep = dv.behind
    x1 = wall_inner_x(d)
    y = CONSOLE_Y[0] + dv.cx
    z = plate_z(d)[0] + dv.cy
    return Box(dep, w, h, align=(Align.MAX, Align.CENTER, Align.CENTER)).moved(
        Location((x1, y, z))
    )


def panes(d: Datums = D) -> list[tuple[str, Device, Part]]:
    """(label, device, flat pane) for each recessed instrument: the pocket's
    capsule outline, ``PANE_T`` thick, drawn flat at Z = 0."""
    out: list[tuple[str, Device, Part]] = []
    for dv in DEVICES:
        if dv.kind != "pocket":
            continue
        length, height = dv.pocket
        face = _capsule_face(0.0, 0.0, length, height)
        out.append((f"{PANE_STEM}_{dv.label.lower()}", dv, extrude(face, amount=PANE_T)))
    return out


def _pane_plane(dv: Device, d: Datums = D) -> Plane:
    """A pane sits in its pocket, flush with the outer face."""
    base = plate_plane(d)
    return Plane(
        origin=base.origin + base.x_dir * dv.cx + base.y_dir * dv.cy + base.z_dir * (T - PANE_T),
        x_dir=base.x_dir,
        z_dir=base.z_dir,
    )


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, placed solid) for everything this module puts in the
    assembly: birch, acrylic, and the two reference solids."""
    out: list[tuple[str, str, Part]] = [
        (PART_NAME, "carcass", plate_plane(d) * build_plate(d)),
        (CHEEK_NAME, "carcass", cheek_plane(d) * build_cheek(d)),
        (RIB_NAME, "carcass", rib_plane(d) * build_rib(d)),
        (REVEAL_NAME, "acrylic", reveal_plane(d) * build_reveal(d)),
        (KEEPOUT_NAME, "reference", build_keepout(d)),
        (ESTOP_ENV_NAME, "reference", build_estop_env(d)),
    ]
    for label, dv, pane in panes(d):
        out.append((label, "acrylic", _pane_plane(dv, d) * pane))
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples for
    ``assembly.joints``. The plate and the panes are housed; everything else
    in the chase meets on faces."""
    from stations.cnc_shapeoko.parts.bay_walls import WALLS

    wall = WALLS[3].name
    x0 = wall_inner_x(d)
    out: list[tuple] = [
        (wall, PART_NAME, "housing", "x", x0, x0 + T,
         "plate's tongue and lip in the wall's aperture and rabbet"),
        (PART_NAME, KEEPOUT_NAME, "bearing", None, 0.0, 0.0,
         "the chase air starts at the plate's inner face"),
        (PART_NAME, ESTOP_ENV_NAME, "bearing", None, 0.0, 0.0,
         "the module's bracket hangs off the plate's inner face"),
        (KEEPOUT_NAME, ESTOP_ENV_NAME, "bearing", None, 0.0, 0.0,
         "the allocation is subtracted from the air"),
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
        ("spine_panel", CHEEK_NAME, "butt", None, 0.0, 0.0,
         "cheek's rear edge on the spine's front face; the spine cuts nothing"),
        ("spine_panel", RIB_NAME, "butt", None, 0.0, 0.0, "rib's rear end on the spine"),
        (CHEEK_NAME, REVEAL_NAME, "butt", None, 0.0, 0.0,
         "reveal on the cheek's front edge, screwed into it"),
        (RIB_NAME, REVEAL_NAME, "butt", None, 0.0, 0.0, "reveal on the rib's front end"),
        (wall, REVEAL_NAME, "butt", None, 0.0, 0.0, "reveal beside the wall's front edge"),
    ]
    for label, dv, _pane in panes(d):
        out.append(
            (PART_NAME, label, "housing", "x", x0 + T - dv.pocket_depth, x0 + T,
             f"{dv.label} pane flush in its pocket")
        )
    return out


def estop_callout_anchor(d: Datums = D) -> tuple[float, float]:
    """Plate-local centre for C17's EMERGENCY STOP callout: under the mushroom
    guard, above the pendant socket's flange. The one red text on the station
    is cut here; this file cuts no text."""
    dv = next(v for v in DEVICES if v.red)
    below = next(v for v in DEVICES if v.label == "PENDANT")
    top = below.cy + below.front[1] / 2
    bottom = dv.cy - dv.front[1] / 2
    return (dv.cx, (top + bottom) / 2)


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
    own ceiling, sampled along the band). The rabbet is ``LIP_T`` deep and the
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
    """What the device occupies on the outer face: its bezel/flange, or the
    pocket for a recessed instrument."""
    if dv.kind == "pocket":
        w, h = dv.pocket
    else:
        w, h = max(dv.front[0], dv.bore_d), max(dv.front[1], dv.bore_d)
    return ((dv.cx - w / 2, dv.cy - h / 2), (dv.cx + w / 2, dv.cy + h / 2))


def _cut_rect(dv: Device) -> tuple[tuple[float, float], tuple[float, float]]:
    """What the plate actually loses to the device on its outer face: the
    pocket, or the bore and its screw holes. The web rule is about the birch
    between CUTS; a flange lying on the face is not a cut."""
    if dv.kind == "pocket":
        w, h = dv.pocket
        return ((dv.cx - w / 2, dv.cy - h / 2), (dv.cx + w / 2, dv.cy + h / 2))
    x0 = x1 = dv.cx
    y0 = y1 = dv.cy
    r = dv.bore_d / 2
    x0, x1, y0, y1 = x0 - r, x1 + r, y0 - r, y1 + r
    for dx, dy in dv.d_holes:
        hr = dv.d_hole_d / 2
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
    tw, th = tongue_size(d)
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

    # -- 22mm bores are 22.3, every rectangular cutout is a capsule, one red
    reds = [dv for dv in DEVICES if dv.red]
    if len(reds) != 1:
        notes.append(f"{len(reds)} devices are tagged red; the E-stop is the budget")
    for dv in DEVICES:
        if dv.kind == "bore" and dv.front == (30.0, 30.0) and abs(dv.bore_d - BORE_22) > 0.05:
            notes.append(f"{dv.label} is a 22mm device bored {dv.bore_d:.2f}")
        if dv.kind == "pocket":
            length, height = dv.pocket
            if length < height:
                notes.append(f"{dv.label} pocket is taller than it is long; the capsule turns")
            if T - dv.pocket_depth < POCKET_FLOOR_MIN - 1e-9:
                notes.append(
                    f"{dv.label} pocket is {dv.pocket_depth:.1f} deep in an {T:.0f} plate, "
                    f"leaving {T - dv.pocket_depth:.1f} under the {POCKET_FLOOR_MIN:.1f} floor"
                )
            if dv.floor_slot != (0.0, 0.0) and dv.floor_slot[0] < dv.floor_slot[1]:
                notes.append(f"{dv.label} floor slot is taller than it is long")

    # -- devices on the face: at least a cutter web between neighbours, and
    # 22mm devices at the maker's pitch
    for i, a in enumerate(DEVICES):
        for b in DEVICES[i + 1:]:
            gap = _rect_gap(_cut_rect(a), _cut_rect(b))
            if gap < ROUTER_D:
                notes.append(
                    f"{a.label} and {b.label} are cut {gap:.1f}mm apart on the plate's "
                    f"face, under a {ROUTER_D:.2f}mm web"
                )
            if _rect_gap(_front_rect(a), _front_rect(b)) < 0:
                notes.append(f"{a.label} and {b.label} overlap on the plate's outer face")
            if a.front == (30.0, 30.0) and b.front == (30.0, 30.0):
                pitch = hypot(a.cx - b.cx, a.cy - b.cy)
                if pitch < PITCH_22_MIN:
                    notes.append(
                        f"{a.label} and {b.label} are {pitch:.0f}mm apart, under the "
                        f"{PITCH_22_MIN:.0f}mm the XB4 sheet asks for"
                    )
    for dv in DEVICES:
        (fx0, fy0), (fx1, fy1) = _front_rect(dv)
        if fx0 < LIP or fy0 < LIP or fx1 > w - LIP or fy1 > h - LIP:
            notes.append(f"{dv.label} reaches onto the plate's lip on the outer face")
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
        f"the Carbide E-stop module's envelope is not measured: {ESTOP_ALLOC[0]:.0f} x "
        f"{ESTOP_ALLOC[1]:.0f} x {ESTOP_ALLOC[2]:.0f} behind the plate is an ALLOCATION "
        f"on its bracket, {CHASE - ESTOP_ALLOC[2]:.0f}mm inside a chase the "
        f"{CHASE_DRIVER.label} sets at {CHASE:.0f}. MEASURE THIS: calipers on the "
        "pendant, W x H x D and where the mushroom sits on its face. If it is deeper "
        f"than {CHASE - CHASE_MARGIN:.0f}mm the chase grows and every narrowed drawer "
        "narrows again."
    )
    notes.append(
        "PL183.cable_behind is None (params): the mating USB-C plug's straight length "
        f"behind the {27.5:.1f}mm body is not on the sheet. The chase gives it "
        f"{CHASE - 27.5:.0f}mm. MEASURE THIS with the cable that will live there."
    )
    notes.append(
        "PL229 is unresolved (params.PL229, no listing carries it): all three "
        "USB-C cutouts are PL183 from the listing's 5-pack. MEASURE THIS: read the "
        "number off the second bulkhead; if it is not a PL183 its cutout is not cut."
    )
    notes.append(
        f"BAG_BAR height is an assumption ({BAR_H:.0f}mm) and sets only its pocket depth. "
        "MEASURE THIS on the part or its Kingbright sheet; the pane sits proud if it is taller."
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
        notes.append("the narrowed drawer count does not match the openings crossing the band")
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
        PART_NAME: ((x_w, x_w + T), (CONSOLE_Y[0], CONSOLE_Y[1]), (z0, z0 + h)),
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

    # -- the wall's rabbet corners show
    notes.append(
        "CONSOLE CORNERS, standing note. The plate's inset is joinery, so the wall's "
        f"rabbet keeps square corners with four blind {ROUTER_D:.2f}mm reliefs, and "
        "each shows as a crescent at a corner of the plate on the outer face. A "
        "matched-radius corner would hide them; the rule stands until ruled on. "
        "Expected, and worth knowing before the first cut."
    )
    return notes


# ====================================================================
# EXPORT
# ====================================================================


def _plate_layers(d: Datums = D) -> dict[str, list[Face]]:
    """``flat_pattern`` plus the two layers it cannot infer: E_STOP, the one
    red bore, and ACRYLIC, the three pane outlines the laser cuts."""
    layers = flat_pattern(build_plate(d))
    est = next(v for v in DEVICES if v.red)
    layers["E_STOP"] = [Circle(est.bore_d / 2).faces()[0].moved(Location((est.cx, est.cy, 0)))]
    layers["ACRYLIC"] = [_capsule_face(dv.cx, dv.cy, *dv.pocket) for dv in DEVICES if dv.kind == "pocket"]
    return layers


LAYER_COLOUR = {"E_STOP": ColorIndex.RED}
"""The DXF's E_STOP layer is drawn in the red house.RED reserves for consequence
(the only place this module names it): the shop reads one red circle on the
drawing and knows which bore it is."""
_RED_SWATCH = house.RED


def export(d: Datums = D) -> list:
    """STEP + DXF for the plate (birch on CUT, panes on ACRYLIC, the E-stop
    bore on E_STOP), the cheek and rib (birch), the reveal and the panes
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
    for label, _dv, pane in panes(d):
        written += export_part(pane, label, layers={"ACRYLIC": flat_pattern(pane)["CUT"]})
    for name, solid in ((KEEPOUT_NAME, build_keepout(d)), (ESTOP_ENV_NAME, build_estop_env(d))):
        p = out_dir / f"{name}.step"
        export_step(solid, p, unit=Unit.MM)
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
        f"plate {w:.0f} x {h:.0f} x {T:.0f} flush in the right end wall, tongue "
        f"{tongue_size(d)[0]:.0f} x {tongue_size(d)[1]:.0f}"
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
    for n in check_console_plate(d):
        print(f"  - {n}")
    for p in export(d):
        print(f"wrote {p}")
