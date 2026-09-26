"""Drawer inserts: full-width HDPE strips, generated from the tool list.

RULED 2026-09-25 (Jared, after the foam trays overflowed D2 and D3): "all the
cutters need to be oriented by kind and oriented standing up. and we need to
learn from the way that carbide 3d has built their holders ... we have too
much goofy shit going on." The research behind this file (tool-storage
practice, Carbide 3D's 13 holders measured off their STLs, insert materials,
a red team of the old trays and one of this design's first draft) is written
up at notes.aaand.space/cnc-drawer-inserts.html.

WHAT AN INSERT IS
=================

Each drawer holds a stack of loose STRIPS, front to back. A strip is the full
inside width of the drawer and a whole number of 25 mm modules deep (Carbide's
rack module: every one of its caddies is 25, 50, 75, 100 or 125 in plan), and
it holds one KIND of thing. The last strip in every drawer is the KEYSTONE: a
BIN strip cut to whatever depth is left, so the stack fills the drawer and
nothing slides. No fasteners, no frame. Buying a cutter re-mills one strip.

Every strip is 1/2 in two-colour HDPE (King ColorCore class, black over a
white core over black). A pocket goes through the black cap into the white,
so an EMPTY place shows white from across the room and a full one shows the
tool. That is the whole missing-tool signal; there are no free places, so an
empty one always means something is out.

HOW EACH THING IS HELD (the ``store`` column)
=============================================

    bore     a cutter or a driver standing shank down, flutes up: shank (or
             the ``hold_mm`` diameter) + BORE_CLEAR. Standing, a cutter shows
             its own diameter, so no number is milled beside it.
    collet   an ER16 collet standing nut-off in a stepped bore, a negative of
             its own flange over its waist (Carbide's collet caddies).
    cup      something round standing in a round drop-in: ``hold_mm`` + DROP.
    socket   a part standing on end in a snug rectangle, ``hold_mm`` + SNUG
             (Carbide's clamp cell: 0.4 a side).
    slot     a flat part standing on edge in a snug rectangle.
    shadow   a part lying in a pocket of its own outline: the captured loop
             (``silhouette``, 1.0 a side over the traced tool), or for a
             calipered rod with no capture its L x W + DROP.
    case     lives inside another row's case; no place of its own.
    loose    lives in its drawer's BIN.

RULED 2026-09-25 (Jared): only the cutters stand; everything else that is not
a clamp in its caddy lies in its own outline ("we shouldn't have loose pockets
for anything"). Every tool has a home in a drawer; there is no dock.

Every place is DEPTH_MAX deep, the most 12.7 stock gives with the white still
under it. One kind word per strip, V-carved through the cap; nothing else is
written. There are no scoops: a standing thing stands proud and is picked up
by its top, and a lying one sits in a shadow at most half its height, so
half of it stands proud to pinch.

A strip is laid out one of two ways. ``grid``: identical places in rows,
shelf-packed across the strip. ``interlock``: long lying tools head to tail,
alternately turned half round and slid forward until they meet WALL, so a
T-handle's shaft runs past its neighbour's handle (a driver stand laid flat).
"""

from __future__ import annotations

import csv
import itertools
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import cv2
import numpy as np
from build123d import (
    Align,
    Box,
    Circle,
    Cylinder,
    Face,
    Location,
    Part,
    Plane,
    Rectangle,
    RectangleRounded,
    Wire,
    extrude,
)

from stations.cnc_shapeoko.carcass import DATUMS, EXPORT_DIR, T, Datums, export_part
from stations.cnc_shapeoko.parts import callouts, drawers
from stations.cnc_shapeoko.parts.drawers import BOTTOM_GROOVE_Z, BOTTOM_T, DRAWERS, DrawerSpec

D: Datums = DATUMS

TOOL_LIST = Path(__file__).resolve().parents[1] / "tools" / "tool_list.csv"
"""Committed snapshot of the Sheet's TRAY tab. Read only."""

# ================================================================ stock

STOCK_T = 12.7
"""ESTIMATE. 1/2 in King ColorCore, nominal. Calipers on the sheet when it
lands; every depth below leans on it. MEASURE THIS."""

SHEET = (1219.2, 609.6)
"""The stock as bought: one 24 x 48 in sheet (King ColorCore 1/2 in, black /
white / black; Piedmont Plastics, Phoenix, stocks King). Every strip of all
three drawers nests on one."""

CAP_T = 1.27
"""The ColorCore cap, 0.050 in per King's data (materials research). The white
starts this far below the face."""

DEPTH_MAX = 11.0
"""Every place's depth: the white floor is kept 0.4 above the bottom cap, so
an empty place never shows black. Carbide's caddies go 9 to 19 deep in 20; the
red team's rule was 25 to 33 percent of standing height, and 11 in 12.7 is
the most this stock gives."""

MODULE = 25.0
"""Carbide's rack module. Strip depths are multiples of it, and it is the
least pitch between two standing cutters: a student's fingers go between
exposed flutes, and 25 is the grid the red team asked for."""

BORE_CLEAR = 0.25
"""Over a shank. Carbide's bit caddy measures +0.22 on a 1/4 shank and +0.13
to +0.27 on 1/8 (carbide_geometry.md); the bore coupon settles it."""

SNUG = 0.8
"""Over a socket's or slot's cross-section, total: 0.4 a side, the essential
clamp caddy's 20.9 cell over the clamp's 20 body."""

DROP = 2.0
"""Over a cup, or a shadow drawn from calipers, total: the captured loops'
own clearance (``capture_ingest.FOAM_CLEAR``, 1.0 a side)."""

CAPTURES = Path(__file__).resolve().parents[1] / "tools" / "captures"

RES = 0.25
"""Raster cell for the interlock layout and the checks between outlines."""

NOTCH = 6.0
"""A traced outline is closed by this radius. A notch in it narrower than 12
would leave an HDPE nub the tool has to be threaded past; a rigid tool is
lifted straight out, so the pocket ignores it (the hardware case's traced
bites were capture noise or its hinge knuckles). It also leaves every inside
corner wider than the 1/8 flat."""

WALL = 3.0
"""Least HDPE between two places across a row (Carbide's clamp cells: 2.7)."""

FINGER = 11.0
"""Extra gap in front of a row of sockets or slots, for the fingers that lift
a standing part (Carbide's clamp caddy: 12.9 cells on a 24 row pitch)."""

