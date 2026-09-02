"""Shared spine for the Shapeoko 5 Pro 4x4 station carcass.

This module holds interfaces only. It contains no part geometry. Every part
under ``stations/cnc_shapeoko/parts/`` imports its datums and its joinery from
here so that no two parts do the same arithmetic twice and disagree about the
answer.

Read this docstring before writing a part. It is the contract.


THE DATUM
=========

One right-handed coordinate system, millimetres, shared by every part.

    origin  the floor, at the intersection of the LEFT inner leg face and the
            FRONT inner leg face of the Shapeoko leg frame

    +X      to the RIGHT, as seen by an operator standing at the front of the
            machine.  X runs 0 .. leg_x_inner.
    +Y      to the REAR, away from the operator.  Y runs 0 .. leg_y_inner.
            The brain band is at high Y.  The open stock face is at Y = 0.
    +Z      UP from the floor.  Z runs 0 .. clear_h (underside of the machine
            frame).  Nothing the carcass owns lives above clear_h.

leg_x_inner is the one unmeasured number in the whole model.  Nothing in this
module hardcodes around it.  When Jared's tape lands, one line in ``params.py``
changes and every datum below moves with it.


THE BANDS
=========

Y splits into two bands at the spine panel:

    front band   Y 0 .. y_spine     three bays, all opening to the FRONT
    spine        Y y_spine .. +T    the full-width structural divider
    brain band   Y y_spine+T .. y_rear    VFD, motion controller, mini PC,
                                          distribution.  Rear-panel access.

X splits the front band into three bays between four vertical panels:

    wall 0   left end wall           x 0 .. T
    LUNGS    CT 36 EI on slides      clear width bay_lungs_w
    wall 1   lungs/stock divider
    STOCK    HALF blanks on edge     clear width = WHATEVER IS LEFT
    wall 2   stock/hands divider
    HANDS    drawers                 clear width bay_hands_w
    wall 3   right end wall          x leg_x_inner-T .. leg_x_inner

STOCK IS THE BAY THAT GIVES.  Lungs is pinned to the left end and sized by the
extractor.  Hands is pinned to the right end and sized by the drawer.  Stock is
the remainder, and it is the only bay whose width changes when leg_x_inner
changes.  ``Datums.stock_clear_w`` is derived, never read from params.


ALL THREE BAYS OPEN TO THE FRONT
================================

The v4 brief labels the left face "Lungs" and the right face "Hands".  Those
labels stay as callouts and service zones.  The bays themselves load from the
front, for reasons that are geometry rather than taste:

  * the extractor's 630mm long axis has to run in Y (params' own check compares
    extractor_env[0] against front_bay_d()), so the unit pulls toward the
    operator, not sideways
  * a drawer pulling out the right face would be 882mm wide and 400 deep, and
    the BOM buys 500mm slides
  * end walls that are also doors are not end walls, and the carcass loses the
    two panels that brace it in Y-Z

The brief's operator sentence survives unchanged: standing front right, drawers
are at hand and material is a step to the left.


THE PANEL CONVENTION
====================

Every sheet part is modelled FLAT, in its own local coordinates:

    local origin    lower-left corner of the cut blank
    local +X        blank width      (0 .. w)
    local +Y        blank height     (0 .. h)
    local +Z        material thickness (0 .. t), the "back" face at Z=0

Draw the part flat.  Cut every joint flat.  Then hand it to
``Datums.<name>_plane`` to be stood up in station coordinates.  Two things fall
out of this for free: the joinery helpers below are all 2D-in-XY and need no
orientation argument, and the DXF flat pattern is the part as drawn rather than
a projection that has to be trusted.


WHAT DERIVES FROM WHAT
======================

Nothing in a part file may contain a dimension literal.  Joint geometry comes
from ``T`` (= CARCASS_T).  Fastener spacing comes from ``T``.  Bay boundaries
come from ``Datums``.  Tool facts (cutter diameter, kerf, screw diameters) are
in the TOOLING block below because they are properties of the machine and the
fastener, not of the design; they are the only numbers here that do not move
when the design moves.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, ceil, degrees, hypot
from pathlib import Path

from build123d import (
    Align,
    Box,
    Cylinder,
    ExportDXF,
    Face,
    Location,
    Part,
    Plane,
    Shape,
    Unit,
    export_step,
)

from lib.house import CARCASS_T, GRID, PANEL_T, SHEET_5X5_BALTIC, fits
from stations.cnc_shapeoko.params import STATION, Station

__all__ = [
    "T",
    "PT",
    "ROUTER_D",
    "ROUTER_R",
    "KERF_LASER",
    "DADO_FIT",
    "DADO_W",
    "DADO_D",
    "RABBET_D",
    "RABBET_W",
    "TAB_W",
    "TAB_FIT",
    "SCREW_D",
    "SCREW_PILOT_D",
    "SCREW_CLEAR_D",
    "SCREW_CBORE_D",
    "GX16_PANEL_D",
    "GLAND_M20_D",
    "GLAND_M25_D",
    "SCREW_PITCH",
    "SCREW_END_INSET",
    "SCREW_EDGE_OFF",
    "HOUSE_ENGAGE",
    "PLINTH_H",
    "ISOLATOR_H",
    "SERVICE_GAP",
    "TOP_GAP_MIN",
    "LEG_SLOT_V",
    "Datums",
    "DATUMS",
    "snap_up",
    "snap_dn",
    "panel",
    "groove",
    "rabbet",
    "through_slot",
    "finger_layout",
    "finger_slots",
    "finger_notches",
    "screw_positions",
    "screw_line",
    "bore",
    "relief",
    "flat_pattern",
    "export_part",
    "EXPORT_DIR",
    "check_carcass",
]


# ---------------------------------------------------------------- tooling
# Facts about the cutter, the laser and the fastener. Not design parameters:
# these do not move when the design moves. Everything else in this file does.

ROUTER_D = 6.35     # 1/4in downcut compression, the carcass cutter
ROUTER_R = ROUTER_D / 2
KERF_LASER = 0.15   # 3mm acrylic on the Universal, measured on scrap

SCREW_D = 5.0           # 5mm Confirmat / M5 into the panel edge
SCREW_PILOT_D = 3.0
SCREW_CLEAR_D = 5.4
SCREW_CBORE_D = 10.0

GX16_PANEL_D = 16.0     # GX16 aviation shell, panel cutout. The house connector.
GLAND_M20_D = 20.0      # M20 cable gland, 6-12mm cable. A mains flex or a
                        # pre-terminated pendant lead; the default sealed crossing.
GLAND_M25_D = 25.0      # M25, 13-18mm cable. Only where a bundle needs it.


# ---------------------------------------------------------------- material
T = CARCASS_T       # 18mm Baltic birch. Every joint below is a function of this.
PT = PANEL_T        # 3mm smoked acrylic


# ---------------------------------------------------------------- joinery
# All of it derives from T. Change CARCASS_T to 15 and every joint regenerates.

DADO_FIT = 0.2      # plywood runs undersize; a dado cut exactly T is a gap
DADO_W = T + DADO_FIT
DADO_D = T / 3      # the standard third-of-thickness housing
RABBET_D = T / 2
RABBET_W = T + DADO_FIT

TAB_W = T * 2       # nominal finger width; finger_layout rounds to fit the edge
TAB_FIT = 0.15      # per side, on a slot receiving a tab

SCREW_PITCH = T * 8         # 144mm along a glued-and-screwed edge
SCREW_END_INSET = T * 1.5   # first and last fastener in from the corner
SCREW_EDGE_OFF = T / 2      # on the centreline of the panel being screwed into

HOUSE_ENGAGE = DADO_D
"""How far a housed panel edge enters the part that receives it.

