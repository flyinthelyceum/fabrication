"""Fitted trays, milled from two-tone Kaizen foam on the Shapeoko, generated
from the tool list rather than drawn pocket by pocket.

The brief's rule, verbatim: "Every tray is a parametric part in the same
build123d model as the carcass, generated from a tool list, exported as pocket
geometry on named DXF layers for the machine that cuts it. Adding a cutter to
the list regenerates the tray. That is the only version of this that survives
contact with a school."

So this module hardcodes no tool. It reads
``stations/cnc_shapeoko/tools/tool_list.csv`` -- a committed snapshot of the
canonical Google Sheet, per that directory's README -- and cuts one pocket per
unit of stock. The CSV is the input and it is never written to from here.

RULED 2026-09-03: FOAM, NOT FDM
===============================

Jared: "why aren't we milling from foam?" There was no recorded reason to
print. Trays are cut from ``FOAM_T`` two-tone Kaizen foam, a black top layer
over a white core, so an empty pocket shows a bright floor and a missing tool
reads from across the room. Brackets may still print, trays do not.

RULED 2026-09-11: UPRIGHT, BARE, ON A TILE
==========================================

The frontier scan of 2026-09-11 (notes.aaand.space/cnc-cutter-pockets.html)
replaced the two catalog box rules with a bore, and the one-tray-per-drawer
blank with tiles:

    bore      a CATALOG cutter stands in a bore of its shank diameter plus
              ``BORE_CLEAR``, ``BORE_DEPTH`` deep (the 1/8 shank row
              ``BORE_DEPTH_SMALL``), cutting edge UP. The number etched on
              the shank is hidden either way; the label beside the bore
              carries the identity. A cutter too long to stand under the
              drawer above (``stand_oal_max``) falls back to a captured
              silhouette pocket, and ``check_trays`` says so.
    collet    a CATALOG collet stands in a ``COLLET_BORE_D`` bore
              ``COLLET_BORE_DEPTH`` deep, nut off, wiped dry.
    captured  any row with ``dims_status=CAPTURED`` and a ``silhouette``:
              ``tools/capture_ingest.py`` recovered the tool's outline from a
              photo and wrote ``tools/captures/T0xx.dxf``, one closed loop in
              mm, offset by ``capture_ingest.FOAM_CLEAR``. The pocket IS that
              loop; its depth is ``height_class`` plus ``FOAM_DEPTH_ALLOW``.
    tube      a sealed spare in its shipping tube, lying: one pocket per
              tube, read off the ADD tab (``tools/tool_list_add.csv``), so
              the count reads from the drawer.

Bores are laid on a ruled grid (``BORE_ROWS``: 1/8, 1/4, 1/4 wide-body, 3/8;
``COLLET_ROW``) with more bores than cutters, because the strongest regret in
a year of foam is the recut tax. A bore with a tool has a label; a bore with
no label is by definition free. Bores get no finger scoop (the tool stands
proud); captured and tube pockets keep their capsule scoop.

Drawer 1 is TWO tiles, ``tray_d1_a`` (the cutter bore grid, front) and
``tray_d1_b`` (collets, wrenches, spares, behind), each its own DXF, so a
tile can be re-milled alone when a cutter is bought. The ``tile`` column of
the tool list says which. D2 and D3 stay one tray each for now.

LABELS (the C-01 blocker)
=========================

A label is milled beside its pocket through the black cap into the white
core. The scan's finding: a V-carve at small text never reaches white,
because a V bit's depth is set by its stroke width. The rule here computes
the label from the bit (``LABEL_BIT``: tip diameter and included angle) and
the cap (``TOP_LAYER_T``):

    TEXT_D     = TOP_LAYER_T + TEXT_BITE, and for a V bit no shallower than
                 the depth at which its groove is ``LABEL_STROKE_MIN`` wide
    stroke     = tip + 2 * TEXT_D * tan(angle / 2)   (the groove at the face)
    white      = tip + 2 * (TEXT_D - TOP_LAYER_T) * tan(angle / 2)
                 (the part of the groove that is below the cap: what reads)
    LABEL_H    = the least cap height whose counters stay open at that
                 stroke: 2 * (stroke + LABEL_COUNTER_MIN)

For the #112 1/16in flat the groove is 1.59 wide and white across its whole
floor, and a 6.5 cap fits the grid. For a V bit the white is only the strip
below the cap: the #502 (40 deg included) at 3.7 deep shows 0.4mm of white
inside a 2.7 groove, and the cap it needs (8.5) does not fit Tile A. The
numbers are printed by ``label_bit_table``; ``check_trays`` refuses a bit
whose white strip is under ``LABEL_WHITE_MIN``.

The glyphs are a single-stroke font (``GLYPHS``, this file): the DXF's
``TEXT_D<mm>`` layer carries the stroke CENTRELINES as open polylines, cut
as a contour ON the line, no offset, with ``LABEL_BIT``. The text is the
``label`` column of the tool list (twelve characters, upper-cased); a label
that outruns its cell is clipped from the right and reported.

WHAT A ROW NEEDS
================

``dims_status`` is one of CATALOG, CAPTURED, MEASURE, NONE. A CATALOG cutter
needs ``shank_d_mm`` and ``oal_mm``; a CATALOG collet needs ``oal_mm``; a
CAPTURED row needs ``silhouette`` and ``height_class``; a MEASURE row needs a
photo; a NONE row (kind bin or case: loose stock in a bin, hardware in its
own case) gets no pocket by design. A row whose ``status`` is ``struck`` does
not exist. A row that does not resolve to a rule is SKIPPED, COUNTED and
PRINTED by id and name, because a tool that quietly fails to appear in its
own tray is a tool nobody notices is homeless.

OUTPUT
======

One DXF per tile, importable by Carbide Create, with the geometry on layers
named by depth so the CAM reader takes depth from the layer and never from a
guess:

    OUTLINE          the tile blank, through
    POCKET_D<mm>     closed loops (bores, captured loops with their scoop,
                     tube pockets), pocket to that depth with the #102
    TEXT_D<mm>       label stroke centrelines, open polylines; contour on
                     the line, no offset, with ``LABEL_BIT``

plus a STEP of each tile for the assembly. No STL.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from build123d import (
    Align,
    Box,
    Circle,
    Face,
    GeomType,
    Kind,
    Location,
    Part,
    Plane,
    Polyline,
    Rectangle,
    Sketch,
    Wire,
    extrude,
    make_face,
    offset,
)

from lib.house import GRID, POCKET_TOOL_D, fits
from stations.cnc_shapeoko import params
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    T,
    Datums,
    export_part,
)
from stations.cnc_shapeoko.parts import drawers
from stations.cnc_shapeoko.parts.drawers import (
    BOTTOM_GROOVE_Z,
    BOTTOM_T,
    DRAWERS,
    DrawerSpec,
)

__all__ = [
    "TOOL_LIST",
    "TOOL_LIST_ADD",
    "TRAY_V1",
    "TILES",
    "TileSpec",
    "SOCKET_RULES",
    "DIMS_STATUS",
    "BORE_ROWS",
    "COLLET_ROW",
    "BoreRow",
    "LabelBit",
    "LABEL_BITS",
    "LABEL_BIT",
    "TEXT_D",
    "LABEL_H",
    "ToolRow",
    "Socket",
    "Pocket",
    "TrayPlan",
    "read_tools",
    "read_loop",
    "silhouette_path",
    "rows_for",
    "bbox",
    "socket",
    "stand_oal_max",
    "pocket_depth",
    "label_text",
    "label_width",
    "label_bit_table",
    "skipped",
    "spec_for",
    "tiles_for",
    "plan",
    "plan_all",
    "layers",
    "build",
    "place",
    "placed_all",
    "check_trays",
    "export",
    "export_all",
    "preview_svg",
]

D: Datums = DATUMS

TOOL_LIST = Path(__file__).resolve().parents[1] / "tools" / "tool_list.csv"
"""Committed snapshot of the Sheet's TRAY tab. Read only: regenerate it by
re-exporting the Sheet, never by editing it here."""

TOOL_LIST_ADD = TOOL_LIST.with_name("tool_list_add.csv")
"""Committed snapshot of the Sheet's ADD tab: the buy list. Read here for
one thing only, the sealed spares that get a tube pocket on Tile B."""

TRAY_V1 = "D1"
"""The drawer whose tiles the assembly places. D1 is the only drawer with
dimensioned rows; ``plan()`` works for all three."""


# ================================================================ parameters
# Foam facts and pocket rules. One block, a SOURCE / CONFIDENCE tag on each.

FOAM_T = 30.0
"""Kaizen foam sheet thickness. SOURCE: brief v8 BOM, "Kaizen foam, two-tone,
30mm, FastCap, 3"; FastCap Kaizen Foam 30mm B/W is listed 1-1/8in, 2 x 4 ft,
and the sheet runs +3 / -1 (scan 2026-09-11, A-05). CONFIDENCE: catalog,
high on the nominal. The blank is not measured until it is in hand."""

TOP_LAYER_T = 3.2
"""The black cap over the white core. SOURCE: ``params.SOURCES["kaizen_top_layer_t"]``,
FastCap's own 30mm B/W sheet: a 1/8in cap, about 3.2. The 5.0 this carried
until 2026-09-11 came from a reseller listing. CONFIDENCE:
``params.CONFIDENCE["kaizen_top_layer_t"]``, MEASURE: calipers on the blank in
hand set it, and ``check_trays`` says so until they do. Every label depth and
every floor-is-white check leans on this number."""

FOAM_SHEET = (609.6, 1219.2)
"""One Kaizen sheet, 2 x 4 ft (FastCap says +/- 1in). SOURCE: the same listing.
CONFIDENCE: catalog. ``check_trays`` refuses a blank that does not come off
one sheet."""

SOCKET_RULES = ("bore", "collet", "captured", "tube")
"""The only four ways a row gets a pocket. SOURCE: spec v3 as amended by the
2026-09-11 scan. A row that fits none of them is reported, never guessed at."""

DIMS_STATUS = ("CATALOG", "CAPTURED", "MEASURE", "NONE")
"""The ``dims_status`` vocabulary. CATALOG: the datasheet's numbers (cutters,
collets). CAPTURED: photographed, silhouette on disk. MEASURE: nothing yet.
NONE: no pocket by design (a bin, a case)."""

NO_POCKET_KINDS = ("bin", "case")
"""Kinds that never get a pocket: loose stock in a bin, hardware living in
its own organiser case. SOURCE: the Sheet's re-export of 2026-09-11."""

