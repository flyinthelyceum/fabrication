"""Birch nest and sheet count: the first-cut gate. Task C18.

    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/nest.py

WHAT IT IS
==========

Every sheet part the assembly places, laid onto the stock it is cut from, and
the count that comes out. Three materials, three nests:

    birch     every solid ``assembly.birch_components`` returns (groups
              carcass, plinth, drawer, carriage), on 2438 x 1219 4x8 Baltic
              birch at CARCASS_T.  ->  export/cnc_shapeoko/nest/sheet_NN.dxf
    acrylic   every solid in the assembly's ``acrylic`` group (the rear door's
              reveal, the console's reveal and three panes, the cradle's lip),
              on the Universal's large bed.  ->  nest/laser_NN.dxf
    foam      one Kaizen tray per drawer, from ``trays.plan``, on the 2x4 foam
              sheet.  ->  nest/foam_NN.dxf

The birch count is the number the brief (v7, "3 sheets") and the build guide
("plan five") were waiting on. It is computed here and asserted by
``check.py`` as a STANDING line, so the order and the model cannot drift apart
without the gate saying so.

WHERE THE RECTANGLES COME FROM
==============================

The nest reads the ASSEMBLY, not the export folder. ``export/`` is gitignored
and a DXF on disk is only as current as the last time somebody ran that
module; the placed solid in ``assembly.components`` is the part the gate just
checked. Each birch or acrylic component's bounding box is one sheet
thickness on one axis and the blank on the other two, so the blank is read
straight off the placed solid: no per-part table of sizes to fall out of date.

The DRAWINGS on the sheets are the parts' own: ``export()`` rebuilds each
part's flat panel through the same builder and layer derivation its module's
export uses, then checks the flat's footprint against the placed solid's
before drawing it. A flat that does not match the assembly is a registry
error here and stops the export; the count never sees it.

GREEDY, AND WHY THAT IS ENOUGH
==============================

Rectangles only, shelf-packed, first fit, biggest first. No polygon nesting:
the parts are panels with joinery on their edges, and the 10mm gap between
rectangles is the kerf and the clamp margin, not wasted material. The number
this produces is a ceiling the shop can only beat.

The machine's travel (1237 on both axes) is shorter than the sheet's 2438
length, so no 4x8 sheet goes on the Shapeoko whole. Every Shapeoko sheet
is ripped first, on the track saw, into blanks the machine can reach across:

    SHELVES run across the full 2438 width, as tall as their tallest part;
    a full-width rip lies in the gap between shelves.
    within a shelf, parts stand in COLUMNS, left to right, each column as
    wide as its first part and stacked upward with anything narrower that
    still fits under the shelf's top.
    adjacent columns are grouped into SEGMENTS whose parts span no more
    than the travel; a crosscut lies in the gap between segments.

A blank is one segment: one shelf tall, one segment long. Its parts and the
cutter around them lie within the travel on both axes (the toolpath is the
outline plus ``REACH``; the 10mm margin around the parts is clamp and kerf
the gantry never has to reach), and every rip is a straight through-cut: a
guillotine pattern the track saw can actually make. The rips are on the
sheet DXF's ``RIP`` layer. Two parts are bigger than the travel on one axis,
the deck and the top cap; those are track-saw parts by the 2026-09-02 ruling,
take a sheet each, and are flagged TRACK SAW on the printout and in the
manifest. Their sheets carry no other part (task C18: "take a sheet each");
the offcut is STRIP by house rule.

GRAIN
=====

The sheet's face grain lies along the nest's X (``GRAIN_AXIS``, the 4x8's
long edge). Whether
a part may turn on the sheet is ``grain_rule``: a standing panel whose face
is seen (walls, spine, partition, both doors) keeps its grain vertical; a
rail, a stick, a drawer box panel and the console plate keep it along their
length; everything else (hidden plates, bottoms, shelves, the track-saw
pair) may turn. None of that is measured, it is shop convention, and it is
CONFIDENCE: convention with a standing RULING WANTED line until Jared
confirms or names exceptions in ``GRAIN_OVERRIDES``.

LAYERS ON A SHEET
=================

Each part's own layers (``CUT`` / ``BACK`` / ``POCKET_<SIDE>_<d>`` /
``VCARVE`` / ``REGISTER`` / ``E_STOP``, or ``ACRYLIC``, or the tray's
``OUTLINE`` / ``POCKET_D<d>`` / ``TEXT_D<d>``) ride onto the sheet under the
same names, moved and turned with the part, so the shop reads one drawing
language on a part drawing and on a nest. A ``BACK`` feature on a nest is
seen through the material from the front exactly as it is on the part
drawing; the second fixture flips the whole blank. On top of those:

    SHEET          the stock outline
    RIP            the track-saw rips (Shapeoko sheets only)
    PART_<label>   the placed blank's rectangle, one per part, so the part's
                   name is in the layer table exactly once per placement
    LABEL          the part's name as glyph outlines inside its rectangle.
                   Reference, not a toolpath, like OUTLINE_FLIPPED.

The rear door's word is carved on its OUTSIDE face and lives in its own
flipped drawing (``rear_door_carve.dxf``, C17); a nest is the first fixture,
so the door contributes its CUT frame here and the carve stays where it is.
The console plate's ``ACRYLIC`` layer (its pane outlines) is dropped from the
birch sheet: the panes are acrylic parts and ride the laser nest.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Edge,
    ExportDXF,
    Face,
    Location,
    Part,
    Rectangle,
    Unit,
)

from lib.house import CARCASS_T, LASER_BED_LARGE, PANEL_T, SHEET_4X8, SHEET_5X5_BALTIC
from stations.cnc_shapeoko.assembly import (
    Component,
    acrylic_components,
    birch_components,
    components,
)
from stations.cnc_shapeoko.carcass import DATUMS, EXPORT_DIR, ROUTER_D, Datums, flat_pattern
from stations.cnc_shapeoko.parts import (
    base_deck,
    bay_walls,
    brain_partition,
    callouts,
    console_plate,
    drawers,
    exhaust_plenum,
    lungs_carriage,
    lungs_door,
    mains_backplate,
    rear_door,
    signal_mounts,
    spine_panel,
    stiles,
    stock_rails,
    top_cap,
    trays,
    vfd_mount,
)

__all__ = [
    "Blank",
    "Placement",
    "Sheet",
    "Nest",
    "blanks",
    "nest",
    "check_nest",
    "export",
    "main",
]

D: Datums = DATUMS


# ================================================================ parameters
# Everything specific to the nest. No dimension literal appears below this
# block; each value names where it came from.

NEST_DIR = EXPORT_DIR / "nest"
"""Where the sheets go. SOURCE: task C18 acceptance, export/cnc_shapeoko/nest/."""

SHEET = (SHEET_4X8[1], SHEET_4X8[0])
SHEET_T = CARCASS_T
"""The birch stock: 4x8 Baltic at the carcass thickness, long edge along the
nest's X so the sheet's grain lies along GRAIN_AXIS. RULED 2026-09-09: the
project nests on 4x8, not 5x5 (Spellman stocks 4x8; the workbench nests on it
too). SOURCE: lib.house, reference_spellman_hardwoods. CONFIDENCE: ruling."""

SHEET_5X5 = SHEET_5X5_BALTIC
STOCK_OVERRIDES: dict[str, tuple[float, float]] = {
    spine_panel.PART_NAME: SHEET_5X5,
}
"""Parts that do not come out of a 4x8 in their grain orientation, and the
stock they take instead. RULED 2026-09-09: the spine (1230 across its
vertical grain, against 1219 across a 4x8) is cut from ONE 5x5, its grain
neither turned nor narrowed; Spellman supplies both sizes. The 5x5 sheet is
opened first and the 4x8 pass fills what it leaves before it opens a sheet of
its own, so the 5x5 never carries the spine alone. The 5x5's face grain runs
along one edge (the mill marks it); the sheet lies with that edge along X,
the same GRAIN_AXIS as the 4x8. SOURCE: ruling; the grain edge is shop
convention. CONFIDENCE: ruling."""

LASER_BED = LASER_BED_LARGE
LASER_T = PANEL_T
"""The acrylic stock as the Universal sees it: one large bed of 3mm clear.
SOURCE: task C18 spec ("the Universal's large bed, LASER_BED_LARGE"),
lib.house. The finish ruling 2026-09-03 makes every reveal clear."""

FOAM_SHEET = trays.FOAM_SHEET
FOAM_T = trays.FOAM_T
"""One two-tone Kaizen sheet. SOURCE: trays.py, which reads the listing."""

GAP = 10.0
"""Kerf and margin: between any two rectangles, and between a rectangle and
the edge of the blank it is cut from. SOURCE: task C18 spec ("10mm
kerf/margin"). CONFIDENCE: spec. The same number serves all three nests: the
foam is cut on the same machine with the same clamps, and the laser's 0.15
kerf is lost inside it."""

REACH = ROUTER_D
"""What the gantry must reach past a part's outline on a blank: one cutter
diameter, the outline toolpath's outside edge. A blank's parts may span the
travel less this. SOURCE: carcass.ROUTER_D, the 1/4in carcass cutter.
CONFIDENCE: rule."""

GRAIN_AXIS = "X"
"""The sheet's face grain runs along the nest's X. SOURCE: convention. A 4x8's
face grain runs its 8ft length; the sheet lies long-edge-along-X before the
first rip and the drawing is right. CONFIDENCE:
convention."""

TRACK_SAW_PARTS = ("base_deck", top_cap.NAME)
"""Birch parts that do not go on the Shapeoko at all and take a sheet each.
SOURCE: ruling 2026-09-02 (carcass.check_carcass flags both: 1254 x 1089
against 1237 of travel) and task C18 ("take a sheet each, STANDING"). Any
OTHER part over the travel is a BLOCKING item here, not a third track-saw
part: the list is a ruling, not a rule."""

GRAIN_VERTICAL = (
    *(w.name for w in bay_walls.WALLS),
    spine_panel.PART_NAME,
    brain_partition.PART_NAME,
    rear_door.PART_NAME,
    lungs_door.PART_NAME,
    *stiles.labels(D),
)
"""Standing panels whose face is seen: grain runs UP the panel as it stands.
SOURCE: shop convention. CONFIDENCE: convention, RULING WANTED."""

GRAIN_LONG_PREFIXES = (
    "plinth_rail_",
    "drawer",
    bay_walls.SPACER_STEM,
    stock_rails.LABEL,
    console_plate.PART_NAME,
    console_plate.RIB_NAME,
    f"{lungs_carriage.PART_NAME}_lip",
    f"{lungs_carriage.PART_NAME}_cheek",
    signal_mounts.CHEEK_STEM,
)
"""Rails, sticks, drawer box panels and the console plate: grain runs along
the long edge. Matched by label prefix (``drawer`` covers all fifteen box
panels; a bottom's grain is invisible and along-length costs nothing).
SOURCE: shop convention. CONFIDENCE: convention, RULING WANTED."""

GRAIN_OVERRIDES: dict[str, str] = {}
"""Per-label rulings, ``label -> "vertical" | "long" | "any"``, applied over
the two lists above. Empty until Jared names one."""

LABEL_H = 12.0
LABEL_H_MIN = 3.0
LABEL_FILL = 0.8
"""The glyph label inside each placed rectangle: cap height, the smallest
worth cutting, and how much of the rectangle's shorter side or width the
label may fill before it is shrunk. SOURCE: rule, legible from a metre.
CONFIDENCE: rule. Reference layer, never a toolpath."""

FOOTPRINT_TOL = 0.5
"""How far a flat's footprint may differ from the placed solid's before the
export refuses to draw it. SOURCE: rule; the smallest real feature in the
carcass is the 0.2 dado fit. CONFIDENCE: rule."""


# ================================================================ blanks


@dataclass(frozen=True)
class Blank:
    """One part as a rectangle waiting to be placed.

    ``a`` lies along the grain when ``fixed``; ``b`` is the other edge. When
    the part may turn, ``a`` and ``b`` are just its two edges, longest first.
    """

    label: str
    material: str       # birch | acrylic | foam
    a: float
    b: float
    fixed: bool
    rule: str           # vertical | long | any | track saw
    track_saw: bool = False

    @property
    def area(self) -> float:
        return self.a * self.b

    def orientations(self) -> list[tuple[float, float]]:
        """(along X, along Y) the part may take on the sheet."""
        if self.fixed or abs(self.a - self.b) < 1e-6:
            return [(self.a, self.b)]
        return [(self.a, self.b), (self.b, self.a)]


def grain_rule(label: str) -> str:
    if label in GRAIN_OVERRIDES:
        return GRAIN_OVERRIDES[label]
    if label in TRACK_SAW_PARTS:
        return "track saw"
    if label in GRAIN_VERTICAL:
        return "vertical"
    if any(label.startswith(p) for p in GRAIN_LONG_PREFIXES):
        return "long"
    return "any"


def _sizes(c: Component) -> tuple[float, float, float]:
    bb = c.bbox
    return (bb.size.X, bb.size.Y, bb.size.Z)


def blank_from_component(c: Component, material: str, t: float) -> Blank:
    """The rectangle a placed sheet part is cut from, off its bounding box:
    the axis one thickness long is the thickness, the other two are the
    blank. A standing panel's vertical edge is its Z extent."""
    sz = _sizes(c)
    thick = min(range(3), key=lambda i: abs(sz[i] - t))
    if abs(sz[thick] - t) > FOOTPRINT_TOL:
        raise ValueError(
            f"{c.label}: no axis of {sz[0]:.1f} x {sz[1]:.1f} x {sz[2]:.1f} is "
            f"{t:.1f} thick; it is not a {material} sheet part"
        )
    edges = [sz[i] for i in range(3) if i != thick]
    rule = grain_rule(c.label)
    if rule == "vertical" and thick != 2:
        horizontal = [sz[i] for i in range(3) if i not in (thick, 2)][0]
        return Blank(c.label, material, sz[2], horizontal, True, rule)
    if rule == "long":
        return Blank(c.label, material, max(edges), min(edges), True, rule)
    if rule == "vertical":
        # a lying panel has no vertical edge; fall back to along-length
        return Blank(c.label, material, max(edges), min(edges), True, "long")
    return Blank(
        c.label, material, max(edges), min(edges), False, rule,
        track_saw=c.label in TRACK_SAW_PARTS,
    )


def blanks(comps: list[Component] | None = None, d: Datums = D) -> list[Blank]:
    """Every rectangle the three nests place: birch and acrylic off the
    assembly, foam off the tray plans."""
    comps = components(d) if comps is None else comps
    out: list[Blank] = []
    for c in birch_components(comps):
        out.append(blank_from_component(c, "birch", SHEET_T))
    for c in acrylic_components(comps):
        out.append(blank_from_component(c, "acrylic", LASER_T))
    for spec in drawers.DRAWERS:
        p = trays.plan(spec.key, d)
        out.append(Blank(f"tray_{spec.key.lower()}", "foam", max(p.w, p.d), min(p.w, p.d), False, "any"))
    return out


# ================================================================ the packer


@dataclass
class Placement:
    blank: Blank
    sheet: int          # 1-based
    x: float
    y: float
    along_x: float
    along_y: float
    shelf: int
    segment: int

    @property
    def x1(self) -> float:
        return self.x + self.along_x

    @property
    def y1(self) -> float:
        return self.y + self.along_y


@dataclass
class Column:
    x: float
    w: float                    # the first part's width: the column's blank
    y: float                    # next free y in the stack
    segment: int


@dataclass
class Shelf:
    y: float
    h: float
    x: float                    # next free x for a new column
    columns: list[Column] = field(default_factory=list)
    seg_x0: float = 0.0         # first part x of the current segment
    segments: int = 1
    rips: list[float] = field(default_factory=list)   # crosscut x positions


@dataclass
class Sheet:
    index: int
    material: str
    kind: str                   # TRACK SAW | SHAPEOKO | LASER | FOAM
    size: tuple[float, float]
    travel: float | None        # longest part span the machine reaches; None = whole sheet
    shelves: list[Shelf] = field(default_factory=list)
    placements: list[Placement] = field(default_factory=list)

    @property
    def used_area(self) -> float:
        return sum(p.along_x * p.along_y for p in self.placements)

    @property
    def fill(self) -> float:
        return self.used_area / (self.size[0] * self.size[1])

    @property
    def blanks(self) -> int:
        return sum(sh.segments for sh in self.shelves)

    def rips(self) -> list[Edge]:
        """The track-saw lines: one full-width rip in the gap above every
        shelf but the first, and every crosscut, drawn as edges."""
        out: list[Edge] = []
        w, _h = self.size
        for i, sh in enumerate(self.shelves):
            if i:
                y = sh.y - GAP / 2
                out.append(Edge.make_line((0, y, 0), (w, y, 0)))
            for x in sh.rips:
                out.append(Edge.make_line((x, sh.y - GAP / 2, 0), (x, sh.y + sh.h + GAP / 2, 0)))
        return out

    # -- placement ---------------------------------------------------------

    def _place(self, b: Blank, sh: Shelf, col: Column, ax: float, ay: float) -> Placement:
        p = Placement(b, self.index, col.x, col.y, ax, ay, self.shelves.index(sh), col.segment)
        col.y += ay + GAP
        self.placements.append(p)
        return p

    def _new_column(self, b: Blank, sh: Shelf, ax: float, ay: float) -> Placement | None:
        W, _H = self.size
        if ay > sh.h or sh.x + ax + GAP > W:
            return None
        if self.travel is not None and (sh.x + ax) - sh.seg_x0 + REACH > self.travel:
            # start a new segment: the crosscut lies in this gap
            sh.rips.append(sh.x - GAP / 2)
            sh.seg_x0 = sh.x
            sh.segments += 1
        col = Column(sh.x, ax, sh.y, sh.segments)
        sh.columns.append(col)
        sh.x += ax + GAP
        return self._place(b, sh, col, ax, ay)

    def try_place(self, b: Blank) -> Placement | None:
        W, H = self.size
        if self.travel is not None and max(b.a, b.b) + REACH > self.travel:
            return None
        # 1. on top of an existing column, under its shelf's top
        for ax, ay in b.orientations():
            for sh in self.shelves:
                for col in sh.columns:
                    if ax <= col.w and col.y + ay <= sh.y + sh.h:
                        return self._place(b, sh, col, ax, ay)
        # 2. a new column on an existing shelf
        for ax, ay in b.orientations():
            for sh in self.shelves:
                p = self._new_column(b, sh, ax, ay)
                if p:
                    return p
        # 3. a new shelf, in the part's preferred orientation
        for ax, ay in b.orientations():
            y = (self.shelves[-1].y + self.shelves[-1].h + GAP) if self.shelves else GAP
            if GAP + ax + GAP > W or y + ay + GAP > H:
                continue
            sh = Shelf(y, ay, GAP, seg_x0=GAP)
            self.shelves.append(sh)
            return self._new_column(b, sh, ax, ay)
        return None


@dataclass
class Nest:
    sheets: list[Sheet]
    unplaced: list[Blank]

    def by_material(self, material: str) -> list[Sheet]:
        return [s for s in self.sheets if s.material == material]

    def placements(self) -> list[Placement]:
        return [p for s in self.sheets for p in s.placements]


def _pack(bl: list[Blank], material: str, size: tuple[float, float], kind: str,
          travel: float | None, sheets: list[Sheet], unplaced: list[Blank],
          open_new: bool = True) -> list[Blank]:
    """First fit, biggest first, onto the open sheets of one material and
    size; a new sheet when none takes the part. With ``open_new`` False no
    sheet is opened and the parts nothing took come back instead of going
    to ``unplaced``: that is how a later stock fills an earlier one's
    remainder."""
    order = sorted(bl, key=lambda b: (-max(b.a, b.b), -b.area, b.label))
    left: list[Blank] = []
    for b in order:
        placed = None
        for s in sheets:
            if s.material != material or s.kind != kind or s.size != size:
                continue
            placed = s.try_place(b)
            if placed:
                break
        if placed:
            continue
        if not open_new:
            left.append(b)
            continue
        s = Sheet(len(sheets) + 1, material, kind, size, travel)
        sheets.append(s)
        if s.try_place(b) is None:
            sheets.pop()
            unplaced.append(b)
    return left


def nest(bl: list[Blank] | None = None, comps: list[Component] | None = None,
         d: Datums = D) -> Nest:
    """The three nests, birch first (its sheets are numbered first)."""
    bl = blanks(comps, d) if bl is None else bl
    travel = min(d.s.travel_x, d.s.travel_y)
    sheets: list[Sheet] = []
    unplaced: list[Blank] = []

    birch = [b for b in bl if b.material == "birch"]
    # the ruling's track-saw pair, a sheet each, before anything is packed
    for b in sorted((b for b in birch if b.track_saw), key=lambda b: b.label):
        s = Sheet(len(sheets) + 1, "birch", "TRACK SAW", SHEET, None)
        sheets.append(s)
        if s.try_place(b) is None:
            sheets.pop()
            unplaced.append(b)
    shapeoko = [b for b in birch if not b.track_saw]
    # anything else over the travel cannot be placed at all; say so, do not
    # quietly promote it to the track saw
    for b in shapeoko:
        if max(b.a, b.b) + REACH > travel:
            unplaced.append(b)
    shapeoko = [b for b in shapeoko if b not in unplaced]
    # the parts ruled onto another stock open their sheets first; the 4x8
    # pass fills what those sheets have left before it opens its own
    for size in sorted(set(STOCK_OVERRIDES.values())):
        _pack([b for b in shapeoko if STOCK_OVERRIDES.get(b.label) == size],
              "birch", size, "SHAPEOKO", travel, sheets, unplaced)
    rest = [b for b in shapeoko if b.label not in STOCK_OVERRIDES]
    for size in sorted(set(STOCK_OVERRIDES.values())):
        rest = _pack(rest, "birch", size, "SHAPEOKO", travel, sheets, unplaced,
                     open_new=False)
    _pack(rest, "birch", SHEET, "SHAPEOKO", travel, sheets, unplaced)

    _pack([b for b in bl if b.material == "acrylic"], "acrylic", LASER_BED, "LASER", None,
          sheets, unplaced)
    _pack([b for b in bl if b.material == "foam"], "foam", FOAM_SHEET, "FOAM", travel,
          sheets, unplaced)
    return Nest(sheets, unplaced)


# ================================================================ checks


def check_nest(comps: list[Component] | None = None, d: Datums = D) -> list[str]:
    """The count as a standing line, and anything that stops the count from
    being the whole story."""
    comps = components(d) if comps is None else comps
    notes: list[str] = []
    try:
        bl = blanks(comps, d)
    except ValueError as e:
        return [f"nest cannot read a blank: {e}"]
    n = nest(bl, comps, d)
    travel = min(d.s.travel_x, d.s.travel_y)

    for b in n.unplaced:
        if b.material == "birch":
            notes.append(
                f"nest: {b.label} is {b.a:.0f} x {b.b:.0f} and has no place on a "
                f"{_stock_name(STOCK_OVERRIDES.get(b.label, SHEET))} sheet in its grain "
                f"orientation within "
                f"{travel:.0f}mm of travel, and it is not on the track-saw ruling "
                f"({', '.join(TRACK_SAW_PARTS)}). It has no sheet."
            )
        elif b.material == "acrylic":
            notes.append(
                f"nest: {b.label} is {b.a:.0f} x {b.b:.0f} and does not fit "
                f"LASER_BED_LARGE {LASER_BED[0]:.0f} x {LASER_BED[1]:.0f}"
            )
        else:
            notes.append(
                f"nest: {b.label} is {b.a:.0f} x {b.b:.0f} and does not fit a Kaizen "
                f"sheet {FOAM_SHEET[0]:.0f} x {FOAM_SHEET[1]:.0f}"
            )

    # A blank the nest placed and ``flats`` has no drawing for is a part the
    # sheet count includes and the DXF export cannot write. ``export`` raises
    # on it; the gate has to see it first, because the count going up is not
    # the same as the file existing. (Found 2026-09-04 by the plenum.)
    reg = flats(d)
    missing = sorted({p.blank.label for p in n.placements() if p.blank.label not in reg})
    if missing:
        notes.append(
            "nest: no flat drawing for " + ", ".join(missing)
            + ". The sheet count carries them and the DXF export cannot write them; "
            "register each in nest.flats."
        )

    birch = n.by_material("birch")
    track = [s for s in birch if s.kind == "TRACK SAW"]
    shap = [s for s in birch if s.kind == "SHAPEOKO"]
    n_birch = sum(len(s.placements) for s in birch)
    notes.append(
        f"nest: {_stock_count(birch)} Baltic {SHEET_T:.0f}mm, standing note. "
        f"{len(track)} TRACK SAW ({', '.join(p.blank.label for s in track for p in s.placements)}, "
        f"a sheet each by ruling 2026-09-02) + {len(shap)} Shapeoko, ripped to blanks under "
        f"{travel:.0f} on the track saw first. {n_birch} birch parts, {GAP:.0f}mm kerf/margin, "
        f"grain along {GRAIN_AXIS}, rectangles only. Replaces the brief's 3 and the guide's "
        f"5. Plus {len(n.by_material('acrylic'))} bed of 3mm clear on the Universal "
        f"({sum(len(s.placements) for s in n.by_material('acrylic'))} parts) and "
        f"{len(n.by_material('foam'))} Kaizen sheet "
        f"({sum(len(s.placements) for s in n.by_material('foam'))} trays). "
        f"Sheets in {NEST_DIR.relative_to(EXPORT_DIR.parents[1])}."
    )
    notes.append(
        "nest: GRAIN, standing note. Grain along the sheet's X; standing seen panels "
        f"({', '.join(GRAIN_VERTICAL)}) keep it vertical, rails, sticks, drawer panels and "
        "the console plate keep it along their length, the rest may turn. Shop convention, "
        "CONFIDENCE convention. RULING WANTED: confirm, or name exceptions in "
        "nest.GRAIN_OVERRIDES; the count moves only if a fixed panel turns."
    )
    return notes


# ================================================================ drawings


def flats(d: Datums = D) -> dict[str, tuple[Part | None, dict[str, list[Face]]]]:
    """``label -> (flat solid, layers)`` for every blank, built the way each
    part's own export builds them. The solid is None for a tray: its layers
    are read off the plan and the foam is never a solid here."""
    out: dict[str, tuple[Part | None, dict[str, list[Face]]]] = {}

    def add(label: str, part: Part | None, layers: dict[str, list[Face]] | None = None) -> None:
        out[label] = (part, flat_pattern(part) if layers is None else layers)

    # -- birch ----------------------------------------------------------
    add("base_deck", base_deck.build_deck())
    add("plinth_rail_front", base_deck.build_plinth_rail_x())
    add("plinth_rail_rear", base_deck.build_plinth_rail_x(grille=True))
    rail_y = base_deck.build_plinth_rail_y()
    rail_y_layers = flat_pattern(rail_y)
    for j in range(len(base_deck.Y_RAIL_CX)):
        add(f"plinth_rail_y{j}", rail_y, rail_y_layers)
    for spec, flat in zip(bay_walls.WALLS, bay_walls.build_all(d)):
        add(spec.name, flat)
    add(spine_panel.PART_NAME, spine_panel.build(d))
    add(top_cap.NAME, top_cap.build(d))
    for spec in drawers.DRAWERS:
        for label, part, _plane in drawers.panels(spec, d):
            if label.endswith("_face"):
                w, _h = drawers.face_size(spec, d)
                layers = flat_pattern(drawers.build_face(spec, d, carve=False))
                layers.update(
                    callouts.layers(
                        [drawers.callout_for(spec, d)], drawers.register_for(spec, d), width=w
                    )
                )
                add(label, part, layers)
            else:
                add(label, part)
    comb_layers = flat_pattern(stock_rails.build(d, carve=False))
    comb_layers.update(
        callouts.layers(
            stock_rails.callouts_local(d), stock_rails.register(d), width=stock_rails.rail_length(d)
        )
    )
    add(stock_rails.LABEL, stock_rails.build(d), comb_layers)
    add(brain_partition.PART_NAME, brain_partition.build(d))
    add(vfd_mount.PART_NAME, vfd_mount.build(d))
    add(mains_backplate.PART_NAME, mains_backplate.build(d))
    for label, part, _plane in lungs_carriage.panels(d):
        add(label, part)
    for label, part, _plane in exhaust_plenum.panels(d):
        add(label, part)
    plate_layers = console_plate._plate_layers(d)
    plate_layers.pop("ACRYLIC", None)      # the panes are their own acrylic parts
    add(console_plate.PART_NAME, console_plate.build_plate(d), plate_layers)
    add(console_plate.CHEEK_NAME, console_plate.build_cheek(d))
    add(console_plate.RIB_NAME, console_plate.build_rib(d))
    add(rear_door.PART_NAME, rear_door.build(d), flat_pattern(rear_door.build(d, carve=False)))
    door_layers = flat_pattern(lungs_door.build(d, carve=False))
    door_layers.update(
        callouts.layers(
            lungs_door.callouts_local(d), lungs_door.register(d), width=lungs_door.door_size(d)[0]
        )
    )
    add(lungs_door.PART_NAME, lungs_door.build(d), door_layers)
    for label in stiles.labels(d):
        add(label, stiles.build(label, d))
    for i in range(d.s.lungs_spacer_plies):
        add(f"{bay_walls.SPACER_STEM}_{i}", bay_walls.build_spacer_ply(i, d))
    add(signal_mounts.PART_NAME, signal_mounts.build(d))
    add(signal_mounts.SHELF_NAME, signal_mounts.build_shelf(d))
    cheek = signal_mounts.build_cheek(d)
    cheek_layers = flat_pattern(cheek)
    for hand in ("l", "r"):
        add(f"{signal_mounts.CHEEK_STEM}_{hand}", cheek, cheek_layers)

    # -- acrylic --------------------------------------------------------
    def acrylic(label: str, pane: Part) -> None:
        add(label, pane, {"ACRYLIC": flat_pattern(pane)["CUT"]})

    acrylic(console_plate.REVEAL_NAME, console_plate.build_reveal(d))
    for label, _dv, pane in console_plate.panes(d):
        acrylic(label, pane)
    acrylic(rear_door.REVEAL_NAME, rear_door.build_reveal(d))
    acrylic(signal_mounts.LIP_NAME, signal_mounts.build_lip(d))

    # -- foam -----------------------------------------------------------
    for spec in drawers.DRAWERS:
        p = trays.plan(spec.key, d)
        add(f"tray_{spec.key.lower()}", None, trays.layers(p))

    return out


def _layer_bbox(layers: dict[str, list[Face]]):
    lo = [float("inf")] * 2
    hi = [float("-inf")] * 2
    for faces in layers.values():
        for f in faces:
            bb = f.bounding_box()
            lo[0], lo[1] = min(lo[0], bb.min.X), min(lo[1], bb.min.Y)
            hi[0], hi[1] = max(hi[0], bb.max.X), max(hi[1], bb.max.Y)
    return lo, hi


def _rotation_for(p: Placement, layers: dict[str, list[Face]]) -> int:
    """0 or 90: which way the flat turns to lie ``along_x`` by ``along_y``.
    Refuses a flat whose footprint is not the placed solid's."""
    lo, hi = _layer_bbox(layers)
    fx, fy = hi[0] - lo[0], hi[1] - lo[1]
    if abs(fx - p.along_x) <= FOOTPRINT_TOL and abs(fy - p.along_y) <= FOOTPRINT_TOL:
        return 0
    if abs(fx - p.along_y) <= FOOTPRINT_TOL and abs(fy - p.along_x) <= FOOTPRINT_TOL:
        return 90
    raise ValueError(
        f"{p.blank.label}: the flat drawing is {fx:.1f} x {fy:.1f} and the placed solid "
        f"is {p.along_x:.1f} x {p.along_y:.1f}. The nest registry does not match the "
        "assembly; fix flats() before cutting."
    )


def _label_faces(text: str, w: float, h: float) -> list[Face]:
    """The part's name as glyphs, shrunk until it sits inside w x h."""
    size = min(LABEL_H, LABEL_FILL * min(w, h))
    if size < LABEL_H_MIN:
        return []
    sk = callouts.text_sketch(text, size)
    bb = sk.bounding_box()
    if bb.size.X > LABEL_FILL * w:
        size *= LABEL_FILL * w / bb.size.X
        if size < LABEL_H_MIN:
            return []
        sk = callouts.text_sketch(text, size)
    return list(sk.faces())


def _write_sheet(s: Sheet, reg: dict[str, tuple[Part | None, dict[str, list[Face]]]],
                 path: Path) -> None:
    ex = ExportDXF(unit=Unit.MM)
    have: set[str] = set()

    def layer(name: str) -> None:
        if name not in have:
            ex.add_layer(name, color=console_plate.LAYER_COLOUR.get(name))
            have.add(name)

    W, H = s.size
    layer("SHEET")
    ex.add_shape(Rectangle(W, H, align=(Align.MIN, Align.MIN)).faces()[0].wires(), layer="SHEET")
    if s.kind == "SHAPEOKO":
        layer("RIP")
        for e in s.rips():
            ex.add_shape(e, layer="RIP")

    for p in s.placements:
        _part, layers = reg[p.blank.label]
        rot = _rotation_for(p, layers)
        turned = {
            name: [f.rotate(Axis.Z, rot) for f in faces] for name, faces in layers.items()
        }
        lo, _hi = _layer_bbox(turned)
        shift = Location((p.x - lo[0], p.y - lo[1], 0))
        for name, faces in turned.items():
            layer(name)
            for f in faces:
                ex.add_shape(f.moved(shift).wires(), layer=name)
        tag = f"PART_{p.blank.label}"
        layer(tag)
        rect = Rectangle(p.along_x, p.along_y, align=(Align.MIN, Align.MIN)).faces()[0]
        ex.add_shape(rect.moved(Location((p.x, p.y, 0))).wires(), layer=tag)
        glyphs = _label_faces(p.blank.label, p.along_x, p.along_y)
        if glyphs:
            layer("LABEL")
            at = Location((p.x + p.along_x / 2, p.y + p.along_y / 2, 0))
            for g in glyphs:
                ex.add_shape(g.moved(at).wires(), layer="LABEL")
    ex.write(path)


def _sheet_stem(s: Sheet, i: int) -> str:
    return {"birch": "sheet", "acrylic": "laser", "foam": "foam"}[s.material] + f"_{i:02d}"


def export(n: Nest | None = None, d: Datums = D, out_dir: Path | None = None) -> list[Path]:
    """One DXF per sheet, a manifest beside them. Rebuilds every flat."""
    n = nest(d=d) if n is None else n
    out_dir = out_dir or NEST_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.dxf"):
        old.unlink()
    reg = flats(d)
    missing = [p.blank.label for p in n.placements() if p.blank.label not in reg]
    if missing:
        raise KeyError(f"nest registry has no drawing for: {', '.join(missing)}")

    written: list[Path] = []
    rows: list[dict] = []
    counters = {"birch": 0, "acrylic": 0, "foam": 0}
    for s in n.sheets:
        counters[s.material] += 1
        stem = _sheet_stem(s, counters[s.material])
        path = out_dir / f"{stem}.dxf"
        _write_sheet(s, reg, path)
        written.append(path)
        for p in s.placements:
            rows.append(
                {
                    "file": path.name,
                    "material": s.material,
                    "kind": s.kind,
                    "part": p.blank.label,
                    "x": f"{p.x:.1f}",
                    "y": f"{p.y:.1f}",
                    "along_x": f"{p.along_x:.1f}",
                    "along_y": f"{p.along_y:.1f}",
                    "grain": p.blank.rule,
                    "shelf": p.shelf + 1,
                    "segment": p.segment,
                }
            )
    manifest = out_dir / "manifest.csv"
    with manifest.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    written.append(manifest)
    return written


# ================================================================ report


def _stock_name(size: tuple[float, float]) -> str:
    return "5x5" if size == SHEET_5X5 else "4x8"


def _stock_count(sheets: list[Sheet]) -> str:
    """``N x 4x8 + M x 5x5``: the order line, one term per stock."""
    n4 = sum(1 for s in sheets if _stock_name(s.size) == "4x8")
    n5 = sum(1 for s in sheets if _stock_name(s.size) == "5x5")
    return f"{n4} x 4x8 + {n5} x 5x5"


def report(n: Nest, d: Datums = D) -> str:
    travel = min(d.s.travel_x, d.s.travel_y)
    lines: list[str] = []
    counters = {"birch": 0, "acrylic": 0, "foam": 0}
    for s in n.sheets:
        counters[s.material] += 1
        stem = _sheet_stem(s, counters[s.material])
        flag = "  TRACK SAW" if s.kind == "TRACK SAW" else ""
        lines.append(
            f"\n{stem}  {s.material} {s.size[0]:.0f} x {s.size[1]:.0f}  {s.kind}  "
            f"{len(s.placements)} parts  {s.fill * 100:.0f}% filled{flag}"
        )
        if s.kind == "SHAPEOKO":
            lines.append(
                f"  {len(s.shelves)} shelves, {s.blanks} blanks within {travel:.0f} of "
                f"travel, {len(s.rips())} rips"
            )
        for p in s.placements:
            over = "  TRACK SAW" if p.blank.track_saw else ""
            lines.append(
                f"  {p.blank.label:28s} {p.along_x:7.1f} x {p.along_y:7.1f}  at "
                f"({p.x:7.1f}, {p.y:7.1f})  grain {p.blank.rule}{over}"
            )
    if n.unplaced:
        lines.append("\nUNPLACED:")
        for b in n.unplaced:
            lines.append(f"  {b.label}  {b.a:.0f} x {b.b:.0f}  {b.material}")
    return "\n".join(lines)


def main() -> int:
    d = D
    comps = components(d)
    bl = blanks(comps, d)
    n = nest(bl, comps, d)
    print(report(n, d))
    birch = n.by_material("birch")
    print(
        f"\nSHEET COUNT: {_stock_count(birch)} Baltic {SHEET_T:.0f}mm "
        f"({sum(1 for s in birch if s.kind == 'TRACK SAW')} track saw + "
        f"{sum(1 for s in birch if s.kind == 'SHAPEOKO')} Shapeoko), "
        f"{len(n.by_material('acrylic'))} laser bed of {LASER_T:.0f}mm clear, "
        f"{len(n.by_material('foam'))} Kaizen sheet"
    )
    for note in check_nest(comps, d):
        print(f"  - {note}")
    written = export(n, d)
    print("\nwrote:")
    for p in written:
        print(f"  {p}  {p.stat().st_size:>9,} bytes")
    return 1 if n.unplaced else 0


if __name__ == "__main__":
    sys.exit(main())
