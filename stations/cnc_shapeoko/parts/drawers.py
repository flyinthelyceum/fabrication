"""Drawers: the three boxes in the hands bay, on full-extension slides.

One generator, three boxes, hung off the slide rows ``bay_walls`` already
drills into the two faces of the hands bay:

    drawer 1  CUTTERS       shallow, top      opening index 2
    drawer 2  INSTRUMENTS   medium, middle    opening index 1
    drawer 3  WORKHOLDING   deep, bottom      opening index 0

The numbering is the brief's, top down, because that is how an operator reads
the stack standing in front of it. ``bay_walls.drawer_openings`` hands back its
openings bottom first, which is how a panel gets cut, and ``DrawerSpec.opening``
is the one place those two orders meet. Nothing else in this file knows the
order the openings arrive in.


WHAT THIS PART OWNS
===================

  * the five panels of each box: two sides, a front, a back, a bottom
  * the rabbets and dados that hold them together, and the dogbones the one
    blind housing needs
  * the pilot rows for the slide's DRAWER member, on the two outer faces,
    matching the pattern ``bay_walls`` drills for the CABINET member
  * the engraved callout on each front, on its own DXF layer
  * the pull, which is an aperture and therefore capsule-ended

It does NOT own where the slides go. ``bay_walls`` committed those rows, and
this file reads ``SLIDE_LEN``, ``SLIDE_FRONT_INSET`` and ``SLIDE_MEMBER_H`` out
of it rather than agreeing with it twice.


THE THREE DIMENSIONS, AND WHERE EACH ONE COMES FROM
===================================================

WIDTH comes from the slide maker, not from the cabinet. Accuride's 3832 sheet
says two different things and they are not interchangeable:
``drawer_slide_side_clear`` (12.7mm per side) is the CONSTRAINT, below which
the slide does not run, and ``drawer_slide_build_under`` (27.0mm off the
opening) is the RECOMMENDATION, which is 13.5 per side and sits inside the
tolerance band instead of on its floor. The box is built to the recommendation
and ``check_drawers`` measures the result against the constraint. Building to
the constraint directly would put every box on the floor of the band with the
whole of plywood's thickness tolerance still to spend.

DEPTH is ``SLIDE_LEN``. A side-mount pair wants its two members the same length
and flush, so the box is exactly as deep as the slide and its front face lands
at ``SLIDE_FRONT_INSET``, which is where ``bay_walls`` starts the cabinet
member. That is also why the fronts sit one grid module back from the bay's
open face: the recess is the slide's, not a styling choice, and it is what the
fingers reach into over the pull.

HEIGHT is the opening less one ``SERVICE_GAP``, snapped DOWN to the grid. The
snap is what makes three boxes out of a bay whose thirds are 293.3, 220.0 and
146.7mm: 260, 200 and 120, each with more than a service gap of air over it.
A drawer that used every millimetre of its opening would bind on a bay that is
600mm of birch away from being square.


THE STOCK IS 18mm, THE SAME BIRCH AS THE CARCASS
================================================

``PANEL_T`` is 3mm smoked acrylic, so it was never a candidate; the only birch
in this model is ``CARCASS_T``. That is heavier than a drawer needs -- 18mm
sides cost 36mm of the box's inside width -- and it is still right. One
thickness means one sheet to buy and one offcut pile, and every joint in this
file is already a function of ``T`` through ``DADO_W``, ``DADO_D`` and
``RABBET_D``, so a second thickness would need a second joinery vocabulary to
go with it. ``BOTTOM_T`` is named separately for the day a 6mm bottom is worth
a second sheet; it is set to ``T`` and everything derives from it.


THE JOINTS, AND WHERE THE DOGBONES ARE
======================================

The carcass's vocabulary, unchanged: housings cut ``DADO_FIT`` oversize,
glued, and screwed through the receiver.

    front   sits in a RABBET at each side's front end, ``RABBET_D`` deep, so
            the side wraps the front's edge and the pull's load goes into a
            shoulder rather than into a screw
    back    sits in a stopped DADO, ``BACK_INSET`` in from each side's back end
    bottom  runs in a groove in all four panels, edge to edge

Every one of those housings runs off at least one edge except the back's, which
is blind at the top because the back stops ``BACK_DROP`` short of the box top --
so contents sweep out over it and the joint does not show on the top edge. That
blind end is the only square inside corner in the drawer, and it gets a
``relief`` on each of its two corners. The rest need none: a round cutter
leaves no unrelieved corner in a housing that never turns one.

The pull is an APERTURE, so it is capsule-ended, per the rule in
``through_slot``'s docstring. Nothing seats in it but a hand.

Screws land above ``SLIDE_MEMBER_H`` on both outer faces, because the slide's
drawer member covers that band and a screw head under a slide is a drawer that
does not close. Their pitch is tighter than the carcass's ``SCREW_PITCH``,
which is sized for a 900mm glue line; a drawer joint is short and gets pulled
in tension every time somebody opens it.


THE FRONTS CARRY THE CALLOUT
============================

Each front is engraved with its bay's name -- CUTTERS, INSTRUMENTS,
WORKHOLDING -- ``ENGRAVE_D`` deep, on its own ``ENGRAVE`` DXF layer so the shop
runs it as a V-carve and fills it. The layer is added by hand in ``export()``
rather than inferred: ``flat_pattern`` would call it a pocket at a depth, which
is true and useless, and a pocket layer and an engrave layer go to different
tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import (
    Align,
    Location,
    Part,
    Plane,
    Sketch,
    Text,
    available_fonts,
    extrude,
)

from lib.house import GRID
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    RABBET_D,
    RABBET_W,
    SCREW_CLEAR_D,
    SERVICE_GAP,
    T,
    Datums,
    bore,
    export_part,
    flat_pattern,
    groove,
    panel,
    relief,
    screw_line,
    screw_positions,
    snap_dn,
    through_slot,
)
from stations.cnc_shapeoko.parts.bay_walls import (
    SLIDE_BORE_D,
    SLIDE_BORE_DEPTH,
    SLIDE_FRONT_INSET,
    SLIDE_LEN,
    SLIDE_MEMBER_H,
    drawer_openings,
)

__all__ = [
    "DrawerSpec",
    "DRAWERS",
    "BOTTOM_T",
    "BACK_INSET",
    "BACK_DROP",
    "BOTTOM_GROOVE_Z",
    "ENGRAVE_D",
    "box_size",
    "box_origin",
    "interior",
    "build_side",
    "build_front",
    "build_back",
    "build_bottom",
    "panels",
    "placed",
    "placed_all",
    "joint_table",
    "check_drawers",
    "export",
]

D: Datums = DATUMS


# ================================================================ parameters
# Everything specific to the three boxes. The slide's own numbers come from
# bay_walls, the birch and the joinery from carcass.py, the side clearance from
# params.py. No dimension literal appears below this block.

BOTTOM_T = T
"""Bottom panel thickness. Set to the carcass stock so the drawer is one
material; named so a thinner bottom is one edit and not a hunt."""

BACK_INSET = T
"""How far the back's dado sits in from each side's back end. One thickness, so
the side wraps the back and the slide has full-length material under it."""

BACK_DROP = GRID
"""How far the back stops below the box top, so contents sweep out over it.
This is what makes the back's dado blind, and the blind end is where the two
dogbones go."""

BOTTOM_GROOVE_Z = T / 2
"""Underside of the bottom's groove, above the box's bottom edge. Half a
thickness leaves the same material below the groove as the groove is deep."""

TOP_CLEAR = SERVICE_GAP
"""Air over the box inside its opening, before the height is snapped to the
grid. The service gap the rest of the station already uses."""

SCREW_PITCH_DRAWER = T * 4
SCREW_INSET_DRAWER = T
"""Fastener spacing on a drawer's corner joints. Tighter than the carcass's
``SCREW_PITCH`` (T * 8), which is sized for a 900mm glue line. A drawer corner
is short and is pulled in tension on every open."""

PULL_H = GRID
PULL_L = GRID * 6
PULL_DROP = GRID * 1.5
"""The pull: a capsule aperture, one grid module tall and six long, its centre
``PULL_DROP`` below the top edge of the front."""

ENGRAVE_D = 1.0
"""Depth of the engraved callout. Deep enough to hold a fill, shallow enough
that an 18mm front is still an 18mm front."""

CALLOUT_H = GRID * 0.6
"""Cap height of the callout text."""

CALLOUT_FONTS = ("Helvetica", "Arial", "DejaVu Sans", "Liberation Sans")
"""Preference order for every engraved callout in the station. Resolved against
``available_fonts()`` at import, because a headless box and a laptop do not have
the same font list and a font that is missing is silently substituted -- which
is a different drawing, cut without anyone being told."""


def _house_font() -> str:
    """First preferred font this machine actually has, else whatever it has."""
    try:
        have = {f.name for f in available_fonts()}
    except Exception:                       # no font manager on this box
        return CALLOUT_FONTS[0]
    for name in CALLOUT_FONTS:
        if name in have:
            return name
    return min(have) if have else CALLOUT_FONTS[0]


CALLOUT_FONT = _house_font()


# ================================================================ the table


@dataclass(frozen=True)
class DrawerSpec:
    """One of the three boxes. ``opening`` indexes ``drawer_openings``, which
    counts from the bottom, and ``number`` is the brief's, which counts from
    the top."""

    number: int
    key: str            # matches the ``drawer`` column of tools/tool_list.csv
    callout: str        # engraved on the front
    contents: str
    opening: int        # index into bay_walls.drawer_openings()

    @property
    def name(self) -> str:
        return f"drawer{self.number}_{self.callout.lower()}"


DRAWERS: tuple[DrawerSpec, ...] = (
    DrawerSpec(1, "D1", "CUTTERS", "endmills, V-bits and the ER-16 collets", 2),
    DrawerSpec(2, "D2", "INSTRUMENTS", "boots, probe, hand tools, pendant", 1),
    DrawerSpec(3, "D3", "WORKHOLDING", "clamps, T-track hardware, tapes", 0),
)


# ================================================================ sizes


def opening(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    """(floor above deck_top, clear height) of this drawer's opening."""
    return drawer_openings(d)[spec.opening]


