"""Lungs carriage: the pull-out tray the CT 15 rides on, and what rides with it.

WHAT THIS PART IS
=================

Four panels of birch and three kinds of air.

``lungs_carriage_*``  A shallow tray on the Accuride 3832 slides whose cabinet
                      members ``bay_walls`` already drills for on both faces of
                      the lungs bay. Two CHEEKS carry the slides' drawer
                      members on their outer faces and house everything else on
                      their inner faces; a PLATFORM the unit stands on runs in
                      a dado along each cheek; a raised LIP at the rear, housed
                      in both cheeks, is what the unit is pulled against when
                      the tray is yanked out for a bag change and what carries
                      the pressure sensor.

``ct15_env``          The extractor, ``EXTRACTORS["CT15"]`` calipered, as a
                      reference solid on the platform. Not birch, not cut: in
                      the assembly so the hose, the exhaust plenum (C08), the
                      lungs door (C09) and the receptacle box all collide with
                      the unit honestly instead of with a number in a docstring.


``dp_sensor_pad``     The differential-pressure sensor's body on its pad on the
                      lip's rear face, as a reference solid over the two holes
                      the lip cuts for it. The tap itself is J13's; this part
                      gives it somewhere to land and a way through the lip.


WHY IT IS A TRAY AND NOT A BOARD
================================

A side-mount slide is screwed to a vertical face. A bare platform has no
vertical face, so the first thing this part needs is two cheeks, and once the
cheeks exist the platform is a member housed between them rather than a board
with hardware hung off its edges. The cheeks then run ``LIP_H`` above the
platform, which is what lets the lip be HOUSED in them at the rear instead of
standing on the platform held by screws through end grain: a lip that gets
pulled against every time the tray is opened wants a dado on both ends, not a
screw. The stack-up ``bay_walls.check_bay_walls`` measures (slide member,
unit, service gap) is exactly this tray: the platform's top face is
``SLIDE_MEMBER_H`` above the deck, no more.

The cheeks stand on the deck's own face, the way the bottom drawer does: the
bay's slide row starts at the deck, so the only air under the tray is the
slide's running clearance. Same fact, same note, in ``check_lungs_carriage``.


THE JOINTS, AND WHERE THE DOGBONES ARE NOT
==========================================

The carcass's vocabulary: housings cut ``DADO_FIT`` oversize, glued, screwed
through the receiver.

    platform  runs in a dado on each cheek's inner face, edge to edge, glued.
              No screws: the joint sits inside the band the slide's drawer
              member covers, and a screw head under a slide is a tray that
              does not close.
    lip       sits in a dado on each cheek's inner face, from the platform's
              dado up through the cheek's top edge, screwed through the cheek
              above the slide band. Its bottom edge lands in the platform's
              dado, so the housing has no blind end and no square inside
              corner: nothing here is relieved because nothing here turns a
              corner. The platform butts the lip's front face.

The two holes and the tube route in the lip are APERTURES. Holes are round;
the route is a capsule, per ``through_slot``'s rule. Joinery stays square.


ORIENTATION OF THE UNIT, AND WHAT IS NOT KNOWN ABOUT IT
=======================================================

The unit's long axis runs in Y, as ``Station.extractor_env`` says it must, so
it pulls toward the operator. Which END faces the operator is a design choice
this file makes and tags: the hose inlet end goes to the REAR, against the lip,
because the hose port is high and rear in the left end wall and because the
pressure sensor's tube leaves the lip. ``params.ct15_inlet``, ``ct15_exhaust``
and ``ct15_plug_lead.exit`` are all still None (MEASURE, C00), so the inlet
elbow, the exhaust grille and the lead's exit are NOT marked on the envelope:
the reference solid is the calipered box and nothing on its faces, and the
manual's one positional fact -- the exhaust grille is on the head's RIGHT side
face -- is carried in the check as a note, not as geometry.


FULL EXTENSION, THE DOOR AND THE LEG
====================================

The tray is checked in two positions. CLOSED, its front sits behind the lungs
door's landing: the door's thickness plus the lay-up on its inside face (C09,
which is why the lungs bay's slide row starts at ``bay_walls.LUNGS_SLIDE_INSET``
and not at the drawers' inset). OPEN, it is translated toward the
operator by the slide's rated travel -- that is -Y on this datum, where +Y runs
to the rear -- and the unit has to pass between the two front legs. The leg is
an angle. Its X-facing flange is measured and bolted; its Y-facing flange is
NOT: neither its width (``LegHoles.flange_w``) nor which way it runs
(``LegHoles.front_flange_inboard``) has been read off the machine. If that
flange runs INTO the opening across the bay's front, it stands in the tray's
way by tens of millimetres and nothing pulls out. ``machine.front_leg_flanges``
builds it at the width the bolt pattern proves, this part intersects the
tray's SWEPT volume with it, and the result is reported as a MEASURE until the
direction is read -- and as a blocking clash the moment it reads inboard.

The sweep matters. The flange is a 3.5mm plate just outside the bay's front
face; a solid that ends up entirely in front of it at full extension has
passed THROUGH it on the way, and a test at the end position alone would say
nothing. ``swept`` builds the volume a solid occupies over the whole travel,
so a hit at any point of the pull reads, not only a hit at the end of it.

PANEL CONVENTION
================

Every panel is drawn flat on the house convention and stood up by its plane:

    cheek     local X = station +Y (0 at the tray front), local Y = station +Z,
              thickness into +X
    platform  local X = station +X, local Y = station +Y, flat
    lip       local X = station +X, local Y = station +Z, thickness into -Y,
              so its Z = 0 face is the REAR face the sensor lands on
"""

