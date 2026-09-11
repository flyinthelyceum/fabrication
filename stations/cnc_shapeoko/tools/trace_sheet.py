"""The capture sheets, the card and (for history) the tracing collar: the
physical things a tool capture needs (spec v3, 2026-09-04; the sheet family
added the same day; the photo capture replaced tracing on 2026-09-11, so the
sheets' rules and the card now read LAY / MEASURE / PHOTO / FORM).

    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/trace_sheet.py
    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/trace_sheet.py --size TABLOID

writes, beside this file:

    trace_sheet_<size>.pdf  one per paper size in ``SIZES`` (letter, a4,
                        tabloid, a3, a2, arch_b). Print at 100%. Four ArUco
                        tags (DICT_4X4_50) at the corners of the printable
                        area, a trace window with a 1mm border, the TAG /
                        HEIGHT boxes, the rules, a 100mm scale bar, all of it
                        inside a 14mm gutter.
    trace_sheet.pdf     the LETTER sheet again under its old name, so every
                        link and every printed reference to it still works.
    trace_sheet_<size>.png  each page rasterised (pdftoppm at RENDER_DPI when
                        it is on the box, else matplotlib), for a look and for
                        the synthetic test. ``trace_sheet.png`` is LETTER's.
                        10/20/30/40/50 wide, open at the top and through the
                        block's depth. A tool that slides into the 20 and not
                        the 10 is height class 20. Labels embossed.
    tracing_collar.stl  the TRACE collar, RETIRED 2026-09-11 with the trace
                        capture (the photo capture reads the tool's own
                        silhouette; see ``capture_ingest``). Still generated
                        so the v1 captures' history stays reproducible: a
                        14.0 OD cylinder a hex pencil rides in, PEN_R in
                        ``capture_ingest`` its radius.
    capture_card.pdf    the laminated card: the procedure in large type, one
                        page, for Drawer 1 beside the sheets.

WHY A FAMILY, AND WHY IT STOPS WHERE IT DOES
============================================

The LETTER sheet's window is 180 x 180. Jared's jog pendant is 228 long and
does not lie in it at any rotation, and the collar makes that worse: the
pencil rides 7mm outside the tool, so a 228mm tool draws a 242mm loop. One
sheet size was never going to be enough.

The family is LETTER and TABLOID (RT4 trimmed the rest) under THE SIZING
PRINCIPLE:

    A TRACE SHEET NEVER HAS TO BE BIGGER THAN THE DRAWER. Anything that will
    not lie in a drawer does not get a foam pocket, so it never gets traced.

The drawers are the ones in ``parts/drawers.py``. After the 2026-09-04 inset
front ruling every box is 259 wide outside, 18mm birch a side, on 500mm
slides with a front rabbet, a back set in one thickness and the back panel's
own thickness behind it:

    clear interior  446 deep x 223 wide      (``drawers.interior``)

A tool that fills that interior end to end draws a loop 446 + 2 x 7 = 460 long
and 223 + 14 = 237 wide. A2's window is 384.1 x 474.6, which holds 460 x 237
with 14.6mm to spare on the long axis. That is the whole reason A2's tags are
40mm and not the 50 the sheet would otherwise carry: a bigger tag eats the
window from both ends, and the window has to keep covering the drawer.

SELF-IDENTIFYING SHEETS
=======================

Every size uses a DIFFERENT quartet of ArUco ids out of DICT_4X4_50, so the
ids in the photo say which paper it is:

    LETTER 0-3    TABLOID 8-11

``capture_ingest`` reads the quartet and looks the geometry up here. Nobody
types the paper size into a form, and a sheet photographed under the wrong
assumed size is impossible rather than quietly wrong by the ratio of the two
pages. LETTER keeps ids 0-3 and keeps its exact v1 geometry, so sheets that
were traced and photographed before the family existed ingest to the same
numbers they always did.

THE 14mm GUTTER
===============

Jared's printer will not lay a sheet down at 100% inside a smaller margin: it
produced gutters, which forced a scaled print, and a scaled print breaks the
tag-based mm mapping by exactly the scale factor (fixed on the ingest side
with ``capture_ingest``'s ``print_scale``, but the sheet should not need it).
Every element on every page in the family sits inside ``MARGIN`` of the page
edge on all four sides.

The four tags sit at the four corners of that printable area, and the window
is sized and placed so it is CLEAR of them. The tags occupy only the top and
bottom ``tag_mm`` bands of the page; the window lives in the clear paper
between those two bands. The corridor between the left and right tags in
those bands (``corridor_x0``..``corridor_x1``) is where the hand-filled
boxes, the rules and the scale bar live, clear of the tags' quiet zones so no
ink ever touches a marker.

SHEET FRAME
===========

Every number here is in SHEET MM: origin at the page's top-left corner, x to
the right, y DOWN, like an image. The ingest's homography maps a photo into
this frame at ``capture_ingest.PX_PER_MM``; the tag corners it uses are
``SheetSpec.tag_corners`` below, so the geometry the printer lays down and the
geometry the ingest assumes come from one place.

ArUco's corner order for an upright marker is top-left, top-right,
bottom-right, bottom-left; ``tag_corners`` returns that order in this frame,
and the markers are drawn upright on the page, so corner i of a detection
matches corner i here without a permutation.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

# ================================================================ the sheet

MARGIN = 14.0
"""Printable margin, page edge to the nearest ink, on all four sides, on every
size in the family. SOURCE: Jared's printer would not lay the v3 sheet (6mm
margin) down at 100%; it produced gutters, forcing a scaled print, which
breaks the tag-based mm mapping by the scale factor. 14mm clears that
printer's unprintable band. CONFIDENCE: fact, from the failed print (ruling
2026-09-04)."""

ARUCO_DICT = "DICT_4X4_50"
"""One dictionary for the whole family: 50 markers, of which the family uses
24. A 4x4 marker is six cells a side including its border, so ``tag_mm`` / 6
is the cell the phone has to resolve. CONFIDENCE: spec."""

TAG_QUIET = 3.0
"""White kept clear around each marker; ArUco wants a quiet zone of at least
one cell (5mm would be ideal, 3 detects reliably and keeps the window).
CONFIDENCE: rule."""

FIELD_SIDE_PAD = 3.95
BAND_GAP_TOP = 4.0
BAND_GAP_BOT = 7.4
"""Paper between the gutter and the window's side, between the top tag band
and the window, and between the window and the bottom tag band. These three
are the whole of the window's placement rule, and their values are the ones
that reproduce the v1 LETTER window EXACTLY: 180.0 x 180.0 at (17.95, 48.0).
Nothing else in the family is allowed to move them, because moving them moves
LETTER's window and re-ingesting an already photographed sheet stops giving
the same answer. The bottom gap is the larger of the two because the size
line is printed in it. CONFIDENCE: derived, pinned to v1."""

TRACE_INSET = 2.0
"""How far inside the window boundary the ingest crops, so the 1mm border line
never lands in the threshold image. Mirrors ``capture_ingest.FIELD_INSET``;
``test_capture`` asserts the two are equal. CONFIDENCE: rule."""

CLEAR_PAPER = 3.0
"""Paper the photo capture wants between the tool and the crop edge, so the
silhouette has white on every side and never touches the edge (which
rejects). CONFIDENCE: rule."""


@dataclass(frozen=True)
class SheetSpec:
    """One paper size in the family. Everything else is derived."""

    name: str
    page_w: float
    page_h: float
    tag_mm: float
    tag_ids: tuple[int, int, int, int]
    purpose: str

    # ---- the page -------------------------------------------------------

    @property
    def slug(self) -> str:
        return self.name.lower()

    @property
    def printable_w(self) -> float:
        return self.page_w - 2 * MARGIN

    @property
    def printable_h(self) -> float:
        return self.page_h - 2 * MARGIN

    # ---- the tags -------------------------------------------------------

    def tag_origin(self, tag_id: int) -> tuple[float, float]:
        """Top-left corner of one marker's black square, sheet mm. Ids run
        clockwise from the page's top-left."""
        i = self.tag_ids.index(tag_id)
        far_x = self.page_w - MARGIN - self.tag_mm
        far_y = self.page_h - MARGIN - self.tag_mm
        return ((MARGIN, MARGIN), (far_x, MARGIN), (far_x, far_y), (MARGIN, far_y))[i]

    def tag_corners(self, tag_id: int) -> np.ndarray:
        """The four corners of one marker's black square, sheet mm, in ArUco's
        order: top-left, top-right, bottom-right, bottom-left."""
        x0, y0 = self.tag_origin(tag_id)
        t = self.tag_mm
        return np.array([[x0, y0], [x0 + t, y0], [x0 + t, y0 + t], [x0, y0 + t]], dtype=np.float64)

    def tag_masks(self) -> list[tuple[float, float, float, float]]:
        """(x0, y0, x1, y1) per marker, the black square plus its quiet zone:
        what the ingest whites out of the window, in ``tag_ids`` order."""
        out = []
        for tid in self.tag_ids:
            x0, y0 = self.tag_origin(tid)
            out.append((x0 - TAG_QUIET, y0 - TAG_QUIET, x0 + self.tag_mm + TAG_QUIET, y0 + self.tag_mm + TAG_QUIET))
        return out

    def tag_mask(self, tag_id: int) -> tuple[float, float, float, float]:
        return self.tag_masks()[self.tag_ids.index(tag_id)]

    # ---- the corridor and the window ------------------------------------

    @property
    def corridor_x0(self) -> float:
        return MARGIN + self.tag_mm + TAG_QUIET

    @property
    def corridor_x1(self) -> float:
        return self.page_w - MARGIN - self.tag_mm - TAG_QUIET

    @property
    def corridor_w(self) -> float:
        return self.corridor_x1 - self.corridor_x0

    @property
    def field_w(self) -> float:
        return self.page_w - 2 * (MARGIN + FIELD_SIDE_PAD)

    @property
    def field_h(self) -> float:
        return self.page_h - 2 * MARGIN - 2 * self.tag_mm - BAND_GAP_TOP - BAND_GAP_BOT

    def field_rect(self) -> tuple[float, float, float, float]:
        """(x0, y0, x1, y1) of the trace window, sheet mm."""
        x0 = MARGIN + FIELD_SIDE_PAD
        y0 = MARGIN + self.tag_mm + BAND_GAP_TOP
        return (x0, y0, x0 + self.field_w, y0 + self.field_h)

    # ---- what it will actually take -------------------------------------

    def max_tool(self) -> tuple[float, float]:
        """The largest tool this sheet will take, mm, longer side first: the
        window less the crop's ``TRACE_INSET`` and ``CLEAR_PAPER`` of paper
        the photo needs round the tool, each side. (Until 2026-09-11 the
        collar's diameter was in here too.)"""
        pad = 2 * (TRACE_INSET + CLEAR_PAPER)
        a, b = self.field_h - pad, self.field_w - pad
        return (max(a, b), min(a, b))

    def line(self) -> str:
        L, W = self.max_tool()
        return (
            f"{self.name:<7} {self.page_w:>5.0f} x {self.page_h:<5.0f}  window "
            f"{self.field_w:>6.1f} x {self.field_h:<6.1f}  tags {self.tag_ids[0]}-{self.tag_ids[3]} "
            f"@ {self.tag_mm:.0f}mm  tool <= {L:.0f} x {W:.0f}"
        )


