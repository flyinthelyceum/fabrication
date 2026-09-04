"""Stiles: the four fixed birch verticals standing behind the legs' Y flanges.

WHAT THIS PART IS
=================

RULED 2026-09-04 (Jared), verbatim: "absolutely no overlays. reconfigure
depth to ensure everything is a la kerf design cabinets." The legs were
measured the same day: every flange runs INBOARD, 84 outside, so at each of
the four corners a 3.5mm steel band stands across the carcass plane,
``LegHoles.flange_reach`` (80.48) past the end wall's outer face, floor to
table. Behind that band, inside the opening, this part stands one fixed
birch STILE per corner:

    stile_front_left      x  t .. t + stile_w        y  0 .. t
    stile_front_right     x  x_right - t - stile_w .. x_right - t
    stile_rear_left       the same two X spans       y  y_rear - t .. y_rear
    stile_rear_right

``Datums.stile_w`` is the flange's reach past the end wall's inner face plus
``Station.stile_toe_land``: 64.48 at the measured leg. The stile is ``t``
deep, so its outer face is the carcass plane the flange band lies on, and it
runs the full opening height with a tenon THROUGH the deck and THROUGH the
cap, exposed at the deck's underside and the cap's top face and at the two
edges the notches open on. That is the Kerf language the ruling names:
every joint a visible housing, and every door and drawer front INSET between
a stile and a divider, flush in the carcass plane, no overlay anywhere.

WHAT HANGS ON THEM
==================

    lungs door       hinged on the FRONT-LEFT stile's inner edge, a proud
                     knuckle in the gap, opens to 180 against the leg's
                     flange (``lungs_door``)
    rear door        between the two REAR stiles' inner edges, on the deck's
                     rear edge hinge (``rear_door``)
    drawer fronts    between the stock/hands divider and the console cheek,
                     inside the FRONT-RIGHT stile (``drawers``)
    console reveal   between the console cheek and the FRONT-RIGHT stile
                     (``console_plate``)

WHAT THE MACHINE DOES TO THEM
=============================

The stile stands at the leg corner, so the frame's X gusset plate (at y 0..
plate_t, reaching into X from the leg face as it rises) meets the tenon
where it passes through the cap. The stile is relieved to that plate's own
solid, the way the walls and the cap are, over the same footprint test
(``gussets_over``), so the notch and the machine check are one solid.

PANEL CONVENTION
================

Drawn flat: local +Y up from the tenon's bottom (``deck_z[0]``), local +Z
through the thickness from the INSIDE face at Z = 0 to the OUTER face -- the
carcass plane, the face the room sees -- at Z = t, so the DXF's CUT layer is
that face. Local +X runs station +X on the front stiles and station -X on
the rear ones (the rear pair are seen from behind), so local +Y is up on all
four. The four blanks are one rectangle; only the gusset relief at the top
corner nearest the wall tells them apart.
"""

from __future__ import annotations

from build123d import Compound, Part, Plane

from lib.house import SHEET_5X5_BALTIC, fits
from stations.cnc_shapeoko.carcass import (
    DATUMS,
    T,
    Datums,
    export_part,
    gusset_prism,
    gussets_over,
    panel,
    to_local,
)

__all__ = [
    "STEM",
    "TENON",
    "labels",
    "blank_size",
    "span",
    "plane",
    "build",
    "place",
    "placed_all",
    "joint_table",
    "check_stiles",
    "export",
]

D: Datums = DATUMS

STEM = "stile"

# ================================================================ parameters
# The stile's width and its four positions are Datums' (``stile_w``,
# ``stiles``); the land past the toe is params' (``stile_toe_land``). What is
# this part's alone:

TENON = T
"""How far the tenon runs into the deck and into the cap: the whole panel,
so the end grain shows on the far face. RULED 2026-09-04 (Kerf: exposed
through-tenon joinery where stiles meet deck and cap). SOURCE: ruling;
CONFIDENCE ruling. The blind ``TONGUE_D`` the walls use is not this joint."""


