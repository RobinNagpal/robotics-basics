# The sensors, and the software for each

What you can identify and what you can measure are both decided first by the
instrument. This document is the instruments: what each kind of sensor gives you,
how each one fails, what accuracy you can actually expect, the library you talk
to it with, the ROS 2 package that wraps it — and the calibration without which
none of those numbers mean anything.

The accuracy figures are the manufacturers' own published specifications, checked
against their data sheets in September 2026. They are specifications, not what
you will get on a bad day.

## Contents

1. [What each sensor gives you](#1-what-each-sensor-gives-you)
2. [Event, thermal and polarisation cameras](#2-event-thermal-and-polarisation-cameras)
3. [Calibration, which decides all of it](#3-calibration-which-decides-all-of-it)

---

## 1. What each sensor gives you
If you are going to measure the distance rather than infer it, this is what you
can buy. The numbers below are the manufacturers' own published figures, checked
against their data sheets in September 2026, and they are specifications rather
than what you will get on a bad day.

| Sensor | How it works | Published accuracy | Roughly |
| --- | --- | --- | --- |
| [RealSense D405](https://www.realsenseai.com/products/stereo-depth-camera-d405/) | active stereo, close range | ±2% at 50 cm, works from 7 cm | a few hundred pounds |
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

**Active stereo** — the RealSense and Orbbec Gemini families — projects a speckle
pattern so that a blank surface has texture to match. That fixes the textureless
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
[section 2.2](#22-thermal-polarisation-and-the-rest).

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
study](../08_one-arm-training/07_case-study/01_place-glass.md) uses, for exactly
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

### 1.5 Measuring by touch

Touch is the other way to get a distance, and it is worth remembering that it is
the most accurate instrument an arm has. A robot's own joint encoders locate the
tool to a few hundredths of a millimetre, so a contact detected by a
force-torque sensor is a far better measurement than any camera in the table above.

In ROS 2 the pieces are the
[`force_torque_sensor_broadcaster` and `admittance_controller`](https://control.ros.org/rolling/doc/ros2_controllers/doc/controllers_index.html)
in [ros2_controllers](https://github.com/ros-controls/ros2_controllers)
(Apache-2.0). [Measuring by touch](03_programmed-methods.md#27-measuring-by-touching-it)
covers what it is good for.

### 1.6 The software that comes with each sensor

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
| a force-torque sensor | [ros2_controllers](https://github.com/ros-controls/ros2_controllers) | Apache-2.0 | `force_torque_sensor_broadcaster` | the probing in [section 6.7](03_programmed-methods.md#27-measuring-by-touching-it) |
| scanning LiDAR | vendor SDK | Apache-2.0 drivers | [velodyne](https://github.com/ros-drivers/velodyne), [ouster-ros](https://github.com/ouster-lidar/ouster-ros), [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2), [sick_scan_xd](https://github.com/SICKAG/sick_scan_xd) | [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) for mapping — not the methods in this area |
| one-point infrared | [VL53L1X driver](https://github.com/stm32duino/VL53L1X) | BSD-3 | read over I2C from a microcontroller | nothing — it is one number |
| a printed marker | [OpenCV ArUco](https://github.com/opencv/opencv), [AprilTag](https://github.com/AprilRobotics/apriltag) | Apache-2.0 / BSD-2 | [ros_aruco_opencv](https://github.com/fictionlab/ros_aruco_opencv), [apriltag_ros](https://github.com/christianrauch/apriltag_ros) | calibration, and the scale trick in [section 6.3](03_programmed-methods.md#23-a-marker-of-known-size) |

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

## 2. Event, thermal and polarisation cameras
Sensors that answer questions an ordinary camera cannot.

### 2.1 Event cameras

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

### 2.2 Thermal, polarisation and the rest

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

## 3. Calibration, which decides all of it
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

