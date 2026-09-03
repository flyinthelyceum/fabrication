"""The five carcass parts, brought together in station coordinates.

Build order 6. This module owns no geometry. It imports every part module's
builder, places each part with the same datum plane the part's own module uses,
and then asks three questions the individual parts cannot ask about themselves:

    1. does the whole thing close up          -> one STEP, exported
    2. do any two parts occupy the same mm3   -> the interference report
    3. does the assembled envelope fit under the machine
                                              -> the fit report

Nothing here may invent a location. If a part module publishes a placement
helper (``place``, ``placed_all``, ``build_assembly``), this module calls it.
Where a part has none, it uses the ``Datums`` plane named in that part's own
docstring. When ``leg_x_inner`` moves, every location below moves with it,
because none of them are written down here.


WHAT AN OVERLAP MEANS IN THIS CARCASS
=====================================

Every joint in the station is a HOUSING: the receiver has material removed and
the member drops into the void. Housings are cut ``DADO_FIT`` (0.2mm) oversize,
because plywood runs undersize and a dado cut exactly T is a gap. There is not
one press-fit tab in the carcass; ``finger_slots`` went unused in all five
parts.

So the intended overlap between any two parts of this carcass is EXACTLY ZERO,
and the interesting question is not "is this overlap intended" but "where is
it". Two answers, and they want different fixes:

    SHORT HOUSING   the two parts are a declared joint, the overlap lies inside
                    that joint's engagement band -- the slab of the receiver
                    within ``HOUSE_ENGAGE`` of its mating face -- and the housing
                    exists over PART of the footprint. It stops early. Fix:
                    lengthen it. The parts are right about each other; one is
                    short.

    MISSING HOUSING same band, but the member is engaged over 100% of its
                    footprint: the receiver cut nothing at all here. Either the
                    housing was never cut, or it was cut somewhere else. Fix:
                    find out which, because a housing in the wrong place is two
                    faults, not one.

    COLLISION       everything else. Two parts that were never meant to touch,
                    or a member driven clean through a receiver. Fix: move
                    something.

The engaged fraction that separates SHORT from MISSING is measured, not
declared: the overlap is divided by the volume the member would occupy in an
uncut receiver.

``JOINTS`` below is the declaration of intent, written from the five part
modules' own docstrings rather than inferred from the solids -- an inferred
joint table would agree with whatever the model does, including its mistakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from build123d import Box, Compound, Location, Part, Shape, Unit, export_step

from stations.cnc_shapeoko.carcass import (
    DATUMS,
    EXPORT_DIR,
    HOUSE_ENGAGE,
    TOP_GAP_MIN,
    Datums,
    check_carcass,
    clear_over_relieved,
)
from stations.cnc_shapeoko.parts import (
    base_deck,
    bay_walls,
    leg_tie,
    spine_panel,
    top_cap,
)

__all__ = [
    "ASSEMBLY_NAME",
    "NOISE_VOL",
    "Component",
    "Joint",
    "Overlap",
    "components",
    "assembly",
    "joints",
    "interference",
    "envelope",
    "check_assembly",
    "main",
]

ASSEMBLY_NAME = "carcass_assembly"

NOISE_VOL = 1.0
"""mm3 below which an intersection is boolean noise, not a shared volume.

