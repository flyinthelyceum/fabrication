"""One command that answers one question: is this model safe to cut?

    .venv/bin/python -m stations.cnc_shapeoko.check

Everything in the station already checks itself, but the checks are spread
across nine modules and nobody is going to run nine commands before walking to
the machine. This runs all of them and sorts what comes back into two piles,
because they are not the same kind of thing:

  BLOCKING   geometry that is wrong. Two parts in the same material, a part
             reaching into the machine's own steel, a part overflowing its bay.
             Cutting against any of these wastes sheet.

  TODO       a part the design needs and the model does not have yet. Does not
             stop you cutting the parts that DO exist; does stop final assembly.
             Fed by UNMODELLED below, which names every such part explicitly.
             A green gate can only see the parts that are modelled, so the
             closing line counts the ones that are not.

  MEASURE    waiting on Jared and a tape. Not a modelling error.

  STANDING   true, already decided, not going to change, and kept visible on
             purpose. Also build instructions the geometry cannot enforce.

The exit code follows BLOCKING alone, so this can gate a cut without a human
reading it. A standing note must never be able to stop the shop.

CLASSIFICATION IS A STOPGAP. It matches phrases that are written deliberately
into the check messages, which means renaming a message silently reclassifies
it. Anything unmatched falls to BLOCKING, so drift fails loud rather than quiet.
The real fix is for each check to return its own severity instead of a bare
string; that refactor touches nine modules and has not been done. It is
deliberately NOT done here either (C01, 2026-09-03): the UNMODELLED list is the
honest stopgap and the severity refactor is its own task.
"""

from __future__ import annotations

import sys

from stations.cnc_shapeoko import params
from stations.cnc_shapeoko.assembly import (
    check_assembly,
    components,
    envelope,
    interference,
)
from stations.cnc_shapeoko.carcass import DATUMS, check_carcass
from stations.cnc_shapeoko.machine import check_machine
from stations.cnc_shapeoko.parts import (
    base_deck,
    bay_walls,
    drawers,
    leg_joint,
    mast_base,
    spine_panel,
    stock_rails,
    top_cap,
    trays,
)

# A note is STANDING when it says so itself. These phrases are written into the
# check messages deliberately; grep for them there before editing this list.
STANDING_MARKS = (
    "Expected, and worth knowing",
    "Not fixable",
    "TRADED CLEARANCE",
    "standing note",
    "washer is not optional",           # a build instruction, not a defect
    "not the 220mm params estimates",   # params keeps a dead estimate on purpose
    "EARTH BONDING",                    # the star point. Never clears.
    "PE IS NEVER SWITCHED",             # earth survives the interlock
    "ANODIZE IS AN INSULATOR",          # bonding lug build instruction
)

TODO_MARKS = (
    "UNMODELLED:",
)

# Every part the build plan (C02..C18) still owes the model. Each task deletes
# its own name when its part lands in assembly.py, so the closing line's count
# falls to zero only when final assembly is actually modelled. Never let this
# list drift from the plan: a part missing from here is a part the gate cannot
# see and will not count.
UNMODELLED = (
    "rear_door",
    "lungs_carriage",
    "brain_partition",
    "exhaust_plenum",
    "console_plate",
    "lungs_door",
    "mains_backplate",
    "vfd_mount",
    "signal_mounts",
    "stock_wash",
)

MEASURE_MARKS = (
    "not measured",
    "MEASURE THIS",
    "matches neither published leg config",
    "Jared's tape",
)


def classify(note: str) -> str:
    if any(m in note for m in TODO_MARKS):
        return "TODO"
    if any(m in note for m in STANDING_MARKS):
        return "STANDING"
    if any(m in note for m in MEASURE_MARKS):
        return "MEASURE"
    return "BLOCKING"


def collect() -> list[tuple[str, str, str]]:
    """(bucket, source, note) for every check in the station."""
    d = DATUMS
    comps = components(d)

    sources: list[tuple[str, list[str]]] = [
        ("params", params.check()),
        ("earthing", params.check_earthing()),
        ("carcass", check_carcass(d)),
        ("base_deck", base_deck.check_base_deck()),
        ("bay_walls", bay_walls.check_bay_walls(d)),
        ("drawers", drawers.check_drawers(d)),
        ("trays", trays.check_trays(d)),
        ("spine_panel", spine_panel.check_spine(d)),
        ("top_cap", top_cap.check_top_cap(d)),
        ("mast_base", mast_base.check_mast_base(d)),
        ("stock_rails", stock_rails.check_stock_rails(d)),
        ("leg_joint", leg_joint.check_leg_joint(d)),
        ("assembly", check_assembly(comps, d)),
        ("machine", check_machine(comps, d)),
        (
            "unmodelled",
            [f"UNMODELLED: {name} is a part this plan builds and the model "
             "does not have yet" for name in UNMODELLED],
        ),
    ]

    out: list[tuple[str, str, str]] = []
    for name, notes in sources:
        for n in notes:
            out.append((classify(n), name, " ".join(n.split())))

    # Structural facts that are not opinions: overlap and envelope.
    for o in interference(comps, d):
        out.append(("BLOCKING", "assembly", f"interference: {o}"))
    for f in envelope(comps, d):
        if f.slack < 0:
            out.append(("BLOCKING", "assembly", f"does not fit: {f.line()}"))

    return out


def main() -> int:
    rows = collect()
    order = ("BLOCKING", "TODO", "MEASURE", "STANDING")
    d = DATUMS

    print(
        f"CNC station  ·  {d.s.spec['name']}  ·  "
        f"lungs {d.s.bay_lungs_w:.0f} | stock {d.stock_clear_w:.0f} clear "
        f"({d.stock_capacity} blanks) | hands {d.s.bay_hands_w:.0f}  ·  "
        f"bay {d.bay_h:.0f}, reveal {d.top_gap:.0f} (UNRELIEVED ceiling; the relieved reveal check_carcass uses is in the notes below)"
    )

    for bucket in order:
        hits = [r for r in rows if r[0] == bucket]
        print(f"\n{bucket}  ({len(hits)})")
        if not hits:
            print("  none")
        for _, src, note in hits:
            print(f"  [{src}] {note}")

    blocking = sum(1 for r in rows if r[0] == "BLOCKING")
    print()
    if blocking:
        print(f"NOT SAFE TO CUT: {blocking} blocking issue(s).")
    else:
        todo = sum(1 for r in rows if r[0] == "TODO")
        print(
            "SAFE TO CUT as modelled. The measurements above still gate the real "
            f"sheet, and {todo} part(s) remain unmodelled for final assembly: "
            + ", ".join(UNMODELLED)
            + "."
        )
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
