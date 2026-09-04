"""Fitted trays, generated from the tool list rather than drawn pocket by pocket.

The brief's rule, verbatim: "Every tray is a parametric part in the same
build123d model as the carcass, generated from a tool list. Adding a cutter to
the list regenerates the tray. That is the only version of this that survives
contact with a school."

So this module hardcodes no tool. It reads
``stations/cnc_shapeoko/tools/tool_list.csv`` -- a committed snapshot of the
canonical Google Sheet, per that directory's README -- and lays out one socket
per unit of stock. The CSV is the input and it is never written to from here.

v1 CUTS ONE TRAY, FOR DRAWER 1
==============================

``TRAY_V1`` is D1 because D1 is the only drawer whose contents are dimensioned:
10 of the list's 46 rows carry ``dims_status=ok`` and all 10 are in D1. The
other 36 are ``MEASURE`` -- they exist, they are stock, nobody has put calipers
on them yet -- and a row without dimensions cannot become a pocket that fits.

MEASURE ROWS ARE NOT DROPPED. They are skipped, counted, and printed by id and
name, because a tool that quietly fails to appear in its own tray is a tool
nobody notices is homeless. ``check_trays`` carries the same count so the
station's one check command reports it too.

D2 and D3 are out of scope for v1 and the hook is ``plan()``, which takes a
drawer key and works for any of them the moment their rows are measured. What
those two will additionally need is a socket rule per kind: this file knows how
to hold a round shank (``cutter``) and a collet body (``collet``), and D2/D3 are
mostly ``block``, ``hex`` and ``wrench``, which are not round and want a milled
cavity from a bounding box rather than a bore. ``SOCKET_RULES`` is where that
goes, and ``skipped()`` already reports every row that falls off the end of it.


THE SOCKET
==========

A cutter stands SHANK DOWN, flutes up: the edge is the expensive part and the
part you need to read. The bore is the shank plus ``SOCKET_CLEAR_D`` on
diameter, because an FDM hole comes out undersize and a tray you have to ream
is a tray that gets left on the bench.

Depth is ``min(oal * (1 - PROUD_MIN_FRAC), SOCKET_DEPTH_MAX)``, so every tool
stands at least a third of its length proud and no bore is deeper than one grid
module. Both halves matter. The proud third is what fingers get hold of; the
cap is what stops a 63.5mm endmill setting the height of the whole tray, and it
still leaves a 3:1 bore on the shallowest shank here, which is more than enough
to hold a tool upright.

Each socket also gets a FINGER RELIEF: a second, larger bore on the operator's
side of it, centred on the socket's own rim, cut to the same depth. It opens
the front of the socket so a thumb and finger can close on the shank, and it
leaves the back half of the bore to hold the tool square.

The collet socket is the ER-16 body diameter, 17.0mm, plus the same clearance.
That number is DIN 6499 rather than a caliper reading; ``params.SOURCES`` has
the chain and says so.


THE LAYOUT
==========

One socket per lane, sockets in a column at the left of each column band, label
engraved to the right of its own socket. It reads as a list, which is the point:
the brief wants "a tray photographed at the end of a period is an inventory",
and an inventory is a list with one line missing.

Every socket centre lands on the 20mm house grid IN TRAY-LOCAL COORDINATES.
It cannot land on the station grid: the hands bay's X comes from the leg
opening, which is a tape reading, and no amount of snapping inside a drawer
changes that.


THIS TRAY PRINTS, WHICH MEANS IT IS TILED
=========================================

The README's pipeline puts fitted trays on the AD5M or the Bambu, not on the
CNC. A tray sized to D1's inside is 335 x 444mm and neither machine has a bed
that size, so ``tiles()`` splits it on grid lines into pieces that fit
``PRINT_BED_MIN`` less its margin, and the seams are chosen to fall between
sockets rather than through one. The whole tray still exports as one STEP and
one STL, because that is the thing to look at; the tiles are the things to
print.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import ceil
from pathlib import Path

from build123d import (
    Align,
    Box,
    Location,
    Part,
    Plane,
    Sketch,
    Text,
    Unit,
    export_step,
    export_stl,
    extrude,
)

from lib.house import GRID, PRINT_BED_MARGIN, PRINT_BED_MIN
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    T,
    Datums,
    bore,
    export_part,
    flat_pattern,
    snap_up,
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
    "ToolRow",
    "Socket",
    "TrayPlan",
    "read_tools",
    "rows_for",
    "skipped",
    "spec_for",
    "plan",
    "build",
    "place",
    "tiles",
    "check_trays",
    "export",
]

D: Datums = DATUMS

TOOL_LIST = Path(__file__).resolve().parents[1] / "tools" / "tool_list.csv"
"""Committed snapshot of the Sheet's TRAY tab. Read only: regenerate it by
re-exporting the Sheet, never by editing it here."""

TRAY_V1 = "D1"
"""The one drawer v1 generates a tray for. See the module docstring."""

TRAY_LABEL = f"tray_{TRAY_V1.lower()}"
"""What the tray is called in the assembly and on disk. One name, so the
component, the STEP, the STL and the tiles cannot drift apart."""


# ================================================================ parameters
# Tool facts and print facts. Neither moves when the design moves.

ER16_COLLET_OD = 17.0
"""ER-16 collet body diameter. DIN 6499 / ISO 15488, not a caliper reading;
``params.SOURCES["er16_collet_od"]`` carries the chain and the standing note
that Jared's calipers supersede it. Here rather than in params for the same
reason ``ROUTER_D`` is in carcass.py: it is a property of the tooling, not of
the station."""

SOCKET_CLEAR_D = 0.8
"""Added to every socket bore, on diameter. An FDM hole prints undersize by
roughly this much once the walls have shrunk onto it, so the printed socket
comes out at nominal and the tool drops in without a reamer."""

PROUD_MIN_FRAC = 1 / 3
"""Least of its own length a tool must stand out of its socket. Fingers."""

SOCKET_DEPTH_MAX = GRID
"""Deepest any bore goes: one grid module. Caps the tray's height against the
longest cutter on the list and still holds the smallest shank here at better
than 3:1."""

TRAY_FLOOR_T = 5.0
"""Plastic under the deepest socket."""

TRAY_FIT = 1.0
"""Clearance per side between the tray and the drawer's inside faces."""

