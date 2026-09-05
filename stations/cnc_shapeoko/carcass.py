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
    +Z      UP from the floor.  Z runs 0 .. z_beam (underside of the machine's
            frame beam).  The ceiling on the way up is not one number: four
            gussets hang off the beam and eat into both X and Y, so what the
            carcass may reach at any point is ``Station.clear_z(x, y)`` and
            ``clear_h_min`` is only that surface's lowest value.

The leg opening was measured on 2026-09-02 and the model moved with it: X gained
154mm, Y lost 61.  Nothing in this module hardcodes around either, which is why
that was two lines in ``params.py`` and no geometry.


THE BANDS
=========

Y splits into two bands at the spine panel:

    front band   Y 0 .. y_spine     three bays, all opening to the FRONT
    spine        Y y_spine .. +T    the full-width structural divider
    brain band   Y y_spine+T .. y_rear    VFD, motion controller, mini PC,
                                          distribution.  Rear-panel access.

X splits the front band into three bays between four vertical panels:

    wall 0   left end wall           x 0 .. T
    LUNGS    CT 15 HEPA on slides    clear width bay_lungs_w
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
    Polygon,
    Shape,
    Unit,
    export_step,
    extrude,
)

from lib.house import CARCASS_T, GRID, PANEL_T, SHEET_5X5_BALTIC, fits, on_grid
from stations.cnc_shapeoko.params import STATION, Gusset, Station

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
    "SERVICE_GAP",
    "TOP_GAP_MIN",
    "STOCK_HEADROOM",
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
    "edge_chamfer",
    "stile_notch",
    "gusset_prism",
    "to_local",
    "gusset_domain",
    "gussets_over",
    "clear_over_relieved",
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
# The vertical budget. The ceiling is a surface rather than a number, so the
# carcass is built bottom-up from its contents and the leftover becomes a
# reveal against whatever the envelope puts overhead. See Datums.top_gap.

PLINTH_H = GRID * 3     # 60mm toe kick. Levellers and the low air intake.
SERVICE_GAP = GRID      # clearance above the tallest thing in any bay
TOP_GAP_MIN = GRID      # the carcass never touches the machine frame

