"""Tool capture ingest: a photo of a tool lying on a capture sheet in, a
pocket polyline out.

    PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/tools/capture_ingest.py <image> <tag> <height_mm>

    ingest(image_path, tag, height, source="photo", print_scale=1.0) -> Result

Two sources. ``source="photo"`` (the default since 2026-09-11) is a phone
photo of the TOOL ITSELF lying flat in the sheet's window, plus the tool's
measured height in mm; the tool's silhouette against the white paper is the
outline. ``source="trace"`` (v1, 2026-09-04 to 2026-09-11) is a photo of a
pencil line drawn round the tool with the TRACE collar; it is kept, unchanged,
so the two captures made that way (T025, T026) can be re-run, but nothing new
should use it: the collar was red-teamed on 2026-09-11 as too clunky for a
student to get right. ``source="camera"`` is the v2 plug (the machine's own
Z-plate camera over a fiducial mat) and raises until it is built.

THE PHOTO PIPELINE
==================

    ArUco detect (DICT_4X4_50) -> which SHEET SIZE is in the frame, from the
       quartet of ids the markers belong to (``trace_sheet.SIZE_FOR_TAG``);
       reject on two quartets, on none, or on fewer than MIN_TAGS of the one
       that is there (``identify``; shared with the trace path)
    -> homography from the detected corners to that size's sheet mm at
       PX_PER_MM, warp the photo into the sheet frame, crop the window inside
       its border line, white out any tag square that overlaps the crop
       (``_locate``, ``rectify``, ``field_crop``; shared with the trace path)
    -> SEGMENT the tool against the window (``segment_tool``). Which window
       is read off a band just inside it: MAGENTA (sheets from 2026-09-11
       11:00 on, ``trace_sheet.WINDOW_FILL``) is a CHROMA KEY, every pixel
       whose hue is off the field's or whose saturation is too low to be the
       field is tool, and a shadow (darker magenta, same hue, still
       saturated) stays background; a WHITE window (every sheet before that)
       takes the grabCut path below, unchanged. On white one Otsu is not
       enough: a metal tool has highlights as bright as the paper and casts a
       soft shadow darker than the paper, so the threshold is only the SEED.
       Seed: darkness-or-saturation score, Otsu, opened at 2 x PENCIL_MM so a
       pencil line already on the sheet cannot seed, components over
       MIN_TOOL_MM2, eroded by SEED_ERODE_MM (probable foreground) and by
       SEED_SURE_MM (sure foreground). Then cv2.grabCut on the colour crop,
       initialised with the paper outside the window as sure background, a
       BORDER_BAND_MM band inside the window as probable background, the seed
       as above, and everything else probable background; GRABCUT_ITERS
       rounds at GRABCUT_PX_PER_MM.
    -> clean the grabCut mask: open at PENCIL_MM (pencil lines off, one
       hugging the tool detached: today's students traced first, and the
       line runs along the tool's own edge); close at HIGHLIGHT_CLOSE_MM
    -> the tool's BODY is the largest component that has a part 2 x
       PENCIL_MM thick (a retraced loop is thick but thin everywhere; a tool
       is not); every component within MERGE_MM of the body is merged back
       into it, thick or thin (a strip a highlight cut off), the gap closed,
       the holes filled (highlights inside the tool)
    -> reject: no thick component over MIN_TOOL_MM2 (no tool in the window);
       the tool touching the crop edge (too big for this sheet); a second
       thick component over SECOND_FRAC of the body (two tools)
    -> PERSPECTIVE: the tool stands above the sheet plane, so its silhouette
       is inflated away from the camera's nadir (see below). Correct it with
       the camera height D from the photo's EXIF and h_eff from the measured
       height, in sheet mm
    -> Douglas-Peucker at DP_TOL, rescale into TRUE mm by ``print_scale``,
       then the pocket as the corrected outline offset by FOAM_CLEAR (one
       build123d offset, ``Kind.ARC``)
    -> the outline is turned so its minimum-area rectangle lies along X and
       its bounding box's corner sits at the origin; L and W are that
       rectangle's sides
    -> height class = ceil(height_mm / 10) x 10, one of HEIGHT_CLASSES
    -> write captures/<tag>.dxf (the pocket loop, mm) and
       captures/preview/<tag>.png (the rectified sheet, the silhouette in
       orange, the pocket in cyan, L / W / H and the D used in the corner)
    -> upsert the tag's row in tool_list.csv: dims_status CAPTURED,
       silhouette, height_class, bbox_l_mm, bbox_w_mm, bbox_h_mm (the
       measured mm)

A rejection writes NOTHING: no DXF, no preview, no row. The Result carries
one line saying why, and that line is what the Form's CAPTURE tab and the
morning digest show. An accepted capture may ALSO carry a note in ``reason``
("camera height assumed 650"); the wrapper appends it to the digest.

THE PERSPECTIVE OF A TOOL ABOVE THE SHEET
=========================================

The four tags rectify the SHEET PLANE exactly. A silhouette edge at height h
above that plane is seen along a ray from the camera, and where that ray
meets the paper is further from the camera's nadir than the edge itself
(similar triangles, camera at height D over nadir c, all in sheet mm):

    p' = c + (p - c) * D / (D - h)          what the rectified image shows
    p  = c + (p' - c) * (D - h) / D         the correction

h is not the tool's measured height: the widest edge of a real tool (a
wrench's jaw, a clamp's bar, a caliper's beam) sits somewhere in its
thickness, around the middle, and the edge the camera sees is the highest
point along that ray, which is the top for a slab and lower for a rounded
bar. h_eff = H_EFF_FRAC x measured height is the estimate; FOAM_CLEAR absorbs
the residual. With the sheet a third of the screen (D about 600) a 20mm tool inflates by 3.4%, 1.7mm on
a 50mm width; corrected with h_eff = 10 the residual is under 0.9mm each way
whether the true edge is at 0 or at 20. CONFIDENCE: estimate.

D comes from the photo's EXIF. A lens of 35mm-equivalent focal length f35
projects an object of size S at distance D onto s = f35 * S / D mm of a
35mm frame, and that frame's diagonal (FRAME_DIAG_MM, sqrt(36^2 + 24^2) =
43.27) is the image's diagonal in pixels, whatever the sensor's aspect
ratio, so s in pixels is s * image_diag_px / 43.27 and

    D = f35 * S * image_diag_px / (43.27 * s_px)

On a 3:2 frame this is exactly f35 * S * image_long_px / (36 * s_px); phones
shoot 4:3, and the diagonal form is the one their f35 is defined against
(CIPA). S and s_px are the widest span between two detected tag corners, in
sheet mm and in the UNWARPED photo, so a keystoned photo averages its near
and far scale. c, the nadir, is the image's principal point (its centre)
mapped through the homography into sheet mm; exact for a phone held flat,
which is what the card says to do. No EXIF (a screenshot, a stripped
upload): D = D_FALLBACK_MM and the Result says so.

THE GATE ON D IS A RESIDUAL, NOT A FLOOR. What is not known is where the
widest edge sits in the tool's thickness; h_eff = h / 2 carries +/- h / 2 of
that, and at the far end of the silhouette, L / 2 from the nadir, that is a
residual of about (L / 2) * (h / 2) / D in the outline. A 50mm jaw 16 tall
at D 262 leaves 0.8mm, inside FOAM_CLEAR; the 228mm pendant 40 tall at the
same D leaves 8.7mm and must be shot from further away. So the photo is
identified, rectified and segmented FIRST, L is measured, and then
residual > RESIDUAL_MAX rejects, naming the D that would do. A hard floor
stays only where the model itself breaks: D under D_HARD_MIN_MM (a phone
almost on the paper). The first real photos (2026-09-11) showed the flat
300 floor rejecting a small tool it would have measured to 0.8mm.

THE SHEET SIZE IS NEVER AN ARGUMENT
===================================

Nobody tells this module what paper the tool is on. Each size in
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

THE TRACE PIPELINE (source="trace", history)
============================================

    ... the shared front end above, on the grey image ...
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
    -> Douglas-Peucker, rescale by ``print_scale``, the two insets (half
       stroke plus PEN_R) as one build123d offset, then the pocket as the
       tool outline offset by FOAM_CLEAR; align, write, upsert as above

THE OFFSETS
===========

shapely is not in the venv and nothing new is added for this; the polygon
offsets are build123d's ``offset`` on a face made from the polyline, with
``Kind.ARC`` so an inset never self-intersects at a reflex corner. What the
trace path lost to the collar (a concave corner tighter than PEN_R came back
as a PEN_R fillet) the photo path does not: the silhouette is the tool's own
edge, to the pixel, and only the pencil-line opening (PENCIL_MM) rounds it,
by half a millimetre at a sharp corner.

WHAT THE PHOTO PATH CANNOT SEE
==============================

A specular highlight is paper-bright. One that is enclosed by the tool (a
streak down a wrench, a patch on a clamp's bar) is a hole and is filled. One
that runs the FULL length of an edge, with a strip of tool beyond it, cuts
that strip off: the strip is thin everywhere and is dropped like a pencil
line, and the pocket comes out narrower by the strip. A hard band like that
is rare under diffuse shop light and no flash, and it is visible in the
preview as a straight step in the orange line. The remedy is to turn the
tool or the sheet relative to the light and photograph it again, not a
rescue rule: anything that re-admits a dark strip beside the tool
re-admits a pencil line hugging it. LOOK AT THE PREVIEW.

A hard shadow is the other one. Under diffuse shop light a tool's shadow is
a 5 to 15% penumbra and grabCut leaves it with the paper; under one lamp or
a flash it is a 25% band with an edge, and grabCut takes it as tool along
that side, about 1.5mm on the synthetic stadium. Hence no flash, no lamp.
"""

