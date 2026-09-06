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


PITCH = 96.0
"""Centre-to-centre spacing of the 20mm dog holes. MFT pitch, added 2026-09-05.

GRID and PITCH are two different systems and they do not reconcile below 2400mm,
which is their least common multiple. Forcing a dimension to satisfy both drives
it to 480mm steps, and the only bench-scale results are too small to work at or
too deep for the room. So they divide the work instead:

    GRID  governs BLANKS AND PARTS. A blank on the 20mm module drops onto any
          worktop and gets clamped without improvising. This is what STOCK_MODULE
          is derived from and what ``on_grid`` tests.

    PITCH governs WORKTOPS THAT BUTT. Two tops only read as one surface if the
          hole pattern runs continuous across the seam, which requires each top
          to be a whole number of pitches with a half-pitch margin at the edge.
          This is what ``continuous`` tests.

A worktop is not a blank, so it answers to PITCH and is exempt from GRID. The
stock module already shows the split: 600 is exactly 30 grid modules and 6.25
pitches, and nobody has ever wanted it to be otherwise.
"""

EDGE_MARGIN = PITCH / 2
"""Last hole to the edge of a worktop. Half a pitch on each of two butted tops
sums to one full pitch across the seam, which is the whole trick."""


def on_grid(mm: float) -> bool:
    """True when a dimension lands on the 20mm grid."""
    return abs(mm / GRID - round(mm / GRID)) < 1e-9


def continuous(mm: float) -> bool:
    """True when a worktop dimension keeps the hole pitch running across a seam.

    The dimension has to be a whole number of pitches. Given that, a half-pitch
    margin at each edge puts the last hole of one top exactly one pitch from the
    first hole of the next.
    """
    return abs(mm / PITCH - round(mm / PITCH)) < 1e-9


def holes(mm: float) -> int:
    """How many dog holes fit a worktop dimension that satisfies ``continuous``."""
    return int(round(mm / PITCH))


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


def printable(size: tuple[float, float, float], bed=PRINT_BED_MIN, margin: float = PRINT_BED_MARGIN) -> bool:
    """True when a printed part, as it stands on the bed (x, y, z), fits the
    smallest bed in the room with ``margin`` kept clear at every edge."""
    return fits((size[0], size[1]), (bed[0] - 2 * margin, bed[1] - 2 * margin)) and size[2] <= bed[2]


def export_stl(
    part,
    path,
    *,
    bed=PRINT_BED_MIN,
    margin: float = PRINT_BED_MARGIN,
    tolerance: float = 0.01,
    angular_tolerance: float = 0.2,
):
    """Write a printed part's mesh, refusing one that will not fit the bed.

    ``part`` is the solid in its PRINT orientation, standing on Z = 0. The bed
    check runs on its bounding box before any file is written, so a carrier
    that outgrows the AD5M fails here and not at the slicer. build123d is
    imported lazily: this module is the standards sheet and has no CAD
    dependency of its own.
    """
    from build123d import export_stl as _export_stl

    bb = part.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)
    if not printable(size, bed, margin):
        raise ValueError(
            f"{size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} does not fit a "
            f"{bed[0]:.0f} x {bed[1]:.0f} x {bed[2]:.0f} bed with {margin:.0f}mm clear at every edge"
        )
    _export_stl(part, path, tolerance=tolerance, angular_tolerance=angular_tolerance)
    return path


# ---------------------------------------------------------------- materials

CARCASS_T = 12.0        # Baltic birch (house stock, ruling 18, 2026-09-04).
                        # Parametric: joinery derives from this. Was 18.0.
PANEL_T = 3.0           # smoked acrylic. Parametric: order and design unblock each other.

MATERIALS = {
    "carcass": "Baltic birch 18mm, raw or Osmo, matching the bench fleet",
    "reveal": "smoked acrylic 3mm",
    "mast": "aluminium extrusion 40x40, black anodized",
    "wear": "black delrin",
}
"""Material Non-Artifice. Four materials, each doing the thing it is good at,
none pretending to be another."""


# ---------------------------------------------------------------- foam pockets

POCKET_TOOL_D = 3.175
"""Flat endmill every foam pocket is cut with: the #102 1/8in flat, the
smallest flat cutter the station owns (tool_list.csv T017). A pocket's internal
corners are this cutter's radius; apertures round INWARD, joinery stays square.
A 1/4in would refuse the 1/8in cutters' own pockets (5.2mm wide)."""


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
