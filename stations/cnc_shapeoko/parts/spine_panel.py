"""Spine panel: the full-width divider between the front bays and the brain band.

Build order 2 of 5. The deck makes the station a board; the spine makes it an L.

WHAT THIS PART IS
=================

One 18mm Baltic birch panel standing on the deck at ``y_spine``, spanning the
whole opening between the two end walls and running the full bay height. It does
three jobs, in this order of importance:

1. It braces the carcass in X-Z. The deck alone is a board that folds; the deck
   plus this panel is an L that does not. Every part after this one registers off
   that L, which is why the spine is cut second and why being out of square here
   is unrecoverable later.
2. It divides sealed power from exposed signal. It carries the housing for the
   brain-band partition and it is the panel every front-to-back run passes
   through, so the boundary between "mains behind a driver" and "signal behind
   smoked acrylic" is a physical thing rather than a wiring habit.
3. It houses the two internal dividers. Their rear edges land in grooves in its
   front face and are screwed through it from the service side.

THE JOINTS, AND WHO OWNS WHICH HALF
===================================

``Datums`` sizes every panel to its CLEAR SPAN between datum FACES.  A blank is
that clear span plus ``HOUSE_ENGAGE`` at each edge that is HOUSED, and nothing
extra at an edge that merely butts, so no datum moves when the joinery does.
For the spine:

    width         ``spine_size[0]`` exactly, the clear span between the end
                  walls' inner faces.  No addition: the ends butt.
    height        ``spine_size[1] + 2 * HOUSE_ENGAGE``
    bottom edge   tongue into the deck's housing        (deck cuts the dado)
    top edge      tongue into the top cap's housing     (top cap cuts it)
    left  end     butts the LEFT end wall's inner face
    right end     butts the RIGHT end wall's inner face
    front face    houses the two internal dividers      (cut here)
    rear face     houses the brain-band sealed/signal partition   (cut here)

The end walls run the full depth to ``y_rear`` rather than stopping at the
spine, because the brain band needs side walls and the rear panel needs
something to land on.  That makes the spine-to-end-wall joint a butt onto a
continuous face rather than a corner, so the fasteners live in the WALL: a
vertical row of clearance holes on the spine's centreline, driven into the
spine's end grain.  Nothing is cut here for it, which is why this panel is
exactly ``spine_size`` wide.

INTERFACE, one line each, for the parts cut alongside this one:

    base_deck   dado at y_spine, DADO_W wide, HOUSE_ENGAGE deep, spanning at
                least the clear span x_left+t .. x_right-t
    bay_walls   end walls run to y_rear and carry the spine's tie screws;
                dividers are front_bay_d + HOUSE_ENGAGE deep and their rear
                tongue seats in the grooves this file cuts
    top_cap     dado at y_spine mirroring the deck's, plus the tie screws down
                into this panel's top edge

THE VENT CORRIDOR IS A KEEP-OUT
===============================

``Datums.vfd_keepout_x`` is the VFD's air path and nothing may sit in it.  That
is not just a mounting rule: a pass-through in the corridor is a hole that bleeds
the chimney into a front bay, which is worse than an obstruction because it is
invisible.  Every crossing in this file is placed right of the corridor and
``check_spine`` fires if one ever is not.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Location, Part

from lib.house import GRID
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    GLAND_M20_D,
    GX16_PANEL_D,
    HOUSE_ENGAGE,
    SCREW_CLEAR_D,
    SCREW_EDGE_OFF,
    T,
    DATUMS,
    Datums,
    bore,
    export_part,
    groove,
    panel,
    relief,
    screw_line,
)

PART_NAME = "spine_panel"


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# Shared boundaries come from Datums, joinery from carcass.py, material
# from house.py. No number below is free: each one is a multiple of the
# bench grid or of the material thickness, so 18mm -> 15mm regenerates it.
# ====================================================================

# -- the brain-band sealed/signal partition ---------------------------
PARTITION_HOUSE_D = DADO_D / 2
"""Depth of the partition's housing in the REAR face.

Shallower than a structural dado on purpose. The partition is a barrier, not a
brace, and the wall-2 housing is already 6mm into the opposite face nearby; a
third of the thickness from each side would leave a third down a 649mm line.
T/3 front and T/6 back leaves T/2."""

SPLIT_TRANSIT_H = GRID * 2
"""Height of the ONE interruption in the partition housing.

Every low-voltage lead that has to cross from sealed to signal -- the current
transformer on the spindle leg -- passes here and nowhere else. One gap, labelled, above the WAGO rails and below the top: a
split with a single legible exception is a split a student can read. A split
with leads wandering through it in three places is decoration."""

SPLIT_TRANSIT_Z = GRID * 24
"""Height of the transit above deck_top. High in the band, clear of the
distribution rails, low enough to stay under the top cap's exhaust."""