A panel's BLANK is its clear span plus this much at every housed edge, while its
DATUM stays the face. Nothing in ``Datums`` moves: ``spine_size`` is still the
clear span between the wall faces, and the spine's blank is that plus engagement
where the deck and the top cap house it. Set this to 0 and every joint in the
carcass becomes a butt joint without a datum changing.
"""


# ---------------------------------------------------------------- stack-up
# The vertical budget. clear_h is the ceiling and it is a medium-confidence
# estimate, so the carcass is built bottom-up from its contents and the leftover
# becomes a reveal. See Datums.top_gap.

PLINTH_H = GRID * 3     # 60mm toe kick. Levellers and the low air intake.
ISOLATOR_H = 15.0       # rubber isolation feet under the extractor platform
SERVICE_GAP = GRID      # clearance above the tallest thing in any bay
TOP_GAP_MIN = GRID      # the carcass never touches the machine frame

LEG_SLOT_V = 60.0
"""Vertical travel in the leg-tie slots.

table_h matches neither published leg configuration; levelling feet swing the
frame by 52mm and nobody has looked yet. The carcass does not care: it is built
from the floor up, the leg ties are slotted, and the swing lands in the slot and
in top_gap. 60 > 52 with room either side.
"""


# ---------------------------------------------------------------- grid


def snap_up(mm: float) -> float:
    """Round up to the 20mm bench grid."""
    return ceil(mm / GRID - 1e-9) * GRID


def snap_dn(mm: float) -> float:
    """Round down to the 20mm bench grid."""
    return int(mm / GRID + 1e-9) * GRID


# ---------------------------------------------------------------- datums


@dataclass(frozen=True)
class Datums:
    """Every shared boundary in the station, derived from one Station.

    Parts read from here. Parts never recompute a boundary, and never read a
    bay width straight out of params, because params carries the brief's
    estimates and this carries what the panels actually leave.
    """

    s: Station
    t: float = T

    # -- X: the four vertical panels and the three bays between them --------

    @property
    def x_left(self) -> float:
        return 0.0

    @property
    def x_right(self) -> float:
        return self.s.leg_x_inner

    @property
    def wall_x(self) -> tuple[float, float, float, float]:
        """Left edge of each of the four vertical panels, left to right.

        Panel i occupies x in [wall_x[i], wall_x[i] + t].
        Lungs is pinned to the left, hands to the right, stock takes the rest.
        """
        x0 = self.x_left
        x1 = x0 + self.t + self.s.bay_lungs_w
        x3 = self.x_right - self.t
        x2 = x3 - self.s.bay_hands_w - self.t
        return (x0, x1, x2, x3)

    @property
    def lungs_x(self) -> tuple[float, float]:
        return (self.wall_x[0] + self.t, self.wall_x[1])

    @property
    def stock_x(self) -> tuple[float, float]:
        return (self.wall_x[1] + self.t, self.wall_x[2])

    @property
    def hands_x(self) -> tuple[float, float]:
        return (self.wall_x[2] + self.t, self.wall_x[3])

    @property
    def stock_clear_w(self) -> float:
        """What the stock bay actually gets once four panels are subtracted.

        THIS, not params.bay_stock_w, is the number the stock rack is cut to.
        params carries the brief's 220mm estimate, which was taken before the
        panels had thickness.
        """
        a, b = self.stock_x
        return b - a

    @property
    def stock_capacity(self) -> int:
        """HALF blanks on edge at the rack pitch."""
        return int(self.stock_clear_w // self.s.sheet_pitch)

    # -- Y: front band, spine, brain band -----------------------------------

    @property
    def y_front(self) -> float:
        return 0.0

    @property
    def y_rear(self) -> float:
        return self.s.leg_y_inner

    @property
    def y_spine(self) -> float:
        """Front face of the spine panel. It occupies [y_spine, y_spine + t]."""
        return self.y_rear - self.s.bay_brain_d - self.t

    @property
    def front_bay_d(self) -> float:
        """Clear depth of any front bay. Matches Station.front_bay_d()."""
        return self.y_spine - self.y_front

    @property
    def brain_d(self) -> float:
        """Clear depth of the brain band, spine to the rear-panel plane."""
        return self.y_rear - (self.y_spine + self.t)

    # -- Z: the stack-up ----------------------------------------------------

    @property
    def plinth_z(self) -> tuple[float, float]:
        return (0.0, PLINTH_H)

    @property
    def deck_z(self) -> tuple[float, float]:
        """The deck panel. Its top face is the datum every bay stands on."""
        return (PLINTH_H, PLINTH_H + self.t)

    @property
    def deck_top(self) -> float:
        return self.deck_z[1]

    @property
    def lungs_stack_h(self) -> float:
        """Everything under the extractor's lid, measured up from deck_top."""
        return (
            self.t                  # pull-out platform
            + ISOLATOR_H            # rubber isolators
            + self.s.extractor_env[2]
            + SERVICE_GAP
        )

    @property
    def bay_h(self) -> float:
        """Clear height of every bay. Set by the tallest content, which is the
        extractor on its carriage."""
        return self.lungs_stack_h

    @property
    def top_z(self) -> tuple[float, float]:
        z0 = self.deck_top + self.bay_h
        return (z0, z0 + self.t)

    @property
    def carcass_h(self) -> float:
        return self.top_z[1]

    @property
    def top_gap(self) -> float:
        """Reveal between the carcass top and the underside of the machine
        frame. The carcass is built from the floor up and this is the leftover,
        which is why the 52mm levelling-feet question cannot break it."""
        return self.s.clear_h - self.carcass_h

    # -- brain band: the ventilation corridor -------------------------------

    @property
    def vent_corridor_x(self) -> tuple[float, float]:
        """X span of the brain band reserved for the VFD and its air.

        The VFD is turned 90 degrees about Z from the brief's arrangement so its
        vented face looks ALONG the brain band, into open span, instead of at a
        panel 130mm away. Carbide asks for 300mm off that face; the band is
        1064mm long and can give it. The band is a chimney, not a sealed box:
        intake through the plinth, exhaust through the top cap.
        """
        x0 = self.wall_x[0] + self.t
        return (x0, x0 + self.s.vfd_box[1] + self.s.vfd_vent_clear)

    @property
    def vfd_footprint(self) -> tuple[float, float]:
        """(X, Y) the VFD body occupies, turned. Its 200mm width goes into the
        band's depth, its 130mm depth across the band's length."""
        return (self.s.vfd_box[1], self.s.vfd_box[0])

    @property
    def brain_intake_y(self) -> tuple[float, float]:
        """Y span of the low air intake through the deck, under the VFD."""
        return (self.y_spine + self.t, self.y_rear)

    @property
    def hose_port(self) -> tuple[float, float, float]:
        """Centre of the extraction port through the LEFT end wall, in station
        coordinates.

        The hose leaves sideways and turns in free air outside the machine
        footprint. It has to: hose_bend_r() is 144mm and there is nowhere inside
        the carcass, or in top_gap, with 144mm to give. High and rear, clear of
        the leg gusset.
        """
        return (
            self.wall_x[0] + self.t / 2,
            self.y_spine - self.s.hose_id * 1.5,
            self.top_z[0] - self.s.hose_id * 1.5,
        )

    # -- placement planes ---------------------------------------------------
    # A part is drawn flat per the panel convention, then placed with one of
    # these: ``plane * flat_part`` or ``flat_part.moved(Location(plane))``.

    @property
    def deck_plane(self) -> Plane:
        """Deck: local +X to station +X, local +Y to station +Y, flat."""
        return Plane(origin=(0, 0, self.deck_z[0]), x_dir=(1, 0, 0), z_dir=(0, 0, 1))

    @property
    def top_plane(self) -> Plane:
        """Top cap: same orientation as the deck, at top_z."""
        return Plane(origin=(0, 0, self.top_z[0]), x_dir=(1, 0, 0), z_dir=(0, 0, 1))

    @property
    def spine_plane(self) -> Plane:
        """Spine: local +X to station +X, local +Y up, thickness into -Y so the
        panel lands in [y_spine, y_spine + t]. Local origin at the panel's
        lower-left as seen from the FRONT of the station."""
        return Plane(
            origin=(self.t, self.y_spine + self.t, self.deck_top),
            x_dir=(1, 0, 0),
            z_dir=(0, -1, 0),
        )

    def wall_plane(self, i: int) -> Plane:
        """Vertical panel i (0..3): local +X to station +Y, local +Y up,
        thickness into +X. Local origin at the panel's lower-FRONT corner, so
        local X = 0 is the open front of the bay."""
        return Plane(
            origin=(self.wall_x[i], 0, self.deck_top),
            x_dir=(0, 1, 0),
            z_dir=(1, 0, 0),
        )

    # -- blank sizes, so parts do not re-derive them -------------------------

    @property
    def deck_size(self) -> tuple[float, float]:
        return (self.x_right - self.x_left, self.y_rear - self.y_front)

    @property
    def top_size(self) -> tuple[float, float]:
        return self.deck_size

    @property
    def spine_size(self) -> tuple[float, float]:
        return (self.x_right - 2 * self.t, self.bay_h)

    @property
    def wall_size(self) -> tuple[float, float]:
        return (self.front_bay_d, self.bay_h)


