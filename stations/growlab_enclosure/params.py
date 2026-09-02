"""Parameter block for the growlab enclosure — starting with the Pi + i3 tray.

Every number the model needs lives here and nowhere else. Millimetres throughout.
Following the same discipline as the CNC station: sourced values, confidence tags,
a check() that reports constraint violations before any geometry is cut.

The first part is the compute tray: a printed plate that carries the Raspberry Pi 5
with the Atlas i3 InterLink stacked on it as a HAT, mounted in the signal (exposed)
zone of the enclosure. See docs in flyinthelyceum/grow-lab: V1_PHYSICAL_BUILD.md,
the enclosure-zoning and front-panel artifacts.
"""

from dataclasses import dataclass

from lib.house import CARCASS_T, PANEL_T  # noqa: F401  (context; tray is printed, not sheet)

# Where each number came from. A reader who doubts a value chases it here.
SOURCES = {
    "pi_board": "https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf",
    "pi_hole_pitch": "https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf",
    "pi_hole_inset": "https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf",
    "pi_hole_d": "Pi mounting holes are 2.7mm dia for M2.5 (HAT/Pi spec)",
    "pi_port_h": "Pi 5 RJ45/USB stack height, ~13.5mm above PCB (mechanical drawing)",
    "hat_board": "https://atlas-scientific.com/electrical-isolation/i3-interlink/ — HAT footprint; EXACT i3 outline unconfirmed, using HAT-spec envelope",
    "hat_hole_pitch": "Raspberry Pi HAT spec: same 58x49 pattern as the Pi",
    "hat_standoff_h": "40-pin GPIO header is 8.5mm; standard HAT stack standoff 11mm",
    "insert_m25": "Heat-set insert for M2.5: ~4.0mm OD, receiving hole ~0.1-0.2mm under OD (research 2026-09-01)",
}

# Confidence carried into the model, so a reader knows which numbers are guesses.
CONFIDENCE = {
    "pi_board": "high",         # Raspberry Pi 5 official mechanical drawing
    "pi_hole_pitch": "high",    # 58 x 49, the fixed Pi/HAT rectangle
    "pi_hole_inset": "high",    # 3.5mm from the board edges
    "pi_hole_d": "high",
    "pi_port_h": "medium",      # port stack height varies a little by connector
    "hat_board": "low",         # i3 exact outline not yet measured; HAT envelope assumed. MEASURE.
    "hat_hole_pitch": "high",   # HAT spec locks this to the Pi pattern
    "hat_standoff_h": "medium", # 11mm typical; confirm the i3 clears the Pi's tall ports
    "insert_m25": "medium",     # depends on the insert bought; set receiving hole to its spec
}


@dataclass(frozen=True)
class Tray:
    # ---- Raspberry Pi 5 board ---------------------------------------------
    pi_board: tuple[float, float] = (85.0, 56.0)     # official mechanical drawing
    pi_hole_pitch: tuple[float, float] = (58.0, 49.0)  # the fixed Pi/HAT hole rectangle
    pi_hole_inset: float = 3.5                        # hole centres 3.5mm from board edges
    pi_hole_d: float = 2.7                            # thru for M2.5
    pi_port_h: float = 13.5                           # RJ45/USB stack above the PCB

    # ---- Atlas i3 InterLink (HAT on the Pi) -------------------------------
    hat_board: tuple[float, float] = (65.0, 56.0)    # HAT-spec envelope; i3 exact TBD (MEASURE)
    hat_hole_pitch: tuple[float, float] = (58.0, 49.0)  # HAT spec = the Pi rectangle
    hat_standoff_h: float = 11.0                      # Pi PCB top to HAT PCB bottom

    # ---- the tray ---------------------------------------------------------
    tray_t: float = 4.0            # printed base-plate thickness
    board_lift: float = 6.0        # standoff height: Pi PCB above the tray floor,
                                   # clearance for the underside + airflow
    margin: float = 6.0            # tray plate margin around the board footprint
    insert_od: float = 4.0         # M2.5 heat-set insert outer diameter
    insert_hole_d: float = 3.8     # receiving hole = OD minus ~0.2 for the melt
    insert_depth: float = 7.0      # hole depth from the boss top; must stop short of the floor
    boss_wall: float = 1.5         # printed wall around the insert, sets the boss radius
    fastener: str = "M2.5"         # board -> standoff, and HAT -> standoff

    # ---- context (from lib.house) -----------------------------------------
    panel_t: float = PANEL_T       # smoked acrylic reveal, if the tray shows through

    def tray_size(self) -> tuple[float, float]:
        """Outer plate footprint: board plus a margin all round."""
        return (self.pi_board[0] + 2 * self.margin,
                self.pi_board[1] + 2 * self.margin)

    def hole_centres(self) -> list[tuple[float, float]]:
        """The four mounting-hole centres, tray-local (origin at plate corner)."""
        x0 = self.margin + self.pi_hole_inset
        y0 = self.margin + self.pi_hole_inset
        px, py = self.pi_hole_pitch
        return [(x0, y0), (x0 + px, y0), (x0, y0 + py), (x0 + px, y0 + py)]

    def stack_h(self) -> float:
        """Tray floor to the top of the HAT PCB."""
        return self.board_lift + self.hat_standoff_h

    def boss_r(self) -> float:
        """Standoff boss radius: the insert plus a printed wall around it."""
        return self.insert_od / 2 + self.boss_wall

    def floor_under_insert(self) -> float:
        """Material left under the insert hole. Must be positive or the hole punches through."""
        return (self.tray_t + self.board_lift) - self.insert_depth