FINGER_RELIEF_D = GRID * 0.7
FINGER_BITE = 2.0
"""The finger relief: a bore this wide, offset toward the front of the drawer
until it has eaten ``FINGER_BITE`` into the socket's front wall.

The BITE is what makes it a relief rather than a bigger hole. Centring the
relief on the socket's rim -- which is where this started -- opens exactly half
of every bore, and half of a 7.15mm bore does not hold a 6.35mm endmill
upright: the tool leans into the relief. Two millimetres of bite opens a mouth
most of the bore's width and only 2mm deep, so a finger and thumb reach the
shank down the socket's whole depth while the bore still surrounds three
quarters of it. Caught by rendering the DXF and looking at it."""

SOCKET_WALL = 4.0
"""Least plastic between a socket and its neighbour, or the tray's edge."""

LABEL_H = 4.0
LABEL_D = 0.8
LABEL_GAP = 4.0
"""Engraved label: cap height, depth, and the air between a socket's cell and
the start of its text."""

MARGIN = GRID
"""Tray edge to the first socket cell, so the layout starts on the grid."""


def _snap_up_to(mm: float, step: float) -> float:
    """Round up to an arbitrary step. ``carcass.snap_up`` is the house grid and
    stays the house grid; the tray's own height is not a grid dimension."""
    return ceil(mm / step - 1e-9) * step

STL_TOL = 0.01
STL_ANGULAR_TOL = 0.2
"""Mesh tolerance for the printed deliverable. build123d's default (0.001mm)
tessellates the engraved text into a file a slicer chokes on; 0.01mm is still
twenty-five times finer than a 0.4mm nozzle lays down."""

TRAY_H_STEP = 5.0
"""The tray's height is rounded up to this, so it is a number a person can
read off a caliper rather than the deepest socket plus a floor."""