DATUMS = Datums(STATION)


# ---------------------------------------------------------------- blanks


def panel(w: float, h: float, t: float = T) -> Part:
    """A flat blank in panel-local coordinates: corner at the origin, extending
    into +X, +Y, +Z. Every sheet part starts here."""
    return Box(w, h, t, align=(Align.MIN, Align.MIN, Align.MIN))


# ---------------------------------------------------------------- joinery
# Cutters. Each returns a solid to SUBTRACT from a flat panel. Every default
# derives from T.


def _segment(start: tuple[float, float], end: tuple[float, float]):
    dx, dy = end[0] - start[0], end[1] - start[1]
    return hypot(dx, dy), degrees(atan2(dy, dx))


def groove(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    width: float = DADO_W,
    depth: float = DADO_D,
    thickness: float = T,
    side: str = "back",
    justify: str = "center",
) -> Part:
    """Cutter for a dado or housing running from ``start`` to ``end`` in
    panel-local XY.

    width      defaults to DADO_W = T + fit, the mating panel's thickness
    depth      defaults to DADO_D = T/3
    side       "back" cuts in from the Z=0 face, "front" from Z=thickness
    justify    "center" puts the groove on the line; "left"/"right" hangs it to
               one side of the line, which is what a rabbet at an edge wants
    """
    length, angle = _segment(start, end)
    if length <= 0:
        raise ValueError("groove needs a non-zero length")

    if justify == "center":
        off = 0.0
    elif justify == "left":
        off = width / 2
    elif justify == "right":
        off = -width / 2
    else:
        raise ValueError(f"justify must be center|left|right, got {justify!r}")

    z0 = 0.0 if side == "back" else thickness - depth
    if side not in ("back", "front"):
        raise ValueError(f"side must be back|front, got {side!r}")

    cutter = Box(length, width, depth, align=(Align.MIN, Align.CENTER, Align.MIN))
    cutter = cutter.moved(Location((0, off, 0)))
    return cutter.moved(Location((start[0], start[1], z0), (0, 0, angle)))


