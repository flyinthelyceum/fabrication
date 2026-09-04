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

from build123d import Align, Box, Compound, Location, Part, Unit, export_step

from stations.cnc_shapeoko.assembly import NOISE_VOL, Component, components
from stations.cnc_shapeoko.carcass import DATUMS, EXPORT_DIR, Datums, gusset_prism
from stations.cnc_shapeoko.params import Gusset

__all__ = [
    "MACHINE_NAME",
    "Clash",
    "solid",
    "gussets",
    "front_leg_flanges",
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


def front_leg_flanges(d: Datums = DATUMS) -> list[tuple[str, Part]]:
    """The two front legs' Y-facing flanges, as the envelope anything pulled
    out of a front bay has to pass, in station coordinates.

    Built for the INBOARD case only: the flange running from the leg's corner
    into the opening, ``leg_wall_t`` thick in Y just outside the leg opening's
    front face, ``flange_w`` wide in X, floor to table. That is the case that
    can stand in something's way; the outboard case is outside the opening and
    clashes with nothing in it, so when ``LegHoles.front_flange_inboard`` reads
    False this returns nothing.

    ``flange_w`` is unmeasured. Until it is, the plate is built at the width
    the bolt pattern PROVES -- the outer hole's far edge, ``span_h`` plus half
    the hole -- which is a floor on the real width and never an overstatement.
    The direction is unmeasured too; a caller checking against these plates
    reports MEASURE while it is None and a clash once it is True.
    """
    s = d.s
    h = s.leg_holes
    if h.front_flange_inboard is False:
        return []
    w = h.flange_w if h.flange_w is not None else h.span_h + h.hole_d / 2
    t = s.leg_wall_t
    z0, z1 = 0.0, s.table_h          # floor to the table: the leg's whole height
    out: list[tuple[str, Part]] = []
    for label, x0 in (("front left leg, Y flange", d.x_left), ("front right leg, Y flange", d.x_right - w)):
        plate = Box(w, t, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
            Location((x0, d.y_front - t, z0))
        )
        out.append((label, plate))
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
    w = h.flange_w if h.flange_w is not None else h.span_h + h.hole_d / 2
    t = s.leg_wall_t
    out: list[tuple[str, str, Part]] = [
        (
            "front left leg, X flange",
            "measured",
            Box(t, w + t, s.table_h, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
                Location((d.x_left - t, d.y_front - t, 0.0))
            ),
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


def check_machine(
    comps: list[Component] | None = None, d: Datums = DATUMS
) -> list[str]:
    """Constraints the machine imposes on the station, part by part."""
    notes: list[str] = []
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