STOCK_HEADROOM = GRID   # lift a HALF blank clear of its slot to get it out


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

        The stock bay is the remainder: lungs is pinned to the left end and
        hands to the right, so this is what is left between the dividers, and
        it is the number the stock rack is cut to.
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

    @property
    def end_wall_y(self) -> tuple[float, float]:
        """Station Y span of the two END walls, which is not the same as a bay.

        The dividers stop at the spine. The end walls run the FULL depth, because
        the spine's end faces land on them, the brain band has to have two side
        walls, and the rear door has to land on something. That makes this span
        the birch the carcass presents on its outer faces, which is what the leg
        bolts drive their inserts into and what the brain-band louvre is cut out
        of.

        Here rather than in a part because more than one part reads it and two of
        them once disagreed: ``bay_walls`` cut the end walls to this while the
        old leg-tie module assumed they stopped at ``front_bay_d``, and invented
        a missing part out of the difference. ``leg_joint`` reads this property.
        """
        return (self.y_front, self.y_rear)

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
            + self.s.extractor_env[2]
            + SERVICE_GAP
        )

    @property
    def bay_h(self) -> float:
        """Clear height of every bay.

        NOT set by the fitted extractor alone, which is the trap this property
        exists to avoid. A CT 15 on its carriage is 488mm and sizing the bay off
        it would leave a 600mm HALF blank unable to stand on edge in the stock
        rack, which is the whole point of the stock bay.

        Bay height is therefore the tallest of what the rack needs and what the
        lungs stack needs, and today the rack wins. (Until 2026-09-03 the second
        term was the withdrawn CT 36 EI's stack; the fitted stack is shorter, so
        the number did not move.)
        """
        return snap_up(
            max(
                self.s.sheet_slot[1] + STOCK_HEADROOM,
                self.lungs_stack_h,
            )
        )

    @property
    def top_z(self) -> tuple[float, float]:
        z0 = self.deck_top + self.bay_h
        return (z0, z0 + self.t)

    @property
    def carcass_h(self) -> float:
        return self.top_z[1]

    @property
    def clear_over_carcass(self) -> float:
        """Lowest ceiling the machine imposes anywhere over the carcass.

        The carcass footprint IS the leg opening -- the 2026-09-02 ruling puts
        it flush to the leg inner faces -- so this asks the clearance envelope
        for its worst corner, which is where a gusset comes down to meet a leg.
        A part with a smaller footprint gets a higher ceiling, and asks
        ``Station.clear_z`` for its own.
        """
        return self.s.clear_z_over(
            (self.x_left, self.x_right), (self.y_front, self.y_rear)
        )

    @property
    def top_gap(self) -> float:
        """Reveal between the carcass top and the lowest thing above it. The
        carcass is built from the floor up and this is the leftover, which is
        why the 52mm levelling-feet question cannot break it."""
        return self.clear_over_carcass - self.carcass_h

    # -- brain band: the ventilation corridor -------------------------------

    @property
    def vfd_x(self) -> tuple[float, float]:
        """X span the VFD body occupies in the brain band.

        Ruling 2026-09-02: the drive vents THROUGH THE PANEL. It keeps Carbide's
        stock vertical orientation and stands at the LEFT end of the brain band
        with its vented left face looking at the left brain-band cheek, which
        carries the louvre. Carbide's 300mm is satisfied by the room on the far
        side of that louvre.

        This replaces the turned-drive arrangement, which met the 300mm inside
        the box by spending 430mm of the band as an empty corridor. The band is
        where the electrical wants room to be laid out legibly and that was the
        wrong thing to spend it on.
        """
        x0 = self.wall_x[0] + self.t + self.s.vfd_panel_standoff
        return (x0, x0 + self.s.vfd_box[0])

    @property
    def vfd_footprint(self) -> tuple[float, float]:
        """(X, Y) the VFD body occupies, in Carbide's stock orientation: its
        200mm width across the band, its 130mm depth into the band."""
        return (self.s.vfd_box[0], self.s.vfd_box[1])

    @property
    def vfd_keepout_x(self) -> tuple[float, float]:
        """X span of the brain band that belongs to the drive and its air.

        Nothing may sit in it: no pass-through, no bore, no shelf. It runs from
        the inner face of the louvred cheek to the far side of the drive, so it
        covers the standoff the vented face breathes through as well as the body.

        This replaces vent_corridor_x, and it is the whole material gain from
        the 2026-09-02 ruling. The corridor reserved the drive's depth plus
        Carbide's 300mm, roughly 430mm of the band. This reserves the standoff
        plus the drive's width, and hands the difference back to the electrical.
        """
        return (self.wall_x[0] + self.t, self.vfd_x[1])

    @property
    def brain_split_x(self) -> float:
        """Left face of the brain-band partition dividing sealed power from
        exposed signal. It sits on the right face of the stock/hands divider so
        one plane runs unbroken from the open front to the rear panel.

        Lives here rather than in spine_panel because the top cap needs it too:
        the exhaust field stops at this plane.
        """
        return self.wall_x[2] + self.t

    @property
    def brain_exhaust_x(self) -> tuple[float, float]:
        """X span of the top cap's exhaust louvre field.

        The chimney has to let the air that rises off the drive leave, and that
        plume spreads as it climbs, so the field is wider than vfd_keepout_x.
        It stops at the sealed/exposed split for two reasons: the heat is all on
        the sealed side, and slots over the signal side would be a route for a
        dropped object into a band carrying mains.

        Anchoring the field here rather than to the keep-out is what keeps the
        2026-09-02 trade paid for. The keep-out shrank from 430mm to 240mm when
        the drive stopped needing an internal corridor, and an exhaust tied to
        it would have shrunk with it, which is the opposite of what venting
        through a panel asks for.
        """
        return (self.vfd_keepout_x[0], self.brain_split_x)

    @property
    def louvre_x(self) -> tuple[float, float]:
        """X span of the louvre field in the left brain-band cheek. The cheek is
        a Y-Z panel, so the louvre's own extent is in Y and Z; this is the wall
        it lives in, kept here so parts do not rediscover which panel it is."""
        return (self.wall_x[0], self.wall_x[0] + self.t)

    @property
    def louvre_area_avail(self) -> float:
        """Gross area the left cheek can give the louvre over the brain band.

        The free area is a fraction of this once the grille is drawn, which is
        why the check compares the requirement against the gross with margin
        rather than pretending the panel is an open hole."""
        return self.brain_d * self.bay_h

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

    @property
    def mast_base(self) -> tuple[float, float, float]:
        """Centre of the mast base pad, in station coordinates: the middle of
        the 40x40 M8 bolt square on the top cap's TOP face, on the side
        ``parts.top_cap.MAST_SIDE`` names. RULED 2026-09-03: left rear.

        This is the datum the mast is authored against in Fusion (J06). The
        pad itself is the top cap's to place, so this reads it back from
        there rather than repeating the arithmetic; the import is deferred
        because top_cap imports this module.
        """
        from stations.cnc_shapeoko.parts.top_cap import MAST_SIDE, mast_pad

        pad = mast_pad(MAST_SIDE, self)
        return (
            (pad.xs[0] + pad.xs[1]) / 2,
            (pad.ys[0] + pad.ys[1]) / 2,
            self.carcass_h,
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

    # -- the stiles: the flange band is a fixed birch stile (2026-09-04) -----
    # RULED by Jared: "absolutely no overlays. reconfigure depth to ensure
    # everything is a la kerf design cabinets." At each of the four corners
    # the leg's Y flange stands across the carcass plane, ``flange_reach``
    # past the end wall's outer face. Behind that band, inside the opening,
    # stands one fixed birch stile, ``t`` deep (y 0..t at the front, y_rear-t..
    # y_rear at the rear), from the end wall's inner face to ``stile_toe_land``
    # past the flange's toe, full opening height, tongued THROUGH the deck
    # and the cap. Every door and drawer front is inset between a stile and
    # a divider, flush in the carcass plane. ``parts/stiles.py`` builds them;
    # everything else reads the spans from here.

    @property
    def stile_w(self) -> float:
        """Width of a stile in X: from the end wall's inner face to the leg
        flange's toe plus the land past it. 64.48 at the measured leg."""
        reach = self.s.leg_holes.flange_reach
        if reach is None:
            reach = self.s.leg_holes.span_h + self.s.leg_holes.hole_d / 2
        return reach - self.t + self.s.stile_toe_land

    @property
    def stiles(self) -> tuple[tuple[str, tuple[float, float], tuple[float, float]], ...]:
        """(label, x span, y span) of the four stiles, station coordinates:
        front-left, front-right, rear-left, rear-right."""
        w = self.stile_w
        xl = (self.x_left + self.t, self.x_left + self.t + w)
        xr = (self.x_right - self.t - w, self.x_right - self.t)
        yf = (self.y_front, self.y_front + self.t)
        yr = (self.y_rear - self.t, self.y_rear)
        return (
            ("stile_front_left", xl, yf),
            ("stile_front_right", xr, yf),
            ("stile_rear_left", xl, yr),
            ("stile_rear_right", xr, yr),
        )

    @property
    def lungs_opening_x(self) -> tuple[float, float]:
        """Clear X of the lungs bay's front opening: the front-left stile's
        inner edge to the lungs/stock divider's face. What the lungs door
        fills and the tray passes through."""
        return (self.lungs_x[0] + self.stile_w, self.lungs_x[1])

    @property
    def hands_opening_x(self) -> tuple[float, float]:
        """Clear X of the hands bay's front opening between the stock/hands
        divider and the front-right stile. The console cheek stands inside
        it; ``console_plate`` and ``drawers`` split it."""
        return (self.hands_x[0], self.hands_x[1] - self.stile_w)

    @property
    def rear_opening_x(self) -> tuple[float, float]:
        """Clear X of the brain band's rear opening, stile to stile: what the
        rear door fills."""
        return (self.x_left + self.t + self.stile_w, self.x_right - self.t - self.stile_w)

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
    corner_r: float | None = None,
) -> Part:
    """Cutter for a through slot centred at ``center``, ``length`` along the
    slot axis (rotated ``angle`` degrees from +X).

    A ROUND CUTTER CANNOT LEAVE A SQUARE INSIDE CORNER, and this slot has two
    different right answers depending on what the slot is for. Getting them the
    wrong way round is how a joint ends up 3mm tight on every corner.

    APERTURE (a vent, a hose port, a hand hole). Nothing seats in it, so the
    corner may simply be round. Pass ``corner_r=width / 2`` for a full capsule,
    which is the roundest a slot of that width can be and reads as intended.

    JOINERY (a tongue housing). A square member has to seat, so the corner must
    be relieved OUTWARD with a dogbone, never rounded inward. Leave
    ``corner_r`` alone and drop a ``relief()`` on each inside corner, which is
    what the blind housings in this file already do.

    The default is therefore 0.0, a square cutter: it changes nothing for the
    joinery callers, and it refuses to guess an aperture's intent on their
    behalf. ``corner_r`` is clamped to half of each side, so a capsule is the
    roundest available result and no argument turns the cutter inside out.
    """
    r = 0.0 if corner_r is None else corner_r
    r = max(0.0, min(r, width / 2, length / 2))

    over = thickness  # overshoot both faces so the boolean is clean
    h = thickness + 2 * over

    if r <= 0.0:
        cutter = Box(length, width, h, align=(Align.CENTER,) * 3)
    else:
        # Rounded rectangle as a union: a cross of two boxes plus a cylinder on
        # each corner. Built from Box and Cylinder rather than a rounded sketch
        # so the slot stays one primitive family with the rest of this file.
        # Either cross-arm degenerates when the radius reaches half that side:
        # at r == width/2 the slot is a capsule, and at both it is a plain
        # circle. Build only the arms that still have material in them, because
        # a zero-thickness Box is not an empty solid, it is an OCP failure.
        cutter = None
        if length - 2 * r > 0:
            cutter = Box(length - 2 * r, width, h, align=(Align.CENTER,) * 3)
        if width - 2 * r > 0:
            arm = Box(length, width - 2 * r, h, align=(Align.CENTER,) * 3)
            cutter = arm if cutter is None else cutter + arm
        for sx in (-1, 1):
            for sy in (-1, 1):
                cyl = Cylinder(r, h, align=(Align.CENTER,) * 3).moved(
                    Location((sx * (length / 2 - r), sy * (width / 2 - r), 0))
                )
                cutter = cyl if cutter is None else cutter + cyl

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