def rabbet(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    width: float = RABBET_W,
    depth: float = RABBET_D,
    thickness: float = T,
    side: str = "back",
    toward: str = "left",
) -> Part:
    """Cutter for an edge rabbet. Run start->end along the edge; ``toward``
    names which side of that line the material comes off."""
    return groove(
        start,
        end,
        width=width,
        depth=depth,
        thickness=thickness,
        side=side,
        justify=toward,
    )


def through_slot(
    center: tuple[float, float],
    length: float,
    width: float,
    *,
    thickness: float = T,
    angle: float = 0.0,
) -> Part:
    """Cutter for a through slot centred at ``center``, ``length`` along the
    slot axis (rotated ``angle`` degrees from +X)."""
    over = thickness  # overshoot both faces so the boolean is clean
    cutter = Box(length, width, thickness + 2 * over, align=(Align.CENTER,) * 3)
    return cutter.moved(Location((center[0], center[1], thickness / 2), (0, 0, angle)))


def finger_layout(
    length: float,
    *,
    tab: float = TAB_W,
    phase: int = 0,
) -> list[tuple[float, float]]:
    """Split an edge of ``length`` into an odd number of fingers and return the
    spans belonging to one side of the joint, as (start, end) offsets from the
    start of the edge.

    Both panels in the joint call this with the same ``length`` and ``tab`` and
    opposite ``phase``, so the two sets interlock by construction and neither
    part owns the layout.

    An odd count means the joint starts and ends with material on phase 0, which
    is what you want at a corner.
    """
    if length <= 0:
        raise ValueError("finger_layout needs a positive length")
    n = max(3, int(round(length / tab)))
    if n % 2 == 0:
        n += 1
    step = length / n
    return [(i * step, (i + 1) * step) for i in range(n) if i % 2 == phase % 2]


