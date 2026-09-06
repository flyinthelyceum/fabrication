"""Tool capture ingest: a photo of a traced sheet in, a pocket polyline out.

    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/capture_ingest.py <image> <tag> <height> [--print-scale S]

    ingest(image_path, tag, height_slot, source="trace", print_scale=1.0) -> Result

The v1 image source is a phone photo of ``trace_sheet.pdf`` with one tool's
outline drawn on it by a pencil riding in the TRACE collar. Because the trace
lies on the sheet's plane, four ArUco tags rectify it completely: no camera
height, no tilt, no parallax, no lighting model. ``source="camera"`` is the
v2 plug (the machine's own Z-plate camera over a fiducial mat) and raises
until it is built.

PIPELINE
========

    ArUco detect (DICT_4X4_50) -> which SHEET SIZE is in the frame, from the
       quartet of ids the markers belong to (``trace_sheet.SIZE_FOR_TAG``);
       reject on two quartets, on none, or on fewer than MIN_TAGS of the one
       that is there
    -> homography from the detected corners to that size's sheet mm at
       PX_PER_MM (``SheetSpec.tag_corners`` is the only source of those
       positions)
    -> warp the photo into the sheet frame, crop the trace field inside its
       border line, white out any tag square that overlaps the crop (the
       14mm-margin sheet keeps the field clear of the tags, so this is
       normally a no-op)
    -> flatten the lighting (divide by a wide blur), invert, Otsu, close 2px
    -> contours with holes (RETR_CCOMP): the top-level contours are the
       candidate traces; the largest is the tool
    -> reject: a second top-level contour over SECOND_FRAC of the largest
       (two tools); the largest touching the crop edge (ran off the field);
       no hole inside the largest (an open trace)
    -> the pencil line has a width; it is estimated from the trace itself,
       (outer area - hole area) / mean perimeter, so the stroke's centreline
       is the outer contour inset by half of that. The centreline is where
       the collar's axis went: the tool's outline is that, inset by PEN_R
    -> Douglas-Peucker at DP_TOL on the outer contour, rescale into TRUE mm
       by ``print_scale`` (see DEFAULT_PRINT_SCALE), then the two insets
       (half stroke plus PEN_R) as one build123d offset of the polygon face,
       then the pocket as the tool outline offset by FOAM_CLEAR
    -> the tool outline is turned so its minimum-area rectangle lies along X
       and its bounding box's corner sits at the origin; L and W are that
       rectangle's sides
    -> write captures/<tag>.dxf (the pocket loop, mm) and
       captures/preview/<tag>.png (the rectified sheet, the detected trace in
       orange, the pocket in cyan, L / W / H in the corner)
    -> upsert the tag's row in tool_list.csv: dims_status CAPTURED,
       silhouette, height_class, bbox_l_mm, bbox_w_mm

A rejection writes NOTHING: no DXF, no preview, no row. The Result carries
one line saying why, and that line is what the Form's CAPTURE tab and the
morning digest show.

THE SHEET SIZE IS NEVER AN ARGUMENT
===================================

Nobody tells this module what paper the trace is on. Each size in
``trace_sheet.SIZES`` carries its own quartet of ArUco ids -- LETTER 0-3,
TABLOID 8-11 (RT4 trimmed the rest) -- so the markers in the
photo name the geometry, and ``identify`` looks it up. Two consequences worth
having:

  * a student who prints TABLOID and photographs it gets TABLOID's window and
    TABLOID's mm, with nothing to get wrong on a form;
  * the failure that would otherwise be silent -- a sheet read against the
    wrong page size, every dimension out by the ratio of the two pages -- is
    not reachable. It is a rejection, not a wrong number.

``identify`` counts a quartet as a candidate sheet at ``SHEET_MIN_TAGS``
markers, not one: a single stray id out of a 50-marker dictionary is a
detector false positive, and one false positive should not reject an
otherwise good capture. Two candidates in one frame is "two different sheet
sizes in frame" and rejects.

THE OFFSETS
===========

shapely is not in the venv and nothing new is added for this; the polygon
offsets are build123d's ``offset`` on a face made from the polyline, with
``Kind.ARC`` so an inset never self-intersects at a reflex corner. The only
thing lost is what any 7mm collar loses: a concave corner of the tool
tighter than PEN_R comes back as a PEN_R fillet, which makes the foam tongue
there smaller than the notch, never larger. The tool still drops in.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from stations.cnc_shapeoko.tools import trace_sheet as sheet

HERE = Path(__file__).resolve().parent
CAPTURES = HERE / "captures"
PREVIEWS = CAPTURES / "preview"
TOOL_LIST = HERE / "tool_list.csv"

# ================================================================ parameters

PEN_R = 7.0
"""Radius of the surface that rides the tool while tracing: the TRACE collar,
``trace_sheet.COLLAR_OD`` / 2, a pencil in its hex bore. The pencil's own
taper never touches the tool, so this is the whole of the offset between the
drawn line's centreline and the tool's outline. SOURCE: design, ruling
2026-09-04. CONFIDENCE: design; verify with calipers on the printed collar
and correct here if the printer ran fat or thin."""

FOAM_CLEAR = 1.0
"""Added around the recovered tool outline to make the pocket. SOURCE:
choice, Kaizen practice for a friction fit in a foam that compresses.
CONFIDENCE: choice, settled by the fit test (spec step 5)."""

DEFAULT_PRINT_SCALE = 1.0
"""``ingest``'s ``print_scale`` default: an unscaled, 100% print. DEFINITION:
measured scale-bar length / 100 (the bar prints at ``trace_sheet.SCALE_BAR_MM``,
100mm nominal). If the printer will not lay the sheet down at 100% and Jared
prints it smaller instead, every mm in the photo is smaller than the sheet's
tags say by that same factor, and the recovered L/W come back inflated by
1 / print_scale (a 94% print reads ~6% large). The homography and the crop
still run against the sheet's NOMINAL (unscaled) tag positions -- that frame
is what the rectified preview image is drawn in -- so the traced outline is
rescaled into TRUE mm right after it is read off the contour, before the
PEN_R and FOAM_CLEAR offsets (both true, physical mm) are applied to it; the
preview overlay is converted back the other way, so it still lines up with
the nominal-frame pixels it is drawn over. Equivalent to scaling the tag
positions before the homography instead. SOURCE: ruling 2026-09-04.
CONFIDENCE: rule; verify a scaled print returns the correct mm before
trusting a capture made on one."""

PX_PER_MM = 10.0
"""The rectified sheet's resolution: 0.1mm a pixel, 2159 x 2794 for LETTER and
4200 x 5940 for A2.
Finer than any phone delivers at arm's length, coarse enough to run in a
second. CONFIDENCE: choice."""

FIELD_INSET = 2.0
"""The crop is this far inside the field boundary, so the 1mm border line
(centred on that boundary) never appears in the threshold image. A trace
that touches the crop edge is within 2mm of the border and is rejected as
having run off the field. CONFIDENCE: rule."""

MASK_PAD = 1.0
"""Extra white around each tag's quiet zone when it is masked out of the
field crop, for the printer's registration. CONFIDENCE: rule."""