from __future__ import annotations

import csv
import math
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
"""TRACE PATH ONLY. Radius of the surface that rides the tool while tracing: the TRACE collar,
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

# ---- photo source

MAGENTA_HUE = (150, 175)
"""The window is magenta when the median hue of the saturated pixels in the
border band lands in this window, in OpenCV's 0-179 hue units (300 to 350
degrees). Process magenta prints at about 325 degrees (162), a phone's white
balance and a warm shop light move it 10 degrees either way, and the printer's
inks another few. Red is at 0/180 and blue at 120, both well outside.
CONFIDENCE: estimate; verified on the synthetic sheet, to be checked on the
first colour print."""

FIELD_SAT_MIN = 90
"""A pixel below this saturation (of 255) is not the magenta field whatever
its hue: a white tool, a grey tool, a chrome highlight, a pencil line. The
printed field sits near 200; a shadow on it keeps its saturation.
CONFIDENCE: estimate."""

FIELD_FRAC = 0.6
"""Fraction of the border band that has to be magenta for the window to
count as magenta. A tool lying across the band takes some of it; a white
sheet has none. CONFIDENCE: rule."""

HUE_TOL = 12
"""How far a pixel's hue may sit from the band's median hue (OpenCV units,
about 24 degrees) and still be field: the printed magenta is flat, and a
tool of any colour but magenta is further off than this. CONFIDENCE:
estimate."""

GRABCUT_PX_PER_MM = 5.0
"""grabCut runs on the colour crop downsampled to this: 0.2mm a pixel, 900 x
900 on LETTER, well under a second. The mask comes back up to PX_PER_MM
bilinearly, so the boundary is placed to about a tenth of a millimetre.
CONFIDENCE: choice."""

GRABCUT_ITERS = 5

BORDER_BAND_MM = 6.0
"""Band inside the window edge initialised as probable background: paper,
the shadow of nothing, and where the tool is NOT allowed to be (a tool this
close to the edge is rejected anyway). CONFIDENCE: rule."""

PENCIL_MM = 1.5
"""A pencil line's width on the sheet as the mask sees it (the line plus
the blur of a phone at 600mm and the rectification), and the opening that
removes one from the mask. Lines up to this wide detach from a tool they
hug; a component that is thin everywhere at 2 x this (a retraced loop)
cannot be the tool's body. A tool feature narrower than PENCIL_MM (a
scriber's last millimetre and a half) is lost, and a sharp corner is
rounded by PENCIL_MM / 2. SOURCE: the two 2026-09-11 sheets, bare-pencil
traces 0.5 to 1.5mm wide, and the synthetic 0.8mm ring, which survived a
1.0 open at D 600 and was merged into the tool. CONFIDENCE: estimate."""

PAPER_DARK_FRAC = 0.30
SAT_MIN = 80
"""The seed: a pixel darker than the PAPER MODEL at that point by more than
PAPER_DARK_FRAC of it, or more saturated than SAT_MIN (a red handle, blue
anodising, under any light). The paper model is a quadratic in x and y fit
to the BORDER_BAND_MM band, which is paper by construction, so a dim or
vignetted photo does not move the seed: Otsu did, it split the paper itself
on the 2026-09-11 sheet shot at 178/255. A soft shadow is 10 to 20% darker
than the paper and stays out of the seed; grabCut decides its edge.
CONFIDENCE: estimate, from the two 2026-09-11 photos."""

SHADOW_FRAC = 0.15
"""After grabCut, a pixel less than this fraction darker than the paper
model and unsaturated is penumbra, not tool, whatever the colour model
said: under diffuse light a tool's shadow is 5 to 15% and a tool itself is
darker than that or coloured. This is what stops the soft shadow's side of
the outline creeping out by half a millimetre. A tool lighter than 85% of
the paper (white plastic) is beyond the photo path anyway. CONFIDENCE:
estimate, from the synthetic stadium at D 600."""

SEED_ERODE_MM = 1.0
SEED_SURE_MM = 6.0
"""The seed blob eroded by SEED_ERODE_MM is probable foreground for grabCut
(a millimetre keeps the seed inside the tool through the edge's blur and
shadow, and still keeps a 2.3mm strip of tool beside a highlight: 2mm did
not); eroded by SEED_SURE_MM it is sure foreground, the anchor the colour
model cannot lose. A tool narrower than 2 x SEED_SURE_MM has no sure core and
is seeded as probable only. CONFIDENCE: rule."""

HIGHLIGHT_CLOSE_MM = 1.0
"""After the pencil-line open, a close at this width bridges the sub-
millimetre gaps a specular highlight cuts through a metal tool's mask, so
the strip beyond the highlight stays part of the tool and the hole fill
can do the rest. Smaller than the gap between a tool and a pencil line
that has already been opened away. CONFIDENCE: estimate, from the composite
test on the 2026-09-11 T056 sheet."""

MIN_TOOL_MM2 = 100.0
"""Under this area a component is a mark, not a tool: a 1/8in endmill lying
flat is 127. CONFIDENCE: rule."""

H_EFF_FRAC = 0.5
"""The silhouette's edge is assumed at this fraction of the measured height
(see THE PERSPECTIVE OF A TOOL ABOVE THE SHEET). CONFIDENCE: estimate;
FOAM_CLEAR absorbs the residual."""

FRAME_DIAG_MM = math.hypot(36.0, 24.0)
"""The 35mm frame's diagonal, 43.27: what FocalLengthIn35mmFilm is defined
against, and what the photo's pixel diagonal stands for."""