# ================================================================ derivations


def labels(d: Datums = D) -> list[str]:
    return [label for label, _x, _y in d.stiles]


def span(label: str, d: Datums = D) -> tuple[tuple[float, float], tuple[float, float]]:
    """(x span, y span) of one stile, station coordinates."""
    for lab, xs, ys in d.stiles:
        if lab == label:
            return (xs, ys)
    raise KeyError(label)


def blank_size(d: Datums = D) -> tuple[float, float]:
    """(width, height) of every stile's blank: the stile's width, and the
    opening height plus a tenon through the deck and through the cap."""
    return (d.stile_w, d.bay_h + 2 * TENON)


def z_bottom(d: Datums = D) -> float:
    """Station Z of the tenon's bottom: the deck's underside."""
    return d.deck_top - TENON


def plane(label: str, d: Datums = D) -> Plane:
    """The stile's frame. Local Z runs from the inside face out to the
    carcass plane; local X runs +X on the front stiles and -X on the rear
    ones, which is what keeps local Y up on both."""
    (x0, x1), (y0, y1) = span(label, d)
    if "_front_" in label:
        return Plane(origin=(x0, y1, z_bottom(d)), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    # the rear stiles face the other way; local X runs -X so local Y stays up
    return Plane(origin=(x1, y0, z_bottom(d)), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))


# ================================================================ build


def _gusset_relief(label: str, d: Datums = D) -> Part | None:
    """The gusset plates this stile's own footprint would clash with, cut out
    of it as their own trapezoidal solids, in the stile's frame."""
    (x0, x1), (y0, y1) = span(label, d)
    cutters = None
    for g in gussets_over((x0, x1), (y0, y1), d.s.gussets):
        c = to_local(plane(label, d), gusset_prism(g))
        cutters = c if cutters is None else cutters + c
    return cutters


def build(label: str, d: Datums = D) -> Part:
    """One stile, flat. A plain blank less the machine's steel: every joint
    it makes is cut in the part that receives it (the deck's and the cap's
    notches), and its outer face carries nothing."""
    w, h = blank_size(d)
    p = panel(w, h, d.t)
    relief = _gusset_relief(label, d)
    if relief is not None:
        p -= relief
    return p


def place(label: str, flat: Part | None = None, d: Datums = D) -> Part:
    flat = build(label, d) if flat is None else flat
    return plane(label, d) * flat


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, placed solid) for the four stiles: birch, nested."""
    return [(label, "carcass", place(label, d=d)) for label in labels(d)]


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples: the
    tenon through the deck and through the cap (housings, the notches cut
    ``DADO_FIT`` oversize so no volume is shared), and the outer edge on the
    end wall's inner face (butt)."""
    from stations.cnc_shapeoko.parts.bay_walls import WALLS

    out: list[tuple] = []
    for label in labels(d):
        wall = WALLS[0].name if label.endswith("_left") else WALLS[3].name
        out.append(("base_deck", label, "housing", "z", d.deck_z[0], d.deck_top,
                    "stile's tenon through the deck's edge notch"))
        out.append(("top_cap", label, "housing", "z", d.top_z[0], d.top_z[1],
                    "stile's tenon through the cap's edge notch"))
        out.append((wall, label, "butt", None, 0.0, 0.0,
                    "stile's outer edge on the end wall's inner face"))
    return out


# ================================================================ checks


