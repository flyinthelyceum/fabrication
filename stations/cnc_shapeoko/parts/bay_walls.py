"""Bay walls: the four verticals of the Shapeoko station carcass.

One generator, four panels, at ``Datums.wall_x[0..3]``:

    0  left end wall        outboard face left, lungs bay right
    1  lungs/stock divider  lungs left, stock right
    2  stock/hands divider  stock left, hands right
    3  right end wall       hands left, outboard face right

They are one part because they share one joint vocabulary, and because they are
exactly what moves when ``leg_x_inner`` moves. Lungs is pinned to the left end
and hands to the right, so only wall 2 travels: the stock bay narrows and
nothing is redrawn.


WHAT THIS PART OWNS
===================

  * the blank, its tongues into the deck and top-cap housings, and (on the
    dividers) its tongue into the spine's front-face housing
  * the extractor carriage slide mounts, on the two faces of the lungs bay
  * the drawer slide mounts, on the two faces of the hands bay
  * the stock rack rail housings, which set the rack's pitch line
  * the hose port through the left end wall
  * the VFD louvre through the left end wall, over the brain band
  * the clearance holes that fasten the spine's two ends to the end walls
  * the leg-bolt inserts in the two end walls' OUTER faces, which is the joint
    that holds the whole station to the machine. ``leg_joint`` owns where they
    go and what hole they want; this panel is where they land.


TWO PLACES THIS PART DEPARTS FROM ``Datums.wall_size``, ON PURPOSE
=================================================================

``Datums.wall_size`` is (front_bay_d, bay_h) = the CLEAR opening, shoulder to
shoulder. It is not the blank. Two corrections, both derived, neither a literal:

1. HEIGHT. The blank is ``bay_h + 2 * TONGUE_D``. The wall seats ``TONGUE_D``
   into a housing in the deck's top face and the same into the top cap's
   underside. A vertical that merely butts a deck face has nothing locating it
   during glue-up and nothing but screws resisting rack, which is the joint the
   spine's own docstring calls the reason to have a spine at all.

2. WIDTH, and only on the end walls. The spine is ``x_right - 2t`` wide, which
   is exactly the clear span between the end walls' inner faces, so the spine's
   two END faces land on the end walls and need material behind them. A wall
   stopped at ``y_spine`` shares nothing with the spine but a line. The end
   walls therefore run the full depth, ``y_rear``, which also gives the brain
   band the two side walls it has to have and gives the rear panel something to
   land on. The dividers stop at the spine, plus one tongue.

So there are two blank widths, differing by exactly the amount the geometry
demands. Both come out of ``Datums``.


THE DIVIDER / SPINE JOINT
=========================

A divider's rear edge carries a ``TONGUE_D`` tongue into a housing in the
spine's FRONT face. Its bottom-rear and top-rear corners are notched back by
``TONGUE_D`` square so the deck and top-cap tongues stop at ``y_spine`` and do
not fight the spine's own tongues into the same two housings.

The end walls take the spine's end faces as a butt joint, fastened with a
vertical row of clearance holes through the wall on the spine's centreline.


THE LEFT END WALL IS THE LOUVRED CHEEK
======================================

The 2026-09-02 ruling gave up Carbide's 300mm of clear air off the drive's
vented face and bought it back with a louvre to room air. This panel is that
louvre. Nothing else was ever going to be: ``Datums.louvre_x`` names the left
end wall, the drive stands ``vfd_panel_standoff`` off its inner face, and the
end walls already run the full depth, so the brain band's left side IS this
blank rather than a separate cheek.

Until the field below existed the ruling was a comment. ``check_carcass`` only
asked whether the panel was big enough GROSS, which a 250 x 660 panel always is;
what the ruling actually owes is FREE area, and free area only exists once slots
are cut. ``check_bay_walls`` now measures the field it cut against
``Station.louvre_free_area_req`` rather than against the panel it came out of.

The slots run UP. Over the brain band the top cap is carried by the spine and by
these two end walls and by nothing in between, so the ribs between the slots are
that load path and a field of horizontal slots would have cut straight across
it. Running them vertically also puts the aperture in the direction the air is
already going: in low through the plinth, up past the drive, out high through
the top cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isclose, pi

from build123d import Compound, Location, Part

from lib.house import GRID
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    ISOLATOR_H,
    RABBET_D,
    ROUTER_D,
    SCREW_CLEAR_D,
    SCREW_END_INSET,
    SCREW_PILOT_D,
    SCREW_PITCH,
    SERVICE_GAP,
    T,
    Datums,
    bore,
    export_part,
    groove,
    gusset_prism,
    gussets_over,
    panel,
    relief,
    screw_line,
    screw_positions,
    through_slot,
    to_local,
)
from stations.cnc_shapeoko.parts import leg_joint

__all__ = [
    "WallSpec",
    "WALLS",
    "blank_size",
    "louvre_field",
    "build",
    "build_all",
    "place",
    "placed_all",
    "check_bay_walls",
]

D: Datums = DATUMS


# ================================================================ parameters
# Everything specific to the four verticals. Everything else comes from
# carcass.py (joinery, tooling, stack-up), params.py (the machine and its
# contents) or house.py (the grid and the materials). No dimension literal
# appears below this block.

# ---- joinery allowance ----------------------------------------------------
TONGUE_D = DADO_D
"""How far a wall enters the deck, top-cap and spine housings.

