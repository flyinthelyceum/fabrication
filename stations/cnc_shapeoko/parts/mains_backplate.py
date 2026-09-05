"""Mains backplate: the sealed side's electrical, laid out on two DIN rails.

WHAT THIS PART IS
=================

One birch plate and a set of reference solids.

``mains_backplate``     One 18mm Baltic birch plate screwed flat to the spine's
                        REAR face in the sealed zone, between the drive's
                        keep-out and the brain-band partition, in the band of
                        panel BETWEEN the two crossing rows so every gland and
                        bulkhead in the spine stays reachable with a wrench.
                        Everything electrical on the sealed side mounts to it
                        and nothing mounts to the spine, so the whole rail set
                        comes off as one unit with the drive's plate beside it.

``din_rail_live``       Two lengths of EN 60715 TH35 rail screwed to the plate,
``din_rail_contactor``  one per circuit group. Two rails, not one, because the
                        split is the whole point of the sealed zone (brief v6):

    ALWAYS-LIVE   upstream of the contactor, behind its own fuse. PC brick,
                  ESP32 supply, mast feed, stock wash. Opening the rear door
                  leaves the console reporting and the mast lit.
    CONTACTOR     downstream of the contactor. VFD, motion controller,
                  extractor through the SSR. Everything that moves or cuts.

``contactor_env``       Reference solids, not birch, not cut, not on the
``ssr_env``             cutting list: the DIN-standard envelope of each device
``pe_busbar_env``       stood on its rail so every later brain-band layout
``fuse_env_*``          collides with the electrical honestly. Same idea as
``ct_env_spindle``      ``vfd_mount.vfd_keepout``.

``extractor_receptacle`` A steel surface box with one NEMA 5-15R on the LUNGS
                        face of the spine at the EXTRACTOR MAINS crossing, fed
                        through the gland bore the spine already cuts (I92).
                        The extractor plugs into it with its own cord, and the
                        box is the extractor-chassis leg of the earth star.

WHERE THE CONTACTOR STANDS (I74)
================================

Brief v7: "Let the mains contactor be heard instead. A real relay closing when
the machine arms is a sound with a referent. Site the contactor where it can
be heard, and add nothing else." The operator stands at the right end, at the
console. The partition's transit is the one opening in the sealed wall and it
is top-right of the plate, so the contactor is the RIGHTMOST device on the
UPPER rail, with nothing between it and the transit gap.
``check_mains_backplate`` measures the contactor's centre to the transit gap's
centre against ``CONTACTOR_TRANSIT_MAX``.

THE STAR POINT, AND WHAT NEVER LANDS ON IT
==========================================

``pe_busbar_env`` is the ONE earth star of the station, ``params.bond_star_point``.
Everything metal bonds to it: the drive's PE, the receptacle box (and through
it the CT 15's chassis), the hose cuff lead, the mast, the carcass hardware.
The motion controller's logic 0V NEVER lands on it, by doctrine: that is the
path that turns a hose discharge into a false limit switch. The bar is at the
left end of the ALWAYS-LIVE rail, directly above the EXTRACTOR MAINS gland and
under the MAST FEED gland, so two of the five legs are the shortest possible.

``PE_SWITCHED = False``. The contactor drops L and N only. Earth is continuous
through every device on both rails, and through the interlock, so opening the
rear door never removes the static path at the moment it exposes the machine.

THE CURRENT TRANSFORMER
=======================

``ct_env_spindle``     clamps the SPINDLE LEG, the VFD's output to the motor
                       (brief v7 §Path B: "around the spindle output leg").
                       Sited at the left end of the plate, over the drive's
                       end of the CONTACTOR rail, so the lead from the drive
                       passes through it on its way out. This is the CT whose
                       reading starts the extractor and feeds the console's
                       load number.
The spindle CT is a low-voltage lead that crosses to the signal side through
the partition's transit, which is why the transit is in the top-right corner of
this plate.

THE JOINTS
==========

    plate front face   flat on the spine's rear face, screwed through. The
                       spine cuts nothing: pilots are drilled at assembly
                       through the plate's own holes, blind, between the
                       crossing rows where the spine has no bore. A blind
                       screw is not a pass-through.
    plate rear face    the two rails screw to it through their own slots,
                       pilots drilled at assembly (an EN 60715 slotted rail
                       has 25mm-pitch slots and its phase from a cut end is
                       whatever the cut left; drilling through the slot is
                       how a rail is always fitted). Devices clip to the rails.
                       The CT is held to the plate face with a cable-tie
                       saddle: a CT clamps a conductor, not a rail.
    receptacle box     its back flat on the spine's FRONT face, two screws
                       into the spine, blind, pilots through the box's own
                       holes; its rear knockout on the gland's axis.

Screw heads sit in counterbores on the DEVICE face so the rails land flat.

WHAT IS MEASURED, WHAT IS NOT
=============================

The rail is a standard. The modular devices (contactor, fuse holders) are
bounded by DIN 43880 whatever brand arrives, so their envelopes are the
standard's and carry no MEASURE. The SSR-with-heatsink, the 8-way earth bar
and the CT are bought as generic Amazon lines with no SKU on the BOM, so each
is modelled from a REPRESENTATIVE listing or datasheet, tagged as such, and
``check_mains_backplate`` carries them as MEASURE until the ordered parts are
in hand. None of them drives a carcass dimension.

PANEL CONVENTION
================

Drawn flat like the drive's plate: local origin at the plate's lower-left
corner as seen from the REAR of the station, local +X to station +X, local +Y
up, local +Z through the thickness from the DEVICE face (Z = 0) to the spine
face (Z = t). Rails and envelopes are built directly in STATION coordinates
from the plate's datum corner, because they are placed, never cut.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Align, Box, Location, Part, Plane

from lib.house import GRID, SHEET_5X5_BALTIC, STOCK_MODULE, fits
from stations.cnc_shapeoko.carcass import (
    DADO_W,
    DATUMS,
    SCREW_CBORE_D,
    SCREW_CLEAR_D,
    SCREW_EDGE_OFF,
    Datums,
    bore,
    export_part,
    panel,
    screw_positions,
    snap_dn,
    snap_up,
)
from stations.cnc_shapeoko.parts import brain_partition
from stations.cnc_shapeoko.parts.spine_panel import (
    BORE_CLEAR_MIN,
    BORE_D,
    CROSSINGS,
    ROW_HIGH_Z,
    ROW_LOW_Z,
    ROW_Z,
    crossing_x,
)

PART_NAME = "mains_backplate"
RAIL_LIVE_NAME = "din_rail_live"
RAIL_CONTACTOR_NAME = "din_rail_contactor"
RECEPTACLE_NAME = "extractor_receptacle"

IN = 25.4


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# Shared boundaries come from Datums, the crossings from spine_panel,
# the transit from brain_partition, material from house.
# ====================================================================

PLATE_T = DATUMS.t
"""Plate thickness. SOURCE: task C05 spec, "birch backplate (carcass_t)".
CONFIDENCE: ruling. It takes wood screws for two rails and a dozen devices;
the drive's plate beside it is the same stock for the same reason."""