EDGE = 3.5
"""Least HDPE between a place and a strip's edge. Two strips abut, so two
places either side of a joint have 7 between them; Carbide's own walls are
2.7, and an ER16 collet (17.6 bore) then stands in one 25 module."""

STACK_CLEAR = 1.0
"""Total, in width and in the stack's depth: HDPE grows about 1.2e-4 per
degree, 0.45 mm over 464 at an 8 degree swing in the shop."""

HEAD_CLEAR = 10.0
"""Air between the top of anything standing and the part above the drawer."""

LABEL_H = 14.0
"""Cap height of a strip's kind word. With the #302 (60 degree) at LABEL_D the
groove is still wider than 0.5 where it passes the cap (red team, B3)."""

LABEL_D = 1.9
VBIT_HALF = math.radians(30.0)
LABEL_GAP = 6.0
LIFT_D = 16.0
"""A through hole per strip, where there is room, for the finger that lifts
the strip out."""

POCKET_R = 3.175 / 2
"""Inside corners are what the 1/8 flat leaves."""

KEYSTONE = "BIN"

# ================================================================ strips


@dataclass(frozen=True)
class StripSpec:
    name: str       # the kind word milled on it, and the tool list's strip column
    note: str
    layout: str = "grid"


STRIPS: dict[str, tuple[StripSpec, ...]] = {
    "D1": (
        StripSpec("FLAT", "flat-bottom cutters, smallest shank first; the McFly at the end"),
        StripSpec("SHEET", "sheet goods: downcut and compression"),
        StripSpec("BALL", "ball and tapered ball"),
        StripSpec("V", "V-bits, engravers, the drag knife"),
        StripSpec("COLLETS", "ER16, nut off"),
        StripSpec("WRENCHES", "the spindle and collet-nut wrenches, head to tail", "interlock"),
        StripSpec("HEX", "T-handle drivers lying, head to tail, smallest first like the cutters", "interlock"),
    ),
    "D2": (
        StripSpec("INSTRUMENTS", "things used at the machine: probe, pen, oil, deburr"),
        StripSpec("PENDANT", "the jog pendant, lying"),
        StripSpec("BOOTS", "the dust-boot parts, lying"),
    ),
    "D3": (
        StripSpec("CLAMPS", "Essential Clamps, nose down"),
        StripSpec("CRUSH-IT", "Crush-It clamps, stops and jaws"),
        StripSpec("FIXTURES", "the joinery stop on edge, the hardware case lying"),
    ),
}
"""Front to back. The keystone BIN follows the last one in every drawer. The
T-handles moved D3 -> D1 on 2026-09-25: lying, they need a 225 strip, D3 had
188 left and D1 a 338 BIN with nothing loose to hold."""

STORES = ("bore", "collet", "cup", "socket", "slot", "shadow", "case", "loose")
PLACED = ("bore", "collet", "cup", "socket", "slot", "shadow")

COLLET_STEP = ((17.6, 5.0), (13.0, DEPTH_MAX))
"""(diameter, depth) from the face: the ER16 body (17.0, ``params.SOURCES
["er16_collet_od"]``) plus 0.6 over the taper's waist, the stepped bore of
Carbide's collet caddies (red team, M5). The 13 waist is an ESTIMATE off the
DIN 6499 8-degree taper; the bore coupon settles it."""
COLLET_H = 27.5
"""The ER16 body's length, same source."""

# ================================================================ rows


def _num(raw: str | None) -> float | None:
    raw = (raw or "").strip()
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


@dataclass(frozen=True)
class Row:
    id: str
    name: str
    drawer: str
    strip: str
    store: str
    qty: int
    shank_d: float | None
    cut_d: float | None
    oal: float | None
    bbox: tuple[float | None, float | None, float | None]
    hold: tuple[float, ...]
    height_class: float | None
    status: str
    silhouette: str = ""

    @property
    def active(self) -> bool:
        return self.status.strip().lower() != "struck"


def read_rows(path: Path = TOOL_LIST) -> list[Row]:
    out: list[Row] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            hold = tuple(float(v) for v in (r.get("hold_mm") or "").lower().split("x") if v.strip())
            out.append(Row(
                id=(r.get("id") or "").strip(),
                name=(r.get("name") or "").strip(),
                drawer=(r.get("drawer") or "").strip().upper(),
                strip=(r.get("strip") or "").strip().upper(),
                store=(r.get("store") or "").strip().lower(),
                qty=int(_num(r.get("qty")) or 1),
                shank_d=_num(r.get("shank_d_mm")),
                cut_d=_num(r.get("cut_d_mm")),
                oal=_num(r.get("oal_mm")),
                bbox=(_num(r.get("bbox_l_mm")), _num(r.get("bbox_w_mm")), _num(r.get("bbox_h_mm"))),
                hold=hold,
                height_class=_num(r.get("height_class")),
                status=(r.get("status") or "active").strip() or "active",
                silhouette=(r.get("silhouette") or "").strip(),
            ))
    return out


# ================================================================ places


@dataclass(frozen=True)
class Place:
    """One held thing, strip-local: X across the drawer from the strip's left
    end, Y from its front edge. ``shape`` is "circle" (w = d = diameter),
    "rect", or "poly" (``poly``, the outline about the centre, w x d its
    box); ``steps`` is the collet's stepped bore."""

    tool_id: str
    store: str
    shape: str
    cx: float
    cy: float
    w: float
    d: float
    depth: float
    height: float       # what stands above the strip's face, plus the floor under it
    steps: tuple[tuple[float, float], ...] = ()
    poly: tuple[tuple[float, float], ...] = ()

    @property
    def box(self) -> tuple[float, float, float, float]:
        return (self.cx - self.w / 2, self.cy - self.d / 2, self.cx + self.w / 2, self.cy + self.d / 2)