Same depth as the housing that receives it, so one number moves both sides of
the joint and it is already the house third-of-thickness."""

# ---- slides, the one vendor fact this part needs --------------------------
# Side-mount ball-bearing slides, the class the BOM buys for both the extractor
# carriage and the drawers. Height and thickness are the member's section;
# length is the pair's rated travel.
SLIDE_MEMBER_H = 45.0       # cabinet-member height, Accuride 3832 class
SLIDE_MEMBER_T = 12.7       # one member plus its clearance, per side
SLIDE_LEN = 500.0           # BOM slide length
SLIDE_FRONT_INSET = GRID    # slide's front end set back from the open front

SLIDE_BORE_D = SCREW_PILOT_D    # blind pilot for the slide's fixing screw
SLIDE_BORE_DEPTH = RABBET_D     # half the panel, so an end wall shows nothing

EXTRACTOR_SLIDE_Z = SLIDE_MEMBER_H / 2
"""Slide centreline above ``deck_top`` in the lungs bay.

Puts the cabinet member's lower edge on the deck face, which is as low as a
side-mount slide goes. See ``check_bay_walls``: this is 27mm higher than the
platform height the spine's stack-up assumes, and that is a real open item
rather than something to round away."""

# ---- lungs bay lining -----------------------------------------------------
LINING_T = 12.0
"""Mass-loaded vinyl plus open-cell foam, bonded to the bay faces. Not modelled
as geometry, because it is a bonded lay-up rather than a part, but it eats bay
width and the check has to know."""

# ---- hands bay ------------------------------------------------------------
DRAWER_SHARES = (4, 3, 2)
"""Bottom to top: deep workholding, medium instruments, shallow cutters. Shares
of ``bay_h`` rather than heights, so the drawers re-proportion if the bay
changes instead of leaving a gap at the top."""

# ---- stock bay ------------------------------------------------------------
RACK_RAIL_H = GRID * 2
"""Height of the comb rail that carries the slot pitch. Two grid modules: tall
enough to hold a 600 blank upright, short enough to lift one out over."""

RACK_RAIL_FRACS = (0.25, 0.75)
"""Where the two comb rails sit along the blank's own depth. Quarter points, so
a HALF blank is supported inboard of both its ends."""

# ---- hose port ------------------------------------------------------------
HOSE_PORT_CLEAR = 4.0
"""Radial clearance around ``hose_id`` for the cuff that lands in the port."""

# ---- the VFD louvre, left end wall only -----------------------------------
LOUVRE_PITCH = GRID
LOUVRE_RIB_W = GRID * 0.4
LOUVRE_SLOT_W = LOUVRE_PITCH - LOUVRE_RIB_W
"""Louvre field on the bench grid: a 12mm slot and an 8mm rib repeat every 20mm.