ROW_CLEAR = GRID * 3
"""Plate edge to the centre of the nearest crossing row, above and below.
SOURCE: design, on the bench grid; no ruling or datasheet supplies it.
CONFIDENCE: design. An M20 gland's locknut is 24mm across flats and wants a
wrench swung on it; 60mm from the bore centre leaves 50mm past the bore's edge
for the nut and the hand. The plate is the band of spine between the rows and
never covers a bore."""

PE_SWITCHED = False
"""The contactor drops L and N only. SOURCE: doctrine, params.check_earthing
"PE IS NEVER SWITCHED" and brief v7 §static path. CONFIDENCE: ruling. Earth is
continuous through both rails and through the interlock. A 2-pole contactor
cannot break PE, which is why the BOM line is 2-pole; the check refuses True."""

CONTACTOR_TRANSIT_MAX = 150.0
"""Furthest the contactor's centre may sit from the partition transit's
centre. SOURCE: task C05 acceptance (I74). CONFIDENCE: ruling."""

# ---- the rail --------------------------------------------------------
RAIL_H = 35.0
RAIL_D = 7.5
"""EN 60715 TH35-7.5 top-hat rail: 35mm across, 7.5mm off the mounting face.
SOURCE: EN 60715 (IEC 60715), the profile every device below clips to.
CONFIDENCE: standard."""

RAIL_END_INSET = GRID * 3
"""Rail end in from each plate end. SOURCE: design, on the grid. CONFIDENCE:
design. Clears the spine-screw columns at SCREW_EDGE_OFF, and leaves the
spindle CT its seat on the plate face at the drive's end of the upper rail."""

RAIL_LIVE_Y = GRID * 4
RAIL_CONTACTOR_Y = GRID * 13
"""Rail centrelines above the plate's bottom edge, ALWAYS-LIVE low and
CONTACTOR high. SOURCE: design, on the grid. CONFIDENCE: design. Two 90mm
device rows at 180mm centres leave 90mm of wiring room between them, the
contactor row tops out 55mm under the plate's top edge, and the transit gap
sits in the top-right corner beside the contactor. The higher rail is the
contactor's so its click leaves through the transit."""

GROUP_GAP = GRID
"""Air between device groups on a rail. SOURCE: design. CONFIDENCE: design.
Modular devices inside a group sit shoulder to shoulder, as they are made to;
between groups one grid module of rail is left for the fingers and the label."""

# ---- DIN 43880 modular devices: contactor and fuse holders ---------------
DIN_MODULE_W = 17.5
"""One module along the rail. SOURCE: DIN 43880 as manufactured; the standard
writes 18, the industry cuts 17.5 (Camdenboss CNMB drawing: CNMB/1 17.5,
CNMB/2 36.0). CONFIDENCE: standard."""

DIN_DEVICE_H = 90.0
DIN_DEVICE_D = 58.0
"""Modular device across the rail, and depth from the rail's mounting face to
the device's front. SOURCE: Camdenboss CNMB DIN 43880 module box, drawing
"90.0" and distributor listing 90 x 58 x 36 (CNMB/2, CPC EN82485). The depth
is from the plate the rail sits on, so it already contains the rail.
CONFIDENCE: standard envelope; any brand of modular contactor or 10x38 fuse
holder fits inside it, which is what DIN 43880 is for."""

