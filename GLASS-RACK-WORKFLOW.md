# Workflow: clearing a table of empty glasses onto a rack

This document is the build order for one job. It says what happens first, what
happens next, and which named tool does each step. It is the plainest version of the
plan, written to be followed rather than admired.

The job is this. Glasses are standing on a table. Some are empty and some still have
water in them. A drying rack stands somewhere on the same table with six slots in it.
The robot has to pick up each empty glass, turn it over, stand it mouth-down in a free
slot, and say out loud when each one is done. The glasses with water in them must be
left where they are.

This is for somebody about to build the first version. The design reasoning behind the
choices — why a depth camera cannot see a glass, why the turn has to be planned
backwards, what the grip force window is — lives in
[the case study](docs/07_one-arm-training/07_case-study/01_place-glass.md), which is
the longer document this one condenses. Read that if you want the argument. Read this
if you want the sequence.

## Contents

1. [What we know and what we do not](#1-what-we-know-and-what-we-do-not)
2. [The shape of the solution](#2-the-shape-of-the-solution)
3. [What you write down before the robot moves](#3-what-you-write-down-before-the-robot-moves)
4. [The workflow, step by step](#4-the-workflow-step-by-step)
5. [Every tool in one table](#5-every-tool-in-one-table)
6. [How the robot reports each glass](#6-how-the-robot-reports-each-glass)
7. [When a step fails](#7-when-a-step-fails)
8. [Build it in this order](#8-build-it-in-this-order)
9. [Where to read more](#9-where-to-read-more)

---

## 1. What we know and what we do not

The split between the two decides almost every choice further down. Anything in the
first column can be written in a file. Anything in the second column has to be worked
out by a camera or a sensor, every single run.

| Known in advance | Not known until the robot looks |
| --- | --- |
| The five glass types and their measurements | How many glasses are on the table |
| The empty and full weight of each type | Which types are on the table this time |
| The rack has six slots, and how far apart they are | Which of them have water in them |
| The height of the rack and the size of a slot | Where each glass is standing |
| Where the arm and the table camera are bolted | Where the rack is on the table |
| | Which slots are already taken |

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
drop the ones that look like they hold water
while there is an empty glass and a free slot:
    choose the next glass, and the slot it will go in
    pick it up using the recipe for its type
    lift it clear and weigh it            # last chance to notice water
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

Two checks for water sit in that loop rather than one. The first is the camera, which
is cheap and happens before anything is touched. The second is the weight, which is
certain but only available once the glass is off the table. Both come before the turn,
because after the turn the water is on the floor.

---

## 3. What you write down before the robot moves

Two files, written by a person with a ruler and a kitchen scale, before any code runs.

### The glass library

One record per type. The numbers below are an example set, and the only honest thing
to do with them is measure your own. What matters is the list of fields, because every
field is read by a step further down.

| Type | Rim across | Height | Empty | Full | Water gate | Hold it by |
| --- | --- | --- | --- | --- | --- | --- |
| Straight glass | 80 mm | 90 mm | 250 g | 600 g | 294 g | the side wall, low down |
| Wine glass | 85 mm | 200 mm | 180 g | 480 g | 218 g | the stem |
| Handled glass | 75 mm | 130 mm | 420 g | 820 g | 470 g | the wall opposite the handle |
| Milkshake glass | 90 mm | 175 mm | 300 g | 750 g | 356 g | the wall, where it is most upright |
| Irish coffee glass | 70 mm | 150 mm | 220 g | 500 g | 255 g | the bowl, above the foot |

The water gate is not measured, it is calculated: empty weight plus an eighth of the
difference between empty and full. That puts the line low enough that a mouthful of
water left in the bottom still fails it. It has to be one number per type, because a
full wine glass here weighs less than an empty straight glass — a single global
threshold would pass water through.

Each record also needs the numbers the arm uses directly: the height up the glass to
close the fingers, the width the fingers should reach at that height, the grip force,
the direction to approach from, and how wide the glass is when it is standing upside
down. That last one decides which slots it can use.

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

## 4. The workflow, step by step

Each step below says what happens, what it uses, and how the robot knows the step
worked. The last part is what turns a demonstration into something you can leave
running.

### Step 1: find the rack and count the free slots

The robot takes one picture from the table camera and finds the rack in it. The
reliable way is a printed marker, an [AprilTag](https://github.com/AprilRobotics/apriltag),
glued to the rack base. A tag is a flat
black-and-white pattern that a camera can locate exactly, in position and in rotation,
from one frame. Given the tag, every slot position comes from the rack file.

Then it decides which slots are occupied. Run the same segmentation model used in step
2 over the rack region, and mark a slot as taken if a glass outline covers it. Six
slots is small enough that this is reliable.

**Uses:** [apriltag_ros](https://github.com/AprilRobotics/apriltag_ros) to read the marker,
running inside [ROS 2](https://docs.ros.org/en/jazzy/index.html), the Robot Operating
System; the table camera read through
[image_pipeline](https://github.com/ros-perception/image_pipeline), the ROS 2 packages
that turn a raw camera frame into a corrected one;
[YOLO segmentation](https://github.com/ultralytics/ultralytics) for occupancy.

**Confirmed by:** a tag pose that is within the table area and has not jumped since the
last cycle, and a free-slot count between zero and six. If the tag is not visible at
all, stop: there is nowhere to put anything.

### Step 2: find the glasses and say what each one is

One picture of the table, one pass of a segmentation model, and the result is an
outline and a type for every glass. Segmentation means the model returns the shape of
each object, not just a box around it, and outlines are what the next step needs.

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

### Step 3: drop the ones that look full

The same model pass gives the water label, if you train it with two classes per type —
empty and full — rather than one. A water line in a glass is visible in an ordinary
picture, so this costs nothing beyond the labelling.

**Uses:** the step 2 model, with the classes doubled.

**Confirmed by:** nothing yet. This is a filter, not a decision. Anything it passes is
still weighed in step 6.

### Step 4: choose the next glass and its slot

Now there is a list of empty glasses and a list of free slots, and something has to
pair them. Keep it simple and greedy: take the glass nearest the robot with nothing
standing between it and the arm, and give it the free slot whose neighbours are
emptiest.

Two rules from the rack file apply here. Wide types need a gap beside them, so placing
one removes two slots from the list. And filling order matters: work outward from the
far end so that the glasses already placed are never between the arm and the next slot.

**Uses:** ordinary [Python](https://www.python.org/). This is arithmetic over six slots and a handful of glasses,
not a planning problem, and reaching for a solver here would be a mistake.

**Confirmed by:** a chosen slot that is still free in this cycle's occupancy check.

### Step 5: pick it up

The arm moves to the grasp pose from the type's record, and closes the fingers with a
commanded force rather than to a commanded width. Force is the right command because
the glass is what decides when to stop: too little and it slips, too much and the rim
cracks, and there is no width that is right for both a dry glass and a wet one.

Two details from earlier docs matter and are easy to get wrong. Hold the glass at the
end that becomes the *top* after the turn, so the fingers are nowhere near the rack
when it goes down. And turn the wrist backwards *before* closing, so that the 180
degrees of turn still fits inside the wrist's travel. Most arms have a last joint that
stops at about 175 degrees, and a turn planned after the grasp is a turn that does not
fit.

**Uses:** [MoveIt 2](https://github.com/moveit/moveit2) to plan the reach;
[MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor) to plan
the grasp, the turn and the placement as one problem rather than three;
[gripper_controllers](https://control.ros.org/jazzy/doc/ros2_controllers/gripper_controllers/doc/userdoc.html)
in [ros2_controllers](https://github.com/ros-controls/ros2_controllers), commanded as a
force.

**Confirmed by:** the finger width when the force arrives. If it matches the width in
the record, the glass is where perception said it was. If the fingers close further
than that, there is no glass there, and the cycle stops before the arm lifts nothing.

### Step 6: lift it and weigh it

The arm lifts the glass clear of the table and holds still for a moment. The wrist
force sensor now reads the weight of the glass plus the gripper, and subtracting the
gripper gives the glass. Compare it against the water gate for this type.

This is the check that cannot be fooled, and it sits in the one place where a wrong
answer is still recoverable: the glass is in the air but has not been turned. Over the
gate, put it back exactly where it came from and move on.

**Uses:**
[force_torque_sensor_broadcaster](https://control.ros.org/jazzy/doc/ros2_controllers/force_torque_sensor_broadcaster/doc/userdoc.html),
which publishes the wrist force and torque as a ROS topic.

**Confirmed by:** a weight that matches either the empty figure or the full figure for
the type the robot thinks it is holding. A weight that matches neither means the type
is wrong, and the right response is to put it down and flag it.

### Step 7: turn it over

The wrist rotates 180 degrees and the glass is now mouth-down. The move is planned as
part of step 5's problem, not as a separate one.

**Uses:** [MoveIt Task Constructor](https://github.com/moveit/moveit_task_constructor).

**Confirmed by:** the wrist torque before and after. A change in the moment means the
glass shifted in the fingers, which is worth catching now rather than above the rack.

### Step 8: lower it into the slot

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

### Step 9: let go, back off, and look

Before the fingers open, read the wrist force again. If the rack is now carrying the
glass, the load has gone. If it has not, the glass is hanging up on something and
opening the fingers will drop it — so lift away and try the slot again.

After the fingers open and the arm has retreated, take one more picture and ask the
step 2 model whether there is a glass standing in that slot.

**Uses:** the same force topic and the same segmentation model. Nothing new.

**Confirmed by:** the load transfer, then the picture. Both have to agree before the
glass is counted.

### Step 10: report and loop

Publish one message for this glass, then go back to step 1. When there are no empty
glasses left, or no free slots left, stop and publish a summary.

---

## 5. Every tool in one table

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
| Weigh the glass | [force_torque_sensor_broadcaster](https://control.ros.org/jazzy/doc/ros2_controllers/force_torque_sensor_broadcaster/doc/userdoc.html) in the same package | a scale in the table, which cannot weigh a glass the arm is already holding |
| Come down onto the rack | the [admittance_controller](https://control.ros.org/jazzy/doc/ros2_controllers/admittance_controller/doc/userdoc.html), or [cartesian_controllers](https://github.com/fzi-forschungszentrum-informatik/cartesian_controllers) | commanding a height into a rigid plastic base |
| Sequence the steps and recover | [BehaviorTree.CPP](https://github.com/BehaviorTree/BehaviorTree.CPP) | a state machine, which becomes unreadable as soon as recovery branches multiply |
| Hold the per-type numbers | one file, one record per type | constants spread through the code |
| Record every attempt | [rosbag2](https://github.com/ros2/rosbag2), which ships with ROS 2 | log lines, which cannot show you the frame before the drop |

Two of these carry a real cost. MoveIt Task Constructor is a noticeably steeper climb
than plain MoveIt, and you can put it off until the turn actually fails to plan.
BehaviorTree.CPP adds a second language, written in XML, that anybody reading your
logic has to learn first.

The hardware is shorter. A two-finger parallel gripper with soft silicone pads, because
the pads raise friction and friction is the only thing that widens the low side of the
grip force window; suction is no use on a curved, wet, inverted object. A camera above
the table, and a second on the wrist, because the wrist camera removes the
camera-to-arm calibration error on the last few centimetres, and that is the error that
actually sinks this task. And a force reading at the wrist, needed twice: to weigh the
glass and to stop the descent.

---

## 6. How the robot reports each glass

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
| Result | placed, refused as full, refused as unrecognised, or failed at step N |

A refusal is a result, not an error. A glass with water in it that was left alone is
the system working, and it should be reported in the same words every time so that a
day's log can be counted.

Record every attempt with [rosbag2](https://github.com/ros2/rosbag2): the camera frames, the force trace, the finger
width, and the planned and actual poses. Without them, a failure next month is a story
rather than a bug.

---

## 7. When a step fails

Decide these before writing the code, because they change its shape.

| What happens | What the robot does |
| --- | --- |
| No glass where perception said | abandon this glass, take a new picture, carry on |
| Weight over the water gate | put it back exactly where it was, mark it full, carry on |
| Weight matches no record | put it back, mark it unknown, leave it for a person |
| Glass shifts in the fingers | put it down and grasp again, at most twice |
| Rim meets the rack too early | lift away, try the same slot once, then mark the slot bad |
| Load does not transfer before release | do not open the fingers, lift away, try again |
| Nothing standing in the slot afterwards | stop the cell and call a person |
| Anything breaks | stop the cell and call a person |

The last two are deliberately blunt. Broken glass leaves shards, and an arm that will
carry on moving through them, so a drop is never a retry. Water is worse than
breakage, because it spreads, it reaches the electronics, and it is a slip hazard for
the people nearby — which is the whole reason there are two gates before the turn
rather than one.

---

## 8. Build it in this order

Four sittings, each of which ends with something that runs.

1. **One straight glass, everything known.** Mark a spot on the table, measure the rack
   once, and hard-code both. No camera. This gets the grasp, the turn, the force
   descent and the release working, and it is the rig on which everything else is
   tested. Do it in [Gazebo](https://github.com/gazebosim/gz-sim) first, where a dropped glass costs nothing.
2. **Add the camera.** Steps 1 to 4 of section 4, so the glass can be anywhere, the
   rack can be anywhere, and full glasses are left alone. This is where most of the
   work is.
3. **Add the other four types.** Write the library, replace every constant in step 1
   with a lookup, and add the per-type rules about handles, tapers and slot spacing.
4. **Add the reporting and the recovery.** Section 6 and section 7, moved into a
   behaviour tree. Only now is it something you can leave running.

Do not start one of these until the previous one fails for a reason you can say out
loud. Getting the grip force from the simulator is the one thing that will not work:
rigid fingers on a thin rigid shell is close to the worst case for a physics engine, so
take the reach, the planning and the clearances from simulation, and get the grip from
a real glass.

---

## 9. Where to read more

- [The case study](docs/07_one-arm-training/07_case-study/01_place-glass.md) is the
  reasoning behind every choice here, including
  [what to use for each job](docs/07_one-arm-training/07_case-study/01_place-glass.md#4-which-part-uses-what)
  and
  [what to do about a glass with no record](docs/07_one-arm-training/07_case-study/01_place-glass.md#5-when-an-unfamiliar-glass-turns-up).
- [Tools and libraries](docs/06_tools-and-libraries.md) explains each of the tools in
  section 5 properly, with code, including
  [MoveIt 2](docs/06_tools-and-libraries.md#5-moveit-2-planning-a-safe-path),
  [ros2_control](docs/06_tools-and-libraries.md#6-ros2_control-driving-the-motors) and
  [behaviour trees](docs/06_tools-and-libraries.md#11-behaviour-trees-putting-a-task-in-order).
- [Programmed methods](docs/07_one-arm-training/02_programmed-methods.md) covers the
  [force control](docs/07_one-arm-training/02_programmed-methods.md#6-feedback-control)
  that steps 5, 6, 8 and 9 all depend on.
- [One-arm training](docs/07_one-arm-training/01_overview.md) is the map of every other
  way this job could have been built, and
  [why the programmed route suits this one](docs/07_one-arm-training/01_overview.md#5-which-method-for-which-task).
