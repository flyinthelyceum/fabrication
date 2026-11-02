# Shapeoko 5 Pro

- **Machine:** Shapeoko 5 Pro with the 65 mm VFD spindle, the CNC station's machine.
- **Console PC:** `cnc-station-02`, running Carbide Motion. The Shapeoko shows up as
  `/dev/ttyACM0` and the jog pendant as `/dev/ttyACM1`.
- **Manuals:** [Carbide 3D docs](https://docs.carbide3d.com/) and
  [troubleshooting homing](https://qr.carbide3d.com/error/hm009).

Unlike the other files here, the wiring below is not from a maker's manual. We found no
published pinout, so it was traced at the machine with a meter on 2026-10-30.

## Power pendant wiring

![Wiring from the E-stop and feed hold bundles to the J2 connector](shapeoko-5-pro-pendant-wiring.svg)

**J1, E-stop, 3 wire**

| Wire | Terminal | Signal |
|---|---|---|
| White | C | ES2 |
| Blue | NO | ES1 |
| Green | NC | marked Δ |

**J3, feed hold, 5 wire**

| Wire | Terminal | Signal |
|---|---|---|
| Black | C | GND |
| Red | NC | |
| Blue | NO | |
| Green | 1 | VIN |
| Yellow | D | FH |

**J2, 6 wire, pendant back to the machine.** Positions count top to bottom, left to right,
facing the "POWER PENDANT" inside labeling.

| Position | Signal |
|---|---|
| 1 | ES2 |
| 2 | FH |
| 3 | GND |
| 4 | VIN |
| 5 | ES1 |
| 6 | GND |

**Still untraced:** where J1 Green goes, where J3 Red and Blue go, what terminals 1 and D
belong to, and which GND position J3 Black lands on.

## Open fault: HM009, GRBL Alarm 9 (2026-10-30)

The machine connects, then homing fails about 10 seconds in. The gantry LEDs stay off and
the axes do not move. Carbide Motion's log shows `Pn:PH` (probe and feed hold inputs both
active) with the Z count reaching 232.5.

| Check | Reading |
|---|---|
| J1 White to Green | Closed in both button positions: the E-stop is stuck latched |
| J3 Black to Red | Closed released: the switch works |
| J3 Black to Blue | Closed pressed: the switch works |
| J3 Green or Yellow to those contacts | No continuity in either position |
| J1 White to Blue (J2 position 1 to 5) | Not yet metered in both positions |

**Cause (2026-10-30):** the E-stop will not mechanically release, so it is latched pressed.
Replacement: Gebildet 22 mm 2NO 2NC latching E-stop, 6 blade terminals, Amazon B094FBG1MB.

**Fitting the replacement:** do not copy the old terminal labels across. Wire ES1 and ES2 to
one pole so that J2 position 1 to 5 reads closed released and open pressed, confirm that with
a meter before power, then confirm pressing the button stops the machine.

**Log reading, 2026-11-02 (journal on `cnc-station-02`, after both switches were reworked).** Alarm 9 is unchanged: Z counts to 232.5, X and Y stay at 0. Feed hold is not the cause. The first homing attempt on 10-30 (08:16) and today's (12:44) both failed with `Pn:P` alone, no H. `P` was absent at idle through 10-29, appeared at the 10-30 power-up and has been on in every status line since. H first appeared 10-30 08:27, in the same stretch the pendant was being traced, and has toggled in and out today, so the FH line reaches the controller.

Inference, not metered: a stuck `P`, no motion and dark gantry LEDs share one cause, the E-stop loop or the rail it switches still being dead. H reads active when the FH line is open (10-30 timing), which would make FH fail-safe: released must hold it closed. J3 Black is GND and terminal 1 is VIN, so tying common to 1 shorts VIN to GND through a closed contact. No `$14` or other settings appear in the journal, so the polarity is not read from firmware.

**Traced 2026-11-02, supersedes the J3 table above.** Continuity to J2, power off: J3 Black = position 2 (FH). J3 Yellow = positions 3 and 6 (GND). J3 Green = position 4 (VIN). J3 Blue = positions 3 and 6 (GND). J3 Red = nothing. J1 White = position 1 (ES2). Terminals 1 and D are probably the button backlight (inference). Feed hold wiring: Black on C, Blue on NO, Green and Yellow on 1 and D, Red spare. The ES1 connector at J2 position 5 was loose and intermittently open; Jared tightened it 11-02, and positions 1 to 5 now read closed released, open pressed. The loop reads 0 V closed and 3.3 V open, so it is a low-voltage signal. VIN read 13.9 to 14.7 V and did not change with the E-stop; correct level unknown.

After that fix the fault remained: Main Power and Machine On lit, front C logo lit, gantry LEDs dark, X and Y slide freely, `Pn:P` steady. The USB link to the station has not dropped since 10-30 10:02 through several machine power-offs, so the controller stays alive on USB and can connect and count Z with the motors unpowered (inference).

**Traps:**
- Do not jumper ES1 to ES2 or bypass the E-stop to test or to run. Mains work and the
  interlock are Mr. Reasy's alone.
- Do not unlock past the alarm with `$X` to run a job. An unhomed machine has no reference.
- J3 Green and Yellow showing no continuity to the contacts is not by itself a fault.


**Step 14, 2026-11-02 16:00.** Initialize produced no motion at all. Going into the control box. Carbide publishes no teardown; the forum knows only that the board is called the Warthog, with an ESP32, a 328p running Grbl, and a reported 24V 2.6A fuse on the AUX port. Correction: USB did drop today at 15:45 and 16:01, both during our reseating and unplugging, so the "never dropped" note holds only through 15:44. The Carbide 5.1 Pro assembly guide is in Drive at My Drive/IC/CNC Station 2026 (id 1YfQRNmvPAUUoKE_ugUIEqYutmEx_A7u5); it warns that pushing the gantry fast back-feeds the board, and the red controller LED lighting while moved by hand is the sign. Warranty: 18 months, excludes damage from repairs tried outside Carbide, void on modifying electronics. Purchase date not on file.
