"""Signal mounts: the exposed side of the brain band, laid out on one subplate.

WHAT THIS PART IS
=================

One birch subplate, a birch-and-acrylic cradle, a short DIN rail, ONE printed
bracket, and a set of reference solids. Everything on the signal side of the
partition mounts to the subplate and nothing mounts to the spine, so the whole
side comes off as one unit the way the mains backplate does on the sealed side.

``signal_subplate``       18mm Baltic birch, flat on the spine's REAR face
                          between the partition and the right end wall, in the
                          band of spine BETWEEN the two crossing rows so every
                          GX16 and the pendant gland stay reachable with a
                          spanner. The mirror of ``mains_backplate`` across the
                          partition.

``mini_pc_cradle_*``      A birch shelf on the subplate's device face, two
                          birch cheeks, and a CLEAR acrylic lip on the shelf's
                          door edge. The PC stands UPRIGHT on the shelf on
                          its 37mm-flat profile, its big face looking at the
                          rear door's reveal and its rear ports looking at the
                          subplate across ``CABLE_ROOM``. Every cradle
                          dimension is arithmetic on ``params.mini_pc_env``:
                          the Lenovo ThinkStation P350 Tiny (RT3), a fitted
                          cradle, not a reserved seat.

``mini_pc_env``           The PC as a reference solid on the shelf. Its
                          projection onto the door plane is checked against
                          the reveal window's outline: a student looking in
                          through the clear pane sees the computer.

``din_rail_signal``       One short EN 60715 TH35 rail on the subplate, as a
                          top-hat profile rather than a box, because the one
                          thing that clips to it is the one part in the
                          station that is 3D printed and the clip's hooks have
                          to be shown reaching behind the flanges.

``esp32_carrier``         The PRINTED part. A flat carrier with a fixed hook
                          and a latch that snap over the rail and a flat front
                          face with four heat-set inserts for the station
                          controller's protoboard. Printed front face down,
                          hooks up. ``export`` writes its STL through
                          ``lib.house.export_stl``, which refuses a part that
                          does not fit ``PRINT_BED_MIN`` with the house margin.

``esp32_board_env``       The protoboard and the ESP32 on it, as a reference
                          solid standing off the carrier's front face.

``motion_controller_env`` The Carbide Motion controller, placed ONLY when
                          ``params.motion_controller_env`` carries a number.
                          It is None today (C00: Carbide publishes no envelope
                          and the community figure is a lead, not a datasheet)
                          so nothing is placed and nothing is cut for its feet;
                          the subplate reserves ``controller_seat`` for it and
                          ``check_signal_mounts`` carries the measurement.

WHERE THINGS SIT, AND WHY
=========================

The layout is three horizontal bands on the subplate, read from the top:

    TOP      the PC. Its shelf sits so the PC's rear ports are at the height
             of the partition's transit, which is where the brick's DC lead
             arrives from the sealed side: the shortest run on the signal
             side is the one carrying the computer's power. The cradle's X is
             DERIVED from the reveal window, not chosen: it is the leftmost
             position at which the PC's left edge clears the window's left
             edge by ``PC_WINDOW_MARGIN``.
    MIDDLE   the rail and the ESP32 carrier at the LEFT, under the transit,
             so the CT lead and the ESP32's supply land on the board
             without crossing anything.
    BOTTOM   the controller's seat: the whole width of the plate, from its
             bottom edge up to a service gap under the rail band, and as deep
             as the band allows to the door's landing.

The always-live rule (C05, I60) is not geometry and is checked as text: the PC
brick and the ESP32 supply are on ``mains_backplate``'s ALWAYS-LIVE rail and
absent from its CONTACTOR rail, and this module's check reads that module's
table rather than repeating it. Guards kill motion and cutting, never compute.

AIRFLOW
=======

The top cap's exhaust field stops at the partition by ``Datums.brain_exhaust_x``:
there are no slots over the signal side by construction, so nothing here can
block one. The check still asks the question of ``top_cap.vent_field`` rather
than of this paragraph, and it holds every solid on this side at least a
``SERVICE_GAP`` under the cap.

THE JOINTS
==========

    subplate front face   flat on the spine's rear face, screwed through,
                          counterbored on the DEVICE face. The spine cuts
                          nothing: blind pilots at assembly, between the rows.
    shelf rear edge       end grain on the subplate's device face. Screwed
                          THROUGH the subplate from its spine face into the
                          shelf, counterbored on the SPINE face so the plate
                          still lands flat. The subplate is assembled on the
                          bench with its cradle on, then hung as one.
    cheek rear edge       same fixing, one screw each.
    cheek bottom edge     on the shelf's top face, screwed up through the shelf.
    lip                   PT clear acrylic on the shelf's front edge, two
                          exposed pan heads into the end grain. Clear, so it
                          retains the PC without hiding it.
    rail                  screwed to the subplate through its own slots,
                          pilots at assembly. Reference solid.
    carrier               hooks behind the rail's flanges. Faces only.
    board                 bears on the carrier's front and the plate's face.

WHAT IS MEASURED, WHAT IS NOT
=============================

The PC is the Lenovo P350 Tiny (``params.mini_pc_env``, datasheet).
The rail is a standard. The protoboard and its hole pattern are
REPRESENTATIVE (no SKU, no board named) and the check carries them as MEASURE;
none of them moves the subplate. The controller is None and drives nothing.

PANEL CONVENTION
================

Subplate drawn flat like the mains backplate: local origin at its lower-left
corner as seen from the REAR of the station, local +X to station +X, local +Y
up, local +Z through the thickness from the DEVICE face (Z = 0) to the spine
face (Z = t). The shelf is drawn flat on the deck convention (+X station X,
+Y station +Y, +Z up). The cheeks are drawn flat on the wall convention
(+X station Y, +Y up, thickness into +X). The lip is drawn flat like the
subplate. The carrier is drawn in its PRINT orientation: X and Y the bed,
Z = 0 the front (board) face, hooks rising in +Z; placed so print +Z runs
into station -Y, toward the plate. Rail and envelopes are built directly in
STATION coordinates, because they are placed, never cut.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import Align, Box, Location, Part, Plane

from lib.house import (
    GRID,
    PRINT_BED_MARGIN,
    PRINT_BED_MIN,
    QUARTER,
    SHEET_4X8,
    export_stl,
    fits,
    printable,
)
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    PT,
    SCREW_CBORE_D,
    SCREW_CLEAR_D,
    SCREW_EDGE_OFF,
    SCREW_PILOT_D,
    SERVICE_GAP,
    Datums,
    bore,
    export_part,
    panel,
    screw_positions,
    snap_dn,
    snap_up,
)
from stations.cnc_shapeoko import params
from stations.cnc_shapeoko.parts import brain_partition, mains_backplate, rear_door, top_cap
from stations.cnc_shapeoko.parts.spine_panel import (
    BORE_CLEAR_MIN,
    BORE_D,
    CROSSINGS,
    ROW_HIGH_Z,
    ROW_LOW_Z,
    ROW_Z,
    crossing_x,
    signal_x,
)

PART_NAME = "signal_subplate"
SHELF_NAME = "mini_pc_cradle_shelf"
CHEEK_STEM = "mini_pc_cradle_cheek"
LIP_NAME = "mini_pc_cradle_lip"
PC_NAME = "mini_pc_env"
RAIL_NAME = "din_rail_signal"
CARRIER_NAME = "esp32_carrier"
BOARD_NAME = "esp32_board_env"
CONTROLLER_NAME = "motion_controller_env"

D: Datums = DATUMS


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# Shared boundaries come from Datums, the crossings from spine_panel, the
# transit from brain_partition, the window from rear_door, the rail set
# from mains_backplate, the PC and the controller from params, material
# and the print bed from house.
# ====================================================================

PLATE_T = D.t
"""Subplate thickness. SOURCE: task C13 spec, "a birch subplate (carcass_t)".
CONFIDENCE: ruling. Same stock as the mains backplate across the partition,
for the same reason: it takes wood screws for a shelf, two cheeks and a rail."""

ROW_CLEAR = mains_backplate.ROW_CLEAR
"""Plate edge to the centre of the nearest crossing row. SOURCE:
mains_backplate.ROW_CLEAR, so both plates leave the same spanner room on
the spine's rear face. CONFIDENCE: design, by reuse. The signal row's GX16
S19 nuts and the pendant's M20 gland nut want the same swing."""

