"""The shop cut list: every sheet-goods part, from every repo that cuts one.

    .venv/bin/python scripts/cutlist_sync.py            # writes cutlist/parts.json

WHAT IT IS
==========

One JSON file the Shop Cut List page renders: physical sheet -> how it is cut
(CNC nest or track saw) -> the parts on it, each with a stable id. Nothing in
it is typed by hand. Each project's own nest is run in its own interpreter
(the repos both have a top-level ``lib`` package, so they cannot share one) and
its placements are read back as JSON.

    workbench     ~/projects/workbench   bench/nest.py (18mm, CNC on 1219
                  blanks), bench/bom.py (5.2mm bottoms, same blanks; MDF top
                  layers, track saw)
    cnc station   this repo              stations/cnc_shapeoko/tools/nest.py
                  (12mm birch: track-saw sheets, Shapeoko sheets ripped
                  into blanks first). Acrylic and foam are not sheet goods
                  from the lumber order and are left out.

STABLE IDS
==========

Identical parts are interchangeable, so a part's id is its project, its name
and a counter (``wb-rib-017``), not its spot on a sheet. When a nest reshuffles,
"17 of 40 ribs cut" survives. Each id carries ``geom`` (blank size and
thickness); the page flags a part that was ticked at a different ``geom``,
because it was cut to the old size.

STOCK
=====

``STOCK`` below is receiving data, not geometry: what Spellman invoice 212240
(delivered 2026-09-18) put in the shop, and what is still backordered. Change
it when the 12mm 4x8 arrives. A sheet on backordered stock is shown but
marked waiting.

AFTER A MODEL CHANGE
====================

Run this script, commit ``cutlist/parts.json`` and ``cutlist/cut-list.html``,
and republish the page (ask Claude: "republish the cut list"). The same run
updates the students' Google Sheet (``scripts/cutlist_gsheet.py``) without
touching their ticks; ``--no-sheet`` skips it. Progress lives in the page's database,
keyed by part id, so a republish never wipes it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FAB = Path(__file__).resolve().parents[1]
WB = Path.home() / "projects" / "workbench"
PY = FAB / ".venv" / "bin" / "python"
OUT = FAB / "cutlist" / "parts.json"
PAGE = FAB / "cutlist" / "cut-list.html"      # the page to publish: template + parts

STOCK = {
    # key: (label, thickness mm, sheet size mm, on hand, status)
    "bb18-4x8": ("18mm Baltic birch BB/BB, 4x8", 18.0, (2438.4, 1219.2), 19, "on hand"),
    "bb12-4x8": ("12mm Baltic birch BB/BB, 4x8", 12.0, (2438.4, 1219.2), 0,
                 "backordered (10 on order, Spellman SO 1044690)"),
    "bb12-5x5": ("12mm Baltic birch BB/BB, 5x5", 12.0, (1525.0, 1525.0), 1, "on hand"),
    "bb5-4x8": ("5.2mm import birch A-3, 4x8", 5.2, (2438.4, 1219.2), 9, "on hand"),
    "mdf19-4x8": ("3/4in MDF (Duraply), 4x8", 19.05, (2438.4, 1219.2), 7, "on hand"),
}

# ------------------------------------------------------------------ extractors
# Each runs inside its repo and prints one JSON object on its last line.

WB_SNIPPET = r"""
import json
from bench import assembly, params as P, nest, bom
from bench.parts import jig
panels = assembly.all_panels()
jp = jig.panel()
fill = [(jp.name, jp.blank_l, jp.blank_w, jp.grain)] * jig.FLEET_QTY
m = nest.nest_fleet(panels, fill_items=fill)
thin, _ = nest.shelf_nest(bom._sheet_items(panels, P.DRAWER_BOTTOM_T))
per_sheet, layers, mdf = bom.mdf_sheets(panels)
t_of = {p.name: p.t for p in panels}
t_of[jp.name] = P.CARCASS_T
pl = lambda ps: [dict(blank=p.blank, part=p.part, x=p.x, y=p.y, l=p.l, w=p.w, rot=p.rot) for p in ps]
print(json.dumps(dict(
    blank=nest.BLANK, margin=nest.MARGIN, blanks_per_sheet=P.BLANKS_PER_SHEET,
    t18=P.CARCASS_T, t_thin=P.DRAWER_BOTTOM_T, t_mdf=P.MDF_PLY_T,
    thick=t_of, birch=pl(m["places"]), thin=pl(thin),
    top_l=P.TOP_L, top_d=P.TOP_D, mdf_layers=layers, mdf_per_sheet=per_sheet, mdf_sheets=mdf,
    benches=P.BENCH_COUNT)))
