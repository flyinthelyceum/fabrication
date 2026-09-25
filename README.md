# fabrication

The CAD spine for the Innovation Commons machine stations and the growlab. One
parametric source of truth per part, git-versioned, exporting STEP for Fusion and
DXF for the laser.

## Why this exists

Every station and enclosure in the shop was going to be modelled somewhere. Putting
them in one repo means the house standards live in code rather than in a habit, and
a dimension change regenerates the joinery instead of breaking it.

## Layout

```
lib/house.py                      house standards as code: the 20mm grid, the 600mm
                                  stock module, materials, connectors, red doctrine
stations/cnc_shapeoko/params.py   the Shapeoko 5 Pro 4x4 station parameter block
docs/build123d/                   vendored build123d reference, pinned to the
                                  installed version. Start at INDEX.md.
export/                           STEP and DXF output, gitignored
```

## Setup

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

build123d needs Python 3.13. The system 3.14 has no OCP wheels.

Run a parameter block to see its constraint report:

```bash
PYTHONPATH=. .venv/bin/python stations/cnc_shapeoko/params.py
```

## Doc grounding

`~/.claude/hooks/cad-doc-grounding.sh` fires on any Write or Edit to a `.py` file in
this repo. It asserts the vendored reference is present and injects a pointer to it
before CAD gets authored, so the API comes from the docs rather than from a model's
memory of them. It blocks the write if the reference has gone missing.

The docs are pinned to the version in `requirements.txt`. Bump both in the same
commit or the hook warns that they have drifted.

## House rules

Parameters live in one block per part, never buried in geometry. Joinery, kerf, and
fastener spacing derive from material thickness. Fitted drawer inserts are generated from a
tool list rather than drawn one pocket at a time. STEP and DXF both come from the
same model.

## Related

- CNC station brief v7: https://notes.aaand.space/cnc-station-enclosure.html
- CNC station build sequence: https://notes.aaand.space/cnc-station-build.html
- Working the station in Fusion: https://notes.aaand.space/cnc-station-fusion.html
- Design Standards tab on the Personal Bench BOM sheet is the human source of truth
  for the house standards mirrored in `lib/house.py`.
