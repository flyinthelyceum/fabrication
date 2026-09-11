"""Synthetic verification of the capture pipeline: the photo source (the
default since 2026-09-11) and the trace source (v1, kept for history).

    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/test_capture.py

No real photo is involved. The sheet PDF is rasterised at 300dpi, a known
shape is drawn on it, the page is put in front of a modelled phone, and the
ingest has to give the shape back.

PHOTO SOURCE

    P1. A phone (PHONE_W x PHONE_H, f35 = F35, EXIF written) held flat at
        D = 450 over the sheet, its nadir 30mm off the tool's centre, rolled
        5 degrees. A dark 50 x 100 stadium is rendered as a tool measured 20
        tall whose silhouette edge sits at h_eff = 10 (H_EFF_FRAC x 20), so
        it is drawn inflated about the nadir by D / (D - 10): 2.3% at the
        far end, with a soft shadow, a soft highlight streak and a lighter
        patch. Recovered L, W within 0.5mm of 100 x 50; D within 3% of 450.
    P2. The same with a pencil outline 3mm outside the tool, on the paper
        (a student who traced first). Same tolerance: the line is not the
        outline and does not move it.
    P3. Both sheet sizes through the photo path, identified from their
        quartets.
    P4. No EXIF (a PNG): the capture still runs, D falls back to 650, and
        the Result's reason says so.
    P5. Reject paths: a sheet with only a pencil loop (no tool in the
        window), a tool across the window edge, two tools, the phone at 250
        (too close), a 55mm height (no such class), a height that is not a
        number. Each rejects with its reason and writes nothing.

TRACE SOURCE (history; every call passes source="trace")

    0. The whole SHEET FAMILY, one size at a time: the size's own PDF is
       rasterised, a 50 x 100 stadium is drawn in its window, the page is
       warped as a phone would see it, and the ingest has to name the paper
       (from its ArUco quartet, never from an argument) and give the stadium
       back within 0.3mm. Six sizes, six quartets, one code path.
    1. A 50 x 100 stadium. The collar's axis runs PEN_R outside the tool, so
       the drawn line's CENTRELINE is the stadium offset by PEN_R (a 64 x 114
       stadium), 1mm wide. Perspective of about 20 degrees plus a small
       rotation. Recovered L, W must be within 0.3mm of 100 x 50.
    2. Print scale: the rendered sheet raster scaled to 94% (a printer that
       will not lay the sheet down at 100%), a real, unscaled 50 x 100
       stadium drawn on it at the density that scaled print actually has.
       Ingesting with print_scale=0.94 recovers 100 x 50 within 0.3mm; the
       same image ingested with the default print_scale=1.0 comes back about
       6% large, proving the failure ``print_scale`` fixes is real.
    3. Reject paths: two tags covered (one covered still rectifies, and the
       test says so), an open arc, two stadiums, two sheet SIZES in one frame,
       and a frame with no known quartet at all. Each rejects with its reason
       and writes nothing.
    4. Tray: the stadium's DXF as a CAPTURED row (T999, D2) in a COPY of the
       tool list, never the real one; trays.plan lays it out and the pocket's
       box is the pocket loop's box.

Every write goes to a temporary directory; the real captures/ and
tool_list.csv are untouched.
"""

from __future__ import annotations

import csv
import math
import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

from stations.cnc_shapeoko.tools import capture_ingest as ci
from stations.cnc_shapeoko.tools import trace_sheet as sheet

HERE = Path(__file__).resolve().parent
DPI = sheet.RENDER_DPI
PX = DPI / 25.4                      # rendered pixels per sheet mm

TOOL_L, TOOL_W = 100.0, 50.0         # the stadium: straight 50, radius 25
STROKE_MM = 1.0
TOL_MM = 0.3


def sheet_png(spec: sheet.SheetSpec = sheet.LETTER, tmp: Path | None = None) -> np.ndarray:
    """One size's page, rasterised at DPI. The committed PNG beside this file
    is used when it is there; otherwise the PDF is regenerated into ``tmp``."""
    png = HERE / f"trace_sheet_{spec.slug}.png"
    if not png.exists():
        out = tmp or HERE
        sheet.draw_sheet(spec, out / f"trace_sheet_{spec.slug}.pdf", out / f"trace_sheet_{spec.slug}.png")
        png = out / f"trace_sheet_{spec.slug}.png"
    img = cv2.imread(str(png), cv2.IMREAD_COLOR)
    assert img is not None, png
    assert abs(img.shape[1] / spec.page_w - PX) < 0.05, (img.shape, PX)
    return img