D_FALLBACK_MM = 650.0
"""Camera height when the photo carries no EXIF focal length: the sheet
about a third of the screen.
The Result's reason names it so the digest shows the capture ran on an
assumption. CONFIDENCE: estimate."""

RESIDUAL_MAX = 1.0
"""The largest outline error the h_eff estimate may leave, (L / 2) * (h / 2)
/ D, before the capture rejects as too close for a tool this size. Set to
FOAM_CLEAR: an error up to the clearance still drops the tool in. See THE
GATE ON D IS A RESIDUAL. CONFIDENCE: choice, tied to FOAM_CLEAR."""

D_HARD_MIN_MM = 150.0
"""Below this the pinhole model is not worth correcting with (the phone is
almost on the paper, the nadir estimate is meaningless): reject outright.
CONFIDENCE: rule."""

D_FLOOR_MM = 300.0
"""The flat floor of 2026-09-11 morning, kept for the record; the residual
gate replaced it the same day (T042 at D 262 would have measured to 0.8mm).
Not used."""

MERGE_MM = 3.0
"""A component this close to the tool's body is a piece of the tool a
highlight cut off (a bright band running along an edge leaves the strip
beyond it as its own island, often under 2mm wide), and is merged back
whatever its thickness, the gap closed at this width and the holes filled.
The one thing this re-admits is a pencil line over PENCIL_MM wide (a heavy
retrace) hugging the tool within MERGE_MM, which then pads the outline by
its own width: a pocket a little big. The alternative, dropping every thin
piece first, made a pocket too SMALL by the strip on any shiny tool, and a
too-small pocket is a re-cut tray. Lines a pencil normally draws (under
PENCIL_MM) are gone before this runs; a second TOOL is further away than
this. A band wider than MERGE_MM still leaves a notch, and the preview shows
it. CONFIDENCE: estimate, from the synthetic stadium whose highlight runs
out through the cap and the composite on the 2026-09-11 T056 sheet."""

