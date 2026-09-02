"""Parameter block for the Shapeoko 5 Pro 4x4 station carcass.

Every number the model needs lives here and nowhere else. Most of them are
estimates scaled from photographs and published specs, tagged below with their
confidence. None of them gate the CAD: measuring the real machine is an edit to
this file, not a redesign.

Brief: https://notes.aaand.space/cnc-station-enclosure.html (v4, 2026-09-01)

Sourced pass 2026-09-01: manufacturer figures reconciled in from the URLs in
SOURCES. Where a sourced number disagrees with the brief the brief's value is
kept and the disagreement is written on the line, not silently resolved.
"""

from dataclasses import dataclass
from math import ceil

from lib.house import CARCASS_T, GRID, PANEL_T, QUARTER, STOCK_MODULE, on_grid

# Where each number came from. A reader who doubts a value chases it here.
SOURCES = {
    "footprint_x": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "footprint_y": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "footprint_z": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "travel_x": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "travel_y": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "t_slot_pitch": "https://carbide3d.com/shapeoko/shapeoko5pro-specs/",
    "table_h_no_feet": "https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "table_h_with_feet": "https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "leg_wall_t": "https://shop.carbide3d.com/products/shapeoko51pro-leg44",
    "leg_mount_pitch": "https://community.carbide3d.com/t/leg-kit-center-to-center-spacing-and-hole-diameter/105167",
    "leg_mount_hole_d": "https://community.carbide3d.com/t/leg-kit-center-to-center-spacing-and-hole-diameter/105167",
    "leg_x_inner": "UNSOURCED. Jared's tape. See the comment on the field.",
    "leg_y_inner": "UNSOURCED. Jared's tape.",
    "leg_splay": "UNSOURCED. Carbide publishes no leg geometry at all.",
    "extractor_env": "See EXTRACTORS. Each entry carries its own festoolusa URL.",
    "hose_id": "https://carbide3d.com/hub/docs/sweepy-pro-s5-pro/",
    "hose_bend_mult": "UNSOURCED ASSUMPTION. No maker publishes a bend radius for D36/32.",
    "vfd_box": "UNSOURCED. Carbide publishes no VFD enclosure dimensions.",
    "vfd_vent_clear": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "vfd_mount_pitch": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "mini_pc_env": "https://download.intel.com/newsroom/2023/client-computing/Intel-NUC-13-Pro-Tech-Product-Spec.pdf",
}

# ---------------------------------------------------------------- extractors
#
# The station is built around ONE of these and has to be able to grow into the
# other. Jared ordered the CT 15 HEPA; the CT 36 EI is the v2 growth path.
#
# THIS TABLE IS WHY THE REGISTRY EXISTS. The brief carried an envelope tagged
# "CT48 E" that was in fact the CT 36's to within 4mm on height, and a real CT 48
# has never stood under this frame in any version of the design. Envelopes and
# bag part numbers are per size and do not interchange, so both live on the same
# row as the name and neither can drift away from it again.
#
#   CT 15      470 x 320 x 435    15 L    130 CFM   fitted
#   CT 26 EI   630 x 365 x 540    26 L              would also fit
#   CT 36 EI   630 x 365 x 596    36 L              the growth path
#   CT 48 EI   740 x 406 x 1005   48 L              will not fit, ever
#
EXTRACTORS = {
    "CT15": {
        "name": "Festool CT 15 HEPA CLEANTEC",
        "env": (470.0, 320.0, 435.0),   # festoolusa spec table, verified 2026-09-02
        "capacity_l": 15,
        "airflow_cfm": 130.0,           # festoolusa: "130 CFM (3 700 l/min)"
        "bag": "Festool SC-FIS-CT MINI/MIDI-2/5/CT15, part 204308",
        "url": "https://www.festoolusa.com/products/dust-extractors/dust-extractors-for-cleaning/578441---ct-15-hepa-us",
    },
    "CT36EI": {
        "name": "Festool CT 36 EI HEPA CLEANTEC",
        "env": (630.0, 365.0, 596.0),   # festoolusa spec table. Height is body
                                        # only; the carry handle is not in it.
        "capacity_l": 36,
        "airflow_cfm": None,            # not read off the spec table yet
        "bag": "Festool SC FIS-CT 36/5, part 496186",
        "url": "https://www.festoolusa.com/products/dust-extractors/workshop-dust-extractors/577872---ct-36-ei-hepa-us",
    },
}

