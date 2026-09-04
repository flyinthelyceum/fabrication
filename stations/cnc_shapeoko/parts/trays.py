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
print. One-piece tray per drawer, cut from the drawer's inside floor in
``FOAM_T`` two-tone Kaizen foam, a black top layer over a white core, so an
empty pocket shows a bright floor and a missing tool reads from across the
room. The STL pipeline, the print tiles and the seam finder are gone from this
file; brackets may still print, trays do not.

THREE SOCKET RULES (spec v3, 2026-09-04)
========================================

``SOCKET_RULES = ("cutter", "collet", "captured")``. A pocket comes from one
of three places and nowhere else:

    cutter    a catalog row: ``oal_mm`` long by its largest diameter, a box.
    collet    a catalog row: ``oal_mm`` by the DIN 6499 ER-16 body, a box.
    captured  any row with ``dims_status=CAPTURED`` and a ``silhouette``:
              the tool was traced on the fiducial sheet with the TRACE
              collar, ``tools/capture_ingest.py`` recovered its outline and
              wrote ``tools/captures/T0xx.dxf``, one closed loop in mm that
              is the outline inset by the collar's radius and offset by
              ``capture_ingest.FOAM_CLEAR``. The pocket IS that loop; its
              depth is ``height_class`` (the go/no-go gauge slot the tool
              passed, 10..50) plus ``FOAM_DEPTH_ALLOW``.

The bounding-box-plus-clearance rule that took three caliper numbers is
gone: a wrench is not a box, and the trace costs a student ninety seconds.
Every pocket, whichever rule made it, gets its internal corners at the flat
endmill's radius (``POCKET_TOOL_D / 2``, the house constant; apertures round
inward) and a capsule finger scoop on its long side. Packing is by each
pocket's box: the derived box for the catalog rules, the loop's bounding box
for a capture. Foam forgives the rest.

``hex`` is a layout habit rather than a socket rule: once captured, the keys
stand long arm along the drawer's depth in a size-ordered row, and the SIZE
is the label milled through the black layer beside each, so a missing 2.5
reads as a bright hole with "2.5" over it.

WHAT A ROW NEEDS
================

``dims_status`` is one of CATALOG, CAPTURED, MEASURE. A CATALOG cutter or
collet needs ``oal_mm`` and a diameter; a CAPTURED row needs ``silhouette``
and ``height_class``; a MEASURE row needs tracing. A row that does not
resolve to a rule is SKIPPED, COUNTED and PRINTED by id and name, because a
tool that quietly fails to appear in its own tray is a tool nobody notices is
homeless. ``check_trays`` carries the same count so the station's one check
command reports it too.

D1 generates in full from its eleven CATALOG rows (twelve pockets; the #201
is stocked twice). Its wrenches, the collet nut and the inserts, and every
row of D2 (instruments, the pendant, the hex rack) and D3 (workholding), run
through the same ``plan()`` today and cut nothing until they are traced. The
moment a row carries a silhouette and a height class it has a pocket.

OUTPUT
======

One DXF per tray, importable by Carbide Create, with the geometry on layers
named by depth so the CAM reader takes depth from the layer and never from a
guess:

    OUTLINE          the tray blank, through
    POCKET_D<mm>     closed loops, pocket to that depth from the top face
    TEXT_D<mm>       label glyphs, ``TOP_LAYER_T`` plus a bite so the floor
                     reads bright; a text cutter, not the pocket endmill

plus a STEP of the tray for the assembly. No STL.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
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
    Text,
    extrude,
    make_face,
    offset,
)

from lib.house import GRID, POCKET_TOOL_D, fits
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
    "TRAY_V1",
    "TRAY_LABEL",
    "SOCKET_RULES",
    "DIMS_STATUS",
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
    "pocket_depth",
    "label_text",
    "skipped",
    "spec_for",
    "plan",
    "layers",
    "build",
    "place",
    "check_trays",
    "export",
]

D: Datums = DATUMS

TOOL_LIST = Path(__file__).resolve().parents[1] / "tools" / "tool_list.csv"
"""Committed snapshot of the Sheet's TRAY tab. Read only: regenerate it by
re-exporting the Sheet, never by editing it here."""

TRAY_V1 = "D1"
"""The drawer whose tray the assembly places. D1 is the only drawer with
dimensioned rows; ``plan()`` works for all three."""