from __future__ import annotations

from build123d import Align, Box, GeomType, Location, Part, Plane, extrude

from lib.house import GRID, SHEET_4X8, fits
from stations.cnc_shapeoko.carcass import (
    DADO_D,
    DADO_W,
    DATUMS,
    SCREW_CLEAR_D,
    SERVICE_GAP,
    T,
    Datums,
    bore,
    export_part,
    groove,
    panel,
    screw_line,
    screw_positions,
    through_slot,
)
from stations.cnc_shapeoko.params import EXTRACTORS
from stations.cnc_shapeoko.parts import mains_backplate
from stations.cnc_shapeoko.parts.bay_walls import (
    LINING_T,
    LUNGS_SLIDE_INSET,
    SLIDE_BORE_D,
    SLIDE_BORE_DEPTH,
    SLIDE_LEN,
    SLIDE_MEMBER_H,
)

__all__ = [
    "PART_NAME",
    "CT15_NAME",
    "DP_NAME",
    "SLIDE_TRAVEL",
    "LIP_H",
    "CHEEK_H",
    "carriage_width",
    "carriage_origin",
    "platform_size",
    "ct15_station",
    "dp_station",
    "build_cheek",
    "build_platform",
    "build_lip",
    "build_ct15",
    "build_dp_sensor",
    "panels",
    "placed_all",
    "extended",
    "swept",
    "joint_table",
    "check_lungs_carriage",
    "export",
]

D: Datums = DATUMS

PART_NAME = "lungs_carriage"
CT15_NAME = "ct15_env"
DP_NAME = "dp_sensor_pad"


# ====================================================================
# PARAMETERS -- everything specific to this part, and nothing else.
# The bay, the lining and the slide allowance come from params through
# Datums; the slide's own numbers from bay_walls; the unit from EXTRACTORS;
# the joinery from carcass. No dimension literal appears in the geometry.
# ====================================================================

# ---- the slide, the one vendor fact bay_walls does not carry ------------
SLIDE_TRAVEL = 508.0
"""Rated travel of the 500mm pair at full extension. SOURCE: Accuride 3832EC
quick reference, document 3700-9508(1183)-MK114-R5-1215,
accuride.com/media/amasty/amfile/attach/d4ba99d10b86f194bef3fdc51f9ccb24.pdf,
row 3832-C20EC: slide length 19.68in [500], travel 20.00in [508].
CONFIDENCE: datasheet, READ 2026-09-03 off that PDF (the row and the "Closed
Position: Drawer Member Flush or Under" note both extracted by text). The
maker's HTML product page redirects in a loop; the PDF is what to cite. Flush
or under when closed means the tray's front edge travels the full 508."""

SLIDE_HEIGHT_SHEET = 45.7
"""The same sheet's slide height, 1.80in [45.7mm]. SOURCE: as above, "Overall
slide dimensions: 1.80" x 1/2"" and "Height: 1.80'' [45.7 mm]", read 2026-09-03.
CONFIDENCE: datasheet. Recorded because ``bay_walls.SLIDE_MEMBER_H`` carries
45.0 and this part builds to that; the 0.7mm is the sheet's and bay_walls's to
reconcile, not this tray's. Nothing here reads it except the check."""

# ---- the tray --------------------------------------------------------------
LIP_H = GRID * 2
"""How far the lip and the cheeks rise above the platform's top face.
SOURCE: design, on the bench grid. CONFIDENCE: design. Two modules, up into
the unit's chassis by a hand's worth, so a yanked tray pulls the unit by its
body. Also the height of the sensor's pad on the lip."""

CHEEK_H = SLIDE_MEMBER_H + LIP_H
"""Cheek height above the deck. SOURCE: derived. The slide band plus the lip's
rise, so the lip can be housed in the cheeks rather than stood on the
platform."""

PLATFORM_TOP = SLIDE_MEMBER_H
"""Platform top face above ``deck_top``. SOURCE: bay_walls.check_bay_walls,
which already budgets the lungs stack as slide member + unit +
service gap. CONFIDENCE: derived. This tray IS that stack-up; the platform sits
no higher than the member it hangs on."""

PLATFORM_Z0 = PLATFORM_TOP - T
"""Platform underside above ``deck_top``. Derived."""

LIP_INSET = T
"""How far the lip's dado sits in from each cheek's rear end. SOURCE: the
drawers' ``BACK_INSET``, one thickness, so the cheek wraps the lip and the
slide's drawer member has full-length birch under it. CONFIDENCE: derived."""

LUNGS_DOOR_LANDING = T + LINING_T
"""What the bay's front gives up to the lungs door (C09): the door's own
thickness, flush in the front, plus the lay-up bonded to its inside face.
SOURCE: lungs_door, landed 2026-09-04; was ``T`` alone by analogy with the
rear door's landing while C09 was unmodelled. CONFIDENCE: derived. The closed
tray's front sits behind it at ``bay_walls.LUNGS_SLIDE_INSET``."""

SCREW_PITCH_TRAY = T * 4
SCREW_INSET_TRAY = T
"""Fastener rhythm on the lip's housings, the drawers' figure: a short joint in
tension every time the tray is opened. SOURCE: drawers. CONFIDENCE: derived."""