MAIN_FILTER = "Festool HEPA-HF-CT 26/36/48 PTFE, part 205412"
"""One filter covers the 26, 36 and 48. It does NOT cover the CT 15, whose main
filter has not been read off a spec table yet. Tagged so the gap is visible when
the consumable line gets ordered."""

# Confidence tags carried from the brief's parameter table, so a reader of the
# model knows which numbers are load-bearing guesses.
CONFIDENCE = {
    "table_h": "medium",     # 889 is exactly 35in; Carbide publishes 893 without
                             # feet and 945 with. Which config Jared owns is open.
    "clear_h": "medium",     # floor to underside of frame, less gussets.
                             # Carbide publishes no frame clearance. Still an estimate.
    "leg_x_inner": "low",    # scaled from the leg-kit photo. MEASURE THIS.
    "leg_y_inner": "low",    # same method
    "leg_splay": "low",      # visible in the leg-kit render
    "vfd_box": "low",        # downgraded: no published dims exist. Measure with calipers.
    "extractor_env": "high",     # festoolusa spec table for whichever row is selected
    "vfd_panel_standoff": "assumption",     # see the field. A traded clearance.
    "vfd_louvre_free_ratio": "assumption",  # nobody publishes one
    "lungs_lining_t": "medium",  # MLV plus open-cell foam, lay-up not yet bought
    "lungs_slide_t": "high",     # Accuride 3832 class member section
    "lungs_side_clear": "medium",   # a hand's clearance, chosen not sourced
    "footprint_x": "high",       # carbide3d spec table
    "footprint_y": "high",       # carbide3d spec table
    "footprint_z": "medium",     # live spec 23.25in, older forum quotes of the same field 21in
    "travel_x": "high",          # carbide3d spec table
    "travel_y": "high",          # carbide3d spec table
    "t_slot_pitch": "high",      # carbide3d spec table
    "table_h_no_feet": "high",   # carbide leg kit page
    "table_h_with_feet": "high", # carbide leg kit page
    "leg_wall_t": "high",        # 10-gauge powder-coated steel, carbide leg kit page
    "leg_mount_pitch": "medium", # Carbide staff reply on the forum, not a spec sheet
    "leg_mount_hole_d": "medium",# same reply
    "hose_id": "high",           # carbide sweepy pro doc, 35/36mm
    "hose_bend_mult": "assumption",  # nobody publishes one. Flagged, not sourced.
    "vfd_vent_clear": "high",    # carbide 65mm spindle doc, 30cm
    "vfd_mount_pitch": "high",   # carbide 65mm spindle doc
    "mini_pc_env": "medium",     # NUC 13 Pro tall chassis, as the class of thing
}