SOCKET_RULES = ("cutter", "collet")
"""Kinds this file knows how to hold. Everything else is reported, not
invented. See the module docstring on what D2 and D3 will need here."""


# ================================================================ the list


@dataclass(frozen=True)
class ToolRow:
    """One row of the tool list, typed. Unknown numbers stay None rather than
    becoming zero, because a zero-diameter socket is a hole in a tray."""

    id: str
    name: str
    drawer: str
    kind: str
    shank_d: float | None
    cut_d: float | None
    oal: float | None
    qty: int
    dims_status: str
    socket_note: str

    @property
    def measured(self) -> bool:
        return self.dims_status.strip().lower() == "ok"


def _num(raw: str) -> float | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def read_tools(path: Path = TOOL_LIST) -> list[ToolRow]:
    """Every row of the snapshot, in file order."""
    out: list[ToolRow] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            qty = _num(r.get("qty", "")) or 1
            out.append(
                ToolRow(
                    id=(r.get("id") or "").strip(),
                    name=(r.get("name") or "").strip(),
                    drawer=(r.get("drawer") or "").strip(),
                    kind=(r.get("kind") or "").strip(),
                    shank_d=_num(r.get("shank_d_mm", "")),
                    cut_d=_num(r.get("cut_d_mm", "")),
                    oal=_num(r.get("oal_mm", "")),
                    qty=int(qty),
                    dims_status=(r.get("dims_status") or "").strip(),
                    socket_note=(r.get("socket_note") or "").strip(),
                )
            )
    return out


def rows_for(key: str, rows: list[ToolRow] | None = None) -> list[ToolRow]:
    """Every row assigned to one drawer."""
    rows = read_tools() if rows is None else rows
    return [r for r in rows if r.drawer == key]


def socket_bore(row: ToolRow) -> float | None:
    """Bore diameter for one row, or None when this file cannot hold it."""
    if row.kind == "cutter" and row.shank_d:
        return row.shank_d + SOCKET_CLEAR_D
    if row.kind == "collet":
        return ER16_COLLET_OD + SOCKET_CLEAR_D
    return None


def socket_depth(row: ToolRow) -> float | None:
    """Bore depth: at least a third of the tool proud, never over one module."""
    if not row.oal:
        return None
    return min(row.oal * (1 - PROUD_MIN_FRAC), SOCKET_DEPTH_MAX)


def label_text(row: ToolRow) -> str:
    """Name, plus the numbers a person needs at the drawer rather than at the
    sheet. Flutes would go here too; this snapshot has no flute column, so
    nothing is invented to fill one."""
    bits = [row.name]
    if row.cut_d:
        bits.append(f"cut {row.cut_d:g}")
    return "  ".join(bits)


def skipped(key: str, rows: list[ToolRow] | None = None) -> list[tuple[ToolRow, str]]:
    """(row, why) for every row of this drawer that gets no socket."""
    out: list[tuple[ToolRow, str]] = []
    for r in rows_for(key, rows):
        if not r.measured:
            out.append((r, "no socket yet: MEASURE"))
        elif r.kind not in SOCKET_RULES:
            out.append((r, f"no socket yet: no rule for kind {r.kind!r}"))
        elif socket_bore(r) is None or socket_depth(r) is None:
            out.append((r, "no socket yet: dims_status says ok but a number is missing"))
    return out


# ================================================================ the plan


@dataclass(frozen=True)
class Socket:
    """One bore, its finger relief and its label, in tray-local XY."""

    tool_id: str
    name: str
    label: str
    kind: str
    bore_d: float
    depth: float
    cx: float
    cy: float
    label_x: float

    @property
    def bite(self) -> float:
        """How far the relief eats into this socket's front wall.

        Clamped to a quarter of the bore's diameter, so the bore always keeps
        three quarters of its circumference no matter how small the shank is.
        On the 3.175mm shanks a flat 2mm bite reaches past the bore's own
        centre, and a tool in a socket that is more than half open leans."""
        return min(FINGER_BITE, self.bore_d / 4)

    @property
    def relief_cy(self) -> float:
        """Centre of the finger relief, toward the front of the drawer, offset
        so the relief cuts ``bite`` into the socket's front wall."""
        return self.cy - (self.bore_d / 2 + FINGER_RELIEF_D / 2 - self.bite)

    def keepout(self, label_w: float) -> tuple[tuple[float, float], tuple[float, float]]:
        """((x0, x1), (y0, y1)) that no tile seam may cross: bore, relief and
        label together."""
        r = self.bore_d / 2
        fr = FINGER_RELIEF_D / 2
        return (
            (self.cx - max(r, fr), self.label_x + label_w),
            (min(self.cy - r, self.relief_cy - fr), self.cy + r),
        )