# ---- the unit ---------------------------------------------------------------
CT15 = EXTRACTORS["CT15"]
"""The fitted unit's row. SOURCE: params.EXTRACTORS, calipered 2026-09-02.
CONFIDENCE: calipered. ``env`` is (Y long axis, X width, Z height)."""

CT15_INLET_END = "rear"
"""Which end of the unit faces the lip. SOURCE: design, see the module
docstring: hose port high and rear in the left end wall, sensor tube leaving
the lip. CONFIDENCE: design. ``params.ct15_inlet`` is None, so this places the
unit's box and marks nothing on it."""

# ---- the pressure sensor ----------------------------------------------------
DP_SENSOR = "Sensirion SDP810-500Pa, tube connection, article 1-101532-01"
DP_SOURCE = (
    "Sensirion SDP8xx-Digital datasheet v1.1 (April 2019), section 7.2 "
    "Dimensions SDP81x - Tube Connection, figure 2, page 11; "
    "sensirion.com/media/documents/90500156/6167E43B/"
    "Sensirion_Differential_Pressure_Datasheet_SDP8xx_Digital.pdf"
)
"""The sensor the pad is cut for. SOURCE: the brief's BOM line reads
"Adafruit / Sensirion"; adafruit.com carries NO SDP8xx product (site search
'sdp810', 2026-09-03: "No products found"), so there is no Adafruit breakout
and no Adafruit page to read. The sensor's OWN body carries the mounting holes
and the barbs, and the datasheet dimensions them. CONFIDENCE: datasheet, READ
2026-09-03 from the PDF at the URL above (page 11 rendered and read; the
figure is vector art and does not extract as text). The datasheet's ordering
table (page 1) gives SDP810-500Pa the article number 1-101532-01, which is what
J13 and the BOM should carry instead of "Adafruit / Sensirion": the bare sensor
from a Sensirion distributor, plus a mating lead for its 4-pin 2.0mm header,
which is J13's to source."""

DP_BODY = (29.0, 18.0, 10.25)
"""Sensor body (W, H, depth behind the mounting face), figure 2: 29 +-0.4 by
18 +-0.4, 10.25 +-0.25 to the barb shoulder. SOURCE: DP_SOURCE, read
2026-09-03. CONFIDENCE: datasheet."""

DP_NOZZLE_L = 13.5
"""Barb length beyond the body, figure 2. SOURCE: DP_SOURCE. CONFIDENCE:
datasheet. The envelope's depth is the body plus this."""

DP_HOLE_PITCH = 24.0
"""Centre distance of the sensor's two mounting holes, figure 2: "(24)".
SOURCE: DP_SOURCE. CONFIDENCE: datasheet."""

DP_HOLE_D = 2.9
"""The sensor's mounting hole, figure 2: "(o2.9)", an M2.5 clearance.
SOURCE: DP_SOURCE. CONFIDENCE: datasheet. The lip gets the same hole so one
screw and one nut close the joint."""

DP_HOLE_DROP = 4.5
"""Hole centres below the body's top edge, figure 2: "4.5". SOURCE: DP_SOURCE.
CONFIDENCE: datasheet."""

DP_NOZZLE_PITCH = 12.6
"""Centre distance of the two barbs, figure 2: "12.6 +-0.2". SOURCE: DP_SOURCE.
CONFIDENCE: datasheet. Sets the route's length so both tubes pass."""

DP_TUBE_ID = 4.0
"""Tube bore the barb takes, figure 2: barb o5.2 over a o4 stem, o3.5 neck.
SOURCE: DP_SOURCE. CONFIDENCE: datasheet. A 4mm-ID tube over a 5.2 barb."""

DP_ROUTE_W = 8.0
"""Width of the tube route through the lip, figure 2: "(o8)", the barb's
shoulder, the widest thing on the pneumatic side. SOURCE: DP_SOURCE.
CONFIDENCE: derived. A tube over the 5.2 barb is under 8 for any wall this
station would use; the route is a CAPSULE ``DP_NOZZLE_PITCH`` longer than it is
wide so both tubes go through side by side under their barbs."""

DP_ROUTE_DROP = DP_BODY[1] / 2 + DP_ROUTE_W / 2
"""Route centre below the pad centre: just under the body's lower edge, so the
tubes turn once and go through. SOURCE: derived. CONFIDENCE: design."""


# ====================================================================
# GEOMETRY. Nothing below is a dimension; it is all arithmetic on the
# block above and on Datums.
# ====================================================================


def carriage_width(d: Datums = D) -> float:
    """Outside width of the tray, cheek face to cheek face: the bay less the
    left slide's spacer block (2026-09-04), the lining and the slide member
    on each side. The hand clearance the bay also budgets
    (``lungs_side_clear``) is spent INSIDE this width, between the unit and
    the lining; see ``check_lungs_carriage``."""
    s = d.s
    return s.bay_lungs_w - s.lungs_spacer - 2 * (s.lungs_lining_t + s.lungs_slide_t)


def lining_faces(d: Datums = D) -> tuple[float, float]:
    """Station X of the bay's two lining faces: on the spacer block's bay
    face to the left, on the divider's lungs face to the right."""
    s = d.s
    return (d.lungs_x[0] + s.lungs_spacer + s.lungs_lining_t, d.lungs_x[1] - s.lungs_lining_t)