BORE_CLEAR = 0.25
"""Bore diameter over the shank. SOURCE: scan 2026-09-11 (B): the one
published number found, an Etsy holder "sized to .26 for a little
clearance". CONFIDENCE: inference; the offcut test cut is the check."""

BORE_DEPTH = 25.0
BORE_DEPTH_SMALL = 20.0
SMALL_SHANK_MAX = 3.5
"""How deep a cutter stands: 25 for a 1/4 or 3/8 shank, 20 for a 1/8 shank
(``shank_d`` at or under ``SMALL_SHANK_MAX``). SOURCE: scan 2026-09-11 (A-01,
B). 25 leaves 5 of floor on a nominal sheet and 4 on a thin one.
CONFIDENCE: rule."""

STAND_CLEAR = 10.0
"""Least air between a standing cutter's tip and the drawer above. A 63.5
OAL #201 in a 25 bore stands 38.5 proud of a 30 sheet and leaves 13.5 under
the 82 clear height (scan A-01: "13 mm to the drawer above"). SOURCE: rule.
CONFIDENCE: rule."""

COLLET_BORE_D = 17.6
COLLET_BORE_DEPTH = 22.0
"""ER-16 collet bore: the 17.0 DIN 6499 body (``params.SOURCES["er16_collet_od"]``)
plus 0.6, 22 deep so 5.5 of the 27.5 body stands proud to grab. SOURCE: scan
2026-09-11 (A-04). CONFIDENCE: rule on a standard size."""


@dataclass(frozen=True)
class BoreRow:
    """One ruled row of a bore grid: what stands in it, how many bores it
    carries and how close they sit. ``shank_d`` matches cutter rows; None
    means the collet row. ``wide`` takes the cutters whose cutting diameter
    exceeds the shank by more than a V-bit's (``WIDE_BODY_MIN``): the McFly,
    an insert V. ``cols`` fixes the bores per physical row (the collet
    row's 2 x 7); None lets the tile's width decide."""

    name: str
    bore_d: float
    depth: float
    pitch: float
    count: int
    shank_d: float | None = None
    wide: bool = False
    cols: int | None = None
    side_label: bool = False
    """Label BESIDE the bore (to its left) instead of in front of it: for the
    rows that are loose in X and dear in Y, the wide bodies and the 3/8."""


BORE_ROWS: tuple[BoreRow, ...] = (
    BoreRow("1/8 shank", 3.4, BORE_DEPTH_SMALL, 15.0, 10, shank_d=3.175),
    BoreRow("1/4 shank", 6.6, BORE_DEPTH, GRID, 20, shank_d=6.35),
    BoreRow("1/4 wide body", 6.6, BORE_DEPTH, 32.0, 3, shank_d=6.35, wide=True, side_label=True),
    BoreRow("3/8 shank", 9.8, BORE_DEPTH, 25.0, 2, shank_d=9.525, side_label=True),
)
"""Tile A's grid, front to back. SOURCE: scan 2026-09-11 (B), Jared's ruling
of the same day: 10 x 3.4 at 15, 20 x 6.6 at 20, 3 x 6.6 at 32 for wide
bodies, 2 x 9.8 at 25. The bore is the shank plus ``BORE_CLEAR`` rounded to
0.1; the pitch is the LEAST centre-to-centre: an empty cell is one pitch
wide, a labelled cell is as wide as its label needs, and cells flow
left to right and wrap (``_grid``). CONFIDENCE: ruling on the counts and
sizes; the pitch values are the scan's inference."""

COLLET_ROW = BoreRow("ER-16 collet", COLLET_BORE_D, COLLET_BORE_DEPTH, 24.0, 14, cols=7)
"""Tile B's collet grid: 14 bores in two rows of 7, three filled today, the
rest for the metric set (ADD A025). SOURCE: scan 2026-09-11 (A-04, B)."""

WIDE_BODY_MIN = 20.0
"""A cutter whose ``cut_d`` is over this stands in the wide-body row. The
V-bits (12.7) stay in the 20-pitch row, per the Sheet's socket_note on T022
and T023 and the scan's table; the McFly (25.4) and an insert V (27) do not.
SOURCE: scan 2026-09-11 (B). CONFIDENCE: rule."""

BODY_CLEAR = 1.0
"""Air between a standing cutter's body (its ``cut_d``) and the label or the
tile edge beside it, so a V-bit or the McFly does not sit on its own label.
SOURCE: rule. CONFIDENCE: rule."""

FOAM_DEPTH_ALLOW = 2.0
"""Added to a captured tool's ``height_class`` for its pocket depth. The
class is a ceiling (a 20 is at most 20 thick), so the tool sits at least
this far below the top face. SOURCE: spec v3. CONFIDENCE: rule."""

FOAM_REVEAL = 2.0
"""A lying tool sits this far below the top face, and every floor sits at
least this far into the bright core. SOURCE: rule, this file. CONFIDENCE:
rule."""

FOAM_FLOOR_MIN = 5.0
"""Least foam under any pocket: depth caps at ``FOAM_T`` less this, 25 on a
30 sheet, so a -1 sheet still leaves 4. SOURCE: scan 2026-09-11 (A-05).
CONFIDENCE: rule. Was 3.0 before the scan."""

POCKET_R = POCKET_TOOL_D / 2
"""Every internal corner of every pocket. SOURCE: ``lib.house.POCKET_TOOL_D``,
the #102 1/8in flat endmill. CONFIDENCE: house constant."""

SCOOP_W = GRID
SCOOP_REACH = 16.0
"""The finger scoop: a capsule ``SCOOP_W`` wide on a LYING pocket's front
side, reaching ``SCOOP_REACH`` beyond the pocket wall at the pocket's own
depth. Bores get none: the tool stands proud. SOURCE: rule. CONFIDENCE:
rule; the capsule clamps to the long side when that side is shorter than a
module."""

WALL = 6.0
"""Least foam between two pockets, or between a pocket and its neighbour's
scoop. SOURCE: rule, Kaizen practice. CONFIDENCE: rule."""

MARGIN = 10.0
"""Tile edge to the first pocket. Foam this thin at an edge tears; ten holds.
SOURCE: rule. CONFIDENCE: rule."""

TUBE_1_4 = (80.0, 13.0)
TUBE_1_8 = (58.0, 10.0)
"""A sealed Carbide 3D cutter tube, length by diameter, for a 1/4 and a 1/8
shank cutter. SOURCE: estimate off the tubes the starter pack came in, NOT
calipered; the spares' pockets are placeholders until one is measured.
CONFIDENCE: estimate, MEASURE."""


# ---- labels ---------------------------------------------------------------


@dataclass(frozen=True)
class LabelBit:
    """A cutter that could mill the labels: its tip diameter and included
    angle. A flat endmill has ``angle`` 0 and a groove as wide as its tip;
    a V bit's groove widens with depth."""

    name: str
    tip_d: float
    angle: float            # included angle, degrees; 0 for a flat
    owned: bool
    source: str

    def groove(self, depth: float) -> float:
        """Width of the groove at ``depth`` below the face."""
        return self.tip_d + 2.0 * depth * math.tan(math.radians(self.angle) / 2.0)

    def white(self, depth: float) -> float:
        """The width of the groove that is BELOW the black cap: what reads
        as white from above. A flat's whole floor; a V's centre strip."""
        return self.groove(depth - TOP_LAYER_T) if depth > TOP_LAYER_T else 0.0


LABEL_BITS: dict[str, LabelBit] = {
    "#112": LabelBit("#112", 1.5875, 0.0, False,
                     "Carbide 3D #112 .0625in flat, ADD A031 (shop JSON 2026-09-11)"),
    "#102": LabelBit("#102", POCKET_TOOL_D, 0.0, True,
                     "Carbide 3D #102 .125in flat, tool_list T017; the pocket cutter"),
    "#502": LabelBit("#502", 0.1, 40.0, False,
                     "Carbide 3D #502 engraver, 40 deg included / 20 deg taper, ADD A020"),
    "#501": LabelBit("#501", 0.1, 60.0, False,
                     "Carbide 3D #501 engraver, 60 deg included / 30 deg taper, ADD A030"),
}
"""The candidates, with what each one's groove does through the cap. The
scan's fix named "a 30 deg engraver": the #501 is 30 deg of TAPER, 60
included; the #502 is the narrowest Carbide 3D sells. Both are V bits, so
their white is a strip narrower than their groove (``LabelBit.white``)."""

LABEL_BIT = LABEL_BITS["#112"]
"""The label cutter. CHOSEN 2026-09-11 by the numbers in ``label_bit_table``:
the only bit whose groove is white across its whole width AND whose cap
height fits Tile A's grid with the Sheet's twelve-character labels. Not
owned (ADD A031, $35, in stock). The #102, owned, needs a 9.5 cap that
overflows the tile; the #502 shows 0.4mm of white in a 2.7 groove.
Switch the key to move every label, depth and pitch at once."""

TEXT_BITE = 0.5
"""Labels are milled through the black cap and half a millimetre into the
white, so the glyph floor reads bright even when the cap runs thick.
SOURCE: rule against ``TOP_LAYER_T``. CONFIDENCE: rule."""

LABEL_STROKE_MIN = 1.5
"""For a V bit: the least groove width at the face worth reading at all,
which sets its depth when the cap alone would leave it a hairline.
SOURCE: rule. CONFIDENCE: rule."""

LABEL_WHITE_MIN = 1.0
"""Least width of white a label stroke must show. Below this the label is a
dark groove in black foam, the C-01 blocker. SOURCE: rule. CONFIDENCE:
rule."""

LABEL_COUNTER_MIN = 1.5
"""Least foam left inside a glyph (the hole in a 0, the gap between the bars
of an E) and between two glyphs. A sliver thinner than this, standing
``TEXT_D`` tall in PE foam, tears out with the cutter. SOURCE: rule.
CONFIDENCE: rule; the offcut test cut is the check."""

LABEL_WALL = 2.5
LABEL_GAP = LABEL_WALL
"""Least foam between a label and anything else: a pocket, a bore, the next
label. A label groove is only ``TEXT_D`` deep, so it needs less wall than a
pocket does. SOURCE: rule. CONFIDENCE: rule."""

