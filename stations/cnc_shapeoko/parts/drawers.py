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
  * the INSET FACE of each drawer (2026-09-04): a sixth panel, the front the
    operator sees, standing flush in the carcass plane between the
    stock/hands divider and the console cheek, screwed to the box's front
    from inside. RULED: "absolutely no overlays ... a la kerf design
    cabinets". The box front is structure; the face is the front.
  * the rabbets and dados that hold them together, and the dogbones the one
    blind housing needs
  * the pilot rows for the slide's DRAWER member, on the two outer faces,
    matching the pattern ``bay_walls`` drills for the CABINET member
  * the V-carved callout on each FACE, on its own DXF layer, and the
    register the painted face goes back on the machine with
  * the pull, which is an aperture and therefore capsule-ended, through the
    face and, where the box front stands behind it, relieved through the
    box front too so the fingers pass

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

Since C12 (2026-09-03) a box can also be NARROWED: every drawer whose opening
crosses ``console_plate.CONSOLE_BAND`` gives up ``console_plate.DRAWER_GIVE``
on its RIGHT side to the console's chase, by Jared's ruling that the console's
device depth comes out of the overlapped drawers' width and not out of moving
the plate. ``narrowing`` reads which and how much off that module; the box's
left side and both side clearances stay where they were, and its right-hand
slide moves inboard onto the chase's cheek. The others stay 373.

DEPTH is ``SLIDE_LEN``. A side-mount pair wants its two members the same length
and flush, so the box is exactly as deep as the slide and its front face lands
at ``SLIDE_FRONT_INSET``, which is where ``bay_walls`` starts the cabinet
member: one panel thickness back, directly behind the inset face that fills
the first ``T`` of the bay.

THE FACE (2026-09-04, Kerf)
===========================

Each drawer's FACE is a separate ``T`` panel standing in the front opening
between the stock/hands divider's face and the console cheek's bay face
(``console_plate.cheek_x``), ``FRONT_REVEAL`` off each, its outer face flush
with the carcass plane at ``y_front``. The three faces stack with
``FRONT_REVEAL`` between them and to the deck and the cap
(``face_z``), so the column reads as one run of inset panels; the box behind
each is narrower by the slides' clearance and shorter by the service gap, and
the face covers both. Four screws from inside the box through its front into
the face (``FACE_SCREW``); the face carries the pull and the callout, and the
box front is plain. Where the pull's capsule lies over the box front, the
front takes a matching relief a hand-clearance larger so the fingers pass.

HEIGHT is the opening less one ``SERVICE_GAP``, snapped DOWN to the grid. The
snap is what makes three boxes out of a bay whose 4:3:2 shares are 275.6,
206.7 and 137.8mm: 240, 180 and 100, each with more than a service gap of air
over it.
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

Each front is V-carved with its bay's name -- CUTTERS, INSTRUMENTS,
WORKHOLDING -- ``callouts.VCARVE_D`` deep on its outer face, through the
matte black to raw birch, no fill (finish ruling, 2026-09-03). The letters
and the carve come from ``callouts``, which was this file's own helper until
C17 and produces the same geometry it did then. Two DXF layers are added by
hand in ``export()`` rather than inferred: ``VCARVE``, the letter outlines
(``flat_pattern`` would call the carve a pocket at a depth, which is true and
useless, since a pocket and a V-carve go to different tools on different
fixtures), and ``REGISTER``, the two circles the painted front is pinned back
on the machine with. A front has no screw holes on its face -- it is held in
the sides' rabbets and screwed through the sides -- so the register is the
pull's two end arcs, ``PULL_H`` pins 100mm apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Part, Plane

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
from stations.cnc_shapeoko.parts import callouts, console_plate
from stations.cnc_shapeoko.parts.bay_walls import (
    SLIDE_BORE_D,
    SLIDE_BORE_DEPTH,
    SLIDE_FRONT_INSET,
    SLIDE_LEN,
    SLIDE_MEMBER_H,
    drawer_openings,
)
from stations.cnc_shapeoko.parts.rear_door import TOP_REVEAL