TRAY_LABEL = f"tray_{TRAY_V1.lower()}"
"""What the tray is called in the assembly and on disk. One name, so the
component, the STEP and the DXF cannot drift apart."""


# ================================================================ parameters
# Foam facts and pocket rules. One block, a SOURCE / CONFIDENCE tag on each.

FOAM_T = 30.0
"""Kaizen foam sheet thickness. SOURCE: brief v8 BOM, "Kaizen foam, two-tone,
30mm, FastCap, 3"; FastCap Kaizen Foam 30mm B/W is listed 1-1/8in, 2 x 4 ft.
CONFIDENCE: catalog, high. The blank is not measured until it is in hand."""

TOP_LAYER_T = 5.0
"""The black top layer over the white core. SOURCE: FastCap's 30mm B/W listing
(rokhardware / fastoolnow, 2026-09-04): "1/8in (5mm) black layer on white foam".
CONFIDENCE: catalog, high on the nominal; the layer's tolerance is not
published, which is what ``TEXT_BITE`` and ``FOAM_REVEAL`` are for."""

FOAM_SHEET = (609.6, 1219.2)
"""One Kaizen sheet, 2 x 4 ft (FastCap says +/- 1in). SOURCE: the same listing.
CONFIDENCE: catalog. ``check_trays`` refuses a blank that does not come off
one sheet."""

SOCKET_RULES = ("cutter", "collet", "captured")
"""The only three ways a row gets a pocket. SOURCE: spec v3. A row that fits
none of them is reported, never guessed at."""

DIMS_STATUS = ("CATALOG", "CAPTURED", "MEASURE")
"""The ``dims_status`` vocabulary. CATALOG: the datasheet's numbers (cutters,
collets). CAPTURED: traced, silhouette on disk. MEASURE: nothing yet."""

FOAM_DEPTH_ALLOW = 2.0
"""Added to a captured tool's ``height_class`` for its pocket depth. The
class is a ceiling (a 20 is at most 20 thick), so the tool sits at least
this far below the top face. SOURCE: spec v3; the value is ``FOAM_REVEAL``'s
reasoning applied to a class instead of a caliper. CONFIDENCE: rule."""

FOAM_REVEAL = 2.0
"""The tool sits this far below the top face, and the floor sits at least this
far into the bright core. SOURCE: rule, this file. Below the surface so the
drawer above sweeps nothing off, and deep enough past the colour boundary that
a layer running thick still leaves the floor white. CONFIDENCE: rule."""

FOAM_FLOOR_MIN = 3.0
"""Least foam under any pocket. Depth is capped at ``FOAM_T`` less this and a
tool that then stands proud is reported, never cut through. SOURCE: rule.
CONFIDENCE: rule."""

POCKET_R = POCKET_TOOL_D / 2
"""Every internal corner of every pocket. SOURCE: ``lib.house.POCKET_TOOL_D``,
the #102 1/8in flat endmill. CONFIDENCE: house constant."""

SCOOP_W = GRID
SCOOP_REACH = 16.0
"""The finger scoop: a capsule ``SCOOP_W`` wide on the pocket's long side,
reaching ``SCOOP_REACH`` beyond the pocket wall at the pocket's own depth. One
grid module of width is a thumb and a finger; sixteen of reach gets them under
a tool that is sitting a reveal below the surface. SOURCE: rule.
CONFIDENCE: rule; the capsule clamps to the long side when that side is
shorter than a module."""

WALL = 6.0
"""Least foam between two pockets, or between a pocket and its neighbour's
scoop. SOURCE: rule, Kaizen practice. CONFIDENCE: rule."""

MARGIN = 10.0
"""Tray edge to the first pocket. Foam this thin at an edge tears; ten holds.
SOURCE: rule. CONFIDENCE: rule."""

LABEL_H = 4.0
LABEL_H_MIN = 2.5
LABEL_GAP = 2.0
"""Label cap height, the least it may shrink to when a name outruns its pocket,
and the air between the pocket's back wall and the text. SOURCE: rule.
CONFIDENCE: rule."""

TEXT_BITE = 0.5
TEXT_D = TOP_LAYER_T + TEXT_BITE
"""Labels are milled through the black layer and half a millimetre into the
white, so the glyph floor reads bright even when the layer runs thick.
SOURCE: rule against ``TOP_LAYER_T``. CONFIDENCE: rule."""