@dataclass(frozen=True)
class TrayPlan:
    key: str
    w: float
    d: float
    h: float
    sockets: tuple[Socket, ...]
    label_w: float
    cell_w: float
    col_w: float
    lane_h: float
    cols: int


def _text(txt: str) -> Sketch:
    return Text(
        txt,
        font_size=LABEL_H,
        font=drawers.CALLOUT_FONT,
        align=(Align.MIN, Align.CENTER),
    )


def _text_width(txt: str) -> float:
    bb = _text(txt).bounding_box()
    return bb.max.X - bb.min.X


def plan(key: str = TRAY_V1, d: Datums = D) -> TrayPlan:
    """Lay the tray out for one drawer.

    Works for any drawer key. v1 only calls it with D1, because D1 is the only
    one whose rows are measured; see the module docstring.
    """
    spec = spec_for(key)
    iw, idep, _ih = drawers.interior(spec, d)
    tray_w = iw - 2 * TRAY_FIT
    tray_d = idep - 2 * TRAY_FIT

    rows = rows_for(key)
    no_socket = {r.id for r, _why in skipped(key, read_tools())}
    units: list[ToolRow] = []
    for r in rows:
        if r.id in no_socket:
            continue
        units.extend([r] * max(1, r.qty))

    if not units:
        return TrayPlan(key, tray_w, tray_d, TRAY_FLOOR_T, (), 0.0, 0.0, 0.0, 0.0, 1)

    bores = [socket_bore(r) for r in units]
    depths = [socket_depth(r) for r in units]
    label_w = max(_text_width(label_text(r)) for r in units)

    cell_w = snap_up(max(max(bores), FINGER_RELIEF_D) + 2 * SOCKET_WALL)
    # A lane holds one socket, its relief in front of it, and a wall each end.
    # Each socket gets its OWN lane height (a 7mm cutter's lane is 30, a
    # collet's is 40) rather than every lane taking the tallest: since the
    # console narrowed D1 to one column (C12), twelve tallest-lanes ran 36mm
    # off the tray's back and the per-socket stack fits with 34 to spare.
    # Lanes snap to the HALF grid: the seam finder needs a clear grid line
    # somewhere between sockets, not a socket on every grid line, and a
    # 27mm reach snapped to 20 is 40 again. ``lane_h`` on the plan stays the
    # tallest, for anything reading it.
    lane_hs = [
        _snap_up_to(b + FINGER_RELIEF_D - min(FINGER_BITE, b / 4) + 2 * SOCKET_WALL, GRID / 2)
        for b in bores
    ]
    lane_h = max(lane_hs)
    # The column carries a socket cell, a gap, the longest label and one wall,
    # THEN snaps up to the grid. The wall is what leaves a gutter between the
    # end of one column's text and the next column's socket, and the gutter is
    # where a print seam is allowed to land. Snapping the label alone -- which
    # is what this did first -- let the text overrun its own column by the gap,
    # and then no grid line anywhere in X was clear of a socket or a word.
    col_w = snap_up(cell_w + LABEL_GAP + label_w + SOCKET_WALL)
    cols = max(1, int((tray_w - MARGIN) // col_w))

    sockets: list[Socket] = []
    per_col = ceil(len(units) / cols)
    for i, (row, bd, dep) in enumerate(zip(units, bores, depths)):
        col, lane = divmod(i, per_col)
        col_x = MARGIN + col * col_w
        lane_y = MARGIN + sum(lane_hs[col * per_col:i])
        sockets.append(
            Socket(
                tool_id=row.id,
                name=row.name,
                label=label_text(row),
                kind=row.kind,
                bore_d=bd,
                depth=dep,
                cx=col_x + cell_w / 2,
                cy=lane_y + lane_hs[i] / 2,
                label_x=col_x + cell_w + LABEL_GAP,
            )
        )

    h = _snap_up_to(max(depths) + TRAY_FLOOR_T, TRAY_H_STEP)
    return TrayPlan(
        key, tray_w, tray_d, h, tuple(sockets), label_w, cell_w, col_w, lane_h, cols
    )


def spec_for(key: str) -> DrawerSpec:
    for s in DRAWERS:
        if s.key == key:
            return s
    raise KeyError(f"no drawer with key {key!r}")


# ================================================================ geometry


def _labels(p: TrayPlan) -> Sketch | None:
    """Every label as one flat sketch at Z = 0, in tray-local XY."""
    sk = None
    for s in p.sockets:
        one = _text(s.label).moved(Location((s.label_x, s.cy, 0)))
        sk = one if sk is None else sk + one
    return sk


def build(p: TrayPlan | None = None, *, labels: bool = True) -> Part:
    """The tray: a slab, one bore and one finger relief per socket, and the
    labels engraved into the top face."""
    p = plan() if p is None else p
    part = Box(p.w, p.d, p.h, align=(Align.MIN, Align.MIN, Align.MIN))

    for s in p.sockets:
        part -= bore(
            s.cx, s.cy, s.bore_d, thickness=p.h, depth=s.depth, side="front"
        )
        part -= bore(
            s.cx,
            s.relief_cy,
            FINGER_RELIEF_D,
            thickness=p.h,
            depth=s.depth,
            side="front",
        )

    if labels:
        sk = _labels(p)
        if sk is not None:
            part -= extrude(sk, amount=LABEL_D).moved(
                Location((0, 0, p.h - LABEL_D))
            )
    return part


def _plane(spec: DrawerSpec, d: Datums = D) -> Plane:
    """Tray-local to station: X across the drawer, Y from its front, Z up from
    the top face of the drawer's bottom panel."""
    x0, y0, z0 = drawers.box_origin(spec, d)
    return Plane(
        origin=(
            x0 + T + TRAY_FIT,
            y0 + T + TRAY_FIT,
            z0 + BOTTOM_GROOVE_Z + BOTTOM_T,
        ),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1),
    )


def place(part: Part | None = None, key: str = TRAY_V1, d: Datums = D) -> Part:
    """The tray, sitting in its drawer in station coordinates."""
    part = build(plan(key, d)) if part is None else part
    return _plane(spec_for(key), d) * part


# ================================================================ tiling


def seams(p: TrayPlan, span: float, axis: int) -> list[float]:
    """Cut lines along one axis that keep every tile inside the print bed.

    Walks the grid: take the furthest grid line still within a bed's reach,
    then back off one module at a time until the line misses every socket's
    keep-out. A seam through a socket is a socket that no longer holds a tool.
    """
    bed = PRINT_BED_MIN[axis] - 2 * PRINT_BED_MARGIN
    boxes = [s.keepout(p.label_w)[axis] for s in p.sockets]
    out: list[float] = []
    at = 0.0
    while span - at > bed:
        cut = at + int(bed / GRID) * GRID
        while cut > at + GRID and any(lo < cut < hi for lo, hi in boxes):
            cut -= GRID
        if cut <= at:                       # nothing legal: report, do not loop
            break
        out.append(cut)
        at = cut
    return out


def tiles(p: TrayPlan | None = None, part: Part | None = None) -> list[tuple[str, Part]]:
    """The tray cut into printable pieces, named by their row and column."""
    p = plan() if p is None else p
    part = build(p) if part is None else part
    xs = [0.0] + seams(p, p.w, 0) + [p.w]
    ys = [0.0] + seams(p, p.d, 1) + [p.d]

    out: list[tuple[str, Part]] = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            cell = Box(
                xs[i + 1] - xs[i],
                ys[j + 1] - ys[j],
                p.h,
                align=(Align.MIN, Align.MIN, Align.MIN),
            ).moved(Location((xs[i], ys[j], 0)))
            piece = part & cell
            if piece is None or piece.volume <= 0:
                continue
            out.append((f"tray_{p.key.lower()}_tile_r{j}c{i}", piece))
    return out


# ================================================================ checks


def check_trays(d: Datums = D) -> list[str]:
    """What the D1 tray has to be true for, plus what it is still waiting on."""
    notes: list[str] = []
    key = TRAY_V1
    spec = spec_for(key)
    p = plan(key, d)
    iw, idep, ih = drawers.interior(spec, d)

    if not p.sockets:
        notes.append(
            f"the {key} tray has no sockets: every row in that drawer is "
            "MEASURE THIS or has no socket rule."
        )

    if p.w > iw or p.d > idep:
        notes.append(
            f"the {key} tray is {p.w:.0f} x {p.d:.0f} into a {iw:.0f} x "
            f"{idep:.0f} drawer inside. It does not go in."
        )

    if p.h > ih:
        notes.append(
            f"the {key} tray is {p.h:.0f}mm tall in {ih:.0f}mm of drawer. "
            "The drawer above it will not clear."
        )

    # the tallest tool, standing in its socket, has to clear the box
    tallest = 0.0
    oal = {r.id: r.oal for r in rows_for(key) if r.oal}
    for s in p.sockets:
        if s.tool_id in oal:
            tallest = max(tallest, p.h + oal[s.tool_id] - s.depth)
    if tallest > ih:
        notes.append(
            f"the tallest tool in {key} stands {tallest:.0f}mm off the drawer "
            f"bottom and the box gives {ih:.0f}mm. It fouls the drawer above."
        )

    # sockets must not run into each other or off the tray
    for i, a in enumerate(p.sockets):
        if (
            a.cx - a.bore_d / 2 < 0
            or a.cx + a.bore_d / 2 > p.w
            or a.relief_cy - FINGER_RELIEF_D / 2 < 0
            or a.cy + a.bore_d / 2 > p.d
        ):
            notes.append(f"socket {a.tool_id} at ({a.cx:.0f}, {a.cy:.0f}) is off the tray")
        for b in p.sockets[i + 1:]:
            gap = ((a.cx - b.cx) ** 2 + (a.cy - b.cy) ** 2) ** 0.5
            if gap < (a.bore_d + b.bore_d) / 2 + SOCKET_WALL:
                notes.append(
                    f"sockets {a.tool_id} and {b.tool_id} are {gap:.0f}mm apart "
                    f"and need {(a.bore_d + b.bore_d) / 2 + SOCKET_WALL:.0f}"
                )

    # tiles have to fit the smallest bed in the room
    bed = (PRINT_BED_MIN[0] - 2 * PRINT_BED_MARGIN, PRINT_BED_MIN[1] - 2 * PRINT_BED_MARGIN)
    xs = [0.0] + seams(p, p.w, 0) + [p.w]
    ys = [0.0] + seams(p, p.d, 1) + [p.d]
    for i in range(len(xs) - 1):
        if xs[i + 1] - xs[i] > bed[0]:
            notes.append(
                f"{key} tray tile column {i} is {xs[i + 1] - xs[i]:.0f}mm wide "
                f"into a {bed[0]:.0f}mm bed: no grid line clears the sockets there"
            )
    for j in range(len(ys) - 1):
        if ys[j + 1] - ys[j] > bed[1]:
            notes.append(
                f"{key} tray tile row {j} is {ys[j + 1] - ys[j]:.0f}mm deep "
                f"into a {bed[1]:.0f}mm bed: no grid line clears the sockets there"
            )

    if p.h > PRINT_BED_MIN[2]:
        notes.append(f"the {key} tray is taller than the print bed's Z")

    # what is still waiting on a tape, in this drawer and in the others
    miss = skipped(key)
    if miss:
        notes.append(
            f"{len(miss)} of {len(rows_for(key))} {key} rows have no socket: "
            + ", ".join(r.id for r, _w in miss)
            + ". MEASURE THIS -- calipers, then re-export the Sheet."
        )
    others = [s.key for s in DRAWERS if s.key != key]
    rest = sum(len(skipped(k)) for k in others)
    if rest:
        notes.append(
            f"{rest} rows in {' and '.join(others)} have no socket and no tray: "
            "those trays are out of scope for v1. MEASURE THIS."
        )

    return notes


# ================================================================ export


def export(key: str = TRAY_V1, d: Datums = D, out_dir: Path | None = None) -> list[Path]:
    """STEP and STL for the whole tray, an STL per printable tile, and a DXF
    carrying the label layer.

    The trays PRINT -- README's pipeline and the brief both put fitted trays on
    the AD5M or the Bambu -- so the mesh is the deliverable and the DXF is the
    engrave-and-fill artwork, not a cut file.
    """
    p = plan(key, d)
    part = build(p)
    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"tray_{key.lower()}"    # == TRAY_LABEL for the v1 drawer
    written: list[Path] = []

    step = out_dir / f"{name}.step"
    export_step(part, step, unit=Unit.MM)
    written.append(step)

    stl = out_dir / f"{name}.stl"
    export_stl(part, stl, tolerance=STL_TOL, angular_tolerance=STL_ANGULAR_TOL)
    written.append(stl)

    for tile_name, tile in tiles(p, part):
        tp = out_dir / f"{tile_name}.stl"
        export_stl(tile, tp, tolerance=STL_TOL, angular_tolerance=STL_ANGULAR_TOL)
        written.append(tp)

    # the label layer, read off the tray WITHOUT its labels so the text does
    # not also arrive as a pocket at 0.8mm
    layers = {"CUT": flat_pattern(build(p, labels=False))["CUT"]}
    sk = _labels(p)
    if sk is not None:
        layers["ENGRAVE"] = list(sk.faces())
    written += export_part(part, name, step=False, layers=layers, out_dir=out_dir)
    return written


# ================================================================ report


if __name__ == "__main__":
    d = DATUMS
    key = TRAY_V1
    spec = spec_for(key)
    p = plan(key, d)
    rows = read_tools()
    iw, idep, ih = drawers.interior(spec, d)

    print(
        f"tray {key} ({spec.callout}): {p.w:.1f} x {p.d:.1f} x {p.h:.1f} "
        f"into a {iw:.0f} x {idep:.0f} x {ih:.0f} drawer inside, "
        f"{len(p.sockets)} sockets from {len(rows)} tool-list rows"
    )
    print(
        f"  layout: {p.cols} column(s) {p.col_w:.0f}mm wide "
        f"({p.cell_w:.0f}mm socket cell + {p.label_w:.0f}mm of label), "
        f"{p.lane_h:.0f}mm lanes"
    )
    for s in p.sockets:
        print(
            f"    {s.tool_id:<5} {s.kind:<7} bore {s.bore_d:5.2f} x "
            f"{s.depth:4.1f} deep   at ({s.cx:6.1f}, {s.cy:6.1f})"
            f"{'' if (s.cx % GRID or s.cy % GRID) else '  on grid'}   {s.label}"
        )

    miss = skipped(key)
    print(f"\n  {len(miss)} {key} row(s) with no socket:")
    for r, why in miss:
        print(f"    {r.id:<5} {r.name:<55} {why}")
    for other in (s.key for s in DRAWERS if s.key != key):
        om = skipped(other)
        print(f"\n  {len(om)} {other} row(s) with no socket (no {other} tray in v1):")
        for r, why in om:
            print(f"    {r.id:<5} {r.name:<55} {why}")

    ts = tiles(p)
    print(f"\n  {len(ts)} print tile(s) for a {PRINT_BED_MIN[0]:.0f}mm bed:")
    for tile_name, tile in ts:
        bb = tile.bounding_box()
        print(
            f"    {tile_name:<24} {bb.size.X:6.1f} x {bb.size.Y:6.1f} x "
            f"{bb.size.Z:5.1f}   {tile.volume / 1000:7.1f} cm3"
        )

    found = check_trays(d)
    if found:
        print(f"\n{len(found)} tray note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno tray constraint violations")

    for path in export(key, d):
        print(f"wrote {path}")
