# Frames, conventions, and the bug class that comes from mixing them

Every number that describes a position, a direction, a rotation or a force in a
robot cell is measured from somewhere. The place it is measured from is called a
**frame**: an origin with three axes, attached to one physical thing. A number
without its frame is not a weak number. It is not a number at all.

This document is about what happens when a number is used in the wrong frame. The
answer is the reason the subject deserves its own document. The program does not
stop. Nothing throws. The arm moves smoothly to a position that is wrong by a
hundred and eighty millimetres, or the force guard that was supposed to stop the
tool reads zero while the tool is being pushed sideways at nine newtons. The
wrong answer looks exactly like a right answer, and it looks like one all the way
through testing, until a person watches the arm and says that is not where I
meant.

The second half of the problem is that the conventions genuinely differ between
the pieces of software in one cell. Not through carelessness: each choice is
defensible in the place it was made. The robot description says a rotation one
way, the simulator another, the camera library a third, and the numerical library
underneath them all lays a matrix out in memory a fourth. None of them is wrong.
They only have to be converted, and the conversion is the part that gets
forgotten.

## Who this is for, and what it is not

This is for someone who already writes code that moves an arm or reads a camera,
and who has either been bitten by this or is about to be. You need to know what a
frame and a transform are. You do not need to be able to derive anything.

[Position, frames and transforms](../03_arm/01_overview.md) teaches the
underlying maths from nothing, on a two-joint arm, over five programs you can
read and run. It explains what a frame is, what a transform is, why the order of
operations matters, and how to hand the whole thing to ROS. **Read that one
first if any of those words are new.** This document is its practical companion
and deliberately does not repeat it. That one answers "what is a transform and
how does it work". This one answers "which convention does this particular
library use, and what breaks when I get it wrong".

Two other documents in this repository touch the subject from their own side.
[Arm movement: getting there](01_overview.md) sets out the five kinds of move and
where the millimetres go. [The sensors, and the software for
each](../06_object-perception/02_sensors.md) covers calibration, which is the
process of measuring the transforms this document assumes you already have. A
frame error and a calibration error produce the same symptom, and section 5 is
partly about telling them apart.

Every convention stated below was checked against a primary source — a message
definition, a REP, or the library's own code — and the source is named where the
claim is made. Every number was produced by running the calculation, not
remembered. Where a published figure disagreed with what the calculation
returned, the calculation won and the difference is noted.

## Contents

