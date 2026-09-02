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

from dataclasses import dataclass, field

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
    "extractor_env": "https://www.festoolusa.com/products/dust-extractors/workshop-dust-extractors/577872---ct-36-ei-hepa-us",
    "hose_id": "https://carbide3d.com/hub/docs/sweepy-pro-s5-pro/",
    "hose_bend_mult": "UNSOURCED ASSUMPTION. No maker publishes a bend radius for D36/32.",
    "vfd_box": "UNSOURCED. Carbide publishes no VFD enclosure dimensions.",
    "vfd_vent_clear": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "vfd_mount_pitch": "https://carbide3d.com/hub/docs/65mm-er16-spindle/",
    "mini_pc_env": "https://download.intel.com/newsroom/2023/client-computing/Intel-NUC-13-Pro-Tech-Product-Spec.pdf",
}

# Consumables the lungs bay has to store. Not geometry, but they are the reason
# the bag-change hinge exists, and getting the part number wrong wastes a week.
CONSUMABLES = {
    "filter_bag": "Festool SC FIS-CT 36/5, part 496186",     # festoolusa.
                                                             # Was the CT 48 bag (497539),
                                                             # left behind when the unit was
                                                             # ruled a CT 36. Bags are per
                                                             # size; the 48's does not fit.
    "main_filter": "Festool HEPA-HF-CT 26/36/48 PTFE, part 205412",   # festoolusa
}

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
    "extractor_env": "high",     # CT36 EI, festoolusa spec table
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

    # ---- bays -------------------------------------------------------------
    bay_brain_d: float = 250.0      # rear band, full width
    bay_lungs_w: float = 480.0      # CT48 on slides, plus lining and clearance
    bay_stock_w: float = 220.0      # remainder. 8 to 10 blanks at 20mm pitch.
    bay_hands_w: float = 400.0      # drawer width

    # ---- components -------------------------------------------------------
    vfd_box: tuple[float, float, float] = (200.0, 130.0, 300.0)   # vertical.
                                    # Kept: the only figure found is a customer's
                                    # forum measurement, 152 x 178 x 260 (w x d x h),
                                    # which is smaller than this in two axes. The
                                    # brief's envelope is the conservative one.
    vfd_vent_clear: float = 300.0   # carbide 65mm spindle doc, 30cm from the vented
                                    # (left) face to any obstruction
    vfd_mount_pitch: float = 85.0   # two slotted wall-mount holes, carbide spindle doc
    extractor_env: tuple[float, float, float] = (630.0, 365.0, 596.0)
                                    # festoolusa CT 36 EI spec table.
                                    # THE UNIT WAS MISLABELLED, not mis-estimated. The
                                    # brief carried 630 x 365 x 600 tagged "CT48 E".
                                    # That envelope is the CT 36 to within 4mm on
                                    # height. A real CT 48 is 740 x 406 x 1005 and has
                                    # never fitted under this frame in any version of
                                    # the design. Ruling 2026-09-02: the station takes
                                    # a CT 36. Jared's fallback was a CT 15, but the
                                    # bay was already sized for the 36 and holds it
                                    # with room, so the capacity is free.
                                    # Height is body only; the carry handle is not in
                                    # the published figure.
                                    # For reference, all festoolusa spec tables:
                                    #   CT 15      470 x 320 x 435    15 L
                                    #   CT 26 EI   630 x 365 x 540    26 L
                                    #   CT 36 EI   630 x 365 x 596    36 L  <- this one
                                    #   CT 48 EI   740 x 406 x 1005   48 L  (will not fit)
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
            f"extractor is taller than the clearance under the frame "
            f"({s.extractor_env[2]:.0f} into {s.clear_h:.0f}, over by "
            f"{s.extractor_env[2] - s.clear_h:.0f}mm). The CT48's published height "
            "does not stand under this machine in any orientation the bay allows."
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

    if s.bay_brain_d < s.vfd_box[1] + s.vfd_vent_clear:
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


if __name__ == "__main__":
    s = STATION
    print(f"front bays {s.front_bays():.0f}mm into {s.leg_x_inner:.0f}mm, "
          f"slack {s.slack():.0f}mm")
    print(f"station rack holds {s.stock_capacity()} HALF blanks on edge")
    found = check(s)
    if found:
        print(f"\n{len(found)} constraint note(s):")
        for p in found:
            print(f"  - {p}")
    else:
        print("\nno constraint violations")