END_CLEAR = GRID * 2
"""Plate's right end to the right end wall's inner face. SOURCE: design, on
the grid. CONFIDENCE: design. The end wall drives screws along X into the
spine's end grain (bay_walls._spine_screws) and the plate's own screw column
sits SCREW_EDGE_OFF in from its end; two modules keep the column outside a
40mm screw's reach. The left end takes no such clearance: the partition is a
housed panel, not a fastened one, and the plate snaps up off its face."""

# ---- the PC and its cradle ---------------------------------------------
PC_ENV = params.STATION.mini_pc_env
"""(W across X, D into the band, H up) of the PC standing upright. SOURCE:
params.mini_pc_env, the Lenovo ThinkStation P350 Tiny, CONFIDENCE datasheet
(PSREF). Stood on its 37mm flat profile so it reaches only 36.5 into the brain
band and shows its 179 x 182.9 face through the reveal. Every cradle number
below is arithmetic on it."""

CABLE_ROOM = GRID * 2
"""Air between the subplate's face and the PC's rear. SOURCE: design, on the
grid. CONFIDENCE: design. The rear carries the DC jack, HDMI and RJ45; a
straight HDMI plug and its bend want 40mm, and the brick's lead arrives here
from the transit."""

PC_SIDE_CLEAR = GRID / 2
"""PC side to cheek, per side. SOURCE: design. CONFIDENCE: design. 10mm of
air each side and a low cheek locate the standing PC without pinching its
side vents; it cannot walk sideways."""

PC_FRONT_CLEAR = GRID / 2
"""PC front to the lip. CONFIDENCE: design. Room for a finger on the power
button's edge and for the chassis's own tolerance."""

CHEEK_T = D.t
SHELF_T = D.t
"""Cheeks and shelf are carcass stock. CONFIDENCE: ruling by reuse."""

CHEEK_H = GRID * 2
"""Cheek height above the shelf's top. SOURCE: design, on the grid.
CONFIDENCE: design. A low cheek at the base of the upright PC: it locates
the foot and lets the tall face stand clear above it."""

LIP_T = PT
LIP_MATERIAL = "clear acrylic 3mm"
"""The door-edge lip is the reveal material. SOURCE: finish ruling 2026-09-03
(every reveal is CLEAR) applied to the one part of the cradle that stands
between the PC and the pane: a birch lip would hide the bottom of the
computer the window exists to show. CONFIDENCE: ruling (material), design
(the lip). A laser part, the QUARTER blank."""

LIP_H_ABOVE = CHEEK_H
"""Lip height above the shelf's top, matching the cheeks. CONFIDENCE: design."""

LIP_SCREW = "5 x 12 pan head, the house screw, exposed"
LIP_SCREW_D = SCREW_CLEAR_D
LIP_PILOT_D = SCREW_PILOT_D
LIP_PILOT_DEPTH = 12.0 - PT
"""Two through the lip into the shelf's front end grain. SOURCE: rear_door's
pane fixing. CONFIDENCE: chosen."""

PC_WINDOW_MARGIN = GRID / 2
"""How far inside the reveal window's outline the PC's projection must lie.
SOURCE: task C13 acceptance ("its projection onto the door plane lies inside
the reveal window outline"), with a margin so the check is not decided at the
pane's edge. CONFIDENCE: spec. This number and the window DERIVE the cradle's
X on the plate; nothing chooses it."""

CRADLE_CARRIER_GAP = GRID / 8
"""Running clearance between the cradle shelf's underside and the printed
carrier's top. SOURCE: design. CONFIDENCE: design. The P350 stands 182.9 tall
on its 37mm flat profile (RT3) and the cradle sits directly above the carrier
in the same X band under the reveal window, so the shelf has to miss the
carrier by this much. The band between the carrier's top and the window's
top-margin is tight (about 3mm of play at 12mm stock), so this is small; the
window fit and the cap clearance are checked in ``check_signal_mounts``."""

# ---- the rail and the printed carrier ----------------------------------
RAIL_H = mains_backplate.RAIL_H
RAIL_D = mains_backplate.RAIL_D
RAIL_T = 1.0
RAIL_CROWN_W = 27.0
"""EN 60715 TH35-7.5 top-hat: 35 across the flange tips, 7.5 off the mounting
face, 1.0 sheet, crown 27 across outside. SOURCE: EN 60715 (IEC 60715), the
same rail mains_backplate mounts; the crown width and sheet from the same
figure. CONFIDENCE: standard. Modelled as the profile rather than a box
because the carrier's hooks reach behind the flanges."""

RAIL_X_LOCAL = GRID
RAIL_LEN = GRID * 7
"""Rail start from the plate's left edge and its length. SOURCE: design, on
the grid. CONFIDENCE: design. One carrier of CARRIER_W plus a module of rail
each side for the fingers and a second clip-on later; the transit is above
its left end."""

RAIL_Y_LOCAL = GRID * 8
"""Rail centreline above the plate's bottom edge. SOURCE: design, on the
grid. CONFIDENCE: design. Under the cradle and over the controller's seat.
Dropped from GRID*10 to GRID*8 (RT3, 2026-09-04): the upright P350 cradle
stacks directly above the carrier under the reveal, and the P350's big face is
nearly as wide as the window, so its top corners have to stay clear of the
window's rounded corners; lowering the rail lowers the whole cradle enough to
clear both the carrier and those corners while the seat below stays ample."""

CARRIER_MATERIAL = "PLA, 0.2mm layers, 4 walls, printed front face down"
BOARD = (70.0, 50.0)
BOARD_HOLE_INSET = 2.5
BOARD_HOLE_D = 2.5
"""(along the rail, across it) of the station controller's protoboard, and
its corner hole pattern. SOURCE: the common stocked 7 x 5cm double-sided
protoboard; the ESP32-DevKitC (55 x 28, Espressif) sits on it with headers.
CONFIDENCE: REPRESENTATIVE, MEASURE THIS against the board actually in hand
(BOM: "ESP32 station controller, printed DIN-clip carrier, stocked"). Drives
the carrier's outline and insert pattern only, and the carrier is the
cheapest part in the station to re-print."""

CARRIER_MARGIN = 5.0
"""Carrier outline beyond the board, each side. CONFIDENCE: design."""