FLATTEN_BLUR_MM = 25.0
"""Width of the blur that estimates the paper's shading before Otsu. Much
wider than any pencil line, narrower than a phone's vignette.
CONFIDENCE: choice."""

CLOSE_PX = 2
"""Morphological close radius after the threshold, in rectified pixels:
bridges a pencil line that thinned to nothing for a fifth of a millimetre.
CONFIDENCE: spec."""

DP_TOL = 0.3
"""Douglas-Peucker tolerance on the outer contour, mm. SOURCE: spec v3."""

ARC_CHORD_TOL = 0.05
"""Chord error when the arcs an offset introduces are sampled back into the
polyline. Finer than DP_TOL because these arcs are exact geometry, not
pencil. CONFIDENCE: choice."""

MIN_TRACE_MM2 = 100.0
"""Under this area a top-level contour is a speck, not a candidate.
CONFIDENCE: rule."""

SECOND_FRAC = 0.25
"""A second top-level contour bigger than this fraction of the largest means
two tools on the sheet. SOURCE: spec v3 ("comparable area")."""

HOLE_FRAC = 0.05
"""The largest hole inside the trace must be at least this fraction of the
trace's outer area for the trace to count as a closed loop. An open arc has
no hole; a closed loop around anything bigger than a coin has a large one.
CONFIDENCE: rule."""