LABEL_AIR = 8.0
"""Air between two neighbouring labels in a bore row, so "#301 90" and
"#202" read as two labels and not one string: a word space in the stroke
font, which is a glyph gap either side of a one-unit blank. SOURCE: rule,
from looking at the first render. CONFIDENCE: rule."""


def text_depth(bit: LabelBit = LABEL_BIT) -> float:
    """How deep the label cutter goes: through the cap by ``TEXT_BITE``, and
    for a V bit no shallower than makes its groove ``LABEL_STROKE_MIN`` wide.
    Rounded to 0.1 because it names a DXF layer."""
    d = TOP_LAYER_T + TEXT_BITE
    if bit.angle > 0:
        d = max(d, (LABEL_STROKE_MIN - bit.tip_d) / (2.0 * math.tan(math.radians(bit.angle) / 2.0)))
    return round(d, 1)


def label_cap(bit: LabelBit = LABEL_BIT, depth: float | None = None) -> float:
    """The least cap height whose counters stay open at this bit's stroke:
    a glyph is four units tall with a bar at two, so the cap is twice a
    stroke plus a counter. Rounded up to 0.5."""
    depth = text_depth(bit) if depth is None else depth
    return math.ceil(2.0 * (bit.groove(depth) + LABEL_COUNTER_MIN) * 2.0) / 2.0


TEXT_D = text_depth()
"""Label depth for ``LABEL_BIT``: 3.7 through a 3.2 cap. Computed, never
typed: change the bit or the cap and the layer name follows."""

LABEL_STROKE = LABEL_BIT.groove(TEXT_D)
"""The label groove at the face, for ``LABEL_BIT`` at ``TEXT_D``."""

LABEL_H = label_cap()
"""Label cap height, computed from the stroke: 6.5 for the #112."""

LABEL_BOX_H = LABEL_H + LABEL_STROKE
"""What a label occupies in Y: its cap plus a stroke (half above, half
below the centrelines)."""

ARC_CHORD_TOL = 0.05
"""Chord error when a captured loop's DXF is read back and any arc in it is
sampled to points. The ingest writes lines only; this covers a hand-edited
DXF. CONFIDENCE: choice."""


# ---- the stroke font -------------------------------------------------------
# Single-stroke glyphs on a grid: x in glyph-width units (2 for most, the
# width given first), y in 0..4 with the bar at 2. Each stroke is a
# polyline of centreline points; the cutter follows it ON the line. Upper
# case, digits and the few marks a tool label uses. Anything else is
# dropped from the label and reported.

_G = dict[str, tuple[float, tuple[tuple[tuple[float, float], ...], ...]]]

GLYPHS: _G = {
    " ": (1.0, ()),
    "0": (2.0, (((0, 0), (2, 0), (2, 4), (0, 4), (0, 0.001)),)),
    "1": (1.0, (((0, 3), (1, 4), (1, 0)),)),
    "2": (2.0, (((0, 4), (2, 4), (2, 2), (0, 2), (0, 0), (2, 0)),)),
    "3": (2.0, (((0, 4), (2, 4), (2, 0), (0, 0)), ((0.6, 2), (2, 2)))),
    "4": (2.0, (((0, 4), (0, 2), (2, 2)), ((2, 4), (2, 0)))),
    "5": (2.0, (((2, 4), (0, 4), (0, 2), (2, 2), (2, 0), (0, 0)),)),
    "6": (2.0, (((2, 4), (0, 4), (0, 0), (2, 0), (2, 2), (0, 2)),)),
    "7": (2.0, (((0, 4), (2, 4), (0.7, 0)),)),
    "8": (2.0, (((0.5, 2), (0, 1.5), (0, 0.5), (0.5, 0), (1.5, 0), (2, 0.5), (2, 1.5), (1.5, 2),
                 (2, 2.5), (2, 3.5), (1.5, 4), (0.5, 4), (0, 3.5), (0, 2.5), (0.5, 2), (1.5, 2)),)),
    "9": (2.0, (((0, 0), (2, 0), (2, 4), (0, 4), (0, 2), (2, 2)),)),
    "A": (2.0, (((0, 0), (0, 3), (1, 4), (2, 3), (2, 0)), ((0, 2), (2, 2)))),
    "B": (2.0, (((0, 0), (0, 4), (2, 4), (2, 2), (0, 2)), ((2, 2), (2, 0), (0, 0)))),
    "C": (2.0, (((2, 4), (0, 4), (0, 0), (2, 0)),)),
    "D": (2.0, (((0, 0), (0, 4), (1.4, 4), (2, 3.4), (2, 0.6), (1.4, 0), (0, 0)),)),
    "E": (2.0, (((2, 4), (0, 4), (0, 0), (2, 0)), ((0, 2), (1.4, 2)))),
    "F": (2.0, (((2, 4), (0, 4), (0, 0)), ((0, 2), (1.4, 2)))),
    "G": (2.0, (((2, 4), (0, 4), (0, 0), (2, 0), (2, 2), (1, 2)),)),
    "H": (2.0, (((0, 0), (0, 4)), ((2, 0), (2, 4)), ((0, 2), (2, 2)))),
    "I": (1.0, (((0, 4), (1, 4)), ((0.5, 4), (0.5, 0)), ((0, 0), (1, 0)))),
    "J": (2.0, (((2, 4), (2, 0.6), (1.4, 0), (0.6, 0), (0, 0.6)),)),
    "K": (2.0, (((0, 0), (0, 4)), ((2, 4), (0, 1.6)), ((0.7, 2.2), (2, 0)))),
    "L": (2.0, (((0, 4), (0, 0), (2, 0)),)),
    "M": (2.0, (((0, 0), (0, 4), (1, 2), (2, 4), (2, 0)),)),
    "N": (2.0, (((0, 0), (0, 4), (2, 0), (2, 4)),)),
    "O": (2.0, (((0.5, 0), (1.5, 0), (2, 0.5), (2, 3.5), (1.5, 4), (0.5, 4), (0, 3.5), (0, 0.5), (0.5, 0.001)),)),
    "P": (2.0, (((0, 0), (0, 4), (2, 4), (2, 2), (0, 2)),)),
    "Q": (2.0, (((0.5, 0), (1.5, 0), (2, 0.5), (2, 3.5), (1.5, 4), (0.5, 4), (0, 3.5), (0, 0.5), (0.5, 0.001)),
                ((1.2, 0.8), (2.2, -0.2)))),
    "R": (2.0, (((0, 0), (0, 4), (2, 4), (2, 2), (0, 2)), ((0.8, 2), (2, 0)))),
    "S": (2.0, (((2, 3.5), (1.5, 4), (0.5, 4), (0, 3.5), (0, 2.5), (0.5, 2), (1.5, 2), (2, 1.5), (2, 0.5),
                 (1.5, 0), (0.5, 0), (0, 0.5)),)),
    "T": (2.0, (((0, 4), (2, 4)), ((1, 4), (1, 0)))),
    "U": (2.0, (((0, 4), (0, 0.6), (0.6, 0), (1.4, 0), (2, 0.6), (2, 4)),)),
    "V": (2.0, (((0, 4), (1, 0), (2, 4)),)),
    "W": (2.0, (((0, 4), (0.5, 0), (1, 2.4), (1.5, 0), (2, 4)),)),
    "X": (2.0, (((0, 0), (2, 4)), ((0, 4), (2, 0)))),
    "Y": (2.0, (((0, 4), (1, 2), (2, 4)), ((1, 2), (1, 0)))),
    "Z": (2.0, (((0, 4), (2, 4), (0, 0), (2, 0)),)),
    "#": (2.6, (((0.5, 0), (0.8, 4)), ((1.8, 0), (2.1, 4)), ((0, 1), (2.6, 1)), ((0, 3), (2.6, 3)))),
    "/": (1.2, (((0, 0), (1.2, 4)),)),
    "-": (1.5, (((0, 2), (1.5, 2)),)),
    ".": (0.6, (((0.1, 0), (0.5, 0)),)),
    "+": (2.0, (((0, 2), (2, 2)), ((1, 1), (1, 3)))),
}


def _glyph_units(h: float, stroke: float) -> tuple[float, float]:
    """(x unit, y unit) in mm for a cap height ``h``: the y unit is a
    quarter of the cap; a two-unit glyph is at least a stroke and a counter
    wide (so a 0 has a hole) and otherwise six tenths of the cap."""
    uy = h / 4.0
    ux = max(0.6 * h, stroke + LABEL_COUNTER_MIN) / 2.0
    return ux, uy


def label_strokes(txt: str, h: float = LABEL_H, stroke: float = LABEL_STROKE) -> tuple[list[tuple[tuple[float, float], ...]], float]:
    """The centreline polylines of ``txt`` in mm, the label's left stroke
    edge at x 0 and its baseline stroke edge at y 0, plus the label's total
    width (stroke included). Glyphs the font lacks are skipped."""
    ux, uy = _glyph_units(h, stroke)
    gap = stroke + LABEL_COUNTER_MIN         # centreline to centreline air between glyphs
    x = stroke / 2.0
    y0 = stroke / 2.0
    out: list[tuple[tuple[float, float], ...]] = []
    first = True
    for ch in txt.upper():
        if ch not in GLYPHS:
            continue
        w, strokes = GLYPHS[ch]
        if not first:
            x += gap
        first = False
        for s in strokes:
            out.append(tuple((x + px * ux, y0 + py * uy) for px, py in s))
        x += w * ux
    width = (x + stroke / 2.0) if not first else 0.0
    return out, width


def label_width(txt: str, h: float = LABEL_H, stroke: float = LABEL_STROKE) -> float:
    return label_strokes(txt, h, stroke)[1]


def clip_label(txt: str, room: float) -> str:
    """The longest head of ``txt`` that fits ``room``; the text gives way
    from the right, never the cap height, which the stroke fixed."""
    txt = txt.upper()
    while txt and label_width(txt) > room:
        txt = txt[:-1].rstrip()
    return txt


def label_bit_table() -> list[tuple[str, float, float, float, float, bool]]:
    """(name, depth, groove, white, cap, owned) for every candidate bit."""
    out = []
    for b in LABEL_BITS.values():
        d = text_depth(b)
        out.append((b.name, d, b.groove(d), b.white(d), label_cap(b, d), b.owned))
    return out


# ================================================================ the list


