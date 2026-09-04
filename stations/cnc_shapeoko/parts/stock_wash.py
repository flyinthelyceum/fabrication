"""Stock wash: one LED channel under the cap, ahead of the comb, fed from the
STOCK WASH crossing. Task C14.

WHAT IT IS
==========

The stock bay has no door. Nine HALF blanks stand on edge in the comb and the
operator reads them from across the room: ply count, void, veneer, which one
is the 12mm. The brief (v8, "Front centre: Stock") gives the bay a low-angle
LED wash across the edges so the material is legible at the moment of choice.
This module is that wash, as the carcass sees it:

  ``stock_wash_channel``   one aluminium LED channel of the standard 17 x 8
                           surface-mount class, its frosted diffuser facing
                           DOWN, its base on the cap's underside, running the
                           bay's clear width less one grid module at each
                           end. One reference solid carrying three BOM lines:
                           the channel, the 24V warm-white strip inside it,
                           the diffuser that closes it. No red: the strip is
                           non-addressable single-colour warm white, and red
                           on this station is the E-stop and the mast's FAULT
                           state and nothing else.
  ``stock_wash_plug``      the GX16 cable plug hanging off the STOCK WASH
                           bore on the bay side of the spine, as the envelope
                           the Handson drawing gives it. Reserves the room the
                           plug needs behind the blanks.
  ``stock_wash_lead``      the 2-core lead from the plug's tail to the
                           channel's fed end, as a 5mm solid along ``route``,
                           so the assembly's interference check compares the
                           run against the comb, the blanks, the divider and
                           the spine rather than trusting a sentence.

The strip is DRIVEN by firmware (C19, held): the ToF proximity state at the
console wakes the wash as a person approaches and dims it when the room
empties. That is a sensor informing a light. It votes on nothing; the wash
has no stopping authority and never will (``house.STOPPING_AUTHORITY``).

WHERE IT SITS, AND WHY NOT "UNDER THE RAIL"
===========================================

The task says "under the C02 top rail's front lip". Ruling 11 made the top
rail a COMB: its slots are open at the bottom and every blank's top edge
passes up through it to ``stock_rails.blank_top_z``, 15mm above the comb's
own bottom edge. Anything hung under the comb across the bay's width is in
the path of eight blanks. So "under the rail" can only mean the band the comb
leaves in front of itself: ``stock_rails.COMB_INSET`` (one grid module)
between the carcass's front plane and the comb's front face, under the cap,
above the blank tops. That band is 20 deep and 25 tall and the channel is
17 x 8, base up against the cap. The channel is centred in the band's depth
so it clears the front plane and the STOCK header's face by the same margin,
and it takes 8 of the 25mm over the blank tops, leaving a blank
``blank_clear`` to slide out under it.

ANGLED TO RAKE, AS GEOMETRY RATHER THAN TILT
============================================

Raking light is light that arrives nearly parallel to a surface, so the
surface's relief casts the shadows that make it readable. The edge faces
here are vertical planes; a source above them and a few millimetres AHEAD
of them rakes them by position alone. A blank standing with its front edge
on the STOCK header's face (y = comb front) has the diffuser 1.5..18.5mm
ahead of it and 17mm above its top, so light reaches the top of the edge
at ``rake_angles()[0]`` off the face and the bottom at ``rake_angles()[1]``:
low-angle, from the top down, the whole height. TILTING the channel adds
nothing to that (aiming the peak at mid-height of a 600 edge from 17mm above
it is a two-degree tilt) and the band cannot hold a tilted channel anyway:
``tilt_room()`` says how much of the 20mm a 10 degree set would need. So
the channel is flat, the diffuser faces straight down, and the angle the
task asks for is the geometry, reported by the check instead of chosen as a
parameter.

The consequence, worth reading before the first blank goes in: the wash
rakes a blank's FRONT edge only when that edge stands behind the diffuser.
A blank pushed flush with the carcass front stands UNDER the channel and gets
its top edge lit and its front edge in shadow. The index is the STOCK
header's face: push a blank in until its front edge is flush with the
header. The deck cuts no stop for that today (a 600 blank so indexed stops
181mm short of its groove's end); that is ``base_deck``'s to add if ruled,
and the check carries it as a standing note.

THE FEED
========

The STOCK WASH crossing is a GX16 bore in the spine (``spine_panel``), high
row, on the SEALED side of the split, riding the ALWAYS-LIVE rail
(``mains_backplate.CROSSING_RAIL``). The lead leaves the plug's tail on the bore's
axis, crosses to the right divider's stock face at that height, runs forward
along the divider under the comb's end (the comb butts the divider from
z 658 up; the run passes at z 638), rises to the channel's height in the
end gap and enters the channel's right end cap. ``route()`` states that
polyline in station coordinates and ``check_stock_wash`` proves every
vertex lies inside the stock bay's clear air and off every blank. The
dimming element is C19's and lives on the signal side, per the spine's own
transit docstring; this module models nothing behind the spine.

WHAT IT EXPORTS
===============

STEP only, like ``mast_base``: the channel is a bought extrusion cut to
length on the mitre saw, not a sheet part, so there is no DXF nest entry.
The cut length is on the BOM line and in the STEP.

PLACEMENT CONVENTION
====================

Station coordinates throughout. The channel is drawn in its own frame with
the origin at its lower-left-front corner (local +X along the bay, +Y
rearward, +Z up, the diffuser on the Z = 0 face) and placed with ``plane``.
"""

