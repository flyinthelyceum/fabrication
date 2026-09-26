"""Callouts: the words V-carved into the birch faces, and the register that
lands each one where the model drew it.

WHAT THIS MODULE IS
===================

One text helper for every birch callout in the station, and the two DXF
layers a second fixture needs. It was ``drawers._callout`` until C17
(2026-09-04) and its output there is unchanged: the drawer fronts carve the
same letters at the same depth in the same place. What changed is that five
parts now share it instead of one owning it:

    drawer fronts      TOOLING / INSTRUMENTS / WORKHOLDING     ``drawers``
    rear door          the drive's word, and MAINS at the IEC  ``rear_door``
    lungs door         EXTRACTION                              ``lungs_door``
    stock comb         STOCK, the header                       ``stock_rails``
    console plate      the E-stop's word, under its guard      ``console_plate``

Each part owns its own words, where they sit and which two of its holes are
the register; this module owns the letters, the carve, the layers and the
checks. Nothing here has a solid of its own: a callout rides in the part it
is cut into, which the assembly already places.

THE PROCESS THE LAYERS ARE FOR (finish ruling, 2026-09-03)
==========================================================

The carcass is painted matte black. The callouts are V-carved THROUGH the
paint to raw birch and left unfilled, so the word is the material showing
through the finish. That order -- paint, then carve -- is the whole reason
this module exists: a part is cut on the first fixture, comes off the
machine, is sanded and painted, and goes BACK on for the carve. Where it
goes back is what ``REGISTER`` says: two circles, each coincident with a void
the part already has, so two dowel pins in the spoilboard put the painted
part exactly where the model has it and the letters land where the model
drew them. No new holes: every register is two features the part carries
anyway (a screw line, a pull's end arcs, a slot's capsule tips), listed per
part below.

The Shapeoko cuts every birch callout. The Universal cuts clear acrylic and
nothing else, so no birch part writes an engrave layer for it and no acrylic
part carries text. The carve here is a ``VCARVE_D``-deep flat stand-in in the
STEP so Fusion shows the word; the real V profile is CAM's, from the letter
outlines on the ``VCARVE`` layer, with the 60-degree bit the tool list
carries (T023).

WHICH FACE, AND THE FLIP
========================

A panel is drawn flat with its CUT face at Z = t. Four of the five carved
faces ARE the CUT face, so the second fixture sees the same drawing as the
first and ``VCARVE`` / ``REGISTER`` sit in the CUT frame. The rear door is
the exception: its operator face is the OUTSIDE face at Z = 0, the BACK of
its drawing. For a back-face carve the part goes on the machine turned over,
and the second fixture sees the first drawing MIRRORED. So for that part
both layers are written as the carved face is seen -- the CUT drawing
flipped about the panel's vertical centreline, x' = w - x -- and the
register circles coincide with the holes only when the part lies carved face
up. That is the frame the CAM operator needs; a layer in the CUT frame would
carve the word backwards in the wrong place. A flipped layer never shares a
file with the CUT frame: one DXF in two frames is a trap for whoever opens
it, so a back-face part writes its second fixture as its OWN file,
``<part>_carve.dxf``, holding the flipped outline for reference and the two
layers, every entity in the one frame (``carve_drawing``). Its first-fixture
DXF carries the CUT frame only. ``layers`` does the flip; ``check_callouts``
works in the part's own frame, before it.

REGISTER, PER PART
==================

    drawer fronts     the pull's two end arcs, PULL_H pins, 100 apart
    lungs door        the pull's two end arcs, the same pins
    stock comb        the first and last slot's capsule tips, SLOT_W pins
    rear door         the two catch bores, SCREW_CLEAR_D pins, on the split
    console plate     the two short-edge lip screws, SCREW_CLEAR_D pins

A pin in a round hole bears all round; a pin in a capsule's end bears on
the half of its circle the arc makes, and two of them in a pull's two ends
locate a panel as well as two holes do. ``check_callouts`` measures both:
a pin of the register's diameter fits the void, and bears on at least the
half a capsule end gives it. The two are also held ``REGISTER_SPAN_MIN``
apart, because a register's angular error is its positional error divided
by its span.

Three of the five registers are capsule ends, and the task's words were
"screw-line or hinge holes". That is a deviation from the letter, chosen
because the drawer fronts, the lungs door and the comb have no round hole on
the carved face and the rule was no new holes. RULED (J2, 2026-09-04): the
capsule-end register is ACCEPTED AS BUILT, so ``check_callouts`` no longer
raises it. It still flags a register that is not a void, or one that bears
so little of its pin the panel would rattle: those are defects, not the ruling.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, radians, tan

from build123d import (
    Align,
    Circle,
    Face,
    Location,
    Part,
    Plane,
    Sketch,
    Text,
    available_fonts,
    extrude,
)

from lib.house import GRID
from stations.cnc_shapeoko.carcass import T

__all__ = [
    "VCARVE_D",
    "VBIT_ANGLE",
    "VBIT_KERF",
    "CALLOUT_H",
    "CALLOUT_CLEAR",
    "CALLOUT_FONTS",
    "CALLOUT_FONT",
    "VCARVE_LAYER",
    "REGISTER_LAYER",
    "REGISTER_SPAN_MIN",
    "Callout",
    "Register",
    "text_sketch",
    "text_width",
    "fit_height",
    "sketch",
    "carve",
    "flip",
    "layers",
    "OUTLINE_LAYER",
    "carve_drawing",
    "check_callouts",
    "describe",
]


# ================================================================ parameters
# Everything specific to the carve. The words, their places and the register
# holes belong to the parts that carry them. No dimension literal appears
# below this block.

VCARVE_D = 1.0
"""Depth of the carve's stand-in pocket in the STEP, and the depth CAM is
asked for at the letter's centreline. SOURCE: drawers.ENGRAVE_D before C17,
value unchanged ("shallow enough that an 18mm front is still an 18mm
front"). CONFIDENCE: chosen."""

VBIT_ANGLE = 60.0
"""Included angle of the V-bit the carve runs with. SOURCE: tools/tool_list.csv
T023, "#302 .50in 60-degree V-bit", in drawer D1. CONFIDENCE: spec (the tool
in the drawer)."""

VBIT_KERF = 2 * VCARVE_D * tan(radians(VBIT_ANGLE / 2))
"""Width the bit opens at the surface when it is VCARVE_D deep: 1.15mm for a
60 at 1mm. SOURCE: geometry. What the paint edge of a stroke actually is."""

CALLOUT_H = GRID * 0.6
"""Cap height of a callout, the station's one text size wherever the face has
room for it. SOURCE: drawers.CALLOUT_H before C17, value unchanged.
CONFIDENCE: chosen."""

CALLOUT_CLEAR = GRID / 8
"""Least paint left between a letter and the nearest edge, cut or device
flange: 2.5mm, better than two kerfs of the bit at depth. Also what
``fit_height`` takes off each side of a band that is too narrow for
CALLOUT_H. SOURCE: VBIT_KERF, rounded up to a grid fraction. CONFIDENCE:
chosen."""

CALLOUT_FONTS = ("Helvetica", "Arial", "DejaVu Sans", "Liberation Sans")
"""Preference order for every carved callout in the station. Resolved against
``available_fonts()`` at import, because a headless box and a laptop do not
have the same font list and a font that is missing is silently substituted --
which is a different drawing, cut without anyone being told. SOURCE:
drawers.CALLOUT_FONTS before C17, unchanged."""

VCARVE_LAYER = "VCARVE"
REGISTER_LAYER = "REGISTER"
"""The two DXF layers a callout part writes on top of ``flat_pattern``'s:
letter outlines for the V toolpath, and the two register circles."""

OUTLINE_LAYER = "OUTLINE_FLIPPED"
"""The one more layer a back-face part's separate carve drawing carries: its
CUT layer turned over, so the register circles can be seen sitting on the
part's holes in the frame the second fixture sees. Reference only: it is
not a toolpath, the part it outlines is already cut."""

REGISTER_SPAN_MIN = GRID * 4
"""Least distance between the two register datums. At 80mm a 0.1mm pin fit
is 0.07 degrees, under 0.5mm of drift across the widest carved word.
SOURCE: chosen. CONFIDENCE: chosen."""

PIN_EPS = 0.05
"""Radial margin the register check probes with: inside the circle by this
much the void must be empty, outside it the wall must be there. SOURCE:
chosen, a tenth of a millimetre on the diameter."""


def _house_font() -> str:
    """First preferred font this machine actually has, else whatever it has."""
    try:
        have = {f.name for f in available_fonts()}
    except Exception:                       # no font manager on this box
        return CALLOUT_FONTS[0]
    for name in CALLOUT_FONTS:
        if name in have:
            return name
    return min(have) if have else CALLOUT_FONTS[0]


CALLOUT_FONT = _house_font()


# ================================================================ the table


@dataclass(frozen=True)
class Callout:
    """One word on one face, panel-local.

    ``centre`` is the centre of the word's bounding box on the carved face,
    in the panel's own frame (the CUT drawing's frame, whichever face the
    word is on). ``face`` is ``"front"`` for the CUT face at Z = t or
    ``"back"`` for the face at Z = 0; a back-face word is mirrored in the
    model so it reads from -Z, and flipped again in ``layers``.
    """

    text: str
    centre: tuple[float, float]
    height: float = CALLOUT_H
    face: str = "front"

    def __post_init__(self) -> None:
        if self.face not in ("front", "back"):
            raise ValueError(f"face must be front|back, got {self.face!r}")


@dataclass(frozen=True)
class Register:
    """The two voids the second fixture's pins seat in, panel-local: each an
    ``(x, y, d)`` where ``d`` is the pin's diameter, which is the hole's or
    the capsule's width. ``what`` names them for the report."""

    a: tuple[float, float, float]
    b: tuple[float, float, float]
    what: str

    @property
    def span(self) -> float:
        return hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])


