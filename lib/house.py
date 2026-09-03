"""House fabrication standards, as code.

Source of truth for these values is the Design Standards tab on the Personal Bench
BOM sheet. This module is the machine-readable copy. When the two disagree, the
sheet wins and this file gets corrected.

Everything is millimetres unless the name says otherwise. Temperatures that reach
a human are Fahrenheit; sensors that read Celsius convert at the display.
"""

# ---------------------------------------------------------------- the grid

GRID = 20.0
"""The bench dog grid. Every worktop in the room is on it, so any blank that
lands on it stops needing improvised workholding."""


def on_grid(mm: float) -> bool:
    """True when a dimension lands on the 20mm grid."""
    return abs(mm / GRID - round(mm / GRID)) < 1e-9


# ---------------------------------------------------------------- stock module

STOCK_MODULE = 600.0
"""Studio stock module, confirmed 2026-09-01. Exactly 30 grid modules.

Rejected alternative: 610mm (24in) matches the small laser bed exactly and divides
a 4x8 sheet with zero trim, but lands the grid at 30.5 modules. The grid gets used
every clamp-up. The 10mm never gets used.
"""

FULL = (600.0, 1200.0)      # working sheet, wall rack in the room
HALF = (600.0, 600.0)       # default project blank, station rack
QUARTER = (300.0, 600.0)    # laser blank, fills the small Universal bed
# STRIP is whatever the module leaves. Jigs, test cuts, small parts.

SHEET_4X8 = (1219.2, 2438.4)
SHEET_5X5_BALTIC = (1525.0, 1525.0)

LASER_BED_SMALL = (304.8, 609.6)    # Universal, 12 x 24 in
LASER_BED_LARGE = (457.2, 812.8)    # Universal, 18 x 32 in

PRINT_BED_AD5M = (220.0, 220.0, 220.0)      # Flashforge Adventurer 5M
PRINT_BED_BAMBU = (256.0, 256.0, 256.0)     # Bambu P1S / X1C
PRINT_BED_MIN = PRINT_BED_AD5M
"""The smallest bed in the room. A printed part sized to this one runs on
either machine, which is the only reason to have a house figure rather than
per-printer figures scattered through the parts."""

PRINT_BED_MARGIN = 10.0
"""Kept clear at every edge of a print bed. Skirt, purge line, and the fact
that a bed's stated size is its glass, not its first layer."""


def fits(blank: tuple[float, float], bed: tuple[float, float]) -> bool:
    """True when a blank fits a bed in either orientation."""
    b = sorted(blank)
    d = sorted(bed)
    return b[0] <= d[0] and b[1] <= d[1]


def bed_fill(blank: tuple[float, float], bed: tuple[float, float]) -> float:
    """Fraction of a bed's area a blank covers. 0.0 when it does not fit."""
    if not fits(blank, bed):
        return 0.0
    return (blank[0] * blank[1]) / (bed[0] * bed[1])


# ---------------------------------------------------------------- materials

CARCASS_T = 18.0        # Baltic birch. Parametric: joinery derives from this.
PANEL_T = 3.0           # smoked acrylic. Parametric: order and design unblock each other.

MATERIALS = {
    "carcass": "Baltic birch 18mm, raw or Osmo, matching the bench fleet",
    "reveal": "smoked acrylic 3mm",
    "mast": "aluminium extrusion 40x40, black anodized",
    "wear": "black delrin",
}
"""Material Non-Artifice. Four materials, each doing the thing it is good at,
none pretending to be another."""


# ---------------------------------------------------------------- connectors

HOUSE_CONNECTOR = "GX16-6"
"""One connector per run, sized to conductor count. Do NOT multiply GX16s:
combine runs of six conductors or fewer into one. Above six, step up inside the
aviation family (GX16-10, GX20-12) to hold the look.

Genuine exceptions leave the system: pH/EC probes are BNC coax, cameras are CSI
flat-flex through a sealed gland, and literal ethernet is RJ45.
"""


# ---------------------------------------------------------------- doctrine

RED = "#ff0033"
"""Reserved for consequence. On a machine station the E-stop is the entire red
budget. No red LEDs, no red labels, no red trim."""

STOPPING_AUTHORITY = ("e_stop", "panel_interlock")
"""Sensors inform, guards protect.

Only these two may stop a machine. Both are mechanical, both are legible at a
glance, both fail closed. Every other sensor reports and gets no vote. Software
that says no in a classroom gets bypassed inside a term, and the bypass takes a
real safety layer with it on the way past.
"""