__all__ = [
    "DrawerSpec",
    "DRAWERS",
    "BOTTOM_T",
    "BACK_INSET",
    "BACK_DROP",
    "BOTTOM_GROOVE_Z",
    "narrowing",
    "callout_for",
    "register_for",
    "box_size",
    "box_origin",
    "interior",
    "FRONT_REVEAL",
    "face_x",
    "face_z",
    "face_size",
    "build_face",
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
``PULL_DROP`` below the top edge of the FACE."""

FRONT_REVEAL = TOP_REVEAL
"""Gap between a face and whatever bounds it: the divider, the cheek, the
deck, the cap, the next face. The house reveal, the rear door's figure.
SOURCE: rear_door.TOP_REVEAL. CONFIDENCE: design (2026-09-04)."""

HAND_RELIEF = GRID / 2
"""How far past the pull the box front's relief runs, all round, where the
pull lies over it: fingers through the face need room behind it. SOURCE:
lungs_door.HAND_RELIEF, the same figure for the same reason. CONFIDENCE:
design."""

FACE_SCREW = f"4 x {2 * T - 4:.0f} pan head, four per drawer, from inside the box through its front into the face"
"""How the face fixes to the box: through the box front's 18 into the face's
18, stopping 4 short of the room face. Positions are the shop's on the fit
(the face is squared in its opening first, then screwed). CONFIDENCE:
chosen."""

# The carve's depth, cap height and font moved to ``callouts`` in C17 with
# their values unchanged (VCARVE_D, CALLOUT_H, CALLOUT_FONT).


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

    def outside(self, d: Datums | None = None) -> tuple[float, float, float]:
        """Outside (w, depth, h), narrowing included. What the slides see."""
        return box_size(self, D if d is None else d)

    def inside(self, d: Datums | None = None) -> tuple[float, float, float]:
        """Clear (w, depth, h) inside the box. What a tray is cut to."""
        return interior(self, D if d is None else d)


DRAWERS: tuple[DrawerSpec, ...] = (
    DrawerSpec(1, "D1", "CUTTERS", "endmills, V-bits and the ER-16 collets", 2),
    DrawerSpec(2, "D2", "INSTRUMENTS", "dust boots, pen holder, way oil, deburr and brush", 1),
    DrawerSpec(3, "D3", "WORKHOLDING", "clamps, Crush-It, T-handle drivers, joinery stop, hardware case", 0),
)


# ================================================================ sizes


def opening(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    """(floor above deck_top, clear height) of this drawer's opening."""
    return drawer_openings(d)[spec.opening]


def narrowing(spec: DrawerSpec, d: Datums = D) -> float:
    """How much this box gives up on its right side to the console's chase:
    ``DRAWER_GIVE`` (the keep-out plus the cheek its slide screws to) when its
    opening crosses the console band, else 0."""
    if spec.opening in console_plate.narrowed_openings(d):
        return console_plate.DRAWER_GIVE
    return 0.0


def box_size(spec: DrawerSpec, d: Datums = D) -> tuple[float, float, float]:
    """Outside (width, depth, height) of one box.

    Width from the slide maker's build recommendation less whatever the
    console takes, depth from the slide's length, height from the opening less
    a service gap, snapped down to grid.
    """
    w = d.s.bay_hands_w - d.s.drawer_slide_build_under - narrowing(spec, d)
    depth = SLIDE_LEN
    h = snap_dn(opening(spec, d)[1] - TOP_CLEAR)
    return (w, depth, h)


def box_origin(spec: DrawerSpec, d: Datums = D) -> tuple[float, float, float]:
    """Station coordinates of the box's lower, left, front corner.

    One side clearance off the divider so the two clearances are equal -- the
    right-hand one is measured to the console cheek when the box is narrowed,
    to the end wall when it is not -- set back by ``SLIDE_FRONT_INSET`` so the
    box front is flush with the front end of the cabinet member, and standing
    on its opening's floor.
    """
    x0 = d.hands_x[0] + d.s.drawer_slide_build_under / 2
    y0 = SLIDE_FRONT_INSET
    z0 = d.deck_top + opening(spec, d)[0]
    return (x0, y0, z0)


def side_clearance(spec: DrawerSpec, d: Datums = D) -> float:
    """Air between one side of the box and the face its slide mounts to: the
    bay wall, or the console cheek on a narrowed box's right side."""
    return (d.s.bay_hands_w - narrowing(spec, d) - box_size(spec, d)[0]) / 2


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


def face_x(d: Datums = D) -> tuple[float, float]:
    """Station X span every face fills: the stock/hands divider's face to the
    console cheek's bay face, one reveal in from each. Derived; one span for
    all three because the cheek runs to the deck (2026-09-04)."""
    return (d.hands_x[0] + FRONT_REVEAL, console_plate.cheek_x(d)[0] - FRONT_REVEAL)


def face_z(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    """Station Z span of one face: its opening, less a full reveal at the
    deck and the cap and half a reveal at each face-to-face joint, so every
    gap in the column is ``FRONT_REVEAL``."""
    openings = drawer_openings(d)
    floor, height = openings[spec.opening]
    lo = FRONT_REVEAL if spec.opening == 0 else FRONT_REVEAL / 2
    hi = FRONT_REVEAL if spec.opening == len(openings) - 1 else FRONT_REVEAL / 2
    return (d.deck_top + floor + lo, d.deck_top + floor + height - hi)


def face_size(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    """The face's blank, (width, height)."""
    x0, x1 = face_x(d)
    z0, z1 = face_z(spec, d)
    return (x1 - x0, z1 - z0)


def pull_local(spec: DrawerSpec, d: Datums = D) -> tuple[float, float]:
    """Face-local centre of the pull: mid-width, PULL_DROP below the top."""
    w, h = face_size(spec, d)
    return (w / 2, h - PULL_DROP)


def pull_on_front(spec: DrawerSpec, d: Datums = D) -> tuple[float, float] | None:
    """Front-local centre of the pull's relief in the BOX FRONT, or None when
    the pull's band lies wholly above the box front's top edge."""
    fw, fh = front_size(spec, d)
    x0, _y0, z0 = box_origin(spec, d)
    px, pz = pull_local(spec, d)
    z_pull = face_z(spec, d)[0] + pz
    y_local = z_pull - z0
    if y_local - PULL_H / 2 - HAND_RELIEF >= fh:
        return None
    return (face_x(d)[0] + px - (x0 + T - RABBET_D), y_local)


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


def _plane_face(spec: DrawerSpec, d: Datums = D) -> Plane:
    """The face: like the front, local X = station +X, local Y up, thickness
    into -Y from its inside face at y_front + T, so local Z = T is the face
    the operator reads."""
    return Plane(
        origin=(face_x(d)[0], d.y_front + T, face_z(spec, d)[0]),
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


def callout_for(spec: DrawerSpec, d: Datums = D) -> callouts.Callout:
    """The face's word, centred in the band below the pull, on the Z = t
    face the operator reads. One geometry, two jobs: ``callouts.carve`` cuts
    it into the face, and ``callouts.layers`` writes its outlines to the
    DXF. Drawing the callout twice is how a carve ends up not matching the
    model."""
    w, h = face_size(spec, d)
    cy = (h - PULL_DROP - PULL_H / 2) / 2
    return callouts.Callout(spec.callout, (w / 2, cy))


def register_for(spec: DrawerSpec, d: Datums = D) -> callouts.Register:
    """The second fixture's datums: the pull's two end arcs, which a
    ``PULL_H`` pin seats in. The face carries no screw holes on its face."""
    cx, cy = pull_local(spec, d)
    dx = (PULL_L - PULL_H) / 2
    return callouts.Register(
        (cx - dx, cy, PULL_H), (cx + dx, cy, PULL_H), "the pull's two end arcs"
    )


def build_face(spec: DrawerSpec, d: Datums = D, *, carve: bool = True) -> Part:
    """The inset face, flat: the blank, the capsule pull, the word. Its
    Z = t face is the one the operator reads. Nothing else: the face screws
    on from behind and its edges are reveals."""
    w, h = face_size(spec, d)
    p = panel(w, h)
    p -= through_slot(pull_local(spec, d), PULL_L, PULL_H, corner_r=PULL_H / 2)
    if carve:
        p = callouts.carve(p, [callout_for(spec, d)])
    return p


def build_front(spec: DrawerSpec, d: Datums = D) -> Part:
    """The box front, flat: plain birch behind the face, with the bottom
    groove and, where the face's pull lies over it, a relief for the hand."""
    w, h = front_size(spec, d)
    p = panel(w, h)

    # bottom groove, on the inside face (Z = 0 under _plane_front)
    gy = BOTTOM_GROOVE_Z + DADO_W / 2
    p -= groove((0, gy), (w, gy), width=DADO_W, depth=DADO_D, side="back")

    # the hand's way through behind the pull: an aperture, capsule-ended,
    # HAND_RELIEF larger than the pull all round, running out the top edge
    # where the pull sits above it
    at = pull_on_front(spec, d)
    if at is not None:
        p -= through_slot(
            at, PULL_L + 2 * HAND_RELIEF, PULL_H + 2 * HAND_RELIEF,
            corner_r=(PULL_H + 2 * HAND_RELIEF) / 2,
        )
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
        (f"{spec.name}_face", build_face(spec, d), _plane_face(spec, d)),
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
        out.append(
            (f"{n}_front", f"{n}_face", "bearing", None, 0.0, 0.0,
             f"face flat on the box front's outer face, {FACE_SCREW}")
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
            f"{n}_face": (face_x(d), (d.y_front, d.y_front + T), face_z(spec, d)),
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

        # the face: inset in its opening, flush, covering the box, its pull
        # relieved through the box front where it needs to be
        fx0, fx1 = face_x(d)
        fz0, fz1 = face_z(spec, d)
        if fx0 - FRONT_REVEAL < d.hands_x[0] - 1e-6 or fx1 + FRONT_REVEAL > console_plate.cheek_x(d)[0] + 1e-6:
            notes.append(f"{n}_face runs past the divider or the cheek")
        if fx0 > x0 + 1e-6 or fx1 < x0 + w - 1e-6:
            notes.append(f"{n}_face ({fx0:.1f}..{fx1:.1f}) does not cover its box ({x0:.1f}..{x0 + w:.1f})")
        # the box stands on its opening's floor and the face keeps its reveal
        # to the deck or the face below, so the box front's lowest FRONT_REVEAL
        # shows in the gap: black on black, and the same on every drawer
        if fz0 > z0 + FRONT_REVEAL + 1e-6 or fz1 < z0 + h - 1e-6:
            notes.append(f"{n}_face (z {fz0:.1f}..{fz1:.1f}) does not cover its box (z {z0:.1f}..{z0 + h:.1f})")
        if fz1 - fz0 < PULL_DROP + PULL_H / 2 + FRONT_REVEAL:
            notes.append(f"{n}_face is {fz1 - fz0:.1f} tall and the pull runs off it")
        at = pull_on_front(spec, d)
        if at is not None and (at[1] - PULL_H / 2 - HAND_RELIEF) < BOTTOM_GROOVE_Z + DADO_W:
            notes.append(f"{n}: the hand relief in the box front runs into the bottom groove")
        if abs(SLIDE_FRONT_INSET - T) > 1e-9:
            notes.append(
                f"the box front sits at y {SLIDE_FRONT_INSET:.1f} and the face is {T:.0f} "
                "thick: the face does not lie on the box front"
            )

        # the callout lands on birch, and the face goes back on its pins
        notes += callouts.check_callouts(
            build_face(spec, d),
            [callout_for(spec, d)],
            register_for(spec, d),
            size=face_size(spec, d),
            label=f"{n}_face",
        )

    # Every box pulls out through the front plane, and a front leg's Y flange
    # is a plate across that plane at each corner (MEASURED 2026-09-04,
    # inboard), with a stile behind it (RULED the same day). A box whose X
    # span overlaps either does not pass it at any point of its travel, so
    # this is an interval test, not a sweep. ``machine`` is imported here
    # because it imports the assembly that imports this part.
    from stations.cnc_shapeoko.machine import front_leg_flanges
    from stations.cnc_shapeoko.parts import stiles

    fixed = list(front_leg_flanges(d)) + [
        (label, part) for label, _g, part in stiles.placed_all(d) if "_front_" in label
    ]
    for flabel, flange in fixed:
        fb = flange.bounding_box()
        for spec in DRAWERS:
            x0, _y0, _z0 = box_origin(spec, d)
            w = box_size(spec, d)[0]
            clear = side_clearance(spec, d)
            over = min(x0 + w + clear, fb.max.X) - max(x0 - clear, fb.min.X)
            if over > 0.0:
                notes.append(
                    f"{spec.name} and its slides span x {x0 - clear:.1f}..{x0 + w + clear:.1f} "
                    f"and the {flabel} stands across the front plane at x {fb.min.X:.1f}.."
                    f"{fb.max.X:.1f}: the box overlaps it by {over:.1f}mm. The drawer does "
                    "not pull out."
                )
    notes.append(
        f"INSET FACES, standing note. RULED 2026-09-04 (Kerf, no overlays): each drawer's "
        f"face is a separate {T:.0f}mm panel flush in the carcass plane, x "
        f"{face_x(d)[0]:.1f}..{face_x(d)[1]:.1f} between the divider and the console "
        f"cheek with {FRONT_REVEAL:.0f} reveals all round; faces "
        + ", ".join(f"{sp.name} {face_size(sp, d)[0]:.1f} x {face_size(sp, d)[1]:.1f}" for sp in DRAWERS)
        + f"; {FACE_SCREW}. The box front behind it is plain and relieved for the hand "
        "where the pull lies over it. Expected, and worth knowing before a front is "
        "cut to the box."
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
    """STEP and DXF for one box's five panels and its face.

    The face goes out with the ``VCARVE`` and ``REGISTER`` layers that
    ``flat_pattern`` cannot infer: its CUT layers are read off the un-carved
    blank so the callout does not also appear as a pocket, and the STEP
    still carries the carve.
    """
    written = []
    for label, part, _plane in panels(spec, d):
        if label.endswith("_face"):
            w, _h = face_size(spec, d)
            layers = flat_pattern(build_face(spec, d, carve=False))
            layers.update(
                callouts.layers([callout_for(spec, d)], register_for(spec, d), width=w)
            )
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
            + (f"   narrowed {narrowing(spec, d):.1f} for the console" if narrowing(spec, d) else "")
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