# -- the crossings ----------------------------------------------------
ROW_LOW_Z = GRID * 4
"""Height above deck_top of the mains / pre-terminated-cable row. Low, because
that is where an extractor's inlet and a pendant's cable want to be, and because
separating mains from signal by height makes the segregation visible."""

ROW_HIGH_Z = GRID * 28
"""Height above deck_top of the connector row. High, so console runs leave over
the top of a drawer stack rather than through it."""

BORE_EDGE_MIN = SCREW_EDGE_OFF
"""Material between a bore and a window edge that is only a LINE: the end of the
VFD's air corridor. Half the thickness, the same rule the fasteners use, because
here the only thing at stake is the panel not tearing out."""

BORE_CLEAR_MIN = T
"""Material between a bore and a window edge that is a PANEL FACE.

A bulkhead is not a hole, it is a hole plus a nut plus the wrench that tightens
it. A GX16 nut is wider than its shell and a gland nut is wider still, so a
connector nine millimetres off a perpendicular panel is a connector that cannot
be assembled. One thickness is the clearance that makes the difference between a
drawing that checks out and a station that goes together."""


@dataclass(frozen=True)
class Crossing:
    """One front-to-back run through the spine.

    The run list drives the geometry, the way a tool list drives a fitted tray.
    Adding a run adds a hole and re-spaces its neighbours; nobody draws a hole.
    """

    label: str      # engraved callout, and the name on the wiring schedule
    bay: str        # which front bay it emerges into: lungs | stock | hands
    zone: str       # which side of the split it leaves from: sealed | signal
    kind: str       # gx16 (a run that terminates) | gland (a cable that passes)
    row: str        # low | high


CROSSINGS: tuple[Crossing, ...] = (
    # Sealed side. Mains to the extractor, and the one low-voltage feed that
    # has to reach a bay sitting behind the sealed zone.
    Crossing("EXTRACTOR MAINS", "lungs", "sealed", "gland", "low"),
    # STRUCK 2026-09-09 (subtract pass, items 03/04/08/14): the MAST FEED
    # gland (mast strip struck, mast camera parked to 2026-11-02) and the
    # STOCK WASH GX16 (the wash struck with its ToF driver). The cap's feed
    # slot stays cut for the camera's return; its crossing is re-added then.
    # Signal side. Everything the operator touches, at the operator's corner.
    Crossing("CONSOLE STOP", "hands", "signal", "gx16", "high"),
    Crossing("CONSOLE CONTROL", "hands", "signal", "gx16", "high"),
    Crossing("CONSOLE INSTRUMENT", "hands", "signal", "gx16", "high"),
    Crossing("PENDANT AND USB", "hands", "signal", "gland", "low"),
)

BORE_D = {"gx16": GX16_PANEL_D, "gland": GLAND_M20_D}
ROW_Z = {"low": ROW_LOW_Z, "high": ROW_HIGH_Z}


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the
# block above and on Datums.
# ====================================================================


def blank_size(d: Datums = DATUMS) -> tuple[float, float]:
    """Cut size of the spine blank.

    Width is the clear span untouched, because both ends butt an end wall's
    inner face. Height is the clear span plus engagement at each end, because
    both the deck and the top cap house this panel.
    """
    w, h = d.spine_size
    return (w, h + 2 * HOUSE_ENGAGE)


def blank_offset(d: Datums = DATUMS) -> tuple[float, float]:
    """Where the blank's lower-left corner sits in ``spine_plane``'s local frame.

    The plane's origin is the panel's DATUM corner. In X that is the blank
    corner too; in Y the blank reaches below it by the housing engagement.
    """
    return (0.0, -HOUSE_ENGAGE)


def lx(station_x: float, d: Datums = DATUMS) -> float:
    """Station X to panel-local X."""
    return station_x - d.t - blank_offset(d)[0]


def ly(z_above_deck: float) -> float:
    """Height above deck_top to panel-local Y."""
    return z_above_deck + HOUSE_ENGAGE


def bay_window(c: Crossing, d: Datums = DATUMS) -> tuple[float, float]:
    """The X window a crossing has to live in, in station coordinates.

    The intersection of the bay it feeds, the zone it leaves from, and the
    complement of the VFD's air corridor. A run emerges in the bay that uses it,
    which is why these cannot simply be spread across the panel.
    """
    a = max(_bay_x(c.bay, d)[0], _zone_x(c.zone, d)[0], d.vfd_keepout_x[1])
    b = min(_bay_x(c.bay, d)[1], _zone_x(c.zone, d)[1])
    return (a, b)