ER16_COLLET_OD = 17.0
"""ER-16 collet body diameter, for the collet rows' derived box. DIN 6499 /
ISO 15488, not a caliper reading; ``params.SOURCES["er16_collet_od"]`` carries
the chain and the standing note that Jared's calipers supersede it.
CONFIDENCE: standard, high."""

HEX_SIZE = re.compile(r"(\d+(?:\.\d+)?|\d+/\d+)\s*(mm|in|\")", re.IGNORECASE)
"""How a hex row's size is read off its name ("2.5mm hex key", "5/32in").
A row whose name carries no size labels with its box thickness, which for a
hex key is its across-flats."""

ARC_CHORD_TOL = 0.05
"""Chord error when a captured loop's DXF is read back and any arc in it is
sampled to points. The ingest writes lines only; this covers a hand-edited
DXF. CONFIDENCE: choice."""


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

    @property
    def status(self) -> str:
        return self.dims_status.strip().upper()

    @property
    def rule(self) -> str | None:
        """Which of ``SOCKET_RULES`` makes this row's pocket, or None."""
        if self.status == "CAPTURED" and self.silhouette and self.height_class:
            return "captured"
        if self.status == "CATALOG" and self.kind in ("cutter", "collet"):
            return self.kind
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
    """Every row of the snapshot, in file order. ``bbox_*_mm`` are the
    ingest's record of a capture's L and W and ``socket_note`` is a free
    note; neither is read here, because neither makes a pocket."""
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
    from build123d import GeomType, Wire, import_dxf

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


def rows_for(key: str, rows: list[ToolRow] | None = None) -> list[ToolRow]:
    """Every row assigned to one drawer. ``key`` is case-blind."""
    rows = read_tools() if rows is None else rows
    key = key.upper()
    return [r for r in rows if r.drawer == key]


@dataclass(frozen=True)
class Socket:
    """What one row's rule resolved to: the box the pocket packs by (L the
    longer side, W, T the tool's thickness or height class), the pocket's
    size as laid before rotation, and the loop when there is one."""

    rule: str
    l: float
    w: float
    t: float
    pw: float
    pd: float
    loop: tuple[tuple[float, float], ...] | None = None


def bbox(row: ToolRow) -> tuple[float, float, float] | None:
    """(L, W, T) for one row, or None when it has no pocket. Kept for the
    hex sort and the report; ``socket`` is what the plan uses."""
    s = socket(row)
    return None if s is None else (s.l, s.w, s.t)


_loops: dict[Path, tuple[tuple[float, float], ...]] = {}


def socket(row: ToolRow) -> Socket | None:
    """Resolve one row through ``SOCKET_RULES``. None when no rule fits or
    the rule's inputs are missing; the reason is ``skipped``'s to tell."""
    rule = row.rule
    if rule == "cutter":
        if not (row.oal and (row.shank_d or row.cut_d)):
            return None
        d = max(row.shank_d or 0.0, row.cut_d or 0.0)
        l, w, t = row.oal, d, d
    elif rule == "collet":
        if not row.oal:
            return None
        l, w, t = row.oal, ER16_COLLET_OD, ER16_COLLET_OD
    elif rule == "captured":
        path = silhouette_path(row)
        if not path.exists():
            return None
        if path not in _loops:
            _loops[path] = read_loop(path)
        loop = _loops[path]
        pw = max(p[0] for p in loop)
        pd = max(p[1] for p in loop)
        return Socket("captured", max(pw, pd), min(pw, pd), float(row.height_class), pw, pd, loop)
    else:
        return None
    if l <= 0 or w <= 0 or t <= 0:
        return None
    l, w = max(l, w), min(l, w)
    return Socket(rule, l, w, t, l, w)


def pocket_depth(t: float, allow: float = FOAM_REVEAL) -> float:
    """``max(T, TOP_LAYER_T) + allow``, capped to leave the floor. The allow
    is ``FOAM_REVEAL`` over a caliper thickness and ``FOAM_DEPTH_ALLOW`` over
    a height class."""
    return min(max(t, TOP_LAYER_T) + allow, FOAM_T - FOAM_FLOOR_MIN)