def edge_chamfer(
    axis: str,
    at: tuple[float, float],
    size: float,
    span: tuple[float, float],
    into: tuple[float, float] = (1.0, 1.0),
) -> Part:
    """Cutter for a 45-degree chamfer on one straight edge of a flat panel,
    panel-local. Subtract it.

    ``axis`` is the edge's direction, ``"y"`` (a vertical edge of a standing
    panel drawn flat, at local (x, z) = ``at``) or ``"z"`` (a corner of a
    lying panel, at local (x, y) = ``at``). ``span`` is the edge's run along
    that axis and ``into`` the signs of the two cross axes on which the
    material lies, so the same call chamfers any of a panel's four corners.

    RULED 2026-09-04: the leg's inside corner is a fillet, and the carcass's
    outer corners stand in it unless chamfered ``Station.corner_chamfer``.
    The triangle is overshot by ``size`` on its two legs so the boolean is
    clean; its hypotenuse is exactly the line a + b = size.
    """
    over = size
    sa, sb = into
    pts = [
        (-sa * over, -sb * over),
        (sa * (size + over), -sb * over),
        (-sa * over, sb * (size + over)),
    ]
    if sa * sb < 0:
        # a mirrored triangle winds the other way, which flips the face's
        # normal and sends the extrusion out of the panel instead of along it
        pts.reverse()
    lo, hi = span
    length = (hi - lo) + 2 * over
    if axis == "y":
        # triangle in the XZ plane, extruded along +Y (Plane.XZ's normal is -Y)
        body = extrude(Plane.XZ * Polygon(*pts), -length)
        return body.moved(Location((at[0], lo - over, at[1])))
    if axis == "z":
        body = extrude(Plane.XY * Polygon(*pts), length)
        return body.moved(Location((at[0], at[1], lo - over)))
    raise ValueError(f"axis must be y|z, got {axis!r}")