from __future__ import annotations

from math import atan2, cos, degrees, hypot, radians, sin

from build123d import Align, Box, Cylinder, Location, Part, Plane, Sphere

from lib.house import GRID, HOUSE_CONNECTOR
from stations.cnc_shapeoko.carcass import DATUMS, Datums, export_part
from stations.cnc_shapeoko.parts import spine_panel, stock_rails
from stations.cnc_shapeoko.parts.console_plate import GX16_BEHIND
from stations.cnc_shapeoko.parts.mains_backplate import CROSSING_RAIL

__all__ = [
    "LABEL",
    "PLUG_LABEL",
    "LEAD_LABEL",
    "CROSSING",
    "CHANNEL_W",
    "CHANNEL_H",
    "END_GAP",
    "channel_length",
    "channel_x",
    "channel_y",
    "channel_z",
    "blank_clear",
    "rake_angles",
    "tilt_room",
    "bore_station",
    "route",
    "route_length",
    "plane",
    "build",
    "place",
    "build_plug",
    "build_lead",
    "placed_all",
    "joint_table",
    "wire_schedule",
    "check_stock_wash",
]

D: Datums = DATUMS


# ================================================================ parameters
# Everything specific to the wash. No dimension literal appears below this
# block; each value names where it came from.

LABEL = "stock_wash_channel"
"""The channel's name in the assembly and on its export."""

PLUG_LABEL = "stock_wash_plug"
LEAD_LABEL = "stock_wash_lead"

CROSSING = "STOCK WASH"
"""The spine crossing this run leaves by. SOURCE: spine_panel.CROSSINGS; the
bore's position is read from there, never restated here."""

RAIL = CROSSING_RAIL[CROSSING]
"""Which distribution rail feeds the wash. SOURCE: mains_backplate.CROSSING_RAIL.
ALWAYS-LIVE: a light in a bay is not a thing that moves or cuts, so it stays
up with the panel when the contactor drops."""

CHANNEL_W = 17.0
CHANNEL_H = 8.0
"""Channel section, width across the diffuser by depth of the U. SOURCE: task
C14 spec, "standard 17x8 profile", the surface-mount class every listing
sells (Muzata U1SW and its clones). CONFIDENCE: spec, REPRESENTATIVE: no SKU
on the BOM. The listings run 17.1..17.4 wide and 7..8.6 deep; the band has
1.5mm each side of 17 and 17mm under 8, so the class fits whichever clone
arrives. MEASURE THIS when the channel is in hand; the clip under the base
is not modelled and drops the channel by its own thickness."""