"""

FAB_SNIPPET = r"""
import json
from stations.cnc_shapeoko.tools import nest as N
n = N.nest()
out = []
for s in n.by_material("birch"):
    out.append(dict(
        index=s.index, kind=s.kind, size=list(s.size), t=N.SHEET_T,
        shelves=[dict(y=sh.y, h=sh.h, rips=list(sh.rips)) for sh in s.shelves],
        parts=[dict(part=p.blank.label, x=p.x, y=p.y, l=p.along_x, w=p.along_y,
                    shelf=p.shelf, segment=p.segment, grain=p.blank.rule) for p in s.placements]))
print(json.dumps(dict(sheets=out, gap=N.GAP)))
"""


def run(repo: Path, snippet: str) -> dict:
    r = subprocess.run([str(PY), "-c", snippet], cwd=repo, capture_output=True, text=True,
                       env={"PYTHONPATH": str(repo), "PATH": "/usr/bin:/bin"})
    if r.returncode:
        sys.exit(f"{repo.name}: extractor failed\n{r.stderr[-2000:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def sha(repo: Path) -> str:
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo,
                          capture_output=True, text=True).stdout.strip()


def r1(v: float) -> float:
    return round(v, 1)


def mm_in(v: float) -> str:
    """Nearest 1/16in, for the tape."""
    s = round(v / 25.4 * 16)
    whole, frac = divmod(s, 16)
    if not frac:
        return f'{whole}"'
    n, d = frac, 16
    while n % 2 == 0:
        n, d = n // 2, d // 2
    return f'{whole} {n}/{d}"' if whole else f'{n}/{d}"'


class Ids:
    """``<project>-<name>-NNN``, counted per name in the order parts are met."""

    def __init__(self) -> None:
        self.n: dict[str, int] = {}

    def __call__(self, project: str, name: str) -> str:
        k = f"{project}-{name}"
        self.n[k] = self.n.get(k, 0) + 1
        return f"{k}-{self.n[k]:03d}"


def part(ids: Ids, project: str, name: str, l: float, w: float, t: float, **kw) -> dict:
    a, b = max(l, w), min(l, w)
    return dict(id=ids(project, name), name=name, l=r1(a), w=r1(b), t=t,
                geom=f"{r1(a)}x{r1(b)}x{t:g}", size_in=f"{mm_in(a)} x {mm_in(b)}", **kw)


# ------------------------------------------------------------------ workbench


def workbench(ids: Ids) -> list[dict]:
    d = run(WB, WB_SNIPPET)
    src = f"workbench@{sha(WB)}"
    B = d["blank"]
    sheets: list[dict] = []

    def blank_sheets(places: list[dict], stock: str, t: float, label: str, method: str, prep: str) -> None:
        places = sorted(places, key=lambda p: (p["blank"], p["y"], p["x"]))
        n = max(p["blank"] for p in places) + 1
        per = d["blanks_per_sheet"]
        for s in range(-(-n // per)):
            blanks = []
            for b in range(s * per, min((s + 1) * per, n)):
                blanks.append(dict(
                    name="AB"[b - s * per], size=[B, B],
                    parts=[part(ids, "wb", p["part"], p["l"], p["w"], t,
                                x=r1(p["x"]), y=r1(p["y"]), pl=r1(p["l"]), pw=r1(p["w"]))
                           for p in places if p["blank"] == b]))
            sheets.append(dict(
                id=f"wb-{label}-{s + 1:02d}", project="Workbench fleet", stock=stock,
                title=f"Workbench {label} sheet {s + 1}", method=method, source=src,
                prep=[dict(id=f"wb-{label}-{s + 1:02d}-x1",
                           text=prep.format(B=B, Bin=mm_in(B)))],
                blanks=blanks))

    blank_sheets(d["birch"], "bb18-4x8", d["t18"], "18mm", "CNC",
                 "Track saw: crosscut the 4x8 in half into two {Bin} ({B:.0f}mm) square blanks, A and B.")
    blank_sheets(d["thin"], "bb5-4x8", d["t_thin"], "5mm", "CNC",
                 "Track saw: crosscut the 4x8 in half into two {Bin} ({B:.0f}mm) square blanks, A and B.")

    # MDF: plain rectangles, track saw only. Layers per sheet from bom.mdf_sheets.
    L, D = d["top_l"], d["top_d"]
    left = d["mdf_layers"]
    for s in range(d["mdf_sheets"]):
        k = min(d["mdf_per_sheet"], left)
        left -= k
        sid = f"wb-mdf-{s + 1:02d}"
        steps = [f"Rip the sheet to {mm_in(L)} ({L:.0f}mm) wide."]
        steps += [f"Crosscut {mm_in(D)} ({D:.0f}mm) off the end, piece {i + 1}." for i in range(k)]
        sheets.append(dict(
            id=sid, project="Workbench fleet", stock="mdf19-4x8", title=f"Workbench MDF top sheet {s + 1}",
            method="TRACK SAW", source=src,
            prep=[dict(id=f"{sid}-s{i + 1}", text=t) for i, t in enumerate(steps)],
            blanks=[dict(name="", size=[2438.4, 1219.2],
                         parts=[part(ids, "wb", "top_layer", L, D, d["t_mdf"],
                                     x=r1(i * (D + 3.2)), y=0.0, pl=r1(D), pw=r1(L))
                                for i in range(k)])]))
    return sheets


# ------------------------------------------------------------------ cnc station


def station(ids: Ids) -> list[dict]:
    d = run(FAB, FAB_SNIPPET)
    src = f"fabrication@{sha(FAB)}"
    sheets: list[dict] = []
    for s in d["sheets"]:
        w, h = s["size"]
        stock = "bb12-5x5" if abs(w - h) < 1 else "bb12-4x8"
        sid = f"st-12mm-{s['index']:02d}"
        steps: list[str] = []
        if s["kind"] == "TRACK SAW":
            for p in s["parts"]:
                steps.append(f"Track saw: cut {p['part']} out whole, {mm_in(max(p['l'], p['w']))} x "
                             f"{mm_in(min(p['l'], p['w']))}. The rest is offcut.")
        else:
            shelves = s["shelves"]
            for i, sh in enumerate(shelves[1:], start=1):
                y = sh["y"] - d["gap"] / 2
                steps.append(f"Rip the full length at {mm_in(y)} ({y:.0f}mm) from the bottom long edge, "
                             f"between strip {i} and strip {i + 1}.")
            for i, sh in enumerate(shelves):
                for x in sh["rips"]:
                    steps.append(f"Strip {i + 1}: crosscut at {mm_in(x)} ({x:.0f}mm) from the left end.")
            steps.append("Each piece is one Shapeoko blank. Load the sheet's DXF and cut the parts.")
        sheets.append(dict(
            id=sid, project="CNC station", stock=stock,
            title=f"CNC station sheet {s['index']}" + (" (spine, 5x5)" if stock == "bb12-5x5" else ""),
            method="TRACK SAW" if s["kind"] == "TRACK SAW" else "CNC", source=src,
            dxf=f"export/cnc_shapeoko/nest/sheet_{s['index']:02d}.dxf",
            prep=[dict(id=f"{sid}-s{i + 1}", text=t) for i, t in enumerate(steps)],
            blanks=[dict(name="", size=[w, h],
                         parts=[part(ids, "st", p["part"], p["l"], p["w"], s["t"],
                                     x=r1(p["x"]), y=r1(p["y"]), pl=r1(p["l"]), pw=r1(p["w"]))
                                for p in sorted(s["parts"], key=lambda p: (p["y"], p["x"]))])]))
    return sheets


def main() -> int:
    ids = Ids()
    sheets = workbench(ids) + station(ids)
    stock = {k: dict(label=v[0], t=v[1], size=list(v[2]), on_hand=v[3], status=v[4],
                     needed=sum(1 for s in sheets if s["stock"] == k))
             for k, v in STOCK.items()}
    doc = dict(generated=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               sources=sorted({s["source"] for s in sheets}), stock=stock, sheets=sheets)
    OUT.parent.mkdir(exist_ok=True)
    new = json.dumps(doc, indent=1)
    old = OUT.read_text() if OUT.exists() else ""
    strip = lambda t: t.split("\n", 2)[-1] if t else t      # ignore the timestamp line
    OUT.write_text(new + "\n")
    page = (FAB / "cutlist" / "template.html").read_text().replace(
        "__PARTS_JSON__", json.dumps(doc, separators=(",", ":")).replace("</", "<\\/"))
    PAGE.write_text(page)
    n = sum(len(b["parts"]) for s in sheets for b in s["blanks"])
    print(f"cutlist: {len(sheets)} sheets, {n} parts -> {OUT.relative_to(FAB)}")
    for k, v in stock.items():
        flag = "" if v["needed"] <= v["on_hand"] else f"  SHORT {v['needed'] - v['on_hand']}"
        print(f"  {v['label']}: {v['needed']} needed, {v['on_hand']} on hand ({v['status']}){flag}")
    if strip(old) and strip(old) != strip(new + "\n"):
        print("  parts changed since the last run: commit parts.json and republish the page")
    # the student-writable Google Sheet, if this machine has one (scripts/cutlist_gsheet.py)
    sys.path.insert(0, str(Path(__file__).parent))
    import cutlist_gsheet
    if cutlist_gsheet.CONF.exists() and "--no-sheet" not in sys.argv:
        print(f"  sheet: {cutlist_gsheet.sync(doc)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
