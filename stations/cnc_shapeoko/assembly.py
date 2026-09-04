"""The carcass parts, brought together in station coordinates.

Build order 6. This module owns no geometry. It imports every part module's
builder, places each part with the same datum plane the part's own module uses,
and then asks three questions the individual parts cannot ask about themselves:

    1. does the whole thing close up          -> one STEP, exported
    2. do any two parts occupy the same mm3   -> the interference report
    3. does the assembled envelope fit under the machine
                                              -> the fit report

It also prints the leg-bolt axes. Those are not parts and never appear in a
solid: the joint is the machine's steel, the carcass's birch and a fastener, and
what an assembly report can usefully say about it is where each axis runs. See
``parts/leg_joint.py``.

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
    brain_partition,
    drawers,
    leg_joint,
    mains_backplate,
    mast_base,
    spine_panel,
    stock_rails,
    top_cap,
    trays,
    vfd_mount,
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
    group: str          # carcass | plinth | drawer | tray | steel | reference
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

    # 5. the leg joint adds no solid. It is bolts through the machine's own legs
    # into inserts in the end walls, so what it contributes to the carcass is
    # holes, already cut by bay_walls, and the axes main() prints.

    # 6. the three drawers, panel by panel rather than fused, for the same
    # reason the plinth is enumerated rail by rail: a rabbet between a side and
    # a front is a joint like any other and a fused box would hide it.
    for label, part in drawers.placed_all(d):
        out.append(Component(label, "drawer", part))

    # 7. the fitted tray in drawer 1, generated from the tool list
    out.append(Component(trays.TRAY_LABEL, "tray", trays.place(d=d)))

    # 8. the mast's steel backing plate, under the cap at the mast pad. Not
    # birch, but it lives in the brain band's corner beside two housed panels,
    # which is exactly the kind of neighbour the interference check exists for.
    out.append(Component(mast_base.NAME, "steel", mast_base.place(d=d)))

    # 9. the two stock rack comb rails, seated in the housings the dividers
    # already cut. Front and rear, both on the deck; see the module docstring
    # for why there is no top rail.
    for label, part in stock_rails.placed_all(d):
        out.append(Component(label, "carcass", part))

    # 10. the brain-band sealed/signal partition, its tongue in the housing
    # the spine's rear face already cuts, butting the deck, the cap and the
    # rear door's landing. One opening, the split transit; no hardware holes.
    out.append(
        Component(brain_partition.PART_NAME, "carcass", brain_partition.place(d=d))
    )

    # 11. the VFD's standoff plate on the spine's rear face, standing on the
    # deck, and the drive itself as a reference solid so every later brain-band
    # layout collides with it here rather than in the shop. Not birch, not cut;
    # in the assembly for the same reason the mast plate is.
    out.append(Component(vfd_mount.PART_NAME, "carcass", vfd_mount.place(d=d)))
    out.append(Component(vfd_mount.KEEPOUT_NAME, "reference", vfd_mount.build_keepout(d)))

    # 12. the sealed side's electrical: the mains backplate on the spine's
    # rear face between the crossing rows, its two DIN rails, every device as
    # a reference envelope on its rail, and the extractor's receptacle box on
    # the lungs face of the spine. The rails and the box are steel; the
    # envelopes are air the way the drive's keep-out is.
    for label, group, part in mains_backplate.placed_all(d):
        out.append(Component(label, group, part))

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

    # -- spine houses the brain-band PARTITION in its rear face --------------
    # Half-depth housing, so the band is the partition's own tongue and not
    # HOUSE_ENGAGE. Interrupted at the split transit, where the partition is
    # notched to match; the two are drawn from the same two constants.
    js.append(
        Joint("spine_panel", brain_partition.PART_NAME, "housing", "y",
              d.y_spine + d.t - brain_partition.TONGUE, d.y_spine + d.t,
              "partition's front tongue into the spine's rear-face housing")
    )
    js.append(
        Joint("base_deck", brain_partition.PART_NAME, "butt", None, note=
              "partition stands on the deck's top face; the deck cuts no housing")
    )
    js.append(
        Joint("top_cap", brain_partition.PART_NAME, "butt", None, note=
              "partition's top edge lands on the cap's underside; the cap cuts no housing")
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

    # -- inside each drawer box, and the tray that sits in one -------------
    for a, b, kind, axis, lo, hi, note in drawers.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))
    js.append(
        Joint(
            trays.TRAY_LABEL,
            f"{trays.spec_for(trays.TRAY_V1).name}_bottom",
            "bearing",
            None,
            note="the tray stands on the drawer's bottom panel",
        )
    )

    # -- the stock rails are housed in both dividers and stand on the deck --
    for a, b, kind, axis, lo, hi, note in stock_rails.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the mast backing plate bears on the cap's underside ----------------
    js.append(
        Joint("top_cap", mast_base.NAME, "bearing", None, note=
              "steel plate flat against the cap's underside, bolted through")
    )

    # -- the VFD plate lies flat on the spine and stands on the deck; the
    # drive hangs on the plate. Three faces, no volume.
    js.append(
        Joint("spine_panel", vfd_mount.PART_NAME, "butt", None, note=
              "plate flat on the spine's rear face, screwed through; the spine cuts nothing")
    )
    js.append(
        Joint("base_deck", vfd_mount.PART_NAME, "butt", None, note=
              "plate stands on the deck's top face; the deck cuts no housing")
    )
    js.append(
        Joint(vfd_mount.PART_NAME, vfd_mount.KEEPOUT_NAME, "bearing", None, note=
              "the drive's back hangs flat on the plate's rear face")
    )

    # -- the mains backplate is flat on the spine; its rails, devices and the
    # receptacle box are all faces. Read off the module's own table.
    for a, b, kind, axis, lo, hi, note in mains_backplate.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # The leg joint declares nothing here. It is not a joint between two CARCASS
    # parts: it is a bolt from the machine into one of them, and the machine is
    # not in this assembly. ``leg_joint.check_leg_joint`` and
    # ``bay_walls.check_bay_walls`` own it.

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

    Reported ONCE on X now. It used to be reported twice, because the leg ties
    reached outboard across an assumed splay gap to the leg itself and the
    carcass had to be measured with and without them. Both halves of that are
    gone: the legs are square, and the joint is a bolt into the end wall's own
    outer face, so nothing in this assembly sits outside ``leg_x_inner`` and
    there is no second number to report.
    """
    comps = components(d) if comps is None else comps
    s = d.s

    def span(sel, axis: str) -> tuple[float, float]:
        lo = min(getattr(c.bbox.min, axis) for c in sel)
        hi = max(getattr(c.bbox.max, axis) for c in sel)
        return lo, hi

    x0, x1 = span(comps, "X")
    y0, y1 = span(comps, "Y")
    z0, z1 = span(comps, "Z")

    # The carcass footprint is the leg opening -- flush to the leg inner
    # faces by the 2026-09-02 ruling -- and every corner is where a gusset
    # comes down to meet a leg, cut back by the relief in bay_walls.py and
    # top_cap.py. clear_over_relieved assumes exactly that cut, the same
    # assumption those two modules' own build() functions make.
    ceiling = clear_over_relieved((d.x_left, d.x_right), (d.y_front, d.y_rear), s)

    fits = [
        Fit("carcass + plinth", x1 - x0, s.leg_x_inner, "X"),
        Fit("carcass + plinth", y1 - y0, s.leg_y_inner, "Y"),
        Fit("carcass + plinth", z1 - z0, ceiling, "Z"),
    ]

    # Each drawer against the two things that size it: the opening less the
    # slide maker's side clearance, and the slide's own length. Both rooms are
    # the vendor's numbers, not the cabinet's, which is the point of reporting
    # them here rather than inside the part.
    room_w = s.bay_hands_w - 2 * s.drawer_slide_side_clear
    for spec in drawers.DRAWERS:
        w, dep, _h = drawers.box_size(spec, d)
        fits.append(Fit(f"{spec.name} width", w, room_w, "X"))
        fits.append(Fit(f"{spec.name} depth", dep, bay_walls.SLIDE_LEN, "Y"))

    # and the stack against the bay it slides into, once: all three boxes are
    # the same depth, and this is the row that moves if the spine moves.
    fits.append(
        Fit(
            "drawers in bay",
            bay_walls.SLIDE_LEN + bay_walls.SLIDE_FRONT_INSET,
            d.front_bay_d,
            "Y",
        )
    )

    tray_spec = trays.spec_for(trays.TRAY_V1)
    plan = trays.plan(trays.TRAY_V1, d)
    iw, idep, _ih = drawers.interior(tray_spec, d)
    fits.append(Fit(f"{trays.TRAY_LABEL} width", plan.w, iw, "X"))
    fits.append(Fit(f"{trays.TRAY_LABEL} depth", plan.d, idep, "Y"))

    return fits