@dataclass(frozen=True)
class ToolRow:
    """One row of the tool list, typed. Unknown numbers stay None rather than
    becoming zero, because a zero-length pocket is a hole in a tray."""

    id: str
    name: str
    drawer: str
    kind: str
    shank_d: float | None
    cut_d: float | None
    oal: float | None
    qty: int
    dims_status: str
    height_class: float | None = None
    silhouette: str = ""
    tile: str = ""
    label: str = ""
    status: str = "active"
    tube: tuple[float, float] | None = None
    """A tube row's (length, diameter): only the ADD tab's spares carry one."""

    @property
    def status_(self) -> str:
        return self.dims_status.strip().upper()

    @property
    def struck(self) -> bool:
        return self.status.strip().lower() == "struck"

    @property
    def rule(self) -> str | None:
        """Which of ``SOCKET_RULES`` makes this row's pocket, or None. A
        cutter too long to stand takes ``captured`` when it has a
        silhouette; ``skipped`` explains it when it has not."""
        if self.struck or self.kind in NO_POCKET_KINDS:
            return None
        if self.tube is not None:
            return "tube"
        if self.status_ == "CAPTURED" and self.silhouette and self.height_class:
            return "captured"
        if self.status_ == "CATALOG" and self.kind == "cutter":
            return "bore"
        if self.status_ == "CATALOG" and self.kind == "collet":
            return "collet"
        return None


def _num(raw: str) -> float | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def read_tools(path: Path = TOOL_LIST) -> list[ToolRow]:
    """Every row of the snapshot, in file order, struck rows included (they
    are filtered by ``rows_for``). ``bbox_*_mm`` are the ingest's record of
    a capture's L and W and ``socket_note`` is a free note; neither is read
    here, because neither makes a pocket."""
    out: list[ToolRow] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            qty = _num(r.get("qty", "")) or 1
            out.append(
                ToolRow(
                    id=(r.get("id") or "").strip(),
                    name=(r.get("name") or "").strip(),
                    drawer=(r.get("drawer") or "").strip().upper(),
                    kind=(r.get("kind") or "").strip().lower(),
                    shank_d=_num(r.get("shank_d_mm", "")),
                    cut_d=_num(r.get("cut_d_mm", "")),
                    oal=_num(r.get("oal_mm", "")),
                    qty=int(qty),
                    dims_status=(r.get("dims_status") or "").strip(),
                    height_class=_num(r.get("height_class", "")),
                    silhouette=(r.get("silhouette") or "").strip(),
                    tile=(r.get("tile") or "").strip().upper(),
                    label=(r.get("label") or "").strip(),
                    status=(r.get("status") or "active").strip() or "active",
                )
            )
    return out


_PACK = re.compile(r"(\d+)-pack", re.I)
_PART = re.compile(r"#\d{3}")


def read_spares(path: Path = TOOL_LIST_ADD, drawer: str = TRAY_V1) -> list[ToolRow]:
    """The ADD tab's sealed spares as tube rows: one unit per cutter in the
    pack, lying in its tube on the tile the ADD row names. Only rows whose
    category says spares and whose status is proposed or owned; a struck
    row is not coming. Absent file, no spares."""
    if not path.exists():
        return []
    out: list[ToolRow] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cat = (r.get("category") or "").lower()
            status = (r.get("status") or "").strip().lower()
            if "spare" not in cat or status not in ("proposed", "owned"):
                continue
            tile = (r.get("tile") or "").strip().upper()
            dims = (r.get("dims") or "").lower()
            name = r.get("name") or ""
            m = _PACK.search(name)
            per = int(m.group(1)) if m else 1
            qty = int(_num(r.get("qty", "")) or 1) * per
            tube = TUBE_1_8 if "1/8" in dims else TUBE_1_4
            part = _PART.search(name)
            out.append(
                ToolRow(
                    id=(r.get("id") or "").strip(),
                    name=name.strip(),
                    drawer=drawer,
                    kind="tube",
                    shank_d=None, cut_d=None, oal=None,
                    qty=qty,
                    dims_status="CATALOG",
                    tile=tile,
                    label=(part.group(0) if part else (r.get("part_no") or "").strip()),
                    tube=tube,
                )
            )
    return out


def silhouette_path(row: ToolRow) -> Path:
    """Where a captured row's loop lives: ``silhouette`` relative to the tool
    list's directory (``captures/T0xx.dxf``), or absolute as given."""
    p = Path(row.silhouette)
    return p if p.is_absolute() else TOOL_LIST.parent / p


def read_loop(path: Path) -> tuple[tuple[float, float], ...]:
    """The closed loop in a capture's DXF as points, mm, its bounding box's
    corner at the origin. One loop per file; the largest wins if a hand
    edit left more."""
    from build123d import import_dxf

    wires = Wire.combine(import_dxf(str(path)))
    if not wires:
        raise ValueError(f"{path}: no loop")
    wire = max(wires, key=lambda w: w.length)
    if not wire.is_closed:
        raise ValueError(f"{path}: the loop is not closed")
    pts: list[tuple[float, float]] = []
    for e in wire.edges():
        if e.geom_type == GeomType.LINE:
            n = 1
        else:
            r = max(getattr(e, "radius", 1.0), 1e-6)
            step = 2 * math.acos(max(1 - ARC_CHORD_TOL / r, -1.0))
            n = max(int(math.ceil(e.length / (r * step))), 2)
        for i in range(n):
            p = e.position_at(i / n)
            pts.append((p.X, p.Y))
    x0 = min(p[0] for p in pts)
    y0 = min(p[1] for p in pts)
    return tuple((x - x0, y - y0) for x, y in pts)


def rows_for(key: str, rows: list[ToolRow] | None = None, tile: str | None = None) -> list[ToolRow]:
    """Every live row assigned to one drawer, and to one tile of it when
    ``tile`` is given. Struck rows do not exist. ``key`` is case-blind."""
    rows = read_tools() if rows is None else rows
    key = key.upper()
    out = [r for r in rows if r.drawer == key and not r.struck]
    if tile is not None:
        out = [r for r in out if r.tile == tile.upper()]
    return out


@dataclass(frozen=True)
class Socket:
    """What one row's rule resolved to: the box the pocket packs by (L the
    longer side, W, T the tool's thickness or height class), the pocket's
    size as laid before rotation, the loop when there is one, and for a
    bore its diameter and depth."""

    rule: str
    l: float
    w: float
    t: float
    pw: float
    pd: float
    loop: tuple[tuple[float, float], ...] | None = None
    bore_d: float = 0.0
    bore_depth: float = 0.0


def bbox(row: ToolRow) -> tuple[float, float, float] | None:
    """(L, W, T) for one row, or None when it has no pocket. Kept for the
    report; ``socket`` is what the plan uses."""
    s = socket(row)
    return None if s is None else (s.l, s.w, s.t)


_loops: dict[Path, tuple[tuple[float, float], ...]] = {}


def bore_depth_for(shank_d: float) -> float:
    return BORE_DEPTH_SMALL if shank_d <= SMALL_SHANK_MAX else BORE_DEPTH


def stand_oal_max(spec: DrawerSpec | None = None, shank_d: float = 6.35, d: Datums = D) -> float:
    """The longest cutter that stands in its bore under the drawer above:
    the clear height, less the foam, plus the bore, less ``STAND_CLEAR``."""
    spec = spec_for(TRAY_V1) if spec is None else spec
    _iw, _idep, ih = drawers.interior(spec, d)
    return ih - FOAM_T + bore_depth_for(shank_d) - STAND_CLEAR


def bore_row_for(row: ToolRow) -> BoreRow | None:
    """The ruled row a cutter stands in, by shank and body, or None."""
    if row.shank_d is None:
        return None
    wide = (row.cut_d or 0.0) > WIDE_BODY_MIN
    mine = [br for br in BORE_ROWS if br.shank_d is not None and abs(br.shank_d - row.shank_d) < 0.1]
    for br in mine:
        if br.wide == wide:
            return br
    return mine[0] if len(mine) == 1 and not wide else None


def socket(row: ToolRow, spec: DrawerSpec | None = None, d: Datums = D) -> Socket | None:
    """Resolve one row through ``SOCKET_RULES``. None when no rule fits or
    the rule's inputs are missing; the reason is ``skipped``'s to tell."""
    rule = row.rule
    if rule == "bore":
        if not (row.oal and row.shank_d):
            return None
        spec = spec_for(row.drawer) if spec is None and row.drawer else spec
        if row.oal > stand_oal_max(spec, row.shank_d, d):
            # too long to stand: lies in its silhouette, if it has one
            if row.silhouette and row.height_class:
                return _captured(row)
            return None
        br = bore_row_for(row)
        if br is None:
            return None
        body = max(row.shank_d, row.cut_d or 0.0)
        return Socket("bore", row.oal, body, row.oal, br.bore_d, br.bore_d,
                      bore_d=br.bore_d, bore_depth=br.depth)
    if rule == "collet":
        if not row.oal:
            return None
        return Socket("collet", row.oal, COLLET_BORE_D, row.oal, COLLET_BORE_D, COLLET_BORE_D,
                      bore_d=COLLET_BORE_D, bore_depth=COLLET_BORE_DEPTH)
    if rule == "captured":
        return _captured(row)
    if rule == "tube":
        l, dia = row.tube
        pw, pd = l + 2 * FOAM_REVEAL, dia + 2 * FOAM_REVEAL
        return Socket("tube", pw, pd, dia, pw, pd)
    return None


def _captured(row: ToolRow) -> Socket | None:
    path = silhouette_path(row)
    if not path.exists():
        return None
    if path not in _loops:
        _loops[path] = read_loop(path)
    loop = _loops[path]
    pw = max(p[0] for p in loop)
    pd = max(p[1] for p in loop)
    return Socket("captured", max(pw, pd), min(pw, pd), float(row.height_class), pw, pd, loop)


def pocket_depth(t: float, allow: float = FOAM_REVEAL) -> float:
    """``max(T, TOP_LAYER_T) + allow``, capped to leave the floor. The allow
    is ``FOAM_REVEAL`` over a caliper thickness and ``FOAM_DEPTH_ALLOW`` over
    a height class."""
    return min(max(t, TOP_LAYER_T) + allow, FOAM_T - FOAM_FLOOR_MIN)


def label_text(row: ToolRow) -> str:
    """What is milled beside the pocket: the Sheet's ``label`` column,
    twelve characters, upper-cased for the stroke font. A row with no
    label falls back to a twelve-character head of its name, and
    ``check_trays`` says so."""
    return (row.label or row.name[:12]).upper()