# ================================================================ letters


def text_sketch(text: str, height: float = CALLOUT_H, font: str = CALLOUT_FONT) -> Sketch:
    """The word as a flat sketch centred on the origin at Z = 0. This is the
    drawers' Text call, verbatim, so their DXF does not move."""
    return Text(
        text,
        font_size=height,
        font=font,
        align=(Align.CENTER, Align.CENTER),
    )


def text_width(text: str, height: float = CALLOUT_H) -> float:
    """Width of the word's bounding box, for a part that anchors an edge of
    the word rather than its centre."""
    return text_sketch(text, height).bounding_box().size.X


def fit_height(band: float) -> float:
    """Cap height for a word in a band ``band`` tall: CALLOUT_H when it fits
    with CALLOUT_CLEAR above and below, else what the band leaves."""
    return min(CALLOUT_H, band - 2 * CALLOUT_CLEAR)


def sketch(c: Callout) -> Sketch:
    """The word in the panel frame at Z = 0. A back-face word is mirrored
    about its own vertical centreline first, so it reads from -Z."""
    sk = text_sketch(c.text, c.height)
    if c.face == "back":
        sk = sk.mirror(Plane.YZ)
    return sk.moved(Location((c.centre[0], c.centre[1], 0)))


def carve(part: Part, callouts: list[Callout], *, thickness: float = T) -> Part:
    """Cut every word's stand-in pocket ``VCARVE_D`` deep into its face of the
    flat panel. This is the drawers' subtraction, verbatim."""
    for c in callouts:
        cut = extrude(sketch(c), amount=VCARVE_D)
        z = thickness - VCARVE_D if c.face == "front" else 0.0
        part -= cut.moved(Location((0, 0, z)))
    return part