def carriage_origin(d: Datums = D) -> tuple[float, float, float]:
    """Station coordinates of the tray's lower, left, front corner: one
    spacer, one lining and one slide off the left end wall (RULED 2026-09-04:
    the left slide on a spacer, so the tray clears the front-left stile's
    edge and the lungs door's knuckle on the pull), front flush with the
    cabinet member's front end (the lungs bay's own inset, behind the door
    and its lay-up), standing on the deck."""
    s = d.s
    x0 = lining_faces(d)[0] + s.lungs_slide_t
    return (x0, LUNGS_SLIDE_INSET, d.deck_top)


def inner_width(d: Datums = D) -> float:
    """Clear width between the cheeks' inner faces."""
    return carriage_width(d) - 2 * T


def lip_y(d: Datums = D) -> tuple[float, float]:
    """Station Y span of the lip: front face, rear face."""
    _x0, y0, _z0 = carriage_origin(d)
    rear = y0 + SLIDE_LEN - LIP_INSET
    return (rear - T, rear)


def platform_size(d: Datums = D) -> tuple[float, float]:
    """The platform's blank: the clear width plus its two tongues, and the
    depth from the tray's front to the lip's front face."""
    _x0, y0, _z0 = carriage_origin(d)
    return (inner_width(d) + 2 * DADO_D, lip_y(d)[0] - y0)


def lip_size(d: Datums = D) -> tuple[float, float]:
    """The lip's blank: the clear width plus its two tongues, and its height
    from the platform's underside to the cheeks' top edge."""
    return (inner_width(d) + 2 * DADO_D, CHEEK_H - PLATFORM_Z0)