def window_margins(c: Crossing, d: Datums = DATUMS) -> tuple[float, float]:
    """Material required at each end of a crossing's window.

    A window edge that is a panel face needs assembly clearance for the nut. A
    window edge that is only the end of the air corridor needs nothing but
    material, because there is nothing there to foul.
    """
    lo, hi = bay_window(c, d)
    m_lo = BORE_EDGE_MIN if lo == d.vfd_keepout_x[1] else BORE_CLEAR_MIN
    m_hi = BORE_EDGE_MIN if hi == d.vfd_keepout_x[1] else BORE_CLEAR_MIN
    return (m_lo, m_hi)


def _bay_x(bay: str, d: Datums) -> tuple[float, float]:
    return {"lungs": d.lungs_x, "stock": d.stock_x, "hands": d.hands_x}[bay]


def _zone_x(zone: str, d: Datums) -> tuple[float, float]:
    return {"sealed": sealed_x(d), "signal": signal_x(d)}[zone]


def x_split(d: Datums = DATUMS) -> float:
    """Left face of the brain-band partition, in station X.

    It sits on the RIGHT face of the stock/hands divider, so one plane runs
    unbroken from the open front of the station to the rear panel. That is the
    stiffest place to put it and the easiest to read; it also keeps the
    partition's housing clear of the screw line that fastens the divider, which
    a partition coplanar with the divider would have sat directly on top of.
    """
    return d.brain_split_x


def sealed_x(d: Datums = DATUMS) -> tuple[float, float]:
    """X span of the sealed-power zone: right of the VFD's air corridor, left of
    the partition. The contactor, the fused inlet and the WAGO rails live here,
    because nothing may be mounted in the corridor itself."""
    return (d.vfd_keepout_x[1], x_split(d))


def signal_x(d: Datums = DATUMS) -> tuple[float, float]:
    """X span of the exposed-signal zone: right of the partition to the right
    end wall. Mini PC, motion controller, the station microcontroller's rail
    seat (PARKED to 2027-01-05) and the ethernet bulkhead, at the operator's
    corner."""
    return (x_split(d) + d.t, d.wall_x[3])


def centre_band(c: Crossing, d: Datums = DATUMS) -> tuple[float, float]:
    """The range a crossing's CENTRE may take, in station X.

    The window shrunk by the bore's own radius and by the margin each end
    demands. Spreading has to happen inside this rather than inside the raw
    window, because the two margins are not the same number and a midpoint would
    quietly break the tighter side.
    """
    lo, hi = bay_window(c, d)
    m_lo, m_hi = window_margins(c, d)
    r = BORE_D[c.kind] / 2
    return (lo + m_lo + r, hi - m_hi - r)


def _spread(n: int, lo: float, hi: float) -> list[float]:
    """Centres for n features evenly spread across [lo, hi]. One goes in the
    middle; the ends of a longer row land on the limits."""
    if n == 1:
        return [(lo + hi) / 2]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def crossing_x(d: Datums = DATUMS) -> dict[str, float]:
    """STATION X of every crossing's bore centre, keyed by label.

    Crossings sharing a bay and a row share a window and get spread across the
    band all of them can live in. Station coordinates, because that is the frame
    the windows, the bays and the vent corridor are all stated in; the panel
    frame is a shift applied once, at the end, in ``crossing_positions``.
    """
    out: dict[str, float] = {}
    groups: dict[tuple[str, str], list[Crossing]] = {}
    for c in CROSSINGS:
        groups.setdefault((c.bay, c.row), []).append(c)

    for members in groups.values():
        bands = [centre_band(m, d) for m in members]
        lo = max(b[0] for b in bands)
        hi = min(b[1] for b in bands)
        for c, x in zip(members, _spread(len(members), lo, hi)):
            out[c.label] = x
    return out


def crossing_positions(d: Datums = DATUMS) -> dict[str, tuple[float, float]]:
    """Panel-local (x, y) for every crossing, keyed by label."""
    xs = crossing_x(d)
    return {c.label: (lx(xs[c.label], d), ly(ROW_Z[c.row])) for c in CROSSINGS}