SILHOUETTE_COLOUR = (0, 140, 255)  # BGR: orange, same as the trace

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
    D: float | None = None
    """Photo source: the camera height used, mm."""
    height_class: float | None = None

    def line(self) -> str:
        if self.ok:
            note = f" ({self.reason})" if self.reason else ""
            return f"ok: {self.size} sheet, L {self.L:.1f} W {self.W:.1f}, {self.dxf_path}{note}"
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


def homography(tags: dict[int, np.ndarray], spec: sheet.SheetSpec) -> np.ndarray:
    """Photo pixels -> rectified pixels (sheet mm x PX_PER_MM), from every
    detected corner of that size's quartet."""
    src = np.concatenate([tags[i] for i in sorted(tags)])
    dst = np.concatenate([spec.tag_corners(i) for i in sorted(tags)]) * PX_PER_MM
    H, _mask = cv2.findHomography(src, dst, 0)
    return H


def rectify(img: np.ndarray, tags: dict[int, np.ndarray], spec: sheet.SheetSpec, H: np.ndarray | None = None) -> np.ndarray:
    """The photo (grey or colour) warped into that size's sheet frame at
    PX_PER_MM."""
    if H is None:
        H = homography(tags, spec)
    size = (int(round(spec.page_w * PX_PER_MM)), int(round(spec.page_h * PX_PER_MM)))
    return cv2.warpPerspective(img, H, size, flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))


@dataclass(frozen=True)
class Located:
    """The shared front end's answer: which sheet, its tags, the homography."""
    spec: sheet.SheetSpec
    tags: dict[int, np.ndarray]
    H: np.ndarray


def _locate(gray: np.ndarray) -> Located | Result:
    """Detect, identify, insist on MIN_TAGS, fit the homography. Both sources
    start here; a Result is a rejection."""
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
    return Located(spec, tags, homography(tags, spec))


def field_crop(rect: np.ndarray, spec: sheet.SheetSpec) -> tuple[np.ndarray, tuple[int, int]]:
    """The window, inside its border, tags whited out; grey or colour in,
    the same out. Returns the crop and its (x, y) origin in rectified
    pixels."""
    x0, y0, x1, y1 = spec.field_rect()
    px0, py0 = int(round((x0 + FIELD_INSET) * PX_PER_MM)), int(round((y0 + FIELD_INSET) * PX_PER_MM))
    px1, py1 = int(round((x1 - FIELD_INSET) * PX_PER_MM)), int(round((y1 - FIELD_INSET) * PX_PER_MM))
    crop = rect[py0:py1, px0:px1].copy()
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


def _clean_polygon(pts_mm: np.ndarray, eps: float = 0.02) -> np.ndarray:
    """Consecutive duplicates and hairpin spikes out of a polygon, so the
    kernel's offset never sees a zero-length or reversed edge. A mask's
    contour, corrected and rotated, can carry both; the pencil trace's never
    did because it was inset first."""
    pts = np.asarray(pts_mm, dtype=np.float64)
    for _ in range(3):
        n = len(pts)
        if n < 4:
            return pts
        keep = np.ones(n, bool)
        for i in range(n):
            a, b, c_ = pts[i - 1], pts[i], pts[(i + 1) % n]
            u, v = b - a, c_ - b
            if np.hypot(*u) < eps:
                keep[i] = False
                continue
            cross = u[0] * v[1] - u[1] * v[0]
            dot = u[0] * v[0] + u[1] * v[1]
            if abs(cross) < eps * max(np.hypot(*u), np.hypot(*v)) and dot < 0:
                keep[i] = False          # a hairpin: the point doubles back on its own edge
        if keep.all():
            return pts
        pts = pts[keep]
    return pts


def _offset_polygon(pts_mm: np.ndarray, amount: float) -> np.ndarray:
    """A closed polygon offset by ``amount`` (negative = inset), as a closed
    polygon again, arcs sampled at ARC_CHORD_TOL chord error. build123d does
    the offset so a reflex corner never folds over."""
    from build123d import GeomType, Kind, Polyline, make_face, offset

    pts_mm = _clean_polygon(pts_mm)
    face = make_face(Polyline(*[tuple(p) for p in pts_mm], close=True))
    if abs(amount) < 1e-9:
        return pts_mm
    try:
        result = offset(face, amount=amount, kind=Kind.ARC)
    except RuntimeError:
        # the kernel's offset folds over at a concavity narrower than the
        # offset (a 0.6mm notch in a photographed edge, under a 1mm outset)
        # and hands back a compound, not a wire. The raster offset is the
        # same geometry to RASTER_PX_PER_MM and cannot fail.
        return _offset_polygon_raster(pts_mm, amount)
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


RASTER_PX_PER_MM = 20.0
"""Resolution of the raster offset the kernel's offset falls back to:
0.05mm a pixel, the same as ARC_CHORD_TOL. CONFIDENCE: choice."""