def stile_notch(
    x: tuple[float, float],
    y_edge: float,
    depth: float,
    *,
    open_to: str,
    thickness: float = T,
    fit: float = DADO_FIT,
) -> Part:
    """Cutter for the THROUGH notch a stile's tenon passes in the deck or the
    cap: a rectangle ``x`` wide by ``depth`` deep, open on the blank's front
    (``open_to="front"``, the edge at panel-local ``y_edge`` with material at
    +Y) or rear edge (``"rear"``, material at -Y), ``fit`` oversize, with a
    dogbone at each of its two inside corners. JOINERY: square, relieved
    outward, never rounded in (see ``through_slot``).

    Exposed on purpose (Kerf language, RULED 2026-09-04): the tenon's end
    grain shows flush in the deck's underside and the cap's top face, and
    the notch's mouth shows on the edge.
    """
    x0, x1 = x
    w = (x1 - x0) + fit
    over = thickness
    if open_to == "front":
        y0, y1 = y_edge - over, y_edge + depth + fit / 2
        y_in = y1
    elif open_to == "rear":
        y0, y1 = y_edge - depth - fit / 2, y_edge + over
        y_in = y0
    else:
        raise ValueError(f"open_to must be front|rear, got {open_to!r}")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cut = through_slot((cx, cy), w, y1 - y0, thickness=thickness)
    for xe in (cx - w / 2, cx + w / 2):
        cut += relief(xe, y_in, thickness=thickness)
    return cut