def skipped(key: str, rows: list[ToolRow] | None = None, tile: str | None = None,
            d: Datums = D) -> list[tuple[ToolRow, str]]:
    """(row, why) for every live row of this drawer (or tile) that gets no
    pocket and should have one. Bins and cases are not listed: no pocket is
    their design."""
    out: list[tuple[ToolRow, str]] = []
    spec = spec_for(key)
    for r in rows_for(key, rows, tile):
        if r.kind in NO_POCKET_KINDS:
            continue
        if r.rule is None:
            if r.status_ == "CATALOG":
                out.append((r, f"no pocket yet: CATALOG but no catalog rule for kind {r.kind!r}, photograph it (MEASURE THIS)"))
            elif r.status_ == "CAPTURED":
                out.append((r, "no pocket yet: CAPTURED but silhouette or height_class is blank, re-run the ingest (MEASURE THIS)"))
            else:
                out.append((r, "no pocket yet: MEASURE, photograph it on the capture sheet (MEASURE THIS)"))
        elif socket(r, spec, d) is None:
            if r.rule == "captured":
                out.append((r, f"no pocket yet: silhouette {r.silhouette} is not on disk, re-run the ingest (MEASURE THIS)"))
            elif r.rule == "bore" and r.oal and r.shank_d and r.oal > stand_oal_max(spec, r.shank_d, d):
                out.append((r, f"too long to stand: {r.oal:g} OAL over the {stand_oal_max(spec, r.shank_d, d):g} a bore "
                               f"allows under the drawer above. It lies in a captured pocket: photograph it (MEASURE THIS)"))
            elif r.rule == "bore" and r.shank_d and bore_row_for(r) is None:
                out.append((r, f"no bore row takes a {r.shank_d:g} shank"
                               f"{' with a wide body' if (r.cut_d or 0) > WIDE_BODY_MIN else ''}: add one to BORE_ROWS"))
            else:
                out.append((r, f"no pocket yet: CATALOG {r.kind} without oal/shank, fill the catalog columns (MEASURE THIS)"))
    return out


# ================================================================ the plan


@dataclass(frozen=True)
class TileSpec:
    """One foam blank in a drawer: its key (A, B, or "" for a whole-floor
    tray), its depth along the drawer, and where it starts from the front.
    Width is always the drawer's inside width."""

    key: str
    depth: float
    y0: float = 0.0

    def label(self, drawer: str) -> str:
        return f"tray_{drawer.lower()}" + (f"_{self.key.lower()}" if self.key else "")


TILE_A_D = 150.0
"""Tile A's depth along the drawer: the bore grid. SOURCE: scan 2026-09-11
(A-03), "TILE A, 271 x 150". Tile B takes the rest of the floor.
CONFIDENCE: ruling."""

TILES: dict[str, tuple[TileSpec, ...]] = {
    "D1": (TileSpec("A", TILE_A_D, 0.0), TileSpec("B", -1.0, TILE_A_D)),
}
"""Which drawers are tiled and how. A depth of -1 means "the rest of the
floor", resolved by ``tiles_for`` against ``drawers.interior``."""


def spec_for(key: str) -> DrawerSpec:
    key = key.upper()
    for s in DRAWERS:
        if s.key == key:
            return s
    raise KeyError(f"no drawer with key {key!r}")


def tiles_for(key: str, d: Datums = D) -> tuple[TileSpec, ...]:
    """The blanks that make up one drawer's tray, front to back, sized
    against the drawer's inside floor."""
    key = key.upper()
    _iw, idep, _ih = drawers.interior(spec_for(key), d)
    out: list[TileSpec] = []
    for t in TILES.get(key, (TileSpec("", -1.0, 0.0),)):
        depth = (idep - t.y0) if t.depth < 0 else t.depth
        out.append(TileSpec(t.key, depth, t.y0))
    return tuple(out)


@dataclass(frozen=True)
class Pocket:
    """One pocket, its scoop and its label, in tile-local XY (X across the
    drawer, Y from the tile's front, origin at the tile's front-left
    corner). A bore is a circle of ``bore_d`` centred in its ``pw`` x
    ``pd`` box; an empty bore has no tool and no label."""

    tool_id: str
    name: str
    label: str
    kind: str
    rule: str           # which of SOCKET_RULES made it, or "empty" for a free bore
    l: float            # the tool's box
    w: float
    t: float
    x: float            # pocket box, min corner
    y: float
    pw: float           # pocket box, size as laid
    pd: float
    depth: float
    rotated: bool       # L along Y; scoop on the +X long side
    label_x: float      # label box, min corner
    label_y: float
    label_h: float
    loop: tuple[tuple[float, float], ...] | None = None
    """A captured pocket's loop, pocket-local (its box's corner at 0, 0),
    before rotation. None for a box pocket or a bore."""
    bore_d: float = 0.0
    body_d: float = 0.0
    """A standing cutter's widest diameter (its ``cut_d``): what overhangs
    the bore in the air."""
    row: str = ""
    """The ruled bore row this bore belongs to, for the report."""
    label_full: str = ""
    """The label as the Sheet gave it, before any clip."""

    @property
    def is_bore(self) -> bool:
        return self.bore_d > 0

    @property
    def proud(self) -> float:
        """How far the tool stands above the top face: a cutter's length
        out of its bore, or zero unless a lying tool's floor cap bit."""
        return max(0.0, self.t - self.depth)

    @property
    def scoop_w(self) -> float:
        if self.is_bore:
            return 0.0
        long_side = self.pd if self.rotated else self.pw
        return min(SCOOP_W, long_side - 2 * POCKET_R)

    def scoop_cx(self) -> float:
        """The scoop sits on the front-right quarter of a lying pocket so the
        label, left-aligned in the same front band, has the room."""
        return self.x + max(self.pw - self.scoop_w / 2 - POCKET_R, self.pw / 2)

    def extent(self) -> tuple[float, float, float, float]:
        """(x0, y0, x1, y1) of pocket plus scoop: what another pocket must
        keep ``WALL`` away from."""
        if self.is_bore:
            return (self.x, self.y, self.x + self.pw, self.y + self.pd)
        if self.rotated:
            return (self.x, self.y, self.x + self.pw + SCOOP_REACH, self.y + self.pd)
        return (self.x, self.y - SCOOP_REACH, self.x + self.pw, self.y + self.pd)

    def body(self) -> Sketch:
        """The pocket without its scoop, in tile XY: the bore, the box, or
        the captured loop turned to lie as the box was laid."""
        if self.is_bore:
            return Circle(self.bore_d / 2).moved(Location((self.x + self.pw / 2, self.y + self.pd / 2)))
        if self.loop is None:
            return Rectangle(self.pw, self.pd, align=(Align.MIN, Align.MIN)).moved(
                Location((self.x, self.y))
            )
        face = make_face(Polyline(*self.loop, close=True))
        if self.rotated:
            # the loop's long side ran along X; the pocket was laid with L along Y
            face = face.moved(Location((0, 0, 0), (0, 0, 90)))
            bb = face.bounding_box()
            face = face.moved(Location((-bb.min.X, -bb.min.Y)))
        return face.moved(Location((self.x, self.y)))

    def outline(self) -> Sketch:
        """The milled loop: pocket body plus half-capsule scoop (lying
        pockets only), opened by the endmill's radius so every internal
        corner is what the cutter leaves. A bore is its circle."""
        if self.is_bore:
            return self.body()
        rect = self.body()
        sw = self.scoop_w
        stem = max(SCOOP_REACH - sw / 2, 0.0)
        if self.rotated:
            cx, cy = self.x + self.pw, self.y + self.pd / 2
            parts = [rect, Circle(sw / 2).moved(Location((cx + stem, cy)))]
            if stem > 0:
                parts.append(
                    Rectangle(stem, sw, align=(Align.MIN, Align.CENTER)).moved(Location((cx, cy)))
                )
        else:
            cx, cy = self.scoop_cx(), self.y
            parts = [rect, Circle(sw / 2).moved(Location((cx, cy - stem)))]
            if stem > 0:
                parts.append(
                    Rectangle(sw, stem, align=(Align.CENTER, Align.MAX)).moved(Location((cx, cy)))
                )
        sk = parts[0]
        for p in parts[1:]:
            sk = sk + p
        return offset(offset(sk, -POCKET_R, kind=Kind.ARC), POCKET_R, kind=Kind.ARC)

    def label_strokes(self) -> list[tuple[tuple[float, float], ...]]:
        """The label's centrelines in tile XY."""
        if not self.label:
            return []
        strokes, _w = label_strokes(self.label, self.label_h)
        return [tuple((self.label_x + px, self.label_y + py) for px, py in s) for s in strokes]

    def label_box(self) -> tuple[float, float, float, float] | None:
        if not self.label:
            return None
        return (self.label_x, self.label_y, self.label_x + label_width(self.label, self.label_h),
                self.label_y + self.label_h + LABEL_STROKE)


@dataclass(frozen=True)
class TrayPlan:
    key: str
    tile: TileSpec
    w: float            # the blank: the drawer's inside width
    d: float            # the tile's depth
    h: float            # FOAM_T
    pockets: tuple[Pocket, ...]
    used_d: float       # rear edge of the last row, plus margin
    notes: tuple[str, ...] = ()
    """What the composition had to do that the gate should see: labels
    clipped, rows overflowing, fallbacks."""

    @property
    def label(self) -> str:
        return self.tile.label(self.key)

    @property
    def filled(self) -> int:
        return sum(1 for p in self.pockets if p.rule != "empty")

    @property
    def bores(self) -> int:
        return sum(1 for p in self.pockets if p.is_bore)


def _units(key: str, rows: list[ToolRow] | None, tile: str | None, d: Datums) -> list[ToolRow]:
    """One entry per unit of stock, file order, rows with a pocket only."""
    no_pocket = {r.id for r, _why in skipped(key, rows, tile, d)}
    units: list[ToolRow] = []
    for r in rows_for(key, rows, tile):
        if r.id in no_pocket or r.kind in NO_POCKET_KINDS:
            continue
        units.extend([r] * max(1, r.qty))
    return units