60% open, where the top cap's exhaust field is 50%. The difference is not taste.
That field answers ``VENT_MIN_OPEN_FRAC``, an assumption this repo made up; this
one answers ``Station.louvre_free_area_req``, which is the price of a clearance
Carbide asked for and did not get. At the house 50% the brain band's slice of
this panel comes up roughly 30cm2 short of that price, so the field opens until
it pays. The rib is what gets spent, and ``LOUVRE_RIB_MIN`` is the floor."""

LOUVRE_RIB_MIN = ROUTER_D
"""Thinnest rib the field may leave. One cutter diameter of 18mm birch: below it
the ribs stop being the top cap's load path over the brain band and the panel is
a grille pretending to be a wall."""

LOUVRE_LAND = T
"""Solid birch at every bound of the field: the spine's end bearing in front,
the rear door's landing behind, the deck and top-cap housings below and above,
and around any leg-bolt insert the field would otherwise run through."""


# ================================================================ wall table


@dataclass(frozen=True)
class WallSpec:
    """One of the four verticals: which bay is on which face, and how deep it
    runs. ``left`` and ``right`` name the bay each face looks into, or None for
    an outboard face."""

    index: int
    name: str
    left: str | None
    right: str | None

    @property
    def is_end(self) -> bool:
        return self.left is None or self.right is None

    def side_of(self, bay: str) -> str | None:
        """Which panel face looks into ``bay``, in ``groove``/``relief`` terms.

        The wall plane maps local +Z to station +X, so the panel's back face
        (local Z=0) is the wall's LEFT face and its front face (local Z=t) is
        the wall's RIGHT face."""
        if self.left == bay:
            return "back"
        if self.right == bay:
            return "front"
        return None


WALLS: tuple[WallSpec, ...] = (
    WallSpec(0, "left_end", None, "lungs"),
    WallSpec(1, "lungs_stock", "lungs", "stock"),
    WallSpec(2, "stock_hands", "stock", "hands"),
    WallSpec(3, "right_end", "hands", None),
)


# ================================================================ local frame
# local X = station Y (0 at the open front)
# local Y = up, with local Y = TONGUE_D sitting on deck_top
# local Z = thickness, back face at station x = wall_x[i]


def _y(station_z: float, d: Datums = D) -> float:
    """Station Z to panel-local Y."""
    return station_z - d.deck_top + TONGUE_D


def blank_size(spec: WallSpec, d: Datums = D) -> tuple[float, float]:
    """(width, height) of the cut blank for one wall.

    End walls run the full depth so the spine's ends and the brain band's sides
    have material. Dividers stop at the spine, plus their tongue into it.

    The end wall's depth comes from ``Datums.end_wall_y`` rather than from
    ``y_rear`` directly, because ``leg_joint`` reads the same property to know
    how much birch this panel presents to a leg bolt."""
    y0, y1 = d.end_wall_y
    w = y1 - y0 if spec.is_end else d.front_bay_d + TONGUE_D
    return (w, d.wall_size[1] + 2 * TONGUE_D)


# ================================================================ features


def _outline(spec: WallSpec, d: Datums = D) -> Part:
    """The blank, with the divider's two rear corner notches."""
    w, h = blank_size(spec, d)
    p = panel(w, h)
    if not spec.is_end:
        # Clear the spine's own tongues out of the deck and top-cap housings.
        for y0 in (TONGUE_D / 2, h - TONGUE_D / 2):
            p -= through_slot(
                (d.front_bay_d + TONGUE_D / 2, y0), TONGUE_D, TONGUE_D
            )
    return p


def _slide_row(y_local: float, side: str, d: Datums = D) -> Part:
    """Blind pilot bores for one slide's cabinet member, on one face."""
    x0 = SLIDE_FRONT_INSET
    cutters = None
    for p in screw_positions(SLIDE_LEN, pitch=SCREW_PITCH, inset=SCREW_END_INSET):
        c = bore(
            x0 + p, y_local, SLIDE_BORE_D, depth=SLIDE_BORE_DEPTH, side=side
        )
        cutters = c if cutters is None else cutters + c
    return cutters


def _lungs_face(side: str, d: Datums = D) -> Part:
    """Extractor carriage: one slide row, low in the bay."""
    return _slide_row(TONGUE_D + EXTRACTOR_SLIDE_Z, side, d)


def drawer_openings(d: Datums = D) -> list[tuple[float, float]]:
    """(floor, height) of each drawer opening above deck_top, bottom first."""
    total = sum(DRAWER_SHARES)
    out: list[tuple[float, float]] = []
    floor = 0.0
    for share in DRAWER_SHARES:
        height = d.bay_h * share / total
        out.append((floor, height))
        floor += height
    return out


def _hands_face(side: str, d: Datums = D) -> Part:
    """Drawers: one slide row per opening."""
    cutters = None
    for floor, _height in drawer_openings(d):
        row = _slide_row(TONGUE_D + floor + SLIDE_MEMBER_H / 2, side, d)
        cutters = row if cutters is None else cutters + row
    return cutters


def rack_rail_y(d: Datums = D) -> tuple[float, ...]:
    """Panel-local X of each stock rack comb rail.

    The blanks stand at the open front, because the front face is the one with
    no door and the rack is meant to be read from across the room."""
    depth = d.s.sheet_slot[0]
    return tuple(depth * f for f in RACK_RAIL_FRACS)


