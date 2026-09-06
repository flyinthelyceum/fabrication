"""The machine's own steel, as geometry the carcass has to duck under.

Build order 7. This module owns no station geometry. It builds the eight frame
gusset plates Jared measured on 2026-09-02 and asks the one question no part
can ask about itself: does this part reach into the machine?


WHY THIS EXISTS, AND WHAT IT REPLACED
=====================================

Until 2026-09-02 the machine was one number, ``clear_h`` = 780, an estimate of
the usable height under the frame. Every check compared a part's top against it.
That number was wrong in both directions at once: too generous where a gusset
comes down, and far too mean everywhere a gusset does not reach.

Ruled by Jared once the tape came off the machine: "clear_h as a global
constraint gives up a ton of space between the gussets on x and still over a
foot of usable full height on y. Model the gussets in their entirety and let's
develop around them."

So ``params.Gusset`` carries the profile arithmetic, ``Station.clear_z(x, y)``
is the ceiling at a point, and this module turns the same four gussets into
solids and intersects them with the placed carcass. Both readings come off the
same measurements, and the solids are what tells you WHERE a part is in trouble
rather than only that it is.


WHAT A CLASH MEANS HERE
=======================

Nothing. There is no such thing as an intended overlap between the carcass and
the machine, so unlike ``assembly.interference`` there is no joint table and no
verdict to reach: every shared mm3 is a collision. What the report carries
instead is the two ways out, both measured off the shared solid:

    DROP    lower the part by this much and it clears the gusset
    REACH   how far in from the leg's inner face the gusset comes at the height
            the part is trying to occupy, which is how deep a relief in the part
            would have to be

Neither is a recommendation. Which one to spend is a design decision and it is
Jared's.


WHAT IS SETTLED AND WHAT IS STILL OPEN
=======================================

Jared's photographs and calipers make the gussets flat plates,
``gusset_plate_t`` thick (6.35mm, 1/4in), at the leg they brace, not the
wall-to-wall solids the first pass modelled for want of that measurement. How
many of them there are was open until Jared RULED it 2026-09-02, verbatim:
"Each side has two gussets so eight total mirrored across the centerline of
each axis." ``Station.gussets`` places eight, not four, and that is settled.

Still open: every solid this module builds runs intrusion-depth solid from the
leg face to the top band. The measured ``gusset_y_block`` says a Y gusset's
inner end may really be only a ~95 x 86mm block, not solid the whole way. If
so, every clash this module reports is smaller than the real one, in the more
room direction. ``params.check`` carries the note.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import Align, Box, Compound, Cylinder, Location, Part, Plane, Unit, export_step

from stations.cnc_shapeoko.assembly import NOISE_VOL, Component, components
from stations.cnc_shapeoko.carcass import DATUMS, EXPORT_DIR, Datums, gusset_prism
from stations.cnc_shapeoko.params import Gusset
from stations.cnc_shapeoko.parts.leg_joint import bolts as leg_bolts

__all__ = [
    "MACHINE_NAME",
    "Clash",
    "solid",
    "gussets",
    "front_leg_flanges",
    "leg_envelopes",
    "leg_clearance",
    "front_left_leg_envelope",
    "clearance",
    "check_machine",
    "main",
]

MACHINE_NAME = "machine_gussets"


# ---------------------------------------------------------------- solids


def solid(g: Gusset) -> Part:
    """One gusset plate as a trapezoidal prism in station coordinates.

    ``carcass.gusset_prism`` is the single source of this shape now: a part
    that needs a relief cut subtracts the same solid this module intersects
    against, so the notch and the check that verifies it cannot drift apart.
    """
    return gusset_prism(g)


def gussets(d: Datums = DATUMS) -> list[tuple[Gusset, Part]]:
    """All eight, each paired with the parameters it was built from."""
    return [(g, solid(g)) for g in d.s.gussets]


def _slab(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Part:
    """An axis-aligned box from two corners in any order, station coordinates."""
    x0, x1 = sorted(x)
    y0, y1 = sorted(y)
    z0, z1 = sorted(z)
    return Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x0, y0, z0))
    )


def _flange_reach(d: Datums = DATUMS) -> float:
    """How far a flange reaches into the opening past the leg's inner face.
    The measured ``flange_reach`` (2026-09-04); while it was unmeasured, the
    width the bolt pattern proved -- the outer hole's far edge -- which is a
    floor on the real width and never an overstatement."""
    h = d.s.leg_holes
    return h.flange_reach if h.flange_reach is not None else h.span_h + h.hole_d / 2


def front_leg_flanges(d: Datums = DATUMS) -> list[tuple[str, Part]]:
    """The two front legs' Y-facing flanges, as the envelope anything pulled
    out of a front bay has to pass, in station coordinates.

    Built for the INBOARD case only: the flange running from the leg's HEEL
    (its outer corner, ``leg_wall_t`` outside both inner faces) into the
    opening, ``leg_wall_t`` thick in Y just outside the leg opening's front
    face, ``flange_w`` wide in X from the heel so its toe stands
    ``flange_reach`` past the inner face, floor to table. That is the case
    that can stand in something's way; the outboard case is outside the
    opening and clashes with nothing in it, so when
    ``LegHoles.front_flange_inboard`` reads False this returns nothing.

    MEASURED 2026-09-04: inboard, 84.0 outside, on every leg. The inner
    fillet is not part of this plate; ``leg_envelopes`` carries it.
    """
    s = d.s
    h = s.leg_holes
    if h.front_flange_inboard is False:
        return []
    reach = _flange_reach(d)
    t = s.leg_wall_t
    z = (0.0, s.table_h)             # floor to the table: the leg's whole height
    y = (d.y_front - t, d.y_front)
    return [
        ("front left leg, Y flange", _slab((d.x_left - t, d.x_left + reach), y, z)),
        ("front right leg, Y flange", _slab((d.x_right - reach, d.x_right + t), y, z)),
    ]


def leg_envelopes(d: Datums = DATUMS) -> list[tuple[str, Part]]:
    """All four legs as the steel the carcass stands inside, station
    coordinates: (label, solid) per corner.

    Each leg is one angle (MEASURED 2026-09-03), both flanges INBOARD
    (MEASURED 2026-09-04), ``flange_w`` outside, ``leg_wall_t`` thick, floor
    to table, its HEEL at the corner one wall outside the station datum on
    each axis, and its INSIDE corner a fillet of ``inner_fillet_r`` -- steel
    filling the corner between the two inner faces, which is exactly where a
    square carcass corner flush to both faces wants to be. The X flange is
    the bolted one; the Y flange is the band across a bay's open front or the
    brain band's rear.

    Everything here is a solid in the machine's own steel, so the carcass
    shares nothing with it, ever: ``leg_clearance`` reports every mm3.
    """
    s = d.s
    h = s.leg_holes
    if h.front_flange_inboard is not True:
        return []
    reach = _flange_reach(d)
    t = s.leg_wall_t
    r = h.inner_fillet_r
    z = (0.0, s.table_h)
    hole_r = h.hole_d / 2
    over = 1.0  # overshoot past both flange faces so the boolean is clean
    bolts_by_leg: dict[str, list] = {}
    for b in leg_bolts(d):
        bolts_by_leg.setdefault(b.leg, []).append(b)
    out: list[tuple[str, Part]] = []
    corners = (
        ("front left leg", d.x_left, d.y_front, 1.0, 1.0, "left_front"),
        ("front right leg", d.x_right, d.y_front, -1.0, 1.0, "right_front"),
        ("rear left leg", d.x_left, d.y_rear, 1.0, -1.0, "left_rear"),
        ("rear right leg", d.x_right, d.y_rear, -1.0, -1.0, "right_rear"),
    )
    for label, cx, cy, sx, sy, leg_key in corners:
        # the inner faces meet at (cx, cy); sx, sy point INTO the opening
        x_flange = _slab((cx - sx * t, cx), (cy - sy * t, cy + sy * reach), z)
        y_flange = _slab((cx - sx * t, cx + sx * reach), (cy - sy * t, cy), z)
        leg = x_flange + y_flange
        if r > 0.0:
            fillet = _slab((cx, cx + sx * r), (cy, cy + sy * r), z) - Cylinder(
                r, z[1] - z[0], align=(Align.CENTER, Align.CENTER, Align.MIN)
            ).moved(Location((cx + sx * r, cy + sy * r, z[0])))
            leg = leg + fillet
        # The X flange is the same wall leg_joint.bolts() already bolts the
        # carcass end wall through, so its M6 clearance holes reuse those
        # positions rather than re-deriving the pattern; a hole only removes
        # steel, so the clash volume this envelope feeds stays a valid gate.
        for b in bolts_by_leg.get(leg_key, []):
            plane = Plane(
                origin=(cx - sx * t, b.y, b.z), x_dir=(0.0, 1.0, 0.0), z_dir=(sx, 0.0, 0.0)
            )
            cutter = plane * Cylinder(
                hole_r, t + 2 * over, align=(Align.CENTER, Align.CENTER, Align.MIN)
            ).moved(Location((0, 0, -over)))
            leg = leg - cutter
        leg.label = label
        out.append((label, leg))
    return out


def front_left_leg_envelope(d: Datums = DATUMS) -> list[tuple[str, str, Part]]:
    """The front-left leg as the steel a door hinged on the left end wall's
    front edge swings against: (label, case, solid), station coordinates.

    The leg is an angle (MEASURED 2026-09-03). Its X-facing flange is the
    bolted one: ``leg_wall_t`` thick just outside ``x_left``, running from
    the corner into the opening by ``flange_w`` -- the width the bolt pattern
    proves until the flange is measured -- and it is present in both cases,
    so its case reads "measured". Its Y-facing flange is the open reading:
    while ``LegHoles.front_flange_inboard`` is None BOTH cases are built and
    labelled, "inboard" (``front_leg_flanges``, the plate across the bay's
    front) and "outboard" (the same plate running away from the opening,
    across the leg's front face at x < x_left); once it is measured only the
    real one is. The vertex is covered either way: the X flange runs from
    ``y_front - leg_wall_t`` so the corner is steel in both.

    A caller reports gaps and shared volume per case; the swing that matters
    is the one the tape settles.
    """
    s = d.s
    h = s.leg_holes
    w = _flange_reach(d)
    t = s.leg_wall_t
    out: list[tuple[str, str, Part]] = [
        (
            "front left leg, X flange",
            "measured",
            _slab((d.x_left - t, d.x_left), (d.y_front - t, d.y_front + w), (0.0, s.table_h)),
        )
    ]
    for label, plate in front_leg_flanges(d):
        if label.startswith("front left"):
            out.append((f"{label} (inboard case)", "inboard", plate))
    if h.front_flange_inboard is not True:
        out.append(
            (
                "front left leg, Y flange (outboard case)",
                "outboard",
                Box(w, t, s.table_h, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
                    Location((d.x_left - w, d.y_front - t, 0.0))
                ),
            )
        )
    return out


# ---------------------------------------------------------------- clashes


@dataclass(frozen=True)
class Clash:
    """One part reaching into one gusset."""

    part: str
    gusset: str
    volume: float
    bbox: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    drop: float
    reach: float

    def line(self) -> str:
        (x0, x1), (y0, y1), (z0, z1) = self.bbox
        return (
            f"{self.part} <-> {self.gusset}: {self.volume / 1000:,.1f} cm3\n"
            f"                  x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  "
            f"z {z0:.1f}..{z1:.1f}\n"
            f"                  drop {self.drop:.1f}mm, or relieve {self.reach:.1f}mm "
            "in from the leg face"
        )


def _overlaps(a, b) -> bool:
    """Bounding-box prefilter, so a boolean is only paid for where it can bite."""
    return not (
        a.max.X < b.min.X or b.max.X < a.min.X
        or a.max.Y < b.min.Y or b.max.Y < a.min.Y
        or a.max.Z < b.min.Z or b.max.Z < a.min.Z
    )


def clearance(
    comps: list[Component] | None = None, d: Datums = DATUMS
) -> list[Clash]:
    """Every part that shares more than ``NOISE_VOL`` with a gusset."""
    comps = components(d) if comps is None else comps
    found: list[Clash] = []

    for g, body in gussets(d):
        gbb = body.bounding_box()
        for c in comps:
            if not _overlaps(c.bbox, gbb):
                continue
            try:
                shared = c.part & body
            except Exception:               # empty intersection, on some kernels
                continue
            if shared is None or shared.volume <= NOISE_VOL:
                continue

            bb = shared.bounding_box()
            axis = ("X", "Y")[g.axis == "y"]
            us = sorted(g.u_at(v) for v in (getattr(bb.min, axis), getattr(bb.max, axis)))
            found.append(
                Clash(
                    c.label,
                    g.label,
                    shared.volume,
                    (
                        (bb.min.X, bb.max.X),
                        (bb.min.Y, bb.max.Y),
                        (bb.min.Z, bb.max.Z),
                    ),
                    bb.max.Z - g.ceiling_at(us[0]),
                    us[1],
                )
            )

    found.sort(key=lambda c: -c.volume)
    return found


# ---------------------------------------------------------------- checks


def leg_clearance(
    comps: list[Component] | None = None, d: Datums = DATUMS
) -> list[tuple[str, str, float, tuple[tuple[float, float], tuple[float, float], tuple[float, float]]]]:
    """(part, leg, shared mm3, bbox) for every part sharing more than
    ``NOISE_VOL`` with a leg's steel, AS PLACED. Pull-outs and swings are the
    parts' own to sweep (the carriage, the two doors, the drawers); this is
    the standing carcass against the four angles, fillets included."""
    comps = components(d) if comps is None else comps
    found = []
    for label, leg in leg_envelopes(d):
        lb = leg.bounding_box()
        for c in comps:
            if not _overlaps(c.bbox, lb):
                continue
            try:
                shared = c.part & leg
            except Exception:
                continue
            if shared is None or shared.volume <= NOISE_VOL:
                continue
            bb = shared.bounding_box()
            found.append(
                (
                    c.label,
                    label,
                    shared.volume,
                    ((bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z)),
                )
            )
    found.sort(key=lambda f: -f[2])
    return found


def check_machine(
    comps: list[Component] | None = None, d: Datums = DATUMS
) -> list[str]:
    """Constraints the machine imposes on the station, part by part."""
    notes: list[str] = []
    for part, leg, vol, ((x0, x1), (y0, y1), (z0, z1)) in leg_clearance(comps, d):
        notes.append(
            f"{part} stands inside the {leg}'s steel: {vol / 1000:,.2f} cm3, "
            f"x {x0:.1f}..{x1:.1f} y {y0:.1f}..{y1:.1f} z {z0:.1f}..{z1:.1f}. "
            "The angle's flanges run inboard and its inside corner is a "
            f"{d.s.leg_holes.inner_fillet_r:.2f}mm fillet (MEASURED 2026-09-04)."
        )
    for cl in clearance(comps, d):
        (_, _), (_, _), (z0, z1) = cl.bbox
        notes.append(
            f"{cl.part} runs into the {cl.gusset}: {cl.volume / 1000:,.1f} cm3 of "
            f"birch inside the machine's steel, z {z0:.1f}..{z1:.1f}. It clears "
            f"if the part drops {cl.drop:.1f}mm, or if it is relieved "
            f"{cl.reach:.1f}mm in from the leg face over that height."
        )
    return notes


def export(comp: Compound, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{MACHINE_NAME}.step"
    export_step(comp, p, unit=Unit.MM)
    return p


# ---------------------------------------------------------------- main


def main() -> None:
    d = DATUMS
    s = d.s

    print(
        f"MACHINE: ceiling {s.clear_h_min:.2f} at the leg faces, "
        f"{s.z_beam:.2f} at the beam underside (derived)"
    )
    children = []
    for g, body in gussets(d):
        bb = body.bounding_box()
        children.append(body)
        body.label = g.label
        print(
            f"  {g.label:16s} eats {g.intrude:8.3f}mm of {g.axis.upper()}, "
            f"z {g.z_bot:.2f}..{g.z_beam:.2f}   "
            f"x {bb.min.X:7.1f}..{bb.max.X:7.1f}  "
            f"y {bb.min.Y:7.1f}..{bb.max.Y:7.1f}  "
            f"{body.volume / 1000:8.1f} cm3"
        )

    print("\nwhat the envelope allows")
    print(
        f"  everywhere                 up to {s.clear_h_min:.2f}"
    )
    print(
        f"  x {s.gusset_x_intrude:.2f}..{s.leg_x_inner - s.gusset_x_intrude:.2f}"
        f"  y {s.gusset_y_intrude:.2f}..{s.leg_y_inner - s.gusset_y_intrude:.2f}"
        f"   up to {s.z_beam:.2f}, the full height"
    )

    comps = components(d)
    print("\nclearance against the carcass")
    found = clearance(comps, d)
    if not found:
        print(f"  nothing shares more than {NOISE_VOL:.0f} mm3 with a gusset")
    for cl in found:
        print(f"  {cl.line()}")

    path = export(Compound(label=MACHINE_NAME, children=children))
    print(f"\nwrote {path}  {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
