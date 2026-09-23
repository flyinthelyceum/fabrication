"""The student-writable cut list: a Google Sheet on Jared's Brophy Drive.

    .venv/bin/python scripts/cutlist_sync.py                  # JSON + page + Sheet
    .venv/bin/python scripts/cutlist_gsheet.py --create ROSTER.json   # once

WHY A SHEET
===========

The Shop Cut List page (claude.ai) only takes ticks from people in Jared's
claude.ai organization. Students have Brophy Google accounts, so the Sheet is
where they tick a part and put their name. The page stays as the shop-screen
board.

WHAT THE SYNC OWNS, AND WHAT IT NEVER TOUCHES
=============================================

One tab per project. Every row is keyed by its id in column M (a part id from
parts.json, a prep-step id, or a sheet id for the grey header rows). Students
own five columns: A (Cut), E (Cut by), F (Date), G (Needs recut), H (Note).
The sync reads those by id before it writes and puts them back on the same id,
so a re-nest that reorders rows never loses a tick. If the rows are unchanged
it writes only the columns it owns, so a student ticking during a sync is
never overwritten.

A part ticked at one size whose size then changes in the model gets a note in
column O ("cut at 600x400x18, model now ..."). A ticked part that leaves the
model is kept at the bottom of its tab under "No longer in the model", so the
record of who cut what is never deleted.

WHERE THE IDS LIVE
==================

The Sheet id is in ~/.config/labnode/cutlist_sheet.json, not in this repo:
fabrication is public, and the Sheet holds student names. The roster is
written to a hidden Roster tab once, at --create, and never read from the repo.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FAB = Path(__file__).resolve().parents[1]
PARTS = FAB / "cutlist" / "parts.json"
CONF = Path.home() / ".config" / "labnode" / "cutlist_sheet.json"
TOKENS = Path.home() / ".config" / "google-drive-mcp" / "tokens.json"
KEYS = Path.home() / ".config" / "google-drive-mcp" / "gcp-oauth.keys.json"
OWNER = "jreasy@brophyprep.org"
IC_FOLDER = "1p4JPsxnCyQ9othTi-dEk47YVIWXoCDbI"      # Brophy Drive: IC
TITLE = "Shop Cut List (sheet goods)"

HEAD = ["Cut", "Part", "Size (in)", "Size (mm)", "Cut by", "Date", "Needs recut", "Note",
        "Sheet", "Method", "Material", "Qty", "ID", "Kind", "Flag"]
STUDENT = [0, 4, 5, 6, 7]                   # A E F G H, never overwritten
NCOL = len(HEAD)
TABS = {"Workbench fleet": "Workbench", "CNC station": "CNC station"}

# ------------------------------------------------------------------ google


def token() -> str:
    """A fresh access token for the Brophy account, refreshed in memory."""
    acct = json.loads(TOKENS.read_text())["accounts"]["default"]
    k = json.loads(KEYS.read_text())["installed"]
    body = urllib.parse.urlencode(dict(client_id=k["client_id"], client_secret=k["client_secret"],
                                       refresh_token=acct["refreshToken"],
                                       grant_type="refresh_token")).encode()
    r = urllib.request.urlopen(urllib.request.Request(k["token_uri"], data=body), timeout=20)
    return json.loads(r.read())["access_token"]


class G:
    def __init__(self) -> None:
        self.tok = token()

    def call(self, url: str, body: dict | None = None, method: str | None = None) -> dict:
        req = urllib.request.Request(
            url, data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.tok}", "Content-Type": "application/json"},
            method=method or ("POST" if body is not None else "GET"))
        try:
            return json.loads(urllib.request.urlopen(req, timeout=60).read() or b"{}")
        except urllib.error.HTTPError as e:
            sys.exit(f"google api {e.code}: {e.read().decode()[:1500]}")

    def sheets(self, sid: str, path: str = "", body: dict | None = None, **q) -> dict:
        qs = ("?" + urllib.parse.urlencode(q, doseq=True)) if q else ""
        return self.call(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}{path}{qs}", body)

    def batch(self, sid: str, reqs: list[dict]) -> dict:
        return self.sheets(sid, ":batchUpdate", {"requests": reqs}) if reqs else {}


# ------------------------------------------------------------------ rows


def mat(doc: dict, stock: str) -> str:
    return doc["stock"][stock]["label"]


def rows_for(doc: dict, project: str) -> list[list]:
    """The rows the sync owns, in order. Student columns are left blank here."""
    out: list[list] = []
    for s in doc["sheets"]:
        if s["project"] != project:
            continue
        st = doc["stock"][s["stock"]]
        wait = "" if st["on_hand"] > 0 else f"  WAITING: {st['status']}"
        out.append(["", f"{s['title']}  ·  {s['method']}  ·  {st['label']}{wait}", "", "", "", "",
                    "", "", s["id"], s["method"], st["label"], "", s["id"], "sheet", ""])
        for i, p in enumerate(s["prep"], start=1):
            out.append([False, f"Step {i}: {p['text']}", "", "", "", "", False, "", s["id"],
                        s["method"], "", "", p["id"], "prep", ""])
        for b in s["blanks"]:
            for p in b["parts"]:
                name = p["name"] + (f"  (blank {b['name']})" if b["name"] else "")
                out.append([False, name, p["size_in"], f"{p['l']:g} x {p['w']:g} x {p['t']:g}",
                            "", "", False, "", s["id"], s["method"], mat(doc, s["stock"]), 1,
                            p["id"], "part", p["geom"]])
    return out


def merge(new: list[list], old: dict[str, list]) -> list[list]:
    """Put each old row's student columns back on its id; flag size changes;
    keep ticked parts that left the model."""
    seen = set()
    for r in new:
        rid = r[12]
        seen.add(rid)
        o = old.get(rid)
        if not o or r[13] == "sheet":
            continue
        for c in STUDENT:
            r[c] = o[c]
        was = o[14] if o[13] == "part" else ""
        cut = o[0] is True or str(o[0]).upper() == "TRUE"
        if r[13] == "part":
            if cut and was and not was.startswith("cut at") and was != r[14]:
                r[14] = f"cut at {was}, model now {r[14]}"
            elif str(was).startswith("cut at"):
                r[14] = was if was.endswith(r[14]) else f"{was.split(',')[0]}, model now {r[14]}"
    gone = [o for rid, o in old.items()
            if rid not in seen and o[13] in ("part", "prep") and any(o[c] not in ("", False, "FALSE") for c in STUDENT)]
    if gone:
        new.append(["", "No longer in the model (kept for the record)", "", "", "", "", "", "",
                    "", "", "", "", "gone", "sheet", ""])
        new.extend(gone)
    return new


def as_cells(row: list) -> list:
    return ["" if v is None else v for v in row]


def a1(tab: str, cells: str) -> str:
    return urllib.parse.quote(f"'{tab}'!{cells}")


def read_tab(g: G, sid: str, tab: str) -> list[list]:
    v = g.sheets(sid, f"/values/{a1(tab, 'A2:O')}", valueRenderOption="UNFORMATTED_VALUE")
    rows = v.get("values", [])
    return [r + [""] * (NCOL - len(r)) for r in rows]


# ------------------------------------------------------------------ format


def rng(tid: int, r0: int, r1: int, c0: int = 0, c1: int = NCOL) -> dict:
    return dict(sheetId=tid, startRowIndex=r0, endRowIndex=r1, startColumnIndex=c0, endColumnIndex=c1)


def format_tab(g: G, sid: str, tid: int, rows: list[list], roster_n: int, fresh: bool) -> None:
    n = len(rows) + 1
    reqs: list[dict] = []
    if fresh:
        widths = [44, 260, 120, 130, 150, 90, 70, 160, 110, 90, 200, 40, 170, 60, 220]
        reqs += [dict(updateDimensionProperties=dict(
            range=dict(sheetId=tid, dimension="COLUMNS", startIndex=i, endIndex=i + 1),
            properties=dict(pixelSize=w), fields="pixelSize")) for i, w in enumerate(widths)]
        reqs.append(dict(updateSheetProperties=dict(
            properties=dict(sheetId=tid, gridProperties=dict(frozenRowCount=1, frozenColumnCount=2)),
            fields="gridProperties.frozenRowCount,gridProperties.frozenColumnCount")))
        reqs.append(dict(repeatCell=dict(range=rng(tid, 0, 1), cell=dict(userEnteredFormat=dict(
            textFormat=dict(bold=True, foregroundColor=dict(red=1, green=1, blue=1)),
            backgroundColor=dict(red=.15, green=.15, blue=.15))), fields="userEnteredFormat")))
        # grey when cut, red when a recut is needed (red wins: it is added first)
        for formula, color, idx in [("=$G2=TRUE", dict(red=.96, green=.78, blue=.76), 0),
                                    ("=$A2=TRUE", dict(red=.85, green=.85, blue=.85), 1),
                                    ('=$N2="sheet"', dict(red=.93, green=.9, blue=.82), 2)]:
            reqs.append(dict(addConditionalFormatRule=dict(index=idx, rule=dict(
                ranges=[rng(tid, 1, 2000)],
                booleanRule=dict(condition=dict(type="CUSTOM_FORMULA", values=[dict(userEnteredValue=formula)]),
                                 format=dict(backgroundColor=color,
                                             textFormat=dict(bold=idx == 2)))))))
        # ID, Kind, Flag-geometry columns are bookkeeping: hide Kind
        reqs.append(dict(updateDimensionProperties=dict(
            range=dict(sheetId=tid, dimension="COLUMNS", startIndex=13, endIndex=14),
            properties=dict(hiddenByUser=True), fields="hiddenByUser")))
    # per-row validation: checkboxes on part/prep rows, roster dropdown, date
    reqs.append(dict(setDataValidation=dict(range=rng(tid, 1, 2000, 0, NCOL))))  # clear
    tick = dict(condition=dict(type="BOOLEAN"))
    who = dict(condition=dict(type="ONE_OF_RANGE", values=[dict(userEnteredValue=f"=Roster!$A$1:$A${roster_n}")]),
               strict=False, showCustomUi=True)
    day = dict(condition=dict(type="DATE_IS_VALID"), strict=False)
    for i, r in enumerate(rows, start=1):
        if r[13] == "sheet":
            continue
        for c, rule in [(0, tick), (6, tick), (4, who), (5, day)]:
            reqs.append(dict(setDataValidation=dict(range=rng(tid, i, i + 1, c, c + 1), rule=rule)))
    reqs.append(dict(repeatCell=dict(range=rng(tid, 1, n, 5, 6), cell=dict(userEnteredFormat=dict(
        numberFormat=dict(type="DATE", pattern="ddd m/d"))), fields="userEnteredFormat.numberFormat")))
    reqs.append(dict(repeatCell=dict(range=rng(tid, 1, n, 1, 2), cell=dict(userEnteredFormat=dict(
        wrapStrategy="WRAP")), fields="userEnteredFormat.wrapStrategy")))
    g.batch(sid, reqs)


def protect(g: G, sid: str, tid: int) -> None:
    """Students may edit only Cut, Cut by, Date, Needs recut and Note."""
    meta = g.sheets(sid, fields="sheets(properties.sheetId,protectedRanges)")
    reqs = [dict(deleteProtectedRange=dict(protectedRangeId=p["protectedRangeId"]))
            for s in meta["sheets"] if s["properties"]["sheetId"] == tid for p in s.get("protectedRanges", [])]
    reqs.append(dict(addProtectedRange=dict(protectedRange=dict(
        range=dict(sheetId=tid), description="Only Cut, Cut by, Date, Needs recut and Note are for students",
        unprotectedRanges=[rng(tid, 1, 2000, 0, 1), rng(tid, 1, 2000, 4, 8)],
        editors=dict(users=[OWNER])))))
    g.batch(sid, reqs)


# ------------------------------------------------------------------ progress


def progress(g: G, sid: str, doc: dict) -> None:
    vals = [["Shop Cut List", "", "", ""],
            [f"Parts from {', '.join(doc['sources'])}", "", "", ""],
            ["", "", "", ""],
            ["Project", "Parts cut", "Parts total", "Done"]]
    for proj, tab in TABS.items():
        q = f"'{tab}'"
        r = len(vals) + 1
        vals.append([proj, f'=COUNTIFS({q}!$N:$N,"part",{q}!$A:$A,TRUE)', f'=COUNTIF({q}!$N:$N,"part")',
                     f"=IF(C{r}=0,\"\",B{r}/C{r})"])
    vals += [["", "", "", ""], ["Sheet", "Parts cut", "Parts total", "Done"]]
    for s in doc["sheets"]:
        q = f"'{TABS[s['project']]}'"
        r = len(vals) + 1
        st = doc["stock"][s["stock"]]
        label = s["title"] + ("  (waiting on stock)" if st["on_hand"] == 0 else "")
        vals.append([label, f'=COUNTIFS({q}!$I:$I,"{s["id"]}",{q}!$N:$N,"part",{q}!$A:$A,TRUE)',
                     f'=COUNTIFS({q}!$I:$I,"{s["id"]}",{q}!$N:$N,"part")', f"=IF(C{r}=0,\"\",B{r}/C{r})"])
    vals += [["", "", "", ""], ["Stock", "Needed", "On hand", "Status"]]
    for v in doc["stock"].values():
        vals.append([v["label"], v["needed"], v["on_hand"], v["status"]])
    g.sheets(sid, "/values/Progress!A1:D300:clear", {})
    g.call(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/Progress!A1?valueInputOption=USER_ENTERED",
           {"values": vals}, method="PUT")
    tid = tab_ids(g, sid)["Progress"]
    pct = [i for i, r in enumerate(vals) if str(r[3]).startswith("=IF")]
    reqs = [dict(repeatCell=dict(range=rng(tid, i, i + 1, 3, 4), cell=dict(userEnteredFormat=dict(
        numberFormat=dict(type="PERCENT", pattern="0%"))), fields="userEnteredFormat.numberFormat")) for i in pct]
    heads = [i for i, r in enumerate(vals) if r[1] in ("Parts cut", "Needed")] + [0]
    reqs += [dict(repeatCell=dict(range=rng(tid, i, i + 1, 0, 4), cell=dict(userEnteredFormat=dict(
        textFormat=dict(bold=True))), fields="userEnteredFormat.textFormat")) for i in heads]
    reqs.append(dict(updateDimensionProperties=dict(range=dict(sheetId=tid, dimension="COLUMNS",
                     startIndex=0, endIndex=1), properties=dict(pixelSize=320), fields="pixelSize")))
    g.batch(sid, reqs)


# ------------------------------------------------------------------ sync


def tab_ids(g: G, sid: str) -> dict[str, int]:
    meta = g.sheets(sid, fields="sheets.properties")
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}


def sync(doc: dict | None = None, quiet: bool = False) -> str:
    conf = json.loads(CONF.read_text())
    sid = conf["spreadsheet_id"]
    doc = doc or json.loads(PARTS.read_text())
    g = G()
    ids = tab_ids(g, sid)
    roster_n = len(g.sheets(sid, "/values/Roster!A1:A200").get("values", []))
    for proj, tab in TABS.items():
        tid = ids[tab]
        old_rows = read_tab(g, sid, tab)
        old = {r[12]: r for r in old_rows if r[12]}
        rows = merge(rows_for(doc, proj), old)
        same = [r[12] for r in rows] == [r[12] for r in old_rows]
        if same:
            # rows unchanged: write only the columns the sync owns (B-D, I-O)
            data = [dict(range=f"'{tab}'!B2:D{len(rows) + 1}", values=[as_cells(r[1:4]) for r in rows]),
                    dict(range=f"'{tab}'!I2:O{len(rows) + 1}", values=[as_cells(r[8:15]) for r in rows])]
            g.sheets(sid, "/values:batchUpdate", {"valueInputOption": "RAW", "data": data})
        else:
            g.sheets(sid, f"/values/{a1(tab, 'A2:O3000')}:clear", {})
            g.call(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/"
                   f"{a1(tab, 'A1')}?valueInputOption=RAW",
                   {"values": [HEAD] + [as_cells(r) for r in rows]}, method="PUT")
            format_tab(g, sid, tid, rows, roster_n, fresh=not old_rows)
        if not quiet:
            flagged = sum(1 for r in rows if str(r[14]).startswith("cut at"))
            print(f"  sheet tab {tab}: {len(rows)} rows ({'values only' if same else 'rebuilt'})"
                  + (f", {flagged} cut at an old size" if flagged else ""))
    progress(g, sid, doc)
    return f"https://docs.google.com/spreadsheets/d/{sid}/edit"


def create(roster_file: str) -> str:
    names = json.loads(Path(roster_file).read_text())["names"]
    g = G()
    ss = g.call("https://sheets.googleapis.com/v4/spreadsheets", dict(
        properties=dict(title=TITLE),
        sheets=[dict(properties=dict(title=t, index=i)) for i, t in
                enumerate(["Progress", *TABS.values(), "Roster"])]))
    sid = ss["spreadsheetId"]
    # move into Brophy Drive / IC
    g.call(f"https://www.googleapis.com/drive/v3/files/{sid}?addParents={IC_FOLDER}&removeParents=root",
           {}, method="PATCH")
    g.call(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/Roster!A1?valueInputOption=RAW",
           {"values": [[n] for n in names]}, method="PUT")
    ids = tab_ids(g, sid)
    g.batch(sid, [dict(updateSheetProperties=dict(properties=dict(sheetId=ids["Roster"], hidden=True),
                                                  fields="hidden"))])
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps(dict(spreadsheet_id=sid), indent=1) + "\n")
    url = sync()
    for t in TABS.values():
        protect(g, sid, ids[t])
    for t in ("Progress", "Roster"):
        protect_all(g, sid, ids[t])
    return url


def protect_all(g: G, sid: str, tid: int) -> None:
    g.batch(sid, [dict(addProtectedRange=dict(protectedRange=dict(
        range=dict(sheetId=tid), description="Written by the sync script", editors=dict(users=[OWNER]))))])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--create":
        print(create(sys.argv[2]))
    else:
        print(sync())