def _offset_polygon_raster(pts_mm: np.ndarray, amount: float) -> np.ndarray:
    """The polygon as a mask at RASTER_PX_PER_MM, dilated (outset) or eroded
    (inset) by a disk of |amount|, and its outer contour back in mm."""
    k = RASTER_PX_PER_MM
    pad = int(np.ceil(abs(amount) * k)) + 4
    lo = pts_mm.min(axis=0)
    px = np.round((pts_mm - lo) * k).astype(np.int32) + pad
    hi = px.max(axis=0) + pad + 1
    mask = np.zeros((int(hi[1]), int(hi[0])), np.uint8)
    cv2.fillPoly(mask, [px], 255)
    r = int(round(abs(amount) * k))
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    mask = cv2.dilate(mask, disk) if amount > 0 else cv2.erode(mask, disk)
    contours, _h = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return np.zeros((0, 2))
    outer = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(outer, ARC_CHORD_TOL * k, True).reshape(-1, 2).astype(np.float64)
    return (approx - pad) / k + lo


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


def upsert_row(csv_path: Path, tag: str, height_class: float, silhouette: str, L: float, W: float,
               height_mm: float | None = None) -> None:
    """Update the tag's row in the snapshot, or append one if the tag is new.
    Every other cell is left exactly as it was. ``height_mm`` (the photo
    source's measured height) goes to bbox_h_mm; the trace source, which only
    knew the slot, leaves that cell alone."""
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
    if height_mm is not None:
        update["bbox_h_mm"] = f"{height_mm:g}"
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


# ================================================================ photo source


def read_f35(image_path: str | Path) -> float | None:
    """FocalLengthIn35mmFilm out of the photo's EXIF, or None. Read with
    PIL: the tag lives in the Exif sub-IFD (0x8769 / 0xA405); a writer that
    put it at the top level is accepted too."""
    try:
        from PIL import Image

        ex = Image.open(str(image_path)).getexif()
        v = ex.get_ifd(0x8769).get(0xA405) or ex.get(0xA405)
        return float(v) if v else None
    except Exception:
        return None


def tag_span(tags: dict[int, np.ndarray], spec: sheet.SheetSpec) -> tuple[float, float]:
    """(mm, px): the widest separation between two detected tag corners on
    the sheet, and the same two corners' distance in the unwarped photo."""
    mm = np.concatenate([spec.tag_corners(i) for i in sorted(tags)])
    px = np.concatenate([tags[i] for i in sorted(tags)])
    d = np.linalg.norm(mm[:, None, :] - mm[None, :, :], axis=2)
    a, b = np.unravel_index(int(np.argmax(d)), d.shape)
    return float(d[a, b]), float(np.linalg.norm(px[a] - px[b]))


def camera_height(f35: float, span_mm: float, span_px: float, image_shape: tuple[int, ...]) -> float:
    """D, sheet mm: see THE PERSPECTIVE OF A TOOL ABOVE THE SHEET.
    D = f35 * S * image_diag_px / (FRAME_DIAG_MM * s_px)."""
    diag_px = math.hypot(image_shape[0], image_shape[1])
    return f35 * span_mm * diag_px / (FRAME_DIAG_MM * span_px)


def nadir_mm(H: np.ndarray, image_shape: tuple[int, ...]) -> np.ndarray:
    """The image's principal point (its centre) in sheet mm: where a
    flat-held phone's vertical meets the paper."""
    c = np.array([[[image_shape[1] / 2.0, image_shape[0] / 2.0]]], dtype=np.float64)
    return cv2.perspectiveTransform(c, H).reshape(2) / PX_PER_MM


def correct_perspective(pts_mm: np.ndarray, c_mm: np.ndarray, D: float, h_eff: float) -> np.ndarray:
    """p = c + (p' - c) * (D - h_eff) / D, on every point."""
    return c_mm + (pts_mm - c_mm) * ((D - h_eff) / D)


def _disk(mm: float, px_per_mm: float) -> np.ndarray:
    r = max(int(round(mm * px_per_mm / 2)), 1)
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    """255 inside every closed boundary: flood the background from the
    border, and what the flood did not reach is foreground."""
    h, w = mask.shape
    flood = np.pad((mask > 0).astype(np.uint8), 1)
    ff = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(flood, ff, (0, 0), 2)
    return np.where(flood[1:-1, 1:-1] == 2, 0, 255).astype(np.uint8)


def _keep_thick(mask: np.ndarray, open_mm: float, px_per_mm: float) -> np.ndarray:
    """Every component of ``mask`` that has SOME pixel surviving an opening
    at ``open_mm``, kept whole. A pencil loop is thin everywhere and goes; a
    tool with a thin tip keeps its tip."""
    survivors = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _disk(open_mm, px_per_mm))
    n, labels = cv2.connectedComponents((mask > 0).astype(np.uint8))
    keep = np.unique(labels[survivors > 0])
    out = np.isin(labels, keep[keep > 0])
    return (out * 255).astype(np.uint8)