CONTACTOR_MODULES = 2
"""A 25A 2-pole modular contactor is two modules wide. SOURCE: the modular
contactor family (Schneider iCT 2P, ABB ESB 2P, and the generic 2P the BOM
buys) is built on 2 modules for 2 poles. CONFIDENCE: inference from the family;
the BOM line carries no SKU. Sizes one reference solid and nothing else."""

FUSE_MODULES = 1
"""A 10 x 38 DIN fuse holder, one pole, is one module. SOURCE: the 10x38
fuse-holder family. CONFIDENCE: standard."""

# ---- the representative parts: no SKU on the BOM ----------------------------
SSR_ENV = (30.0, 91.0, 64.0)
"""(along the rail, across the rail, depth off the RAIL face) of a 25A SSR
with its heatsink on a DIN clip. SOURCE: Lorentzzi DSSR-25DA listing,
"91*30*64 mm", a DIN-rail SSR with the heatsink fitted; orientation ASSUMED
30 along the rail, and the 64 taken off the rail face rather than the plate. CONFIDENCE: representative, MEASURE when the ordered part
is in hand. The BOM line is "Solid state relay, 25A, with heatsink" with no
SKU. Drives only its own reference solid."""

BUSBAR_ENV = (78.0, 35.0, 10.0)
"""(along, across, depth off the RAIL face) of an 8-way brass earth bar on a
DIN clip. SOURCE: VXB 8-position DIN rail terminal block listing, 78 x 35 x
10 mm; which axis is which is ASSUMED, and the depth is taken off the rail
face, not the plate. CONFIDENCE: representative, LOW, MEASURE when in hand.
Drives only its own reference solid; the star point is where the bar is, not
how big it is."""

CT_ENV = (34.0, 32.0, 23.5)
"""(across the conductor, along the conductor, thickness) of a split-core CT.
SOURCE: YHDC SCT013 datasheet drawing, front view 34 x 32, side view 23.5
with the hinge; window 13 x 13. CONFIDENCE: representative datasheet. The BOM
line is "Split-core current transformer, 30A" with no SKU; the SCT013-030 is
what that line buys on Amazon. MEASURE when in hand."""

CT_WINDOW = 13.0
"""Conductor window of the CT, square. SOURCE: YHDC SCT013 datasheet.
CONFIDENCE: datasheet. Passes one insulated conductor up to 13mm; the spindle
leg and the extractor's line conductor both do."""

# ---- the extractor receptacle (I92) -----------------------------------
BOX_ENV = (2.125 * IN, 4.0 * IN, 1.875 * IN)
"""(width, height, depth) of a 1-gang steel handy box, stood vertical.
SOURCE: Hubbell-Raco 660, 4 x 2-1/8 x 1-7/8 in, distributor listings (Platt
0052363, Ferguson R660). CONFIDENCE: catalog. Surface box, so the receptacle
is the extractor's own plug into a steel box bonded to the star."""

RECEPTACLE = "NEMA 5-15R single, in a Raco 660 handy box with a raised cover"
"""SOURCE: task C05 spec (I92), "a single NEMA 5-15R in a surface box".
CONFIDENCE: ruling. The CT 15's plug is 5-15P (params.ct15_plug_lead)."""

# ---- plate to spine ----------------------------------------------------
SPINE_SCREW_D = SCREW_CLEAR_D
SPINE_SCREW_CBORE_D = SCREW_CBORE_D
SPINE_SCREW_CBORE_DEPTH = PLATE_T / 2
SPINE_SCREW_LEN_MAX = PLATE_T + DATUMS.t / 2
"""Same fastening as the drive's plate: carcass clearance and counterbore on
the device face, screw no longer than the plate plus half the spine. SOURCE:
carcass standard and vfd_mount. CONFIDENCE: derived."""

# ---- the rails, and what rides them --------------------------------------


@dataclass(frozen=True)
class Rail:
    label: str          # assembly label of the rail solid
    name: str           # the callout: ALWAYS-LIVE | CONTACTOR
    y_local: float      # rail centreline above the plate's bottom edge
    loads: tuple[str, ...]


RAILS: tuple[Rail, ...] = (
    Rail(RAIL_LIVE_NAME, "ALWAYS-LIVE", RAIL_LIVE_Y,
         ("PC brick", "ESP32 supply", "mast feed", "stock wash",
          "contactor coil (through the E-stop loop and the arm key)")),
    Rail(RAIL_CONTACTOR_NAME, "CONTACTOR", RAIL_CONTACTOR_Y,
         ("VFD", "motion controller", "extractor via SSR")),
)
"""Which loads ride which rail. SOURCE: brief v6/v7 §distribution, "an
always-live spur carries the mini PC, the station microcontroller, and the
mast. The contactor carries only what moves or cuts." CONFIDENCE: ruling. The
stock wash is a light in a bay, not a thing that moves or cuts, so it is
always-live with the mast. The coil supply is always-live by necessity: a
contactor whose coil is downstream of itself never pulls in."""

CROSSING_RAIL: dict[str, str] = {
    "EXTRACTOR MAINS": "CONTACTOR",
    "MAST FEED": "ALWAYS-LIVE",
    "STOCK WASH": "ALWAYS-LIVE",
    "CONSOLE STOP": "ALWAYS-LIVE",
    "CONSOLE CONTROL": "CONTACTOR",
    "CONSOLE INSTRUMENT": "ALWAYS-LIVE",
    "PENDANT AND USB": "CONTACTOR + ALWAYS-LIVE",
}
"""Which rail each of the spine's seven crossings rides, by label. Keyed to
``spine_panel.CROSSINGS`` and checked against it, so a crossing added there
without a line here fails the gate rather than leaving the schedule short."""