MIN_TAGS = 3
"""Tags of the identified size needed to rectify. Three corners fix a
homography; the fourth is redundancy. CONFIDENCE: rule."""

SHEET_MIN_TAGS = 2
"""Detections of one size's quartet before that size counts as a sheet in the
frame. One is a false positive out of a 50-marker dictionary and is ignored;
two is a sheet, and two sizes at two each is two sheets in one photo.
CONFIDENCE: rule."""

HEIGHT_CLASSES = sheet.GAUGE_SLOTS

PREVIEW_PX_PER_MM = 3.0
TRACE_COLOUR = (0, 140, 255)      # BGR: orange
POCKET_COLOUR = (220, 200, 0)     # BGR: cyan


# ================================================================ result


@dataclass(frozen=True)
class Result:
    ok: bool
    reason: str
    dxf_path: Path | None = None
    preview_path: Path | None = None
    L: float | None = None
    W: float | None = None
    size: str | None = None
    """Which sheet size the tags said this was. Set on every accepted capture,
    and on a rejection whenever the size was identified before the reason."""

    def line(self) -> str:
        if self.ok:
            return f"ok: {self.size} sheet, L {self.L:.1f} W {self.W:.1f}, {self.dxf_path}"
        return f"rejected: {self.reason}"


def _reject(reason: str, size: str | None = None) -> Result:
    return Result(ok=False, reason=reason, size=size)


# ================================================================ steps


def detect_tags(gray: np.ndarray) -> dict[int, np.ndarray]:
    """id -> 4 x 2 image corners for every marker found that belongs to SOME
    sheet in the family. Ids outside the family are dropped here."""
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, sheet.ARUCO_DICT))
    params = cv2.aruco.DetectorParameters()
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    corners, ids, _rej = cv2.aruco.ArucoDetector(d, params).detectMarkers(gray)
    found: dict[int, np.ndarray] = {}
    if ids is None:
        return found
    for c, i in zip(corners, ids.flatten()):
        if int(i) in sheet.SIZE_FOR_TAG:
            found[int(i)] = c.reshape(4, 2).astype(np.float64)
    return found


def identify(found: dict[int, np.ndarray]) -> tuple[sheet.SheetSpec | None, dict[int, np.ndarray], str]:
    """Which sheet size is in the frame. Returns (spec, that size's tags,
    reason); ``spec`` is None exactly when ``reason`` is non-empty.

    A size counts as present at SHEET_MIN_TAGS of its own quartet, so a lone
    stray detection is ignored rather than being read as a second sheet."""
    by_size: dict[str, dict[int, np.ndarray]] = {}
    for tid, corners in found.items():
        by_size.setdefault(sheet.SIZE_FOR_TAG[tid].name, {})[tid] = corners
    present = sorted(n for n, t in by_size.items() if len(t) >= SHEET_MIN_TAGS)
    if len(present) > 1:
        return None, {}, f"two different sheet sizes in frame ({' and '.join(present)}): one sheet per photo"
    if not present:
        seen = ", ".join(str(i) for i in sorted(found)) or "none"
        return None, {}, (
            "no known sheet size found: the four corner squares were not read "
            f"(corner squares seen: {seen}). Sheet cut off, out of focus, or not a trace sheet."
        )
    spec = sheet.SIZES[present[0]]
    return spec, by_size[present[0]], ""