def gusset_prism(g: Gusset) -> Part:
    """One gusset plate, as the trapezoidal prism of steel it is, in STATION
    coordinates.

    The single source of the machine's shape: ``machine.py`` intersects this
    against a placed carcass to find a clash, and a part that needs a relief
    cut subtracts it directly, so the notch and the check that verifies the
    notch are built from the same solid and cannot drift apart.

    The profile is drawn in the plane the gusset constrains: the sketch's
    first coordinate is the axis it eats into, its second is Z, and the
    extrusion runs ``g.plate_t`` along the other axis -- the plate's own
    measured thickness, not the full leg opening. Four points, because the
    shape is four points: it hangs off the beam at full intrusion for its top
    band, then tapers back to the leg's inner face. The extrusion is drawn at
    cross = 0 and then moved out to ``g.cross_lo``, the leg end this plate
    actually sits against.
    """
    profile = [
        (0.0, g.z_bot),
        (g.intrude, g.z_bot + g.taper_h),
        (g.intrude, g.z_beam),
        (0.0, g.z_beam),
    ]
    pts = [(g.coord_at(u), z) for u, z in profile]
    if g.side == "far":
        # coord_at ran the profile backwards along the axis, which reverses the
        # face normal and would extrude the prism out of the opening.
        pts.reverse()

    plane, amount = (Plane.XZ, -g.plate_t) if g.axis == "x" else (Plane.YZ, g.plate_t)
    body = extrude(plane * Polygon(*pts), amount)
    shift = (0.0, g.cross_lo, 0.0) if g.axis == "x" else (g.cross_lo, 0.0, 0.0)
    return body.moved(Location(shift))


def to_local(plane: Plane, shape: Shape) -> Shape:
    """A shape in STATION coordinates, moved into ``plane``'s local frame --
    the inverse of ``plane * shape``.

    THE PANEL CONVENTION above requires every cut to happen flat, before a
    part is stood up, so the DXF flat pattern is the part as drawn rather than
    a projection that has to be trusted. A station-coordinate reference --
    ``gusset_prism``, most often -- has to cross into the panel's own frame to
    be subtracted from it there.
    """
    return shape.moved(plane.location.inverse())


def gusset_domain(g: Gusset) -> tuple[tuple[float, float], tuple[float, float]]:
    """(x range, y range) of one gusset's domain, in station coordinates: the
    footprint where it is capable of pulling the ceiling below ``z_beam``.

    A part with no material anywhere in this rectangle, at any Z, cannot clash
    with ``g`` -- and a part that does have material there is exactly what
    needs relieving, over ``g``'s own ``z_bot``..``z_beam``.
    """
    lo_u, hi_u = g.coord_at(0.0), g.coord_at(g.intrude)
    u_range = (min(lo_u, hi_u), max(lo_u, hi_u))
    cross_range = (g.cross_lo, g.cross_hi)
    return (u_range, cross_range) if g.axis == "x" else (cross_range, u_range)