BASE_T = 6.0
"""Carrier base thickness. SOURCE: design. CONFIDENCE: design. Deep enough
for a short M3 heat-set insert with a floor under it, stiff enough that the
hooks are the flexure, not the base."""

INSERT = "M3 heat-set insert, 4.0 OD x 4.0 long, the BOM's 'heat-set inserts' line"
INSERT_HOLE_D = 4.0
INSERT_HOLE_DEPTH = 4.5
"""Insert pilot in the printed base. SOURCE: representative M3 x 4 brass
heat-set (4.0mm body; printed pilot at the body diameter is the convention,
the insert displaces the wall). CONFIDENCE: representative. MEASURE THIS
against the inserts in the drawer."""

STANDOFF_H = 6.0
STANDOFF = "M3 x 6 nylon female-female standoff, four"
"""Board off the carrier's face. SOURCE: design. CONFIDENCE: design. Solder
side clear of the print."""

BOARD_STACK_H = 20.0
"""Board plus the ESP32 on headers plus the tallest thing on it, off the
board's top. SOURCE: ESP32-DevKitC on stacked headers, about 18. CONFIDENCE:
representative; sizes one reference solid."""

HOOK_L = GRID * 2
HOOK_RIB_T = 2.5
HOOK_LIP_T = 2.0
HOOK_LIP_REACH = 2.5
HOOK_GAP = 0.3
"""The clip. A rib outside each rail flange runs from the base back to near
the mounting face; a lip on it turns inward under the flange. HOOK_L is the
rib's length along the rail, centred; the rest are print-scale numbers.
SOURCE: design, the shape every DIN clip has. CONFIDENCE: design. The lower
one is the latch: printed at HOOK_RIB_T it flexes to snap on; the upper one
is the hook. Lead-in chamfers are the print's, not the model's."""

# ---- the controller -----------------------------------------------------
CONTROLLER_ENV = params.motion_controller_env
CONTROLLER_MOUNT = params.motion_controller_mount
"""Read from params.CATALOG (C00). Both None on 2026-09-04: Carbide publishes
neither, and the community figure (336.6 x 171.5 x 88.9) is a LEAD that the
catalog rules out of driving design. When ``motion_controller_env`` becomes
(W, H, D), the reference solid lands in ``controller_seat`` and the check
compares; when ``motion_controller_mount`` becomes a tuple of (x, y) foot
offsets from the enclosure's back's lower-left corner, the subplate cuts a
SCREW_PILOT_D pilot at each. CONFIDENCE: MEASURE, both."""

CONTROLLER_LEAD = (336.6, 171.5, 88.9)
"""The community reading, carried so the check can say what the measurement
may bring. SOURCE: params.SOURCES["motion_controller_env"], community thread
59644. CONFIDENCE: LEAD, NOT EVIDENCE. Sizes nothing."""

SEAT_GAP = GRID
"""Air between the controller's seat and the rail band above it. CONFIDENCE:
design."""

# ---- plate to spine, plate to cradle -----------------------------------
SPINE_SCREW_D = SCREW_CLEAR_D
SPINE_SCREW_CBORE_D = SCREW_CBORE_D
SPINE_SCREW_CBORE_DEPTH = PLATE_T / 2
SPINE_SCREW_LEN_MAX = PLATE_T + D.t / 2
"""Same fastening as the mains backplate: carcass clearance, counterbore on
the DEVICE face, screw no longer than the plate plus half the spine.
CONFIDENCE: derived."""

CRADLE_SCREW_D = SCREW_CLEAR_D
CRADLE_SCREW_CBORE_D = SCREW_CBORE_D
CRADLE_SCREW_CBORE_DEPTH = PLATE_T / 2
"""Through the subplate into the shelf's and cheeks' rear end grain,
counterbored on the SPINE face so the plate still lands flat on the spine.
CONFIDENCE: derived. The heads are against the spine and unreachable once
the plate is hung, which is the point: the cradle is assembled on the bench."""

CHEEK_SCREW_D = SCREW_CLEAR_D
"""Up through the shelf into each cheek's bottom edge. Heads under the shelf,
exposed. CONFIDENCE: derived."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the
# block above and on Datums.
# ====================================================================


# ---- the subplate ---------------------------------------------------------


def plate_x(d: Datums = D) -> tuple[float, float]:
    """Station X span: off the partition's right face snapped up to the grid,
    to END_CLEAR short of the end wall snapped down. Both ends are air."""
    return (snap_up(signal_x(d)[0]), snap_dn(d.wall_x[3] - END_CLEAR))


def plate_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span: the band between the two crossing rows."""
    return (d.deck_top + ROW_LOW_Z + ROW_CLEAR, d.deck_top + ROW_HIGH_Z - ROW_CLEAR)


def plate_y(d: Datums = D) -> tuple[float, float]:
    """Station Y span: flat on the spine's rear face."""
    y0 = d.y_spine + d.t
    return (y0, y0 + PLATE_T)


def plate_size(d: Datums = D) -> tuple[float, float]:
    x0, x1 = plate_x(d)
    z0, z1 = plate_z(d)
    return (x1 - x0, z1 - z0)


def device_face_y(d: Datums = D) -> float:
    """Station Y of the plate's rear face, where everything mounts."""
    return plate_y(d)[1]


def door_landing_y(d: Datums = D) -> float:
    """Station Y the band ends at: the rear door's inside face."""
    return d.y_rear - brain_partition.DOOR_LANDING


def band_depth(d: Datums = D) -> float:
    """Air from the plate's face to the door's inside face."""
    return door_landing_y(d) - device_face_y(d)