A 1mm3 lump is a 1 x 1 x 1 cube. No joint in this carcass is decided at that
scale: the smallest real feature is the 0.2mm dado fit over a 660mm edge, which
is 2400mm3 if it ever went the wrong way.
"""

BAND_EPS = 1e-6


# ---------------------------------------------------------------- components


@dataclass(frozen=True)
class Component:
    """One placed solid in the assembly."""

    label: str
    group: str          # carcass | plinth | tie
    part: Part

    @property
    def bbox(self):
        return self.part.bounding_box()


def components(d: Datums = DATUMS) -> list[Component]:
    """Every part of the carcass, placed in station coordinates.

    The plinth is enumerated rail by rail rather than taken whole from
    ``base_deck.build_plinth()``, because a rail-to-rail housing is a joint like
    any other and a fused plinth would hide it from the interference check.
    """
    out: list[Component] = []

    # 1. base deck, on its own plane
    out.append(Component("base_deck", "carcass", d.deck_plane * base_deck.build_deck()))

    # ... and the plinth under it, on base_deck's own rail planes
    rail_x = base_deck.build_plinth_rail_x()
    rail_x_grille = base_deck.build_plinth_rail_x(grille=True)
    rail_y = base_deck.build_plinth_rail_y()
    out.append(
        Component("plinth_rail_front", "plinth", base_deck._plane_rail_x_front() * rail_x)
    )
    out.append(
        Component(
            "plinth_rail_rear", "plinth", base_deck._plane_rail_x_rear() * rail_x_grille
        )
    )
    for j in range(len(base_deck.Y_RAIL_CX)):
        out.append(
            Component(f"plinth_rail_y{j}", "plinth", base_deck._plane_rail_y(j) * rail_y)
        )

    # 2. the four verticals, each stood up by their own module
    for i, wall in enumerate(bay_walls.placed_all(d)):
        out.append(Component(f"{bay_walls.WALLS[i].name}", "carcass", wall))

    # 3. the spine
    out.append(Component("spine_panel", "carcass", spine_panel.place(d=d)))

    # 4. the top cap
    out.append(Component("top_cap", "carcass", d.top_plane * top_cap.build(d)))

    # 5. the four leg ties
    for name, tie in leg_tie.placed():
        out.append(Component(f"leg_tie_{name}", "tie", tie))

    return out


def assembly(comps: list[Component] | None = None, d: Datums = DATUMS) -> Compound:
    """The whole carcass as one labelled assembly tree."""
    comps = components(d) if comps is None else comps
    children: list[Shape] = []
    for c in comps:
        p = c.part
        p.label = c.label
        children.append(p)
    return Compound(label=ASSEMBLY_NAME, children=children)


# ---------------------------------------------------------------- joints


@dataclass(frozen=True)
class Joint:
    """A declared joint between two parts, and where it is allowed to engage.

    ``axis`` / ``lo`` / ``hi`` describe the engagement band: the slab of station
    space where the member enters the receiver. ``axis is None`` means the joint
    is a butt, a bearing face or a bolt -- no material is meant to interpenetrate
    anywhere, so any shared volume at all is a collision.
    """

    a: str
    b: str
    kind: str
    axis: str | None = None
    lo: float = 0.0
    hi: float = 0.0
    note: str = ""

    def key(self) -> frozenset[str]:
        return frozenset((self.a, self.b))


def joints(d: Datums = DATUMS) -> dict[frozenset[str], Joint]:
    """Design intent, read off the five part modules' docstrings.

    Every band derives from ``Datums`` and ``HOUSE_ENGAGE``. Nothing here is a
    literal, so the table follows CARCASS_T and leg_x_inner like everything else.
    """
    js: list[Joint] = []
    wall_names = [w.name for w in bay_walls.WALLS]

    # -- deck houses every vertical, DADO_D into its TOP face ---------------
    deck_lo, deck_hi = d.deck_top - HOUSE_ENGAGE, d.deck_top
    for n in wall_names + ["spine_panel"]:
        js.append(
            Joint("base_deck", n, "housing", "z", deck_lo, deck_hi,
                  "tongue down into the deck's top-face housing")
        )

    # -- top cap houses every vertical, HOUSE_ENGAGE into its UNDERSIDE -----
    top_lo, top_hi = d.top_z[0], d.top_z[0] + HOUSE_ENGAGE
    for n in wall_names + ["spine_panel"]:
        js.append(
            Joint("top_cap", n, "housing", "z", top_lo, top_hi,
                  "tongue up into the cap's underside housing")
        )

    # -- spine houses the two DIVIDERS in its front face -------------------
    spine_lo, spine_hi = d.y_spine, d.y_spine + HOUSE_ENGAGE
    for i in (1, 2):
        js.append(
            Joint("spine_panel", wall_names[i], "housing", "y", spine_lo, spine_hi,
                  "divider's rear tongue into the spine's front-face housing")
        )

    # -- spine BUTTS the two end walls; the tie is a screw, not a tongue ----
    for i in (0, 3):
        js.append(
            Joint("spine_panel", wall_names[i], "butt", None, note=
                  "spine end face lands flat on the end wall, screwed through")
        )

    # -- deck sits ON the plinth; the joint is a counterbored screw ---------
    rails = ["plinth_rail_front", "plinth_rail_rear"] + [
        f"plinth_rail_y{j}" for j in range(len(base_deck.Y_RAIL_CX))
    ]
    for r in rails:
        js.append(Joint("base_deck", r, "bearing", None, note="deck bears on the rail"))

    # -- the two X rails house the four cross rails ------------------------
    py0, py1 = base_deck.PLINTH_Y
    t = d.t
    front_face = py0 + t
    rear_face = py1 - t
    for j in range(len(base_deck.Y_RAIL_CX)):
        js.append(
            Joint("plinth_rail_front", f"plinth_rail_y{j}", "housing", "y",
                  front_face - HOUSE_ENGAGE, front_face,
                  "cross rail bottoms out in the front rail's housing")
        )
        js.append(
            Joint("plinth_rail_rear", f"plinth_rail_y{j}", "housing", "y",
                  rear_face, rear_face + HOUSE_ENGAGE,
                  "cross rail bottoms out in the rear rail's housing")
        )

    # -- leg ties bear on the outer faces of the end walls -----------------
    for name, _ in leg_tie.placements():
        wall = wall_names[0] if name.startswith("left") else wall_names[3]
        js.append(
            Joint(wall, f"leg_tie_{name}", "bearing", None,
                  note="tie pad bears on the end wall's outer face, screwed from inside")
        )

    return {j.key(): j for j in js}


# ---------------------------------------------------------------- interference


@dataclass(frozen=True)
class Overlap:
    a: str
    b: str
    volume: float
    bbox: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    lumps: int
    engaged: float
    verdict: str
    why: str

    def line(self) -> str:
        (x0, x1), (y0, y1), (z0, z1) = self.bbox
        frac = "" if self.engaged <= 0 else f", {100 * self.engaged:.0f}% of the joint"
        return (
            f"{self.verdict:15s} {self.a} <-> {self.b}: {self.volume:,.0f} mm3 "
            f"in {self.lumps} lump(s){frac}\n"
            f"                  x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  "
            f"z {z0:.1f}..{z1:.1f}\n"
            f"                  {self.why}"
        )


def _bboxes_touch(a, b, gap: float = 0.0) -> bool:
    return not (
        a.max.X < b.min.X - gap or b.max.X < a.min.X - gap
        or a.max.Y < b.min.Y - gap or b.max.Y < a.min.Y - gap
        or a.max.Z < b.min.Z - gap or b.max.Z < a.min.Z - gap
    )


def _in_band(bb, axis: str, lo: float, hi: float) -> bool:
    lo_v = getattr(bb.min, axis.upper())
    hi_v = getattr(bb.max, axis.upper())
    return lo_v >= lo - BAND_EPS and hi_v <= hi + BAND_EPS


def _engagement_volume(member: Part, receiver_bb, j: Joint) -> float:
    """What the member would occupy inside an UNCUT receiver, over this joint.

    The receiver's nominal slab is its own bounding box, trimmed to the joint's
    engagement band. Intersecting the member with that slab gives the volume the
    housing has to make room for. Dividing the measured overlap by it says
    whether the housing is short or absent, and does so from the solids rather
    than from anybody's docstring.
    """
    lo = {"x": receiver_bb.min.X, "y": receiver_bb.min.Y, "z": receiver_bb.min.Z}
    hi = {"x": receiver_bb.max.X, "y": receiver_bb.max.Y, "z": receiver_bb.max.Z}
    lo[j.axis], hi[j.axis] = j.lo, j.hi
    size = [hi[a] - lo[a] for a in ("x", "y", "z")]
    if min(size) <= 0:
        return 0.0
    mid = [(hi[a] + lo[a]) / 2 for a in ("x", "y", "z")]
    slab = Location(tuple(mid)) * Box(*size)
    try:
        return (member & slab).volume
    except Exception:
        return 0.0


def interference(
    comps: list[Component] | None = None, d: Datums = DATUMS
) -> list[Overlap]:
    """Every pair of parts that shares more than ``NOISE_VOL`` of space."""
    comps = components(d) if comps is None else comps
    table = joints(d)
    found: list[Overlap] = []

    for ca, cb in combinations(comps, 2):
        if not _bboxes_touch(ca.bbox, cb.bbox):
            continue
        try:
            shared = ca.part & cb.part
        except Exception:                       # empty intersection, on some kernels
            continue
        if shared is None:
            continue
        vol = shared.volume
        if vol <= NOISE_VOL:
            continue

        bb = shared.bounding_box()
        box = ((bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z))
        lumps = len(shared.solids())
        j = table.get(frozenset((ca.label, cb.label)))

        engaged = 0.0
        if j is None:
            verdict, why = (
                "COLLISION",
                "no joint is declared between these two parts. They were never "
                "meant to meet.",
            )
        elif j.axis is None:
            verdict, why = (
                "COLLISION",
                f"declared joint is a {j.kind} ({j.note}); a {j.kind} shares "
                "faces, never volume.",
            )
        elif _in_band(bb, j.axis, j.lo, j.hi):
            # which part is the receiver: the one whose face the band sits on
            recv, memb = (ca, cb) if ca.label == j.a else (cb, ca)
            nominal = _engagement_volume(memb.part, recv.bbox, j)
            engaged = vol / nominal if nominal > NOISE_VOL else 0.0
            if engaged >= 1 - 1e-3:
                verdict, why = (
                    "MISSING HOUSING",
                    f"the member is engaged over 100% of its footprint in the "
                    f"band {j.axis} {j.lo:.1f}..{j.hi:.1f} ({j.note}). "
                    f"{recv.label} cut no housing here at all -- check whether "
                    "it cut one somewhere else.",
                )
            else:
                verdict, why = (
                    "SHORT HOUSING",
                    f"inside the declared engagement band {j.axis} "
                    f"{j.lo:.1f}..{j.hi:.1f} ({j.note}), over "
                    f"{100 * engaged:.0f}% of the joint. {recv.label}'s housing "
                    "stops early; the member is right, the receiver is short.",
                )
        else:
            verdict, why = (
                "COLLISION",
                f"reaches outside the declared engagement band {j.axis} "
                f"{j.lo:.1f}..{j.hi:.1f} ({j.note}), so it is not a housing "
                "that fell short.",
            )

        found.append(Overlap(ca.label, cb.label, vol, box, lumps, engaged, verdict, why))

    found.sort(key=lambda o: -o.volume)
    return found


# ---------------------------------------------------------------- envelope


@dataclass(frozen=True)
class Fit:
    label: str
    have: float
    room: float
    axis: str

    @property
    def slack(self) -> float:
        return self.room - self.have

    def line(self) -> str:
        state = "fits" if self.slack >= 0 else "OVER"
        return (
            f"{self.axis}  {self.label:22s} {self.have:8.1f} into {self.room:8.1f}  "
            f"{self.slack:+8.1f}mm  {state}"
        )


def envelope(comps: list[Component] | None = None, d: Datums = DATUMS) -> list[Fit]:
    """The assembled solid measured against the hole it has to live in.

    Reported twice on X, because the leg ties are deliberately OUTSIDE the leg
    inner faces: they reach across the splay gap to the leg itself. A tie that
    did not cross x=0 would not be a tie. The carcass proper is the number that
    has to clear ``leg_x_inner``.
    """
    comps = components(d) if comps is None else comps
    s = d.s

    def span(sel, axis: str) -> tuple[float, float]:
        lo = min(getattr(c.bbox.min, axis) for c in sel)
        hi = max(getattr(c.bbox.max, axis) for c in sel)
        return lo, hi

    body = [c for c in comps if c.group != "tie"]
    x0, x1 = span(body, "X")
    y0, y1 = span(body, "Y")
    z0, z1 = span(body, "Z")
    tx0, tx1 = span(comps, "X")

    # The carcass footprint is the leg opening -- flush to the leg inner
    # faces by the 2026-09-02 ruling -- and every corner is where a gusset
    # comes down to meet a leg, cut back by the relief in bay_walls.py and
    # top_cap.py. clear_over_relieved assumes exactly that cut, the same
    # assumption those two modules' own build() functions make.
    ceiling = clear_over_relieved((d.x_left, d.x_right), (d.y_front, d.y_rear), s)

    return [
        Fit("carcass + plinth", x1 - x0, s.leg_x_inner, "X"),
        Fit("with leg ties", tx1 - tx0, s.leg_x_inner, "X"),
        Fit("carcass + plinth", y1 - y0, s.leg_y_inner, "Y"),
        Fit("carcass + plinth", z1 - z0, ceiling, "Z"),
    ]


# ---------------------------------------------------------------- checks


def check_assembly(comps: list[Component] | None = None, d: Datums = DATUMS) -> list[str]:
    """Constraints that only exist once the parts are in one place."""
    comps = components(d) if comps is None else comps
    notes: list[str] = []

    for f in envelope(comps, d):
        if f.slack < 0 and f.label != "with leg ties":
            notes.append(
                f"assembled {f.axis} extent {f.have:.1f}mm does not fit "
                f"{f.room:.1f}mm ({-f.slack:.1f}mm over)"
            )

    body = [c for c in comps if c.group != "tie"]
    top = max(c.bbox.max.Z for c in body)
    ceiling = clear_over_relieved((d.x_left, d.x_right), (d.y_front, d.y_rear), d.s)
    reveal = ceiling - top
    if reveal < TOP_GAP_MIN:
        notes.append(
            f"assembled reveal is {reveal:.1f}mm against a {TOP_GAP_MIN:.0f}mm "
            "minimum; the carcass is touching the machine frame"
        )

    floor = min(c.bbox.min.Z for c in body)
    if abs(floor) > BAND_EPS:
        notes.append(f"the assembly does not stand on the floor: lowest z is {floor:.2f}")

    for o in interference(comps, d):
        notes.append(
            f"{o.verdict}: {o.a} / {o.b} share {o.volume:,.0f} mm3. No joint in "
            "this carcass is meant to share any."
        )

    return notes


def export(comp: Compound, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{ASSEMBLY_NAME}.step"
    export_step(comp, p, unit=Unit.MM)
    return p


# ---------------------------------------------------------------- main


def main() -> None:
    d = DATUMS
    comps = components(d)
    asm = assembly(comps, d)

    print(f"{ASSEMBLY_NAME}: {len(comps)} placed solids")
    for c in comps:
        bb = c.bbox
        print(
            f"  {c.group:7s} {c.label:22s} "
            f"x {bb.min.X:7.1f}..{bb.max.X:7.1f}  "
            f"y {bb.min.Y:7.1f}..{bb.max.Y:7.1f}  "
            f"z {bb.min.Z:6.1f}..{bb.max.Z:6.1f}  "
            f"{c.part.volume / 1000:8.1f} cm3"
        )

    bb = asm.bounding_box()
    print(
        f"\nassembled bbox  x {bb.min.X:.1f}..{bb.max.X:.1f}  "
        f"y {bb.min.Y:.1f}..{bb.max.Y:.1f}  z {bb.min.Z:.1f}..{bb.max.Z:.1f}"
        f"   ({bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f})"
    )
    solids = asm.solids()
    print(
        f"                {len(solids)} solids, "
        f"{sum(s.volume for s in solids) / 1000:.1f} cm3 of material"
    )

    print("\nfit under the machine")
    for f in envelope(comps, d):
        print(f"  {f.line()}")
    print(
        f"  reveal above the top cap: {d.top_gap:.1f}mm "
        f"(minimum {TOP_GAP_MIN:.0f}mm)"
    )

    print("\ninterference")
    found = interference(comps, d)
    if not found:
        print(f"  no pair shares more than {NOISE_VOL:.0f} mm3")
    for o in found:
        print(f"  {o.line()}")

    path = export(asm)
    print(f"\nwrote {path}  {path.stat().st_size:,} bytes")

    for name, notes in (
        ("carcass", check_carcass(d)),
        ("assembly", check_assembly(comps, d)),
    ):
        if notes:
            print(f"\n{len(notes)} {name} note(s):")
            for n in notes:
                print(f"  - {n}")
        else:
            print(f"\nno {name} constraint violations")


if __name__ == "__main__":
    main()
