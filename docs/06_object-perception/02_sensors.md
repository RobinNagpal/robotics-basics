# The sensors, and the software for each

What you can identify and what you can measure are both decided first by the
instrument. This document is the instruments: what each kind of sensor gives you,
how each one fails, what accuracy you can actually expect, the library you talk
to it with, the ROS 2 package that wraps it — and the two things without which
none of those numbers mean anything, which are the calibration and the frame each
reading arrives in.

The accuracy figures are the manufacturers' own published specifications, checked
against their data sheets in September 2026. They are specifications, not what
you will get on a bad day.

## Contents

1. [What each sensor gives you](#1-what-each-sensor-gives-you)
2. [Measuring by touch](#2-measuring-by-touch)
3. [Event, thermal and polarisation cameras](#3-event-thermal-and-polarisation-cameras)
4. [Calibration, which decides all of it](#4-calibration-which-decides-all-of-it)
5. [Frames, and which one a reading is in](#5-frames-and-which-one-a-reading-is-in)

---

## 1. What each sensor gives you
If you are going to measure the distance rather than infer it, this is what you
can buy. The numbers below are the manufacturers' own published figures, checked
against their data sheets in September 2026, and they are specifications rather
than what you will get on a bad day.

| Sensor | How it works | Published accuracy | Roughly |
| --- | --- | --- | --- |
| [RealSense D405](https://www.realsenseai.com/products/stereo-depth-camera-d405/) | **passive** stereo, close range — see [the wrist camera, §7](08_the-wrist-camera.md) | ±2% at 50 cm on a *textured* target, works from 7 cm | a few hundred pounds |
| [RealSense D435i](https://www.realsenseai.com/products/depth-camera-d435i/) | active stereo, general purpose | under 2% at 2 m; RMS about 2 mm at 1 m | a few hundred pounds |
| [Orbbec Gemini 335L](https://store.orbbec.com/products/gemini-335l) | active stereo, IP65 | 0.8% at 2 m, 1.6% at 4 m | a few hundred pounds |
| [Orbbec Femto Bolt](https://www.orbbec.com/products/tof-camera/femto-bolt/) | time of flight | systematic error under 11 mm plus 0.1% of distance | a few hundred pounds |
| [Zivid 2+](https://www.zivid.com/) | structured light | **±0.2 mm on a 100 mm distance at 1 m** | quote only, thousands |
| [Photoneo PhoXi L](https://photoneo.com/products/phoxi-scan-l/) | structured light | point-to-point 0.524 mm, temporal noise 0.19 mm | quote only, thousands |
| [Keyence LJ-X8000](https://www.keyence.com/products/measure/laser-2d/lj-x8000/) | laser profile | single-digit micrometres per point | quote only, thousands |
| [Livox Mid-360](https://www.livoxtech.com/mid-360) | scanning LiDAR | 3 cm at 0.2 m — see [1.2](#12-lidar-and-why-it-is-almost-never-on-the-arm) | a few hundred pounds |
| [ST VL53 family](https://www.adafruit.com/product/5425) | one-point time of flight | a few mm over centimetres, in one direction only | a few pounds |

The gap between rows four and five of that table is the whole story of this
field. A consumer depth camera gets you to a few millimetres; an industrial
scanner gets you to a fifth of a millimetre and costs twenty times as much. Which
you need is decided by the tolerance of the job, and most table-top robot jobs are
genuinely happy in the first group.

Two pieces of news from 2025 and 2026 matter if you are choosing hardware now.
Intel spun RealSense out as an independent company in July 2025, and on 22
September 2026 Cognex agreed to acquire it for $500 million, with the deal
expected to close in the last quarter of 2026 — the terms are in [Cognex's own
filing with the Securities and Exchange
Commission](https://www.sec.gov/Archives/edgar/data/0000851205/000085120526000071/cgnx-20260922.htm). The
code has moved with it: `IntelRealSense/librealsense` now redirects to
[`realsenseai/librealsense`](https://github.com/realsenseai/librealsense), which is
still Apache-2.0 and still actively developed. The practical effect is that the
cheap hobbyist depth camera and the expensive industrial vision vendor are about
to be the same company.

### 1.1 How the four sensing principles fail

Every one of these sensors has a characteristic failure, and knowing which one you
are buying matters more than the accuracy figure.

**Passive stereo** matches features between two ordinary cameras. It works in
sunlight and costs almost nothing, and it fails completely on a blank wall,
because there is nothing to match.

**Active stereo** — most of the RealSense and Orbbec Gemini families — projects a
speckle pattern so that a blank surface has texture to match. The D405 is the
exception and is worth singling out, because it is the one most often put on a
wrist: its depth module has no infrared projector and carries an infrared-cut
filter, so it is *passive*, and its published accuracy is measured on a textured
target where the active models are measured on blank white. A featureless surface
100 mm from the lens returns nothing. That fixes the textureless
case and leaves the others: the pattern goes straight through transparent things,
bounces away from mirrored ones, and is washed out by strong sunlight.

**Structured light** — Zivid, Photoneo — projects a coded pattern and reads it with
one camera. It is the most accurate of the four by a wide margin. Its particular
weakness is motion: the pattern is captured over several exposures, so anything
that moves during the scan smears.

**Time of flight** times the light's return, so there is no matching problem at
all and blank surfaces are fine. Its particular weakness is multipath: light that
bounces off a mirror or a polished surface on its way back arrives late, is added
to the direct return, and produces a confidently wrong distance. It also produces
"flying pixels" — points floating in mid-air at the edges of objects.

All four share one blind spot. Semi-transparent materials — frosted glass, some
plastics, skin — scatter light beneath the surface, which delays the return for
time of flight and bends the pattern for the triangulating methods.

Five jobs a depth sensor suits:

- measuring opaque, matt objects, which is most of what a factory handles
- finding the work surface, which nearly every other technique then builds on
- obstacle avoidance, where approximate geometry is enough
- bin picking, where you need the shape of a pile and not the identity of it
- giving the scale that a colour camera cannot supply

Five jobs it cannot do:

- glass, clear plastic, and anything transparent
- polished metal, chrome and mirrors
- matt black surfaces, which absorb the projected pattern
- objects smaller than the sensor's resolution at that range
- measuring to better than a millimetre with anything in the consumer group

### 1.2 LiDAR, and why it is almost never on the arm

LiDAR is the sensor people ask about most and the one that fits this job worst,
so it is worth being precise about both halves of that.

**Half of it is already in the table above, under another name.** A time-of-flight
camera *is* a LiDAR — the formal term is *scannerless* LiDAR, because it captures
the whole scene with one pulse instead of sweeping a beam across it point by
point. The Orbbec Femto Bolt is a LiDAR in exactly that sense. If you came here
looking for LiDAR and found "time of flight", you have found it.

**The other half — scanning LiDAR — is built for a different problem.** An
[Ouster OS1](https://ouster.com/products/hardware/os1-lidar-sensor) or a
[Livox Mid-360](https://www.livoxtech.com/mid-360) sweeps a beam over tens of
metres and returns millions of points a second. That is the right instrument for
a vehicle or a mobile robot, and the wrong one for an arm, for a reason the
manufacturers' own numbers make plain.

The Livox Mid-360 specifies a range precision of **≤2 cm at 10 m, and ≤3 cm at
0.2 m** — the close figure is the *worse* of the two, because the sensor is
designed for distance. Put those beside the sensors in the table above, at the
range an arm actually works:

| At roughly a third of a metre | Specified precision |
| --- | --- |
| Livox Mid-360 scanning LiDAR | about 30 mm |
| RealSense D405 depth camera | about 7 mm |
| Zivid 2+ structured-light scanner | about 0.2 mm |

A scanning LiDAR is four times worse than a cheap depth camera and a hundred and
fifty times worse than a scanner, at the only distance that matters to a gripper.
It is also physically large, it usually spins, and several models have a blind
zone that covers most of an arm's workspace.

**Where LiDAR does belong on a robot with an arm is on its base.** The standard
mobile-manipulator design has a LiDAR at ankle height for navigation and obstacle
avoidance, and a depth camera on the wrist for manipulation. Two sensors, two
jobs, and they never do each other's. The ROS 2 drivers are
[velodyne](https://github.com/ros-drivers/velodyne),
[ouster-ros](https://github.com/ouster-lidar/ouster-ros),
[livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2) and
[sick_scan_xd](https://github.com/SICKAG/sick_scan_xd), and what consumes them is
mapping and localisation — [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox)
and friends — not anything in this area of the docs.

Five jobs scanning LiDAR suits:

- navigating the mobile base that carries the arm
- obstacle detection over a whole room, where centimetres are fine
- mapping a work cell once, to know where the fixed furniture is
- outdoor work, where sunlight defeats projected-pattern sensors
- safety-adjacent monitoring of a large area, as a non-rated supplement

Five jobs it cannot do:

- measure an object to millimetres, which is four times beyond its specification
- see anything inside its blind zone, which on many models is the whole workspace
- resolve a small object, since the beam spacing is angular and the object is near
- fit on a wrist, being large, heavy and often rotating
- handle glass or polished metal any better than the cheaper sensors above

### 1.3 Infrared, in four different roles

"IR sensor" covers four unrelated things, and mixing them up is common.

**The projector inside an active stereo camera.** RealSense and Orbbec Gemini
cameras throw an infrared speckle pattern onto the scene so that a blank surface
has texture to match. This is invisible infrared doing the work, and it is why
those cameras behave badly in direct sunlight — daylight contains enough infrared
to wash the pattern out.

**Thermal cameras**, which sense emitted long-wave infrared rather than reflected
light, and therefore measure temperature. They are covered in
[section 3.2](#32-thermal-polarisation-and-the-rest).

**One-point distance sensors.** A chip such as ST's VL53 family
([a typical breakout](https://www.adafruit.com/product/5425),
[driver](https://github.com/stm32duino/VL53L1X)) measures time of flight over a
few centimetres to a few metres, in one direction, for a couple of pounds. On a
gripper these are genuinely useful as *pre-touch* sensors: mounted between the
fingers, one tells you an object is about to be there before the fingers reach
it, which is a cheap check on a camera measurement that might be wrong.

**Photoelectric and break-beam sensors.** An emitter and a detector, and
something has interrupted the beam or it has not.
[Keyence](https://www.keyence.com/products/sensor/photoelectric/) and
[SICK](https://www.sick.com/us/en/catalog/products/detection-sensors/photoelectric-sensors/c/g568801)
sell them by the thousand. These are not perception in the sense of the rest of
these documents — they answer one bit, presence or absence — and enormous amounts
of working industrial automation runs on exactly that bit. A part-present check
before the arm closes costs a few pounds and removes a whole class of failure.

One warning about the fifth role, which is not on this list on purpose.
**[Safety light curtains](https://www.sick.com/us/en/catalog/products/safety/safety-light-curtains/c/g190310)
are also infrared, and they are not something you build.** They are rated
equipment certified to standards such as IEC 61496, wired into a safety relay,
and the certification is the product. An array of hobby IR sensors is not a light
curtain and must never be used as one.

Five jobs infrared sensing suits:

- projecting texture so a stereo camera works on a blank surface
- pre-touch proximity on a gripper, at a cost of a few pounds
- part-present and part-absent checks, which need no vision at all
- counting things passing a point on a conveyor
- detecting temperature differences that no colour camera can see

Five jobs it cannot do:

- work reliably in direct sunlight, which floods the band with its own infrared
- measure the shape of anything, being one point or one bit
- see through or around anything, despite persistent folklore
- act as a safety device unless it is certified equipment wired as such
- give a usable reading off glass, which passes infrared much as it passes light

### 1.4 Where to put the camera

The first decision in any cell, made before any of the choices above, and the one
that quietly determines several of them. There are two places and the trade is
real.

**Eye-in-hand** means the camera is on the wrist. It can be carried to any
viewpoint, so it can look straight down a glass from the side and then from a
quarter turn round; and because resolution depends on how close it gets, it can
have a good look at a small thing by moving nearer. The costs are that the
background changes with every move, which rules out
[background subtraction](03_programmed-methods.md#12-background-subtraction)
entirely; that every picture has to be paired with the arm pose it was taken
from, so the calibration you need is hand-eye; and that moving to look takes
seconds the cell may not have.

**Eye-to-hand** means the camera is fixed, usually above or beside the cell. The
background is constant, so the cheap methods work; nothing has to move before you
can look; and one picture covers the whole workspace. The costs are that the
viewpoint is fixed, so whatever is hidden stays hidden; resolution is fixed too,
so a small object far from the camera is small forever; and the arm itself will
sooner or later be between the camera and the thing you want to see.

| | Eye-in-hand | Eye-to-hand |
| --- | --- | --- |
| background | moves with the camera | constant |
| resolution on a small object | improve it by going closer | fixed |
| occlusion | move to see round it | permanent |
| calibration needed | hand-eye | camera to robot base |
| cheap methods that work | colour, depth clustering | those, plus background subtraction |
| time cost per look | seconds | none |
| the arm gets in the way | never | regularly |

**A great many real cells have both**, and the division of labour is consistent:
the fixed camera finds roughly where things are and decides what to do next, and
the wrist camera goes and looks properly at the one object being worked on. That
is also the structure the [glass case
study](../10_one-arm-training/07_case-study/01_place-glass.md) uses, for exactly
that reason.

Five jobs a wrist camera suits:

- measuring one object properly, from a viewpoint you choose
- looking at the same object twice from different angles, to find a handle
- a final check down the fingers just before they close
- cells too large for one fixed camera to cover usefully
- anything where the object may need to be approached before it can be understood

Five jobs it does not:

- watching the whole cell at once, which is what a fixed camera is for
- anything using background subtraction, which needs a still background
- high-rate work, since every look costs a move
- seeing what the arm is about to collide with, being attached to the arm
- keeping a view of an object while the arm does something else

### 1.5 The software that comes with each sensor

A sensor is only as useful as its driver, and the software is where most of the
practical differences show up. Read this as: the library you talk to the sensor
with, the ROS 2 package that wraps it, and what you would then run on its output.

| Sensor | Library | Licence | ROS 2 driver | What you run on its output |
| --- | --- | --- | --- | --- |
| RealSense D4xx | [librealsense](https://github.com/realsenseai/librealsense) | Apache-2.0 | [realsense-ros](https://github.com/realsenseai/realsense-ros) | [Open3D](https://github.com/isl-org/Open3D) or [PCL](https://github.com/PointCloudLibrary/pcl) for plane fitting and oriented boxes |
| Orbbec Gemini, Femto | [OrbbecSDK v2](https://github.com/orbbec/OrbbecSDK_v2) | MIT | [OrbbecSDK_ROS2](https://github.com/orbbec/OrbbecSDK_ROS2) | the same |
| Zivid | proprietary SDK | closed, with a BSD-3 wrapper | [zivid-ros](https://github.com/zivid/zivid-ros) | the same, plus their own bin-picking tooling |
| Photoneo PhoXi | PhoXi Control, dongle-licensed | closed, MIT wrapper | [PhoXi-ROS-API](https://github.com/photoneo/PhoXi-ROS-API) | the same |
| a plain colour camera | [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 | [usb_cam](https://github.com/ros-drivers/usb_cam), [image_pipeline](https://github.com/ros-perception/image_pipeline) | the geometry in [section 6](03_programmed-methods.md#2-measuring-the-object), or a depth model from [section 7](05_models-that-measure.md#1-depth-from-a-single-picture) |
| a stereo pair | OpenCV `StereoSGBM`, or [RAFT-Stereo](https://github.com/princeton-vl/RAFT-Stereo) | Apache-2.0 / MIT | [image_pipeline](https://github.com/ros-perception/image_pipeline)'s `stereo_image_proc` | as for RGB-D, once you have the disparity |
| a force-torque sensor | [ros2_controllers](https://github.com/ros-controls/ros2_controllers) | Apache-2.0 | `force_torque_sensor_broadcaster` | the probing in [section 2.9](03_programmed-methods.md#29-measuring-by-touching-it) |
| scanning LiDAR | vendor SDK | Apache-2.0 drivers | [velodyne](https://github.com/ros-drivers/velodyne), [ouster-ros](https://github.com/ouster-lidar/ouster-ros), [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2), [sick_scan_xd](https://github.com/SICKAG/sick_scan_xd) | [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) for mapping — not the methods in this area |
| one-point infrared | [VL53L1X driver](https://github.com/stm32duino/VL53L1X) | BSD-3 | read over I2C from a microcontroller | nothing — it is one number |
| a printed marker | [OpenCV ArUco](https://github.com/opencv/opencv), [AprilTag](https://github.com/AprilRobotics/apriltag) | Apache-2.0 / BSD-2 | [ros_aruco_opencv](https://github.com/fictionlab/ros_aruco_opencv), [apriltag_ros](https://github.com/christianrauch/apriltag_ros) | calibration, and the scale trick in [section 6.3](03_programmed-methods.md#24-a-marker-of-known-size) |

Three practical notes that are not obvious from the table.

**On a Mac, use Open3D and not PCL from Python.** PCL's C++ library installs
cleanly through Homebrew with native Apple Silicon builds, but its Python
bindings are dead: `python-pcl` last shipped in 2019 for x86 and Python 3.7, and
`pclpy` is Windows-only. Open3D ships native `arm64` wheels and its
`segment_plane` and `cluster_dbscan` cover the same ground.

**For ArUco and AprilTag in ROS 2, the obvious package is the wrong one.** The
official [AprilRobotics/apriltag_ros](https://github.com/AprilRobotics/apriltag_ros)
has not been touched since 2024; [christianrauch/apriltag_ros](https://github.com/christianrauch/apriltag_ros)
is the maintained one. Similarly the widely linked `pal-robotics/aruco_ros` is
stuck on Humble, and [fictionlab/ros_aruco_opencv](https://github.com/fictionlab/ros_aruco_opencv)
is current.

**The industrial scanners give you ROS 2 but not macOS.** Both the Zivid and
Photoneo wrappers are permissively licensed and both wrap a closed binary
runtime that ships for Windows and Linux only.

## 2. Measuring by touch

Every sensor so far measures light. This one measures contact, and it is worth a
section of its own for two reasons: it is the most accurate instrument an arm
has, and it works on the things that defeat every optical method — glass, chrome,
matt black, and anything in the dark.

**The first thing to be clear about is which part does the measuring.** When an
arm feels its way down and stops on contact, the measurement is not coming from
the touch sensor. It comes from the **joint encoders**, which know where the tool
was at the instant contact was reported. On an industrial arm that is repeatable
to a few hundredths of a millimetre. The touch sensor's only job is to say
*when*. That division matters, because it means a cheap contact switch and an
expensive tactile array give you the same positional accuracy for a guarded move
— what the expensive one buys you is everything in section 2.1 below.

**The second thing is what touch cannot do.** It measures one contact at a time,
over a patch a few millimetres across. It does not measure an object's
dimensions; you build those up by touching repeatedly, which is slow. Treat touch
as the thing that confirms and refines an optical measurement, or replaces it
where optics has no signal at all — not as a survey instrument.

### 2.1 What you can actually do with it

**The guarded move.** Drive slowly in one direction until a force threshold or a
contact sensor fires, and record the pose. This is the oldest measuring technique
in robotics and still the most accurate. It is how you find the true height of a
work surface, the top of a stack, or the bottom of a bore.

**Check that the sensor you are waiting on can actually fire.** This sounds
trivial and is the most common way a guarded move fails silently. Sensors on the
gripper pads detect what the *pads* touch. Lower a held object onto a surface and
the pads touch nothing whatever — the object's own base does. The descent then
runs its full travel, reports that it found nothing, and gives up, while the
object has been standing on the surface for the last forty millimetres.

The signal that does fire is the one on the other side of the problem: **the load
leaving the wrist.** When the surface takes the weight, the force sensor stops
reading it. So the rule is to watch the sensor that observes the *event you care
about*, which for setting something down is the transfer of weight and not a
touch at all.

**And contact is not support.** Having established that something touched, you
have not established that it is being held up. An object whose rim has caught on
the lip of a fixture registers a perfectly good contact while still hanging
entirely from the gripper, and opening the fingers then drops it. Before
releasing anything, confirm the weight has actually gone: the wrist should be
back to reading the gripper alone. That check costs nothing and is the difference
between a placement and a drop.

**Weighing what is held.** A wrist force sensor reads everything below it, so
subtracting the known weight of the gripper leaves the payload. This is the only
way to learn the mass of an object whose wall thickness you cannot see, which is
exactly the problem the [glass case
study](../10_one-arm-training/07_case-study/01_place-glass.md) has: it lifts each
glass ten millimetres and weighs it before committing to a squeeze.

**And the sentence above is a trap as it stands.** "Everything below it" is only
true along the world vertical, and a force sensor reports in the *tool's* frame.
Point the tool straight down and the two agree, which is why this works in the
first demonstration anybody writes. Grasp from the side — the tool's reach axis
now horizontal — and gravity pulls across the sensor's axis rather than along it,
so the naive reading of the tool's own z is **zero**. Every object weighs nothing,
convincingly, and the bug survives a long time because nothing errors.

The fix is one line and it is not optional: rotate the measured wrench — the six
numbers of a force and a torque taken together, which is what a six-axis sensor
produces — into the world frame with the tool's current orientation, then take the
world-vertical component.

    weight = (R_tool_to_world · f_measured) · [0, 0, 1]

Do that and the answer is right whatever angle the wrist is at, which also means
you may weigh the object in whatever pose the grasp happened to need. This is one
instance of a general problem, and
[section 5](#5-frames-and-which-one-a-reading-is-in) treats it properly.

**Filtering the reading, which needs more than you would think.** A wrist sensor
watched during a grasp is not a quiet signal. Closing the fingers, starting a
move and stopping one all put transients through it that are many times the
payload — a real trace went from 0 g to 9577 g and back inside a fraction of a
second, on an object weighing 200 g. A single sample taken at the wrong instant
is worse than no measurement, because it is a plausible number.

Take the **median of a few dozen samples** — around 32 at 100 Hz, so a third of a
second — with the arm held still. The median rather than the mean, because these
are spikes rather than noise, and a mean is dragged by one of them while a median
ignores it entirely. Then weigh only when the arm has settled, which is a good
reason to make the weighing a deliberate pause rather than something read on the
move. [Section 2.6](#26-conditioning-a-force-or-contact-reading) works through how
to choose that window and what the choice costs you.

**Detecting slip.** Two ways. The cheap one watches the gripper's finger gap and
calls it slipping if the fingers creep closed. The good one reads shear or
high-frequency vibration off a tactile sensor and catches it before the object
has visibly moved.

**Localising the contact.** A tactile array says *where on the pad* the contact
is, which tells you whether you gripped centrally or caught an edge — a check no
camera can make once the fingers are closed.

**Tactile exploration.** Touch an unknown object at many points and fit a surface
through them. This is how you measure something the camera cannot see at all. It
is genuinely slow — seconds per point — so it is used for the last millimetre of
a critical feature, not for surveying.

**Pre-touch**, which is sensing just before contact: a one-point infrared or
capacitive sensor between the fingers reports an object arriving a centimetre
early, giving you a chance to abort. See
[section 1.3](#13-infrared-in-four-different-roles).

### 2.2 Estimating a mass before you can weigh it

The weighing above happens with the object already in the air, which is late: you
had to choose a squeeze before lifting it. So there has to be an estimate first,
and the way to make one is worth writing down because it is not obvious that it
can be made at all.

**Treat the object as a shell, not a solid.** The outline from a side-on
measurement gives the surface swept by the wall. Multiply that area by a wall
thickness and a density and you have a volume of material rather than a volume of
object — which for anything hollow is the only figure that means anything. Add
the base as a disc, because it is solid and on a short object it is a good
fraction of the weight.

The wall thickness is the part you cannot see, and the honest way to handle it is
to stop pretending. Keep a **category** rather than a number — thin, normal,
thick — attached to the *kind* of object, and note that this is a guess about a
class and not a measurement of an instance. It is a fraction of a millimetre
either way, and it is enough.

**Expect the estimate to be about a third out in either direction**, and design
for that rather than trying to improve it. A third is fine for choosing a first
squeeze and useless as a final one, which is exactly why the sequence is estimate,
grip gently, lift, weigh, correct. If the estimate were good you would not need
the wrist sensor; if it were absent you would not know where to start.

**The force cap is the other half.** Per kind of object, record the most force it
can take before it is damaged — and treat exceeding it as a refusal rather than
something to clamp to the limit and continue with. An object that turns out to
need more grip than its walls can bear is an object that cannot be safely held,
and the useful response is to say so. Clamping to the cap and lifting anyway is
how you get a crack rather than a report.

### 2.3 The sensors

| Sensor | What it reports | Roughly |
| --- | --- | --- |
| **6-axis wrist force-torque**: [ATI](https://www.ati-ia.com/products/ft/sensors.aspx), [Robotiq FT 300](https://robotiq.com/products/ft-300-force-torque-sensor), [Bota](https://www.botasys.com/force-torque-sensors) | three forces and three torques at the wrist | FT 300: 300 N and ±30 Nm at 100 Hz; hundreds to thousands of pounds |
| **Joint torque sensing** | torque at every joint, so contact anywhere on the arm | built into Franka and KUKA iiwa; on a UR it is estimated from motor current and is much coarser |
| **A contact switch or a simulated contact sensor** | one bit: touching or not | pennies, and enough for a guarded move |
| **Vision-based tactile**: [GelSight Mini](https://www.gelsight.com/gelsightmini/), DIGIT, TacTip | a camera watching a gel deform, so a dense 3D map of the contact patch | GelSight Mini around $499 plus consumable gels |
| **Magnetic skin**: [AnySkin](https://github.com/raunaqbhirangi/anyskin) | shear and normal force over a soft skin | cheap, and the skin is replaceable |
| **Pressure arrays**: [Tekscan](https://www.tekscan.com/), [Contactile](https://www.contactile.com/) | a grid of pressures | industrial pricing |

Vision-based tactile sensors are the interesting ones and the most
misunderstood. A GelSight is literally a camera looking at the back of a soft gel
pad: when the pad presses on something, the camera sees the deformation, and
photometric stereo turns that into a height map of the contact patch at a
resolution finer than human touch. It gives you the *shape of the contact*, not
the shape of the object, and not where the object is.

### 2.4 The software

| Tool | Licence | What it is for |
| --- | --- | --- |
| [ros2_controllers](https://github.com/ros-controls/ros2_controllers) | Apache-2.0 | `force_torque_sensor_broadcaster` publishes the wrench; `admittance_controller` makes the arm comply with it |
| [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | BSD-3 | FZI's force and compliance controllers; last pushed 2024 |
| [franka_ros2](https://github.com/frankarobotics/franka_ros2) | Apache-2.0 | joint torques from an arm that really measures them |
| [ros2_robotiq_gripper](https://github.com/PickNikRobotics/ros2_robotiq_gripper) | BSD-3 | a common gripper, with its finger position feedback |
| [gsrobotics](https://github.com/gelsightinc/gsrobotics) | **GPL-3.0** | GelSight's own SDK — note the copyleft |
| [digit-interface](https://github.com/facebookresearch/digit-interface) | **CC BY-NC 4.0** | Meta's DIGIT driver; non-commercial, and last touched in 2021 |
| [TACTO](https://github.com/facebookresearch/tacto) | MIT | simulates a vision-based tactile sensor, so you can develop without hardware |
| [Taxim](https://github.com/Robo-Touch/Taxim) | MIT | an example-based simulator for the same, with better realism |

The two simulators are worth more than they look for a repo like this one. They
let you build and test the tactile half of a pipeline with no sensor on the desk,
the same way Gazebo lets you build the rest of it.

### 2.5 Models

There are far fewer than on the vision side, and the useful ones are recent.

| Model | Licence | What it does |
| --- | --- | --- |
| [NeuralFeels](https://github.com/facebookresearch/neuralfeels) | **MIT** | fuses vision and touch into a neural field, recovering the shape *and* pose of an object being turned in the hand |
| [Sparsh](https://huggingface.co/facebook/sparsh-vjepa-base) | **CC BY-NC 4.0** | self-supervised representations of tactile images, meant as a backbone for downstream tactile tasks |

NeuralFeels is the one to look at if you want to see where this is going: it is
the tactile answer to the problem the [reconstruction
section](05_models-that-measure.md#4-reconstruction-when-you-do-not) solves with
cameras, and it works in the case cameras cannot — an object held in the hand and
therefore mostly hidden by it.

Five jobs touch suits:

- finding the true height of a surface before placing something on it
- glass, polished metal and matt black, where every optical method fails
- learning the weight of something, which no camera can see
- verifying an optical measurement before committing to a delicate action
- measuring a feature the camera cannot see into, such as a bore

Five jobs it cannot do:

- survey a scene — you must already know roughly where to reach
- measure quickly, since each contact costs seconds where a picture costs
  milliseconds
- measure anything soft, which deforms before the sensor fires
- measure anything unfixed, which slides away from the probe
- measure anything fragile without a force limit, which is why the glass study
  caps its squeeze per kind of glass

### 2.6 Conditioning a force or contact reading

Section 2.1 says to take the median of a few dozen samples. That one sentence
hides most of the work, so this subsection does it properly. It answers four
questions: why a single sample is not a measurement, why the median rather than
the mean, how long the window should be, and what the filtering costs you. It is
for anyone about to read a number off a force sensor and act on it.

**A single sample from a force sensor is not a measurement of the thing you asked
about.** The sensor reports the total force passing through the wrist at that
instant. While the arm is moving, that total is made up of the arm's own
acceleration, the gripper motor's reaction as the fingers close, the structure
still oscillating after the last stop, and the payload — in roughly that order of
size. The trace quoted in section 2.1 ran from 0 g to 9577 g and back inside a
fraction of a second while the object on the end weighed 200 g. Sampling once
takes whichever of those numbers happened to be passing.

**Noise and transients are different problems, and they want different filters.**
Noise is small, present in every sample, and roughly symmetric about the true
value; it comes from the electronics and from the quantisation of the reading. A
transient is large, rare, one-sided, and caused by a real mechanical event such as
the fingers closing or the arm stopping. Averaging is the right answer to noise,
because errors that are symmetric about the truth cancel as you add them up.
Averaging is the wrong answer to transients, because a single large value drags
the mean by its own size divided by the number of samples, and 9577 g divided by
32 samples is still 299 g of error on a 200 g object.

Here are seven samples of that 200 g object, one of which caught the spike.

    198, 201, 199, 9577, 200, 202, 199

They sum to 10776, so the mean is 10776 / 7 = 1539 g, which is more than seven
times the true weight. Sorted, the same samples are 198, 199, 199, 200, 201, 202,
9577, and the middle one is 200 g. The median did not average the spike down. It
discarded it, because a median depends only on the order of the samples and not
at all on how far the extreme ones lie.

That property has a number attached. A median tolerates just under half the
samples being arbitrarily wrong before it leaves the range of the good ones: with
a window of 33 samples, 16 of them can be spikes of any size whatever and the
middle value still comes from clean data. A mean tolerates none, because one
sample of sufficient size moves it wherever you like. Use an odd window so that
the median is a real sample rather than the average of the two middle ones, since
averaging two samples reintroduces a small amount of the sensitivity you were
trying to remove.

**Settling time is the delay between the end of the motion command and the point
where the reading stays inside a band you have chosen around its final value.**
It is not the end of the trajectory. The controller finishes when it runs out of
trajectory points; the mechanism finishes when it has actually stopped moving,
and the gap between the two is the arm flexing and then ringing. Ringing is the
decaying oscillation a flexible structure is left with after it has been stopped
abruptly. A worked illustration, with its assumptions stated because they differ
from arm to arm: suppose the arm's structure flexes most readily at 8 Hz, which
is its dominant mode, so one cycle lasts 1 / 8 = 0.125 s,
and suppose each cycle loses 40% of the amplitude. To fall from a 5 N swing to
0.1 N the amplitude has to reach 0.1 / 5 = 0.02 of its starting value. Multiplying
0.6 by itself seven times gives 0.028, which is not yet there, and eight times
gives 0.017, which is. Eight cycles at 0.125 s each is 1.0 s.

Three further effects add to that figure, which is why settling time is usually
longer than people expect. The sensor has its own internal filter with a delay of
its own. A payload held in a compliant gripper swings on the fingers after the
wrist has stopped. And the strain gauges inside a force sensor drift thermally
for seconds after the load on them changes. A second is a realistic settling time
for a light arm carrying something, and a twentieth of a second is not, so a
pipeline that pauses for 50 ms before weighing is measuring the ring rather than
the payload.

**The window then follows from the sensor's rate and the residual motion.** Once
the arm has settled there is still a little movement at the same 8 Hz, so the
window should span at least three cycles for the median to land in the middle of
the residual rather than on one side of it. Three cycles of 8 Hz is 3 / 8 =
0.375 s. At the 100 Hz output rate of a sensor such as the Robotiq FT 300 in
section 2.3 that is 0.375 × 100 = 38 samples, so take 39 and keep it odd. The 32
samples suggested in section 2.1 are 32 / 100 = 0.32 s, which is 0.32 × 8 = 2.6
cycles: about the shortest window that works. Run the same calculation for a
sensor publishing a thousand times a second and it gives 0.375 × 1000 = 375
samples. The rate changes the sample count and leaves the duration alone, and it
is the duration that decides whether the filter works.

**Filtering costs you time, and the cost is half the window.** A median over 33
samples reports a value from the middle of its window, so at 100 Hz it lags
reality by 16 samples, which is 16 / 100 = 0.16 s. An arm descending at 50 mm/s
while you watch the filtered signal for contact travels 50 × 0.16 = 8 mm past the
surface before the filter notices. That is why the guarded move and the weighing
in section 2.1 must not share a filter. Contact detection wants a short window or
a raw threshold and accepts the occasional false trigger; measurement wants a
long window and accepts the delay.

**Percentile filters do the same job when you want an extreme rather than the
middle.** A percentile is the value below which a stated fraction of the samples
lie once they are sorted. The median is the 50th percentile, and the same sorting
gives you any other one, and the useful ones are near the ends. If you want the
largest force the gripper applied while closing, so as to check it against the
force cap in section 2.2, the maximum is the wrong statistic: the maximum is by
construction the single most extreme sample, which makes it the one most likely
to be a spike. The 95th
percentile of 200 samples is the 190th in sorted order, so ten spikes can sit
above it without moving it at all. The 5th percentile does the same work at the
other end, which is what you want for noticing the instant the load left the
wrist during a placement.

**A reading taken while the arm is moving answers a different question from one
taken while it is still.** Read the table below as the question each kind of
reading actually answers, which is not always the question the code thinks it
asked.

| When the reading is taken | What it tells you | What it cannot tell you |
| --- | --- | --- |
| stationary, settled, filtered | the static load below the wrist, which is the payload plus the gripper | anything about what happened during the move |
| while moving | whether something is resisting the motion right now | the payload's weight, which the inertia and friction terms swamp |

Both readings are useful and they are not interchangeable. Compliance control and
collision detection want the moving reading, and want it filtered lightly enough
to still be timely. Weighing, taring and any comparison against a threshold in
newtons want the stationary one. A pipeline that weighs on the move is not
measuring a light object at all; it is measuring its own acceleration.

Two practical points close this off. The tare comes first, because a wrist
reading includes the gripper's own weight: the quantity you want is the
difference between a settled reading with the object and a settled reading
without it, taken at the same wrist orientation, for the reason section 2.1
gives. And the filter belongs in the same place as the frame conversion in
[section 5.4](#54-the-rule-that-prevents-it) — applied once, at the boundary
where readings arrive, with only the conditioned value passed onward.

Read the software table as: what to call, where it comes from, and the licence as
read from that project's own LICENSE file.

| Tool | Licence | What it does here |
| --- | --- | --- |
| [NumPy](https://github.com/numpy/numpy) `median` and `percentile` | BSD-3-Clause | one number out of a buffer you have already collected |
| [SciPy](https://github.com/scipy/scipy) `ndimage.median_filter` and `ndimage.percentile_filter` | BSD-3-Clause | a running filter across a whole recorded trace, for looking at afterwards |
| [ros2_controllers](https://github.com/ros-controls/ros2_controllers) `force_torque_sensor_broadcaster` | Apache-2.0 | publishes the wrench, and subtracts a constant `offset` per axis — which is a tare, not a filter |

Five jobs a median over a settled window suits:

- weighing a held object, which is what section 2.1 uses it for
- taking a zero before a grasp, so the gripper's own weight drops out
- rejecting the spike the fingers make as they close
- checking a settled force against a damage cap before committing to a lift
- turning a noisy tactile pressure into a number you can threshold

Five jobs it cannot do:

- detect the instant of contact, since it reports the middle of its window
- measure anything that is genuinely changing, which it smooths into a value that
  is wrong in a believable way
- find a peak, which it discards by construction — use a high percentile instead
- correct a sensor whose zero has drifted, since the median of a biased signal is
  biased by exactly the same amount
- rescue a window that straddles a real event, which returns a value that was
  never true at any instant

## 3. Event, thermal and polarisation cameras
Sensors that answer questions an ordinary camera cannot.

### 3.1 Event cameras

An event camera has no frames. Each pixel reports independently, in microseconds,
whenever the brightness it sees changes. That gives no motion blur, a dynamic
range far beyond a normal sensor, and very little data when nothing is moving.

For a robot arm it is a specialist tool — good for catching fast motion and for
scenes with extreme lighting contrast, and awkward everywhere else, because
almost every model in this document expects frames.

The open software is Prophesee's [OpenEB](https://github.com/prophesee-ai/openeb)
and iniVation's [dv-processing](https://gitlab.com/inivation/dv/dv-processing),
with [libcaer_driver](https://github.com/ros-event-camera/libcaer_driver) for
ROS 2. The research literature is collected in
[this list](https://github.com/uzh-rpg/event-based_vision_resources).

### 3.2 Thermal, polarisation and the rest

**Thermal** cameras identify by temperature, which is sometimes exactly the
distinguishing feature — a hot casting, an occupied seat, a person in a safety
zone. They have low resolution and they are not what you segment a mug with.

**Polarisation** cameras measure the angle of polarisation of the light, which is
strongly changed by glass and by specular surfaces. It is frequently suggested as
the answer for transparent objects, so it is worth saying plainly what a search
of the open-source landscape in September 2026 turns up: **essentially nothing**.
There are no maintained open repositories doing transparent-object grasping from
polarisation. The published work on transparent objects has gone in a different
direction — see [section 6.6](04_models-that-find.md#17-transparent-and-shiny-objects).

Five jobs where the sensor choice is the deciding factor:

- glass and clear plastic, where an ordinary RGB-D camera returns nothing useful
- parts that differ only in a fraction of a millimetre, which needs a real scanner
- scenes with extreme contrast, where an event camera's dynamic range wins
- anything moving fast enough to blur a normal frame
- distinguishing objects by temperature rather than appearance

Five where it is not:

- ordinary opaque objects on a table, where a cheap camera and a good model win
- anything where the limit is the model's class list rather than the picture
- jobs where the object is large and the tolerance is loose
- prototypes, where the wrong lesson is to buy hardware before trying software
- any problem the lighting would have fixed more cheaply

## 4. Calibration, which decides all of it
Calibration is the least interesting subject in this document and it is usually
the largest term in the error budget. The chart in [section
4](01_overview.md#8-where-the-millimetres-go) makes the point numerically: a hand-eye
calibration one degree out costs almost 6 mm at a 340 mm reach, more than twice
what a one-pixel segmentation error costs.

There are two calibrations and they are separate.

**Intrinsic calibration** finds the lens numbers — `fx`, `fy`, `cx`, `cy` and the
distortion — by photographing a known pattern from many angles. A good result has
a reprojection error below one pixel; a very good one is around 0.1 to 0.3 pixels.
A ChArUco board is now preferred to a plain chessboard, because a partly hidden
ChArUco board simply returns fewer corners while a partly hidden chessboard breaks
the row and column indexing entirely.

**Hand-eye calibration** finds where the camera is relative to the arm. OpenCV's
`calibrateHandEye` offers five methods — Tsai, Park, Horaud, Andreff and
Daniilidis — and the practical guidance from OpenCV's own issue discussions is that
**Park converges reliably in the widest range of cases**. Published results for
careful hand-eye calibration land around 0.9 mm of translation error and a quarter
of a degree of rotation.

| Tool | Licence | State |
| --- | --- | --- |
| [OpenCV `calib3d`](https://github.com/opencv/opencv) | Apache-2.0 | the reference implementation of both |
| [easy_handeye2](https://github.com/marcoesposito1988/easy_handeye2) | LGPL-3.0 | the usual ROS 2 choice, actively maintained |
| [mrcal](https://github.com/dkogan/mrcal) | Apache-2.0 | unusual and valuable: it propagates calibration *uncertainty*, not just a point estimate |
| [moveit_calibration](https://github.com/moveit/moveit_calibration) | BSD-3 | its ROS 2 work sits on an unmerged branch; treat as semi-maintained |
| [Kalibr](https://github.com/ethz-asl/kalibr) | BSD | camera and IMU rigs; slow-moving |

The conclusion worth carrying away is one of proportion. With a consumer depth
camera at two to five millimetres, a one-millimetre hand-eye error is not your
problem. Fit a Zivid at 0.2 mm and that same one millimetre becomes the entire
error. **Buying a better sensor without recalibrating buys you nothing.**

## 5. Frames, and which one a reading is in
Every number produced by every sensor in this document is a number in some frame
of reference, and almost none of them say which. This section answers one question: when a
sensor hands you three numbers, what are they three numbers *of*? It is for
anyone writing the code between a sensor and a motion command, and it comes last
because it depends on the calibration in section 4 being done — a frame is only
useful once you know where it is.

It earns a section rather than a footnote for one reason. Using a reading in the
wrong frame does not raise an error. It produces a plausible number.

### 5.1 The frames in a typical cell

A frame of reference is an origin and three axes. A reading expressed in one
frame is a different set of numbers from the same physical fact expressed in
another, and converting between them needs a transform, which is a rotation and a
translation. A robot arm cell normally has at least six frames in use at once.

Read the table below as: the name the frame usually goes by, where its origin
sits physically, and how its axes are oriented.

| Frame | Where its origin sits | How the axes point |
| --- | --- | --- |
| `world` | a fixed point in the cell, chosen once and never moved | x forward, y left, z up |
| `base_link`, the robot base | the centre of the arm's mounting face | the same convention; this is the frame the arm reports its own tool pose in |
| `tool0`, the flange | the arm's output flange, before any gripper | set by the arm vendor, usually with z out along the reach axis |
| the tool centre point | between the fingertips, or wherever the work happens | set by you, in the gripper's model |
| `camera_link` | somewhere in the camera body that the vendor chose | x forward, y left, z up — the body convention |
| the camera optical frame | the same physical place as `camera_link` | z forward, x right, y down |
| the force sensor frame | the sensor's own mounting face, inside the wrist | whatever the bolt pattern allowed, which is often not aligned with the flange |

Those conventions are ROS's, and they are written down in
[REP 103](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst). A
REP is a ROS Enhancement Proposal, which is the document type ROS uses for its
standards, and this one fixes units and coordinate conventions across the whole
system. It says that all
systems are right-handed, and that in relation to a body the axes are x forward, y
left, z up. It then defines the exception that catches nearly everybody: a camera
usually has a second frame whose name ends in `_optical`, and that frame uses z
forward, x right, y down. Two frames, the same physical point, and a rotation
between them.
[REP 105](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst) names
the fixed frames for a robot that drives around — `earth`, `map`, `odom` and
`base_link` — which matters if the arm sits on a mobile base, because then "world"
is a chain of four frames rather than one.

**The idea to carry away is that a frame belongs to a reading, not to the robot.**
There is no such thing as "the robot's frame". Two readings taken at the same
instant by two sensors bolted a centimetre apart are in two different frames. A
reading's frame is a property of that reading in the same way its units are, and
it has to travel with the reading for the same reason.

### 5.2 Every sensor reports in its own frame, and almost none of them say so

Each instrument in this document answers in the frame that is natural to its own
construction, which is rarely the frame you want.

A wrist force-torque sensor reports three forces along its own axes and three
torques about them. Those axes rotate with the wrist, so the same hanging weight
produces different numbers at different wrist orientations, which is the whole
content of the trap in section 2.1.

A camera reports in its optical frame. Every pixel coordinate, every depth value
and every pose recovered from a marker comes out in z forward, x right, y down,
because that is the convention the projection geometry is written in. This is
*not* the frame the camera link uses, and both frames usually exist in the same
robot model with names that differ by one suffix.

A point cloud may be in either. Which one it is in is a decision the driver made,
so read the cloud's own frame name rather than assuming; two drivers for two
cameras in the same cell may differ.

The joint encoders report angles about each joint's own axis. Forward kinematics —
the calculation that turns a set of joint angles into the pose of the tool —
turns those into a pose in the base frame, and that pose is the one output of the
whole arm that arrives in a frame you chose rather than one the hardware imposed.

A one-point range sensor of the kind in section 1.3 reports a distance along its
own axis and has no frame in its output at all, because it has no message — it has
a number on a bus.

ROS 2 does carry the frame. Every stamped message has a `header.frame_id` naming
the frame its contents are in. Two things then go wrong. The first is that the
field is filled in by the driver, so a driver that names the link frame while
publishing optical-frame data is perfectly well-formed and completely wrong. The
second does more damage: the frame survives exactly as long as the message does.
The moment you write `f = msg.wrench.force.z` you are holding a single number,
and that number carries no frame with it.

Outside ROS there is usually no frame at all. A vendor SDK returns six doubles; a
research code base returns an array of three numbers; neither carries a name, and
the convention lives in a comment if it lives anywhere.

One project takes the naming seriously enough to be worth copying.
[ros2_controllers](https://github.com/ros-controls/ros2_controllers), Apache-2.0
as read from its LICENSE file, gives `force_torque_sensor_broadcaster` a
`frame_id` parameter validated as not empty, so the controller refuses to start
until it has been told which frame it is publishing in. That is the right amount
of pedantry for a value that is about to be turned into motion.

### 5.3 The bug, in four instances

The four below look like four unrelated faults. They are one fault, and the
generalisation at the end is the part worth remembering.

**The wrist force sensor read along the wrong axis.** This is the instance already
described in section 2.1. A wrist sensor reports in the tool frame, so taking the
tool's own z as the weight works perfectly while the tool points down and returns
zero for a side grasp, because gravity then pulls across that axis instead of
along it. Every object weighs nothing, convincingly.

**A depth point read in the wrong camera frame.** Take a point the camera sees
300 mm ahead of it, 50 mm to its right and 100 mm below the optical axis. In the
optical frame that point is (0.05, 0.10, 0.30) in metres, because x is right, y is
down and z is forward. In the camera's link frame the same point is (0.30, −0.05,
−0.10), because x is forward, y is left and z is up. Hand the optical triple to
code expecting the link convention and the object is reported 0.05 m in front of
the camera instead of 0.30, 0.10 m to the left instead of 0.05 to the right, and
0.30 m above instead of 0.10 below. The three errors are 0.25 m, 0.15 m and
0.40 m. Each of those numbers is a perfectly sensible distance in a table-top
cell, so the planner finds a route and the arm moves confidently to the wrong
place.

**An orientation applied in the wrong frame.** A grasp direction is a rotation,
usually held as a quaternion, which is a set of four numbers of which a valid
rotation uses only those of unit length. A unit quaternion is still a unit
quaternion after a change of frame, so checks for validity, normalisation and
magnitude all pass whatever frame the rotation was worked out in. Apply an
approach direction computed in the camera's optical frame as though it were in
the tool frame and the gripper arrives rotated by whatever the camera-to-tool
rotation happens to be — and between a camera's optical frame and its own link
frame that is already a pair of right angles, before the mounting is counted. The
fingers then close across the object's long axis instead of along it, and the
failure gets reported as a mechanical one: the gripper is too narrow for this
object.

**The right frame at the wrong instant.** A transform between two moving frames is
a function of time, so looking one up with "now" instead of the reading's own
timestamp is a frame error of the temporal kind. A wrist camera moving at 0.25 m/s
with a transform 50 ms out of date places the picture 0.25 × 0.05 = 0.0125 m, or
12.5 mm, from where the arm believes it was taken. Nothing in the pipeline is
wrong except the moment it was asked about. The [wrist camera
document](08_the-wrist-camera.md) goes into what staleness costs at various
speeds.

**The shape all four share.** A frame error applies a rotation, a translation, or
both, to a quantity that was already correct. A rotation does not change a
vector's length, and a translation inside a work cell is a few tens of
centimetres. So the wrong answer comes out with the right units, a magnitude in
the right range, and a direction that is wrong. Every check that looks only at
size passes: it is a number, it is finite, it is inside the workspace, the
quaternion is normalised. Only a check that compares *direction* against an
independent reference catches it, which is what section 5.5 is about.

### 5.4 The rule that prevents it

Four habits, none of which costs anything at the time.

**Name the frame in the variable.** Write `force_tool`, `point_cam_optical` and
`pose_base`, never `force`, `point` and `pose`. The benefit is that the bug
becomes visible where the value is used rather than only once the arm moves:
`weight = force_tool.z` invites the question that `weight = force.z` does not.
Apply the same rule to function arguments and to the names of the values a
function returns.

**Name the direction of a transform too**, because applying a transform backwards
is the second most common version of this bug. Write `T_base_from_camera`, so that
reading left to right, `T_base_from_camera · point_camera = point_base` and the
adjacent labels cancel the way units cancel in a physics calculation. A chain then
checks itself by inspection. `T_base_from_tool · T_tool_from_camera ·
point_camera` is right, and swapping either term leaves a `camera` next to a
`tool`, which is visibly wrong on the page.

**Convert at the boundary.** The function that receives a message converts it once,
immediately, into the single frame the rest of the code works in, and everything
downstream is in that frame by construction. In ROS 2 that means tf2, the
transform library described in section 5.5: its buffer from `tf2_ros`, together
with the `doTransform` helpers in `tf2_geometry_msgs`, which handle points, poses,
quaternions, vectors and wrenches.

A wrench is worth a paragraph of its own here, because transforming one is not
just a rotation. The `doTransform` for a wrench in
[geometry2](https://github.com/ros2/geometry2) rotates the force, rotates the
torque, and then adds the extra torque that the translation creates, which is the
cross product of the offset with the rotated force. A 5 N force referred to a
point 100 mm away picks up 5 × 0.1 = 0.5 Nm of torque that was not in the original
reading. That torque is real rather than an artefact — it is the moment about the
new origin — and code that rotates the force by hand and leaves the torque
untouched is quietly wrong about it.

**Never let a raw reading travel more than one function without its frame
attached.** Pass the stamped message, or a small pair of frame name and value, and
not a bare array. Once a number has been through three functions as a plain
float, the only way to recover its frame is to read every one of them.

There is a ready-made example of the boundary rule in the same repository as the
broadcaster above. `force_torque_sensor_broadcaster` ships a wrench transformer
node that subscribes to the raw wrench and republishes it, on a separate topic for
each frame, into every frame named in its `target_frames` parameter, using tf2
with a lookup timeout that defaults to 0.1 s. The conversion happens once, in one
place, and each consumer subscribes to the frame it actually wants.

### 5.5 How to check

There are two checks. One is in software and one uses your hands, and neither
substitutes for the other.

**tf2 answers where any frame was relative to any other, at a stated time.** It is
the transform library in [geometry2](https://github.com/ros2/geometry2),
BSD-3-Clause as read from its LICENSE file. The obvious alternative is to write
the camera-to-base transform into whichever node needs it as a fixed matrix, and
tf2 is worth preferring because that alternative keeps the same geometry in
several places, so recalibrating corrects some copies and leaves the rest wrong.
What tf2 costs you is that the tree has to be complete and continuously
published: a node that stops publishing its transform takes every query through
it down with it. Nodes publish transforms, tf2
assembles them into a tree and interpolates between the published samples, and
`lookup_transform` takes two frame names and a timestamp. Passing the reading's
own stamp rather than the current time is exactly what avoids the fourth instance
in section 5.3. The buffer keeps a finite history — `BUFFER_CORE_DEFAULT_CACHE_TIME`
in `tf2/buffer_core.hpp` is 10 seconds — so a lookup for an older stamp fails
instead of extrapolating, which is the behaviour you want. To look at the tree,
`ros2 run tf2_tools view_frames` renders it to a file, `ros2 run tf2_ros tf2_echo`
prints a single transform as it changes, and rviz2 draws every frame's axes in
three dimensions, which is the quickest way to notice that a camera's axes point
somewhere unexpected.

The limit of tf2 has to be stated plainly, because it is often misread as a
guarantee. tf2 tells you when a transform is *missing*. It cannot tell you when a
transform is *wrong*. A tree built on a bad hand-eye calibration is complete,
well-formed and self-consistent, and it answers every query promptly with the
wrong number.

**So the second check is physical, and it is the only one that tests the numbers
against the world.** Put a known object at a known place and compare what the
pipeline reports with what you measured. Tape a printed marker to the table and
measure its centre from the robot base with a rule. Choose a position that is
asymmetric in all three axes — not straight ahead, not level with the base — so
that a swapped pair of axes or a wrong sign gives a visibly different answer
instead of the same one. Say you measure the marker at 400 mm forward, 150 mm to
the left and 20 mm above the base plane, which in the convention of section 5.1 is
(0.400, 0.150, 0.020) in the base frame. If the pipeline reports (0.150, 0.400,
0.020) you have swapped x and y. If it reports (0.400, −0.150, 0.020) your y sign
is inverted. If it reports the three numbers you measured, the chain is right for
that point.

Then repeat at three places that are not in a straight line. A single point can be
matched by a great many wrong transforms, since any rotation about the axis
through that point leaves it where it is. Three points that are not collinear pin
a rigid transform down completely, so agreement at all three means the rotation is
right as well as the offset.

There is a version of this check for the frames a camera cannot see, and it uses
the guarded move from section 2.1. Drive the tool slowly to the position the
pipeline reported and let it make contact. The joint encoders then tell you where
the tool really was at the instant it touched, in the base frame, and the
difference between that and the reported position is the error of the entire
chain, calibration included.

Five jobs tf2 suits:

- answering where the camera was at the instant a particular picture was taken
- composing a chain of transforms without writing the matrix algebra by hand
- holding one definition of the cell's geometry that every node shares
- catching a missing calibration, since a disconnected tree raises rather than
  guessing
- letting you look at every frame's axes in rviz2 and spot a wrong one at once

Five jobs it cannot do:

- tell you a transform is wrong, as opposed to absent
- restore the frame of a reading you have already stripped down to a bare number
- correct a driver that filled its `frame_id` in wrongly, which it cannot detect
- answer for a stamp older than its buffer, which by default holds ten seconds
- give a frame to a vendor SDK whose output never had one