def plane(d: Datums = D) -> Plane:
    """The plate's frame: local +X to station +X, local +Y up, thickness
    into -Y so Z = 0 is the device face. Origin at the datum corner."""
    return Plane(
        origin=(plate_x(d)[0], plate_y(d)[1], plate_z(d)[0]),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def _local(x: float, z: float, d: Datums = D) -> tuple[float, float]:
    """Station (x, z) to plate-local (x, y)."""
    return (x - plate_x(d)[0], z - plate_z(d)[0])


def spine_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Plate-to-spine screws: two columns at the carcass edge distance, on
    the carcass fastener rhythm."""
    w, h = plate_size(d)
    return [(x, p) for x in (SCREW_EDGE_OFF, w - SCREW_EDGE_OFF) for p in screw_positions(h)]


# ---- the cradle -------------------------------------------------------------


def pc_size() -> tuple[float, float, float]:
    """(W along X, D into the band, H up) of the PC, standing upright."""
    return PC_ENV


def shelf_size(d: Datums = D) -> tuple[float, float]:
    """(W along X, depth off the plate face) of the shelf blank."""
    w, dep, _h = pc_size()
    return (
        2 * CHEEK_T + 2 * PC_SIDE_CLEAR + w,
        CABLE_ROOM + dep + PC_FRONT_CLEAR,
    )


def window_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], float]:
    """The reveal window's outline on the door plane, STATION (x, z), and its
    corner radius. Read from rear_door, which owns it."""
    (x0, x1), (y0, y1) = rear_door.window_local(d)
    zb = rear_door.z_bottom(d)
    xl = rear_door.x_left(d)
    return ((x0 + xl, x1 + xl), (zb + y0, zb + y1), rear_door.WINDOW_R)


def cradle_x_local(d: Datums = D) -> float:
    """Plate-local X of the cradle's left (cheek) face, DERIVED: the PC is
    CENTRED in the reveal window, so the big face shows with equal margin each
    side. Centring, not left-align, because the P350's face very nearly fills
    the window's width and a snapped left edge would spend all the slack on one
    side and fail the far margin."""
    (wx0, wx1), _z, _r = window_station(d)
    w, _dep, _h = pc_size()
    x_pc_min = (wx0 + wx1) / 2 - w / 2
    x_cheek = x_pc_min - PC_SIDE_CLEAR - CHEEK_T
    return x_cheek - plate_x(d)[0]


def shelf_y_local(d: Datums = D) -> float:
    """Plate-local height of the shelf's UNDERSIDE, DERIVED to stand the shelf
    ``CRADLE_CARRIER_GAP`` clear of the printed carrier's top: the cradle sits
    directly above the carrier in the same X band (both are under the reveal
    window), so the shelf's underside is what has to miss it. The upright PC
    then reaches up into the window; the window is tall enough and well under
    the cap, so the PC still fits the pane with its margin and clears the cap.
    ``check_signal_mounts`` verifies the window fit, the cap and the carrier."""
    carrier_top = carrier_station(d)[2][1]
    shelf_underside = carrier_top + CRADLE_CARRIER_GAP
    return shelf_underside - plate_z(d)[0]


def shelf_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """(x, y, z) spans of the shelf."""
    w, dep = shelf_size(d)
    x0 = plate_x(d)[0] + cradle_x_local(d)
    y0 = device_face_y(d)
    z0 = plate_z(d)[0] + shelf_y_local(d)
    return ((x0, x0 + w), (y0, y0 + dep), (z0, z0 + SHELF_T))


def cheek_station(side: str, d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """(x, y, z) spans of one cheek, standing on the shelf at one end."""
    (sx0, sx1), (sy0, sy1), (_sz0, sz1) = shelf_station(d)
    x0 = sx0 if side == "l" else sx1 - CHEEK_T
    return ((x0, x0 + CHEEK_T), (sy0, sy1), (sz1, sz1 + CHEEK_H))


def lip_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """(x, y, z) spans of the lip: on the shelf's front edge, the shelf's full
    width, from the shelf's underside to LIP_H_ABOVE over its top."""
    (sx0, sx1), (_sy0, sy1), (sz0, sz1) = shelf_station(d)
    return ((sx0, sx1), (sy1, sy1 + LIP_T), (sz0, sz1 + LIP_H_ABOVE))


def lip_size(d: Datums = D) -> tuple[float, float]:
    (x0, x1), _y, (z0, z1) = lip_station(d)
    return (x1 - x0, z1 - z0)


def pc_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """(x, y, z) spans of the PC: on the shelf, between the cheeks, its rear
    CABLE_ROOM off the plate."""
    w, dep, h = pc_size()
    (sx0, _sx1), (sy0, _sy1), (_sz0, sz1) = shelf_station(d)
    x0 = sx0 + CHEEK_T + PC_SIDE_CLEAR
    y0 = sy0 + CABLE_ROOM
    return ((x0, x0 + w), (y0, y0 + dep), (sz1, sz1 + h))


def shelf_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Plate-local centres of the screws through the plate into the shelf's
    rear end grain: on the shelf's mid-thickness, at the fastener rhythm."""
    w, _dep = shelf_size(d)
    x0 = cradle_x_local(d)
    y = shelf_y_local(d) + SHELF_T / 2
    return [(x0 + p, y) for p in screw_positions(w)]


def cheek_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Plate-local centres of the one screw per cheek into its rear end
    grain: on the cheek's mid-thickness, mid-height."""
    w, _dep = shelf_size(d)
    x0 = cradle_x_local(d)
    y = shelf_y_local(d) + SHELF_T + CHEEK_H / 2
    return [(x0 + CHEEK_T / 2, y), (x0 + w - CHEEK_T / 2, y)]


def shelf_cheek_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Shelf-local (x, y) of the screws up through the shelf into the two
    cheeks' bottom edges: on each cheek's centreline, at the rhythm along the
    shelf's depth."""
    w, dep = shelf_size(d)
    return [(x, p) for x in (CHEEK_T / 2, w - CHEEK_T / 2) for p in screw_positions(dep)]


def lip_screws_local(d: Datums = D) -> list[tuple[float, float]]:
    """Lip-local (x, y) of its two screws: on the shelf's mid-thickness, a
    module in from each end."""
    lw, _lh = lip_size(d)
    return [(GRID, SHELF_T / 2), (lw - GRID, SHELF_T / 2)]


# ---- the rail ---------------------------------------------------------------


def rail_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Bounding (x, y, z) spans of the rail."""
    px0 = plate_x(d)[0]
    pz0 = plate_z(d)[0]
    face = device_face_y(d)
    return (
        (px0 + RAIL_X_LOCAL, px0 + RAIL_X_LOCAL + RAIL_LEN),
        (face, face + RAIL_D),
        (pz0 + RAIL_Y_LOCAL - RAIL_H / 2, pz0 + RAIL_Y_LOCAL + RAIL_H / 2),
    )


def rail_centre_z(d: Datums = D) -> float:
    return plate_z(d)[0] + RAIL_Y_LOCAL


def _box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Part:
    """A station-coordinate box from three spans."""
    return Box(x[1] - x[0], y[1] - y[0], z[1] - z[0],
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x[0], y[0], z[0]))
    )


def build_rail(d: Datums = D) -> Part:
    """The top-hat profile, STATION coordinates: crown on the plate, two webs,
    two flanges standing RAIL_D off the plate with the hooks' room behind."""
    (x0, x1), (y0, _y1), _z = rail_station(d)
    zc = rail_centre_z(d)
    xs = (x0, x1)
    crown = _box(xs, (y0, y0 + RAIL_T), (zc - RAIL_CROWN_W / 2, zc + RAIL_CROWN_W / 2))
    part = crown
    for s in (-1, 1):
        web_z = sorted((s * (RAIL_CROWN_W / 2 - RAIL_T), s * RAIL_CROWN_W / 2))
        part += _box(xs, (y0, y0 + RAIL_D), (zc + web_z[0], zc + web_z[1]))
        fl_z = sorted((s * RAIL_CROWN_W / 2, s * RAIL_H / 2))
        part += _box(xs, (y0 + RAIL_D - RAIL_T, y0 + RAIL_D), (zc + fl_z[0], zc + fl_z[1]))
    return part


# ---- the printed carrier ----------------------------------------------------


def carrier_size() -> tuple[float, float]:
    """(along the rail, across it) of the carrier's base."""
    return (BOARD[0] + 2 * CARRIER_MARGIN, BOARD[1] + 2 * CARRIER_MARGIN)


def carrier_height() -> float:
    """Print height: base plus the hooks' reach to the mounting face."""
    return BASE_T + RAIL_D - HOOK_GAP


def insert_holes_local() -> list[tuple[float, float]]:
    """Carrier-print-local (x, y) of the four insert pilots, centred on the
    base, at the board's corner pattern."""
    cw, ch = carrier_size()
    bw, bh = BOARD
    return [
        (cw / 2 + sx * (bw / 2 - BOARD_HOLE_INSET), ch / 2 + sy * (bh / 2 - BOARD_HOLE_INSET))
        for sx in (-1, 1) for sy in (-1, 1)
    ]


def build_carrier() -> Part:
    """The carrier in PRINT orientation: base on Z = 0 (front face down),
    hooks rising in +Z. Local X along the rail, local Y across it."""
    cw, ch = carrier_size()
    base = Box(cw, ch, BASE_T, align=(Align.MIN, Align.MIN, Align.MIN))
    part = base

    # the two hooks, mirrored about the rail's centreline (local y = ch/2)
    x0 = cw / 2 - HOOK_L / 2
    for s in (-1, 1):
        rib_in = ch / 2 + s * (RAIL_H / 2 + HOOK_GAP)
        rib = sorted((rib_in, rib_in + s * HOOK_RIB_T))
        # rib: from the base's back (z = BASE_T) to HOOK_GAP short of the plate
        part += Box(HOOK_L, rib[1] - rib[0], RAIL_D - HOOK_GAP,
                    align=(Align.MIN, Align.MIN, Align.MIN)).moved(
            Location((x0, rib[0], BASE_T))
        )
        # lip: turns inward under the flange, HOOK_LIP_T thick, HOOK_LIP_REACH in
        lip_out = ch / 2 + s * (RAIL_H / 2 + HOOK_GAP)
        lip = sorted((lip_out, lip_out - s * (HOOK_GAP + HOOK_LIP_REACH)))
        z0 = BASE_T + RAIL_T + HOOK_GAP          # under the flange's inner face
        part += Box(HOOK_L, lip[1] - lip[0], HOOK_LIP_T,
                    align=(Align.MIN, Align.MIN, Align.MIN)).moved(
            Location((x0, lip[0], z0))
        )

    # the insert pilots, blind from the front face (Z = 0)
    for x, y in insert_holes_local():
        part -= bore(x, y, INSERT_HOLE_D, thickness=BASE_T, depth=INSERT_HOLE_DEPTH, side="back")
    return part


def carrier_plane(d: Datums = D) -> Plane:
    """Print frame to station: print X to station X, print Y up, print +Z
    into station -Y (toward the plate). Origin: the carrier's lower-left
    front corner, its front face BASE_T off the rail's outer face."""
    (rx0, _rx1), (_ry0, ry1), _z = rail_station(d)
    cw, ch = carrier_size()
    x0 = rx0 + (RAIL_LEN - cw) / 2
    return Plane(
        origin=(x0, ry1 + BASE_T, rail_centre_z(d) - ch / 2),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def carrier_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Bounding (x, y, z) spans of the placed carrier."""
    p = carrier_plane(d)
    cw, ch = carrier_size()
    (_rx, (ry0, _ry1), _rz) = rail_station(d)
    return (
        (p.origin.X, p.origin.X + cw),
        (ry0 + HOOK_GAP, p.origin.Y),
        (p.origin.Z, p.origin.Z + ch),
    )


def board_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The protoboard and its stack, off the carrier's front face."""
    (cx0, cx1), (_cy0, cy1), (cz0, cz1) = carrier_station(d)
    bw, bh = BOARD
    return (
        ((cx0 + cx1) / 2 - bw / 2, (cx0 + cx1) / 2 + bw / 2),
        (cy1 + STANDOFF_H, cy1 + STANDOFF_H + BOARD_STACK_H),
        ((cz0 + cz1) / 2 - bh / 2, (cz0 + cz1) / 2 + bh / 2),
    )


# ---- the controller's seat --------------------------------------------------


def controller_seat(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """(x, y, z) spans of the volume reserved for the controller: the plate's
    full width, from the plate's bottom to SEAT_GAP under the rail band, and
    from the plate's face to the door's landing."""
    px0, px1 = plate_x(d)
    pz0 = plate_z(d)[0]
    band_bottom = min(rail_station(d)[2][0], carrier_station(d)[2][0])
    return ((px0, px1), (device_face_y(d), door_landing_y(d)), (pz0, band_bottom - SEAT_GAP))


def controller_station(d: Datums = D) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None:
    """Where the controller lands when its envelope is known: the seat's
    lower-left corner, its back on the plate. None while params is None."""
    if CONTROLLER_ENV is None:
        return None
    w, h, dep = CONTROLLER_ENV
    (sx0, _sx1), (sy0, _sy1), (sz0, _sz1) = controller_seat(d)
    return ((sx0, sx0 + w), (sy0, sy0 + dep), (sz0, sz0 + h))


def controller_pilots_local(d: Datums = D) -> list[tuple[float, float]]:
    """Plate-local pilots for the controller's feet, from params, when known."""
    if CONTROLLER_MOUNT is None or controller_station(d) is None:
        return []
    (cx0, _cx1), _y, (cz0, _cz1) = controller_station(d)
    lx, ly = _local(cx0, cz0, d)
    return [(lx + fx, ly + fy) for fx, fy in CONTROLLER_MOUNT]


# ---- builders ---------------------------------------------------------------


def build(d: Datums = D) -> Part:
    """The subplate, flat in panel-local coordinates."""
    w, h = plate_size(d)
    part = panel(w, h, PLATE_T)

    # Plate to spine: through clearance, counterbored on the DEVICE face.
    for x, y in spine_screws_local(d):
        part -= bore(x, y, SPINE_SCREW_D, thickness=PLATE_T)
        part -= bore(x, y, SPINE_SCREW_CBORE_D, thickness=PLATE_T,
                     depth=SPINE_SCREW_CBORE_DEPTH, side="back")

    # Plate to cradle: through clearance, counterbored on the SPINE face.
    for x, y in shelf_screws_local(d) + cheek_screws_local(d):
        part -= bore(x, y, CRADLE_SCREW_D, thickness=PLATE_T)
        part -= bore(x, y, CRADLE_SCREW_CBORE_D, thickness=PLATE_T,
                     depth=CRADLE_SCREW_CBORE_DEPTH, side="front")

    # The controller's feet, only once params knows the pattern.
    for x, y in controller_pilots_local(d):
        part -= bore(x, y, SCREW_PILOT_D, thickness=PLATE_T, depth=PLATE_T / 2, side="back")

    # No apertures. Every run reaches this side through the spine's own
    # crossings above and below the plate, or through the partition's transit.
    return part


def place(part: Part | None = None, d: Datums = D) -> Part:
    part = build(d) if part is None else part
    return plane(d) * part


def build_shelf(d: Datums = D) -> Part:
    """The shelf, flat on the deck convention: +X station X, +Y into the
    band, +Z up. Screws up through it into the cheeks."""
    w, dep = shelf_size(d)
    part = panel(w, dep, SHELF_T)
    for x, y in shelf_cheek_screws_local(d):
        part -= bore(x, y, CHEEK_SCREW_D, thickness=SHELF_T)
    return part


def shelf_plane(d: Datums = D) -> Plane:
    (x0, _x1), (y0, _y1), (z0, _z1) = shelf_station(d)
    return Plane(origin=(x0, y0, z0), x_dir=(1, 0, 0), z_dir=(0, 0, 1))


def build_cheek(d: Datums = D) -> Part:
    """One cheek, flat on the wall convention: +X into the band, +Y up,
    thickness into +X. No holes: the screws enter its edges."""
    (_x, (y0, y1), (z0, z1)) = cheek_station("l", d)
    return panel(y1 - y0, z1 - z0, CHEEK_T)


def cheek_plane(side: str, d: Datums = D) -> Plane:
    (x0, _x1), (y0, _y1), (z0, _z1) = cheek_station(side, d)
    return Plane(origin=(x0, y0, z0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def build_lip(d: Datums = D) -> Part:
    """The clear lip, flat like the subplate: +X station X, +Y up, PT thick.
    Two screw holes on the shelf's mid-thickness."""
    lw, lh = lip_size(d)
    part = panel(lw, lh, LIP_T)
    for x, y in lip_screws_local(d):
        part -= bore(x, y, LIP_SCREW_D, thickness=LIP_T)
    return part


def lip_plane(d: Datums = D) -> Plane:
    """The plate's convention: local +Y up, thickness into -Y from the lip's
    outer face, so Z = 0 is the face the screw heads sit on and Z = PT lands
    on the shelf's edge."""
    (x0, _x1), (_y0, y1), (z0, _z1) = lip_station(d)
    return Plane(origin=(x0, y1, z0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))


def build_pc(d: Datums = D) -> Part:
    return _box(*pc_station(d))


def build_board(d: Datums = D) -> Part:
    return _box(*board_station(d))


def build_controller(d: Datums = D) -> Part | None:
    st = controller_station(d)
    return None if st is None else _box(*st)


def place_carrier(part: Part | None = None, d: Datums = D) -> Part:
    part = build_carrier() if part is None else part
    return carrier_plane(d) * part


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, part) for everything this module puts in the assembly."""
    out: list[tuple[str, str, Part]] = [
        (PART_NAME, "carcass", place(d=d)),
        (SHELF_NAME, "carcass", shelf_plane(d) * build_shelf(d)),
        (f"{CHEEK_STEM}_l", "carcass", cheek_plane("l", d) * build_cheek(d)),
        (f"{CHEEK_STEM}_r", "carcass", cheek_plane("r", d) * build_cheek(d)),
        (LIP_NAME, "acrylic", lip_plane(d) * build_lip(d)),
        (PC_NAME, "reference", build_pc(d)),
        (RAIL_NAME, "steel", build_rail(d)),
        (CARRIER_NAME, "print", place_carrier(d=d)),
        (BOARD_NAME, "reference", build_board(d)),
    ]
    ctl = build_controller(d)
    if ctl is not None:
        out.append((CONTROLLER_NAME, "reference", ctl))
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples. Every
    joint here is a face: nothing on this side shares volume with anything,
    by construction."""
    out: list[tuple] = [
        ("spine_panel", PART_NAME, "butt", None, 0.0, 0.0,
         "subplate flat on the spine's rear face, screwed through; the spine cuts nothing"),
        (PART_NAME, SHELF_NAME, "butt", None, 0.0, 0.0,
         "shelf's rear end grain on the subplate's device face, screwed through the plate"),
        (PART_NAME, RAIL_NAME, "bearing", None, 0.0, 0.0,
         "rail screwed to the subplate through its own slots"),
        (RAIL_NAME, CARRIER_NAME, "bearing", None, 0.0, 0.0,
         "carrier's hooks behind the rail's flanges, its back on their faces"),
        (CARRIER_NAME, BOARD_NAME, "bearing", None, 0.0, 0.0,
         f"board on {STANDOFF} into the carrier's inserts"),
        (SHELF_NAME, PC_NAME, "bearing", None, 0.0, 0.0,
         "the PC stands upright on the shelf"),
        (SHELF_NAME, LIP_NAME, "bearing", None, 0.0, 0.0,
         "lip flat on the shelf's front edge, two screws into the end grain"),
    ]
    for side in ("l", "r"):
        out.append((SHELF_NAME, f"{CHEEK_STEM}_{side}", "bearing", None, 0.0, 0.0,
                    "cheek stands on the shelf's top face, screwed up through the shelf"))
        out.append((PART_NAME, f"{CHEEK_STEM}_{side}", "butt", None, 0.0, 0.0,
                    "cheek's rear end grain on the subplate, one screw through the plate"))
        out.append((f"{CHEEK_STEM}_{side}", LIP_NAME, "bearing", None, 0.0, 0.0,
                    "lip covers the cheek's front end grain"))
    if controller_station(d) is not None:
        out.append((PART_NAME, CONTROLLER_NAME, "bearing", None, 0.0, 0.0,
                    "controller's back on the subplate, on its own feet"))
    return out


# ---------------------------------------------------------------- questions


def _inside_rounded(x: float, z: float, xs: tuple[float, float], zs: tuple[float, float], r: float, margin: float) -> bool:
    """Whether a point lies inside a rounded rectangle shrunk by ``margin``."""
    x0, x1 = xs[0] + margin, xs[1] - margin
    z0, z1 = zs[0] + margin, zs[1] - margin
    rr = max(r - margin, 0.0)
    if not (x0 <= x <= x1 and z0 <= z <= z1):
        return False
    cx = x0 + rr if x < x0 + rr else (x1 - rr if x > x1 - rr else x)
    cz = z0 + rr if z < z0 + rr else (z1 - rr if z > z1 - rr else z)
    return (x - cx) ** 2 + (z - cz) ** 2 <= rr ** 2 + 1e-9


def pc_in_window(d: Datums = D) -> bool:
    """Whether the PC's projection onto the door plane lies inside the reveal
    window's outline by PC_WINDOW_MARGIN: all four corners of its outline."""
    (px0, px1), _y, (pz0, pz1) = pc_station(d)
    xs, zs, r = window_station(d)
    return all(_inside_rounded(x, z, xs, zs, r, PC_WINDOW_MARGIN)
               for x in (px0, px1) for z in (pz0, pz1))


def pc_obstructions(d: Datums = D) -> list[str]:
    """Opaque solids of this module standing between the PC's front and the
    door whose projection overlaps the PC's. Acrylic is not opaque."""
    (px0, px1), (_py0, py1), (pz0, pz1) = pc_station(d)
    hits: list[str] = []
    for label, group, part in placed_all(d):
        if label == PC_NAME or group == "acrylic":
            continue
        bb = part.bounding_box()
        if bb.max.Y <= py1 + 1e-6:
            continue
        if bb.max.X > px0 and bb.min.X < px1 and bb.max.Z > pz0 and bb.min.Z < pz1:
            hits.append(label)
    return hits


def vent_slots_over_signal(d: Datums = D) -> list[float]:
    """Station X centres of the cap's exhaust slots that lie over the signal
    side. Empty by construction of Datums.brain_exhaust_x; asked of top_cap
    rather than assumed."""
    sx0, sx1 = signal_x(d)
    v = top_cap.vent_field(d)
    return [xc for xc in v.x_centres if xc + top_cap.VENT_SLOT_W / 2 > sx0 and xc - top_cap.VENT_SLOT_W / 2 < sx1]


def vent_intruders(d: Datums = D) -> list[str]:
    """Solids of this module within GRID of the cap's underside under a slot
    over the signal side."""
    v = top_cap.vent_field(d)
    z_floor = d.top_z[0] - GRID
    hits: list[str] = []
    for xc in vent_slots_over_signal(d):
        x0, x1 = xc - top_cap.VENT_SLOT_W / 2, xc + top_cap.VENT_SLOT_W / 2
        for label, _group, part in placed_all(d):
            bb = part.bounding_box()
            if bb.max.Z > z_floor and bb.max.X > x0 and bb.min.X < x1 and bb.max.Y > v.y0 and bb.min.Y < v.y1:
                hits.append(label)
    return hits


def carrier_print_size() -> tuple[float, float, float]:
    bb = build_carrier().bounding_box()
    return (bb.size.X, bb.size.Y, bb.size.Z)


# ---------------------------------------------------------------- checks


def check_signal_mounts(d: Datums = D) -> list[str]:
    """What this side has to be true for. The assembly's interference check
    owns whether anything here hits a neighbour; these are the things that
    are wrong before the solids are compared."""
    notes: list[str] = []
    w, h = plate_size(d)
    px0, px1 = plate_x(d)
    pz0, pz1 = plate_z(d)
    sx0, sx1 = signal_x(d)
    face = device_face_y(d)
    door = door_landing_y(d)

    # -- doctrine first: compute is always-live, read off the mains plate
    live = " ".join(mains_backplate._rail("ALWAYS-LIVE").loads).lower()
    ctr = " ".join(mains_backplate._rail("CONTACTOR").loads).lower()
    for load in ("pc brick", "esp32"):
        if load not in live:
            notes.append(f"'{load}' is not on the mains backplate's ALWAYS-LIVE rail (C05, I60)")
        if load in ctr:
            notes.append(
                f"'{load}' is on the CONTACTOR rail: guards kill motion and cutting, never compute"
            )
    if "motion controller" not in ctr:
        notes.append("the motion controller is not on the CONTACTOR rail; the interlock has to drop it")

    # -- the plate sits in the signal zone, clear of the partition, the
    #    wall, and the crossing rows
    if px0 < sx0 - 1e-6 or px0 <= d.brain_split_x:
        notes.append(f"plate starts at x {px0:.1f}, not right of the partition's face at {sx0:.1f}")
    if px1 > d.wall_x[3] - END_CLEAR + 1e-6:
        notes.append(f"plate reaches x {px1:.1f}, inside END_CLEAR of the end wall at {d.wall_x[3]:.1f}")
    for c in CROSSINGS:
        if c.zone != "signal":
            continue
        bx = crossing_x(d)[c.label]
        bz = d.deck_top + ROW_Z[c.row]
        r = BORE_D[c.kind] / 2
        if px0 - 1e-6 <= bx <= px1 + 1e-6 and pz0 - r - BORE_CLEAR_MIN < bz < pz1 + r + BORE_CLEAR_MIN:
            notes.append(
                f"the plate covers or crowds the {c.label} bore at z {bz:.1f}: its nut "
                f"needs {BORE_CLEAR_MIN:.0f}mm past the bore's edge"
            )
    if pz1 > d.top_z[0] - 1e-6 or pz0 < d.deck_top + 1e-6:
        notes.append(f"plate z {pz0:.1f}..{pz1:.1f} leaves the band {d.deck_top:.1f}..{d.top_z[0]:.1f}")
    if h <= 0 or w <= 0:
        notes.append("the plate has no area: the rows or the zone have closed on it")
        return notes

    # -- every solid: right of the partition, behind the spine, ahead of the
    #    door, on the deck or above it, a service gap under the cap
    for label, _group, part in placed_all(d):
        bb = part.bounding_box()
        if bb.min.X <= d.brain_split_x or bb.min.X < sx0 - 1e-6 or bb.max.X > d.wall_x[3] + 1e-6:
            notes.append(f"{label} spans x {bb.min.X:.1f}..{bb.max.X:.1f}, outside the signal zone {sx0:.1f}..{d.wall_x[3]:.1f}")
        if bb.min.Y < d.y_spine + d.t - 1e-6:
            notes.append(f"{label} reaches y {bb.min.Y:.1f}, into the spine")
        if bb.max.Y > door + 1e-6:
            notes.append(f"{label} reaches y {bb.max.Y:.1f}, into the rear door's landing at {door:.1f}")
        if bb.min.Z < d.deck_top - 1e-6:
            notes.append(f"{label} reaches below the deck")
        if bb.max.Z > d.top_z[0] - SERVICE_GAP + 1e-6:
            notes.append(
                f"{label} reaches z {bb.max.Z:.1f}, inside {SERVICE_GAP:.0f}mm of the cap's "
                f"underside at {d.top_z[0]:.1f}: the exhaust field's air"
            )

    # -- the PC is seen through the reveal, and nothing opaque stands in front
    if not pc_in_window(d):
        (qx0, qx1), _y, (qz0, qz1) = pc_station(d)
        xs, zs, _r = window_station(d)
        notes.append(
            f"the PC's projection x {qx0:.1f}..{qx1:.1f} z {qz0:.1f}..{qz1:.1f} does not lie "
            f"inside the reveal window x {xs[0]:.1f}..{xs[1]:.1f} z {zs[0]:.1f}..{zs[1]:.1f} "
            f"by {PC_WINDOW_MARGIN:.0f}mm"
        )
    for label in pc_obstructions(d):
        notes.append(f"{label} stands between the PC and the reveal; the window shows a bracket, not a computer")
    (_x, (_y0, sy1), _z) = lip_station(d)
    if door - sy1 < GRID:
        notes.append(f"the cradle's lip is {door - sy1:.1f}mm from the door's inside face, under a grid module")

    # -- the exhaust field over the signal side, asked of top_cap
    for label in vent_intruders(d):
        notes.append(f"{label} stands within {GRID:.0f}mm of the cap's underside under an exhaust slot")

    # -- the carrier prints on the smallest bed
    size = carrier_print_size()
    if not printable(size, PRINT_BED_MIN, PRINT_BED_MARGIN):
        notes.append(
            f"the carrier prints {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f}, which does not fit "
            f"the {PRINT_BED_MIN[0]:.0f} bed with {PRINT_BED_MARGIN:.0f}mm clear"
        )
    if INSERT_HOLE_DEPTH >= BASE_T:
        notes.append(f"the insert pilot is {INSERT_HOLE_DEPTH:.1f} deep in a {BASE_T:.1f} base: it is through")
    if HOOK_LIP_REACH >= (RAIL_H - RAIL_CROWN_W) / 2:
        notes.append("the hook's lip reaches past the flange onto the web; the clip cannot seat")

    # -- the controller: placed if known, reserved if not
    (kx0, kx1), (ky0, ky1), (kz0, kz1) = controller_seat(d)
    seat = (kx1 - kx0, kz1 - kz0, ky1 - ky0)
    st = controller_station(d)
    if st is None:
        lead_fits = any(
            fits((a, b), (seat[0], seat[1])) and c <= seat[2]
            for a, b, c in (
                (CONTROLLER_LEAD[0], CONTROLLER_LEAD[1], CONTROLLER_LEAD[2]),
                (CONTROLLER_LEAD[0], CONTROLLER_LEAD[2], CONTROLLER_LEAD[1]),
                (CONTROLLER_LEAD[1], CONTROLLER_LEAD[2], CONTROLLER_LEAD[0]),
            )
        )
        notes.append(
            "catalog motion_controller_env is None, MEASURE THIS: the Carbide Motion controller is "
            f"NOT placed. The subplate reserves a seat {seat[0]:.0f} x {seat[1]:.0f} x {seat[2]:.0f} "
            "(W x H x depth to the door) at its bottom; the reference solid and the foot pilots land "
            "the moment params carries the tuple. The community lead "
            f"{CONTROLLER_LEAD[0]:.1f} x {CONTROLLER_LEAD[1]:.1f} x {CONTROLLER_LEAD[2]:.1f} "
            f"{'would fit' if lead_fits else 'would NOT fit'} the seat in some orientation; it is a "
            "lead, not a datasheet, and sizes nothing. A measured controller that outgrows the seat "
            "goes on the deck under the subplate, which is the next layout and not this one."
        )
    else:
        (cx0, cx1), (cy0, cy1), (cz0, cz1) = st
        if cx1 > kx1 + 1e-6 or cy1 > ky1 + 1e-6 or cz1 > kz1 + 1e-6:
            notes.append(
                f"the controller {cx1 - cx0:.0f} x {cz1 - cz0:.0f} x {cy1 - cy0:.0f} outgrows its seat "
                f"{seat[0]:.0f} x {seat[1]:.0f} x {seat[2]:.0f}; the layout moves"
            )
    if CONTROLLER_MOUNT is None:
        notes.append(
            "catalog motion_controller_mount is None, MEASURE THIS: no foot pilots are cut in the "
            "subplate. Read the slot/foot pattern off the enclosure's back as (x, y) from its "
            "lower-left corner."
        )

    # -- what the representative parts have not told us yet
    notes.append(
        f"the protoboard ({BOARD[0]:.0f}x{BOARD[1]:.0f}, holes o{BOARD_HOLE_D:.1f} at "
        f"{BOARD_HOLE_INSET:.1f} in) and the heat-set insert (o{INSERT_HOLE_D:.1f} pilot) are "
        "REPRESENTATIVE: no SKU on the BOM, no board named. MEASURE THIS when in hand; the "
        "board moves only the carrier's outline and insert pattern."
    )

    # -- the schedule, kept visible on every run
    notes.append("WIRE SCHEDULE, standing note. " + " | ".join(wire_schedule(d)))

    for label, size2 in ((PART_NAME, (w, h)), (SHELF_NAME, shelf_size(d)),
                         (f"{CHEEK_STEM}_l", (cheek_station('l', d)[1][1] - cheek_station('l', d)[1][0], CHEEK_H))):
        if not fits(size2, SHEET_4X8):
            notes.append(f"{label} blank {size2[0]:.0f} x {size2[1]:.0f} does not come out of a 4x8 sheet")
    if not fits(lip_size(d), QUARTER):
        notes.append(f"the lip {lip_size(d)[0]:.0f} x {lip_size(d)[1]:.0f} does not come out of a QUARTER blank")

    return notes


def wire_schedule(d: Datums = D) -> list[str]:
    """What crosses to this side and where it lands, one line each."""
    tz0, tz1 = brain_partition.transit_z(d)
    return [
        f"WIRE SCHEDULE {PART_NAME}: everything here is ALWAYS-LIVE DC or signal; no mains crosses the partition",
        f"transit z {tz0:.0f}..{tz1:.0f} at x {d.brain_split_x:.0f}: PC brick DC (ALWAYS-LIVE) to the PC's rear at "
        f"z {pc_station(d)[2][0]:.0f}..{pc_station(d)[2][1]:.0f}; ESP32 supply DC (ALWAYS-LIVE) and the CT lead to the carrier; "
        "the motion controller's supply, contactor-fed, as the mains schedule has it",
        "spine crossings, high row: CONSOLE STOP, CONSOLE CONTROL, CONSOLE INSTRUMENT (GX16) above the plate; "
        "low row: PENDANT AND USB (gland) below it; pendant to the controller, USB to the PC",
        "rear door: RJ45 to the PC's rear; GX16 pendant and mast-camera bulkheads; the reveal shows the PC",
        "controller logic 0V never lands on the PE star (params.bond_excluded)",
    ]


# ---------------------------------------------------------------- export


def export(d: Datums = D, out_dir: Path | None = None) -> list[Path]:
    """STEP + DXF for the sheet parts, STEP for the references, STEP + STL
    for the printed carrier in its print orientation."""
    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    written += export_part(build(d), PART_NAME, out_dir=out_dir)
    written += export_part(build_shelf(d), SHELF_NAME, out_dir=out_dir)
    written += export_part(build_cheek(d), CHEEK_STEM, out_dir=out_dir)
    written += export_part(build_lip(d), LIP_NAME, out_dir=out_dir)
    carrier = build_carrier()
    written += export_part(carrier, CARRIER_NAME, dxf=False, out_dir=out_dir)
    written.append(export_stl(carrier, out_dir / f"{CARRIER_NAME}.stl"))
    for label, group, part in placed_all(d):
        if group in ("reference", "steel"):
            written += export_part(part, label, dxf=False, out_dir=out_dir)
    return written


if __name__ == "__main__":
    d = D
    w, h = plate_size(d)
    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {PLATE_T:.0f}, on the spine's rear face, signal side")
    for label, group, part in placed_all(d):
        bb = part.bounding_box()
        print(
            f"  {group:9s} {label:24s} x {bb.min.X:7.1f}..{bb.max.X:7.1f}  "
            f"y {bb.min.Y:7.1f}..{bb.max.Y:7.1f}  z {bb.min.Z:6.1f}..{bb.max.Z:6.1f}"
        )
    sw, sd = shelf_size(d)
    print(
        f"  cradle: shelf {sw:.0f} x {sd:.0f} x {SHELF_T:.0f} at plate-local x {cradle_x_local(d):.0f} "
        f"(derived from the reveal), cheeks {CHEEK_H:.0f} tall, {LIP_MATERIAL} lip {lip_size(d)[0]:.0f} x {lip_size(d)[1]:.0f}; "
        f"PC {PC_ENV[0]:.0f} x {PC_ENV[1]:.0f} x {PC_ENV[2]:.0f} in the window: {pc_in_window(d)}, "
        f"obstructions {pc_obstructions(d) or 'none'}"
    )
    cs = carrier_print_size()
    print(
        f"  {CARRIER_NAME}: prints {cs[0]:.1f} x {cs[1]:.1f} x {cs[2]:.1f} on a "
        f"{PRINT_BED_MIN[0]:.0f} bed with {PRINT_BED_MARGIN:.0f} clear: {printable(cs)}; "
        f"{len(insert_holes_local())} x {INSERT}"
    )
    (kx0, kx1), (ky0, ky1), (kz0, kz1) = controller_seat(d)
    print(
        f"  controller seat {kx1 - kx0:.0f} x {kz1 - kz0:.0f} x {ky1 - ky0:.0f}; "
        f"params.motion_controller_env = {CONTROLLER_ENV}"
    )
    print(
        f"  exhaust slots over the signal side: {len(vent_slots_over_signal(d))}; "
        f"intruders {vent_intruders(d) or 'none'}; cap underside {d.top_z[0]:.0f}"
    )
    print()
    for line in wire_schedule(d):
        print("  " + line)

    found = check_signal_mounts(d)
    if found:
        print(f"\n{len(found)} signal mounts note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno signal mounts constraint violations")

    for p in export(d):
        print(f"wrote {p}")