SIZES: dict[str, SheetSpec] = {
    s.name: s
    for s in (
        SheetSpec("LETTER", 215.9, 279.4, 30.0, (0, 1, 2, 3),
                  "the default. Everything in the cutter and instrument drawers."),
        SheetSpec("TABLOID", 279.0, 432.0, 40.0, (8, 9, 10, 11),
                  "the long-tool sheet: the jog pendant, a torque wrench, a long clamp."),
    )
}
"""The family: LETTER and TABLOID (RT4, 2026-09-04, trimmed the metric and
ARCH B twins away -- the shop prints on these two). Tag size is a documented
constant per size, not a formula: 30mm on LETTER, 40mm on TABLOID, big enough
to detect with the sheet a third of the screen and small enough to keep out of the window. LETTER
keeps ids 0-3 and TABLOID 8-11 so already-printed sheets still read.
CONFIDENCE: derived, and stated in the README."""

SIZE_FOR_TAG: dict[int, SheetSpec] = {tid: s for s in SIZES.values() for tid in s.tag_ids}
"""ArUco id -> the sheet that carries it. This is the whole of the
self-identification: the ingest detects markers, looks each id up here, and
the geometry follows."""

LETTER = SIZES["LETTER"]
DEFAULT_SIZE = LETTER
"""What everything means when nobody says. ``trace_sheet.pdf`` is this one and
keeps its name, and ids 0-3 keep meaning exactly this geometry."""