def finger_slots(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    mating_t: float = T,
    thickness: float = T,
    tab: float = TAB_W,
    phase: int = 0,
    fit: float = TAB_FIT,
) -> Part:
    """Through slots in the RECEIVING panel, centred on the joint line from
    ``start`` to ``end``. The mating panel's tabs come from ``finger_layout``
    with the same phase."""
    length, angle = _segment(start, end)
    spans = finger_layout(length, tab=tab, phase=phase)
    cutters = []
    ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
    for a, b in spans:
        mid = (a + b) / 2
        cutters.append(
            through_slot(
                (start[0] + mid * ux, start[1] + mid * uy),
                (b - a) + 2 * fit,
                mating_t + 2 * fit,
                thickness=thickness,
                angle=angle,
            )
        )
    out = cutters[0]
    for c in cutters[1:]:
        out += c
    return out


def finger_notches(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    depth: float = T,
    thickness: float = T,
    tab: float = TAB_W,
    phase: int = 0,
    fit: float = TAB_FIT,
) -> Part:
    """The complement, for the TABBED panel: cutters that remove the spans of
    its edge which are NOT tabs, to ``depth`` (the receiving panel's thickness).

    Call with the phase OPPOSITE to the one you passed ``finger_slots``. Run
    ``start`` to ``end`` along the tabbed edge; material comes off the side the
    edge faces, which is handled by the caller placing the edge correctly.
    """
    length, angle = _segment(start, end)
    spans = finger_layout(length, tab=tab, phase=phase)
    ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
    nx, ny = -uy, ux  # left normal
    cutters = []
    for a, b in spans:
        mid = (a + b) / 2
        cx = start[0] + mid * ux + nx * depth / 2
        cy = start[1] + mid * uy + ny * depth / 2
        cutters.append(
            through_slot(
                (cx, cy),
                (b - a) - 2 * fit,
                depth,
                thickness=thickness,
                angle=angle,
            )
        )
    out = cutters[0]
    for c in cutters[1:]:
        out += c
    return out


