"""Top cap for the Shapeoko 5 Pro 4x4 station carcass. Build order 4 of 5.

WHAT IT IS
==========

The top skin of the torsion box. It drops on last, houses the top edge of all
four bay walls and the spine, and its own top face is ``Datums.carcass_h``. Above
it is ``Datums.top_gap``, the reveal, and then the machine frame. The cap never
touches the frame.

It does three jobs beyond closing the box:

1.  IT IS THE TOP OF THE VFD CHIMNEY.  ``carcass.py`` decision 1 made the brain
    band a chimney rather than a sealed 250mm box: air in low through the plinth
    and the deck, up past the vertically standing drive, out high through this
    panel.  The exhaust aperture is a louvre field of through slots sitting
    directly over ``Datums.brain_exhaust_x`` and spanning ``brain_intake_y``, so
    the exhaust is over the intake by construction and moves when the corridor
    moves.  The slots run front-to-back, which leaves continuous ribs tying the
    spine housing to the rear edge; slots running across would have left the cap
    as a ladder of unsupported rungs over a 430mm span.

2.  IT CARRIES THE MAST BASE PADS.  Four M8 clearance holes per pad, on a square
    at the extrusion's own 40mm section, at each rear outboard corner.  A 40x40
    mast cannot rise through a 35mm reveal, so the mast base bolts down HERE and
    the column cantilevers outboard past the leg and rises outside the machine
    footprint (the frame overhangs the leg opening by roughly 210mm a side, so
    the column clears the frame regardless of where on the cap the pad sits).
    Which corner the mast actually takes is not settled: ``Datums.hose_port`` is
    in the LEFT end wall and the hose runs to the mast, which argues left.  Both
    pads are cut anyway, because the alternative is drilling the second one in
    situ under an assembled machine.  Set ``MAST_PADS`` to one side and the model
    regenerates with one.

3.  IT TIES THE VERTICALS.  A ``DADO_D`` housing registers each panel and a
    ``screw_line`` down each centreline pulls the cap onto it.

WHAT IT DOES NOT DO
===================

It cuts no housing at the rear edge.  The rear of the brain band is a DOOR (the
brief's rear panel with the circuit indicators on its inside face), and a door
carries nothing.  So over the brain band the cap is carried by the spine and by
the two end walls, which run the full depth to ``y_rear``, and by nothing in
between.  The mast pads are placed on that basis: the front bolt row sits
``MAST_PAD_SETBACK`` behind the spine centreline, near enough that the pad bears
on the spine rather than on 18mm of ply in bending.  A steel backing plate under
each pad spreads the bolt load, the same move the leg-tie bracket makes against
the 3.4mm leg wall.  That plate is not a birch part and is not modelled here.


WHAT THIS PART CUTS, FOR THE PARTS IT MATES WITH
================================================

Everything here is a housing ``DADO_W`` wide and ``HOUSE_ENGAGE`` deep in the
UNDERSIDE, plus a row of plain clearance holes on the housed panel's centreline:

    end walls (0, 3)   edge rabbet, x 0..DADO_W and x_right-DADO_W..x_right,
                       running y 0..y_rear, through at both ends
    dividers  (1, 2)   centred dado on wall_x[i] + t/2, running y 0..y_spine,
                       blind at the rear with a dogbone at each corner
    spine              centred dado on y_spine + t/2, running the FULL blank
                       width x 0..x_right, through at both ends

ONE OPEN ITEM, AND IT IS NOT THIS PART'S TO SETTLE.  ``bay_walls`` cuts the end
walls 1150 deep (full depth, so the brain band gets side walls) while
``spine_panel`` cuts the spine 1100 wide (full width, so its ends reach the end
walls) and describes the end walls as stopping at ``y_spine``.  Both cannot be
true: they claim the same 18 x 18 column at each rear corner.  This part cuts the
UNION of the two readings, so the cap accepts whichever way that corner is
resolved without being recut, and the housings that would be left empty under one
reading are hidden 6mm pockets in the underside.  The tie screws are placed the
other way round, only where both readings agree there is material, except along
the end walls behind ``y_spine``, where they follow ``bay_walls`` because that is
the part that is actually cut that way.

PANEL CONVENTION
================

Drawn flat per ``carcass.py``: origin at the lower-left of the blank, +X width,
+Y height, +Z thickness, back face at Z=0.  ``Datums.top_plane`` has
``x_dir=(1,0,0)`` and ``z_dir=(0,0,1)``, so for this part panel-local X and Y are
station X and Y unchanged, and the back face at local Z=0 is the UNDERSIDE at
station z = ``top_z[0]``.  Every housing is therefore cut ``side="back"``.

Every dimension below derives from ``params.py``, ``house.py`` or ``carcass.py``.
Nothing here is measured off the drawing.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Part

from lib.house import GRID
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    ROUTER_D,
    SCREW_CLEAR_D,
    SCREW_D,
    T,
    TOP_GAP_MIN,
    Datums,
    bore,
    clear_over_relieved,
    export_part,
    groove,
    gusset_prism,
    gussets_over,
    panel,
    relief,
    screw_line,
    snap_up,
    through_slot,
    to_local,
)

NAME = "top_cap"


# ---------------------------------------------------------------- parameters
# Everything specific to THIS part. Shared boundaries come from Datums, joinery
# from carcass.py, standards from house.py. No literal below appears in the
# geometry twice, and none of them is a measurement.

# -- the mast base pads --------------------------------------------------------

MAST_PADS: tuple[str, ...] = ("left", "right")
"""Which rear outboard corners get a pad. hose_port says the mast goes LEFT;
the right pad is cut now because drilling it later means drilling under an
assembled machine. Set to ("left",) once the handedness is settled."""

MAST_BOLT_D = 8.0
"""M8 through the cap into the mast base plate. Bigger than the carcass's own
SCREW_D because this one carries a cantilevered column, a counterweight and a
hose under tension, not a glued panel joint."""

MAST_BOLT_CLEAR_D = MAST_BOLT_D + (SCREW_CLEAR_D - SCREW_D)
"""Same clearance allowance the carcass uses on its own fasteners, scaled to the
bigger bolt, so one number governs fit across the station."""

MAST_BOLT_PITCH = GRID * 2
"""Square bolt pattern at the extrusion's own 40x40 section, so the base plate's
bolt square reads as the mast's own footprint rather than an arbitrary rectangle.
Also 2 grid modules."""

MAST_PAD_EDGE_INSET = GRID * 2
"""Outboard bolt row in from the outboard edge of the blank. One extrusion width
of solid birch outside the bolt, which is well past the 2D minimum edge distance
the check below enforces."""

MAST_PAD_SETBACK = MAST_BOLT_PITCH / 2
"""Front bolt row behind the spine centreline. Half a bolt pitch: far enough to
clear the spine's own screw line, near enough that the pad bears on the spine."""