# v1 names, kept so nothing that reads this module breaks. LETTER's numbers.
PAGE_W, PAGE_H = LETTER.page_w, LETTER.page_h
TAG_IDS = LETTER.tag_ids
TAG_MM = LETTER.tag_mm
TAG_MARGIN = MARGIN
FIELD_W, FIELD_H = LETTER.field_w, LETTER.field_h
FIELD_X0, FIELD_Y0 = LETTER.field_rect()[0], LETTER.field_rect()[1]
CORRIDOR_X0, CORRIDOR_X1 = LETTER.corridor_x0, LETTER.corridor_x1


def tag_corners(tag_id: int, spec: SheetSpec | None = None) -> np.ndarray:
    """v1 entry point. The spec is looked up from the id when it is not
    given, so a bare id still resolves to the sheet that owns it."""
    return (spec or SIZE_FOR_TAG.get(tag_id, DEFAULT_SIZE)).tag_corners(tag_id)


def tag_masks(spec: SheetSpec | None = None) -> list[tuple[float, float, float, float]]:
    return (spec or DEFAULT_SIZE).tag_masks()


def field_rect(spec: SheetSpec | None = None) -> tuple[float, float, float, float]:
    return (spec or DEFAULT_SIZE).field_rect()


FIELD_BORDER_W = 1.0
"""The window's border line, centred on the window boundary. The ingest crops
inside it (``capture_ingest.FIELD_INSET``) so the line is never a contour."""