CROSSING_FEEDS: dict[str, str] = {
    "EXTRACTOR MAINS": "the receptacle on the lungs face, from the SSR",
    "MAST FEED": "mast strip 3-core and camera USB, from the always-live spur",
    "STOCK WASH": "stock bay wash light, from the always-live spur",
    "CONSOLE STOP": "E-stop contacts in the contactor coil loop; the coil is always-live, the E-stop opens it",
    "CONSOLE CONTROL": "motion controller signals; the controller itself is contactor-fed",
    "CONSOLE INSTRUMENT": "ESP32 to the instrument panel; always-live so the panel reports with the door open",
    "PENDANT AND USB": "pendant to the motion controller (CONTACTOR) and USB to the PC (ALWAYS-LIVE), one gland",
}


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the
# block above and on Datums.
# ====================================================================


def plate_x(d: Datums = DATUMS) -> tuple[float, float]:
    """Station X span of the plate: from the drive's keep-out snapped up to
    the grid, to the partition's housing snapped down. Both ends are air."""
    x0 = snap_up(d.vfd_keepout_x[1])
    x1 = snap_dn(d.brain_split_x - DADO_W / 2)
    return (x0, x1)


def plate_z(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Z span: the band between the two crossing rows."""
    return (d.deck_top + ROW_LOW_Z + ROW_CLEAR, d.deck_top + ROW_HIGH_Z - ROW_CLEAR)


def plate_y(d: Datums = DATUMS) -> tuple[float, float]:
    """Station Y span: flat on the spine's rear face."""
    y0 = d.y_spine + d.t
    return (y0, y0 + PLATE_T)


def plate_size(d: Datums = DATUMS) -> tuple[float, float]:
    x0, x1 = plate_x(d)
    z0, z1 = plate_z(d)
    return (x1 - x0, z1 - z0)


def device_face_y(d: Datums = DATUMS) -> float:
    """Station Y of the plate's rear face, where the rails sit."""
    return plate_y(d)[1]


def rail_x_local(d: Datums = DATUMS) -> tuple[float, float]:
    w, _h = plate_size(d)
    return (RAIL_END_INSET, w - RAIL_END_INSET)


def rail_length(d: Datums = DATUMS) -> float:
    a, b = rail_x_local(d)
    return b - a


@dataclass(frozen=True)
class Env:
    """One reference solid on the plate, in plate-local terms.

    ``along`` / ``across`` / ``depth`` are the box's extent along the rail
    (station X), across it (station Z) and off the mounting face (station +Y).
    ``on_rail`` names the rail it clips to, or None for a part held to the
    plate face itself. ``x0`` is the local X of its left edge; ``y_c`` the
    local Y of its centre.
    """

    label: str
    callout: str
    along: float
    across: float
    depth: float
    on_rail: str | None
    x0: float
    y_c: float
    depth_from_rail: bool = False
    """False: ``depth`` is from the PLATE face, the way DIN 43880 states a
    modular device. True: from the RAIL's outer face, the way a listing for a
    clip-on part states it when it states it at all; conservative by RAIL_D."""

    @property
    def x1(self) -> float:
        return self.x0 + self.along

    @property
    def x_c(self) -> float:
        return self.x0 + self.along / 2


def _rail(name: str) -> Rail:
    return next(r for r in RAILS if r.name == name)


def envelopes(d: Datums = DATUMS) -> list[Env]:
    """Every reference solid, laid out. The layout is a list, not a drawing:
    change an envelope and its neighbours re-space."""
    rx0, rx1 = rail_x_local(d)
    live = _rail("ALWAYS-LIVE")
    ctr = _rail("CONTACTOR")
    out: list[Env] = []

    # -- CONTACTOR rail, left to right ------------------------------------
    # The spindle CT on the plate face at the drive's end, left of the rail.
    ct_x0 = (rx0 - GROUP_GAP - CT_ENV[0]) if rx0 - GROUP_GAP - CT_ENV[0] > 0 else 0.0
    out.append(Env("ct_env_spindle", "CT SPINDLE LEG", CT_ENV[0], CT_ENV[1], CT_ENV[2],
                   None, ct_x0, ctr.y_local))

    x = rx0
    out.append(Env("fuse_env_vfd", "FUSE VFD", FUSE_MODULES * DIN_MODULE_W,
                   DIN_DEVICE_H, DIN_DEVICE_D, ctr.name, x, ctr.y_local))
    x += FUSE_MODULES * DIN_MODULE_W
    out.append(Env("fuse_env_extractor", "FUSE EXTRACTOR", FUSE_MODULES * DIN_MODULE_W,
                   DIN_DEVICE_H, DIN_DEVICE_D, ctr.name, x, ctr.y_local))
    x += FUSE_MODULES * DIN_MODULE_W + GROUP_GAP
    ssr = Env("ssr_env", "SSR EXTRACTOR", SSR_ENV[0], SSR_ENV[1], SSR_ENV[2],
              ctr.name, x, ctr.y_local, depth_from_rail=True)
    out.append(ssr)

    # The contactor: rightmost, nearest the transit and the operator (I74).
    cw = CONTACTOR_MODULES * DIN_MODULE_W
    out.append(Env("contactor_env", "CONTACTOR", cw, DIN_DEVICE_H, DIN_DEVICE_D,
                   ctr.name, rx1 - cw, ctr.y_local))

    # -- ALWAYS-LIVE rail, left to right -----------------------------------
    x = rx0
    out.append(Env("pe_busbar_env", "PE STAR", BUSBAR_ENV[0], BUSBAR_ENV[1], BUSBAR_ENV[2],
                   live.name, x, live.y_local, depth_from_rail=True))
    x += BUSBAR_ENV[0] + GROUP_GAP
    out.append(Env("fuse_env_spur", "FUSE ALWAYS-LIVE SPUR", FUSE_MODULES * DIN_MODULE_W,
                   DIN_DEVICE_H, DIN_DEVICE_D, live.name, x, live.y_local))

    return out


def env_by_label(label: str, d: Datums = DATUMS) -> Env:
    return next(e for e in envelopes(d) if e.label == label)


def _box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Part:
    """A station-coordinate box from three spans."""
    return Box(x[1] - x[0], y[1] - y[0], z[1] - z[0],
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x[0], y[0], z[0]))
    )