def screw_positions(
    length: float,
    *,
    pitch: float = SCREW_PITCH,
    inset: float = SCREW_END_INSET,
) -> list[float]:
    """Fastener offsets along an edge of ``length``, evenly spaced at no more
    than ``pitch``, with the first and last ``inset`` from the ends.

    Derived from T, so a 15mm carcass gets a tighter pattern without anyone
    editing a part.
    """
    span = length - 2 * inset
    if span <= 0:
        return [length / 2]
    n = max(2, ceil(span / pitch) + 1)
    step = span / (n - 1)
    return [inset + i * step for i in range(n)]


def screw_line(
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    thickness: float = T,
    d: float = SCREW_CLEAR_D,
    cbore_d: float | None = None,
    cbore_depth: float | None = None,
    pitch: float = SCREW_PITCH,
    inset: float = SCREW_END_INSET,
) -> Part:
    """Cutter for a row of through-fasteners along a line in panel-local XY.

    ``d`` is the clearance hole in the panel being screwed THROUGH. Pass
    ``cbore_d`` to counterbore from the Z=thickness face.
    """
    length, _ = _segment(start, end)
    ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
    over = thickness
    out = None
    for p in screw_positions(length, pitch=pitch, inset=inset):
        cx, cy = start[0] + p * ux, start[1] + p * uy
        hole = Cylinder(
            d / 2, thickness + 2 * over, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ).moved(Location((cx, cy, -over)))
        out = hole if out is None else out + hole
        if cbore_d:
            cd = cbore_depth if cbore_depth is not None else thickness / 2
            cb = Cylinder(
                cbore_d / 2, cd + over, align=(Align.CENTER, Align.CENTER, Align.MIN)
            ).moved(Location((cx, cy, thickness - cd)))
            out = out + cb
    return out


def bore(
    x: float,
    y: float,
    d: float,
    *,
    thickness: float = T,
    depth: float | None = None,
    side: str = "back",
) -> Part:
    """Cutter for one round hole at ``x, y`` in panel-local XY.

    ``screw_line`` covers a row of fasteners on an edge. This is the single hole
    that is not part of a row: a bolt through a mounting pad, a bulkhead cutout,
    a cable gland or grommet, a blind flat-bottomed counterbore. ``relief`` is
    the same shape sized to the cutter and doing a different job.

    depth   ``None`` (the default) cuts through. A number cuts that deep only.
    side    which face a blind bore is cut from, matching ``groove``.
    """
    over = thickness
    if depth is None:
        return Cylinder(
            d / 2, thickness + 2 * over, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ).moved(Location((x, y, -over)))

    if side == "back":
        z0 = -over
    elif side == "front":
        z0 = thickness - depth
    else:
        raise ValueError(f"side must be back|front, got {side!r}")

    return Cylinder(
        d / 2, depth + over, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((x, y, z0)))


def relief(
    x: float,
    y: float,
    *,
    r: float = ROUTER_R,
    thickness: float = T,
    depth: float | None = None,
    side: str = "back",
) -> Part:
    """Dogbone corner relief. A round cutter cannot cut an inside corner; drop
    one of these on every inside corner of a routed pocket or slot so the mating
    part seats fully.

    depth   ``None`` (the default) cuts through, which is what a through slot
            wants. Pass a number to cut only that deep, which is what the blind
            end of a housing wants: a through dogbone at the end of a 6mm dado
            is a hole in the panel.
    side    which face a blind relief is cut from, matching ``groove``.
    """
    return bore(x, y, 2 * r, thickness=thickness, depth=depth, side=side)


# ---------------------------------------------------------------- export

EXPORT_DIR = Path(__file__).resolve().parents[2] / "export" / "cnc_shapeoko"