def ct15_station(
    d: Datums = D,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The unit's box in station coordinates: centred between the cheeks, its
    inlet end against the lip, standing on the platform."""
    x0, _y0, z0 = carriage_origin(d)
    long, wide, tall = CT15["env"]
    cx = x0 + carriage_width(d) / 2
    y_rear = lip_y(d)[0]
    z_bot = z0 + PLATFORM_TOP
    return ((cx - wide / 2, cx + wide / 2), (y_rear - long, y_rear), (z_bot, z_bot + tall))


def dp_pad_local(d: Datums = D) -> tuple[float, float]:
    """Centre of the sensor's body on the lip, in lip-local XY: across the
    lip's middle, in the middle of the band that stands above the platform."""
    w, _h = lip_size(d)
    return (w / 2, (PLATFORM_TOP - PLATFORM_Z0) + LIP_H / 2)


def dp_holes_local(d: Datums = D) -> list[tuple[float, float]]:
    """The two mounting holes in lip-local XY, from the body's outline."""
    cx, cy = dp_pad_local(d)
    y = cy + DP_BODY[1] / 2 - DP_HOLE_DROP
    return [(cx - DP_HOLE_PITCH / 2, y), (cx + DP_HOLE_PITCH / 2, y)]


def dp_route_local(d: Datums = D) -> tuple[float, float]:
    """Centre of the tube route capsule in lip-local XY."""
    cx, cy = dp_pad_local(d)
    return (cx, cy - DP_ROUTE_DROP)


def dp_station(
    d: Datums = D,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """The sensor's envelope, body plus barbs, standing off the lip's REAR
    face, in station coordinates."""
    x0, _y0, z0 = carriage_origin(d)
    cx, cy = dp_pad_local(d)
    bw, bh, bd = DP_BODY
    sx = x0 + T - DADO_D + cx
    sz = z0 + PLATFORM_Z0 + cy
    y_face = lip_y(d)[1]
    return (
        (sx - bw / 2, sx + bw / 2),
        (y_face, y_face + bd + DP_NOZZLE_L),
        (sz - bh / 2, sz + bh / 2),
    )


# ---------------------------------------------------------------- planes


def _plane_cheek(hand: str, d: Datums = D) -> Plane:
    x0, y0, z0 = carriage_origin(d)
    x = x0 if hand == "l" else x0 + carriage_width(d) - T
    return Plane(origin=(x, y0, z0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def _cheek_faces(hand: str) -> tuple[str, str]:
    """(inner, outer) in ``groove``/``bore`` terms. Both cheeks are drawn in
    the same orientation, so which face looks into the tray flips with the
    hand; the flip is here and nowhere else."""
    return ("front", "back") if hand == "l" else ("back", "front")


def _plane_platform(d: Datums = D) -> Plane:
    x0, y0, z0 = carriage_origin(d)
    return Plane(
        origin=(x0 + T - DADO_D, y0, z0 + PLATFORM_Z0),
        x_dir=(1, 0, 0),
        z_dir=(0, 0, 1),
    )


def _plane_lip(d: Datums = D) -> Plane:
    x0, _y0, z0 = carriage_origin(d)
    return Plane(
        origin=(x0 + T - DADO_D, lip_y(d)[1], z0 + PLATFORM_Z0),
        x_dir=(1, 0, 0),
        z_dir=(0, -1, 0),
    )


# ---------------------------------------------------------------- panels


def _lip_dado_x() -> float:
    """Cheek-local X of the lip dado's centreline."""
    return SLIDE_LEN - LIP_INSET - DADO_W / 2


def build_cheek(hand: str, d: Datums = D) -> Part:
    """One cheek, flat. ``hand`` is "l" or "r"."""
    inner, outer = _cheek_faces(hand)
    p = panel(SLIDE_LEN, CHEEK_H)

    # platform dado, edge to edge along the inner face
    gy = PLATFORM_Z0 + DADO_W / 2
    p -= groove((0, gy), (SLIDE_LEN, gy), width=DADO_W, depth=DADO_D, side=inner)

    # lip dado, from the platform's dado up through the top edge. Its lower
    # end opens into the platform dado, so it has no blind end to relieve.
    lx = _lip_dado_x()
    p -= groove(
        (lx, PLATFORM_Z0), (lx, CHEEK_H), width=DADO_W, depth=DADO_D, side=inner
    )

    # the slide's DRAWER member on the outer face: the pattern bay_walls
    # drills for the cabinet member, flush with it, because the tray is as
    # long as the slide and starts where the cabinet member starts
    for x in screw_positions(SLIDE_LEN):
        p -= bore(x, SLIDE_MEMBER_H / 2, SLIDE_BORE_D, depth=SLIDE_BORE_DEPTH, side=outer)

    # screws through the cheek into the lip, above the slide band
    p -= screw_line(
        (lx, SLIDE_MEMBER_H + SCREW_INSET_TRAY),
        (lx, CHEEK_H),
        d=SCREW_CLEAR_D,
        pitch=SCREW_PITCH_TRAY,
        inset=SCREW_INSET_TRAY,
    )
    return p


def build_platform(d: Datums = D) -> Part:
    """The platform, flat. No features: it runs in two dados and is glued,
    and the unit stands directly on it."""
    w, dep = platform_size(d)
    return panel(w, dep)


def build_lip(d: Datums = D) -> Part:
    """The lip, flat. Its Z = 0 face is the rear face the sensor lands on.
    Two round holes for the sensor's screws and one capsule for its tubes:
    apertures, so no corner is square."""
    w, h = lip_size(d)
    p = panel(w, h)
    for x, y in dp_holes_local(d):
        p -= bore(x, y, DP_HOLE_D)
    rx, ry = dp_route_local(d)
    p -= through_slot(
        (rx, ry), DP_NOZZLE_PITCH + DP_ROUTE_W, DP_ROUTE_W, corner_r=DP_ROUTE_W / 2
    )
    return p


# ---------------------------------------------------------------- references


def _box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Part:
    return Box(x[1] - x[0], y[1] - y[0], z[1] - z[0],
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(
        Location((x[0], y[0], z[0]))
    )


def build_ct15(d: Datums = D) -> Part:
    """The unit as a reference solid, STATION coordinates."""
    return _box(*ct15_station(d))


def build_dp_sensor(d: Datums = D) -> Part:
    """The sensor's envelope on its pad, STATION coordinates."""
    return _box(*dp_station(d))


# ---------------------------------------------------------------- assembly


def panels(d: Datums = D) -> list[tuple[str, Part, Plane]]:
    """(label, flat part, plane) for the four birch panels."""
    return [
        (f"{PART_NAME}_cheek_l", build_cheek("l", d), _plane_cheek("l", d)),
        (f"{PART_NAME}_cheek_r", build_cheek("r", d), _plane_cheek("r", d)),
        (f"{PART_NAME}_platform", build_platform(d), _plane_platform(d)),
        (f"{PART_NAME}_lip", build_lip(d), _plane_lip(d)),
    ]


def placed_all(d: Datums = D) -> list[tuple[str, str, Part]]:
    """(label, group, part) for everything this module puts in the assembly,
    in the CLOSED position."""
    out: list[tuple[str, str, Part]] = [
        (label, "carriage", plane * part) for label, part, plane in panels(d)
    ]
    out.append((CT15_NAME, "reference", build_ct15(d)))
    out.append((DP_NAME, "reference", build_dp_sensor(d)))
    return out


def extended(part: Part) -> Part:
    """The same solid at full extension: toward the operator, which is -Y on
    this datum, by the slide's rated travel."""
    return part.moved(Location((0, -SLIDE_TRAVEL, 0)))


def swept(part: Part) -> Part:
    """Every point the solid occupies between CLOSED and full extension: the
    union of the solid and the prism of each of its faces along the travel.

    A point of the swept volume that is not in the closed solid lies on a
    segment that leaves the solid through its boundary, so the boundary's
    prisms cover it; that is the whole sweep, exactly, with no step size to
    choose. Planar faces are extruded along -Y (a face parallel to Y sweeps a
    sheet with no volume and is skipped). A curved face -- the slide bores,
    the screw holes and the tube route's walls -- is
    swept as the prism of its own bounding box, which is never less than its
    true sweep and, for every curved face on this tray, sits inside the
    silhouette of the plate or cylinder that carries it."""
    v = (0.0, -1.0, 0.0)
    pieces: list[Part] = [part]
    for f in part.faces():
        if f.geom_type == GeomType.PLANE:
            if abs(f.normal_at().Y) < 1e-9:
                continue
            pieces.append(extrude(f, amount=SLIDE_TRAVEL, dir=v))
        else:
            bb = f.bounding_box()
            pieces.append(
                _box(
                    (bb.min.X, bb.max.X),
                    (bb.min.Y - SLIDE_TRAVEL, bb.max.Y),
                    (bb.min.Z, bb.max.Z),
                )
            )
    out = Part() + pieces
    return out


def joint_table(d: Datums = D) -> list[tuple]:
    """Declared joints, as ``(a, b, kind, axis, lo, hi, note)`` tuples, the
    shape ``drawers.joint_table`` uses."""
    x0, _y0, _z0 = carriage_origin(d)
    w = carriage_width(d)
    n = PART_NAME
    out: list[tuple] = []
    for hand, face_x, inward in (("l", x0 + T, -1.0), ("r", x0 + w - T, 1.0)):
        lo, hi = sorted((face_x, face_x + inward * DADO_D))
        for member in ("platform", "lip"):
            out.append(
                (f"{n}_cheek_{hand}", f"{n}_{member}", "housing", "x", lo, hi,
                 f"{member} edge in the cheek's dado")
            )
    out.append((f"{n}_platform", f"{n}_lip", "butt", None, 0.0, 0.0,
                "platform's rear edge butts the lip's front face"))
    out.append((f"{n}_platform", CT15_NAME, "bearing", None, 0.0, 0.0,
                "the unit stands directly on the platform"))
    out.append((f"{n}_lip", DP_NAME, "bearing", None, 0.0, 0.0,
                "sensor body flat on the lip's rear face over its two holes"))
    out.append((f"{n}_lip", CT15_NAME, "butt", None, 0.0, 0.0,
                "the unit's inlet end against the lip's front face"))
    return out


# ---------------------------------------------------------------- checks


def pullout_obstacles(d: Datums = D) -> list[tuple[str, Part]]:
    """(label, solid) of everything the tray has to pass on the pull: the two
    front legs' Y flange bands (steel), the two FRONT stiles (birch, 2026-09-04)
    and the lungs door's knuckle, which stands proud of the carcass plane in
    the gap between the front-left stile and the door.

    ``machine`` and ``lungs_door`` are imported here rather than at the top
    because both import this part; the same deferral ``Datums.mast_base``
    makes for ``top_cap``."""
    from stations.cnc_shapeoko.machine import front_leg_flanges
    from stations.cnc_shapeoko.parts import lungs_door, stiles

    out: list[tuple[str, Part]] = list(front_leg_flanges(d))
    for label, _group, part in stiles.placed_all(d):
        if "_front_" in label:
            out.append((label, part))
    out.append((lungs_door.HINGE_NAME, lungs_door.build_hinge(d)))
    return out


def pullout_clash(d: Datums = D) -> list[tuple[str, str, float, float, float]]:
    """(part, obstacle, shared mm3, x overlap mm, travel at first contact mm)
    for every tray solid whose SWEPT volume, closed to full extension, reaches
    into a front leg's Y-facing flange, a front stile or the lungs door's
    knuckle (``pullout_obstacles``).

    The whole travel is tested, not the end of it: the flange is a thin plate
    at the bay's front face, and a solid standing entirely in front of it at
    full extension went through it on the way. ``swept`` is what is
    intersected; the end position alone would have missed the unit."""
    flanges = pullout_obstacles(d)
    out: list[tuple[str, str, float, float, float]] = []
    if not flanges:
        return out
    for label, _group, part in placed_all(d):
        cb = part.bounding_box()
        sw = None
        for flabel, flange in flanges:
            fb = flange.bounding_box()
            if cb.max.X <= fb.min.X or fb.max.X <= cb.min.X:
                continue
            if cb.min.Y - SLIDE_TRAVEL >= fb.max.Y or fb.min.Y >= cb.max.Y:
                continue
            if sw is None:
                sw = swept(part)
            try:
                shared = sw & flange
            except Exception:
                continue
            if shared is None or shared.volume <= 1.0:
                continue
            overlap = min(cb.max.X, fb.max.X) - max(cb.min.X, fb.min.X)
            first = max(cb.min.Y - fb.max.Y, 0.0)
            out.append((label, flabel, shared.volume, overlap, first))
    return out


def check_lungs_carriage(d: Datums = D) -> list[str]:
    """What this tray has to be true for. The assembly's interference check
    owns whether it hits a neighbour; these are the things that are wrong
    before the solids are compared, plus the two positions only this part
    knows about."""
    notes: list[str] = []
    s = d.s
    x0, y0, z0 = carriage_origin(d)
    w = carriage_width(d)
    pw, pdep = platform_size(d)
    (cx0, cx1), (cy0, cy1), (cz0, cz1) = ct15_station(d)
    long, wide, tall = CT15["env"]

    # -- the width is the bay's own arithmetic, not a choice
    want = s.bay_lungs_w - s.lungs_spacer - 2 * (s.lungs_lining_t + s.lungs_slide_t)
    if abs(w - want) > 0.1:
        notes.append(f"carriage is {w:.1f} wide against the bay's {want:.1f}")

    # -- the unit's box is the calipered envelope, exactly
    bb = build_ct15(d).bounding_box()
    got = (bb.size.Y, bb.size.X, bb.size.Z)
    if any(abs(g - e) > 1e-6 for g, e in zip(got, CT15["env"])):
        notes.append(
            f"{CT15_NAME} is {got[0]:.3f} x {got[1]:.3f} x {got[2]:.3f} and "
            f"EXTRACTORS['CT15'] is {long} x {wide} x {tall}"
        )

    # -- hand clearance: the unit to each LINING face, the bay's own figure
    lin_l, lin_r = lining_faces(d)
    for side, gap in (("left", cx0 - lin_l), ("right", lin_r - cx1)):
        if gap < s.lungs_side_clear - 1e-6:
            notes.append(
                f"the unit sits {gap:.1f}mm off the {side} lining face against "
                f"lungs_side_clear {s.lungs_side_clear:.1f}"
            )

    # -- the unit fits the tray: between the cheeks, on the platform
    if wide > inner_width(d):
        notes.append(f"the unit is {wide:.1f} wide between cheeks {inner_width(d):.1f} apart")
    if long > pdep:
        notes.append(f"the unit is {long:.1f} long on a {pdep:.1f} platform")
    if cy0 < y0 - 1e-6:
        notes.append(f"the unit's front at y {cy0:.1f} overhangs the tray's front at {y0:.1f}")

    # -- and the bay: under the cap with the service gap, on the deck
    if cz1 + SERVICE_GAP > d.top_z[0] + 1e-6:
        notes.append(
            f"the unit's top at z {cz1:.1f} plus {SERVICE_GAP:.0f} service is "
            f"over the cap's underside at {d.top_z[0]:.1f}"
        )
    if cz0 < d.deck_top:
        notes.append("the unit is below the deck")
    if y0 + SLIDE_LEN > d.front_bay_d + 1e-6:
        notes.append(
            f"the tray runs to y {y0 + SLIDE_LEN:.1f} in a {d.front_bay_d:.1f} bay: it hits the spine"
        )

    # -- the receptacle box on the spine's lungs face, which mains_backplate
    #    said this part would own the geometry of. Measured, not arithmetic.
    (bx0, bx1), (by0, _by1), (bz0, bz1) = mains_backplate.receptacle_station(d)
    tray_rear = max(y0 + SLIDE_LEN, dp_station(d)[1][1])
    if by0 < tray_rear and bz0 < z0 + CHEEK_H and bx0 < x0 + w and bx1 > x0:
        notes.append(
            f"the receptacle box's front at y {by0:.1f} is inside the tray's "
            f"reach to y {tray_rear:.1f} at a height they share"
        )

    # -- the lungs door's landing (C09): the closed tray sits behind it
    if y0 < LUNGS_DOOR_LANDING:
        notes.append(
            f"the closed tray's front at y {y0:.1f} is inside the lungs door's "
            f"{LUNGS_DOOR_LANDING:.0f}mm landing"
        )

    # -- the sensor's holes and route stay in the lip's band above the platform
    lw, lh = lip_size(d)
    band = (PLATFORM_TOP - PLATFORM_Z0, lh)
    for hx, hy in dp_holes_local(d):
        if not (band[0] + DP_HOLE_D < hy < band[1] - DP_HOLE_D) or not (DP_HOLE_D < hx < lw - DP_HOLE_D):
            notes.append(f"a sensor hole at lip-local ({hx:.1f}, {hy:.1f}) leaves the lip's pad band")
    rx, ry = dp_route_local(d)
    if ry - DP_ROUTE_W / 2 < band[0]:
        notes.append(
            f"the tube route's bottom at lip-local y {ry - DP_ROUTE_W / 2:.1f} is "
            f"below the platform's top at {band[0]:.1f}: the tube comes out under the unit"
        )
    if DP_ROUTE_W < DP_TUBE_ID:
        notes.append("the tube route is narrower than the tube")

    # -- the slide sheet against what bay_walls carries
    if abs(SLIDE_MEMBER_H - SLIDE_HEIGHT_SHEET) > 1e-6:
        notes.append(
            f"bay_walls.SLIDE_MEMBER_H is {SLIDE_MEMBER_H:.1f} and the Accuride "
            f"3832 sheet says {SLIDE_HEIGHT_SHEET:.1f}; the tray builds to bay_walls. "
            "Expected, and worth knowing before the members are screwed on: the "
            "cheek is a hair shorter than the member band."
        )

    # -- the placement is a rotation, and a rotation is where signs go wrong
    lip_f, lip_r = lip_y(d)
    want_bb = {
        f"{PART_NAME}_cheek_l": ((x0, x0 + T), (y0, y0 + SLIDE_LEN), (z0, z0 + CHEEK_H)),
        f"{PART_NAME}_cheek_r": ((x0 + w - T, x0 + w), (y0, y0 + SLIDE_LEN), (z0, z0 + CHEEK_H)),
        f"{PART_NAME}_platform": (
            (x0 + T - DADO_D, x0 + w - T + DADO_D),
            (y0, lip_f),
            (z0 + PLATFORM_Z0, z0 + PLATFORM_TOP),
        ),
        f"{PART_NAME}_lip": (
            (x0 + T - DADO_D, x0 + w - T + DADO_D),
            (lip_f, lip_r),
            (z0 + PLATFORM_Z0, z0 + CHEEK_H),
        ),
    }
    for label, _group, part in placed_all(d):
        if label not in want_bb:
            continue
        bb = part.bounding_box()
        got3 = ((bb.min.X, bb.max.X), (bb.min.Y, bb.max.Y), (bb.min.Z, bb.max.Z))
        for axis, g, e in zip("xyz", got3, want_bb[label]):
            if abs(g[0] - e[0]) > 0.05 or abs(g[1] - e[1]) > 0.05:
                notes.append(
                    f"{label} landed at {axis} {g[0]:.1f}..{g[1]:.1f} and belongs "
                    f"at {e[0]:.1f}..{e[1]:.1f}. Its plane is wrong."
                )

    # -- full extension against the front legs
    h = s.leg_holes
    clashes = pullout_clash(d)
    worst = max((c[3] for c in clashes), default=0.0)
    soonest = min((c[4] for c in clashes), default=0.0)
    hit = ", ".join(f"{c[0]} by {c[3]:.1f}" for c in clashes)
    if h.front_flange_inboard is None:
        if clashes:
            notes.append(
                "the leg's Y-facing flange is not measured: neither its width "
                "nor which way it runs. IF it runs into the opening across the "
                "bay's front (vertex at the leg's outer corner), then somewhere "
                f"in the {SLIDE_TRAVEL:.0f}mm of travel toward the operator "
                f"(first contact after {soonest:.0f}mm) the tray reaches "
                f"{worst:.1f}mm into it at the width the bolt pattern proves "
                f"({h.span_h + h.hole_d / 2:.1f}mm): {hit}mm, swept over the "
                "whole pull. Nothing pulls out of the lungs bay -- or the hands "
                "bay. MEASURE THIS: on a front leg, does the flange without "
                "holes run along the machine's front INTO the leg opening, or "
                "away from it; and how wide. Write LegHoles.front_flange_inboard "
                "and LegHoles.flange_w."
            )
    elif h.front_flange_inboard:
        for label, flabel, vol, overlap, first in clashes:
            notes.append(
                f"{label} runs {overlap:.1f}mm into the {flabel} from "
                f"{first:.0f}mm of travel on ({vol / 1000:.1f} cm3 swept). "
                "The tray does not pull out."
            )

    # -- what the unit's faces have not told us
    notes.append(
        f"{CT15_NAME} is the calipered box and nothing on it: the inlet elbow, "
        "the exhaust grille and the lead's exit are catalog Nones (ct15_inlet, "
        "ct15_exhaust, ct15_plug_lead.exit). The unit is placed inlet end to the "
        f"lip ({CT15_INLET_END}) by design; the manual puts the exhaust grille on "
        "the head's RIGHT side face, toward the lungs/stock divider. Expected, "
        "and worth knowing before the plenum (C08) is drawn against this box."
    )

    # -- standing on the deck, the bottom drawer's own note
    notes.append(
        f"{PART_NAME} stands on deck_top with no air under it: the bay's slide "
        "row starts at the deck, so the only under-clearance the tray has is the "
        "slide's own running clearance. Expected, and worth knowing."
    )

    for label, part, _plane in panels(d):
        bb = part.bounding_box()
        if not fits((bb.size.X, bb.size.Y), SHEET_4X8):
            notes.append(f"{label} blank does not come out of a 4x8 sheet")

    return notes


# ---------------------------------------------------------------- export


def export(d: Datums = D) -> list:
    """STEP and DXF for the four panels; STEP only for the references."""
    written = []
    for label, part, _plane in panels(d):
        written += export_part(part, label)
    written += export_part(build_ct15(d), CT15_NAME, dxf=False)
    written += export_part(build_dp_sensor(d), DP_NAME, dxf=False)
    return written


# ---------------------------------------------------------------- report

if __name__ == "__main__":
    d = DATUMS
    x0, y0, z0 = carriage_origin(d)
    w = carriage_width(d)
    pw, pdep = platform_size(d)
    lw, lh = lip_size(d)
    (cx0, cx1), (cy0, cy1), (cz0, cz1) = ct15_station(d)

    print(f"{PART_NAME}: {w:.1f} wide x {SLIDE_LEN:.0f} deep x {CHEEK_H:.0f} tall, at x {x0:.1f}, y {y0:.0f}, on the deck")
    print(f"  cheeks {SLIDE_LEN:.0f} x {CHEEK_H:.0f} x {T:.0f}   platform {pw:.1f} x {pdep:.1f} x {T:.0f}   lip {lw:.1f} x {lh:.0f} x {T:.0f}")
    print(f"  platform top {PLATFORM_TOP:.0f} above the deck; lip rises {LIP_H:.0f} above it")
    print(
        f"  {CT15_NAME}: x {cx0:.1f}..{cx1:.1f}  y {cy0:.1f}..{cy1:.1f}  z {cz0:.1f}..{cz1:.1f} "
        f"directly on the platform; {d.top_z[0] - cz1:.0f}mm under the cap"
    )
    (sx0, sx1), (sy0, sy1), (sz0, sz1) = dp_station(d)
    print(
        f"  {DP_NAME}: {DP_SENSOR}, body {DP_BODY[0]:.0f} x {DP_BODY[1]:.0f} on the lip's rear "
        f"face at y {sy0:.1f}, barbs to y {sy1:.1f}; 2 x o{DP_HOLE_D} at {DP_HOLE_PITCH:.0f} pitch, "
        f"route {DP_ROUTE_W:.0f} x {DP_NOZZLE_PITCH + DP_ROUTE_W:.1f} capsule"
    )
    print(f"  full extension: {SLIDE_TRAVEL:.0f}mm toward the operator, tray front at y {y0 - SLIDE_TRAVEL:.0f}")

    found = check_lungs_carriage(d)
    if found:
        print(f"\n{len(found)} lungs carriage note(s):")
        for n in found:
            print(f"  - {n}")
    else:
        print("\nno lungs carriage constraint violations")

    for p in export(d):
        print(f"wrote {p}")