def _stock_face(side: str, d: Datums = D) -> Part:
    """Stock rack: a housing for each comb rail's end, sitting on the deck.

    The rails carry ``sheet_pitch``. The wall carries where the rails go, which
    is the rack's pitch line."""
    y0 = TONGUE_D
    y1 = TONGUE_D + RACK_RAIL_H
    cutters = None
    for x in rack_rail_y(d):
        c = groove(
            (x, y0), (x, y1), width=DADO_W, depth=DADO_D, side=side
        )
        # A round cutter cannot cut the four inside corners of a blind housing.
        for cx in (x - DADO_W / 2, x + DADO_W / 2):
            for cy in (y0, y1):
                c += relief(cx, cy, r=ROUTER_D / 2, depth=DADO_D, side=side)
        cutters = c if cutters is None else cutters + c
    return cutters


def _spine_screws(d: Datums = D) -> Part:
    """Clearance holes through an end wall into the spine's end grain."""
    x = d.y_spine + T / 2
    return screw_line(
        (x, TONGUE_D),
        (x, TONGUE_D + d.bay_h),
        d=SCREW_CLEAR_D,
    )


def _hose_port(d: Datums = D) -> Part:
    """Through port in the left end wall. The hose leaves sideways and turns in
    free air: ``hose_bend_r`` is bigger than anything inside the carcass."""
    _x, y_station, z_station = d.hose_port
    return bore(
        y_station,
        _y(z_station, d),
        d.s.hose_id + 2 * HOSE_PORT_CLEAR,
    )


@dataclass(frozen=True)
class _Louvre:
    """The VFD louvre, resolved in panel-local coordinates.

    Every slot runs the full height of the field. A column that would cross a
    leg-bolt insert is not shortened, it is DROPPED: an insert sits in the
    middle of the field's height rather than at its foot, so trimming a slot
    around one leaves two stubs and a rib that carries nothing, where omitting
    the column leaves solid birch exactly where the bolt is. See
    ``louvre_field``.
    """

    x_centres: tuple[float, ...]
    y0: float
    y1: float

    @property
    def count(self) -> int:
        return len(self.x_centres)

    @property
    def free_area(self) -> float:
        """What the ruling is actually paid in: open area through the panel.

        Measured on the CAPSULE, not on the rectangle that used to stand in for
        it. Rounding both ends of a slot costs ``(4 - pi) * r**2`` of opening,
        which is small per slot and is counted across the whole field because
        this number is the price of a traded clearance. Reporting the rectangle
        would claim free area the panel does not have.
        """
        r = LOUVRE_SLOT_W / 2
        corner_loss = (4.0 - pi) * r * r
        return self.count * max(
            LOUVRE_SLOT_W * (self.y1 - self.y0) - corner_loss, 0.0
        )


