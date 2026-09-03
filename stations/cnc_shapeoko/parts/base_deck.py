"""Base deck and plinth: the datum part of the Shapeoko station carcass.

Build order 1 of 5. Nothing else in the carcass can be located until this exists,
because ``Datums.deck_top`` is the Z datum every vertical stands on.

WHAT THIS MODULE EMITS
======================

Four flat blanks, all 18mm Baltic birch, all drawn on the panel convention in
``carcass.py`` (lower-left corner at the local origin, +X width, +Y height, +Z
thickness, back face at Z=0):

    base_deck            1100 x 1150   the datum panel, one per station
    plinth_rail_front     1020 x 60    toe kick, front
    plinth_rail_rear      1020 x 60    toe kick, rear, carries the intake grille
    plinth_rail_y         1046 x 60    x4, identical: two perimeter, two internal

``build()`` returns the deck, because the deck is the part. The plinth builders
sit beside it and ``build_plinth()`` / ``build_assembly()`` stand the whole base
up in station coordinates so the stack-up can be measured rather than asserted.


WHAT THE DECK CARRIES
=====================

housings        four wall housings at ``Datums.wall_x`` and one full-width spine
                housing at ``Datums.y_spine``, all DADO_D deep into the TOP face,
                all merging into one continuous trench so no joint has a 0.1mm
                land in it. The two END wall housings are rabbets rather than
                dados: those walls sit flush with the deck edge, so their housing
                runs off the edge instead of leaving a fin outboard of itself.

plinth screws   one counterbored fastener line per plinth rail. The counterbore
                is deep enough that a screw head under a wall housing still
                finishes below the housing floor, which is the one place these
                two feature sets collide.

leveller bores  four bores through the deck at the plinth's inside corners. The
                leveller is a stud in a socket screwed to the deck's UNDERSIDE
                (hardware, not geometry, and it is in the brief's BOM); the bore
                is how a hex driver reaches its head from inside a bay instead of
                from the floor.

brain intake    the bottom of the VFD chimney. A slotted field through the deck
                inside ``Datums.vfd_keepout_x``, between the spine housing and
                the rear plinth rail. Air enters the room-side grille in the rear
                plinth rail, crosses the plinth cavity as a plenum, rises through
                this field into the brain band, and leaves through the top cap.
                The plinth is therefore not decorative: it is the intake plenum.

No reliefs are cut on the intake slots or the grille. A dogbone earns its place
where a mating part has to seat; a radiused corner on an air slot is just a
radiused corner.
"""

from __future__ import annotations

from build123d import Part, Plane

from lib.house import GRID
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    PLINTH_H,
    SCREW_CBORE_D,
    T,
    bore,
    export_part,
    groove,
    panel,
    relief,
    screw_line,
    screw_positions,
    through_slot,
)

__all__ = [
    "build",
    "build_deck",
    "build_plinth_rail_x",
    "build_plinth_rail_y",
    "build_plinth",
    "build_assembly",
    "check_base_deck",
]

D = DATUMS


# ---------------------------------------------------------------- parameters
# Everything specific to this part. Everything else comes from carcass.py,
# params.py or house.py. No dimension below is a literal.

PLINTH_SETBACK = GRID * 2
"""Toe kick, all four sides. Two grid modules rather than one, because a toe kick
is for a foot and one module is not.

It used to be justified by the leg-tie bracket, which bolted up into the void
under the deck overhang. That bracket is gone -- the carcass bolts straight to
the legs now, through the end walls, see ``parts/leg_joint.py`` -- and the value
is unchanged because the toe kick was always the other half of the reason. The
plinth also stays set back from the leg faces, which is why no leg bolt can land
in it: below ``deck_z[0]`` there is no birch at the leg face at all."""

OVERSHOOT = T
"""How far a cutter runs past a blank edge, so an edge-breaking feature makes a
clean boolean instead of a coincident-face sliver."""

DECK_SCREW_CBORE_DEPTH = DADO_D + T / 4
"""Plinth fastener counterbore. Two of the six fastener lines run straight down
the middle of a wall housing, so the head has to finish below the housing floor
(DADO_D down) or the wall will not seat. A quarter of the panel below that gives
the head its seat with a margin, and still leaves most of the panel intact."""

