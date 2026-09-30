# Stratasys F170 (FDM, F123 series)

- **Model:** F170, part of the Stratasys F123 series (with the F270 and F370). Runs
  GrabCAD Print / GrabCAD Print Pro, Windows 10 or 11 64-bit only, min. 8 GB RAM
  (F170 spec sheet, p.1). Serial/nameplate not recorded here; photograph it next time
  someone's at the machine, same as the Weller entry.
- **Status in the IC: CONFIRMED present.** Jared's voice walk 2026-08-31 ("there's no
  other 3D printers", his exhaustive list) plus the canonical fleet record, which
  explicitly supersedes the `ic.brophyprep.org` site-scrape machine rows:
  `~/projects/canvas-integration/inventory/finalize-2026-08-31/machine-fleet-2026-08-31.md`.
- **uPrint SE Plus: NOT IN THE SHOP.** The same 08-31 walk lists it under "GONE (in
  scrape, explicitly absent from walk's exhaustive printer list)." Any reference to a
  uPrint on the old IC site scrape is stale. Specs kept at the bottom of this file for
  reference only, in case that changes.
- **Manuals:**
  - [F170 product spec sheet](https://www.stratasys.com/siteassets/3d-printers/printer-catalog/fdm-printers/f123-series-printers/brochures/stratasys-F170-spec-sheet-0625a.pdf)
    (PSS_FDM_F170_0625a, 2 pp.), called "F170 spec sheet" below.
  - [FDM Support Removal best-practice guide](https://www.sys-uk.com/wp-content/uploads/2020/06/FDM-Best-Practice-EN-Support-Removal.pdf)
    (BP_FDM_SupportRemoval_0219b, 14 pp.), called "Support Removal guide" below; the
    source for WaterWorks/EcoWorks/tank temperatures.
  - [P400SC WaterWorks concentrate SDS](https://me.berkeley.edu/wp-content/uploads/2020/10/Stratasys-P4000SC-SDS.pdf)
    (SDS-400625, rev. 26-Nov-2017).
  - [ABS-M30 material data sheet](https://me.berkeley.edu/wp-content/uploads/2020/10/ABS-M30-Materials-Data-Sheet.pdf)
    (MSS_FDM_ABSM30_EN_1117a).
  - [PLA material data sheet](https://www.stratasys.com/siteassets/materials/materials-catalog/fdm-materials/pla/mss_fdm_pla_0118a.pdf)
    (MSS_FDM_PLA_0118a).
  - [F123 series troubleshooting guide](https://support.stratasys.com/SupportCenter/HTML5UserGuides/F123_UG_April_2021/Responsive%20HTML5/F123_Series_User_Guide-HTML/Troubleshooting/Troubleshooting.htm)
    (HTML, Stratasys support site).
  - [uPrint SE / SE Plus spec sheet](https://3dprinting.co.uk/wp-content/uploads/2016/07/uPrintSE-uPrint-SE-Plus-Spec-Sheet.pdf)
    (PSS_FDM_uPrintSE_0216a, 4 pp.).

## Build volume, layer heights, materials

| | F170 | uPrint SE Plus (not in shop) |
|---|---|---|
| Build envelope | 254 x 254 x 254 mm (10x10x10 in) | 203 x 203 x 152 mm (8x8x6 in) |
| Layer heights | 0.127 / 0.178 / 0.254 / 0.330 mm | 0.254 or 0.330 mm |
| Model material | PLA, ABS-M30, ASA, ABS-CF10, FDM TPU 92A | ABSplus only, 9 colors |
| Support material | QSR (soluble) or Breakaway (PLA only) | SR-30 (soluble) |

Sources: F170 spec sheet p.1-2; uPrint spec sheet p.3.

A part 242 x 113 x 50 mm fits the F170 (about 12 mm clearance on the long axis).
It does **not** fit the uPrint SE Plus on any axis (max 203 mm) even before accounting
for its GONE status.

**Trap:** on the F170, PLA is only validated at the single 0.254 mm layer height and
takes **breakaway** support only (F170 spec sheet p.2 material table; PLA data
sheet p.3: "Layer Thickness Capability 0.010 in. (0.254mm), Support Structure
Breakaway"). Soluble QSR support requires ABS-M30, ASA, ABS-CF10, or TPU 92A as the
model material (F170 spec sheet p.2). **If the goal is the soluble-bath workflow, the
part has to be sliced in ABS-M30 or ASA. PLA cannot use it.**

## Support removal: QSR dissolves in WaterWorks

- QSR is Stratasys's soluble support material for F-Series printers (F170, F190CR,
  F370, F370CR) only; older machines (uPrint, Dimension) use SR-30 instead (Support
  Removal guide, p.2, footnote 1: "QSR material is used on the F-Series printers only").
- Removal solution: **WaterWorks** concentrate (P400SC), a powder dissolved in water. Composition: sodium carbonate 60-80%, **sodium hydroxide 10-30%**,
  disodium metasilicate 1-3% (P400SC SDS, p.2). Danger-rated, corrosive to skin/eyes;
  fresh solution pH ≈ 12.6 (Support Removal guide, p.12, Table 2-2).
- Tank temperature for SR-35/QSR: **70°C (158°F)** (Support Removal guide, p.9, Table
  2-1).
- Tank: Stratasys recommends a circulation or ultrasonic tank and names the **SCA
  3600** as sized for the F123 series (Support Removal guide, p.6-7). **Not confirmed
  the IC owns one.** No wash or support-cleaning system appears in the 08-31 machine-fleet
  walk or the canonical inventory sheet. Check this before committing to the workflow.
- Typical soak: inspect at 2 hours, then periodically until the clean cycle is done
  (Support Removal guide, p.10); other Stratasys-facing sources put QSR in the 2-4 hour
  range generally. **Parts with thin, deep channels dissolve slower** (p.7), which matters
  for any model with a long enclosed bore. Ultrasonic tanks are named as best for "thin
  channels, small holes and trapped cavities such as tubes" (p.5), but tanks typically
  paired with F123-series printers use circulation (p.6 note), so a long bore
  may run past the typical window.
- Parts must stay fully submerged; they can crack if not fully immersed or if they bob
  in and out (p.9).
- Solution needs replacing when it clouds, browns, or drops below pH 11.5 (p.12). A
  real-world operating page for this exact printer describes running the bath "until it
  is the color of whole milk" before it needs changing
  ([Montana State F170 Printer Basics](https://www.montana.edu/mie/3d_printer_facilities_documents/f170_printer_basics.html)).

**Acetone: do not use it on ABS-M30 parts.** Acetone is a solvent for ABS (ABS is
soluble in ketones). That is the mechanism behind acetone vapor-smoothing, a cosmetic
finishing trick with no role in support removal. Above roughly 50% acetone by
volume it causes hazing and crazing within hours, and direct contact will soften or
dissolve thin walls and fine lattice struts (RapidDirect "ABS Acetone Smoothing" guide;
engineerdog "Effect of Acetone Vapor Polishing on 3D Printed ABS Parts"). The
soluble-support bath itself is the heated WaterWorks solution above; keep acetone away
from the model entirely.

## Workflow: GrabCAD Print

- Import formats: native CAD, STEP, Parasolid, OBJ, 3MF, VRML, STL (GrabCAD Print
  documentation).
- Support material is **auto-selected from the model material**; there is no direct
  soluble-vs-breakaway toggle. Pick ABS-M30 or ASA and GrabCAD Print generates soluble
  QSR support; pick PLA and it generates breakaway support (Stratasys "Adjusting FDM
  print settings" support page). Manual override only applies when a given model
  material has more than one compatible support option.
- Draft Mode is the PLA/breakaway-oriented speed setting: sparse fill, less support,
  built to make **manual** support removal faster, and it never produces soluble support
  (same source).
- Common failure modes, from the F123 series troubleshooting guide:
  - "Out of model material" / "Out of support material": one or both spools empty.
  - "Amount of support material currently installed... not sufficient for the selected
    build": checked before the job starts; load a full spool if this flags.
  - "Support material currently installed does not match the support material
    configuration of the selected job": wrong support spool loaded for the chosen
    model material.
  - Spool mixups (axles swapped between spools) can make the system misread breakage as
    depletion.

## ABS-M30 vs PLA (F170)

| | ABS-M30 | PLA |
|---|---|---|
| Specific gravity | 1.04 | 1.264 |
| Tensile modulus | 2,230 MPa (XZ) / 2,180 MPa (ZX) | 3,039 MPa (XZ) / 2,539 MPa (ZX) |
| Tensile strength, ultimate | 32 MPa (XZ) / 28 MPa (ZX) | 48 MPa (XZ) / 26 MPa (ZX) |
| Elongation at break | 7% (XZ) / 2% (ZX) | 2.5% (XZ) / 1.0% (ZX) |
| IZOD impact, notched | 128 J/m | 27 J/m |
| IZOD impact, unnotched | 300 J/m | 192 J/m |
| Support on F170 | Soluble (QSR) | Breakaway only |

Sources: ABS-M30 data sheet p.1-2; PLA data sheet p.2-3.

PLA is stiffer (higher tensile modulus) and denser, but ABS-M30 absorbs more than 4x
the impact energy before failing (notched IZOD) and stretches about 3x further before
breaking. For a part built to survive impacts, ABS-M30's toughness is the more relevant
number; how much of that the printed lattice actually keeps depends heavily on wall
count and print orientation, which these sheet values don't capture on their own.

## Print time: rough estimate only

Stratasys's own F123-series **standard-mode** STL build-speed figure is **0.91 in³/hr
(≈14.9 cm³/hr)**, quoted against the older Fortus 250mc (49% faster in standard mode,
98% faster in PLA draft mode), relayed via 3dprintingindustry.com's writeup of
Stratasys's F123 comparison spec and unverified against a Stratasys PDF. For a
lattice with **60-80 cm³ of model plus a similar volume of support**, total deposited
volume runs roughly 120-160 cm³:

- If the throughput figure is a **model-only** rate: about 4-5.5 hours.
- If it's closer to a **total deposited-volume** rate (more realistic for a
  support-heavy organic lattice): about 8-11 hours.

**Call it 8-10 hours as the planning number, plus wash time.** That lines up in
order of magnitude with the AD5M PLA halves plan's own dry-run slice (8h33m for a
similarly support-heavy print, 51% support by mass, per `project_cirin_car` memory),
different machine, similar shape of problem. This F170 figure is a **labeled estimate**,
not a measured run of this specific file.

---

## uPrint SE Plus (reference only: gone from the shop)

- Build size 203 x 203 x 152 mm (8x8x6 in); layer height 0.254 mm or 0.330 mm; model
  material ABSplus only, in 9 colors; support SR-30, soluble (uPrint spec sheet, p.3).
- Uses **CatalystEX** software, an older and simpler slicer than GrabCAD Print, STL in
  (uPrint spec sheet, p.4).
- Support removal: **WaveWash** tank + **EcoWorks** cleaning agent, a different
  system from the F170's SCA/WaterWorks setup (uPrint spec sheet, p.2, p.4). EcoWorks
  runs slower than WaterWorks; other sources put SR-30's best-dissolve range at
  70-75°C and warn that temperatures above about 75°C can distort parts (search-sourced
  only and unverified against a Stratasys PDF page, so lower confidence than the F170
  figures above).
- Moot for a 242 mm part regardless of chemistry: that exceeds every uPrint SE Plus
  axis (max 203 mm), and the machine is GONE per the 08-31 walk.