def build(d: Datums = DATUMS) -> Part:
    """The spine panel, flat in panel-local coordinates.

    Z = 0 is the REAR face, looking into the brain band. Z = t is the FRONT
    face, looking into the three bays. That falls out of ``Datums.spine_plane``,
    whose z_dir points forward.
    """
    w, h = blank_size(d)
    part = panel(w, h, d.t)

    # Both ends are butt joints onto the end walls' inner faces, so the blank's
    # width IS the joint and nothing is cut for it. The tie screws come through
    # the wall, from the wall's file.

    # -- housings for the two internal dividers, in the FRONT face -------
    # Through grooves, running clean off both ends of the blank: the divider
    # slides in from the top, and a through groove has no stopped corner to
    # relieve. The screws follow the same line, driven from the service side
    # into the divider's rear edge.
    for i in (1, 2):
        cx = lx(d.wall_x[i] + d.t / 2, d)
        part -= groove(
            (cx, 0.0),
            (cx, h),
            width=DADO_W,
            depth=DADO_D,
            thickness=d.t,
            side="front",
        )
        part -= screw_line(
            (cx, ly(0.0)),
            (cx, ly(d.bay_h)),
            thickness=d.t,
            d=SCREW_CLEAR_D,
        )

    # -- housing for the brain-band partition, in the REAR face ----------
    # Interrupted once, at the split transit. Blind reliefs at the four stopped
    # corners so the partition seats to the bottom of the groove either side of
    # the gap instead of riding on a cutter radius.
    px = lx(x_split(d) + d.t / 2, d)
    y_lo = ly(SPLIT_TRANSIT_Z) - SPLIT_TRANSIT_H / 2
    y_hi = ly(SPLIT_TRANSIT_Z) + SPLIT_TRANSIT_H / 2
    for a, b in ((0.0, y_lo), (y_hi, h)):
        part -= groove(
            (px, a),
            (px, b),
            width=DADO_W,
            depth=PARTITION_HOUSE_D,
            thickness=d.t,
            side="back",
        )
    for y in (y_lo, y_hi):
        for sign in (-1, 1):
            part -= relief(
                px + sign * DADO_W / 2,
                y,
                thickness=d.t,
                depth=PARTITION_HOUSE_D,
                side="back",
            )

    # -- the crossings ---------------------------------------------------
    for c in CROSSINGS:
        x, y = crossing_positions(d)[c.label]
        part -= bore(x, y, BORE_D[c.kind], thickness=d.t)

    return part


def place(part: Part | None = None, d: Datums = DATUMS) -> Part:
    """The flat panel stood up in station coordinates.

    ``spine_plane``'s origin is the panel's lower-left DATUM corner, so the
    blank -- which reaches past that corner by a wall thickness at the end and
    by the housing engagement at the bottom -- is offset back by exactly that
    much before the plane is applied.
    """
    part = build(d) if part is None else part
    dx, dy = blank_offset(d)
    return d.spine_plane * part.moved(Location((dx, dy, 0)))


# ---------------------------------------------------------------- checks