def rectify(img: np.ndarray, tags: dict[int, np.ndarray], spec: sheet.SheetSpec) -> np.ndarray:
    """The photo warped into that size's sheet frame at PX_PER_MM."""
    src = np.concatenate([tags[i] for i in sorted(tags)])
    dst = np.concatenate([spec.tag_corners(i) for i in sorted(tags)]) * PX_PER_MM
    H, _mask = cv2.findHomography(src, dst, 0)
    size = (int(round(spec.page_w * PX_PER_MM)), int(round(spec.page_h * PX_PER_MM)))
    return cv2.warpPerspective(img, H, size, flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))


def field_crop(rect_gray: np.ndarray, spec: sheet.SheetSpec) -> tuple[np.ndarray, tuple[int, int]]:
    """The trace field, inside its border, tags whited out. Returns the crop
    and its (x, y) origin in rectified pixels."""
    x0, y0, x1, y1 = spec.field_rect()
    px0, py0 = int(round((x0 + FIELD_INSET) * PX_PER_MM)), int(round((y0 + FIELD_INSET) * PX_PER_MM))
    px1, py1 = int(round((x1 - FIELD_INSET) * PX_PER_MM)), int(round((y1 - FIELD_INSET) * PX_PER_MM))
    crop = rect_gray[py0:py1, px0:px1].copy()
    for mx0, my0, mx1, my1 in spec.tag_masks():
        ax0 = int(round((mx0 - MASK_PAD) * PX_PER_MM)) - px0
        ay0 = int(round((my0 - MASK_PAD) * PX_PER_MM)) - py0
        ax1 = int(round((mx1 + MASK_PAD) * PX_PER_MM)) - px0
        ay1 = int(round((my1 + MASK_PAD) * PX_PER_MM)) - py0
        ax0, ay0 = max(ax0, 0), max(ay0, 0)
        ax1, ay1 = min(ax1, crop.shape[1]), min(ay1, crop.shape[0])
        if ax1 > ax0 and ay1 > ay0:
            crop[ay0:ay1, ax0:ax1] = 255
    return crop, (px0, py0)


def threshold(crop: np.ndarray) -> np.ndarray:
    """Pen on white as 255 on 0: flatten the lighting, invert, Otsu, close."""
    k = int(FLATTEN_BLUR_MM * PX_PER_MM) | 1
    bg = cv2.GaussianBlur(crop, (k, k), 0).astype(np.float32) + 1.0
    flat = np.clip(crop.astype(np.float32) / bg * 255.0, 0, 255).astype(np.uint8)
    inv = 255 - flat
    _t, binary = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CLOSE_PX + 1, 2 * CLOSE_PX + 1))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)


def _mm_poly(px_pts: np.ndarray, origin: tuple[int, int]) -> np.ndarray:
    """Crop pixels -> sheet mm (y down), n x 2."""
    pts = px_pts.reshape(-1, 2).astype(np.float64)
    pts[:, 0] += origin[0]
    pts[:, 1] += origin[1]
    return pts / PX_PER_MM