END_GAP = GRID
"""Air between each end of the channel and the divider's face. One grid
module. SOURCE: task C14 acceptance, "clear width minus 2*GRID". What it
buys: the end caps, and the lead's entry at the fed end, which comes up the
divider's face and turns into the channel there."""

STRIP = "LED strip, 24V DC, warm white, non-addressable, single colour"
"""SOURCE: task C14 spec ("non-addressable warm white, 24V, no red").
CONFIDENCE: spec. Two conductors. It is NOT the mast's addressable strip:
that one carries the seven-state grammar and its FAULT red; this one has one
state, on, and firmware sets how much."""

STRIP_CONDUCTORS = 2
"""What the lead carries: 24V and return. The dimming is upstream (C19)."""

CONNECTOR = HOUSE_CONNECTOR
"""The bulkhead in the spine is the house connector, sized to conductor
count by house rule; a 2-core run rides the same GX16 family. SOURCE:
lib.house.HOUSE_CONNECTOR."""

DIFFUSER = "frosted polycarbonate cover for the 17x8 channel, snap-in"
"""SOURCE: task C14 spec ("frosted diffuser"). CONFIDENCE: spec. Sold with the
channel in every kit; carried as its own BOM line because the task asks for
one and because a milky cover and a clear one are different lights."""

PLUG_L = 35.5
PLUG_D = 18.3
"""GX16 cable plug: overall length and knurl diameter. SOURCE: Handson
Technology GX16 datasheet, mechanical drawing (the sheet console_plate reads
GX16_BEHIND from): plug 35.5 overall, knurl Ø18.3, thread engagement 6.5.
CONFIDENCE: datasheet."""

SOCKET_PROUD = GX16_BEHIND - 8.6 - 2.0
"""How far the socket's front stands off the panel face it mounts through:
the drawing's 15.6 overall less its 8.6 thread and the 2.0 solder-tail
allowance it draws behind the nut, which is the 5 dimension on the socket's
front. SOURCE: same drawing. CONFIDENCE: datasheet, read off the figure."""

LEAD_D = 5.0
"""Lead diameter. SOURCE: Handson GX16 datasheet, "cable diameter <= 5.0mm":
the largest lead the plug's clamp takes, so the run is modelled at the
plug's limit and never tighter than the real one. CONFIDENCE: datasheet."""

LEAD_STRAIGHT = 5 * LEAD_D
"""Straight run out of the plug's clamp before the first bend: five
diameters, the minimum bend radius a flexible cord is given as a rule of
thumb. SOURCE: rule of thumb, no figure on the Handson sheet. CONFIDENCE:
choice. It also keeps the lead's first leg out of the plug's own body."""

LEAD_OFF = LEAD_D
"""Lead axis stood off the divider's face by one lead diameter: a saddle
clip's height under a 5mm lead. The clips are not modelled. CONFIDENCE:
choice."""

TILT_PROBE = 10.0
"""Degrees. The tilt the check costs out against the band's depth, to show
why the channel is flat. Not a design input. CONFIDENCE: choice of probe."""

EPS = 1e-6
"""Comparison tolerance, the same figure assembly.BAND_EPS uses."""


# ================================================================ derivations


def channel_length(d: Datums = D) -> float:
    """The cut length: the clear bay less one end gap each side."""
    return d.stock_clear_w - 2 * END_GAP


def channel_x(d: Datums = D) -> tuple[float, float]:
    """Station X span: centred in the clear bay, END_GAP off each divider."""
    return (d.stock_x[0] + END_GAP, d.stock_x[1] - END_GAP)


def band_y(d: Datums = D) -> tuple[float, float]:
    """The band the comb leaves ahead of itself: front plane to comb front."""
    return (d.y_front, stock_rails.comb_y(d)[0])