BOX_H = 16.0
BOX_W_MAX = 60.0
BOX_GAP = 14.0
BOX_H_BAND_FRAC = 0.55
"""The two hand-filled boxes: as wide as the corridor allows up to
``BOX_W_MAX``, ``BOX_GAP`` apart, sitting at the bottom of the top tag band so
the sheet's title has the band's top half. ``BOX_H`` grows with the sheet but
never takes more than ``BOX_H_BAND_FRAC`` of the band, which is what leaves
the title room to grow too. Written by hand, read by a human: the Form carries
the same two values for the machine."""

SCALE_BAR_MM = 100.0
"""Print at 100% and this bar measures 100 with a ruler; if it does not, the
sheet is scaled and every capture from it is wrong by the same ratio."""

PRINT_CHECK_LINE = (
    "Print at 100%.  If this bar is not 100mm, write the measured length here: ____ mm"
)

RULES = (
    "ONE TOOL, lying FLAT inside the window as it sits in the drawer, on its widest face, clear of "
    "the border line. Write its TAG in the box.",
    "MEASURE its tallest point above the paper in mm and write it in the HEIGHT box.",
    "PHOTO from straight above, phone flat, high enough that the sheet is about a third of the screen, "
    "all four corner squares in frame, no flash, the tool still on the sheet.",
    "FORM: tag, height, photo. Does not fit the window: take a bigger sheet. A plain rectangular "
    "slab: write L, W and thickness in the boxes instead.",
)
"""The whole procedure, on the sheet, where the hand is: LAY, MEASURE, PHOTO,
FORM. Four rules, wrapped to the bottom tag band's corridor at draw time.
SOURCE: the photo capture, 2026-09-11, which retired the collar and the
tracing (see capture_ingest). The v3 rules (collar, slot under 20mm) were
here from 2026-09-04 to 2026-09-11."""

RULE_FONT_PT = 7.0
RULE_LEADING = 1.40
"""Rule type is as big as the corridor's width, the band's height and
``RULE_FONT_PT`` times the sheet's scale all allow. On LETTER the corridor's
width binds and the type comes out near 6.5pt; on the big sheets the band's
height binds. Type on every sheet is scaled by ``page_h / LETTER.page_h``,
because a bigger sheet is photographed and read from further away."""

RENDER_DPI = 300

CARD_TITLE = "CNC TRAY CAPTURE"
CARD_SUB = "one tool, about a minute"
CARD_STEPS = (
    ("LAY", "Take a capture sheet: the smallest size the tool lies in with a finger's width of clear paper all round. Lay the tool FLAT inside the window, on its widest face, as it sits in the drawer, clear of the border line. Write its TAG (T0__, from the drawer label) in the TAG box."),
    ("MEASURE", "Measure the tool's tallest point above the paper with the ruler, in mm. Write it in the HEIGHT box."),
    ("PHOTO", "Stand over the sheet. Phone flat, high enough that the whole sheet is about a third of the screen, all four corner squares showing. The bigger the tool, the higher the phone. No flash, no lamp shadow. Do not move the tool."),
    ("FORM", "Open the form “CNC tray capture”: tag, height in mm, the photo. Done. The software reads the corner squares to know which paper you used and takes the tool's own outline from the photo. The tray regenerates; a rejected sheet comes back with one line saying why."),
)
CARD_EXCEPTIONS = (
    ("IT DOES NOT FIT THE WINDOW",
     "Take a bigger sheet: LETTER, then TABLOID. If the tool is a plain rectangular slab, do not photograph "
     "it at all: write L, W and thickness in the boxes and submit the sheet."),
    ("IT WILL NOT LIE FLAT, OR IT SHINES",
     "A tool that rocks or stands on a knob throws its outline: prop it level with a scrap of card. A bright "
     "reflection running along an edge can cut that edge off the outline: turn the sheet under the light and "
     "shoot again. Look at the preview the software posts back."),
)
CARD_FOOT = (
    "One tool per sheet.  Never a hand in the window, never a tool on its edge, never a lamp or a flash throwing a hard shadow.",
    "Sheets and the ruler live in Drawer 1.  Print at 100%: the bar at the bottom must measure 100mm.",
)
"""The card, verbatim. It is the sheet's rules unfolded into the four things
a hand does, in the order it does them, plus the two cases where the answer
is not to photograph. SOURCE: the photo capture, 2026-09-11. The v3 card
(SHEET / HEIGHT / LAY / TRACE / PHOTO / FORM, the collar and the gauge) ran
from 2026-09-04 to 2026-09-11; Jared red-teamed the collar as too clunky."""


