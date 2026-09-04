"""The trace sheet, the height gauge and the tracing collar: the three physical
things a tool capture needs (spec v3, 2026-09-04).

    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/trace_sheet.py

writes, beside this file:

    trace_sheet.pdf     Letter, print at 100%. Four ArUco tags (DICT_4X4_50,
                        ids 0-3, 30mm), a 180 x 180 trace field with a 1mm
                        border, the TAG / HEIGHT boxes, the rule line, a
                        100mm scale bar for the human check, all of it inside
                        a 14mm margin.
    trace_sheet.png     the same page rasterised (pdftoppm at RENDER_DPI when
                        it is on the box, else matplotlib), for a look and
                        for the synthetic test.
    height_gauge.stl    the go/no-go height gauge: a block with five slots,
                        10/20/30/40/50 wide, open at the top and through the
                        block's depth. A tool that slides into the 20 and not
                        the 10 is height class 20. Labels embossed.
    tracing_collar.stl  the TRACE collar: a 14.0 OD cylinder a standard hex
                        pencil rides in, so the contact surface against the
                        tool is a cylinder of known radius whatever the tool's
                        height or the pencil's taper. PEN_R in
                        ``capture_ingest`` is this collar's radius.
    capture_card.pdf    the laminated card: the procedure in large type, one
                        page, for Drawer 1 beside the sheets.

THE 14mm MARGIN
================

Jared's printer will not lay this sheet down at 100% inside a smaller
margin: it produced gutters, which forced a scaled print, and a scaled print
breaks the tag-based mm mapping by exactly the scale factor (fixed on the
ingest side with ``capture_ingest``'s ``print_scale``, but the sheet should
not need it). Every element on the page -- tags, field, boxes, rule line,
scale bar -- sits inside ``MARGIN`` from the page edge, on all four sides.

The four tags sit at the four corners of that printable area (``TAG_MARGIN
== MARGIN``), and the trace field is sized and placed so it is CLEAR of the
tags -- no overlap, unlike the v3 sheet this replaces. The tags occupy only
the top and bottom 30mm bands of the page; the field lives entirely in the
191.4mm of clear paper between those two bands. The corridor between the
tags in those top and bottom bands (``CORRIDOR_X0``..``CORRIDOR_X1``) is
where the hand-filled boxes, the rule line and the scale bar live, clear of
the tags' quiet zones so no ink ever touches a marker.

SHEET FRAME
===========

Every constant here is in SHEET MM: origin at the page's top-left corner, x
to the right, y DOWN, like an image. The ingest's homography maps a photo
into this frame at ``capture_ingest.PX_PER_MM``; the tag corners it uses are
``tag_corners()`` below, so the geometry the printer lays down and the
geometry the ingest assumes come from one place.

ArUco's corner order for an upright marker is top-left, top-right,
bottom-right, bottom-left; ``tag_corners`` returns that order in this frame,
and the markers are drawn upright on the page, so corner i of a detection
matches corner i here without a permutation.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

# ================================================================ the sheet

PAGE_W, PAGE_H = 215.9, 279.4
"""US Letter. SOURCE: the paper in the Innovation Commons printers.
CONFIDENCE: fact."""

MARGIN = 14.0
"""Printable margin, page edge to the nearest ink, on all four sides.
SOURCE: Jared's printer would not lay the v3 sheet (6mm margin) down at
100%; it produced gutters, forcing a scaled print, which breaks the
tag-based mm mapping by the scale factor. 14mm clears that printer's
unprintable band. CONFIDENCE: fact, from the failed print (ruling
2026-09-04)."""

PRINTABLE_W = PAGE_W - 2 * MARGIN
PRINTABLE_H = PAGE_H - 2 * MARGIN
"""The printable area: 187.9 x 251.4. Nothing is drawn outside it."""

ARUCO_DICT = "DICT_4X4_50"
TAG_IDS = (0, 1, 2, 3)
TAG_MM = 30.0
"""Marker side, black square to black square. SOURCE: spec v3. A 4x4 marker
is six cells a side including its border, five millimetres a cell, which a
phone resolves from arm's length. CONFIDENCE: spec."""

TAG_MARGIN = MARGIN
"""Page edge to the marker's black square: the tags sit at the printable
area's own four corners. CONFIDENCE: rule."""

TAG_QUIET = 3.0
"""White kept clear around each marker; ArUco wants a quiet zone of at least
one cell (5mm here would be ideal, 3 detects reliably and keeps the field).
CONFIDENCE: rule."""

