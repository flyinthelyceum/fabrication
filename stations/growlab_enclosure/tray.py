"""Compute tray for the growlab enclosure: Raspberry Pi 5 + Atlas i3 InterLink HAT.

A printed plate with four standoff bosses on the fixed Pi/HAT hole rectangle, each
taking an M2.5 heat-set insert. Every dimension comes from params.py; nothing is
buried here. STEP goes to Fusion for finishing, STL goes to the printer, both from
the same model.

Run from the repo root:
    .venv/bin/python -m stations.growlab_enclosure.tray
"""

from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    Hole,
    Location,
    Locations,
    export_step,
    export_stl,
)

from stations.growlab_enclosure.params import TRAY, Tray, check

OUT = Path(__file__).parent / "out"


def build(t: Tray = TRAY):
    """The tray as a build123d Part. Origin at the plate corner, so the
    tray-local hole_centres() from params map onto it one to one."""
    w, h = t.tray_size()
    corner = (Align.MIN, Align.MIN, Align.MIN)
    boss_top = t.tray_t + t.board_lift

    with BuildPart() as tray:
        # base plate
        Box(w, h, t.tray_t, align=corner)

        # standoff bosses rising from the plate top at each mounting hole
        with Locations(*[Location((x, y, t.tray_t)) for x, y in t.hole_centres()]):
            Cylinder(
                t.boss_r(),
                t.board_lift,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # heat-set insert holes, cut down from each boss top, stopping short of the floor
        with Locations(*[Location((x, y, boss_top)) for x, y in t.hole_centres()]):
            Hole(t.insert_hole_d / 2, depth=t.insert_depth)

    return tray.part


if __name__ == "__main__":
    for note in check():
        print("note:", note)

    part = build()
    OUT.mkdir(exist_ok=True)
    step_path = OUT / "tray.step"
    stl_path = OUT / "tray.stl"
    export_step(part, step_path)
    export_stl(part, stl_path)

    bb = part.bounding_box()
    print(
        f"tray bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
        f"volume {part.volume:.0f} mm3"
    )
    print(f"wrote {step_path} and {stl_path}")