def check_spine(d: Datums = DATUMS) -> list[str]:
    """What this part has to be true for, beyond what carcass.py already checks."""
    notes: list[str] = []
    xs = crossing_x(d)

    for c in CROSSINGS:
        lo, hi = bay_window(c, d)
        band = centre_band(c, d)
        r = BORE_D[c.kind] / 2
        x = xs[c.label]
        if hi - lo <= 0:
            notes.append(
                f"{c.label}: no window left. Its bay ({c.bay}) and its zone "
                f"({c.zone}) no longer overlap clear of the vent corridor, so "
                "the run has nowhere to cross."
            )
            continue
        if band[1] < band[0]:
            m_lo, m_hi = window_margins(c, d)
            notes.append(
                f"{c.label}: a {BORE_D[c.kind]:.0f}mm bulkhead does not fit its "
                f"{hi - lo:.0f}mm window ({lo:.0f}..{hi:.0f}) with "
                f"{m_lo:.0f}/{m_hi:.0f}mm of margin. Either the run moves bay or "
                "the bulkhead gets smaller."
            )
            continue
        if x < band[0] - 1e-6 or x > band[1] + 1e-6:
            notes.append(
                f"{c.label}: bore centre x={x:.0f} is outside its usable band "
                f"{band[0]:.0f}..{band[1]:.0f}"
            )
        if x - r < d.vfd_keepout_x[1]:
            notes.append(
                f"{c.label} at x={x:.0f} reaches into the VFD air corridor "
                f"(ends at {d.vfd_keepout_x[1]:.0f}). A pass-through there "
                "bleeds the chimney into a front bay."
            )

    # bores must not land in a housing groove
    housings = [d.wall_x[i] + d.t / 2 for i in (1, 2)]
    housings.append(x_split(d) + d.t / 2)
    for c in CROSSINGS:
        x = xs[c.label]
        for hx in housings:
            if abs(x - hx) < (BORE_D[c.kind] + DADO_W) / 2:
                notes.append(
                    f"{c.label} at x={x:.0f} overlaps the housing at x={hx:.0f}"
                )

    # bores must not collide with each other
    for i, a in enumerate(CROSSINGS):
        for b in CROSSINGS[i + 1:]:
            if a.row != b.row:
                continue
            gap = abs(xs[a.label] - xs[b.label])
            need = (BORE_D[a.kind] + BORE_D[b.kind]) / 2 + BORE_EDGE_MIN
            if gap < need:
                notes.append(
                    f"{a.label} and {b.label} are {gap:.0f}mm apart on the "
                    f"{a.row} row and need {need:.0f}mm"
                )

    if PARTITION_HOUSE_D + DADO_D >= d.t:
        notes.append(
            f"the divider housing ({DADO_D:.1f}mm from the front) and the "
            f"partition housing ({PARTITION_HOUSE_D:.1f}mm from the back) leave "
            f"{d.t - DADO_D - PARTITION_HOUSE_D:.1f}mm of material where they "
            "cross. The spine stops being a brace at that line."
        )

    sealed = sealed_x(d)
    if sealed[1] - sealed[0] < d.s.vfd_box[0]:
        notes.append(
            f"sealed zone is {sealed[1] - sealed[0]:.0f}mm wide between the vent "
            f"corridor and the partition. The contactor, the fused inlet and the "
            "WAGO rails all have to mount there."
        )

    signal = signal_x(d)
    if signal[1] - signal[0] < d.s.mini_pc_env[0]:
        notes.append(
            f"signal zone is {signal[1] - signal[0]:.0f}mm wide and the mini PC "
            f"alone is {d.s.mini_pc_env[0]:.0f}mm"
        )

    if ROW_HIGH_Z >= d.bay_h or ROW_LOW_Z <= 0:
        notes.append(
            f"a crossing row is outside the {d.bay_h:.0f}mm bay height "
            f"(low {ROW_LOW_Z:.0f}, high {ROW_HIGH_Z:.0f})"
        )

    if SPLIT_TRANSIT_Z + SPLIT_TRANSIT_H / 2 >= d.bay_h:
        notes.append("the split transit runs off the top of the panel")

    if abs(blank_size(d)[0] - d.spine_size[0]) > 1e-6:
        notes.append(
            "the blank is no longer the clear span between the end walls, which "
            "is the one thing the wall file assumes when it drills the tie screws"
        )

    return notes


if __name__ == "__main__":
    d = DATUMS
    flat = build(d)
    bb = flat.bounding_box()
    placed = place(flat, d)
    pbb = placed.bounding_box()

    w, h = blank_size(d)
    print(f"{PART_NAME}: blank {w:.1f} x {h:.1f} x {d.t:.1f}")
    print(
        f"  flat bbox   {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}"
        f"   volume {flat.volume / 1000:.1f} cm3"
        f"  ({100 * flat.volume / (w * h * d.t):.1f}% of the blank)"
    )
    print(
        f"  placed      x {pbb.min.X:.1f}..{pbb.max.X:.1f}  "
        f"y {pbb.min.Y:.1f}..{pbb.max.Y:.1f}  z {pbb.min.Z:.1f}..{pbb.max.Z:.1f}"
    )
    print(
        f"  clear span  x {d.t:.0f}..{d.x_right - d.t:.0f}  "
        f"z {d.deck_top:.0f}..{d.top_z[0]:.0f}   "
        f"tongue {HOUSE_ENGAGE:.0f} into deck and top cap, "
        "ends butt the end walls"
    )
    print(
        f"  split at x={x_split(d):.0f}   "
        f"sealed {sealed_x(d)[0]:.0f}..{sealed_x(d)[1]:.0f}   "
        f"signal {signal_x(d)[0]:.0f}..{signal_x(d)[1]:.0f}   "
        f"corridor keep-out {d.vfd_keepout_x[0]:.0f}..{d.vfd_keepout_x[1]:.0f}"
    )
    pos = crossing_positions(d)
    xs = crossing_x(d)
    for c in CROSSINGS:
        x, y = pos[c.label]
        lo, hi = bay_window(c, d)
        print(
            f"    {c.label:<20} {c.kind:<5} {BORE_D[c.kind]:.0f}mm  "
            f"station x {xs[c.label]:7.1f}  panel ({x:7.1f}, {y:6.1f})   "
            f"{c.zone}/{c.bay} window {lo:.0f}..{hi:.0f}"
        )

    found = check_spine(d)
    if found:
        print(f"\n{len(found)} spine note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno spine constraint violations")

    for p in export_part(flat, PART_NAME):
        print(f"wrote {p}")