TRAY = Tray()


def check(t: Tray = TRAY) -> list[str]:
    """Report every constraint the current numbers violate. Run after edits;
    cheaper than finding the conflict in geometry."""
    problems: list[str] = []

    # holes must sit inside the board footprint
    px, py = t.pi_hole_pitch
    if px + 2 * t.pi_hole_inset > t.pi_board[0] or py + 2 * t.pi_hole_inset > t.pi_board[1]:
        problems.append(
            f"hole rectangle {px}x{py} + 2x{t.pi_hole_inset}mm inset does not fit "
            f"the {t.pi_board[0]}x{t.pi_board[1]}mm board"
        )

    # HAT must share the Pi hole pattern or it will not seat on the same standoffs
    if t.hat_hole_pitch != t.pi_hole_pitch:
        problems.append(
            f"HAT hole pitch {t.hat_hole_pitch} differs from the Pi {t.pi_hole_pitch}; "
            "they cannot share standoffs"
        )

    # the HAT standoff must clear the Pi's tall ports, or the HAT fouls the RJ45/USB
    if t.hat_standoff_h < t.pi_port_h:
        problems.append(
            f"HAT standoff {t.hat_standoff_h}mm is shorter than the Pi's "
            f"{t.pi_port_h}mm port stack. Confirm the i3 clears the ports (its 65mm "
            "length may sit clear of them) or raise the standoff."
        )

    # heat-set receiving hole must be under the insert OD, or it will not grip
    if t.insert_hole_d >= t.insert_od:
        problems.append(
            f"insert receiving hole {t.insert_hole_d}mm is not under the "
            f"{t.insert_od}mm insert OD; the melt has nothing to bite"
        )

    # inserts need wall around them; the margin must exceed the insert radius
    if t.margin < t.insert_od / 2 + 1.0:
        problems.append(
            f"tray margin {t.margin}mm is too thin for an {t.insert_od}mm insert "
            "plus a 1mm wall"
        )

    # the insert hole must stop short of the plate floor
    if t.floor_under_insert() < 1.0:
        problems.append(
            f"insert hole {t.insert_depth}mm leaves only {t.floor_under_insert():.1f}mm "
            f"under it (boss {t.board_lift} + plate {t.tray_t}); it punches through or nearly does"
        )

    return problems


if __name__ == "__main__":
    t = TRAY
    w, h = t.tray_size()
    print(f"tray plate {w:.0f} x {h:.0f} mm, {t.tray_t:.0f}mm thick")
    print(f"stack: tray floor -> HAT top = {t.stack_h():.0f}mm")
    print(f"mounting holes (tray-local): {[(round(x,1), round(y,1)) for x, y in t.hole_centres()]}")
    found = check(t)
    if found:
        print(f"\n{len(found)} constraint note(s):")
        for p in found:
            print(f"  - {p}")
    else:
        print("\nno constraint violations")