def env_station(e: Env, d: Datums = DATUMS) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Station (x, y, z) spans of one envelope. A device on a rail starts at
    the rail's outer face, so it never shares volume with the rail, and ends
    at its depth from the plate face (DIN 43880) or from the rail face (a
    clip-on listing, ``depth_from_rail``); a part on the plate face starts at
    the face."""
    px0, _px1 = plate_x(d)
    pz0, _pz1 = plate_z(d)
    face = device_face_y(d)
    y0 = face + (RAIL_D if e.on_rail else 0.0)
    y1 = face + e.depth + (RAIL_D if e.depth_from_rail else 0.0)
    return (
        (px0 + e.x0, px0 + e.x1),
        (y0, y1),
        (pz0 + e.y_c - e.across / 2, pz0 + e.y_c + e.across / 2),
    )


def env_centre(e: Env, d: Datums = DATUMS) -> tuple[float, float, float]:
    (x0, x1), (y0, y1), (z0, z1) = env_station(e, d)
    return ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)


def rail_station(r: Rail, d: Datums = DATUMS) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    px0, _ = plate_x(d)
    pz0, _ = plate_z(d)
    a, b = rail_x_local(d)
    face = device_face_y(d)
    return (
        (px0 + a, px0 + b),
        (face, face + RAIL_D),
        (pz0 + r.y_local - RAIL_H / 2, pz0 + r.y_local + RAIL_H / 2),
    )


def transit_centre(d: Datums = DATUMS) -> tuple[float, float, float]:
    """Centre of the partition's transit opening, station coordinates: on the
    split plane, from the spine's rear face to TRANSIT_D past it."""
    z0, z1 = brain_partition.transit_z(d)
    y0 = d.y_spine + d.t
    return (d.brain_split_x, y0 + brain_partition.TRANSIT_D / 2, (z0 + z1) / 2)


def contactor_to_transit(d: Datums = DATUMS) -> float:
    cx, cy, cz = env_centre(env_by_label("contactor_env", d), d)
    tx, ty, tz = transit_centre(d)
    return ((cx - tx) ** 2 + (cy - ty) ** 2 + (cz - tz) ** 2) ** 0.5


def bore_axis(label: str, d: Datums = DATUMS) -> tuple[float, float]:
    """Station (x, z) of a spine crossing's bore axis."""
    c = next(c for c in CROSSINGS if c.label == label)
    return (crossing_x(d)[label], d.deck_top + ROW_Z[c.row])


def receptacle_station(d: Datums = DATUMS) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The handy box on the lungs face of the spine, centred on the
    EXTRACTOR MAINS bore axis, its back on the spine's front face."""
    bx, bz = bore_axis("EXTRACTOR MAINS", d)
    w, h, dep = BOX_ENV
    return (
        (bx - w / 2, bx + w / 2),
        (d.y_spine - dep, d.y_spine),
        (bz - h / 2, bz + h / 2),
    )


def receptacle_centre(d: Datums = DATUMS) -> tuple[float, float, float]:
    (x0, x1), (y0, y1), (z0, z1) = receptacle_station(d)
    return ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)


def spine_screws_local(d: Datums = DATUMS) -> list[tuple[float, float]]:
    """Plate-to-spine screws: two columns at the carcass edge distance, on
    the carcass fastener rhythm, outboard of both rails."""
    w, h = plate_size(d)
    out: list[tuple[float, float]] = []
    for x in (SCREW_EDGE_OFF, w - SCREW_EDGE_OFF):
        for p in screw_positions(h):
            out.append((x, p))
    return out