RAIL_SCREW_INSET = PLINTH_H / 4
RAIL_SCREW_PITCH = PLINTH_H / 2
"""Fastener spacing for the rail-to-rail joints. The carcass-wide SCREW_PITCH is
144mm, which puts two screws 6mm apart on a 60mm edge; a joint this short sets
its own pattern off the plinth height and gets two screws 30mm apart."""

RAIL_SCREW_CBORE_DEPTH = T / 4
"""Rail fasteners are driven from the outside of the plinth and their heads stay
visible. Counterbored flush, not plugged: the plinth is structure and it says so."""

LEVELLER_CLEAR = GRID
"""Gap from a leveller bore to the inside face of either rail at its corner."""

LEVELLER_BORE_D = SCREW_CBORE_D
"""Access bore for the leveller driver. Same cutter as the screw counterbore, so
the deck needs one more tool for this feature and not two."""

INTAKE_MARGIN = GRID
INTAKE_SLOT_W = GRID / 2
INTAKE_PITCH = GRID
"""Intake grille: half-open at the bench grid pitch, in the deck and in the rear
plinth rail alike, so the two read as one aperture seen from two sides."""

EPS = DADO_W / 100
"""Tolerance for deciding whether a corner falls inside the blank or on its edge."""


# ---------------------------------------------------------------- derived
# The base's own geometry, all of it a function of the datums above.

DECK_W, DECK_H = D.deck_size

PLINTH_X = (PLINTH_SETBACK, DECK_W - PLINTH_SETBACK)
PLINTH_Y = (PLINTH_SETBACK, DECK_H - PLINTH_SETBACK)

X_RAIL_LEN = PLINTH_X[1] - PLINTH_X[0]
X_RAIL_CY = (PLINTH_Y[0] + T / 2, PLINTH_Y[1] - T / 2)

Y_RAIL_CX = (
    PLINTH_X[0] + T / 2,
    D.wall_x[1] + T / 2,
    D.wall_x[2] + T / 2,
    PLINTH_X[1] - T / 2,
)
"""Cross rails run under the two internal bay walls, so the load path from a
vertical goes straight to the floor, and under the two perimeter lines. The end
walls sit PLINTH_SETBACK outboard of the perimeter rails and cantilever it."""

Y_RAIL_SPAN = (PLINTH_Y[0] + T, PLINTH_Y[1] - T)
Y_RAIL_LEN = (Y_RAIL_SPAN[1] - Y_RAIL_SPAN[0]) + 2 * DADO_D
Y_RAIL_Y0 = Y_RAIL_SPAN[0] - DADO_D

LEVELLER_X = (
    PLINTH_X[0] + T + LEVELLER_CLEAR,
    PLINTH_X[1] - T - LEVELLER_CLEAR,
)
LEVELLER_Y = (
    PLINTH_Y[0] + T + LEVELLER_CLEAR,
    PLINTH_Y[1] - T - LEVELLER_CLEAR,
)
LEVELLER_XY = tuple((x, y) for y in LEVELLER_Y for x in LEVELLER_X)
"""Four feet, one in each inside corner of the plinth frame, clear of both rails
that meet there."""

SPINE_CY = D.y_spine + T / 2
SPINE_HOUSING_FRONT = SPINE_CY - DADO_W / 2
SPINE_HOUSING_REAR = SPINE_CY + DADO_W / 2

INTAKE_X = (
    Y_RAIL_CX[0] + T / 2 + INTAKE_MARGIN,
    D.vfd_keepout_x[1] - INTAKE_MARGIN,
)
INTAKE_Y = (
    SPINE_HOUSING_REAR + INTAKE_MARGIN,
    LEVELLER_Y[1] - INTAKE_MARGIN,
)
"""The intake field is bounded by what is under it: the left cross rail blocks
air to its left, the spine housing is the front land, and the rear leveller row
is the last thing before the rear rail."""


def _housing_cx(i: int) -> float:
    """Centreline of the housing for vertical panel ``i``.

    An internal wall gets a dado on its own centreline. An end wall sits flush
    with the deck edge, so its housing is pulled inboard by half a dado width and
    becomes a rabbet: the fit lands on the inside face and there is no 0.1mm fin
    of birch left outboard of the joint.
    """
    if i == 0:
        return DADO_W / 2
    if i == len(D.wall_x) - 1:
        return DECK_W - DADO_W / 2
    return D.wall_x[i] + T / 2