def _bore_pocket(r: ToolRow | None, s: Socket | None, br: BoreRow, cx: float, cy: float,
                 label: str, label_full: str, lx: float, ly: float) -> Pocket:
    """One bore, filled (``r`` and ``s``) or empty, centred at (cx, cy)."""
    if r is None:
        return Pocket(
            tool_id="", name="", label="", kind="", rule="empty",
            l=0.0, w=0.0, t=0.0,
            x=cx - br.bore_d / 2, y=cy - br.bore_d / 2, pw=br.bore_d, pd=br.bore_d,
            depth=br.depth, rotated=False,
            label_x=0.0, label_y=0.0, label_h=LABEL_H,
            bore_d=br.bore_d, body_d=br.bore_d, row=br.name,
        )
    body = max(s.w, br.bore_d)
    return Pocket(
        tool_id=r.id, name=r.name, label=label, kind=r.kind, rule=s.rule,
        l=s.l, w=s.w, t=s.t,
        x=cx - br.bore_d / 2, y=cy - br.bore_d / 2, pw=br.bore_d, pd=br.bore_d,
        depth=min(s.bore_depth, FOAM_T - FOAM_FLOOR_MIN), rotated=False,
        label_x=lx, label_y=ly, label_h=LABEL_H,
        bore_d=br.bore_d, body_d=body, row=br.name, label_full=label_full,
    )


def _cell(br: BoreRow, r: ToolRow | None, s: Socket | None) -> tuple[float, float, float, str, float]:
    """(width, centre offset from the cell's left edge, body diameter, label,
    label width) of one bore's cell. An empty cell is one pitch; a labelled
    cell is as wide as the label needs, the label in front of the bore or
    beside it (``side_label``)."""
    if r is None:
        return br.pitch, br.pitch / 2, br.bore_d, "", 0.0
    lab = label_text(r)
    lw = label_width(lab)
    body = max(s.w, br.bore_d)
    if br.side_label:
        left = lw + BODY_CLEAR + body / 2
        right = max(br.pitch / 2, body / 2 + LABEL_AIR / 2)
        return left + right, left, body, lab, lw
    w = max(br.pitch, lw + LABEL_AIR, body + 2 * LABEL_WALL)
    return w, w / 2, body, lab, lw


def _grid(rows: tuple[BoreRow, ...], units: list[tuple[ToolRow, Socket]], tile_w: float,
          y: float, notes: list[str]) -> tuple[list[Pocket], float]:
    """Lay ruled bore rows front to back from ``y``. Each ruled row fills
    from the front-left with the cutters that belong to it, widest label
    first so a row's pitch reads as designed, then its free bores at the
    ruled pitch; cells flow left to right and wrap at the tile's width (or
    at ``cols`` per row). Returns the pockets and the Y the next thing may
    start at."""
    usable = tile_w - 2 * MARGIN
    out: list[Pocket] = []
    for br in rows:
        mine = [(r, s) for r, s in units if (
            (s.rule == "collet" and br.shank_d is None)
            or (s.rule == "bore" and br.shank_d is not None and bore_row_for(r) is br)
        )]
        if len(mine) > br.count:
            over = mine[br.count:]
            notes.append(
                f"the {br.name} row has {br.count} bores and {len(mine)} cutters: "
                + ", ".join(f"{r.id} {label_text(r)}" for r, _s in over)
                + " have no bore. Add bores to BORE_ROWS or move a cutter."
            )
            mine = mine[: br.count]
        mine.sort(key=lambda rs: -label_width(label_text(rs[0])))
        cells = [(r, s) for r, s in mine] + [(None, None)] * (br.count - len(mine))
        for r, s in mine:
            w, _off, _body, lab, lw = _cell(br, r, s)
            if w > usable:
                notes.append(f"label {lab!r} on {r.id} is {lw:.0f} wide and the tile has {usable:.0f}: it does not fit.")

        def pack(cap: int | None) -> list[list[tuple]]:
            """Physical rows: cells flow left to right and wrap at the tile's
            width, or at ``cap`` cells per row."""
            phys: list[list[tuple]] = [[]]
            x = 0.0
            for r, s in cells:
                w, off, body, lab, lw = _cell(br, r, s)
                full = (x > 0 and x + w > usable + 1e-6) or (cap is not None and len(phys[-1]) >= cap)
                if full:
                    phys.append([])
                    x = 0.0
                phys[-1].append((r, s, w, off, body, lab, lw))
                x += w
            return phys

        phys = pack(br.cols)
        if len(phys) > 1:
            # balance the rows so the last one is not a straggler
            phys = pack(math.ceil(br.count / len(phys)))
        for prow in phys:
            body_r = max(c[4] for c in prow) / 2
            if br.side_label:
                half = max(LABEL_BOX_H / 2, body_r, br.bore_d / 2 + LABEL_GAP)
                cy = y + half
                x = MARGIN
                for r, s, w, off, body, lab, lw in prow:
                    cx = x + off
                    lx, ly = x, cy - LABEL_BOX_H / 2
                    out.append(_bore_pocket(r, s, br, cx, cy, lab, lab, lx, ly))
                    x += w
                y = cy + half
            else:
                clear = max(br.bore_d / 2 + LABEL_GAP, body_r + BODY_CLEAR)
                ly = y
                cy = ly + LABEL_BOX_H + clear
                x = MARGIN
                for r, s, w, off, body, lab, lw in prow:
                    cx = x + off
                    lx = cx - lw / 2
                    out.append(_bore_pocket(r, s, br, cx, cy, lab, lab, lx, ly))
                    x += w
                y = cy + clear
    return out, y


def _shelf(units: list[tuple[ToolRow, Socket]], tile_w: float, y: float, notes: list[str]) -> tuple[list[Pocket], float]:
    """Lying pockets (captured, tube) in shelf rows, biggest first, front to
    back, left to right. Each pocket's scoop takes the right end of the band
    in front of it and its label sits in that band to the scoop's left; a
    label too wide for that room moves to its own band in front of the
    scoop. Returns the pockets and the next free Y."""
    out: list[Pocket] = []
    usable = tile_w - 2 * MARGIN
    units = sorted(units, key=lambda rs: -(rs[1].pw * rs[1].pd))
    shelves: list[dict] = []          # {"y": row_y, "x": next free x, "h": row height}
    for r, s in units:
        pw, pd, loop = s.pw, s.pd, s.loop
        if loop is None and pw < pd:
            pw, pd = pd, pw                 # a box is laid long side along X first
        rotated = pw > usable
        if rotated:
            pw, pd = pd, pw
        if loop is None:
            pw = max(pw, POCKET_TOOL_D)     # a pocket is never narrower than its cutter
            pd = max(pd, POCKET_TOOL_D)

        lab_full = label_text(r)
        lw = label_width(lab_full)
        sw = min(SCOOP_W, (pd if rotated else pw) - 2 * POCKET_R)
        if rotated:
            beside = pw                      # the band in front is the pocket's own width
        else:
            beside = max(pw - sw / 2 - POCKET_R, pw / 2) - sw / 2 - LABEL_WALL
        own_band = lw > beside
        lab = clip_label(lab_full, usable)
        if lab != lab_full.upper():
            notes.append(
                f"label {lab_full!r} on {r.id} is {lw:.0f} wide and the tile has {usable:.0f}: "
                f"milled as {lab!r}. Shorten the Sheet's label."
            )
        front = (0.0 if rotated else SCOOP_REACH)
        band = LABEL_BOX_H + LABEL_GAP if (own_band or rotated) else 0.0
        cell_w = max(pw + (SCOOP_REACH if rotated else 0.0), lw)
        cell_h = pd + front + band

        # first shelf with the room, else a new one behind the last
        home = next((sh for sh in shelves if sh["x"] + cell_w <= tile_w - MARGIN + 1e-6), None)
        if home is None:
            home = {"y": (shelves[-1]["y"] + shelves[-1]["h"] + WALL) if shelves else y, "x": MARGIN, "h": 0.0}
            shelves.append(home)
        x, row_y = home["x"], home["y"]
        py = row_y + band + front
        if own_band or rotated:
            lx, ly = x, row_y
        else:
            lx, ly = x, py - SCOOP_REACH + (SCOOP_REACH - LABEL_BOX_H) / 2
        depth = pocket_depth(s.t, FOAM_DEPTH_ALLOW if loop is not None else FOAM_REVEAL)
        out.append(
            Pocket(
                tool_id=r.id, name=r.name, label=lab, kind=r.kind, rule=s.rule,
                l=s.l, w=s.w, t=s.t,
                x=x, y=py, pw=pw, pd=pd,
                depth=depth, rotated=rotated,
                label_x=lx, label_y=ly, label_h=LABEL_H,
                loop=loop, label_full=lab_full,
            )
        )
        home["x"] = x + cell_w + WALL
        home["h"] = max(home["h"], cell_h)
    return out, (shelves[-1]["y"] + shelves[-1]["h"]) if shelves else y


def plan(key: str = TRAY_V1, d: Datums = D, rows: list[ToolRow] | None = None,
         tile: TileSpec | str | None = None, spares: list[ToolRow] | None = None) -> TrayPlan:
    """Lay one tile out: the cutter bore grid first, then the collet grid,
    then the lying pockets in shelf rows, all front to back.

    Works for any drawer key and raises for none of them. ``tile`` picks one
    of ``tiles_for(key)`` by key ("A"); None takes the first (the only one,
    for an untiled drawer). A tile whose rows are all MEASURE plans an
    empty blank, which is the honest tray for it. ``rows`` replaces the
    snapshot and ``spares`` the ADD tab, for a test or a what-if.
    """
    key = key.upper()
    spec = spec_for(key)
    tiles = tiles_for(key, d)
    if tile is None:
        ts = tiles[0]
    elif isinstance(tile, TileSpec):
        ts = tile
    else:
        hits = [t for t in tiles if t.key == tile.upper()]
        if not hits:
            raise KeyError(f"drawer {key} has no tile {tile!r}; it has {[t.key for t in tiles]}")
        ts = hits[0]
    iw, _idep, _ih = drawers.interior(spec, d)
    tile_w, tile_d = iw, ts.depth
    tile_key = ts.key or None

    notes: list[str] = []
    units = _units(key, rows, tile_key, d)
    if key == TRAY_V1:
        for sp in (read_spares() if spares is None else spares):
            if (tile_key is None or sp.tile == tile_key):
                units.extend([sp] * max(1, sp.qty))
    resolved = [(r, socket(r, spec, d)) for r in units]
    resolved = [(r, s) for r, s in resolved if s is not None]

    pockets: list[Pocket] = []
    y = MARGIN
    grid_units = [(r, s) for r, s in resolved if s.rule == "bore"]
    if grid_units or (key == TRAY_V1 and tile_key == "A"):
        got, y = _grid(BORE_ROWS, grid_units, tile_w, y, notes)
        pockets.extend(got)
    collet_units = [(r, s) for r, s in resolved if s.rule == "collet"]
    if collet_units or (key == TRAY_V1 and tile_key == "B"):
        if pockets:
            y += WALL
        got, y = _grid((COLLET_ROW,), collet_units, tile_w, y, notes)
        pockets.extend(got)
    lying = [(r, s) for r, s in resolved if s.rule in ("captured", "tube")]
    if lying:
        if pockets:
            y += WALL
        got, y = _shelf(lying, tile_w, y, notes)
        pockets.extend(got)

    used = (y + MARGIN) if pockets else 0.0
    return TrayPlan(key, ts, tile_w, tile_d, FOAM_T, tuple(pockets), used, tuple(notes))