def plane(d: Datums = DATUMS) -> Plane:
    """The plate's frame: local +X to station +X, local +Y up, thickness into
    -Y so the plate lands on the spine's rear face with its Z = 0 face looking
    at the devices. Origin at the datum corner."""
    return Plane(
        origin=(plate_x(d)[0], plate_y(d)[1], plate_z(d)[0]),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def build(d: Datums = DATUMS) -> Part:
    """The plate, flat in panel-local coordinates."""
    w, h = plate_size(d)
    part = panel(w, h, PLATE_T)

    # Plate to spine: through clearance, counterbored on the device face.
    for x, y in spine_screws_local(d):
        part -= bore(x, y, SPINE_SCREW_D, thickness=PLATE_T)
        part -= bore(x, y, SPINE_SCREW_CBORE_D, thickness=PLATE_T,
                     depth=SPINE_SCREW_CBORE_DEPTH, side="back")

    # No apertures. Nothing passes through this plate; every run leaves the
    # sealed zone through the spine's own crossings, above and below it.
    return part


def place(part: Part | None = None, d: Datums = DATUMS) -> Part:
    """The flat plate stood up in station coordinates."""
    part = build(d) if part is None else part
    return plane(d) * part


def build_rails(d: Datums = DATUMS) -> list[tuple[str, Part]]:
    """Both rails as reference solids, STATION coordinates."""
    return [(r.label, _box(*rail_station(r, d))) for r in RAILS]


def build_envelopes(d: Datums = DATUMS) -> list[tuple[str, Part]]:
    """Every device envelope, STATION coordinates."""
    return [(e.label, _box(*env_station(e, d))) for e in envelopes(d)]


def build_receptacle(d: Datums = DATUMS) -> Part:
    """The handy box, STATION coordinates."""
    return _box(*receptacle_station(d))


def placed_all(d: Datums = DATUMS) -> list[tuple[str, str, Part]]:
    """(label, group, part) for everything this module puts in the assembly."""
    out: list[tuple[str, str, Part]] = [(PART_NAME, "carcass", place(d=d))]
    out += [(label, "steel", part) for label, part in build_rails(d)]
    out += [(label, "reference", part) for label, part in build_envelopes(d)]
    out.append((RECEPTACLE_NAME, "steel", build_receptacle(d)))
    return out


def joint_table(d: Datums = DATUMS) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples, the
    shape ``drawers.joint_table`` uses. Every joint here is a face: nothing on
    this plate shares volume with anything, by construction."""
    out: list[tuple] = [
        ("spine_panel", PART_NAME, "butt", None, 0.0, 0.0,
         "plate flat on the spine's rear face, screwed through; the spine cuts nothing"),
        ("spine_panel", RECEPTACLE_NAME, "bearing", None, 0.0, 0.0,
         "box back flat on the spine's front face over the EXTRACTOR MAINS gland"),
    ]
    for r in RAILS:
        out.append((PART_NAME, r.label, "bearing", None, 0.0, 0.0,
                    f"{r.name} rail screwed to the plate through its own slots"))
    for e in envelopes(d):
        if e.on_rail:
            out.append((_rail(e.on_rail).label, e.label, "bearing", None, 0.0, 0.0,
                        f"{e.callout} clipped to the {e.on_rail} rail"))
        else:
            out.append((PART_NAME, e.label, "bearing", None, 0.0, 0.0,
                        f"{e.callout} saddled to the plate face"))
    return out


# ---------------------------------------------------------------- schedule


def wire_schedule(d: Datums = DATUMS) -> list[str]:
    """The wiring schedule, one line each: the two rails and their loads,
    then which rail each of the spine's seven crossings rides."""
    lines: list[str] = [f"WIRE SCHEDULE {PART_NAME}: two rails, PE_SWITCHED = {PE_SWITCHED}"]
    for r in RAILS:
        lines.append(f"rail {r.name}: " + ", ".join(r.loads))
    lines.append("PE star: " + d.s.bond_star_point + "; never on the bar: "
                 + "; ".join(d.s.bond_excluded))
    for c in CROSSINGS:
        rail = CROSSING_RAIL.get(c.label, "UNASSIGNED")
        feeds = CROSSING_FEEDS.get(c.label, "")
        lines.append(
            f"crossing {c.label} ({c.zone}/{c.bay}, {c.kind} {BORE_D[c.kind]:.0f}mm): "
            f"rides {rail}; {feeds}"
        )
    lines.append(
        "transit carries only low voltage: the CT lead, the ESP32's DC, the PC "
        "brick's DC and the motion controller's DC cross the partition there; no mains does"
    )
    lines.append(
        "not modelled: the PC brick (console PC is OPEN, 2026-09-02) and the ESP32 "
        "supply, both ALWAYS-LIVE loads on the lower rail"
    )
    return lines


# ---------------------------------------------------------------- checks


def check_mains_backplate(d: Datums = DATUMS) -> list[str]:
    """What this part has to be true for. The assembly's interference check
    owns whether anything here hits a neighbour; these are the things that
    are wrong before the solids are compared."""
    notes: list[str] = []
    w, h = plate_size(d)
    px0, px1 = plate_x(d)
    pz0, pz1 = plate_z(d)
    k0, k1 = d.vfd_keepout_x
    rear_face = d.y_spine + d.t
    door = d.y_rear - brain_partition.DOOR_LANDING

    # -- doctrine first
    if PE_SWITCHED:
        notes.append(
            "PE_SWITCHED is True. PE IS NEVER SWITCHED: the contactor drops L and "
            "N only, or opening the door removes the static path as it exposes the "
            "machine. Set it back to False and buy the 2-pole."
        )
    ctr_loads = " ".join(_rail("CONTACTOR").loads).lower()
    for compute in ("pc", "esp32", "console", "instrument"):
        if compute in ctr_loads:
            notes.append(
                f"the CONTACTOR rail carries '{compute}': guards kill motion and "
                "cutting, never compute. Move it to ALWAYS-LIVE."
            )
    for must in ("VFD", "motion controller", "extractor"):
        if not any(must.lower() in l.lower() for l in _rail("CONTACTOR").loads):
            notes.append(f"'{must}' is not on the CONTACTOR rail; the interlock has to drop it")
    for must in ("PC brick", "ESP32", "mast", "stock wash"):
        if not any(must.lower() in l.lower() for l in _rail("ALWAYS-LIVE").loads):
            notes.append(f"'{must}' is not on the ALWAYS-LIVE rail")

    # -- the schedule covers exactly the spine's crossings
    labels = {c.label for c in CROSSINGS}
    for missing in sorted(labels - set(CROSSING_RAIL)):
        notes.append(f"crossing {missing} has no rail in the wire schedule")
    for extra in sorted(set(CROSSING_RAIL) - labels):
        notes.append(f"the wire schedule names a crossing the spine does not cut: {extra}")

    # -- the plate sits in the sealed zone, clear of the housing and the rows
    if px0 < k1 - 1e-6:
        notes.append(f"plate starts at x {px0:.1f}, inside the drive's keep-out ending {k1:.1f}")
    if px1 > d.brain_split_x - DADO_W / 2 + 1e-6:
        notes.append(
            f"plate reaches x {px1:.1f}, over the partition housing starting "
            f"{d.brain_split_x - DADO_W / 2:.1f}"
        )
    for c in CROSSINGS:
        if c.zone != "sealed":
            continue
        bx, bz = bore_axis(c.label, d)
        r = BORE_D[c.kind] / 2
        if px0 - 1e-6 <= bx <= px1 + 1e-6 and pz0 - r - BORE_CLEAR_MIN < bz < pz1 + r + BORE_CLEAR_MIN:
            notes.append(
                f"the plate covers or crowds the {c.label} bore at z {bz:.1f}: its "
                f"gland nut needs {BORE_CLEAR_MIN:.0f}mm past the bore's edge"
            )
    if pz1 > d.top_z[0] - 1e-6 or pz0 < d.deck_top + 1e-6:
        notes.append(f"plate z {pz0:.1f}..{pz1:.1f} leaves the band {d.deck_top:.1f}..{d.top_z[0]:.1f}")
    if h <= 0 or w <= 0:
        notes.append("the plate has no area: the rows or the zone have closed on it")
        return notes

    # -- every envelope: in the zone, behind the spine, ahead of the door,
    #    under the cap, and on the plate
    for label, box in build_rails(d) + build_envelopes(d):
        bb = box.bounding_box()
        if bb.min.X < k1 - 1e-6 or bb.max.X > d.brain_split_x + 1e-6:
            notes.append(f"{label} spans x {bb.min.X:.1f}..{bb.max.X:.1f}, outside the sealed zone {k1:.1f}..{d.brain_split_x:.1f}")
        if bb.min.Y < rear_face - 1e-6:
            notes.append(f"{label} reaches y {bb.min.Y:.1f}, into the spine")
        if bb.max.Y > door + 1e-6:
            notes.append(f"{label} reaches y {bb.max.Y:.1f}, into the rear door's landing at {door:.1f}")
        if bb.max.Z > d.top_z[0] - 1e-6:
            notes.append(f"{label} reaches z {bb.max.Z:.1f}, above the cap's underside")
        if bb.min.X < px0 - 1e-6 or bb.max.X > px1 + 1e-6 or bb.min.Z < pz0 - 1e-6 or bb.max.Z > pz1 + 1e-6:
            notes.append(f"{label} hangs off the plate (x {bb.min.X:.1f}..{bb.max.X:.1f}, z {bb.min.Z:.1f}..{bb.max.Z:.1f})")

    # -- envelopes do not crowd each other along a rail
    envs = envelopes(d)
    for i, a in enumerate(envs):
        for b in envs[i + 1:]:
            ax = env_station(a, d)
            bx = env_station(b, d)
            if (ax[0][1] > bx[0][0] + 1e-6 and bx[0][1] > ax[0][0] + 1e-6
                    and ax[2][1] > bx[2][0] + 1e-6 and bx[2][1] > ax[2][0] + 1e-6):
                notes.append(f"{a.label} and {b.label} overlap on the plate face")

    # -- the contactor is where it can be heard (I74)
    dist = contactor_to_transit(d)
    if dist > CONTACTOR_TRANSIT_MAX:
        notes.append(
            f"the contactor's centre is {dist:.0f}mm from the transit gap, over "
            f"{CONTACTOR_TRANSIT_MAX:.0f}: its click is not leaving toward the operator"
        )
    ctr = env_by_label("contactor_env", d)
    if any(e.on_rail == "CONTACTOR" and e.x_c > ctr.x_c for e in envs):
        notes.append("a device sits right of the contactor on its rail; the contactor is the rightmost by ruling")

    # -- the receptacle sits on the gland's axis, on the lungs side (I92)
    bx, bz = bore_axis("EXTRACTOR MAINS", d)
    rx, ry, rz = receptacle_centre(d)
    if abs(rx - bx) > 1.0 or abs(rz - bz) > 1.0:
        notes.append(f"the receptacle box centre ({rx:.1f}, {rz:.1f}) is off the EXTRACTOR MAINS axis ({bx:.1f}, {bz:.1f})")
    (bx0, bx1), (by0, by1), (bz0, bz1) = receptacle_station(d)
    if by1 > d.y_spine + 1e-6:
        notes.append("the receptacle box is not on the lungs side of the spine")
    if bx0 < d.lungs_x[0] - 1e-6 or bx1 > d.lungs_x[1] + 1e-6:
        notes.append(f"the receptacle box x {bx0:.1f}..{bx1:.1f} leaves the lungs bay {d.lungs_x[0]:.1f}..{d.lungs_x[1]:.1f}")
    if bz0 < d.deck_top - 1e-6:
        notes.append("the receptacle box reaches below the deck")
    room = d.front_bay_d - BOX_ENV[2] - d.s.extractor_env[0]
    if room < 0:
        notes.append(
            f"the receptacle box stands {BOX_ENV[2]:.1f}mm into the lungs bay and the "
            f"extractor is {d.s.extractor_env[0]:.0f} long in a {d.front_bay_d:.0f} bay: "
            f"{-room:.0f}mm short"
        )

    # -- what the ordered parts have not told us yet
    notes.append(
        "the SSR-with-heatsink, the 8-way PE bar and the spindle CT are modelled "
        f"from representative listings ({SSR_ENV[0]:.0f}x{SSR_ENV[1]:.0f}x{SSR_ENV[2]:.0f}, "
        f"{BUSBAR_ENV[0]:.0f}x{BUSBAR_ENV[1]:.0f}x{BUSBAR_ENV[2]:.0f}, "
        f"{CT_ENV[0]:.0f}x{CT_ENV[1]:.0f}x{CT_ENV[2]:.1f}) because the BOM lines carry "
        "no SKU. MEASURE THIS when they arrive; none of them moves the plate."
    )

    # -- the schedule, kept visible on every run
    notes.append("WIRE SCHEDULE, standing note. " + " | ".join(wire_schedule(d)))

    if not fits((w, h), SHEET_5X5_BALTIC):
        notes.append(f"plate blank {w:.0f} x {h:.0f} does not come out of a 5x5 sheet")

    return notes


if __name__ == "__main__":
    d = DATUMS
    flat = build(d)
    placed = place(flat, d)
    bb = placed.bounding_box()
    w, h = plate_size(d)

    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {PLATE_T:.0f}, on the spine's rear face"
          f"{'  (one STOCK_MODULE wide)' if abs(w - STOCK_MODULE) < 1e-6 else ''}")
    print(
        f"  placed  x {bb.min.X:.1f}..{bb.max.X:.1f}  y {bb.min.Y:.1f}..{bb.max.Y:.1f}  "
        f"z {bb.min.Z:.1f}..{bb.max.Z:.1f}   volume {flat.volume / 1000:.1f} cm3"
    )
    print(
        f"  {len(spine_screws_local(d))} screws into the spine, {SPINE_SCREW_D:.1f} clear, "
        f"{SPINE_SCREW_CBORE_D:.0f} x {SPINE_SCREW_CBORE_DEPTH:.0f} cbore on the device face; "
        f"screw no longer than {SPINE_SCREW_LEN_MAX:.0f}"
    )
    for r in RAILS:
        (x0, x1), (y0, y1), (z0, z1) = rail_station(r, d)
        print(f"  {r.label:<20} {r.name:<12} {x1 - x0:.0f} long  x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  z {z0:.1f}..{z1:.1f}")
    for e in envelopes(d):
        (x0, x1), (y0, y1), (z0, z1) = env_station(e, d)
        print(
            f"    {e.label:<18} {e.callout:<22} {e.along:.1f} x {e.across:.1f} x {e.depth:.1f}  "
            f"x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  z {z0:.1f}..{z1:.1f}  "
            f"{'on ' + e.on_rail if e.on_rail else 'on the plate face'}"
        )
    tx, ty, tz = transit_centre(d)
    print(f"  contactor centre {contactor_to_transit(d):.1f}mm from the transit gap at ({tx:.1f}, {ty:.1f}, {tz:.1f}); limit {CONTACTOR_TRANSIT_MAX:.0f}")
    (x0, x1), (y0, y1), (z0, z1) = receptacle_station(d)
    ax, az = bore_axis("EXTRACTOR MAINS", d)
    print(
        f"  {RECEPTACLE_NAME}: {RECEPTACLE}; box {BOX_ENV[0]:.1f} x {BOX_ENV[1]:.1f} x {BOX_ENV[2]:.1f}  "
        f"x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  z {z0:.1f}..{z1:.1f}  on the EXTRACTOR MAINS axis ({ax:.1f}, {az:.1f}), lungs side"
    )

    print()
    for line in wire_schedule(d):
        print("  " + line)

    found = check_mains_backplate(d)
    if found:
        print(f"\n{len(found)} mains backplate note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno mains backplate constraint violations")

    for p in export_part(flat, PART_NAME):
        print(f"wrote {p}")
    for label, part in build_rails(d) + build_envelopes(d) + [(RECEPTACLE_NAME, build_receptacle(d))]:
        for p in export_part(part, label, dxf=False):
            print(f"wrote {p}   (STEP only: reference solid, not a sheet part)")
