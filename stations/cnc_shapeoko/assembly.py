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
    callouts,
    console_plate,
    drawers,
    exhaust_plenum,
    leg_joint,
    lungs_carriage,
    lungs_door,
    mains_backplate,
    mast_base,
    rear_door,
    signal_mounts,
    spine_panel,
    stiles,
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
    "BIRCH_GROUPS",
    "birch_components",
    "acrylic_components",
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
    group: str          # carcass | plinth | drawer | carriage | tray | steel | reference
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

    # 2b. the four stiles (2026-09-04, Kerf): fixed birch behind each leg's
    # flange band, tenoned through the deck and the cap; and the left slide's
    # spacer block on the left end wall's lungs face, ply by ply
    for label, group, part in stiles.placed_all(d):
        out.append(Component(label, group, part))
    for label, group, part in bay_walls.spacer_placed(d):
        out.append(Component(label, group, part))

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

    # 7. the fitted tray in drawer 1, generated from the tool list: two
    # tiles since 2026-09-11, the bore grid in front and the rest behind
    for label, part in trays.placed_all(d):
        out.append(Component(label, "tray", part))

    # 8. the mast's steel backing plate, under the cap at the mast pad. Not
    # birch, but it lives in the brain band's corner beside two housed panels,
    # which is exactly the kind of neighbour the interference check exists for.
    out.append(Component(mast_base.NAME, "steel", mast_base.place(d=d)))

    # 9. the stock comb, hanging from the cap's underside housing and butting
    # both dividers, and one HALF blank as a reference solid standing in its
    # deck groove and through the comb's slot, so both cuts are checked as
    # housings. Ruling 11, 2026-09-03: no bottom rail.
    for label, group, part in stock_rails.placed_all(d):
        out.append(Component(label, group, part))

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

    # 13. the lungs carriage in its CLOSED position: four panels of the tray,
    # the CT 15 as a reference solid on the platform, and the pressure
    # sensor's body on the lip. The tray is what the receptacle box, the
    # plenum and the lungs door are finally compared against as a solid.
    for label, group, part in lungs_carriage.placed_all(d):
        out.append(Component(label, group, part))

    # 14. the console (C12): the plate flush in the right end wall, the cheek
    # and rib that wall its chase off from the narrowed drawers, the clear
    # reveal over the chase's front, the three panes in their pockets, and two
    # reference solids -- the chase air the drawers are checked against and
    # the E-stop module's allocation inside it.
    for label, group, part in console_plate.placed_all(d):
        out.append(Component(label, group, part))

    # 15. the rear brain door (C07), CLOSED: the door itself in the band's
    # last t, the clear pane in its inside-face rabbet, the interlock switch
    # on the door and its striker on the left end wall, the two lamp bodies
    # standing out through their pockets, and the two folded stays. The open
    # door is not a component; ``rear_door.door_open`` answers that question
    # in the part's own check.
    for label, group, part in rear_door.placed_all(d):
        out.append(Component(label, group, part))

    # 16. the lungs door (C09), CLOSED: the door flush in the bay's front, the
    # lay-up on its inside face as a reference slab the closed carriage is
    # measured against, the strike plate on the door and the catch body on
    # the divider. The knuckle is not a component: it stands proud of the
    # front plane by design and ``lungs_door`` checks it against the leg
    # itself. The open door is ``lungs_door.door_open``.
    for label, group, part in lungs_door.placed_all(d):
        out.append(Component(label, group, part))

    # 17. the signal side (C13): the subplate on the spine's rear face right
    # of the partition, the PC's cradle (shelf, two cheeks, clear lip) and
    # the PC as a reference solid, the short DIN rail as a top-hat profile
    # with the ONE printed part hooked on it and the board as a
    # reference (the sensing layer is PARKED to 2027-01-05; the USB hub was
    # struck 2026-09-09, the P350 has the ports). The motion controller appears only once params carries its
    # envelope; until then its seat is reserved and the check says so.
    for label, group, part in signal_mounts.placed_all(d):
        out.append(Component(label, group, part))

    # 19. the exhaust plenum (C08): the baffled birch box across the rear of
    # the lungs bay, its lay-up on the back wall and both baffles as reference
    # slabs, and the hose corridor as the reference air that sets its top. The
    # bay is the plenum's first chamber, so the box meets the unit nowhere;
    # what it has to clear is the carriage, the receptacle box and the hose.
    for label, group, part in exhaust_plenum.placed_all(d):
        out.append(Component(label, group, part))

    return out