def box_size(spec: DrawerSpec, d: Datums = D) -> tuple[float, float, float]:
    """Outside (width, depth, height) of one box.

    Width from the slide maker's build recommendation, depth from the slide's
    length, height from the opening less a service gap, snapped down to grid.
    """
    w = d.s.bay_hands_w - d.s.drawer_slide_build_under
    depth = SLIDE_LEN
    h = snap_dn(opening(spec, d)[1] - TOP_CLEAR)
    return (w, depth, h)


def box_origin(spec: DrawerSpec, d: Datums = D) -> tuple[float, float, float]:
    """Station coordinates of the box's lower, left, front corner.

    Centred across the hands bay so the two side clearances are equal, set back
    by ``SLIDE_FRONT_INSET`` so the box front is flush with the front end of
    the cabinet member, and standing on its opening's floor.
    """
    w, _depth, _h = box_size(spec, d)
    x0 = d.hands_x[0] + (d.s.bay_hands_w - w) / 2
    y0 = SLIDE_FRONT_INSET
    z0 = d.deck_top + opening(spec, d)[0]
    return (x0, y0, z0)


def side_clearance(spec: DrawerSpec, d: Datums = D) -> float:
    """Air between one side of the box and the bay wall it faces."""
    return (d.s.bay_hands_w - box_size(spec, d)[0]) / 2