def plan_all(key: str = TRAY_V1, d: Datums = D, rows: list[ToolRow] | None = None) -> list[TrayPlan]:
    return [plan(key, d, rows, t) for t in tiles_for(key, d)]


# ================================================================ geometry


def _stroke_wire(pts: tuple[tuple[float, float], ...]) -> Wire:
    return Polyline(*pts)


def _stroke_face(pts: tuple[tuple[float, float], ...], r: float) -> Sketch:
    """The slot the cutter leaves following a centreline: a capsule per
    segment, unioned."""
    sk: Sketch | None = None
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        ln = math.hypot(dx, dy)
        parts = [Circle(r).moved(Location((ax, ay))), Circle(r).moved(Location((bx, by)))]
        if ln > 1e-6:
            ang = math.degrees(math.atan2(dy, dx))
            parts.append(
                Rectangle(ln, 2 * r, align=(Align.MIN, Align.CENTER)).moved(
                    Location((ax, ay, 0), (0, 0, ang))
                )
            )
        for p in parts:
            sk = p if sk is None else sk + p
    return sk


def layers(p: TrayPlan) -> dict[str, list]:
    """The DXF, per layer, at Z = 0 in tile-local XY. POCKET layers carry
    faces (closed loops); the TEXT layer carries open wires, the label
    centrelines the cutter follows."""
    out: dict[str, list] = {
        "OUTLINE": list(Rectangle(p.w, p.d, align=(Align.MIN, Align.MIN)).faces()),
    }
    for pk in p.pockets:
        out.setdefault(f"POCKET_D{pk.depth:g}", []).extend(pk.outline().faces())
    text: list = []
    for pk in p.pockets:
        for s in pk.label_strokes():
            text.append(_stroke_wire(s))
    if text:
        out[f"TEXT_D{TEXT_D:g}"] = text
    return out


def build(p: TrayPlan | None = None, *, labels: bool = True) -> Part:
    """The tile: a foam slab, one pocket per unit of stock and one bore per
    ruled position, the labels milled through the top layer."""
    p = plan() if p is None else p
    part = Box(p.w, p.d, p.h, align=(Align.MIN, Align.MIN, Align.MIN))
    for name, faces in layers(p).items():
        if name == "OUTLINE" or name.startswith("TEXT_D"):
            continue
        depth = float(name[len("POCKET_D"):])
        for f in faces:
            part -= extrude(f, amount=depth).moved(Location((0, 0, p.h - depth)))
    if labels:
        r = LABEL_STROKE / 2
        for pk in p.pockets:
            for s in pk.label_strokes():
                sk = _stroke_face(s, r)
                for f in sk.faces():
                    part -= extrude(f, amount=TEXT_D).moved(Location((0, 0, p.h - TEXT_D)))
    return part


def _plane(spec: DrawerSpec, tile: TileSpec, d: Datums = D) -> Plane:
    """Tile-local to station: X across the drawer, Y from the tile's front,
    Z up from the top face of the drawer's bottom panel. The blank starts at
    the side's inner face and ``tile.y0`` behind the front's inner face."""
    x0, y0, z0 = drawers.box_origin(spec, d)
    return Plane(
        origin=(x0 + T, y0 + T + tile.y0, z0 + BOTTOM_GROOVE_Z + BOTTOM_T),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1),
    )


def place(part: Part | None = None, key: str = TRAY_V1, d: Datums = D,
          tile: TileSpec | str | None = None) -> Part:
    """One tile, sitting in its drawer in station coordinates."""
    p = plan(key, d, tile=tile)
    part = build(p) if part is None else part
    return _plane(spec_for(key), p.tile, d) * part


def placed_all(d: Datums = D, key: str = TRAY_V1) -> list[tuple[str, Part]]:
    """(label, placed part) for every tile of one drawer."""
    return [(p.label, _plane(spec_for(key), p.tile, d) * build(p)) for p in plan_all(key, d)]


# ================================================================ checks


def check_trays(d: Datums = D, rows: list[ToolRow] | None = None) -> list[str]:
    """What the D1 tiles have to be true for, plus what every tray is still
    waiting on."""
    notes: list[str] = []
    key = TRAY_V1
    spec = spec_for(key)
    iw, idep, ih = drawers.interior(spec, d)
    plans = plan_all(key, d, rows)

    # the cap, and the label rule that leans on it
    if params.CONFIDENCE.get("kaizen_top_layer_t") != "measured":
        notes.append(
            f"TOP_LAYER_T is {TOP_LAYER_T:g}, FastCap's 1/8in cap, not measured. Every label "
            f"depth (TEXT_D {TEXT_D:g}) and floor-is-white check leans on it. Calipers on the "
            "blank in hand, then params.CONFIDENCE[\"kaizen_top_layer_t\"] = \"measured\". MEASURE THIS."
        )
    white = LABEL_BIT.white(TEXT_D)
    if white < LABEL_WHITE_MIN:
        notes.append(
            f"labels with the {LABEL_BIT.name} at {TEXT_D:g} deep show {white:.2f}mm of white in a "
            f"{LABEL_STROKE:.2f} groove; the least that reads is {LABEL_WHITE_MIN:g}. Black on black: "
            "pick another LABEL_BIT."
        )
    if not LABEL_BIT.owned:
        notes.append(
            f"LABEL CUTTER, standing note. Labels are cut with the {LABEL_BIT.name} "
            f"({LABEL_BIT.source}), which the station does not own yet: {LABEL_STROKE:.2f} groove, "
            f"white across its floor, {LABEL_H:g} cap, {TEXT_D:g} deep. The pockets cut with the "
            f"#102 do not wait on it; the TEXT_D{TEXT_D:g} layer does."
        )

    if sum(p.d for p in plans) > idep + 0.1 or any(abs(p.w - iw) > 0.1 for p in plans):
        notes.append(
            f"the {key} tiles are " + " + ".join(f"{p.w:.1f} x {p.d:.1f}" for p in plans)
            + f" and the drawer's inside floor is {iw:.1f} x {idep:.1f}. The tiles are the floor; they are not."
        )

    for p in plans:
        name = p.label
        if not p.pockets:
            notes.append(f"{name} has no pockets: every row on it is MEASURE.")
            continue
        if not fits((p.w, p.d), FOAM_SHEET):
            notes.append(
                f"{name} is {p.w:.0f} x {p.d:.0f} and a Kaizen sheet is "
                f"{FOAM_SHEET[0]:.0f} x {FOAM_SHEET[1]:.0f}. It does not come off one sheet."
            )
        if p.h > ih:
            notes.append(f"{name} is {p.h:.0f}mm of foam in {ih:.0f}mm of drawer. The drawer above it will not clear.")
        if p.used_d > p.d + 1e-6:
            notes.append(
                f"{name} needs {p.used_d:.1f}mm of its {p.d:.0f}mm depth. The last rows run off the back: "
                "a wider label cutter, shorter labels, or more depth for this tile (TILE_A_D)."
            )
        tallest = max((p.h + pk.proud for pk in p.pockets), default=0.0)
        if tallest > ih - STAND_CLEAR + 1e-6:
            notes.append(
                f"the tallest tool on {name} stands {tallest:.1f}mm off the drawer bottom and the box "
                f"gives {ih:.0f} less {STAND_CLEAR:g} of air. It fouls the drawer above."
            )
        for n in p.notes:
            notes.append(f"{name}: {n}" + ("" if "no bore" in n else " Expected, and worth knowing."))
        for pk in p.pockets:
            if pk.is_bore:
                if pk.depth < TOP_LAYER_T + FOAM_REVEAL:
                    notes.append(f"{name} bore {pk.tool_id or pk.row} is {pk.depth:g} deep: its floor is not white")
                if pk.rule != "empty" and not pk.label:
                    notes.append(f"{name} bore {pk.tool_id} holds {pk.name} and carries no label: it reads as free")
                if pk.rule != "empty" and pk.tool_id and not any(
                    r.id == pk.tool_id and r.label for r in rows_for(key, rows)
                ) and pk.kind != "tube":
                    notes.append(
                        f"{name} {pk.tool_id} has no label in the Sheet; milled as {pk.label!r} off its name. "
                        "Fill the label column. Expected, and worth knowing."
                    )
                continue
            if pk.t + FOAM_REVEAL > pk.depth + 1e-6:
                notes.append(
                    f"pocket {pk.tool_id} on {name} is {pk.depth:.1f} deep for a {pk.t:.1f} thick "
                    f"tool: the {FOAM_FLOOR_MIN:.0f}mm floor cap caught it and it sits "
                    f"{pk.depth - pk.t:.1f} below the face, not {FOAM_REVEAL:.0f}. "
                    "Expected, and worth knowing before the drawer above is loaded."
                )
            if pk.depth < TOP_LAYER_T:
                notes.append(f"pocket {pk.tool_id} on {name} is {pk.depth:.1f} deep in a {TOP_LAYER_T:g}mm top layer: its floor is black")
            for e in pk.outline().edges().filter_by(GeomType.CIRCLE):
                if e.radius < POCKET_R - 1e-6:
                    notes.append(
                        f"pocket {pk.tool_id} on {name} has a {e.radius:.2f} corner the "
                        f"{POCKET_TOOL_D:g} endmill cannot cut"
                    )
                    break
        for pk in p.pockets:
            x0, y0, x1, y1 = pk.extent()
            if x0 < 0 or y0 < 0 or x1 > p.w or y1 > p.d:
                notes.append(f"pocket {pk.tool_id or pk.row} on {name} at ({pk.x:.0f}, {pk.y:.0f}) runs off the tile")
            lb = pk.label_box()
            if lb and (lb[0] < 0 or lb[1] < 0 or lb[2] > p.w or lb[3] > p.d):
                notes.append(f"label {pk.label!r} on {name} runs off the tile")
            if pk.is_bore and pk.rule != "empty":
                # the standing body must clear the tile edge and every label
                cx, cy, br = pk.x + pk.pw / 2, pk.y + pk.pd / 2, pk.body_d / 2
                if cx - br < 0 or cx + br > p.w:
                    notes.append(f"{name} {pk.tool_id}'s {pk.body_d:g} body overhangs the tile edge")
                for other in p.pockets:
                    ob = other.label_box()
                    if not ob:
                        continue
                    nx = min(max(cx, ob[0]), ob[2])
                    ny = min(max(cy, ob[1]), ob[3])
                    if math.hypot(nx - cx, ny - cy) < br - 1e-6:
                        notes.append(
                            f"{name} {pk.tool_id}'s {pk.body_d:g} body stands over the label "
                            f"{other.label!r} of {other.tool_id or 'a bore'}"
                        )

        # pocket to pocket: bores may sit closer than WALL (the ruled pitch
        # governs them); lying pockets keep WALL from everything
        for i, a in enumerate(p.pockets):
            ax0, ay0, ax1, ay1 = a.extent()
            for b in p.pockets[i + 1:]:
                bx0, by0, bx1, by1 = b.extent()
                gap_x = max(bx0 - ax1, ax0 - bx1)
                gap_y = max(by0 - ay1, ay0 - by1)
                need = LABEL_WALL if (a.is_bore and b.is_bore) else WALL
                if max(gap_x, gap_y) < need - 1e-6:
                    notes.append(
                        f"pockets {a.tool_id or a.row} and {b.tool_id or b.row} on {name} leave "
                        f"{max(gap_x, gap_y):.1f}mm of foam and need {need:g}"
                    )
        # labels keep LABEL_WALL from every pocket that is not their own
        for a in p.pockets:
            lb = a.label_box()
            if not lb:
                continue
            for b in p.pockets:
                if b is a:
                    continue
                bx0, by0, bx1, by1 = b.extent()
                gap_x = max(bx0 - lb[2], lb[0] - bx1)
                gap_y = max(by0 - lb[3], lb[1] - by1)
                if max(gap_x, gap_y) < LABEL_WALL - 1e-6:
                    notes.append(
                        f"label {a.label!r} of {a.tool_id} on {name} leaves {max(gap_x, gap_y):.1f}mm to "
                        f"pocket {b.tool_id or b.row} and needs {LABEL_WALL:g}"
                    )

    # spares: placeholder tubes until one is calipered
    if any(pk.kind == "tube" for p in plans for pk in p.pockets):
        n = sum(1 for p in plans for pk in p.pockets if pk.kind == "tube")
        notes.append(
            f"{n} spare tube pockets on tray_d1_b are cut to TUBE_1_4 {TUBE_1_4[0]:g} x {TUBE_1_4[1]:g} / "
            f"TUBE_1_8 {TUBE_1_8[0]:g} x {TUBE_1_8[1]:g}, an estimate off the starter pack's tubes. "
            "Calipers on one tube of each. MEASURE THIS."
        )

    # what is still waiting on a photo, in this drawer and in the others
    miss = skipped(key, rows, None, d)
    if miss:
        notes.append(
            f"{len(miss)} of {len(rows_for(key, rows))} {key} rows have no pocket: "
            + ", ".join(f"{r.id} ({why.split(':')[0]})" for r, why in miss)
            + ". MEASURE THIS -- photograph it on the capture sheet, submit the Form "
            "(tools/README.md), then re-export the Sheet."
        )
    for other in (s.key for s in DRAWERS if s.key != key):
        om = skipped(other, rows, None, d)
        if om:
            notes.append(
                f"{len(om)} of {len(rows_for(other, rows))} {other} rows have no pocket; "
                f"the {other} tray cuts the day they are photographed. MEASURE THIS."
            )

    return notes