def _paper_model(V: np.ndarray, band: int) -> np.ndarray:
    """The paper's brightness everywhere in the crop, as a quadratic surface
    fit to the border band (paper by construction), refit once without the
    outliers a pencil line or a shadow crossing the band leaves."""
    h, w = V.shape
    m = np.zeros((h, w), bool)
    m[:band, :] = True
    m[-band:, :] = True
    m[:, :band] = True
    m[:, -band:] = True
    ys, xs = np.nonzero(m)
    ys, xs = ys[::3], xs[::3]
    v = V[ys, xs].astype(np.float64)

    def design(x, y):
        x = x / w - 0.5
        y = y / h - 0.5
        return np.column_stack([np.ones_like(x), x, y, x * x, y * y, x * y])

    A = design(xs.astype(np.float64), ys.astype(np.float64))
    coef, *_ = np.linalg.lstsq(A, v, rcond=None)
    resid = v - A @ coef
    keep = np.abs(resid) < 3 * max(np.median(np.abs(resid)) * 1.4826, 2.0)
    if keep.sum() > 12:
        coef, *_ = np.linalg.lstsq(A[keep], v[keep], rcond=None)
    gy, gx = np.mgrid[0:h, 0:w]
    return (design(gx.ravel().astype(np.float64), gy.ravel().astype(np.float64)) @ coef).reshape(h, w)


def field_kind(hsv: np.ndarray, band: int) -> tuple[str, int]:
    """("magenta", median hue) when the border band is the magenta field,
    else ("white", 0). See MAGENTA_HUE."""
    h, w = hsv.shape[:2]
    m = np.zeros((h, w), bool)
    m[:band, :] = True
    m[-band:, :] = True
    m[:, :band] = True
    m[:, -band:] = True
    hue = hsv[:, :, 0][m].astype(int)
    sat = hsv[:, :, 1][m].astype(int)
    val = hsv[:, :, 2][m].astype(int)
    magenta = (hue >= MAGENTA_HUE[0]) & (hue <= MAGENTA_HUE[1]) & (sat > FIELD_SAT_MIN) & (val > 40)
    if magenta.mean() < FIELD_FRAC:
        return "white", 0
    return "magenta", int(np.median(hue[magenta]))


def _mask_chroma(hsv: np.ndarray, h0: int) -> np.ndarray:
    """Tool = not the field. The field is every pixel within HUE_TOL of the
    band's hue and saturated above FIELD_SAT_MIN; a shadow is darker but the
    same hue and still saturated, so it is field."""
    hue = hsv[:, :, 0].astype(int)
    dh = np.abs(hue - h0)
    dh = np.minimum(dh, 180 - dh)
    field = (dh <= HUE_TOL) & (hsv[:, :, 1] > FIELD_SAT_MIN)
    return ((~field) * 255).astype(np.uint8)


def segment_tool(crop_bgr: np.ndarray) -> tuple[np.ndarray, str, str]:
    """The tool against the window as 255 on 0, at the crop's resolution
    (PX_PER_MM), the reason if there is none, and which field it was
    ("magenta" or "white"). See THE PHOTO PIPELINE."""
    s = GRABCUT_PX_PER_MM / PX_PER_MM
    small = cv2.resize(crop_bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    g = GRABCUT_PX_PER_MM
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    band = int(round(BORDER_BAND_MM * g))
    field, h0 = field_kind(hsv, band)
    if field == "magenta":
        fg = _mask_chroma(hsv, h0)
        fg[:2, :] = 0
        fg[-2:, :] = 0
        fg[:, :2] = 0
        fg[:, -2:] = 0
        return _finish_mask(fg, g, crop_bgr.shape), "", field
    return _segment_white(small, hsv, band, g, crop_bgr.shape)


def _finish_mask(fg: np.ndarray, g: float, shape: tuple[int, ...]) -> np.ndarray:
    """The morphology both fields share, then back up to PX_PER_MM."""
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, _disk(PENCIL_MM, g))          # pencil lines off, hugging ones detached
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, _disk(HIGHLIGHT_CLOSE_MM, g))  # highlight gaps bridged
    # what is thin everywhere (a retraced loop) and what is a piece of the
    # tool is decided by the caller against the tool's body: see MERGE_MM
    up = cv2.resize(fg, (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
    return ((up >= 128) * 255).astype(np.uint8)


def _segment_white(small: np.ndarray, hsv: np.ndarray, band: int, g: float, shape: tuple[int, ...]) -> tuple[np.ndarray, str, str]:
    """The white-window path: paper model, seed, grabCut."""
    # the seed: darker than the paper would be here, or saturated
    paper = _paper_model(hsv[:, :, 2], band)
    dark = (paper - hsv[:, :, 2].astype(np.float64)) > PAPER_DARK_FRAC * np.maximum(paper, 1.0)
    seed = ((dark | (hsv[:, :, 1] > SAT_MIN)) * 255).astype(np.uint8)
    seed[:band, :] = 0
    seed[-band:, :] = 0
    seed[:, :band] = 0
    seed[:, -band:] = 0
    # is there a tool at all? Only what survives an open at 2 x PENCIL_MM
    # counts toward MIN_TOOL_MM2, so a pencil loop, however retraced, never
    # seeds; but the seed itself is every component (opened at PENCIL_MM,
    # so a line does not ride in on the tool) that has such a thick part,
    # kept WHOLE, so a strip of tool beside a highlight is seeded too
    thick = cv2.morphologyEx(seed, cv2.MORPH_OPEN, _disk(2 * PENCIL_MM, g))
    n, labels, stats, _c = cv2.connectedComponentsWithStats((thick > 0).astype(np.uint8))
    big = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= MIN_TOOL_MM2 * g * g]
    if not big:
        return np.zeros(shape[:2], np.uint8), "no tool found in the window: lay the tool flat inside the window and photograph it in place", "white"
    seed = _keep_thick(cv2.morphologyEx(seed, cv2.MORPH_OPEN, _disk(PENCIL_MM, g)), 2 * PENCIL_MM, g)
    pr_fg = cv2.erode(seed, _disk(2 * SEED_ERODE_MM, g))
    sure_fg = cv2.erode(seed, _disk(2 * SEED_SURE_MM, g))

    mask = np.full(small.shape[:2], cv2.GC_PR_BGD, np.uint8)
    mask[pr_fg > 0] = cv2.GC_PR_FGD
    mask[sure_fg > 0] = cv2.GC_FGD
    # the crop IS the window; a one-pixel frame of sure background stands
    # for the paper outside it, and the band inside is probable background
    mask[0, :] = cv2.GC_BGD
    mask[-1, :] = cv2.GC_BGD
    mask[:, 0] = cv2.GC_BGD
    mask[:, -1] = cv2.GC_BGD
    bgm = np.zeros((1, 65), np.float64)
    fgm = np.zeros((1, 65), np.float64)
    cv2.grabCut(small, mask, None, bgm, fgm, GRABCUT_ITERS, cv2.GC_INIT_WITH_MASK)
    fg = (np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)) * 255).astype(np.uint8)
    penumbra = ((paper - hsv[:, :, 2].astype(np.float64)) < SHADOW_FRAC * np.maximum(paper, 1.0)) & (hsv[:, :, 1] <= SAT_MIN)
    fg[penumbra] = 0                                                         # shadow is paper (see SHADOW_FRAC)
    return _finish_mask(fg, g, shape), "", "white"