def interior(spec: DrawerSpec, d: Datums = D) -> tuple[float, float, float]:
    """Clear (width, depth, height) inside the box, measured off the bottom's
    top face. This is what a tray is cut to."""
    w, depth, h = box_size(spec, d)
    return (
        w - 2 * T,
        depth - T - BACK_INSET - T,
        h - (BOTTOM_GROOVE_Z + BOTTOM_T),
    )


def bottom_size(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    """The bottom's blank: the clear interior plus the groove it runs in on all
    four sides."""
    iw, idep, _ih = interior(spec, d)
    return (iw + 2 * DADO_D, idep + 2 * DADO_D)


def back_size(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    iw, _idep, _ih = interior(spec, d)
    _w, _depth, h = box_size(spec, d)
    return (iw + 2 * DADO_D, h - BACK_DROP)


def front_size(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    iw, _idep, _ih = interior(spec, d)
    _w, _depth, h = box_size(spec, d)
    return (iw + 2 * RABBET_D, h)


def _back_dado_x(spec: DrawerSpec, d: Datums = D) -> float:
    """Side-local X of the back dado's centreline."""
    _w, depth, _h = box_size(spec, d)
    return depth - BACK_INSET - DADO_W / 2


# ================================================================ local frames
# Every panel is drawn flat on the house convention: local X across the blank,
# local Y up it, local Z the thickness with the back face at Z = 0. The planes
# below stand each one up, and check_drawers asserts every placed bounding box
# against the span it was supposed to land in -- which is the only honest way to
# check a sign in a rotation.
#
#   side    local X = station +Y (0 at the box front), local Y = station +Z
#   front   local X = station +X, local Y = station +Z, thickness into -Y
#   back    same orientation as the front, so both fronts of the drawing are
#           the faces you look at when the drawer is open
#   bottom  local X = station +X, local Y = station +Y, flat


def _plane_side(spec: DrawerSpec, hand: str, d: Datums = D) -> Plane:
    x0, y0, z0 = box_origin(spec, d)
    w, _depth, _h = box_size(spec, d)
    x = x0 if hand == "left" else x0 + w - T
    return Plane(origin=(x, y0, z0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def _side_faces(hand: str) -> tuple[str, str]:
    """(inner, outer) in ``groove``/``bore`` terms for one side.

    Both sides are drawn in the same orientation, so which face is the inside
    of the box flips with the hand. That flip is here and nowhere else.
    """
    return ("front", "back") if hand == "left" else ("back", "front")


def _plane_front(spec: DrawerSpec, d: Datums = D) -> Plane:
    x0, y0, z0 = box_origin(spec, d)
    return Plane(
        origin=(x0 + T - RABBET_D, y0 + T, z0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)
    )


def _plane_back(spec: DrawerSpec, d: Datums = D) -> Plane:
    x0, y0, z0 = box_origin(spec, d)
    _w, depth, _h = box_size(spec, d)
    return Plane(
        origin=(x0 + T - DADO_D, y0 + depth - BACK_INSET, z0),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def _plane_bottom(spec: DrawerSpec, d: Datums = D) -> Plane:
    x0, y0, z0 = box_origin(spec, d)
    return Plane(
        origin=(x0 + T - DADO_D, y0 + T - DADO_D, z0 + BOTTOM_GROOVE_Z),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1),
    )


# ================================================================ features


def _edge_screws(
    cx: float, lo: float, hi: float, *, thickness: float = T
) -> Part | None:
    """A row of clearance holes up one corner joint, or one hole when the band
    is too short to space two. Returns None when there is no band at all."""
    if hi - lo <= 2 * SCREW_INSET_DRAWER:
        if hi - lo <= 0:
            return None
        return bore(cx, (lo + hi) / 2, SCREW_CLEAR_D, thickness=thickness)
    return screw_line(
        (cx, lo),
        (cx, hi),
        thickness=thickness,
        d=SCREW_CLEAR_D,
        pitch=SCREW_PITCH_DRAWER,
        inset=SCREW_INSET_DRAWER,
    )


def build_side(spec: DrawerSpec, hand: str, d: Datums = D) -> Part:
    """One side of the box, flat. ``hand`` is "left" or "right"."""
    _w, depth, h = box_size(spec, d)
    inner, outer = _side_faces(hand)
    back_h = back_size(spec, d)[1]
    cx_back = _back_dado_x(spec, d)

    p = panel(depth, h)

    # front rabbet: the front's edge, wrapped by the side. Runs edge to edge.
    p -= groove(
        (RABBET_W / 2, 0),
        (RABBET_W / 2, h),
        width=RABBET_W,
        depth=RABBET_D,
        side=inner,
    )

    # back dado: stopped at back_h, so it does not show on the top edge
    p -= groove(
        (cx_back, 0), (cx_back, back_h), width=DADO_W, depth=DADO_D, side=inner
    )
    for sign in (-1, 1):
        p -= relief(
            cx_back + sign * DADO_W / 2, back_h, depth=DADO_D, side=inner
        )

    # bottom groove, edge to edge: it crosses the back dado at the same depth,
    # which leaves the bottom's rear corners a clean pocket to sit in
    gy = BOTTOM_GROOVE_Z + DADO_W / 2
    p -= groove((0, gy), (depth, gy), width=DADO_W, depth=DADO_D, side=inner)

    # the slide's DRAWER member, on the outer face. Same pattern bay_walls
    # drills for the cabinet member, and flush with it: the box is exactly as
    # deep as the slide and starts where the cabinet member starts.
    for x in screw_positions(SLIDE_LEN):
        p -= bore(
            x,
            SLIDE_MEMBER_H / 2,
            SLIDE_BORE_D,
            depth=SLIDE_BORE_DEPTH,
            side=outer,
        )

    # corner screws, above the band the drawer member covers
    for cx, top in ((RABBET_W / 2, h), (cx_back, back_h)):
        row = _edge_screws(cx, SLIDE_MEMBER_H, top)
        if row is not None:
            p -= row

    return p


def _callout(spec: DrawerSpec, d: Datums = D) -> Sketch:
    """The engraved callout as a flat sketch at Z = 0, in panel-local XY.

    One geometry, two jobs: extruded it is the pocket cut into the front, and
    as faces it is the ENGRAVE layer of the DXF. Drawing the callout twice is
    how a fill ends up not matching the cut.
    """
    w, h = front_size(spec, d)
    sk = Text(
        spec.callout,
        font_size=CALLOUT_H,
        font=CALLOUT_FONT,
        align=(Align.CENTER, Align.CENTER),
    )
    cy = (h - PULL_DROP - PULL_H / 2) / 2
    return sk.moved(Location((w / 2, cy, 0)))


def build_front(spec: DrawerSpec, d: Datums = D, *, engrave: bool = True) -> Part:
    """The drawer front, flat. Its Z = t face is the one the operator reads."""
    w, h = front_size(spec, d)
    p = panel(w, h)

    # bottom groove, on the inside face (Z = 0 under _plane_front)
    gy = BOTTOM_GROOVE_Z + DADO_W / 2
    p -= groove((0, gy), (w, gy), width=DADO_W, depth=DADO_D, side="back")

    # the pull: an aperture, so capsule-ended
    p -= through_slot(
        (w / 2, h - PULL_DROP), PULL_L, PULL_H, corner_r=PULL_H / 2
    )

    if engrave:
        cut = extrude(_callout(spec, d), amount=ENGRAVE_D)
        p -= cut.moved(Location((0, 0, T - ENGRAVE_D)))
    return p


def build_back(spec: DrawerSpec, d: Datums = D) -> Part:
    """The back, flat. Shorter than the box by ``BACK_DROP``."""
    w, h = back_size(spec, d)
    p = panel(w, h)
    gy = BOTTOM_GROOVE_Z + DADO_W / 2
    # the inside face of the back is its Z = t face under _plane_back
    p -= groove((0, gy), (w, gy), width=DADO_W, depth=DADO_D, side="front")
    return p


def build_bottom(spec: DrawerSpec, d: Datums = D) -> Part:
    """The bottom, flat. No features: it runs in four grooves and is glued."""
    w, dep = bottom_size(spec, d)
    return panel(w, dep, BOTTOM_T)


# ================================================================ assembly


def panels(spec: DrawerSpec, d: Datums = D) -> list[tuple[str, Part, Plane]]:
    """(label, flat part, plane) for every panel of one box."""
    return [
        (f"{spec.name}_side_l", build_side(spec, "left", d), _plane_side(spec, "left", d)),
        (f"{spec.name}_side_r", build_side(spec, "right", d), _plane_side(spec, "right", d)),
        (f"{spec.name}_front", build_front(spec, d), _plane_front(spec, d)),
        (f"{spec.name}_back", build_back(spec, d), _plane_back(spec, d)),
        (f"{spec.name}_bottom", build_bottom(spec, d), _plane_bottom(spec, d)),
    ]


def placed(spec: DrawerSpec, d: Datums = D) -> list[tuple[str, Part]]:
    """Every panel of one box, stood up in station coordinates."""
    return [(label, plane * part) for label, part, plane in panels(spec, d)]


def placed_all(d: Datums = D) -> list[tuple[str, Part]]:
    """Every panel of all three boxes."""
    out: list[tuple[str, Part]] = []
    for spec in DRAWERS:
        out.extend(placed(spec, d))
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints inside each box, as
    ``(a, b, kind, axis, lo, hi, note)`` tuples.

    Tuples rather than ``assembly.Joint`` objects so that a part module never
    imports the assembly that imports it. ``assembly.joints`` turns these into
    Joints alongside the carcass's own.
    """
    out: list[tuple] = []
    for spec in DRAWERS:
        x0, y0, z0 = box_origin(spec, d)
        w, depth, _h = box_size(spec, d)
        n = spec.name
        # the two sides' inner faces, and how far a housing reaches into them
        for hand, face_x, inward in (
            ("side_l", x0 + T, -1.0),
            ("side_r", x0 + w - T, 1.0),
        ):
            for member, deep in (
                ("front", RABBET_D),
                ("back", DADO_D),
                ("bottom", DADO_D),
            ):
                lo, hi = sorted((face_x, face_x + inward * deep))
                out.append(
                    (
                        f"{n}_{hand}",
                        f"{n}_{member}",
                        "housing",
                        "x",
                        lo,
                        hi,
                        f"{member} edge in the side's housing",
                    )
                )
        # the front and back house the bottom's two ends in Y
        f_face = y0 + T
        b_face = y0 + depth - BACK_INSET - T
        out.append(
            (f"{n}_front", f"{n}_bottom", "housing", "y", f_face - DADO_D, f_face,
             "bottom's front edge in the front's groove")
        )
        out.append(
            (f"{n}_back", f"{n}_bottom", "housing", "y", b_face, b_face + DADO_D,
             "bottom's rear edge in the back's groove")
        )
    return out


# ================================================================ checks


def check_drawers(d: Datums = D) -> list[str]:
    """What the three boxes have to be true for."""
    notes: list[str] = []
    s = d.s

    for spec in DRAWERS:
        w, depth, h = box_size(spec, d)
        floor, clear_h = opening(spec, d)
        clear = side_clearance(spec, d)
        n = spec.name

        if clear < s.drawer_slide_side_clear:
            notes.append(
                f"{n} leaves {clear:.1f}mm per side and the slide maker's "
                f"minimum is {s.drawer_slide_side_clear:.1f}mm. Below it the "
                "slide binds."
            )

        if h + SERVICE_GAP > clear_h + 1e-9:
            notes.append(
                f"{n} is {h:.0f}mm tall in a {clear_h:.0f}mm opening, leaving "
                f"{clear_h - h:.0f}mm. Under a {SERVICE_GAP:.0f}mm service gap "
                "the box drags on the drawer above it."
            )

        if depth + SLIDE_FRONT_INSET > d.front_bay_d + 1e-9:
            notes.append(
                f"{n} is {depth:.0f}mm deep behind a {SLIDE_FRONT_INSET:.0f}mm "
                f"inset, into a {d.front_bay_d:.0f}mm bay. It hits the spine."
            )

        if BACK_DROP >= h:
            notes.append(f"{n}: the back has dropped below its own bottom groove")

        if BOTTOM_GROOVE_Z + BOTTOM_T + SLIDE_MEMBER_H > h:
            notes.append(
                f"{n}: the slide's drawer member is taller than the box side "
                "above the bottom groove; there is nothing to screw it to"
            )

        # the placement is a rotation, and a rotation is where signs go wrong.
        # Check every panel landed in the span it was supposed to.
        x0, y0, z0 = box_origin(spec, d)
        want = {
            f"{n}_side_l": ((x0, x0 + T), (y0, y0 + depth), (z0, z0 + h)),
            f"{n}_side_r": ((x0 + w - T, x0 + w), (y0, y0 + depth), (z0, z0 + h)),
            f"{n}_front": (
                (x0 + T - RABBET_D, x0 + w - T + RABBET_D),
                (y0, y0 + T),
                (z0, z0 + h),
            ),
            f"{n}_back": (
                (x0 + T - DADO_D, x0 + w - T + DADO_D),
                (y0 + depth - BACK_INSET - T, y0 + depth - BACK_INSET),
                (z0, z0 + h - BACK_DROP),
            ),
            f"{n}_bottom": (
                (x0 + T - DADO_D, x0 + w - T + DADO_D),
                (y0 + T - DADO_D, y0 + depth - BACK_INSET - T + DADO_D),
                (z0 + BOTTOM_GROOVE_Z, z0 + BOTTOM_GROOVE_Z + BOTTOM_T),
            ),
        }
        for label, part in placed(spec, d):
            bb = part.bounding_box()
            got = (
                (bb.min.X, bb.max.X),
                (bb.min.Y, bb.max.Y),
                (bb.min.Z, bb.max.Z),
            )
            for axis, g, e in zip("xyz", got, want[label]):
                if abs(g[0] - e[0]) > 0.05 or abs(g[1] - e[1]) > 0.05:
                    notes.append(
                        f"{label} landed at {axis} {g[0]:.1f}..{g[1]:.1f} and "
                        f"belongs at {e[0]:.1f}..{e[1]:.1f}. Its plane is wrong."
                    )

    # The bottom drawer stands on the deck's own face, because bay_walls put
    # its slide row at the bottom of the bay and the box hangs level with it.
    bottom = min(DRAWERS, key=lambda s2: opening(s2, d)[0])
    if opening(bottom, d)[0] <= 1e-9:
        notes.append(
            f"{bottom.name} sits on deck_top with no air under it: the bay's "
            "lowest slide row starts at the deck, so the only under-clearance "
            "the bottom drawer has is the slide's own running clearance. "
            "Expected, and worth knowing before somebody stores a mat on the "
            "deck under it."
        )

    return notes


# ================================================================ export


def export(spec: DrawerSpec, d: Datums = D) -> list:
    """STEP and DXF for one box's five panels.

    The front goes out with an ``ENGRAVE`` layer that ``flat_pattern`` cannot
    infer: it is read off the un-engraved blank so the callout does not also
    appear as a pocket, and the STEP still carries the engraving.
    """
    written = []
    for label, part, _plane in panels(spec, d):
        if label.endswith("_front"):
            layers = flat_pattern(build_front(spec, d, engrave=False))
            layers["ENGRAVE"] = list(_callout(spec, d).faces())
            written += export_part(part, label, layers=layers)
        else:
            written += export_part(part, label)
    return written


# ================================================================ report


if __name__ == "__main__":
    d = DATUMS
    print(
        f"drawers: hands bay {d.s.bay_hands_w:.0f} clear x "
        f"{d.front_bay_d:.0f} deep x {d.bay_h:.0f} tall, "
        f"{SLIDE_LEN:.0f}mm slides at {SLIDE_FRONT_INSET:.0f}mm inset"
    )
    for spec in DRAWERS:
        w, dep, h = box_size(spec, d)
        floor, clear_h = opening(spec, d)
        iw, idep, ih = interior(spec, d)
        x0, y0, z0 = box_origin(spec, d)
        print(
            f"  {spec.number} {spec.callout:<12} {w:6.1f} x {dep:6.1f} x {h:6.1f} "
            f"outside   inside {iw:6.1f} x {idep:6.1f} x {ih:5.1f}"
        )
        print(
            f"      opening {clear_h:6.1f} tall at z {d.deck_top + floor:6.1f}   "
            f"side clearance {side_clearance(spec, d):.1f}mm per side "
            f"(minimum {d.s.drawer_slide_side_clear:.1f})   "
            f"headroom {clear_h - h:.1f}mm"
        )

    found = check_drawers(d)
    if found:
        print(f"\n{len(found)} drawer note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno drawer constraint violations")

    for spec in DRAWERS:
        for p in export(spec, d):
            print(f"wrote {p}")