1. [The frames in a typical arm cell](#1-the-frames-in-a-typical-arm-cell)
   · [1.1 The seven frames you meet](#11-the-seven-frames-you-meet)
   · [1.2 The frame is a property of the number](#12-the-frame-is-a-property-of-the-number)
   · [1.3 Which direction a transform goes](#13-which-direction-a-transform-goes)
2. [The conventions that differ, and where each one is written down](#2-the-conventions-that-differ-and-where-each-one-is-written-down)
   · [2.1 Quaternion ordering](#21-quaternion-ordering)
   · [2.2 The camera link and the camera optical frame](#22-the-camera-link-and-the-camera-optical-frame)
   · [2.3 Row-major and column-major](#23-row-major-and-column-major)
   · [2.4 Euler angles, intrinsic and extrinsic](#24-euler-angles-intrinsic-and-extrinsic)
   · [2.5 Degrees and radians](#25-degrees-and-radians)
   · [2.6 Pre- and post-multiplication](#26-pre--and-post-multiplication)
3. [The bug class, in five instances](#3-the-bug-class-in-five-instances)
   · [3.1 The force guard that reads zero while the tool is pushed](#31-the-force-guard-that-reads-zero-while-the-tool-is-pushed)
   · [3.2 The point cloud that stands the scene on end](#32-the-point-cloud-that-stands-the-scene-on-end)
   · [3.3 The quaternion read in the wrong order](#33-the-quaternion-read-in-the-wrong-order)
   · [3.4 The pose composed in the wrong order](#34-the-pose-composed-in-the-wrong-order)
   · [3.5 The roll, pitch and yaw read as intrinsic](#35-the-roll-pitch-and-yaw-read-as-intrinsic)
   · [3.6 What the five have in common](#36-what-the-five-have-in-common)
4. [The practices that prevent it](#4-the-practices-that-prevent-it)
   · [4.1 Put the frame in the name](#41-put-the-frame-in-the-name)
   · [4.2 Convert at the boundary, and keep one frame inside](#42-convert-at-the-boundary-and-keep-one-frame-inside)
   · [4.3 Never let a reading travel alone](#43-never-let-a-reading-travel-alone)
   · [4.4 Why PoseStamped exists](#44-why-posestamped-exists)
5. [How to check](#5-how-to-check)
   · [5.1 Interrogating TF2](#51-interrogating-tf2)
   · [5.2 The known object in a known place](#52-the-known-object-in-a-known-place)
   · [5.3 The unit vector probe](#53-the-unit-vector-probe)
6. [Units and scale](#6-units-and-scale)
7. [Sources and licences](#7-sources-and-licences)

---

## 1. The frames in a typical arm cell

### 1.1 The seven frames you meet

A small arm cell — one arm, one gripper, one camera, one force sensor — has
about seven frames that you will name in code. The table lists them with the
name they usually carry, what they are attached to, and the one question each
one is the natural answer to. Read the third column as "when I am working on
this, these are the numbers that stay simple".

| Frame | Attached to | Natural for |
| --- | --- | --- |
| `world` | the room, or the cell floor | where the arm, the table and the fixtures are relative to each other |
| `base_link` | the arm's mounting plate | joint angles, reach checks, and everything the arm's own controller says |
| `flange` or `tool0` | the last mechanical face of the arm, before any tooling | mounting a gripper, and comparing one end effector against another |
| tool centre point, `tcp` | the working point of the tool — between the fingers, or the tip of a screwdriver bit | the pose you actually want to command, because it is the part that touches the object |
| `camera_link` | the camera body | mounting the camera, and drawing it in a viewer |
| `camera_optical_frame` | the same camera body, rotated | anything computed from pixels, because the projection maths is short in these axes |
| force sensor frame | the load cell between flange and tool | the six numbers the sensor actually reports |

Two entries on that list deserve the attention. The flange and the tool centre
point are both "the end of the arm", and they are typically 100 to 200 mm apart;
sending a flange pose where a tool pose was meant puts the tool that far into the
table. The camera link and the camera optical frame are the *same physical
object* in the same place, differing only by a rotation, which is what makes
confusing them so easy and so silent.

The object you are picking has a frame too, and so does the fixture it sits in.
Those are not in the table because they come and go with the task, but they obey
the same rules.

### 1.2 The frame is a property of the number

The important idea in this document is one sentence long. **The frame belongs to
the number, not to the robot.**

A robot does not "have a frame". It has many, all of them valid at once, and
every single quantity you compute is expressed in exactly one of them. The
gripper is at `(0.43, 0.65, 0.30)` in `base_link` and at `(0, 0, 0)` in its own
frame, at the same instant, with nothing having moved. Both are correct. A force
of nine newtons is `(0, 0, -9)` in the sensor frame and something else entirely
in `base_link`. A point from the camera is one triple in the optical frame and a
different triple in `camera_link`.

So when you write `position = something`, the variable holds a number *and* an
unwritten fact about where it was measured from. The compiler does not know that
fact. The type system, in every language commonly used for robots, does not know
it either: a position in `base_link` and a position in the camera optical frame
are both `float[3]`, or both `numpy.ndarray` of shape `(3,)`, and they add
together without complaint.

That is the whole mechanism of this bug class. The information that would have
caught the mistake was never in the program.

### 1.3 Which direction a transform goes

Before any convention below makes sense, one piece of vocabulary has to be
pinned down, because it is stated two opposite ways in the wild.

In ROS, a transform is published from a parent frame to a child frame, written
`parent → child`. It holds the pose of the child expressed in the parent. When
you *apply* it, it takes a point whose numbers are in the **child** frame and
gives you that same point's numbers in the **parent** frame. The transform points
one way and the data travels the other, and that is the sentence people trip on.

TF2, the part of ROS that stores and joins transforms, names its lookup
arguments accordingly. Its
[interface header](https://raw.githubusercontent.com/ros2/geometry2/rolling/tf2/include/tf2/buffer_core_interface.hpp)
documents `lookupTransform` as taking a `target_frame`, "the frame to which data
should be transformed", and a `source_frame`, "the frame where the data
originated". So `lookupTransform("base_link", "camera_optical_frame", t)` returns
the thing that converts camera numbers into base numbers.

The command line tool that prints the same transform names its arguments the
other way round, which is worth knowing before you debug with it. The usage text
in [`tf2_echo.cpp`](https://raw.githubusercontent.com/ros2/geometry2/rolling/tf2_ros/src/tf2_echo.cpp)
reads `Usage: tf2_echo source_frame target_frame`, and then adds the note "This
is the transform to get data from target_frame into the source_frame." The code
below that text passes its first argument as `lookupTransform`'s *target*. The
tool is not wrong, but its two arguments carry the opposite names to the library
call it makes, so read the note rather than the argument names.

---

## 2. The conventions that differ, and where each one is written down

Everything in this section is a choice that reasonable people made differently.
For each one, the primary source is linked, because "I am fairly sure it is
`w` first" is how this bug gets into the code.

### 2.1 Quaternion ordering

A **quaternion** is four numbers that describe a rotation. Three numbers form a
vector part, conventionally called `x`, `y` and `z`, and one is a scalar part
called `w`. The rotation is unchanged by the order you store them in. The order
you *read* them in changes everything.

There are two orders in use, and both are common enough that neither can be
assumed:

- scalar-last, `(x, y, z, w)`, where the identity rotation is `(0, 0, 0, 1)`
- scalar-first, `(w, x, y, z)`, where the identity rotation is `(1, 0, 0, 0)`

ROS uses scalar-last. The
[`geometry_msgs/Quaternion`](https://raw.githubusercontent.com/ros2/common_interfaces/rolling/geometry_msgs/msg/Quaternion.msg)
definition lists the fields as `x`, `y`, `z`, `w` with defaults `0, 0, 0, 1`, so
the message's own default value is the identity and the field order is the
convention. The URDF parser agrees: in
[`urdf_model/pose.h`](https://raw.githubusercontent.com/ros/urdfdom_headers/master/include/urdf_model/pose.h),
`Rotation::clear()` sets `x`, `y` and `z` to zero and `w` to one.

MuJoCo uses scalar-first. Its
[XML reference](https://raw.githubusercontent.com/google-deepmind/mujoco/main/doc/XMLreference.rst)
gives the `quat` attribute a default of `"1 0 0 0"`, and its
[modeling guide](https://raw.githubusercontent.com/google-deepmind/mujoco/main/doc/modeling.rst)
states that a rotation by angle `a` about a unit axis `(x, y, z)` is the
quaternion `(cos(a/2), sin(a/2)·(x, y, z))` — scalar first, explicitly.

SciPy uses scalar-last by default and will do either on request. In
[`_rotation.py`](https://raw.githubusercontent.com/scipy/scipy/main/scipy/spatial/transform/_rotation.py),
`from_quat` and `as_quat` both take a `scalar_first` keyword, documented as
choosing between "scalar-last (default)" and "scalar-first order — `(w, x, y,
z)`". Running it on a 90 degree yaw gives `[0, 0, 0.7071, 0.7071]` by default and
`[0.7071, 0, 0, 0.7071]` with `scalar_first=True`.

The change worth knowing about in 2026 is NVIDIA's. Isaac Lab used scalar-first
through version 2.x and switched to scalar-last in 3.0. Its
[3.0 migration guide](https://github.com/isaac-sim/IsaacLab/blob/develop/docs/source/migration/migrating_to_isaaclab_3-0.rst)
states plainly that "The quaternion format changed from WXYZ to XYZW", gives a
table showing the identity moving from `(1.0, 0.0, 0.0, 0.0)` to
`(0.0, 0.0, 0.0, 1.0)`, and explains the reason as alignment with Warp, PhysX and
Newton, which removes internal conversions. The
[3.0 early-access release](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-EA)
was published on 16 September 2026. The guide's own advice is that any hard-coded
quaternion carried over from a 2.x project now needs converting, and it ships a
`scripts/tools/find_quaternions.py` helper to locate them, with a warning that
the helper is not reliable enough to run unsupervised. Take that warning
seriously: a tool that guesses which four-element tuples are quaternions will
miss some and invent others.

### 2.2 The camera link and the camera optical frame

A camera in ROS has two frames in the same place, and this is deliberate rather
than an accident of history.

[REP 103](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst),
the document that fixes units and coordinate conventions across ROS, sets the
body convention as x forward, y left, z up, all frames right-handed. That is the
convention `camera_link` follows, and it is the convention that makes a camera
sit sensibly in a robot model next to everything else. The same REP then adds a
section headed "Suffix Frames" which says that for cameras "there is often a
second frame defined with a `_optical` suffix", using z forward, x right, y
down.

The optical convention exists because that is what the projection maths wants.
OpenCV's [calib3d module
documentation](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/calib3d/include/opencv2/calib3d.hpp)
defines normalised camera coordinates as `x' = Xc/Zc` and `y' = Yc/Zc`, then
multiplies by the intrinsic matrix to get pixel `(u, v)`. Dividing by `Zc` is
what makes `Z` the depth along the optical axis, and pixel columns increasing
rightwards with rows increasing downwards is what makes `X` right and `Y` down.
Every formula in stereo, in projection, in undistortion, assumes it. ROS defines
both frames so that neither community has to bend: the robot model gets its x
forward frame, and the vision code gets its z forward frame, joined by one fixed
rotation.

That rotation is bigger than people expect. Running it out, the
`camera_link → camera_optical_frame` transform is a rotation of exactly 120
degrees about the axis `(-0.5774, 0.5774, -0.5774)`. As a scalar-last quaternion
it is `(-0.5, 0.5, -0.5, 0.5)`, and as a URDF `rpy` it is
`(-π/2, 0, -π/2)`; those two were computed independently and agree. Applied to
the optical axes it maps optical x to camera_link `-y`, optical y to camera_link
`-z`, and optical z to camera_link `x`.

It is not a ninety degree turn, and describing it as one — as people often do —
under-states how far wrong the answer goes. It is the composition of two quarter
turns, and section 3.2 works out what it does to a point cloud.

### 2.3 Row-major and column-major

A matrix is a grid, and memory is a line. Laying the grid out along the line can
be done row by row, called **row-major**, or column by column, called
**column-major**. The stored numbers are the same numbers in a different order,
so reading a column-major buffer as row-major transposes the matrix — and the
transpose of a rotation matrix is its inverse, which means the arm turns the
wrong way rather than failing.

The two libraries under almost every robotics stack disagree, and both
disagreements are documented in their own source:

- Eigen, the C++ linear algebra library that MoveIt, PCL, Open3D and most C++
  robotics code build on, is column-major by default.
  [`Macros.h`](https://gitlab.com/libeigen/eigen/-/raw/master/Eigen/src/Core/util/Macros.h)
  defines `EIGEN_DEFAULT_MATRIX_STORAGE_ORDER_OPTION` as `Eigen::ColMajor`
  unless `EIGEN_DEFAULT_TO_ROW_MAJOR` is set, and the
  [storage orders page](https://gitlab.com/libeigen/eigen/-/raw/master/doc/StorageOrders.dox)
  explains both layouts with a worked example.
- NumPy is row-major by default. Creating `numpy.zeros((2, 3))` and inspecting
  its flags gives `C_CONTIGUOUS = True` and `F_CONTIGUOUS = False`, which is
  NumPy's way of saying row-major, checked here on NumPy 2.5.3.

In practice you meet this at a boundary where a buffer crosses between languages,
or where a library hands you a pointer rather than an object. Inside one library,
you are safe. The moment you write `numpy.frombuffer` or pass a raw pointer to
C++, you are asserting a layout, and nothing checks the assertion.

### 2.4 Euler angles, intrinsic and extrinsic

Three angles can describe any rotation, and this is the most dangerous
representation in the document. Three numbers are not enough information to
recover a rotation unless you also know four more things: which three axes, in
which order, whether each rotation is about the axes of the fixed parent frame or
about the axes that have already moved, and which of two valid solutions was
chosen.

Rotating about the axes of the original fixed frame is called **extrinsic**.
Rotating about the axes as they are carried along by the previous rotations is
called **intrinsic**. The same three numbers give different rotations under the
two readings.

REP 103 lists Euler angles last of four rotation representations and says why:
they are "generally discouraged due to having 24 'valid' conventions with
different domains using different conventions by default". Quaternions are listed
first, for being compact and having no singularities.

The libraries encode the choice in the case of the letters, and they do not
encode it the same way:

- SciPy uses **upper case for intrinsic and lower case for extrinsic**. Its
  source documents the sequence argument as "3 characters belonging to the set
  {'X', 'Y', 'Z'} for intrinsic rotations, or {'x', 'y', 'z'} for extrinsic
  rotations", and its own example contrasts `R.from_euler("ZYX", ...)` labelled
  intrinsic with `R.from_euler("zyx", ...)` labelled extrinsic.
- MuJoCo uses **lower case for intrinsic and upper case for extrinsic**, the
  exact opposite. The `eulerseq` compiler attribute in its XML reference is
  documented as "Lower case letters denote axes that rotate with the frame
  (intrinsic), while upper case letters denote axes that remain fixed in the
  parent frame (extrinsic)". The default is `"xyz"`, which is therefore
  intrinsic.

That single pair of facts is the reason to distrust your memory here. Two widely
used libraries assign opposite meanings to the same typographic signal, and both
are internally consistent and correctly documented.

URDF's `rpy` attribute is extrinsic, about the fixed parent axes, in the order x
then y then z. That is not asserted from memory: `setFromRPY` in
[`urdf_model/pose.h`](https://raw.githubusercontent.com/ros/urdfdom_headers/master/include/urdf_model/pose.h)
was evaluated on `(25°, 40°, 55°)` and produced
`(0.026222, 0.390098, 0.357954, 0.847942)`, which matches SciPy's
`from_euler('xyz', ...)` — extrinsic — to six decimal places, and matches
`from_euler('ZYX', [yaw, pitch, roll])` exactly as well, those two being the same
rotation stated two ways. MuJoCo's documentation says the same thing from the
other side: "The 'rpy' convention used in URDF corresponds to 'XYZ' in MJCF",
upper case, which in MuJoCo's lettering means fixed parent axes.

TF2 will hand you Euler angles if you ask, with the ambiguity visible in the
source. In
[`Matrix3x3.hpp`](https://raw.githubusercontent.com/ros2/geometry2/rolling/tf2/include/tf2/LinearMath/Matrix3x3.hpp),
`getRPY` is documented as "roll pitch and yaw about fixed axes XYZ", so it is
extrinsic and agrees with URDF. It also takes a `solution_number` argument,
"which solution of two possible solutions (1 or 2)", and it forwards to
`getEulerYPR`, whose own comment says "euler angles around YXZ" while its
parameters are named yaw about Z, pitch about Y and roll about X. The function is
correct; its comment is not self-consistent. Read the parameter names, and
notice that the branch immediately below them handles the case where the pitch is
at a singularity, which is gimbal lock happening in the library you are calling.

Use quaternions or matrices for anything a machine reads. Use Euler angles for
things a person reads, and label them with the convention on the same line.

### 2.5 Degrees and radians

This is the least interesting entry and it still costs people days.

REP 103 standardises on SI units, listing the metre for length and the radian for
angle. Everything in ROS that carries an angle carries radians.

Two concrete traps sit near that rule. MuJoCo's `compiler` element has an `angle`
attribute documented as `[radian, degree], "degree" for MJCF, always "radian" for
URDF` — so an MJCF model file defaults to degrees, and the same physical model
imported from URDF is forced to radians. And within OpenCV, which is otherwise a
radian library, `decomposeProjectionMatrix` and `RQDecomp3x3` are both documented
as returning "three Euler angles ... in degrees".

The failure is usually loud, which is the one mercy here. A joint commanded to 90
when it expected radians tries to travel 5156.6 degrees, which is 116.6 degrees
after wrapping and a long way past any joint limit. A joint commanded to 1.57
when it expected degrees moves 1.57 degrees instead of 89.95, which is a visibly
tiny motion. Neither is subtle once you look at the arm. The dangerous version is
a small angle used in a calculation rather than sent to a motor, where 0.5
radians and 0.5 degrees both look plausible: at a 600 mm reach they are 300.0 mm
and 5.2 mm of arc respectively.

### 2.6 Pre- and post-multiplication

Joining two transforms is not commutative. `A` then `B` is a different result
from `B` then `A`, in general, and both are valid transforms, so neither
raises.

The convention that matters is which side the new transform goes on. With column
vectors and the usual `point_in_parent = T · point_in_child` form, chaining from
base outwards means writing `base_T_tool = base_T_flange · flange_T_tool`, with
each new link appended on the right. Libraries that use row vectors reverse it.
Graphics code frequently uses row vectors; robotics code generally does not.

The reliable test is not to memorise a rule but to check the names line up. If
you write the two transforms as `a_T_b` and `b_T_c`, the adjacent letters must
match, and the product is `a_T_c`. `a_T_b · c_T_d` is meaningless however
plausible the code looks, and `b_T_c · a_T_b` is the swap that section 3.4
measures. This naming trick is the single cheapest habit in this document.

---

## 3. The bug class, in five instances

The five below come from different parts of the stack and they are the same bug.
Each one is a reading taken in one frame and used in another. In each one the
program runs, the numbers stay in range, and the answer is wrong.

All the figures in this section were produced by running the arithmetic with
NumPy 2.5.3 and SciPy 1.18.1.

### 3.1 The force guard that reads zero while the tool is pushed

A **wrench** is the six numbers a force-torque sensor reports: three of force and
three of torque. The sensor sits between the flange and the tool, and it reports
in its own frame, whose z axis conventionally runs along the tool axis.

A guarded move — described in [controlling the move](04_controlling-the-move.md)
— moves in a direction until something stops it. The obvious way to write the
stop condition is to watch the force along the tool axis, because for a top-down
insertion that is where the contact force appears. Written in code, that is the
z component of the wrench in the sensor frame.

Now change the task to a side grasp, where the tool approaches horizontally and
the contact pushes across the fingers rather than along the tool. Nine newtons of
contact force now arrive as `(-9, 0, 0)` in the sensor frame. The z component is
`0.0`. The magnitude is `9.0`. The guard watches z, sees zero, and keeps pushing.

Nothing in that program is broken. The sensor is accurate, the frame is correct,
the arithmetic is right. The reading was simply interpreted as "the force", when
it was only "the force along one particular axis of one particular frame". The
fix is to watch the magnitude, or to convert the wrench into the frame the task
actually cares about, and either way to say in the variable name which one you
did.

### 3.2 The point cloud that stands the scene on end

A **point cloud** is a list of three-dimensional points. A depth camera produces
one, and in ROS it arrives as a
[`sensor_msgs/PointCloud2`](https://raw.githubusercontent.com/ros2/common_interfaces/rolling/sensor_msgs/msg/PointCloud2.msg),
whose first field is a `std_msgs/Header` described in the message itself as
carrying "the coordinate frame ID (for 3d points)". Drivers stamp that header
with the optical frame, because the points were computed with the projection
maths of section 2.2.

Take a point 1.2 metres straight ahead of the lens. In the optical frame that is
`(0, 0, 1.2)`, because optical z is forward. Convert it properly and in
`camera_link` it is `(1.2, 0, 0)`, because camera_link x is forward. Use the
optical numbers as though they were already camera_link numbers and the point is
taken to be 1.2 metres straight *up*, because camera_link z is up. The two
interpretations are 1.697 metres apart.

Do that to a whole cloud and the effect is structural rather than random. A
table-top, which in optical coordinates is a set of points at roughly constant z,
becomes a set of points at roughly constant height in the mistaken reading —
that is, a wall standing in front of the camera. Every plane fit still converges.
Every clustering step still returns objects. A grasp planner given that cloud
produces confident, wrong, upright grasps.

The reason this is so easy to do is that the conversion is free to omit. Both
frames are at the same place, so the translation is zero, and a great deal of
code passes the points through untouched and only fixes the translation later.
The 120 degree rotation from section 2.2 is what is lost.

### 3.3 The quaternion read in the wrong order

Take a rotation of 90 degrees about z. In scalar-last order that quaternion is
`(0, 0, 0.7071, 0.7071)`.

Hand those four numbers to a library that reads scalar-first. It takes `w` to be
`0`, and `(x, y, z)` to be `(0, 0.7071, 0.7071)`. The result has a norm of
exactly `1.0`, so no normalisation check fires. It is a perfectly valid rotation:
180 degrees about the diagonal axis `(0, 0.7071, 0.7071)`. It is simply not the
rotation that was sent. The two differ by 120 degrees.

Applied to the unit vector along x, the correct rotation gives `(0, 1, 0)` and
the misread one gives `(-1, 0, 0)`. At a tool offset of 0.5 metres from the wrist,
those two orientations put the tool tip 707 millimetres apart.

This is the purest example of the class. There is no invalid state to detect. A
quaternion misread in the other order is still a unit quaternion, still a
rotation, still something every downstream function accepts. The only defence is
knowing which convention each side of the boundary uses, and section 2.1 lists
where to look it up for the four libraries you are most likely to be joining.

### 3.4 The pose composed in the wrong order

Take an arm whose flange sits 0.45 m out along x and 0.30 m up, yawed 60 degrees,
and a tool that extends 0.12 m along the flange z axis and is pitched 20 degrees
relative to it.

Composed correctly, as `base_T_flange · flange_T_tool`, the tool centre point
lands at `(0.45, 0.0, 0.42)` in the base frame.

Composed the other way round, as `flange_T_tool · base_T_flange`, it lands at
`(0.5255, 0.0, 0.248)`. The two are 187.8 millimetres apart and the orientations
differ by 19.9 degrees.

Both results are well inside the arm's workspace. Both pass a reach check. Both
are smooth, repeatable and stable, so a test that runs the same motion twice and
compares sees nothing. A person watching the arm sees it go to roughly the right
area and miss.

This one hides particularly well when the tool offset is small. Shrink the
offset to a few millimetres and the error shrinks with it, so the bug sits in the
code through development on a stub tool and appears when someone fits the real
gripper.

### 3.5 The roll, pitch and yaw read as intrinsic

A robot description gives a joint origin as `rpy = (25°, 40°, 55°)`. Section 2.4
established that URDF means extrinsic — about the fixed parent axes, x then y
then z.

Read the same three numbers as intrinsic, which is what `from_euler('XYZ', ...)`
does in SciPy, and you get a different rotation. The two differ by 45.007
degrees. A 0.30 metre tool offset ends up 167.9 millimetres from where it should
be.

The reason this instance is worth stating separately is that it is the one where
the two answers are closest together. A quaternion in the wrong order is wrong by
120 degrees and will usually look wrong. Forty-five degrees on a wrist frequently
looks like a calibration problem, and people spend days recalibrating a camera to
chase an error that was in a text file.

### 3.6 What the five have in common

Read the five again and the same four properties appear in each.

The reading is valid. In every case the number that came out of the sensor or the
file was correct, and the frame it was measured in was correct too.

The misuse is type-correct. Three floats went where three floats were expected,
four where four were expected. Nothing a compiler or a runtime checks was
violated.

The result is plausible. A unit quaternion, a reachable pose, a plane that fits,
a force of zero. Every value stayed inside the range a reviewer would accept.

The magnitude is large. 707 millimetres, 187.8 millimetres, 167.9 millimetres,
1.697 metres, or a guard that never fires. These are not tolerance problems. They
are the difference between working and not.

That combination is why the practices in section 4 are worth the small cost they
carry. You cannot test your way out of a bug whose output looks like success.

---

## 4. The practices that prevent it

None of the four below is clever. Their whole value is that they move the frame
from something you remember into something the code says.

### 4.1 Put the frame in the name

Name a variable for the frame it is expressed in, every time, in the variable
itself and not in a comment beside it.

The convention that pays for itself is `frame_thing` for a quantity and
`a_T_b` for a transform. So `base_grasp_pose` is a pose in `base_link`,
`optical_points` is a cloud in the camera optical frame, and `base_T_camera`
converts camera numbers into base numbers.

The reason to prefer the name over a comment is not tidiness. It is that the name
travels. A comment sits at the declaration; the variable is used forty lines
later, and in a different function, and passed to a third. When the line reads
`base_grasp = base_T_camera · camera_grasp` the letters line up and the statement
checks itself, in the way section 2.6 described. When it reads
`grasp = transform · grasp` there is nothing to check.

### 4.2 Convert at the boundary, and keep one frame inside

Pick one frame for each piece of the system to think in, convert everything on
the way in, and convert back only on the way out.

For arm work that frame is almost always `base_link`, because the arm's own
kinematics, joint limits and reach checks are expressed there. For perception it
is usually the camera optical frame up to the point where a detection becomes a
pose, and `base_link` from there on.

The gain is that the number of conversions in the program drops to the number of
boundaries, which is small and enumerable, instead of being scattered through
every function that touches a pose. A conversion you can point at is a conversion
you can test. The cost is one extra transform lookup at each boundary, which is
microseconds, and a small loss of precision from converting back and forth, which
is far below the millimetre this document is written about.

### 4.3 Never let a reading travel alone

A raw array from a sensor should not pass through more than one function before
its frame is attached to it. Either convert it, or wrap it in something that
carries the frame, but do not pass `(x, y, z)` down two more layers and expect
the fourth function to know where it came from.

This is the practice that catches the point cloud in section 3.2 and the wrench
in section 3.1, both of which are bugs of distance: the reading was correct where
it was taken and had lost its meaning by the time it was used. The function that
reads the driver knows the frame for certain. Every function after that is
guessing.

### 4.4 Why PoseStamped exists

ROS supplies two messages for a pose and the difference between them is exactly
this document's subject.

[`geometry_msgs/Pose`](https://raw.githubusercontent.com/ros2/common_interfaces/rolling/geometry_msgs/msg/Pose.msg)
is a `Point` and a `Quaternion`: seven numbers, described in the message file as
"a representation of pose in free space". Free space, with no statement of where
that space is measured from.

[`geometry_msgs/PoseStamped`](https://raw.githubusercontent.com/ros2/common_interfaces/rolling/geometry_msgs/msg/PoseStamped.msg)
is a `Header` and a `Pose`, described as "A Pose with reference coordinate frame
and timestamp". The
[`Header`](https://raw.githubusercontent.com/ros2/common_interfaces/rolling/std_msgs/msg/Header.msg)
contributes two fields and its own comment explains the purpose: it is "generally
used to communicate timestamped data in a particular coordinate frame", and its
`frame_id` is documented as the "transform frame with which this data is
associated".

What you lose by using a bare `Pose` is the ability for anything downstream to
transform it, check it, or complain. TF2 cannot convert a pose that does not say
what frame it is in, so the caller must supply that separately, which means the
frame is now carried in a parameter, a naming convention, or someone's head. The
same pairing exists across the message set: `WrenchStamped` wraps a `Wrench`, and
`PointCloud2` has a header built in because a cloud without a frame is not usable
at all.

The timestamp is the second half of the value and is easy to overlook. A frame on
a moving arm is only defined at an instant. A pose in `tool0` from 200
milliseconds ago is in a different place from a pose in `tool0` now, and only the
stamped version lets TF2 notice.

The same distinction appears outside ROS, and it is worth checking before you
adopt a library. PCL's point type carries a
[`PCLHeader`](https://raw.githubusercontent.com/PointCloudLibrary/pcl/master/common/include/pcl/PCLHeader.h)
with a `frame_id` field, commented "Coordinate frame ID". Open3D's
[`geometry::PointCloud`](https://raw.githubusercontent.com/isl-org/Open3D/main/cpp/open3d/geometry/PointCloud.h)
has four data members — `points_`, `normals_`, `colors_` and `covariances_` —
and no frame field of any kind. Open3D is an excellent library and this is a
reasonable design for what it is, but it means that the moment a cloud enters
Open3D its frame exists only in your code, and you are responsible for it until
the cloud comes back out.

---

## 5. How to check

Three techniques, in increasing order of how much they cost and how much they
prove. Each one is described with the jobs it suits and the jobs it cannot do,
because each has a range outside which it will quietly tell you nothing is wrong.

### 5.1 Interrogating TF2

TF2 is the ROS 2 library that stores every published transform and joins them on
request. It lives in [ros2/geometry2](https://github.com/ros2/geometry2). Three
of its tools answer three different questions.

`ros2 run tf2_ros tf2_echo` prints one transform repeatedly. Reading
[its source](https://raw.githubusercontent.com/ros2/geometry2/rolling/tf2_ros/src/tf2_echo.cpp)
shows what you get: a translation, the rotation "in Quaternion (xyzw)", the
rotation as roll-pitch-yaw in radians and again in degrees, and the full 4×4
matrix. It prints the convention next to the numbers, which is exactly the habit
section 4.1 asks of your own code. When the lookup fails it catches the
exception and prints the entire list of known frames, which is usually the
information you actually needed.

`ros2 run tf2_tools view_frames` listens to `/tf` and `/tf_static` for a few
seconds and renders the frame tree.
[The script](https://raw.githubusercontent.com/ros2/geometry2/rolling/tf2_tools/tf2_tools/view_frames.py)
builds a Graphviz `dot` file and converts it to a PDF, labelling every edge with
the broadcaster that publishes it, the average rate, the buffer length and the
timestamps of the oldest and most recent transforms. That labelling is the point:
two publishers fighting over one edge, or an edge arriving at 2 Hz when you
thought it was 100 Hz, show up immediately.

`ros2 run tf2_ros tf2_monitor` reports delays and publication rates on the
transform graph, which is the tool for the failures that are about time rather
than geometry.

Five jobs this suits:

- Finding out whether a frame you are about to look up exists at all, before you
  write the code that assumes it.
- Seeing which node publishes a given edge, when two are fighting over it.
- Confirming that a static transform you wrote into a description file is the one
  actually being broadcast.
- Reading a rotation in four representations at once, which makes an ordering or
  a degree-radian mistake obvious by comparison.
- Catching a transform that is stale, arriving late, or published at a rate too
  low for the motion you are running.

Five jobs it cannot do:

- It cannot tell you that a transform is *wrong*. A confidently mismeasured
  camera mount prints as cleanly as a correct one.
- It cannot see any frame that was never published, including every frame that
  exists only inside a single program.
- It cannot detect a frame mix-up inside your own process, where the numbers
  never enter the transform graph.
- It cannot tell you which convention a third-party library used to produce a
  quaternion it handed you.
- It cannot resolve a units mistake, because it prints what was published and a
  millimetre published as a metre is a valid metre.

### 5.2 The known object in a known place

Put a real object at a measured place, measure it with a ruler, and compare.
Fix a calibration target or a machined block to the table at a known offset from
the arm's base, then have the system report where it thinks the object is.

This is the only check on this list that can find an error in the transforms
themselves rather than in how you used them, because it is the only one that
consults reality. It is also the check that separates a frame error from a
calibration error, which matters because they produce the same symptom. A frame
error is usually large, structured and identical every time — 90 degrees, 120
degrees, a swap of two axes, a factor of a thousand. A calibration error is small
and varies with pose; [the sensors
document](../06_object-perception/02_sensors.md) puts careful hand-eye
calibration at around 0.9 mm of translation error and a quarter of a degree of
rotation. If your error is 170 millimetres, stop recalibrating and go and read
section 2.

Five jobs this suits:

- Deciding whether the problem is a frame convention or a calibration, before
  spending days on the wrong one.
- Validating a whole chain end to end, including every transform you did not
  write and cannot see.
- Catching a units error, because a factor of a thousand is unmistakable against
  a ruler.
- Establishing a number you can put in a commissioning document and re-measure
  in six months.
- Finding an axis swap, because moving the object 100 mm along the table's x and
  watching the reported y change says exactly what happened.

Five jobs it cannot do:

- It cannot run in continuous integration, or at all without a physical cell and
  a person.
- It cannot separate two errors that partly cancel, which is common once someone
  has already "fixed" one of them.
- It cannot find an error that only appears at poses you did not test, which
  includes most orientation errors if you only test near one orientation.
- It cannot beat the precision of your measurement, so it will not see anything
  below roughly a millimetre without proper metrology.
- It cannot tell you which link in the chain is wrong, only that the chain is.

### 5.3 The unit vector probe

Apply the transform you are unsure about to `(1, 0, 0)`, then to `(0, 1, 0)`,
then to `(0, 0, 1)`, and read the three answers. Each one tells you where one
axis of the source frame ends up in the target frame, and between them they are
the whole rotation, written in a form you can check against a physical
expectation.

Section 2.2 is the worked example. Probing the `camera_link → camera_optical_frame`
transform gives optical x to `(0, -1, 0)`, optical y to `(0, 0, -1)` and optical
z to `(1, 0, 0)`. Read that as three sentences: the optical frame's "right" is
the camera_link frame's "minus y", which is right; its "down" is "minus z", which
is down; its "forward" is "x", which is forward. Three lines of arithmetic
confirm a convention that would otherwise be a quaternion you have to trust.

Five jobs this suits:

- Confirming that a transform you just built does what its name says, in three
  lines and no hardware.
- Checking a convention conversion you wrote yourself, such as scalar-first to
  scalar-last.
- Spotting an inadvertent transpose, because a transposed rotation sends the axes
  somewhere obviously different.
- Writing an assertion that stays in the test suite and fails the day someone
  changes a description file.
- Explaining a rotation to a colleague, since three axis images are far easier to
  argue about than four quaternion components.

Five jobs it cannot do:

- It says nothing about translation, so a transform with a correct rotation and a
  wrong offset passes.
- It cannot tell you whether the transform is the one the task needed, only what
  it does.
- It cannot detect a direction mix-up on its own, since a transform and its
  inverse both produce tidy-looking axis images.
- It cannot find an error in data that never passes through that transform.
- It will not reveal a units error, because unit vectors have no scale to get
  wrong.

---

## 6. Units and scale

REP 103 fixes the metre and the radian as the units for everything in ROS. The
conflict is with hardware and with computer aided design, which mostly work in
millimetres, and with the vendor interfaces that follow their hardware.

A factor of a thousand is the easiest error in this whole document to spot and
one of the most common to make. It is easy to spot because nothing else in a
table-top robot cell is off by three orders of magnitude: a reach of 350 is
obviously not metres and a reach of 0.35 is obviously not millimetres, and every
reach check, joint limit and collision box rejects the wrong one immediately.

It is common because the conversion sits at exactly the boundaries section 4.2
describes and there are many of them. A mesh exported from CAD in millimetres and
referenced by a URDF that assumes metres gives a gripper a thousand times too
large. A vendor motion interface that takes millimetres, called from ROS code
holding metres, sends a 0.35 mm move where 350 mm was meant — and that one is
quiet, because a very small move looks like a stalled arm rather than a crash.

Treat the unit exactly like the frame. Put it in the name when it is not the
project default, so `reach_mm` stands out against everything else being in
metres, and convert at the boundary rather than at the point of use. The habit is
the same habit, and so is the reason for it: the information that would catch the
mistake has to be in the code rather than in your memory of what the vendor
document said.

---

## 7. Sources and licences

Every convention above was read from one of the sources below rather than
recalled. The table lists each one with the licence of the project it belongs to,
read from that project's own licence file, and what it was used for here. Read
it as a list of places to look things up yourself, because a convention you check
takes a minute and a convention you assume costs a day.

| Source | Licence | What it settles here |
| --- | --- | --- |
| [REP 103](https://github.com/ros-infrastructure/rep/blob/master/rep-0103.rst) | the REP repository publishes no licence file | SI units, right-handed frames, x forward y left z up, the `_optical` suffix convention, and the ranking that puts Euler angles last |
| [ros2/geometry2](https://github.com/ros2/geometry2) | BSD-3-Clause, from `LICENSE` | TF2's target and source argument meanings, `tf2_echo` output, `view_frames` output, and `getRPY` being about fixed axes |
| [ros2/common_interfaces](https://github.com/ros2/common_interfaces/blob/rolling/geometry_msgs/LICENSE) | Apache-2.0, from `geometry_msgs/LICENSE` | the field order of `Quaternion`, and what `PoseStamped` adds to `Pose` |
| [ros/urdfdom_headers](https://github.com/ros/urdfdom_headers) | BSD, from `LICENSE` | URDF's quaternion order and the exact meaning of `rpy` |
| [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) | Apache-2.0, from `LICENSE` | scalar-first quaternions, `eulerseq` lettering, and degrees defaulting for MJCF but not URDF |
| [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) | BSD-3-Clause, from `LICENSE` | the 3.0 change from scalar-first to scalar-last, and what it breaks |
| [scipy/scipy](https://github.com/scipy/scipy) | BSD-3-Clause, from `LICENSE.txt` | `scalar_first`, and upper case meaning intrinsic |
| [opencv/opencv](https://github.com/opencv/opencv) | Apache-2.0, from `LICENSE` | the pinhole model that makes the optical frame z forward, and the two functions that return degrees |
| [libeigen/eigen](https://gitlab.com/libeigen/eigen) | MPL-2.0, from `COPYING.README` | column-major being the default |
| [PointCloudLibrary/pcl](https://github.com/PointCloudLibrary/pcl) | BSD, from `LICENSE.txt` | `PCLHeader` carrying a `frame_id` |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | MIT, from `LICENSE` | `PointCloud` carrying no frame at all |

Two of those licences are worth a second look before you ship. Eigen is
MPL-2.0, not BSD, and its own `COPYING.README` warns that some optional external
dependencies such as FFTW and MPFR C++ are under different licences including the
GPL. The `geometry_msgs` package is Apache-2.0 while the TF2 code that consumes
it is BSD-3-Clause; both are permissive, but the ROS message packages and the ROS
libraries are not uniformly licensed and it is a mistake to assume they are.
GitHub's automatic licence detection reported no SPDX identifier for NumPy, PCL,
Open3D and urdfdom_headers, so those four were read as text: NumPy carries the
three-clause BSD text, PCL and urdfdom_headers carry BSD licence agreements, and
Open3D carries the MIT licence.

Where to go next. [Position, frames and transforms](../03_arm/01_overview.md) is
the place to go if anything above was assumed rather than explained; it builds the
maths from nothing. [Reaching and reachability](02_reaching-and-reachability.md)
is where a pose in the right frame meets the question of whether the arm can get
to it. [Controlling the move](04_controlling-the-move.md) covers force control
and guarded moves, which is where the wrench of section 3.1 is actually used.
And [the sensors document](../06_object-perception/02_sensors.md) covers
calibration, which is how the transforms this document assumes get measured in
the first place.