def flat_pattern(part: Shape, *, tol: float = 1e-6) -> dict[str, list[Face]]:
    """Pull the DXF layers out of a flat panel drawn on the panel convention.

    Returns a mapping of layer name to faces, all moved to Z=0:

        CUT                  the outline and every through feature, seen from
                             the +Z (front) face
        BACK                 the Z=0 face, which carries anything cut from
                             underneath
        POCKET_FRONT_<d>     floor of a blind pocket cut <d> deep from the
                             front face
        POCKET_BACK_<d>      floor of a blind pocket cut <d> deep from the back

    Which face a pocket is cut from is read off its floor's outward normal. A
    solid's face normals point out of the solid, so the floor of a back-cut
    groove -- which still has material above it -- points -Z. The layer name
    therefore carries both the setup and the depth, and the shop never has to
    infer a flip from a drawing.
    """
    faces = part.faces().filter_by(Plane.XY)
    if not faces:
        raise ValueError("flat_pattern expects a panel lying flat on Plane.XY")
    zs = sorted({round(f.center().Z, 6) for f in faces})
    z_top, z_bot = zs[-1], zs[0]

    layers: dict[str, list[Face]] = {}
    for f in faces:
        z = round(f.center().Z, 6)
        flat = f.moved(Location((0, 0, -z)))
        if abs(z - z_top) < tol:
            layers.setdefault("CUT", []).append(flat)
        elif abs(z - z_bot) < tol:
            layers.setdefault("BACK", []).append(flat)
        elif f.normal_at().Z < 0:
            # outward normal points down into the void above it: material is
            # still overhead, so this floor was reached from the back face
            layers.setdefault(f"POCKET_BACK_{z - z_bot:g}", []).append(flat)
        else:
            layers.setdefault(f"POCKET_FRONT_{z_top - z:g}", []).append(flat)
    return layers


def export_part(
    part: Shape,
    name: str,
    *,
    step: bool = True,
    dxf: bool = True,
    out_dir: Path | None = None,
    layers: dict[str, list[Face]] | None = None,
) -> list[Path]:
    """Write STEP for Fusion and DXF for the laser, from the same model.

    ``part`` must be the FLAT panel-local solid, not the placed one, so the DXF
    is the blank as it will be cut. Returns the paths written.

    ``layers`` overrides the automatic ``flat_pattern`` read. Pass it for a part
    that is machined rather than cut from sheet: ``flat_pattern`` infers setup
    side and depth from faces parallel to Plane.XY, which is exactly right for a
    panel and wrong for anything with an angled face. Keep the layer vocabulary
    (CUT / BACK / POCKET_<SIDE>_<depth>) so the shop reads one drawing language.
    """
    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    if step:
        p = out_dir / f"{name}.step"
        export_step(part, p, unit=Unit.MM)
        written.append(p)

    if dxf:
        p = out_dir / f"{name}.dxf"
        exporter = ExportDXF(unit=Unit.MM)
        for layer, faces in (layers if layers is not None else flat_pattern(part)).items():
            exporter.add_layer(layer)
            for f in faces:
                exporter.add_shape(f.wires(), layer=layer)
        exporter.write(p)
        written.append(p)

    return written


# ---------------------------------------------------------------- checks