# ---------------------------------------------------------------- checks


def check_assembly(comps: list[Component] | None = None, d: Datums = DATUMS) -> list[str]:
    """Constraints that only exist once the parts are in one place."""
    comps = components(d) if comps is None else comps
    notes: list[str] = []

    for f in envelope(comps, d):
        if f.slack < 0:
            notes.append(
                f"assembled {f.axis} extent {f.have:.1f}mm does not fit "
                f"{f.room:.1f}mm ({-f.slack:.1f}mm over)"
            )

    top = max(c.bbox.max.Z for c in comps)
    ceiling = clear_over_relieved((d.x_left, d.x_right), (d.y_front, d.y_rear), d.s)
    reveal = ceiling - top
    if reveal < TOP_GAP_MIN:
        notes.append(
            f"assembled reveal is {reveal:.1f}mm against a {TOP_GAP_MIN:.0f}mm "
            "minimum; the carcass is touching the machine frame"
        )

    floor = min(c.bbox.min.Z for c in comps)
    if abs(floor) > BAND_EPS:
        notes.append(f"the assembly does not stand on the floor: lowest z is {floor:.2f}")

    for o in interference(comps, d):
        notes.append(
            f"{o.verdict}: {o.a} / {o.b} share {o.volume:,.0f} mm3. No joint in "
            "this carcass is meant to share any."
        )

    # The drive's standoff is air by ruling: nothing may stand between its
    # vented face and the louvre. Checked here because only the assembly can
    # see every part that might.
    for c in standoff_intruders(comps, d):
        notes.append(
            f"{c.label} stands in the VFD's standoff slab, between the vented "
            f"face and the louvre; that {d.s.vfd_panel_standoff:.0f}mm is the "
            "only clearance the drive gets inside the box"
        )

    return notes