def marker_image(tag_id: int, px: int = 600) -> np.ndarray:
    """One ArUco marker as a uint8 image, 0 black / 255 white."""
    import cv2

    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, ARUCO_DICT))
    return cv2.aruco.generateImageMarker(d, tag_id, px)


def _fit_font(text_w_mm: float, longest: str, cap: float, per_char_em: float = 0.55) -> float:
    """Point size at which ``longest`` fills ``text_w_mm``, capped. DejaVu
    Sans averages about 0.55em a character over mixed-case text and about 0.62
    bold; this is a layout estimate, and the rendered PNG is the check."""
    per_char_mm = per_char_em * 0.3528
    return min(cap, text_w_mm / (max(len(longest), 1) * per_char_mm))


def _layout_rules(width_mm: float, height_mm: float, pt_max: float) -> tuple[float, list[str], float]:
    """The biggest type at which ``RULES``, wrapped to ``width_mm``, still fits
    ``height_mm``. Walking the size DOWN rather than fixing the line breaks is
    what lets a wide sheet put a whole rule on one line and set it half again
    as large as LETTER can: the corridor on A2 is 306mm to LETTER's 122."""
    import textwrap

    best = (3.0, [ln for r in RULES for ln in textwrap.wrap(r, 200)], 3.0 * 0.3528 * RULE_LEADING)
    pt = pt_max
    while pt >= 3.0:
        cpl = max(int(width_mm / (pt * 0.55 * 0.3528)), 10)
        lines = [ln for r in RULES for ln in textwrap.wrap(r, cpl)]
        pitch = pt * 0.3528 * RULE_LEADING
        if len(lines) * pitch <= height_mm:
            return (pt, lines, pitch)
        pt -= 0.1
    return best