def _insert_keepouts_local(
    spec: WallSpec, d: Datums = D
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Leg-bolt insert footprints on this wall, in panel-local XY.

    ``leg_joint`` publishes them in station Y and Z, the same way the leg ties
    published their pads, and this converts: local X is station Y and ``_y``
    carries station Z. Nothing here re-derives where a bolt goes.
    """
    return [
        ((y0, y1), (_y(z0, d), _y(z1, d)))
        for _label, wall, (y0, y1), (z0, z1) in leg_joint.keepouts(d)
        if wall == spec.index
    ]


def louvre_field(d: Datums = D) -> _Louvre:
    """Vertical slots through the left end wall, over the brain band only.

    In front of the brain band the panel is the lungs bay's outer skin and a
    slot there would open a bay that is meant to be acoustically lined. Behind
    it there is nothing to open into. So the field starts at the spine's rear
    face and ends at the blank's rear edge, a ``LOUVRE_LAND`` in from each.
    """
    x0 = d.y_spine + d.t + LOUVRE_LAND
    x_limit = d.end_wall_y[1] - LOUVRE_LAND
    n = max(int((x_limit - x0 + LOUVRE_RIB_W) // LOUVRE_PITCH), 0)
    centres = tuple(x0 + LOUVRE_SLOT_W / 2 + i * LOUVRE_PITCH for i in range(n))

    y0 = TONGUE_D + LOUVRE_LAND
    y1 = TONGUE_D + d.bay_h - LOUVRE_LAND

    # A slot may not run through a leg bolt. The rear leg's insert columns land
    # in this band, so the field gives up whichever columns reach them and keeps
    # solid birch around the bolt instead.
    keepouts = _insert_keepouts_local(WALLS[0], d)
    kept = tuple(
        cx
        for cx in centres
        if not any(
            cx + LOUVRE_SLOT_W / 2 > kx0 - LOUVRE_LAND
            and cx - LOUVRE_SLOT_W / 2 < kx1 + LOUVRE_LAND
            for (kx0, kx1), _ky in keepouts
        )
    )

    return _Louvre(kept, y0, y1)


def _louvre(d: Datums = D) -> Part | None:
    """Through slots for the field. ``None`` when the band has closed up, so a
    degenerate field is reported by the check rather than raised in build.

    The slots are CAPSULES, not rectangles. Two reasons, and the second is the
    one that matters. A round cutter cannot leave a square inside corner, so a
    rectangular slot is undeliverable geometry. And this field is the visible
    face of the vent ruling, where a radius that reads as deliberate is worth
    more than a corner that has to be explained; a half-width radius is the
    roundest a slot of this width can be, so it is the one that looks intended.
    """
    v = louvre_field(d)
    if v.y1 - v.y0 <= 0:
        return None
    cutters = None
    for cx in v.x_centres:
        c = through_slot(
            (cx, (v.y0 + v.y1) / 2),
            v.y1 - v.y0,
            LOUVRE_SLOT_W,
            angle=90.0,
            corner_r=LOUVRE_SLOT_W / 2,
        )
        cutters = c if cutters is None else cutters + c
    return cutters


# ================================================================ machine relief
#
# Below the machine's frame, this panel's blank runs flush to the leg faces,
# and at each corner a gusset hangs in exactly the space that flush footprint
# wants. ``check_machine`` finds the clash; this cuts it away, over the SAME
# solid, so the notch and the check that verifies it cannot drift apart.


def _wall_local(shape: Part, i: int, d: Datums = D) -> Part:
    """A station-coordinate shape, moved into wall ``i``'s BUILD-local frame --
    ``wall_plane``'s local frame, plus the ``TONGUE_D`` that ``place`` shifts
    the finished panel by afterward. Matches ``_y``: the same station Z ends
    up at the same local Y either way."""
    return to_local(d.wall_plane(i), shape).moved(Location((0, TONGUE_D, 0)))


def _gusset_relief(spec: WallSpec, d: Datums = D) -> Part | None:
    """The gusset plates this wall's OWN nominal (unrelieved) footprint would
    otherwise clash with, cut out of it, following each one's taper rather
    than a square notch to full depth -- the relief IS the gusset's own
    trapezoidal solid, so its shape is the machine's, not a drawn approximation
    of it."""
    x_range = (d.wall_x[spec.index], d.wall_x[spec.index] + d.t)
    y_range = (0.0, blank_size(spec, d)[0])
    cutters = None
    for g in gussets_over(x_range, y_range, d.s.gussets):
        c = _wall_local(gusset_prism(g), spec.index, d)
        cutters = c if cutters is None else cutters + c
    return cutters


# ================================================================ leg joint
#
# The end walls' OUTER faces ARE the leg inner faces: the carcass footprint is
# flush to them by the 2026-09-02 ruling, and the legs are square, so a bolt
# through a leg's own hole lands straight in this panel with nothing between.
# ``leg_joint`` owns the pattern and the hole; this panel receives them, the same
# way it receives the gusset relief -- as a station-coordinate solid brought into
# the panel's frame, so the cut and the check that verifies it are one solid.


def _insert_cuts(spec: WallSpec, d: Datums = D) -> Part | None:
    """Counterbore and pilot for every leg-bolt insert in this wall.

    ``None`` on the two dividers, which touch no leg.
    """
    cut = leg_joint.insert_cutters(spec.index, d)
    return None if cut is None else _wall_local(cut, spec.index, d)


# ================================================================ build


def build(i: int = 0, d: Datums = D) -> Part:
    """The flat, panel-local solid for wall ``i``."""
    spec = WALLS[i]
    p = _outline(spec, d)

    for bay, feature in (
        ("lungs", _lungs_face),
        ("stock", _stock_face),
        ("hands", _hands_face),
    ):
        side = spec.side_of(bay)
        if side is not None:
            p -= feature(side, d)

    if spec.is_end:
        p -= _spine_screws(d)

    if spec.index == 0:
        p -= _hose_port(d)
        louvre = _louvre(d)
        if louvre is not None:
            p -= louvre

    inserts = _insert_cuts(spec, d)
    if inserts is not None:
        p -= inserts

    relief_cut = _gusset_relief(spec, d)
    if relief_cut is not None:
        p -= relief_cut

    return p


def build_all(d: Datums = D) -> list[Part]:
    return [build(i, d) for i in range(len(WALLS))]


def place(i: int, flat: Part, d: Datums = D) -> Part:
    """Stand a flat wall up in station coordinates.

    The blank's local Y=0 is the bottom of the tongue, ``TONGUE_D`` below
    ``deck_top``, so it drops by that much before meeting ``wall_plane``."""
    return d.wall_plane(i) * flat.moved(Location((0, -TONGUE_D, 0)))


def placed_all(d: Datums = D) -> list[Part]:
    return [place(i, w, d) for i, w in enumerate(build_all(d))]


# ================================================================ feature map
#
# What is already cut in a panel, as circles in panel-local XY, so a new feature
# can be asked whether it lands on an old one. Built from the SAME helpers the
# build cuts with -- ``screw_positions``, ``rack_rail_y``, ``drawer_openings`` --
# so a feature that moves cannot move here without moving there.


FEATURE_WEB = ROUTER_D
"""Birch that has to survive between two features. One cutter diameter: below it
the router is cutting air on both sides of a rib it cannot support."""


def _wall_features(
    spec: WallSpec, d: Datums = D
) -> list[tuple[str, float, float, float]]:
    """(label, local x, local y, radius) of every feature already in this wall.

    Blind and through alike. An insert is blind from the OUTER face and a slide
    bore is blind from the INNER face, but they are cut in the same 18mm of
    birch from opposite sides, and 9mm plus 15mm does not fit in 18: two blind
    features that overlap in plan meet in the middle of the panel.
    """
    out: list[tuple[str, float, float, float]] = []

    slide_r = SLIDE_BORE_D / 2
    slide_xs = [
        SLIDE_FRONT_INSET + p
        for p in screw_positions(SLIDE_LEN, pitch=SCREW_PITCH, inset=SCREW_END_INSET)
    ]

    if spec.side_of("lungs") is not None:
        for x in slide_xs:
            out.append(("lungs slide mount", x, TONGUE_D + EXTRACTOR_SLIDE_Z, slide_r))

    if spec.side_of("hands") is not None:
        for k, (floor, _h) in enumerate(drawer_openings(d)):
            y = TONGUE_D + floor + SLIDE_MEMBER_H / 2
            for x in slide_xs:
                out.append((f"drawer {k} slide mount", x, y, slide_r))

    if spec.side_of("stock") is not None:
        # A comb-rail housing is a groove, not a hole; a circle on its centreline
        # at half the dado width is the right keep-out for a bolt beside it.
        for x in rack_rail_y(d):
            y0, y1 = TONGUE_D, TONGUE_D + RACK_RAIL_H
            out.append(("stock rack rail housing", x, (y0 + y1) / 2, DADO_W / 2))

    if spec.is_end:
        x = d.y_spine + T / 2
        for p in screw_positions(d.bay_h):
            out.append(("spine screw", x, TONGUE_D + p, SCREW_CLEAR_D / 2))

    if spec.index == 0:
        _x, y_station, z_station = d.hose_port
        out.append(
            (
                "hose port",
                y_station,
                _y(z_station, d),
                (d.s.hose_id + 2 * HOSE_PORT_CLEAR) / 2,
            )
        )

    return out


# ================================================================ checks


def check_bay_walls(d: Datums = D) -> list[str]:
    """Constraints these four panels own."""
    s = d.s
    notes: list[str] = []

    # -- the lungs stack-up, which is where this part disagrees with the spine
    # The real stack stands on a slide member, not on a bare platform: a
    # side-mount cabinet member cannot sit lower than the deck face. Compare the
    # real stack against the bay rather than against lungs_stack_h's assumption.
    needed = SLIDE_MEMBER_H + ISOLATOR_H + s.extractor_env[2] + SERVICE_GAP
    over = needed - d.bay_h
    if over > 0:
        notes.append(
            f"the fitted {s.spec['name']} on a {SLIDE_MEMBER_H:.0f}mm side-mount "
            f"member wants {needed:.0f}mm into a {d.bay_h:.0f}mm bay, over by "
            f"{over:.0f}mm, taking the {d.top_gap:.0f}mm reveal to "
            f"{d.top_gap - over:.0f}mm. Ways out: a shorter slide member, "
            "spending the service gap, or letting the carcass grow."
        )

    # -- lungs bay width, once the acoustic lining and the slides are in
    carriage_w = (
        d.lungs_x[1] - d.lungs_x[0] - 2 * LINING_T - 2 * SLIDE_MEMBER_T
    )
    if carriage_w < s.extractor_env[1]:
        notes.append(
            f"lungs carriage is {carriage_w:.0f}mm wide once "
            f"{LINING_T:.0f}mm of lining and {SLIDE_MEMBER_T:.1f}mm of slide "
            f"go on each side, against the extractor's {s.extractor_env[1]:.0f}mm"
        )

    # -- the extractor still has to lie down in the bay
    if s.extractor_env[0] + SLIDE_FRONT_INSET > d.front_bay_d:
        notes.append(
            f"extractor {s.extractor_env[0]:.0f}mm long plus a "
            f"{SLIDE_FRONT_INSET:.0f}mm slide inset does not lie in a "
            f"{d.front_bay_d:.0f}mm bay"
        )

    # -- drawers
    for k, (floor, height) in enumerate(drawer_openings(d)):
        if height < SLIDE_MEMBER_H + SERVICE_GAP:
            notes.append(
                f"drawer {k} opening is {height:.0f}mm, under a "
                f"{SLIDE_MEMBER_H:.0f}mm slide plus {SERVICE_GAP:.0f}mm service"
            )
        if TONGUE_D + floor + SLIDE_MEMBER_H > blank_size(WALLS[2], d)[1]:
            notes.append(f"drawer {k} slide runs off the top of the wall")

    # -- stock rack
    if s.sheet_slot[0] > d.front_bay_d:
        notes.append(
            f"a HALF blank is {s.sheet_slot[0]:.0f}mm deep into a "
            f"{d.front_bay_d:.0f}mm bay, so the rack rails fall outside the wall"
        )
    if d.stock_capacity < 1:
        notes.append(
            f"stock bay is {d.stock_clear_w:.0f}mm clear and holds no blanks at "
            f"{s.sheet_pitch:.0f}mm pitch. The bay has stopped being a rack."
        )

    # -- hose port has to be in the panel, clear of the edges
    w, h = blank_size(WALLS[0], d)
    port_r = (s.hose_id + 2 * HOSE_PORT_CLEAR) / 2
    px, py = d.hose_port[1], _y(d.hose_port[2], d)
    if not (port_r < px < w - port_r and port_r < py < h - port_r):
        notes.append(
            f"hose port at local ({px:.0f}, {py:.0f}) does not clear the left "
            f"end wall's {w:.0f} x {h:.0f} blank"
        )

    # -- the VFD louvre, which is what the traded clearance was bought with
    v = louvre_field(d)
    if s.vfd_vent_mode == "panel":
        if v.count == 0:
            notes.append(
                f"the brain band is {d.brain_d:.0f}mm deep and the louvre's "
                f"{LOUVRE_LAND:.0f}mm lands eat it. No slot left, so the drive "
                "vents into a sealed cheek."
            )
        elif v.free_area < s.louvre_free_area_req:
            notes.append(
                f"the brain-band louvre is {v.free_area / 100:.0f}cm2 free "
                f"against the {s.louvre_free_area_req / 100:.0f}cm2 the traded "
                f"clearance was paid for with ({s.vfd_louvre_free_ratio:.1f}x "
                f"the drive's {s.vfd_fan_count} {s.vfd_fan:.1f}mm square fan "
                "apertures). Carbide's 300mm was given up for this aperture "
                "and the aperture is short."
            )

    if LOUVRE_SLOT_W < ROUTER_D:
        notes.append(
            f"louvre slot is {LOUVRE_SLOT_W:.1f}mm and the carcass cutter is "
            f"{ROUTER_D:.2f}mm. The field needs a smaller tool."
        )
    if LOUVRE_RIB_W < LOUVRE_RIB_MIN:
        notes.append(
            f"louvre ribs are {LOUVRE_RIB_W:.1f}mm against a "
            f"{LOUVRE_RIB_MIN:.2f}mm floor. Over the brain band these ribs carry "
            "the top cap, and the field has opened until they stopped being a "
            "load path."
        )

    # -- leg-bolt inserts against everything already cut in the same panel
    # This is the question the leg ties never had to answer: they bolted to the
    # OUTSIDE of the birch and shared nothing with it but a pad. An insert is
    # 15mm into an 18mm panel, so it meets a blind slide bore coming the other
    # way even though neither goes through.
    insert_r = leg_joint.WALL_CBORE_D / 2
    for spec in WALLS:
        feats = _wall_features(spec, d)
        for (kx0, kx1), (ky0, ky1) in _insert_keepouts_local(spec, d):
            cx, cy = (kx0 + kx1) / 2, (ky0 + ky1) / 2
            for label, fx, fy, fr in feats:
                gap = hypot(cx - fx, cy - fy) - insert_r - fr
                if gap < FEATURE_WEB:
                    notes.append(
                        f"a leg-bolt insert in the {spec.name} at local "
                        f"({cx:.0f}, {cy:.0f}) lands {gap:.1f}mm from a {label} "
                        f"at ({fx:.0f}, {fy:.0f}), against a {FEATURE_WEB:.2f}mm "
                        "web. Both are blind and they are cut from opposite "
                        "faces of the same 18mm panel, so they meet inside it."
                    )

    # -- what the louvre gave up to the bolts, which is a design fact and not a
    # defect. Reported so the field's slot count is never read as a full field.
    x0 = d.y_spine + d.t + LOUVRE_LAND
    x_limit = d.end_wall_y[1] - LOUVRE_LAND
    nominal = max(int((x_limit - x0 + LOUVRE_RIB_W) // LOUVRE_PITCH), 0)
    dropped = nominal - louvre_field(d).count
    if dropped:
        notes.append(
            f"the brain-band louvre gives up {dropped} of {nominal} columns to "
            "the rear leg's bolt inserts, keeping solid birch where the bolt is "
            "rather than running a slot through it. The field still pays the "
            "traded clearance on the columns that remain. Expected, and worth "
            "knowing before the field is read as short."
        )

    # -- the two blank widths are the ones the geometry demands, not a choice
    if not isclose(blank_size(WALLS[1], d)[0], d.front_bay_d + TONGUE_D):
        notes.append("divider blank width has drifted off front_bay_d")

    return notes


# ================================================================ main

_EXPORT_STEM = "bay_wall"


if __name__ == "__main__":
    walls = build_all()
    placed = placed_all()

    print("BAY WALLS: four verticals, one generator")
    print(
        f"  blanks: end wall {blank_size(WALLS[0])[0]:.0f} x "
        f"{blank_size(WALLS[0])[1]:.0f} x {T:.0f}   "
        f"divider {blank_size(WALLS[1])[0]:.0f} x "
        f"{blank_size(WALLS[1])[1]:.0f} x {T:.0f}"
    )
    print(
        f"  clear opening per Datums.wall_size "
        f"{D.wall_size[0]:.0f} x {D.wall_size[1]:.0f}, plus {TONGUE_D:.0f}mm of "
        f"tongue top and bottom"
    )
    lv = louvre_field()
    print(
        f"  VFD louvre in wall 0: {lv.count} slots {LOUVRE_SLOT_W:.0f} wide at "
        f"{LOUVRE_PITCH:.0f} pitch on {LOUVRE_RIB_W:.0f}mm ribs, "
        f"{lv.free_area / 100:.0f}cm2 free against "
        f"{D.s.louvre_free_area_req / 100:.0f}cm2 required"
    )

    written: list[str] = []
    for spec, flat, up in zip(WALLS, walls, placed):
        fb = flat.bounding_box()
        pb = up.bounding_box()
        print(
            f"\n  wall {spec.index} {spec.name}"
            f"\n    flat bbox   {fb.size.X:.1f} x {fb.size.Y:.1f} x {fb.size.Z:.1f}"
            f"   volume {flat.volume / 1000:.0f} cm3"
            f"\n    placed      x {pb.min.X:.1f}..{pb.max.X:.1f}"
            f"   y {pb.min.Y:.1f}..{pb.max.Y:.1f}"
            f"   z {pb.min.Z:.1f}..{pb.max.Z:.1f}"
        )
        for p in export_part(flat, f"{_EXPORT_STEM}_{spec.index}_{spec.name}"):
            written.append(str(p))

    ab = Compound(children=placed).bounding_box()
    print(
        f"\n  four walls placed: "
        f"{ab.size.X:.1f} x {ab.size.Y:.1f} x {ab.size.Z:.1f}   "
        f"x {ab.min.X:.1f}..{ab.max.X:.1f}  y {ab.min.Y:.1f}..{ab.max.Y:.1f}  "
        f"z {ab.min.Z:.1f}..{ab.max.Z:.1f}"
    )

    print("\n  wrote:")
    for p in written:
        print(f"    {p}")

    found = check_bay_walls()
    if found:
        print(f"\n{len(found)} bay-wall note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno bay-wall constraint violations")