@dataclass
class Group:
    """Identical places laid as a little grid: ``n`` of them, each ``fw`` x
    ``fd`` on a ``px`` x ``py`` pitch."""

    row: Row
    n: int
    fw: float
    fd: float
    px: float
    py: float
    shape: str
    depth: float
    height: float
    steps: tuple[tuple[float, float], ...] = ()
    poly: tuple[tuple[float, float], ...] = ()

    def turned(self) -> "Group":
        """Rotated a quarter turn: the finger gap and the outline turn with
        the part."""
        gx = self.px - self.fw
        gy = self.py - self.fd
        return Group(self.row, self.n, self.fd, self.fw, self.fd + gy, self.fw + gx,
                     self.shape, self.depth, self.height, self.steps,
                     tuple((-y, x) for x, y in self.poly))

    def size(self, cols: int) -> tuple[float, float, int, int]:
        """Cell footprint: every place owns a ``px`` x ``py`` cell, centred in
        it, and cells butt against their neighbours'."""
        cols = max(1, min(cols, self.n))
        rows = math.ceil(self.n / cols)
        cols = math.ceil(self.n / rows)          # balance: no straggler row
        return cols * self.px, rows * self.py, cols, rows

    @property
    def pad(self) -> tuple[float, float]:
        return (self.px - self.fw) / 2, (self.py - self.fd) / 2


def group_for(r: Row) -> Group | None:
    """The row's places as a group, or None when a measurement is missing."""
    L, W, H = r.bbox
    s = r.store
    if s == "bore":
        base = r.hold[0] if r.hold else r.shank_d
        if base is None:
            return None
        dia = base + BORE_CLEAR
        body = max(dia, r.cut_d or 0.0, r.hold[1] if len(r.hold) >= 2 else 0.0)   # a T-handle's thickness
        pitch = max(MODULE, body + 10.0)
        stand = max(r.oal or 0.0, L or 0.0)
        return Group(r, r.qty, dia, dia, pitch, MODULE, "circle", DEPTH_MAX, stand)
    if s == "collet":
        dia = COLLET_STEP[0][0]
        return Group(r, r.qty, dia, dia, max(MODULE, dia + 6.0), MODULE, "circle",
                     DEPTH_MAX, COLLET_H, COLLET_STEP)
    if s == "cup":
        if not r.hold or L is None:
            return None
        dia = r.hold[0] + DROP
        return Group(r, r.qty, dia, dia, dia + WALL, dia + WALL, "circle", DEPTH_MAX, L)
    if s == "socket":
        a, b = (r.hold[0], r.hold[1]) if len(r.hold) >= 2 else (W, H)
        if a is None or b is None or L is None:
            return None
        return Group(r, r.qty, a + SNUG, b + SNUG, a + SNUG + WALL, b + SNUG + FINGER, "rect", DEPTH_MAX, L)
    if s == "slot":
        a, b = (r.hold[0], r.hold[1]) if len(r.hold) >= 2 else (L, H)
        if a is None or b is None or W is None:
            return None
        return Group(r, r.qty, a + SNUG, b + SNUG, a + SNUG + WALL, b + SNUG + FINGER, "rect", DEPTH_MAX, W)
    if s == "shadow":
        H = H if H is not None else r.height_class      # a trace knows its slot, not its height
        loop = outline_of(r)
        if loop is None or H is None:
            return None
        fw, fd = _extent(loop)
        return Group(r, r.qty, fw, fd, fw + WALL, fd + WALL, "poly", min(DEPTH_MAX, H / 2), H, (), loop)
    return None


def _extent(pts) -> tuple[float, float]:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def _centred(pts: np.ndarray) -> np.ndarray:
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    return pts - (lo + hi) / 2


def _square(pts: np.ndarray) -> np.ndarray:
    """Turn a traced loop so its straight edges run along X and Y, its long
    side along X, its heavier end at the left. The ingest aligns a trace to
    its least-area box, which lays a T-handle's shaft on the diagonal."""
    e = np.roll(pts, -1, axis=0) - pts
    ln = np.hypot(e[:, 0], e[:, 1])
    ang = np.degrees(np.arctan2(e[:, 1], e[:, 0])) % 90.0
    tries = np.arange(0.0, 90.0, 0.25)
    off = np.abs((ang[None, :] - tries[:, None] + 45.0) % 90.0 - 45.0)
    score = (ln[None, :] * (off < 2.0)).sum(axis=1)
    k = int(np.argmax(score))
    if score[k] >= 0.3 * ln.sum():
        near = off[k] < 2.0
        a0 = tries[k] + float(np.average((ang[near] - tries[k] + 45.0) % 90.0 - 45.0, weights=ln[near]))
        a = -math.radians(a0)
        c, s_ = math.cos(a), math.sin(a)
        pts = pts @ np.array([[c, -s_], [s_, c]]).T
    w, d = np.ptp(pts, axis=0)
    if d > w:
        pts = pts @ np.array([[0.0, 1.0], [-1.0, 0.0]])
    pts = _centred(pts)
    x0, x1 = pts[:, 0].min(), pts[:, 0].max()
    band = 0.15 * (x1 - x0)
    left, right = pts[pts[:, 0] < x0 + band], pts[pts[:, 0] > x1 - band]
    if len(left) and len(right) and np.ptp(right[:, 1]) > np.ptp(left[:, 1]) * 1.2:
        pts = -pts
    return pts


def _closed(pts: np.ndarray, r: float = NOTCH, res: float = 0.1) -> np.ndarray:
    """The loop with every notch narrower than 2 r filled (a morphological
    closing on a fine raster, traced back to a polygon)."""
    lo = pts.min(axis=0) - 2 * r
    px = np.round((pts - lo) / res).astype(np.int32)
    w, h = px.max(axis=0) + int(2 * r / res) + 2
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [px], 1)
    k = int(round(r / res))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = cv2.approxPolyDP(max(cs, key=cv2.contourArea), 0.5, True)[:, 0, :]
    return c * res + lo


def outline_of(r: Row) -> tuple[tuple[float, float], ...] | None:
    """The shadow's loop about its box centre, squared up: the capture's
    POCKET loop, or a calipered rod's L x W + DROP."""
    if r.silhouette:
        path = CAPTURES / Path(r.silhouette).name
        if not path.exists():
            return None
        import ezdxf
        pts = np.array([(e.dxf.start.x, e.dxf.start.y) for e in ezdxf.readfile(str(path)).modelspace()
                        if e.dxftype() == "LINE"])
        pts = _centred(_closed(_square(pts)))
    else:
        L, W, _H = r.bbox
        if L is None or W is None:
            return None
        a, b = (L + DROP) / 2, (W + DROP) / 2
        pts = np.array([(-a, -b), (a, -b), (a, b), (-a, b)])
    return tuple((float(x), float(y)) for x, y in pts)