MAST_PAD_MARGIN = GRID
"""Solid birch claimed around the bolt square for the backing plate. Nothing else
is cut inside this footprint, which is what keeps the louvre field off the pad."""

MAST_CANTILEVER_MAX = GRID * 4
"""How far behind the spine's rear face the rearmost mast bolt may sit before the
cap is being asked to be a beam. 80mm of 18mm birch over a 40mm bolt square with
a steel backing plate is a bracket; much more than that is a diving board."""

# -- the chimney exhaust -------------------------------------------------------

VENT_SLOT_W = GRID / 2
VENT_RIB_W = GRID / 2
VENT_PITCH = VENT_SLOT_W + VENT_RIB_W
"""Louvre field on the bench grid: a 10mm slot and a 10mm rib repeat every 20mm.
The slot is comfortably wider than ROUTER_D so it cuts in two passes and does not
need a smaller cutter."""

VENT_RAIL_FRONT = T
"""Solid rail between the spine housing and the first slot."""

VENT_RAIL_REAR = T * 2
"""Solid rail along the rear edge. Twice the front rail because this edge is the
cantilever's free end and has no panel under it."""

VENT_RAIL_SIDE = T
"""Solid rail at each end of the field, against the corridor bounds and against
the mast pad footprint."""

VENT_MIN_SLOTS = 8
"""Below this the field has stopped being a chimney mouth and is decoration.
Fires if leg_x_inner shrinks far enough to squeeze the corridor."""

VENT_MIN_OPEN_FRAC = 0.15
"""ASSUMPTION, not a spec. Open area over the brain band's plan area. Nobody
publishes a free-area figure for a passive electronics chimney; 15% is the number
this model will be judged against and it is written down so it can be argued
with. Currently the field clears it by a wide margin."""

# -- the ties ------------------------------------------------------------------