def label_text(row: ToolRow) -> str:
    """What is milled beside the pocket: a hex key's SIZE, everything else's
    name. Flute count and coating would go here too; this snapshot has no
    such columns, so nothing is invented to fill them."""
    if row.kind == "hex":
        m = HEX_SIZE.search(row.name)
        if m:
            return m.group(1) + ("" if m.group(2).lower() == "mm" else "in")
        box = bbox(row)
        return f"{box[2]:g}" if box else row.name
    return row.name


def skipped(key: str, rows: list[ToolRow] | None = None) -> list[tuple[ToolRow, str]]:
    """(row, why) for every row of this drawer that gets no pocket. Every
    reason ends the same way: trace it."""
    out: list[tuple[ToolRow, str]] = []
    for r in rows_for(key, rows):
        if r.rule is None:
            if r.status == "CATALOG":
                out.append((r, f"no pocket yet: CATALOG but no catalog rule for kind {r.kind!r}, trace it (MEASURE)"))
            elif r.status == "CAPTURED":
                out.append((r, "no pocket yet: CAPTURED but silhouette or height_class is blank, re-run the ingest (MEASURE)"))
            else:
                out.append((r, "no pocket yet: MEASURE, trace it"))
        elif socket(r) is None:
            if r.rule == "captured":
                out.append((r, f"no pocket yet: silhouette {r.silhouette} is not on disk, re-run the ingest (MEASURE)"))
            else:
                out.append((r, f"no pocket yet: CATALOG {r.kind} without oal/diameter, fill the catalog columns (MEASURE)"))
    return out


# ================================================================ the plan


@dataclass(frozen=True)
class Pocket:
    """One pocket, its scoop and its label, in tray-local XY (X across the
    drawer, Y from its front, origin at the tray's front-left corner)."""

    tool_id: str
    name: str
    label: str
    kind: str
    rule: str           # which of SOCKET_RULES made it
    l: float            # the tool's box
    w: float
    t: float
    x: float            # pocket box, min corner
    y: float
    pw: float           # pocket box, size as laid
    pd: float
    depth: float
    rotated: bool       # L along Y; scoop on the +X long side
    label_x: float      # label anchor, centred, baseline
    label_y: float
    label_h: float
    loop: tuple[tuple[float, float], ...] | None = None
    """A captured pocket's loop, pocket-local (its box's corner at 0, 0),
    before rotation. None for a box pocket."""

    @property
    def proud(self) -> float:
        """How far the tool stands above the top face. Zero unless the floor
        cap bit."""
        return max(0.0, self.t - self.depth)

    @property
    def scoop_w(self) -> float:
        long_side = self.pd if self.rotated else self.pw
        return min(SCOOP_W, long_side - 2 * POCKET_R)

    def extent(self) -> tuple[float, float, float, float]:
        """(x0, y0, x1, y1) of pocket plus scoop: what another pocket must
        keep ``WALL`` away from."""
        if self.rotated:
            return (self.x, self.y, self.x + self.pw + SCOOP_REACH, self.y + self.pd)
        return (self.x, self.y - SCOOP_REACH, self.x + self.pw, self.y + self.pd)

    def body(self) -> Sketch:
        """The pocket without its scoop, in tray XY: the box, or the captured
        loop turned to lie as the box was laid."""
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
        """The milled loop: pocket body plus half-capsule scoop, opened by
        the endmill's radius so every internal corner is what the cutter
        leaves."""
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
            cx, cy = self.x + self.pw / 2, self.y
            parts = [rect, Circle(sw / 2).moved(Location((cx, cy - stem)))]
            if stem > 0:
                parts.append(
                    Rectangle(sw, stem, align=(Align.CENTER, Align.MAX)).moved(Location((cx, cy)))
                )
        sk = parts[0]
        for p in parts[1:]:
            sk = sk + p
        return offset(offset(sk, -POCKET_R, kind=Kind.ARC), POCKET_R, kind=Kind.ARC)


@dataclass(frozen=True)
class TrayPlan:
    key: str
    w: float            # the blank: the drawer's inside floor
    d: float
    h: float            # FOAM_T
    pockets: tuple[Pocket, ...]
    used_d: float       # rear edge of the last row, plus margin