# ================================================================ export


def export(key: str = TRAY_V1, d: Datums = D, out_dir: Path | None = None,
           tile: TileSpec | str | None = None) -> list[Path]:
    """STEP of one tile for Fusion and the assembly; DXF for Carbide Create
    with the pockets on depth-named layers and the labels as centrelines.
    No STL: the trays are milled."""
    p = plan(key, d, tile=tile)
    part = build(p)
    out_dir = out_dir or EXPORT_DIR
    return export_part(part, p.label, layers=layers(p), out_dir=out_dir)


def export_all(key: str = TRAY_V1, d: Datums = D, out_dir: Path | None = None) -> list[Path]:
    out: list[Path] = []
    for t in tiles_for(key, d):
        out.extend(export(key, d, out_dir, t))
    return out


def _sample(face: Face, tol: float = 0.2) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for e in face.outer_wire().edges():
        if e.geom_type == GeomType.LINE:
            n = 1
        else:
            n = max(int(e.length / tol), 8)
        for i in range(n):
            q = e.position_at(i / n)
            pts.append((q.X, q.Y))
    return pts


def preview_svg(p: TrayPlan, path: Path, scale: float = 4.0) -> Path:
    """The tile as the shop will see it from above: black foam, white
    pocket floors, white label grooves, grey ghosts of the standing bodies,
    a faint outline round every free bore. Plain SVG, no library."""
    W, H = p.w * scale, p.d * scale
    pad = 8 * scale
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + 2 * pad:.0f}" height="{H + 2 * pad + 14 * scale:.0f}" '
        f'viewBox="0 0 {W + 2 * pad:.0f} {H + 2 * pad + 14 * scale:.0f}">',
        f'<rect width="100%" height="100%" fill="#d9d4c7"/>',
        f'<g transform="translate({pad:.1f},{pad + H:.1f}) scale({scale},{-scale})">',
        f'<rect x="0" y="0" width="{p.w}" height="{p.d}" fill="#141414" stroke="#888" stroke-width="0.3"/>',
    ]
    for pk in p.pockets:
        for f in pk.outline().faces():
            pts = _sample(f)
            d_ = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
            fill = "#f4f1ea" if pk.rule != "empty" else "#cfcac0"
            out.append(f'<polygon points="{d_}" fill="{fill}"/>')
        if pk.is_bore and pk.rule != "empty" and pk.body_d > pk.bore_d + 0.5:
            out.append(
                f'<circle cx="{pk.x + pk.pw / 2:.2f}" cy="{pk.y + pk.pd / 2:.2f}" r="{pk.body_d / 2:.2f}" '
                f'fill="none" stroke="#7a7a7a" stroke-width="0.4" stroke-dasharray="1,1"/>'
            )
        for s in pk.label_strokes():
            d_ = " ".join(f"{x:.2f},{y:.2f}" for x, y in s)
            out.append(
                f'<polyline points="{d_}" fill="none" stroke="#f4f1ea" stroke-width="{LABEL_STROKE:.2f}" '
                'stroke-linecap="round" stroke-linejoin="round"/>'
            )
    out.append("</g>")
    out.append(
        f'<text x="{pad:.0f}" y="{H + 2 * pad + 10 * scale:.0f}" font-family="Helvetica, Arial, sans-serif" '
        f'font-size="{7 * scale:.0f}" fill="#333">{p.label}  {p.w:g} x {p.d:g} x {p.h:g} Kaizen  '
        f'{p.bores} bores ({p.filled} filled; grey = free)  labels {LABEL_BIT.name} {LABEL_H:g} cap, TEXT_D{TEXT_D:g}  '
        f'used {p.used_d:.0f} of {p.d:g}</text>'
    )
    out.append("</svg>")
    path.write_text("\n".join(out), encoding="utf-8")
    return path


# ================================================================ report


if __name__ == "__main__":
    d = DATUMS
    print("label cutter candidates (depth, groove at the face, white below the cap, cap height):")
    for name, depth, groove, white, cap, owned in label_bit_table():
        mark = "  <-- LABEL_BIT" if name == LABEL_BIT.name else ""
        print(f"    {name:<5} {depth:4.1f} deep   groove {groove:4.2f}   white {white:4.2f}   cap {cap:4.1f}"
              f"   {'owned' if owned else 'to buy'}{mark}")
    print()
    for spec in DRAWERS:
        key = spec.key
        iw, idep, ih = drawers.interior(spec, d)
        for p in plan_all(key, d):
            print(
                f"{p.label} ({spec.callout}): {p.w:.1f} x {p.d:.1f} x {p.h:.1f} foam "
                f"at y {p.tile.y0:.0f} on a {iw:.1f} x {idep:.1f} floor under {ih:.0f}mm of drawer, "
                f"{len(p.pockets)} pockets ({p.bores} bores, {p.filled} filled) from "
                f"{len(rows_for(key, tile=p.tile.key or None))} tool-list rows, "
                f"{p.used_d:.1f}mm of depth used"
            )
            for pk in p.pockets:
                if pk.is_bore:
                    print(
                        f"    {pk.tool_id or '-':<5} {pk.rule:<8} {pk.row:<14} bore {pk.bore_d:4.1f} x {pk.depth:4.1f} deep"
                        f"   at ({pk.x + pk.pw / 2:6.1f}, {pk.y + pk.pd / 2:6.1f})"
                        f"   body {pk.body_d:4.1f}  proud {pk.proud:4.1f}   {pk.label}"
                    )
                else:
                    print(
                        f"    {pk.tool_id:<5} {pk.rule:<8} box {pk.l:5.1f} x {pk.w:5.1f} x {pk.t:5.1f}"
                        f"   pocket {pk.pw:5.1f} x {pk.pd:5.1f} x {pk.depth:4.1f} deep"
                        f"   at ({pk.x:6.1f}, {pk.y:6.1f}){'  rotated' if pk.rotated else ''}"
                        f"   {pk.label}"
                    )
            for n in p.notes:
                print(f"  note: {n}")
        miss = skipped(key)
        print(f"  {len(miss)} {key} row(s) with no pocket:")
        for r, why in miss:
            print(f"    {r.id:<5} {r.name:<55} {why}")
        print()

    found = check_trays(d)
    if found:
        print(f"{len(found)} tray note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("no tray constraint violations")

    for path in export_all(TRAY_V1, d):
        print(f"wrote {path}")
    for p in plan_all(TRAY_V1, d):
        print(f"wrote {preview_svg(p, EXPORT_DIR / f'{p.label}.svg')}")