SCREW_CBORE = None
"""No counterbore on the tie screws. The housing floor is only T - DADO_D below
the top face on these lines, so a standard T/2 counterbore would leave 3mm of ply
under the head. A pan head and washer sit on the surface instead, hidden by the
35mm reveal and honest about being a fastener."""


# ---------------------------------------------------------------- derivations


@dataclass(frozen=True)
class _Pad:
    """One mast base pad, resolved in panel-local coordinates."""

    side: str
    xs: tuple[float, float]
    ys: tuple[float, float]

    @property
    def bolts(self) -> list[tuple[float, float]]:
        return [(x, y) for x in self.xs for y in self.ys]

    @property
    def span_x(self) -> tuple[float, float]:
        return (min(self.xs) - MAST_PAD_MARGIN, max(self.xs) + MAST_PAD_MARGIN)

    @property
    def span_y(self) -> tuple[float, float]:
        return (min(self.ys) - MAST_PAD_MARGIN, max(self.ys) + MAST_PAD_MARGIN)


def mast_pads(d: Datums = DATUMS) -> list[_Pad]:
    """The pads, placed off the blank edges and the spine, not off literals."""
    w, _ = d.top_size
    pads: list[_Pad] = []
    for side in MAST_PADS:
        if side == "left":
            x_out = d.x_left + MAST_PAD_EDGE_INSET
            x_in = x_out + MAST_BOLT_PITCH
        elif side == "right":
            x_out = w - MAST_PAD_EDGE_INSET
            x_in = x_out - MAST_BOLT_PITCH
        else:
            raise ValueError(f"MAST_PADS takes left|right, got {side!r}")
        y_front = d.y_spine + d.t / 2 + MAST_PAD_SETBACK
        pads.append(_Pad(side, (x_out, x_in), (y_front, y_front + MAST_BOLT_PITCH)))
    return pads


@dataclass(frozen=True)
class _VentField:
    """The chimney exhaust, resolved in panel-local coordinates."""

    x_centres: tuple[float, ...]
    y0: float
    y1: float

    @property
    def count(self) -> int:
        return len(self.x_centres)

    @property
    def slot_len(self) -> float:
        return self.y1 - self.y0

    @property
    def open_area(self) -> float:
        return self.count * VENT_SLOT_W * self.slot_len