def _offset_polygon(pts_mm: np.ndarray, amount: float) -> np.ndarray:
    """A closed polygon offset by ``amount`` (negative = inset), as a closed
    polygon again, arcs sampled at ARC_CHORD_TOL chord error. build123d does
    the offset so a reflex corner never folds over."""
    from build123d import GeomType, Kind, Polyline, make_face, offset

    face = make_face(Polyline(*[tuple(p) for p in pts_mm], close=True))
    if abs(amount) < 1e-9:
        return pts_mm
    result = offset(face, amount=amount, kind=Kind.ARC)
    faces = result.faces()
    if not faces:
        raise ValueError("offset produced no face")
    wire = max(faces, key=lambda f: f.area).outer_wire()
    out: list[tuple[float, float]] = []
    for e in wire.edges():
        if e.geom_type == GeomType.LINE:
            n = 1
        else:
            r = max(getattr(e, "radius", 1.0), 1e-6)
            step = 2 * np.arccos(max(1 - ARC_CHORD_TOL / r, -1.0))
            n = max(int(np.ceil(e.length / (r * step))), 2)
        for i in range(n):
            p = e.position_at(i / n)
            out.append((p.X, p.Y))
    return np.array(out, dtype=np.float64)


def _align_to_min_rect(pts_mm: np.ndarray) -> tuple[np.ndarray, float, float, np.ndarray]:
    """Rotate so the minimum-area rectangle's long side runs along X and its
    corner sits at the origin. Returns (aligned points, L, W, the 2 x 3
    affine that did it)."""
    (cx, cy), (rw, rh), ang = cv2.minAreaRect(pts_mm.astype(np.float32))
    if rw < rh:
        ang += 90.0
        rw, rh = rh, rw
    M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
    raw = (M[:, :2] @ pts_mm.T).T + M[:, 2]
    shift = raw.min(axis=0)
    rot = raw - shift
    # M must fold in the SAME shift that was just applied to ``raw`` (not
    # M[:, :2] @ pts_mm.T alone, which drops the rotation's own translation
    # term and left the returned M's inverse not actually undoing the
    # alignment -- this is what sent the preview's pocket overlay tens of
    # mm from the tool).
    M[:, 2] -= shift
    return rot, float(rw), float(rh), M


def _write_dxf(pts_mm: np.ndarray, path: Path) -> None:
    from build123d import Polyline, Unit
    from build123d.exporters import ExportDXF

    wire = Polyline(*[tuple(p) for p in pts_mm], close=True)
    ex = ExportDXF(unit=Unit.MM)
    ex.add_layer("POCKET")
    ex.add_shape(wire, layer="POCKET")
    path.parent.mkdir(parents=True, exist_ok=True)
    ex.write(str(path))


def _write_preview(rect: np.ndarray, trace_mm: np.ndarray, pocket_sheet_mm: np.ndarray, text: str, path: Path, spec: sheet.SheetSpec) -> None:
    s = PREVIEW_PX_PER_MM / PX_PER_MM
    img = cv2.resize(rect, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.polylines(img, [np.round(trace_mm * PREVIEW_PX_PER_MM).astype(np.int32)], True, TRACE_COLOUR, 2, cv2.LINE_AA)
    cv2.polylines(img, [np.round(pocket_sheet_mm * PREVIEW_PX_PER_MM).astype(np.int32)], True, POCKET_COLOUR, 2, cv2.LINE_AA)
    x0, y0, _x1, _y1 = spec.field_rect()
    org = (int((x0 + 4) * PREVIEW_PX_PER_MM), int((y0 + 12) * PREVIEW_PX_PER_MM))
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, POCKET_COLOUR, 2, cv2.LINE_AA)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)


CSV_COLUMNS = (
    "id", "name", "drawer", "kind", "shank_d_mm", "cut_d_mm", "oal_mm",
    "bbox_l_mm", "bbox_w_mm", "bbox_h_mm", "qty", "dims_status", "socket_note",
    "height_class", "silhouette",
)