def check_stiles(d: Datums = D) -> list[str]:
    """What the four stiles have to be true for. The machine module owns
    whether one stands in the steel; the deck and the cap own their notches;
    the doors and fronts own their reveals to a stile's inner edge."""
    notes: list[str] = []
    s = d.s
    h = s.leg_holes
    w, hgt = blank_size(d)

    reach = h.flange_reach
    if reach is None:
        notes.append(
            "the leg's flange width is not measured (LegHoles.flange_w is None): "
            "the stile is sized to the width the bolt pattern proves and may be "
            "short of the toe. MEASURE THIS."
        )
    else:
        toe_past_wall = reach - d.t
        if w < toe_past_wall:
            notes.append(
                f"a stile is {w:.2f} wide and the flange's toe stands {toe_past_wall:.2f} "
                "past the end wall's inner face: steel shows past the stile"
            )
        if w - toe_past_wall < s.stile_toe_land - 1e-9:
            notes.append(
                f"a stile's inner edge is {w - toe_past_wall:.2f} past the toe against "
                f"a {s.stile_toe_land:.1f} land"
            )

    if not fits((w, hgt), SHEET_5X5_BALTIC):
        notes.append(f"stile blank {w:.0f} x {hgt:.0f} does not come out of a 5x5 sheet")

    for label in labels(d):
        (x0, x1), (y0, y1) = span(label, d)
        bb = place(label, d=d).bounding_box()
        want = ((x0, x1), (y0, y1), (z_bottom(d), d.top_z[1]))
        got = ((bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z))
        for axis, g, e in zip("xyz", got, want):
            if abs(g[0] - e[0]) > 0.05 or abs(g[1] - e[1]) > 0.05:
                notes.append(
                    f"{label} landed at {axis} {g[0]:.1f}..{g[1]:.1f} and belongs at "
                    f"{e[0]:.1f}..{e[1]:.1f}. Its plane is wrong."
                )
        hit = gussets_over((x0, x1), (y0, y1), s.gussets)
        if hit:
            notes.append(
                f"{label} is relieved to {', '.join(g.label for g in hit)} where its tenon "
                "passes the cap. Expected, and worth knowing before the tenon is read as "
                "a plain rectangle."
            )

    notes.append(
        f"STILES, standing note. RULED 2026-09-04: the flange band at each corner is a "
        f"fixed birch stile, {w:.2f} wide ({d.stile_w - s.stile_toe_land:.2f} to the "
        f"flange's toe plus {s.stile_toe_land:.1f} land), {d.t:.0f} deep, tenoned "
        f"{TENON:.0f} THROUGH the deck and the cap, exposed. Openings between stiles: "
        f"lungs {d.lungs_opening_x[1] - d.lungs_opening_x[0]:.2f}, hands "
        f"{d.hands_opening_x[1] - d.hands_opening_x[0]:.2f} (the console cheek stands "
        f"inside it), rear {d.rear_opening_x[1] - d.rear_opening_x[0]:.2f}. Every door "
        "and drawer front is inset, flush in the carcass plane; no overlay anywhere. "
        "Expected, and worth knowing before a front is read against the brief."
    )
    return notes


# ================================================================ export


def export(d: Datums = D) -> list:
    written = []
    for label in labels(d):
        written += export_part(build(label, d), label)
    return written


if __name__ == "__main__":
    d = D
    w, h = blank_size(d)
    print(f"{STEM}s: four blanks {w:.2f} x {h:.0f} x {d.t:.0f}, tenon {TENON:.0f} through deck and cap")
    for label, group, part in placed_all(d):
        bb = part.bounding_box()
        print(
            f"  {label:<20} x {bb.min.X:7.1f}..{bb.max.X:7.1f}  y {bb.min.Y:7.1f}..{bb.max.Y:7.1f}"
            f"  z {bb.min.Z:6.1f}..{bb.max.Z:6.1f}  {part.volume / 1000:.1f} cm3"
        )
    ab = Compound(children=[p for _l, _g, p in placed_all(d)]).bounding_box()
    print(f"  all four: x {ab.min.X:.1f}..{ab.max.X:.1f} y {ab.min.Y:.1f}..{ab.max.Y:.1f}")
    for n in check_stiles(d):
        print(f"  - {n}")
    for p in export(d):
        print(f"wrote {p}")