@dataclass(frozen=True)
class Station:
    # ---- machine envelope -------------------------------------------------
    table_h: float = 889.0          # 35 in, top of the table. Carbide's own page says
                                    # 893mm for the same 35in. Kept the brief's exact
                                    # conversion; see table_h_no_feet / _with_feet.
    clear_h: float = 780.0          # usable height under the frame
    leg_x_inner: float = 1100.0     # inside faces of the legs, left to right.
                                    # NOT changed by research. The only figure found is
                                    # 1130.3 (44.5in) from one forum post on a 2x4
                                    # machine, axis inferred not stated, 5.1 leg kit.
                                    # A forum anecdote on the wrong machine does not
                                    # beat a tape. community.carbide3d.com/t/.../103406
    leg_y_inner: float = 1150.0     # inside faces, front to back
    leg_splay: float = 6.0          # degrees

    # ---- machine, as published --------------------------------------------
    # The station has to live inside these. None of them were in the brief.
    footprint_x: float = 1524.0     # 60 in, carbide3d spec table
    footprint_y: float = 1498.6     # 59 in, carbide3d spec table
    footprint_z: float = 590.55     # 23.25 in, carbide3d spec table. CONTRADICTION:
                                    # older forum quotes of this same field say 21 in
                                    # (533.4). The published spec appears to have moved.
    travel_x: float = 1237.0        # carbide3d spec table
    travel_y: float = 1237.0        # carbide3d spec table
    t_slot_pitch: float = 102.6     # centre to centre, carbide3d spec table
    table_h_no_feet: float = 893.0  # carbide leg kit page, its own mm for 35 in
    table_h_with_feet: float = 945.0    # carbide leg kit page, 36 in
    leg_wall_t: float = 3.4         # 10-gauge steel, carbide leg kit page.
                                    # Anything bolted to a leg gets a backing washer.
    leg_mount_pitch: tuple[float, float] = (40.0, 65.0)   # carbide staff, forum 105167.
                                    # 65 is off the 20mm grid: a bolt-through plate
                                    # cannot be grid-indexed on both axes.
    leg_mount_hole_d: float = 7.0   # thru for M6, same source

    # ---- extractor selection ----------------------------------------------
    extractor: str = "CT15"
    """The unit that was ORDERED and that v1 is built around."""

    extractor_growth: str = "CT36EI"
    """The unit v2 has to accept without a redesign. Everything expensive to
    change is sized for this one; only the lungs/stock divider, the stock rack
    and the slide member are sized for the fitted unit. See check_growth_path."""

    # ---- bays -------------------------------------------------------------
    bay_brain_d: float = 250.0      # rear band, full width
    bay_stock_w: float = 220.0      # DEAD ESTIMATE. Stock is the remainder and
                                    # Datums.stock_clear_w is the real number;
                                    # this is kept only so check() can report
                                    # how far the brief's arithmetic was out.
    bay_hands_w: float = 400.0      # drawer width

    # ---- lungs bay allowance ----------------------------------------------
    # bay_lungs_w is DERIVED from these and the fitted extractor. It used to be a
    # 480 literal sized around a CT 48 that was really a CT 36, which left 66mm
    # of slack nothing had named. Naming the three allowances means the bay
    # resizes correctly when the extractor changes instead of keeping a cushion
    # whose size nobody could account for.
    lungs_lining_t: float = 12.0    # MLV plus open-cell foam, bonded, per side
    lungs_slide_t: float = 12.7     # slide member plus its clearance, per side
    lungs_side_clear: float = 20.0  # hand clearance, carriage to lining, per side

    # ---- components -------------------------------------------------------
    vfd_box: tuple[float, float, float] = (200.0, 130.0, 300.0)   # vertical.
                                    # Kept: the only figure found is a customer's
                                    # forum measurement, 152 x 178 x 260 (w x d x h),
                                    # which is smaller than this in two axes. The
                                    # brief's envelope is the conservative one.
    vfd_vent_clear: float = 300.0   # carbide 65mm spindle doc, 30cm from the vented
                                    # (left) face to any obstruction
    vfd_mount_pitch: float = 85.0   # two slotted wall-mount holes, carbide spindle doc

    # ---- VFD ventilation: a knowing deviation -----------------------------
    # Ruling 2026-09-02, Jared: the drive vents THROUGH THE PANEL.
    #
    # Carbide asks for 300mm of clear air off the drive's vented LEFT face. This
    # station does not give it 300mm of clear air. The drive stands vertically in
    # Carbide's own stock orientation at the LEFT end of the brain band, its
    # vented face looking at a louvred opening in the left brain-band cheek
    # vfd_panel_standoff away, and the 300mm is satisfied by the open room on the
    # other side of that louvre rather than by span inside the box.
    #
    # THIS IS A TRADE, NOT A SOLUTION, and it is written here so nobody later
    # reads a passing check as Carbide's clearance having been met. What was
    # bought for it: the brain band stops reserving a 430mm internal corridor,
    # which was the previous model's answer and which turned the drive 90 degrees
    # out of the orientation its stock mount sets.
    #
    # What pays for it, all three required together:
    #   1. louvre free area >= vfd_louvre_free_ratio x the vented face area
    #   2. intake low, through the plinth and the deck
    #   3. exhaust high, through the top cap's louvre field over the band
    vfd_vent_mode: str = "panel"
    vfd_panel_standoff: float = 40.0        # 2 grid modules, vented face to the
                                            # cheek's inner face. ASSUMPTION.
    vfd_louvre_free_ratio: float = 1.5      # ASSUMPTION, not sourced. Nobody
                                            # publishes a free-area figure for a
                                            # louvre standing in for a clearance.
                                            # 1.5 pays for the air having to turn
                                            # through 90 degrees to leave.

    mini_pc_env: tuple[float, float, float] = (117.0, 112.0, 54.0)   # NUC 13 Pro tall

    # ---- sheet goods ------------------------------------------------------
    carcass_t: float = CARCASS_T
    panel_t: float = PANEL_T
    stock_module: float = STOCK_MODULE
    sheet_slot: tuple[float, float] = (600.0, 600.0)   # HALF blank on edge
    sheet_pitch: float = 20.0                          # slot spacing in the rack
    laser_blank: tuple[float, float] = QUARTER

    # ---- extraction -------------------------------------------------------
    hose_id: float = 36.0           # antistatic, the run to the boot.
                                    # Confirmed: carbide sweepy pro takes 35/36mm.
    hose_bend_mult: float = 4.0     # ASSUMPTION, not a spec. No manufacturer publishes
                                    # a bend radius for the D36/32 hose family, so the
                                    # model uses a multiple of hose diameter.
    overrun_s: int = 12             # hose clear time after the spindle drops
    cyclone: bool = False           # struck 2026-09-01. All internal, no external port.

    def front_bays(self) -> float:
        """Sum of the three front bay widths."""
        return self.bay_lungs_w + self.bay_stock_w + self.bay_hands_w

    def slack(self) -> float:
        """Millimetres left over across the front. The brief's warning is that
        this is currently zero against an estimated leg_x_inner."""
        return self.leg_x_inner - self.front_bays()

    def front_bay_d(self) -> float:
        """Usable depth of a front bay: the leg opening less the rear brain band
        and the panel that divides them."""
        return self.leg_y_inner - self.bay_brain_d - self.carcass_t

    def hose_bend_r(self) -> float:
        """Working bend radius for the extraction hose. An assumption, derived so
        that it moves when hose_id moves."""
        return self.hose_id * self.hose_bend_mult

    def stock_capacity(self) -> int:
        """HALF blanks the station rack holds on edge."""
        return int(self.bay_stock_w // self.sheet_pitch)

    # ---- the fitted extractor, and the one v2 has to accept ---------------

    @property
    def spec(self) -> dict:
        """The EXTRACTORS row for the unit that is actually going in."""
        return EXTRACTORS[self.extractor]

    @property
    def growth_spec(self) -> dict:
        """The EXTRACTORS row v2 has to accept without a redesign."""
        return EXTRACTORS[self.extractor_growth]

    @property
    def extractor_env(self) -> tuple[float, float, float]:
        """(long axis in Y, width in X, height in Z) of the fitted unit.

        Derived from the selector, never written down twice. The unit's long axis
        runs front to back so it pulls toward the operator; see the carcass
        module's note on why all three front bays load from the front."""
        return self.spec["env"]

    @property
    def consumables(self) -> dict:
        """Bag and filter for whatever is fitted. Bags are per size."""
        return {"filter_bag": self.spec["bag"], "main_filter": MAIN_FILTER}

    # ---- lungs bay width, derived rather than estimated -------------------

    def lungs_allowance(self) -> float:
        """Total width the bay spends on everything that is not the extractor:
        acoustic lining, slide member and hand clearance, both sides."""
        return 2 * (self.lungs_lining_t + self.lungs_slide_t + self.lungs_side_clear)

    def lungs_w_for(self, key: str) -> float:
        """Clear lungs width that housing EXTRACTORS[key] needs, on the grid.

        Snapped UP: the bay is allowed to be generous, never short. This is the
        one bay dimension the fitted unit sets, which is what makes the growth
        path a divider move rather than a rebuild."""
        need = EXTRACTORS[key]["env"][1] + self.lungs_allowance()
        return _snap_up(need)

    @property
    def bay_lungs_w(self) -> float:
        """Clear width of the lungs bay, set by the FITTED extractor."""
        return self.lungs_w_for(self.extractor)

    @property
    def bay_lungs_w_growth(self) -> float:
        """What the lungs bay becomes under the growth extractor. The difference
        between this and bay_lungs_w is the whole cost of the conversion, and it
        comes out of stock."""
        return self.lungs_w_for(self.extractor_growth)

    # ---- VFD panel venting ------------------------------------------------

    @property
    def vfd_vent_face(self) -> tuple[float, float]:
        """(depth, height) of the drive's vented LEFT face, standing vertically
        in Carbide's stock orientation."""
        return (self.vfd_box[1], self.vfd_box[2])

    @property
    def vfd_vent_face_area(self) -> float:
        d, h = self.vfd_vent_face
        return d * h

    @property
    def louvre_free_area_req(self) -> float:
        """Free area the brain-band louvre has to present for the traded
        clearance to be paid for. See the vfd_vent_mode comment block."""
        return self.vfd_vent_face_area * self.vfd_louvre_free_ratio


def _snap_up(mm: float) -> float:
    """Round up to the bench grid.

    carcass.py has the same helper, but params sits underneath carcass and
    cannot import from it without a cycle. Both derive from house.GRID, so
    there is one grid, not two."""
    return ceil(mm / GRID - 1e-9) * GRID


STATION = Station()


def check(s: Station = STATION) -> list[str]:
    """Report every constraint the current numbers violate.

    Run this after editing a parameter. It is cheaper than discovering the
    conflict in geometry.
    """
    problems: list[str] = []

    if s.slack() < 0:
        problems.append(
            f"front bays overflow the leg opening by {-s.slack():.0f}mm "
            f"({s.front_bays():.0f} into {s.leg_x_inner:.0f}). "
            "Stock is the bay that gives; the room's wall rack absorbs it."
        )
    elif s.slack() == 0:
        problems.append(
            "front bays sum to leg_x_inner with zero slack. This is the brief's "
            "open item: one tape measurement between the inside faces of the legs."
        )

    if CONFIDENCE.get("leg_x_inner") == "low":
        problems.append(
            f"leg_x_inner is still {s.leg_x_inner:.0f}mm scaled off a photograph, "
            "not measured. It is the one unsourced number the whole model stands "
            "on, and stock is the bay that absorbs whatever the tape says. This "
            "note does not clear until CONFIDENCE says it was measured."
        )

    if s.leg_x_inner >= s.footprint_x:
        problems.append(
            f"leg_x_inner {s.leg_x_inner:.0f}mm is not inside the machine's own "
            f"{s.footprint_x:.0f}mm footprint. One of the two is wrong."
        )

    if s.table_h not in (s.table_h_no_feet, s.table_h_with_feet):
        problems.append(
            f"table_h {s.table_h:.0f}mm matches neither published leg config "
            f"({s.table_h_no_feet:.0f} without leveling feet, "
            f"{s.table_h_with_feet:.0f} with). Which feet are on the machine "
            f"moves the clearance by {s.table_h_with_feet - s.table_h_no_feet:.0f}mm."
        )

    if s.extractor_env[2] > s.clear_h:
        problems.append(
            f"{s.spec['name']} is taller than the clearance under the frame "
            f"({s.extractor_env[2]:.0f} into {s.clear_h:.0f}, over by "
            f"{s.extractor_env[2] - s.clear_h:.0f}mm). It does not stand under "
            "this machine in any orientation the bay allows."
        )

    if s.extractor_env[0] > s.front_bay_d():
        problems.append(
            f"extractor is deeper than a front bay ({s.extractor_env[0]:.0f} into "
            f"{s.front_bay_d():.0f}mm), so it cannot lie down in the lungs bay either"
        )

    if s.clear_h - s.extractor_env[2] < s.hose_bend_r():
        problems.append(
            f"no room above the extractor for the hose to turn: "
            f"{s.clear_h - s.extractor_env[2]:.0f}mm of headroom against a "
            f"{s.hose_bend_r():.0f}mm working bend radius (assumed, not published)"
        )

    if s.vfd_box[2] > s.clear_h:
        problems.append("VFD box is taller than the clearance under the frame")

    if s.vfd_vent_mode == "panel":
        # The old question was whether the bay is deep enough to hold Carbide's
        # 300mm inside it. Under the 2026-09-02 ruling that is the wrong question:
        # the clearance is deliberately taken outside the box. What has to hold
        # instead is that the trade was actually paid for.
        problems.append(
            f"TRADED CLEARANCE, standing note. Carbide asks {s.vfd_vent_clear:.0f}mm "
            f"of clear air off the drive's vented face. It gets "
            f"{s.vfd_panel_standoff:.0f}mm and then a louvre to room air. Ruled by "
            "Jared 2026-09-02. This note never clears; it is here so a passing check "
            "is never read as Carbide's clearance having been met. Paid for by a "
            f"louvre of at least {s.louvre_free_area_req / 100.0:.0f}cm2 free area "
            f"({s.vfd_louvre_free_ratio:.1f}x the "
            f"{s.vfd_vent_face[0]:.0f} x {s.vfd_vent_face[1]:.0f}mm vented face), "
            "intake low through the plinth, exhaust high through the top cap."
        )
        if s.bay_brain_d < s.vfd_box[1] + s.vfd_panel_standoff:
            problems.append(
                f"brain bay {s.bay_brain_d:.0f}mm deep cannot hold the VFD's "
                f"{s.vfd_box[1]:.0f}mm depth plus the {s.vfd_panel_standoff:.0f}mm "
                "standoff its vented face needs to the louvre. Panel venting does "
                "not remove the standoff, only Carbide's 300mm."
            )
    elif s.bay_brain_d < s.vfd_box[1] + s.vfd_vent_clear:
        problems.append(
            f"brain bay {s.bay_brain_d:.0f}mm deep cannot hold the VFD's "
            f"{s.vfd_box[1]:.0f}mm depth plus Carbide's {s.vfd_vent_clear:.0f}mm "
            "ventilation clearance. Either the bay grows, the VFD vents to open air "
            "through the panel, or the clearance is knowingly traded down."
        )

    if s.bay_brain_d < s.mini_pc_env[1]:
        problems.append(
            f"brain bay {s.bay_brain_d:.0f}mm is shallower than the mini PC's "
            f"{s.mini_pc_env[1]:.0f}mm"
        )

    if s.bay_lungs_w < s.extractor_env[1]:
        problems.append(
            f"lungs bay {s.bay_lungs_w:.0f}mm is narrower than the extractor's "
            f"{s.extractor_env[1]:.0f}mm, before lining and slides"
        )

    if not on_grid(s.stock_module):
        problems.append(f"stock module {s.stock_module}mm is off the {GRID}mm grid")

    if not on_grid(s.t_slot_pitch):
        problems.append(
            f"machine T-slot pitch {s.t_slot_pitch}mm is off the {GRID}mm bench grid. "
            "Not fixable: it is the machine. Jigs that cross from bench to bed carry "
            "the conversion, and the station rack stays on the bench grid."
        )

    if max(s.sheet_slot) > min(s.travel_x, s.travel_y):
        problems.append(
            f"a HALF blank {max(s.sheet_slot):.0f}mm does not fit the machine's "
            f"{min(s.travel_x, s.travel_y):.0f}mm travel"
        )

    if s.sheet_slot[1] > s.clear_h:
        problems.append(
            "a HALF blank will not stand on edge under the table. "
            "The station rack holds ready-use stock only."
        )

    return problems


def check_growth_path(s: Station = STATION) -> list[str]:
    """Can the station still take the growth extractor without a redesign.

    The promise made on 2026-09-02 is that swapping a CT 15 for a CT 36 costs a
    divider move and a slide member, not a new carcass. That promise is only
    worth anything if it is tested, so this asserts every dimension that would
    be EXPENSIVE to revisit against the growth unit, not the fitted one.

    Anything this reports is a dimension where the growth path has quietly been
    lost and the model is still claiming it.
    """
    g = s.growth_spec
    env = g["env"]
    problems: list[str] = []

    if env[0] > s.front_bay_d():
        problems.append(
            f"GROWTH LOST: {g['name']} is {env[0]:.0f}mm long into a "
            f"{s.front_bay_d():.0f}mm front bay. Bay depth is expensive to change, "
            "so this has to be sized for the growth unit from the start."
        )

    if env[2] > s.clear_h:
        problems.append(
            f"GROWTH LOST: {g['name']} is {env[2]:.0f}mm tall into {s.clear_h:.0f}mm "
            "of clearance under the frame. No divider move recovers this."
        )

    if s.clear_h - env[2] < s.hose_bend_r():
        problems.append(
            f"GROWTH LOST: {s.clear_h - env[2]:.0f}mm of headroom over "
            f"{g['name']} against a {s.hose_bend_r():.0f}mm hose bend radius"
        )

    grow_w = s.bay_lungs_w_growth
    if grow_w + s.bay_hands_w >= s.leg_x_inner:
        problems.append(
            f"GROWTH LOST: lungs {grow_w:.0f}mm plus hands {s.bay_hands_w:.0f}mm "
            f"leaves nothing for stock inside {s.leg_x_inner:.0f}mm"
        )

    return problems


def conversion_steps(s: Station = STATION) -> list[str]:
    """The named cost of going from the fitted extractor to the growth one.

    If this list ever grows past a divider, a rack and a slide member, the
    growth path has stopped being cheap and the claim in the brief is stale.
    """
    delta = s.bay_lungs_w_growth - s.bay_lungs_w
    return [
        f"set extractor = {s.extractor_growth!r} in params. One line.",
        f"move the lungs/stock divider {delta:.0f}mm right, into the second dado "
        "station already cut in the deck and the top cap. Lift the birch spline "
        "out of it and drop it into the vacated one.",
        f"recut the stock rack: it loses {delta:.0f}mm of width and the blanks "
        "it holds drop accordingly.",
        f"swap the lungs slide member for one no taller than the growth stack "
        "allows, and change the bag to " + s.growth_spec["bag"] + ".",
    ]


if __name__ == "__main__":
    s = STATION
    print(f"fitted:  {s.spec['name']}  {s.extractor_env[0]:.0f} x "
          f"{s.extractor_env[1]:.0f} x {s.extractor_env[2]:.0f}")
    print(f"growth:  {s.growth_spec['name']}  lungs bay would go "
          f"{s.bay_lungs_w:.0f} -> {s.bay_lungs_w_growth:.0f}mm")
    print(f"front bays {s.front_bays():.0f}mm into {s.leg_x_inner:.0f}mm, "
          f"slack {s.slack():.0f}mm")
    print(f"station rack holds {s.stock_capacity()} HALF blanks on edge")

    grown = check_growth_path(s)
    if grown:
        print(f"\n{len(grown)} GROWTH PATH failure(s):")
        for p in grown:
            print(f"  - {p}")
    else:
        print("\ngrowth path intact. Conversion to the CT 36:")
        for i, step in enumerate(conversion_steps(s), 1):
            print(f"  {i}. {step}")

    found = check(s)
    if found:
        print(f"\n{len(found)} constraint note(s):")
        for p in found:
            print(f"  - {p}")
    else:
        print("\nno constraint violations")