def channel_y(d: Datums = D) -> tuple[float, float]:
    """Station Y span: centred in the band, so the margin to the front plane
    and to the STOCK header's face is the same."""
    b0, b1 = band_y(d)
    y0 = b0 + ((b1 - b0) - CHANNEL_W) / 2
    return (y0, y0 + CHANNEL_W)


def channel_z(d: Datums = D) -> tuple[float, float]:
    """Station Z span: base against the cap's underside, diffuser below."""
    return (d.top_z[0] - CHANNEL_H, d.top_z[0])


def blank_clear(d: Datums = D) -> float:
    """Air between a standing blank's top edge and the diffuser."""
    return channel_z(d)[0] - stock_rails.blank_top_z(d)


def diffuser_centre_yz(d: Datums = D) -> tuple[float, float]:
    y0, y1 = channel_y(d)
    return ((y0 + y1) / 2, channel_z(d)[0])


def rake_angles(d: Datums = D) -> tuple[float, float]:
    """(top, bottom) angle in degrees between the light and a blank's front
    edge face, for a blank indexed to the STOCK header's face: measured from
    the diffuser's centre line to the edge's top and to the groove floor."""
    cy, cz = diffuser_centre_yz(d)
    face_y = stock_rails.comb_y(d)[0]
    dy = face_y - cy
    top = stock_rails.blank_top_z(d)
    floor = d.deck_top - stock_rails.GROOVE_D
    return (degrees(atan2(dy, cz - top)), degrees(atan2(dy, cz - floor)))


def tilt_room(angle: float = TILT_PROBE) -> float:
    """Depth of band a channel set ``angle`` degrees off flat would need."""
    a = radians(angle)
    return CHANNEL_W * cos(a) + CHANNEL_H * sin(a)


def bore_station(d: Datums = D) -> tuple[float, float, float]:
    """Station (x, y, z) of the STOCK WASH bore's axis on the spine's FRONT
    face, read from the spine's own crossing table."""
    x = spine_panel.crossing_x(d)[CROSSING]
    row = next(c.row for c in spine_panel.CROSSINGS if c.label == CROSSING)
    return (x, d.y_spine, d.deck_top + spine_panel.ROW_Z[row])


def plug_span_y(d: Datums = D) -> tuple[float, float]:
    """Station Y the plug's body occupies: from its tail to the socket's
    front, which stands SOCKET_PROUD off the spine."""
    y1 = d.y_spine - SOCKET_PROUD
    return (y1 - PLUG_L, y1)


def route(d: Datums = D) -> list[tuple[float, float, float]]:
    """THE FEED, as a polyline in station coordinates, bore to channel.

    Legs, in order:
      0 -> 1  out of the plug's tail on the bore's axis (the plug itself)
      1 -> 2  straight on out of the clamp, LEAD_STRAIGHT, before the bend
      2 -> 3  across the bay at the bore's height to the right divider's
              stock face, one LEAD_OFF off it
      3 -> 4  forward along the divider at that height, under the comb's
              end, to the channel's Y centre line
      4 -> 5  up the divider's face to the channel's height
      5 -> 6  along the channel's axis into its right end cap
    """
    bx, by, bz = bore_station(d)
    x_face = d.stock_x[1] - LEAD_OFF
    yc, _ = diffuser_centre_yz(d)
    zc = sum(channel_z(d)) / 2
    x_end = channel_x(d)[1]
    tail_y = plug_span_y(d)[0]
    bend_y = tail_y - LEAD_STRAIGHT
    return [
        (bx, by, bz),
        (bx, tail_y, bz),
        (bx, bend_y, bz),
        (x_face, bend_y, bz),
        (x_face, yc, bz),
        (x_face, yc, zc),
        (x_end, yc, zc),
    ]


def route_length(d: Datums = D) -> float:
    """Lead length along the polyline from the plug's tail to the channel."""
    pts = route(d)[1:]
    return sum(
        hypot(hypot(b[0] - a[0], b[1] - a[1]), b[2] - a[2])
        for a, b in zip(pts, pts[1:])
    )