def _housing_rear(i: int) -> float:
    """Rear end of the housing for vertical panel ``i``, in deck coordinates.

    A divider stops at the spine centreline, where its housing merges with the
    spine's. An end wall is cut to the full depth of the station, so its housing
    runs off the rear edge of the blank.
    """
    if i in (0, len(D.wall_x) - 1):
        return DECK_H + OVERSHOOT
    return SPINE_CY


def deck_intake_area() -> float:
    """Free area of the slotted field through the deck, mm2."""
    return len(_slot_field(INTAKE_X)) * INTAKE_SLOT_W * (INTAKE_Y[1] - INTAKE_Y[0])


def rail_grille_area() -> float:
    """Free area of the room-side grille in the rear plinth rail, mm2.

    This is the throat of the whole chimney, and it is set by PLINTH_H rather
    than by anything to do with the VFD: a 60mm toe kick less two grid modules of
    land leaves a 20mm-tall slot. Nobody in this repo has a sourced airflow
    figure for a Carbide VFD, so the number is reported rather than judged. If
    the drive ever runs hot, the plinth is where to look first, and growing
    PLINTH_H is the cheapest move in the model.
    """
    return (
        len(_slot_field(_grille_x_local()))
        * INTAKE_SLOT_W
        * (PLINTH_H - 2 * INTAKE_MARGIN)
    )