# ================================================================ layout


@dataclass
class Strip:
    drawer: str
    name: str
    w: float
    d: float
    y0: float                       # from the stack's front, which is the drawer's inside front
    places: list[Place] = field(default_factory=list)
    label: tuple[float, float] = (0.0, 0.0)     # centre of the word
    lift: tuple[float, float] | None = None
    notes: list[str] = field(default_factory=list)
    keystone: bool = False
    loose: bool = False             # the keystone holds its drawer's loose things

    @property
    def label_text(self) -> str:
        return self.name

    @property
    def filename(self) -> str:
        return f"insert_{self.drawer.lower()}_{self.name.lower().replace('-', '')}"


def _snap(v: float) -> float:
    return math.ceil(v / MODULE - 1e-9) * MODULE


def _options(g: Group) -> list[tuple[Group, int]]:
    """The turns and column counts worth trying for one group."""
    out = []
    for v in ([g, g.turned()] if g.shape in ("rect", "poly") else [g]):
        seen = set()
        for cols in range(1, g.n + 1):
            c = v.size(cols)[2]
            if c not in seen:
                seen.add(c)
                out.append((v, c))
    return out


def _pack(chosen: list[tuple[Group, int]], w: float, x_first: float) -> list[tuple[Group, float, float, int]] | None:
    """Shelf-pack groups of cells, each already turned and given its column
    count, into bands across the strip: into the band where it adds least
    depth, a new band only when none has room. ``x_first`` is where holes may
    start in the first band (after the word, when the word sits beside them).
    Returns (group, cell x, cell y, cols), or None when one will not fit."""
    bands: list[list[float]] = []            # [depth, cursor, x_min]
    placed: list[tuple[int, Group, float, int]] = []
    right = w - EDGE
    for v, c in chosen:
        gw, gd, c, _r = v.size(c)
        px_ = v.pad[0]
        best = None
        for bi, band in enumerate(bands):
            start = max(band[1], band[2] - px_)
            if start + gw - px_ <= right + 1e-6:
                grow = max(0.0, gd - band[0])
                if best is None or grow < best[0]:
                    best = (grow, bi, start)
        if best is None or best[0] >= gd:
            x_min = x_first if not bands else EDGE
            start = x_min - px_
            if start + gw - px_ > right + 1e-6:
                return None
            bands.append([gd, start + gw, x_min])
            placed.append((len(bands) - 1, v, start, c))
        else:
            grow, bi, start = best
            bands[bi][0] += grow
            bands[bi][1] = start + gw
            placed.append((bi, v, start, c))
    tops = [sum(b[0] for b in bands[:i]) for i in range(len(bands))]
    return [(v, x, tops[bi] + (bands[bi][0] - v.size(c)[1]) / 2, c) for bi, v, x, c in placed]