def plane(d: Datums = D) -> Plane:
    """The channel's frame in station space: origin at its lower-left-front
    corner, local axes parallel to station axes."""
    return Plane(
        origin=(channel_x(d)[0], channel_y(d)[0], channel_z(d)[0]),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1),
    )


# ================================================================ build


def build(d: Datums = D) -> Part:
    """The channel, strip and diffuser as one envelope, in its own frame."""
    return Box(
        channel_length(d), CHANNEL_W, CHANNEL_H,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )


def place(flat: Part | None = None, d: Datums = D) -> Part:
    """The channel in station coordinates, under the cap ahead of the comb."""
    flat = build(d) if flat is None else flat
    return plane(d) * flat


def build_plug(d: Datums = D) -> Part:
    """The GX16 cable plug on the bore's axis, station coordinates: a
    cylinder from the socket's front to the plug's tail."""
    bx, _, bz = bore_station(d)
    y0, y1 = plug_span_y(d)
    return Plane(origin=(bx, y0, bz), z_dir=(0, 1, 0)) * Cylinder(
        PLUG_D / 2, y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def build_lead(d: Datums = D) -> Part:
    """The lead as a solid along ``route`` from the plug's tail on: one
    cylinder per leg, a sphere at every bend so the corners are closed."""
    pts = route(d)[1:]
    solid: Part | None = None
    for a, b in zip(pts, pts[1:]):
        v = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        length = hypot(hypot(v[0], v[1]), v[2])
        if length <= EPS:
            continue
        seg = Plane(origin=a, z_dir=v) * Cylinder(
            LEAD_D / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        solid = seg if solid is None else solid + seg
    for p in pts[1:-1]:
        solid = solid + Sphere(LEAD_D / 2).moved(Location(p))
    return solid


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, part): the channel, the plug and the lead, all
    reference solids -- bought, not cut."""
    return [
        (LABEL, "reference", place(d=d)),
        (PLUG_LABEL, "reference", build_plug(d)),
        (LEAD_LABEL, "reference", build_lead(d)),
    ]


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples, the
    shape ``stock_rails.joint_table`` uses. The channel's base bears on the
    cap's underside through its clips; nothing else it meets is a joint, and
    the plug and the lead are meant to touch nothing at all."""
    return [
        ("top_cap", LABEL, "bearing", None, 0.0, 0.0,
         "channel base flat against the cap's underside, on its clips"),
    ]


def wire_schedule(d: Datums = D) -> str:
    """The run, in the sentence the mains schedule uses."""
    bx, by, bz = bore_station(d)
    return (
        f"WIRE SCHEDULE stock_wash: crossing {CROSSING} (sealed/stock, "
        f"{spine_panel.BORE_D['gx16']:.0f}mm bore at station x {bx:.1f} z {bz:.1f}, "
        f"{CONNECTOR} family) rides {RAIL}; {STRIP_CONDUCTORS} conductors, "
        f"{STRIP}; dimmed by C19 from the ToF proximity state, on the signal side, "
        f"crossing the split at the transit; lead {LEAD_D:.0f}mm, "
        f"{route_length(d):.0f}mm from the plug's tail to the channel's right end"
    )


# ================================================================ checks


def _inside_bay(p: tuple[float, float, float], d: Datums, r: float = 0.0) -> bool:
    x, y, z = p
    return (
        d.stock_x[0] + r - EPS <= x <= d.stock_x[1] - r + EPS
        and d.y_front + r - EPS <= y <= d.y_spine + EPS
        and d.deck_top + r - EPS <= z <= d.top_z[0] - r + EPS
    )


def check_stock_wash(d: Datums = D) -> list[str]:
    """What the wash has to be true for, measured off the numbers and the
    solids. The assembly's interference check owns whether the three solids
    hit the comb, the blanks, the divider or the cap."""
    notes: list[str] = []
    x0, x1 = channel_x(d)
    y0, y1 = channel_y(d)
    z0, z1 = channel_z(d)
    b0, b1 = band_y(d)

    # -- the length is the acceptance's arithmetic, off the solid -------------
    bb = place(d=d).bounding_box()
    want = d.stock_clear_w - 2 * GRID
    if abs(bb.size.X - want) > 0.1:
        notes.append(
            f"channel is {bb.size.X:.2f} long, not the clear bay less two "
            f"grid modules, {want:.2f}"
        )
    if abs(bb.min.X - x0) > EPS or abs(bb.max.X - x1) > EPS:
        notes.append(f"channel spans x {bb.min.X:.2f}..{bb.max.X:.2f}, not {x0:.2f}..{x1:.2f}")

    # -- under the cap, in the comb's front band, over the blank tops ---------
    if abs(bb.max.Z - d.top_z[0]) > EPS:
        notes.append(
            f"channel base at z {bb.max.Z:.1f} is not on the cap's underside {d.top_z[0]:.1f}"
        )
    if bb.min.Y < b0 - EPS or bb.max.Y > b1 + EPS:
        notes.append(
            f"channel y {bb.min.Y:.1f}..{bb.max.Y:.1f} leaves the band ahead of the "
            f"comb, {b0:.1f}..{b1:.1f}: it is proud of the front or in the header"
        )
    if blank_clear(d) <= 0:
        notes.append(
            f"the diffuser at z {z0:.1f} hangs at or below a standing blank's top "
            f"{stock_rails.blank_top_z(d):.1f}: it is in the path of every blank"
        )

    # -- the feed lies inside the stock bay, off every blank ------------------
    pts = route(d)
    for i, p in enumerate(pts):
        r = 0.0 if i == 0 else LEAD_D / 2
        if not _inside_bay(p, d, r):
            notes.append(
                f"route vertex {i} ({p[0]:.1f}, {p[1]:.1f}, {p[2]:.1f}) lies outside "
                "the stock bay's clear air"
            )
    half = stock_rails.BLANK_T / 2 + LEAD_D / 2
    for cx in stock_rails.slot_x_station(d):
        for a, b in zip(pts[1:], pts[2:]):
            lo, hi = min(a[0], b[0]), max(a[0], b[0])
            in_x = lo - half <= cx <= hi + half
            in_yz = (
                min(a[1], b[1]) - LEAD_D / 2 < d.s.sheet_slot[0]
                and min(a[2], b[2]) - LEAD_D / 2 < stock_rails.blank_top_z(d)
            )
            if in_x and in_yz:
                notes.append(
                    f"the lead's leg ({a[0]:.0f}, {a[1]:.0f}, {a[2]:.0f}) -> "
                    f"({b[0]:.0f}, {b[1]:.0f}, {b[2]:.0f}) crosses the blank at x {cx:.1f}"
                )
                break
    comb_z0 = stock_rails.comb_z(d)[0]
    if pts[4][2] + LEAD_D / 2 > comb_z0 - EPS:
        notes.append(
            f"the lead runs forward at z {pts[3][2]:.1f} and the comb's end comes "
            f"down to {comb_z0:.1f}: the run is trapped between comb and divider"
        )

    # -- the channel is representative, so its clone is measured --------------
    notes.append(
        f"{LABEL} is the {CHANNEL_W:.0f} x {CHANNEL_H:.0f} surface-mount class "
        "with no SKU on the BOM, and its mounting clip is not modelled. MEASURE "
        "THIS when the channel is in hand: the band holds "
        f"{(b1 - b0 - CHANNEL_W) / 2:.1f}mm each side of it and "
        f"{blank_clear(d):.1f}mm under it, and the clip spends part of the second."
    )

    # -- standing: what the geometry does and does not light ------------------
    top, bottom = rake_angles(d)
    notes.append(
        "WASH INDEX, standing note. The diffuser faces straight down from "
        f"y {y0:.1f}..{y1:.1f} under the cap, {blank_clear(d):.0f}mm over a standing "
        "blank's top. It rakes a blank's FRONT edge only when that edge stands "
        f"behind it: indexed to the STOCK header's face at y {b1:.0f}, the edge is lit "
        f"at {top:.0f} degrees off its face at the top and {bottom:.1f} at the groove "
        "floor. A blank pushed flush with the carcass front stands under the channel "
        "and gets its top edge lit instead. The deck cuts no rear stop for the "
        f"indexed position (a {d.s.sheet_slot[0]:.0f} blank so placed ends "
        f"{stock_rails.groove_y(d)[1] - b1 - d.s.sheet_slot[0]:.0f}mm short of its "
        "groove's end); base_deck's to add if ruled. The channel is flat because a "
        f"{TILT_PROBE:.0f} degree set would need {tilt_room():.1f} of the band's "
        f"{b1 - b0:.0f}mm and buys nothing a source this close does not already give. "
        "Expected, and worth knowing before the first blank is racked."
    )
    notes.append(wire_schedule(d) + ". Expected, and worth knowing before the harness is cut.")

    return notes


# ================================================================ main

if __name__ == "__main__":
    d = D
    flat = build(d)
    x0, x1 = channel_x(d)
    y0, y1 = channel_y(d)
    z0, z1 = channel_z(d)
    bx, by, bz = bore_station(d)

    print("STOCK WASH: one channel under the cap, ahead of the comb")
    print(
        f"  {LABEL}: {channel_length(d):.3f} x {CHANNEL_W:.0f} x {CHANNEL_H:.0f}, "
        f"x {x0:.3f}..{x1:.3f}  y {y0:.1f}..{y1:.1f}  z {z0:.1f}..{z1:.1f}; "
        f"{blank_clear(d):.1f} over a blank's top, {END_GAP:.0f} off each divider"
    )
    top, bottom = rake_angles(d)
    print(
        f"  rake on an indexed blank's front edge: {top:.1f} deg at the top, "
        f"{bottom:.2f} deg at the groove floor; a {TILT_PROBE:.0f} deg tilt would "
        f"need {tilt_room():.1f} of the band's {band_y(d)[1] - band_y(d)[0]:.0f}"
    )
    print(
        f"  bore {CROSSING}: station ({bx:.2f}, {by:.2f}, {bz:.1f}), rail {RAIL}; "
        f"plug y {plug_span_y(d)[0]:.1f}..{plug_span_y(d)[1]:.1f}"
    )
    print("  feed polyline, station coordinates:")
    for i, (px, py, pz) in enumerate(route(d)):
        print(f"    {i}  ({px:8.2f}, {py:8.2f}, {pz:6.1f})")
    print(f"  lead {route_length(d):.0f}mm from the plug's tail to the channel")

    for label, group, part in placed_all(d):
        pb = part.bounding_box()
        print(
            f"\n  {label} ({group})"
            f"\n    placed  x {pb.min.X:.1f}..{pb.max.X:.1f}   y {pb.min.Y:.1f}..{pb.max.Y:.1f}"
            f"   z {pb.min.Z:.1f}..{pb.max.Z:.1f}   volume {part.volume / 1000:.1f} cm3"
        )

    print("\n  BOM lines this solid carries:")
    print(f"    LED channel, aluminium {CHANNEL_W:.0f}x{CHANNEL_H:.0f} surface-mount, cut to {channel_length(d):.0f}, with end caps and clips")
    print(f"    {STRIP}, {channel_length(d):.0f}mm run")
    print(f"    {DIFFUSER}")

    print("\n  wrote:")
    for p_ in export_part(flat, LABEL, dxf=False):
        print(f"    {p_}   (STEP only: bought extrusion, no nest entry)")

    found = check_stock_wash(d)
    if found:
        print(f"\n{len(found)} stock wash note(s):")
        for n_ in found:
            print(f"  - {n_}")
    else:
        print("\nno stock wash constraint violations")