# ================================================================ layers


def _circle(x: float, y: float, d: float) -> Face:
    return Circle(d / 2).faces()[0].moved(Location((x, y, 0)))


def flip(face: Face, width: float) -> Face:
    """The face as seen after the panel is turned over about its vertical
    centreline: x' = width - x, y unchanged."""
    return face.mirror(Plane.YZ.offset(width / 2))


def layers(
    callouts: list[Callout], register: Register, *, width: float
) -> dict[str, list[Face]]:
    """``VCARVE`` and ``REGISTER``, drawn as the carved face is seen in the
    second fixture: in the CUT frame for a front-face carve, flipped about
    the panel's vertical centreline (``width`` wide) for a back-face one.
    Every word on one part has to be on one face, because one fixture cuts
    them all."""
    faces = {c.face for c in callouts}
    if len(faces) != 1:
        raise ValueError(f"one fixture carves one face; got {sorted(faces)}")
    back = callouts[0].face == "back"

    vc: list[Face] = []
    for c in callouts:
        vc.extend(sketch(c).faces())
    reg = [_circle(*register.a), _circle(*register.b)]
    if back:
        vc = [flip(f, width) for f in vc]
        reg = [flip(f, width) for f in reg]
    return {VCARVE_LAYER: vc, REGISTER_LAYER: reg}


def carve_drawing(
    callouts: list[Callout], register: Register, *, width: float, cut: list[Face]
) -> dict[str, list[Face]]:
    """The second fixture of a BACK-face carve as its own drawing: the part's
    CUT layer flipped for reference, then ``VCARVE`` and ``REGISTER``, every
    entity in the one frame the carved face is seen in. Write it as
    ``<part>_carve.dxf`` next to the first-fixture DXF, which keeps only the
    CUT frame; never put both frames in one file."""
    if callouts[0].face != "back":
        raise ValueError("carve_drawing is for a back-face carve; a front-face part's layers ride its own DXF")
    out = {OUTLINE_LAYER: [flip(f, width) for f in cut]}
    out.update(layers(callouts, register, width=width))
    return out