def draw_sheet(spec: SheetSpec, pdf_path: Path, png_path: Path | None = None) -> list[Path]:
    """Lay one size out in matplotlib in sheet mm (y down) and write the PDF,
    plus a PNG when asked. Returns the paths written."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    MM = 1 / 25.4
    PT = 72 / 25.4      # points per mm, for line widths

    fig = plt.figure(figsize=(spec.page_w * MM, spec.page_h * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, spec.page_w)
    ax.set_ylim(spec.page_h, 0)         # y down
    ax.set_aspect("equal")
    ax.axis("off")

    # the window and its 1mm border
    fx0, fy0, fx1, fy1 = spec.field_rect()
    ax.add_patch(
        Rectangle((fx0, fy0), spec.field_w, spec.field_h, fill=False,
                  lw=FIELD_BORDER_W * PT, ec="black", joinstyle="miter")
    )

    # the tags: white quiet zone first, then the marker, then its id label in
    # the small gap toward the window (below a top tag, above a bottom tag) so
    # the label never lands outside the gutter
    for tid in spec.tag_ids:
        qx0, qy0, qx1, qy1 = spec.tag_mask(tid)
        ax.add_patch(Rectangle((qx0, qy0), qx1 - qx0, qy1 - qy0, fc="white", ec="none", zorder=5))
        tx, ty = spec.tag_origin(tid)
        ax.imshow(
            marker_image(tid),
            cmap="gray", vmin=0, vmax=255,
            extent=(tx, tx + spec.tag_mm, ty + spec.tag_mm, ty),   # left, right, bottom, top in a y-down frame
            interpolation="nearest", zorder=6,
        )
    # no "id N" caption under a marker: it collided with the size line under
    # the window, and that line already names the quartet

    # ---- the top tag band's corridor: the title, then the two hand boxes.
    # Type grows with the sheet, because a bigger sheet is read further away.
    k = spec.page_h / LETTER.page_h
    band_top = MARGIN
    box_h = min(BOX_H * k, BOX_H_BAND_FRAC * spec.tag_mm)
    title_band = spec.tag_mm - box_h
    title = f"CAPTURE SHEET  ·  {spec.name.replace('_', ' ')}  {spec.page_w:.0f} x {spec.page_h:.0f} mm"
    title_pt = _fit_font(spec.corridor_w - 6.0, title, title_band * 0.72 / 0.3528, per_char_em=0.62)
    ax.text(spec.corridor_x0 + 3.0, band_top + title_band / 2, title,
            ha="left", va="center", fontsize=title_pt, fontweight="bold")

    box_w = min(BOX_W_MAX * k, (spec.corridor_w - BOX_GAP * k) / 2)
    boxes_x = spec.corridor_x0 + (spec.corridor_w - (2 * box_w + BOX_GAP * k)) / 2
    box_y = band_top + spec.tag_mm - box_h
    for i, (label, blank) in enumerate((("TAG", "T0 _ _"), ("HEIGHT", "_ _"))):
        bx = boxes_x + i * (box_w + BOX_GAP * k)
        ax.add_patch(Rectangle((bx, box_y), box_w, box_h, fill=False, lw=0.5 * PT, ec="black"))
        ax.text(bx + 2 * k, box_y + box_h / 2, label, ha="left", va="center", fontsize=7 * k, fontweight="bold")
        ax.text(bx + box_w - 3 * k, box_y + box_h / 2, blank, ha="right", va="center", fontsize=11 * k, family="monospace")

    # ---- the strip under the window: what this sheet IS, and where it came
    # from. No tag reaches this band, so it runs the full printable width.
    strip_y = fy1 + BAND_GAP_BOT / 2
    strip_cap = BAND_GAP_BOT * 0.45 / 0.3528
    max_l, max_w = spec.max_tool()
    ax.text(MARGIN, strip_y,
            f"{spec.name.replace('_', ' ')}   window {spec.field_w:.0f} x {spec.field_h:.0f} mm   "
            f"largest tool {max_l:.0f} x {max_w:.0f}   corner squares {spec.tag_ids[0]}-{spec.tag_ids[3]}",
            ha="left", va="center", fontsize=min(5.5 * k, strip_cap), color="0.25")
    ax.text(spec.page_w - MARGIN, strip_y,
            "tool capture sheet v3, 2026-09-11  |  tools/trace_sheet.py",
            ha="right", va="center", fontsize=min(4.5 * k, strip_cap), color="0.5")

    # ---- the bottom tag band's corridor: the scale bar, the print check, the
    # rules. The type is sized so six rule lines fit the band's height and the
    # longest line fits the corridor's width.
    cb_top = spec.page_h - MARGIN - spec.tag_mm
    cb_bot = spec.page_h - MARGIN
    sx = spec.corridor_x0 + 3.0
    sy = cb_top + 3.2 * spec.tag_mm / LETTER.tag_mm
    ax.plot([sx, sx + SCALE_BAR_MM], [sy, sy], color="black", lw=0.6 * PT, solid_capstyle="butt")
    for x in (sx, sx + SCALE_BAR_MM):
        ax.plot([x, x], [sy - 2, sy + 2], color="black", lw=0.5 * PT)
    for i in range(1, 10):
        ax.plot([sx + 10 * i, sx + 10 * i], [sy - 1, sy + 1], color="black", lw=0.3 * PT)

    check_y = sy + 4.2 * spec.tag_mm / LETTER.tag_mm
    rules_top = check_y + 3.4 * spec.tag_mm / LETTER.tag_mm
    rule_pt, rule_lines, pitch = _layout_rules(
        spec.corridor_w, cb_bot - 1.0 - rules_top, RULE_FONT_PT * k
    )
    ax.text(sx, check_y, PRINT_CHECK_LINE, ha="left", va="center", fontsize=min(rule_pt, 6.0 * k))
    for i, line in enumerate(rule_lines):
        ax.text(sx, rules_top + (i + 0.5) * pitch, line, ha="left", va="center", fontsize=rule_pt)

    written = [pdf_path]
    fig.savefig(pdf_path, format="pdf")
    if png_path is not None:
        if shutil.which("pdftoppm"):
            stem = png_path.with_suffix("")
            subprocess.run(
                ["pdftoppm", "-r", str(RENDER_DPI), "-png", "-singlefile", str(pdf_path), str(stem)],
                check=True,
            )
        else:
            fig.savefig(png_path, format="png", dpi=RENDER_DPI)
        written.append(png_path)
    plt.close(fig)
    return written


def draw_card(pdf_path: Path) -> Path:
    """The laminated card: Letter, large type, one page."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    MM = 1 / 25.4
    W, H = LETTER.page_w, LETTER.page_h
    fig = plt.figure(figsize=(W * MM, H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    ax.text(14, 16, CARD_TITLE, fontsize=26, fontweight="bold", va="center", ha="left")
    ax.text(14, 26, CARD_SUB, fontsize=12, va="center", ha="left", color="0.35")
    ax.plot([14, W - 14], [32, 32], color="black", lw=1.5)
    y = 42
    for i, (word, text) in enumerate(CARD_STEPS, 1):
        ax.add_patch(FancyBboxPatch((14, y - 5), 10, 10, boxstyle="round,pad=0,rounding_size=2", fc="black", ec="none"))
        ax.text(19, y, str(i), fontsize=13, fontweight="bold", color="white", ha="center", va="center")
        ax.text(29, y - 1.5, word, fontsize=11.5, fontweight="bold", ha="left", va="center")
        ax.text(29, y + 6.0, text, fontsize=9, ha="left", va="top", wrap=True, linespacing=1.3)
        y += 32          # four steps, three lines of text each at most
    ax.plot([14, W - 14], [y - 10, y - 10], color="black", lw=1.5)
    ax.text(14, y - 3, "WHEN NOT TO PHOTOGRAPH", fontsize=11.5, fontweight="bold", ha="left", va="center")
    y += 5
    for word, text in CARD_EXCEPTIONS:
        ax.text(14, y, word, fontsize=9.5, fontweight="bold", ha="left", va="center")
        ax.text(14, y + 4.0, text, fontsize=9, ha="left", va="top", wrap=True, linespacing=1.3)
        y += 22
    ax.plot([14, W - 14], [y - 5, y - 5], color="black", lw=0.8)
    for j, line in enumerate(CARD_FOOT):
        ax.text(14, y + 2 + j * 7, line, fontsize=8.5, ha="left", va="center", color="0.15")
    ax.text(W - 14, H - 10, "tools/trace_sheet.py  |  capture card v3, 2026-09-11", fontsize=6, ha="right", va="center", color="0.5")
    # matplotlib wraps to the figure edge; keep the step text inside the gutter
    for t in ax.texts:
        t._get_wrap_line_width = lambda: (W - 29 - 14) * MM * fig.dpi
    fig.savefig(pdf_path, format="pdf")
    plt.close(fig)
    return pdf_path


# ================================================================ height classes

GAUGE_SLOTS = (10.0, 20.0, 30.0, 40.0, 50.0)
"""Slot widths, the height classes. SOURCE: spec v3. A tool whose thickness
slides into a slot is at most that class. The gauge's STL generator went with
the subtract pass (bd13c82, 2026-09-05); the block in Drawer 1, the sheet's
HEIGHT box and ``capture_ingest.HEIGHT_CLASSES`` all still read these five, so
the widths stay. CONFIDENCE: spec."""


# ================================================================ tracing collar

COLLAR_OD = 14.0
COLLAR_L = 25.0
COLLAR_CONTACT_H = 15.0
COLLAR_GRIP_OD = 13.0
COLLAR_BORE_AF = 7.2
COLLAR_TEXT_H = 4.0
COLLAR_TEXT_PROUD = 0.4
"""The collar. A 14.0 OD contact cylinder for the bottom 15mm, a 13.0 grip
above it carrying the word TRACE raised 0.4 (so the letters peak at 6.9
radius and never pass the contact cylinder's 7.0, whatever the tool's height
turns the collar against). The bore is a hexagon 7.2 across flats, clearance
on a standard 7mm hex pencil; the lead exits flush at the bottom face so the
contact edge and the lead tip are coplanar. SOURCE: ruling 2026-09-04 (the
pen is a pencil in a collar, so PEN_R is a design number, not a measurement).
CONFIDENCE: design; the printed part's OD is checked with calipers once and
``capture_ingest.PEN_R`` corrected if the printer runs fat or thin."""


def build_tracing_collar():
    """The collar as a build123d Part, bottom (contact) face on Z = 0."""
    import math

    from build123d import (
        Align,
        Cylinder,
        Location,
        Plane,
        RegularPolygon,
        Text,
        extrude,
    )

    contact = Cylinder(COLLAR_OD / 2, COLLAR_CONTACT_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    grip = Cylinder(COLLAR_GRIP_OD / 2, COLLAR_L - COLLAR_CONTACT_H, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, 0, COLLAR_CONTACT_H))
    )
    body = contact + grip
    # the hex bore: RegularPolygon takes the circumradius; across-flats / 2 / cos 30
    r_hex = COLLAR_BORE_AF / 2 / math.cos(math.radians(30))
    bore = extrude(RegularPolygon(r_hex, 6), amount=COLLAR_L + 2).moved(Location((0, 0, -1)))
    body -= bore

    # TRACE, one letter per tangent plane around the grip band, raised COLLAR_TEXT_PROUD
    word = "TRACE"
    r_grip = COLLAR_GRIP_OD / 2
    z_mid = COLLAR_CONTACT_H + (COLLAR_L - COLLAR_CONTACT_H) / 2
    step = math.radians(360 / len(word)) * 0.42          # letters over ~150 degrees of the collar
    start = -step * (len(word) - 1) / 2
    cap = Cylinder(r_grip + COLLAR_TEXT_PROUD, COLLAR_L - COLLAR_CONTACT_H, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, 0, COLLAR_CONTACT_H))
    )
    for i, ch in enumerate(word):
        a = start + i * step
        # tangent plane at angle a, its normal pointing outward, origin a hair inside the grip surface
        n = (math.cos(a), math.sin(a), 0)
        origin = (n[0] * (r_grip - 0.6), n[1] * (r_grip - 0.6), z_mid)
        pl = Plane(origin=origin, z_dir=n, x_dir=(-math.sin(a), math.cos(a), 0))
        glyph = extrude(pl * Text(ch, font_size=COLLAR_TEXT_H, align=(Align.CENTER, Align.CENTER)), amount=0.6 + COLLAR_TEXT_PROUD + 0.5)
        body += glyph & cap
    return body