def _text(txt: str, h: float) -> Sketch:
    return Text(
        txt,
        font_size=h,
        font=drawers.CALLOUT_FONT,
        align=(Align.CENTER, Align.MIN),
    )


def _text_width(txt: str, h: float) -> float:
    bb = _text(txt, h).bounding_box()
    return bb.max.X - bb.min.X


def _fit_label(txt: str, room: float) -> tuple[str, float]:
    """Cap height, then the text, give way until the label fits its pocket."""
    w = _text_width(txt, LABEL_H)
    if w <= room:
        return txt, LABEL_H
    h = max(LABEL_H_MIN, LABEL_H * room / w)
    while txt and _text_width(txt, h) > room:
        txt = txt[:-1].rstrip()
    return txt, h


def _units(key: str, rows: list[ToolRow] | None = None) -> list[ToolRow]:
    """One entry per unit of stock, file order, the hex keys gathered into a
    size-ordered run where the first of them appeared."""
    no_pocket = {r.id for r, _why in skipped(key, rows)}
    units: list[ToolRow] = []
    hexes: list[ToolRow] = []
    hex_at: int | None = None
    for r in rows_for(key, rows):
        if r.id in no_pocket:
            continue
        if r.kind == "hex":
            if hex_at is None:
                hex_at = len(units)
            hexes.extend([r] * max(1, r.qty))
        else:
            units.extend([r] * max(1, r.qty))
    if hexes:
        hexes.sort(key=lambda r: (bbox(r)[2], bbox(r)[0]))
        units[hex_at:hex_at] = hexes
    return units


def plan(key: str = TRAY_V1, d: Datums = D, rows: list[ToolRow] | None = None) -> TrayPlan:
    """Lay one drawer's tray out: shelf rows, front to back, left to right.

    Works for any drawer key and raises for none of them. A drawer whose rows
    are all MEASURE plans an empty blank, which is the honest tray for it.
    ``rows`` replaces the snapshot, for a test or a what-if.
    """
    key = key.upper()
    spec = spec_for(key)
    iw, idep, _ih = drawers.interior(spec, d)
    tray_w, tray_d = iw, idep

    pockets: list[Pocket] = []
    x = MARGIN
    row_y = MARGIN
    row_h = 0.0
    for r in _units(key, rows):
        s = socket(r)
        l, w, t = s.l, s.w, s.t
        pw, pd = s.pw, s.pd
        loop = s.loop
        if loop is None and pw < pd:
            pw, pd = pd, pw                 # a box is laid long side along X first
        rotated = r.kind == "hex" or MARGIN + pw + MARGIN > tray_w
        if rotated:
            pw, pd = pd, pw
        if loop is None:
            pw = max(pw, POCKET_TOOL_D)        # a pocket is never narrower than its cutter
            pd = max(pd, POCKET_TOOL_D)

        label, lh = _fit_label(label_text(r), pw)
        cell_w = pw + (SCOOP_REACH if rotated else 0.0)
        cell_h = pd + LABEL_GAP + lh + (0.0 if rotated else SCOOP_REACH)

        if pockets and x + cell_w > tray_w - MARGIN:
            row_y += row_h + WALL
            row_h = 0.0
            x = MARGIN
        py = row_y + (0.0 if rotated else SCOOP_REACH)
        pockets.append(
            Pocket(
                tool_id=r.id,
                name=r.name,
                label=label,
                kind=r.kind,
                rule=s.rule,
                l=l, w=w, t=t,
                x=x, y=py, pw=pw, pd=pd,
                depth=pocket_depth(t, FOAM_DEPTH_ALLOW if loop is not None else FOAM_REVEAL),
                rotated=rotated,
                label_x=x + pw / 2,
                label_y=py + pd + LABEL_GAP,
                label_h=lh,
                loop=loop,
            )
        )
        x += cell_w + WALL
        row_h = max(row_h, cell_h)

    used = (row_y + row_h + MARGIN) if pockets else 0.0
    return TrayPlan(key, tray_w, tray_d, FOAM_T, tuple(pockets), used)


def spec_for(key: str) -> DrawerSpec:
    key = key.upper()
    for s in DRAWERS:
        if s.key == key:
            return s
    raise KeyError(f"no drawer with key {key!r}")


# ================================================================ geometry