# ================================================================ checks


def _rects_overlap(a, b, gap: float) -> bool:
    (ax0, ay0), (ax1, ay1) = a
    (bx0, by0), (bx1, by1) = b
    return ax0 < bx1 + gap and bx0 < ax1 + gap and ay0 < by1 + gap and by0 < ay1 + gap


SKIN = 0.5
"""Depth of the skin under the carved face the register's bearing is read
in. A pin's bearing is an ANGLE (how much of its circle the void's wall
touches), and reading it through the part's whole thickness confuses that
with depth: a 5.4 hole counterbored 12 deep from the back of an 18 plate
read 33% and looked like a rattle. SOURCE: chosen, half the carve depth."""


def _probe(
    part: Part,
    x: float,
    y: float,
    r_in: float,
    r_out: float,
    thickness: float,
    z: tuple[float, float] | None = None,
) -> float:
    """Volume the flat part shares with a ring (or disc when r_in is 0)
    standing at (x, y) through its full thickness, or through ``z`` = (z0, z1)
    of it."""
    face = Circle(r_out)
    if r_in > 0:
        face = face - Circle(r_in)
    z0, z1 = (-thickness, 2 * thickness) if z is None else z
    probe = extrude(face, amount=z1 - z0).moved(Location((x, y, z0)))
    shared = part.intersect(probe)
    if shared is None:
        return 0.0
    if hasattr(shared, "volume"):
        return shared.volume
    return sum(s.volume for s in shared)     # a ShapeList of pieces


def _union_area(faces) -> float:
    """Area of the faces fused into one region; overlaps counted once."""
    fused = faces[0]
    for f in faces[1:]:
        fused = fused.fuse(f)
    return sum(f.area for f in fused.faces())


