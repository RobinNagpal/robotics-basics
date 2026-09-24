# The two-finger gripper, end to end

The parallel two-finger gripper is what most robot arms have on the end of them,
and it is what nearly every project in this repository assumes. The five
documents before this one cover gripping in general. This one takes the general
material and works it through on one gripper, concretely, with the ROS 2
interfaces you would actually call and the pseudo code you would actually write.

It uses the Robotiq 2F-85 as the worked example throughout, because it is the
most widely deployed gripper of its kind and its manuals publish real numbers.
Everything here transfers to a Schunk EGP, an OnRobot 2FG7 or a simulated gripper
of your own; the numbers change and the shape of the problem does not.

## Who this is for

Someone who has an arm with two fingers on it, has read
[the overview](01_overview.md), and now wants to know what to call, what comes
back, and what to do with it. You do not need to have used ros2_control. Terms
are explained where they appear.

## Contents

1. [What this gripper actually is](#1-what-this-gripper-actually-is)
2. [The ROS 2 interfaces, concretely](#2-the-ros-2-interfaces-concretely)
3. [Knowing how much force was applied](#3-knowing-how-much-force-was-applied)
4. [The grasp, as pseudo code](#4-the-grasp-as-pseudo-code)
5. [The feedback loop, as pseudo code](#5-the-feedback-loop-as-pseudo-code)
6. [The packages you would use](#6-the-packages-you-would-use)
7. [What is specific to this gripper](#7-what-is-specific-to-this-gripper)

---

## 1. What this gripper actually is

Two fingers that move towards each other, driven by one motor. That last part
matters more than anything else in this document.

**One motor, two fingers, and no independent control of either.** You command a
position and the fingers go there together. You cannot close one finger and not
the other, and you cannot ask for a different force on each side.

**It is underactuated.** The 2F-85's fingers are linkages, not rigid jaws, and
they have more degrees of freedom than the single motor can independently drive.
The consequence is covered in [the overview](01_overview.md#7-the-three-things-every-tutorial-leaves-out)
and is worth restating because it decides what you get: whether the gripper ends
up in a **parallel** grasp — pads flat and facing each other — or an
**encompassing** grasp, wrapping the fingertips round the object, is not
something you command. It depends on where the object sits and how it resists.
The payload differs between the two, and nothing in the program changes when the
gripper switches.

**It is self-locking.** Once closed on something, it holds without power. That is
a safety property — a power cut does not drop the object — and it is also why
"open the fingers" is a command you must issue rather than a default state.

The published numbers for the two common sizes, from Robotiq's own manuals:

| | 2F-85 | 2F-140 |
| --- | --- | --- |
| stroke | 85 mm | 140 mm |
| grip force | 20 to 235 N | 10 to 125 N |
| rated payload, friction grasp | 5 kg | 2.5 kg |
| finger speed | 20 to 150 mm/s | 30 to 250 mm/s |
| full-stroke closing time | 0.57 to 4.3 s, computed | 0.56 to 4.7 s, computed |

Read the force row as a *range you select*, not an accuracy. What arrives at the
object also depends on the object, which section 3 returns to.

The closing-time row is computed from the finger speed, not published: Robotiq's
specification table gives a speed and no time. Dividing the stroke by the speed
gives 85 / 150 = 0.57 s at full speed and 85 / 20 = 4.3 s at the slowest
setting. A real close is shorter than the full stroke, because the fingers start
partly closed and stop on the object — so treat these as an upper bound and
measure your own. Anyone quoting a figure of a few tens of milliseconds for this
gripper has taken it from somewhere other than the manual; the mechanism cannot
move 85 mm that fast.

## 2. The ROS 2 interfaces, concretely

There are three layers and it helps to keep them apart.

**The hardware interface** is the driver. It talks the gripper's own protocol and
presents it to ros2_control as a set of named *interfaces* — quantities that can
be commanded, and quantities that can be read.

**The controller** claims those interfaces and offers a ROS action or topic.

**Your code** calls that action.

For a two-finger gripper the controller you want is
[`parallel_gripper_controller`](https://github.com/ros-controls/ros2_controllers/tree/master/parallel_gripper_controller),
which is the current one in
[ros2_controllers](https://github.com/ros-controls/ros2_controllers). Its
parameters, read from its own declaration file, are worth knowing before you use
it:

| Parameter | Default | What it does |
| --- | --- | --- |
| `joint` | — | the single joint this gripper is |
| `state_interfaces` | `[position, velocity]` | what it reads back — add `effort` only if your hardware really exports it |
| `max_effort` | `10.0` | "Default effort used for grasping (Newtons)" |
| `max_effort_interface` | `""` | a command interface to write the effort to, if the hardware has one |
| `goal_tolerance` | `0.01` | metres |
| `allow_stalling` | `false` | whether stalling counts as success |
| `stall_velocity_threshold` | `0.001` | m/s below which it counts as stalled |
| `stall_timeout` | `1.0` | seconds it must stay there |

`allow_stalling` deserves a moment. Closing on an object *always* stalls the
fingers early — that is what gripping is. With `allow_stalling` false, the action
reports failure for every successful grasp. Setting it true is not a workaround;
it is the correct setting for grasping, and the default suits moving to a
position with nothing in the way.

### 2.1 The two actions

[`control_msgs`](https://github.com/ros-controls/control_msgs) defines both. The
older and more common one:

```
GripperCommand.action

  goal:    float64 position     # the gap you want, in metres
           float64 max_effort   # the most force to use getting there

  result:  float64 position     # the gap it ended at
           float64 effort       # "The current effort exerted (in Newtons)"
           bool    stalled      # exerting max effort and not moving
           bool    reached_goal # reached the commanded position
```

The newer `ParallelGripperCommand.action` carries a `sensor_msgs/JointState`
instead, so position, velocity and effort can be given per joint, and returns the
same two booleans.

Note what the whole of the feedback is: a position, an effort, and two booleans.
[Section 5.1 of holding on](05_holding-on.md#51-every-signal-you-can-get-and-what-each-one-settles)
sets out what that can and cannot settle.

## 3. Knowing how much force was applied

This is the question this document exists to answer properly, and the honest
answer has three parts.

### 3.1 The field exists and is specified in Newtons

`GripperCommand`'s result and feedback both carry `float64 effort`, and the
message's own comment says **"The current effort exerted (in Newtons)"**. So the
interface for reading applied force is defined, standard, and unambiguous about
units.

### 3.2 For the most common gripper, nothing fills it in

The official ROS 2 driver is
[ros2_robotiq_gripper](https://github.com/PickNikRobotics/ros2_robotiq_gripper).
Its hardware interface exports exactly two state interfaces, and this is the
whole function:

```cpp
std::vector<hardware_interface::StateInterface>
RobotiqGripperHardwareInterface::export_state_interfaces()
{
  state_interfaces.emplace_back(StateInterface(joint, HW_IF_POSITION, &gripper_position_));
  state_interfaces.emplace_back(StateInterface(joint, HW_IF_VELOCITY, &gripper_velocity_));
  return state_interfaces;
}
```

Position and velocity. **There is no effort state interface**, so nothing
downstream can report the force being applied. The driver also rejects any
command interface that is not position, and the maximum force is a *static
hardware parameter* read from the URDF at startup — `gripper_max_force` — rather
than something you set per grasp or read back.

So for the most widely used two-finger gripper in the world, through its official
ROS 2 driver: **you cannot read the force, and you cannot command it per grasp.**
The `effort` field will be whatever the controller put there, which is not a
measurement.

This is not a criticism of the driver. The underlying gripper reports motor
current rather than fingertip force, and the relationship between the two depends
on which grasp mode the linkage settled into — see section 1. Publishing a number
in Newtons would mean inventing one.

### 3.3 What to do instead

Five routes, in order of how much they cost you.

**Command the force and trust the specification.** Set `max_effort`, and rely on
the manufacturer's force-against-setting table. This is what most cells do, and
it is reasonable as long as you remember the force reaching the object varies
with the object's hardness. The overview covers that; Robotiq's own measurements
span 220 N on steel and 115 N on soft rubber at one setting.

**Read the joint effort, if your hardware offers one.** Some grippers do export
an effort state interface, in which case `joint_state_broadcaster` will publish
it in `sensor_msgs/JointState.effort` and you can add `effort` to the
controller's `state_interfaces`. Check first: `JointState`'s own documentation
says the effort array may be left empty, and many drivers do exactly that.

```
ros2 topic echo /joint_states --field effort
```

An empty array or a constant zero means the field is not populated, not that the
force is zero.

**Read the motor current, through the vendor's own interface.** The Robotiq
protocol exposes a current register, and vendor-specific drivers surface it. It
is a real measurement and it is not Newtons; converting requires a calibration
you do yourself, and that calibration is only valid for one grasp mode.

**Measure the result instead of the cause.** You do not usually care about the
grip force for its own sake; you care whether the object is held. The wrist
force-torque sensor answers that directly, and
[holding on, section 5.1](05_holding-on.md#51-every-signal-you-can-get-and-what-each-one-settles)
explains why the pair of finger gap and wrist weight settles what neither settles
alone.

**Put a sensor on the finger.** A tactile pad gives you the contact patch and the
force distribution over it. This is the only route that measures what is actually
happening at the object, and it is covered in
[the sensors section of the perception area](../06_object-perception/02_sensors.md#23-the-sensors).

The practical recommendation is the fourth. Commanding a force and confirming the
outcome at the wrist is cheaper, more reliable and more informative than trying to
read a number the hardware does not produce.

## 4. The grasp, as pseudo code

The five-step sequence from [holding on](05_holding-on.md#1-the-squeeze-sequence),
written out for this gripper. In pseudo code first:

```
estimate mass from the measured outline           (shell volume x wall category)
force = mass * g * safety / (2 * friction)
if force > damage_cap(kind): refuse, and say why

open fingers to grip_width + clearance
move to the pre-grasp pose
move straight in to the grasp pose

close fingers to grip_width with max_effort = contact_force   (gentle)
wait for the action to settle
if |gap_reached - grip_width| > tolerance: refuse, and say why

close again with max_effort = force                           (the real squeeze)
lift 10 mm
weight = median of 32 wrist samples, rotated into the world frame
mass_measured = (weight - gripper_weight) / g

if required_force(mass_measured) > damage_cap(kind): put it down, refuse
if required_force(mass_measured) > force:
    put it down, re-close at the higher force, lift again
```

The same thing as ROS 2 calls, with the parts that matter:

```python
from control_msgs.action import GripperCommand

def close_to(gap_m: float, effort_n: float) -> GripperCommand.Result:
    goal = GripperCommand.Goal()
    goal.command.position = gap_m / 2.0      # per finger, on a symmetric pair
    goal.command.max_effort = effort_n
    return client.send_goal(goal).result     # blocks until stalled or reached

# gentle contact first: the width the fingers stop at is a measurement
touched = close_to(grip_width, CONTACT_FORCE_N)
if abs(touched.position * 2 - grip_width) > 0.004:
    raise NoGrip("the fingers met the object at a width the camera did not predict")

# then the real squeeze, worked out from the estimate
close_to(grip_width, required_force(estimated_mass))
```

Two details in that code are the whole reason for writing it out.

**`position` is usually per finger, not the gap.** A symmetric two-finger gripper
has one joint whose value is one finger's travel, so the gap is twice it. Getting
this wrong gives you an object half the width you meant, and the failure looks
like a perception error.

**The width at first contact is a measurement, and a free one.** The fingers stop
where the object is. Comparing that against what the camera predicted is the
cheapest check in the whole sequence, and it catches a grasp that is in the wrong
place before any force is applied.

## 5. The feedback loop, as pseudo code

What to watch while holding, and what to do about each thing you might see.
[Holding on, section 5](05_holding-on.md#5-feedback-and-what-to-do-with-it) has
the full table; this is that table as a loop.

```
held_at = gripper gap now
expected = mass_measured * g + gripper_weight

every control cycle while carrying:

    gap = gripper gap now
    if held_at - gap > SLIP_TOLERANCE:
        the object is being squashed or is sliding
        -> if force < damage_cap: increase force, else put it down and refuse

    weight = wrist force, world vertical
    if weight < expected - MARGIN:
        the object has gone, or is going
        -> stop the arm, look, and report

    torque = wrist torque magnitude
    if torque has changed since the lift:
        the object has rotated in the fingers
        -> stop; a corrected grasp from stale measurements is worse than none

before opening the fingers:
    if weight has not returned to gripper_weight:
        whatever it is standing on is not taking the weight
        -> do not open; it is caught, not placed
```

The last check is the one people leave out, and
[holding on, section 8](05_holding-on.md#8-letting-go) is about it. Contact is
not support.

## 6. The packages you would use

Everything here is Apache-2.0 or BSD unless the row says otherwise, and all of it
runs on an Apple Silicon Mac through RoboStack.

| Package | Licence | What it gives you |
| --- | --- | --- |
| [ros2_control](https://github.com/ros-controls/ros2_control) | Apache-2.0 | the interface framework the rest sits on |
| [ros2_controllers](https://github.com/ros-controls/ros2_controllers) | Apache-2.0 | `parallel_gripper_controller`, `joint_state_broadcaster`, `force_torque_sensor_broadcaster` |
| [control_msgs](https://github.com/ros-controls/control_msgs) | Apache-2.0 | `GripperCommand` and `ParallelGripperCommand` |
| [ros2_robotiq_gripper](https://github.com/PickNikRobotics/ros2_robotiq_gripper) | BSD-3 | the Robotiq driver, description and controllers |
| [moveit2](https://github.com/moveit/moveit2) | BSD-3 | drives the gripper through the same action, as part of a plan |

For simulation, Gazebo's `gz_ros2_control` presents the same interfaces a real
driver would, so a gripper developed against the simulator does not change when
it meets hardware. That is the main reason to go through ros2_control rather than
talking to the gripper directly.

## 7. What is specific to this gripper

Worth separating, because a good deal of general grasping advice does not apply
to two fingers and it is not always obvious which.

**Two contacts cannot resist twist.** Two pads can hold an object against gravity
and against a pull, and they resist rotation about the grasp axis only through
the friction of the patches themselves. That is why
[the centre-of-mass torque](03_choosing-a-grip.md#5-the-centre-of-mass-and-the-torque-nobody-budgets-for)
matters so much more here than on a three-finger or a suction gripper.

**The grasp is a line, not a point.** What you must choose is where the line
between the two pads crosses the object, and at what angle. That is two fewer
degrees of freedom than a general 6-DoF grasp pose, which makes the search much
cheaper — and is why a geometric rule works so well for objects with a
describable shape.

**Width is a measurement you get for free.** No other gripper type tells you the
object's dimension as a side effect of grasping it.

**Symmetry means two solutions.** Every grasp has an identical twin rotated half
a turn, because swapping which finger is on which side changes nothing about the
grip. It changes a great deal about whether the arm can reach — and whether it
can still turn afterwards, which
[arm movement](../08_arm-movement/01_overview.md) covers.

Five jobs a two-finger gripper suits:

- objects with two roughly parallel faces, or a graspable neck or stem
- anything where you want the object's width measured as part of picking it up
- cells where one gripper must handle a range of sizes without changing tooling
- work needing a firm hold that survives acceleration, unlike suction
- any object a rule can describe, where the grasp is decided rather than searched

Five jobs it cannot do:

- large flat sheets, which have nothing to get either side of — that is suction
- objects heavier than the friction grasp supports, where a form-fitting or
  magnetic hold is needed
- resisting twist about the grasp axis, which needs a third contact
- anything requiring a grip and a manipulation at once, which needs more fingers
- reaching into a space narrower than the gripper body, which is a constraint on
  the whole design and not on the grasp