def standoff_intruders(
    comps: list[Component] | None = None, d: Datums = DATUMS
) -> list[Component]:
    """Every part sharing more than ``NOISE_VOL`` with the VFD's standoff
    slab, the air between the drive's vented face and the end wall's louvre."""
    comps = components(d) if comps is None else comps
    slab = vfd_mount.standoff_slab(d)
    sb = slab.bounding_box()
    hits: list[Component] = []
    for c in comps:
        if not _bboxes_touch(c.bbox, sb):
            continue
        try:
            shared = c.part & slab
        except Exception:
            continue
        if shared is not None and shared.volume > NOISE_VOL:
            hits.append(c)
    return hits


def export(comp: Compound, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{ASSEMBLY_NAME}.step"
    export_step(comp, p, unit=Unit.MM)
    return p


def export_in_machine(
    comps: list[Component] | None = None,
    d: Datums = DATUMS,
    out_dir: Path | None = None,
) -> Path:
    """One STEP carrying the carcass AND the machine's gussets.

    Both are already modelled on the same datum, so the honest way to see the
    fit is one file that opens with everything where it belongs, rather than
    two files and a positioning job done by hand in Fusion. A hand-positioned
    import is a second chance to be wrong about the very relationship the file
    exists to show.
    """
    from stations.cnc_shapeoko.machine import gussets

    comps = comps if comps is not None else components(d)
    parts: list[Shape] = [c.part for c in comps]
    for g, solid in gussets(d):
        parts.append(solid)

    out_dir = out_dir or EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "carcass_in_machine.step"
    export_step(Compound(children=parts), p, unit=Unit.MM)
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
    relieved = clear_over_relieved(
        (d.x_left, d.x_right), (d.y_front, d.y_rear), d.s
    ) - d.carcass_h
    print(
        f"  reveal above the top cap: Datums.top_gap {d.top_gap:.1f}mm under "
        f"the UNRELIEVED ceiling, clear_over_relieved {relieved:.1f}mm once the "
        f"corner reliefs are cut (minimum {TOP_GAP_MIN:.0f}mm; check_carcass "
        "uses the relieved one)"
    )

    print("\nhands bay: three drawers and the D1 tray")
    for spec in drawers.DRAWERS:
        w, dep, h = drawers.box_size(spec, d)
        floor, clear_h = drawers.opening(spec, d)
        iw, idep, ih = drawers.interior(spec, d)
        print(
            f"  {spec.number} {spec.callout:<12} {w:6.1f} x {dep:6.1f} x "
            f"{h:6.1f} outside   inside {iw:6.1f} x {idep:6.1f} x {ih:5.1f}   "
            f"floor z {d.deck_top + floor:6.1f}   "
            f"{drawers.side_clearance(spec, d):.1f}mm per side on a "
            f"{bay_walls.SLIDE_LEN:.0f}mm slide"
        )
    plan = trays.plan(trays.TRAY_V1, d)
    miss = trays.skipped(trays.TRAY_V1)
    print(
        f"  {trays.TRAY_LABEL}: {plan.w:.1f} x {plan.d:.1f} x {plan.h:.1f}, "
        f"{len(plan.sockets)} sockets from the tool list, "
        f"{len(miss)} {trays.TRAY_V1} row(s) still MEASURE, "
        f"{len(trays.tiles(plan))} print tiles"
    )

    print("\nstock bay: two comb rails on the deck")
    print(
        f"  {len(stock_rails.RAILS)} x {stock_rails.rail_length(d):.1f} x "
        f"{stock_rails.RAIL_H:.0f} x {stock_rails.RAIL_T:.0f}, "
        f"{stock_rails.slot_count(d)} slots {stock_rails.SLOT_W:.1f} wide at "
        f"{stock_rails.pitch(d):.1f} pitch, tooth {stock_rails.tooth_w(d):.1f}; "
        f"a blank stands at z {stock_rails.blank_stand_z(d):.1f}"
    )

    print("\nbrain band: the sealed/signal partition")
    pw, ph = brain_partition.blank_size(d)
    tz0, tz1 = brain_partition.transit_z(d)
    print(
        f"  {brain_partition.PART_NAME}: {pw:.1f} x {ph:.1f} x {d.t:.0f} at "
        f"x {d.brain_split_x:.1f}, tongue {brain_partition.TONGUE:.0f} into the spine, "
        f"rear edge at y {d.y_rear - brain_partition.DOOR_LANDING:.1f} for the door; "
        f"transit z {tz0:.0f}..{tz1:.0f}, {brain_partition.TRANSIT_D:.0f} deep, the only opening"
    )

    print("\nbrain band: the drive and its plate")
    pw, ph = vfd_mount.plate_size(d)
    kb = vfd_mount.build_keepout(d).bounding_box()
    print(
        f"  {vfd_mount.PART_NAME}: {pw:.1f} x {ph:.1f} x {vfd_mount.PLATE_T:.0f} on the "
        f"spine's rear face at x {vfd_mount.plate_x(d)[0]:.1f}, standing on the deck; "
        f"2 x {vfd_mount.INSERT_PILOT_D:.3f} insert pilots at {vfd_mount.MOUNT_PITCH:.0f} pitch"
    )
    print(
        f"  {vfd_mount.KEEPOUT_NAME}: x {kb.min.X:.1f}..{kb.max.X:.1f}  "
        f"y {kb.min.Y:.1f}..{kb.max.Y:.1f}  z {kb.min.Z:.1f}..{kb.max.Z:.1f}; vented face "
        f"{vfd_mount.standoff(d):.1f} off the end wall's inner face, "
        f"{len(standoff_intruders(comps, d))} part(s) in the standoff slab"
    )

    print("\nbrain band: the sealed side's electrical")
    pw, ph = mains_backplate.plate_size(d)
    print(
        f"  {mains_backplate.PART_NAME}: {pw:.1f} x {ph:.1f} x {mains_backplate.PLATE_T:.0f} on the "
        f"spine's rear face at x {mains_backplate.plate_x(d)[0]:.1f}, between the crossing rows; "
        f"{len(mains_backplate.RAILS)} rails {mains_backplate.rail_length(d):.0f} long, "
        f"{len(mains_backplate.envelopes(d))} device envelopes; contactor "
        f"{mains_backplate.contactor_to_transit(d):.0f}mm from the transit gap "
        f"(limit {mains_backplate.CONTACTOR_TRANSIT_MAX:.0f}); PE_SWITCHED = {mains_backplate.PE_SWITCHED}"
    )
    rx, ry, rz = mains_backplate.receptacle_centre(d)
    print(
        f"  {mains_backplate.RECEPTACLE_NAME}: {mains_backplate.RECEPTACLE} at "
        f"({rx:.1f}, {ry:.1f}, {rz:.1f}) on the lungs face of the spine, on the EXTRACTOR MAINS axis"
    )

    print("\nleg joint: bolt axes, station coordinates")
    bs = leg_joint.bolts(d)
    length = leg_joint.bolt_length()
    st = leg_joint.floor_state(d)
    print(
        f"  {len(bs)} x {leg_joint.BOLT_THREAD} through the legs' own "
        f"{d.s.leg_holes.hole_d:.1f}mm holes into {leg_joint.INSERT_PART}"
    )
    print(
        f"  plinth {'ON THE FLOOR' if st.on_floor else 'OFF THE FLOOR, the carcass HANGS'}"
        f"; rows {st.lowest:.0f}..{st.highest:.0f} against the end wall's usable "
        f"band {st.band[0]:.0f}..{st.band[1]:.0f}"
    )
    for b in bs:
        hx, hy, hz = b.head_face()
        tx, ty, tz = b.tip(length)
        print(
            f"  {b.label:<20} {bay_walls.WALLS[b.wall].name:<10} "
            f"head ({hx:8.2f}, {hy:7.1f}, {hz:6.1f})  ->  "
            f"tip ({tx:8.2f}, {ty:7.1f}, {tz:6.1f})   "
            f"{'+X' if b.inward > 0 else '-X'}"
        )

    mx, my, mz = d.mast_base
    print("\nmast base, for Fusion (J06)")
    print(
        f"  pad centre ({mx:.1f}, {my:.1f}, {mz:.1f}) on the cap's top face, "
        f"{top_cap.MAST_SIDE} rear, 4 x M{top_cap.MAST_BOLT_D:.0f} on a "
        f"{top_cap.MAST_BOLT_PITCH:.0f}mm square; "
        f"{mast_base.MATERIAL} plate {mast_base.PLATE:.0f} x {mast_base.PLATE:.0f} x "
        f"{mast_base.PLATE_T:.0f} under it"
    )

    print("\ninterference")
    found = interference(comps, d)
    if not found:
        print(f"  no pair shares more than {NOISE_VOL:.0f} mm3")
    for o in found:
        print(f"  {o.line()}")

    path = export(asm)
    print(f"\nwrote {path}  {path.stat().st_size:,} bytes")

    in_machine = export_in_machine(comps, d)
    print(f"wrote {in_machine}  {in_machine.stat().st_size:,} bytes"
          "   (carcass + the machine's gussets, one datum, for Fusion)")

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