BIRCH_GROUPS = ("carcass", "plinth", "drawer", "carriage")
"""The groups whose every member is a CARCASS_T birch sheet part. Steel, foam,
acrylic, printed and reference solids carry their own group names, so the
birch nest (tools/nest.py, C18) reads its part list off this tuple and never
off a second list of names."""


def birch_components(comps: list[Component] | None = None, d: Datums = DATUMS) -> list[Component]:
    """Every placed solid the birch nest has to find a sheet for."""
    comps = components(d) if comps is None else comps
    return [c for c in comps if c.group in BIRCH_GROUPS]


def acrylic_components(comps: list[Component] | None = None, d: Datums = DATUMS) -> list[Component]:
    """Every placed solid the Universal cuts: the ``acrylic`` group."""
    comps = components(d) if comps is None else comps
    return [c for c in comps if c.group == "acrylic"]


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

    # -- the stiles through the deck and the cap, against the end walls -----
    for a, b, kind, axis, lo, hi, note in stiles.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the spacer's plies: on the deck, on the wall, on each other --------
    plies = [f"{bay_walls.SPACER_STEM}_{i}" for i in range(d.s.lungs_spacer_plies)]
    js.append(Joint(wall_names[0], plies[0], "bearing", None, note="first ply glued to the wall's lungs face, screwed from outside"))
    for a, b in zip(plies, plies[1:]):
        js.append(Joint(a, b, "bearing", None, note="plies laminated face to face"))
    for p in plies:
        js.append(Joint("base_deck", p, "butt", None, note="ply stands on the deck"))

    # -- inside each drawer box, and the tray that sits in one -------------
    for a, b, kind, axis, lo, hi, note in drawers.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))
    for p in trays.plan_all(trays.TRAY_V1, d):
        js.append(
            Joint(
                p.label,
                f"{trays.spec_for(trays.TRAY_V1).name}_bottom",
                "bearing",
                None,
                note="the tile stands on the drawer's bottom panel",
            )
        )

    # -- the stock comb is housed in the cap and butts both dividers; the
    # reference blank is housed in the deck's groove and the comb's slot ----
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

    # -- inside the lungs carriage: two housings per cheek, the rest faces.
    for a, b, kind, axis, lo, hi, note in lungs_carriage.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the console: plate and panes housed, everything else in the chase
    # meets on faces. The keep-out has NO joint with any drawer on purpose:
    # a drawer in the chase is a collision.
    for a, b, kind, axis, lo, hi, note in console_plate.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the rear door: its ends on the end walls, the partition's edge on
    # its inside face, the pane housed in its rabbet, everything on it bears.
    for a, b, kind, axis, lo, hi, note in rear_door.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the lungs door: its lay-up and the strike bear on it, the catch
    # bears on the divider; its edges meet nothing but the knuckle gap and
    # the reveals.
    for a, b, kind, axis, lo, hi, note in lungs_door.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the signal side: the subplate on the spine, the cradle on the
    # subplate, the carrier on its rail; every joint a face.
    for a, b, kind, axis, lo, hi, note in signal_mounts.joint_table(d):
        js.append(Joint(a, b, kind, axis, lo, hi, note))

    # -- the exhaust plenum: the floor, the top and both walls housed in the
    # side walls' rabbets, the baffles housed in the plates' dados, the lay-up
    # bearing on its faces, and the box screwed to the bay on faces.
    for a, b, kind, axis, lo, hi, note in exhaust_plenum.joint_table(d):
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
        """Room less have, snapped to zero inside ``BAND_EPS``. An OCC bounding
        box is a tolerance box, not the solid's edge: the carve on an outer
        face (C17) grew the carcass's by 1e-7 and a fit that is exactly 0.0
        by construction read as 0.0mm over. The floor check reads the same
        box through the same epsilon."""
        s = self.room - self.have
        return 0.0 if abs(s) < BAND_EPS else s

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
    for spec in drawers.DRAWERS:
        w, dep, _h = drawers.box_size(spec, d)
        # a narrowed box's room is the bay less the console's keep-out
        room_w = s.bay_hands_w - drawers.narrowing(spec, d) - 2 * s.drawer_slide_side_clear
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
    plans = trays.plan_all(trays.TRAY_V1, d)
    iw, idep, _ih = drawers.interior(tray_spec, d)
    for plan in plans:
        fits.append(Fit(f"{plan.label} width", plan.w, iw, "X"))
    fits.append(Fit("tray_d1 tiles depth", sum(p.d for p in plans), idep, "Y"))

    # The lungs carriage against the bay less its lining and slides, and the
    # unit against the platform it stands on.
    s2 = d.s
    fits.append(
        Fit(
            "lungs carriage width",
            lungs_carriage.carriage_width(d),
            s2.bay_lungs_w - 2 * (s2.lungs_lining_t + s2.lungs_slide_t),
            "X",
        )
    )
    fits.append(
        Fit(
            f"{lungs_carriage.CT15_NAME} on platform",
            s2.extractor_env[0],
            lungs_carriage.platform_size(d)[1],
            "Y",
        )
    )

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
    """One STEP carrying the carcass AND the machine's legs and gussets.

    Both are already modelled on the same datum, so the honest way to see the
    fit is one file that opens with everything where it belongs, rather than
    two files and a positioning job done by hand in Fusion. A hand-positioned
    import is a second chance to be wrong about the very relationship the file
    exists to show.
    """
    from stations.cnc_shapeoko.machine import gussets, leg_envelopes

    comps = comps if comps is not None else components(d)
    parts: list[Shape] = [c.part for c in comps]
    for g, solid in gussets(d):
        parts.append(solid)
    # The legs are floor-to-table L-sections. Without them the gussets float in
    # Fusion and the file appears to say the leg has no flange below the band.
    for _, solid in leg_envelopes(d):
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
        nar = drawers.narrowing(spec, d)
        print(
            f"  {spec.number} {spec.callout:<12} {w:6.1f} x {dep:6.1f} x "
            f"{h:6.1f} outside   inside {iw:6.1f} x {idep:6.1f} x {ih:5.1f}   "
            f"floor z {d.deck_top + floor:6.1f}   "
            f"{drawers.side_clearance(spec, d):.1f}mm per side on a "
            f"{bay_walls.SLIDE_LEN:.0f}mm slide"
            + (f"   NARROWED by {nar:.1f} for the console, right slide on the cheek" if nar else "")
        )
    miss = trays.skipped(trays.TRAY_V1)
    for plan in trays.plan_all(trays.TRAY_V1, d):
        print(
            f"  {plan.label}: {plan.w:.1f} x {plan.d:.1f} x {plan.h:.1f} foam, "
            f"{len(plan.pockets)} pockets ({plan.bores} bores, {plan.filled} filled) from the tool list"
        )
    print(f"  {len(miss)} {trays.TRAY_V1} row(s) still MEASURE")

    print("\nstock bay: one comb under the cap, grooves in the deck")
    print(
        f"  comb {stock_rails.rail_length(d):.1f} x {stock_rails.blank_h():.0f} x "
        f"{stock_rails.RAIL_T:.0f} ({stock_rails.RAIL_H:.0f} showing), "
        f"{stock_rails.slot_count(d)} slots {stock_rails.SLOT_W:.1f} wide, "
        f"{stock_rails.slot_depth(d):.1f} deep at {stock_rails.pitch(d):.1f} pitch, "
        f"tooth {stock_rails.tooth_w(d):.1f}; {stock_rails.slot_count(d)} deck grooves "
        f"{stock_rails.GROOVE_D:.0f} deep; a blank's top at z "
        f"{stock_rails.blank_top_z(d):.1f}, {stock_rails.comb_engage(d):.1f} into the comb"
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

    print("\nlungs bay: the carriage and what rides on it")
    cx0, cy0, cz0 = lungs_carriage.carriage_origin(d)
    cw = lungs_carriage.carriage_width(d)
    (ex0, ex1), (ey0, ey1), (ez0, ez1) = lungs_carriage.ct15_station(d)
    print(
        f"  {lungs_carriage.PART_NAME}: {cw:.1f} x {bay_walls.SLIDE_LEN:.0f} x "
        f"{lungs_carriage.CHEEK_H:.0f} at x {cx0:.1f}, y {cy0:.0f}, on the deck; "
        f"platform top {lungs_carriage.PLATFORM_TOP:.0f} above it, lip {lungs_carriage.LIP_H:.0f} higher; "
        f"travel {lungs_carriage.SLIDE_TRAVEL:.0f} toward the operator"
    )
    print(
        f"  {lungs_carriage.CT15_NAME}: x {ex0:.1f}..{ex1:.1f}  y {ey0:.1f}..{ey1:.1f}  "
        f"z {ez0:.1f}..{ez1:.1f} directly on the platform; "
        f"{d.top_z[0] - ez1:.0f}mm under the cap; "
        f"{lungs_carriage.DP_NAME} on the lip's rear face, 2 x o{lungs_carriage.DP_HOLE_D} "
        f"at {lungs_carriage.DP_HOLE_PITCH:.0f} pitch"
    )

    print("\nconsole: the plate in the right end wall, and its chase")
    (cy0, cy1), (cz0, cz1) = console_plate.console_band(d)
    pw, ph = console_plate.plate_size(d)
    kx0, kx1 = console_plate.chase_x(d)
    print(
        f"  {console_plate.PART_NAME}: {pw:.0f} x {ph:.0f} x {console_plate.PLATE_T:.0f} flush in the right end "
        f"wall, band y {cy0:.0f}..{cy1:.0f} z {cz0:.0f}..{cz1:.0f}; {len(console_plate.DEVICES)} "
        f"devices, chase {console_plate.CHASE:.0f} set by {console_plate.CHASE_DRIVER.label} "
        f"({console_plate.CHASE_DRIVER.behind[2]:.0f} + {console_plate.CHASE_MARGIN:.0f})"
    )
    print(
        f"  {console_plate.KEEPOUT_NAME}: x {kx0:.1f}..{kx1:.1f}  y {cy0:.0f}..{cy1:.0f}  "
        f"z {cz0:.0f}..{cz1:.0f} (reference)"
    )
    worst = min(console_plate.leg_bolt_clearance(d), key=lambda t: t[1])
    print(
        f"  nearest leg bolt axis: {worst[0]} at {worst[1]:.1f}mm "
        f"(land {console_plate.LEG_LAND:.0f}); keep-out {console_plate.CONSOLE_KEEPOUT:.0f}, "
        f"drawers narrowed by DRAWER_GIVE {console_plate.DRAWER_GIVE:.1f}: "
        + ", ".join(
            f"{sp.name} -> {drawers.box_size(sp, d)[0]:.1f} outside, {drawers.interior(sp, d)[0]:.1f} inside"
            for sp in drawers.DRAWERS if drawers.narrowing(sp, d)
        )
    )

    print("\nrear door: the drop-down shelf, closed and open")
    dw, dh = rear_door.door_size(d)
    ob = rear_door.door_open(d).bounding_box()
    ax = rear_door.hinge_axis(d)
    (wx0, wx1), (wy0, wy1) = rear_door.window_local(d)
    pw, ph = rear_door.pane_size(d)
    print(
        f"  {rear_door.PART_NAME}: {dw:.1f} x {dh:.1f} x {d.t:.0f} between the end walls, "
        f"bay {d.bay_h:.0f} less HINGE_CLEAR {rear_door.HINGE_CLEAR:.0f}; hinge axis y "
        f"{ax.position.Y:.1f} z {ax.position.Z:.1f}; open it lies y {ob.min.Y:.0f}..{ob.max.Y:.0f} "
        f"z {ob.min.Z:.0f}..{ob.max.Z:.0f}; {len(rear_door.cuts(d))} cuts, split at door x "
        f"{rear_door.split_local(d):.1f}"
    )
    print(
        f"  {rear_door.REVEAL_NAME}: {pw:.1f} x {ph:.1f} x {rear_door.PT:.0f} "
        f"{rear_door.MATERIAL_REVEAL} over door x {wx0:.0f}..{wx1:.0f} y {wy0:.0f}..{wy1:.0f}; "
        f"{rear_door.SWITCH_ENV_NAME} axis y {rear_door.switch_axis(d)[0]:.1f} "
        f"z {rear_door.switch_axis(d)[1]:.1f} into the left end wall"
    )

    print("\nlungs door: flush in the bay's front, hinged on the end wall's edge")
    lw, lh = lungs_door.door_size(d)
    lax = lungs_door.hinge_axis(d)
    (kx0, kx1), (ky0, ky1), (kz0, kz1) = lungs_door.catch_station(d)
    print(
        f"  {lungs_door.PART_NAME}: {lw:.1f} x {lh:.1f} x {d.t:.0f} in the {d.s.bay_lungs_w:.0f} bay, "
        f"HINGE_GAP {lungs_door.HINGE_GAP:.0f} + SIDE_REVEAL {lungs_door.SIDE_REVEAL:.0f}; pin at "
        f"x {lax.position.X:.1f} y {lax.position.Y:.1f}, vertical; pull {lungs_door.PULL_L:.0f} x "
        f"{lungs_door.PULL_H:.0f} at door ({lungs_door.pull_local(d)[0]:.0f}, {lungs_door.pull_local(d)[1]:.0f})"
    )
    print(
        f"  {lungs_door.LINING_NAME}: {lungs_door.lining_size(d)[0]:.0f} x {lungs_door.lining_size(d)[1]:.0f} x "
        f"{lungs_door.lining_t(d):.0f} on the inside face, y {d.t:.0f}..{d.t + lungs_door.lining_t(d):.0f}; "
        f"the tray closes at y {lungs_carriage.carriage_origin(d)[1]:.0f}; "
        f"{lungs_door.CATCH_NAME} x {kx0:.0f}..{kx1:.0f} y {ky0:.0f}..{ky1:.0f} z {kz0:.0f}..{kz1:.0f} on the divider"
    )

    print("\nexhaust plenum: the lined bay is the chamber; it breathes out through an end-wall capsule (RT1)")
    (ex0, ex1), (ez0, ez1) = exhaust_plenum.exit_station(d)
    worst = min(a for _n, a in exhaust_plenum.free_areas(d))
    print(
        f"  {exhaust_plenum.PART_NAME}: no box, no birch; tightest section {worst / 100:.0f} cm2 "
        f"against {exhaust_plenum.section_req() / 100:.0f} required"
    )
    print(
        f"  exit: {ex1 - ex0:.0f} x {ez1 - ez0:.0f} capsule through {bay_walls.WALLS[0].name} at "
        f"y {ex0:.0f}..{ex1:.0f} z {ez0:.0f}..{ez1:.0f}, {(ez0 + ez1) / 2 - d.deck_top:.0f} over the deck"
    )

    print("\ncallouts: V-carved through the paint on a second fixture (C17); each rides in its part")
    carved = [
        (rear_door.PART_NAME, rear_door.callouts_local(d), rear_door.register(d)),
        (lungs_door.PART_NAME, lungs_door.callouts_local(d), lungs_door.register(d)),
        (stock_rails.LABEL, stock_rails.callouts_local(d), stock_rails.register(d)),
        (console_plate.PART_NAME, console_plate.callouts_local(d), console_plate.register(d)),
    ] + [
        (f"{sp.name}_front", [drawers.callout_for(sp, d)], drawers.register_for(sp, d))
        for sp in drawers.DRAWERS
    ]
    for name, words, reg in carved:
        for line in callouts.describe(words, reg):
            print(f"  {name}: {line}")

    print("\nsignal side: the subplate, the cradle, the rail and the one printed part")
    sw, sh = signal_mounts.plate_size(d)
    (qx0, qx1), (qy0, qy1), (qz0, qz1) = signal_mounts.pc_station(d)
    (kx0, kx1), (ky0, ky1), (kz0, kz1) = signal_mounts.controller_seat(d)
    cs = signal_mounts.carrier_print_size()
    print(
        f"  {signal_mounts.PART_NAME}: {sw:.0f} x {sh:.0f} x {signal_mounts.PLATE_T:.0f} on the spine's rear "
        f"face at x {signal_mounts.plate_x(d)[0]:.1f}, between the crossing rows; cradle at plate-local x "
        f"{signal_mounts.cradle_x_local(d):.0f} (derived from the reveal), {signal_mounts.LIP_MATERIAL} lip"
    )
    print(
        f"  {signal_mounts.PC_NAME}: {signal_mounts.PC_ENV[0]:.0f} x {signal_mounts.PC_ENV[1]:.0f} x "
        f"{signal_mounts.PC_ENV[2]:.0f} at x {qx0:.1f}..{qx1:.1f} y {qy0:.1f}..{qy1:.1f} z {qz0:.1f}..{qz1:.1f}; "
        f"in the reveal window: {signal_mounts.pc_in_window(d)}; "
        f"{signal_mounts.CARRIER_NAME} prints {cs[0]:.0f} x {cs[1]:.0f} x {cs[2]:.1f}; "
        f"controller seat {kx1 - kx0:.0f} x {kz1 - kz0:.0f} x {ky1 - ky0:.0f}, env = {signal_mounts.CONTROLLER_ENV}; "
        f"exhaust slots over the signal side: {len(signal_mounts.vent_slots_over_signal(d))}"
    )

    print("\nstiles: the flange band as a fixed birch stile, four corners")
    sw, sh = stiles.blank_size(d)
    print(
        f"  four blanks {sw:.2f} x {sh:.0f} x {d.t:.0f}, tenon {stiles.TENON:.0f} through deck and cap; "
        f"openings lungs {d.lungs_opening_x[1] - d.lungs_opening_x[0]:.2f}, hands "
        f"{d.hands_opening_x[1] - d.hands_opening_x[0]:.2f}, rear {d.rear_opening_x[1] - d.rear_opening_x[0]:.2f}; "
        f"left slide spacer {d.s.lungs_spacer:.0f} ({d.s.lungs_spacer_plies} plies)"
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
          "   (carcass + the machine's legs and gussets, one datum, for Fusion)")

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