def check_carcass(d: Datums = DATUMS) -> list[str]:
    """Constraints the carcass owns, as opposed to the ones params owns.

    params.check() answers "do the numbers agree with the machine". This answers
    "does a carcass made of 18mm panels fit inside those numbers".
    """
    s = d.s
    notes: list[str] = []

    if d.top_gap < TOP_GAP_MIN:
        notes.append(
            f"carcass is {d.carcass_h:.0f}mm tall into {s.clear_h:.0f}mm of "
            f"clearance, leaving {d.top_gap:.0f}mm. Below the {TOP_GAP_MIN:.0f}mm "
            "reveal the carcass starts touching the machine frame, which is the "
            "one thing it must not do."
        )

    if abs(d.stock_clear_w - s.bay_stock_w) > 1e-6:
        notes.append(
            f"stock bay is {d.stock_clear_w:.0f}mm clear, not the "
            f"{s.bay_stock_w:.0f}mm params estimates: four {d.t:.0f}mm panels "
            f"eat {4 * d.t:.0f}mm the brief's arithmetic did not carry. "
            f"Rack holds {d.stock_capacity} HALF blanks at "
            f"{s.sheet_pitch:.0f}mm pitch, not {s.stock_capacity()}."
        )

    if d.stock_clear_w < s.sheet_pitch * 4:
        notes.append(
            f"stock bay is down to {d.stock_clear_w:.0f}mm, under four blanks. "
            "At this point the ready-use rack has stopped being worth its width "
            "and the bay should become drawer or open shelf."
        )

    if s.sheet_slot[1] > d.bay_h:
        notes.append(
            f"a HALF blank on edge is {s.sheet_slot[1]:.0f}mm against a "
            f"{d.bay_h:.0f}mm bay. It will not stand in the rack."
        )

    corridor = d.vent_corridor_x
    if corridor[1] > d.wall_x[3]:
        notes.append(
            f"the VFD ventilation corridor runs to x={corridor[1]:.0f} and the "
            f"brain band ends at x={d.wall_x[3]:.0f}. Turning the drive's vented "
            "face along the band no longer buys the clearance."
        )

    if d.vfd_footprint[1] > d.brain_d:
        notes.append(
            f"turned, the VFD needs {d.vfd_footprint[1]:.0f}mm of the brain "
            f"band's {d.brain_d:.0f}mm depth. It does not fit sideways either."
        )

    if s.vfd_box[2] + SERVICE_GAP > d.bay_h:
        notes.append(
            f"VFD is {s.vfd_box[2]:.0f}mm tall into a {d.bay_h:.0f}mm bay with "
            f"{SERVICE_GAP:.0f}mm of service gap"
        )

    travel = min(s.travel_x, s.travel_y)
    for label, size in (
        ("deck", d.deck_size),
        ("top cap", d.top_size),
        ("spine", d.spine_size),
        ("bay wall", d.wall_size),
    ):
        if max(size) > travel:
            notes.append(
                f"{label} blank {size[0]:.0f} x {size[1]:.0f} exceeds the "
                f"machine's own {travel:.0f}mm travel. The station cannot cut "
                "its own part."
            )
        if not fits(size, SHEET_5X5_BALTIC):
            notes.append(
                f"{label} blank {size[0]:.0f} x {size[1]:.0f} does not come out "
                "of a 5x5 Baltic sheet"
            )

    if not fits(d.deck_size, (600.0, 1200.0)):
        notes.append(
            f"deck {d.deck_size[0]:.0f} x {d.deck_size[1]:.0f} is bigger than a "
            "FULL blank, so the carcass's own biggest panels come off the 5x5 "
            "sheet directly and never touch the 600 stock module. Expected, and "
            "worth knowing before ordering."
        )

    if LEG_SLOT_V <= s.table_h_with_feet - s.table_h_no_feet:
        notes.append(
            f"leg-tie slot travel {LEG_SLOT_V:.0f}mm does not cover the "
            f"{s.table_h_with_feet - s.table_h_no_feet:.0f}mm levelling-feet swing"
        )

    return notes


if __name__ == "__main__":
    d = DATUMS
    print("DATUM: origin at the floor, left-front inside corner of the leg frame")
    print(f"  X  0 .. {d.x_right:.0f}   walls at {[f'{x:.0f}' for x in d.wall_x]}")
    print(
        f"     lungs {d.lungs_x[0]:.0f}..{d.lungs_x[1]:.0f}   "
        f"stock {d.stock_x[0]:.0f}..{d.stock_x[1]:.0f}   "
        f"hands {d.hands_x[0]:.0f}..{d.hands_x[1]:.0f}"
    )
    print(
        f"  Y  0 .. {d.y_rear:.0f}   spine at {d.y_spine:.0f}   "
        f"front bay depth {d.front_bay_d:.0f}   brain depth {d.brain_d:.0f}"
    )
    print(
        f"  Z  plinth {d.plinth_z[1]:.0f}   deck top {d.deck_top:.0f}   "
        f"bay {d.bay_h:.0f}   top {d.top_z[0]:.0f}..{d.top_z[1]:.0f}   "
        f"reveal {d.top_gap:.0f}"
    )
    print(
        f"  stock rack {d.stock_clear_w:.0f}mm clear, "
        f"{d.stock_capacity} HALF blanks on edge"
    )
    print(
        f"  vent corridor x {d.vent_corridor_x[0]:.0f}..{d.vent_corridor_x[1]:.0f} "
        f"in a {d.wall_x[3] - d.t:.0f}mm band"
    )
    print(
        f"  blanks: deck {d.deck_size[0]:.0f}x{d.deck_size[1]:.0f}  "
        f"spine {d.spine_size[0]:.0f}x{d.spine_size[1]:.0f}  "
        f"wall {d.wall_size[0]:.0f}x{d.wall_size[1]:.0f}"
    )
    print(
        f"  joinery from T={T:.0f}: dado {DADO_W:.1f}w x {DADO_D:.1f}d, "
        f"rabbet {RABBET_D:.1f}d, tab {TAB_W:.0f}, screws every {SCREW_PITCH:.0f}"
    )

    found = check_carcass(d)
    if found:
        print(f"\n{len(found)} carcass note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno carcass constraint violations")
