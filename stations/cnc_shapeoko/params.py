"""Parameter block for the Shapeoko 5 Pro 4x4 station carcass.

Every number the model needs lives here and nowhere else. Most of them are
estimates scaled from photographs and published specs, tagged below with their
confidence. None of them gate the CAD: measuring the real machine is an edit to
this file, not a redesign.

Brief: https://notes.aaand.space/cnc-station-enclosure.html (v4, 2026-09-01)
"""

from dataclasses import dataclass, field

from lib.house import CARCASS_T, GRID, PANEL_T, QUARTER, STOCK_MODULE, on_grid

# Confidence tags carried from the brief's parameter table, so a reader of the
# model knows which numbers are load-bearing guesses.
CONFIDENCE = {
    "table_h": "high",       # Carbide leg kit spec, 36 in with feet
    "clear_h": "medium",     # floor to underside of frame, less gussets
    "leg_x_inner": "low",    # scaled from the leg-kit photo. MEASURE THIS.
    "leg_y_inner": "low",    # same method
    "leg_splay": "low",      # visible in the leg-kit render
    "vfd_box": "medium",     # Carbide VFD enclosure photo, stock orientation
    "extractor_env": "medium",   # CT48 E
}


@dataclass(frozen=True)
class Station:
    # ---- machine envelope -------------------------------------------------
    table_h: float = 889.0          # 35 in, top of the table
    clear_h: float = 780.0          # usable height under the frame
    leg_x_inner: float = 1100.0     # inside faces of the legs, left to right
    leg_y_inner: float = 1150.0     # inside faces, front to back
    leg_splay: float = 6.0          # degrees

    # ---- bays -------------------------------------------------------------
    bay_brain_d: float = 250.0      # rear band, full width
    bay_lungs_w: float = 480.0      # CT48 on slides, plus lining and clearance
    bay_stock_w: float = 220.0      # remainder. 8 to 10 blanks at 20mm pitch.
    bay_hands_w: float = 400.0      # drawer width

    # ---- components -------------------------------------------------------
    vfd_box: tuple[float, float, float] = (200.0, 130.0, 300.0)   # vertical
    extractor_env: tuple[float, float, float] = (630.0, 365.0, 600.0)

    # ---- sheet goods ------------------------------------------------------
    carcass_t: float = CARCASS_T
    panel_t: float = PANEL_T
    stock_module: float = STOCK_MODULE
    sheet_slot: tuple[float, float] = (600.0, 600.0)   # HALF blank on edge
    sheet_pitch: float = 20.0                          # slot spacing in the rack
    laser_blank: tuple[float, float] = QUARTER

    # ---- extraction -------------------------------------------------------
    hose_id: float = 36.0           # antistatic, the run to the boot
    overrun_s: int = 12             # hose clear time after the spindle drops
    cyclone: bool = False           # struck 2026-09-01. All internal, no external port.

    def front_bays(self) -> float:
        """Sum of the three front bay widths."""
        return self.bay_lungs_w + self.bay_stock_w + self.bay_hands_w

    def slack(self) -> float:
        """Millimetres left over across the front. The brief's warning is that
        this is currently zero against an estimated leg_x_inner."""
        return self.leg_x_inner - self.front_bays()

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

    if s.extractor_env[2] > s.clear_h:
        problems.append("extractor is taller than the clearance under the frame")

    if s.vfd_box[2] > s.clear_h:
        problems.append("VFD box is taller than the clearance under the frame")

    if s.bay_lungs_w < s.extractor_env[1]:
        problems.append(
            f"lungs bay {s.bay_lungs_w:.0f}mm is narrower than the extractor's "
            f"{s.extractor_env[1]:.0f}mm, before lining and slides"
        )

    if not on_grid(s.stock_module):
        problems.append(f"stock module {s.stock_module}mm is off the {GRID}mm grid")

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