# ================================================================ main

def sheet_paths(spec: SheetSpec, out_dir: Path = HERE) -> tuple[Path, Path]:
    """(pdf, png) for one size. LETTER keeps the v1 names as well, written by
    ``write_all``, so every link to ``trace_sheet.pdf`` still resolves."""
    return (out_dir / f"trace_sheet_{spec.slug}.pdf", out_dir / f"trace_sheet_{spec.slug}.png")


def write_sheets(sizes: list[SheetSpec], out_dir: Path = HERE) -> list[Path]:
    written: list[Path] = []
    for spec in sizes:
        pdf, png = sheet_paths(spec, out_dir)
        written += draw_sheet(spec, pdf, png)
        if spec is DEFAULT_SIZE:
            # the v1 names, byte-identical content, so nothing that points at
            # trace_sheet.pdf or trace_sheet.png has to be repointed
            for src, dst in ((pdf, out_dir / "trace_sheet.pdf"), (png, out_dir / "trace_sheet.png")):
                shutil.copyfile(src, dst)
                written.append(dst)
        print(f"  {spec.line()}")
    return written


def write_all(out_dir: Path = HERE, sizes: list[SheetSpec] | None = None, stl: bool = True) -> list[Path]:
    from lib.house import export_stl

    written = write_sheets(list(SIZES.values()) if sizes is None else sizes, out_dir)
    written.append(draw_card(out_dir / "capture_card.pdf"))
    if stl:
        for name, builder in (("tracing_collar.stl", build_tracing_collar),):
            part = builder()
            p = out_dir / name
            export_stl(part, p)
            bb = part.bounding_box()
            print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, {part.volume / 1000:.1f} cm3")
            written.append(p)
    return written


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="The trace sheet family, the capture card, the gauge and the collar.")
    parser.add_argument("--size", action="append", metavar="NAME",
                        help=f"one of {', '.join(SIZES)} (repeatable; default all of them)")
    parser.add_argument("--no-stl", action="store_true", help="skip the gauge and the collar")
    args = parser.parse_args()
    chosen = None
    if args.size:
        unknown = [s for s in args.size if s.upper() not in SIZES]
        if unknown:
            parser.error(f"unknown size(s) {', '.join(unknown)}; known: {', '.join(SIZES)}")
        chosen = [SIZES[s.upper()] for s in args.size]
    for p in write_all(sizes=chosen, stl=not args.no_stl):
        print(f"wrote {p}")