def _overlaps_1d(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def gussets_over(
    footprint_x: tuple[float, float],
    footprint_y: tuple[float, float],
    gussets: tuple[Gusset, ...],
) -> list[Gusset]:
    """Which of ``gussets`` have a domain overlapping this XY footprint.

    The one place that decides which corners a part needs relieved, so a
    relief list is never typed out by hand and cannot go stale: a part is
    relieved for exactly the gussets whose domain its OWN nominal (unrelieved)
    footprint would otherwise reach into.
    """
    out = []
    for g in gussets:
        gx, gy = gusset_domain(g)
        if _overlaps_1d(footprint_x, gx) and _overlaps_1d(footprint_y, gy):
            out.append(g)
    return out


def clear_over_relieved(
    footprint_x: tuple[float, float],
    footprint_y: tuple[float, float],
    s: Station = STATION,
) -> float:
    """Worst ceiling over a footprint, ASSUMING every gusset whose domain the
    footprint overlaps has actually been cut away there.

    ``gussets_over`` is the exact test ``bay_walls._gusset_relief`` and
    ``top_cap._gusset_relief`` use to decide what to subtract, so calling it
    again here with the same footprint asks for exactly the set of gussets a
    part built from that footprint has already been relieved for -- no
    separate list to keep in sync. A gusset that does NOT overlap the
    footprint is not excused and still pulls the ceiling down at full
    strength; only [machine], with the real solid, verifies the cut was
    actually made. The four corners remain enough to sample: each gusset's
    ceiling is still monotonic in one coordinate and flat in the other, and
    excluding some of them does not change where the worst of the rest sits.
    """
    cleared = {g.label for g in gussets_over(footprint_x, footprint_y, s.gussets)}
    worst = s.z_beam
    for x in footprint_x:
        for y in footprint_y:
            z = s.z_beam
            for g in s.gussets:
                if g.label in cleared:
                    continue
                coord, cross = (x, y) if g.axis == "x" else (y, x)
                if g.applies_at(cross):
                    z = min(z, g.ceiling_at(g.u_at(coord)))
            worst = min(worst, z)
    return worst


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

    ceiling = clear_over_relieved((d.x_left, d.x_right), (d.y_front, d.y_rear), s)
    reveal = ceiling - d.carcass_h
    if reveal < TOP_GAP_MIN:
        notes.append(
            f"carcass is {d.carcass_h:.0f}mm tall into {ceiling:.0f}mm of "
            "clearance over its own (relieved) footprint, leaving "
            f"{reveal:.0f}mm. Below the {TOP_GAP_MIN:.0f}mm reveal the carcass "
            "starts touching the machine frame, which is the one thing it "
            "must not do."
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

    if d.vfd_x[1] > d.wall_x[3]:
        notes.append(
            f"the VFD runs to x={d.vfd_x[1]:.0f} and the brain band ends at "
            f"x={d.wall_x[3]:.0f}. It does not stand at the left end of the band."
        )

    if d.vfd_footprint[1] > d.brain_d:
        notes.append(
            f"the VFD needs {d.vfd_footprint[1]:.0f}mm of the brain band's "
            f"{d.brain_d:.0f}mm depth in Carbide's stock orientation"
        )

    if d.s.vfd_vent_mode == "panel" and d.louvre_area_avail < d.s.louvre_free_area_req:
        notes.append(
            f"the left brain-band cheek is {d.brain_d:.0f} x {d.bay_h:.0f}mm gross "
            f"and the traded clearance wants {d.s.louvre_free_area_req / 100.0:.0f}cm2 "
            "of FREE area out of it. A louvre never gives its gross area, so this "
            "one cannot be paid for out of this panel."
        )

    # The BAY CLEAR WIDTH is what the grid governs, and bay_lungs_w already
    # snaps it up. The divider's absolute x is clear width plus an 18mm end
    # wall and lands off-grid by construction, which is fine: it is a dado in a
    # carcass, not a fence indexed off a bench dog.
    if not on_grid(d.s.bay_lungs_w):
        notes.append(
            f"the lungs bay is {d.s.bay_lungs_w:.1f}mm clear, off the "
            f"{GRID:.0f}mm grid. The rack pitch and the lining lay-up both "
            "assume a bay that divides by the grid."
        )

    if s.vfd_box[2] + SERVICE_GAP > d.bay_h:
        notes.append(
            f"VFD is {s.vfd_box[2]:.0f}mm tall into a {d.bay_h:.0f}mm bay with "
            f"{SERVICE_GAP:.0f}mm of service gap"
        )

    for label, size in (
        ("deck", d.deck_size),
        ("top cap", d.top_size),
        ("spine", d.spine_size),
        ("bay wall", d.wall_size),
    ):
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
        f"  VFD x {d.vfd_x[0]:.0f}..{d.vfd_x[1]:.0f} in a "
        f"{d.wall_x[3] - d.t:.0f}mm band, vented face "
        f"{d.s.vfd_panel_standoff:.0f}mm off the left cheek louvre"
    )
    print(
        f"  bay {d.bay_h:.0f} = max(blank {d.s.sheet_slot[1]:.0f}+"
        f"{STOCK_HEADROOM:.0f}, lungs stack {d.lungs_stack_h:.0f})"
    )
    print(f"  divider station x {d.wall_x[1]:.0f}")
    mx, my, mz = d.mast_base
    print(f"  mast base pad centre ({mx:.1f}, {my:.1f}, {mz:.1f}), 40x40 M8 square")
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