def _lay(name: str, groups: list[Group], w: float, notes: list[str],
         x_col: float | None = None) -> tuple[list[Place], tuple[float, float], float]:
    """Place a strip's groups and its word. Tries the word beside the first
    band and the word in a band of its own, each with the groups in list
    order and largest cell first, and keeps the shallowest strip. Returns
    places, the word's centre and the strip's depth (a whole module count).
    ``x_col`` is the drawer's common first column: every strip whose word sits
    beside its places starts them there, so the drawer reads as one grid."""
    lw = callouts.text_width(name, LABEL_H)
    for g in groups:
        if min(g.fw, g.fd) > w - 2 * EDGE:
            notes.append(f"{g.row.id} does not fit across the {name} strip ({min(g.fw, g.fd):.1f} in {w - 2 * EDGE:.1f}).")
    groups = [g for g in groups if min(g.fw, g.fd) <= w - 2 * EDGE]
    orders = [groups, sorted(groups, key=lambda g: -g.px * g.py * g.n)]
    best = None
    for beside in (True, False):
        for order in orders:
          for chosen in itertools.product(*(_options(g) for g in order)):
            packed = _pack(list(chosen), w, (x_col or EDGE + lw + LABEL_GAP) if beside else EDGE)
            if packed is None:
                continue
            places: list[Place] = []
            for g, x, y, c in packed:
                for i in range(g.n):
                    cx = x + g.px / 2 + (i % c) * g.px
                    cy = y + g.py / 2 + (i // c) * g.py
                    places.append(Place(g.row.id, g.row.store, g.shape, cx, cy, g.fw, g.fd, g.depth,
                                        (STOCK_T - g.depth) + g.height, g.steps, g.poly))
            if not places:
                label = (EDGE + lw / 2, MODULE / 2)
                depth = MODULE
            else:
                y0 = min(p.box[1] for p in places)
                if beside:
                    band_hi = max(p.box[3] for (g, x, y, c) in packed[:1] for p in places if p.tool_id == g.row.id)
                    ly = (y0 + band_hi) / 2          # the word centred on its first group
                    shift = EDGE - min(y0, ly - LABEL_H / 2)
                else:
                    ly = y0 - LABEL_GAP - LABEL_H / 2
                    shift = EDGE - (ly - LABEL_H / 2)
                places = [replace(p, cy=p.cy + shift) for p in places]
                ly += shift
                used = max(max(p.box[3] for p in places), ly + LABEL_H / 2) + EDGE
                depth = _snap(used)
                centre = (depth - used) / 2
                places = [replace(p, cy=p.cy + centre) for p in places]
                label = (EDGE + lw / 2, ly + centre)
            key = (depth, not beside)
            if best is None or key < best[0]:
                best = (key, places, label, depth)
    if best is None:
        notes.append(f"the {name} strip's places do not pack across {w:.0f}.")
        return [], (EDGE + lw / 2, MODULE / 2), MODULE
    return best[1], best[2], best[3]


def outline(p: Place) -> np.ndarray:
    """The place's pocket outline in strip coordinates."""
    if p.poly:
        return np.array(p.poly) + (p.cx, p.cy)
    if p.shape == "circle":
        r = max(p.w, *(dia for dia, _ in p.steps)) / 2 if p.steps else p.w / 2
        t = np.linspace(0.0, 2 * math.pi, 48, endpoint=False)
        return np.stack([p.cx + r * np.cos(t), p.cy + r * np.sin(t)], axis=1)
    x0, y0, x1, y1 = p.box
    return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def _mask(shapes: list[np.ndarray], w: float, d: float, grow: float = 0.0) -> np.ndarray:
    """Filled outlines on a RES raster over ``w`` x ``d``, grown by ``grow``."""
    m = np.zeros((int(math.ceil(d / RES)) + 1, int(math.ceil(w / RES)) + 1), np.uint8)
    for pts in shapes:
        cv2.fillPoly(m, [np.round(np.asarray(pts) / RES).astype(np.int32)], 1)
    k = int(round(grow / RES))
    if k > 0:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    return m


def _rect(cx: float, cy: float, w: float, d: float) -> np.ndarray:
    return np.array([(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (cx + w / 2, cy + d / 2),
                     (cx - w / 2, cy + d / 2)])


def _lift(strip: Strip) -> tuple[float, float] | None:
    """The first spot, from the right end and the front, where a lift hole
    keeps WALL off every place's outline and the word, and EDGE off every
    edge."""
    r = LIFT_D / 2
    lw = callouts.text_width(strip.name, LABEL_H)
    shapes = [outline(p) for p in strip.places] + [_rect(*strip.label, lw, LABEL_H)]
    busy = _mask(shapes, strip.w, strip.d, r + WALL)
    y = EDGE + r
    while y <= strip.d - EDGE - r + 1e-6:
        x = strip.w - EDGE - r
        while x >= EDGE + r - 1e-6:
            if not busy[int(round(y / RES)), int(round(x / RES))]:
                return (x, y)
            x -= 2.5
        y += 2.5
    return None


def _cells(pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Raster cells of an outline whose box starts at the origin."""
    w, d = pts.max(axis=0)
    return np.nonzero(_mask([pts], float(w), float(d)))


def _interlock_run(name: str, items: list[Group], w: float, along: str,
                   back: float | None = None) -> tuple[list[tuple[Group, np.ndarray]], tuple[float, float]] | None:
    """One interlock pass. ``along`` "x": long sides across the strip, heavy
    ends alternately at the left and right edges, each slid forward. "y":
    long sides front to back, heavy ends alternately at the front and at
    ``back``, each slid in from the left. None when something will not fit."""
    lw = callouts.text_width(name, LABEL_H)
    far = (back + EDGE + 1.0) if back is not None else 1000.0
    ny = int(math.ceil(far / RES)) + 1
    shapes: list[np.ndarray] = []
    placed: list[tuple[Group, np.ndarray]] = []
    for k, g in enumerate(items):
        pts = np.array(g.poly)
        if along == "y":
            pts = pts @ np.array([[0.0, 1.0], [-1.0, 0.0]])     # heavy end to the front
        if k % 2:
            pts = -pts
        pts = pts - pts.min(axis=0)
        ext = pts.max(axis=0)
        ys, xs = _cells(pts)
        occ = _mask(shapes, w, far, WALL)
        if along == "x":
            ox = EDGE if k % 2 == 0 else w - EDGE - ext[0]
            if ox < EDGE - 1e-6:
                return None
            jx, oy = int(round(ox / RES)), EDGE
            while True:
                jy = int(round(oy / RES))
                if ys.max() + jy >= ny:
                    return None
                if not occ[ys + jy, xs + jx].any():
                    break
                oy += 0.5
        else:
            oy = EDGE if k % 2 == 0 else back - ext[1]
            if oy < EDGE - 1e-6:
                return None
            jy, ox = int(round(oy / RES)), EDGE
            while True:
                jx = int(round(ox / RES))
                if ox + ext[0] > w - EDGE + 1e-6:
                    return None
                if not occ[ys + jy, xs + jx].any():
                    break
                ox += 0.5
        shapes.append(pts + (ox, oy))
        placed.append((g, pts + (ox, oy)))
    occ = _mask(shapes, w, far, WALL)
    ly = EDGE + LABEL_H / 2
    while ly <= far - EDGE - LABEL_H / 2:
        lx = EDGE + lw / 2
        while lx <= w - EDGE - lw / 2:
            x0, y0 = int((lx - lw / 2) / RES), int((ly - LABEL_H / 2) / RES)
            if not occ[y0:y0 + int(LABEL_H / RES) + 1, x0:x0 + int(lw / RES) + 1].any():
                return placed, (lx, ly)
            lx += 1.0
        ly += 1.0
    return None


_INTERLOCKED: dict = {}


def _interlock(name: str, groups: list[Group], w: float,
               notes: list[str]) -> tuple[list[Place], tuple[float, float], float]:
    """Long lying tools head to tail, laid both ways (see ``_interlock_run``);
    the shallower strip wins. For "y" the back line is the least that fits,
    found by bisection. The word takes the first gap, front to back, left to
    right."""
    items = [g for g in groups for _ in range(g.n)]
    key = (name, round(w, 3), tuple((g.row.id, g.poly, g.depth) for g in items))
    if key not in _INTERLOCKED:
        runs = []
        r = _interlock_run(name, items, w, "x")
        if r:
            runs.append(r)
        lo = max(np.ptp(np.array(g.poly)[:, 0]) for g in items) + EDGE if items else MODULE
        hi = lo + 200.0
        if _interlock_run(name, items, w, "y", hi):
            while hi - lo > 0.5:
                mid = (lo + hi) / 2
                if _interlock_run(name, items, w, "y", mid):
                    hi = mid
                else:
                    lo = mid
            runs.append(_interlock_run(name, items, w, "y", hi))
        _INTERLOCKED[key] = runs
    runs = _INTERLOCKED[key]
    if not runs:
        notes.append(f"the {name} strip's tools do not interlock across {w:.0f}.")
        return [], (EDGE + callouts.text_width(name, LABEL_H) / 2, MODULE / 2), MODULE

    def used(run):
        placed, label = run
        return max([p[:, 1].max() for _g, p in placed] + [label[1] + LABEL_H / 2]) + EDGE

    placed, label = min(runs, key=lambda run: _snap(used(run)))
    u = used((placed, label))
    depth = _snap(u)
    centre = (depth - u) / 2
    places = []
    for g, pts in placed:
        lo_, hi_ = pts.min(axis=0), pts.max(axis=0)
        c = (lo_ + hi_) / 2
        places.append(Place(g.row.id, g.row.store, "poly", float(c[0]), float(c[1] + centre),
                            float(hi_[0] - lo_[0]), float(hi_[1] - lo_[1]), g.depth, (STOCK_T - g.depth) + g.height,
                            (), tuple((float(x), float(y)) for x, y in pts - c)))
    return places, (label[0], label[1] + centre), depth


def spec_for(key: str) -> DrawerSpec:
    for s in DRAWERS:
        if s.key == key:
            return s
    raise KeyError(key)


def ceiling(spec: DrawerSpec, d: Datums = D) -> float:
    """Clear height over the drawer's bottom panel to the part above it: the
    next drawer's box, or the cap over the top one. The drawer box's sides
    are lower, but nothing slides over them."""
    return drawers.opening(spec, d)[1] - (BOTTOM_GROOVE_Z + BOTTOM_T)


@dataclass
class DrawerPlan:
    key: str
    strips: list[Strip]
    w: float
    d: float
    notes: list[str]

    @property
    def used(self) -> float:
        return sum(s.d for s in self.strips if not s.keystone)


def plan(key: str, d: Datums = D, rows: list[Row] | None = None) -> DrawerPlan:
    spec = spec_for(key)
    iw, idep, _ih = drawers.interior(spec, d)
    w, depth = iw - STACK_CLEAR, idep - STACK_CLEAR
    rows = [r for r in (read_rows() if rows is None else rows) if r.active and r.drawer == key]
    notes: list[str] = []
    strips: list[Strip] = []
    y0 = 0.0
    x_col = EDGE + max(callouts.text_width(ss.name, LABEL_H) for ss in STRIPS[key] if ss.layout == "grid") + LABEL_GAP
    for ss in STRIPS[key]:
        mine = [r for r in rows if r.strip == ss.name and r.store in PLACED]
        groups = []
        for r in sorted(mine, key=lambda r: (r.store != "bore", (r.hold[0] if r.hold else r.shank_d) or 0.0,
                                             r.cut_d or 0.0, r.id)):
            g = group_for(r)
            if g is None:
                notes.append(f"{r.id} {r.name} ({r.store} on {ss.name}) has no dimensions to hold it by: "
                             "capture it or caliper it. MEASURE THIS.")
                continue
            groups.append(g)
        snotes: list[str] = []
        if ss.layout == "interlock":
            places, label, sd = _interlock(ss.name, groups, w, snotes)
        else:
            places, label, sd = _lay(ss.name, groups, w, snotes, x_col)
        st = Strip(key, ss.name, w, sd, y0, places, label, None, snotes)
        st.lift = _lift(st)
        strips.append(st)
        y0 += sd
    rest = depth - y0
    bin_ = Strip(key, KEYSTONE, w, max(rest, 0.0), y0, [], (EDGE + callouts.text_width(KEYSTONE, LABEL_H) / 2,
                                                             EDGE + LABEL_H / 2 + EDGE), None, [], True,
                 any(r.store == "loose" for r in rows))
    strips.append(bin_)
    for r in rows:
        if r.store not in STORES:
            notes.append(f"{r.id} {r.name} has store {r.store!r}: it has no home in {key}. "
                         f"The tool list's store column takes {', '.join(STORES)}.")
        elif r.store in PLACED and r.strip not in {s.name for s in STRIPS[key]}:
            notes.append(f"{r.id} {r.name} is on strip {r.strip!r}, which {key} does not have: it has no home.")
    return DrawerPlan(key, strips, w, depth, notes)


def plan_all(d: Datums = D, rows: list[Row] | None = None) -> list[DrawerPlan]:
    return [plan(s.key, d, rows) for s in DRAWERS]


# ================================================================ geometry


KEY_RIM = 12.0
"""The keystone's frame rails. Its bin is a window cut through, the drawer's
own bottom its floor: a bin needs no white floor, and a window is one
profile pass where a pocket this size is an hour of clearing."""


def _bin_recess(s: Strip) -> tuple[float, float, float, float] | None:
    """The keystone's window, behind its word: where the drawer's loose
    things go. A drawer with nothing loose gets a solid keystone: an empty
    window is a pocket for nothing."""
    if not s.loose:
        return None
    y_lo = EDGE + LABEL_H + EDGE
    if s.d - KEY_RIM - y_lo < MODULE:
        return None
    return (KEY_RIM, y_lo, s.w - KEY_RIM, s.d - KEY_RIM)


def _face(p: Place) -> Face:
    return Face(Wire.make_polygon([(x + p.cx, y + p.cy, 0.0) for x, y in p.poly], close=True))


def build(s: Strip, *, label: bool = True) -> Part:
    part = Box(s.w, s.d, STOCK_T, align=(Align.MIN, Align.MIN, Align.MIN))
    if s.d <= 0:
        return part
    top = STOCK_T
    for p in s.places:
        if p.steps:
            for dia, depth in p.steps:
                part -= Cylinder(dia / 2, depth, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
                    Location((p.cx, p.cy, top)))
        elif p.shape == "circle":
            part -= Cylinder(p.w / 2, p.depth, align=(Align.CENTER, Align.CENTER, Align.MAX)).moved(
                Location((p.cx, p.cy, top)))
        elif p.poly:
            part -= extrude(_face(p), amount=p.depth).moved(Location((0, 0, top - p.depth)))
        else:
            r = min(POCKET_R, p.w / 2 - 0.01, p.d / 2 - 0.01)
            sk = RectangleRounded(p.w, p.d, r)
            part -= extrude(sk, amount=p.depth).moved(Location((p.cx, p.cy, top - p.depth)))
    rec = _bin_recess(s) if s.keystone else None
    if rec:
        x0, y0, x1, y1 = rec
        part -= extrude(RectangleRounded(x1 - x0, y1 - y0, POCKET_R), amount=STOCK_T).moved(
            Location(((x0 + x1) / 2, (y0 + y1) / 2, 0)))
    if s.lift:
        part -= Cylinder(LIFT_D / 2, STOCK_T).moved(Location((s.lift[0], s.lift[1], STOCK_T / 2)))
    if label and s.d >= MODULE:
        sk = callouts.text_sketch(s.label_text, LABEL_H).moved(Location((s.label[0], s.label[1], 0)))
        part -= extrude(sk, amount=LABEL_D).moved(Location((0, 0, top - LABEL_D)))
    return part


def layers(s: Strip) -> dict[str, list]:
    """The DXF per layer, strip-local at Z = 0. POCKET_D<depth> are closed
    loops, THROUGH the lift hole, VCARVE the word's outlines (the #302 at
    LABEL_D in Fusion's Engrave)."""
    out: dict[str, list] = {"OUTLINE": list(Rectangle(s.w, s.d, align=(Align.MIN, Align.MIN)).faces())}

    def add(layer: str, faces) -> None:
        out.setdefault(layer, []).extend(faces)

    for p in s.places:
        if p.steps:
            for dia, depth in p.steps:
                add(f"POCKET_D{depth:g}", Circle(dia / 2).moved(Location((p.cx, p.cy))).faces())
        elif p.shape == "circle":
            add(f"POCKET_D{p.depth:g}", Circle(p.w / 2).moved(Location((p.cx, p.cy))).faces())
        elif p.poly:
            add(f"POCKET_D{p.depth:g}", [_face(p)])
        else:
            r = min(POCKET_R, p.w / 2 - 0.01, p.d / 2 - 0.01)
            add(f"POCKET_D{p.depth:g}", RectangleRounded(p.w, p.d, r).moved(Location((p.cx, p.cy))).faces())
    rec = _bin_recess(s) if s.keystone else None
    if rec:
        x0, y0, x1, y1 = rec
        add("THROUGH", RectangleRounded(x1 - x0, y1 - y0, POCKET_R).moved(
            Location(((x0 + x1) / 2, (y0 + y1) / 2))).faces())
    if s.lift:
        add("THROUGH", Circle(LIFT_D / 2).moved(Location(s.lift)).faces())
    if s.d >= MODULE:
        add(callouts.VCARVE_LAYER, callouts.text_sketch(s.label_text, LABEL_H).moved(Location(s.label)).faces())
    return out


def _plane(spec: DrawerSpec, s: Strip, d: Datums = D) -> Plane:
    """Strip-local to station: X across the drawer, Y back from the drawer's
    inside front, Z up from the bottom panel's top face. The stack is centred
    in the width and starts at the front, its clearance at the back."""
    x0, y0, z0 = drawers.box_origin(spec, d)
    return Plane(origin=(x0 + T + STACK_CLEAR / 2, y0 + T + s.y0, z0 + BOTTOM_GROOVE_Z + BOTTOM_T),
                 x_dir=(1, 0, 0), z_dir=(0, 0, 1))


def label_of(s: Strip) -> str:
    return s.filename


def placed_all(d: Datums = D) -> list[tuple[str, Part]]:
    out = []
    for p in plan_all(d):
        spec = spec_for(p.key)
        for s in p.strips:
            if s.d > 0:
                out.append((label_of(s), _plane(spec, s, d) * build(s)))
    return out


# ================================================================ coupon

COUPON = (100.0, 50.0)


def coupon_places() -> list[Place]:
    """Settle the clearances before a strip is cut (red team, change 11):
    1/8 bores 3.3 / 3.4 / 3.5, 1/4 bores 6.5 / 6.6 / 6.7, one collet step,
    one clamp socket. Push a real shank, collet and clamp into each."""
    out = []
    for i, dia in enumerate((3.3, 3.4, 3.5)):
        out.append(Place(f"B{dia:g}", "bore", "circle", 12.0 + i * 12.0, 12.0, dia, dia, DEPTH_MAX, 0.0))
    for i, dia in enumerate((6.5, 6.6, 6.7)):
        out.append(Place(f"B{dia:g}", "bore", "circle", 12.0 + i * 14.0, 36.0, dia, dia, DEPTH_MAX, 0.0))
    out.append(Place("ER16", "collet", "circle", 64.0, 16.0, COLLET_STEP[0][0], COLLET_STEP[0][0],
                     DEPTH_MAX, 0.0, COLLET_STEP))
    out.append(Place("EC", "socket", "rect", 86.0, 25.0, 12.8, 20.8, DEPTH_MAX, 0.0))
    return out


def coupon() -> Strip:
    return Strip("COUPON", "FIT", COUPON[0], COUPON[1], 0.0, coupon_places(), (64.0, 40.0), None, [])


# ================================================================ checks


def check_inserts(d: Datums = D, rows: list[Row] | None = None) -> list[str]:
    notes: list[str] = []
    rows = read_rows() if rows is None else rows
    if STOCK_T - DEPTH_MAX - CAP_T < 0.3:
        notes.append(f"DEPTH_MAX {DEPTH_MAX:g} in {STOCK_T:g} stock leaves {STOCK_T - DEPTH_MAX:.2f} under a "
                     f"place and the bottom cap is {CAP_T:g}: an empty place shows black.")
    white = 2 * (LABEL_D - CAP_T) * math.tan(VBIT_HALF)
    if white < 0.5:
        notes.append(f"the kind word, V-carved {LABEL_D:g} deep through a {CAP_T:g} cap, shows {white:.2f} of "
                     "white: under 0.5 it does not read. Deepen LABEL_D.")
    notes.append(f"STOCK_T is {STOCK_T:g}, 1/2 in ColorCore nominal, not measured. Calipers on the sheet, "
                 "then set it. MEASURE THIS.")
    for p in plan_all(d, rows):
        spec = spec_for(p.key)
        top = ceiling(spec, d) - HEAD_CLEAR
        notes.extend(f"{p.key}: {n}" for n in p.notes)
        if p.used > p.d + 1e-6:
            notes.append(f"{p.key}'s strips need {p.used:.0f} of its {p.d:.0f} of depth: a strip runs off the "
                         "back. Move a thing to another drawer or strike it.")
        ks = p.strips[-1]
        loose = [r for r in rows if r.active and r.drawer == p.key and r.store == "loose"]
        if loose and _bin_recess(ks) is None:
            notes.append(f"UNMODELLED: {p.key}'s keystone is {ks.d:.0f} deep, too thin for a window, so "
                         + ", ".join(f"{r.id} {r.name}" for r in loose) + " have no home. Caliper them for "
                         "fitted places, or move them to a drawer with room.")
        if 0 < ks.d < MODULE:
            notes.append(f"{p.key}'s keystone is {ks.d:.1f} deep: too thin to cut or to lift. Expected, and "
                         "worth knowing; fold it into the strip in front.")
        notes.append(f"{p.key}'s keystone BIN is {ks.d:.1f} deep off the model's {p.d + STACK_CLEAR:.0f}. Cut it "
                     "to the built drawer's measured inside depth less the other strips and "
                     f"{STACK_CLEAR:g}. MEASURE THIS.")
        for s in p.strips:
            notes.extend(f"{p.key} {s.name}: {n}" for n in s.notes)
            if s.lift is None and s.d > 0 and not s.keystone:
                notes.append(f"{p.key} {s.name} has no room for a lift hole. Expected, and worth knowing: "
                             "lift it by a place.")
            for pl in s.places:
                if pl.height > top + 1e-6:
                    notes.append(f"{p.key} {s.name}: {pl.tool_id} stands {pl.height:.1f} over the drawer bottom "
                                 f"and the part above leaves {top + HEAD_CLEAR:.1f} less {HEAD_CLEAR:g}. It "
                                 "hits the drawer above.")
                x0, y0, x1, y1 = pl.box
                if x0 < EDGE - 1e-6 or x1 > s.w - EDGE + 1e-6 or y0 < EDGE - 1e-6 or y1 > s.d - EDGE + 1e-6:
                    notes.append(f"{p.key} {s.name}: {pl.tool_id} runs within {EDGE:g} of the strip's edge.")
            for a, b in ((a, b) for i, a in enumerate(s.places) for b in s.places[i + 1:]):
                ax0, ay0, ax1, ay1 = a.box
                bx0, by0, bx1, by1 = b.box
                if ax0 < bx1 + WALL - 1e-6 and bx0 < ax1 + WALL - 1e-6 and ay0 < by1 + WALL - 1e-6 and by0 < ay1 + WALL - 1e-6:
                    if a.poly or b.poly:        # boxes meet; do the outlines?
                        near = _mask([outline(a)], s.w, s.d, WALL - 2 * RES) & _mask([outline(b)], s.w, s.d)
                        if not near.any():
                            continue
                    notes.append(f"{p.key} {s.name}: {a.tool_id} and {b.tool_id} are closer than {WALL:g}.")
    return notes


# ================================================================ export


def export(d: Datums = D, out_dir: Path | None = None) -> list[Path]:
    """STEP of every strip for Fusion and the assembly, DXF with the pockets
    on depth-named layers and the kind word on ``VCARVE``; the fit coupon
    too. Into ``export/cnc_shapeoko/inserts``."""
    out_dir = (EXPORT_DIR / "inserts") if out_dir is None else out_dir
    out: list[Path] = []
    for s in [s for p in plan_all(d) for s in p.strips if s.d > 0] + [coupon()]:
        out.extend(export_part(build(s), s.filename, layers=layers(s), out_dir=out_dir))
    return out


def preview_svg(p: DrawerPlan, path: Path, scale: float = 2.0) -> Path:
    """Top view of one drawer's stack: black cap, white places, the word."""
    W, H = p.w * scale + 20, (p.d + STACK_CLEAR) * scale + 20
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H + 20:.0f}" '
           f'viewBox="0 0 {W:.0f} {H + 20:.0f}"><rect width="100%" height="100%" fill="#d9d4c7"/>',
           f'<g transform="translate(10,{H - 10:.0f}) scale({scale},{-scale})">']
    for s in p.strips:
        out.append(f'<rect x="0" y="{s.y0:.2f}" width="{s.w:.2f}" height="{s.d:.2f}" fill="#141414" '
                   'stroke="#666" stroke-width="0.4"/>')
        for pl in s.places:
            if pl.shape == "circle":
                out.append(f'<circle cx="{pl.cx:.2f}" cy="{s.y0 + pl.cy:.2f}" r="{pl.w / 2:.2f}" fill="#f2efe8"/>')
            elif pl.poly:
                pts = " ".join(f"{x + pl.cx:.2f},{s.y0 + y + pl.cy:.2f}" for x, y in pl.poly)
                out.append(f'<polygon points="{pts}" fill="#f2efe8"/>')
            else:
                out.append(f'<rect x="{pl.cx - pl.w / 2:.2f}" y="{s.y0 + pl.cy - pl.d / 2:.2f}" width="{pl.w:.2f}" '
                           f'height="{pl.d:.2f}" rx="1.6" fill="#f2efe8"/>')
        rec = _bin_recess(s) if s.keystone else None
        if rec:
            out.append(f'<rect x="{rec[0]:.2f}" y="{s.y0 + rec[1]:.2f}" width="{rec[2] - rec[0]:.2f}" '
                       f'height="{rec[3] - rec[1]:.2f}" rx="1.6" fill="#f2efe8"/>')
        if s.lift:
            out.append(f'<circle cx="{s.lift[0]:.2f}" cy="{s.y0 + s.lift[1]:.2f}" r="{LIFT_D / 2:.2f}" fill="#b98b5e"/>')
        if s.d >= MODULE:
            out.append(f'<text x="{s.label[0]:.2f}" y="{-(s.y0 + s.label[1]) + LABEL_H * 0.35:.2f}" '
                       f'transform="scale(1,-1)" font-family="Helvetica" font-size="{LABEL_H:.1f}" '
                       f'text-anchor="middle" fill="#f2efe8">{s.name}</text>')
    out.append('</g>')
    out.append(f'<text x="10" y="{H + 12:.0f}" font-family="Helvetica" font-size="13">{p.key}: '
               f'{p.used:.0f} of {p.d:.0f} in strips, keystone BIN {p.strips[-1].d:.0f}</text></svg>')
    path.write_text("\n".join(out))
    return path


if __name__ == "__main__":
    for p in plan_all():
        spec = spec_for(p.key)
        print(f"{p.key} ({spec.callout}): {p.w:.0f} x {p.d:.0f}, ceiling {ceiling(spec):.1f}; strips use "
              f"{p.used:.0f}, keystone BIN {p.strips[-1].d:.0f}")
        for s in p.strips:
            print(f"  {s.name:<12} {s.d:5.0f} deep at y {s.y0:5.0f}   {len(s.places):2d} places"
                  f"{'   lift ' + format(s.lift[0], '.0f') + ',' + format(s.lift[1], '.0f') if s.lift else ''}")
            for pl in s.places:
                print(f"      {pl.tool_id:<6} {pl.store:<7} {pl.w:6.2f} x {pl.d:6.2f} x {pl.depth:4.1f}   at "
                      f"({pl.cx:6.1f}, {pl.cy:5.1f})   stands {pl.height:5.1f}")
        for n in p.notes:
            print(f"  note: {n}")