def layers(p: TrayPlan) -> dict[str, list[Face]]:
    """The DXF, as faces per layer, at Z = 0 in tray-local XY."""
    out: dict[str, list[Face]] = {
        "OUTLINE": list(Rectangle(p.w, p.d, align=(Align.MIN, Align.MIN)).faces()),
    }
    for pk in p.pockets:
        out.setdefault(f"POCKET_D{pk.depth:g}", []).extend(pk.outline().faces())
    text: list[Face] = []
    for pk in p.pockets:
        if pk.label:
            text.extend(
                _text(pk.label, pk.label_h).moved(Location((pk.label_x, pk.label_y))).faces()
            )
    if text:
        out[f"TEXT_D{TEXT_D:g}"] = text
    return out


def build(p: TrayPlan | None = None, *, labels: bool = True) -> Part:
    """The tray: a foam slab, one pocket per unit of stock, the labels milled
    through the top layer."""
    p = plan() if p is None else p
    part = Box(p.w, p.d, p.h, align=(Align.MIN, Align.MIN, Align.MIN))
    for name, faces in layers(p).items():
        if name == "OUTLINE":
            continue
        if name.startswith("TEXT_D"):
            if not labels:
                continue
            depth = TEXT_D
        else:
            depth = float(name[len("POCKET_D"):])
        for f in faces:
            part -= extrude(f, amount=depth).moved(Location((0, 0, p.h - depth)))
    return part


def _plane(spec: DrawerSpec, d: Datums = D) -> Plane:
    """Tray-local to station: X across the drawer, Y from its front, Z up from
    the top face of the drawer's bottom panel. The blank is the inside floor,
    so it starts at the side's inner face."""
    x0, y0, z0 = drawers.box_origin(spec, d)
    return Plane(
        origin=(x0 + T, y0 + T, z0 + BOTTOM_GROOVE_Z + BOTTOM_T),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1),
    )


def place(part: Part | None = None, key: str = TRAY_V1, d: Datums = D) -> Part:
    """The tray, sitting in its drawer in station coordinates."""
    part = build(plan(key, d)) if part is None else part
    return _plane(spec_for(key), d) * part


# ================================================================ checks