def check_callouts(
    part: Part,
    callouts: list[Callout],
    register: Register,
    *,
    size: tuple[float, float],
    thickness: float = T,
    keep_clear: list[tuple[tuple[float, float], tuple[float, float]]] = (),
    label: str = "",
) -> list[str]:
    """What a carved part has to be true for. ``part`` is the flat, CARVED
    panel; ``size`` its blank; ``keep_clear`` the rectangles on the carved
    face a word may not run into that are not cuts (a device's flange, a
    hinge leaf). Cuts need no declaring: the carve's floor is read off the
    solid, and a letter that hangs over a hole has less floor than sketch.
    """
    notes: list[str] = []
    w, h = size
    tag = f"{label}: " if label else ""

    for c in callouts:
        sk = sketch(c)
        bb = sk.bounding_box()
        rect = ((bb.min.X, bb.min.Y), (bb.max.X, bb.max.Y))

        if (
            bb.min.X < CALLOUT_CLEAR
            or bb.max.X > w - CALLOUT_CLEAR
            or bb.min.Y < CALLOUT_CLEAR
            or bb.max.Y > h - CALLOUT_CLEAR
        ):
            notes.append(
                f"{tag}{c.text} spans x {bb.min.X:.1f}..{bb.max.X:.1f} y "
                f"{bb.min.Y:.1f}..{bb.max.Y:.1f} on a {w:.0f} x {h:.0f} blank; it "
                f"comes within {CALLOUT_CLEAR:.1f}mm of an edge"
            )
        for kc in keep_clear:
            if _rects_overlap(rect, kc, CALLOUT_CLEAR):
                notes.append(
                    f"{tag}{c.text} at x {bb.min.X:.1f}..{bb.max.X:.1f} y "
                    f"{bb.min.Y:.1f}..{bb.max.Y:.1f} runs within {CALLOUT_CLEAR:.1f}mm of "
                    f"x {kc[0][0]:.1f}..{kc[1][0]:.1f} y {kc[0][1]:.1f}..{kc[1][1]:.1f}, "
                    "which it was told to keep clear of"
                )

        # every letter lands on birch: the carve's floor is the sketch's area
        z_floor = thickness - VCARVE_D if c.face == "front" else VCARVE_D
        floor = 0.0
        for f in part.faces().filter_by(Plane.XY):
            cen = f.center()
            if abs(cen.Z - z_floor) > 1e-6:
                continue
            if bb.min.X - 1e-6 <= cen.X <= bb.max.X + 1e-6 and bb.min.Y - 1e-6 <= cen.Y <= bb.max.Y + 1e-6:
                floor += f.area
        # the word as ONE region: two glyphs that touch (DejaVu's letters on
        # CI, where the house font is absent) would otherwise count their
        # overlap twice and fail a word that carves clean
        want = _union_area(sk.faces())
        # two boolean paths (a fuse, a cut) disagree by ~0.1mm2 on the same
        # word; a letter over a cut edge is square millimetres. Below the
        # kerf's own square the carve cannot express the difference anyway.
        if abs(floor - want) > VBIT_KERF ** 2:
            notes.append(
                f"{tag}{c.text} is carved into {floor:.1f}mm2 of floor and its letters "
                f"are {want:.1f}mm2: {want - floor:.1f}mm2 of the word hangs over a cut or "
                "is not carved at all"
            )

    # the register: a pin fits each void and bears on it, and the two are far
    # enough apart to hold an angle
    # bearing is read in a SKIN under the carved face, where the fixture's
    # pin meets the part first and where a counterbore from the other face
    # cannot make a round hole look like half of one
    z_face = thickness if callouts[0].face == "front" else 0.0
    skin = (z_face - SKIN, z_face) if callouts[0].face == "front" else (0.0, SKIN)
    # RULED (J2, 2026-09-04): the capsule-end register is ACCEPTED AS BUILT.
    # The "REGISTER IS NOT A ROUND HOLE" RULING WANTED note is retired; the
    # not-a-void and rattle checks below stay, because those are real defects.
    for x, y, dia in (register.a, register.b):
        r = dia / 2
        inside = _probe(part, x, y, 0.0, r - PIN_EPS, thickness)
        if inside > 1e-3:
            notes.append(
                f"{tag}register at ({x:.1f}, {y:.1f}) is not a void: a {dia:.1f}mm pin "
                f"meets {inside:.1f}mm3 of birch. It is not one of the part's holes."
            )
        ring = _probe(part, x, y, r + PIN_EPS, r + 3 * PIN_EPS, thickness, skin)
        # the same ring through a solid disc AT the datum: what 100% bearing is.
        disc = extrude(Circle(r + 4 * PIN_EPS), amount=thickness).moved(Location((x, y, 0)))
        full = _probe(disc, x, y, r + PIN_EPS, r + 3 * PIN_EPS, thickness, skin)
        if ring < 0.45 * full:
            notes.append(
                f"{tag}register at ({x:.1f}, {y:.1f}) bears on {100 * ring / full:.0f}% of a "
                f"{dia:.1f}mm pin; a hole gives 100, a capsule end 50. The pin would rattle."
            )
    if register.span < REGISTER_SPAN_MIN:
        notes.append(
            f"{tag}register datums are {register.span:.1f}mm apart, under "
            f"{REGISTER_SPAN_MIN:.0f}; the second fixture cannot hold an angle on them"
        )
    return notes


# ================================================================ report


def describe(callouts: list[Callout], register: Register) -> list[str]:
    """Report lines for a part's ``__main__``: each word, where and how big,
    and the register it goes back on."""
    out: list[str] = []
    for c in callouts:
        bb = sketch(c).bounding_box()
        out.append(
            f"callout {c.text!r} {c.height:.1f} cap on the {c.face} face, centre "
            f"({c.centre[0]:.1f}, {c.centre[1]:.1f}), x {bb.min.X:.1f}..{bb.max.X:.1f} "
            f"y {bb.min.Y:.1f}..{bb.max.Y:.1f}, {VCARVE_LAYER} layer"
        )
    (ax, ay, ad), (bx, by, bd) = register.a, register.b
    out.append(
        f"register {register.what}: ({ax:.1f}, {ay:.1f}) d {ad:.1f} and ({bx:.1f}, {by:.1f}) "
        f"d {bd:.1f}, {register.span:.1f} apart, {REGISTER_LAYER} layer"
        + (" (flipped: back-face carve)" if callouts and callouts[0].face == "back" else "")
    )
    return out


if __name__ == "__main__":
    print(
        f"callouts: font {CALLOUT_FONT}, cap {CALLOUT_H:.0f}, carve {VCARVE_D:.1f} deep with a "
        f"{VBIT_ANGLE:.0f}-degree V ({VBIT_KERF:.2f} kerf at depth), {CALLOUT_CLEAR:.1f} clear; "
        f"layers {VCARVE_LAYER} + {REGISTER_LAYER}, register span >= {REGISTER_SPAN_MIN:.0f}"
    )
    for word in ("STOCK", "EXTRACTION"):
        print(f"  {word!r} is {text_width(word):.1f} wide at {CALLOUT_H:.0f} cap")