TAG_ORIGIN: dict[int, tuple[float, float]] = {
    0: (TAG_MARGIN, TAG_MARGIN),
    1: (PAGE_W - TAG_MARGIN - TAG_MM, TAG_MARGIN),
    2: (PAGE_W - TAG_MARGIN - TAG_MM, PAGE_H - TAG_MARGIN - TAG_MM),
    3: (TAG_MARGIN, PAGE_H - TAG_MARGIN - TAG_MM),
}
"""Top-left corner of each marker's black square, sheet mm. Ids run
clockwise from the page's top-left."""

CORRIDOR_X0 = TAG_MARGIN + TAG_MM + TAG_QUIET
CORRIDOR_X1 = PAGE_W - TAG_MARGIN - TAG_MM - TAG_QUIET
"""The clear paper between the left and right tags' quiet zones (47..168.9),
in the top and bottom 30mm tag bands. Every hand box, the rule line and the
scale bar sit inside this corridor so no ink ever touches a marker or its
quiet zone."""

FIELD_W, FIELD_H = 180.0, 180.0
FIELD_X0 = (PAGE_W - FIELD_W) / 2
FIELD_Y0 = 48.0
"""The trace field: 180 x 180, centred across the page, from y 48 to 228.
The top tags' band ends at 44, the bottom tags' band starts at 235.4: the
field sits with a clear 4mm gap below the top tags and a clear 7.4mm gap
above the bottom tags, touching neither. SOURCE: spec v3 for the shape (a
traced tool, not a printer margin), shrunk and moved 2026-09-04 so the field
clears the tags outright instead of hiding under them."""

FIELD_BORDER_W = 1.0
"""The field's border line, centred on the field boundary. The ingest crops
inside it (``capture_ingest.FIELD_INSET``) so the line is never a contour."""

BOX_H = 16.0
BOX_Y = 20.0
TAG_BOX = (48.0, BOX_Y, 52.0, BOX_H)        # x, y, w, h
HEIGHT_BOX = (114.0, BOX_Y, 52.0, BOX_H)
"""The two hand-filled boxes in the top tag band's corridor (x 47..168.9),
clear of the tags on either side. Written by hand, read by a human: the Form
carries the same two values for the machine."""

SCALE_BAR = (CORRIDOR_X0 + 3.0, 241.0, 100.0)
"""x, y, length of the scale bar, in the bottom tag band's corridor. Print
at 100% and this measures 100 with a ruler; if it does not, the sheet is
scaled and every capture from it is wrong by the same ratio."""

PRINT_CHECK_LINE = (
    "Print at 100%.  If this bar is not 100mm, write the measured length "
    "here: ____ mm"
)
"""Printed directly under the scale bar, so a scaled print is caught by eye
and a ruler before a single tool is traced. SOURCE: ruling 2026-09-04."""

RULE_LINE = (
    "ONE TOOL, lying as it sits in the drawer.  Pencil in the TRACE collar, "
    "straight up like a candle, collar riding the tool.  Trace the OUTSIDE only."
)
"""The whole procedure, on the sheet, where the hand is. SOURCE: spec v3,
amended 2026-09-04 for the collar."""

RENDER_DPI = 300

CARD_TITLE = "CNC TRAY CAPTURE"
CARD_SUB = "one tool, about ninety seconds"
CARD_STEPS = (
    ("SHEET", "Take a fresh trace sheet from the stack. Write the tool's TAG (T0__, from the drawer label) in the TAG box."),
    ("HEIGHT", "Slide the tool edge-on into the gauge. The smallest slot it enters is its height: 10, 20, 30, 40 or 50. Write it in the HEIGHT box."),
    ("LAY", "Lay the tool inside the field, as it sits in the drawer. Clear of the border line and of the four corner squares."),
    ("TRACE", "Pencil in the TRACE collar. Straight up like a candle, collar riding the tool. Trace the OUTSIDE only, all the way round, until the line meets itself."),
    ("PHOTO", "Lift the tool off. Photograph the whole sheet from above: all four corner squares in frame, sheet flat, no shadow across the line."),
    ("FORM", "Open the form \u201cCNC tray capture\u201d: tag, height, photo. Done. The tray regenerates; a rejected sheet comes back with one line saying why."),
)
CARD_FOOT = (
    "One tool per sheet.  Never a hand in the field, never a tool on its edge, never a tool that moved.",
    "Sheets, collar, pencil and gauge live in Drawer 1.  Print sheets at 100%: the bar at the bottom must measure 100mm.",
)
"""The card, verbatim. It is the spec's rule line unfolded into the six
things a hand does, in the order it does them. SOURCE: spec v3, amended
2026-09-04 for the collar."""


def tag_corners(tag_id: int) -> np.ndarray:
    """The four corners of one marker's black square, sheet mm, in ArUco's
    order: top-left, top-right, bottom-right, bottom-left."""
    x0, y0 = TAG_ORIGIN[tag_id]
    return np.array(
        [[x0, y0], [x0 + TAG_MM, y0], [x0 + TAG_MM, y0 + TAG_MM], [x0, y0 + TAG_MM]],
        dtype=np.float64,
    )