def _slot_field(span: tuple[float, float]) -> list[float]:
    """Centres of a half-open slot field across ``span``, on the grid pitch and
    centred in whatever the span actually is."""
    width = span[1] - span[0]
    n = int(width // INTAKE_PITCH)
    if n < 1:
        return []
    covered = n * INTAKE_PITCH - (INTAKE_PITCH - INTAKE_SLOT_W)
    first = span[0] + (width - covered) / 2 + INTAKE_SLOT_W / 2
    return [first + k * INTAKE_PITCH for k in range(n)]


# ---------------------------------------------------------------- the deck


def build_deck() -> Part:
    """The datum panel, flat in panel-local coordinates.

    Local +X is station +X and local +Y is station +Y, so a station coordinate is
    a deck coordinate; ``Datums.deck_plane`` only lifts it to deck_z.
    """
    p = panel(DECK_W, DECK_H)

    # Housings for the four verticals. A divider runs from the open front edge
    # back into the spine housing so the two merge, rather than stopping 0.1mm
    # short of it and leaving a land nothing can seat over. An END wall runs the
    # whole depth of the deck and off the rear edge, because the end walls are
    # cut to the full leg_y_inner so the brain band gets side walls and the
    # spine's end faces have something to land on. Housing them only to the
    # spine leaves the last 250mm of an end wall's tongue sitting on solid deck.
    for i in range(len(D.wall_x)):
        cx = _housing_cx(i)
        p -= groove((cx, -OVERSHOOT), (cx, _housing_rear(i)), side="front")

    # Spine housing, edge to edge. Running it past both edges rather than only
    # over the spine's own 1064mm means it breaks out cleanly into the end-wall
    # housings instead of ending 0.2mm inside them.
    p -= groove(
        (-OVERSHOOT, SPINE_CY), (DECK_W + OVERSHOOT, SPINE_CY), side="front"
    )

    # Inside corners of that trench: where a DIVIDER housing's side wall meets
    # the front wall of the spine housing. Blind, to the housing floor. The end
    # walls have no such corner: their housings run straight through.
    for i in range(1, len(D.wall_x) - 1):
        cx = _housing_cx(i)
        for side_x in (cx - DADO_W / 2, cx + DADO_W / 2):
            if EPS < side_x < DECK_W - EPS:
                p -= relief(
                    side_x, SPINE_HOUSING_FRONT, depth=DADO_D, side="front"
                )

    # The GROWTH lungs/stock divider station. Since the 2026-09-03 ruling withdrew
    # the CT 36 EI, this coincides EXACTLY with the fitted station, so the two
    # subtracts are one dado and the panel is unchanged. Kept rather than deleted
    # so a future growth unit is one params line again. Historically: converting
    # to the growth extractor moves one panel into a slot that already exists
    # instead of recutting the deck, which is the largest panel in the station.
    # It takes a removable birch spline meanwhile so the stock bay floor stays
    # flat and does not collect chips.
    gcx = D.wall_x_growth[1] + T / 2
    p -= groove((gcx, -OVERSHOOT), (gcx, _housing_rear(1)), side="front")
    for side_x in (gcx - DADO_W / 2, gcx + DADO_W / 2):
        if EPS < side_x < DECK_W - EPS:
            p -= relief(side_x, SPINE_HOUSING_FRONT, depth=DADO_D, side="front")

    # Deck down onto the plinth. Heads counterbored below the housing floor.
    for cy in X_RAIL_CY:
        p -= screw_line(
            (PLINTH_X[0], cy),
            (PLINTH_X[1], cy),
            cbore_d=SCREW_CBORE_D,
            cbore_depth=DECK_SCREW_CBORE_DEPTH,
        )
    for cx in Y_RAIL_CX:
        p -= screw_line(
            (cx, Y_RAIL_SPAN[0]),
            (cx, Y_RAIL_SPAN[1]),
            cbore_d=SCREW_CBORE_D,
            cbore_depth=DECK_SCREW_CBORE_DEPTH,
        )

    # Leveller driver access, one per foot.
    for x, y in LEVELLER_XY:
        p -= bore(x, y, LEVELLER_BORE_D)

    # The low air intake: bottom of the VFD chimney.
    for cx in _slot_field(INTAKE_X):
        p -= through_slot(
            (cx, (INTAKE_Y[0] + INTAKE_Y[1]) / 2),
            INTAKE_Y[1] - INTAKE_Y[0],
            INTAKE_SLOT_W,
            corner_r=INTAKE_SLOT_W / 2,   # aperture: capsule, nothing seats here
            angle=90.0,
        )

    return p


def build() -> Part:
    """The part this module is named for."""
    return build_deck()


# ---------------------------------------------------------------- the plinth


def build_plinth_rail_x(*, grille: bool = False) -> Part:
    """A front-to-back-facing plinth rail, flat.

    Local Z=0 is the INNER face, the one that carries the cross-rail housings.
    Local +X runs along the rail from the end nearest the station origin, which
    for the rear rail means the blank reads right to left; its placement plane
    carries that flip so both rails are drawn the same way up.

    ``grille`` cuts the room-side air inlet, which only the rear rail has.
    """
    r = panel(X_RAIL_LEN, PLINTH_H)

    # The rear rail's local +X is station -X, so its housings mirror. Only the
    # rear rail carries the grille, so ``grille`` is also the flag for "this is
    # the rear blank"; _grille_x_local() already mirrors on the same reading.
    for lx in _rail_x_local(mirror=grille):
        # Housing for a cross rail, edge to edge in height, so it breaks out top
        # and bottom and has no inside corner to relieve.
        r -= groove(
            (lx, -OVERSHOOT),
            (lx, PLINTH_H + OVERSHOOT),
            depth=DADO_D,
            side="back",
        )
        # Two screws into the cross rail's end, driven from outside the plinth.
        r -= screw_line(
            (lx, 0.0),
            (lx, PLINTH_H),
            cbore_d=SCREW_CBORE_D,
            cbore_depth=RAIL_SCREW_CBORE_DEPTH,
            pitch=RAIL_SCREW_PITCH,
            inset=RAIL_SCREW_INSET,
        )

    if grille:
        band = (INTAKE_MARGIN, PLINTH_H - INTAKE_MARGIN)
        for cx in _slot_field(_grille_x_local()):
            r -= through_slot(
                (cx, (band[0] + band[1]) / 2),
                band[1] - band[0],
                INTAKE_SLOT_W,
                corner_r=INTAKE_SLOT_W / 2,   # aperture: capsule
                angle=90.0,
            )

    return r


def _rail_x_local(mirror: bool = False) -> list[float]:
    """Cross-rail centrelines in an X rail's local coordinates.

    Each X rail is drawn from its own local origin outward, and the rear rail's
    local +X runs station -X, so it measures from the other end of the plinth.
    The two blanks are NOT the same drawing: the cross rails sit under the two
    internal bay walls, which are not symmetric about the plinth's centreline
    unless lungs and hands happen to be the same width. Measuring both from
    PLINTH_X[0] mirrors the two internal housings to the wrong places and only
    looks right on the two perimeter rails.
    """
    origin = PLINTH_X[1] if mirror else PLINTH_X[0]
    return [abs(cx - origin) for cx in Y_RAIL_CX]


def _grille_x_local() -> tuple[float, float]:
    """The intake corridor in the rear rail's local coordinates. Mirrored,
    because that rail's local +X runs station -X."""
    return (PLINTH_X[1] - INTAKE_X[1], PLINTH_X[1] - INTAKE_X[0])


def build_plinth_rail_y() -> Part:
    """A cross rail, flat. All four are the same blank.

    It carries no features: it is located by the housings in the two X rails and
    fastened through them, and it is DADO_D longer at each end than its clear
    span so its ends bottom out in those housings.
    """
    return panel(Y_RAIL_LEN, PLINTH_H)


def _plane_rail_x_front() -> Plane:
    """Local +X to station +X, local +Y up, thickness into -Y, so local Z=0 lands
    on the rail's inner face."""
    return Plane(
        origin=(PLINTH_X[0], PLINTH_Y[0] + T, 0.0),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


def _plane_rail_x_rear() -> Plane:
    """The mirror of the front rail: local +X to station -X, thickness into +Y."""
    return Plane(
        origin=(PLINTH_X[1], PLINTH_Y[1] - T, 0.0),
        x_dir=(-1, 0, 0),
        z_dir=(0, 1, 0),
    )


def _plane_rail_y(j: int) -> Plane:
    """Cross rail ``j``: local +X to station +Y, local +Y up, thickness into +X."""
    return Plane(
        origin=(Y_RAIL_CX[j] - T / 2, Y_RAIL_Y0, 0.0),
        x_dir=(0, 1, 0),
        z_dir=(1, 0, 0),
    )


def build_plinth() -> Part:
    """The whole rail frame, standing in station coordinates."""
    out = _plane_rail_x_front() * build_plinth_rail_x()
    out += _plane_rail_x_rear() * build_plinth_rail_x(grille=True)
    rail = build_plinth_rail_y()
    for j in range(len(Y_RAIL_CX)):
        out += _plane_rail_y(j) * rail
    return out


def build_assembly() -> Part:
    """Deck on plinth, in station coordinates. Floor to deck_top."""
    return build_plinth() + D.deck_plane * build_deck()


# ---------------------------------------------------------------- checks


def check_base_deck() -> list[str]:
    """The collisions this part has to keep clear as leg_x_inner moves.

    Everything here is a derived-against-derived comparison, so it fires when a
    parameter change walks two features into each other rather than when a number
    looks wrong.
    """
    notes: list[str] = []

    # The screw head under a wall housing.
    if DECK_SCREW_CBORE_DEPTH <= DADO_D:
        notes.append(
            "plinth screw counterbore does not finish below the housing floor, "
            "so a wall lands on a screw head instead of on the deck"
        )

    # Intake against everything under it.
    if INTAKE_X[1] <= INTAKE_X[0] or INTAKE_Y[1] <= INTAKE_Y[0]:
        notes.append(
            f"brain intake has closed up: x {INTAKE_X[0]:.0f}..{INTAKE_X[1]:.0f}, "
            f"y {INTAKE_Y[0]:.0f}..{INTAKE_Y[1]:.0f}. The VFD chimney has lost "
            "its bottom and the brain band is a sealed box again."
        )
    elif deck_intake_area() < rail_grille_area():
        notes.append(
            f"the deck field is {deck_intake_area() / 100:.0f}cm2 open against a "
            f"{rail_grille_area() / 100:.0f}cm2 rail grille, so the DECK has "
            "become the restriction in the chimney. The throat belongs at the "
            "rail, where it is a serviceable filter face; the deck is buried "
            "under the brain band and nobody will ever clean it."
        )
    for cx in Y_RAIL_CX:
        if INTAKE_X[0] - INTAKE_MARGIN < cx < INTAKE_X[1] + INTAKE_MARGIN:
            notes.append(
                f"cross rail at x={cx:.0f} runs under the brain intake and blocks "
                "it. Move the intake or the rail."
            )

    # Leveller bores against the rails they sit between.
    for x, y in LEVELLER_XY:
        for cx in Y_RAIL_CX:
            if abs(x - cx) < (T + LEVELLER_BORE_D) / 2:
                notes.append(
                    f"leveller bore at x={x:.0f} lands on the cross rail at "
                    f"x={cx:.0f}. The bore has to open into the plinth cavity, "
                    "not into 60mm of edge-on birch."
                )

    # Cross rails have to stay in order and apart as leg_x_inner moves.
    for a, b in zip(Y_RAIL_CX, Y_RAIL_CX[1:]):
        if b - a < T + DADO_W:
            notes.append(
                f"plinth cross rails at x={a:.0f} and x={b:.0f} are "
                f"{b - a:.0f}mm apart, closer than two rails and a housing. "
                "At this leg_x_inner the plinth wants one fewer rail."
            )

    if PLINTH_SETBACK <= T:
        notes.append(
            f"toe kick is {PLINTH_SETBACK:.0f}mm against a {T:.0f}mm panel, so "
            "the deck no longer overhangs its own plinth rails and there is no "
            "kick left to stand at"
        )

    return notes


if __name__ == "__main__":
    deck = build_deck()
    rail_front = build_plinth_rail_x()
    rail_rear = build_plinth_rail_x(grille=True)
    rail_y = build_plinth_rail_y()
    base = build_assembly()

    def line(label: str, part: Part) -> None:
        b = part.bounding_box()
        print(
            f"  {label:<20} {b.size.X:8.1f} x {b.size.Y:8.1f} x {b.size.Z:6.1f}"
            f"   {part.volume / 1000:9.1f} cm3"
        )

    print("BASE DECK AND PLINTH, flat blanks (panel-local):")
    line("base_deck", deck)
    line("plinth_rail_front", rail_front)
    line("plinth_rail_rear", rail_rear)
    line("plinth_rail_y", rail_y)

    print("\nassembled, station coordinates:")
    bb = base.bounding_box()
    print(
        f"  x {bb.min.X:7.1f} .. {bb.max.X:7.1f}    "
        f"y {bb.min.Y:7.1f} .. {bb.max.Y:7.1f}    "
        f"z {bb.min.Z:7.1f} .. {bb.max.Z:7.1f}"
    )
    print(f"  deck top at {D.deck_top:.1f}, the Z datum for everything above")

    print("\nderived:")
    print(
        f"  wall housings at "
        f"{[f'{_housing_cx(i):.1f}' for i in range(len(D.wall_x))]}, "
        f"spine housing at {SPINE_CY:.1f}"
    )
    print(
        f"  plinth {PLINTH_X[0]:.0f}..{PLINTH_X[1]:.0f} x "
        f"{PLINTH_Y[0]:.0f}..{PLINTH_Y[1]:.0f}, set back {PLINTH_SETBACK:.0f}, "
        f"cross rails at {[f'{x:.0f}' for x in Y_RAIL_CX]}"
    )
    print(f"  levellers at {[f'({x:.0f},{y:.0f})' for x, y in LEVELLER_XY]}")
    print(
        f"  intake x {INTAKE_X[0]:.0f}..{INTAKE_X[1]:.0f}  "
        f"y {INTAKE_Y[0]:.0f}..{INTAKE_Y[1]:.0f}  "
        f"{len(_slot_field(INTAKE_X))} slots, "
        f"{deck_intake_area() / 100:.0f}cm2 through the deck"
    )
    print(
        f"  chimney throat is the rail grille: "
        f"{len(_slot_field(_grille_x_local()))} slots, "
        f"{rail_grille_area() / 100:.0f}cm2, set by PLINTH_H={PLINTH_H:.0f}"
    )
    print(
        f"  deck screws per X rail: {len(screw_positions(X_RAIL_LEN))}, "
        f"per cross rail: {len(screw_positions(Y_RAIL_SPAN[1] - Y_RAIL_SPAN[0]))}"
    )

    written = []
    written += export_part(deck, "base_deck")
    written += export_part(rail_front, "plinth_rail_front")
    written += export_part(rail_rear, "plinth_rail_rear")
    written += export_part(rail_y, "plinth_rail_y")
    print("\nwrote:")
    for path in written:
        print(f"  {path}  {path.stat().st_size:>9,} bytes")

    found = check_base_deck()
    if found:
        print(f"\n{len(found)} base note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno base constraint violations")
