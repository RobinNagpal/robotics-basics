# Version 1: standing glasses upside down on a rack

This document is the build order for the first working version of the glass job. It
says what happens first, what happens next, and which named tool does each step. It is
written to be followed rather than admired, and it is deliberately the simplest version
that does something useful.

The job is this. Glasses are standing on a table. A drying rack stands somewhere on the
same table with six slots in it. The robot has to pick up each glass, turn it over,
stand it mouth-down in a free slot, and say when each one is done.

Two things are left out of this version on purpose. Water is one: here every glass is
assumed to be empty, and nothing checks for liquid. That check is real work — a camera
pass, a weight gate per glass type, and a rule about what to do with a full one — and
it is the first thing to add in version 2.
[The case study](01_place-glass.md) explains how. Learning a skill from demonstrations
is the other, and it is further off still.

This is for somebody about to build the thing. The design reasoning behind the choices
— why a depth camera cannot see a glass, why the turn has to be planned backwards, what
the grip force window is — lives in [the case study](01_place-glass.md), which is the
longer document this one condenses. Read that if you want the argument. Read this if
you want the sequence.

## Contents

1. [What we know and what we do not](#1-what-we-know-and-what-we-do-not)
2. [The shape of the solution](#2-the-shape-of-the-solution)
3. [What you write down before the robot moves](#3-what-you-write-down-before-the-robot-moves)
4. [Where to hold each glass, and how hard to squeeze](#4-where-to-hold-each-glass-and-how-hard-to-squeeze)
5. [The workflow, step by step](#5-the-workflow-step-by-step)
6. [Every tool in one table](#6-every-tool-in-one-table)
7. [How the robot reports each glass](#7-how-the-robot-reports-each-glass)
8. [When a step fails](#8-when-a-step-fails)
9. [Build it in this order](#9-build-it-in-this-order)
10. [Where to read more](#10-where-to-read-more)

---

## 1. What we know and what we do not

The split between the two decides almost every choice further down. Anything in the
first column can be written in a file. Anything in the second column has to be worked
out by a camera or a sensor, every single run.

| Known in advance | Not known until the robot looks |
| --- | --- |
| The five glass types and their measurements | How many glasses are on the table |
| The weight of each type | Which types are on the table this time |
| The rack has six slots, and how far apart they are | Where each glass is standing |
| The height of the rack and the size of a slot | Which way a handle is pointing |
| Where the arm and the table camera are bolted | Where the rack is on the table |
| Where to hold each type, and how hard | Which slots are already taken |

The five types are a straight glass, such as a rocks or vodka glass; a wine glass with
a bowl, a stem and a foot; a glass with a handle, such as a beer mug; a milkshake
glass, tall with sloping walls; and an Irish coffee glass, which is short-stemmed and
often has a small handle.

Two entries in the right-hand column are the ones that shape the whole design. Because
the number of glasses is unknown, the robot cannot make one plan at the start and
follow it; it has to look, do one glass, and look again. Because the rack position is
unknown, every slot position has to be worked out from something the camera can find,
not from a constant in the code.

---

## 2. The shape of the solution

The robot runs one loop, and the loop handles one glass from start to finish before it
looks at the table again.

```
find the rack, and which of its six slots are free
look at the table and list the glasses, with a type for each
while there is a glass on the table and a free slot:
    choose the next glass, and the slot it will go in
    pick it up using the recipe for its type
    lift it clear and check its weight      # is this the glass we think it is?
    turn it 180 degrees, mouth down
    lower it into the slot until it touches
    let go, retreat, and check it is standing
    report this glass as done
    look at the table again
report what is left and why
```

Looking again after every glass costs a second or two and is worth it. Glasses get
nudged, a person puts another one down, and a glass that slipped in the fingers is
back on the table in a place nobody planned for. A plan made once at the start would
be wrong by the third glass.

---

## 3. What you write down before the robot moves

Two files, written by a person with a ruler and a kitchen scale, before any code runs.

### The glass library

One record per type. The numbers below are an example set, and the only honest thing
to do with them is measure your own. What matters is the list of fields, because every
field is read by a step further down.

| Type | Rim across | Height | Weight | Hold it by |
| --- | --- | --- | --- | --- |
| Straight glass | 80 mm | 90 mm | 250 g | the side wall, low down |
| Wine glass | 85 mm | 200 mm | 180 g | the stem |
| Handled glass | 75 mm | 130 mm | 420 g | the wall opposite the handle |
| Milkshake glass | 90 mm | 175 mm | 300 g | the wall, low down where it is most upright |
| Irish coffee glass | 70 mm | 150 mm | 220 g | the bowl, just above the foot |

Each record also needs the numbers the arm uses directly: how far up the glass to close
the fingers, how wide the fingers should be at that height, how hard to squeeze, which
direction to come in from, and how wide the glass is when it is standing upside down.
That last one decides which slots it can use.
[Section 4](#4-where-to-hold-each-glass-and-how-hard-to-squeeze) is about where those
numbers come from, because they are the ones people leave until last and then guess.

Each type is awkward in its own way, and the awkwardness is the reason the record
exists rather than a single routine for all five.

| Type | What makes it different | What the recipe does about it |
| --- | --- | --- |
| Straight glass | nothing, it is a cylinder with straight walls | the plain case, build this one first |
| Wine glass | a thin bowl that cracks, on a narrow stem | close on the stem, which is strong, the same diameter on every wine glass, and clear of the bowl |
| Handled glass | the handle sticks out and can hit a neighbour | perception must report which way the handle points, and the placement turns it outward |
| Milkshake glass | sloping walls, so parallel fingers slide up the taper as they close | grip low, where the wall is most vertical, and stop on force rather than on width |
| Irish coffee glass | short stem, thin glass, sometimes a handle | treat it as the wine glass recipe with the handle rule of the mug |

### The rack file

The rack is known but its place on the table is not. So the file holds the rack's own
measurements — six slots, the spacing between them, the slot height, and where each
slot sits relative to a corner of the rack. At run time the camera finds the rack once
and every slot position follows from that one measurement.

Spacing is what limits how a slot can be used. With slots 100 mm apart, a straight
glass 80 mm across leaves 10 mm of clearance on each side. Because the glass is tall,
that budget is spent by tilt faster than by position: the arm can be out by 10 mm
sideways, or it can be tilted by `atan(10 / 90)`, which is 6.3 degrees, and not both.
For the milkshake glass, 90 mm across and 175 mm tall, the same sum gives 1.6 degrees,
which no arm should be asked for. So the rack file also says which types have to skip
a slot. Leaving a gap next to the milkshake glass turns 1.6 degrees into 17.4 degrees,
and that is a placement that works.

---

## 4. Where to hold each glass, and how hard to squeeze

Two numbers decide whether a glass survives being picked up: the spot where the fingers
close on it, and how hard they close. Both are different for each of the five types.
This section says where those numbers come from, how the arm turns them into a real
position above a real table, and how it checks afterwards that it got it right.

The short answer to "how does the arm know?" is that it does not work it out. A person
measures it once per type and writes it in the glass library, and the arm looks it up.
Nothing here is learned or guessed at run time.

### Why one answer does not fit all five

Imagine holding each of these yourself, with two fingers and your eyes shut.

- The **straight glass** is easy. It is a tube. Anywhere on the side works.
- The **wine glass** is not. The bowl is thin and will crack. The stem is narrow,
  strong, and always about the same thickness. You would hold the stem, and so does
  the robot.
- The **handled glass** has a lump sticking out of it. Close your fingers in the wrong
  direction and one of them lands on the handle, so the glass is held by its handle at
  an angle nobody planned. You have to come in square to the handle, which means the
  robot has to know which way the handle is facing.
- The **milkshake glass** is a cone. Squeeze a cone with two flat fingers and it
  squirts upwards out of your grip, the way a wet bar of soap does. You hold it low
  down, where the sides are closest to vertical.
- The **Irish coffee glass** is a small wine glass with thicker walls. Hold the bowl
  just above the foot, where the glass is at its strongest.

A single rule — "close on the middle of the object at ten newtons" — breaks the wine
glass, drops the milkshake glass, and lands on the mug handle. That is the whole
argument for one record per type.

### The three rules that pick the spot

In this order, because they sometimes disagree and the earlier rule wins.

1. **Hold the end that becomes the top after the turn.** The glass is going to be
   turned upside down, so whatever the fingers are holding ends up in the air. Hold it
   low, near its base, and after the turn the fingers are high above the rack instead
   of in among the pegs and the neighbouring glasses.
2. **Hold the strongest part.** Thin bowls crack. Stems, thick walls and the area just
   above a foot do not.
3. **Hold where the wall is straight up and down.** Two flat fingers closing on a
   slope push the glass along that slope. On a vertical wall they just press.

Applying those three rules to the five types gives the numbers below. Height is
measured up from the table, and the opening is how far apart the fingers should be when
they touch. As before, these are an example set: measure your own glasses.

| Type | Close the fingers this high up | Fingers this far apart | Come in from |
| --- | --- | --- | --- |
| Straight glass | 30 mm | 78 mm | any side |
| Wine glass | 90 mm, on the stem | 9 mm | any side |
| Handled glass | 40 mm | 72 mm | square to the handle |
| Milkshake glass | 40 mm | 60 mm | any side |
| Irish coffee glass | 60 mm | 62 mm | square to the handle, if it has one |

Two of those rows are worth a second look. The wine glass opening is 9 mm rather than
85 mm, because the fingers are on the stem and not on the bowl. And the milkshake
opening is 60 mm even though the rim is 90 mm, because the glass is much narrower at
the bottom than at the top, and 40 mm up is near the bottom.

### How the arm turns that into a place in the room

The record says something like "40 mm up, fingers 72 mm apart, come in square to the
handle". That is a description of a spot on the glass, not a spot on the table. Three
things together turn one into the other.

| What the arm needs | Where it comes from |
| --- | --- |
| Which record to read | the type, from the segmentation model in step 2 |
| Where the base of this glass is sitting | the outline from the same model, met with the table plane from the depth camera |
| Which way it is turned | only matters for a handle: the handle is the bit of the outline that sticks out of the circle |

Add the three together and you have a target pose — a position and a direction — in the
robot's own coordinates, which is the only language the planner speaks.
[MoveIt 2](https://github.com/moveit/moveit2) then finds a path to it that does not go
through the table or the other glasses.

For four of the five types the direction does not matter, so the robot is free to pick
the approach that keeps the arm away from neighbouring glasses. For the mug it is not
free, and that single difference is why perception has to report a rotation rather than
just a point.

### How hard to squeeze, and where that number comes from

A glass held between two fingers is not sitting on anything. It hangs there, and the
only thing stopping it sliding down is friction — the grip between the rubber pad and
the glass. Press harder and there is more friction. Press too hard and the glass
cracks. The right force is the smallest one that is safely above sliding.

You can calculate the lower end of that. In words:

> the force each pad presses with = (the weight of the glass × a safety factor)
> ÷ (2 × the grip factor)

Taking each piece in turn. The **weight** in newtons is the mass in kilograms times
9.81, so a 250 g glass weighs 2.45 N. The **2** is there because two pads are each
doing half the holding. The **grip factor** is how grippy the pad is against glass;
for a soft silicone pad on dry glass, 0.6 is a reasonable figure to start from and a
figure you should measure. The **safety factor** of 2 means you squeeze twice as hard
as the sum says, which covers a small knock and a slightly greasy glass.

For the straight glass that is 2.45 × 2 ÷ (2 × 0.6) = 4.1 N, so 4 N per pad. The same
sum for the other four gives this, and again these are numbers for the example glasses:

| Type | Weight | Force per pad |
| --- | --- | --- |
| Straight glass | 250 g | 4 N |
| Wine glass | 180 g | 3 N |
| Handled glass | 420 g | 7 N |
| Milkshake glass | 300 g | 7 N |
| Irish coffee glass | 220 g | 4 N |

The milkshake glass is the one that does not follow the sum. It works out at 5 N, and
the table says 7 N, because the sloping wall is also trying to push the glass out of
the grip and that has to be paid for. Half again is a sensible allowance.

Three things about these numbers matter more than the numbers themselves.

- **This is the floor, not the ceiling.** The sum tells you the least you can squeeze.
  The most you can squeeze is whatever cracks the rim, and you do not measure that,
  because measuring it costs a glass every time. So set the force from the sum, watch
  ten picks, and raise it by one newton at a time only if something slips.
- **A wet glass is a different glass.** Water roughly halves the grip factor, so it
  roughly doubles the force needed, and that can push you up near the cracking end.
  This is why the pads are soft silicone rather than hard plastic: grippier pads mean
  less force for the same hold.
- **Heavier is not automatically stronger.** The mug needs 7 N because it is heavy.
  The wine glass needs 3 N because it is light. If you gave the wine glass the mug's
  number you would be squeezing a thin stem more than twice as hard as it needs.

### How the number gets into the gripper

Command a force, not a width. The fingers close, the force builds, and the controller
stops when it reaches the number from the record. That is
[gripper_controllers](https://control.ros.org/jazzy/doc/ros2_controllers/gripper_controllers/doc/userdoc.html)
in [ros2_controllers](https://github.com/ros-controls/ros2_controllers), driven by
[ros2_control](https://github.com/ros-controls/ros2_control), doing exactly what it is
for.

The obvious alternative is to command a width: "close to 72 mm". Do not. A width that
is right for a dry glass is too loose for a wet one, glasses of the same type vary by a
millimetre or two, and if perception was 3 mm out the fingers reach the commanded width
without ever touching the glass — and nothing reports a problem, because the gripper
did exactly what it was told.

### How the arm knows it got it right

Three checks, all using sensors the job already has, and all before anything is
irreversible.

| When | What to look at | What it tells you |
| --- | --- | --- |
| As the fingers close | the finger width at the moment the force arrives | matching the record means the glass is where perception said it was; closing further means nothing is there |
| Just after the lift | the twist in the wrist force sensor | an unexpected twist means the grip is off to one side, high, or low |
| Before the turn | tilt the glass 20 degrees slowly and watch the finger width | a width that creeps means it is sliding, while sliding is still recoverable |

A failed check costs one regrasp. Not checking costs a glass.

### Filling in the library for a new type

The whole of this section is one afternoon of work per type, and it goes like this.
Stand the glass on the table and measure its height and its rim. Decide the grip height
using the three rules. Measure how wide the glass is at exactly that height — that is
the finger opening. Weigh it, and put the weight through the sum to get a starting
force. Then run ten picks, and raise the force a newton at a time until none of them
slip. Write all of it into the file and never go looking for the force that breaks it.

---

## 5. The workflow, step by step

Each step below says what happens, what it uses, and how the robot knows the step
worked. The last part is what turns a demonstration into something you can leave
running.

### Step 1: find the rack and count the free slots

The robot takes one picture from the table camera and finds the rack in it. The
reliable way is a printed marker, an [AprilTag](https://github.com/AprilRobotics/apriltag),
glued to the rack base. A tag is a flat black-and-white pattern that a camera can
locate exactly, in position and in rotation, from one frame. Given the tag, every slot
position comes from the rack file.

Then it decides which slots are occupied. Run the same segmentation model used in step
2 over the rack region, and mark a slot as taken if a glass outline covers it. Six
slots is small enough that this is reliable.

**Uses:** [apriltag_ros](https://github.com/AprilRobotics/apriltag_ros) to read the
marker, running inside [ROS 2](https://docs.ros.org/en/jazzy/index.html), the Robot
Operating System; the table camera read through
[image_pipeline](https://github.com/ros-perception/image_pipeline), the ROS 2 packages
that turn a raw camera frame into a corrected one;
[YOLO segmentation](https://github.com/ultralytics/ultralytics) for occupancy.

**Confirmed by:** a tag pose that is within the table area and has not jumped since the
last cycle, and a free-slot count between zero and six. If the tag is not visible at
all, stop: there is nowhere to put anything.

### Step 2: find the glasses and say what each one is

One picture of the table, one pass of a segmentation model, and the result is an
outline and a type for every glass. Segmentation means the model returns the shape of
each object, not just a box around it, and outlines are what the next steps need.

A depth camera is nearly useless for the glass itself, because most of its light goes
straight through the glass and the rest is bent by the curved wall, so the depth
picture has a hole exactly where the glass is. Depth is still used, for the table
plane. The outline comes from the ordinary colour picture, and where the outline meets
the table plane is where the glass is standing.

**Uses:** [YOLO segmentation](https://github.com/ultralytics/ultralytics), trained on a
few hundred pictures of your own five types;
[SAM 2](https://github.com/facebookresearch/sam2), the Segment Anything Model, to
outline those training pictures quickly instead of drawing them by hand;
[Open3D](https://github.com/isl-org/Open3D) to fit the table plane and a cylinder to
each outline.

**Why this rather than the obvious alternative:** colour thresholding, which is how
most beginner pipelines find an object, has nothing to work with on something
transparent. It costs you a labelling job on your own table, and a component whose
reasoning you cannot read.

**Confirmed by:** every detection having a type, a position on the table plane, and a
cylinder fit that actually fits. A poor fit means it is not one of the five, and the
right response is to leave it alone.

### Step 3: choose the next glass and its slot

Now there is a list of glasses and a list of free slots, and something has to pair
them. Keep it simple and greedy: take the glass nearest the robot with nothing standing
between it and the arm, and give it the free slot whose neighbours are emptiest.

Two rules from the rack file apply here. Wide types need a gap beside them, so placing
one removes two slots from the list. And filling order matters: work outward from the
far end so that the glasses already placed are never between the arm and the next slot.

**Uses:** ordinary [Python](https://www.python.org/). This is arithmetic over six slots
and a handful of glasses, not a planning problem, and reaching for a solver here would
be a mistake.

**Confirmed by:** a chosen slot that is still free in this cycle's occupancy check.

### Step 4: pick it up

The arm goes to the grasp pose worked out in
[section 4](#4-where-to-hold-each-glass-and-how-hard-to-squeeze) and closes the fingers
at the force from that type's record.

One detail is easy to get wrong and expensive to discover late. Turn the wrist
backwards *before* closing the fingers, so that the 180 degrees of turn still fits
inside the wrist's travel. Most arms have a last joint that stops at about 175 degrees,
and a turn planned after the grasp is a turn that does not fit.

**Uses:** [MoveIt 2](https://github.com/moveit/moveit2) to plan the reach;
[MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) to plan
the grasp, the turn and the placement as one problem rather than three;
[gripper_controllers](https://control.ros.org/jazzy/doc/ros2_controllers/gripper_controllers/doc/userdoc.html)
in [ros2_controllers](https://github.com/ros-controls/ros2_controllers), commanded as a
force.

**Confirmed by:** the finger width when the force arrives, as in section 4.

### Step 5: lift it and check the weight

The arm lifts the glass clear of the table and holds still for a moment. The wrist
force sensor reads the weight of the glass plus the gripper, and subtracting the
gripper gives the glass. It should match the weight in the record for the type the
robot thinks it is holding.

This is the cheapest check in the whole job and it sits in the one place where a wrong
answer is still recoverable: the glass is in the air, but nothing has been turned over
yet. A weight that matches no record at all means the type is wrong, and the right
response is to put it back down and flag it.

**Uses:**
[force_torque_sensor_broadcaster](https://control.ros.org/jazzy/doc/ros2_controllers/force_torque_sensor_broadcaster/doc/userdoc.html),
which publishes the wrist force and twist as a ROS topic.

**Confirmed by:** the weight matching the record within a tolerance you set from how
much your own glasses of one type vary.

### Step 6: turn it over

The wrist rotates 180 degrees and the glass is now mouth-down. The move is planned as
part of step 4's problem, not as a separate one.

**Uses:** [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor).

**Confirmed by:** the wrist twist before and after. A change means the glass shifted in
the fingers, which is worth catching now rather than above the rack.

### Step 7: lower it into the slot

The arm moves above the chosen slot, then comes straight down, vertically. It does not
descend to a commanded height. It descends until the force sensor says the rim has met
the rack. The rack is light plastic and the exact height of its base is not worth
trusting to a measurement.

The descent must be vertical and upright. This is where the tilt budget from section 3
is spent, and a tilted descent is what knocks over the glass in the next slot.

**Uses:** the
[admittance_controller](https://control.ros.org/jazzy/doc/ros2_controllers/admittance_controller/doc/userdoc.html)
in [ros2_controllers](https://github.com/ros-controls/ros2_controllers), or
[cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers).
Either one moves on a force instead of to a position. The cost is a force reading you
trust plus an afternoon of tuning with nothing visible to show for it.

**Confirmed by:** contact force arriving within the expected range of heights. Too
early means it hit something that should not be there. Too late means the slot is not
where the rack file says.

### Step 8: let go, back off, and look

Before the fingers open, read the wrist force again. If the rack is now carrying the
glass, the load has gone. If it has not, the glass is hanging up on something and
opening the fingers will drop it — so lift away and try the slot again.

After the fingers open and the arm has retreated, take one more picture and ask the
step 2 model whether there is a glass standing in that slot.

**Uses:** the same force topic and the same segmentation model. Nothing new.

**Confirmed by:** the load transfer, then the picture. Both have to agree before the
glass is counted.

### Step 9: report and loop

Publish one message for this glass, then go back to step 1. When there are no glasses
left on the table, or no free slots left, stop and publish a summary.

---

## 6. Every tool in one table

This is the whole shortlist in one place. Read it as one row per job: what we use, and
the obvious alternative we are not using, with the reason we are not.

| Job | What we use | Rather than |
| --- | --- | --- |
| Run everything and let the parts talk | [ROS 2](https://docs.ros.org/en/jazzy/index.html), the Robot Operating System | writing your own message passing, and then your own tooling for it |
| Describe the arm | [URDF](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html), the Unified Robot Description Format | a bespoke model that no other tool can read |
| Try it before the hardware exists | [Gazebo](https://github.com/gazebosim/gz-sim) | [MuJoCo](https://github.com/google-deepmind/mujoco), whose contact model is better but which makes cameras and ROS harder, and here those matter more |
| Find the rack | an [AprilTag](https://github.com/AprilRobotics/apriltag) marker read by [apriltag_ros](https://github.com/AprilRobotics/apriltag_ros) | recognising the rack itself, which is more work for a thing you are allowed to glue a marker to |
| Get corrected pictures out of the camera | [image_pipeline](https://github.com/ros-perception/image_pipeline) | opening the camera device yourself, and then writing your own lens correction |
| Find the glasses and their type | [YOLO segmentation](https://github.com/ultralytics/ultralytics) | colour thresholding, which has nothing to work with on a transparent object |
| Label the training pictures | [SAM 2](https://github.com/facebookresearch/sam2) | outlining a few hundred glasses by hand |
| Fit the table plane and the glass shape | [Open3D](https://github.com/isl-org/Open3D) | [PCL](https://github.com/PointCloudLibrary/pcl), the Point Cloud Library, which is capable and heavier than this needs |
| Plan reach, turn and place as one | [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) | planning each stage on its own, and discovering that the grasp makes the turn impossible |
| Plan an ordinary move | [MoveIt 2](https://github.com/moveit/moveit2) | hand-written waypoints, which stop working the day the rack moves |
| Drive the joints | [ros2_control](https://github.com/ros-controls/ros2_control) | your own control loop, where the hard part is the timing |
| Squeeze without breaking | the gripper controller in [ros2_controllers](https://github.com/ros-controls/ros2_controllers), commanded as a force | commanding a finger width, which is wrong for a wet glass and wrong for a tapered one |
| Check the weight | [force_torque_sensor_broadcaster](https://control.ros.org/jazzy/doc/ros2_controllers/force_torque_sensor_broadcaster/doc/userdoc.html) in the same package | a scale in the table, which cannot weigh a glass the arm is already holding |
| Come down onto the rack | the [admittance_controller](https://control.ros.org/jazzy/doc/ros2_controllers/admittance_controller/doc/userdoc.html), or [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | commanding a height into a rigid plastic base |
| Sequence the steps and recover | [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | a state machine, which becomes unreadable as soon as recovery branches multiply |
| Hold the per-type numbers | one file, one record per type | constants spread through the code |
| Record every attempt | [rosbag2](https://github.com/ros2/rosbag2), which ships with ROS 2 | log lines, which cannot show you the frame before the drop |

Two of these carry a real cost. MoveIt Task Constructor is a noticeably steeper climb
than plain MoveIt, and you can put it off until the turn actually fails to plan.
BehaviorTree.CPP adds a second language, written in XML, that anybody reading your
logic has to learn first.

The hardware is shorter. A two-finger parallel gripper with soft silicone pads, because
the pads raise friction and friction is the only thing that lets you hold a glass
gently, as
[section 4](#4-where-to-hold-each-glass-and-how-hard-to-squeeze) works through; suction
is no use on a curved, inverted object. A camera above the table, and a second on the
wrist, because the wrist camera removes the camera-to-arm calibration error on the last
few centimetres, and that is the error that actually sinks this task. And a force
reading at the wrist, needed twice: to check the weight and to stop the descent.

---

## 7. How the robot reports each glass

The requirement is a confirmation per glass, one by one. That is a
[ROS 2 action](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Actions.html), not a
topic. An action is the ROS call that runs for a while, sends progress while it runs,
and ends in success or failure — which is the shape of this job exactly.

Define one action for one glass. The goal names the glass and the slot. The feedback
says which step is running. The result says what happened.

| Field | What it carries |
| --- | --- |
| Goal | the glass identifier, its type, and the slot chosen for it |
| Feedback | the current step, the measured weight, the measured finger width |
| Result | placed, refused as unrecognised, or failed at step N |

A refusal is a result, not an error. A glass the robot did not recognise and left alone
is the system working, and it should be reported in the same words every time so that a
day's log can be counted.

Record every attempt with [rosbag2](https://github.com/ros2/rosbag2): the camera
frames, the force trace, the finger width, and the planned and actual poses. Without
them, a failure next month is a story rather than a bug.

---

## 8. When a step fails

Decide these before writing the code, because they change its shape.

| What happens | What the robot does |
| --- | --- |
| No glass where perception said | abandon this glass, take a new picture, carry on |
| Fingers close further than the record says | open, abandon this glass, take a new picture |
| Weight matches no record | put it back, mark it unknown, leave it for a person |
| Glass shifts in the fingers | put it down and grasp again, at most twice |
| Rim meets the rack too early | lift away, try the same slot once, then mark the slot bad |
| Load does not transfer before release | do not open the fingers, lift away, try again |
| Nothing standing in the slot afterwards | stop the cell and call a person |
| Anything breaks | stop the cell and call a person |

The last two are deliberately blunt. Broken glass leaves shards, and an arm that will
carry on moving through them, so a drop is never a retry. Stopping and calling somebody
is the correct response, and deciding that now changes the shape of the recovery code
you write.

---

## 9. Build it in this order

Four sittings, each of which ends with something that runs.

1. **One straight glass, everything known.** Mark a spot on the table, measure the rack
   once, and hard-code both. No camera. This gets the grasp, the turn, the force
   descent and the release working, and it is the rig on which everything else is
   tested. Do it in [Gazebo](https://github.com/gazebosim/gz-sim) first, where a
   dropped glass costs nothing.
2. **Add the camera.** Steps 1 to 3 of section 5, so the glass can be anywhere and the
   rack can be anywhere. This is where most of the work is.
3. **Add the other four types.** Write the library, replace every constant in step 1
   with a lookup, and add the per-type grip points, forces and slot rules from
   section 4.
4. **Add the reporting and the recovery.** Section 7 and section 8, moved into a
   behaviour tree. Only now is it something you can leave running.

Do not start one of these until the previous one fails for a reason you can say out
loud. Getting the grip force from the simulator is the one thing that will not work:
rigid fingers on a thin rigid shell is close to the worst case for a physics engine, so
take the reach, the planning and the clearances from simulation, and get the grip from
a real glass.

After all four, the next version is the one that deals with water, and
[the case study](01_place-glass.md) is where that is worked out.

---

## 10. Where to read more

- [The case study](01_place-glass.md) is the reasoning behind every choice here,
  including [what to use for each job](01_place-glass.md#4-which-part-uses-what),
  [where to hold a glass and why the middle is wrong](01_place-glass.md#where-to-hold-it),
  and [what to do about a glass with no record](01_place-glass.md#5-when-an-unfamiliar-glass-turns-up).
  It is also where the water checks left out of this version are explained.
- [Tools and libraries](../../06_tools-and-libraries.md) explains each of the tools in
  section 6 properly, with code, including
  [MoveIt 2](../../06_tools-and-libraries.md#5-moveit-2-planning-a-safe-path),
  [ros2_control](../../06_tools-and-libraries.md#6-ros2_control-driving-the-motors) and
  [behaviour trees](../../06_tools-and-libraries.md#11-behaviour-trees-putting-a-task-in-order).
- [Programmed methods](../02_programmed-methods.md) covers the
  [force control](../02_programmed-methods.md#6-feedback-control) that steps 4, 5, 7
  and 8 all depend on.
- [One-arm training](../01_overview.md) is the map of every other way this job could
  have been built, and
  [why the programmed route suits this one](../01_overview.md#5-which-method-for-which-task).