def tag_masks() -> list[tuple[float, float, float, float]]:
    """(x0, y0, x1, y1) per marker, the black square plus its quiet zone:
    what the ingest whites out of the field."""
    out = []
    for tid in TAG_IDS:
        x0, y0 = TAG_ORIGIN[tid]
        out.append((x0 - TAG_QUIET, y0 - TAG_QUIET, x0 + TAG_MM + TAG_QUIET, y0 + TAG_MM + TAG_QUIET))
    return out


def field_rect() -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) of the trace field, sheet mm."""
    return (FIELD_X0, FIELD_Y0, FIELD_X0 + FIELD_W, FIELD_Y0 + FIELD_H)


def marker_image(tag_id: int, px: int = 600) -> np.ndarray:
    """One ArUco marker as a uint8 image, 0 black / 255 white."""
    import cv2

    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, ARUCO_DICT))
    return cv2.aruco.generateImageMarker(d, tag_id, px)


def draw_sheet(pdf_path: Path, png_path: Path | None = None) -> list[Path]:
    """Lay the page out in matplotlib in sheet mm (y down) and write the PDF,
    plus a PNG when asked. Returns the paths written."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    MM = 1 / 25.4
    PT = 72 / 25.4      # points per mm, for line widths

    fig = plt.figure(figsize=(PAGE_W * MM, PAGE_H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(PAGE_H, 0)         # y down
    ax.set_aspect("equal")
    ax.axis("off")

    # the field and its 1mm border
    x0, y0, x1, y1 = field_rect()
    ax.add_patch(
        Rectangle((x0, y0), FIELD_W, FIELD_H, fill=False, lw=FIELD_BORDER_W * PT, ec="black", joinstyle="miter")
    )

    # the tags: white quiet zone first, then the marker, then its id label in
    # the small gap toward the field (below a top tag, above a bottom tag) so
    # the label never lands outside the margin
    for tid in TAG_IDS:
        qx0, qy0, qx1, qy1 = tag_masks()[tid]
        ax.add_patch(Rectangle((qx0, qy0), qx1 - qx0, qy1 - qy0, fc="white", ec="none", zorder=5))
        tx, ty = TAG_ORIGIN[tid]
        ax.imshow(
            marker_image(tid),
            cmap="gray", vmin=0, vmax=255,
            extent=(tx, tx + TAG_MM, ty + TAG_MM, ty),   # left, right, bottom, top in a y-down frame
            interpolation="nearest", zorder=6,
        )
        top_row = ty < PAGE_H / 2
        label_y = ty + TAG_MM + 2.2 if top_row else ty - 2.2
        ax.text(tx + TAG_MM / 2, label_y, f"id {tid}", ha="center", va="top" if top_row else "bottom", fontsize=5, color="0.4", zorder=7)

    # the two hand boxes
    for (bx, by, bw, bh), label, blank in ((TAG_BOX, "TAG", "T0 _ _"), (HEIGHT_BOX, "HEIGHT", "_ _")):
        ax.add_patch(Rectangle((bx, by), bw, bh, fill=False, lw=0.5 * PT, ec="black"))
        ax.text(bx + 2, by + bh / 2, label, ha="left", va="center", fontsize=7, fontweight="bold")
        ax.text(bx + bw - 3, by + bh / 2, blank, ha="right", va="center", fontsize=11, family="monospace")

    # the scale bar, in the bottom tag band's corridor
    sx, sy, sl = SCALE_BAR
    ax.plot([sx, sx + sl], [sy, sy], color="black", lw=0.6 * PT, solid_capstyle="butt")
    for x in (sx, sx + sl):
        ax.plot([x, x], [sy - 2, sy + 2], color="black", lw=0.5 * PT)
    for i in range(1, 10):
        ax.plot([sx + 10 * i, sx + 10 * i], [sy - 1, sy + 1], color="black", lw=0.3 * PT)

    # the print-scale check line, directly under the bar
    ax.text(sx, sy + 7.0, PRINT_CHECK_LINE, ha="left", va="center", fontsize=5.5)

    # the rule line, two lines of small type below that, still inside the corridor
    ax.text(sx, sy + 15.5, RULE_LINE[: RULE_LINE.index("Pencil")].strip(), ha="left", va="center", fontsize=6)
    ax.text(sx, sy + 21.0, RULE_LINE[RULE_LINE.index("Pencil"):].strip(), ha="left", va="center", fontsize=6)

    # provenance, tiny, in the top corridor's spare band under the boxes
    ax.text(CORRIDOR_X1, BOX_Y + BOX_H + 5.5, "CNC station tool capture sheet v1, 2026-09-04  |  tools/trace_sheet.py", ha="right", va="center", fontsize=4, color="0.4")

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
    fig = plt.figure(figsize=(PAGE_W * MM, PAGE_H * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(PAGE_H, 0)
    ax.axis("off")
    ax.text(14, 18, CARD_TITLE, fontsize=30, fontweight="bold", va="center", ha="left")
    ax.text(14, 30, CARD_SUB, fontsize=13, va="center", ha="left", color="0.35")
    ax.plot([14, PAGE_W - 14], [37, 37], color="black", lw=1.5)
    y = 50
    for i, (word, text) in enumerate(CARD_STEPS, 1):
        ax.add_patch(FancyBboxPatch((14, y - 6), 12, 12, boxstyle="round,pad=0,rounding_size=2", fc="black", ec="none"))
        ax.text(20, y, str(i), fontsize=15, fontweight="bold", color="white", ha="center", va="center")
        ax.text(31, y - 1.5, word, fontsize=13, fontweight="bold", ha="left", va="center")
        ax.text(31, y + 8.5, text, fontsize=10.5, ha="left", va="top", wrap=True, linespacing=1.35)
        y += 34
    ax.plot([14, PAGE_W - 14], [y - 12, y - 12], color="black", lw=1.5)
    for j, line in enumerate(CARD_FOOT):
        ax.text(14, y - 4 + j * 9, line, fontsize=9.5, ha="left", va="center", color="0.15")
    ax.text(PAGE_W - 14, PAGE_H - 10, "tools/trace_sheet.py  |  capture card v1, 2026-09-04", fontsize=6, ha="right", va="center", color="0.5")
    # matplotlib wraps to the figure edge; keep the step text inside the margin
    for t in ax.texts:
        t._get_wrap_line_width = lambda: (PAGE_W - 31 - 14) * MM * fig.dpi
    fig.savefig(pdf_path, format="pdf")
    plt.close(fig)
    return pdf_path


# ================================================================ height gauge

GAUGE_SLOTS = (10.0, 20.0, 30.0, 40.0, 50.0)
"""Slot widths, the height classes. SOURCE: spec v3. A tool whose thickness
slides into a slot is at most that class. CONFIDENCE: spec."""

GAUGE_WALL = 5.0
GAUGE_D = 60.0
GAUGE_H = 60.0
GAUGE_FLOOR = 15.0
GAUGE_L = sum(GAUGE_SLOTS) + GAUGE_WALL * (len(GAUGE_SLOTS) + 1)
"""The block: 180 x 60 x 60. The brief said 120 long; five slots totalling
150mm of width plus six 5mm walls need 180, so the length is what the slots
demand and the deviation is recorded here rather than hidden by narrowing a
slot. Slots are 45 deep (60 less a 15 floor) and run through the block's
60mm depth so a long tool passes straight through. Fits the AD5M bed with
its margin. CONFIDENCE: derived from the spec's five widths."""

GAUGE_LABEL_H = 8.0
GAUGE_LABEL_PROUD = 0.8


def build_height_gauge():
    """The gauge as a build123d Part, standing on Z = 0 in print orientation."""
    from build123d import (
        Align,
        Box,
        Location,
        Plane,
        Text,
        extrude,
    )

    block = Box(GAUGE_L, GAUGE_D, GAUGE_H, align=(Align.MIN, Align.MIN, Align.MIN))
    x = GAUGE_WALL
    for w in GAUGE_SLOTS:
        slot = Box(w, GAUGE_D + 2, GAUGE_H - GAUGE_FLOOR, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
            Location((x, -1, GAUGE_FLOOR))
        )
        block -= slot
        # the label, embossed on the front face (y = 0) under its slot
        txt = Text(f"{w:g}", font_size=GAUGE_LABEL_H, align=(Align.CENTER, Align.CENTER))
        glyphs = extrude(Plane.XZ * txt, amount=GAUGE_LABEL_PROUD)      # Plane.XZ's normal is -Y, so this stands proud of the front face
        block += glyphs.moved(Location((x + w / 2, 0, GAUGE_FLOOR / 2)))
        x += w + GAUGE_WALL
    return block


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

def write_all(out_dir: Path = HERE) -> list[Path]:
    from lib.house import export_stl

    written = draw_sheet(out_dir / "trace_sheet.pdf", out_dir / "trace_sheet.png")
    written.append(draw_card(out_dir / "capture_card.pdf"))
    for name, builder in (("height_gauge.stl", build_height_gauge), ("tracing_collar.stl", build_tracing_collar)):
        part = builder()
        p = out_dir / name
        export_stl(part, p)
        bb = part.bounding_box()
        print(f"{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f}, {part.volume / 1000:.1f} cm3")
        written.append(p)
    return written


if __name__ == "__main__":
    for p in write_all():
        print(f"wrote {p}")