def check_trays(d: Datums = D, rows: list[ToolRow] | None = None) -> list[str]:
    """What the D1 tray has to be true for, plus what every tray is still
    waiting on."""
    notes: list[str] = []
    key = TRAY_V1
    spec = spec_for(key)
    p = plan(key, d, rows)
    iw, idep, ih = drawers.interior(spec, d)

    if not p.pockets:
        notes.append(f"the {key} tray has no pockets: every row in that drawer is MEASURE.")

    if abs(p.w - iw) > 0.1 or abs(p.d - idep) > 0.1:
        notes.append(
            f"the {key} tray is {p.w:.1f} x {p.d:.1f} and the drawer's inside "
            f"floor is {iw:.1f} x {idep:.1f}. The blank is the floor; it is not."
        )

    if not fits((p.w, p.d), FOAM_SHEET):
        notes.append(
            f"the {key} tray is {p.w:.0f} x {p.d:.0f} and a Kaizen sheet is "
            f"{FOAM_SHEET[0]:.0f} x {FOAM_SHEET[1]:.0f}. It does not come off one sheet."
        )

    if p.h > ih:
        notes.append(
            f"the {key} tray is {p.h:.0f}mm of foam in {ih:.0f}mm of drawer. "
            "The drawer above it will not clear."
        )

    if p.used_d > p.d + 1e-6:
        notes.append(
            f"the {key} pockets need {p.used_d:.0f}mm of the tray's {p.d:.0f}mm "
            "depth. The last rows run off the back. Fewer tools, or D3."
        )

    # the thickest tool, lying in its pocket, has to clear the box
    tallest = max((p.h + pk.proud for pk in p.pockets), default=0.0)
    if tallest > ih:
        notes.append(
            f"the tallest tool in {key} stands {tallest:.0f}mm off the drawer "
            f"bottom and the box gives {ih:.0f}mm. It fouls the drawer above."
        )

    for pk in p.pockets:
        if pk.t + FOAM_REVEAL > pk.depth + 1e-6:
            notes.append(
                f"pocket {pk.tool_id} is {pk.depth:.1f} deep for a {pk.t:.1f} thick "
                f"tool: the {FOAM_FLOOR_MIN:.0f}mm floor cap caught it and it sits "
                f"{pk.depth - pk.t:.1f} below the face, not {FOAM_REVEAL:.0f}. "
                "Expected, and worth knowing before the drawer above is loaded."
            )
        if pk.depth < TOP_LAYER_T:
            notes.append(f"pocket {pk.tool_id} is {pk.depth:.1f} deep in a {TOP_LAYER_T:.0f}mm top layer: its floor is black")
        x0, y0, x1, y1 = pk.extent()
        if x0 < 0 or y0 < 0 or x1 > p.w or y1 > p.d:
            notes.append(f"pocket {pk.tool_id} at ({pk.x:.0f}, {pk.y:.0f}) runs off the tray")
        for e in pk.outline().edges().filter_by(GeomType.CIRCLE):
            if e.radius < POCKET_R - 1e-6:
                notes.append(
                    f"pocket {pk.tool_id} has a {e.radius:.2f} corner the "
                    f"{POCKET_TOOL_D:g} endmill cannot cut"
                )
                break

    for i, a in enumerate(p.pockets):
        ax0, ay0, ax1, ay1 = a.extent()
        for b in p.pockets[i + 1:]:
            bx0, by0, bx1, by1 = b.extent()
            gap_x = max(bx0 - ax1, ax0 - bx1)
            gap_y = max(by0 - ay1, ay0 - by1)
            if max(gap_x, gap_y) < WALL - 1e-6:
                notes.append(
                    f"pockets {a.tool_id} and {b.tool_id} leave "
                    f"{max(gap_x, gap_y):.1f}mm of foam and need {WALL:.0f}"
                )

    # what is still waiting on a trace, in this drawer and in the others
    miss = skipped(key, rows)
    if miss:
        notes.append(
            f"{len(miss)} of {len(rows_for(key, rows))} {key} rows have no pocket: "
            + ", ".join(r.id for r, _w in miss)
            + ". MEASURE THIS -- trace it on the sheet with the collar, gauge its height, "
            "submit the Form (tools/README.md), then re-export the Sheet."
        )
    for other in (s.key for s in DRAWERS if s.key != key):
        om = skipped(other, rows)
        if om:
            notes.append(
                f"{len(om)} of {len(rows_for(other, rows))} {other} rows have no pocket; "
                f"the {other} tray cuts the day they are traced. MEASURE THIS."
            )

    return notes


# ================================================================ export


def export(key: str = TRAY_V1, d: Datums = D, out_dir: Path | None = None) -> list[Path]:
    """STEP of the tray for Fusion and the assembly; DXF for Carbide Create
    with the pockets on depth-named layers. No STL: the trays are milled."""
    key = key.upper()
    p = plan(key, d)
    part = build(p)
    out_dir = out_dir or EXPORT_DIR
    name = f"tray_{key.lower()}"    # == TRAY_LABEL for the placed drawer
    return export_part(part, name, layers=layers(p), out_dir=out_dir)


# ================================================================ report


if __name__ == "__main__":
    d = DATUMS
    for spec in DRAWERS:
        key = spec.key
        p = plan(key, d)
        iw, idep, ih = drawers.interior(spec, d)
        print(
            f"tray {key} ({spec.callout}): {p.w:.1f} x {p.d:.1f} x {p.h:.1f} foam "
            f"on a {iw:.1f} x {idep:.1f} floor under {ih:.0f}mm of drawer, "
            f"{len(p.pockets)} pockets from {len(rows_for(key))} tool-list rows, "
            f"{p.used_d:.0f}mm of depth used"
        )
        for pk in p.pockets:
            print(
                f"    {pk.tool_id:<5} {pk.rule:<8} box {pk.l:5.1f} x {pk.w:5.1f} x {pk.t:5.1f}"
                f"   pocket {pk.pw:5.1f} x {pk.pd:5.1f} x {pk.depth:4.1f} deep"
                f"   at ({pk.x:6.1f}, {pk.y:6.1f}){'  rotated' if pk.rotated else ''}"
                f"   {pk.label}"
            )
        miss = skipped(key)
        print(f"  {len(miss)} {key} row(s) with no pocket (trace them):")
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

    for path in export(TRAY_V1, d):
        print(f"wrote {path}")