def upsert_row(csv_path: Path, tag: str, height_class: float, silhouette: str, L: float, W: float) -> None:
    """Update the tag's row in the snapshot, or append one if the tag is new.
    Every other cell is left exactly as it was."""
    rows: list[dict[str, str]] = []
    fields: list[str] = list(CSV_COLUMNS)
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fields = list(reader.fieldnames or fields)
            rows = list(reader)
    for col in ("height_class", "silhouette"):
        if col not in fields:
            fields.append(col)
    update = {
        "dims_status": "CAPTURED",
        "silhouette": silhouette,
        "height_class": f"{height_class:g}",
        "bbox_l_mm": f"{L:.1f}",
        "bbox_w_mm": f"{W:.1f}",
    }
    hit = False
    for r in rows:
        if (r.get("id") or "").strip().upper() == tag.upper():
            r.update(update)
            hit = True
    if not hit:
        new = {k: "" for k in fields}
        new.update({"id": tag, "name": f"{tag} (captured, unnamed)", "qty": "1"})
        new.update(update)
        rows.append(new)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ================================================================ ingest


def ingest(
    image_path: str | Path,
    tag: str,
    height_slot: float | int | str,
    source: str = "trace",
    *,
    print_scale: float = DEFAULT_PRINT_SCALE,
    out_dir: Path = CAPTURES,
    csv_path: Path | None = TOOL_LIST,
) -> Result:
    """One capture. The paper size is NOT an argument: the ArUco quartet in
    the photo names it (see ``identify``). ``print_scale`` corrects a sheet
    printed at other than 100% (see ``DEFAULT_PRINT_SCALE``). ``out_dir`` and
    ``csv_path`` exist so a test can point the writes anywhere;
    ``csv_path=None`` skips the row."""
    if source == "camera":
        raise NotImplementedError("v2: machine Z-plate camera")
    if source != "trace":
        raise ValueError(f"unknown source {source!r}")

    tag = tag.strip().upper()
    try:
        height_class = float(height_slot)
    except (TypeError, ValueError):
        return _reject(f"height slot {height_slot!r} is not a number")
    if height_class not in HEIGHT_CLASSES:
        return _reject(f"height slot {height_class:g} is not one of {', '.join(f'{h:g}' for h in HEIGHT_CLASSES)}")

    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        return _reject(f"could not read image {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    found = detect_tags(gray)
    spec, tags, why = identify(found)
    if spec is None:
        return _reject(why)
    if len(tags) < MIN_TAGS:
        return _reject(
            f"{len(tags)} of 4 corner squares found on the {spec.name} sheet (need {MIN_TAGS}): "
            "square covered, sheet cut off, or out of focus",
            size=spec.name,
        )

    rect = rectify(gray, tags, spec)
    crop, origin = field_crop(rect, spec)
    binary = threshold(crop)

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None or len(contours) == 0:
        return _reject("no trace found in the field", spec.name)
    hier = hierarchy[0]
    min_area_px = MIN_TRACE_MM2 * PX_PER_MM ** 2
    tops = [(cv2.contourArea(c), i) for i, c in enumerate(contours) if hier[i][3] == -1 and cv2.contourArea(c) >= min_area_px]
    if not tops:
        return _reject("no trace found in the field", spec.name)
    tops.sort(reverse=True)
    area_out, idx = tops[0]
    if len(tops) > 1 and tops[1][0] > SECOND_FRAC * area_out:
        return _reject(f"two traces in the field (second is {tops[1][0] / area_out:.0%} of the largest): one tool per sheet", spec.name)

    outer = contours[idx]
    bx, by, bw, bh = cv2.boundingRect(outer)
    if bx <= 0 or by <= 0 or bx + bw >= crop.shape[1] or by + bh >= crop.shape[0]:
        return _reject(f"trace touches the edge of the {spec.name} window: the tool ran off the field, take a bigger sheet", spec.name)

    holes = [(cv2.contourArea(contours[j]), j) for j in range(len(contours)) if hier[j][3] == idx]
    hole_area, hole_idx = max(holes) if holes else (0.0, -1)
    if hole_area < HOLE_FRAC * area_out:
        return _reject("trace is not a closed loop: the line does not meet itself", spec.name)

    p_out = cv2.arcLength(outer, True)
    p_hole = cv2.arcLength(contours[hole_idx], True)
    stroke_px = (area_out - hole_area) / ((p_out + p_hole) / 2)
    stroke_mm = stroke_px / PX_PER_MM

    approx = cv2.approxPolyDP(outer, DP_TOL * PX_PER_MM, True)
    trace_mm = _mm_poly(approx, origin)                        # outer edge of the pencil line, in the sheet's NOMINAL (unscaled) frame -- this is what the preview is drawn over, so it is never rescaled
    # print_scale correction: the homography above ran against the sheet's
    # nominal tag positions regardless of how the sheet actually printed, so
    # a scaled print leaves every mm in that frame inflated by 1 / print_scale
    # (see DEFAULT_PRINT_SCALE). PEN_R and FOAM_CLEAR are TRUE, physical mm --
    # the collar's real radius, a real clearance -- so the trace must be
    # rescaled into true mm HERE, before either offset is applied, not after:
    # applying a true-mm offset inside the still-inflated frame and rescaling
    # afterward does not cancel, it leaves a residual error the size of the
    # offset times (1/print_scale - 1).
    trace_mm_true = trace_mm * print_scale
    stroke_mm_true = stroke_mm * print_scale
    tool_sheet = _offset_polygon(trace_mm_true, -(stroke_mm_true / 2 + PEN_R))
    if len(tool_sheet) < 3:
        return _reject("trace collapsed under the collar inset: nothing that small is a tool", spec.name)
    tool_local, L, W, M = _align_to_min_rect(tool_sheet)       # true mm from here on
    pocket_local_raw = _offset_polygon(tool_local, FOAM_CLEAR)
    pocket_min = pocket_local_raw.min(axis=0)
    pocket_local = pocket_local_raw - pocket_min
    # the pocket back in the sheet's NOMINAL frame, for the preview only -- the
    # preview is drawn on ``rect``, which is still in that nominal frame.
    # ``pocket_local + pocket_min`` undoes the zeroing above to get back
    # ``pocket_local_raw`` (still in the tool_local frame, i.e. what
    # ``Minv`` actually maps from) -- unlike ``tool_local.min(axis=0) -
    # FOAM_CLEAR``, which only approximates that offset when the tool's
    # bbox extremes have axis-aligned outward normals, false for a
    # concave outline like a jaw notch (this is what put the pocket
    # overlay nowhere near the tool in the preview).
    Minv = cv2.invertAffineTransform(M)
    pocket_true = (Minv[:, :2] @ (pocket_local + pocket_min).T).T + Minv[:, 2]
    pocket_sheet = pocket_true / print_scale

    dxf_path = out_dir / f"{tag}.dxf"
    preview_path = out_dir / "preview" / f"{tag}.png"
    _write_dxf(pocket_local, dxf_path)
    _write_preview(
        rect, trace_mm, pocket_sheet,
        f"{tag}  {spec.name}  L {L:.1f}  W {W:.1f}  H<={height_class:g}  line {stroke_mm_true:.2f}  {len(tags)} tags  print_scale {print_scale:.3f}",
        preview_path, spec,
    )
    if csv_path is not None:
        try:
            rel = str(dxf_path.relative_to(csv_path.parent))
        except ValueError:
            rel = str(dxf_path)
        upsert_row(csv_path, tag, height_class, rel, L, W)
    return Result(ok=True, reason="", dxf_path=dxf_path, preview_path=preview_path, L=L, W=W, size=spec.name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tool capture ingest: a photo of a traced sheet in, a pocket polyline out.")
    parser.add_argument("image")
    parser.add_argument("tag")
    parser.add_argument("height")
    parser.add_argument("--print-scale", type=float, default=DEFAULT_PRINT_SCALE, dest="print_scale",
                         help="measured scale-bar length / 100 (default 1.0, a 100%% print)")
    args = parser.parse_args()
    r = ingest(args.image, args.tag, args.height, print_scale=args.print_scale)
    print(r.line())
    sys.exit(0 if r.ok else 1)