def _height_class(height_mm: float) -> float:
    return float(math.ceil(height_mm / 10.0 - 1e-9) * 10)


def _ingest_photo(img: np.ndarray, image_path: Path, tag: str, height_mm: float, *, print_scale: float, out_dir: Path, csv_path: Path | None) -> Result:
    height_class = _height_class(height_mm)
    if height_class not in HEIGHT_CLASSES:
        return _reject(
            f"{height_mm:g} mm is taller than any drawer ({max(HEIGHT_CLASSES):g} max). Measure the height as the "
            "tool LIES on the sheet: a bottle on its side is its diameter."
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    loc = _locate(gray)
    if isinstance(loc, Result):
        return loc
    spec, tags, H = loc.spec, loc.tags, loc.H

    notes: list[str] = []
    f35 = read_f35(image_path)
    span_mm, span_px = tag_span(tags, spec)
    if f35:
        D = camera_height(f35, span_mm * print_scale, span_px, img.shape)
        if D < D_HARD_MIN_MM:
            return _reject(
                f"camera almost on the paper ({D:.0f} mm above the sheet): hold the phone higher, the sheet about a "
                "third of the screen",
                size=spec.name,
            )
    else:
        D = D_FALLBACK_MM
        notes.append(f"camera height assumed {D_FALLBACK_MM:g}")
    h_eff = H_EFF_FRAC * height_mm
    c_mm = nadir_mm(H, img.shape)

    rect = rectify(img, tags, spec, H)
    crop, origin = field_crop(rect, spec)
    mask, why, field = segment_tool(crop)
    if why:
        return _reject(why, spec.name)

    # the tool's BODY is the largest component with a part 2 x PENCIL_MM
    # thick (a retraced pencil loop can out-area a small tool, but it is thin
    # everywhere) ...
    n, labels, stats, _cent = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8))
    thick = _keep_thick(mask, 2 * PENCIL_MM, PX_PER_MM)
    thick_ids = {int(i) for i in np.unique(labels[thick > 0]) if i != 0}
    min_area_px = MIN_TOOL_MM2 * PX_PER_MM ** 2
    comps = sorted(((stats[i, cv2.CC_STAT_AREA], i) for i in thick_ids if stats[i, cv2.CC_STAT_AREA] >= min_area_px), reverse=True)
    if not comps:
        return _reject("no tool found in the window: lay the tool flat inside the window and photograph it in place", spec.name)
    area, idx = comps[0]
    # ... plus every component within MERGE_MM of it, thick or not (a strip a
    # highlight cut off), closed and filled ...
    near = cv2.dilate(((labels == idx) * 255).astype(np.uint8), _disk(2 * MERGE_MM, PX_PER_MM))
    merged_ids = {int(i) for i in np.unique(labels[near > 0]) if i != 0}
    tool_mask = (np.isin(labels, list(merged_ids)) * 255).astype(np.uint8)
    tool_mask = _fill_holes(cv2.morphologyEx(tool_mask, cv2.MORPH_CLOSE, _disk(MERGE_MM, PX_PER_MM)))
    # ... and only a THICK component still separate can be a second tool;
    # thin ones elsewhere (a pencil loop round nothing) are ignored
    others = [a for a, i in comps[1:] if i not in merged_ids]
    if others and others[0] > SECOND_FRAC * area:
        return _reject(f"two tools in the window (second is {others[0] / area:.0%} of the largest): one tool per sheet", spec.name)
    bx, by, bw, bh = cv2.boundingRect(tool_mask)
    if bx <= 0 or by <= 0 or bx + bw >= mask.shape[1] or by + bh >= mask.shape[0]:
        return _reject(f"tool touches the edge of the {spec.name} window: take a bigger sheet", spec.name)

    contours, _h = cv2.findContours(tool_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    outer = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(outer, DP_TOL * PX_PER_MM, True)
    sil_mm = _mm_poly(approx, origin)                            # the silhouette as seen, nominal frame: what the preview draws
    tool_sheet = correct_perspective(sil_mm, c_mm, D, h_eff)     # the tool's edge, nominal frame
    tool_true = tool_sheet * print_scale                         # true mm (see DEFAULT_PRINT_SCALE)
    if len(tool_true) < 3:
        return _reject("silhouette is not a polygon", spec.name)
    tool_local, L, W, M = _align_to_min_rect(tool_true)
    residual = (L / 2) * (height_mm / 2) / D          # see THE GATE ON D IS A RESIDUAL
    if residual > RESIDUAL_MAX:
        need = math.ceil((L / 2) * (height_mm / 2) / RESIDUAL_MAX / 50) * 50
        return _reject(
            f"too close for a tool this size ({D:.0f} mm above the sheet, {L:.0f} long, {height_mm:g} tall): hold the "
            f"phone about {need} mm above the sheet (the sheet about a third of the screen)",
            size=spec.name,
        )
    pocket_local_raw = _offset_polygon(tool_local, FOAM_CLEAR)
    pocket_min = pocket_local_raw.min(axis=0)
    pocket_local = pocket_local_raw - pocket_min
    Minv = cv2.invertAffineTransform(M)
    pocket_true = (Minv[:, :2] @ (pocket_local + pocket_min).T).T + Minv[:, 2]
    pocket_sheet = pocket_true / print_scale

    dxf_path = out_dir / f"{tag}.dxf"
    preview_path = out_dir / "preview" / f"{tag}.png"
    _write_dxf(pocket_local, dxf_path)
    _write_preview(
        rect, sil_mm, pocket_sheet,
        f"{tag}  {spec.name} {field}  L {L:.1f}  W {W:.1f}  H {height_mm:g} (class {height_class:g})  D {D:.0f}  h_eff {h_eff:g}  resid {residual:.2f}  {len(tags)} tags  print_scale {print_scale:.3f}",
        preview_path, spec,
    )
    if csv_path is not None:
        try:
            rel = str(dxf_path.relative_to(csv_path.parent))
        except ValueError:
            rel = str(dxf_path)
        upsert_row(csv_path, tag, height_class, rel, L, W, height_mm=height_mm)
    return Result(ok=True, reason="; ".join(notes), dxf_path=dxf_path, preview_path=preview_path, L=L, W=W, size=spec.name, D=D, height_class=height_class)


# ================================================================ trace source (history)


def _ingest_trace(img: np.ndarray, tag: str, height_slot: float | int | str, *, print_scale: float, out_dir: Path, csv_path: Path | None) -> Result:
    try:
        height_class = float(height_slot)
    except (TypeError, ValueError):
        return _reject(f"height slot {height_slot!r} is not a number")
    if height_class not in HEIGHT_CLASSES:
        return _reject(f"height slot {height_class:g} is not one of {', '.join(f'{h:g}' for h in HEIGHT_CLASSES)}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    loc = _locate(gray)
    if isinstance(loc, Result):
        return loc
    spec, tags = loc.spec, loc.tags

    rect = rectify(gray, tags, spec, loc.H)
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
    return Result(ok=True, reason="", dxf_path=dxf_path, preview_path=preview_path, L=L, W=W, size=spec.name, height_class=height_class)


# ================================================================ ingest


def ingest(
    image_path: str | Path,
    tag: str,
    height: float | int | str,
    source: str = "photo",
    *,
    print_scale: float = DEFAULT_PRINT_SCALE,
    out_dir: Path = CAPTURES,
    csv_path: Path | None = TOOL_LIST,
) -> Result:
    """One capture. ``height`` is the tool's measured height in mm for the
    photo source (free text is tolerated: digits and a point are kept, so
    "20mm" is 20) and the gauge slot for the trace source. The paper size is
    NOT an argument: the ArUco quartet in the photo names it (see
    ``identify``). ``print_scale`` corrects a sheet printed at other than
    100% (see ``DEFAULT_PRINT_SCALE``). ``out_dir`` and ``csv_path`` exist so
    a test can point the writes anywhere; ``csv_path=None`` skips the row."""
    if source == "camera":
        raise NotImplementedError("v2: machine Z-plate camera")
    if source not in ("photo", "trace"):
        raise ValueError(f"unknown source {source!r}")

    tag = tag.strip().upper()
    if source == "photo":
        # "16mml", "72.00", "20 mm": digits and a point kept, then whole mm
        digits = "".join(ch for ch in str(height) if ch.isdigit() or ch == ".")
        try:
            height_mm = float(round(float(digits)))
        except ValueError:
            return _reject(f"height {height!r} is not a number of mm")
        if height_mm <= 0:
            return _reject(f"height {height_mm:g} mm is not a height")

    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        return _reject(f"could not read image {image_path}")

    if source == "photo":
        return _ingest_photo(img, Path(image_path), tag, height_mm, print_scale=print_scale, out_dir=out_dir, csv_path=csv_path)
    return _ingest_trace(img, tag, height, print_scale=print_scale, out_dir=out_dir, csv_path=csv_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tool capture ingest: a photo of a tool on a capture sheet in, a pocket polyline out.")
    parser.add_argument("image")
    parser.add_argument("tag")
    parser.add_argument("height", help="the tool's tallest point, mm (photo source); the gauge slot (trace source)")
    parser.add_argument("--source", choices=("photo", "trace"), default="photo")
    parser.add_argument("--print-scale", type=float, default=DEFAULT_PRINT_SCALE, dest="print_scale",
                         help="measured scale-bar length / 100 (default 1.0, a 100%% print)")
    args = parser.parse_args()
    r = ingest(args.image, args.tag, args.height, source=args.source, print_scale=args.print_scale)
    print(r.line())
    sys.exit(0 if r.ok else 1)