def stadium(cx: float, cy: float, l: float, w: float, n: int = 90) -> np.ndarray:
    """A stadium polyline (mm), long axis along X, dense enough to draw."""
    r = w / 2
    s = (l - w) / 2
    pts = []
    for i in range(n + 1):                       # right cap, -90 .. +90
        a = -math.pi / 2 + math.pi * i / n
        pts.append((cx + s + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(n + 1):                       # left cap, +90 .. +270
        a = math.pi / 2 + math.pi * i / n
        pts.append((cx - s + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


DRAW_SHIFT = 3
"""Fractional bits OpenCV's ``shift`` gives the drawn polyline: eighths of a
pixel. Rounding the stroke to whole pixels instead put up to half a pixel of
error into the caps of every synthetic stadium, and after the warp and the
rectification that showed up as a scatter of about 0.35mm in the recovered L,
which is the tolerance itself. It is the rasteriser's error, not the
pipeline's: the same stadium moved 3mm on the same sheet moved the error from
-0.34 to -0.12. Sub-pixel placement takes the whole family inside 0.23mm."""


def draw_stroke(img: np.ndarray, pts_mm: np.ndarray, closed: bool = True) -> None:
    px = np.round(pts_mm * PX * (1 << DRAW_SHIFT)).astype(np.int32)
    cv2.polylines(img, [px], closed, (40, 40, 40), max(int(round(STROKE_MM * PX)), 1),
                  cv2.LINE_AA, shift=DRAW_SHIFT)


def phone_warp(img: np.ndarray, seed: int = 1) -> np.ndarray:
    """About 20 degrees of keystone plus a few degrees of roll, on a grey
    desk, at a size a phone would produce."""
    h, w = img.shape[:2]
    tilt = math.radians(20)
    # a camera looking down at the sheet tilted about X: the far edge shrinks
    far = 1 - 0.5 * math.sin(tilt)          # ~0.83 of the near width
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([
        [w * (1 - far) / 2, 0], [w * (1 + far) / 2, 0],
        [w, h * 0.92], [0, h * 0.92],
    ])
    H = cv2.getPerspectiveTransform(src, dst)
    R = cv2.getRotationMatrix2D((w / 2, h / 2), 6.0, 0.9)
    R = np.vstack([R, [0, 0, 1]])
    T = np.array([[1, 0, 120], [0, 1, 160], [0, 0, 1]], dtype=np.float64)
    M = T @ R @ H
    out = cv2.warpPerspective(img, M, (w + 300, h + 300), flags=cv2.INTER_LINEAR, borderValue=(120, 120, 120))
    return out


# ---------------------------------------------------------------- the photo source's phone

F35 = 24.0
PHONE_W, PHONE_H = 3024, 4032
"""A phone's main camera: 24mm-equivalent, 4:3, portrait. What both
2026-09-11 photos carried."""

TOOL_H = 20.0
"""The synthetic tool's measured height. Its silhouette edge is rendered at
H_EFF_FRAC x this, which is the pipeline's own assumption, so the test
checks the correction's arithmetic, not the assumption (see
capture_ingest: THE PERSPECTIVE OF A TOOL ABOVE THE SHEET)."""

PHOTO_TOL_MM = 0.5

SHADOW = 0.12
"""How much darker than the paper the synthetic tool's shadow is: a soft
penumbra under diffuse shop light. A hard 25% shadow (one lamp, a flash) is
read as tool along its side by grabCut, about 1.4mm on the stadium, which is
why the card says no flash and no lamp shadow."""


def photo_case(name: str, tmp: Path, D: float, draw, spec: sheet.SheetSpec = sheet.LETTER,
               nadir: tuple[float, float] | None = None, roll: float = 5.0, exif: bool = True) -> Path:
    """A frame from a phone held flat at height ``D`` over the sheet, its
    optical axis through ``nadir`` (sheet mm), rolled ``roll`` degrees about
    that axis. ``draw(canvas, to_px)`` draws on the frame; ``to_px(pts_mm,
    h)`` maps sheet-mm points at height h above the paper to frame pixels by
    the pinhole model: C + (p - nadir) * f_px / (D - h). Written as JPEG with
    FocalLengthIn35mmFilm = F35 in its Exif IFD, or as PNG without EXIF."""
    page = sheet_png(spec, tmp)
    f_px = F35 * math.hypot(PHONE_W, PHONE_H) / ci.FRAME_DIAG_MM
    k0 = f_px / D
    C = np.array([PHONE_W / 2, PHONE_H / 2], dtype=np.float64)
    c_mm = np.array(nadir or (spec.page_w / 2, spec.page_h / 2), dtype=np.float64)
    canvas = np.full((PHONE_H, PHONE_W, 3), 120, np.uint8)
    small = cv2.resize(page, None, fx=k0 / PX, fy=k0 / PX, interpolation=cv2.INTER_AREA)
    tl = np.round(C - c_mm * k0).astype(int)
    assert tl.min() >= 0 and tl[1] + small.shape[0] <= PHONE_H and tl[0] + small.shape[1] <= PHONE_W, (tl, small.shape)
    canvas[tl[1]:tl[1] + small.shape[0], tl[0]:tl[0] + small.shape[1]] = small

    def to_px(pts_mm, h: float = 0.0) -> np.ndarray:
        return C + (np.asarray(pts_mm, dtype=np.float64) - c_mm) * (f_px / (D - h))

    draw(canvas, to_px)
    if roll:
        R = cv2.getRotationMatrix2D((float(C[0]), float(C[1])), roll, 1.0)
        canvas = cv2.warpAffine(canvas, R, (PHONE_W, PHONE_H), flags=cv2.INTER_LINEAR, borderValue=(120, 120, 120))
    if exif:
        from PIL import Image

        p = tmp / f"{name}.jpg"
        ex = Image.Exif()
        ex.get_ifd(0x8769)[0xA405] = int(F35)
        Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).save(p, quality=92, exif=ex.tobytes())
    else:
        p = tmp / f"{name}.png"
        cv2.imwrite(str(p), canvas)
    return p


def draw_photo_tool(canvas: np.ndarray, to_px, outline_mm: np.ndarray, h_edge: float,
                    pencil_out_mm: float | None = None, highlight: bool = True) -> None:
    """A dark tool with a soft shadow, a soft highlight streak along it and a
    lighter patch, its silhouette edge at ``h_edge``; optionally a pencil
    line on the paper ``pencil_out_mm`` outside it."""
    if pencil_out_mm is not None:
        cx, cy = outline_mm.mean(axis=0)
        ring = stadium(cx, cy, TOOL_L + 2 * pencil_out_mm, TOOL_W + 2 * pencil_out_mm)
        px = np.round(to_px(ring, 0.0) * (1 << DRAW_SHIFT)).astype(np.int32)
        k0 = np.linalg.norm(to_px((1, 0)) - to_px((0, 0)))
        cv2.polylines(canvas, [px], True, (110, 110, 110), max(int(round(0.8 * k0)), 1), cv2.LINE_AA, shift=DRAW_SHIFT)
    sh = np.zeros(canvas.shape[:2], np.float32)
    cv2.fillPoly(sh, [np.round(to_px(outline_mm + 1.5, 0.0)).astype(np.int32)], 1.0)
    sh = cv2.GaussianBlur(sh, (41, 41), 0)
    canvas[:] = (canvas.astype(np.float32) * (1 - SHADOW * sh[..., None])).astype(np.uint8)
    poly = np.round(to_px(outline_mm, h_edge) * (1 << DRAW_SHIFT)).astype(np.int32)
    cv2.fillPoly(canvas, [poly], (74, 72, 70), cv2.LINE_AA, shift=DRAW_SHIFT)
    if highlight:
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(to_px(outline_mm, h_edge).astype(np.float32))
        a = math.radians(ang + (90 if rw < rh else 0))
        L = max(rw, rh) * 0.8
        W = min(rw, rh)
        d = np.array([math.cos(a), math.sin(a)])
        n = np.array([-d[1], d[0]])
        c0 = np.array([cx, cy]) + n * W * 0.35
        hl = np.zeros(canvas.shape[:2], np.float32)
        cv2.line(hl, tuple(np.round(c0 - d * L / 2).astype(int)), tuple(np.round(c0 + d * L / 2).astype(int)), 1.0, max(int(W * 0.06), 3))
        hl = cv2.GaussianBlur(hl, (21, 21), 0)
        canvas[:] = np.clip(canvas.astype(np.float32) + hl[..., None] * (235 - 74), 0, 255).astype(np.uint8)
        patch = to_px(outline_mm.mean(axis=0) + np.array([[-8, -6], [8, -6], [8, 6], [-8, 6]]), h_edge)
        cv2.fillPoly(canvas, [np.round(patch).astype(np.int32)], (150, 148, 146), cv2.LINE_AA)


def field_centre(spec: sheet.SheetSpec = sheet.LETTER) -> tuple[float, float]:
    x0, y0, x1, y1 = spec.field_rect()
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def make_case(name: str, tmp: Path, draw, spec: sheet.SheetSpec = sheet.LETTER) -> Path:
    img = sheet_png(spec, tmp)
    draw(img)
    p = tmp / f"{name}.png"
    cv2.imwrite(str(p), phone_warp(img))
    return p


def assert_nothing_written(out: Path) -> None:
    files = [p for p in out.rglob("*") if p.is_file()]
    assert not files, f"a rejection wrote files: {files}"


def test_constants() -> None:
    """The two numbers the sheet and the ingest both have to agree on. They
    live in ``trace_sheet`` (the paper's geometry) and are mirrored in
    ``capture_ingest`` (the pipeline's); a silent divergence would move the
    crop or the collar offset on every size at once."""
    assert ci.FIELD_INSET == sheet.TRACE_INSET, (ci.FIELD_INSET, sheet.TRACE_INSET)
    assert ci.PEN_R == sheet.COLLAR_OD / 2, (ci.PEN_R, sheet.COLLAR_OD)
    print(f"  crop inset {ci.FIELD_INSET}mm and collar radius {ci.PEN_R}mm agree across both modules")


def test_family(tmp: Path) -> None:
    """Every size in the family, end to end. Nothing tells the ingest which
    paper it is looking at: the quartet does."""
    for spec in sheet.SIZES.values():
        cx, cy = field_centre(spec)
        centreline = stadium(cx, cy, TOOL_L + 2 * ci.PEN_R, TOOL_W + 2 * ci.PEN_R)
        img_path = make_case(f"family_{spec.slug}", tmp, lambda im: draw_stroke(im, centreline), spec)
        r = ci.ingest(img_path, "T999", 20, source="trace", out_dir=tmp / f"captures_{spec.slug}", csv_path=None)
        assert r.ok, f"{spec.name}: {r.reason}"
        assert r.size == spec.name, f"{spec.name}: identified as {r.size}"
        assert abs(r.L - TOOL_L) <= TOL_MM, f"{spec.name}: L {r.L:.3f} vs {TOOL_L} (tol {TOL_MM})"
        assert abs(r.W - TOOL_W) <= TOL_MM, f"{spec.name}: W {r.W:.3f} vs {TOOL_W} (tol {TOL_MM})"
        print(f"  {spec.name:<7} tags {spec.tag_ids[0]}-{spec.tag_ids[3]}, window "
              f"{spec.field_w:.0f} x {spec.field_h:.0f}: identified {r.size}, L {r.L:.3f} W {r.W:.3f}")


def test_synthetic_stadium(tmp: Path) -> tuple[Path, ci.Result]:
    cx, cy = field_centre()
    centreline = stadium(cx, cy, TOOL_L + 2 * ci.PEN_R, TOOL_W + 2 * ci.PEN_R)
    img_path = make_case("stadium", tmp, lambda im: draw_stroke(im, centreline))
    out = tmp / "captures_ok"
    csv_copy = tmp / "tool_list.csv"
    shutil.copy(HERE / "tool_list.csv", csv_copy)
    r = ci.ingest(img_path, "T999", 20, source="trace", out_dir=out, csv_path=csv_copy)
    assert r.ok, r.reason
    assert abs(r.L - TOOL_L) <= TOL_MM, f"L {r.L:.3f} vs {TOOL_L} (tol {TOL_MM})"
    assert abs(r.W - TOOL_W) <= TOL_MM, f"W {r.W:.3f} vs {TOOL_W} (tol {TOL_MM})"
    assert r.dxf_path.exists() and r.preview_path.exists()
    # the pocket loop is the tool plus FOAM_CLEAR a side
    from build123d import Wire, import_dxf
    wire = Wire.combine(import_dxf(str(r.dxf_path)))[0]
    assert wire.is_closed, "the pocket loop is not closed"
    bb = wire.bounding_box().size
    assert abs(bb.X - (TOOL_L + 2 * ci.FOAM_CLEAR)) <= TOL_MM, bb
    assert abs(bb.Y - (TOOL_W + 2 * ci.FOAM_CLEAR)) <= TOL_MM, bb
    # the row went into the COPY and nowhere else
    with csv_copy.open(newline="") as fh:
        rows = {r_["id"]: r_ for r_ in csv.DictReader(fh)}
    assert rows["T999"]["dims_status"] == "CAPTURED" and rows["T999"]["height_class"] == "20", rows["T999"]
    assert "T999" not in (HERE / "tool_list.csv").read_text()
    print(f"  stadium: L {r.L:.3f} W {r.W:.3f} (target {TOOL_L} x {TOOL_W}, tol {TOL_MM}); pocket box {bb.X:.3f} x {bb.Y:.3f}")
    return r.dxf_path, r


def test_print_scale(tmp: Path) -> None:
    """A sheet that printed at 94%, not 100%. The tags shrink with the print
    (they are printed ink); the stadium does not (it is a real tool, traced
    at its true size), so it is drawn at the ORIGINAL density (``PX``),
    positioned wherever the field centre landed once the raster shrank."""
    print_scale = 0.94
    img = sheet_png()
    h, w = img.shape[:2]
    scaled = cv2.resize(img, (int(round(w * print_scale)), int(round(h * print_scale))), interpolation=cv2.INTER_AREA)

    cx, cy = field_centre()
    centreline = stadium(cx, cy, TOOL_L + 2 * ci.PEN_R, TOOL_W + 2 * ci.PEN_R)
    centre_px_scaled = np.array([cx, cy]) * PX * print_scale
    pts_px = (centreline - np.array([cx, cy])) * PX + centre_px_scaled
    cv2.polylines(scaled, [np.round(pts_px).astype(np.int32)], True, (40, 40, 40), max(int(round(STROKE_MM * PX)), 1), cv2.LINE_AA)

    img_path = tmp / "print_scale_94.png"
    cv2.imwrite(str(img_path), scaled)

    r_corrected = ci.ingest(img_path, "T999", 20, source="trace", out_dir=tmp / "captures_scale_corrected", csv_path=None, print_scale=print_scale)
    assert r_corrected.ok, r_corrected.reason
    assert abs(r_corrected.L - TOOL_L) <= TOL_MM, f"L {r_corrected.L:.3f} vs {TOOL_L} (tol {TOL_MM})"
    assert abs(r_corrected.W - TOOL_W) <= TOL_MM, f"W {r_corrected.W:.3f} vs {TOOL_W} (tol {TOL_MM})"
    print(f"  print_scale={print_scale}: corrected L {r_corrected.L:.3f} W {r_corrected.W:.3f} (target {TOOL_L} x {TOOL_W}, tol {TOL_MM})")

    r_naive = ci.ingest(img_path, "T999", 20, source="trace", out_dir=tmp / "captures_scale_naive", csv_path=None)
    assert r_naive.ok, r_naive.reason
    expect_inflate = 1.0 / print_scale         # ~1.064, "about 6% large"
    got_inflate_l = r_naive.L / TOOL_L
    got_inflate_w = r_naive.W / TOOL_W
    # the uncorrected path also carries the small residual bias print_scale
    # exists to remove (a fixed real-mm offset applied inside the still-
    # inflated frame); the point here is that it is unmistakably inflated,
    # not that it lands on the theoretical 1/print_scale to the millimetre
    assert abs(got_inflate_l - expect_inflate) < 0.03, f"L inflation {got_inflate_l:.4f} vs expected {expect_inflate:.4f}"
    assert abs(got_inflate_w - expect_inflate) < 0.03, f"W inflation {got_inflate_w:.4f} vs expected {expect_inflate:.4f}"
    print(f"  print_scale=1.0 (uncorrected) on the same image: L {r_naive.L:.3f} W {r_naive.W:.3f}, {(got_inflate_l - 1) * 100:.1f}% / {(got_inflate_w - 1) * 100:.1f}% large -- the failure is real")


def test_rejects(tmp: Path) -> None:
    cx, cy = field_centre()
    centreline = stadium(cx, cy, TOOL_L + 2 * ci.PEN_R, TOOL_W + 2 * ci.PEN_R)

    def cover(im, ids):
        for tid in ids:
            x0, y0, x1, y1 = sheet.LETTER.tag_mask(tid)
            cv2.rectangle(im, (int(x0 * PX), int(y0 * PX)), (int(x1 * PX), int(y1 * PX)), (200, 190, 180), -1)

    def stamp_other_size(im, spec, ids):
        """Two of ANOTHER size's corner squares in the frame: the corner of a
        second sheet caught at the edge of the photo. Drawn inside the LETTER
        window, which is the only clear paper big enough to hold them."""
        for j, tid in enumerate(ids):
            m = cv2.cvtColor(sheet.marker_image(tid, int(round(spec.tag_mm * PX))), cv2.COLOR_GRAY2BGR)
            x = int((cx - 60 + j * 45) * PX)
            y = int((cy - 60) * PX)
            im[y:y + m.shape[0], x:x + m.shape[1]] = m

    cases = [
        ("two_tags_covered", lambda im: (draw_stroke(im, centreline), cover(im, (1, 2))), "corner squares found"),
        ("open_arc", lambda im: draw_stroke(im, centreline[: int(len(centreline) * 0.7)], closed=False), "not a closed loop"),
        ("two_stadiums", lambda im: (draw_stroke(im, stadium(cx - 50, cy, 60, 40)), draw_stroke(im, stadium(cx + 50, cy, 60, 40))), "two traces"),
        ("two_sheet_sizes", lambda im: (draw_stroke(im, centreline), stamp_other_size(im, sheet.SIZES["TABLOID"], (8, 9))), "two different sheet sizes in frame"),
        ("no_known_quartet", lambda im: (draw_stroke(im, centreline), cover(im, (0, 1, 2, 3))), "no known sheet size found"),
    ]
    for name, draw, expect in cases:
        img_path = make_case(name, tmp, draw)
        out = tmp / f"captures_{name}"
        csv_copy = tmp / f"tool_list_{name}.csv"
        shutil.copy(HERE / "tool_list.csv", csv_copy)
        before = csv_copy.read_bytes()
        r = ci.ingest(img_path, "T999", 20, source="trace", out_dir=out, csv_path=csv_copy)
        assert not r.ok, f"{name}: accepted, L {r.L} W {r.W}"
        assert expect in r.reason, f"{name}: wrong reason: {r.reason}"
        assert_nothing_written(out)
        assert csv_copy.read_bytes() == before, f"{name}: the CSV changed"
        print(f"  {name}: rejected, '{r.reason}'")

    # one tag covered still rectifies: three is the floor
    img_path = make_case("one_tag_covered", tmp, lambda im: (draw_stroke(im, centreline), cover(im, (2,))))
    r = ci.ingest(img_path, "T999", 20, source="trace", out_dir=tmp / "captures_one", csv_path=None)
    assert r.ok and abs(r.L - TOOL_L) <= TOL_MM and abs(r.W - TOOL_W) <= TOL_MM, r
    print(f"  one_tag_covered: accepted on three tags, L {r.L:.3f} W {r.W:.3f}")

    # the v2 plug
    try:
        ci.ingest(img_path, "T999", 20, source="camera")
    except NotImplementedError as e:
        assert "v2" in str(e)
        print(f"  source='camera': NotImplementedError('{e}')")
    else:
        raise AssertionError("source='camera' did not raise")


def _check_photo(r: ci.Result, D: float, label: str) -> None:
    assert r.ok, f"{label}: {r.reason}"
    assert abs(r.L - TOOL_L) <= PHOTO_TOL_MM, f"{label}: L {r.L:.3f} vs {TOOL_L} (tol {PHOTO_TOL_MM})"
    assert abs(r.W - TOOL_W) <= PHOTO_TOL_MM, f"{label}: W {r.W:.3f} vs {TOOL_W} (tol {PHOTO_TOL_MM})"
    assert abs(r.D - D) <= 0.03 * D, f"{label}: D {r.D:.1f} vs {D}"


def test_photo_stadium(tmp: Path) -> ci.Result:
    D = 450.0
    h_edge = ci.H_EFF_FRAC * TOOL_H
    cx, cy = field_centre()
    outline = stadium(cx, cy, TOOL_L, TOOL_W)
    nadir = (cx + 30, cy - 20)
    csv_copy = tmp / "tool_list_photo.csv"
    shutil.copy(HERE / "tool_list.csv", csv_copy)

    p = photo_case("photo_stadium", tmp, D, lambda im, to: draw_photo_tool(im, to, outline, h_edge), nadir=nadir)
    r = ci.ingest(p, "T999", "20mm", out_dir=tmp / "captures_photo", csv_path=csv_copy)
    _check_photo(r, D, "P1 stadium")
    assert r.height_class == 20.0 and r.reason == "", r
    from build123d import Wire, import_dxf
    wire = Wire.combine(import_dxf(str(r.dxf_path)))[0]
    bb = wire.bounding_box().size
    assert abs(bb.X - (TOOL_L + 2 * ci.FOAM_CLEAR)) <= PHOTO_TOL_MM and abs(bb.Y - (TOOL_W + 2 * ci.FOAM_CLEAR)) <= PHOTO_TOL_MM, bb
    with csv_copy.open(newline="") as fh:
        rows = {r_["id"]: r_ for r_ in csv.DictReader(fh)}
    assert rows["T999"]["height_class"] == "20" and rows["T999"]["bbox_h_mm"] == "20" and rows["T999"]["dims_status"] == "CAPTURED", rows["T999"]
    assert "T999" not in (HERE / "tool_list.csv").read_text()
    print(f"  P1 stadium at D {D:g}, edge at {h_edge:g}: L {r.L:.3f} W {r.W:.3f}, D read {r.D:.1f}, pocket box {bb.X:.3f} x {bb.Y:.3f}, class {r.height_class:g}, bbox_h_mm 20")
    seen = TOOL_L * D / (D - h_edge)
    print(f"  (uncorrected the stadium would read L {seen:.2f}: the correction is worth {seen - TOOL_L:.2f}mm here)")

    p = photo_case("photo_stadium_pencil", tmp, D, lambda im, to: draw_photo_tool(im, to, outline, h_edge, pencil_out_mm=3.0), nadir=nadir)
    r2 = ci.ingest(p, "T999", 20, out_dir=tmp / "captures_photo_pencil", csv_path=None)
    _check_photo(r2, D, "P2 stadium with pencil ring")
    print(f"  P2 with a pencil ring 3mm outside: L {r2.L:.3f} W {r2.W:.3f}")
    return r


def test_photo_family(tmp: Path) -> None:
    D = 450.0
    h_edge = ci.H_EFF_FRAC * TOOL_H
    for spec in sheet.SIZES.values():
        cx, cy = field_centre(spec)
        outline = stadium(cx, cy, TOOL_L, TOOL_W)
        p = photo_case(f"photo_family_{spec.slug}", tmp, D, lambda im, to: draw_photo_tool(im, to, outline, h_edge), spec=spec, nadir=(cx + 25, cy + 15))
        r = ci.ingest(p, "T999", 20, out_dir=tmp / f"captures_photo_{spec.slug}", csv_path=None)
        _check_photo(r, D, f"P3 {spec.name}")
        assert r.size == spec.name, r.size
        print(f"  P3 {spec.name:<7}: identified {r.size}, L {r.L:.3f} W {r.W:.3f}, D read {r.D:.1f}")


def test_photo_no_exif(tmp: Path) -> None:
    D = ci.D_FALLBACK_MM
    h_edge = ci.H_EFF_FRAC * TOOL_H
    cx, cy = field_centre()
    outline = stadium(cx, cy, TOOL_L, TOOL_W)
    p = photo_case("photo_no_exif", tmp, D, lambda im, to: draw_photo_tool(im, to, outline, h_edge), nadir=(cx + 30, cy - 20), exif=False)
    r = ci.ingest(p, "T999", 20, out_dir=tmp / "captures_photo_noexif", csv_path=None)
    _check_photo(r, D, "P4 no EXIF")
    assert "camera height assumed 650" in r.reason, r.reason
    assert "camera height assumed 650" in r.line()
    print(f"  P4 PNG without EXIF: L {r.L:.3f} W {r.W:.3f}, reason '{r.reason}'")


def test_photo_rejects(tmp: Path) -> None:
    D = 450.0
    h_edge = ci.H_EFF_FRAC * TOOL_H
    cx, cy = field_centre()
    x0, y0, x1, y1 = sheet.LETTER.field_rect()
    outline = stadium(cx, cy, TOOL_L, TOOL_W)

    def pencil_only(im, to):
        ring = stadium(cx, cy, TOOL_L + 6, TOOL_W + 6)
        px = np.round(to(ring, 0.0) * (1 << DRAW_SHIFT)).astype(np.int32)
        k0 = np.linalg.norm(to((1, 0)) - to((0, 0)))
        cv2.polylines(im, [px], True, (110, 110, 110), max(int(round(1.5 * k0)), 1), cv2.LINE_AA, shift=DRAW_SHIFT)
        cv2.polylines(im, [px + 3], True, (120, 120, 120), max(int(round(1.0 * k0)), 1), cv2.LINE_AA, shift=DRAW_SHIFT)

    cases = [
        ("photo_pencil_only", D, pencil_only, "20", "no tool found"),
        ("photo_edge", D, lambda im, to: draw_photo_tool(im, to, stadium(x1 - 40, cy, TOOL_L, TOOL_W), h_edge), "20", "touches the edge"),
        ("photo_two_tools", D, lambda im, to: (draw_photo_tool(im, to, stadium(cx, cy - 40, 60, 40), h_edge), draw_photo_tool(im, to, stadium(cx, cy + 40, 60, 40), h_edge)), "20", "two tools"),
        ("photo_too_close", 250.0, lambda im, to: draw_photo_tool(im, to, outline, h_edge), "20", "camera too close"),
        ("photo_too_tall", D, lambda im, to: draw_photo_tool(im, to, outline, h_edge), "55", "tallest class"),
        ("photo_height_nan", D, lambda im, to: draw_photo_tool(im, to, outline, h_edge), "tall", "not a number"),
    ]
    for name, d, draw, height, expect in cases:
        p = photo_case(name, tmp, d, draw, roll=0.0 if d < 300 else 5.0)
        out = tmp / f"captures_{name}"
        csv_copy = tmp / f"tool_list_{name}.csv"
        shutil.copy(HERE / "tool_list.csv", csv_copy)
        before = csv_copy.read_bytes()
        r = ci.ingest(p, "T999", height, out_dir=out, csv_path=csv_copy)
        assert not r.ok, f"{name}: accepted, L {r.L} W {r.W}"
        assert expect in r.reason, f"{name}: wrong reason: {r.reason}"
        assert_nothing_written(out)
        assert csv_copy.read_bytes() == before, f"{name}: the CSV changed"
        print(f"  {name}: rejected, '{r.reason}'")


def test_tray(tmp: Path, dxf_path: Path) -> None:
    from stations.cnc_shapeoko.parts import trays

    csv_copy = tmp / "tool_list_tray.csv"
    shutil.copy(HERE / "tool_list.csv", csv_copy)
    rows = trays.read_tools(csv_copy)
    rows.append(
        trays.ToolRow(
            id="T999", name="TEST STADIUM", drawer="D2", kind="block",
            shank_d=None, cut_d=None, oal=None, qty=1,
            dims_status="CAPTURED", height_class=20.0, silhouette=str(dxf_path),
        )
    )
    p = trays.plan("D2", rows=rows)
    pk = [k for k in p.pockets if k.tool_id == "T999"]
    assert len(pk) == 1, [k.tool_id for k in p.pockets]
    pk = pk[0]
    assert pk.rule == "captured", pk.rule
    exp_l, exp_w = TOOL_L + 2 * ci.FOAM_CLEAR, TOOL_W + 2 * ci.FOAM_CLEAR
    got = (pk.pd, pk.pw) if pk.rotated else (pk.pw, pk.pd)
    assert abs(got[0] - exp_l) <= TOL_MM and abs(got[1] - exp_w) <= TOL_MM, (got, exp_l, exp_w)
    assert abs(pk.depth - min(20.0 + trays.FOAM_DEPTH_ALLOW, trays.FOAM_T - trays.FOAM_FLOOR_MIN)) < 1e-6, pk.depth
    faces = pk.outline().faces()
    assert len(faces) == 1, len(faces)
    # the loop plus its finger scoop, opened by the endmill radius, is one face bigger than the pocket alone
    assert faces[0].area > exp_l * exp_w * 0.9
    layers = trays.layers(p)
    assert any(k.startswith("POCKET_D") for k in layers), list(layers)
    notes = [n for n in trays.check_trays(rows=rows) if "T999" in n]
    assert not notes, notes
    print(f"  tray D2: T999 pocket {got[0]:.2f} x {got[1]:.2f} x {pk.depth:g} deep at ({pk.x:.1f}, {pk.y:.1f}), {len(p.pockets)} pocket(s), no T999 notes")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="capture_test_"))
    print(f"scratch: {tmp}")
    print("PHOTO SOURCE (default)")
    print("P1/P2. a tool on the sheet, D 450, nadir off-centre, with and without a pencil ring")
    rp = test_photo_stadium(tmp)
    print("P3. both sheet sizes")
    test_photo_family(tmp)
    print("P4. no EXIF")
    test_photo_no_exif(tmp)
    print("P5. reject paths")
    test_photo_rejects(tmp)
    print("TRACE SOURCE (history)")
    print("0a. the two shared constants")
    test_constants()
    print("0b. the sheet family: every size, identified from its own quartet")
    test_family(tmp)
    print("1. synthetic stadium, 20 deg perspective + 6 deg roll")
    dxf_path, r = test_synthetic_stadium(tmp)
    print("2. print scale: a 94% print, corrected vs. uncorrected")
    test_print_scale(tmp)
    print("3. reject paths")
    test_rejects(tmp)
    print("4. tray with one CAPTURED row")
    test_tray(tmp, dxf_path)
    print(f"ALL PASSED   (example previews: photo {rp.preview_path}, trace {r.preview_path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