def vent_field(d: Datums = DATUMS) -> _VentField:
    """Louvre field over the brain band, inside ``brain_exhaust_x`` and clear
    of any mast pad that reaches into it."""
    cx0, cx1 = d.brain_exhaust_x
    by0, by1 = d.brain_intake_y

    y0 = by0 + VENT_RAIL_FRONT
    y1 = by1 - VENT_RAIL_REAR

    left_edge = cx0
    for pad in mast_pads(d):
        px0, px1 = pad.span_x
        py0, py1 = pad.span_y
        overlaps_y = py0 < y1 and py1 > y0
        if overlaps_y and px1 > left_edge and px0 < cx1:
            left_edge = max(left_edge, px1)

    x0 = snap_up(left_edge + VENT_RAIL_SIDE)
    x_limit = cx1 - VENT_RAIL_SIDE
    n = int((x_limit - x0 + VENT_RIB_W) // VENT_PITCH)
    n = max(n, 0)
    centres = tuple(x0 + VENT_SLOT_W / 2 + i * VENT_PITCH for i in range(n))
    return _VentField(centres, y0, y1)


@dataclass(frozen=True)
class _Housing:
    """One vertical panel's housing in the underside of the cap.

    ``x0..x1`` is the housing's width, ``y0..y1`` its run. ``blind`` says whether
    the far end dies in material, which is what decides whether it needs a
    dogbone at the end.
    """

    x0: float
    x1: float
    y0: float
    y1: float
    screw_x: float
    blind: bool
    is_end: bool

    @property
    def mid_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def width(self) -> float:
        return self.x1 - self.x0


def wall_housings(d: Datums = DATUMS) -> list[_Housing]:
    """The housing each of the four bay walls' top edges drops into.

    Two shapes, because the walls are two shapes:

    END WALLS run the full depth to ``y_rear`` (they are also the brain band's
    side walls), so their housing runs right through and breaks out at both the
    front and the rear edge of the blank. They are flush with the outboard edge
    of the blank, so the housing is an edge rabbet run in from that edge rather
    than a centred dado; a centred dado would hang DADO_FIT/2 off the blank and
    leave a 0.1mm feather of birch down the whole edge.

    INTERNAL DIVIDERS stop at ``y_spine``, so their housing is a centred dado
    with a blind end and two dogbones.
    """
    w, _ = d.top_size
    out: list[_Housing] = []
    for x in d.wall_x:
        is_end = x <= d.x_left or x + d.t >= w
        if x <= d.x_left:
            x0, x1 = d.x_left, d.x_left + DADO_W
        elif x + d.t >= w:
            x0, x1 = w - DADO_W, w
        else:
            xc = x + d.t / 2
            x0, x1 = xc - DADO_W / 2, xc + DADO_W / 2
        y1 = d.y_rear if is_end else d.y_spine
        out.append(_Housing(x0, x1, d.y_front, y1, x + d.t / 2, not is_end, is_end))

    # The GROWTH lungs/stock divider station, cut on day one and left empty.
    # Converting to the growth extractor moves one panel into a slot that is
    # already there instead of recutting the cap, which is one of the two
    # largest panels in the station. A removable birch spline fills it meanwhile.
    gx = d.wall_x_growth[1]
    gxc = gx + d.t / 2
    out.append(
        _Housing(
            gxc - DADO_W / 2,
            gxc + DADO_W / 2,
            d.y_front,
            d.y_spine,
            gxc,
            True,
            False,
        )
    )
    return out


def spine_housing(d: Datums = DATUMS) -> tuple[float, float, float]:
    """(y centreline, x start, x end) of the spine's housing.

    Full blank width. ``Datums.spine_size`` is the CLEAR span between the end
    walls' inner faces, but the spine's blank is that plus HOUSE_ENGAGE at every
    housed edge, and the spine panel is cut full width so its ends reach the end
    walls. Running the housing right across also means it breaks out at both
    edges instead of needing dogbones, and it costs nothing: the two outer
    stretches sit inside the end-wall rabbets, which are cut to the same depth.
    """
    return (d.y_spine + d.t / 2, d.x_left, d.top_size[0])


def spine_screw_span(d: Datums = DATUMS) -> tuple[float, float]:
    """Where the spine's tie screws may land: the clear span between the end
    walls, which is spine material under either reading of the wall/spine
    corner."""
    return (d.wall_x[0] + d.t, d.wall_x[3])


# ---------------------------------------------------------------- machine relief
#
# The cap runs flush to all four leg faces, and every gusset hangs in exactly
# the space that flush footprint wants at its own corner. ``check_machine``
# finds the clash; this cuts it away, over the SAME solid, so the notch and
# the check that verifies it cannot drift apart.


def _gusset_relief(d: Datums = DATUMS) -> Part | None:
    """The gusset plates the cap's own nominal (unrelieved) footprint would
    otherwise clash with, cut out of it, following each one's taper rather
    than a square notch to full depth -- the relief IS the gusset's own
    trapezoidal solid. ``top_plane`` has no offset from station X/Y, so a
    station-coordinate gusset needs no adjustment beyond ``to_local``."""
    w, h = d.top_size
    cutters = None
    for g in gussets_over((0.0, w), (0.0, h), d.s.gussets):
        c = to_local(d.top_plane, gusset_prism(g))
        cutters = c if cutters is None else cutters + c
    return cutters


# ---------------------------------------------------------------- build


def build(d: Datums = DATUMS) -> Part:
    """The top cap, flat in panel-local coordinates. Stand it up with
    ``d.top_plane * build()``."""
    w, h = d.top_size
    t = d.t
    p = panel(w, h, t)

    # -- housings + ties for the four bay walls -----------------------------
    for hs in wall_housings(d):
        # run the cutter off the blank at every open end so the housing breaks
        # out cleanly instead of leaving a cutter-radius nib
        p -= groove(
            (hs.mid_x, hs.y0 - t),
            (hs.mid_x, hs.y1 if hs.blind else hs.y1 + t),
            width=hs.width,
            thickness=t,
            side="back",
        )
        # a blind end is an inside corner a round cutter cannot reach; without
        # these the divider is ROUTER_R too long to seat
        if hs.blind:
            for xe in (hs.x0, hs.x1):
                p -= relief(xe, hs.y1, thickness=t, depth=DADO_D, side="back")
        p -= screw_line(
            (hs.screw_x, hs.y0), (hs.screw_x, hs.y1), thickness=t, cbore_d=SCREW_CBORE
        )

    # -- housing + tie for the spine ----------------------------------------
    yc, x0, x1 = spine_housing(d)
    p -= groove((x0 - t, yc), (x1 + t, yc), thickness=t, side="back")
    sx0, sx1 = spine_screw_span(d)
    p -= screw_line((sx0, yc), (sx1, yc), thickness=t, cbore_d=SCREW_CBORE)

    # -- the chimney exhaust ------------------------------------------------
    v = vent_field(d)
    y_mid = (v.y0 + v.y1) / 2
    for xc in v.x_centres:
        p -= through_slot(
            (xc, y_mid),
            v.slot_len,
            VENT_SLOT_W,
            thickness=t,
            angle=90.0,
            corner_r=VENT_SLOT_W / 2,   # aperture: capsule, same as the louvre
        )

    # -- the mast base pads -------------------------------------------------
    for pad in mast_pads(d):
        for bx, by in pad.bolts:
            p -= bore(bx, by, MAST_BOLT_CLEAR_D, thickness=t)

    # -- the machine's own steel ---------------------------------------------
    relief_cut = _gusset_relief(d)
    if relief_cut is not None:
        p -= relief_cut

    return p


# ---------------------------------------------------------------- checks


def check_top_cap(d: Datums = DATUMS) -> list[str]:
    """What this part has to be true, as opposed to what the carcass has to be
    true. Run it after any parameter edit."""
    notes: list[str] = []
    w, h = d.top_size
    t = d.t

    ceiling = clear_over_relieved((0.0, w), (0.0, h), d.s)
    reveal = ceiling - d.top_z[1]
    if reveal < TOP_GAP_MIN:
        notes.append(
            f"reveal is {reveal:.0f}mm against a {TOP_GAP_MIN:.0f}mm minimum, "
            f"over the cap's own (relieved) footprint at a {ceiling:.0f}mm "
            "ceiling. The cap is touching the machine frame, which is the one "
            "thing it must not do."
        )

    v = vent_field(d)
    if v.count < VENT_MIN_SLOTS:
        notes.append(
            f"chimney exhaust is down to {v.count} slots, under the "
            f"{VENT_MIN_SLOTS} this part treats as a working aperture. The VFD "
            "corridor has been squeezed and the brain band is closer to a sealed "
            "box than a chimney."
        )
    if v.slot_len <= 0:
        notes.append(
            f"brain band is {d.brain_d:.0f}mm deep and the exhaust rails eat "
            f"{VENT_RAIL_FRONT + VENT_RAIL_REAR:.0f}mm of it. No slot left."
        )
    else:
        band = (d.brain_exhaust_x[1] - d.brain_exhaust_x[0]) * d.brain_d
        frac = v.open_area / band
        if frac < VENT_MIN_OPEN_FRAC:
            notes.append(
                f"exhaust is {frac * 100:.0f}% open over the sealed band, under "
                f"the {VENT_MIN_OPEN_FRAC * 100:.0f}% this model assumes a passive "
                "chimney needs. The assumption is unsourced; argue with it before "
                "cutting a bigger hole."
            )

    if VENT_SLOT_W < ROUTER_D:
        notes.append(
            f"louvre slot is {VENT_SLOT_W:.1f}mm and the carcass cutter is "
            f"{ROUTER_D:.2f}mm. The field needs a smaller tool."
        )

    for pad in mast_pads(d):
        edge = min(
            min(pad.xs), w - max(pad.xs), min(pad.ys), h - max(pad.ys)
        ) - MAST_BOLT_CLEAR_D / 2
        if edge < MAST_BOLT_CLEAR_D:
            notes.append(
                f"{pad.side} mast pad leaves {edge:.0f}mm of birch between bolt "
                f"and blank edge, under one bolt diameter. The pad has to move "
                "inboard or the bolt has to get smaller."
            )
        cantilever = max(pad.ys) - (d.y_spine + t)
        if cantilever > MAST_CANTILEVER_MAX:
            notes.append(
                f"{pad.side} mast pad's rear bolt sits {cantilever:.0f}mm behind "
                f"the spine, past the {MAST_CANTILEVER_MAX:.0f}mm this part will "
                "carry on an 18mm cantilever. The rear of the band is a door and "
                "supports nothing."
            )
        if max(pad.ys) > h - MAST_PAD_MARGIN:
            notes.append(f"{pad.side} mast pad runs off the rear edge of the blank")

    for hs in wall_housings(d):
        if hs.x0 < d.x_left - 1e-9 or hs.x1 > w + 1e-9:
            notes.append(
                f"a wall housing spans x {hs.x0:.1f}..{hs.x1:.1f} on a "
                f"{w:.0f}mm blank"
            )
        if hs.y1 > h + 1e-9:
            notes.append("a wall housing runs off the rear of the blank")
        if abs(hs.width - DADO_W) > 1e-9:
            notes.append(
                f"a wall housing is {hs.width:.1f}mm wide, not the {DADO_W:.1f}mm "
                "the wall's tongue is cut to"
            )

    yc, sx0, sx1 = spine_housing(d)
    if sx0 > d.x_left + 1e-9 or sx1 < w - 1e-9:
        notes.append(
            "the spine housing no longer runs the full blank width, so the "
            "spine's full-width blank has nowhere to seat at its ends"
        )
    if yc + DADO_W / 2 > h:
        notes.append("the spine housing runs off the rear of the blank")

    end_walls = [hs for hs in wall_housings(d) if hs.is_end]
    if len(end_walls) != 2:
        notes.append(
            f"{len(end_walls)} of the four walls are flush with a blank edge, "
            "not 2. The end-wall rabbets and the divider dados have got confused."
        )

    if v.count and min(v.x_centres) - VENT_SLOT_W / 2 < d.brain_exhaust_x[0]:
        notes.append("louvre field starts outside the brain-band exhaust span")

    return notes


# ---------------------------------------------------------------- main

if __name__ == "__main__":
    d = DATUMS
    part = build(d)
    bb = part.bounding_box()
    v = vent_field(d)

    print(f"{NAME}: {d.top_size[0]:.0f} x {d.top_size[1]:.0f} x {d.t:.0f} blank")
    print(
        f"  bbox   {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}  "
        f"at ({bb.min.X:.1f}, {bb.min.Y:.1f}, {bb.min.Z:.1f})"
    )
    solid = d.top_size[0] * d.top_size[1] * d.t
    print(
        f"  volume {part.volume / 1000:.0f} cm3 of a {solid / 1000:.0f} cm3 blank "
        f"({100 * part.volume / solid:.1f}% left)"
    )

    placed = d.top_plane * part
    pb = placed.bounding_box()
    print(
        f"  stood up: z {pb.min.Z:.0f}..{pb.max.Z:.0f} "
        f"(top_z {d.top_z[0]:.0f}..{d.top_z[1]:.0f}), reveal {d.top_gap:.0f}mm"
    )

    for hs in wall_housings(d):
        kind = "rabbet" if hs.is_end else "dado  "
        print(
            f"  wall {kind}: x {hs.x0:6.1f}..{hs.x1:6.1f}  y {hs.y0:.0f}.."
            f"{hs.y1:.0f}  {'blind' if hs.blind else 'through'}"
        )
    yc, sx0, sx1 = spine_housing(d)
    print(
        f"  spine dado : y {yc - DADO_W / 2:6.1f}..{yc + DADO_W / 2:6.1f}  "
        f"x {sx0:.0f}..{sx1:.0f}  through, all {DADO_D:.1f} deep"
    )
    band = (d.brain_exhaust_x[1] - d.brain_exhaust_x[0]) * d.brain_d
    print(
        f"  exhaust:  {v.count} slots {VENT_SLOT_W:.0f} x {v.slot_len:.0f} at "
        f"{VENT_PITCH:.0f} pitch, x {v.x_centres[0] - VENT_SLOT_W / 2:.0f}.."
        f"{v.x_centres[-1] + VENT_SLOT_W / 2:.0f}, y {v.y0:.0f}..{v.y1:.0f}, "
        f"{v.open_area / 100:.0f} cm2 open ({100 * v.open_area / band:.0f}% of the "
        "corridor)"
    )
    for pad in mast_pads(d):
        print(
            f"  mast {pad.side:5s}: 4 x M{MAST_BOLT_D:.0f} at "
            f"x {pad.xs[0]:.0f}/{pad.xs[1]:.0f}, y {pad.ys[0]:.0f}/{pad.ys[1]:.0f}"
        )

    written = export_part(part, NAME)
    for w_ in written:
        print(f"  wrote {w_}  {w_.stat().st_size} bytes")

    found = check_top_cap(d)
    if found:
        print(f"\n{len(found)} top cap note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno top cap constraint violations")
